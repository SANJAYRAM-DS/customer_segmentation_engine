from pathlib import Path
import json
import hashlib
import pandas as pd
import numpy as np
from datetime import datetime, timezone


def fingerprint_df(df: pd.DataFrame) -> str:
    return hashlib.md5(
        pd.util.hash_pandas_object(df, index=True).values
    ).hexdigest()


def save_predictions(model_name, model_version, predictions, project_root):
    pred_dir = (
        project_root
        / "backend"
        / "monitoring"
        / "predictions"
        / model_name
    )
    pred_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.now(timezone.utc).isoformat()
    fp = fingerprint_df(predictions)

    path = pred_dir / f"predictions_{ts.replace(':', '-')}.parquet"
    predictions.to_parquet(path, index=False)

    meta = {
        "model": model_name,
        "version": model_version,
        "timestamp": ts,
        "rows": len(predictions),
        "dataset_fingerprint": fp,
        "path": str(path),
    }

    with open(path.with_suffix(".json"), "w") as f:
        json.dump(meta, f, indent=2)

    return path