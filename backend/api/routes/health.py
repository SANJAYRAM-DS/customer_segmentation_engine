from fastapi import APIRouter
from backend.caching.loader import loader
import pandas as pd

router = APIRouter()

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
        "customer_id", "health_score", "churn_probability", "clv_12m", "investment_priority"
    ]].to_dict(orient="records")

    return {
        "health_distribution": health_dist,
        "investment_matrix": matrix,
        "actionable_customers": action_list
    }
