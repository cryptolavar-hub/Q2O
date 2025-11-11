"""
Admin API Router - JSON endpoints for React Admin Portal
Provides CRUD operations for Tenants, Activation Codes, and Devices
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from ..deps import get_db
from ..models.licensing import ActivationCode, Device, Tenant, SubscriptionState
from ..schemas.tenant import (
    SortDirection,
    TenantCollectionResponse,
    TenantCreatePayload,
    TenantResponse,
    TenantSortField,
    TenantUpdatePayload,
)
from ..services.tenant_service import create_tenant, delete_tenant, get_tenant_by_slug, list_tenants, update_tenant
from ..core.logging import get_logger
from ..core.exceptions import TenantNotFoundError

router = APIRouter(prefix="/admin/api", tags=["admin_api"])
LOGGER = get_logger(__name__)


# ============================================================================
# DASHBOARD STATS ENDPOINT
# ============================================================================

@router.get("/dashboard-stats")
async def get_dashboard_stats(db: Session = Depends(get_db)):
    """Get dashboard statistics for the main admin page."""
    
    # Count activation codes by status
    all_codes = db.query(ActivationCode).all()
    total_codes = len(all_codes)
    active_codes = sum(1 for c in all_codes if c.revoked_at is None and (c.expires_at is None or c.expires_at > datetime.now()) and c.use_count < c.max_uses)
    expired_codes = sum(1 for c in all_codes if c.expires_at and c.expires_at <= datetime.now())
    revoked_codes = sum(1 for c in all_codes if c.revoked_at is not None)
    
    # Count devices
    all_devices = db.query(Device).all()
    total_devices = len(all_devices)
    active_devices = sum(1 for d in all_devices if not d.is_revoked)
    revoked_devices = sum(1 for d in all_devices if d.is_revoked)
    
    # Count tenants
    all_tenants = db.query(Tenant).all()
    total_tenants = len(all_tenants)
    # Determine active tenants (has active subscription)
    active_tenants = 0
    for tenant in all_tenants:
        if tenant.subscriptions:
            for sub in tenant.subscriptions:
                if sub.state and sub.state.value == 'active':
                    active_tenants += 1
                    break
    
    # Calculate success rate (codes successfully used vs total codes)
    used_codes = sum(1 for c in all_codes if c.used_at is not None)
    success_rate = (used_codes / total_codes * 100) if total_codes > 0 else 0
    
    # Calculate trends (this week vs last week)
    now = datetime.now()
    week_ago = now - timedelta(days=7)
    two_weeks_ago = now - timedelta(days=14)
    
    # Codes created this week vs last week
    codes_this_week = sum(1 for c in all_codes if c.created_at >= week_ago)
    codes_last_week = sum(1 for c in all_codes if two_weeks_ago <= c.created_at < week_ago)
    codes_trend = ((codes_this_week - codes_last_week) / codes_last_week * 100) if codes_last_week > 0 else (100 if codes_this_week > 0 else 0)
    
    # Devices activated this week vs last week
    devices_this_week = sum(1 for d in all_devices if d.created_at >= week_ago)
    devices_last_week = sum(1 for d in all_devices if two_weeks_ago <= d.created_at < week_ago)
    devices_trend = ((devices_this_week - devices_last_week) / devices_last_week * 100) if devices_last_week > 0 else (100 if devices_this_week > 0 else 0)
    
    # Tenants created this week vs last week
    tenants_this_week = sum(1 for t in all_tenants if t.created_at >= week_ago)
    tenants_last_week = sum(1 for t in all_tenants if two_weeks_ago <= t.created_at < week_ago)
    tenants_trend = ((tenants_this_week - tenants_last_week) / tenants_last_week * 100) if tenants_last_week > 0 else (100 if tenants_this_week > 0 else 0)
    
    # Success rate trend (this week vs last week)
    codes_used_this_week = sum(1 for c in all_codes if c.used_at and c.used_at >= week_ago)
    codes_used_last_week = sum(1 for c in all_codes if c.used_at and two_weeks_ago <= c.used_at < week_ago)
    success_this_week = (codes_used_this_week / codes_this_week * 100) if codes_this_week > 0 else 0
    success_last_week = (codes_used_last_week / codes_last_week * 100) if codes_last_week > 0 else 0
    success_trend = success_this_week - success_last_week
    
    return {
        "totalCodes": total_codes,
        "activeCodes": active_codes,
        "expiredCodes": expired_codes,
        "revokedCodes": revoked_codes,
        "totalDevices": total_devices,
        "activeDevices": active_devices,
        "revokedDevices": revoked_devices,
        "totalTenants": total_tenants,
        "activeTenants": active_tenants,
        "successRate": round(success_rate, 1),
        "trends": {
            "codes": {
                "value": round(abs(codes_trend), 1),
                "direction": "up" if codes_trend >= 0 else "down"
            },
            "devices": {
                "value": round(abs(devices_trend), 1),
                "direction": "up" if devices_trend >= 0 else "down"
            },
            "tenants": {
                "value": round(abs(tenants_trend), 1),
                "direction": "up" if tenants_trend >= 0 else "down"
            },
            "successRate": {
                "value": round(abs(success_trend), 1),
                "direction": "up" if success_trend >= 0 else "down"
            }
        }
    }


# ============================================================================
# PYDANTIC MODELS
# ============================================================================


class ActivationCodeGenerate(BaseModel):
    tenant_slug: str
    count: int = 1
    ttl_days: Optional[int] = 365
    label: Optional[str] = None
    max_uses: int = 1


# ============================================================================
# TENANT ENDPOINTS
# ============================================================================

@router.get("/tenants", response_model=TenantCollectionResponse)
async def get_tenants(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    search: Optional[str] = Query(None, max_length=200),
    status: Optional[SubscriptionState] = Query(None),
    sort_field: TenantSortField = Query(TenantSortField.CREATED_AT),
    sort_direction: SortDirection = Query(SortDirection.DESC),
) -> TenantCollectionResponse:
    """Return a paginated collection of tenants.

    Args:
        db: Injected database session.
        page: Page number (1-indexed).
        page_size: Number of records per page.
        search: Optional case-insensitive search term.
        status: Optional subscription status filter.
        sort_field: Field to sort by.
        sort_direction: Direction of sort.

    Returns:
        A paginated tenant collection.
    """

    LOGGER.info(
        "list_tenants_request",
        extra={
            "page": page,
            "pageSize": page_size,
            "search": search,
            "status": status.value if status else None,
            "sortField": sort_field.value,
            "sortDirection": sort_direction.value,
        },
    )
    return list_tenants(
        db,
        page=page,
        page_size=page_size,
        search=search,
        status=status,
        sort_field=sort_field,
        sort_direction=sort_direction,
    )


@router.get("/tenants/{tenant_slug}", response_model=TenantResponse)
async def get_tenant(tenant_slug: str, db: Session = Depends(get_db)) -> TenantResponse:
    """Return a single tenant by slug."""

    try:
        return get_tenant_by_slug(db, tenant_slug)
    except TenantNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error.message) from error


@router.post("/tenants", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
async def create_tenant_endpoint(payload: TenantCreatePayload, db: Session = Depends(get_db)) -> TenantResponse:
    """Create a tenant and return the persisted record."""

    LOGGER.info("create_tenant_request", extra={"slug": payload.slug})
    return create_tenant(db, payload)


@router.put("/tenants/{tenant_slug}", response_model=TenantResponse)
async def update_tenant_endpoint(
    tenant_slug: str,
    payload: TenantUpdatePayload,
    db: Session = Depends(get_db),
) -> TenantResponse:
    """Update tenant details and return the updated record."""

    LOGGER.info("update_tenant_request", extra={"slug": tenant_slug})
    return update_tenant(db, tenant_slug, payload)


@router.delete("/tenants/{tenant_slug}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tenant_endpoint(tenant_slug: str, db: Session = Depends(get_db)) -> None:
    """Delete the requested tenant."""

    LOGGER.info("delete_tenant_request", extra={"slug": tenant_slug})
    delete_tenant(db, tenant_slug)


# ============================================================================
# ACTIVATION CODE ENDPOINTS
# ============================================================================

@router.get("/codes")
async def get_all_codes(
    db: Session = Depends(get_db),
    tenant_slug: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None
):
    """Get all activation codes with optional filtering."""
    
    query = db.query(ActivationCode).join(Tenant)
    
    if tenant_slug:
        query = query.filter(Tenant.slug == tenant_slug)
    
    if status:
        # Calculate status based on expires_at, used_at, revoked
        # This is simplified - in production, you'd have a status column
        pass  # Status filtering logic here
    
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (ActivationCode.code_plain.ilike(search_pattern)) |
            (Tenant.name.ilike(search_pattern))
        )
    
    codes = query.all()
    
    result = []
    for code in codes:
        # Determine status
        status_value = 'active'
        if code.revoked_at is not None:
            status_value = 'revoked'
        elif code.expires_at and code.expires_at < datetime.now():
            status_value = 'expired'
        elif code.use_count >= code.max_uses:
            status_value = 'used'
        
        result.append({
            "id": code.id,
            "code": code.code_plain,
            "tenant": code.tenant.name,
            "tenantSlug": code.tenant.slug,
            "label": code.label,
            "status": status_value,
            "expiresAt": code.expires_at.isoformat() if code.expires_at else None,
            "usedAt": code.used_at.isoformat() if code.used_at else None,
            "createdAt": code.created_at.isoformat() if code.created_at else None,
            "useCount": code.use_count,
            "maxUses": code.max_uses
        })
    
    return {"codes": result, "total": len(result)}


@router.post("/codes/generate")
async def generate_codes_json(data: ActivationCodeGenerate, db: Session = Depends(get_db)):
    """Generate activation codes (JSON API version)."""
    
    # Find tenant
    tenant = db.query(Tenant).filter(Tenant.slug == data.tenant_slug).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    # Generate codes
    import secrets
    generated_codes = []
    
    for _ in range(data.count):
        # Generate random code (format: XXXX-XXXX-XXXX-XXXX)
        code_plain = '-'.join([
            secrets.token_hex(2).upper()[:4]
            for _ in range(4)
        ])
        
        # Calculate expiration
        expires_at = None
        if data.ttl_days:
            expires_at = datetime.now() + timedelta(days=data.ttl_days)
        
        # Create code
        new_code = ActivationCode(
            tenant_id=tenant.id,
            code_plain=code_plain,
            code_hash=code_plain,  # In production, hash this properly
            label=data.label,
            expires_at=expires_at,
            max_uses=data.max_uses,
            use_count=0,
            revoked=False
        )
        
        db.add(new_code)
        generated_codes.append(code_plain)
    
    db.commit()
    
    return {
        "success": True,
        "message": f"Generated {data.count} codes successfully",
        "codes": generated_codes
    }


@router.delete("/codes/{code_id}")
async def delete_code(code_id: int, db: Session = Depends(get_db)):
    """Delete/revoke an activation code."""
    
    code = db.query(ActivationCode).filter(ActivationCode.id == code_id).first()
    
    if not code:
        raise HTTPException(status_code=404, detail="Code not found")
    
    # Mark as revoked instead of deleting
    code.revoked_at = datetime.now()
    db.commit()
    
    return {
        "success": True,
        "message": "Code revoked successfully"
    }


# ============================================================================
# DEVICE ENDPOINTS
# ============================================================================

@router.get("/devices")
async def get_all_devices(
    db: Session = Depends(get_db),
    tenant_slug: Optional[str] = None,
    search: Optional[str] = None
):
    """Get all devices with optional filtering."""
    
    query = db.query(Device).join(Tenant)
    
    if tenant_slug:
        query = query.filter(Tenant.slug == tenant_slug)
    
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (Device.label.ilike(search_pattern)) |
            (Device.hw_fingerprint.ilike(search_pattern)) |
            (Tenant.name.ilike(search_pattern))
        )
    
    devices = query.all()
    
    result = []
    for device in devices:
        result.append({
            "id": device.id,
            "tenant": device.tenant.name,
            "tenantSlug": device.tenant.slug,
            "label": device.label,
            "hwFingerprint": device.hw_fingerprint,
            "deviceType": "desktop",  # Field doesn't exist in model - default value
            "lastSeen": device.last_seen.isoformat() if device.last_seen else None,
            "createdAt": device.created_at.isoformat() if device.created_at else None,
            "isRevoked": device.is_revoked
        })
    
    return {"devices": result, "total": len(result)}


@router.delete("/devices/{device_id}")
async def revoke_device(device_id: int, db: Session = Depends(get_db)):
    """Revoke a device."""
    
    device = db.query(Device).filter(Device.id == device_id).first()
    
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    # Mark as revoked
    device.is_revoked = True
    db.commit()
    
    return {
        "success": True,
        "message": "Device revoked successfully"
    }


