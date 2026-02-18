"""
Evaluation Package
Implements Document 7 requirements for comprehensive model evaluation
"""

from .metrics import (
    evaluate_churn_comprehensive,
    evaluate_clv_comprehensive,
    precision_at_k,
    recall_at_k,
    revenue_weighted_error,
    top_decile_accuracy,
    calibration_metrics,
)

from .report_generator import (
    EvaluationReport,
    generate_evaluation_report,
)

__all__ = [
    "evaluate_churn_comprehensive",
    "evaluate_clv_comprehensive",
    "precision_at_k",
    "recall_at_k",
    "revenue_weighted_error",
    "top_decile_accuracy",
    "calibration_metrics",
    "EvaluationReport",
    "generate_evaluation_report",
]
