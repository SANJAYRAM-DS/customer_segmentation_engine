# backend/models/clv/predict.py

from pathlib import Path
import joblib
import pandas as pd
import numpy as np

from backend.data.feature_registry.loader import load_feature_registry


BASE_DIR = Path(__file__).resolve().parents[3]
MODEL_DIR = BASE_DIR / "backend" / "models" / "model_registry" / "clv"


def load_latest_model():
    models = sorted(MODEL_DIR.glob("clv_two_stage_v*.joblib"))
    if not models:
        raise FileNotFoundError("No CLV model found")

    return joblib.load(models[-1])


def predict(df: pd.DataFrame) -> pd.DataFrame:
    registry = load_feature_registry("clv", "v1")
    expected = list(registry["features"].keys())

    df = df[expected]

    artifact = load_latest_model()
    purchase_model = artifact["purchase_model"]
    spend_model = artifact["spend_model"]
    smearing = artifact["smearing"]

    X = df.drop(columns=["future_90d_spend", "customer_id"], errors="ignore")

    p_buy = purchase_model.predict_proba(X)[:, 1]
    pred_log = spend_model.predict(X)
    pred_spend = np.expm1(pred_log) * smearing

    clv = p_buy * pred_spend

    return pd.DataFrame({
        "customer_id": df["customer_id"],
        "clv_90d": clv,
        "purchase_probability": p_buy,
    })
