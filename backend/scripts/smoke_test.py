from pathlib import Path
from scripts.data_ingestion import load_and_validate

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"

def test_data_ingestion_smoke():
    """
    Smoke test:
    - Ensures ingestion pipeline boots
    - Validates schemas & types
    - Fails fast if contracts break
    """
    data = load_and_validate(RAW_DATA_DIR)

    assert "customers" in data
    assert len(data["customers"]) > 0
    assert data["customers"]["customer_id"].isnull().sum() == 0
