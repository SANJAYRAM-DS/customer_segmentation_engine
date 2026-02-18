from pydantic import BaseModel
from typing import List, Optional, Dict, Any

# Generic Responses
class KPISummary(BaseModel):
    total_customers: int
    avg_churn_prob: float
    avg_clv: float
    snapshot_date: str
    metrics: Dict[str, Any]

class DistributionItem(BaseModel):
    category: str
    count: int
    percentage: float

class ExecutiveOverview(BaseModel):
    kpis: KPISummary
    customer_distribution: List[DistributionItem]
    health_distribution: List[DistributionItem]
    revenue_at_risk: Dict[str, Any]

class SegmentStats(BaseModel):
    segment_name: str
    customer_count: int
    avg_clv: float
    avg_churn_risk: float

class SegmentationResponse(BaseModel):
    segments: List[SegmentStats]
    migrations: List[Dict[str, Any]]
    health_comparison: Dict[str, Any]

class CustomerListItem(BaseModel):
    customer_id: int
    segment_name: Optional[str]
    health_score: Optional[float]  # Health score in 0-100 range
    health_band: Optional[str]
    churn_probability: Optional[float]
    clv_12m: Optional[float]
    investment_priority: Optional[str]
    
class CustomerListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[CustomerListItem]

class AlertsResponse(BaseModel):
    high_risk_churn: int
    dropped_health: int
    high_value_risk: int
    details: List[Dict[str, Any]]
