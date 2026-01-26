import pandas as pd
from pathlib import Path


def load_previous_snapshot(snapshot_dir: Path):
    if not snapshot_dir.exists():
        return None

    snapshots = sorted(
        snapshot_dir.glob("snapshot_date=*/customer_snapshot.parquet")
    )

    if not snapshots:
        return None

    return pd.read_parquet(snapshots[-1])
