from pathlib import Path
import json
import hashlib
import time
from contextlib import contextmanager

import numpy as np
import pandas as pd
import joblib
import yaml

from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import FunctionTransformer, StandardScaler
from sklearn.ensemble import GradientBoostingClassifier, GradientBoostingRegressor
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score, roc_auc_score

from backend.data.feature_registry.loader import load_feature_registry
from backend.models.utils import safe_log1p_with_caps
from backend.models.champion_manager import load_champion, promote_champion
from backend.models.promotion import PromotionPolicy
from backend.orchestration.baseline_stats import save_baseline_stats


# ============================
# PATHS / CONFIG
# ============================

BASE_DIR = Path(__file__).resolve().parents[3]
CONFIG_PATH = Path(__file__).parent / "config.yaml"
MODEL_REGISTRY = BASE_DIR / "backend" / "models" / "model_registry" / "clv"

MODEL_REGISTRY.mkdir(parents=True, exist_ok=True)

with open(CONFIG_PATH, "r") as f:
    cfg = yaml.safe_load(f)

MODEL_NAME = cfg["model"]["name"]
TARGET = cfg["data"]["target"]
ID_COL = cfg["data"]["id_col"]

LOG_COLS = cfg["features"]["log_scaled"]
RATE_COLS = cfg["features"]["rate"]


# ============================
# UTILS
# ============================

def dataset_fingerprint(df: pd.DataFrame) -> str:
    return hashlib.md5(
        pd.util.hash_pandas_object(df, index=True).values
    ).hexdigest()


def next_version() -> int:
    versions = [
        int(p.stem.split("_v")[-1])
        for p in MODEL_REGISTRY.glob(f"{MODEL_NAME}_v*.joblib")
    ]
    return max(versions, default=0) + 1


@contextmanager
def timed_block(name: str):
    start = time.perf_counter()
    yield
    elapsed = time.perf_counter() - start
    print(f"[TIME] {name}: {elapsed:.2f}s")


# ============================
# DATA LOADING (REGISTRY FIRST)
# ============================

def load_dataset() -> pd.DataFrame:
    df = pd.read_parquet(BASE_DIR / cfg["data"]["features_path"])

    registry = load_feature_registry("clv", "v1")
    expected = list(registry["features"].keys())

    # strict enforcement
    return df[expected]


# ============================
# TEMPORAL SPLIT (NO LEAKAGE)
# ============================

def temporal_split(df: pd.DataFrame):
    cutoff = df["recency_days"].quantile(0.8)

    train_df = df[df["recency_days"] < cutoff]
    future_df = df[df["recency_days"] >= cutoff]

    return train_df, future_df


# ============================
# PREPROCESSOR
# ============================

def build_preprocessor(log_caps):
    log_pipe = Pipeline([
        (
            "log",
            FunctionTransformer(
                safe_log1p_with_caps,
                kw_args={"caps": log_caps},
                feature_names_out="one-to-one",
            ),
        ),
        ("scale", StandardScaler()),
    ])

    return ColumnTransformer(
        transformers=[
            ("log", log_pipe, LOG_COLS),
            ("rate", StandardScaler(), RATE_COLS),
        ]
    )


# ============================
# TRAINING
# ============================

def train_purchase_model(prep, X, y_binary):
    base = GradientBoostingClassifier(
        n_estimators=300,
        learning_rate=0.05,
        max_depth=3,
        subsample=0.8,
        random_state=cfg["model"]["random_state"],
    )

    model = Pipeline([
        ("prep", prep),
        ("clf", CalibratedClassifierCV(base, method="isotonic", cv=3)),
    ])

    model.fit(X, y_binary)
    return model


def train_spend_model(prep, X, y_log):
    model = Pipeline([
        ("prep", prep),
        ("reg", GradientBoostingRegressor(
            n_estimators=400,
            learning_rate=0.05,
            max_depth=3,
            subsample=0.8,
            random_state=cfg["model"]["random_state"],
        )),
    ])

    model.fit(X, y_log)
    return model


# ============================
# EVALUATION
# ============================

