"""
Evaluation Report Generator
Implements Document 7 requirements for comprehensive model evaluation reporting
"""

import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Optional
import numpy as np
import pandas as pd

from backend.evaluation.metrics import (
    evaluate_churn_comprehensive,
    evaluate_clv_comprehensive,
    evaluate_by_segment,
    evaluate_by_value_tier,
    evaluate_cold_start_vs_mature,
    calibration_metrics,
)


class EvaluationReport:
    """
    Generates comprehensive evaluation reports for model validation
    
    Implements Document 7 requirements:
    - Offline metrics
    - Segment-level analysis
    - Baseline comparison
    - Statistical validation
    """
    
    def __init__(self, model_type: str, model_version: str):
        """
        Args:
            model_type: Type of model ('churn', 'clv', 'segmentation')
            model_version: Model version identifier
        """
        self.model_type = model_type
        self.model_version = model_version
        self.report = {
            "model_type": model_type,
            "model_version": model_version,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "metrics": {},
            "segment_analysis": {},
            "baseline_comparison": {},
        }
    
    def add_overall_metrics(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        dataset_name: str = "validation",
    ):
        """
        Add overall metrics to report
        
        Args:
            y_true: True labels/values
            y_pred: Predictions
            dataset_name: Name of dataset (e.g., 'train', 'validation', 'test')
        """
        if self.model_type == "churn":
            metrics = evaluate_churn_comprehensive(y_true, y_pred)
            
            # Add calibration metrics
            calib_metrics = calibration_metrics(y_true, y_pred)
            metrics.update(calib_metrics)
            
        elif self.model_type == "clv":
            metrics = evaluate_clv_comprehensive(y_true, y_pred)
        else:
            raise ValueError(f"Unknown model type: {self.model_type}")
        
        self.report["metrics"][dataset_name] = metrics
    
    def add_segment_analysis(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        segments: np.ndarray,
        segment_name: str = "default",
    ):
        """
        Add segment-level performance analysis
        
        Args:
            y_true: True labels/values
            y_pred: Predictions
            segments: Segment labels
            segment_name: Name of segmentation scheme
        """
        if self.model_type == "churn":
            metric_fn = lambda yt, yp: evaluate_churn_comprehensive(yt, yp)
        elif self.model_type == "clv":
            metric_fn = lambda yt, yp: evaluate_clv_comprehensive(yt, yp)
        else:
            return
        
        segment_metrics = evaluate_by_segment(
            y_true, y_pred, segments, metric_fn
        )
        
        self.report["segment_analysis"][segment_name] = segment_metrics
    
    def add_value_tier_analysis(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        customer_values: np.ndarray,
        n_tiers: int = 4,
    ):
        """
        Add value-tier stratified analysis
        
        Args:
            y_true: True labels/values
            y_pred: Predictions
            customer_values: Customer value metric (e.g., total_spend)
            n_tiers: Number of value tiers
        """
        if self.model_type == "churn":
            metric_fn = lambda yt, yp: evaluate_churn_comprehensive(yt, yp)
        elif self.model_type == "clv":
            metric_fn = lambda yt, yp: evaluate_clv_comprehensive(yt, yp)
        else:
            return
        
        tier_metrics = evaluate_by_value_tier(
            y_true, y_pred, customer_values, metric_fn, n_tiers
        )
        
        self.report["segment_analysis"]["value_tiers"] = tier_metrics
    
    def add_cold_start_analysis(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        tenure_days: np.ndarray,
        cold_start_threshold: int = 90,
    ):
        """
        Add cold-start vs mature customer analysis
        
        Args:
            y_true: True labels/values
            y_pred: Predictions
            tenure_days: Customer tenure in days
            cold_start_threshold: Days threshold for cold-start
        """
        if self.model_type == "churn":
            metric_fn = lambda yt, yp: evaluate_churn_comprehensive(yt, yp)
        elif self.model_type == "clv":
            metric_fn = lambda yt, yp: evaluate_clv_comprehensive(yt, yp)
        else:
            return
        
        lifecycle_metrics = evaluate_cold_start_vs_mature(
            y_true, y_pred, tenure_days, metric_fn, cold_start_threshold
        )
        
        self.report["segment_analysis"]["lifecycle"] = lifecycle_metrics
    
    def add_baseline_comparison(
        self,
        baseline_metrics: Dict,
        baseline_name: str = "baseline",
    ):
        """
        Add baseline model comparison
        
        Args:
            baseline_metrics: Metrics from baseline model
            baseline_name: Name of baseline
        """
        self.report["baseline_comparison"][baseline_name] = baseline_metrics
        
        # Compute improvement over baseline
        if "validation" in self.report["metrics"]:
            model_metrics = self.report["metrics"]["validation"]
            
            improvements = {}
            for metric_name in baseline_metrics:
                if metric_name in model_metrics:
                    baseline_val = baseline_metrics[metric_name]
                    model_val = model_metrics[metric_name]
                    
                    # For metrics where lower is better (RMSE, MAE, Brier)
                    if metric_name in ["rmse", "mae", "brier_score", "mape"]:
                        if baseline_val > 0:
                            improvement = (baseline_val - model_val) / baseline_val
                        else:
                            improvement = 0.0
                    # For metrics where higher is better (AUC, R²)
                    else:
                        if baseline_val > 0:
                            improvement = (model_val - baseline_val) / baseline_val
                        else:
                            improvement = 0.0
                    
                    improvements[metric_name] = {
                        "baseline": float(baseline_val),
                        "model": float(model_val),
                        "improvement_pct": float(improvement * 100),
                    }
            
            self.report["baseline_comparison"][f"{baseline_name}_improvements"] = improvements
    
    def add_metadata(self, metadata: Dict):
        """Add custom metadata to report"""
        if "metadata" not in self.report:
            self.report["metadata"] = {}
        self.report["metadata"].update(metadata)
    
    def save(self, output_path: Path):
        """
        Save report to JSON file
        
        Args:
            output_path: Path to save report
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with output_path.open("w") as f:
            json.dump(self.report, f, indent=2)
        
        print(f"[OK] Evaluation report saved: {output_path}")
    
    def get_summary(self) -> str:
        """
        Get human-readable summary of evaluation
        
        Returns:
            Formatted summary string
        """
        lines = []
        lines.append("=" * 60)
        lines.append(f"EVALUATION REPORT: {self.model_type.upper()} v{self.model_version}")
        lines.append("=" * 60)
        
        # Overall metrics
        if "validation" in self.report["metrics"]:
            lines.append("\n📊 VALIDATION METRICS:")
            for metric, value in self.report["metrics"]["validation"].items():
                if isinstance(value, (int, float)):
                    lines.append(f"  {metric}: {value:.4f}")
        
        # Baseline comparison
        if self.report["baseline_comparison"]:
            lines.append("\n📈 BASELINE COMPARISON:")
            for baseline_name, improvements in self.report["baseline_comparison"].items():
                if "_improvements" in baseline_name:
                    for metric, data in improvements.items():
                        improvement = data["improvement_pct"]
                        symbol = "↑" if improvement > 0 else "↓"
                        lines.append(
                            f"  {metric}: {symbol} {abs(improvement):.2f}% "
                            f"(baseline: {data['baseline']:.4f}, model: {data['model']:.4f})"
                        )
        
        # Segment analysis summary
        if self.report["segment_analysis"]:
            lines.append("\n🎯 SEGMENT ANALYSIS:")
            for seg_type, seg_data in self.report["segment_analysis"].items():
                lines.append(f"  {seg_type}:")
                for seg_name, seg_metrics in seg_data.items():
                    if isinstance(seg_metrics, dict) and "count" in seg_metrics:
                        lines.append(f"    {seg_name}: {seg_metrics['count']} samples")
        
        lines.append("\n" + "=" * 60)
        
        return "\n".join(lines)


def generate_evaluation_report(
    model_type: str,
    model_version: str,
    y_true: np.ndarray,
    y_pred: np.ndarray,
    features_df: Optional[pd.DataFrame] = None,
    baseline_metrics: Optional[Dict] = None,
    output_dir: Optional[Path] = None,
) -> EvaluationReport:
    """
    Generate comprehensive evaluation report
    
    Args:
        model_type: Type of model
        model_version: Model version
        y_true: True labels/values
        y_pred: Predictions
        features_df: Optional dataframe with features for segment analysis
        baseline_metrics: Optional baseline metrics for comparison
        output_dir: Optional directory to save report
        
    Returns:
        EvaluationReport object
    """
    report = EvaluationReport(model_type, model_version)
    
    # Overall metrics
    report.add_overall_metrics(y_true, y_pred, "validation")
    
    # Segment analysis (if features provided)
    if features_df is not None:
        # Value tier analysis
        if "total_spend" in features_df.columns:
            report.add_value_tier_analysis(
                y_true, y_pred, features_df["total_spend"].values
            )
        
        # Cold-start analysis
        if "tenure_days" in features_df.columns:
            report.add_cold_start_analysis(
                y_true, y_pred, features_df["tenure_days"].values
            )
    
    # Baseline comparison
    if baseline_metrics is not None:
        report.add_baseline_comparison(baseline_metrics, "baseline")
    
    # Save report
    if output_dir is not None:
        report_path = output_dir / f"evaluation_report_{model_version}.json"
        report.save(report_path)
    
    # Print summary
    print(report.get_summary())
    
    return report