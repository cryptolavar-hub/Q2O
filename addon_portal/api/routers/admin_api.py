"""
Admin API Router - JSON endpoints for React Admin Portal
Provides CRUD operations for Tenants, Activation Codes, and Devices
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta

from ..deps import get_db
from ..models.licensing import Tenant, ActivationCode, Device

router = APIRouter(prefix="/admin/api", tags=["admin_api"])


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
                if sub.status == 'active':
                    active_tenants += 1
                    break
    
    # Calculate success rate (codes successfully used vs total codes)
    used_codes = sum(1 for c in all_codes if c.used_at is not None)
    success_rate = (used_codes / total_codes * 100) if total_codes > 0 else 0
    
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
        "successRate": round(success_rate, 1)
    }


# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class TenantCreate(BaseModel):
    name: str
    slug: str
    logo_url: Optional[str] = None
    primary_color: str = "#875A7B"
    domain: Optional[str] = None
    subscription_plan: str = "Starter"
    usage_quota: int = 10


class TenantUpdate(BaseModel):
    name: Optional[str] = None
    logo_url: Optional[str] = None
    primary_color: Optional[str] = None
    domain: Optional[str] = None
    subscription_plan: Optional[str] = None
    usage_quota: Optional[int] = None


class ActivationCodeGenerate(BaseModel):
    tenant_slug: str
    count: int = 1
    ttl_days: Optional[int] = 365
    label: Optional[str] = None
    max_uses: int = 1


# ============================================================================
# TENANT ENDPOINTS
# ============================================================================

@router.get("/tenants")
async def get_all_tenants(
    db: Session = Depends(get_db),
    search: Optional[str] = None,
    status: Optional[str] = None
):
    """Get all tenants with optional filtering."""
    
    query = db.query(Tenant)
    
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (Tenant.name.ilike(search_pattern)) |
            (Tenant.slug.ilike(search_pattern))
        )
    
    tenants = query.all()
    
    result = []
    for tenant in tenants:
        # Get subscription from relationship
        subscription = tenant.subscriptions[0] if tenant.subscriptions else None
        
        result.append({
            "id": tenant.id,
            "name": tenant.name,
            "slug": tenant.slug,
            "logoUrl": tenant.logo_url,
            "primaryColor": tenant.primary_color,
            "domain": tenant.domain,
            "subscriptionPlan": subscription.plan.name if subscription and subscription.plan else "None",
            "subscriptionStatus": subscription.status if subscription else "none",
            "usageQuota": tenant.usage_quota,
            "usageCurrent": tenant.usage_current,
            "createdAt": tenant.created_at.isoformat() if tenant.created_at else None
        })
    
    return {"tenants": result, "total": len(result)}


@router.get("/tenants/{tenant_slug}")
async def get_tenant(tenant_slug: str, db: Session = Depends(get_db)):
    """Get a single tenant by slug."""
    
    tenant = db.query(Tenant).filter(Tenant.slug == tenant_slug).first()
    
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    subscription = tenant.subscriptions[0] if tenant.subscriptions else None
    
    return {
        "id": tenant.id,
        "name": tenant.name,
        "slug": tenant.slug,
        "logoUrl": tenant.logo_url,
        "primaryColor": tenant.primary_color,
        "domain": tenant.domain,
        "subscriptionPlan": subscription.plan.name if subscription and subscription.plan else "None",
        "subscriptionStatus": subscription.status if subscription else "none",
        "usageQuota": tenant.usage_quota,
        "usageCurrent": tenant.usage_current,
        "createdAt": tenant.created_at.isoformat() if tenant.created_at else None
    }


@router.post("/tenants")
async def create_tenant(data: TenantCreate, db: Session = Depends(get_db)):
    """Create a new tenant."""
    
    # Check if slug already exists
    existing = db.query(Tenant).filter(Tenant.slug == data.slug).first()
    if existing:
        raise HTTPException(status_code=400, detail="Tenant slug already exists")
    
    # Create tenant
    new_tenant = Tenant(
        name=data.name,
        slug=data.slug,
        logo_url=data.logo_url,
        primary_color=data.primary_color,
        domain=data.domain,
        usage_quota=data.usage_quota,
        usage_current=0
    )
    
    db.add(new_tenant)
    db.commit()
    db.refresh(new_tenant)
    
    return {
        "success": True,
        "message": "Tenant created successfully",
        "tenantId": new_tenant.id,
        "slug": new_tenant.slug
    }


@router.put("/tenants/{tenant_slug}")
async def update_tenant(
    tenant_slug: str,
    data: TenantUpdate,
    db: Session = Depends(get_db)
):
    """Update an existing tenant."""
    
    tenant = db.query(Tenant).filter(Tenant.slug == tenant_slug).first()
    
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    # Update fields
    if data.name is not None:
        tenant.name = data.name
    if data.logo_url is not None:
        tenant.logo_url = data.logo_url
    if data.primary_color is not None:
        tenant.primary_color = data.primary_color
    if data.domain is not None:
        tenant.domain = data.domain
    if data.usage_quota is not None:
        tenant.usage_quota = data.usage_quota
    
    db.commit()
    
    return {
        "success": True,
        "message": "Tenant updated successfully"
    }


@router.delete("/tenants/{tenant_slug}")
async def delete_tenant(tenant_slug: str, db: Session = Depends(get_db)):
    """Delete a tenant."""
    
    tenant = db.query(Tenant).filter(Tenant.slug == tenant_slug).first()
    
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    db.delete(tenant)
    db.commit()
    
    return {
        "success": True,
        "message": "Tenant deleted successfully"
    }


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


