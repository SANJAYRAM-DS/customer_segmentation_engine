# backend/snapshot/rules.py
import pandas as pd

def apply_business_flags(df: pd.DataFrame) -> pd.DataFrame:
    df["high_churn_risk_flag"] = df["churn_probability"] >= 0.7
    df["high_value_flag"] = df["clv_12m"] >= df["clv_12m"].quantile(0.8)

    df["at_risk_high_value_flag"] = (
        df["high_churn_risk_flag"] & df["high_value_flag"]
    )

    df["new_customer_flag"] = df["tenure_days"] <= 30
    df["loyal_customer_flag"] = (
        (df["tenure_days"] >= 365) & (df["health_band"] == "high")
    )

    return df
