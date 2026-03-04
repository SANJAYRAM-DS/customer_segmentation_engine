from fastapi import APIRouter
from backend.caching.loader import loader
from backend.api.schemas import AlertsResponse
import os

router = APIRouter()

CHURN_THRESHOLD = float(os.getenv("DEFAULT_CHURN_THRESHOLD", "0.7"))

# In-memory store for acknowledged alerts (replace with DB in production)
_acknowledged_alerts: set = set()

@router.get("/", response_model=AlertsResponse)
def get_alerts():
    df = loader.get_customer_snapshot()
    if df.empty:
        return {"high_risk_churn": 0, "dropped_health": 0, "high_value_risk": 0, "details": []}

    df = loader.sanitize_df(df)

    # Rules
    # 1. Risk increased > 20%
    risk_spike = df[df["churn_probability_delta_7d"] > 0.2]
    
    # 2. Health dropped > 0.3
    health_drop = df[df["health_score_delta_30d"] < -0.3]
    
    # 3. High Value becoming inactive
    high_val_risk = df[(df["clv_12m"] > df["clv_12m"].quantile(0.8)) & (df["is_active_30d"] == False)]

    # 4. Immediate High Risk (Absolute)
    high_risk_absolute = df[df["churn_probability"] > CHURN_THRESHOLD]

    # 5. Moderate Risk
    moderate_risk = df[(df["churn_probability"] > 0.5) & (df["churn_probability"] <= CHURN_THRESHOLD)]
    
    print(f"[ALERTS] High Risk Absolute: {len(high_risk_absolute)}, Moderate: {len(moderate_risk)}, Risk Spike: {len(risk_spike)}, Health Drop: {len(health_drop)}, High Val Risk: {len(high_val_risk)}")

    alerts_list = []
    
    # Format alerts
    for _, row in high_risk_absolute.head(10).iterrows():
        alerts_list.append({
            "type": "high_churn_risk",
            "customer_id": row["customer_id"],
            "message": f"Critical churn risk detected ({row['churn_probability']:.2f})",
            "value": row["churn_probability"],
            "severity": "critical"
        })

    for _, row in moderate_risk.head(10).iterrows():
         alerts_list.append({
            "type": "moderate_churn_risk",
            "customer_id": row["customer_id"],
            "message": f"Elevated churn risk ({row['churn_probability']:.2f}) - Action Required",
            "value": row["churn_probability"],
            "severity": "high"
        })

    for _, row in risk_spike.head(10).iterrows():
        alerts_list.append({
            "type": "risk_spike",
            "customer_id": row["customer_id"],
            "message": f"Churn risk spiked by {row['churn_probability_delta_7d']:.2f}",
            "value": row["churn_probability_delta_7d"],
            "severity": "high"
        })
        
    for _, row in health_drop.head(10).iterrows():
        alerts_list.append({
            "type": "health_drop",
            "customer_id": row["customer_id"],
            "message": f"Health score dropped by {abs(row['health_score_delta_30d']):.2f}",
            "value": row["health_score_delta_30d"],
            "severity": "medium" 
        })
        
    for _, row in high_val_risk.head(10).iterrows():
         alerts_list.append({
            "type": "high_clv_inactive",
            "customer_id": row["customer_id"],
            "message": f"High value customer inactive (CLV: ${row['clv_12m']:.0f})",
            "value": row["clv_12m"],
            "severity": "critical"
        })

    return {
        "high_risk_churn": len(high_risk_absolute),
        "dropped_health": len(health_drop),
        "high_value_risk": len(high_val_risk),
        "details": alerts_list
    }


@router.post("/acknowledge/{alert_id}")
def acknowledge_alert(alert_id: str):
    """
    Acknowledge an alert by its ID.
    In production, persist this to a database.
    """
    _acknowledged_alerts.add(alert_id)
    return {"success": True, "alert_id": alert_id, "acknowledged": True}


@router.get("/summary")
def get_alert_summary():
    """Return high-level alert counts for badge/notification display."""
    df = loader.get_customer_snapshot()
    if df.empty:
        return {"total": 0, "critical": 0, "high": 0, "medium": 0}

    df = loader.sanitize_df(df)

    critical = int((df["churn_probability"] > CHURN_THRESHOLD).sum())
    high = int(((df["churn_probability"] > 0.5) & (df["churn_probability"] <= CHURN_THRESHOLD)).sum())
    medium = int((df.get("health_score_delta_30d", 0) < -0.3).sum()) if "health_score_delta_30d" in df else 0

    return {
        "total": critical + high + medium,
        "critical": critical,
        "high": high,
        "medium": medium
    }