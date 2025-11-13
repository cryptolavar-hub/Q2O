"""Tenant authentication service for OTP and session management."""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, func, select, update
from sqlalchemy.orm import Session

from ..core.exceptions import InvalidOperationError, TenantNotFoundError
from ..core.logging import get_logger
from ..core.settings import settings
from ..models.licensing import Tenant, TenantSession

LOGGER = get_logger(__name__)

# OTP configuration
OTP_LENGTH = 6
OTP_VALIDITY_MINUTES = 10
OTP_RATE_LIMIT_PER_HOUR = 3

# Session configuration
SESSION_IDLE_TIMEOUT_MINUTES = 30
SESSION_MAX_LIFETIME_HOURS = 24


def generate_otp(tenant_slug: str, session: Session) -> str:
    """Generate and store an OTP for tenant authentication.
    
    Args:
        tenant_slug: Tenant slug identifier.
        session: Database session.
        
    Returns:
        The generated OTP code (6 digits).
        
    Raises:
        TenantNotFoundError: If tenant doesn't exist.
        InvalidOperationError: If rate limit exceeded.
    """
    # Find tenant
    tenant = session.scalar(select(Tenant).where(Tenant.slug == tenant_slug))
    if not tenant:
        raise TenantNotFoundError(f"Tenant not found: {tenant_slug}")
    
    # Check rate limit (max 3 OTPs per hour per tenant)
    one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
    recent_otps = session.scalar(
        select(func.count(TenantSession.id))
        .where(
            TenantSession.tenant_id == tenant.id,
            TenantSession.otp_code.isnot(None),
            TenantSession.created_at >= one_hour_ago,
        )
    ) or 0
    
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
    session.flush()
    
    LOGGER.info(
        "otp_generated",
        extra={
            "tenant_id": tenant.id,
            "tenant_slug": tenant_slug,
            "session_id": tenant_session.id,
            "otp_expires_at": otp_expires_at.isoformat(),
        },
    )
    
    return otp_code


def verify_otp(tenant_slug: str, otp_code: str, session: Session) -> str:
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
    tenant = session.scalar(select(Tenant).where(Tenant.slug == tenant_slug))
    if not tenant:
        raise TenantNotFoundError(f"Tenant not found: {tenant_slug}")
    
    # Find valid OTP session
    now = datetime.now(timezone.utc)
    tenant_session = session.scalar(
        select(TenantSession)
        .where(
            TenantSession.tenant_id == tenant.id,
            TenantSession.otp_code == otp_code,
            TenantSession.otp_expires_at > now,
            TenantSession.expires_at > now,
        )
        .order_by(TenantSession.created_at.desc())
    )
    
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
    session.flush()
    
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


def validate_session(session_token: str, session: Session) -> dict:
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
    
    # Find session
    tenant_session = session.scalar(
        select(TenantSession)
        .join(Tenant)
        .where(
            TenantSession.session_token == session_token,
            TenantSession.expires_at > now,
        )
    )
    
    if not tenant_session:
        raise InvalidOperationError("Invalid or expired session.")
    
    # Check idle timeout (30 minutes)
    idle_timeout = timedelta(minutes=SESSION_IDLE_TIMEOUT_MINUTES)
    if tenant_session.last_activity + idle_timeout < now:
        LOGGER.info(
            "session_idle_timeout",
            extra={
                "tenant_id": tenant_session.tenant_id,
                "session_id": tenant_session.id,
                "last_activity": tenant_session.last_activity.isoformat(),
            },
        )
        raise InvalidOperationError("Session expired due to inactivity.")
    
    # Update last activity
    tenant_session.last_activity = now
    session.flush()
    
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


def refresh_session(session_token: str, session: Session) -> dict:
    """Refresh session expiration time.
    
    Args:
        session_token: Current session token.
        session: Database session.
        
    Returns:
        Updated session info with new expiration.
        
    Raises:
        InvalidOperationError: If session is invalid.
    """
    session_info = validate_session(session_token, session)
    
    # Extend expiration (up to max lifetime)
    now = datetime.now(timezone.utc)
    created_at = datetime.fromisoformat(session_info["created_at"].replace("Z", "+00:00"))
    max_expires = created_at + timedelta(hours=SESSION_MAX_LIFETIME_HOURS)
    new_expires = min(now + timedelta(hours=SESSION_MAX_LIFETIME_HOURS), max_expires)
    
    tenant_session = session.get(TenantSession, session_info["session_id"])
    tenant_session.expires_at = new_expires
    tenant_session.last_activity = now
    session.flush()
    
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


def logout(session_token: str, session: Session) -> None:
    """Invalidate a session.
    
    Args:
        session_token: Session token to invalidate.
        session: Database session.
    """
    tenant_session = session.scalar(
        select(TenantSession).where(TenantSession.session_token == session_token)
    )
    
    if tenant_session:
        session.delete(tenant_session)
        session.flush()
        
        LOGGER.info(
            "session_logged_out",
            extra={
                "tenant_id": tenant_session.tenant_id,
                "session_id": tenant_session.id,
            },
        )


def cleanup_expired_sessions(session: Session) -> int:
    """Clean up expired sessions (call periodically).
    
    Args:
        session: Database session.
        
    Returns:
        Number of sessions deleted.
    """
    now = datetime.now(timezone.utc)
    deleted = session.execute(
        delete(TenantSession).where(TenantSession.expires_at <= now)
    ).rowcount
    session.commit()
    
    if deleted > 0:
        LOGGER.info("expired_sessions_cleaned", extra={"count": deleted})
    
    return deleted

