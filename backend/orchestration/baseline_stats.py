# backend/orchestration/baseline_stats.py

import json
import pandas as pd
from pathlib import Path


def save_baseline_stats(df: pd.DataFrame, path: Path):
    stats = {
        "numeric": {
            col: {
                "quantiles": df[col].quantile([0.1, 0.5, 0.9]).to_dict()
            }
            for col in df.select_dtypes("number").columns
        },
        "categorical": {
            col: df[col].value_counts(normalize=True).to_dict()
            for col in df.select_dtypes("object").columns
        },
    }

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(stats, indent=2))
