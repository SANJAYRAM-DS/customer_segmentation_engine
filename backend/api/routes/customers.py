from fastapi import APIRouter, Query
from backend.caching.loader import loader
from backend.api.schemas import CustomerListResponse
from typing import Optional
import os

router = APIRouter()

DEFAULT_PAGE_SIZE = int(os.getenv("DEFAULT_PAGE_SIZE", "50"))
MAX_PAGE_SIZE = int(os.getenv("MAX_PAGE_SIZE", "1000"))

@router.get("/", response_model=CustomerListResponse)
def get_customers(
    page: int = 1,
    page_size: int = DEFAULT_PAGE_SIZE,
    segment: Optional[str] = None,
    health_band: Optional[str] = None,
    priority: Optional[str] = None,
    sort_by: str = "clv_12m",
    ascending: bool = False
):
    # Clamp page size
    page_size = min(page_size, MAX_PAGE_SIZE)

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
