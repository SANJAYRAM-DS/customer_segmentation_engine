from pathlib import Path
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
import json
from datetime import datetime, timezone


class FeatureValidator:
    """Validates features against registry specifications and quality thresholds"""
    
    def __init__(self, registry: dict, max_null_rate: float = 0.5):
        """
        Args:
            registry: Feature registry dictionary
            max_null_rate: Maximum allowed null rate (default 50%)
        """
        self.registry = registry
        self.max_null_rate = max_null_rate
        self.validation_results = []
        
    def validate_schema(self, df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """
        Validate that dataframe matches registry schema
        
        Returns:
            (is_valid, list_of_errors)
        """
        errors = []
        expected_features = set(self.registry["features"].keys())
        actual_features = set(df.columns)
        
        # Check for missing features
        missing = expected_features - actual_features
        if missing:
            errors.append(f"Missing features: {sorted(missing)}")
        
        # Check for unexpected features
        extra = actual_features - expected_features
        if extra:
            errors.append(f"Unexpected features: {sorted(extra)}")
        
        # Validate data types
        for feat_name, feat_spec in self.registry["features"].items():
            if feat_name not in df.columns:
                continue
                
            expected_dtype = feat_spec.get("dtype", "")
            actual_dtype = str(df[feat_name].dtype)
            
            # Map expected to actual dtype patterns
            if not self._dtype_matches(expected_dtype, actual_dtype):
                errors.append(
                    f"Feature '{feat_name}': expected dtype '{expected_dtype}', "
                    f"got '{actual_dtype}'"
                )
        
        return len(errors) == 0, errors
    
    def validate_nulls(self, df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """
        Validate null rates against registry specifications
        
        Returns:
            (is_valid, list_of_warnings)
        """
        warnings = []
        
        for feat_name, feat_spec in self.registry["features"].items():
            if feat_name not in df.columns:
                continue
            
            nullable = feat_spec.get("nullable", True)
            null_rate = df[feat_name].isna().mean()
            
            # Check if feature is marked as non-nullable
            if not nullable and null_rate > 0:
                warnings.append(
                    f"Feature '{feat_name}' marked as non-nullable but has "
                    f"{null_rate:.2%} null values"
                )
            
            # Check if null rate exceeds threshold
            if null_rate > self.max_null_rate:
                warnings.append(
                    f"Feature '{feat_name}' has high null rate: {null_rate:.2%} "
                    f"(threshold: {self.max_null_rate:.2%})"
                )
            
            self.validation_results.append({
                "feature": feat_name,
                "null_rate": float(null_rate),
                "nullable": nullable,
                "passed": null_rate <= self.max_null_rate
            })
        
        return len(warnings) == 0, warnings
    
    def validate_ranges(self, df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """
        Validate numeric feature ranges
        
        Returns:
            (is_valid, list_of_warnings)
        """
        warnings = []
        
        for feat_name, feat_spec in self.registry["features"].items():
            if feat_name not in df.columns:
                continue
            
            # Skip non-numeric features
            if not pd.api.types.is_numeric_dtype(df[feat_name]):
                continue
            
            # Check for infinite values
            inf_count = np.isinf(df[feat_name]).sum()
            if inf_count > 0:
                warnings.append(
                    f"Feature '{feat_name}' contains {inf_count} infinite values"
                )
            
            # Check for negative values in features that should be non-negative
            category = feat_spec.get("category", "")
            if category in ["transactional", "behavioral", "lifecycle"]:
                neg_count = (df[feat_name] < 0).sum()
                if neg_count > 0:
                    warnings.append(
                        f"Feature '{feat_name}' ({category}) contains {neg_count} "
                        f"negative values"
                    )
        
        return len(warnings) == 0, warnings
    
    def validate_category_eligibility(
        self, 
        df: pd.DataFrame, 
        model_type: str
    ) -> Tuple[bool, List[str]]:
        """
        Validate that features belong to allowed categories for model type
        
        Args:
            df: Feature dataframe
            model_type: One of 'churn', 'clv', 'segmentation'
            
        Returns:
            (is_valid, list_of_errors)
        """
        errors = []
        
        allowed = set(self.registry.get("allowed_categories", []))
        forbidden = set(self.registry.get("forbidden_categories", []))
        
        for feat_name, feat_spec in self.registry["features"].items():
            if feat_name not in df.columns:
                continue
            
            category = feat_spec.get("category", "")
            
            # Skip identifier and target features
            if category in ["identifier", "target"]:
                continue
            
            # Check if category is forbidden
            if category in forbidden:
                errors.append(
                    f"Feature '{feat_name}' has forbidden category '{category}' "
                    f"for {model_type} model"
                )
            
            # Check if category is allowed
            if allowed and category not in allowed:
                errors.append(
                    f"Feature '{feat_name}' has category '{category}' which is not "
                    f"in allowed categories: {sorted(allowed)}"
                )
        
        return len(errors) == 0, errors
    
    def compute_distribution_stats(self, df: pd.DataFrame) -> Dict:
        """
        Compute distribution statistics for drift detection
        
        Returns:
            Dictionary with statistics per feature
        """
        stats = {}
        
        for feat_name in df.columns:
            if feat_name not in self.registry["features"]:
                continue
            
            feat_stats = {
                "count": int(df[feat_name].count()),
                "null_count": int(df[feat_name].isna().sum()),
                "null_rate": float(df[feat_name].isna().mean()),
            }
            
            # Numeric features
            if pd.api.types.is_numeric_dtype(df[feat_name]):
                feat_stats.update({
                    "mean": float(df[feat_name].mean()),
                    "std": float(df[feat_name].std()),
                    "min": float(df[feat_name].min()),
                    "max": float(df[feat_name].max()),
                    "p25": float(df[feat_name].quantile(0.25)),
                    "p50": float(df[feat_name].quantile(0.50)),
                    "p75": float(df[feat_name].quantile(0.75)),
                    "p95": float(df[feat_name].quantile(0.95)),
                    "p99": float(df[feat_name].quantile(0.99)),
                })
            
            # Categorical features
            else:
                value_counts = df[feat_name].value_counts()
                feat_stats.update({
                    "unique_count": int(df[feat_name].nunique()),
                    "top_values": value_counts.head(10).to_dict(),
                })
            
            stats[feat_name] = feat_stats
        
        return stats
    
    def validate_all(
        self, 
        df: pd.DataFrame, 
        model_type: Optional[str] = None
    ) -> Dict:
        """
        Run all validation checks
        
        Args:
            df: Feature dataframe
            model_type: Optional model type for category eligibility check
            
        Returns:
            Validation report dictionary
        """
        report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "feature_set": self.registry.get("feature_set", "unknown"),
            "version": self.registry.get("version", "unknown"),
            "row_count": len(df),
            "feature_count": len(df.columns),
            "checks": {},
            "passed": True,
        }
        
        # Schema validation
        schema_valid, schema_errors = self.validate_schema(df)
        report["checks"]["schema"] = {
            "passed": schema_valid,
            "errors": schema_errors,
        }
        if not schema_valid:
            report["passed"] = False
        
        # Null validation
        null_valid, null_warnings = self.validate_nulls(df)
        report["checks"]["nulls"] = {
            "passed": null_valid,
            "warnings": null_warnings,
        }
        if not null_valid:
            report["passed"] = False
        
        # Range validation
        range_valid, range_warnings = self.validate_ranges(df)
        report["checks"]["ranges"] = {
            "passed": range_valid,
            "warnings": range_warnings,
        }
        if not range_valid:
            report["passed"] = False
        
        # Category eligibility (if model type provided)
        if model_type:
            cat_valid, cat_errors = self.validate_category_eligibility(df, model_type)
            report["checks"]["category_eligibility"] = {
                "passed": cat_valid,
                "errors": cat_errors,
            }
            if not cat_valid:
                report["passed"] = False
        
        # Distribution stats
        report["distribution_stats"] = self.compute_distribution_stats(df)
        
        return report
    
    @staticmethod
    def _dtype_matches(expected: str, actual: str) -> bool:
        """Check if actual dtype matches expected dtype pattern"""
        # Normalize dtype strings
        expected = expected.lower()
        actual = actual.lower()
        
        # Direct match
        if expected == actual:
            return True
        
        # Pattern matching
        if "int" in expected and "int" in actual:
            return True
        if "float" in expected and "float" in actual:
            return True
        if expected == "bool" and actual in ["bool", "boolean"]:
            return True
        if expected in ["str", "string", "object"] and actual == "object":
            return True
        
        return False


def save_validation_report(report: Dict, output_path: Path) -> None:
    """Save validation report to JSON file"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with output_path.open("w") as f:
        json.dump(report, f, indent=2)
    
    print(f"[INFO] Validation report saved: {output_path}")


def detect_drift(
    current_stats: Dict,
    baseline_stats: Dict,
    threshold: float = 0.2
) -> List[Dict]:
    """
    Detect distribution drift between current and baseline statistics
    
    Args:
        current_stats: Current distribution statistics
        baseline_stats: Baseline distribution statistics
        threshold: Relative change threshold for drift detection (default 20%)
        
    Returns:
        List of drift alerts
    """
    alerts = []
    
    for feat_name, current in current_stats.items():
        if feat_name not in baseline_stats:
            continue
        
        baseline = baseline_stats[feat_name]
        
        # Check null rate drift
        if "null_rate" in current and "null_rate" in baseline:
            null_change = abs(current["null_rate"] - baseline["null_rate"])
            if null_change > threshold:
                alerts.append({
                    "feature": feat_name,
                    "metric": "null_rate",
                    "baseline": baseline["null_rate"],
                    "current": current["null_rate"],
                    "change": null_change,
                })
        
        # Check mean drift for numeric features
        if "mean" in current and "mean" in baseline:
            if baseline["mean"] != 0:
                mean_change = abs(
                    (current["mean"] - baseline["mean"]) / baseline["mean"]
                )
                if mean_change > threshold:
                    alerts.append({
                        "feature": feat_name,
                        "metric": "mean",
                        "baseline": baseline["mean"],
                        "current": current["mean"],
                        "relative_change": mean_change,
                    })
        
        # Check std drift for numeric features
        if "std" in current and "std" in baseline:
            if baseline["std"] != 0:
                std_change = abs(
                    (current["std"] - baseline["std"]) / baseline["std"]
                )
                if std_change > threshold:
                    alerts.append({
                        "feature": feat_name,
                        "metric": "std",
                        "baseline": baseline["std"],
                        "current": current["std"],
                        "relative_change": std_change,
                    })
    
    return alerts