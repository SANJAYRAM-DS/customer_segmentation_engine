# backend/models/segmentation/train.py

from pathlib import Path
import json
import hashlib
import yaml
import time
from contextlib import contextmanager

import numpy as np
import pandas as pd
import joblib

from sklearn.cluster import MiniBatchKMeans
from sklearn.preprocessing import RobustScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import (
    silhouette_score,
    davies_bouldin_score,
    calinski_harabasz_score,
)

from backend.data.feature_registry.loader import load_feature_registry
from backend.models.champion_manager import load_champion, promote_champion
from backend.models.promotion_policy import better_segmentation
from backend.orchestration.baseline_stats import save_baseline_stats


# -------------------------
# Paths & config
# -------------------------
BASE_DIR = Path(__file__).resolve().parents[3]
CONFIG_PATH = Path(__file__).parent / "config.yaml"
MODEL_REGISTRY = BASE_DIR / "backend/models/model_registry/segmentation"
MODEL_REGISTRY.mkdir(parents=True, exist_ok=True)

with open(CONFIG_PATH, "r") as f:
    cfg = yaml.safe_load(f)

MODEL_NAME = cfg["model"]["name"]
RANDOM_STATE = cfg["model"]["random_state"]
DEFAULT_K = cfg["model"]["default_k"]

DATA_PATH = BASE_DIR / cfg["data"]["features_path"]
ID_COL = cfg["data"]["id_col"]

SEG_FEATURES = cfg["features"]["used"]
MAX_SIL_SAMPLE = cfg["training"]["max_silhouette_sample"]


# -------------------------
# Utils
# -------------------------
@contextmanager
def timed_block(name: str):
    start = time.perf_counter()
    yield
    print(f"[TIME] {name}: {time.perf_counter() - start:.2f}s")


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


# -------------------------
# Load & validate data
# -------------------------
def load_dataset() -> pd.DataFrame:
    df = pd.read_parquet(DATA_PATH)

    registry = load_feature_registry("segmentation", "v1")
    expected = set(registry["features"].keys())

    missing = expected - set(df.columns)
    if missing:
        raise ValueError(f"Missing registry features: {missing}")

    df = df[list(expected)]

    if cfg["training"]["drop_cold_start"]:
        mask = (df[SEG_FEATURES].sum(axis=1) > 0)
        df = df.loc[mask].reset_index(drop=True)

    return df


# -------------------------
# Evaluation
# -------------------------
def evaluate_clusters(X_scaled, labels):
    if len(labels) > MAX_SIL_SAMPLE:
        idx = np.random.choice(len(labels), MAX_SIL_SAMPLE, replace=False)
        X_eval, y_eval = X_scaled[idx], labels[idx]
    else:
        X_eval, y_eval = X_scaled, labels

    return {
        "silhouette": float(silhouette_score(X_eval, y_eval)),
        "davies_bouldin": float(davies_bouldin_score(X_scaled, labels)),
        "calinski_harabasz": float(calinski_harabasz_score(X_scaled, labels)),
    }

def main():
    df = load_dataset()
    fingerprint = dataset_fingerprint(df)

    X = df[SEG_FEATURES].values

    pipeline = Pipeline([
        ("scaler", RobustScaler()),
        ("cluster", MiniBatchKMeans(
            n_clusters=DEFAULT_K,
            random_state=RANDOM_STATE,
            batch_size=2048,
            n_init=10,
            max_iter=200,
        )),
    ])

    with timed_block("Segmentation training"):
        labels = pipeline.fit_predict(X)

    X_scaled = pipeline.named_steps["scaler"].transform(X)
    metrics = evaluate_clusters(X_scaled, labels)

    df["segment"] = labels

    profile = (
        df.groupby("segment")[SEG_FEATURES]
        .mean()
        .round(2)
        .assign(count=df["segment"].value_counts().sort_index())
    )

    # --------------------------------------------------
    # VERSIONING
    # --------------------------------------------------
    version = next_version()
    model_path = MODEL_REGISTRY / f"{MODEL_NAME}_v{version}.joblib"
    meta_path = MODEL_REGISTRY / f"{MODEL_NAME}_v{version}.json"

    artifact = {
        "pipeline": pipeline,
        "features": SEG_FEATURES,
        "n_clusters": DEFAULT_K,
    }

    joblib.dump(artifact, model_path)

    with open(meta_path, "w") as f:
        json.dump(
            {
                "model": MODEL_NAME,
                "version": version,
                "dataset_fingerprint": fingerprint,
                "metrics": metrics,
                "profile": profile.to_dict(),
            },
            f,
            indent=2,
        )

    print("[OK] Segmentation model saved:", model_path)
    print("[METRICS]", metrics)

    # --------------------------------------------------
    # 🏆 CHAMPION LOGIC
    # --------------------------------------------------
    current = load_champion(MODEL_REGISTRY)

    if current is None or better_segmentation(metrics, current["metrics"]):
        promote_champion(
            model_dir=MODEL_REGISTRY,
            model_name=MODEL_NAME,
            version=version,
            metrics=metrics,
            reason="Auto-promotion: better silhouette score",
        )

        save_baseline_stats(
            df[SEG_FEATURES],
            MODEL_REGISTRY / "baseline_stats.json",
        )

        print("[CHAMPION] New segmentation champion promoted")

    else:
        print("[CHALLENGER] Segmentation model not promoted")

    print("\n[PROFILE]\n", profile)


if __name__ == "__main__":
    main()
