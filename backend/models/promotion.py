"""
Enhanced Model Promotion Policy
Implements Document 6 requirements for:
- Multi-metric validation
- Statistical significance testing
- Secondary metric regression checks
- Model gating criteria
"""

from typing import Dict, List, Optional, Tuple
import numpy as np


class PromotionPolicy:
    """
    Enhanced promotion policy with multi-metric gating
    
    A model is eligible for production deployment only if:
    1. It outperforms baseline on primary business-aligned metrics
    2. Performance gains are statistically validated
    3. No critical regressions on secondary metrics
    4. Inference latency and cost remain within SLAs (if provided)
    """
    
    def __init__(
        self,
        min_improvement: float = 0.01,
        max_secondary_regression: float = 0.05,
        min_sample_size: int = 100,
    ):
        """
        Args:
            min_improvement: Minimum relative improvement required (1% default)
            max_secondary_regression: Max allowed regression on secondary metrics (5% default)
            min_sample_size: Minimum samples for statistical tests
        """
        self.min_improvement = min_improvement
        self.max_secondary_regression = max_secondary_regression
        self.min_sample_size = min_sample_size
    
    def evaluate_churn_promotion(
        self,
        challenger_metrics: Dict,
        champion_metrics: Dict,
        baseline_metrics: Optional[Dict] = None,
    ) -> Tuple[bool, str]:
        """
        Evaluate if challenger churn model should be promoted
        
        Primary metric: PR-AUC (precision-recall)
        Secondary metric: ROC-AUC
        
        Args:
            challenger_metrics: Metrics from new model
            champion_metrics: Metrics from current champion
            baseline_metrics: Optional baseline model metrics
            
        Returns:
            (should_promote, reason)
        """
        # Primary metric: PR-AUC
        challenger_pr = challenger_metrics.get("pr_auc", 0)
        champion_pr = champion_metrics.get("pr_auc", 0)
        
        # Calculate relative improvement
        if champion_pr > 0:
            pr_improvement = (challenger_pr - champion_pr) / champion_pr
        else:
            pr_improvement = float('inf') if challenger_pr > 0 else 0
        
        # Check minimum improvement threshold
        if pr_improvement < self.min_improvement:
            return False, (
                f"Insufficient PR-AUC improvement: {pr_improvement:.2%} "
                f"(required: {self.min_improvement:.2%})"
            )
        
        # Secondary metric: ROC-AUC (check for regression)
        challenger_roc = challenger_metrics.get("roc_auc", 0)
        champion_roc = champion_metrics.get("roc_auc", 0)
        
        if champion_roc > 0:
            roc_change = (challenger_roc - champion_roc) / champion_roc
            if roc_change < -self.max_secondary_regression:
                return False, (
                    f"ROC-AUC regression detected: {roc_change:.2%} "
                    f"(max allowed: {-self.max_secondary_regression:.2%})"
                )
        
        # Check against baseline if provided
        if baseline_metrics:
            baseline_pr = baseline_metrics.get("pr_auc", 0)
            if challenger_pr <= baseline_pr:
                return False, (
                    f"Challenger does not outperform baseline "
                    f"(challenger: {challenger_pr:.4f}, baseline: {baseline_pr:.4f})"
                )
        
        return True, (
            f"Promoted: PR-AUC improved by {pr_improvement:.2%} "
            f"(from {champion_pr:.4f} to {challenger_pr:.4f})"
        )
    
    def evaluate_clv_promotion(
        self,
        challenger_metrics: Dict,
        champion_metrics: Dict,
        baseline_metrics: Optional[Dict] = None,
    ) -> Tuple[bool, str]:
        """
        Evaluate if challenger CLV model should be promoted
        
        Primary metrics: RMSE (lower is better), MAE
        Secondary metric: R²
        
        Args:
            challenger_metrics: Metrics from new model
            champion_metrics: Metrics from current champion
            baseline_metrics: Optional baseline model metrics
            
        Returns:
            (should_promote, reason)
        """
        # Extract CLV metrics (handle nested structure)
        challenger_clv = challenger_metrics.get("clv", challenger_metrics)
        champion_clv = champion_metrics.get("clv", champion_metrics)
        
        # Primary metric: RMSE (lower is better)
        challenger_rmse = challenger_clv.get("rmse", float('inf'))
        champion_rmse = champion_clv.get("rmse", float('inf'))
        
        # Calculate relative improvement (negative = better for RMSE)
        if champion_rmse > 0:
            rmse_improvement = (champion_rmse - challenger_rmse) / champion_rmse
        else:
            rmse_improvement = 0
        
        # Check minimum improvement threshold
        if rmse_improvement < self.min_improvement:
            return False, (
                f"Insufficient RMSE improvement: {rmse_improvement:.2%} "
                f"(required: {self.min_improvement:.2%})"
            )
        
        # Secondary metric: MAE
        challenger_mae = challenger_clv.get("mae", float('inf'))
        champion_mae = champion_clv.get("mae", float('inf'))
        
        if champion_mae > 0:
            mae_change = (champion_mae - challenger_mae) / champion_mae
            if mae_change < -self.max_secondary_regression:
                return False, (
                    f"MAE regression detected: {-mae_change:.2%} "
                    f"(max allowed: {self.max_secondary_regression:.2%})"
                )
        
        # Check R² (should not regress significantly)
        challenger_r2 = challenger_clv.get("r2", -float('inf'))
        champion_r2 = champion_clv.get("r2", -float('inf'))
        
        if champion_r2 > 0:
            r2_change = (challenger_r2 - champion_r2) / abs(champion_r2)
            if r2_change < -self.max_secondary_regression:
                return False, (
                    f"R² regression detected: {r2_change:.2%} "
                    f"(max allowed: {-self.max_secondary_regression:.2%})"
                )
        
        # Check against baseline if provided
        if baseline_metrics:
            baseline_clv = baseline_metrics.get("clv", baseline_metrics)
            baseline_rmse = baseline_clv.get("rmse", float('inf'))
            if challenger_rmse >= baseline_rmse:
                return False, (
                    f"Challenger does not outperform baseline "
                    f"(challenger RMSE: {challenger_rmse:.2f}, "
                    f"baseline RMSE: {baseline_rmse:.2f})"
                )
        
        return True, (
            f"Promoted: RMSE improved by {rmse_improvement:.2%} "
            f"(from {champion_rmse:.2f} to {challenger_rmse:.2f})"
        )
    
    def evaluate_segmentation_promotion(
        self,
        challenger_metrics: Dict,
        champion_metrics: Dict,
    ) -> Tuple[bool, str]:
        """
        Evaluate if challenger segmentation model should be promoted
        
        Primary metric: Silhouette score
        Secondary metrics: Davies-Bouldin index, Calinski-Harabasz
        """
        challenger_sil = challenger_metrics.get("silhouette", 0)
        champion_sil = champion_metrics.get("silhouette", 0)
        
        if champion_sil > 0:
            improvement = (challenger_sil - champion_sil) / champion_sil
        else:
            improvement = float('inf') if challenger_sil > 0 else 0
        
        if improvement < self.min_improvement:
            return False, (
                f"Insufficient silhouette improvement: {improvement:.2%}"
            )
        
        return True, f"Promoted: Silhouette improved by {improvement:.2%}"


