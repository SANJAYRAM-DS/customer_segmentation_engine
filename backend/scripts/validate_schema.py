from typing import Set
import pandas as pd

def validate_exact_schema(
    df: pd.DataFrame,
    expected_columns: Set[str],
    table_name: str,
) -> None:
    actual = set(df.columns)

    missing = expected_columns - actual
    unexpected = actual - expected_columns

    if missing:
        raise ValueError(
            f"[{table_name}] Missing columns: {missing}"
        )

    if unexpected:
        raise ValueError(
            f"[{table_name}] Unexpected columns: {unexpected}"
        )
