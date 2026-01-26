from pathlib import Path
import json
import yaml
import hashlib

import numpy as np
import pandas as pd
import joblib

from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, FunctionTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import roc_auc_score, average_precision_score

from backend.data.feature_registry.loader import load_feature_registry
from backend.models.utils import safe_log1p
from backend.models.champion_manager import load_champion, promote_champion
from backend.models.promotion_policy import better_churn
from backend.orchestration.baseline_stats import save_baseline_stats


BASE_DIR = Path(__file__).resolve().parents[3]
REGISTRY_DIR = BASE_DIR / "backend" / "models" / "model_registry" / "churn"
CONFIG_PATH = Path(__file__).parent / "config.yaml"

REGISTRY_DIR.mkdir(parents=True, exist_ok=True)
model_dir = REGISTRY_DIR
current = load_champion(model_dir)
# -------------------------
# Utils
# -------------------------
def dataset_fingerprint(df: pd.DataFrame) -> str:
    return hashlib.md5(
        pd.util.hash_pandas_object(df, index=True).values
    ).hexdigest()


def next_version(model_dir: Path, model_name: str) -> int:
    versions = [
        int(p.stem.split("_v")[-1])
        for p in model_dir.glob(f"{model_name}_v*.joblib")
    ]
    return max(versions, default=0) + 1


# -------------------------
# Load config
# -------------------------
with open(CONFIG_PATH, "r") as f:
    cfg = yaml.safe_load(f)

MODEL_NAME = cfg["model"]["name"]
TARGET = cfg["data"]["target"]
ID_COL = cfg["data"]["id_col"]

CAT_COLS = cfg["features"]["categorical"]
LOG_COLS = cfg["features"]["log_scaled"]
RATE_COLS = cfg["features"]["rate"]


# -------------------------
# Load & validate data
# -------------------------
def load_dataset():
    df = pd.read_parquet(BASE_DIR / cfg["data"]["features_path"])

    registry = load_feature_registry("churn", "v1")
    expected = list(registry["features"].keys())

    # strict registry enforcement
    df = df[expected]

    return df


# -------------------------
# Split (no leakage)
# -------------------------
def temporal_split(df):
    df = df.sort_values("recency_days")
    split = int(len(df) * cfg["training"]["temporal_split_ratio"])

    train = df.iloc[:split]
    future = df.iloc[split:]

    X_train = train.drop(columns=[TARGET, ID_COL])
    y_train = train[TARGET]

    X_future = future.drop(columns=[TARGET, ID_COL])
    y_future = future[TARGET]

    return X_train, y_train, X_future, y_future


# -------------------------
# Pipeline
# -------------------------
def build_pipeline():
    log_pipe = Pipeline([
        ("log", FunctionTransformer(safe_log1p, feature_names_out="one-to-one"))
    ])

    transformers = [
        ("log", log_pipe, LOG_COLS),
        ("rate", "passthrough", RATE_COLS),
    ]

    prep = ColumnTransformer(transformers)

    base = LogisticRegression(
        max_iter=1000,
        class_weight="balanced",
        random_state=cfg["model"]["random_state"]
    )

    pipe = Pipeline([
        ("prep", prep),
        ("model", base)
    ])

    if cfg["training"]["calibrate"]:
        return CalibratedClassifierCV(
            pipe,
            method="sigmoid",
            cv=cfg["training"]["calibration_cv"]
        )

    return pipe


# -------------------------
# Metrics
# -------------------------
def evaluate(model, X, y):
    prob = model.predict_proba(X)[:, 1]
    return {
        "roc_auc": roc_auc_score(y, prob),
        "pr_auc": average_precision_score(y, prob),
    }


# -------------------------
# Train
# -------------------------
def main():
    df = load_dataset()
    fingerprint = dataset_fingerprint(df)

    X_train, y_train, X_future, y_future = temporal_split(df)

    model = build_pipeline()
    model.fit(X_train, y_train)

    metrics = {
        "train": evaluate(model, X_train, y_train),
        "future": evaluate(model, X_future, y_future),
    }

    version = next_version(REGISTRY_DIR, MODEL_NAME)

    model_path = REGISTRY_DIR / f"{MODEL_NAME}_v{version}.joblib"
    meta_path = REGISTRY_DIR / f"{MODEL_NAME}_v{version}.json"

    joblib.dump(model, model_path)

    with open(meta_path, "w") as f:
        json.dump(
            {
                "model": MODEL_NAME,
                "version": version,
                "dataset_fingerprint": fingerprint,
                "metrics": metrics,
                "config": cfg,
            },
            f,
            indent=2,
        )

    # ✅ CHAMPION–CHALLENGER DECISION (CORRECT LOCATION)
    current = load_champion(REGISTRY_DIR)

    if current is None or better_churn(metrics["future"], current["metrics"]):
        promote_champion(
            model_dir=REGISTRY_DIR,
            model_name="churn",
            version=version,
            metrics=metrics["future"],
            reason="Auto-promotion: better PR-AUC",
        )
    baseline_path = (
    REGISTRY_DIR / "baseline_stats.json"
    )

    features = df.drop(columns=[TARGET])  # use training data only
    save_baseline_stats(features, baseline_path)

    print("[OK] Model saved:", model_path)
    print("[METRICS]", metrics["future"])



if __name__ == "__main__":
    main()