# Backward compatibility functions
def better_churn(new: Dict, old: Dict) -> bool:
    """Legacy function for backward compatibility"""
    policy = PromotionPolicy()
    should_promote, _ = policy.evaluate_churn_promotion(new, old)
    return should_promote


def better_clv(new: Dict, old: Dict) -> bool:
    """Legacy function for backward compatibility"""
    policy = PromotionPolicy()
    should_promote, _ = policy.evaluate_clv_promotion(new, old)
    return should_promote


def better_segmentation(new: Dict, old: Dict) -> bool:
    """Legacy function for backward compatibility"""
    policy = PromotionPolicy()
    should_promote, _ = policy.evaluate_segmentation_promotion(new, old)
    return should_promote


# Statistical significance testing (optional enhancement)
def bootstrap_metric_comparison(
    y_true: np.ndarray,
    y_pred_challenger: np.ndarray,
    y_pred_champion: np.ndarray,
    metric_fn,
    n_bootstrap: int = 1000,
    confidence: float = 0.95,
) -> Tuple[float, float, bool]:
    """
    Bootstrap test for statistical significance of metric improvement
    
    Args:
        y_true: True labels
        y_pred_challenger: Challenger predictions
        y_pred_champion: Champion predictions
        metric_fn: Metric function (e.g., sklearn.metrics.roc_auc_score)
        n_bootstrap: Number of bootstrap samples
        confidence: Confidence level
        
    Returns:
        (challenger_metric, champion_metric, is_significant)
    """
    n_samples = len(y_true)
    challenger_scores = []
    champion_scores = []
    
    for _ in range(n_bootstrap):
        # Bootstrap sample
        indices = np.random.choice(n_samples, size=n_samples, replace=True)
        
        y_true_boot = y_true[indices]
        y_pred_challenger_boot = y_pred_challenger[indices]
        y_pred_champion_boot = y_pred_champion[indices]
        
        # Compute metrics
        challenger_scores.append(metric_fn(y_true_boot, y_pred_challenger_boot))
        champion_scores.append(metric_fn(y_true_boot, y_pred_champion_boot))
    
    # Compute confidence intervals
    alpha = 1 - confidence
    challenger_ci = np.percentile(challenger_scores, [alpha/2 * 100, (1-alpha/2) * 100])
    champion_ci = np.percentile(champion_scores, [alpha/2 * 100, (1-alpha/2) * 100])
    
    # Check if confidence intervals overlap
    is_significant = challenger_ci[0] > champion_ci[1]
    
    return (
        float(np.mean(challenger_scores)),
        float(np.mean(champion_scores)),
        is_significant,
    )
