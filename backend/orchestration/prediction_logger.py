from pathlib import Path
import pandas as pd
from datetime import datetime, timezone


LOG_DIR = Path(__file__).resolve().parents[2] / "backend/data/predictions"
LOG_DIR.mkdir(parents=True, exist_ok=True)


def log_predictions(df: pd.DataFrame, model_name: str, version: int):
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    path = LOG_DIR / f"{model_name}_v{version}_{ts}.parquet"
    df.to_parquet(path, index=False)
    return path
