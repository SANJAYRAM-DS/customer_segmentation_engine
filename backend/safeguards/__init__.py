"""
Safeguards Package
Implements Document 13 requirements for failure modes and kill switches
"""

from .kill_switch import (
    KillSwitchManager,
    SafeguardManager,
    KillSwitchScope,
    create_kill_switch_manager,
    emergency_disable_model,
)

__all__ = [
    "KillSwitchManager",
    "SafeguardManager",
    "KillSwitchScope",
    "create_kill_switch_manager",
    "emergency_disable_model",
]
