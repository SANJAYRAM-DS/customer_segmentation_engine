import pandas as pd

CHURN_WINDOW_DAYS = 90
CLV_HORIZON_DAYS = 90


def build_churn_target(orders: pd.DataFrame, snapshot: pd.Timestamp):
    future = orders[
        (orders["order_date"] > snapshot)
        & (orders["order_date"] <= snapshot + pd.Timedelta(days=CHURN_WINDOW_DAYS))
    ]

    active_customers = set(future["customer_id"].unique())
    return lambda df: ~df["customer_id"].isin(active_customers)


def build_clv_target(
    orders: pd.DataFrame, snapshot: pd.Timestamp
) -> pd.DataFrame:
    future = orders[
        (orders["order_date"] > snapshot)
        & (orders["order_date"] <= snapshot + pd.Timedelta(days=CLV_HORIZON_DAYS))
    ]

    return (
        future.groupby("customer_id")["order_value"]
        .sum()
        .rename("future_90d_spend")
        .reset_index()
    )
