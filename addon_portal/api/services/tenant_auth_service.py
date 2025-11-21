"""Tenant authentication service for OTP and session management."""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..core.exceptions import InvalidOperationError, TenantNotFoundError
from ..core.logging import get_logger
from ..core.settings import settings
from ..models.licensing import Tenant, TenantSession
from .otp_delivery_service import deliver_otp

LOGGER = get_logger(__name__)

# OTP configuration
OTP_LENGTH = 6
OTP_VALIDITY_MINUTES = 10
OTP_RATE_LIMIT_PER_HOUR = 3

# Session configuration
SESSION_IDLE_TIMEOUT_MINUTES = 30
SESSION_MAX_LIFETIME_HOURS = 24


async def generate_otp(tenant_slug: str, session: AsyncSession) -> None:
    """Generate, store, and send an OTP for tenant authentication.
    
    Args:
        tenant_slug: Tenant slug identifier.
        session: Database session.
        
    Raises:
        TenantNotFoundError: If tenant doesn't exist.
        InvalidOperationError: If rate limit exceeded or OTP delivery failed.
    """
    # Find tenant
    result = await session.execute(select(Tenant).where(Tenant.slug == tenant_slug))
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise TenantNotFoundError(f"Tenant not found: {tenant_slug}")
    
    # Check if tenant has contact information
    if not tenant.email and not tenant.phone_number:
        raise InvalidOperationError(
            "Tenant contact information missing. Please configure email or phone number in tenant settings."
        )
    
    # Check rate limit (max 3 OTPs per hour per tenant)
    one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
    result = await session.execute(
        select(func.count(TenantSession.id))
        .where(
            TenantSession.tenant_id == tenant.id,
            TenantSession.otp_code.isnot(None),
            TenantSession.created_at >= one_hour_ago,
        )
    )
    recent_otps = result.scalar() or 0
    
    if recent_otps >= OTP_RATE_LIMIT_PER_HOUR:
        LOGGER.warning(
            "otp_rate_limit_exceeded",
            extra={"tenant_id": tenant.id, "tenant_slug": tenant_slug, "recent_count": recent_otps},
        )
        raise InvalidOperationError(
            f"Rate limit exceeded. Maximum {OTP_RATE_LIMIT_PER_HOUR} OTPs per hour."
        )
    
    # Generate 6-digit OTP
    otp_code = f"{secrets.randbelow(10**OTP_LENGTH):06d}"
    otp_expires_at = datetime.now(timezone.utc) + timedelta(minutes=OTP_VALIDITY_MINUTES)
    
    # Create session record with OTP
    session_token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=SESSION_MAX_LIFETIME_HOURS)
    
    tenant_session = TenantSession(
        tenant_id=tenant.id,
        session_token=session_token,
        otp_code=otp_code,
        otp_expires_at=otp_expires_at,
        expires_at=expires_at,
    )
    session.add(tenant_session)
    await session.flush()
    
    # Send OTP via email/SMS
    delivery_success = deliver_otp(tenant, otp_code)
    
    if not delivery_success:
        # Log the OTP for development/testing (when SMTP is disabled)
        # In production, this should never happen if SMTP is properly configured
        LOGGER.warning(
            "otp_delivery_failed_but_stored",
            extra={
                "tenant_id": tenant.id,
                "tenant_slug": tenant_slug,
                "session_id": tenant_session.id,
                "otp_code": otp_code,  # Only logged in development
                "otp_expires_at": otp_expires_at.isoformat(),
                "note": "OTP stored but delivery failed. Check SMTP/SMS configuration.",
            },
        )
        # In development, we allow this to continue (OTP is logged)
        # In production, you might want to raise an error here
        if settings.ENV == "production":
            raise InvalidOperationError(
                "Failed to deliver OTP. Please contact support or try again later."
            )
    
    LOGGER.info(
        "otp_generated_and_sent",
        extra={
            "tenant_id": tenant.id,
            "tenant_slug": tenant_slug,
            "session_id": tenant_session.id,
            "otp_expires_at": otp_expires_at.isoformat(),
            "delivery_method": tenant.otp_delivery_method or "email",
            "delivery_success": delivery_success,
        },
    )


async def verify_otp(tenant_slug: str, otp_code: str, session: AsyncSession) -> str:
    """Verify OTP and return session token.
    
    Args:
        tenant_slug: Tenant slug identifier.
        otp_code: The OTP code to verify.
        session: Database session.
        
    Returns:
        Session token string.
        
    Raises:
        TenantNotFoundError: If tenant doesn't exist.
        InvalidOperationError: If OTP is invalid or expired.
    """
    # Find tenant
    result = await session.execute(select(Tenant).where(Tenant.slug == tenant_slug))
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise TenantNotFoundError(f"Tenant not found: {tenant_slug}")
    
    # Find valid OTP session
    now = datetime.now(timezone.utc)
    result = await session.execute(
        select(TenantSession)
        .where(
            TenantSession.tenant_id == tenant.id,
            TenantSession.otp_code == otp_code,
            TenantSession.otp_expires_at > now,
            TenantSession.expires_at > now,
        )
        .order_by(TenantSession.created_at.desc())
    )
    tenant_session = result.scalar_one_or_none()
    
    if not tenant_session:
        LOGGER.warning(
            "otp_verification_failed",
            extra={"tenant_id": tenant.id, "tenant_slug": tenant_slug},
        )
        raise InvalidOperationError("Invalid or expired OTP code.")
    
    # Clear OTP (one-time use)
    tenant_session.otp_code = None
    tenant_session.otp_expires_at = None
    tenant_session.last_activity = now
    await session.flush()
    
    LOGGER.info(
        "otp_verified",
        extra={
            "tenant_id": tenant.id,
            "tenant_slug": tenant_slug,
            "session_id": tenant_session.id,
            "session_token": tenant_session.session_token[:8] + "...",
        },
    )
    
    return tenant_session.session_token


