"""Service functions for tenant management."""

from __future__ import annotations

from typing import Iterable, Optional, Sequence

from sqlalchemy import asc, desc, func, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session, joinedload, selectinload

from ..core.exceptions import InvalidOperationError, PlanNotFoundError, TenantConflictError, TenantNotFoundError
from ..core.logging import get_logger
from ..models.licensing import Plan, Subscription, SubscriptionState, Tenant
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
        session.commit()
    except SQLAlchemyError as exc:
        session.rollback()
        LOGGER.error("tenant_creation_failed", extra={"tenantId": new_tenant.id, "error": str(exc)})
        raise InvalidOperationError("Tenant creation failed due to a database error.") from exc

    session.refresh(new_tenant)
    return _load_subscription_details(new_tenant)


def update_tenant(session: Session, slug: str, payload: TenantUpdatePayload) -> TenantResponse:
    """Update a tenant and synchronize subscription information."""

    tenant = session.execute(
        select(Tenant)
        .options(joinedload(Tenant.subscriptions).joinedload(Subscription.plan))
        .where(Tenant.slug == slug)
    ).scalar_one_or_none()

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

    try:
        session.commit()
    except SQLAlchemyError as exc:
        session.rollback()
        LOGGER.error("tenant_update_failed", extra={"tenantId": tenant.id, "error": str(exc)})
        raise InvalidOperationError("Tenant update failed due to a database error.") from exc

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


def delete_tenant(session: Session, slug: str) -> None:
    """Permanently remove a tenant.

    Args:
        session: Active database session.
        slug: Tenant slug.

    Raises:
        TenantNotFoundError: If the tenant does not exist.
        InvalidOperationError: If the delete fails.
    """

    tenant = session.execute(select(Tenant).where(Tenant.slug == slug)).scalar_one_or_none()
    if tenant is None:
        raise TenantNotFoundError("Tenant not found.", detail={"slug": slug})

    try:
        session.delete(tenant)
        session.commit()
    except SQLAlchemyError as exc:
        session.rollback()
        LOGGER.error("tenant_delete_failed", extra={"tenantId": tenant.id, "error": str(exc)})
        raise InvalidOperationError("Failed to delete tenant due to a database error.") from exc
