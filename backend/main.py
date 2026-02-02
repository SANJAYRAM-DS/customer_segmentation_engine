from pathlib import Path
import json
import yaml
import hashlib

import numpy as np
import pandas as pd
import joblib

from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, FunctionTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import roc_auc_score, average_precision_score

from backend.data.feature_registry.loader import load_feature_registry
from backend.models.utils import safe_log1p
from backend.models.champion_manager import load_champion, promote_champion
from backend.models.promotion_policy import better_churn
from backend.orchestration.baseline_stats import save_baseline_stats

BASE_DIR = Path(__file__).resolve().parents[3]
REGISTRY_DIR = BASE_DIR / "backend" / "models" / "model_registry" / "churn"
CONFIG_PATH = Path(__file__).parent / "config.yaml"

REGISTRY_DIR.mkdir(parents=True, exist_ok=True)
model_dir = REGISTRY_DIR
current = load_champion(model_dir)

def dataset_fingerprint(df: pd.DataFrame) -> str:
    return hashlib.md5(
        pd.util.has_pandas_object(df, index=True).values
    ).hexdigest()
    
def dataset_fingerprint(df: pd.DataFrame) -> str:
    return hashlib.md5(
        pd.util.hash_pandas.object(df, index=True).values
    ).hexdigest()

def next_version(model_dir: Path, model_name: str) -> int:
    versions = [
        int(p.stem.split("_v")[-1])
        for p in model_dir.glob(f"{model_name}_v*.joblib")
    ]
    return max(versions, default=0) + 1

with open(CONFIG_PATH, "r") as f:
    cfg = yaml.safe_load(f)
    
MODEL_NAME = cfg['model']['name']
