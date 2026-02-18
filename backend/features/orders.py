import pandas as pd


def aggregate_orders(orders: pd.DataFrame, snapshot: pd.Timestamp) -> pd.DataFrame:
    o = orders[orders["order_date"] <= snapshot]

    return (
        o.groupby("customer_id")
        .agg(
            total_spend=("order_value", "sum"),
            avg_order_value=("order_value", "mean"),
            order_count=("order_id", "count"),
            first_order_date=("order_date", "min"),
            last_order_ts=("order_date", "max"),
            discount_rate=("discount_used", "mean"),
        )
        .reset_index()
    )


def rolling_order_features(
    orders: pd.DataFrame, snapshot: pd.Timestamp
) -> pd.DataFrame:
    windows = [7, 30, 90]
    out = []

    for w in windows:
        o = orders[
            (orders["order_date"] <= snapshot)
            & (orders["order_date"] > snapshot - pd.Timedelta(days=w))
        ]

        agg = (
            o.groupby("customer_id")
            .agg(
                spend_sum=("order_value", "sum"),
                order_cnt=("order_id", "count"),
            )
            .rename(
                columns={
                    "spend_sum": f"spend_{w}d",
                    "order_cnt": f"orders_{w}d",
                }
            )
            .reset_index()
        )

        out.append(agg)

    df = out[0]
    for a in out[1:]:
        df = df.merge(a, on="customer_id", how="outer")

    return df