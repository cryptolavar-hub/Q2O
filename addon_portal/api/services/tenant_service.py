"""Service functions for tenant management."""

from __future__ import annotations

from typing import Iterable, Optional, Sequence

from sqlalchemy import asc, delete, desc, func, select, update
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session, joinedload, selectinload

from ..core.exceptions import InvalidOperationError, PlanNotFoundError, TenantConflictError, TenantNotFoundError
from ..core.logging import get_logger
from ..models.licensing import Plan, Subscription, SubscriptionState, Tenant
from .activation_code_service import generate_codes
from ..schemas.tenant import (
    SortDirection,
    TenantCollectionResponse,
    TenantCreatePayload,
    TenantResponse,
    TenantSortField,
    TenantUpdatePayload,
)

LOGGER = get_logger(__name__)


def _apply_sorting(sort_field: TenantSortField, sort_direction: SortDirection) -> Iterable:
    """Return an SQLAlchemy ordering clause for tenant queries.

    Args:
        sort_field: Field to sort by.
        sort_direction: Direction of sort.

    Returns:
        An iterable of SQLAlchemy ordering expressions.
    """

    column_map = {
        TenantSortField.CREATED_AT: Tenant.created_at,
        TenantSortField.NAME: Tenant.name,
        TenantSortField.USAGE: Tenant.usage_current,
    }
    column = column_map[sort_field]
    ordering = desc(column) if sort_direction == SortDirection.DESC else asc(column)
    return (ordering, desc(Tenant.created_at))


def _load_subscription_details(tenant: Tenant) -> TenantResponse:
    subscription: Optional[Subscription] = tenant.subscriptions[0] if tenant.subscriptions else None
    subscription_plan = subscription.plan.name if subscription and subscription.plan else None
    subscription_state = subscription.state if subscription else None

    return TenantResponse(
        id=tenant.id,
        name=tenant.name,
        slug=tenant.slug,
        logo_url=tenant.logo_url,
        primary_color=tenant.primary_color,
        domain=tenant.domain,
        usage_quota=tenant.usage_quota,
        usage_current=tenant.usage_current,
        created_at=tenant.created_at.isoformat(),
        subscription={
            "plan_name": subscription_plan,
            "status": subscription_state,
        },
    )


def list_tenants(
    session: Session,
    *,
    page: int,
    page_size: int,
    search: Optional[str],
    status: Optional[SubscriptionState],
    sort_field: TenantSortField,
    sort_direction: SortDirection,
) -> TenantCollectionResponse:
    """Return a paginated collection of tenants.

    Args:
        session: Active database session.
        page: Requested page number (1-indexed).
        page_size: Page size (max 100).
        search: Optional case-insensitive search term.
        status: Optional subscription status filter.
        sort_field: Sort field to apply.
        sort_direction: Sort direction.

    Returns:
        A :class:`TenantCollectionResponse` containing tenants and pagination metadata.

    Raises:
        InvalidOperationError: If the query fails.
    """

    try:
        base_stmt = (
            select(Tenant)
            .options(selectinload(Tenant.subscriptions).selectinload(Subscription.plan))
        )

        if status is not None:
            base_stmt = base_stmt.join(Tenant.subscriptions).where(Subscription.state == status)

        if search:
            pattern = f"%{search.strip().lower()}%"
            base_stmt = base_stmt.where(
                func.lower(Tenant.name).like(pattern) | func.lower(Tenant.slug).like(pattern)
            )

        total = session.execute(
            base_stmt.with_only_columns(func.count(func.distinct(Tenant.id))).order_by(None)
        ).scalar_one()

        ordering = _apply_sorting(sort_field, sort_direction)
        tenants: Sequence[Tenant] = (
            session.execute(
                base_stmt.order_by(*ordering).offset((page - 1) * page_size).limit(page_size)
            )
            .scalars()
            .unique()
            .all()
        )

        return TenantCollectionResponse(
            items=[_load_subscription_details(tenant) for tenant in tenants],
            total=total,
            page=page,
            page_size=page_size,
        )
    except SQLAlchemyError as exc:
        LOGGER.error("tenant_query_failed", extra={"error": str(exc)})
        raise InvalidOperationError("Failed to retrieve tenants.") from exc


