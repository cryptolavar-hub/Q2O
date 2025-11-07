from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..deps import get_db, current_identity
from ..models.licensing import Tenant, Subscription, Device, SubscriptionState
from ..schemas.licensing import Policy, Branding, HeartbeatRequest
from datetime import datetime

router = APIRouter(prefix="/licenses", tags=["licenses"])

@router.get("/policy", response_model=Policy)
def get_policy(identity = Depends(current_identity), db: Session = Depends(get_db)):
    sub = identity.get("sub","")
    try:
        _, tenant_id_str, _, device_id_str = sub.split(":")
        tenant_id = int(tenant_id_str); device_id = int(device_id_str)
    except Exception:
        raise HTTPException(401, "bad token subject")
    device = db.query(Device).filter_by(id=device_id, tenant_id=tenant_id, is_revoked=False).first()
    if not device: raise HTTPException(401, "device revoked")
    subs = db.query(Subscription).filter_by(tenant_id=tenant_id).first()
    return Policy(plan_name=subs.plan.name, monthly_run_quota=subs.plan.monthly_run_quota, subscription_state=subs.state.value)

@router.post("/heartbeat")
def heartbeat(body: HeartbeatRequest, identity = Depends(current_identity), db: Session = Depends(get_db)):
    sub = identity.get("sub","")
    _, tenant_id_str, _, device_id_str = sub.split(":")
    tenant_id = int(tenant_id_str); device_id = int(device_id_str)
    device = db.query(Device).filter_by(id=device_id, tenant_id=tenant_id).first()
    if not device: raise HTTPException(401, "device not found")
    if device.is_revoked: raise HTTPException(401, "device revoked")
    device.last_seen = datetime.utcnow(); db.add(device); db.commit()
    return {"ok": True}

@router.get("/branding/{tenant_slug}", response_model=Branding)
def get_branding(tenant_slug: str, db: Session = Depends(get_db)):
    tenant = db.query(Tenant).filter_by(slug=tenant_slug).first()
    if not tenant: raise HTTPException(404, "tenant not found")
    return Branding(logo_url=tenant.logo_url, primary_color=tenant.primary_color, domain=tenant.domain)
