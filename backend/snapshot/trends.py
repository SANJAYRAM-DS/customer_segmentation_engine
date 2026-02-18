# backend/snapshot/trends.py
import pandas as pd

def compute_trends(current: pd.DataFrame, previous: pd.DataFrame) -> pd.DataFrame:
    prev = previous.set_index("customer_id")
    cur = current.set_index("customer_id")

    for col, delta_col in [
        ("churn_probability", "churn_probability_delta_30d"),
        ("clv_12m", "clv_delta_30d"),
        ("health_score", "health_score_delta_30d"),
    ]:
        cur[delta_col] = cur[col] - prev[col]
    
    # Placeholder for 7d delta (requires 7d snapshot history)
    cur["churn_probability_delta_7d"] = 0.0

    return cur.reset_index()