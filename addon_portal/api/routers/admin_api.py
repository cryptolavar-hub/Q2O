"""
Admin API Router - JSON endpoints for React Admin Portal
Provides CRUD operations for Tenants, Activation Codes, and Devices
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import datetime, timedelta

from ..deps import get_db
from ..models.licensing import ActivationCode, Device, Tenant, SubscriptionState, Plan, Subscription
from ..models.llm_config import LLMProjectConfig
from ..models.events import PlatformEvent, EventType, EventSeverity
from ..schemas.tenant import (
    SortDirection,
    TenantCollectionResponse,
    TenantCreatePayload,
    TenantResponse,
    TenantSortField,
    TenantUpdatePayload,
)
from ..schemas.plan import PlanResponse, PlanCollectionResponse
from ..services.tenant_service import create_tenant, delete_tenant, get_tenant_by_slug, list_tenants, update_tenant
from ..core.logging import get_logger
from ..core.exceptions import TenantNotFoundError

router = APIRouter(prefix="/admin/api", tags=["admin_api"])
LOGGER = get_logger(__name__)
# Note: OPTIONS requests are handled by CORSOptionsMiddleware in main.py


# ============================================================================
# DASHBOARD STATS ENDPOINT
# ============================================================================

@router.get("/dashboard-stats")
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)):
    """Get dashboard statistics for the main admin page."""
    
    from ..utils.timezone_utils import now_in_server_tz, utc_to_server_tz
    from datetime import timezone as tz
    now_tz = now_in_server_tz()
    
    # Count activation codes by status
    result = await db.execute(select(ActivationCode))
    all_codes = result.scalars().all()
    total_codes = len(all_codes)
    # Convert timezone-naive expires_at (stored as UTC) to server timezone for comparison
    def _convert_expires_at(expires_at):
        """Convert timezone-naive expires_at (UTC) to server timezone."""
        if expires_at is None:
            return None
        if expires_at.tzinfo is None:
            # Assume UTC (as stored in database)
            return utc_to_server_tz(expires_at.replace(tzinfo=tz.utc))
        return utc_to_server_tz(expires_at)
    
    active_codes = sum(1 for c in all_codes if c.revoked_at is None and (c.expires_at is None or _convert_expires_at(c.expires_at) > now_tz) and c.use_count < c.max_uses)
    expired_codes = sum(1 for c in all_codes if c.expires_at and _convert_expires_at(c.expires_at) <= now_tz)
    revoked_codes = sum(1 for c in all_codes if c.revoked_at is not None)
    
    # Count devices
    result = await db.execute(select(Device))
    all_devices = result.scalars().all()
    total_devices = len(all_devices)
    active_devices = sum(1 for d in all_devices if not d.is_revoked)
    revoked_devices = sum(1 for d in all_devices if d.is_revoked)
    
    # Count projects (authorized projects = projects with activation_code_id set)
    result = await db.execute(select(LLMProjectConfig))
    all_projects = result.scalars().all()
    total_projects = len(all_projects)
    active_projects = sum(1 for p in all_projects if p.activation_code_id is not None)
    
    # Count tenants (eagerly load subscriptions to avoid lazy loading issues)
    result = await db.execute(
        select(Tenant).options(selectinload(Tenant.subscriptions).selectinload(Subscription.plan))
    )
    all_tenants = result.scalars().unique().all()
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
    
    # Calculate trends (this week vs last week) using configured server timezone
    from ..utils.timezone_utils import now_in_server_tz, utc_to_server_tz
    now = now_in_server_tz()
    week_ago = now - timedelta(days=7)
    two_weeks_ago = now - timedelta(days=14)
    
    # Codes created this week vs last week (compare in server timezone)
    codes_this_week = sum(1 for c in all_codes if utc_to_server_tz(c.created_at) >= week_ago)
    codes_last_week = sum(1 for c in all_codes if two_weeks_ago <= utc_to_server_tz(c.created_at) < week_ago)
    codes_trend = ((codes_this_week - codes_last_week) / codes_last_week * 100) if codes_last_week > 0 else (100 if codes_this_week > 0 else 0)
    
    # Devices activated this week vs last week
    devices_this_week = sum(1 for d in all_devices if utc_to_server_tz(d.created_at) >= week_ago)
    devices_last_week = sum(1 for d in all_devices if two_weeks_ago <= utc_to_server_tz(d.created_at) < week_ago)
    devices_trend = ((devices_this_week - devices_last_week) / devices_last_week * 100) if devices_last_week > 0 else (100 if devices_this_week > 0 else 0)
    
    # Projects activated this week vs last week (projects with activation_code_id set)
    projects_this_week = sum(1 for p in all_projects if p.activation_code_id and p.started_at and utc_to_server_tz(p.started_at) >= week_ago)
    projects_last_week = sum(1 for p in all_projects if p.activation_code_id and p.started_at and two_weeks_ago <= utc_to_server_tz(p.started_at) < week_ago)
    projects_trend = ((projects_this_week - projects_last_week) / projects_last_week * 100) if projects_last_week > 0 else (100 if projects_this_week > 0 else 0)
    
    # Tenants created this week vs last week
    tenants_this_week = sum(1 for t in all_tenants if utc_to_server_tz(t.created_at) >= week_ago)
    tenants_last_week = sum(1 for t in all_tenants if two_weeks_ago <= utc_to_server_tz(t.created_at) < week_ago)
    tenants_trend = ((tenants_this_week - tenants_last_week) / tenants_last_week * 100) if tenants_last_week > 0 else (100 if tenants_this_week > 0 else 0)
    
    # Success rate trend (this week vs last week)
    codes_used_this_week = sum(1 for c in all_codes if c.used_at and utc_to_server_tz(c.used_at) >= week_ago)
    codes_used_last_week = sum(1 for c in all_codes if c.used_at and two_weeks_ago <= utc_to_server_tz(c.used_at) < week_ago)
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
        "totalProjects": total_projects,
        "activeProjects": active_projects,
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
            "projects": {
                "value": round(abs(projects_trend), 1),
                "direction": "up" if projects_trend >= 0 else "down"
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


@router.get("/recent-activities")
async def get_recent_activities(
    db: AsyncSession = Depends(get_db),
    days: int = Query(7, ge=1, le=90, description="Number of days to look back")
):
    """Get recent activities from event log (database-backed event tracking).
    
    Returns all platform events (Major and Minor) from the event log.
    Events are categorized and include all platform changes.
    
    If the platform_events table doesn't exist yet (migration not run),
    returns empty list instead of failing.
    """
    
    from datetime import timedelta
    from sqlalchemy.exc import ProgrammingError, OperationalError
    from ..utils.timezone_utils import now_in_server_tz
    
    try:
        from ..models.events import PlatformEvent, EventType, EventSeverity
        
        # Use configured server timezone for date calculations
        now = now_in_server_tz()
        start_date = now - timedelta(days=days)
        
        # Fetch events from event log
        result = await db.execute(
            select(PlatformEvent)
            .where(PlatformEvent.created_at >= start_date)
            .order_by(PlatformEvent.created_at.desc())
            .limit(50)
        )
        events = result.scalars().all()
    except (ProgrammingError, OperationalError) as e:
        # Table doesn't exist yet - return empty list
        # This happens if migration 006 hasn't been run
        LOGGER.warning("platform_events table not found, returning empty activities", extra={"error": str(e)})
        return {"activities": []}
    
    # Map event types to icons and backdrops (using string values since event_type/severity are now strings)
    event_icons = {
        EventType.TENANT_CREATED.value: "👥",
        EventType.TENANT_UPDATED.value: "✏️",
        EventType.TENANT_DELETED.value: "🗑️",
        EventType.PROJECT_CREATED.value: "🚀",
        EventType.PROJECT_UPDATED.value: "📝",
        EventType.PROJECT_DELETED.value: "❌",
        EventType.CODE_GENERATED.value: "🔑",
        EventType.CODE_REVOKED.value: "🔒",
        EventType.CODE_ACTIVATED.value: "✅",
        EventType.DEVICE_ENROLLED.value: "📱",
        EventType.DEVICE_REVOKED.value: "🚫",
        EventType.USER_LOGIN.value: "🔐",
        EventType.USER_LOGOUT.value: "👋",
        EventType.SESSION_CREATED.value: "🎫",
        EventType.SESSION_EXPIRED.value: "⏰",
        EventType.CONFIG_UPDATED.value: "⚙️",
    }
    
    event_backdrops = {
        EventSeverity.MAJOR.value: {
            EventType.TENANT_CREATED.value: "bg-rose-100 text-rose-600",
            EventType.TENANT_UPDATED.value: "bg-blue-100 text-blue-600",
            EventType.TENANT_DELETED.value: "bg-red-100 text-red-600",
            EventType.PROJECT_CREATED.value: "bg-green-100 text-green-600",
            EventType.PROJECT_UPDATED.value: "bg-blue-100 text-blue-600",
            EventType.PROJECT_DELETED.value: "bg-red-100 text-red-600",
            EventType.CODE_GENERATED.value: "bg-indigo-100 text-indigo-600",
            EventType.CODE_REVOKED.value: "bg-amber-100 text-amber-600",
        },
        EventSeverity.MINOR.value: {
            EventType.CODE_ACTIVATED.value: "bg-emerald-100 text-emerald-600",
            EventType.DEVICE_ENROLLED.value: "bg-emerald-100 text-emerald-600",
            EventType.DEVICE_REVOKED.value: "bg-amber-100 text-amber-600",
            EventType.USER_LOGIN.value: "bg-purple-100 text-purple-600",
            EventType.USER_LOGOUT.value: "bg-gray-100 text-gray-600",
            EventType.SESSION_CREATED.value: "bg-blue-100 text-blue-600",
            EventType.SESSION_EXPIRED.value: "bg-yellow-100 text-yellow-600",
            EventType.CONFIG_UPDATED.value: "bg-cyan-100 text-cyan-600",
        }
    }
    
    activities = []
    for event in events:
        # event.event_type and event.severity are now strings, not enums
        icon = event_icons.get(event.event_type, "📋")
        backdrop = event_backdrops.get(event.severity, {}).get(event.event_type, "bg-gray-100 text-gray-600")
        
        # Get tenant name from relationship or metadata
        tenant_name = event.actor_name or (event.tenant.name if event.tenant else "Unknown")
        if event.tenant_id and not tenant_name:
            result = await db.execute(select(Tenant).where(Tenant.id == event.tenant_id))
            tenant = result.scalar_one_or_none()
            tenant_name = tenant.name if tenant else "Unknown"
        
        activities.append({
            "type": event.event_type,  # Already a string, no .value needed
            "icon": icon,
            "action": event.title,
            "tenant": tenant_name,
            "timestamp": event.created_at.isoformat() if event.created_at else None,
            "backdrop": backdrop,
            "severity": event.severity,  # Already a string, no .value needed
            "metadata": event.event_metadata or {},
        })
    
    # Sort by timestamp (most recent first) and limit to 20
    activities.sort(key=lambda x: x["timestamp"] or "", reverse=True)
    return {"activities": activities[:20]}


@router.get("/activation-trend")
async def get_activation_trend(
    db: AsyncSession = Depends(get_db),
    days: int = Query(30, ge=7, le=365, description="Number of days for trend")
):
    """Get activation trend data for dashboard chart (codes generated vs projects/devices activated)."""
    
    from datetime import timedelta, timezone as tz
    from sqlalchemy import func, and_
    from ..models.llm_config import LLMProjectConfig
    from ..utils.timezone_utils import now_in_server_tz, utc_to_server_tz, get_server_timezone
    
    # Use configured server timezone for date calculations
    now = now_in_server_tz()
    start_date = now - timedelta(days=days)
    
    # Fetch all codes, projects, and devices (we'll filter by date in Python for reliability)
    result = await db.execute(select(ActivationCode))
    all_codes = result.scalars().all()
    result = await db.execute(
        select(LLMProjectConfig).where(LLMProjectConfig.activation_code_id.isnot(None))
    )
    all_projects = result.scalars().all()
    result = await db.execute(select(Device).where(Device.is_revoked == False))
    all_devices = result.scalars().all()
    
    # Helper function to convert timezone-naive datetime (assumed UTC) to server timezone date
    def _get_date_in_server_tz(dt):
        """Convert timezone-naive datetime (assumed UTC) to server timezone and return date."""
        if dt is None:
            return None
        # If naive, assume UTC (as stored in database)
        if dt.tzinfo is None:
            dt_utc = dt.replace(tzinfo=tz.utc)
        else:
            dt_utc = dt
        # Convert to server timezone and extract date
        return utc_to_server_tz(dt_utc).date()
    
    trend_data = []
    current_date = start_date
    
    while current_date <= now:
        date_str = current_date.strftime('%b %d')
        date_only = current_date.date()
        
        # Codes generated on this date (count ALL codes, regardless of source - Admin Portal or Tenant Dashboard)
        codes_count = sum(1 for c in all_codes if _get_date_in_server_tz(c.created_at) == date_only)
        
        # Projects activated on this date (using activation codes)
        projects_count = sum(1 for p in all_projects if _get_date_in_server_tz(p.created_at) == date_only)
        
        # Devices activated on this date
        devices_count = sum(1 for d in all_devices if _get_date_in_server_tz(d.created_at) == date_only)
        
        trend_data.append({
            "date": date_str,
            "codes": codes_count,
            "projects": projects_count,
            "devices": devices_count,
        })
        
        current_date += timedelta(days=1)
    
    return {"trend": trend_data}


@router.get("/project-device-distribution")
async def get_project_device_distribution(db: AsyncSession = Depends(get_db)):
    """Get distribution of projects and devices for dashboard chart.
    
    Shows ALL projects (not just activated ones) to match Analytics page.
    """
    
    from ..models.llm_config import LLMProjectConfig
    
    # Count ALL active projects (not just activated with codes)
    result = await db.execute(
        select(func.count(LLMProjectConfig.id)).where(LLMProjectConfig.is_active == True)
    )
    active_projects = result.scalar()
    
    # Count total projects
    result = await db.execute(select(func.count(LLMProjectConfig.id)))
    total_projects = result.scalar()
    
    # Count active devices
    result = await db.execute(select(func.count(Device.id)).where(Device.is_revoked == False))
    active_devices = result.scalar()
    
    # Count revoked devices
    result = await db.execute(select(func.count(Device.id)).where(Device.is_revoked == True))
    revoked_devices = result.scalar()
    
    return {
        "projects": {
            "active": active_projects,
            "total": total_projects,
        },
        "devices": {
            "active": active_devices,
            "revoked": revoked_devices,
            "total": active_devices + revoked_devices,
        }
    }


@router.get("/analytics")
async def get_analytics(
    db: AsyncSession = Depends(get_db),
    date_range: str = Query("7d", regex="^(today|7d|30d|90d|1y)$"),
    project_filter: Optional[str] = Query(None, description="Filter by project: 'latest', 'top10', or specific project_id")
):
    """Get analytics data for charts and metrics."""
    
    from datetime import timedelta
    from sqlalchemy import func, and_, desc, text
    from ..models.licensing import Plan, Subscription, SubscriptionState
    from ..models.llm_config import LLMProjectConfig
    from ..utils.timezone_utils import now_in_server_tz, get_postgresql_timezone_string
    
    # Calculate date range using configured server timezone
    now = now_in_server_tz()
    tz_str = get_postgresql_timezone_string()
    
    # Calculate start_date based on date_range
    # For "today", start at midnight of today
    # For other ranges, go back N days from now
    if date_range == "today":
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif date_range == "7d":
        start_date = now - timedelta(days=7)
    elif date_range == "30d":
        start_date = now - timedelta(days=30)
    elif date_range == "90d":
        start_date = now - timedelta(days=90)
    else:  # 1y
        start_date = now - timedelta(days=365)
    
    # Get start_date as date (for filtering) - normalize to start of day
    start_date_normalized = start_date.replace(hour=0, minute=0, second=0, microsecond=0) if date_range != "today" else start_date
    start_date_only = start_date_normalized.date()
    now_date_only = now.date()
    
    # Activation trends (daily codes generated and devices activated)
    # Fetch all codes and devices, filter by date in Python for reliability
    from datetime import timezone as tz
    from ..utils.timezone_utils import utc_to_server_tz
    result = await db.execute(select(ActivationCode))
    all_codes_for_trend = result.scalars().all()
    result = await db.execute(select(Device))
    all_devices_for_trend = result.scalars().all()
    
    # Helper function to convert timezone-naive datetime (assumed UTC) to server timezone date
    def _get_date_in_server_tz_analytics(dt):
        """Convert timezone-naive datetime (assumed UTC) to server timezone and return date."""
        if dt is None:
            return None
        # If naive, assume UTC (as stored in database)
        if dt.tzinfo is None:
            dt_utc = dt.replace(tzinfo=tz.utc)
        else:
            dt_utc = dt
        # Convert to server timezone and extract date
        return utc_to_server_tz(dt_utc).date()
    
    # Filter codes and devices to only those within the date range
    filtered_codes = [
        c for c in all_codes_for_trend 
        if _get_date_in_server_tz_analytics(c.created_at) is not None 
        and start_date_only <= _get_date_in_server_tz_analytics(c.created_at) <= now_date_only
    ]
    filtered_devices = [
        d for d in all_devices_for_trend 
        if _get_date_in_server_tz_analytics(d.created_at) is not None 
        and start_date_only <= _get_date_in_server_tz_analytics(d.created_at) <= now_date_only
    ]
    
    # Build daily trend data
    activation_trend = []
    current_date = start_date_normalized
    while current_date <= now:
        date_str = current_date.strftime('%b %d')
        date_only = current_date.date()
        # Count codes and devices for this specific date
        codes_count = sum(1 for c in filtered_codes if _get_date_in_server_tz_analytics(c.created_at) == date_only)
        devices_count = sum(1 for d in filtered_devices if _get_date_in_server_tz_analytics(d.created_at) == date_only)
        activation_trend.append({
            "date": date_str,
            "codes": codes_count,
            "devices": devices_count
        })
        current_date += timedelta(days=1)
    
    # Tenant usage (current usage vs quota) - with project filtering
    tenant_usage = []
    # Eagerly load subscriptions to avoid lazy loading issues
    result = await db.execute(
        select(Tenant).options(selectinload(Tenant.subscriptions).selectinload(Subscription.plan))
    )
    all_tenants = result.scalars().unique().all()
    
    # Get projects based on filter
    filtered_projects = None
    if project_filter == "latest":
        # Get latest project only
        result = await db.execute(
            select(LLMProjectConfig).order_by(LLMProjectConfig.created_at.desc()).limit(1)
        )
        latest_project = result.scalar_one_or_none()
        if latest_project:
            result = await db.execute(
                select(LLMProjectConfig).where(LLMProjectConfig.id == latest_project.id)
            )
            filtered_projects = result.scalars().all()
        else:
            filtered_projects = []
    elif project_filter == "top10":
        # Get top 10 most recent projects
        result = await db.execute(
            select(LLMProjectConfig).order_by(LLMProjectConfig.created_at.desc()).limit(10)
        )
        filtered_projects = result.scalars().all()
    elif project_filter and project_filter.startswith("project:"):
        # Specific project ID
        project_id = project_filter.replace("project:", "")
        result = await db.execute(
            select(LLMProjectConfig).where(LLMProjectConfig.project_id == project_id)
        )
        filtered_projects = result.scalars().all()
    filtered_project_ids = {p.project_id for p in filtered_projects} if filtered_projects else None
    
    for tenant in all_tenants:
        # Get active subscription
        active_sub = None
        for sub in tenant.subscriptions:
            if sub.state and sub.state.value == 'active':
                active_sub = sub
                break
        
        if active_sub and active_sub.plan:
            # Calculate usage based on projects (if filter applied) or devices
            if filtered_project_ids:
                # Count projects for this tenant that match filter
                result = await db.execute(
                    select(func.count(LLMProjectConfig.id)).where(
                        and_(
                            LLMProjectConfig.tenant_id == tenant.id,
                            LLMProjectConfig.project_id.in_(filtered_project_ids)
                        )
                    )
                )
                usage = result.scalar()
            else:
                # Default: count devices (for backward compatibility)
                result = await db.execute(
                    select(func.count(Device.id)).where(
                        and_(Device.tenant_id == tenant.id, Device.is_revoked == False)
                    )
                )
                usage = result.scalar()
            
            quota = active_sub.plan.monthly_run_quota or 0
            
            # Only include if usage > 0 or if no filter (show all tenants)
            if usage > 0 or not project_filter:
                tenant_usage.append({
                    "tenant": tenant.name or tenant.slug,
                    "usage": usage,
                    "quota": quota
                })
    
    # Sort by usage descending and limit if needed
    tenant_usage.sort(key=lambda x: x["usage"], reverse=True)
    if not project_filter or project_filter == "top10":
        tenant_usage = tenant_usage[:10]  # Top 10
    
    # Subscription distribution
    subscription_distribution = []
    result = await db.execute(select(Plan))
    plans = result.scalars().all()
    for plan in plans:
        result = await db.execute(
            select(func.count(Subscription.id)).where(
                and_(
                    Subscription.plan_id == plan.id,
                    Subscription.state == SubscriptionState.active
                )
            )
        )
        count = result.scalar()
        if count > 0:
            # Assign colors based on plan name
            color_map = {
                'starter': '#4CAF50',
                'pro': '#9B59B6',
                'enterprise': '#FF6B9D',
            }
            color = color_map.get(plan.name.lower(), '#6B7280')
            subscription_distribution.append({
                "name": plan.name,
                "value": count,
                "color": color
            })
    
    # Summary stats
    total_revenue = 0  # Revenue calculation would require Stripe integration
    result = await db.execute(select(func.count(Device.id)).where(Device.is_revoked == False))
    total_usage = result.scalar()
    total_quota = 0
    result = await db.execute(select(Subscription).where(Subscription.state == SubscriptionState.active))
    active_subscriptions = result.scalars().all()
    
    for sub in active_subscriptions:
        if sub.plan and sub.plan.monthly_run_quota:
            total_quota += sub.plan.monthly_run_quota
    
    # Calculate average usage rate
    avg_usage_rate = (total_usage / total_quota * 100) if total_quota > 0 else 0
    
    # Calculate retention rate (30-day active tenants)
    thirty_days_ago = now - timedelta(days=30)
    active_tenants_30d = 0
    total_tenants = len(all_tenants)
    for tenant in all_tenants:
        # Check if tenant has devices activated in last 30 days
        result = await db.execute(
            select(func.count(Device.id)).where(
                and_(
                    Device.tenant_id == tenant.id,
                    Device.created_at >= thirty_days_ago,
                    Device.is_revoked == False
                )
            )
        )
        recent_devices = result.scalar()
        if recent_devices > 0:
            active_tenants_30d += 1
    
    retention_rate = (active_tenants_30d / total_tenants * 100) if total_tenants > 0 else 0
    
    return {
        "activationTrend": activation_trend,  # Return full trend based on date_range filter
        "tenantUsage": tenant_usage[:10],  # Top 10 tenants
        "subscriptionDistribution": subscription_distribution,
        "summaryStats": {
            "totalRevenue": round(total_revenue, 2),
            "avgUsageRate": round(avg_usage_rate, 1),
            "retentionRate": round(retention_rate, 1)
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
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=1000),
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
    return await list_tenants(
        db,
        page=page,
        page_size=page_size,
        search=search,
        status=status,
        sort_field=sort_field,
        sort_direction=sort_direction,
    )


@router.get("/plans", response_model=PlanCollectionResponse)
async def get_plans(db: AsyncSession = Depends(get_db)) -> PlanCollectionResponse:
    """Get all available subscription plans from the database.
    
    This endpoint provides the single source of truth for subscription plans.
    Frontend should use this to populate plan dropdowns dynamically.
    """
    try:
        result = await db.execute(select(Plan).order_by(Plan.monthly_run_quota.asc()))
        plans = result.scalars().all()
        return PlanCollectionResponse(
            plans=[
                PlanResponse(
                    id=plan.id,
                    name=plan.name,
                    stripe_price_id=plan.stripe_price_id,
                    monthly_run_quota=plan.monthly_run_quota,
                )
                for plan in plans
            ]
        )
    except Exception as e:
        LOGGER.error("failed_to_fetch_plans", extra={"error": str(e)})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch subscription plans."
        )


@router.post("/tenants", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
async def create_tenant_endpoint(payload: TenantCreatePayload, db: AsyncSession = Depends(get_db)) -> TenantResponse:
    """Create a tenant and return the persisted record."""

    LOGGER.info("create_tenant_request", extra={"slug": payload.slug})
    return await create_tenant(db, payload)


# IMPORTANT: More specific routes must come BEFORE generic routes
# FastAPI matches routes in order, so /tenants/{slug}/deletion-impact must come before /tenants/{slug}
@router.get("/tenants/{tenant_slug}/deletion-impact")
async def get_tenant_deletion_impact_endpoint(
    tenant_slug: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get a summary of all records that will be deleted with a tenant."""

    LOGGER.info("get_tenant_deletion_impact_request", extra={"slug": tenant_slug})
    from ..services.tenant_service import get_tenant_deletion_impact

    return await get_tenant_deletion_impact(db, tenant_slug)


