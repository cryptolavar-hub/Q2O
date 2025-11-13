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
from ..models.licensing import ActivationCode, Device, Tenant, SubscriptionState, Plan
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
async def get_dashboard_stats(db: Session = Depends(get_db)):
    """Get dashboard statistics for the main admin page."""
    
    from ..utils.timezone_utils import now_in_server_tz, utc_to_server_tz
    from datetime import timezone as tz
    now_tz = now_in_server_tz()
    
    # Count activation codes by status
    all_codes = db.query(ActivationCode).all()
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


@router.get("/recent-activities")
async def get_recent_activities(
    db: Session = Depends(get_db),
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
        events = db.query(PlatformEvent).filter(
            PlatformEvent.created_at >= start_date
        ).order_by(PlatformEvent.created_at.desc()).limit(50).all()
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
            tenant = db.query(Tenant).filter(Tenant.id == event.tenant_id).first()
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
    db: Session = Depends(get_db),
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
    all_codes = db.query(ActivationCode).all()
    all_projects = db.query(LLMProjectConfig).filter(
        LLMProjectConfig.activation_code_id.isnot(None)
    ).all()
    all_devices = db.query(Device).filter(
        Device.is_revoked == False
    ).all()
    
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
    
    # Debug: Log total codes found and sample dates
    if all_codes:
        sample_code = all_codes[0]
        sample_date = _get_date_in_server_tz(sample_code.created_at)
        LOGGER.info("activation_trend_debug", extra={
            "total_codes": len(all_codes),
            "sample_code_created_at": str(sample_code.created_at),
            "sample_code_date_in_server_tz": str(sample_date),
            "server_timezone": str(get_server_timezone()),
            "now_in_server_tz": str(now),
            "start_date": str(start_date),
        })
    
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
async def get_project_device_distribution(db: Session = Depends(get_db)):
    """Get distribution of projects and devices for dashboard chart.
    
    Shows ALL projects (not just activated ones) to match Analytics page.
    """
    
    from ..models.llm_config import LLMProjectConfig
    
    # Count ALL active projects (not just activated with codes)
    active_projects = db.query(LLMProjectConfig).filter(
        LLMProjectConfig.is_active == True
    ).count()
    
    # Count total projects
    total_projects = db.query(LLMProjectConfig).count()
    
    # Count active devices
    active_devices = db.query(Device).filter(Device.is_revoked == False).count()
    
    # Count revoked devices
    revoked_devices = db.query(Device).filter(Device.is_revoked == True).count()
    
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
    db: Session = Depends(get_db),
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
    all_codes_for_trend = db.query(ActivationCode).all()
    all_devices_for_trend = db.query(Device).all()
    
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
    
    # Debug logging (after building activation_trend)
    LOGGER.info("analytics_date_range_debug", extra={
        "date_range": date_range,
        "start_date_normalized": str(start_date_normalized),
        "start_date_only": str(start_date_only),
        "now_date_only": str(now_date_only),
        "total_codes_in_db": len(all_codes_for_trend),
        "filtered_codes_count": len(filtered_codes),
        "total_devices_in_db": len(all_devices_for_trend),
        "filtered_devices_count": len(filtered_devices),
        "activation_trend_length": len(activation_trend),
        "activation_trend_sample": activation_trend[:3] if len(activation_trend) > 0 else [],
        "total_codes_in_trend": sum(item["codes"] for item in activation_trend),
    })
    
    # Tenant usage (current usage vs quota) - with project filtering
    tenant_usage = []
    all_tenants = db.query(Tenant).all()
    
    # Get projects based on filter
    project_filter_query = db.query(LLMProjectConfig)
    
    if project_filter == "latest":
        # Get latest project only
        latest_project = db.query(LLMProjectConfig).order_by(LLMProjectConfig.created_at.desc()).first()
        if latest_project:
            project_filter_query = db.query(LLMProjectConfig).filter(LLMProjectConfig.id == latest_project.id)
        else:
            project_filter_query = db.query(LLMProjectConfig).filter(False)  # No projects
    elif project_filter == "top10":
        # Get top 10 most recent projects
        project_filter_query = db.query(LLMProjectConfig).order_by(LLMProjectConfig.created_at.desc()).limit(10)
    elif project_filter and project_filter.startswith("project:"):
        # Specific project ID
        project_id = project_filter.replace("project:", "")
        project_filter_query = db.query(LLMProjectConfig).filter(LLMProjectConfig.project_id == project_id)
    
    filtered_projects = project_filter_query.all() if project_filter else None
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
                tenant_projects = db.query(LLMProjectConfig).filter(
                    and_(
                        LLMProjectConfig.tenant_id == tenant.id,
                        LLMProjectConfig.project_id.in_(filtered_project_ids)
                    )
                ).count()
                usage = tenant_projects
            else:
                # Default: count devices (for backward compatibility)
                usage = db.query(Device).filter(
                    and_(Device.tenant_id == tenant.id, Device.is_revoked == False)
                ).count()
            
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
    plans = db.query(Plan).all()
    for plan in plans:
        count = db.query(Subscription).filter(
            and_(
                Subscription.plan_id == plan.id,
                Subscription.state == SubscriptionState.active
            )
        ).count()
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
    total_usage = db.query(Device).filter(Device.is_revoked == False).count()
    total_quota = 0
    active_subscriptions = db.query(Subscription).filter(
        Subscription.state == SubscriptionState.active
    ).all()
    
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
        recent_devices = db.query(Device).filter(
            and_(
                Device.tenant_id == tenant.id,
                Device.created_at >= thirty_days_ago,
                Device.is_revoked == False
            )
        ).count()
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


@router.get("/plans", response_model=PlanCollectionResponse)
async def get_plans(db: Session = Depends(get_db)) -> PlanCollectionResponse:
    """Get all available subscription plans from the database.
    
    This endpoint provides the single source of truth for subscription plans.
    Frontend should use this to populate plan dropdowns dynamically.
    """
    try:
        plans = db.query(Plan).order_by(Plan.monthly_run_quota.asc()).all()
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
async def create_tenant_endpoint(payload: TenantCreatePayload, db: Session = Depends(get_db)) -> TenantResponse:
    """Create a tenant and return the persisted record."""

    LOGGER.info("create_tenant_request", extra={"slug": payload.slug})
    return create_tenant(db, payload)


# IMPORTANT: More specific routes must come BEFORE generic routes
# FastAPI matches routes in order, so /tenants/{slug}/deletion-impact must come before /tenants/{slug}
@router.get("/tenants/{tenant_slug}/deletion-impact")
async def get_tenant_deletion_impact_endpoint(
    tenant_slug: str,
    db: Session = Depends(get_db),
) -> dict:
    """Get a summary of all records that will be deleted with a tenant."""

    LOGGER.info("get_tenant_deletion_impact_request", extra={"slug": tenant_slug})
    from ..services.tenant_service import get_tenant_deletion_impact

    return get_tenant_deletion_impact(db, tenant_slug)


@router.get("/tenants/{tenant_slug}", response_model=TenantResponse)
async def get_tenant(tenant_slug: str, db: Session = Depends(get_db)) -> TenantResponse:
    """Return a single tenant by slug."""

    try:
        return get_tenant_by_slug(db, tenant_slug)
    except TenantNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error.message) from error


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
    
    from sqlalchemy.orm import joinedload
    
    query = db.query(ActivationCode).join(Tenant).options(joinedload(ActivationCode.tenant))
    
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
            db.flush()
            # Get the first code ID (representing the batch)
            first_code = db.query(ActivationCode).filter(
                ActivationCode.code_plain == generated_codes[0]
            ).first()
            if first_code:
                log_code_generated(
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
    
    # Log event for code revocation BEFORE committing (so it's part of the same transaction)
    try:
        from ..services.event_service import log_code_revoked
        tenant = db.query(Tenant).filter(Tenant.id == code.tenant_id).first()
        if tenant:
            log_code_revoked(
                session=db,
                code_id=code.id,
                tenant_id=tenant.id,
                tenant_name=tenant.name,
            )
    except Exception as e:
        # Event logging failed - log error but don't fail code revocation
        LOGGER.error("event_logging_failed", extra={"error": str(e), "event": "code_revoked"})
    
    # Commit code revocation and event together
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


