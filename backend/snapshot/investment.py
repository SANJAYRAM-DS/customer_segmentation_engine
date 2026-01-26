# backend/snapshot/investment.py
import pandas as pd
import numpy as np

def assign_investment_priority(df: pd.DataFrame) -> pd.DataFrame:
    conditions = [
        (df["clv_12m"] > df["clv_12m"].quantile(0.8)) & (df["churn_probability"] > 0.6),
        (df["clv_12m"] > df["clv_12m"].quantile(0.8)),
        (df["churn_probability"] > 0.6),
    ]

    choices = ["save", "grow", "monitor"]

    df["investment_priority"] = pd.Series(
        pd.Categorical(
            np.select(conditions, choices, default="low"),
            categories=["save", "grow", "monitor", "low"],
            ordered=True,
        )
    )

    return df
