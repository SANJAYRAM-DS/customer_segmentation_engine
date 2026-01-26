from fastapi import APIRouter, Query
from backend.caching.loader import loader
from backend.api.schemas import CustomerListResponse
from typing import Optional

router = APIRouter()

@router.get("/", response_model=CustomerListResponse)
def get_customers(
    page: int = 1,
    page_size: int = 50,
    segment: Optional[str] = None,
    health_band: Optional[str] = None,
    priority: Optional[str] = None,
    sort_by: str = "clv_12m",
    ascending: bool = False
):
    filters = {}
    if segment: filters["segment_name"] = segment
    if health_band: filters["health_band"] = health_band
    if priority: filters["investment_priority"] = priority

    return loader.get_customer_list(
        page=page,
        page_size=page_size,
        filters=filters,
        sort_by=sort_by,
        ascending=ascending
    )

@router.get("/{customer_id}")
def get_customer_profile(customer_id: int):
    details = loader.get_customer_details(customer_id)
    if details:
        return details
    return {"error": "Customer not found"}
