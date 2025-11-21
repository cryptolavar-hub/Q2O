"""
Billing Schema - Response models for tenant billing information.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field


def _to_camel(string: str) -> str:
    """Convert snake_case to camelCase."""
    parts = string.split("_")
    return parts[0] + "".join(part.capitalize() for part in parts[1:])


class SubscriptionBillingInfo(BaseModel):
    """Subscription billing information."""
    
    model_config = ConfigDict(alias_generator=_to_camel, populate_by_name=True)
    
    plan_name: str
    plan_tier: Optional[str] = None
    monthly_price: Optional[float] = None
    status: str
    next_billing_date: Optional[str] = None
    auto_renewal: bool = True
    stripe_subscription_id: Optional[str] = None
    stripe_customer_id: Optional[str] = None
    current_period_start: Optional[str] = None
    current_period_end: Optional[str] = None


class UsageQuotaInfo(BaseModel):
    """Usage and quota information."""
    
    model_config = ConfigDict(alias_generator=_to_camel, populate_by_name=True)
    
    monthly_run_quota: int
    current_month_usage: int
    usage_percentage: float
    activation_codes_total: int
    activation_codes_used: int
    activation_codes_remaining: int
    activation_codes_percentage: float


class BillingHistoryItem(BaseModel):
    """Single billing history item (invoice/payment)."""
    
    model_config = ConfigDict(alias_generator=_to_camel, populate_by_name=True)
    
    id: str
    date: str
    amount: float
    status: str  # paid, pending, failed
    description: str
    invoice_url: Optional[str] = None
    payment_method_last4: Optional[str] = None


class BillingResponse(BaseModel):
    """Complete billing information response."""
    
    model_config = ConfigDict(alias_generator=_to_camel, populate_by_name=True)
    
    subscription: SubscriptionBillingInfo
    usage: UsageQuotaInfo
    billing_history: List[BillingHistoryItem] = []


class PlanUpgradeRequest(BaseModel):
    """Request to upgrade/downgrade subscription plan."""
    
    model_config = ConfigDict(alias_generator=_to_camel, populate_by_name=True)
    
    plan_id: int
    immediate: bool = False  # If true, change immediately; if false, change at next billing cycle


class ActivationCodePurchaseRequest(BaseModel):
    """Request to purchase additional activation codes."""
    
    model_config = ConfigDict(alias_generator=_to_camel, populate_by_name=True)
    
    quantity: int = Field(..., ge=1, le=100, description="Number of codes to purchase")
    label: Optional[str] = Field(None, max_length=255, description="Optional label for the codes")


class ActivationCodePurchaseResponse(BaseModel):
    """Response after purchasing activation codes."""
    
    model_config = ConfigDict(alias_generator=_to_camel, populate_by_name=True)
    
    success: bool
    codes_generated: int
    codes: List[str] = []  # Only returned if admin or for testing
    total_cost: float
    message: str

