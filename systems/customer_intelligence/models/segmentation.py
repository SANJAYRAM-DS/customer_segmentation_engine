from pathlib import Path
import json
import hashlib
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

# ============================
# CONFIG
# ============================

RANDOM_STATE = 42
MODEL_NAME = "customer_segmentation"
DATA_PATH = Path("../../../data/processed/system1/segmentation/features.parquet")
MODEL_REGISTRY = Path("../../../deployment/model_registry/system1/segmentation")

MODEL_REGISTRY.mkdir(parents = True, exist_ok = True)

SEG_FEATURES = [
    "recency_days",
    "order_count",
    "total_spend",
    "session_frequency",
    "return_rate",
]

DEFAULT_K = 4  # chosen offline, justified & versioned

# ============================
# UTILS
# ============================

def dataset_fingerprint(df: pd.DataFrame) -> str:
    h = hashlib.md5(pd.util.hash_pandas_object(df, index=True).values)
    return h.hexdigest()


def validate_features(df: pd.DataFrame):
    missing = set(SEG_FEATURES) - set(df.columns)
    if missing:
        raise ValueError(f"Missing segmentation features: {missing}")


# ============================
# DATA LOADING
# ============================

def load_dataset(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Missing dataset: {path}")

    df = pd.read_parquet(path)
    validate_features(df)

    # Drop rows where all seg features are zero → cold start
    mask = (df[SEG_FEATURES].sum(axis=1) > 0)
    return df[mask].reset_index(drop=True)


# ============================
# MODEL BUILD
# ============================

def build_pipeline(n_clusters: int) -> Pipeline:
    return Pipeline([
        ("scaler", RobustScaler()),
        ("cluster", MiniBatchKMeans(
            n_clusters=n_clusters,
            random_state=RANDOM_STATE,
            batch_size=2048,
            n_init=10,
            max_iter=200,
        )),
    ])


# ============================
# EVALUATION
# ============================

def evaluate_clusters(X_scaled, labels):
    return {
        "silhouette": silhouette_score(X_scaled, labels),
        "davies_bouldin": davies_bouldin_score(X_scaled, labels),
        "calinski_harabasz": calinski_harabasz_score(X_scaled, labels),
    }


# ============================
# VERSIONING
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

    X = df[SEG_FEATURES].values

    pipeline = build_pipeline(DEFAULT_K)
    labels = pipeline.fit_predict(X)

    # Metrics
    X_scaled = pipeline.named_steps["scaler"].transform(X)
    metrics = evaluate_clusters(X_scaled, labels)

    # Cluster profiling
    df["segment"] = labels
    centroids = pipeline.named_steps["cluster"].cluster_centers_
    centroids = pipeline.named_steps["scaler"].inverse_transform(centroids)

    profile = (
        df.groupby("segment")[SEG_FEATURES]
        .mean()
        .round(2)
        .assign(count=df["segment"].value_counts().sort_index())
    )

    # ============================
    # SAVE ARTIFACT
    # ============================

    version = next_version(MODEL_REGISTRY)

    model_path = MODEL_REGISTRY / f"{MODEL_NAME}_v{version}.joblib"
    meta_path = MODEL_REGISTRY / f"{MODEL_NAME}_v{version}.json"

    artifact = {
        "pipeline": pipeline,
        "features": SEG_FEATURES,
    }

    joblib.dump(artifact, model_path)

    metadata = {
        "model": MODEL_NAME,
        "version": version,
        "dataset_fingerprint": fingerprint,
        "n_clusters": DEFAULT_K,
        "metrics": metrics,
        "cluster_centroids": centroids.tolist(),
        "profile": profile.to_dict(),
    }

    with open(meta_path, "w") as f:
        json.dump(metadata, f, indent=2)

    print("Saved segmentation model:", model_path)
    print("Metrics:", metrics)
    print("\nCluster profile:")
    print(profile)


if __name__ == "__main__":
    main()
