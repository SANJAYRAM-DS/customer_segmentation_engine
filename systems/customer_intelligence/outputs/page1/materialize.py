from pathlib import Path
import pandas as pd
from datetime import datetime, UTC

from .health_score import compute_customer_health_scores

OUTPUT_PATH = Path('../../../../data/output/customer_risk_scores.parquet')

def materialize_customer_risk_scores(base_df: pd.DataFrame):
    df = compute_customer_health_scores(base_df)
    
    df['last_updated'] = datetime.utc_now()
    
    final_cols = [
        "customer_id",
        "segment",
        "churn_probability",
        "clv_12m",
        "health_score",
        "health_band",
        "investment_priority",
        "last_updated",
    ]
    
    df[final_cols].toparquet(OUTPUT_PATH, index=False)
    return df[final_cols]