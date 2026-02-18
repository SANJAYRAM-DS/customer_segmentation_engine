# backend/snapshot/health.py
import pandas as pd
import numpy as np

def compute_health_score(df: pd.DataFrame) -> pd.DataFrame:
    # Ensure inputs are valid
    churn_prob = df["churn_probability"].fillna(0.5)
    spend = df["total_spend"].fillna(0)
    orders_90d = df["orders_90d"].fillna(0)
    sessions_90d = df["sessions_90d"].fillna(0)
    
    # Components (0 to 1)
    
    # 1. Churn Risk Component (Lower risk -> High health) - 40% weight
    risk_comp = (1 - churn_prob)
    
    # 2. Spend Component (Relative to median) - 20% weight
    # Using rank to normalize without strict assumptions on distribution
    spend_comp = spend.rank(pct=True)
    
    # 3. Frequency Component - 20% weight
    freq_comp = orders_90d.rank(pct=True)
    
    # 4. Engagement Component - 20% weight
    eng_comp = sessions_90d.rank(pct=True)
    
    # Weighted Sum
    score = (
        risk_comp * 0.40 +
        spend_comp * 0.20 +
        freq_comp * 0.20 +
        eng_comp * 0.20
    )
    
    # Scale to 0-100
    df["health_score"] = (score * 100).fillna(50).astype(int)
    
    # Assign Bands
    # Critical: 0-39, Watch: 40-59, Good: 60-79, Excellent: 80-100
    conditions = [
        (df["health_score"] >= 80),
        (df["health_score"] >= 60),
        (df["health_score"] >= 40),
        (df["health_score"] < 40)
    ]
    choices = ["Excellent", "Good", "Watch", "Critical"]
    
    df["health_band"] = np.select(conditions, choices, default="Critical")
    
    return df