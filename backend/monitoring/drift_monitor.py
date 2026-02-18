"""
Comprehensive Drift Monitoring System
Implements Document 11 requirements for:
- Feature-level drift detection (PSI, KS, JS divergence)
- Data quality monitoring
- Automated alerting
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from scipy import stats
from scipy.spatial.distance import jensenshannon
import json
from pathlib import Path
from datetime import datetime, timezone


class DriftMonitor:
    """
    Monitors data drift at feature level
    
    Implements Document 11.1: Data Drift Monitoring
    """
    
    def __init__(
        self,
        reference_data: pd.DataFrame,
        feature_names: List[str],
        categorical_features: Optional[List[str]] = None,
        psi_threshold: float = 0.1,
        ks_threshold: float = 0.1,
        js_threshold: float = 0.1,
    ):
        """
        Args:
            reference_data: Baseline/reference dataset
            feature_names: List of features to monitor
            categorical_features: List of categorical feature names
            psi_threshold: PSI alert threshold (default 0.1)
            ks_threshold: KS statistic alert threshold
            js_threshold: Jensen-Shannon divergence threshold
        """
        self.reference_data = reference_data[feature_names]
        self.feature_names = feature_names
        self.categorical_features = categorical_features or []
        self.psi_threshold = psi_threshold
        self.ks_threshold = ks_threshold
        self.js_threshold = js_threshold
        
        # Compute reference statistics
        self.reference_stats = self._compute_reference_stats()
    
    def _compute_reference_stats(self) -> Dict:
        """Compute reference statistics for all features"""
        stats = {}
        
        for feature in self.feature_names:
            if feature in self.categorical_features:
                # Categorical: value counts
                value_counts = self.reference_data[feature].value_counts(normalize=True)
                stats[feature] = {
                    "type": "categorical",
                    "distribution": value_counts.to_dict(),
                }
            else:
                # Numerical: quantiles for PSI
                values = self.reference_data[feature].dropna()
                stats[feature] = {
                    "type": "numerical",
                    "mean": float(values.mean()),
                    "std": float(values.std()),
                    "quantiles": values.quantile([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]).to_dict(),
                }
        
        return stats
    
    def calculate_psi(
        self,
        reference: np.ndarray,
        current: np.ndarray,
        bins: int = 10,
    ) -> float:
        """
        Calculate Population Stability Index (PSI)
        
        PSI = Σ (current% - reference%) * ln(current% / reference%)
        
        Args:
            reference: Reference distribution
            current: Current distribution
            bins: Number of bins for discretization
            
        Returns:
            PSI value
        """
        # Remove NaN values
        reference = reference[~np.isnan(reference)]
        current = current[~np.isnan(current)]
        
        if len(reference) == 0 or len(current) == 0:
            return np.nan
        
        # Create bins based on reference distribution
        breakpoints = np.percentile(reference, np.linspace(0, 100, bins + 1))
        breakpoints = np.unique(breakpoints)  # Remove duplicates
        
        if len(breakpoints) < 2:
            return 0.0
        
        # Bin both distributions
        ref_binned = np.histogram(reference, bins=breakpoints)[0]
        cur_binned = np.histogram(current, bins=breakpoints)[0]
        
        # Convert to proportions
        ref_prop = ref_binned / len(reference)
        cur_prop = cur_binned / len(current)
        
        # Avoid division by zero
        ref_prop = np.where(ref_prop == 0, 0.0001, ref_prop)
        cur_prop = np.where(cur_prop == 0, 0.0001, cur_prop)
        
        # Calculate PSI
        psi = np.sum((cur_prop - ref_prop) * np.log(cur_prop / ref_prop))
        
        return float(psi)
    
    def calculate_ks_statistic(
        self,
        reference: np.ndarray,
        current: np.ndarray,
    ) -> Tuple[float, float]:
        """
        Calculate Kolmogorov-Smirnov statistic
        
        Args:
            reference: Reference distribution
            current: Current distribution
            
        Returns:
            (KS statistic, p-value)
        """
        reference = reference[~np.isnan(reference)]
        current = current[~np.isnan(current)]
        
        if len(reference) == 0 or len(current) == 0:
            return np.nan, np.nan
        
        ks_stat, p_value = stats.ks_2samp(reference, current)
        return float(ks_stat), float(p_value)
    
    def calculate_js_divergence(
        self,
        reference_dist: Dict,
        current_dist: Dict,
    ) -> float:
        """
        Calculate Jensen-Shannon divergence for categorical features
        
        Args:
            reference_dist: Reference category distribution
            current_dist: Current category distribution
            
        Returns:
            JS divergence
        """
        # Get all categories
        all_categories = set(reference_dist.keys()) | set(current_dist.keys())
        
        # Create probability vectors
        ref_probs = np.array([reference_dist.get(cat, 0.0001) for cat in all_categories])
        cur_probs = np.array([current_dist.get(cat, 0.0001) for cat in all_categories])
        
        # Normalize
        ref_probs = ref_probs / ref_probs.sum()
        cur_probs = cur_probs / cur_probs.sum()
        
        # Calculate JS divergence
        js_div = jensenshannon(ref_probs, cur_probs)
        
        return float(js_div)
    
    def detect_drift(self, current_data: pd.DataFrame) -> Dict:
        """
        Detect drift in current data compared to reference
        
        Implements Document 11.1.2: Drift Metrics
        
        Args:
            current_data: Current dataset to check for drift
            
        Returns:
            Dictionary with drift metrics and alerts
        """
        drift_report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "features": {},
            "alerts": [],
            "summary": {
                "total_features": len(self.feature_names),
                "drifted_features": 0,
            },
        }
        
        for feature in self.feature_names:
            if feature not in current_data.columns:
                drift_report["alerts"].append({
                    "feature": feature,
                    "severity": "critical",
                    "message": f"Feature '{feature}' missing from current data",
                })
                continue
            
            feature_stats = self.reference_stats[feature]
            current_values = current_data[feature]
            
            if feature_stats["type"] == "categorical":
                # Categorical drift: JS divergence
                current_dist = current_values.value_counts(normalize=True).to_dict()
                js_div = self.calculate_js_divergence(
                    feature_stats["distribution"],
                    current_dist,
                )
                
                drift_report["features"][feature] = {
                    "type": "categorical",
                    "js_divergence": js_div,
                    "drifted": js_div > self.js_threshold,
                }
                
                if js_div > self.js_threshold:
                    drift_report["alerts"].append({
                        "feature": feature,
                        "severity": "high",
                        "metric": "js_divergence",
                        "value": js_div,
                        "threshold": self.js_threshold,
                        "message": f"Categorical drift detected in '{feature}'",
                    })
                    drift_report["summary"]["drifted_features"] += 1
            
            else:
                # Numerical drift: PSI and KS
                reference_values = self.reference_data[feature].dropna().values
                current_values_clean = current_values.dropna().values
                
                psi = self.calculate_psi(reference_values, current_values_clean)
                ks_stat, ks_pval = self.calculate_ks_statistic(reference_values, current_values_clean)
                
                drift_report["features"][feature] = {
                    "type": "numerical",
                    "psi": psi,
                    "ks_statistic": ks_stat,
                    "ks_pvalue": ks_pval,
                    "drifted": psi > self.psi_threshold or ks_stat > self.ks_threshold,
                }
                
                # PSI alert
                if psi > self.psi_threshold:
                    drift_report["alerts"].append({
                        "feature": feature,
                        "severity": "high" if psi > 0.2 else "medium",
                        "metric": "psi",
                        "value": psi,
                        "threshold": self.psi_threshold,
                        "message": f"PSI drift detected in '{feature}'",
                    })
                    drift_report["summary"]["drifted_features"] += 1
                
                # KS alert
                if ks_stat > self.ks_threshold:
                    drift_report["alerts"].append({
                        "feature": feature,
                        "severity": "medium",
                        "metric": "ks_statistic",
                        "value": ks_stat,
                        "threshold": self.ks_threshold,
                        "message": f"KS drift detected in '{feature}'",
                    })
        
        return drift_report
    
    def check_missingness(self, current_data: pd.DataFrame) -> Dict:
        """
        Check for sudden changes in missing values
        
        Implements Document 11.1.2: Missingness changes
        
        Args:
            current_data: Current dataset
            
        Returns:
            Missingness report
        """
        report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "features": {},
            "alerts": [],
        }
        
        for feature in self.feature_names:
            if feature not in current_data.columns:
                continue
            
            ref_null_rate = self.reference_data[feature].isnull().mean()
            cur_null_rate = current_data[feature].isnull().mean()
            
            null_rate_change = abs(cur_null_rate - ref_null_rate)
            
            report["features"][feature] = {
                "reference_null_rate": float(ref_null_rate),
                "current_null_rate": float(cur_null_rate),
                "change": float(null_rate_change),
            }
            
            # Alert if null rate increases by more than 10%
            if null_rate_change > 0.1:
                report["alerts"].append({
                    "feature": feature,
                    "severity": "high",
                    "message": f"Missingness surge in '{feature}': {ref_null_rate:.2%} → {cur_null_rate:.2%}",
                    "reference_null_rate": float(ref_null_rate),
                    "current_null_rate": float(cur_null_rate),
                })
        
        return report
    
    def save_report(self, report: Dict, output_path: Path):
        """Save drift report to JSON file"""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with output_path.open("w") as f:
            json.dump(report, f, indent=2)
        
        print(f"[OK] Drift report saved: {output_path}")
    
    def print_summary(self, drift_report: Dict):
        """Print human-readable drift summary"""
        print("\n" + "=" * 60)
        print("DRIFT DETECTION SUMMARY")
        print("=" * 60)
        print(f"Timestamp: {drift_report['timestamp']}")
        print(f"Total features monitored: {drift_report['summary']['total_features']}")
        print(f"Features with drift: {drift_report['summary']['drifted_features']}")
        
        if drift_report["alerts"]:
            print(f"\n⚠️  {len(drift_report['alerts'])} ALERTS:")
            for alert in drift_report["alerts"]:
                severity_icon = "🔴" if alert["severity"] == "critical" else "🟠" if alert["severity"] == "high" else "🟡"
                print(f"  {severity_icon} {alert['message']}")
                if "value" in alert:
                    print(f"     Value: {alert['value']:.4f}, Threshold: {alert['threshold']:.4f}")
        else:
            print("\n✅ No drift detected")
        
        print("=" * 60)


def monitor_drift(
    reference_data_path: Path,
    current_data_path: Path,
    feature_names: List[str],
    categorical_features: Optional[List[str]] = None,
    output_dir: Optional[Path] = None,
) -> Dict:
    """
    Convenience function to monitor drift
    
    Args:
        reference_data_path: Path to reference dataset
        current_data_path: Path to current dataset
        feature_names: Features to monitor
        categorical_features: Categorical feature names
        output_dir: Directory to save reports
        
    Returns:
        Drift report
    """
    # Load data
    reference_data = pd.read_parquet(reference_data_path)
    current_data = pd.read_parquet(current_data_path)
    
    # Create monitor
    monitor = DriftMonitor(
        reference_data=reference_data,
        feature_names=feature_names,
        categorical_features=categorical_features,
    )
    
    # Detect drift
    drift_report = monitor.detect_drift(current_data)
    missingness_report = monitor.check_missingness(current_data)
    
    # Combine reports
    drift_report["missingness"] = missingness_report
    
    # Print summary
    monitor.print_summary(drift_report)
    
    # Save report
    if output_dir:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = output_dir / f"drift_report_{timestamp}.json"
        monitor.save_report(drift_report, report_path)
    
    return drift_report
