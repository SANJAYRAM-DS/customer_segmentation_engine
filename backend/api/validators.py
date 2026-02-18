"""
API Input Validators
Pydantic validators for API request validation and sanitization
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List
from enum import Enum


class SortOrder(str, Enum):
    """Sort order enumeration"""
    ASC = "asc"
    DESC = "desc"


class HealthBand(str, Enum):
    """Health band enumeration"""
    CRITICAL = "Critical"
    AT_RISK = "At Risk"
    HEALTHY = "Healthy"
    CHAMPION = "Champion"


class InvestmentPriority(str, Enum):
    """Investment priority enumeration"""
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class CustomerListRequest(BaseModel):
    """Validated customer list request parameters"""
    page: int = Field(default=1, ge=1, le=10000, description="Page number (1-indexed)")
    page_size: int = Field(default=50, ge=1, le=1000, description="Items per page (max 1000)")
    segment: Optional[str] = Field(default=None, max_length=100)
    health_band: Optional[HealthBand] = None
    priority: Optional[InvestmentPriority] = None
    sort_by: str = Field(default="clv_12m", max_length=50)
    ascending: bool = False
    
    @validator('sort_by')
    def validate_sort_field(cls, v):
        """Validate sort field is allowed"""
        allowed_fields = [
            'customer_id', 'segment_name', 'health_band', 
            'churn_probability', 'clv_12m', 'investment_priority',
            'health_score', 'tenure_days', 'recency_days'
        ]
        if v not in allowed_fields:
            raise ValueError(f"Invalid sort field. Allowed: {', '.join(allowed_fields)}")
        return v
    
    @validator('segment')
    def sanitize_segment(cls, v):
        """Sanitize segment name"""
        if v is None:
            return v
        # Remove potentially dangerous characters
        return v.strip()


class CustomerIdRequest(BaseModel):
    """Validated customer ID request"""
    customer_id: int = Field(..., ge=1, le=999999999, description="Customer ID (positive integer)")


class ExportRequest(BaseModel):
    """Validated export request parameters"""
    format: str = Field(default="csv", regex="^(csv|json|excel)$")
    segment: Optional[str] = Field(default=None, max_length=100)
    health_band: Optional[HealthBand] = None
    priority: Optional[InvestmentPriority] = None
    include_pii: bool = Field(default=False, description="Include PII (requires admin role)")
    max_rows: int = Field(default=10000, ge=1, le=100000, description="Maximum rows to export")
    
    @validator('segment')
    def sanitize_segment(cls, v):
        """Sanitize segment name"""
        if v is None:
            return v
        return v.strip()


class DateRangeRequest(BaseModel):
    """Validated date range request"""
    start_date: Optional[str] = Field(default=None, regex=r"^\d{4}-\d{2}-\d{2}$")
    end_date: Optional[str] = Field(default=None, regex=r"^\d{4}-\d{2}-\d{2}$")
    
    @validator('end_date')
    def validate_date_range(cls, v, values):
        """Ensure end_date is after start_date"""
        if v and 'start_date' in values and values['start_date']:
            if v < values['start_date']:
                raise ValueError("end_date must be after start_date")
        return v


class PredictionRequest(BaseModel):
    """Validated prediction request"""
    customer_ids: List[int] = Field(..., min_items=1, max_items=1000)
    model_version: Optional[str] = Field(default=None, max_length=20)
    
    @validator('customer_ids')
    def validate_customer_ids(cls, v):
        """Validate customer IDs"""
        # Check for duplicates
        if len(v) != len(set(v)):
            raise ValueError("Duplicate customer IDs not allowed")
        
        # Check range
        for cid in v:
            if cid < 1 or cid > 999999999:
                raise ValueError(f"Invalid customer ID: {cid}")
        
        return v


class SearchRequest(BaseModel):
    """Validated search request"""
    query: str = Field(..., min_length=1, max_length=200)
    limit: int = Field(default=50, ge=1, le=500)
    
    @validator('query')
    def sanitize_query(cls, v):
        """Sanitize search query"""
        # Remove potentially dangerous characters
        dangerous_chars = ['<', '>', '"', "'", ';', '&', '|']
        for char in dangerous_chars:
            v = v.replace(char, '')
        return v.strip()


def validate_page_params(page: int, page_size: int) -> tuple:
    """
    Validate and sanitize pagination parameters
    
    Args:
        page: Page number (1-indexed)
        page_size: Items per page
        
    Returns:
        Tuple of (validated_page, validated_page_size)
        
    Raises:
        ValueError: If parameters are invalid
    """
    # Validate page
    if page < 1:
        raise ValueError("Page must be >= 1")
    if page > 10000:
        raise ValueError("Page must be <= 10000")
    
    # Validate page_size
    if page_size < 1:
        raise ValueError("Page size must be >= 1")
    if page_size > 1000:
        raise ValueError("Page size must be <= 1000 (use export for larger datasets)")
    
    return page, page_size


def validate_customer_id(customer_id: int) -> int:
    """
    Validate customer ID
    
    Args:
        customer_id: Customer ID to validate
        
    Returns:
        Validated customer ID
        
    Raises:
        ValueError: If customer ID is invalid
    """
    if customer_id < 1:
        raise ValueError("Customer ID must be positive")
    if customer_id > 999999999:
        raise ValueError("Customer ID too large")
    
    return customer_id


def sanitize_string(value: str, max_length: int = 200) -> str:
    """
    Sanitize string input
    
    Args:
        value: String to sanitize
        max_length: Maximum allowed length
        
    Returns:
        Sanitized string
    """
    if not value:
        return value
    
    # Remove dangerous characters
    dangerous_chars = ['<', '>', '"', "'", ';', '&', '|', '\x00']
    for char in dangerous_chars:
        value = value.replace(char, '')
    
    # Trim whitespace
    value = value.strip()
    
    # Enforce max length
    if len(value) > max_length:
        value = value[:max_length]
    
    return value


if __name__ == "__main__":
    print("API Input Validators")
    print("\nAvailable validators:")
    print("  - CustomerListRequest")
    print("  - CustomerIdRequest")
    print("  - ExportRequest")
    print("  - DateRangeRequest")
    print("  - PredictionRequest")
    print("  - SearchRequest")
    print("\nHelper functions:")
    print("  - validate_page_params()")
    print("  - validate_customer_id()")
    print("  - sanitize_string()")
