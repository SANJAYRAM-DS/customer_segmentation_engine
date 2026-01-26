from fastapi import APIRouter
from backend.caching.loader import loader
from backend.api.schemas import ExecutiveOverview

router = APIRouter()

@router.get("/", response_model=ExecutiveOverview)
def get_executive_overview(
    segment_name: str | None = None,
    health_band: str | None = None,
    investment_priority: str | None = None
):
    df = loader.get_customer_snapshot()
    
    if df.empty:
         return {
            "kpis": {"total_customers": 0, "avg_churn_prob": 0.0, "avg_clv": 0.0, "snapshot_date": "", "metrics": {}},
            "customer_distribution": [],
            "health_distribution": [],
            "revenue_at_risk": {"total_clv": 0.0, "clv_at_risk": 0.0, "pct_at_risk": 0.0}
        }

    # Filter
    if segment_name:
        # Fuzzy match or Map
        # Backend "Power User" vs Frontend "Active"
        # We should assume Frontend sends mapped name or we filter loosely
        df = df[df["segment_name"] == segment_name]
    
    if health_band:
        df = df[df["health_band"] == health_band]

    if investment_priority:
        df = df[df["investment_priority"] == investment_priority]

    # Re-calculate KPIs on filtered DF? 
    # Yes, typically dashboard filters affect the metrics shown.
    # Note: Global KPIs (like total customers in DB) usually stay static, but dashboard KPIs reflect filter.
    # We will compute KPIs on the fly from the filtered DF.
    
    total_customers = len(df)
    avg_churn = df["churn_probability"].mean() if not df.empty else 0.0
    avg_clv = df["clv_12m"].mean() if not df.empty else 0.0
    
    active_customers = int(df["is_active_30d"].sum() if "is_active_30d" in df else 0)
    at_risk_count = int((df["churn_probability"] > 0.7).sum() if "churn_probability" in df else 0)
    
    # Mock Churn Rate 30d for filtered set (assumes simple 5% of risk)
    churn_rate = (at_risk_count / total_customers * 0.1) if total_customers > 0 else 0.0
    
    kpis = {
        "total_customers": total_customers,
        "avg_churn_prob": avg_churn,
        "avg_clv": avg_clv,
        "snapshot_date": str(df["snapshot_date"].iloc[0]) if not df.empty else "",
        "metrics": {
            "active_customers": active_customers,
            "at_risk_count": at_risk_count,
            "churn_rate_30d": churn_rate
        }
    }

    # Handle types for serialization
    # Convert categoricals to strings to avoid 'new category' errors on fillna
    for col in df.select_dtypes(include="category").columns:
        df[col] = df[col].astype(str)
        
    # Now safe to fill numeric/string NaNs
    df = df.fillna(0)

    # 1. KPI Summary
    kpi_data = kpis

    # 2. Customer Distribution (Segments)
    dist_list = []
    if "segment_name" in df:
        seg_counts = df["segment_name"].value_counts(normalize=True)
        for name, pct in seg_counts.items():
            dist_list.append({
                "category": name,
                "count": int(len(df) * pct),
                "percentage": round(pct * 100, 1)
            })

    # 3. Health Distribution
    health_list = []
    if "health_band" in df:
        h_counts = df["health_band"].value_counts(normalize=True)
        for name, pct in h_counts.items():
            health_list.append({
                "category": name,
                "count": int(len(df) * pct),
                "percentage": round(pct * 100, 1)
            })

    # 4. Revenue at Risk
    rev_at_risk = 0.0
    total_clv = 0.0
    if "clv_12m" in df and "churn_probability" in df:
        total_clv = df["clv_12m"].sum()
        risk_mask = df["churn_probability"] > 0.7 # Threshold
        rev_at_risk = df.loc[risk_mask, "clv_12m"].sum()

    revenue_data = {
        "total_clv": total_clv,
        "clv_at_risk": rev_at_risk,
        "pct_at_risk": (rev_at_risk / total_clv * 100) if total_clv > 0 else 0.0
    }

    return {
        "kpis": kpi_data,
        "customer_distribution": dist_list,
        "health_distribution": health_list,
        "revenue_at_risk": revenue_data
    }
