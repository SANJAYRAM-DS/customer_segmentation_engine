from pathlib import Path
import joblib
import pandas as pd

from backend.data.feature_registry.loader import load_feature_registry


BASE_DIR = Path(__file__).resolve().parents[2]
MODEL_DIR = BASE_DIR / "backend" / "models" / "model_registry" / "churn"


def load_latest_model():
    models = sorted(MODEL_DIR.glob("churn_logistic_v*.joblib"))
    if not models:
        raise FileNotFoundError("No churn model found")

    return joblib.load(models[-1])


def predict(df: pd.DataFrame) -> pd.DataFrame:
    registry = load_feature_registry("churn", "v1")
    expected = list(registry["features"].keys())

    df = df[expected]

    model = load_latest_model()
    prob = model.predict_proba(df.drop(columns=["churn_90d", "customer_id"]))[:, 1]

    return pd.DataFrame({
        "customer_id": df["customer_id"],
        "churn_probability": prob
    })