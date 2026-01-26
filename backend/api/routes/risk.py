from fastapi import APIRouter
from backend.caching.loader import loader
import pandas as pd

router = APIRouter()

@router.get("/")
def get_risk_metrics():
    df = loader.get_customer_snapshot()
    
    if df.empty:
        return {} # Should match schema? Schema is Dict currently for risk.py (implicit)
    
    df = loader.sanitize_df(df)

    # 1. Churn Prob Distribution
    # Histogram buckets
    cuts = pd.cut(df["churn_probability"], bins=[0, 0.2, 0.5, 0.8, 1.0], labels=["Low", "Medium", "High", "Critical"])
    dist = cuts.value_counts().reset_index()
    dist.columns = ["bucket", "count"]
    
    # 2. High Value At Risk
    # Top 50 by CLV who are High Risk
    risky = df[df["churn_probability"] > 0.7].sort_values("clv_12m", ascending=False).head(50)
    
    high_value_at_risk = risky[[
        "customer_id", "segment_name", "clv_12m", "churn_probability", "health_score"
    ]].to_dict(orient="records")

    return {
        "distribution": dist.to_dict(orient="records"),
        "high_value_at_risk": high_value_at_risk
    }
