from fastapi import APIRouter
from backend.caching.loader import loader
from backend.api.schemas import SegmentationResponse
import pandas as pd

router = APIRouter()

@router.get("/", response_model=SegmentationResponse)
def get_segmentation_stats(
    segment_name: str | None = None,
    health_band: str | None = None,
    investment_priority: str | None = None
):
    # Pre-built aggregations are better for this
    aggs = loader.get_aggregations()
    mig = loader.get_migrations()
    df = loader.get_customer_snapshot()

    df = loader.sanitize_df(df)
    aggs = loader.sanitize_df(aggs)

    # Note: aggs are pre-calculated for all users. We can't easily filter AGGS without raw data.
    # However, 'df' IS the raw snapshot. We can re-aggregate if filters are present.
    
    if segment_name or health_band or investment_priority:
         if segment_name:
             df = df[df["segment_name"] == segment_name]
         if health_band:
             df = df[df["health_band"] == health_band]
         if investment_priority:
             df = df[df["investment_priority"] == investment_priority]
         
         # Re-calc aggs from filtered df
         if not df.empty and "segment_name" in df:
             grouped = df.groupby("segment_name").agg({
                 "customer_id": "count",
                 "clv_12m": "mean",
                 "churn_probability": "mean"
             }).reset_index().rename(columns={"customer_id": "count"})
             aggs = grouped
         else:
             aggs = pd.DataFrame()


    # 1. Segment Stats
    segments = []
    if not aggs.empty:
        # Assuming aggs has columns: segment_name, count, clv_12m, churn_probability
        for _, row in aggs.iterrows():
            segments.append({
                "segment_name": row["segment_name"],
                "customer_count": row["count"],
                "avg_clv": row["clv_12m"],
                "avg_churn_risk": row["churn_probability"]
            })
    
    # 2. Migrations
    migrations = []
    if not mig.empty:
        migrations = mig.to_dict(orient="records")

    # 3. Health Comparison (Radar)
    # Calculate on fly if not in aggs
    dataset_health = {}
    if not df.empty and "segment_name" in df:
        grouped = df.groupby("segment_name").agg({
            "health_score": "mean",
            "session_frequency_30d": "mean",
            "spend_30d": "mean",
            "churn_probability": "mean"
        }).reset_index()
        dataset_health = grouped.to_dict(orient="records")

    return {
        "segments": segments,
        "migrations": migrations,
        "health_comparison": {"data": dataset_health}
    }