@router.get("/tenants/{tenant_slug}", response_model=TenantResponse)
async def get_tenant(tenant_slug: str, db: AsyncSession = Depends(get_db)) -> TenantResponse:
    """Return a single tenant by slug."""

    try:
        return await get_tenant_by_slug(db, tenant_slug)
    except TenantNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error.message) from error


@router.put("/tenants/{tenant_slug}", response_model=TenantResponse)
async def update_tenant_endpoint(
    tenant_slug: str,
    payload: TenantUpdatePayload,
    db: AsyncSession = Depends(get_db),
) -> TenantResponse:
    """Update tenant details and return the updated record."""

    LOGGER.info("update_tenant_request", extra={"slug": tenant_slug})
    return await update_tenant(db, tenant_slug, payload)


@router.delete("/tenants/{tenant_slug}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tenant_endpoint(tenant_slug: str, db: AsyncSession = Depends(get_db)) -> None:
    """Delete the requested tenant and all related records.

    This will permanently delete:
    - All activation codes (revoked first)
    - All devices (revoked first)
    - All subscriptions
    - All usage events and rollups
    - All LLM project configs and agent configs (if associated)
    - The tenant itself

    This action cannot be undone.
    """
    from ..core.exceptions import InvalidOperationError, TenantNotFoundError

    LOGGER.info("delete_tenant_request", extra={"slug": tenant_slug})
    try:
        await delete_tenant(db, tenant_slug)
    except TenantNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error.message) from error
    except InvalidOperationError as error:
        LOGGER.error("delete_tenant_endpoint_failed", extra={"slug": tenant_slug, "error": str(error)})
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error.message) from error


