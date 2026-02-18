"""
Explainability Package
Implements Document 12 requirements for model explanations and trust
"""

from .shap_explainer import (
    SHAPExplainer,
    ReasonCodeGenerator,
    ExplanationStore,
    generate_explanations,
)

__all__ = [
    "SHAPExplainer",
    "ReasonCodeGenerator",
    "ExplanationStore",
    "generate_explanations",
]
