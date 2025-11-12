"""Pydantic schemas for tenant management in the licensing API."""

from __future__ import annotations

import re
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator

from ..models.licensing import SubscriptionState


def _to_camel(string: str) -> str:
    parts = string.split("_")
    return parts[0] + "".join(part.capitalize() for part in parts[1:])


HEX_COLOR_PATTERN = re.compile(r"^#(?:[0-9a-fA-F]{3}){1,2}$")
SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class SortDirection(str, Enum):
    """Supported sort directions for tenant datasets."""

    ASC = "asc"
    DESC = "desc"


class TenantSortField(str, Enum):
    """Supported sort fields for tenant datasets."""

    CREATED_AT = "created_at"
    NAME = "name"
    USAGE = "usage_current"


class TenantCreatePayload(BaseModel):
    """Request payload for creating a tenant."""

    model_config = ConfigDict(alias_generator=_to_camel, populate_by_name=True, extra="forbid")

    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=3, max_length=100)
    logo_url: Optional[HttpUrl] = None
    primary_color: str = Field("#875A7B", description="Brand primary color in hex format.")
    domain: Optional[str] = Field(None, max_length=255, description="Tenant primary domain without schema.")
    subscription_plan: str = Field(..., min_length=1, max_length=100)
    usage_quota: int = Field(10, ge=1, le=100000)

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, value: str) -> str:
        if not SLUG_PATTERN.match(value):
            raise ValueError("Slug must contain lowercase letters, numbers, and hyphens only.")
        return value

    @field_validator("primary_color")
    @classmethod
    def validate_primary_color(cls, value: str) -> str:
        if not HEX_COLOR_PATTERN.match(value):
            raise ValueError("Primary color must be a valid hexadecimal color code (e.g., #AABBCC).")
        return value.upper()

    @field_validator("domain")
    @classmethod
    def normalize_domain(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        normalized = value.strip().lower()
        if not normalized:
            return None
        if "/" in normalized or "http" in normalized:
            raise ValueError("Domain should not include protocol or path components.")
        return normalized


class TenantUpdatePayload(BaseModel):
    """Request payload for updating a tenant."""

    model_config = ConfigDict(alias_generator=_to_camel, populate_by_name=True, extra="forbid")

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    logo_url: Optional[HttpUrl] = None
    primary_color: Optional[str] = None
    domain: Optional[str] = Field(None, max_length=255)
    subscription_plan: Optional[str] = Field(None, min_length=1, max_length=100)
    usage_quota: Optional[int] = Field(None, ge=1, le=100000)

    @field_validator("primary_color")
    @classmethod
    def validate_primary_color(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        if not HEX_COLOR_PATTERN.match(value):
            raise ValueError("Primary color must be a valid hexadecimal color code (e.g., #AABBCC).")
        return value.upper()

    @field_validator("domain")
    @classmethod
    def normalize_domain(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        normalized = value.strip().lower()
        if not normalized:
            return None
        if "/" in normalized or "http" in normalized:
            raise ValueError("Domain should not include protocol or path components.")
        return normalized


class SubscriptionSummary(BaseModel):
    """Response schema for summarizing a tenant subscription."""

    model_config = ConfigDict(alias_generator=_to_camel, populate_by_name=True)

    plan_name: Optional[str] = None
    status: Optional[SubscriptionState] = None


class TenantResponse(BaseModel):
    """Response schema representing a tenant record."""

    model_config = ConfigDict(alias_generator=_to_camel, populate_by_name=True)

    id: int
    name: str
    slug: str
    logo_url: Optional[str] = None
    primary_color: Optional[str] = None
    domain: Optional[str] = None
    usage_quota: int
    usage_current: int
    created_at: str
    subscription: SubscriptionSummary


class TenantCollectionResponse(BaseModel):
    """Paginated response containing tenant records."""

    model_config = ConfigDict(alias_generator=_to_camel, populate_by_name=True)

    items: List[TenantResponse]
    total: int
    page: int
    page_size: int
