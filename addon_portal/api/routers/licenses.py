from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..deps import get_db, current_identity
from ..models.licensing import Tenant, Subscription, Device, SubscriptionState
from ..schemas.licensing import Policy, Branding, HeartbeatRequest
from datetime import datetime

router = APIRouter(prefix="/licenses", tags=["licenses"])

@router.get("/policy", response_model=Policy)
async def get_policy(identity = Depends(current_identity), db: AsyncSession = Depends(get_db)):
    sub = identity.get("sub","")
    try:
        _, tenant_id_str, _, device_id_str = sub.split(":")
        tenant_id = int(tenant_id_str); device_id = int(device_id_str)
    except Exception:
        raise HTTPException(401, "bad token subject")
    result = await db.execute(
        select(Device).where(Device.id == device_id, Device.tenant_id == tenant_id, Device.is_revoked == False)
    )
    device = result.scalar_one_or_none()
    if not device: raise HTTPException(401, "device revoked")
    result = await db.execute(select(Subscription).where(Subscription.tenant_id == tenant_id))
    subs = result.scalar_one_or_none()
    return Policy(plan_name=subs.plan.name, monthly_run_quota=subs.plan.monthly_run_quota, subscription_state=subs.state.value)

@router.post("/heartbeat")
async def heartbeat(body: HeartbeatRequest, identity = Depends(current_identity), db: AsyncSession = Depends(get_db)):
    sub = identity.get("sub","")
    _, tenant_id_str, _, device_id_str = sub.split(":")
    tenant_id = int(tenant_id_str); device_id = int(device_id_str)
    result = await db.execute(select(Device).where(Device.id == device_id, Device.tenant_id == tenant_id))
    device = result.scalar_one_or_none()
    if not device: raise HTTPException(401, "device not found")
    if device.is_revoked: raise HTTPException(401, "device revoked")
    device.last_seen = datetime.utcnow()
    db.add(device)
    await db.commit()
    return {"ok": True}

@router.get("/branding/{tenant_slug}", response_model=Branding)
async def get_branding(tenant_slug: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Tenant).where(Tenant.slug == tenant_slug))
    tenant = result.scalar_one_or_none()
    if not tenant: raise HTTPException(404, "tenant not found")
    return Branding(logo_url=tenant.logo_url, primary_color=tenant.primary_color, domain=tenant.domain)
