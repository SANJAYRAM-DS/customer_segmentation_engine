"""
Comprehensive Evaluation Metrics
Implements Document 7 requirements for:
- Churn metrics: Precision@K, Recall@K, Brier Score
- CLV metrics: MAPE, Revenue-weighted error, Top-decile accuracy
- Calibration metrics
- Segment-level analysis
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from sklearn.metrics import (
    roc_auc_score,
    average_precision_score,
    brier_score_loss,
    mean_absolute_percentage_error,
)


# ============================================================================
# CHURN METRICS (Document 7.1.1)
# ============================================================================

def precision_at_k(y_true: np.ndarray, y_pred_proba: np.ndarray, k: int) -> float:
    """
    Precision @ K: How many of the top K predictions are true positives
    
    Args:
        y_true: True binary labels
        y_pred_proba: Predicted probabilities
        k: Number of top predictions to consider
        
    Returns:
        Precision at K
    """
    # Get indices of top K predictions
    top_k_indices = np.argsort(y_pred_proba)[-k:]
    
    # Count true positives in top K
    true_positives = y_true[top_k_indices].sum()
    
    return true_positives / k


def recall_at_k(y_true: np.ndarray, y_pred_proba: np.ndarray, k: int) -> float:
    """
    Recall @ K: What fraction of all positives are captured in top K
    
    Args:
        y_true: True binary labels
        y_pred_proba: Predicted probabilities
        k: Number of top predictions to consider
        
    Returns:
        Recall at K
    """
    # Get indices of top K predictions
    top_k_indices = np.argsort(y_pred_proba)[-k:]
    
    # Count true positives in top K
    true_positives = y_true[top_k_indices].sum()
    
    # Total actual positives
    total_positives = y_true.sum()
    
    if total_positives == 0:
        return 0.0
    
    return true_positives / total_positives


def evaluate_churn_comprehensive(
    y_true: np.ndarray,
    y_pred_proba: np.ndarray,
    k_values: Optional[List[int]] = None,
) -> Dict:
    """
    Comprehensive churn evaluation metrics
    
    Args:
        y_true: True binary labels
        y_pred_proba: Predicted probabilities
        k_values: List of K values for Precision@K and Recall@K
        
    Returns:
        Dictionary of metrics
    """
    if k_values is None:
        # Default: top 5%, 10%, 20% of customers
        n = len(y_true)
        k_values = [int(n * 0.05), int(n * 0.10), int(n * 0.20)]
    
    metrics = {
        # Ranking metrics
        "roc_auc": float(roc_auc_score(y_true, y_pred_proba)),
        "pr_auc": float(average_precision_score(y_true, y_pred_proba)),
        
        # Calibration metric
        "brier_score": float(brier_score_loss(y_true, y_pred_proba)),
        
        # Business metrics
        "churn_rate": float(y_true.mean()),
        "avg_predicted_prob": float(y_pred_proba.mean()),
    }
    
    # Precision and Recall @ K
    for k in k_values:
        if k > 0 and k <= len(y_true):
            metrics[f"precision_at_{k}"] = float(precision_at_k(y_true, y_pred_proba, k))
            metrics[f"recall_at_{k}"] = float(recall_at_k(y_true, y_pred_proba, k))
    
    return metrics


# ============================================================================
# CLV METRICS (Document 7.1.2)
# ============================================================================

def revenue_weighted_error(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    weights: Optional[np.ndarray] = None,
) -> float:
    """
    Revenue-weighted MAE: Errors weighted by actual revenue
    
    Args:
        y_true: True CLV values
        y_pred: Predicted CLV values
        weights: Optional custom weights (defaults to y_true)
        
    Returns:
        Weighted MAE
    """
    if weights is None:
        weights = y_true
    
    # Avoid division by zero
    total_weight = weights.sum()
    if total_weight == 0:
        return 0.0
    
    weighted_errors = np.abs(y_true - y_pred) * weights
    return float(weighted_errors.sum() / total_weight)


def top_decile_accuracy(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    decile: float = 0.1,
) -> Dict:
    """
    Accuracy metrics for top decile of customers by predicted CLV
    
    Focus on high-value customers as per Document 7.1.2
    
    Args:
        y_true: True CLV values
        y_pred: Predicted CLV values
        decile: Top fraction to analyze (default 10%)
        
    Returns:
        Dictionary with top-decile metrics
    """
    # Get top decile by predicted value
    n_top = int(len(y_pred) * decile)
    top_indices = np.argsort(y_pred)[-n_top:]
    
    y_true_top = y_true[top_indices]
    y_pred_top = y_pred[top_indices]
    
    return {
        f"top_{int(decile*100)}pct_mae": float(np.mean(np.abs(y_true_top - y_pred_top))),
        f"top_{int(decile*100)}pct_mape": float(
            mean_absolute_percentage_error(y_true_top, y_pred_top)
            if (y_true_top != 0).all() else np.nan
        ),
        f"top_{int(decile*100)}pct_total_actual": float(y_true_top.sum()),
        f"top_{int(decile*100)}pct_total_predicted": float(y_pred_top.sum()),
        f"top_{int(decile*100)}pct_capture_rate": float(
            y_true_top.sum() / y_true.sum() if y_true.sum() > 0 else 0
        ),
    }


def evaluate_clv_comprehensive(
    y_true: np.ndarray,
    y_pred: np.ndarray,
) -> Dict:
    """
    Comprehensive CLV evaluation metrics
    
    Args:
        y_true: True CLV values
        y_pred: Predicted CLV values
        
    Returns:
        Dictionary of metrics
    """
    from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
    
    metrics = {
        # Standard regression metrics
        "rmse": float(np.sqrt(mean_squared_error(y_true, y_pred))),
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "r2": float(r2_score(y_true, y_pred)),
        
        # MAPE (with safety check)
        "mape": float(
            mean_absolute_percentage_error(y_true, y_pred)
            if (y_true != 0).all() else np.nan
        ),
        
        # Revenue-weighted error
        "revenue_weighted_mae": revenue_weighted_error(y_true, y_pred),
        
        # Total revenue metrics
        "total_actual": float(y_true.sum()),
        "total_predicted": float(y_pred.sum()),
        "total_error_pct": float(
            abs(y_true.sum() - y_pred.sum()) / y_true.sum() * 100
            if y_true.sum() > 0 else 0
        ),
    }
    
    # Top-decile metrics
    metrics.update(top_decile_accuracy(y_true, y_pred, decile=0.1))
    metrics.update(top_decile_accuracy(y_true, y_pred, decile=0.2))
    
    return metrics


# ============================================================================
# SEGMENT-LEVEL ANALYSIS (Document 7.3)
# ============================================================================

def evaluate_by_segment(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    segments: np.ndarray,
    metric_fn,
    is_classification: bool = False,
) -> Dict:
    """
    Evaluate metrics stratified by customer segment
    
    Args:
        y_true: True labels/values
        y_pred: Predictions (probabilities for classification, values for regression)
        segments: Segment labels for each sample
        metric_fn: Function to compute metrics
        is_classification: Whether this is a classification task
        
    Returns:
        Dictionary with per-segment metrics
    """
    segment_metrics = {}
    
    for segment in np.unique(segments):
        mask = segments == segment
        
        if mask.sum() == 0:
            continue
        
        y_true_seg = y_true[mask]
        y_pred_seg = y_pred[mask]
        
        # Compute metrics for this segment
        if is_classification:
            seg_metrics = metric_fn(y_true_seg, y_pred_seg)
        else:
            seg_metrics = metric_fn(y_true_seg, y_pred_seg)
        
        segment_metrics[f"segment_{segment}"] = {
            "count": int(mask.sum()),
            "metrics": seg_metrics,
        }
    
    return segment_metrics


def evaluate_by_value_tier(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    customer_values: np.ndarray,
    metric_fn,
    n_tiers: int = 4,
) -> Dict:
    """
    Evaluate metrics stratified by customer value tier
    
    Args:
        y_true: True labels/values
        y_pred: Predictions
        customer_values: Historical customer value (e.g., total_spend)
        metric_fn: Function to compute metrics
        n_tiers: Number of value tiers
        
    Returns:
        Dictionary with per-tier metrics
    """
    # Create value tiers using quantiles
    tier_labels = pd.qcut(
        customer_values,
        q=n_tiers,
        labels=[f"tier_{i+1}" for i in range(n_tiers)],
        duplicates='drop'
    )
    
    return evaluate_by_segment(y_true, y_pred, tier_labels, metric_fn)


def evaluate_cold_start_vs_mature(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    tenure_days: np.ndarray,
    metric_fn,
    cold_start_threshold: int = 90,
) -> Dict:
    """
    Separate evaluation for cold-start vs mature customers
    
    Args:
        y_true: True labels/values
        y_pred: Predictions
        tenure_days: Customer tenure in days
        metric_fn: Function to compute metrics
        cold_start_threshold: Days threshold for cold-start (default 90)
        
    Returns:
        Dictionary with cold-start and mature metrics
    """
    cold_start_mask = tenure_days < cold_start_threshold
    mature_mask = ~cold_start_mask
    
    results = {}
    
    if cold_start_mask.sum() > 0:
        results["cold_start"] = {
            "count": int(cold_start_mask.sum()),
            "metrics": metric_fn(y_true[cold_start_mask], y_pred[cold_start_mask]),
        }
    
    if mature_mask.sum() > 0:
        results["mature"] = {
            "count": int(mature_mask.sum()),
            "metrics": metric_fn(y_true[mature_mask], y_pred[mature_mask]),
        }
    
    return results


# ============================================================================
# CALIBRATION ANALYSIS (Document 7.1.1)
# ============================================================================

def compute_calibration_curve(
    y_true: np.ndarray,
    y_pred_proba: np.ndarray,
    n_bins: int = 10,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Compute calibration curve for probability predictions
    
    Args:
        y_true: True binary labels
        y_pred_proba: Predicted probabilities
        n_bins: Number of bins for calibration curve
        
    Returns:
        (bin_edges, observed_frequencies, predicted_probabilities)
    """
    # Create bins
    bin_edges = np.linspace(0, 1, n_bins + 1)
    bin_indices = np.digitize(y_pred_proba, bin_edges[:-1]) - 1
    bin_indices = np.clip(bin_indices, 0, n_bins - 1)
    
    observed_freq = np.zeros(n_bins)
    predicted_prob = np.zeros(n_bins)
    bin_counts = np.zeros(n_bins)
    
    for i in range(n_bins):
        mask = bin_indices == i
        if mask.sum() > 0:
            observed_freq[i] = y_true[mask].mean()
            predicted_prob[i] = y_pred_proba[mask].mean()
            bin_counts[i] = mask.sum()
    
    return bin_edges, observed_freq, predicted_prob


