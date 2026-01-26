import pandas as pd


def aggregate_sessions(
    sessions: pd.DataFrame, snapshot: pd.Timestamp
) -> pd.DataFrame:
    s = sessions[sessions["session_date"] <= snapshot]

    return (
        s.groupby("customer_id")
        .agg(
            session_count=("session_id", "count"),
            avg_pages=("pages_viewed", "mean"),
            avg_session_duration=("session_duration", "mean"),
            last_session_date=("session_date", "max"),
        )
        .reset_index()
    )


def rolling_session_features(
    sessions: pd.DataFrame, snapshot: pd.Timestamp
) -> pd.DataFrame:
    windows = [7, 30, 90]
    out = []

    for w in windows:
        s = sessions[
            (sessions["session_date"] <= snapshot)
            & (sessions["session_date"] > snapshot - pd.Timedelta(days=w))
        ]

        agg = (
            s.groupby("customer_id")
            .agg(
                session_cnt=("session_id", "count"),
                pages_mean=("pages_viewed", "mean"),
            )
            .rename(
                columns={
                    "session_cnt": f"sessions_{w}d",
                    "pages_mean": f"pages_{w}d",
                }
            )
            .reset_index()
        )

        out.append(agg)

    df = out[0]
    for a in out[1:]:
        df = df.merge(a, on="customer_id", how="outer")

    return df