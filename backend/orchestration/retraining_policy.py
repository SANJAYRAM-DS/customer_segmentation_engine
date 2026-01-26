# backend/orchestration/retraining_policy.py

import hashlib
from pathlib import Path
import pandas as pd


def fingerprint_directory(path: Path) -> str:
    """Hash all files in a directory deterministically"""
    h = hashlib.md5()
    for p in sorted(path.glob("*")):
        if p.is_file():
            h.update(p.read_bytes())
    return h.hexdigest()


def fingerprint_dataframe(df: pd.DataFrame) -> str:
    return hashlib.md5(
        pd.util.hash_pandas_object(df, index=True).values
    ).hexdigest()


def should_rebuild_features(prev_fp: str | None, new_fp: str) -> bool:
    return prev_fp != new_fp


def should_retrain_models(prev_fp: str | None, feature_fp: str) -> bool:
    return prev_fp != feature_fp
