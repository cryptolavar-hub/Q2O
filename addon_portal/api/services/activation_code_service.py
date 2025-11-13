"""Service functions for activation code generation and management."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import List, Optional

import hashlib
import secrets
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from ..core.logging import get_logger
from ..core.settings import settings
from ..models.licensing import ActivationCode, Tenant

LOGGER = get_logger(__name__)


def _hash_code(code: str) -> str:
    """Hash activation code for secure storage."""
    return hashlib.sha256((settings.ACTIVATION_CODE_PEPPER + code).encode()).hexdigest()


def _generate_activation_code() -> str:
    """Generate human-readable activation code (e.g., 12RY-S55W-4MZR-KP2J).
    
    Uses alphanumeric characters excluding ambiguous ones (I, O, 0, 1)
    to avoid user confusion.
    """
    chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # No ambiguous chars
    parts = []
    for _ in range(4):
        part = ''.join(secrets.choice(chars) for _ in range(4))
        parts.append(part)
    return '-'.join(parts)


def generate_codes(
    session: Session,
    tenant_id: int,
    count: int,
    *,
    ttl_days: Optional[int] = None,
    label: Optional[str] = None,
    max_uses: int = 1,
) -> List[str]:
    """Generate activation codes for a tenant.
    
    Args:
        session: Active database session.
        tenant_id: ID of the tenant to generate codes for.
        count: Number of codes to generate.
        ttl_days: Optional expiration time in days.
        label: Optional label for the codes.
        max_uses: Maximum number of uses per code (default: 1).
    
    Returns:
        List of plain-text activation codes (e.g., ["12RY-S55W-4MZR-KP2J", ...]).
    
    Raises:
        InvalidOperationError: If code generation fails.
    """
    from ..core.exceptions import InvalidOperationError
    
    try:
        # Verify tenant exists
        tenant = session.query(Tenant).filter(Tenant.id == tenant_id).first()
        if not tenant:
            raise InvalidOperationError(f"Tenant {tenant_id} not found.")
        
        # Calculate expiration
        expires_at = None
        if ttl_days:
            expires_at = datetime.utcnow() + timedelta(days=ttl_days)
        
        generated_codes = []
        
        for _ in range(count):
            # Generate random code (format: XXXX-XXXX-XXXX-XXXX)
            code_plain = _generate_activation_code()
            
            # Create code record
            new_code = ActivationCode(
                tenant_id=tenant_id,
                code_plain=code_plain,
                code_hash=_hash_code(code_plain),
                label=label,
                expires_at=expires_at,
                max_uses=max_uses,
                use_count=0,
                revoked_at=None,
            )
            
            session.add(new_code)
            generated_codes.append(code_plain)
        
        session.commit()
        LOGGER.info(
            "activation_codes_generated",
            extra={
                "tenant_id": tenant_id,
                "count": count,
                "label": label,
            },
        )
        
        return generated_codes
    
    except SQLAlchemyError as exc:
        session.rollback()
        LOGGER.error(
            "activation_code_generation_failed",
            extra={"tenant_id": tenant_id, "count": count, "error": str(exc)},
        )
        raise InvalidOperationError("Failed to generate activation codes.") from exc

