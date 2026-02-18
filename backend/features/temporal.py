import pandas as pd


def add_temporal_features(df: pd.DataFrame, snapshot: pd.Timestamp) -> pd.DataFrame:
    df = df.copy()

    df["tenure_days"] = (snapshot - df["signup_date"]).dt.days.clip(lower=0)
    df["recency_days"] = (snapshot - df["last_order_ts"]).dt.days.clip(lower=0)

    df["order_frequency"] = df["order_count"] / df["tenure_days"].clip(lower=1)
    df["session_frequency"] = df["session_count"] / df["tenure_days"].clip(lower=1)
    df["return_rate"] = df["return_count"] / df["order_count"].clip(lower=1)

    return df