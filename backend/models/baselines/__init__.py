"""
Baseline Models Package

Provides simple, interpretable baseline models for:
- Churn prediction (rule-based)
- CLV estimation (RFM-based, historical average)

These baselines establish minimum performance bars and serve as
fallbacks during system outages.
"""

from .rule_based_churn import RuleBasedChurnBaseline
from .rfm_clv import RFMCLVBaseline, HistoricalAverageCLV

__all__ = [
    "RuleBasedChurnBaseline",
    "RFMCLVBaseline",
    "HistoricalAverageCLV",
]
