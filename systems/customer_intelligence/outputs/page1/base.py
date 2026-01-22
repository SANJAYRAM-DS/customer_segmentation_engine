# systems/customer_intelligence/outputs/base.py

import numpy as np
import pandas as pd

SEGMENT_SCORES = {
    "Loyal": 1.00,
    "Active": 0.75,
    "New": 0.60,
    "At-Risk": 0.30,
    "Churned": 0.00,
}

HEALTH_BANDS = [
    (80, "Excellent"),
    (60, "Good"),
    (40, "Watch"),
    (20, "Critical"),
    (0,  "Lost"),
]

INVESTMENT_MATRIX = {
    ("High", "High"): "Invest",
    ("Low", "High"): "Protect",
    ("High", "Low"): "Nurture",
    ("Low", "Low"): "Let Go",
}

def assign_health_band(score: float) -> str:
    for threshold, band in HEALTH_BANDS:
        if score >= threshold:
            return band
    return "Lost"


def clv_percentile_score(clv, p10, p90):
    val = (np.log1p(clv) - np.log1p(p10)) / (np.log1p(p90) - np.log1p(p10))
    return np.clip(val, 0, 1)
