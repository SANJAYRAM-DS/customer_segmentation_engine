from pathlib import Path
from typing import Dict, Any
from datetime import datetime, timezone
import json
import traceback
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]


# File contract
REQUIRED_FILES = {
    "customers": "customers.parquet",
    "orders": "orders.parquet",
    "returns": "returns.parquet",
    "sessions": "sessions.parquet",
}

# Expected schema
EXPECTED_COLUMNS = {
    "customers": {
        "customer_id",
        "signup_date",
        "country",
        "acquisition_channel",
        "device_type",
        "last_order_date",
        "is_churned",
    },
    "orders": {
        "order_id",
        "customer_id",
        "order_date",
        "order_value",
        "payment_type",
        "discount_used",
    },
    "returns": {
        "return_id",
        "order_id",
        "customer_id",
        "return_reason",
        "refund_amount",
        "return_date",
    },
    "sessions": {
        "session_id",
        "customer_id",
        "session_date",
        "pages_viewed",
        "session_duration",
        "source",
    },
}


# Custom exception
class DataIngestionError(Exception):
    """Raised when raw data ingestion fails"""

# Core loaders
def load_parquet(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise DataIngestionError(f"Missing file: {path}")

    try:
        df = pd.read_parquet(path, engine="pyarrow")
    except Exception as e:
        raise DataIngestionError(f"Failed reading {path}: {e}")

    if df.empty:
        raise DataIngestionError(f"{path.name} is empty")

    return df

#Validate schema
def validate_schema(df: pd.DataFrame, name: str) -> None:
    expected = EXPECTED_COLUMNS[name]
    actual = set(df.columns)

    missing = expected - actual
    if missing:
        raise DataIngestionError(
            f"Schema mismatch in '{name}'. Missing columns: {missing}"
        )


# Ingestion
def ingest_raw_data(raw_dir: str) -> Dict[str, pd.DataFrame]:
    raw_dir = Path(raw_dir)
    data: Dict[str, pd.DataFrame] = {}

    for name, fname in REQUIRED_FILES.items():
        df = load_parquet(raw_dir / fname)
        validate_schema(df, name)
        data[name] = df

    return data


# Type enforcement
def enforce_types(data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
    for df in data.values():
        if "customer_id" in df.columns:
            df["customer_id"] = df["customer_id"].astype("int64")

    customers = data["customers"]
    customers["signup_date"] = pd.to_datetime(customers["signup_date"], errors="raise")
    customers["last_order_date"] = pd.to_datetime(
        customers["last_order_date"], errors="coerce"
    )
    customers["is_churned"] = customers["is_churned"].astype("bool")

    orders = data["orders"]
    orders["order_date"] = pd.to_datetime(orders["order_date"], errors="raise")
    orders["order_value"] = orders["order_value"].astype("float64")
    orders["discount_used"] = orders["discount_used"].astype("bool")

    returns = data["returns"]
    returns["refund_amount"] = returns["refund_amount"].astype("float64")
    returns["return_date"] = pd.to_datetime(returns["return_date"], errors="raise")

    sessions = data["sessions"]
    sessions["session_date"] = pd.to_datetime(sessions["session_date"], errors="raise")

    return data


# Data quality report
def generate_quality_report(data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
    report: Dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "tables": {},
        "warnings": [],
        "process_log": [],
        "status": "success",
    }

    now = pd.Timestamp.now()

    for name, df in data.items():
        table_report = {
            "row_count": int(len(df)),
            "duplicate_rows": int(df.duplicated().sum()),
            "columns": {},
        }

        for col in df.columns:
            series = df[col]
            col_report = {
                "dtype": str(series.dtype),
                "null_count": int(series.isna().sum()),
                "null_pct": float(series.isna().mean()),
            }

            if pd.api.types.is_numeric_dtype(series):
                col_report.update(
                    {
                        "min": float(series.min()),
                        "max": float(series.max()),
                    }
                )


            if pd.api.types.is_datetime64_any_dtype(series):
                col_report.update(
                    {
                        "min": series.min().isoformat() if series.notna().any() else None,
                        "max": series.max().isoformat() if series.notna().any() else None,
                        "future_dates": int((series > now).sum()),
                    }
                )

            table_report["columns"][col] = col_report

        report["tables"][name] = table_report

    # Referential integrity (soft warning)
    orphan_orders = (
        set(data["orders"]["customer_id"])
        - set(data["customers"]["customer_id"])
    )

    if orphan_orders:
        report["warnings"].append(
            {
                "type": "referential_integrity",
                "message": "Orders with missing customers detected",
                "count": len(orphan_orders),
            }
        )

    return report


def save_quality_report(report: Dict[str, Any], base_dir: Path) -> Path:
    """
    Saves data quality report and returns the absolute path.
    """
    report_dir = base_dir / "backend" / "reports" / "data"
    report_dir.mkdir(parents=True, exist_ok=True)

    path = report_dir / "data_quality_report.json"
    with path.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    return path.resolve()



# Hard data quality checks
def run_quality_checks(data: Dict[str, pd.DataFrame]) -> None:
    if data["customers"]["customer_id"].duplicated().any():
        raise DataIngestionError("Duplicate customer_id found in customers")

    if data["orders"]["order_id"].duplicated().any():
        raise DataIngestionError("Duplicate order_id found in orders")

    if data["returns"]["return_id"].duplicated().any():
        raise DataIngestionError("Duplicate return_id found in returns")

    if data["sessions"]["session_id"].isnull().any():
        raise DataIngestionError("Null session_id found in sessions")

    if (data["orders"]["order_value"] < 0).any():
        raise DataIngestionError("Negative order_value detected")

    if (data["returns"]["refund_amount"] < 0).any():
        raise DataIngestionError("Negative refund_amount detected")

    if (data["sessions"]["pages_viewed"] < 0).any():
        raise DataIngestionError("Negative pages_viewed detected")

    if (data["sessions"]["session_duration"] < 0).any():
        raise DataIngestionError("Negative session_duration detected")


# Public API (tracked + guarded)
def load_and_validate(raw_dir: str) -> Dict[str, pd.DataFrame]:
    """
    Single entry point for ingestion layer
    Tracks each step and persists failure context.
    """
    process_log = []
    base_dir = PROJECT_ROOT
    report: Dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "process_log": process_log,
        "status": "failed",
    }

    try:
        process_log.append({"step": "ingest_raw_data", "status": "started"})
        data = ingest_raw_data(raw_dir)
        process_log.append({"step": "ingest_raw_data", "status": "completed"})

        process_log.append({"step": "enforce_types", "status": "started"})
        data = enforce_types(data)
        process_log.append({"step": "enforce_types", "status": "completed"})

        process_log.append({"step": "generate_quality_report", "status": "started"})
        report = generate_quality_report(data)
        report["process_log"] = process_log
        process_log.append({"step": "generate_quality_report", "status": "completed"})

        process_log.append({"step": "run_quality_checks", "status": "started"})
        run_quality_checks(data)
        process_log.append({"step": "run_quality_checks", "status": "completed"})

        report["status"] = "success"
        report_path = save_quality_report(report, base_dir)
        report["report_path"] = str(report_path)
        return data

    except Exception as e:
        report.update(
            {
                "error_type": type(e).__name__,
                "error_message": str(e),
                "traceback": traceback.format_exc(),
                "status": "failed",
            }
        )
        report_path = save_quality_report(report, base_dir)
        report["report_path"] = str(report_path)
        raise

if __name__ == "__main__":
    RAW_DATA_DIR = PROJECT_ROOT / "backend" / "data" / "raw"

    try:
        load_and_validate(RAW_DATA_DIR)
        print("[OK] Data ingestion completed successfully")
        print(f"[INFO] Report saved at: {PROJECT_ROOT / 'backend' / 'reports' / 'data_quality_report.json'}")

    except Exception as e:
        print("[ERROR] Data ingestion failed")
        print(str(e))
        print(f"[INFO] Check report at: {PROJECT_ROOT / 'backend' / 'reports' / 'data_quality_report.json'}")
