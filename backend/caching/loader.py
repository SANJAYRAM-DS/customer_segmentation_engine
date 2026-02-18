from pathlib import Path
import json
import pandas as pd
from datetime import datetime
from functools import lru_cache

# Constants
BASE_DIR = Path(__file__).resolve().parents[2]
OUTPUTS_DIR = BASE_DIR / "backend/data/outputs"
SNAPSHOTS_DIR = BASE_DIR / "backend/data/snapshots/customer_snapshot"

class DataLoader:
    def __init__(self):
        self._latest_snapshot_date = None
        self._refresh_latest_date()

    def _refresh_latest_date(self):
        """Find the latest available output snapshot."""
        # Try outputs dir first
        if OUTPUTS_DIR.exists():
            dirs = sorted(OUTPUTS_DIR.glob("snapshot_date=*"))
            if dirs:
                self._latest_snapshot_date = dirs[-1].name.split("=")[1]
                return
        # Fallback: try snapshots dir (strip time component if present)
        if SNAPSHOTS_DIR.exists():
            dirs = sorted(SNAPSHOTS_DIR.glob("snapshot_date=*"))
            if dirs:
                raw = dirs[-1].name.split("=")[1]
                # Normalize: strip time part (e.g. '2023-04-24T00-00-00' -> '2023-04-24')
                self._latest_snapshot_date = raw[:10]

    @property
    def latest_date(self) -> str:
        if not self._latest_snapshot_date:
            self._refresh_latest_date()
        return self._latest_snapshot_date

    def sanitize_df(self, df: pd.DataFrame) -> pd.DataFrame:
        """Sanitize DataFrame for JSON output (fillna, categorical->str)."""
        df = df.copy()
        for col in df.select_dtypes(include="category").columns:
            df[col] = df[col].astype(str)
        return df.fillna(0)  # Or None if you prefer nulls in JSON

    def _get_output_path(self, filename: str) -> Path:
        if not self.latest_date:
            raise FileNotFoundError("No output snapshots found.")
        return OUTPUTS_DIR / f"snapshot_date={self.latest_date}" / filename

    def get_kpis(self) -> dict:
        path = self._get_output_path("kpis.json")
        if not path.exists():
            return {}
        with open(path, "r") as f:
            return json.load(f)

    def get_aggregations(self) -> pd.DataFrame:
        path = self._get_output_path("aggregations.parquet")
        return pd.read_parquet(path) if path.exists() else pd.DataFrame()

    def get_distributions(self) -> pd.DataFrame:
        path = self._get_output_path("distributions.parquet")
        return pd.read_parquet(path) if path.exists() else pd.DataFrame()

    def get_migrations(self) -> pd.DataFrame:
        path = self._get_output_path("migrations.parquet")
        return pd.read_parquet(path) if path.exists() else pd.DataFrame()

    def get_trends(self) -> pd.DataFrame:
        path = self._get_output_path("trends.parquet")
        return pd.read_parquet(path) if path.exists() else pd.DataFrame()

    @lru_cache(maxsize=1)
    def get_customer_snapshot(self) -> pd.DataFrame:
        """
        Loads the full customer snapshot. Cached in memory for speed.
        Tries both 'YYYY-MM-DD' and 'YYYY-MM-DDTHH-MM-SS' folder name formats.
        """
        if not self.latest_date:
            return pd.DataFrame()

        # Try exact date match first, then with time suffix
        candidates = [
            SNAPSHOTS_DIR / f"snapshot_date={self.latest_date}" / "customer_snapshot.parquet",
            SNAPSHOTS_DIR / f"snapshot_date={self.latest_date}T00-00-00" / "customer_snapshot.parquet",
        ]
        for path in candidates:
            if path.exists():
                return pd.read_parquet(path)

        return pd.DataFrame()
    def get_customer_details(self, customer_id: int) -> dict:
        df = self.get_customer_snapshot()
        df = self.sanitize_df(df) # SANITIZE HERE
        record = df[df["customer_id"] == customer_id]
        if record.empty:
            return None
        
        customer_data = record.to_dict(orient="records")[0]
        
        # Inject Mock Trends
        # In a real system, we'd query a time-series DB or load multiple snapshot files
        import numpy as np
        
        # Consistent random seed based on ID
        np.random.seed(customer_id)
        
        # Generate 6 months of history
        dates = pd.date_range(end=pd.Timestamp.now(), periods=6, freq="ME").strftime("%Y-%m-%d").tolist()
        
        # Mock Health Trend
        current_health = customer_data.get("health_score", 50)
        health_trend = []
        val = current_health
        for _ in reversed(dates):
            health_trend.append({"date": _, "value": int(val)})
            val = np.clip(val + np.random.randint(-5, 6), 0, 100)
        health_trend.reverse() # Oldest first
        
        # Mock Risk Trend
        current_risk = customer_data.get("churn_probability", 0.5)
        risk_trend = []
        val = current_risk
        for D in dates:
             risk_trend.append({"date": D, "value": round(val, 2)})
             val = np.clip(val + np.random.uniform(-0.1, 0.1), 0, 1)
        
        customer_data["trends"] = {
            "healthScore": health_trend,
            "churnProbability": risk_trend
        }
        
        return customer_data

    def get_customer_list(self, 
                          page: int = 1, 
                          page_size: int = 50, 
                          filters: dict = None, 
                          sort_by: str = "churn_probability", 
                          ascending: bool = False) -> dict:
        
        df = self.get_customer_snapshot()
        
        if df.empty:
            return {"total": 0, "page": page, "items": []}

        df = self.sanitize_df(df) # SANITIZE HERE

        # Apply Filters
        if filters:
            for col, val in filters.items():
                if val is not None and col in df.columns:
                    # Simple equality for now, extend as needed
                    df = df[df[col] == val]

        # Sorting
        if sort_by in df.columns:
            df = df.sort_values(by=sort_by, ascending=ascending)

        # Pagination
        total = len(df)
        start = (page - 1) * page_size
        end = start + page_size
        
        items = df.iloc[start:end].to_dict(orient="records")
        
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": items
        }

# Global instance
loader = DataLoader()
