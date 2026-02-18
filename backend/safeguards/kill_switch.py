"""
Kill Switch Infrastructure
Implements Document 13.3: Kill Switches for immediate containment of faulty components
"""

import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set
from enum import Enum


class KillSwitchScope(Enum):
    """Scope of kill switch activation"""
    MODEL_VERSION = "model_version"
    MODEL_TYPE = "model_type"
    INFERENCE_ENDPOINT = "inference_endpoint"
    CUSTOMER_SEGMENT = "customer_segment"
    GEOGRAPHIC_REGION = "geographic_region"
    DOWNSTREAM_CONSUMER = "downstream_consumer"


class KillSwitchManager:
    """
    Manages kill switches for system components
    
    Implements Document 13.3: Kill Switches
    """
    
    def __init__(self, config_path: Path):
        """
        Args:
            config_path: Path to kill switch configuration file
        """
        self.config_path = config_path
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Load or initialize configuration
        if self.config_path.exists():
            with self.config_path.open("r") as f:
                self.config = json.load(f)
        else:
            self.config = {
                "kill_switches": {},
                "activation_history": [],
            }
            self._save()
    
    def activate_kill_switch(
        self,
        scope: KillSwitchScope,
        target: str,
        reason: str,
        activated_by: str,
        additional_context: Optional[Dict] = None,
    ) -> str:
        """
        Activate a kill switch
        
        Implements Document 13.3.2: How They Work
        
        Args:
            scope: Scope of kill switch
            target: Target identifier (e.g., model version, segment)
            reason: Reason for activation
            activated_by: Who activated the switch
            additional_context: Additional context
            
        Returns:
            Kill switch ID
        """
        kill_switch_id = f"{scope.value}_{target}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        kill_switch = {
            "id": kill_switch_id,
            "scope": scope.value,
            "target": target,
            "status": "active",
            "reason": reason,
            "activated_by": activated_by,
            "activated_at": datetime.now(timezone.utc).isoformat(),
            "deactivated_at": None,
            "additional_context": additional_context or {},
        }
        
        # Store kill switch
        self.config["kill_switches"][kill_switch_id] = kill_switch
        
        # Log activation
        self.config["activation_history"].append({
            "kill_switch_id": kill_switch_id,
            "action": "activated",
            "timestamp": kill_switch["activated_at"],
            "user": activated_by,
            "reason": reason,
        })
        
        self._save()
        
        print(f"\n🔴 KILL SWITCH ACTIVATED")
        print(f"ID: {kill_switch_id}")
        print(f"Scope: {scope.value}")
        print(f"Target: {target}")
        print(f"Reason: {reason}")
        print(f"Activated by: {activated_by}")
        
        return kill_switch_id
    
    def deactivate_kill_switch(
        self,
        kill_switch_id: str,
        deactivated_by: str,
        recovery_notes: Optional[str] = None,
    ) -> bool:
        """
        Deactivate a kill switch
        
        Implements Document 13.3: Recovery & Re-Enablement
        
        Args:
            kill_switch_id: Kill switch ID
            deactivated_by: Who deactivated the switch
            recovery_notes: Notes about recovery
            
        Returns:
            True if successful
        """
        if kill_switch_id not in self.config["kill_switches"]:
            print(f"[ERROR] Kill switch not found: {kill_switch_id}")
            return False
        
        kill_switch = self.config["kill_switches"][kill_switch_id]
        
        if kill_switch["status"] != "active":
            print(f"[ERROR] Kill switch is not active: {kill_switch_id}")
            return False
        
        # Update status
        kill_switch["status"] = "deactivated"
        kill_switch["deactivated_at"] = datetime.now(timezone.utc).isoformat()
        kill_switch["deactivated_by"] = deactivated_by
        kill_switch["recovery_notes"] = recovery_notes
        
        # Log deactivation
        self.config["activation_history"].append({
            "kill_switch_id": kill_switch_id,
            "action": "deactivated",
            "timestamp": kill_switch["deactivated_at"],
            "user": deactivated_by,
            "recovery_notes": recovery_notes,
        })
        
        self._save()
        
        print(f"\n✅ KILL SWITCH DEACTIVATED")
        print(f"ID: {kill_switch_id}")
        print(f"Deactivated by: {deactivated_by}")
        if recovery_notes:
            print(f"Recovery notes: {recovery_notes}")
        
        return True
    
    def is_blocked(
        self,
        scope: KillSwitchScope,
        target: str,
    ) -> bool:
        """
        Check if a target is blocked by an active kill switch
        
        Args:
            scope: Scope to check
            target: Target identifier
            
        Returns:
            True if blocked
        """
        for kill_switch in self.config["kill_switches"].values():
            if (kill_switch["status"] == "active" and
                kill_switch["scope"] == scope.value and
                kill_switch["target"] == target):
                return True
        
        return False
    
    def get_active_kill_switches(self) -> List[Dict]:
        """
        Get all active kill switches
        
        Returns:
            List of active kill switches
        """
        return [
            ks for ks in self.config["kill_switches"].values()
            if ks["status"] == "active"
        ]
    
    def get_kill_switch_history(
        self,
        limit: int = 20,
    ) -> List[Dict]:
        """
        Get kill switch activation history
        
        Args:
            limit: Maximum number of records
            
        Returns:
            List of activation records
        """
        history = sorted(
            self.config["activation_history"],
            key=lambda x: x["timestamp"],
            reverse=True,
        )
        
        return history[:limit]
    
    def _save(self):
        """Save configuration to disk"""
        with self.config_path.open("w") as f:
            json.dump(self.config, f, indent=2)
    
    def print_status(self):
        """Print current kill switch status"""
        active_switches = self.get_active_kill_switches()
        
        print("\n" + "=" * 60)
        print("KILL SWITCH STATUS")
        print("=" * 60)
        
        if active_switches:
            print(f"\n🔴 {len(active_switches)} ACTIVE KILL SWITCHES:")
            for ks in active_switches:
                print(f"\n  ID: {ks['id']}")
                print(f"  Scope: {ks['scope']}")
                print(f"  Target: {ks['target']}")
                print(f"  Reason: {ks['reason']}")
                print(f"  Activated: {ks['activated_at']}")
                print(f"  By: {ks['activated_by']}")
        else:
            print("\n✅ No active kill switches")
        
        print("\n" + "=" * 60)