def create_tenant(session: Session, payload: TenantCreatePayload) -> TenantResponse:
    """Create a new tenant and associated subscription.

    Args:
        session: Active database session.
        payload: Validated tenant creation data.

    Returns:
        Serialized tenant response.

    Raises:
        TenantConflictError: If the tenant slug already exists.
        PlanNotFoundError: If the target subscription plan is missing.
        InvalidOperationError: For unexpected database failures.
    """

    plan = session.execute(select(Plan).where(Plan.name == payload.subscription_plan)).scalar_one_or_none()
    if plan is None:
        raise PlanNotFoundError("Subscription plan not found.", detail={"plan": payload.subscription_plan})

    new_tenant = Tenant(
        name=payload.name,
        slug=payload.slug,
        logo_url=str(payload.logo_url) if payload.logo_url else None,
        primary_color=payload.primary_color,
        domain=payload.domain,
        usage_quota=payload.usage_quota,
    )

    session.add(new_tenant)

    try:
        session.flush()
    except IntegrityError as exc:
        session.rollback()
        LOGGER.warning("tenant_slug_conflict", extra={"slug": payload.slug})
        raise TenantConflictError("A tenant with this slug already exists.") from exc

    subscription = Subscription(
        tenant_id=new_tenant.id,
        plan_id=plan.id,
        state=SubscriptionState.active,
    )
    session.add(subscription)

    try:
        # Log tenant creation event BEFORE committing (so it's part of the same transaction)
        try:
            from ..services.event_service import log_tenant_created
            log_tenant_created(
                session=session,
                tenant_id=new_tenant.id,
                tenant_name=new_tenant.name,
            )
        except Exception as e:
            # Event logging failed - log error but don't fail tenant creation
            LOGGER.error("event_logging_failed", extra={"error": str(e), "event": "tenant_created"})
        
        # Commit everything together (tenant, subscription, and event)
        session.commit()
    except SQLAlchemyError as exc:
        session.rollback()
        LOGGER.error("tenant_creation_failed", extra={"tenantId": new_tenant.id, "error": str(exc)})
        raise InvalidOperationError("Tenant creation failed due to a database error.") from exc
    
    # Auto-generate 10% of plan quota activation codes
    try:
        quota = plan.monthly_run_quota
        code_count = max(1, int(quota * 0.1))  # 10% of quota, minimum 1 code
        generated_codes = generate_codes(
            session=session,
            tenant_id=new_tenant.id,
            count=code_count,
            label="Auto-generated on tenant creation",
            max_uses=1,  # One code = one project activation
        )
        LOGGER.info(
            "tenant_auto_codes_generated",
            extra={
                "tenant_id": new_tenant.id,
                "tenant_slug": new_tenant.slug,
                "code_count": code_count,
                "plan_quota": quota,
            },
        )
    except Exception as exc:
        # Log but don't fail tenant creation if code generation fails
        LOGGER.warning(
            "tenant_auto_code_generation_failed",
            extra={"tenant_id": new_tenant.id, "error": str(exc)},
        )

    session.refresh(new_tenant)
    return _load_subscription_details(new_tenant)


def update_tenant(session: Session, slug: str, payload: TenantUpdatePayload) -> TenantResponse:
    """Update a tenant and synchronize subscription information."""

    tenant = session.execute(
        select(Tenant)
        .options(joinedload(Tenant.subscriptions).joinedload(Subscription.plan))
        .where(Tenant.slug == slug)
    ).unique().scalar_one_or_none()

    if tenant is None:
        raise TenantNotFoundError("Tenant not found.", detail={"slug": slug})

    if payload.name is not None:
        tenant.name = payload.name
    if payload.logo_url is not None:
        tenant.logo_url = str(payload.logo_url)
    if payload.primary_color is not None:
        tenant.primary_color = payload.primary_color
    if payload.domain is not None:
        tenant.domain = payload.domain
    if payload.usage_quota is not None:
        tenant.usage_quota = payload.usage_quota

    if payload.subscription_plan is not None:
        plan = session.execute(select(Plan).where(Plan.name == payload.subscription_plan)).scalar_one_or_none()
        if plan is None:
            raise PlanNotFoundError("Subscription plan not found.", detail={"plan": payload.subscription_plan})

        subscription = tenant.subscriptions[0] if tenant.subscriptions else None
        if subscription is None:
            subscription = Subscription(tenant_id=tenant.id, plan_id=plan.id, state=SubscriptionState.active)
            session.add(subscription)
        else:
            subscription.plan_id = plan.id

    # Track changes for event logging
    changes = {}
    if payload.name is not None and payload.name != tenant.name:
        changes["name"] = {"old": tenant.name, "new": payload.name}
    if payload.logo_url is not None:
        changes["logo_url"] = {"old": tenant.logo_url, "new": str(payload.logo_url)}
    if payload.primary_color is not None:
        changes["primary_color"] = {"old": tenant.primary_color, "new": payload.primary_color}
    if payload.domain is not None:
        changes["domain"] = {"old": tenant.domain, "new": payload.domain}
    if payload.usage_quota is not None:
        changes["usage_quota"] = {"old": tenant.usage_quota, "new": payload.usage_quota}
    
    try:
        session.commit()
    except SQLAlchemyError as exc:
        session.rollback()
        LOGGER.error("tenant_update_failed", extra={"tenantId": tenant.id, "error": str(exc)})
        raise InvalidOperationError("Tenant update failed due to a database error.") from exc

    # Log tenant update event (gracefully handle if table doesn't exist)
    if changes:
        try:
            from ..services.event_service import log_tenant_updated
            log_tenant_updated(
                session=session,
                tenant_id=tenant.id,
                tenant_name=tenant.name,
                changes=changes,
            )
        except Exception as e:
            # Event logging failed (table might not exist) - log warning but don't fail tenant update
            LOGGER.warning("event_logging_failed", extra={"error": str(e), "event": "tenant_updated"})

    session.refresh(tenant)
    return _load_subscription_details(tenant)


