import pandas as pd


def aggregate_returns(
    returns: pd.DataFrame, snapshot: pd.Timestamp
) -> pd.DataFrame:
    r = returns[returns["return_date"] <= snapshot]

    return (
        r.groupby("customer_id")
        .agg(
            return_count=("return_id", "count"),
            total_refund=("refund_amount", "sum"),
        )
        .reset_index()
    )
