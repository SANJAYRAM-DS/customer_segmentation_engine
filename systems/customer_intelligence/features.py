# systems/customer_intelligence/features.py

from pathlib import Path
import pandas as pd
import numpy as np
from typing import Dict

# ---------------------------
# CONFIG
# ---------------------------

CHURN_WINDOW_DAYS = 90
CLV_HORIZON_DAYS = 90

OUTPUT_DIR = Path("data/processed")

# ---------------------------
# SNAPSHOT
# ---------------------------

def get_snapshot_date(orders: pd.DataFrame, quantile: float = 0.8) -> pd.Timestamp:
    return orders["order_date"].quantile(quantile)


# ---------------------------
# BASE AGGREGATIONS
# ---------------------------

def aggregate_orders(orders: pd.DataFrame, snapshot: pd.Timestamp) -> pd.DataFrame:
    orders = orders[orders["order_date"] <= snapshot]

    agg = orders.groupby("customer_id").agg(
        total_spend=("order_value", "sum"),
        avg_order_value=("order_value", "mean"),
        order_count=("order_id", "count"),
        first_order_date=("order_date", "min"),
        last_order_date=("order_date", "max"),
        discount_rate=("discount_used", "mean"),
    )

    return agg.reset_index()


def aggregate_sessions(sessions: pd.DataFrame, snapshot: pd.Timestamp) -> pd.DataFrame:
    sessions = sessions[sessions["session_date"] <= snapshot]

    agg = sessions.groupby("customer_id").agg(
        session_count=("session_id", "count"),
        avg_pages=("pages_viewed", "mean"),
        avg_session_duration=("session_duration", "mean"),
        last_session_date=("session_date", "max"),
    )

    return agg.reset_index()


def aggregate_returns(returns: pd.DataFrame, snapshot: pd.Timestamp) -> pd.DataFrame:
    returns = returns[returns["return_date"] <= snapshot]

    agg = returns.groupby("customer_id").agg(
        return_count=("return_id", "count"),
        total_refund=("refund_amount", "sum"),
    )

    return agg.reset_index()


# ---------------------------
# TEMPORAL FEATURES
# ---------------------------

def add_temporal_features(df: pd.DataFrame, snapshot: pd.Timestamp) -> pd.DataFrame:
    df["tenure_days"] = (snapshot - df["signup_date"]).dt.days.clip(lower=0)
    df["recency_days"] = (snapshot - df["last_order_date"]).dt.days

    df["order_frequency"] = df["order_count"] / df["tenure_days"].clip(lower=1)
    df["session_frequency"] = df["session_count"] / df["tenure_days"].clip(lower=1)
    df["return_rate"] = df["return_count"] / df["order_count"].clip(lower=1)

    return df


# ---------------------------
# ROLLING WINDOWS (NO LEAKAGE)
# ---------------------------

def rolling_order_features(orders: pd.DataFrame, snapshot: pd.Timestamp) -> pd.DataFrame:
    windows = [7, 30, 90]
    out = []

    for w in windows:
        o = orders[
            (orders["order_date"] <= snapshot) &
            (orders["order_date"] > snapshot - pd.Timedelta(days=w))
        ]

        agg = o.groupby("customer_id").agg(
            **{
                f"spend_{w}d": ("order_value", "sum"),
                f"orders_{w}d": ("order_id", "count"),
            }
        ).reset_index()

        out.append(agg)

    df = out[0]
    for a in out[1:]:
        df = df.merge(a, on="customer_id", how="outer")

    return df


def rolling_session_features(sessions: pd.DataFrame, snapshot: pd.Timestamp) -> pd.DataFrame:
    windows = [7, 30]
    out = []

    for w in windows:
        s = sessions[
            (sessions["session_date"] <= snapshot) &
            (sessions["session_date"] > snapshot - pd.Timedelta(days=w))
        ]

        agg = s.groupby("customer_id").agg(
            **{
                f"sessions_{w}d": ("session_id", "count"),
                f"pages_{w}d": ("pages_viewed", "mean"),
            }
        ).reset_index()

        out.append(agg)

    df = out[0]
    for a in out[1:]:
        df = df.merge(a, on="customer_id", how="outer")

    return df


# ---------------------------
# TARGETS
# ---------------------------

def build_churn_target(orders: pd.DataFrame, snapshot: pd.Timestamp) -> pd.Series:
    future = orders[
        (orders["order_date"] > snapshot) &
        (orders["order_date"] <= snapshot + pd.Timedelta(days=CHURN_WINDOW_DAYS))
    ]

    active = future["customer_id"].unique()
    return lambda df: ~df["customer_id"].isin(active)


def build_clv_target(orders: pd.DataFrame, snapshot: pd.Timestamp) -> pd.DataFrame:
    future = orders[
        (orders["order_date"] > snapshot) &
        (orders["order_date"] <= snapshot + pd.Timedelta(days=CLV_HORIZON_DAYS))
    ]

    return (
        future.groupby("customer_id")["order_value"]
        .sum()
        .rename("future_90d_spend")
        .reset_index()
    )


# ---------------------------
# MAIN PIPELINE
# ---------------------------

def build_feature_datasets(data: Dict[str, pd.DataFrame]) -> None:
    customers = data["customers"]
    orders = data["orders"]
    sessions = data["sessions"]
    returns = data["returns"]

    snapshot = get_snapshot_date(orders)

    base = customers.copy()

    base = base.merge(aggregate_orders(orders, snapshot), on="customer_id", how="left")
    base = base.merge(aggregate_sessions(sessions, snapshot), on="customer_id", how="left")
    base = base.merge(aggregate_returns(returns, snapshot), on="customer_id", how="left")

    base = add_temporal_features(base, snapshot)

    base = base.merge(rolling_order_features(orders, snapshot), on="customer_id", how="left")
    base = base.merge(rolling_session_features(sessions, snapshot), on="customer_id", how="left")

    # Fill numeric NA only
    num_cols = base.select_dtypes(include="number").columns
    base[num_cols] = base[num_cols].fillna(0)

    # -----------------------
    # CHURN
    # -----------------------
    churn_df = base.copy()
    churn_fn = build_churn_target(orders, snapshot)
    churn_df["is_churned"] = churn_fn(churn_df)

    churn_dir = OUTPUT_DIR / "churn"
    churn_dir.mkdir(parents=True, exist_ok=True)
    churn_df.to_parquet(churn_dir / "features.parquet", index=False)

    # -----------------------
    # CLV
    # -----------------------
    clv_target = build_clv_target(orders, snapshot)

    clv_df = base.merge(clv_target, on="customer_id", how="left")
    clv_df["future_90d_spend"] = clv_df["future_90d_spend"].fillna(0)

    clv_dir = OUTPUT_DIR / "clv"
    clv_dir.mkdir(parents=True, exist_ok=True)
    clv_df.to_parquet(clv_dir / "features.parquet", index=False)

    # -----------------------
    # SEGMENTATION
    # -----------------------
    seg_dir = OUTPUT_DIR / "segmentation"
    seg_dir.mkdir(parents=True, exist_ok=True)
    base.to_parquet(seg_dir / "features.parquet", index=False)
