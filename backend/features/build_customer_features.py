from pathlib import Path
from datetime import datetime, timezone
import json
import traceback
import numpy as np

from backend.features.orders import aggregate_orders, rolling_order_features
from backend.features.sessions import aggregate_sessions, rolling_session_features
from backend.features.returns import aggregate_returns
from backend.features.temporal import add_temporal_features
from backend.features.targets import build_churn_target, build_clv_target
from backend.features.snapshot import get_snapshot_date
from backend.features.validation import FeatureValidator, save_validation_report
from backend.data_ingestion import load_and_validate
from backend.data.feature_registry.loader import load_feature_registry, get_feature_names


PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / "backend" / "data" / "processed"


# Report writer
def save_feature_report(report: dict) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / "feature_build_report.json"

    with path.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    return path.resolve()


# Main pipeline (tracked)
def build_customer_features(data):
    process_log = []
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "failed",
        "process_log": process_log,
    }

    try:
        process_log.append({"step": "load_inputs", "status": "started"})
        customers = data["customers"]
        orders = data["orders"]
        sessions = data["sessions"]
        returns = data["returns"]
        process_log.append(
            {
                "step": "load_inputs",
                "status": "completed",
                "rows": {
                    "customers": len(customers),
                    "orders": len(orders),
                    "sessions": len(sessions),
                    "returns": len(returns),
                },
            }
        )

        process_log.append({"step": "snapshot", "status": "started"})
        snapshot = get_snapshot_date(orders)
        process_log.append(
            {
                "step": "snapshot",
                "status": "completed",
                "snapshot_date": snapshot.isoformat(),
            }
        )

        base = customers.copy()
        base_rows = len(base)

        process_log.append({"step": "base_aggregations", "status": "started"})
        base = base.merge(
            aggregate_orders(orders, snapshot), on="customer_id", how="left"
        )
        base = base.merge(
            aggregate_sessions(sessions, snapshot), on="customer_id", how="left"
        )
        base = base.merge(
            aggregate_returns(returns, snapshot), on="customer_id", how="left"
        )

        if len(base) != base_rows:
            raise RuntimeError("Row count changed after base aggregations")

        process_log.append(
            {
                "step": "base_aggregations",
                "status": "completed",
                "rows": len(base),
            }
        )

        process_log.append({"step": "temporal_features", "status": "started"})
        base = add_temporal_features(base, snapshot)
        process_log.append({"step": "temporal_features", "status": "completed"})

        process_log.append({"step": "rolling_features", "status": "started"})
        base = base.merge(
            rolling_order_features(orders, snapshot),
            on="customer_id",
            how="left",
        )
        base = base.merge(
            rolling_session_features(sessions, snapshot),
            on="customer_id",
            how="left",
        )

        if len(base) != base_rows:
            raise RuntimeError("Row count changed after rolling features")

        process_log.append(
            {
                "step": "rolling_features",
                "status": "completed",
                "rows": len(base),
            }
        )

        process_log.append({"step": "numeric_safety", "status": "started"})
        num_cols = base.select_dtypes(include="number").columns
        base[num_cols] = (
            base[num_cols].replace([np.inf, -np.inf], 0).fillna(0)
        )
        process_log.append({"step": "numeric_safety", "status": "completed"})

        # CHURN
        process_log.append({"step": "churn_features", "status": "started"})
        churn_df = base.copy()
        churn_df["churn_90d"] = build_churn_target(orders, snapshot)(churn_df)

        registry = load_feature_registry("churn", "v1")
        expected = get_feature_names(registry)
        churn_df = churn_df[expected]
        validate_feature_schema(churn_df, registry, "churn")

        churn_dir = OUTPUT_DIR / "churn"
        churn_dir.mkdir(parents=True, exist_ok=True)
        churn_df.to_parquet(churn_dir / "features.parquet", index=False)

        process_log.append(
            {
                "step": "churn_features",
                "status": "completed",
                "output": str(churn_dir / "features.parquet"),
            }
        )

        # CLV
        process_log.append({"step": "clv_features", "status": "started"})
        clv_target = build_clv_target(orders, snapshot)
        clv_df = base.merge(clv_target, on="customer_id", how="left")
        clv_df["future_90d_spend"] = clv_df["future_90d_spend"].fillna(0)

        registry = load_feature_registry("clv", "v1")
        expected = get_feature_names(registry)
        clv_df = clv_df[expected]
        validate_feature_schema(clv_df, registry, "clv")
        
        clv_dir = OUTPUT_DIR / "clv"
        clv_dir.mkdir(parents=True, exist_ok=True)
        clv_df.to_parquet(clv_dir / "features.parquet", index=False)

        process_log.append(
            {
                "step": "clv_features",
                "status": "completed",
                "output": str(clv_dir / "features.parquet"),
            }
        )

        # SEGMENTATION
        process_log.append({"step": "segmentation_features", "status": "started"})
        registry = load_feature_registry("segmentation", "v1")
        expected = get_feature_names(registry)
        seg_df = base[expected]
        validate_feature_schema(seg_df, registry, "segmentation")

        seg_dir = OUTPUT_DIR / "segmentation"
        seg_dir.mkdir(parents=True, exist_ok=True)
        seg_df.to_parquet(seg_dir / "features.parquet", index=False)

        process_log.append(
            {
                "step": "segmentation_features",
                "status": "completed",
                "output": str(seg_dir / "features.parquet"),
            }
        )

        report["status"] = "success"
        report_path = save_feature_report(report)
        report["report_path"] = str(report_path)

        print("[OK] Feature generation completed")
        print("[INFO] Feature report saved at:", report_path)

        return {
            "snapshot": snapshot,
            "rows": base_rows,
            "report_path": report_path,
        }

    except Exception as e:
        report.update(
            {
                "error_type": type(e).__name__,
                "error_message": str(e),
                "traceback": traceback.format_exc(),
                "status": "failed",
            }
        )
        report_path = save_feature_report(report)

        print("[ERROR] Feature generation failed")
        print("[INFO] Check report at:", report_path)

        raise

def validate_feature_schema(df, registry: dict, model_type: str):
    """
    Comprehensive feature validation using FeatureValidator
    
    Args:
        df: Feature dataframe
        registry: Feature registry dict
        model_type: Model type for category eligibility check
    """
    validator = FeatureValidator(registry, max_null_rate=0.5)
    report = validator.validate_all(df, model_type=model_type)
    
    # Save validation report
    report_dir = OUTPUT_DIR / model_type / "validation"
    report_dir.mkdir(parents=True, exist_ok=True)
    save_validation_report(report, report_dir / "validation_report.json")
    
    # Raise error if validation failed
    if not report["passed"]:
        errors = []
        for check_name, check_result in report["checks"].items():
            if not check_result["passed"]:
                errors.extend(check_result.get("errors", []))
                errors.extend(check_result.get("warnings", []))
        
        error_msg = f"Feature validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
        raise RuntimeError(error_msg)
    
    print(f"[OK] Feature validation passed for {model_type}")



if __name__ == "__main__":
    RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"

    print("[INFO] Loading raw data...")
    data = load_and_validate(RAW_DATA_DIR)

    print("[INFO] Building customer features...")
    result = build_customer_features(data)

    print("[OK] Feature pipeline completed")
    print("[INFO] Snapshot date:", result["snapshot"])
    print("[INFO] Report saved at:", result["report_path"])