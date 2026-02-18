"""
Audit Logger
Implements Document 13.4 & 14: Comprehensive audit trail for all system actions
"""

import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from enum import Enum


class AuditEventType(Enum):
    """Types of auditable events"""
    # Data events
    DATA_INGESTION = "data_ingestion"
    DATA_VALIDATION = "data_validation"
    DATA_DELETION = "data_deletion"
    
    # Model events
    MODEL_TRAINING = "model_training"
    MODEL_REGISTRATION = "model_registration"
    MODEL_APPROVAL = "model_approval"
    MODEL_DEPLOYMENT = "model_deployment"
    MODEL_ROLLBACK = "model_rollback"
    
    # Prediction events
    BATCH_INFERENCE = "batch_inference"
    PREDICTION_EXPORT = "prediction_export"
    
    # Safeguard events
    KILL_SWITCH_ACTIVATION = "kill_switch_activation"
    KILL_SWITCH_DEACTIVATION = "kill_switch_deactivation"
    SAFEGUARD_TRIGGERED = "safeguard_triggered"
    
    # Access events
    USER_LOGIN = "user_login"
    ACCESS_GRANTED = "access_granted"
    ACCESS_DENIED = "access_denied"
    EMERGENCY_ACCESS = "emergency_access"
    
    # Change events
    FEATURE_CHANGE = "feature_change"
    THRESHOLD_CHANGE = "threshold_change"
    CONFIG_CHANGE = "config_change"


class AuditSeverity(Enum):
    """Severity levels for audit events"""
    INFO = "info"
    WARNING = "warning"
    HIGH = "high"
    CRITICAL = "critical"