# ============================================================================
# ACTIVATION CODE ENDPOINTS
# ============================================================================

@router.get("/codes")
async def get_all_codes(
    db: AsyncSession = Depends(get_db),
    tenant_slug: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    page: int = 1,
    page_size: int = 25
):
    """Get activation codes with optional filtering and pagination.
    
    Args:
        page: Page number (1-indexed)
        page_size: Number of items per page (10, 25, 50, 100, or 200)
    """
    from sqlalchemy.orm import joinedload
    
    # Validate page_size
    valid_page_sizes = [10, 25, 50, 100, 200]
    if page_size not in valid_page_sizes:
        page_size = 25
    
    # Build base query
    base_stmt = select(ActivationCode).join(Tenant).options(joinedload(ActivationCode.tenant))
    
    if tenant_slug:
        base_stmt = base_stmt.where(Tenant.slug == tenant_slug)
    
    if status:
        # Calculate status based on expires_at, used_at, revoked
        if status == 'revoked':
            base_stmt = base_stmt.where(ActivationCode.revoked_at.isnot(None))
        elif status == 'expired':
            base_stmt = base_stmt.where(
                ActivationCode.expires_at.isnot(None),
                ActivationCode.expires_at < datetime.now()
            )
        elif status == 'used':
            base_stmt = base_stmt.where(ActivationCode.use_count >= ActivationCode.max_uses)
        elif status == 'active':
            base_stmt = base_stmt.where(
                ActivationCode.revoked_at.is_(None),
                (ActivationCode.expires_at.is_(None) | (ActivationCode.expires_at >= datetime.now())),
                ActivationCode.use_count < ActivationCode.max_uses
            )
    
    if search:
        search_pattern = f"%{search}%"
        base_stmt = base_stmt.where(
            (ActivationCode.code_plain.ilike(search_pattern)) |
            (Tenant.name.ilike(search_pattern)) |
            (ActivationCode.label.ilike(search_pattern))
        )
    
    # Get total count before pagination
    count_stmt = base_stmt.with_only_columns(func.count(ActivationCode.id)).order_by(None)
    result = await db.execute(count_stmt)
    total = result.scalar()
    
    # Apply pagination
    offset = (page - 1) * page_size
    result = await db.execute(
        base_stmt.order_by(ActivationCode.created_at.desc()).offset(offset).limit(page_size)
    )
    codes = result.scalars().all()
    
    # Note: Codes are already fresh from the query above.
    # The query executes a fresh SELECT, so use_count should be current.
    
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
        
        # Get tenant info - use relationship if available, otherwise query
        tenant_name = code.tenant.name if hasattr(code, 'tenant') and code.tenant else "Unknown"
        tenant_slug_val = code.tenant.slug if hasattr(code, 'tenant') and code.tenant else "unknown"
        
        result.append({
            "id": code.id,
            "code": code.code_plain,
            "tenant": tenant_name,
            "tenantSlug": tenant_slug_val,
            "label": code.label,
            "status": status_value,
            "expiresAt": code.expires_at.isoformat() if code.expires_at else None,
            "usedAt": code.used_at.isoformat() if code.used_at else None,
            "createdAt": code.created_at.isoformat() if code.created_at else None,
            "useCount": code.use_count,
            "maxUses": code.max_uses
        })
    
    total_pages = (total + page_size - 1) // page_size  # Ceiling division
    
    return {
        "codes": result,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages
    }


