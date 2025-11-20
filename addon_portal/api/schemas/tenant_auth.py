"""Pydantic schemas for tenant authentication."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class OTPGenerateRequest(BaseModel):
    """Request to generate OTP for tenant login."""

    tenant_slug: str = Field(..., min_length=3, max_length=100, description="Tenant slug identifier")


class OTPGenerateResponse(BaseModel):
    """Response after generating OTP.
    
    Note: OTP code is NOT included in the response for security reasons.
    The OTP is sent directly to the tenant's email or phone number.
    """

    otp_code: str = Field("", description="Always empty - OTP is sent via email/SMS, not returned in API")
    expires_in: int = Field(600, description="OTP validity in seconds (10 minutes)")
    message: str = Field(
        default="OTP has been sent to your registered email or phone number.",
        description="User-friendly message about OTP delivery"
    )


class OTPVerifyRequest(BaseModel):
    """Request to verify OTP and get session token."""

    tenant_slug: str = Field(..., min_length=3, max_length=100)
    otp_code: str = Field(..., min_length=6, max_length=6, description="6-digit OTP code")


class OTPVerifyResponse(BaseModel):
    """Response with session token."""

    session_token: str = Field(..., description="Session token for authenticated requests")
    expires_at: str = Field(..., description="ISO 8601 timestamp when session expires")
    tenant_id: int
    tenant_slug: str


class SessionInfoResponse(BaseModel):
    """Current session information."""

    tenant_id: int
    tenant_slug: str
    expires_at: str
    created_at: str


class SessionRefreshResponse(BaseModel):
    """Refreshed session information."""

    session_token: str
    expires_at: str
    tenant_id: int
    tenant_slug: str

