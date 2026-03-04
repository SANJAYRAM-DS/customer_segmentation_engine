from fastapi import APIRouter
from backend.caching.loader import loader
import pandas as pd
import os

router = APIRouter()

CHURN_THRESHOLD = float(os.getenv("DEFAULT_CHURN_THRESHOLD", "0.7"))

@router.get("/")
def get_health_metrics(
    segment_name: str | None = None,
    health_band: str | None = None,
    investment_priority: str | None = None
):
    df = loader.get_customer_snapshot()

    if not df.empty:
        df = loader.sanitize_df(df)
        
    if segment_name:
        df = df[df["segment_name"] == segment_name]
    if health_band:
        df = df[df["health_band"] == health_band]
    if investment_priority:
        df = df[df["investment_priority"] == investment_priority]

    # 1. Health Score Overview
    health_dist = df["health_band"].value_counts().reset_index().rename(columns={"health_band": "category", "count": "count"}).to_dict(orient="records")

    # 2. Investment Matrix (Quadrants)
    # 2. Investment Matrix (Quadrants)
    # Aggregate counts, avg CLV, avg Risk
    if not df.empty and "investment_priority" in df:
        matrix = df.groupby("investment_priority").agg({
            "customer_id": "count",
            "clv_12m": "mean",
            "churn_probability": "mean"
        }).reset_index().rename(columns={
            "customer_id": "count",
            "clv_12m": "avg_clv",
            "churn_probability": "avg_churn_prob"
        }).to_dict(orient="records")
    else:
        matrix = []

    # 3. Actionable List (Top opportunities)
    # Prioritize 'Grow' and 'Save'
    actionable = df[df["investment_priority"].isin(["grow", "save"])].head(100)
    
    action_list = actionable[[
        "customer_id", "health_score", "health_band", "churn_probability", "clv_12m", "investment_priority"
    ]].to_dict(orient="records")

    return {
        "health_distribution": health_dist,
        "investment_matrix": matrix,
        "actionable_customers": action_list
    }


@router.get("/actionable")
def get_actionable_customers(limit: int = 100):
    """
    Returns the top actionable customers filtered by 'grow' or 'save' investment priority.
    These are the highest-opportunity customers for retention/growth actions.
    """
    df = loader.get_customer_snapshot()
    if df.empty:
        return {"actionable_customers": [], "total": 0}

    df = loader.sanitize_df(df)

    actionable = df[df["investment_priority"].isin(["grow", "save"])].copy()
    # Sort: highest CLV and highest churn risk first
    actionable = actionable.sort_values(
        ["clv_12m", "churn_probability"], ascending=[False, False]
    ).head(limit)

    cols = [
        "customer_id", "segment_name", "health_score", "health_band",
        "churn_probability", "clv_12m", "investment_priority",
        "recency_days", "total_orders", "total_spend"
    ]
    # Only include columns that exist in the dataframe
    cols = [c for c in cols if c in actionable.columns]

    return {
        "actionable_customers": actionable[cols].to_dict(orient="records"),
        "total": len(actionable)
    }