def calibration_metrics(
    y_true: np.ndarray,
    y_pred_proba: np.ndarray,
    n_bins: int = 10,
) -> Dict:
    """
    Compute calibration quality metrics
    
    Args:
        y_true: True binary labels
        y_pred_proba: Predicted probabilities
        n_bins: Number of bins
        
    Returns:
        Dictionary with calibration metrics
    """
    bin_edges, observed, predicted = compute_calibration_curve(
        y_true, y_pred_proba, n_bins
    )
    
    # Expected Calibration Error (ECE)
    bin_indices = np.digitize(y_pred_proba, bin_edges[:-1]) - 1
    bin_indices = np.clip(bin_indices, 0, n_bins - 1)
    
    ece = 0.0
    for i in range(n_bins):
        mask = bin_indices == i
        if mask.sum() > 0:
            bin_accuracy = y_true[mask].mean()
            bin_confidence = y_pred_proba[mask].mean()
            bin_weight = mask.sum() / len(y_true)
            ece += bin_weight * abs(bin_accuracy - bin_confidence)
    
    return {
        "brier_score": float(brier_score_loss(y_true, y_pred_proba)),
        "expected_calibration_error": float(ece),
        "calibration_curve": {
            "bin_edges": bin_edges.tolist(),
            "observed_freq": observed.tolist(),
            "predicted_prob": predicted.tolist(),
        },
    }
