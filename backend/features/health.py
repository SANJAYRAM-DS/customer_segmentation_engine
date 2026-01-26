
import pandas as pd
import numpy as np

def calculate_health_score(df: pd.DataFrame) -> pd.Series:
    """
    Calculate customer health score (0-100) based on:
    - Recency (days since last order): Lower is better
    - Frequency (orders in 90d): Higher is better
    - Monetary (spend in 90d): Higher is better
    - Engagement (sessions in 90d): Higher is better
    - Churn Probability: Lower is better
    """
    
    # Normalize features to 0-1
    # We use rank pct to handle outliers and different scales
    
    # Recency: Lower is better -> 1 - rank
    if "days_since_last_order" in df.columns:
        recency_score = 1 - df["days_since_last_order"].rank(pct=True)
    else:
        recency_score = 0.5

    # Frequency: Higher is better
    if "orders_90d" in df.columns:
        freq_score = df["orders_90d"].rank(pct=True)
    else:
        freq_score = 0.5
        
    # Monetary: Higher is better
    if "spend_90d" in df.columns:
        monetary_score = df["spend_90d"].rank(pct=True)
    else:
        monetary_score = 0.5
        
    # Engagement: Higher is better
    if "sessions_90d" in df.columns:
        engagement_score = df["sessions_90d"].rank(pct=True)
    else:
        engagement_score = 0.5
        
    # Churn Risk: Lower is better -> 1 - existing prob
    if "churn_probability" in df.columns:
        risk_score = 1 - df["churn_probability"]
    else:
        risk_score = 0.5

    # Weighted Average
    # Weights: Risk (30%), Recency (20%), Frequency (20%), Monetary (20%), Engagement (10%)
    health = (
        risk_score * 0.30 +
        recency_score * 0.20 +
        freq_score * 0.20 +
        monetary_score * 0.20 +
        engagement_score * 0.10
    )
    
    # Scale to 0-100 and int
    return (health * 100).fillna(50).astype(int)

def assign_health_band(df: pd.DataFrame) -> pd.Series:
    if "health_score" not in df.columns:
        return pd.Series(["Unknown"] * len(df))
    
    conditions = [
        (df["health_score"] >= 80),
        (df["health_score"] >= 60),
        (df["health_score"] >= 40),
        (df["health_score"] < 40)
    ]
    choices = ["Excellent", "Good", "Watch", "Critical"]
    
    return np.select(conditions, choices, default="Unknown")