@router.post("/codes/generate")
async def generate_codes_json(data: ActivationCodeGenerate, db: AsyncSession = Depends(get_db)):
    """Generate activation codes (JSON API version)."""
    
    # Find tenant
    result = await db.execute(select(Tenant).where(Tenant.slug == data.tenant_slug))
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    # Generate codes
    import secrets
    import hashlib
    from ..core.settings import settings
    
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
    
    generated_codes = []
    
    for _ in range(data.count):
        # Generate random code (format: XXXX-XXXX-XXXX-XXXX, e.g., 12RY-S55W-4MZR-KP2J)
        code_plain = _generate_activation_code()
        
        # Calculate expiration
        expires_at = None
        if data.ttl_days:
            expires_at = datetime.now() + timedelta(days=data.ttl_days)
        
        # Create code
        new_code = ActivationCode(
            tenant_id=tenant.id,
            code_plain=code_plain,
            code_hash=_hash_code(code_plain),  # Properly hash the code
            label=data.label,
            expires_at=expires_at,
            max_uses=data.max_uses,
            use_count=0,
            revoked_at=None
        )
        
        db.add(new_code)
        generated_codes.append(code_plain)
    
    # Log event for code generation BEFORE committing (so it's part of the same transaction)
    try:
        from ..services.event_service import log_code_generated
        if generated_codes:
            # Flush to get code IDs before committing
            await db.flush()
            # Get the first code ID (representing the batch)
            result = await db.execute(
                select(ActivationCode).where(ActivationCode.code_plain == generated_codes[0])
            )
            first_code = result.scalar_one_or_none()
            if first_code:
                await log_code_generated(
                    session=db,
                    code_id=first_code.id,
                    tenant_id=tenant.id,
                    tenant_name=tenant.name,
                    code_count=data.count,
                )
    except Exception as e:
        # Event logging failed - log error but don't fail code generation
        LOGGER.error("event_logging_failed", extra={"error": str(e), "event": "code_generated"})
    
    # Commit codes and event together
    await db.commit()
    
    return {
        "success": True,
        "message": f"Generated {data.count} codes successfully",
        "codes": generated_codes
    }


