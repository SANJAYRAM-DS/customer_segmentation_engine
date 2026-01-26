# backend/models/segmentation/predict.py

from pathlib import Path
import pandas as pd
import joblib
import json

from backend.data.feature_registry.loader import load_feature_registry


BASE_DIR = Path(__file__).resolve().parents[3]
MODEL_REGISTRY = BASE_DIR / "backend/models/model_registry/segmentation"


def load_latest_model():
    models = sorted(MODEL_REGISTRY.glob("customer_segmentation_v*.joblib"))
    if not models:
        raise FileNotFoundError("No segmentation models found")

    return joblib.load(models[-1])


def predict(df: pd.DataFrame) -> pd.DataFrame:
    registry = load_feature_registry("segmentation", "v1")
    expected = list(registry["features"].keys())

    df = df[expected]

    artifact = load_latest_model()
    pipeline = artifact["pipeline"]
    features = artifact["features"]

    labels = pipeline.predict(df[features].values)

    out = df[[col for col in df.columns if col.endswith("id")]].copy()
    out["segment"] = labels

    return out


if __name__ == "__main__":
    # Example batch usage
    data_path = BASE_DIR / "backend/data/processed/segmentation/features.parquet"
    df = pd.read_parquet(data_path)

    preds = predict(df)
    print(preds.head())