class SafeguardManager:
    """
    Manages safeguards and fallback mechanisms
    
    Implements Document 13.2: Safeguards & Fallbacks
    """
    
    def __init__(self, kill_switch_manager: KillSwitchManager):
        """
        Args:
            kill_switch_manager: Kill switch manager instance
        """
        self.kill_switch_manager = kill_switch_manager
        self.last_known_good = {}
    
    def validate_prediction(
        self,
        prediction: float,
        model_type: str,
        customer_id: str,
    ) -> tuple[bool, Optional[float], Optional[str]]:
        """
        Validate and potentially clip predictions
        
        Implements Document 13.2.2: Model Safeguards
        
        Args:
            prediction: Raw prediction value
            model_type: Type of model
            customer_id: Customer ID
            
        Returns:
            (is_valid, clipped_value, reason)
        """
        # Check if model is killed
        if self.kill_switch_manager.is_blocked(
            KillSwitchScope.MODEL_TYPE,
            model_type,
        ):
            return False, None, f"Model type '{model_type}' is disabled by kill switch"
        
        # Clip predictions based on model type
        if model_type == "churn":
            # Churn probability must be in [0, 1]
            if prediction < 0 or prediction > 1:
                clipped = max(0.0, min(1.0, prediction))
                return True, clipped, f"Churn probability clipped: {prediction:.4f} → {clipped:.4f}"
            
        elif model_type == "clv":
            # CLV must be non-negative
            if prediction < 0:
                return True, 0.0, f"Negative CLV clipped to 0: {prediction:.2f}"
            
            # CLV should not exceed reasonable bounds (e.g., $100k)
            max_clv = 100000.0
            if prediction > max_clv:
                return True, max_clv, f"CLV clipped to max: {prediction:.2f} → {max_clv:.2f}"
        
        return True, prediction, None
    
    def get_fallback_prediction(
        self,
        customer_id: str,
        model_type: str,
    ) -> Optional[float]:
        """
        Get last-known-good prediction as fallback
        
        Implements Document 13.2.3: Operational Safeguards
        
        Args:
            customer_id: Customer ID
            model_type: Model type
            
        Returns:
            Last known good prediction or None
        """
        key = f"{model_type}_{customer_id}"
        return self.last_known_good.get(key)
    
    def cache_prediction(
        self,
        customer_id: str,
        model_type: str,
        prediction: float,
    ):
        """
        Cache prediction as last-known-good
        
        Args:
            customer_id: Customer ID
            model_type: Model type
            prediction: Prediction value
        """
        key = f"{model_type}_{customer_id}"
        self.last_known_good[key] = prediction


# Convenience functions

def create_kill_switch_manager(config_dir: Path) -> KillSwitchManager:
    """
    Create kill switch manager
    
    Args:
        config_dir: Configuration directory
        
    Returns:
        KillSwitchManager instance
    """
    config_path = config_dir / "kill_switches.json"
    return KillSwitchManager(config_path)


def emergency_disable_model(
    model_type: str,
    reason: str,
    triggered_by: str,
    config_dir: Path,
) -> str:
    """
    Emergency disable a model type
    
    Args:
        model_type: Model type to disable
        reason: Reason for disabling
        triggered_by: Who triggered the disable
        config_dir: Configuration directory
        
    Returns:
        Kill switch ID
    """
    manager = create_kill_switch_manager(config_dir)
    
    return manager.activate_kill_switch(
        scope=KillSwitchScope.MODEL_TYPE,
        target=model_type,
        reason=reason,
        activated_by=triggered_by,
    )


if __name__ == "__main__":
    print("Kill Switch Infrastructure")
    print("Implements Document 13.3 requirements")
    print("\nThis module provides:")
    print("  - Kill switch activation/deactivation")
    print("  - Scoped kill switches (model, segment, region)")
    print("  - Prediction validation and clipping")
    print("  - Fallback mechanisms")
    print("  - Complete audit trail")