def evaluate_clv(y_true, y_pred):
    return {
        "rmse": float(np.sqrt(mean_squared_error(y_true, y_pred))),
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "r2": float(r2_score(y_true, y_pred)),
    }


# ============================
# MAIN
# ============================

def main():
    df = load_dataset()
    fingerprint = dataset_fingerprint(df)

    train_df, future_df = temporal_split(df)

    X_train = train_df[LOG_COLS + RATE_COLS]
    y_train = train_df[TARGET]
    y_train_log = np.log1p(y_train)

    X_future = future_df[LOG_COLS + RATE_COLS]
    y_future = future_df[TARGET]

    y_buy = (y_train > 0).astype(int)

    log_caps = X_train[LOG_COLS].quantile(0.999).values
    prep = build_preprocessor(log_caps)

    with timed_block("Purchase model"):
        purchase_model = train_purchase_model(prep, X_train, y_buy)

    with timed_block("Spend model"):
        pos_mask = y_train > 0
        spend_model = train_spend_model(
            prep,
            X_train[pos_mask],
            y_train_log[pos_mask],
        )

    with timed_block("Inference + metrics"):
        p_buy = purchase_model.predict_proba(X_future)[:, 1]

        purchase_auc = (
            roc_auc_score((y_future > 0).astype(int), p_buy)
            if (y_future > 0).nunique() > 1
            else None
        )

        residuals = y_train_log[pos_mask] - spend_model.predict(X_train[pos_mask])
        smearing = float(np.mean(np.exp(residuals)))

        pred_log = spend_model.predict(X_future)
        pred_spend = np.expm1(pred_log) * smearing

        final_pred = p_buy * pred_spend
        clv_metrics = evaluate_clv(y_future, final_pred)

    # --------------------------------------------------
    # VERSIONING
    # --------------------------------------------------
    version = next_version()
    model_path = MODEL_REGISTRY / f"{MODEL_NAME}_v{version}.joblib"
    meta_path = MODEL_REGISTRY / f"{MODEL_NAME}_v{version}.json"

    artifact = {
        "purchase_model": purchase_model,
        "spend_model": spend_model,
        "smearing": smearing,
    }

    joblib.dump(artifact, model_path)

    metrics = {
        "purchase_auc": purchase_auc,
        "clv": clv_metrics,
    }

    with open(meta_path, "w") as f:
        json.dump(
            {
                "model": MODEL_NAME,
                "version": version,
                "dataset_fingerprint": fingerprint,
                "metrics": metrics,
            },
            f,
            indent=2,
        )

    print("[OK] CLV model saved:", model_path)
    print("[METRICS]", clv_metrics)

    # --------------------------------------------------
    # 🏆 CHAMPION LOGIC
    # --------------------------------------------------
    current = load_champion(MODEL_REGISTRY)
    
    policy = PromotionPolicy(
        min_improvement=0.01,  # 1% minimum improvement
        max_secondary_regression=0.05,  # 5% max regression on secondary metrics
    )

    if current is None:
        # No existing champion, promote automatically
        promote_champion(
            model_dir=MODEL_REGISTRY,
            model_name=MODEL_NAME,
            version=version,
            metrics=metrics,
            reason="Initial champion model",
        )

        # Baseline stats (TRAIN FEATURES ONLY)
        save_baseline_stats(
            df.drop(columns=[TARGET]),
            MODEL_REGISTRY / "baseline_stats.json",
        )

        print("[CHAMPION] Initial CLV champion promoted")
    else:
        # Use enhanced promotion policy
        should_promote, reason = policy.evaluate_clv_promotion(
            challenger_metrics=metrics["clv"],
            champion_metrics=current["metrics"].get("clv", current["metrics"]),
        )
        
        if should_promote:
            promote_champion(
                model_dir=MODEL_REGISTRY,
                model_name=MODEL_NAME,
                version=version,
                metrics=metrics,
                reason=reason,
            )

            # Baseline stats (TRAIN FEATURES ONLY)
            save_baseline_stats(
                df.drop(columns=[TARGET]),
                MODEL_REGISTRY / "baseline_stats.json",
            )

            print(f"[CHAMPION] {reason}")
        else:
            print(f"[CHALLENGER] {reason}")



if __name__ == "__main__":
    main()