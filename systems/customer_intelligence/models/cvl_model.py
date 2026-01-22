from pathlib import Path
import json
import hashlib
import numpy as np
import pandas as pd

from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, FunctionTransformer, StandardScaler
from sklearn.ensemble import GradientBoostingClassifier, GradientBoostingRegressor
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import (
    mean_squared_error,
    mean_absolute_error,
    r2_score,
    roc_auc_score,
)
import joblib

# ============================
# CONFIG
# ============================

RANDOM_STATE = 42
MODEL_NAME = "clv_two_stage"
DATA_PATH = Path("../../../data/processed/system1/clv/features.parquet")
MODEL_REGISTRY = Path("../../../deployment/model_registry/system1/clv")

MODEL_REGISTRY.mkdir(parents = True, exist_ok = True)

CAT_COLS = ["country", "acquisition_channel", "device_type"]

LOG_COLS = [
    "recency_days","tenure_days","order_count","total_spend","avg_order_value",
    "order_frequency","session_count","session_frequency","avg_session_duration",
    "avg_pages","spend_7d","orders_7d","spend_30d","orders_30d",
    "spend_90d","orders_90d","sessions_7d","sessions_30d",
    "pages_7d","pages_30d","spend_velocity","order_velocity","session_velocity"
]

RATE_COLS = ["return_rate","discount_rate"]

TARGET = "future_90d_spend"
ID_COL = "customer_id"

# ============================
# UTILS
# ============================

def dataset_fingerprint(df: pd.DataFrame) -> str:
    h = hashlib.md5(pd.util.hash_pandas_object(df, index=True).values)
    return h.hexdigest()


def recall_safe_div(num, den):
    return num / den if den > 0 else 0.0


# ============================
# DATA LOADING
# ============================

def load_dataset(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Missing dataset: {path}")

    df = pd.read_parquet(path)

    required = set(CAT_COLS + LOG_COLS + RATE_COLS + [TARGET, ID_COL])
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    return df


# ============================
# TEMPORAL SPLIT (NO LEAKAGE)
# ============================

def temporal_split(df: pd.DataFrame):
    """
    recency_days already encodes snapshot logic.
    Smaller recency = more recent customer.
    """

    cutoff = df["recency_days"].quantile(0.8)

    train_df = df[df["recency_days"] >= cutoff]
    future_df = df[df["recency_days"] < cutoff]

    return train_df, future_df


# ============================
# PREPROCESSING
# ============================

def build_preprocessor(log_caps):

    def safe_log1p(x):
        x = np.asarray(x)
        x = np.clip(x, 0, log_caps)
        return np.log1p(x)

    log_pipe = Pipeline([
        ("log", FunctionTransformer(safe_log1p, feature_names_out="one-to-one")),
        ("scale", StandardScaler())
    ])

    return ColumnTransformer(
        transformers=[
            ("log", log_pipe, LOG_COLS),
            ("rate", StandardScaler(), RATE_COLS),
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse=False), CAT_COLS),
        ],
        remainder="drop"
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
        random_state=RANDOM_STATE,
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
            random_state=RANDOM_STATE,
        )),
    ])

    model.fit(X, y_log)
    return model


# ============================
# EVALUATION
# ============================

def evaluate_clv(y_true, y_pred):
    return {
        "rmse": np.sqrt(mean_squared_error(y_true, y_pred)),
        "mae": mean_absolute_error(y_true, y_pred),
        "r2": r2_score(y_true, y_pred),
    }


# ============================
# REGISTRY
# ============================

def next_version(model_dir: Path) -> int:
    versions = [
        int(p.name.split("_v")[-1])
        for p in model_dir.glob(f"{MODEL_NAME}_v*.joblib")
    ]
    return max(versions, default=0) + 1


# ============================
# MAIN
# ============================

def main():
    df = load_dataset(DATA_PATH)
    fingerprint = dataset_fingerprint(df)

    train_df, future_df = temporal_split(df)

    X_train = train_df[LOG_COLS + RATE_COLS + CAT_COLS]
    y_train = train_df[TARGET]
    y_train_log = np.log1p(y_train)

    X_future = future_df[LOG_COLS + RATE_COLS + CAT_COLS]
    y_future = future_df[TARGET]

    # Purchase target
    y_buy = (y_train > 0).astype(int)

    # Stable log caps (TRAIN ONLY)
    log_caps = X_train[LOG_COLS].quantile(0.999).values

    preprocess = build_preprocessor(log_caps)

    purchase_model = train_purchase_model(preprocess, X_train, y_buy)

    p_buy = purchase_model.predict_proba(X_future)[:, 1]
    auc = roc_auc_score((y_future > 0).astype(int), p_buy)

    # Spend model (positive only)
    pos_mask = y_train > 0
    spend_model = train_spend_model(
        preprocess,
        X_train[pos_mask],
        y_train_log[pos_mask],
    )

    train_pred_log = spend_model.predict(X_train[pos_mask])
    residuals = y_train_log[pos_mask] - train_pred_log
    smearing = float(np.mean(np.exp(residuals)))

    pred_log = spend_model.predict(X_future)
    pred_spend = np.expm1(pred_log) * smearing

    final_pred = p_buy * pred_spend
    metrics = evaluate_clv(y_future, final_pred)

    # ============================
    # SAVE ARTIFACT
    # ============================

    version = next_version(MODEL_REGISTRY)
    model_path = MODEL_REGISTRY / f"{MODEL_NAME}_v{version}.joblib"
    meta_path = MODEL_REGISTRY / f"{MODEL_NAME}_v{version}.json"

    artifact = {
        "purchase_model": purchase_model,
        "spend_model": spend_model,
        "smearing": smearing,
    }

    joblib.dump(artifact, model_path)

    metadata = {
        "model": MODEL_NAME,
        "version": version,
        "dataset_fingerprint": fingerprint,
        "features": {
            "log": LOG_COLS,
            "rate": RATE_COLS,
            "categorical": CAT_COLS,
        },
        "metrics": {
            "purchase_auc": auc,
            "clv": metrics,
        },
    }

    with open(meta_path, "w") as f:
        json.dump(metadata, f, indent=2)

    print("Saved CLV model:", model_path)
    print("Future metrics:", metrics)


if __name__ == "__main__":
    main()
