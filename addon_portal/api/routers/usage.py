from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from ..deps import get_db
from ..models.licensing import Tenant, MonthlyUsageRollup, Subscription

router = APIRouter(prefix="/usage", tags=["usage"])

@router.get("/{tenant_slug}")
def get_usage(tenant_slug: str, db: Session = Depends(get_db)):
    tenant = db.query(Tenant).filter_by(slug=tenant_slug).first()
    if not tenant:
        raise HTTPException(404, "tenant not found")
    today = datetime.utcnow()
    roll = db.query(MonthlyUsageRollup).filter_by(tenant_id=tenant.id, year=today.year, month=today.month).first()
    runs = roll.runs if roll else 0
    sub = db.query(Subscription).filter_by(tenant_id=tenant.id).first()
    quota = sub.plan.monthly_run_quota if sub and sub.plan else 0
    plan = sub.plan.name if sub and sub.plan else None
    return {"tenant": tenant.slug, "year": today.year, "month": today.month, "runs": runs, "quota": quota, "plan": plan}