@router.delete("/codes/{code_id}")
async def delete_code(code_id: int, db: AsyncSession = Depends(get_db)):
    """Delete/revoke an activation code."""
    
    result = await db.execute(select(ActivationCode).where(ActivationCode.id == code_id))
    code = result.scalar_one_or_none()
    
    if not code:
        raise HTTPException(status_code=404, detail="Code not found")
    
    # Mark as revoked instead of deleting
    code.revoked_at = datetime.now()
    
    # Log event for code revocation BEFORE committing (so it's part of the same transaction)
    try:
        from ..services.event_service import log_code_revoked
        result = await db.execute(select(Tenant).where(Tenant.id == code.tenant_id))
        tenant = result.scalar_one_or_none()
        if tenant:
            await log_code_revoked(
                session=db,
                code_id=code.id,
                tenant_id=tenant.id,
                tenant_name=tenant.name,
            )
    except Exception as e:
        # Event logging failed - log error but don't fail code revocation
        LOGGER.error("event_logging_failed", extra={"error": str(e), "event": "code_revoked"})
    
    # Commit code revocation and event together
    await db.commit()
    
    return {
        "success": True,
        "message": "Code revoked successfully"
    }


# ============================================================================
# DEVICE ENDPOINTS
# ============================================================================

@router.get("/devices")
async def get_all_devices(
    db: AsyncSession = Depends(get_db),
    tenant_slug: Optional[str] = None,
    search: Optional[str] = None
):
    """Get all devices with optional filtering."""
    
    base_stmt = select(Device).join(Tenant)
    
    if tenant_slug:
        base_stmt = base_stmt.where(Tenant.slug == tenant_slug)
    
    if search:
        search_pattern = f"%{search}%"
        base_stmt = base_stmt.where(
            (Device.label.ilike(search_pattern)) |
            (Device.hw_fingerprint.ilike(search_pattern)) |
            (Tenant.name.ilike(search_pattern))
        )
    
    result = await db.execute(base_stmt)
    devices = result.scalars().all()
    
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
async def revoke_device(device_id: int, db: AsyncSession = Depends(get_db)):
    """Revoke a device."""
    
    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()
    
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    # Mark as revoked
    device.is_revoked = True
    await db.commit()
    
    return {
        "success": True,
        "message": "Device revoked successfully"
    }


