# backend/orchestration/batch_inference.py

from pathlib import Path
import json
import numpy as np
import pandas as pd
import joblib

from backend.orchestration.batch_inference_utils import save_predictions
from backend.models.champion_manager import load_champion


# ------------------------------------------------------------------
# PATHS
# ------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parents[2]

FEATURE_DIR = BASE_DIR / "backend/data/processed"
MODEL_REGISTRY = BASE_DIR / "backend/models/model_registry"


# ------------------------------------------------------------------
# UTILS
# ------------------------------------------------------------------
def load_model(model_dir: Path, model_name: str):
    champ = load_champion(model_dir)
    if champ:
        return joblib.load(
            model_dir / f"{model_name}_v{champ['version']}.joblib"
        ), champ["version"]

    # fallback (first run)
    path = max(model_dir.glob(f"{model_name}_v*.joblib"))
    version = int(path.stem.split("_v")[-1])
    return joblib.load(path), version


def get_model_version(model_dir: Path, model_name: str) -> int:
    champ = load_champion(model_dir)
    if champ:
        return champ["version"]

    # fallback (first run)
    files = list(model_dir.glob(f"{model_name}_v*.joblib"))
    if not files:
        # If no model exists, maybe return 0 or raise error?
        # For now, let's assume existence if we are here.
        return 0
    path = max(files)
    return int(path.stem.split("_v")[-1])


# ------------------------------------------------------------------
# CHURN
# ------------------------------------------------------------------
def churn_inference(return_df: bool = False):
    model_dir = MODEL_REGISTRY / "churn"
    artifact, version = load_model(model_dir, "churn_logistic")
    
    model = artifact if not isinstance(artifact, dict) else artifact.get("model", artifact)

    features = pd.read_parquet(FEATURE_DIR / "churn" / "features.parquet")

    X = features.drop(columns=["customer_id", "churn_90d"])
    preds = model.predict_proba(X)[:, 1]

    out = pd.DataFrame({
        "customer_id": features["customer_id"],
        "churn_score": preds,
    })

    save_predictions(
        model_name="churn",
        model_version=version,
        predictions=out,
        project_root=BASE_DIR,
    )

    if return_df:
        return len(out), out
    return len(out)


# ------------------------------------------------------------------
# CLV
# ------------------------------------------------------------------
def clv_inference(return_df: bool = False):
    model_dir = MODEL_REGISTRY / "clv"
    artifact, version = load_model(model_dir, "clv_two_stage")

    purchase_model = artifact["purchase_model"]
    spend_model = artifact["spend_model"]
    smearing = artifact["smearing"]

    features = pd.read_parquet(FEATURE_DIR / "clv" / "features.parquet")

    X = features.drop(columns=["customer_id", "future_90d_spend"])
    p_buy = purchase_model.predict_proba(X)[:, 1]

    pred_log = spend_model.predict(X)
    pred_spend = np.expm1(pred_log) * smearing

    final_pred = p_buy * pred_spend

    out = pd.DataFrame({
        "customer_id": features["customer_id"],
        "clv_90d": final_pred,
    })

    save_predictions(
        model_name="clv",
        model_version=version,
        predictions=out,
        project_root=BASE_DIR,
    )

    if return_df:
        return len(out), out
    return len(out)


# ------------------------------------------------------------------
# SEGMENTATION
# ------------------------------------------------------------------
def segmentation_inference(return_df: bool = False):
    model_dir = MODEL_REGISTRY / "segmentation"
    artifact, version = load_model(model_dir, "customer_segmentation")

    pipeline = artifact["pipeline"]
    seg_features = artifact["features"]

    features = pd.read_parquet(FEATURE_DIR / "segmentation" / "features.parquet")

    X = features[seg_features].values
    labels = pipeline.predict(X)

    out = pd.DataFrame({
        "customer_id": features["customer_id"],
        "segment": labels,
    })

    save_predictions(
        model_name="segmentation",
        model_version=version,
        predictions=out,
        project_root=BASE_DIR,
    )

    if return_df:
        return len(out), out
    return len(out)