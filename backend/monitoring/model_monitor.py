"""
Model Performance Monitoring
Implements Document 11.2: Model Drift Monitoring
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional
from pathlib import Path
from datetime import datetime, timezone
import json
from collections import deque

from backend.evaluation.metrics import (
    evaluate_churn_comprehensive,
    evaluate_clv_comprehensive,
    calibration_metrics,
)


class ModelPerformanceMonitor:
    """
    Monitors model performance over time
    
    Implements Document 11.2: Model Drift Monitoring
    """
    
    def __init__(
        self,
        model_type: str,
        window_size: int = 30,
        auc_threshold: float = 0.05,
        mae_threshold: float = 0.10,
        calibration_threshold: float = 0.05,
    ):
        """
        Args:
            model_type: Type of model ('churn', 'clv', 'segmentation')
            window_size: Rolling window size for metrics
            auc_threshold: AUC drop threshold for alerts (5% default)
            mae_threshold: MAE increase threshold for alerts (10% default)
            calibration_threshold: Calibration drift threshold
        """
        self.model_type = model_type
        self.window_size = window_size
        self.auc_threshold = auc_threshold
        self.mae_threshold = mae_threshold
        self.calibration_threshold = calibration_threshold
        
        # Rolling metrics storage
        self.metrics_history = deque(maxlen=window_size)
        self.baseline_metrics = None
    
    def set_baseline(self, baseline_metrics: Dict):
        """
        Set baseline metrics for comparison
        
        Args:
            baseline_metrics: Baseline performance metrics
        """
        self.baseline_metrics = baseline_metrics
        print(f"[INFO] Baseline metrics set for {self.model_type}")
    
    def evaluate_current_performance(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        timestamp: Optional[datetime] = None,
    ) -> Dict:
        """
        Evaluate current model performance
        
        Args:
            y_true: True labels/values
            y_pred: Predictions
            timestamp: Evaluation timestamp
            
        Returns:
            Performance metrics
        """
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)
        
        if self.model_type == "churn":
            metrics = evaluate_churn_comprehensive(y_true, y_pred)
            calib = calibration_metrics(y_true, y_pred)
            metrics.update(calib)
        elif self.model_type == "clv":
            metrics = evaluate_clv_comprehensive(y_true, y_pred)
        else:
            raise ValueError(f"Unknown model type: {self.model_type}")
        
        # Add timestamp
        metrics["timestamp"] = timestamp.isoformat()
        
        # Store in history
        self.metrics_history.append(metrics)
        
        return metrics
    
    def detect_performance_drift(self, current_metrics: Dict) -> Dict:
        """
        Detect performance degradation
        
        Implements Document 11.2.2: Drift Detection Techniques
        
        Args:
            current_metrics: Current performance metrics
            
        Returns:
            Drift detection report
        """
        report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "model_type": self.model_type,
            "alerts": [],
            "metrics_comparison": {},
        }
        
        if self.baseline_metrics is None:
            report["alerts"].append({
                "severity": "info",
                "message": "No baseline metrics set - cannot detect drift",
            })
            return report
        
        # Check churn-specific metrics
        if self.model_type == "churn":
            # AUC degradation
            if "roc_auc" in current_metrics and "roc_auc" in self.baseline_metrics:
                baseline_auc = self.baseline_metrics["roc_auc"]
                current_auc = current_metrics["roc_auc"]
                auc_drop = (baseline_auc - current_auc) / baseline_auc
                
                report["metrics_comparison"]["roc_auc"] = {
                    "baseline": baseline_auc,
                    "current": current_auc,
                    "drop_pct": auc_drop * 100,
                }
                
                if auc_drop > self.auc_threshold:
                    report["alerts"].append({
                        "severity": "high",
                        "metric": "roc_auc",
                        "message": f"AUC degradation detected: {baseline_auc:.4f} → {current_auc:.4f} ({auc_drop*100:.2f}% drop)",
                        "baseline": baseline_auc,
                        "current": current_auc,
                        "threshold": self.auc_threshold,
                    })
            
            # Calibration drift
            if "brier_score" in current_metrics and "brier_score" in self.baseline_metrics:
                baseline_brier = self.baseline_metrics["brier_score"]
                current_brier = current_metrics["brier_score"]
                brier_increase = (current_brier - baseline_brier) / baseline_brier
                
                report["metrics_comparison"]["brier_score"] = {
                    "baseline": baseline_brier,
                    "current": current_brier,
                    "increase_pct": brier_increase * 100,
                }
                
                if brier_increase > self.calibration_threshold:
                    report["alerts"].append({
                        "severity": "medium",
                        "metric": "brier_score",
                        "message": f"Calibration drift detected: Brier score increased {brier_increase*100:.2f}%",
                        "baseline": baseline_brier,
                        "current": current_brier,
                        "threshold": self.calibration_threshold,
                    })
        
        # Check CLV-specific metrics
        elif self.model_type == "clv":
            # MAE degradation
            if "mae" in current_metrics and "mae" in self.baseline_metrics:
                baseline_mae = self.baseline_metrics["mae"]
                current_mae = current_metrics["mae"]
                mae_increase = (current_mae - baseline_mae) / baseline_mae
                
                report["metrics_comparison"]["mae"] = {
                    "baseline": baseline_mae,
                    "current": current_mae,
                    "increase_pct": mae_increase * 100,
                }
                
                if mae_increase > self.mae_threshold:
                    report["alerts"].append({
                        "severity": "high",
                        "metric": "mae",
                        "message": f"MAE degradation detected: {baseline_mae:.2f} → {current_mae:.2f} ({mae_increase*100:.2f}% increase)",
                        "baseline": baseline_mae,
                        "current": current_mae,
                        "threshold": self.mae_threshold,
                    })
            
            # Top-decile accuracy
            if "top_10pct_mae" in current_metrics and "top_10pct_mae" in self.baseline_metrics:
                baseline_top = self.baseline_metrics["top_10pct_mae"]
                current_top = current_metrics["top_10pct_mae"]
                top_increase = (current_top - baseline_top) / baseline_top
                
                report["metrics_comparison"]["top_10pct_mae"] = {
                    "baseline": baseline_top,
                    "current": current_top,
                    "increase_pct": top_increase * 100,
                }
                
                if top_increase > self.mae_threshold:
                    report["alerts"].append({
                        "severity": "high",
                        "metric": "top_10pct_mae",
                        "message": f"Top-decile accuracy degraded: {baseline_top:.2f} → {current_top:.2f}",
                        "baseline": baseline_top,
                        "current": current_top,
                    })
        
        return report
    
    def get_rolling_metrics(self) -> Dict:
        """
        Get rolling window statistics
        
        Returns:
            Rolling metrics summary
        """
        if len(self.metrics_history) == 0:
            return {}
        
        # Convert to DataFrame for easy aggregation
        df = pd.DataFrame(list(self.metrics_history))
        
        rolling_stats = {}
        
        # Get numeric columns only
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        for col in numeric_cols:
            rolling_stats[col] = {
                "mean": float(df[col].mean()),
                "std": float(df[col].std()),
                "min": float(df[col].min()),
                "max": float(df[col].max()),
                "latest": float(df[col].iloc[-1]),
            }
        
        return rolling_stats
    
    def check_prediction_distribution(
        self,
        current_predictions: np.ndarray,
        reference_predictions: np.ndarray,
    ) -> Dict:
        """
        Monitor prediction distribution shifts
        
        Implements Document 11.2.2: Predicted distributions vs historical
        
        Args:
            current_predictions: Current prediction scores
            reference_predictions: Reference/historical predictions
            
        Returns:
            Distribution shift report
        """
        from scipy import stats
        
        report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "alerts": [],
        }
        
        # KS test for distribution shift
        ks_stat, ks_pval = stats.ks_2samp(reference_predictions, current_predictions)
        
        report["ks_statistic"] = float(ks_stat)
        report["ks_pvalue"] = float(ks_pval)
        
        # Mean shift
        ref_mean = reference_predictions.mean()
        cur_mean = current_predictions.mean()
        mean_shift = abs(cur_mean - ref_mean) / ref_mean if ref_mean > 0 else 0
        
        report["mean_shift_pct"] = float(mean_shift * 100)
        
        # Alert on significant shifts
        if ks_stat > 0.1:
            report["alerts"].append({
                "severity": "medium",
                "message": f"Prediction distribution shift detected (KS={ks_stat:.4f})",
                "ks_statistic": float(ks_stat),
            })
        
        if mean_shift > 0.2:  # 20% shift
            report["alerts"].append({
                "severity": "high",
                "message": f"Large mean prediction shift: {ref_mean:.4f} → {cur_mean:.4f} ({mean_shift*100:.2f}%)",
                "reference_mean": float(ref_mean),
                "current_mean": float(cur_mean),
            })
        
        return report
    
    def save_monitoring_report(self, report: Dict, output_path: Path):
        """Save monitoring report to JSON"""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with output_path.open("w") as f:
            json.dump(report, f, indent=2)
        
        print(f"[OK] Monitoring report saved: {output_path}")
    
    def print_summary(self, drift_report: Dict):
        """Print human-readable monitoring summary"""
        print("\n" + "=" * 60)
        print(f"MODEL PERFORMANCE MONITORING: {self.model_type.upper()}")
        print("=" * 60)
        print(f"Timestamp: {drift_report['timestamp']}")
        
        if "metrics_comparison" in drift_report and drift_report["metrics_comparison"]:
            print("\n📊 METRICS COMPARISON:")
            for metric, data in drift_report["metrics_comparison"].items():
                print(f"  {metric}:")
                print(f"    Baseline: {data['baseline']:.4f}")
                print(f"    Current:  {data['current']:.4f}")
                if 'drop_pct' in data:
                    print(f"    Change:   {data['drop_pct']:.2f}%")
                elif 'increase_pct' in data:
                    print(f"    Change:   +{data['increase_pct']:.2f}%")
        
        if drift_report["alerts"]:
            print(f"\n⚠️  {len(drift_report['alerts'])} ALERTS:")
            for alert in drift_report["alerts"]:
                severity_icon = "🔴" if alert["severity"] == "high" else "🟡"
                print(f"  {severity_icon} {alert['message']}")
        else:
            print("\n✅ No performance degradation detected")
        
        print("=" * 60)


def monitor_model_performance(
    model_type: str,
    y_true: np.ndarray,
    y_pred: np.ndarray,
    baseline_metrics: Dict,
    output_dir: Optional[Path] = None,
) -> Dict:
    """
    Convenience function to monitor model performance
    
    Args:
        model_type: Type of model
        y_true: True labels/values
        y_pred: Predictions
        baseline_metrics: Baseline metrics for comparison
        output_dir: Directory to save reports
        
    Returns:
        Performance monitoring report
    """
    monitor = ModelPerformanceMonitor(model_type)
    monitor.set_baseline(baseline_metrics)
    
    # Evaluate current performance
    current_metrics = monitor.evaluate_current_performance(y_true, y_pred)
    
    # Detect drift
    drift_report = monitor.detect_performance_drift(current_metrics)
    
    # Print summary
    monitor.print_summary(drift_report)
    
    # Save report
    if output_dir:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = output_dir / f"performance_monitor_{model_type}_{timestamp}.json"
        monitor.save_monitoring_report(drift_report, report_path)
    
    return drift_report
