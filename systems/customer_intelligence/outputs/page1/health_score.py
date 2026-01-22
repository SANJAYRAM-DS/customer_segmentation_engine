# systems/customer_intelligence/outputs/health_score.py

import numpy as np
import pandas as pd

# -----------------------
# CONFIG
# -----------------------

SEGMENT_SCORE_MAP = {
    "Loyal": 1.00,
    "Active": 0.75,
    "New": 0.60,
    "At-Risk": 0.30,
    "Churned": 0.00,
}

WEIGHTS = {
    "value": 0.35,
    "risk": 0.35,
    "engagement": 0.20,
    "segment": 0.10,
}

HEALTH_BANDS = [
    (80, "Excellent"),
    (60, "Good"),
    (40, "Watch"),
    (20, "Critical"),
    (0, "Lost"),
]

# -----------------------
# HELPERS
# -----------------------

def assign_health_band(score: float) -> str:
    for threshold, band in HEALTH_BANDS:
        if score >= threshold:
            return band
    return "Lost"


def sigmoid(x):
    return 1 / (1 + np.exp(-x))


# -----------------------
# COMPONENTS
# -----------------------

def compute_value_score(clv, p10, p90):
    if clv <= 0 or p90 <= p10:
        return 0.0

    v = (np.log1p(clv) - np.log1p(p10)) / (np.log1p(p90) - np.log1p(p10))
    return float(np.clip(v, 0, 1))


def compute_engagement_score(row, stats):
    z_scores = []

    for feature, weight in stats["weights"].items():
        mu = stats["mean"].get(feature, 0)
        sigma = stats["std"].get(feature, 1)

        if sigma == 0:
            continue

        z = (row[feature] - mu) / sigma
        z_scores.append(weight * z)

    if not z_scores:
        return 0.5  # neutral fallback

    return float(sigmoid(np.sum(z_scores)))


# -----------------------
# MAIN SCORE
# -----------------------

def compute_customer_health_scores(df: pd.DataFrame) -> pd.DataFrame:
    """
    Required columns:
    - customer_id
    - clv_12m
    - churn_probability
    - segment
    - engagement features
    """

    df = df.copy()

    # -----------------------
    # Value normalization
    # -----------------------
    p10, p90 = np.percentile(df["clv_12m"], [10, 90])

    df["V"] = df["clv_12m"].apply(lambda x: compute_value_score(x, p10, p90))
    df["R"] = df["churn_probability"]

    # -----------------------
    # Engagement
    # -----------------------
    ENG_FEATURES = [
        "session_frequency",
        "order_frequency",
        "recency_days",
        "spend_30d",
    ]

    stats = {
        "mean": df[ENG_FEATURES].mean().to_dict(),
        "std": df[ENG_FEATURES].std().replace(0, 1).to_dict(),
        "weights": {
            "session_frequency": 0.3,
            "order_frequency": 0.3,
            "spend_30d": 0.3,
            "recency_days": -0.1,
        },
    }

    df["E"] = df.apply(lambda r: compute_engagement_score(r, stats), axis=1)

    # -----------------------
    # Segment score
    # -----------------------
    df["S"] = df["segment"].map(SEGMENT_SCORE_MAP).fillna(0.0)

    # -----------------------
    # Health score
    # -----------------------
    df["health_score"] = (
        100
        * (
            WEIGHTS["value"] * df["V"]
            + WEIGHTS["risk"] * (1 - df["R"])
            + WEIGHTS["engagement"] * df["E"]
            + WEIGHTS["segment"] * df["S"]
        )
    ).round(1)

    # Edge cases
    df.loc[df["segment"] == "Churned", "health_score"] = 0
    df["health_band"] = df["health_score"].apply(assign_health_band)

    return df

def assign_investment_priority(row):
    clv_level = "High" if row["V"] >= 0.6 else "Low"
    health_level = "High" if row["health_score"] >= 60 else "Low"

    matrix = {
        ("High", "High"): "Invest",
        ("Low", "High"): "Protect",
        ("High", "Low"): "Nurture",
        ("Low", "Low"): "Let Go",
    }

    return matrix[(health_level, clv_level)]

df["investment_priority"] = df.apply(assign_investment_priority, axis=1)