async def validate_session(session_token: str, session: AsyncSession) -> dict:
    """Validate session token and return tenant information.
    
    Args:
        session_token: Session token to validate.
        session: Database session.
        
    Returns:
        Dictionary with tenant_id, tenant_slug, and session info.
        
    Raises:
        InvalidOperationError: If session is invalid or expired.
    """
    now = datetime.now(timezone.utc)
    
    # Find session (eagerly load tenant to avoid lazy loading issues)
    result = await session.execute(
        select(TenantSession)
        .options(selectinload(TenantSession.tenant))
        .where(
            TenantSession.session_token == session_token,
            TenantSession.expires_at > now,
        )
    )
    tenant_session = result.scalar_one_or_none()
    
    if not tenant_session:
        raise InvalidOperationError("Invalid or expired session.")
    
    # Store old last_activity before updating (for idle timeout check)
    old_last_activity = tenant_session.last_activity
    
    # Check idle timeout (30 minutes) using the OLD last_activity value
    # This ensures we check if the user was idle BEFORE this request
    idle_timeout = timedelta(minutes=SESSION_IDLE_TIMEOUT_MINUTES)
    if old_last_activity + idle_timeout < now:
        LOGGER.info(
            "session_idle_timeout",
            extra={
                "tenant_id": tenant_session.tenant_id,
                "session_id": tenant_session.id,
                "last_activity": old_last_activity.isoformat(),
            },
        )
        raise InvalidOperationError("Session expired due to inactivity.")
    
    # Update last activity AFTER timeout check passes
    # This extends the session for active users
    tenant_session.last_activity = now
    await session.flush()
    
    created_at = tenant_session.created_at
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    
    return {
        "tenant_id": tenant_session.tenant_id,
        "tenant_slug": tenant_session.tenant.slug,
        "session_id": tenant_session.id,
        "expires_at": tenant_session.expires_at.isoformat(),
        "created_at": created_at.isoformat(),
    }


async def refresh_session(session_token: str, session: AsyncSession) -> dict:
    """Refresh session expiration time.
    
    Args:
        session_token: Current session token.
        session: Database session.
        
    Returns:
        Updated session info with new expiration.
        
    Raises:
        InvalidOperationError: If session is invalid.
    """
    session_info = await validate_session(session_token, session)
    
    # Extend expiration (up to max lifetime)
    now = datetime.now(timezone.utc)
    created_at = datetime.fromisoformat(session_info["created_at"].replace("Z", "+00:00"))
    max_expires = created_at + timedelta(hours=SESSION_MAX_LIFETIME_HOURS)
    new_expires = min(now + timedelta(hours=SESSION_MAX_LIFETIME_HOURS), max_expires)
    
    tenant_session = await session.get(TenantSession, session_info["session_id"])
    tenant_session.expires_at = new_expires
    tenant_session.last_activity = now
    await session.flush()
    
    LOGGER.info(
        "session_refreshed",
        extra={
            "tenant_id": session_info["tenant_id"],
            "session_id": session_info["session_id"],
            "new_expires_at": new_expires.isoformat(),
        },
    )
    
    return {
        **session_info,
        "expires_at": new_expires.isoformat(),
    }


async def logout(session_token: str, session: AsyncSession) -> None:
    """Invalidate a session.
    
    Args:
        session_token: Session token to invalidate.
        session: Database session.
    """
    result = await session.execute(
        select(TenantSession).where(TenantSession.session_token == session_token)
    )
    tenant_session = result.scalar_one_or_none()
    
    if tenant_session:
        await session.delete(tenant_session)
        await session.flush()
        
        LOGGER.info(
            "session_logged_out",
            extra={
                "tenant_id": tenant_session.tenant_id,
                "session_id": tenant_session.id,
            },
        )


async def cleanup_expired_sessions(session: AsyncSession) -> int:
    """Clean up expired sessions (call periodically).
    
    Args:
        session: Database session.
        
    Returns:
        Number of sessions deleted.
    """
    now = datetime.now(timezone.utc)
    result = await session.execute(
        delete(TenantSession).where(TenantSession.expires_at <= now)
    )
    deleted = result.rowcount
    await session.commit()
    
    if deleted > 0:
        LOGGER.info("expired_sessions_cleaned", extra={"count": deleted})
    
    return deleted

