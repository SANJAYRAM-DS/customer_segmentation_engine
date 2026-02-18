from pathlib import Path
from typing import Dict, Any
from datetime import datetime, timezone
import json
import traceback
import logging
import pandas as pd

# ------------------------------------------------------------------------------
# Logging setup
# ------------------------------------------------------------------------------
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_DIR / "data_ingestion.log"),
    ],
)

logger = logging.getLogger("data_ingestion")

# ------------------------------------------------------------------------------
# Constants
# ------------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = {
    "customers": "customers.parquet",
    "orders": "orders.parquet",
    "returns": "returns.parquet",
    "sessions": "sessions.parquet",
}

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

MAX_INVALID_TIMESTAMP_RATE = 0.001  # 0.1%

# ------------------------------------------------------------------------------
# Exceptions
# ------------------------------------------------------------------------------
class DataIngestionError(Exception):
    pass

# ------------------------------------------------------------------------------
# Core loaders
# ------------------------------------------------------------------------------
def load_parquet(path: Path) -> pd.DataFrame:
    logger.info(f"Loading file: {path}")
    if not path.exists():
        raise DataIngestionError(f"Missing file: {path}")

    df = pd.read_parquet(path, engine="pyarrow")
    if df.empty:
        raise DataIngestionError(f"{path.name} is empty")

    return df

# ------------------------------------------------------------------------------
# Schema validation
# ------------------------------------------------------------------------------
def validate_schema(df: pd.DataFrame, name: str, report: Dict[str, Any]) -> None:
    expected = EXPECTED_COLUMNS[name]
    actual = set(df.columns)

    missing = expected - actual
    unexpected = actual - expected

    if missing:
        raise DataIngestionError(
            f"Schema mismatch in '{name}'. Missing columns: {missing}"
        )

    if unexpected:
        logger.warning(
            f"Schema drift detected in '{name}'. Unexpected columns: {unexpected}"
        )
        report.setdefault("schema_warnings", {})[name] = list(unexpected)

# ------------------------------------------------------------------------------
# Ingestion
# ------------------------------------------------------------------------------
def ingest_raw_data(raw_dir: Path, report: Dict[str, Any]) -> Dict[str, pd.DataFrame]:
    data: Dict[str, pd.DataFrame] = {}

    for name, fname in REQUIRED_FILES.items():
        df = load_parquet(raw_dir / fname)
        validate_schema(df, name, report)
        data[name] = df

    return data

# ------------------------------------------------------------------------------
# Type & time enforcement
# ------------------------------------------------------------------------------
def enforce_types(data: Dict[str, pd.DataFrame], report: Dict[str, Any]) -> None:
    def enforce_datetime(series: pd.Series, col_name: str):
        parsed = pd.to_datetime(series, utc=True, errors="coerce")
        invalid_rate = parsed.isna().mean()

        if invalid_rate > MAX_INVALID_TIMESTAMP_RATE:
            raise DataIngestionError(
                f"High invalid timestamp rate in {col_name}: {invalid_rate:.4f}"
            )

        if invalid_rate > 0:
            logger.warning(
                f"{col_name}: {invalid_rate:.4f} invalid timestamps coerced to NaT"
            )
            report.setdefault("timestamp_warnings", {})[col_name] = invalid_rate

        return parsed

    # Customers
    customers = data["customers"]
    customers["customer_id"] = customers["customer_id"].astype("int64")
    customers["signup_date"] = enforce_datetime(customers["signup_date"], "signup_date")
    customers["last_order_date"] = enforce_datetime(
        customers["last_order_date"], "last_order_date"
    )
    customers["is_churned"] = customers["is_churned"].astype("bool")

    # Orders
    orders = data["orders"]
    orders["customer_id"] = orders["customer_id"].astype("int64")
    orders["order_date"] = enforce_datetime(orders["order_date"], "order_date")
    orders["order_value"] = orders["order_value"].astype("float64")
    orders["discount_used"] = orders["discount_used"].astype("bool")

    # Returns
    returns = data["returns"]
    returns["return_date"] = enforce_datetime(returns["return_date"], "return_date")
    returns["refund_amount"] = returns["refund_amount"].astype("float64")

    # Sessions
    sessions = data["sessions"]
    sessions["session_date"] = enforce_datetime(
        sessions["session_date"], "session_date"
    )

# ------------------------------------------------------------------------------
# Hard quality checks
# ------------------------------------------------------------------------------
def run_quality_checks(data: Dict[str, pd.DataFrame]) -> None:
    if data["customers"]["customer_id"].duplicated().any():
        raise DataIngestionError("Duplicate customer_id detected")

    if (data["orders"]["order_value"] < 0).mean() > 0.001:
        raise DataIngestionError("Excessive negative order_value")

    if (data["sessions"]["session_duration"] < 0).any():
        raise DataIngestionError("Negative session_duration detected")

# ------------------------------------------------------------------------------
# Report persistence
# ------------------------------------------------------------------------------
def save_report(report: Dict[str, Any]) -> Path:
    report_dir = PROJECT_ROOT / "reports" / "data"
    report_dir.mkdir(parents=True, exist_ok=True)

    path = report_dir / "data_quality_report.json"
    with path.open("w") as f:
        json.dump(report, f, indent=2)

    return path

# ------------------------------------------------------------------------------
# Public API
# ------------------------------------------------------------------------------
def load_and_validate(raw_dir: Path) -> Dict[str, pd.DataFrame]:
    report: Dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "failed",
    }

    try:
        logger.info("Starting data ingestion")
        data = ingest_raw_data(raw_dir, report)
        enforce_types(data, report)
        run_quality_checks(data)

        report["status"] = "success"
        save_report(report)
        logger.info("Data ingestion completed successfully")
        return data

    except Exception as e:
        logger.error("Data ingestion failed", exc_info=True)
        report.update(
            {
                "error": str(e),
                "traceback": traceback.format_exc(),
            }
        )
        save_report(report)
        raise