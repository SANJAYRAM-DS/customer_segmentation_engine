from pathlib import Path
import pandas as pd

REQUIRED_FILES = {
    "customers": "customers.parquet",
    "orders": "orders.parquet",
    "returns": "returns.parquet",
    "sessions": "sessions.parquet",
}

class DataIngestionError(Exception):
    pass

def load_parquet(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise DataIngestionError(f"Missing file: {path}")
    return pd.read_parquet(path)

def ingest_raw_data(raw_dir: str) -> dict:
    raw_dir = Path(raw_dir)
    data = {}
    
    for name, fname in REQUIRED_FILES.items():
        df = load_parquet(raw_dir / fname)
        if df.empth:
            raise DataIngestionError(f"{fname} is empty")
        data[name] = df
    return data

def enforce_types(data: dict) -> dict:
    data['orders']['order_date'] = pd.to_datetime(data['orders']['order_date'])
    data['sessions']['session_date'] = pd.to_datetime(data['sessions']['session_date'])
    data['customers']['signup_date'] = pd.to_datetime(data['customers']['signup_date'])
    
    return data