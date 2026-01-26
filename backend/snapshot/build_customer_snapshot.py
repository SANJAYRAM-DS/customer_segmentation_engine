from pathlib import Path
from datetime import datetime, timezone
import pandas as pd

from backend.snapshot.health import compute_health_score
from backend.snapshot.investment import assign_investment_priority
from backend.snapshot.rules import apply_business_flags
from backend.snapshot.trends import compute_trends
from backend.snapshot.schema import validate_snapshot_schema
from backend.snapshot.segment_mapping import map_segment_metadata


BASE_DIR = Path(__file__).resolve().parents[2]
SNAPSHOT_DIR = BASE_DIR / "backend/data/snapshots/customer_snapshot"


def build_customer_snapshot(
    *,
    features: pd.DataFrame,
    churn_preds: pd.DataFrame,
    clv_preds: pd.DataFrame,
    segmentation_preds: pd.DataFrame,
    prev_snapshot: pd.DataFrame | None,
    metadata: dict,
):
    """
    Build and persist a single customer snapshot.
    """

    step_logs: list[dict] = []

    def log(step: str, **data):
        entry = {
            "step": step,
            "ts": datetime.now(timezone.utc).isoformat(),
            **data,
        }
        step_logs.append(entry)
        print(f"[SNAPSHOT] {step} | {data}")

    snapshot_date = metadata["snapshot_date"]
    log("start", snapshot_date=snapshot_date)

    # -------------------------------------------------
    # Merge inputs
    # -------------------------------------------------
    df = (
        features
        .merge(churn_preds, on="customer_id", how="left")
        .merge(clv_preds, on="customer_id", how="left")
        .merge(segmentation_preds, on="customer_id", how="left")
    )

    log("merge_complete", rows=len(df))
    df["snapshot_date"] = snapshot_date

    # -------------------------------------------------
    # ML outputs (normalized contract)
    # -------------------------------------------------
    df["churn_probability"] = df["churn_score"]
    df["clv_12m"] = df["clv_90d"] * 4  # explicit business assumption

    (
        df["segment_id"],
        df["segment_name"],
        df["segment_confidence"],
    ) = map_segment_metadata(df["segment"])

    log("ml_outputs_attached")

    # -------------------------------------------------
    # Behavioral semantics (lock snapshot schema)
    # -------------------------------------------------
    df["total_orders"] = df["order_count"]
    df["total_spend"] = df["total_spend"]
    df["avg_order_value"] = df["avg_order_value"]

    df["spend_30d"] = df["spend_30d"]
    df["spend_90d"] = df["spend_90d"]

    df["order_frequency_30d"] = df["orders_30d"]
    df["order_frequency_90d"] = df["orders_90d"]

    df["session_frequency_30d"] = df["sessions_30d"]
    df["session_frequency_90d"] = df["sessions_90d"]
    
    # Calculate return rate
    df["return_count"] = df["return_count"].fillna(0)
    df["return_rate"] = df["return_count"] / df["total_orders"].replace(0, 1)

    log("behavioral_fields_locked")

    # -------------------------------------------------
    # Engagement
    # -------------------------------------------------
    df["is_active_30d"] = df["recency_days"] <= 30
    df["is_active_90d"] = df["recency_days"] <= 90
    df["days_since_last_order"] = df["recency_days"]
    df["days_since_last_session"] = df["recency_days"]

    log("engagement_features")

    # -------------------------------------------------
    # Health & business logic
    # -------------------------------------------------
    df = compute_health_score(df)
    log("health_score")

    df = assign_investment_priority(df)
    log("investment_priority")

    df = apply_business_flags(df)
    log("business_flags")

    # -------------------------------------------------
    # Trends (row-to-row only)
    # -------------------------------------------------
    prev_used = False
    if prev_snapshot is not None and not prev_snapshot.empty:
        df = compute_trends(df, prev_snapshot)
        prev_used = True
        log("trends_computed")
    else:
        log("trends_skipped", reason="no_previous_snapshot")
        df["churn_probability_delta_7d"] = 0.0
        df["churn_probability_delta_30d"] = 0.0
        df["clv_delta_30d"] = 0.0
        df["health_score_delta_30d"] = 0.0

    # -------------------------------------------------
    # Metadata
    # -------------------------------------------------
    df["feature_version"] = metadata["feature_version"]
    df["model_version"] = metadata["model_version"]
    df["pipeline_run_id"] = metadata["pipeline_run_id"]

    df["data_completeness_score"] = 1 - df.isna().mean(axis=1)

    log("metadata_attached")

    # -------------------------------------------------
    # Schema validation (hard gate)
    # -------------------------------------------------
    validate_snapshot_schema(df)
    log("schema_validated")

    # -------------------------------------------------
    # Persist snapshot
    # -------------------------------------------------
    out_dir = SNAPSHOT_DIR / f"snapshot_date={snapshot_date}"
    out_dir.mkdir(parents=True, exist_ok=True)

    out_path = out_dir / "customer_snapshot.parquet"
    df.to_parquet(out_path, index=False)

    log("snapshot_saved", path=str(out_path))

    # -------------------------------------------------
    # Final logs
    # -------------------------------------------------
    summary_logs = {
        "rows": len(df),
        "snapshot_date": snapshot_date,
        "prev_snapshot_used": prev_used,
        "feature_version": metadata["feature_version"],
        "model_version": metadata["model_version"],
        "pipeline_run_id": metadata["pipeline_run_id"],
        "output_path": str(out_path),
    }

    return df, {
        "summary": summary_logs,
        "steps": step_logs,
    }