def get_tenant_by_slug(session: Session, slug: str) -> TenantResponse:
    """Return a single tenant by slug."""

    tenant = session.execute(
        select(Tenant)
        .options(selectinload(Tenant.subscriptions).selectinload(Subscription.plan))
        .where(Tenant.slug == slug)
    ).scalar_one_or_none()

    if tenant is None:
        raise TenantNotFoundError("Tenant not found.", detail={"slug": slug})

    return _load_subscription_details(tenant)


def get_tenant_deletion_impact(session: Session, slug: str) -> dict:
    """Get a summary of all records that will be deleted with a tenant.

    Args:
        session: Active database session.
        slug: Tenant slug.

    Returns:
        Dictionary with counts of related records.

    Raises:
        TenantNotFoundError: If the tenant does not exist.
    """
    from ..models.licensing import (
        ActivationCode,
        Device,
        Subscription,
        UsageEvent,
        MonthlyUsageRollup,
    )
    from ..models.llm_config import LLMProjectConfig, LLMAgentConfig

    tenant = session.execute(select(Tenant).where(Tenant.slug == slug)).scalar_one_or_none()
    if tenant is None:
        raise TenantNotFoundError("Tenant not found.", detail={"slug": slug})

    tenant_id = tenant.id

    # Count related records
    activation_codes_count = session.execute(
        select(func.count(ActivationCode.id)).where(ActivationCode.tenant_id == tenant_id)
    ).scalar_one() or 0

    active_codes_count = session.execute(
        select(func.count(ActivationCode.id)).where(
            ActivationCode.tenant_id == tenant_id,
            ActivationCode.revoked_at.is_(None),
        )
    ).scalar_one() or 0

    devices_count = session.execute(
        select(func.count(Device.id)).where(Device.tenant_id == tenant_id)
    ).scalar_one() or 0

    active_devices_count = session.execute(
        select(func.count(Device.id)).where(
            Device.tenant_id == tenant_id,
            Device.is_revoked == False,
        )
    ).scalar_one() or 0

    subscriptions_count = session.execute(
        select(func.count(Subscription.id)).where(Subscription.tenant_id == tenant_id)
    ).scalar_one() or 0

    usage_events_count = session.execute(
        select(func.count(UsageEvent.id)).where(UsageEvent.tenant_id == tenant_id)
    ).scalar_one() or 0

    usage_rollups_count = session.execute(
        select(func.count(MonthlyUsageRollup.id)).where(MonthlyUsageRollup.tenant_id == tenant_id)
    ).scalar_one() or 0

    # Check for LLM projects associated with tenant (by client_name matching tenant name or domain)
    llm_projects_count = 0
    llm_agents_count = 0
    if tenant.name:
        llm_projects_count = session.execute(
            select(func.count(LLMProjectConfig.id)).where(
                func.lower(LLMProjectConfig.client_name) == func.lower(tenant.name)
            )
        ).scalar_one() or 0

        if llm_projects_count > 0:
            # Get project IDs to count agents
            project_ids = session.execute(
                select(LLMProjectConfig.project_id).where(
                    func.lower(LLMProjectConfig.client_name) == func.lower(tenant.name)
                )
            ).scalars().all()
            if project_ids:
                llm_agents_count = session.execute(
                    select(func.count(LLMAgentConfig.id)).where(
                        LLMAgentConfig.project_id.in_(project_ids)
                    )
                ).scalar_one() or 0

    return {
        "tenant": {
            "id": tenant.id,
            "name": tenant.name,
            "slug": tenant.slug,
        },
        "activation_codes": {
            "total": activation_codes_count,
            "active": active_codes_count,
            "revoked": activation_codes_count - active_codes_count,
        },
        "devices": {
            "total": devices_count,
            "active": active_devices_count,
            "revoked": devices_count - active_devices_count,
        },
        "subscriptions": {"total": subscriptions_count},
        "usage_events": {"total": usage_events_count},
        "usage_rollups": {"total": usage_rollups_count},
        "llm_projects": {"total": llm_projects_count},
        "llm_agents": {"total": llm_agents_count},
    }


