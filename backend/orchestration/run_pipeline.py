from pathlib import Path
import json
from datetime import datetime, timezone
import pandas as pd

from backend.data_ingestion import load_and_validate
from backend.features.build_customer_features import build_customer_features
from backend.models.build_models import main as train_models
from backend.models.champion_manager import load_champion

from backend.orchestration.retraining_policy import (
    fingerprint_directory,
    should_rebuild_features,
    should_retrain_models,
)

from backend.orchestration.batch_inference import (
    churn_inference,
    clv_inference,
    segmentation_inference,
    get_model_version,
)

from backend.orchestration.drift_check import detect_drift
from backend.orchestration.drift_history import save_drift_report

from backend.snapshot.build_customer_snapshot import (
    build_customer_snapshot,
    SNAPSHOT_DIR,
)
from backend.snapshot.utils import load_previous_snapshot

from backend.outputs.build_outputs import build_outputs


# -------------------------------------------------------------------
# PATHS
# -------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parents[2]

RAW_DIR = BASE_DIR / "backend/data/raw"
STATE_FILE = BASE_DIR / "backend/orchestration/state_store.json"

FEATURE_DIR = BASE_DIR / "backend/data/processed"
MODEL_REGISTRY = BASE_DIR / "backend/models/model_registry"


# -------------------------------------------------------------------
# STATE
# -------------------------------------------------------------------
def load_state():
    if not STATE_FILE.exists():
        return {}
    try:
        content = STATE_FILE.read_text().strip()
        return json.loads(content) if content else {}
    except json.JSONDecodeError:
        print("[WARN] Corrupted state file. Resetting.")
        return {}


def save_state(state: dict):
    STATE_FILE.write_text(json.dumps(state, indent=2))


# -------------------------------------------------------------------
# DRIFT
# -------------------------------------------------------------------
def run_drift_check(model_name: str, numeric_cols, categorical_cols):
    features_path = FEATURE_DIR / model_name / "features.parquet"
    baseline_path = MODEL_REGISTRY / model_name / "baseline_stats.json"

    if not features_path.exists() or not baseline_path.exists():
        print(f"[SKIP] Drift check skipped for {model_name}")
        return {"severe": False}

    df = pd.read_parquet(features_path)

    drift = detect_drift(
        df=df,
        baseline_path=baseline_path,
        numeric_cols=numeric_cols,
        categorical_cols=categorical_cols,
    )

    save_drift_report(model_name, drift, BASE_DIR)
    print(f"[DRIFT] {model_name}: {'SEVERE' if drift['severe'] else 'OK'}")

    return drift


# -------------------------------------------------------------------
# MAIN PIPELINE
# -------------------------------------------------------------------
def main():
    print("=" * 60)
    print("[PIPELINE] START", datetime.now(timezone.utc).isoformat())
    print("=" * 60)

    state = load_state()
    run_id = datetime.now(timezone.utc).isoformat()

    # ===============================================================
    # 1️⃣ DATA → FEATURES
    # ===============================================================
    raw_fp = fingerprint_directory(RAW_DIR)

    rebuild_features = should_rebuild_features(
        state.get("raw_data_fingerprint"),
        raw_fp,
    )

    if rebuild_features:
        print("[STEP] Data ingestion + feature build")
        data = load_and_validate(RAW_DIR)
        feat_out = build_customer_features(data)
        feature_fp = feat_out["snapshot"].isoformat().replace(":", "-")
    else:
        print("[SKIP] Raw data unchanged")
        feature_fp = state.get("feature_fingerprint")

    snapshot_date = feature_fp

    # ===============================================================
    # 2️⃣ DRIFT
    # ===============================================================
    print("[STEP] Drift detection")

    churn_drift = run_drift_check("churn",
        ["recency_days", "tenure_days", "order_frequency", "total_spend"],
        [],
    )

    clv_drift = run_drift_check("clv",
        ["recency_days", "tenure_days", "total_spend", "order_count"],
        [],
    )

    segmentation_drift = run_drift_check("segmentation",
        ["recency_days", "order_count", "total_spend", "session_frequency"],
        [],
    )

    drift_trigger = (
        churn_drift["severe"]
        or clv_drift["severe"]
        or segmentation_drift["severe"]
    )

    # ===============================================================
    # 3️⃣ MODEL TRAINING
    # ===============================================================
    retrain_models = should_retrain_models(
        state.get("feature_fingerprint"),
        feature_fp,
    ) or drift_trigger
    # retrain_models = False

    if retrain_models:
        print("[STEP] Model training")
        train_models()
    else:
        print("[SKIP] Models up-to-date")

    # ===============================================================
    # 4️⃣ BATCH INFERENCE
    # ===============================================================
    print("[STEP] Batch inference")

    _, churn_preds = churn_inference(return_df=True)
    _, clv_preds = clv_inference(return_df=True)
    _, seg_preds = segmentation_inference(return_df=True)

    # ===============================================================
    # 5️⃣ SNAPSHOT
    # ===============================================================
    print("[STEP] Customer snapshot")

    prev_snapshot = load_previous_snapshot(SNAPSHOT_DIR)
    features_df = pd.read_parquet(FEATURE_DIR / "segmentation" / "features.parquet")

    snapshot_df, snapshot_logs = build_customer_snapshot(
        features=features_df,
        churn_preds=churn_preds,
        clv_preds=clv_preds,
        segmentation_preds=seg_preds,
        prev_snapshot=prev_snapshot,
        metadata={
            "snapshot_date": snapshot_date,
            "feature_version": feature_fp,
            "model_version": {
                "churn": get_model_version(MODEL_REGISTRY / "churn", "churn_logistic"),
                "clv": get_model_version(MODEL_REGISTRY / "clv", "clv_two_stage"),
                "segmentation": get_model_version(MODEL_REGISTRY / "segmentation", "customer_segmentation"),
            },
            "pipeline_run_id": run_id,
        },
    )

    # ===============================================================
    # 6️⃣ OUTPUTS
    # ===============================================================
    print("[STEP] Outputs")

    outputs_logs = build_outputs(
        snapshot_date=snapshot_date,
        pipeline_run_id=run_id,
    )

    # ===============================================================
    # 7️⃣ STATE
    # ===============================================================
    save_state({
        "raw_data_fingerprint": raw_fp,
        "feature_fingerprint": feature_fp,
        "last_run": datetime.now(timezone.utc).isoformat(),
        "snapshot_date": snapshot_date,
        "outputs_built": True,
        "drift": {
            "churn": churn_drift["severe"],
            "clv": clv_drift["severe"],
            "segmentation": segmentation_drift["severe"],
        },
    })

    print("=" * 60)
    print("[PIPELINE] COMPLETED SUCCESSFULLY")
    print("=" * 60)


if __name__ == "__main__":
    main()