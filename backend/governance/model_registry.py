"""
Enhanced Model Registry with Governance
Implements Document 14.3: Model Governance
"""

import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional
from enum import Enum


class ApprovalStatus(Enum):
    """Model approval status"""
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    DEPRECATED = "deprecated"


class ModelRegistry:
    """
    Comprehensive model registry with governance
    
    Implements Document 14.3: Model Governance
    """
    
    def __init__(self, registry_path: Path):
        """
        Args:
            registry_path: Path to registry file
        """
        self.registry_path = registry_path
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Load or initialize registry
        if self.registry_path.exists():
            with self.registry_path.open("r") as f:
                self.registry = json.load(f)
        else:
            self.registry = {
                "models": {},
                "approval_history": [],
            }
            self._save()
    
    def register_model(
        self,
        model_id: str,
        model_type: str,
        model_version: str,
        owner: str,
        business_purpose: str,
        training_snapshot_id: str,
        feature_version: str,
        metrics: Dict,
        additional_metadata: Optional[Dict] = None,
    ) -> bool:
        """
        Register a new model
        
        Implements Document 14.3.1: Model Registry
        
        Args:
            model_id: Unique model identifier
            model_type: Type of model
            model_version: Model version
            owner: Named model owner
            business_purpose: Business purpose documentation
            training_snapshot_id: Training data snapshot ID
            feature_version: Feature version
            metrics: Model metrics
            additional_metadata: Additional metadata
            
        Returns:
            True if successful
        """
        if not owner:
            print("[ERROR] Model must have a named owner")
            return False
        
        if not business_purpose:
            print("[ERROR] Business purpose must be documented")
            return False
        
        model_record = {
            "model_id": model_id,
            "model_type": model_type,
            "model_version": model_version,
            "owner": owner,
            "business_purpose": business_purpose,
            "training_snapshot_id": training_snapshot_id,
            "feature_version": feature_version,
            "metrics": metrics,
            "approval_status": ApprovalStatus.DRAFT.value,
            "registered_at": datetime.now(timezone.utc).isoformat(),
            "approved_at": None,
            "approvers": [],
            "deployment_history": [],
            "additional_metadata": additional_metadata or {},
        }
        
        self.registry["models"][model_id] = model_record
        self._save()
        
        print(f"[OK] Model registered: {model_id}")
        print(f"  Owner: {owner}")
        print(f"  Status: {ApprovalStatus.DRAFT.value}")
        
        return True
    
    def request_approval(
        self,
        model_id: str,
        requested_by: str,
        justification: str,
    ) -> bool:
        """
        Request approval for model
        
        Args:
            model_id: Model ID
            requested_by: Who requested approval
            justification: Justification for approval
            
        Returns:
            True if successful
        """
        if model_id not in self.registry["models"]:
            print(f"[ERROR] Model not found: {model_id}")
            return False
        
        model = self.registry["models"][model_id]
        
        if model["approval_status"] != ApprovalStatus.DRAFT.value:
            print(f"[ERROR] Model is not in draft status")
            return False
        
        model["approval_status"] = ApprovalStatus.PENDING_APPROVAL.value
        
        # Log approval request
        self.registry["approval_history"].append({
            "model_id": model_id,
            "action": "approval_requested",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "requested_by": requested_by,
            "justification": justification,
        })
        
        self._save()
        
        print(f"[OK] Approval requested for: {model_id}")
        return True
    
    def approve_model(
        self,
        model_id: str,
        approver: str,
        approval_notes: Optional[str] = None,
    ) -> bool:
        """
        Approve a model for deployment
        
        Implements Document 14.4: Change Approval & Accountability
        
        Args:
            model_id: Model ID
            approver: Named approver
            approval_notes: Optional approval notes
            
        Returns:
            True if successful
        """
        if model_id not in self.registry["models"]:
            print(f"[ERROR] Model not found: {model_id}")
            return False
        
        model = self.registry["models"][model_id]
        
        # Check if model owner is trying to approve their own model
        if model["owner"] == approver:
            print(f"[ERROR] Model owner cannot approve their own model (Separation of Duties)")
            return False
        
        model["approval_status"] = ApprovalStatus.APPROVED.value
        model["approved_at"] = datetime.now(timezone.utc).isoformat()
        model["approvers"].append({
            "approver": approver,
            "approved_at": model["approved_at"],
            "notes": approval_notes,
        })
        
        # Log approval
        self.registry["approval_history"].append({
            "model_id": model_id,
            "action": "approved",
            "timestamp": model["approved_at"],
            "approver": approver,
            "notes": approval_notes,
        })
        
        self._save()
        
        print(f"[OK] Model approved: {model_id}")
        print(f"  Approver: {approver}")
        
        return True
    
    def reject_model(
        self,
        model_id: str,
        rejector: str,
        rejection_reason: str,
    ) -> bool:
        """
        Reject a model
        
        Args:
            model_id: Model ID
            rejector: Who rejected the model
            rejection_reason: Reason for rejection
            
        Returns:
            True if successful
        """
        if model_id not in self.registry["models"]:
            print(f"[ERROR] Model not found: {model_id}")
            return False
        
        model = self.registry["models"][model_id]
        model["approval_status"] = ApprovalStatus.REJECTED.value
        
        # Log rejection
        self.registry["approval_history"].append({
            "model_id": model_id,
            "action": "rejected",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "rejector": rejector,
            "reason": rejection_reason,
        })
        
        self._save()
        
        print(f"[OK] Model rejected: {model_id}")
        print(f"  Reason: {rejection_reason}")
        
        return True
    
    def log_deployment(
        self,
        model_id: str,
        deployment_stage: str,
        deployed_by: str,
        deployment_notes: Optional[str] = None,
    ) -> bool:
        """
        Log model deployment
        
        Implements Document 14.3.2: Auditability & Lineage
        
        Args:
            model_id: Model ID
            deployment_stage: Deployment stage (shadow/canary/production)
            deployed_by: Who deployed the model
            deployment_notes: Optional deployment notes
            
        Returns:
            True if successful
        """
        if model_id not in self.registry["models"]:
            print(f"[ERROR] Model not found: {model_id}")
            return False
        
        model = self.registry["models"][model_id]
        
        # Check if model is approved
        if model["approval_status"] != ApprovalStatus.APPROVED.value:
            print(f"[ERROR] Model must be approved before deployment")
            return False
        
        deployment_record = {
            "stage": deployment_stage,
            "deployed_at": datetime.now(timezone.utc).isoformat(),
            "deployed_by": deployed_by,
            "notes": deployment_notes,
        }
        
        model["deployment_history"].append(deployment_record)
        self._save()
        
        print(f"[OK] Deployment logged: {model_id} → {deployment_stage}")
        
        return True
    
    def deprecate_model(
        self,
        model_id: str,
        deprecated_by: str,
        deprecation_reason: str,
    ) -> bool:
        """
        Deprecate a model
        
        Args:
            model_id: Model ID
            deprecated_by: Who deprecated the model
            deprecation_reason: Reason for deprecation
            
        Returns:
            True if successful
        """
        if model_id not in self.registry["models"]:
            print(f"[ERROR] Model not found: {model_id}")
            return False
        
        model = self.registry["models"][model_id]
        model["approval_status"] = ApprovalStatus.DEPRECATED.value
        model["deprecated_at"] = datetime.now(timezone.utc).isoformat()
        model["deprecated_by"] = deprecated_by
        model["deprecation_reason"] = deprecation_reason
        
        self._save()
        
        print(f"[OK] Model deprecated: {model_id}")
        
        return True
    
    def get_model(self, model_id: str) -> Optional[Dict]:
        """Get model record"""
        return self.registry["models"].get(model_id)
    
    def get_models_by_owner(self, owner: str) -> List[Dict]:
        """Get all models owned by a user"""
        return [
            model for model in self.registry["models"].values()
            if model["owner"] == owner
        ]
    
    def get_models_by_status(self, status: ApprovalStatus) -> List[Dict]:
        """Get all models with a specific status"""
        return [
            model for model in self.registry["models"].values()
            if model["approval_status"] == status.value
        ]
    
    def get_approval_history(
        self,
        model_id: Optional[str] = None,
        limit: int = 20,
    ) -> List[Dict]:
        """
        Get approval history
        
        Args:
            model_id: Optional filter by model ID
            limit: Maximum number of records
            
        Returns:
            List of approval records
        """
        history = self.registry["approval_history"]
        
        if model_id:
            history = [h for h in history if h["model_id"] == model_id]
        
        history = sorted(history, key=lambda x: x["timestamp"], reverse=True)
        
        return history[:limit]
    
    def get_lineage(self, model_id: str) -> Optional[Dict]:
        """
        Get complete lineage for a model
        
        Implements Document 14.3.2: Auditability & Lineage
        
        Args:
            model_id: Model ID
            
        Returns:
            Lineage information
        """
        if model_id not in self.registry["models"]:
            return None
        
        model = self.registry["models"][model_id]
        
        lineage = {
            "model_id": model_id,
            "model_type": model["model_type"],
            "model_version": model["model_version"],
            "owner": model["owner"],
            "data_lineage": {
                "training_snapshot_id": model["training_snapshot_id"],
                "feature_version": model["feature_version"],
            },
            "approval_lineage": {
                "status": model["approval_status"],
                "approved_at": model.get("approved_at"),
                "approvers": model.get("approvers", []),
            },
            "deployment_lineage": model.get("deployment_history", []),
        }
        
        return lineage
    
    def _save(self):
        """Save registry to disk"""
        with self.registry_path.open("w") as f:
            json.dump(self.registry, f, indent=2)
    
    def print_summary(self):
        """Print registry summary"""
        print("\n" + "=" * 60)
        print("MODEL REGISTRY SUMMARY")
        print("=" * 60)
        
        total_models = len(self.registry["models"])
        print(f"\nTotal models: {total_models}")
        
        # Count by status
        for status in ApprovalStatus:
            count = len(self.get_models_by_status(status))
            if count > 0:
                print(f"  {status.value}: {count}")
        
        print("\n" + "=" * 60)


if __name__ == "__main__":
    print("Model Registry with Governance")
    print("Implements Document 14.3 requirements")
    print("\nThis module provides:")
    print("  - Model registration with ownership")
    print("  - Approval workflow")
    print("  - Deployment tracking")
    print("  - Complete lineage")
    print("  - Separation of duties")
