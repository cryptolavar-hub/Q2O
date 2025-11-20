from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..deps import get_db
from ..models.licensing import Tenant, Subscription, Device, SubscriptionState, ActivationCode
from ..schemas.licensing import ActivationRequest, TokenPair
from ..core.security import issue_access_token
from ..core.settings import settings
import hashlib
from datetime import datetime

router = APIRouter(prefix="/authz", tags=["authz"])

def _hash_code(code: str) -> str:
    return hashlib.sha256((settings.ACTIVATION_CODE_PEPPER + code).encode()).hexdigest()

@router.post("/activate", response_model=TokenPair)
async def activate(req: ActivationRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Tenant).where(Tenant.slug == req.tenant_slug))
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(404, "tenant not found")

    result = await db.execute(select(Subscription).where(Subscription.tenant_id == tenant.id))
    subs = result.scalar_one_or_none()
    if not subs or subs.state not in (SubscriptionState.active, SubscriptionState.trialing):
        raise HTTPException(403, "subscription not active")

    # Validate code
    result = await db.execute(
        select(ActivationCode).where(
            ActivationCode.tenant_id == tenant.id,
            ActivationCode.code_hash == _hash_code(req.activation_code)
        )
    )
    code = result.scalar_one_or_none()
    if not code: raise HTTPException(400, "invalid activation code")
    if code.revoked_at: raise HTTPException(400, "activation code revoked")
    if code.expires_at and code.expires_at < datetime.utcnow(): raise HTTPException(400, "activation code expired")
    if code.max_uses is not None and code.use_count >= code.max_uses: raise HTTPException(400, "activation code already used")

    fpr = hashlib.sha256(req.hw_fingerprint.encode()).hexdigest()
    result = await db.execute(
        select(Device).where(Device.tenant_id == tenant.id, Device.hw_fingerprint == fpr)
    )
    device = result.scalar_one_or_none()
    if not device:
        device = Device(tenant_id=tenant.id, hw_fingerprint=fpr)
        db.add(device)
        await db.commit()
        await db.refresh(device)

    access = issue_access_token(tenant.id, device.id, subs.plan.name, subs.plan.monthly_run_quota, subs.state.value)
    refresh_plain = hashlib.sha256(f"{device.id}:{req.activation_code}".encode()).hexdigest()
    device.refresh_token_hash = hashlib.sha256(refresh_plain.encode()).hexdigest()

    code.use_count += 1
    if code.max_uses == 1 and code.used_at is None:
        code.used_at = datetime.utcnow()

    await db.commit()
    return TokenPair(access_token=access, refresh_token=refresh_plain, expires_in=settings.JWT_ACCESS_TTL_SECONDS)

@router.post("/refresh", response_model=TokenPair)
async def refresh(tenant_slug: str, device_id: int, refresh_token: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Tenant).where(Tenant.slug == tenant_slug))
    tenant = result.scalar_one_or_none()
    if not tenant: raise HTTPException(404, "tenant not found")
    result = await db.execute(select(Device).where(Device.id == device_id, Device.tenant_id == tenant.id))
    device = result.scalar_one_or_none()
    if not device or device.is_revoked: raise HTTPException(401, "device not found or revoked")
    import hashlib as _h
    if device.refresh_token_hash != _h.sha256(refresh_token.encode()).hexdigest(): raise HTTPException(401, "invalid refresh token")
    result = await db.execute(select(Subscription).where(Subscription.tenant_id == tenant.id))
    subs = result.scalar_one_or_none()
    from ..core.settings import settings as _s
    access = issue_access_token(tenant.id, device.id, subs.plan.name, subs.plan.monthly_run_quota, subs.state.value)
    return TokenPair(access_token=access, refresh_token=refresh_token, expires_in=_s.JWT_ACCESS_TTL_SECONDS)
