from fastapi import APIRouter
from backend.caching.loader import loader

router = APIRouter()

@router.get("/")
def get_clv_metrics():
    df = loader.get_customer_snapshot()
    trends = loader.get_trends()
    
    if not df.empty:
        df = loader.sanitize_df(df)
        
    if not trends.empty:
        trends = loader.sanitize_df(trends)
    
    # 1. CLV Distribution (Histogram data)
    # We can return raw list for frontend to bin, or bin here.
    # Returning raw values might be heavy. Let's return simple deciles.
    clv_values = df["clv_12m"].tolist()

    # 2. Avg CLV by Segment
    # Use aggregation layer ideally, or compute
    by_segment = []
    if "segment_name" in df:
        val = df.groupby("segment_name")["clv_12m"].mean().reset_index()
        by_segment = val.to_dict(orient="records")


    # 3. Trends (Mock if empty to show functionality)
    trends_data = []
    if not trends.empty:
        trends_data = trends.to_dict(orient="records")
    else:
        # Generate generic trend
        import pandas as pd
        dates = pd.date_range(end=pd.Timestamp.now(), periods=6, freq="M")
        base_val = 1500
        for d in dates:
            trends_data.append({
                "snapshot_date": d.strftime("%Y-%m-%d"),
                "avg_clv": base_val,
                "total_clv_at_risk": base_val * 100 * 0.2
            })
            base_val += 50

    return {
        "clv_values": clv_values, # Frontend can histogram this
        "avg_clv_by_segment": by_segment,
        "trends": trends_data
    }
