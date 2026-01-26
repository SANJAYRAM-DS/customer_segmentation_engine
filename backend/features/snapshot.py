import pandas as pd


def get_snapshot_date(
    orders: pd.DataFrame,
    quantile: float = 0.8,
    min_history_days: int = 30,
) -> pd.Timestamp:
    """
    Compute a leakage-safe snapshot date from historical orders.

    Rules:
    - Snapshot is derived ONLY from order history
    - Uses quantile to avoid extreme tail effects
    - Ensures enough historical depth for features
    - Returns tz-naive Timestamp (compatible with pandas ops)

    Parameters
    ----------
    orders : pd.DataFrame
        Orders dataframe with column `order_date`
    quantile : float, default=0.8
        Quantile used to define snapshot date
    min_history_days : int, default=30
        Minimum required history before snapshot

    Returns
    -------
    pd.Timestamp
        Snapshot date
    """

    if "order_date" not in orders.columns:
        raise ValueError("orders dataframe must contain `order_date`")

    if orders.empty:
        raise ValueError("orders dataframe is empty")

    # Ensure datetime
    order_dates = pd.to_datetime(orders["order_date"], errors="coerce")

    if order_dates.isna().all():
        raise ValueError("order_date column contains no valid timestamps")

    # Quantile-based snapshot (robust to outliers)
    snapshot = order_dates.quantile(quantile)

    if pd.isna(snapshot):
        raise ValueError("Snapshot date could not be computed")

    # Enforce minimum history window
    min_allowed_snapshot = order_dates.min() + pd.Timedelta(days=min_history_days)

    if snapshot < min_allowed_snapshot:
        snapshot = min_allowed_snapshot

    # Ensure tz-naive consistency
    if snapshot.tzinfo is not None:
        snapshot = snapshot.tz_localize(None)

    return snapshot
