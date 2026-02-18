"""
Training Pipeline Orchestrator
Implements Document 8 requirements for:
- Training orchestration with failure handling
- Data snapshotting
- Lineage tracking
- Reproducibility controls
"""

import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Optional, List
import subprocess


class TrainingRun:
    """
    Tracks a single training run with full lineage and reproducibility
    
    Implements Document 8.2: Reproducibility Controls
    """
    
    def __init__(
        self,
        model_type: str,
        run_id: Optional[str] = None,
        output_dir: Optional[Path] = None,
    ):
        """
        Args:
            model_type: Type of model ('churn', 'clv', 'segmentation')
            run_id: Optional run ID (generated if not provided)
            output_dir: Directory to save run artifacts
        """
        self.model_type = model_type
        self.run_id = run_id or self._generate_run_id()
        self.output_dir = output_dir or Path.cwd() / "training_runs" / self.run_id
        
        self.metadata = {
            "run_id": self.run_id,
            "model_type": model_type,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "status": "initialized",
            "lineage": {},
            "config": {},
            "metrics": {},
        }
    
    @staticmethod
    def _generate_run_id() -> str:
        """Generate unique run ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        random_suffix = hashlib.md5(str(datetime.now().timestamp()).encode()).hexdigest()[:6]
        return f"{timestamp}_{random_suffix}"
    
    def add_data_snapshot(
        self,
        snapshot_id: str,
        data_paths: Dict[str, str],
        data_fingerprints: Dict[str, str],
    ):
        """
        Record data snapshot information
        
        Implements Document 8.2.1: Data Snapshotting
        
        Args:
            snapshot_id: Unique snapshot identifier
            data_paths: Paths to data files
            data_fingerprints: MD5 hashes of data files
        """
        self.metadata["lineage"]["data_snapshot"] = {
            "snapshot_id": snapshot_id,
            "paths": data_paths,
            "fingerprints": data_fingerprints,
            "captured_at": datetime.now(timezone.utc).isoformat(),
        }
    
    def add_feature_version(self, feature_set: str, version: str):
        """
        Record feature version
        
        Implements Document 8.2.2: Feature Version Pinning
        
        Args:
            feature_set: Name of feature set
            version: Feature version
        """
        if "features" not in self.metadata["lineage"]:
            self.metadata["lineage"]["features"] = {}
        
        self.metadata["lineage"]["features"][feature_set] = version
    
    def add_code_version(self, git_commit: Optional[str] = None):
        """
        Record code version
        
        Implements Document 8.2.3: Code Versioning
        
        Args:
            git_commit: Git commit hash (auto-detected if not provided)
        """
        if git_commit is None:
            try:
                result = subprocess.run(
                    ["git", "rev-parse", "HEAD"],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                git_commit = result.stdout.strip()
            except:
                git_commit = "unknown"
        
        self.metadata["lineage"]["code"] = {
            "git_commit": git_commit,
            "recorded_at": datetime.now(timezone.utc).isoformat(),
        }
    
    def add_config(self, config: Dict):
        """
        Record training configuration
        
        Implements Document 8.2.3: Hyperparameters
        
        Args:
            config: Training configuration dictionary
        """
        self.metadata["config"] = config
    
    def add_metrics(self, metrics: Dict, dataset: str = "validation"):
        """
        Record evaluation metrics
        
        Args:
            metrics: Metrics dictionary
            dataset: Dataset name
        """
        if "metrics" not in self.metadata:
            self.metadata["metrics"] = {}
        
        self.metadata["metrics"][dataset] = metrics
    
    def add_model_artifact(self, model_path: Path, model_version: int):
        """
        Record model artifact location
        
        Args:
            model_path: Path to saved model
            model_version: Model version number
        """
        self.metadata["model"] = {
            "path": str(model_path),
            "version": model_version,
            "saved_at": datetime.now(timezone.utc).isoformat(),
        }
    
    def mark_success(self):
        """Mark training run as successful"""
        self.metadata["status"] = "success"
        self.metadata["completed_at"] = datetime.now(timezone.utc).isoformat()
    
    def mark_failure(self, error: str):
        """
        Mark training run as failed
        
        Args:
            error: Error message
        """
        self.metadata["status"] = "failed"
        self.metadata["error"] = error
        self.metadata["completed_at"] = datetime.now(timezone.utc).isoformat()
    
    def save(self) -> Path:
        """
        Save training run metadata
        
        Returns:
            Path to saved metadata file
        """
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        metadata_path = self.output_dir / "training_run.json"
        with metadata_path.open("w") as f:
            json.dump(self.metadata, f, indent=2)
        
        return metadata_path


class TrainingPipeline:
    """
    Orchestrates model training with failure handling and lineage tracking
    
    Implements Document 8.4: Pipeline Structure
    """
    
    def __init__(
        self,
        model_type: str,
        config: Dict,
        enable_snapshotting: bool = True,
    ):
        """
        Args:
            model_type: Type of model
            config: Training configuration
            enable_snapshotting: Whether to snapshot data
        """
        self.model_type = model_type
        self.config = config
        self.enable_snapshotting = enable_snapshotting
        
        # Initialize training run
        self.run = TrainingRun(model_type)
        self.run.add_config(config)
        self.run.add_code_version()
    
    def snapshot_data(self, data_paths: Dict[str, Path]) -> str:
        """
        Create immutable data snapshot
        
        Implements Document 8.2.1: Data Snapshotting
        
        Args:
            data_paths: Dictionary of data file paths
            
        Returns:
            Snapshot ID
        """
        snapshot_id = f"snapshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Compute fingerprints
        fingerprints = {}
        for name, path in data_paths.items():
            if path.exists():
                with path.open("rb") as f:
                    fingerprints[name] = hashlib.md5(f.read()).hexdigest()
        
        # Record snapshot
        self.run.add_data_snapshot(
            snapshot_id=snapshot_id,
            data_paths={k: str(v) for k, v in data_paths.items()},
            data_fingerprints=fingerprints,
        )
        
        return snapshot_id
    
    def execute_stage(
        self,
        stage_name: str,
        stage_fn,
        *args,
        **kwargs,
    ) -> any:
        """
        Execute a pipeline stage with error handling
        
        Implements Document 8.4.2: Failure Handling
        
        Args:
            stage_name: Name of stage
            stage_fn: Function to execute
            *args, **kwargs: Arguments to stage function
            
        Returns:
            Stage output
            
        Raises:
            Exception if stage fails
        """
        print(f"[STAGE] {stage_name} - Starting...")
        
        try:
            result = stage_fn(*args, **kwargs)
            print(f"[STAGE] {stage_name} - Completed ✓")
            return result
            
        except Exception as e:
            print(f"[STAGE] {stage_name} - Failed ✗")
            print(f"[ERROR] {e}")
            
            # Mark run as failed
            self.run.mark_failure(f"Stage '{stage_name}' failed: {str(e)}")
            self.run.save()
            
            raise
    
    def run_pipeline(
        self,
        data_paths: Dict[str, Path],
        training_fn,
        evaluation_fn,
    ) -> Dict:
        """
        Run complete training pipeline
        
        Implements Document 8.4.1: Pipeline Stages
        
        Args:
            data_paths: Paths to input data
            training_fn: Function to train model
            evaluation_fn: Function to evaluate model
            
        Returns:
            Pipeline results
        """
        try:
            # Stage 1: Data Snapshotting
            if self.enable_snapshotting:
                snapshot_id = self.execute_stage(
                    "data_snapshot",
                    self.snapshot_data,
                    data_paths,
                )
            
            # Stage 2: Feature Version Pinning
            self.run.add_feature_version(self.model_type, "v1")
            
            # Stage 3: Model Training
            model_artifact, model_version = self.execute_stage(
                "model_training",
                training_fn,
                self.config,
            )
            
            # Stage 4: Evaluation
            metrics = self.execute_stage(
                "evaluation",
                evaluation_fn,
                model_artifact,
            )
            
            # Record results
            self.run.add_metrics(metrics)
            self.run.add_model_artifact(
                Path(f"model_v{model_version}.joblib"),
                model_version,
            )
            
            # Mark success
            self.run.mark_success()
            metadata_path = self.run.save()
            
            print(f"\n[OK] Training pipeline completed successfully")
            print(f"[INFO] Run ID: {self.run.run_id}")
            print(f"[INFO] Metadata: {metadata_path}")
            
            return {
                "run_id": self.run.run_id,
                "model_version": model_version,
                "metrics": metrics,
                "metadata_path": metadata_path,
            }
            
        except Exception as e:
            print(f"\n[ERROR] Training pipeline failed: {e}")
            raise


def create_training_config(model_type: str) -> Dict:
    """
    Create default training configuration
    
    Args:
        model_type: Type of model
        
    Returns:
        Configuration dictionary
    """
    configs = {
        "churn": {
            "model_name": "churn_logistic",
            "random_state": 42,
            "calibrate": True,
            "temporal_split_ratio": 0.8,
        },
        "clv": {
            "model_name": "clv_two_stage",
            "random_state": 42,
            "n_estimators": 300,
            "learning_rate": 0.05,
        },
        "segmentation": {
            "model_name": "customer_segmentation",
            "n_clusters": 4,
            "random_state": 42,
        },
    }
    
    return configs.get(model_type, {})


if __name__ == "__main__":
    # Example usage
    print("Training Pipeline Orchestrator")
    print("Implements Document 8 requirements")
    print("\nThis module provides:")
    print("  - Data snapshotting")
    print("  - Lineage tracking")
    print("  - Failure handling")
    print("  - Reproducibility controls")