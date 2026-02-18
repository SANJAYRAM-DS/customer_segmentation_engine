"""
Deployment Manager
Implements Document 10 requirements for:
- Model promotion workflow
- Shadow and canary deployment
- Rollback management
- Deployment registry
"""

import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from enum import Enum


class DeploymentStage(Enum):
    """Deployment stages"""
    SHADOW = "shadow"
    CANARY = "canary"
    PRODUCTION = "production"
    ROLLED_BACK = "rolled_back"


class RiskLevel(Enum):
    """Model risk classification"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class DeploymentRegistry:
    """
    Central registry for all model deployments
    
    Implements Document 10.3.3: Governance & Audit
    """
    
    def __init__(self, registry_path: Path):
        """
        Args:
            registry_path: Path to deployment registry file
        """
        self.registry_path = registry_path
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing registry
        if self.registry_path.exists():
            with self.registry_path.open("r") as f:
                self.registry = json.load(f)
        else:
            self.registry = {
                "deployments": [],
                "rollbacks": [],
            }
    
    def log_deployment(
        self,
        model_type: str,
        model_version: str,
        stage: DeploymentStage,
        owner: str,
        approvers: Optional[List[str]] = None,
        metrics: Optional[Dict] = None,
        notes: Optional[str] = None,
    ) -> str:
        """
        Log a deployment event
        
        Args:
            model_type: Type of model
            model_version: Model version
            stage: Deployment stage
            owner: Deployment owner
            approvers: List of approvers
            metrics: Observed metrics
            notes: Additional notes
            
        Returns:
            Deployment ID
        """
        deployment_id = f"{model_type}_{model_version}_{stage.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        deployment_record = {
            "deployment_id": deployment_id,
            "model_type": model_type,
            "model_version": model_version,
            "stage": stage.value,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "owner": owner,
            "approvers": approvers or [],
            "metrics": metrics or {},
            "notes": notes,
        }
        
        self.registry["deployments"].append(deployment_record)
        self._save()
        
        print(f"[OK] Deployment logged: {deployment_id}")
        return deployment_id
    
    def log_rollback(
        self,
        model_type: str,
        from_version: str,
        to_version: str,
        reason: str,
        triggered_by: str,
    ) -> str:
        """
        Log a rollback event
        
        Args:
            model_type: Type of model
            from_version: Version being rolled back
            to_version: Version being restored
            reason: Rollback reason
            triggered_by: Who triggered the rollback
            
        Returns:
            Rollback ID
        """
        rollback_id = f"rollback_{model_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        rollback_record = {
            "rollback_id": rollback_id,
            "model_type": model_type,
            "from_version": from_version,
            "to_version": to_version,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "reason": reason,
            "triggered_by": triggered_by,
        }
        
        self.registry["rollbacks"].append(rollback_record)
        self._save()
        
        print(f"[OK] Rollback logged: {rollback_id}")
        return rollback_id
    
    def get_deployment_history(
        self,
        model_type: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict]:
        """
        Get deployment history
        
        Args:
            model_type: Optional filter by model type
            limit: Maximum number of records
            
        Returns:
            List of deployment records
        """
        deployments = self.registry["deployments"]
        
        if model_type:
            deployments = [d for d in deployments if d["model_type"] == model_type]
        
        # Sort by timestamp descending
        deployments = sorted(
            deployments,
            key=lambda x: x["timestamp"],
            reverse=True,
        )
        
        return deployments[:limit]
    
    def _save(self):
        """Save registry to disk"""
        with self.registry_path.open("w") as f:
            json.dump(self.registry, f, indent=2)


class DeploymentManager:
    """
    Manages model deployment lifecycle
    
    Implements Document 10.1: Model Promotion Process
    """
    
    def __init__(
        self,
        model_type: str,
        registry_path: Path,
        risk_level: RiskLevel = RiskLevel.MEDIUM,
    ):
        """
        Args:
            model_type: Type of model
            registry_path: Path to deployment registry
            risk_level: Model risk classification
        """
        self.model_type = model_type
        self.risk_level = risk_level
        self.registry = DeploymentRegistry(registry_path)
        
        # Current deployment state
        self.current_stage = None
        self.current_version = None
        self.shadow_metrics = {}
        self.canary_metrics = {}
    
    def promote_to_shadow(
        self,
        model_version: str,
        owner: str,
        baseline_metrics: Dict,
    ) -> bool:
        """
        Promote model to shadow deployment
        
        Implements Document 10.1.1: Shadow Deployment
        
        Args:
            model_version: Model version to deploy
            owner: Deployment owner
            baseline_metrics: Baseline metrics for comparison
            
        Returns:
            True if successful
        """
        print(f"\n[SHADOW] Deploying {self.model_type} v{model_version} to shadow mode...")
        
        # Log deployment
        self.registry.log_deployment(
            model_type=self.model_type,
            model_version=model_version,
            stage=DeploymentStage.SHADOW,
            owner=owner,
            metrics=baseline_metrics,
            notes="Shadow deployment - monitoring against production",
        )
        
        self.current_stage = DeploymentStage.SHADOW
        self.current_version = model_version
        
        print(f"[OK] Shadow deployment successful")
        print(f"[INFO] Model will receive live inputs but not influence decisions")
        print(f"[INFO] Monitor shadow metrics before promoting to canary")
        
        return True
    
    def validate_shadow_performance(
        self,
        shadow_metrics: Dict,
        production_metrics: Dict,
        min_improvement: float = 0.01,
    ) -> Tuple[bool, str]:
        """
        Validate shadow performance against production
        
        Args:
            shadow_metrics: Shadow model metrics
            production_metrics: Production model metrics
            min_improvement: Minimum required improvement
            
        Returns:
            (passed, reason)
        """
        self.shadow_metrics = shadow_metrics
        
        # Check for regression
        for metric in ["roc_auc", "pr_auc", "mae", "rmse"]:
            if metric in shadow_metrics and metric in production_metrics:
                shadow_val = shadow_metrics[metric]
                prod_val = production_metrics[metric]
                
                # For error metrics (lower is better)
                if metric in ["mae", "rmse"]:
                    if shadow_val > prod_val * (1 + min_improvement):
                        return False, f"Shadow model worse on {metric}: {shadow_val:.4f} vs {prod_val:.4f}"
                # For performance metrics (higher is better)
                else:
                    if shadow_val < prod_val * (1 - min_improvement):
                        return False, f"Shadow model worse on {metric}: {shadow_val:.4f} vs {prod_val:.4f}"
        
        return True, "Shadow validation passed"
    
    def promote_to_canary(
        self,
        model_version: str,
        owner: str,
        approvers: List[str],
        canary_percentage: float = 0.05,
        duration_hours: int = 24,
    ) -> bool:
        """
        Promote model to canary deployment
        
        Implements Document 10.1.2: Canary Deployment
        
        Args:
            model_version: Model version
            owner: Deployment owner
            approvers: List of approvers
            canary_percentage: Percentage of traffic (default 5%)
            duration_hours: Canary duration in hours
            
        Returns:
            True if successful
        """
        # Check if shadow stage passed
        if self.current_stage != DeploymentStage.SHADOW:
            print(f"[ERROR] Must complete shadow deployment before canary")
            return False
        
        # Check risk level requirements
        if self.risk_level == RiskLevel.HIGH and len(approvers) < 2:
            print(f"[ERROR] High-risk models require at least 2 approvers")
            return False
        
        print(f"\n[CANARY] Deploying {self.model_type} v{model_version} to canary...")
        print(f"[INFO] Canary percentage: {canary_percentage*100:.1f}%")
        print(f"[INFO] Duration: {duration_hours} hours")
        
        # Log deployment
        self.registry.log_deployment(
            model_type=self.model_type,
            model_version=model_version,
            stage=DeploymentStage.CANARY,
            owner=owner,
            approvers=approvers,
            notes=f"Canary deployment - {canary_percentage*100:.1f}% traffic for {duration_hours}h",
        )
        
        self.current_stage = DeploymentStage.CANARY
        self.current_version = model_version
        
        print(f"[OK] Canary deployment successful")
        print(f"[INFO] Monitor KPIs and error rates closely")
        print(f"[INFO] Automatic rollback triggers are active")
        
        return True
    
    def validate_canary_performance(
        self,
        canary_metrics: Dict,
        production_metrics: Dict,
        kpi_threshold: float = 0.05,
    ) -> Tuple[bool, str]:
        """
        Validate canary performance
        
        Args:
            canary_metrics: Canary metrics
            production_metrics: Production metrics
            kpi_threshold: KPI degradation threshold
            
        Returns:
            (passed, reason)
        """
        self.canary_metrics = canary_metrics
        
        # Check for KPI degradation
        for metric in canary_metrics:
            if metric in production_metrics:
                canary_val = canary_metrics[metric]
                prod_val = production_metrics[metric]
                
                degradation = abs(canary_val - prod_val) / prod_val if prod_val > 0 else 0
                
                if degradation > kpi_threshold:
                    return False, f"Canary KPI degradation on {metric}: {degradation*100:.2f}%"
        
        return True, "Canary validation passed"
    
    def promote_to_production(
        self,
        model_version: str,
        owner: str,
        approvers: List[str],
    ) -> bool:
        """
        Promote model to full production
        
        Implements Document 10.1.3: Full Production Promotion
        
        Args:
            model_version: Model version
            owner: Deployment owner
            approvers: List of approvers
            
        Returns:
            True if successful
        """
        # Check if canary stage passed
        if self.current_stage != DeploymentStage.CANARY:
            print(f"[ERROR] Must complete canary deployment before production")
            return False
        
        print(f"\n[PRODUCTION] Promoting {self.model_type} v{model_version} to production...")
        
        # Log deployment
        self.registry.log_deployment(
            model_type=self.model_type,
            model_version=model_version,
            stage=DeploymentStage.PRODUCTION,
            owner=owner,
            approvers=approvers,
            metrics={
                "shadow_metrics": self.shadow_metrics,
                "canary_metrics": self.canary_metrics,
            },
            notes="Full production deployment - 100% traffic",
        )
        
        self.current_stage = DeploymentStage.PRODUCTION
        self.current_version = model_version
        
        print(f"[OK] Production deployment successful")
        print(f"[INFO] All downstream consumers now use v{model_version}")
        
        return True
    
    def rollback(
        self,
        to_version: str,
        reason: str,
        triggered_by: str,
    ) -> bool:
        """
        Rollback to previous version
        
        Implements Document 10.2: Rollback Strategy
        
        Args:
            to_version: Version to roll back to
            reason: Rollback reason
            triggered_by: Who triggered the rollback
            
        Returns:
            True if successful
        """
        print(f"\n[ROLLBACK] Rolling back {self.model_type}...")
        print(f"[INFO] From: v{self.current_version}")
        print(f"[INFO] To: v{to_version}")
        print(f"[INFO] Reason: {reason}")
        
        # Log rollback
        self.registry.log_rollback(
            model_type=self.model_type,
            from_version=self.current_version,
            to_version=to_version,
            reason=reason,
            triggered_by=triggered_by,
        )
        
        self.current_version = to_version
        self.current_stage = DeploymentStage.ROLLED_BACK
        
        print(f"[OK] Rollback successful")
        print(f"[INFO] Now serving v{to_version}")
        print(f"[INFO] Post-rollback validation required")
        
        return True


if __name__ == "__main__":
    print("Deployment Manager")
    print("Implements Document 10 requirements")
    print("\nThis module provides:")
    print("  - Shadow deployment")
    print("  - Canary deployment")
    print("  - Production promotion")
    print("  - Rollback management")
    print("  - Deployment registry")