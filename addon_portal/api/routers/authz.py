from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
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
def activate(req: ActivationRequest, db: Session = Depends(get_db)):
    tenant = db.query(Tenant).filter_by(slug=req.tenant_slug).first()
    if not tenant:
        raise HTTPException(404, "tenant not found")

    subs = db.query(Subscription).filter_by(tenant_id=tenant.id).first()
    if not subs or subs.state not in (SubscriptionState.active, SubscriptionState.trialing):
        raise HTTPException(403, "subscription not active")

    # Validate code
    code = db.query(ActivationCode).filter_by(tenant_id=tenant.id, code_hash=_hash_code(req.activation_code)).first()
    if not code: raise HTTPException(400, "invalid activation code")
    if code.revoked_at: raise HTTPException(400, "activation code revoked")
    if code.expires_at and code.expires_at < datetime.utcnow(): raise HTTPException(400, "activation code expired")
    if code.max_uses is not None and code.use_count >= code.max_uses: raise HTTPException(400, "activation code already used")

    fpr = hashlib.sha256(req.hw_fingerprint.encode()).hexdigest()
    device = db.query(Device).filter_by(tenant_id=tenant.id, hw_fingerprint=fpr).first()
    if not device:
        device = Device(tenant_id=tenant.id, hw_fingerprint=fpr)
        db.add(device); db.commit(); db.refresh(device)

    access = issue_access_token(tenant.id, device.id, subs.plan.name, subs.plan.monthly_run_quota, subs.state.value)
    refresh_plain = hashlib.sha256(f"{device.id}:{req.activation_code}".encode()).hexdigest()
    device.refresh_token_hash = hashlib.sha256(refresh_plain.encode()).hexdigest()

    code.use_count += 1
    if code.max_uses == 1 and code.used_at is None:
        code.used_at = datetime.utcnow()

    db.commit()
    return TokenPair(access_token=access, refresh_token=refresh_plain, expires_in=settings.JWT_ACCESS_TTL_SECONDS)

@router.post("/refresh", response_model=TokenPair)
def refresh(tenant_slug: str, device_id: int, refresh_token: str, db: Session = Depends(get_db)):
    tenant = db.query(Tenant).filter_by(slug=tenant_slug).first()
    if not tenant: raise HTTPException(404, "tenant not found")
    device = db.query(Device).filter_by(id=device_id, tenant_id=tenant.id).first()
    if not device or device.is_revoked: raise HTTPException(401, "device not found or revoked")
    import hashlib as _h
    if device.refresh_token_hash != _h.sha256(refresh_token.encode()).hexdigest(): raise HTTPException(401, "invalid refresh token")
    subs = db.query(Subscription).filter_by(tenant_id=tenant.id).first()
    from ..core.settings import settings as _s
    access = issue_access_token(tenant.id, device.id, subs.plan.name, subs.plan.monthly_run_quota, subs.state.value)
    return TokenPair(access_token=access, refresh_token=refresh_token, expires_in=_s.JWT_ACCESS_TTL_SECONDS)