@router.delete("/devices/{device_id}/permanent", status_code=status.HTTP_204_NO_CONTENT)
async def delete_device_permanent(device_id: int, db: AsyncSession = Depends(get_db)):
    """Permanently delete a device."""
    
    from sqlalchemy import delete as sql_delete
    
    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()
    
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    await db.execute(sql_delete(Device).where(Device.id == device_id))
    await db.commit()
    
    LOGGER.info("device_deleted", extra={"deviceId": device_id})


# ============================================================================
# PROJECT ENDPOINTS (Admin)
# ============================================================================

@router.get("/projects/activated")
async def get_activated_projects(
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    search: Optional[str] = Query(None),
    tenant_slug: Optional[str] = Query(None),
):
    """Get all projects that have been activated with activation codes."""
    
    from sqlalchemy.orm import joinedload
    
    # Base query: projects with activation_code_id set
    base_stmt = select(LLMProjectConfig).where(LLMProjectConfig.activation_code_id.isnot(None))
    
    # Filter by tenant if provided
    if tenant_slug:
        base_stmt = base_stmt.join(Tenant).where(Tenant.slug == tenant_slug)
    else:
        # Still need to join Tenant for the relationship
        base_stmt = base_stmt.join(Tenant)
    
    # Search filter
    if search:
        search_pattern = f"%{search}%"
        base_stmt = base_stmt.where(
            (LLMProjectConfig.client_name.ilike(search_pattern)) |
            (LLMProjectConfig.project_id.ilike(search_pattern)) |
            (LLMProjectConfig.description.ilike(search_pattern))
        )
    
    # Get total count (before pagination and joinedload)
    # Create a count query that matches the filters
    count_base = select(LLMProjectConfig.id).where(LLMProjectConfig.activation_code_id.isnot(None))
    
    if tenant_slug:
        count_base = count_base.join(Tenant).where(Tenant.slug == tenant_slug)
    
    if search:
        search_pattern = f"%{search}%"
        count_base = count_base.where(
            (LLMProjectConfig.client_name.ilike(search_pattern)) |
            (LLMProjectConfig.project_id.ilike(search_pattern)) |
            (LLMProjectConfig.description.ilike(search_pattern))
        )
    
    count_stmt = select(func.count()).select_from(count_base.subquery())
    total_result = await db.execute(count_stmt)
    total = total_result.scalar() or 0
    
    # Add joinedload for tenant relationship
    base_stmt = base_stmt.options(joinedload(LLMProjectConfig.tenant))
    
    # Apply pagination
    offset = (page - 1) * page_size
    base_stmt = base_stmt.order_by(LLMProjectConfig.started_at.desc().nulls_last(), LLMProjectConfig.created_at.desc())
    base_stmt = base_stmt.offset(offset).limit(page_size)
    
    result = await db.execute(base_stmt)
    projects = result.scalars().unique().all()
    
    # Get activation codes for these projects
    activation_code_ids = [p.activation_code_id for p in projects if p.activation_code_id]
    codes_result = await db.execute(
        select(ActivationCode).where(ActivationCode.id.in_(activation_code_ids))
    )
    codes = {code.id: code for code in codes_result.scalars().all()}
    
    # Format response
    projects_data = []
    for project in projects:
        code = codes.get(project.activation_code_id) if project.activation_code_id else None
        tenant = project.tenant
        
        projects_data.append({
            "projectId": project.project_id,
            "clientName": project.client_name,
            "tenantName": tenant.name if tenant else "Unknown",
            "tenantSlug": tenant.slug if tenant else "",
            "activationCodeId": project.activation_code_id,
            "activationCode": code.code_plain if code else "Unknown",
            "activatedAt": code.used_at.isoformat() if code and code.used_at else project.started_at.isoformat() if project.started_at else "",
            "executionStatus": project.execution_status or "pending",
            "description": project.description,
        })
    
    return {
        "projects": projects_data,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("/projects/{project_id}/revoke-activation", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_project_activation(
    project_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Revoke activation code assignment from a project."""
    
    result = await db.execute(
        select(LLMProjectConfig).where(LLMProjectConfig.project_id == project_id)
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if not project.activation_code_id:
        raise HTTPException(status_code=400, detail="Project does not have an activation code assigned")
    
    # Remove activation code assignment
    project.activation_code_id = None
    await db.commit()
    
    LOGGER.info("project_activation_revoked", extra={"projectId": project_id})


@router.delete("/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Permanently delete a project (admin only)."""
    
    from ..services.llm_config_service import delete_project
    
    LOGGER.info("delete_project_request", extra={"projectId": project_id})
    try:
        await delete_project(db, project_id, tenant_id=None)  # Admin can delete any project
    except Exception as e:
        LOGGER.error("delete_project_error", extra={"error": str(e), "projectId": project_id})
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or could not be deleted",
        )


