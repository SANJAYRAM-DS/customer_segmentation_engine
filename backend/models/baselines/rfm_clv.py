"""
RFM-Based CLV Baseline
Implements Document 6 Section 6.1.3: Statistical Baselines (CLV)

CLV approximated from:
- Recency (R): Days since last purchase
- Frequency (F): Purchase frequency
- Monetary (M): Average order value

Simple formula: CLV ≈ (Frequency × Monetary) × Survival_Factor
"""

from pathlib import Path
import json
import pandas as pd
import numpy as np
from datetime import datetime, timezone
from typing import Dict, Tuple


class RFMCLVBaseline:
    """
    RFM-based CLV prediction using historical averages
    
    Formula:
        CLV_90d = (order_frequency * 90) * avg_order_value * survival_factor
        
    Where survival_factor is based on recency:
        - recency < 30 days: 0.9 (high likelihood to purchase)
        - recency 30-60 days: 0.6 (medium likelihood)
        - recency > 60 days: 0.3 (low likelihood)
    """
    
    def __init__(
        self,
        horizon_days: int = 90,
        recency_thresholds: Tuple[int, int] = (30, 60),
        survival_factors: Tuple[float, float, float] = (0.9, 0.6, 0.3),
    ):
        self.horizon_days = horizon_days
        self.recency_thresholds = recency_thresholds
        self.survival_factors = survival_factors
        self.name = "rfm_clv"
        self.version = "v1"
        
    def predict(self, df: pd.DataFrame) -> np.ndarray:
        """
        Predict CLV using RFM heuristics
        
        Args:
            df: Feature dataframe with required columns
            
        Returns:
            Array of predicted CLV values
        """
        # Calculate expected orders in horizon
        expected_orders = df["order_frequency"] * self.horizon_days
        
        # Calculate expected value per order
        avg_value = df["avg_order_value"]
        
        # Calculate survival factor based on recency
        survival = np.full(len(df), self.survival_factors[2])  # Default: low
        
        # High survival (recent customers)
        recent_mask = df["recency_days"] < self.recency_thresholds[0]
        survival[recent_mask] = self.survival_factors[0]
        
        # Medium survival
        medium_mask = (
            (df["recency_days"] >= self.recency_thresholds[0]) &
            (df["recency_days"] < self.recency_thresholds[1])
        )
        survival[medium_mask] = self.survival_factors[1]
        
        # CLV = Expected Orders × Avg Value × Survival
        clv = expected_orders * avg_value * survival
        
        # Cap at reasonable maximum (e.g., 10x historical average)
        max_clv = df["total_spend"].mean() * 10
        clv = np.clip(clv, 0, max_clv)
        
        return clv
    
    def evaluate(self, df: pd.DataFrame, target_col: str = "future_90d_spend") -> Dict:
        """
        Evaluate baseline performance
        
        Args:
            df: Feature dataframe with target column
            target_col: Name of target column
            
        Returns:
            Dictionary of metrics
        """
        from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
        
        y_true = df[target_col].values
        y_pred = self.predict(df)
        
        metrics = {
            "rmse": float(np.sqrt(mean_squared_error(y_true, y_pred))),
            "mae": float(mean_absolute_error(y_true, y_pred)),
            "r2": float(r2_score(y_true, y_pred)),
            "mean_prediction": float(y_pred.mean()),
            "mean_actual": float(y_true.mean()),
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
            "type": "rfm_baseline",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "parameters": {
                "horizon_days": self.horizon_days,
                "recency_thresholds": self.recency_thresholds,
                "survival_factors": self.survival_factors,
            },
            "description": "RFM-based CLV baseline using recency, frequency, and monetary value",
        }
        
        meta_path = output_dir / f"{self.name}_{self.version}.json"
        with meta_path.open("w") as f:
            json.dump(metadata, f, indent=2)
        
        return meta_path


class HistoricalAverageCLV:
    """
    Even simpler baseline: predict CLV as historical average spend
    """
    
    def __init__(self, lookback_days: int = 90):
        self.lookback_days = lookback_days
        self.name = "historical_avg_clv"
        self.version = "v1"
        
    def predict(self, df: pd.DataFrame) -> np.ndarray:
        """
        Predict CLV as historical average
        
        Uses spend_90d as proxy for future_90d_spend
        """
        # Use historical 90-day spend as prediction
        return df["spend_90d"].values
    
    def evaluate(self, df: pd.DataFrame, target_col: str = "future_90d_spend") -> Dict:
        """Evaluate baseline performance"""
        from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
        
        y_true = df[target_col].values
        y_pred = self.predict(df)
        
        metrics = {
            "rmse": float(np.sqrt(mean_squared_error(y_true, y_pred))),
            "mae": float(mean_absolute_error(y_true, y_pred)),
            "r2": float(r2_score(y_true, y_pred)),
        }
        
        return metrics


def train_and_evaluate_baselines(
    features_path: Path,
    output_dir: Path,
) -> Dict:
    """
    Train and evaluate all CLV baselines
    
    Args:
        features_path: Path to feature parquet file
        output_dir: Directory to save baselines
        
    Returns:
        Dictionary of baseline metrics
    """
    # Load features
    df = pd.read_parquet(features_path)
    
    results = {}
    
    # RFM Baseline
    print("[INFO] Evaluating RFM CLV baseline...")
    rfm_baseline = RFMCLVBaseline()
    rfm_metrics = rfm_baseline.evaluate(df)
    rfm_baseline.save(output_dir)
    results["rfm"] = rfm_metrics
    print(f"[RFM] {rfm_metrics}")
    
    # Historical Average Baseline
    print("[INFO] Evaluating Historical Average baseline...")
    hist_baseline = HistoricalAverageCLV()
    hist_metrics = hist_baseline.evaluate(df)
    results["historical_avg"] = hist_metrics
    print(f"[HIST] {hist_metrics}")
    
    # Save comparison
    comparison_path = output_dir / "baseline_comparison.json"
    with comparison_path.open("w") as f:
        json.dump(results, f, indent=2)
    
    print(f"[OK] Baseline comparison saved: {comparison_path}")
    
    return results


if __name__ == "__main__":
    BASE_DIR = Path(__file__).resolve().parents[3]
    FEATURES_PATH = BASE_DIR / "backend" / "data" / "processed" / "clv" / "features.parquet"
    OUTPUT_DIR = BASE_DIR / "backend" / "models" / "baselines" / "clv"
    
    if FEATURES_PATH.exists():
        results = train_and_evaluate_baselines(FEATURES_PATH, OUTPUT_DIR)
    else:
        print(f"[ERROR] Features not found: {FEATURES_PATH}")
        print("[INFO] Run feature engineering first")
