from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..deps import get_db
from ..models.licensing import Tenant, MonthlyUsageRollup, Subscription
from ..utils.timezone_utils import now_in_server_tz

router = APIRouter(prefix="/usage", tags=["usage"])

@router.get("/{tenant_slug}")
async def get_usage(tenant_slug: str, db: AsyncSession = Depends(get_db)):
    """Get tenant usage statistics for current month in server timezone."""
    result = await db.execute(select(Tenant).where(Tenant.slug == tenant_slug))
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(404, "tenant not found")
    # Use configured server timezone for date calculations
    today = now_in_server_tz()
    result = await db.execute(
        select(MonthlyUsageRollup).where(
            MonthlyUsageRollup.tenant_id == tenant.id,
            MonthlyUsageRollup.year == today.year,
            MonthlyUsageRollup.month == today.month
        )
    )
    roll = result.scalar_one_or_none()
    runs = roll.runs if roll else 0
    result = await db.execute(select(Subscription).where(Subscription.tenant_id == tenant.id))
    sub = result.scalar_one_or_none()
    quota = sub.plan.monthly_run_quota if sub and sub.plan else 0
    plan = sub.plan.name if sub and sub.plan else None
    return {"tenant": tenant.slug, "year": today.year, "month": today.month, "runs": runs, "quota": quota, "plan": plan}
