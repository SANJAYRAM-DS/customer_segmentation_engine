"""
Rule-Based Churn Baseline
Implements Document 6 Section 6.1.1: Rule-Based Baselines

Simple heuristics based on business logic:
- Churn if no activity in last N days
- At-risk if engagement drops below baseline
"""

from pathlib import Path
import json
import pandas as pd
import numpy as np
from datetime import datetime, timezone
from typing import Dict, Tuple


class RuleBasedChurnBaseline:
    """
    Rule-based churn prediction using simple business heuristics
    
    Rules:
    1. High Risk: recency_days > 60 AND sessions_30d == 0
    2. Medium Risk: recency_days > 30 AND (sessions_30d < 2 OR spend_30d == 0)
    3. Low Risk: Otherwise
    """
    
    def __init__(
        self,
        high_risk_recency: int = 60,
        medium_risk_recency: int = 30,
        min_sessions_threshold: int = 2,
    ):
        self.high_risk_recency = high_risk_recency
        self.medium_risk_recency = medium_risk_recency
        self.min_sessions_threshold = min_sessions_threshold
        self.name = "rule_based_churn"
        self.version = "v1"
        
    def predict(self, df: pd.DataFrame) -> np.ndarray:
        """
        Predict churn probability using rules
        
        Args:
            df: Feature dataframe with required columns
            
        Returns:
            Array of churn probabilities [0, 1]
        """
        # Initialize with low risk
        churn_prob = np.full(len(df), 0.2)
        
        # High risk: no recent activity
        high_risk_mask = (
            (df["recency_days"] > self.high_risk_recency) &
            (df["sessions_30d"] == 0)
        )
        churn_prob[high_risk_mask] = 0.8
        
        # Medium risk: low engagement
        medium_risk_mask = (
            (df["recency_days"] > self.medium_risk_recency) &
            (
                (df["sessions_30d"] < self.min_sessions_threshold) |
                (df["spend_30d"] == 0)
            ) &
            ~high_risk_mask  # Exclude already classified as high risk
        )
        churn_prob[medium_risk_mask] = 0.5
        
        return churn_prob
    
    def predict_binary(self, df: pd.DataFrame, threshold: float = 0.5) -> np.ndarray:
        """
        Predict binary churn labels
        
        Args:
            df: Feature dataframe
            threshold: Classification threshold
            
        Returns:
            Binary predictions (0 or 1)
        """
        probs = self.predict(df)
        return (probs >= threshold).astype(int)
    
    def evaluate(self, df: pd.DataFrame, target_col: str = "churn_90d") -> Dict:
        """
        Evaluate baseline performance
        
        Args:
            df: Feature dataframe with target column
            target_col: Name of target column
            
        Returns:
            Dictionary of metrics
        """
        from sklearn.metrics import (
            roc_auc_score,
            average_precision_score,
            accuracy_score,
            precision_score,
            recall_score,
            f1_score,
        )
        
        y_true = df[target_col].values
        y_prob = self.predict(df)
        y_pred = self.predict_binary(df)
        
        metrics = {
            "roc_auc": float(roc_auc_score(y_true, y_prob)),
            "pr_auc": float(average_precision_score(y_true, y_prob)),
            "accuracy": float(accuracy_score(y_true, y_pred)),
            "precision": float(precision_score(y_true, y_pred, zero_division=0)),
            "recall": float(recall_score(y_true, y_pred, zero_division=0)),
            "f1": float(f1_score(y_true, y_pred, zero_division=0)),
        }
        
        return metrics
    
    def save(self, output_dir: Path) -> Path:
        """
        Save baseline model metadata
        
        Args:
            output_dir: Directory to save model
            
        Returns:
            Path to saved metadata file
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        
        metadata = {
            "model_name": self.name,
            "version": self.version,
            "type": "rule_based",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "parameters": {
                "high_risk_recency": self.high_risk_recency,
                "medium_risk_recency": self.medium_risk_recency,
                "min_sessions_threshold": self.min_sessions_threshold,
            },
            "description": "Rule-based churn baseline using recency and engagement heuristics",
        }
        
        meta_path = output_dir / f"{self.name}_{self.version}.json"
        with meta_path.open("w") as f:
            json.dump(metadata, f, indent=2)
        
        return meta_path


def train_and_evaluate_baseline(
    features_path: Path,
    output_dir: Path,
) -> Tuple[RuleBasedChurnBaseline, Dict]:
    """
    Train and evaluate rule-based churn baseline
    
    Args:
        features_path: Path to feature parquet file
        output_dir: Directory to save baseline
        
    Returns:
        (baseline_model, metrics)
    """
    # Load features
    df = pd.read_parquet(features_path)
    
    # Create baseline
    baseline = RuleBasedChurnBaseline()
    
    # Evaluate
    metrics = baseline.evaluate(df)
    
    # Save
    meta_path = baseline.save(output_dir)
    
    print(f"[OK] Rule-based churn baseline saved: {meta_path}")
    print(f"[METRICS] {metrics}")
    
    return baseline, metrics


if __name__ == "__main__":
    BASE_DIR = Path(__file__).resolve().parents[3]
    FEATURES_PATH = BASE_DIR / "backend" / "data" / "processed" / "churn" / "features.parquet"
    OUTPUT_DIR = BASE_DIR / "backend" / "models" / "baselines" / "churn"
    
    if FEATURES_PATH.exists():
        baseline, metrics = train_and_evaluate_baseline(FEATURES_PATH, OUTPUT_DIR)
    else:
        print(f"[ERROR] Features not found: {FEATURES_PATH}")
        print("[INFO] Run feature engineering first")