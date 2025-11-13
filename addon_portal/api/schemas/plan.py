"""
Plan Schema - Response models for subscription plans.
"""

from pydantic import BaseModel, ConfigDict, Field


def _to_camel(string: str) -> str:
    """Convert snake_case to camelCase."""
    parts = string.split("_")
    return parts[0] + "".join(part.capitalize() for part in parts[1:])


class PlanResponse(BaseModel):
    """Response schema for a subscription plan."""
    
    model_config = ConfigDict(alias_generator=_to_camel, populate_by_name=True)
    
    id: int
    name: str
    stripe_price_id: str
    monthly_run_quota: int


class PlanCollectionResponse(BaseModel):
    """Collection of subscription plans."""
    
    plans: list[PlanResponse]