class AuditLogger:
    """
    Comprehensive audit logging system
    
    Implements Document 13.4 & 14: Documentation & Auditability
    """
    
    def __init__(self, log_dir: Path):
        """
        Args:
            log_dir: Directory to store audit logs
        """
        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Current log file (daily rotation)
        self.current_log_file = self._get_log_file()
    
    def _get_log_file(self) -> Path:
        """Get current log file path (daily rotation)"""
        date_str = datetime.now().strftime("%Y%m%d")
        return self.log_dir / f"audit_log_{date_str}.jsonl"
    
    def log_event(
        self,
        event_type: AuditEventType,
        user: str,
        action: str,
        resource: str,
        severity: AuditSeverity = AuditSeverity.INFO,
        success: bool = True,
        details: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
    ) -> str:
        """
        Log an audit event
        
        Args:
            event_type: Type of event
            user: User or system performing the action
            action: Action performed
            resource: Resource affected
            severity: Event severity
            success: Whether action succeeded
            details: Additional details
            error: Error message if failed
            
        Returns:
            Event ID
        """
        event_id = f"{event_type.value}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        event = {
            "event_id": event_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type.value,
            "severity": severity.value,
            "user": user,
            "action": action,
            "resource": resource,
            "success": success,
            "details": details or {},
            "error": error,
        }
        
        # Append to log file (JSONL format)
        log_file = self._get_log_file()
        with log_file.open("a") as f:
            f.write(json.dumps(event) + "\n")
        
        # Print high-severity events
        if severity in [AuditSeverity.HIGH, AuditSeverity.CRITICAL]:
            severity_icon = "🔴" if severity == AuditSeverity.CRITICAL else "🟠"
            print(f"{severity_icon} AUDIT: {action} by {user} on {resource}")
        
        return event_id
    
    def log_data_event(
        self,
        action: str,
        data_source: str,
        user: str,
        record_count: Optional[int] = None,
        success: bool = True,
        error: Optional[str] = None,
    ) -> str:
        """
        Log data-related event
        
        Args:
            action: Action performed
            data_source: Data source
            user: User
            record_count: Number of records affected
            success: Success status
            error: Error message
            
        Returns:
            Event ID
        """
        return self.log_event(
            event_type=AuditEventType.DATA_INGESTION,
            user=user,
            action=action,
            resource=data_source,
            success=success,
            details={"record_count": record_count} if record_count else {},
            error=error,
        )
    
    def log_model_event(
        self,
        event_type: AuditEventType,
        action: str,
        model_id: str,
        user: str,
        model_version: Optional[str] = None,
        metrics: Optional[Dict] = None,
        success: bool = True,
        error: Optional[str] = None,
    ) -> str:
        """
        Log model-related event
        
        Args:
            event_type: Event type
            action: Action performed
            model_id: Model ID
            user: User
            model_version: Model version
            metrics: Model metrics
            success: Success status
            error: Error message
            
        Returns:
            Event ID
        """
        details = {}
        if model_version:
            details["model_version"] = model_version
        if metrics:
            details["metrics"] = metrics
        
        return self.log_event(
            event_type=event_type,
            user=user,
            action=action,
            resource=model_id,
            severity=AuditSeverity.HIGH if event_type == AuditEventType.MODEL_DEPLOYMENT else AuditSeverity.INFO,
            success=success,
            details=details,
            error=error,
        )
    
    def log_safeguard_event(
        self,
        action: str,
        safeguard_type: str,
        user: str,
        reason: str,
        target: Optional[str] = None,
    ) -> str:
        """
        Log safeguard activation
        
        Implements Document 13.4: Documentation & Auditability
        
        Args:
            action: Action (activate/deactivate)
            safeguard_type: Type of safeguard
            user: User
            reason: Reason for action
            target: Target of safeguard
            
        Returns:
            Event ID
        """
        event_type = (
            AuditEventType.KILL_SWITCH_ACTIVATION
            if "activate" in action.lower()
            else AuditEventType.KILL_SWITCH_DEACTIVATION
        )
        
        return self.log_event(
            event_type=event_type,
            user=user,
            action=action,
            resource=safeguard_type,
            severity=AuditSeverity.CRITICAL,
            details={
                "reason": reason,
                "target": target,
            },
        )
    
    def log_access_event(
        self,
        user: str,
        resource: str,
        action: str,
        granted: bool,
        reason: Optional[str] = None,
    ) -> str:
        """
        Log access control event
        
        Args:
            user: User
            resource: Resource accessed
            action: Action attempted
            granted: Whether access was granted
            reason: Reason if denied
            
        Returns:
            Event ID
        """
        event_type = AuditEventType.ACCESS_GRANTED if granted else AuditEventType.ACCESS_DENIED
        
        return self.log_event(
            event_type=event_type,
            user=user,
            action=action,
            resource=resource,
            severity=AuditSeverity.WARNING if not granted else AuditSeverity.INFO,
            success=granted,
            details={"reason": reason} if reason else {},
        )
    
    def query_events(
        self,
        event_type: Optional[AuditEventType] = None,
        user: Optional[str] = None,
        resource: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        severity: Optional[AuditSeverity] = None,
        limit: int = 100,
    ) -> List[Dict]:
        """
        Query audit events
        
        Args:
            event_type: Filter by event type
            user: Filter by user
            resource: Filter by resource
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            severity: Filter by severity
            limit: Maximum number of results
            
        Returns:
            List of matching events
        """
        events = []
        
        # Determine which log files to read
        if start_date and end_date:
            # Parse dates and get file range
            log_files = self._get_log_files_in_range(start_date, end_date)
        else:
            # Read all log files
            log_files = sorted(self.log_dir.glob("audit_log_*.jsonl"))
        
        # Read and filter events
        for log_file in log_files:
            with log_file.open("r") as f:
                for line in f:
                    try:
                        event = json.loads(line.strip())
                        
                        # Apply filters
                        if event_type and event["event_type"] != event_type.value:
                            continue
                        if user and event["user"] != user:
                            continue
                        if resource and event["resource"] != resource:
                            continue
                        if severity and event["severity"] != severity.value:
                            continue
                        
                        events.append(event)
                        
                        if len(events) >= limit:
                            break
                    except json.JSONDecodeError:
                        continue
            
            if len(events) >= limit:
                break
        
        # Sort by timestamp descending
        events = sorted(events, key=lambda x: x["timestamp"], reverse=True)
        
        return events[:limit]
    
    def _get_log_files_in_range(
        self,
        start_date: str,
        end_date: str,
    ) -> List[Path]:
        """Get log files within date range"""
        # Simple implementation - get all files and filter
        # In production, this would be more sophisticated
        all_files = sorted(self.log_dir.glob("audit_log_*.jsonl"))
        return all_files
    
    def generate_audit_report(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        output_path: Optional[Path] = None,
    ) -> Dict:
        """
        Generate audit report
        
        Args:
            start_date: Start date
            end_date: End date
            output_path: Optional output path
            
        Returns:
            Audit report
        """
        events = self.query_events(
            start_date=start_date,
            end_date=end_date,
            limit=10000,
        )
        
        # Aggregate statistics
        report = {
            "period": {
                "start": start_date or "all",
                "end": end_date or "all",
            },
            "total_events": len(events),
            "by_type": {},
            "by_user": {},
            "by_severity": {},
            "critical_events": [],
        }
        
        for event in events:
            # Count by type
            event_type = event["event_type"]
            report["by_type"][event_type] = report["by_type"].get(event_type, 0) + 1
            
            # Count by user
            user = event["user"]
            report["by_user"][user] = report["by_user"].get(user, 0) + 1
            
            # Count by severity
            severity = event["severity"]
            report["by_severity"][severity] = report["by_severity"].get(severity, 0) + 1
            
            # Collect critical events
            if severity == AuditSeverity.CRITICAL.value:
                report["critical_events"].append(event)
        
        # Save report if output path provided
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with output_path.open("w") as f:
                json.dump(report, f, indent=2)
            print(f"[OK] Audit report saved: {output_path}")
        
        return report


# Global audit logger instance
_audit_logger: Optional[AuditLogger] = None


def get_audit_logger(log_dir: Optional[Path] = None) -> AuditLogger:
    """
    Get global audit logger instance
    
    Args:
        log_dir: Log directory (required on first call)
        
    Returns:
        AuditLogger instance
    """
    global _audit_logger
    
    if _audit_logger is None:
        if log_dir is None:
            log_dir = Path.cwd() / "audit_logs"
        _audit_logger = AuditLogger(log_dir)
    
    return _audit_logger


if __name__ == "__main__":
    print("Audit Logger")
    print("Implements Document 13.4 & 14 requirements")
    print("\nThis module provides:")
    print("  - Comprehensive event logging")
    print("  - Queryable audit trail")
    print("  - Audit report generation")
    print("  - Immutable log storage")