def delete_tenant(session: Session, slug: str) -> None:
    """Permanently remove a tenant and all related records.

    Deletion order (to avoid foreign key constraint violations):
    1. Revoke all active activation codes
    2. Revoke all active devices
    3. Delete usage events and rollups
    4. Delete subscriptions
    5. Delete activation codes
    6. Delete devices
    7. Delete LLM project configs and agent configs (if associated)
    8. Finally delete the tenant

    Args:
        session: Active database session.
        slug: Tenant slug.

    Raises:
        TenantNotFoundError: If the tenant does not exist.
        InvalidOperationError: If the delete fails.
    """
    from datetime import datetime
    from ..models.licensing import (
        ActivationCode,
        Device,
        Subscription,
        UsageEvent,
        MonthlyUsageRollup,
    )
    from ..models.llm_config import LLMProjectConfig, LLMAgentConfig

    tenant = session.execute(select(Tenant).where(Tenant.slug == slug)).scalar_one_or_none()
    if tenant is None:
        raise TenantNotFoundError("Tenant not found.", detail={"slug": slug})

    tenant_id = tenant.id
    now = datetime.utcnow()

    try:
        # Step 1: Revoke all active activation codes
        session.execute(
            update(ActivationCode)
            .where(ActivationCode.tenant_id == tenant_id, ActivationCode.revoked_at.is_(None))
            .values(revoked_at=now)
        )
        LOGGER.info("revoked_activation_codes", extra={"tenantId": tenant_id})

        # Step 2: Revoke all active devices
        session.execute(
            update(Device)
            .where(Device.tenant_id == tenant_id, Device.is_revoked == False)
            .values(is_revoked=True)
        )
        LOGGER.info("revoked_devices", extra={"tenantId": tenant_id})

        # Step 3: Delete usage events and rollups
        session.execute(delete(UsageEvent).where(UsageEvent.tenant_id == tenant_id))
        session.execute(delete(MonthlyUsageRollup).where(MonthlyUsageRollup.tenant_id == tenant_id))
        LOGGER.info("deleted_usage_records", extra={"tenantId": tenant_id})

        # Step 4: Delete subscriptions
        session.execute(delete(Subscription).where(Subscription.tenant_id == tenant_id))
        LOGGER.info("deleted_subscriptions", extra={"tenantId": tenant_id})

        # Step 5: Delete activation codes
        session.execute(delete(ActivationCode).where(ActivationCode.tenant_id == tenant_id))
        LOGGER.info("deleted_activation_codes", extra={"tenantId": tenant_id})

        # Step 6: Delete devices
        session.execute(delete(Device).where(Device.tenant_id == tenant_id))
        LOGGER.info("deleted_devices", extra={"tenantId": tenant_id})

        # Step 7: Delete LLM project configs and agent configs (if associated with tenant)
        if tenant.name:
            # Find projects by client_name matching tenant name
            project_ids = session.execute(
                select(LLMProjectConfig.project_id).where(
                    func.lower(LLMProjectConfig.client_name) == func.lower(tenant.name)
                )
            ).scalars().all()

            if project_ids:
                # Delete agent configs first (due to FK constraint)
                session.execute(
                    delete(LLMAgentConfig).where(LLMAgentConfig.project_id.in_(project_ids))
                )
                # Then delete project configs
                session.execute(
                    delete(LLMProjectConfig).where(LLMProjectConfig.project_id.in_(project_ids))
                )
                LOGGER.info(
                    "deleted_llm_configs",
                    extra={"tenantId": tenant_id, "projectsDeleted": len(project_ids)},
                )

        # Log tenant deletion event BEFORE deleting (so we have tenant info)
        # Gracefully handle if table doesn't exist
        try:
            from ..services.event_service import log_tenant_deleted
            log_tenant_deleted(
                session=session,
                tenant_id=tenant_id,
                tenant_name=tenant.name,
            )
        except Exception as e:
            # Event logging failed (table might not exist) - log warning but don't fail tenant deletion
            LOGGER.warning("event_logging_failed", extra={"error": str(e), "event": "tenant_deleted"})
        
        # Step 8: Finally delete the tenant
        session.delete(tenant)
        session.commit()
        LOGGER.info("tenant_deleted", extra={"tenantId": tenant_id, "slug": slug})

    except SQLAlchemyError as exc:
        session.rollback()
        LOGGER.error("tenant_delete_failed", extra={"tenantId": tenant_id, "error": str(exc)})
        raise InvalidOperationError("Failed to delete tenant due to a database error.") from exc
