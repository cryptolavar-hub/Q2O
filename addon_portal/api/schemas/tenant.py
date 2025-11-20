"""Pydantic schemas for tenant management and project operations."""

from __future__ import annotations

import re
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator, HttpUrl


def _to_camel(s: str) -> str:
    """Convert snake_case to camelCase."""
    parts = s.split("_")
    return parts[0] + "".join(word.capitalize() for word in parts[1:])


HEX_COLOR_PATTERN = re.compile(r"^#(?:[0-9a-fA-F]{3}){1,2}$")
SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class SortDirection(str, Enum):
    """Supported sort directions for tenant datasets."""

    ASC = "asc"
    DESC = "desc"


class TenantSortField(str, Enum):
    """Supported sort fields for tenant datasets."""

    NAME = "name"
    SLUG = "slug"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"
    USAGE = "usage"


class TenantCreatePayload(BaseModel):
    """Request payload for creating a tenant."""

    model_config = ConfigDict(alias_generator=_to_camel, populate_by_name=True, extra="forbid")

    name: str = Field(..., min_length=1, max_length=255, description="Tenant name")
    slug: str = Field(..., min_length=1, max_length=100, description="Unique tenant slug")
    logo_url: Optional[str] = Field(None, max_length=500, description="URL to tenant logo")
    primary_color: Optional[str] = Field(None, max_length=7, description="Primary brand color (hex)")
    domain: Optional[str] = Field(None, max_length=255, description="Tenant domain")
    email: Optional[str] = Field(None, max_length=255, description="Primary email for OTP delivery")
    phone_number: Optional[str] = Field(None, max_length=50, description="Phone number for SMS/WhatsApp OTP")
    otp_delivery_method: Optional[str] = Field("email", max_length=20, description="OTP delivery method: email, sms, whatsapp")
    usage_quota: int = Field(10, ge=1, le=100000)
    subscription_plan: str = Field(..., description="Subscription plan name (e.g., 'Starter', 'Pro', 'Enterprise')")
    plan_id: Optional[int] = Field(None, description="Subscription plan ID (alternative to subscription_plan)")

    @field_validator("email")
    @classmethod
    def validate_email(cls, v):
        if v and "@" not in v:
            raise ValueError("Invalid email format")
        return v

    @field_validator("otp_delivery_method")
    @classmethod
    def validate_otp_delivery_method(cls, v):
        if v and v not in ["email", "sms", "whatsapp", "both"]:
            raise ValueError("otp_delivery_method must be one of: email, sms, whatsapp, both")
        return v


class TenantUpdatePayload(BaseModel):
    """Request payload for updating a tenant."""

    model_config = ConfigDict(alias_generator=_to_camel, populate_by_name=True, extra="forbid")

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    logo_url: Optional[str] = Field(None, max_length=500)
    primary_color: Optional[str] = Field(None, max_length=7)
    domain: Optional[str] = Field(None, max_length=255)
    email: Optional[str] = Field(None, max_length=255)
    phone_number: Optional[str] = Field(None, max_length=50)
    usage_quota: Optional[int] = Field(None, ge=1, le=100000)
    subscription_plan: Optional[str] = Field(None, description="Subscription plan name (e.g., 'Starter', 'Pro', 'Enterprise')")


class TenantSubscriptionInfo(BaseModel):
    """Nested model for tenant subscription information."""

    model_config = ConfigDict(alias_generator=_to_camel, populate_by_name=True)

    plan_name: Optional[str] = None
    status: Optional[str] = None


class TenantResponse(BaseModel):
    """Response model for tenant data."""

    model_config = ConfigDict(alias_generator=_to_camel, populate_by_name=True)

    id: int
    name: str
    slug: str
    logo_url: Optional[str] = None
    primary_color: Optional[str] = None
    domain: Optional[str] = None
    email: Optional[str] = None
    phone_number: Optional[str] = None
    usage_quota: int
    usage_current: int
    activation_codes_total: int = 0  # Total activation codes for this tenant
    activation_codes_used: int = 0  # Number of codes that have been used (use_count > 0)
    created_at: str
    updated_at: str
    subscription: TenantSubscriptionInfo


class TenantCollectionResponse(BaseModel):
    """Response model for a collection of tenants with pagination."""

    model_config = ConfigDict(alias_generator=_to_camel, populate_by_name=True)

    items: List[TenantResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class TenantProjectCreatePayload(BaseModel):
    """Request payload for creating a tenant project (simplified for frontend)."""

    model_config = ConfigDict(alias_generator=_to_camel, populate_by_name=True, extra="forbid")

    name: str = Field(..., min_length=1, max_length=100, description="Project name")
    client_name: Optional[str] = Field(None, max_length=255, description="Client name")
    description: Optional[str] = Field(None, description="Project description")
    objectives: Optional[str] = Field(None, description="Project objectives")


class TenantProjectUpdatePayload(BaseModel):
    """Request payload for updating a tenant project."""

    model_config = ConfigDict(alias_generator=_to_camel, populate_by_name=True, extra="forbid")

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    client_name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    objectives: Optional[str] = None


class ActivationCodeAssignPayload(BaseModel):
    """Request payload for assigning an activation code to a project."""

    model_config = ConfigDict(alias_generator=_to_camel, populate_by_name=True, extra="forbid")

    activation_code: str = Field(..., min_length=1, description="Activation code to assign")
