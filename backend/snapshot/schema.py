# backend/snapshot/schema.py
from typing import List

REQUIRED_COLUMNS: List[str] = [
    "customer_id",
    "snapshot_date",

    # ML outputs
    "churn_probability",
    "clv_12m",
    "segment_id",
    "segment_name",
    "segment_confidence",

    # Behavior
    "recency_days",
    "order_frequency_30d",
    "order_frequency_90d",
    "session_frequency_30d",
    "session_frequency_90d",
    "total_orders",
    "total_spend",
    "spend_30d",
    "spend_90d",
    "avg_order_value",
    "return_rate",

    # Engagement
    "is_active_30d",
    "is_active_90d",
    "days_since_last_session",
    "days_since_last_order",

    # Health & business
    "health_score",
    "health_band",
    "investment_priority",

    # Flags
    "high_churn_risk_flag",
    "high_value_flag",
    "at_risk_high_value_flag",
    "new_customer_flag",
    "loyal_customer_flag",

    # Trends
    "churn_probability_delta_7d",
    "churn_probability_delta_30d",
    "clv_delta_30d",
    "health_score_delta_30d",

    # Metadata
    "data_completeness_score",
    "feature_version",
    "model_version",
    "pipeline_run_id",
]


def validate_snapshot_schema(df):
    missing = set(REQUIRED_COLUMNS) - set(df.columns)
    if missing:
        raise ValueError(f"Snapshot schema missing columns: {missing}")
