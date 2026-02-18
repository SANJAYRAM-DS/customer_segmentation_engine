"""
SHAP-based Model Explainability
Implements Document 12 requirements for:
- Feature-level explanations
- Reason code generation
- Explanation storage and traceability
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import json
from datetime import datetime, timezone

try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False
    print("[WARNING] SHAP not installed. Install with: pip install shap")


class SHAPExplainer:
    """
    Generates SHAP-based explanations for model predictions
    
    Implements Document 12.1: Prediction Explanations
    """
    
    def __init__(
        self,
        model,
        feature_names: List[str],
        model_type: str = "churn",
        background_data: Optional[np.ndarray] = None,
    ):
        """
        Args:
            model: Trained model
            feature_names: List of feature names
            model_type: Type of model ('churn', 'clv')
            background_data: Background dataset for SHAP (optional)
        """
        if not SHAP_AVAILABLE:
            raise ImportError("SHAP is required for explanations. Install with: pip install shap")
        
        self.model = model
        self.feature_names = feature_names
        self.model_type = model_type
        
        # Initialize SHAP explainer
        if background_data is not None:
            self.explainer = shap.Explainer(model.predict_proba, background_data)
        else:
            self.explainer = shap.Explainer(model)
    
    def explain_prediction(
        self,
        X: np.ndarray,
        top_k: int = 5,
    ) -> Dict:
        """
        Generate SHAP explanation for a single prediction
        
        Args:
            X: Feature vector (single sample)
            top_k: Number of top features to return
            
        Returns:
            Explanation dictionary
        """
        # Compute SHAP values
        shap_values = self.explainer(X.reshape(1, -1))
        
        # Get SHAP values for positive class (churn) or regression value
        if self.model_type == "churn":
            values = shap_values.values[0, :, 1]  # Positive class
        else:
            values = shap_values.values[0]
        
        # Get top contributing features
        top_indices = np.argsort(np.abs(values))[-top_k:][::-1]
        
        top_features = []
        for idx in top_indices:
            top_features.append({
                "feature": self.feature_names[idx],
                "value": float(X[idx]),
                "shap_value": float(values[idx]),
                "contribution": "increases" if values[idx] > 0 else "decreases",
            })
        
        explanation = {
            "top_features": top_features,
            "all_shap_values": {
                self.feature_names[i]: float(values[i])
                for i in range(len(self.feature_names))
            },
            "base_value": float(shap_values.base_values[0]),
        }
        
        return explanation
    
    def explain_batch(
        self,
        X: np.ndarray,
        customer_ids: Optional[List] = None,
        top_k: int = 5,
    ) -> pd.DataFrame:
        """
        Generate explanations for a batch of predictions
        
        Args:
            X: Feature matrix
            customer_ids: Optional customer IDs
            top_k: Number of top features per prediction
            
        Returns:
            DataFrame with explanations
        """
        explanations = []
        
        for i in range(len(X)):
            exp = self.explain_prediction(X[i], top_k=top_k)
            
            explanation_row = {
                "customer_id": customer_ids[i] if customer_ids else i,
                "top_features": [f["feature"] for f in exp["top_features"]],
                "top_shap_values": [f["shap_value"] for f in exp["top_features"]],
                "explanation": exp,
            }
            
            explanations.append(explanation_row)
        
        return pd.DataFrame(explanations)


class ReasonCodeGenerator:
    """
    Generates business-friendly reason codes from model explanations
    
    Implements Document 12.2: Risk Reason Codes
    """
    
    def __init__(self, model_type: str = "churn"):
        """
        Args:
            model_type: Type of model ('churn', 'clv')
        """
        self.model_type = model_type
        
        # Define reason code rules for churn
        self.churn_reason_codes = {
            "ENG_DECAY": {
                "description": "Engagement has decreased significantly",
                "conditions": lambda row: (
                    row.get("sessions_30d", 0) < 2 or
                    row.get("recency_days", 0) > 60
                ),
            },
            "RETURN_RISK": {
                "description": "High recent return rate",
                "conditions": lambda row: row.get("return_rate", 0) > 0.3,
            },
            "LOW_SPEND": {
                "description": "Declining spend pattern",
                "conditions": lambda row: (
                    row.get("spend_30d", 0) < row.get("spend_90d", 1) / 3
                ),
            },
            "NEW_COHORT": {
                "description": "New customer with limited history",
                "conditions": lambda row: row.get("tenure_days", 999) < 90,
            },
            "INACTIVE": {
                "description": "No recent activity",
                "conditions": lambda row: (
                    row.get("recency_days", 0) > 30 and
                    row.get("sessions_7d", 0) == 0
                ),
            },
        }
        
        # Define reason codes for CLV
        self.clv_reason_codes = {
            "HIGH_FREQUENCY": {
                "description": "High purchase frequency",
                "conditions": lambda row: row.get("order_frequency", 0) > 0.5,
            },
            "HIGH_AOV": {
                "description": "High average order value",
                "conditions": lambda row: row.get("avg_order_value", 0) > 100,
            },
            "LOYAL_CUSTOMER": {
                "description": "Long tenure and consistent purchases",
                "conditions": lambda row: (
                    row.get("tenure_days", 0) > 365 and
                    row.get("order_frequency", 0) > 0.3
                ),
            },
            "LOW_VALUE": {
                "description": "Low historical spend",
                "conditions": lambda row: row.get("total_spend", 0) < 100,
            },
        }
    
    def generate_reason_codes(
        self,
        features_df: pd.DataFrame,
        predictions: np.ndarray,
        shap_explanations: Optional[pd.DataFrame] = None,
    ) -> pd.DataFrame:
        """
        Generate reason codes for predictions
        
        Args:
            features_df: Feature dataframe
            predictions: Model predictions
            shap_explanations: Optional SHAP explanations
            
        Returns:
            DataFrame with reason codes
        """
        reason_codes_list = []
        
        for idx, row in features_df.iterrows():
            codes = []
            
            # Select reason code rules based on model type
            if self.model_type == "churn":
                rules = self.churn_reason_codes
            else:
                rules = self.clv_reason_codes
            
            # Check each rule
            for code, rule in rules.items():
                try:
                    if rule["conditions"](row):
                        codes.append({
                            "code": code,
                            "description": rule["description"],
                        })
                except:
                    # Skip if feature not available
                    pass
            
            # If SHAP explanations available, add top feature as reason
            if shap_explanations is not None and idx < len(shap_explanations):
                top_feature = shap_explanations.iloc[idx]["top_features"][0]
                codes.append({
                    "code": "TOP_DRIVER",
                    "description": f"Primary driver: {top_feature}",
                })
            
            reason_codes_list.append({
                "customer_id": row.get("customer_id", idx),
                "prediction": float(predictions[idx]),
                "reason_codes": codes,
                "primary_reason": codes[0]["code"] if codes else "UNKNOWN",
            })
        
        return pd.DataFrame(reason_codes_list)


class ExplanationStore:
    """
    Stores and manages prediction explanations
    
    Implements Document 12.3: Historical Traceability
    """
    
    def __init__(self, storage_dir: Path):
        """
        Args:
            storage_dir: Directory to store explanations
        """
        self.storage_dir = storage_dir
        self.storage_dir.mkdir(parents=True, exist_ok=True)
    
    def save_explanations(
        self,
        customer_ids: List,
        predictions: np.ndarray,
        explanations: pd.DataFrame,
        reason_codes: pd.DataFrame,
        model_version: str,
        feature_version: str,
    ) -> Path:
        """
        Save explanations with full lineage
        
        Implements Document 12.3.1: Traceability Components
        
        Args:
            customer_ids: Customer IDs
            predictions: Model predictions
            explanations: SHAP explanations
            reason_codes: Reason codes
            model_version: Model version
            feature_version: Feature version
            
        Returns:
            Path to saved explanations
        """
        timestamp = datetime.now(timezone.utc)
        
        # Create explanation records
        records = []
        for i, customer_id in enumerate(customer_ids):
            record = {
                "customer_id": customer_id,
                "prediction_timestamp": timestamp.isoformat(),
                "model_version": model_version,
                "feature_version": feature_version,
                "prediction": float(predictions[i]),
                "explanation": explanations.iloc[i]["explanation"] if i < len(explanations) else {},
                "reason_codes": reason_codes.iloc[i]["reason_codes"] if i < len(reason_codes) else [],
                "primary_reason": reason_codes.iloc[i]["primary_reason"] if i < len(reason_codes) else "UNKNOWN",
            }
            records.append(record)
        
        # Save to file
        date_str = timestamp.strftime("%Y%m%d")
        output_path = self.storage_dir / f"explanations_{date_str}_{model_version}.json"
        
        with output_path.open("w") as f:
            json.dump(records, f, indent=2)
        
        print(f"[OK] Explanations saved: {output_path}")
        return output_path
    
    def query_explanation(
        self,
        customer_id: str,
        date: Optional[str] = None,
    ) -> Optional[Dict]:
        """
        Query historical explanation for a customer
        
        Implements Document 12.3.2: Auditability
        
        Args:
            customer_id: Customer ID
            date: Optional date (YYYYMMDD format)
            
        Returns:
            Explanation record or None
        """
        # Find relevant files
        if date:
            pattern = f"explanations_{date}_*.json"
        else:
            pattern = "explanations_*.json"
        
        files = sorted(self.storage_dir.glob(pattern), reverse=True)
        
        # Search for customer
        for file_path in files:
            with file_path.open("r") as f:
                records = json.load(f)
            
            for record in records:
                if record["customer_id"] == customer_id:
                    return record
        
        return None


def generate_explanations(
    model,
    X: np.ndarray,
    feature_names: List[str],
    customer_ids: List,
    predictions: np.ndarray,
    features_df: pd.DataFrame,
    model_type: str = "churn",
    model_version: str = "v1",
    feature_version: str = "v1",
    storage_dir: Optional[Path] = None,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Generate comprehensive explanations for predictions
    
    Args:
        model: Trained model
        X: Feature matrix
        feature_names: Feature names
        customer_ids: Customer IDs
        predictions: Model predictions
        features_df: Feature dataframe (for reason codes)
        model_type: Model type
        model_version: Model version
        feature_version: Feature version
        storage_dir: Optional storage directory
        
    Returns:
        (explanations_df, reason_codes_df)
    """
    # Generate SHAP explanations
    explainer = SHAPExplainer(model, feature_names, model_type)
    explanations = explainer.explain_batch(X, customer_ids)
    
    # Generate reason codes
    reason_gen = ReasonCodeGenerator(model_type)
    reason_codes = reason_gen.generate_reason_codes(
        features_df, predictions, explanations
    )
    
    # Store explanations
    if storage_dir:
        store = ExplanationStore(storage_dir)
        store.save_explanations(
            customer_ids, predictions, explanations,
            reason_codes, model_version, feature_version
        )
    
    return explanations, reason_codes