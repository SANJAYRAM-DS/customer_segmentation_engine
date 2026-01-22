from pathlib import Path
import json
import hashlib
import numpy as np
import pandas as pd

from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, FunctionTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, average_precision_score
from sklearn.calibration import CalibratedClassifierCV
from sklearn.model_selection import train_test_split

import joblib

# ============================
# CONFIG
# ============================

RANDOM_STATE = 42
MODEL_NAME = "churn_logistic"
DATA_PATH = Path("../../../data/processed/system1/churn/features.parquet")
MODEL_REGISTRY = Path("../../../deployment/model_registry/system1/churn")

MODEL_REGISTRY.mkdir(parents=True, exist_ok=True)

CAT_COLS = ["country", "acquisition_channel", "device_type"]

LOG_COLS = [
    "recency_days", "tenure_days", "order_count", "total_spend",
    "avg_order_value", "order_frequency", "session_count",
    "session_frequency", "avg_session_duration", "avg_pages"
]

RATE_COLS = ["return_rate", "discount_rate"]

TARGET = "is_churned"
ID_COL = "customer_id"

# ============================
# UTILS
# ============================

def recall_at_k(y_true, y_score, k=0.1):
    threshold = np.quantile(y_score, 1 - k)
    preds = y_score >= threshold
    return (y_true[preds].sum() / max(y_true.sum(), 1))


def dataset_fingerprint(df: pd.DataFrame) -> str:
    """Used for lineage tracking"""
    h = hashlib.md5(pd.util.hash_pandas_object(df, index=True).values)
    return h.hexdigest()


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
# SPLIT (NO LEAKAGE)
# ============================

def temporal_split(df: pd.DataFrame):
    """
    IMPORTANT:
    recency_days already encoded snapshot logic upstream.
    Smaller recency = more recent activity.
    """

    cutoff = df["recency_days"].quantile(0.8)

    train_df = df[df["recency_days"] >= cutoff]
    future_df = df[df["recency_days"] < cutoff]

    X_train = train_df.drop(columns=[TARGET, ID_COL])
    y_train = train_df[TARGET]

    X_future = future_df.drop(columns=[TARGET, ID_COL])
    y_future = future_df[TARGET]

    return X_train, y_train, X_future, y_future


# ============================
# PREPROCESSING
# ============================

def safe_log1p(x):
    x = np.clip(x, 0, np.nanpercentile(x, 99.9))
    return np.log1p(x)


def build_preprocessor():
    log_pipe = Pipeline([
        ("log", FunctionTransformer(safe_log1p, feature_names_out="one-to-one"))
    ])

    return ColumnTransformer(
        transformers=[
            ("log", log_pipe, LOG_COLS),
            ("rate", "passthrough", RATE_COLS),
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse=False), CAT_COLS),
        ],
        remainder="drop"
    )


# ============================
# TRAINING
# ============================

def train_model(X_train, y_train):
    base_model = LogisticRegression(
        max_iter=1000,
        C=1.0,
        class_weight="balanced",
        random_state=RANDOM_STATE,
        n_jobs=1
    )

    pipeline = Pipeline([
        ("prep", build_preprocessor()),
        ("model", base_model)
    ])

    calibrated = CalibratedClassifierCV(
        pipeline,
        method="sigmoid",
        cv=3
    )

    calibrated.fit(X_train, y_train)
    return calibrated


# ============================
# EVALUATION
# ============================

def evaluate(model, X, y):
    prob = model.predict_proba(X)[:, 1]

    return {
        "roc_auc": roc_auc_score(y, prob),
        "pr_auc": average_precision_score(y, prob),
        "recall_at_10pct": recall_at_k(y, prob, 0.1)
    }


# ============================
# MODEL REGISTRY
# ============================

def next_version(model_dir: Path) -> int:
    versions = [
        int(p.name.split("_v")[-1])
        for p in model_dir.glob(f"{MODEL_NAME}_v*.joblib")
    ]
    return max(versions, default=0) + 1


def save_model(model, metadata: dict):
    version = next_version(MODEL_REGISTRY)
    model_path = MODEL_REGISTRY / f"{MODEL_NAME}_v{version}.joblib"
    meta_path = MODEL_REGISTRY / f"{MODEL_NAME}_v{version}.json"

    joblib.dump(model, model_path)

    with open(meta_path, "w") as f:
        json.dump(metadata, f, indent=2)

    return model_path, meta_path


# ============================
# MAIN
# ============================

def main():
    df = load_dataset(DATA_PATH)

    fingerprint = dataset_fingerprint(df)

    X_train, y_train, X_future, y_future = temporal_split(df)

    model = train_model(X_train, y_train)

    train_metrics = evaluate(model, X_train, y_train)
    future_metrics = evaluate(model, X_future, y_future)

    metadata = {
        "model_name": MODEL_NAME,
        "dataset_fingerprint": fingerprint,
        "features": {
            "categorical": CAT_COLS,
            "log_scaled": LOG_COLS,
            "rate": RATE_COLS
        },
        "metrics": {
            "train": train_metrics,
            "future": future_metrics
        }
    }

    model_path, meta_path = save_model(model, metadata)

    print("Model saved:", model_path)
    print("Metadata saved:", meta_path)
    print("Future metrics:", future_metrics)


if __name__ == "__main__":
    main()
