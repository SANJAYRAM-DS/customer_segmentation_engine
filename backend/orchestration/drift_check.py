import json
import numpy as np
import pandas as pd
from pathlib import Path
from scipy.stats import ks_2samp

def psi(expected, actual, bins=10):
    eps = 1e-6
    breakpoints = np.percentile(expected, np.linspace(0, 100, bins + 1))

    e_pct = np.histogram(expected, breakpoints)[0] / len(expected)
    a_pct = np.histogram(actual, breakpoints)[0] / len(actual)

    return float(np.sum((a_pct - e_pct) * np.log((a_pct + eps) / (e_pct + eps))))


def detect_drift(df, baseline_path, numeric_cols, categorical_cols):
    baseline = json.loads(baseline_path.read_text())

    report = {
        "numeric": {},
        "categorical": {},
        "severe": False,
    }

    for col in numeric_cols:
        ref = np.array(list(baseline["numeric"][col]["quantiles"].values()))
        cur = df[col].dropna().values
        score = psi(ref, cur)

        report["numeric"][col] = score
        if score >= 0.25:
            report["severe"] = True

    for col in categorical_cols:
        base = baseline["categorical"][col]
        curr = df[col].value_counts(normalize=True).to_dict()

        drift = sum(abs(curr.get(k, 0) - base.get(k, 0)) for k in set(base) | set(curr))
        report["categorical"][col] = drift

        if drift >= 0.3:
            report["severe"] = True

    return report

def ks_drift(ref: pd.Series, cur: pd.Series, alpha=0.05):
    stat, p = ks_2samp(ref.dropna(), cur.dropna())
    return {
        "statistic": float(stat),
        "p_value": float(p),
        "drift": p < alpha,
    }


def feature_drift_report(
    ref_df: pd.DataFrame,
    cur_df: pd.DataFrame,
    features: list[str],
):
    report = {}
    for f in features:
        report[f] = ks_drift(ref_df[f], cur_df[f])
    return report
