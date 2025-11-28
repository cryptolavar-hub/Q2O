"""Tenant API router for authentication and project management."""

from __future__ import annotations

import io
import zipfile
from datetime import datetime, timezone
from typing import Optional, List
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Header, status, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, extract
from sqlalchemy.orm import selectinload

from ..core.exceptions import ConfigurationError, InvalidOperationError, TenantNotFoundError
from ..models.licensing import Tenant, Subscription, SubscriptionState, ActivationCode
from ..models.llm_config import LLMProjectConfig
from ..services.project_execution_service import execute_project, restart_project
from ..core.logging import get_logger
from ..deps import get_db
from ..schemas.llm import (
    ProjectCollectionResponse,
    ProjectCreatePayload,
    ProjectResponse,
    ProjectUpdatePayload,
)
from ..schemas.tenant import (
    TenantProjectCreatePayload,
    TenantProjectUpdatePayload,
    TenantUpdatePayload,
    TenantResponse,
    ActivationCodeAssignPayload,
)
from ..schemas.billing import (
    BillingResponse,
    SubscriptionBillingInfo,
    UsageQuotaInfo,
    BillingHistoryItem,
    PlanUpgradeRequest,
    ActivationCodePurchaseRequest,
    ActivationCodePurchaseResponse,
)
from ..schemas.plan import PlanResponse
from ..schemas.tenant_auth import (
    OTPGenerateRequest,
    OTPGenerateResponse,
    OTPVerifyRequest,
    OTPVerifyResponse,
    SessionInfoResponse,
    SessionRefreshResponse,
)
from ..core.settings import settings
import hashlib
from ..services.llm_config_service import (
    create_project,
    delete_project,
    get_project,
    list_projects,
    update_project,
)
from ..services.tenant_auth_service import (
    generate_otp,
    logout,
    refresh_session,
    validate_session,
    verify_otp,
)

router = APIRouter(prefix="/api/tenant", tags=["tenant"])
LOGGER = get_logger(__name__)


async def get_tenant_from_session(
    x_session_token: str = Header(..., alias="X-Session-Token"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Dependency to extract tenant info from session token.
    
    Updates last_activity to keep session alive during active use.
    
    Raises:
        HTTPException: If session is invalid or expired.
    """
    try:
        tenant_info = await validate_session(x_session_token, db)
        # Commit the last_activity update immediately to ensure it's persisted
        # This prevents race conditions where navigation triggers multiple requests
        await db.commit()
        return tenant_info
    except InvalidOperationError as e:
        await db.rollback()  # Rollback on error
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )


# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================

@router.post("/auth/otp/generate", response_model=OTPGenerateResponse, status_code=status.HTTP_200_OK)
async def generate_otp_endpoint(
    request: OTPGenerateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Generate and send OTP for tenant login.
    
    Rate limited: Maximum 3 OTPs per hour per tenant.
    OTP expires in 10 minutes.
    OTP is sent via email or SMS based on tenant configuration.
    
    Note: OTP code is NOT returned in the response for security reasons.
    """
    try:
        await generate_otp(request.tenant_slug, db)
        await db.commit()
        # Return success without OTP code (security best practice)
        return OTPGenerateResponse(
            otp_code="",  # Empty - OTP is sent via email/SMS, not returned in API
            expires_in=600,  # 10 minutes
            message="OTP has been sent to your registered email or phone number.",
        )
    except TenantNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except InvalidOperationError as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(e),
        )
    except Exception as e:
        await db.rollback()
        LOGGER.error("otp_generation_error", extra={"error": str(e), "tenant_slug": request.tenant_slug})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate OTP",
        )


@router.post("/auth/otp/verify", response_model=OTPVerifyResponse, status_code=status.HTTP_200_OK)
async def verify_otp_endpoint(
    request: OTPVerifyRequest,
    db: AsyncSession = Depends(get_db),
):
    """Verify OTP and return session token.
    
    OTP is single-use and expires after 10 minutes.
    Session token expires after 24 hours or 30 minutes of inactivity.
    """
    try:
        session_token = await verify_otp(request.tenant_slug, request.otp_code, db)
        
        # Get session info for response
        session_info = await validate_session(session_token, db)
        await db.commit()
        
        return OTPVerifyResponse(
            session_token=session_token,
            expires_at=session_info["expires_at"],
            tenant_id=session_info["tenant_id"],
            tenant_slug=session_info["tenant_slug"],
        )
    except TenantNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except InvalidOperationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )
    except Exception as e:
        await db.rollback()
        LOGGER.error("otp_verification_error", extra={"error": str(e), "tenant_slug": request.tenant_slug})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify OTP",
        )


@router.get("/auth/session", response_model=SessionInfoResponse)
async def get_session_info(
    tenant_info: dict = Depends(get_tenant_from_session),
):
    """Get current session information."""
    return SessionInfoResponse(
        tenant_id=tenant_info["tenant_id"],
        tenant_slug=tenant_info["tenant_slug"],
        expires_at=tenant_info["expires_at"],
        created_at=tenant_info["created_at"],
    )


@router.post("/auth/refresh", response_model=SessionRefreshResponse)
async def refresh_session_endpoint(
    x_session_token: str = Header(..., alias="X-Session-Token"),
    db: AsyncSession = Depends(get_db),
):
    """Refresh session expiration time."""
    try:
        refreshed = await refresh_session(x_session_token, db)
        await db.commit()
        
        return SessionRefreshResponse(
            session_token=x_session_token,
            expires_at=refreshed["expires_at"],
            tenant_id=refreshed["tenant_id"],
            tenant_slug=refreshed["tenant_slug"],
        )
    except InvalidOperationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )
    except Exception as e:
        await db.rollback()
        LOGGER.error("session_refresh_error", extra={"error": str(e)})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to refresh session",
        )


@router.post("/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout_endpoint(
    x_session_token: str = Header(..., alias="X-Session-Token"),
    db: AsyncSession = Depends(get_db),
):
    """Logout and invalidate session."""
    try:
        await logout(x_session_token, db)
        await db.commit()
    except Exception as e:
        await db.rollback()
        LOGGER.error("logout_error", extra={"error": str(e)})


# ============================================================================
# PROFILE ENDPOINTS
# ============================================================================

@router.get("/profile", response_model=TenantResponse)
async def get_tenant_profile(
    tenant_info: dict = Depends(get_tenant_from_session),
    db: AsyncSession = Depends(get_db),
):
    """Get current tenant's profile information."""
    from ..services.tenant_service import get_tenant_by_slug
    
    return await get_tenant_by_slug(db, tenant_info["tenant_slug"])


@router.put("/profile", response_model=TenantResponse)
async def update_tenant_profile(
    payload: TenantUpdatePayload,
    tenant_info: dict = Depends(get_tenant_from_session),
    db: AsyncSession = Depends(get_db),
):
    """Update current tenant's profile information."""
    from ..services.tenant_service import update_tenant
    
    try:
        return await update_tenant(db, tenant_info["tenant_slug"], payload)
    except TenantNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except TenantConflictError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )
    except Exception as e:
        await db.rollback()
        LOGGER.error("profile_update_error", extra={"error": str(e), "tenant_slug": tenant_info["tenant_slug"]})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile",
        )


# ============================================================================
# BILLING ENDPOINTS
# ============================================================================

@router.get("/billing", response_model=BillingResponse)
async def get_tenant_billing(
    tenant_info: dict = Depends(get_tenant_from_session),
    db: AsyncSession = Depends(get_db),
):
    """Get current tenant's billing information."""
    from ..services.tenant_service import get_tenant_by_slug
    from ..models.licensing import Subscription, Plan, ActivationCode, MonthlyUsageRollup
    from ..models.llm_config import LLMProjectConfig
    from ..utils.timezone_utils import now_in_server_tz
    from sqlalchemy import func, extract
    from datetime import datetime, timezone
    
    tenant_response = await get_tenant_by_slug(db, tenant_info["tenant_slug"])
    
    # Get subscription details
    result = await db.execute(
        select(Subscription)
        .options(selectinload(Subscription.plan))
        .where(Subscription.tenant_id == tenant_info["tenant_id"])
        .order_by(Subscription.id.desc())
        .limit(1)
    )
    subscription = result.scalar_one_or_none()
    
    # Build subscription billing info
    subscription_info = SubscriptionBillingInfo(
        plan_name=subscription.plan.name if subscription and subscription.plan else "No Plan",
        plan_tier=subscription.plan.name.lower() if subscription and subscription.plan else None,
        monthly_price=None,  # TODO: Add pricing to Plan model or fetch from Stripe
        status=subscription.state.value if subscription and subscription.state else "inactive",
        next_billing_date=subscription.current_period_end.isoformat() if subscription and subscription.current_period_end else None,
        auto_renewal=True,  # TODO: Add auto_renewal field to Subscription model
        stripe_subscription_id=subscription.stripe_subscription_id if subscription else None,
        stripe_customer_id=subscription.stripe_customer_id if subscription else None,
        current_period_start=subscription.current_period_start.isoformat() if subscription and subscription.current_period_start else None,
        current_period_end=subscription.current_period_end.isoformat() if subscription and subscription.current_period_end else None,
    )
    
    # QA_Engineer: Calculate actual current month usage from MonthlyUsageRollup (not static tenant.usage_current)
    today = now_in_server_tz()
    usage_result = await db.execute(
        select(MonthlyUsageRollup).where(
            MonthlyUsageRollup.tenant_id == tenant_info["tenant_id"],
            MonthlyUsageRollup.year == today.year,
            MonthlyUsageRollup.month == today.month
        )
    )
    usage_rollup = usage_result.scalar_one_or_none()
    
    if usage_rollup:
        current_month_usage = usage_rollup.runs
    else:
        # Fallback: Count project executions this month from LLMProjectConfig
        project_executions_result = await db.execute(
            select(func.count(LLMProjectConfig.id)).where(
                LLMProjectConfig.tenant_id == tenant_info["tenant_id"],
                LLMProjectConfig.execution_started_at.isnot(None),
                extract('year', LLMProjectConfig.execution_started_at) == today.year,
                extract('month', LLMProjectConfig.execution_started_at) == today.month
            )
        )
        current_month_usage = project_executions_result.scalar() or 0
    
    # QA_Engineer: Use plan's monthly_run_quota (not tenant.usage_quota which is static)
    monthly_run_quota = subscription.plan.monthly_run_quota if subscription and subscription.plan else 0
    
    # Calculate usage percentage
    usage_percentage = (current_month_usage / monthly_run_quota * 100) if monthly_run_quota > 0 else 0
    
    # QA_Engineer: Calculate activation codes issued/used THIS MONTH (not all-time)
    # Activation codes issued this month
    codes_issued_this_month_result = await db.execute(
        select(func.count(ActivationCode.id)).where(
            ActivationCode.tenant_id == tenant_info["tenant_id"],
            extract('year', ActivationCode.created_at) == today.year,
            extract('month', ActivationCode.created_at) == today.month
        )
    )
    activation_codes_total = codes_issued_this_month_result.scalar() or 0
    
    # Activation codes used this month (codes that have use_count > 0 and were used this month)
    # Note: We check if used_at is this month, or if use_count increased this month
    codes_used_this_month_result = await db.execute(
        select(func.count(ActivationCode.id)).where(
            ActivationCode.tenant_id == tenant_info["tenant_id"],
            ActivationCode.use_count > 0,
            extract('year', ActivationCode.created_at) == today.year,
            extract('month', ActivationCode.created_at) == today.month
        )
    )
    activation_codes_used = codes_used_this_month_result.scalar() or 0
    
    # Calculate activation codes percentage
    activation_percentage = (activation_codes_used / activation_codes_total * 100) if activation_codes_total > 0 else 0
    
    usage_info = UsageQuotaInfo(
        monthly_run_quota=monthly_run_quota,
        current_month_usage=current_month_usage,
        usage_percentage=round(usage_percentage, 2),
        activation_codes_total=activation_codes_total,
        activation_codes_used=activation_codes_used,
        activation_codes_remaining=activation_codes_total - activation_codes_used,
        activation_codes_percentage=round(activation_percentage, 2),
    )
    
    # TODO: Fetch billing history from Stripe or database
    billing_history: List[BillingHistoryItem] = []
    
    return BillingResponse(
        subscription=subscription_info,
        usage=usage_info,
        billing_history=billing_history,
    )


@router.get("/billing/plans")
async def get_available_plans(
    db: AsyncSession = Depends(get_db),
):
    """Get all available subscription plans for upgrade/downgrade."""
    from ..models.licensing import Plan
    
    result = await db.execute(select(Plan).order_by(Plan.monthly_run_quota))
    plans = result.scalars().all()
    
    return [
        PlanResponse(
            id=plan.id,
            name=plan.name,
            stripe_price_id=plan.stripe_price_id,
            monthly_run_quota=plan.monthly_run_quota,
        )
        for plan in plans
    ]


@router.post("/billing/upgrade")
async def upgrade_subscription_plan(
    request: PlanUpgradeRequest,
    tenant_info: dict = Depends(get_tenant_from_session),
    db: AsyncSession = Depends(get_db),
):
    """Upgrade or downgrade subscription plan via Stripe checkout."""
    import stripe
    from ..core.settings import settings
    from ..models.licensing import Subscription, Plan, Tenant
    from sqlalchemy.orm import selectinload
    
    stripe.api_key = settings.STRIPE_SECRET_KEY
    
    # Verify plan exists
    result = await db.execute(select(Plan).where(Plan.id == request.plan_id))
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan not found",
        )
    
    # Get tenant
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_info["tenant_id"]))
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found",
        )
    
    # Get current subscription
    result = await db.execute(
        select(Subscription)
        .options(selectinload(Subscription.plan))
        .where(Subscription.tenant_id == tenant_info["tenant_id"])
        .order_by(Subscription.id.desc())
        .limit(1)
    )
    subscription = result.scalar_one_or_none()
    
    try:
        # If tenant already has a Stripe customer, use it; otherwise create one
        if subscription and subscription.stripe_customer_id:
            customer_id = subscription.stripe_customer_id
        else:
            # Create Stripe customer
            customer = stripe.Customer.create(
                email=tenant.email,
                name=tenant.name,
                metadata={"tenant_id": str(tenant.id), "tenant_slug": tenant.slug},
            )
            customer_id = customer.id
            
            # Update subscription with customer ID
            if subscription:
                subscription.stripe_customer_id = customer_id
            else:
                # Create new subscription record
                subscription = Subscription(
                    tenant_id=tenant.id,
                    plan_id=plan.id,
                    stripe_customer_id=customer_id,
                    state=SubscriptionState.trialing,
                )
                db.add(subscription)
            await db.commit()
        
        # Create Stripe checkout session for subscription
        checkout_session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=["card"],
            mode="subscription",
            line_items=[
                {
                    "price": plan.stripe_price_id,
                    "quantity": 1,
                }
            ],
            metadata={
                "tenant_id": str(tenant.id),
                "plan_id": str(plan.id),
                "type": "subscription_upgrade",
            },
            success_url=f"{settings.ALLOWED_ORIGINS[0]}/billing?success=true",
            cancel_url=f"{settings.ALLOWED_ORIGINS[0]}/billing?canceled=true",
        )
        
        LOGGER.info(
            "stripe_checkout_created",
            extra={
                "tenant_id": tenant.id,
                "plan_id": plan.id,
                "checkout_session_id": checkout_session.id,
            },
        )
        
        return {"checkoutUrl": checkout_session.url, "sessionId": checkout_session.id}
    except stripe.error.StripeError as e:
        LOGGER.error("stripe_error", extra={"error": str(e), "tenant_id": tenant_info["tenant_id"]})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Stripe error: {str(e)}",
        )
    except Exception as e:
        await db.rollback()
        LOGGER.error("plan_upgrade_error", extra={"error": str(e), "tenant_id": tenant_info["tenant_id"], "plan_id": request.plan_id})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create checkout session",
        )


@router.post("/billing/purchase-codes")
async def purchase_activation_codes(
    request: ActivationCodePurchaseRequest,
    tenant_info: dict = Depends(get_tenant_from_session),
    db: AsyncSession = Depends(get_db),
):
    """Purchase additional activation codes via Stripe checkout."""
    import stripe
    from ..core.settings import settings
    from ..models.licensing import Tenant, Subscription
    
    stripe.api_key = settings.STRIPE_SECRET_KEY
    
    # Pricing per code (can be moved to configuration)
    COST_PER_CODE = 5.00
    
    # Get tenant
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_info["tenant_id"]))
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found",
        )
    
    # Get or create Stripe customer
    result = await db.execute(
        select(Subscription)
        .where(Subscription.tenant_id == tenant_info["tenant_id"])
        .order_by(Subscription.id.desc())
        .limit(1)
    )
    subscription = result.scalar_one_or_none()
    
    try:
        if subscription and subscription.stripe_customer_id:
            customer_id = subscription.stripe_customer_id
        else:
            # Create Stripe customer
            customer = stripe.Customer.create(
                email=tenant.email,
                name=tenant.name,
                metadata={"tenant_id": str(tenant.id), "tenant_slug": tenant.slug},
            )
            customer_id = customer.id
            
            # Update or create subscription record
            if subscription:
                subscription.stripe_customer_id = customer_id
            else:
                subscription = Subscription(
                    tenant_id=tenant.id,
                    plan_id=1,  # Default plan, will be updated later
                    stripe_customer_id=customer_id,
                    state=SubscriptionState.trialing,
                )
                db.add(subscription)
            await db.commit()
        
        # Create Stripe Price for one-time payment (if not exists, create it)
        # For simplicity, we'll use a fixed price ID or create a product/price on the fly
        # In production, you'd want to create these in Stripe dashboard and store the price IDs
        
        # Create checkout session for one-time payment
        checkout_session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=["card"],
            mode="payment",
            line_items=[
                {
                    "price_data": {
                        "currency": "usd",
                        "product_data": {
                            "name": f"Activation Codes ({request.quantity})",
                            "description": f"Purchase {request.quantity} activation code(s) for Q2O Platform",
                        },
                        "unit_amount": int(COST_PER_CODE * 100 * request.quantity),  # Convert to cents
                    },
                    "quantity": 1,
                }
            ],
            metadata={
                "tenant_id": str(tenant.id),
                "quantity": str(request.quantity),
                "type": "activation_codes",
                "label": request.label or f"Purchased {request.quantity} codes",
            },
            success_url=f"{settings.ALLOWED_ORIGINS[0]}/billing?success=true&codes={request.quantity}",
            cancel_url=f"{settings.ALLOWED_ORIGINS[0]}/billing?canceled=true",
        )
        
        LOGGER.info(
            "stripe_checkout_created_for_codes",
            extra={
                "tenant_id": tenant.id,
                "quantity": request.quantity,
                "checkout_session_id": checkout_session.id,
            },
        )
        
        return {
            "checkoutUrl": checkout_session.url,
            "sessionId": checkout_session.id,
            "totalCost": COST_PER_CODE * request.quantity,
        }
    except stripe.error.StripeError as e:
        LOGGER.error("stripe_error", extra={"error": str(e), "tenant_id": tenant_info["tenant_id"]})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Stripe error: {str(e)}",
        )
    except Exception as e:
        await db.rollback()
        LOGGER.error("code_purchase_error", extra={"error": str(e), "tenant_id": tenant_info["tenant_id"]})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create checkout session",
        )


@router.get("/billing/payment-methods")
async def get_payment_methods(
    tenant_info: dict = Depends(get_tenant_from_session),
    db: AsyncSession = Depends(get_db),
):
    """Get saved payment methods for the tenant."""
    import stripe
    from ..core.settings import settings
    from ..models.licensing import Subscription
    
    stripe.api_key = settings.STRIPE_SECRET_KEY
    
    # Get subscription to find Stripe customer
    result = await db.execute(
        select(Subscription)
        .where(Subscription.tenant_id == tenant_info["tenant_id"])
        .order_by(Subscription.id.desc())
        .limit(1)
    )
    subscription = result.scalar_one_or_none()
    
    if not subscription or not subscription.stripe_customer_id:
        return {"paymentMethods": []}
    
    try:
        # Get payment methods from Stripe
        payment_methods = stripe.PaymentMethod.list(
            customer=subscription.stripe_customer_id,
            type="card",
        )
        
        return {
            "paymentMethods": [
                {
                    "id": pm.id,
                    "type": pm.type,
                    "card": {
                        "brand": pm.card.brand,
                        "last4": pm.card.last4,
                        "expMonth": pm.card.exp_month,
                        "expYear": pm.card.exp_year,
                    },
                    "isDefault": pm.id == subscription.stripe_customer_id,  # Simplified - would need to check default payment method
                }
                for pm in payment_methods.data
            ],
        }
    except stripe.error.StripeError as e:
        LOGGER.error("stripe_error_getting_payment_methods", extra={"error": str(e), "tenant_id": tenant_info["tenant_id"]})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve payment methods: {str(e)}",
        )


# ============================================================================
# PROJECT MANAGEMENT ENDPOINTS (Tenant-Scoped)
# ============================================================================

@router.get("/projects", response_model=ProjectCollectionResponse)
async def list_tenant_projects(
    page: int = 1,
    page_size: int = 20,
    search: Optional[str] = None,
    tenant_info: dict = Depends(get_tenant_from_session),
    db: AsyncSession = Depends(get_db),
):
    """List all projects for the authenticated tenant.
    
    Projects are automatically filtered by tenant_id from session.
    Supports search by project name (client_name).
    """
    try:
        return await list_projects(
            session=db,
            page=page,
            page_size=page_size,
            search=search,  # Pass search parameter to service
            tenant_id=tenant_info["tenant_id"],  # Filter by tenant
        )
    except Exception as e:
        LOGGER.error("list_projects_error", extra={"error": str(e), "tenant_id": tenant_info["tenant_id"]})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list projects",
        )


@router.post("/projects", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_tenant_project(
    payload: TenantProjectCreatePayload,
    tenant_info: dict = Depends(get_tenant_from_session),
    db: AsyncSession = Depends(get_db),
):
    """Create a new project for the authenticated tenant.
    
    Maps frontend fields (name, objectives) to backend LLMProjectConfig model.
    tenant_id is automatically set from session.
    
    Requirements:
    - Tenant must have active subscription (or trialing with no existing projects)
    - Project must have ID, Name, Description, and Objectives (all not null)
    """
    import re
    from ..models.llm_config import LLMProjectConfig
    
    # Check subscription status
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_info["tenant_id"]))
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found."
        )
    
    result = await db.execute(select(Subscription).where(Subscription.tenant_id == tenant.id))
    subscription = result.scalar_one_or_none()
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Subscription required to create projects. Please contact support."
        )
    
    # Check subscription state
    if subscription.state == SubscriptionState.trialing:
        # Trialing tenants can only have one project
        result = await db.execute(
            select(func.count(LLMProjectConfig.id)).where(LLMProjectConfig.tenant_id == tenant.id)
        )
        existing_projects = result.scalar()
        
        if existing_projects >= 1:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Trialing subscription allows only one project. Please upgrade to create more projects."
            )
    elif subscription.state not in [SubscriptionState.active, SubscriptionState.trialing]:
        # Block all other states
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"{subscription.state.value.title()} subscription cannot create projects. Please renew your subscription."
        )
    
    # Validate required fields
    if not all([payload.name, payload.description, payload.objectives]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project Name, Description, and Objectives are required."
        )
    
    # Generate project_id from name (slugify)
    base_project_id = re.sub(r'[^a-z0-9]+', '-', payload.name.lower()).strip('-')[:100]
    if not base_project_id:
        base_project_id = f"project-{tenant_info['tenant_id']}-{int(datetime.now().timestamp())}"
    
    # Ensure project_id is unique by appending _001, _002, etc. if needed
    project_id = base_project_id
    counter = 0
    max_attempts = 999  # Limit to _001 through _999
    
    while counter <= max_attempts:
        # Check if this project_id already exists
        result = await db.execute(
            select(LLMProjectConfig).where(LLMProjectConfig.project_id == project_id)
        )
        existing = result.scalar_one_or_none()
        
        if existing is None:
            # Project ID is unique, use it
            break
        
        # Project ID exists, try next number
        counter += 1
        if counter > max_attempts:
            # Fallback to timestamp-based ID if we've exhausted all attempts
            project_id = f"{base_project_id}-{int(datetime.now().timestamp())}"
            break
        
        # Append _001, _002, etc. (zero-padded to 3 digits)
        suffix = f"_{counter:03d}"
        # Ensure total length doesn't exceed reasonable limits (keep base + suffix within 100 chars)
        max_base_length = 100 - len(suffix)
        truncated_base = base_project_id[:max_base_length]
        project_id = f"{truncated_base}{suffix}"
    
    # Map frontend payload to backend ProjectCreatePayload
    backend_payload = ProjectCreatePayload(
        project_id=project_id,
        client_name=payload.client_name or payload.name,  # Use name as fallback
        description=payload.description,
        custom_instructions=payload.objectives,  # Map objectives to custom_instructions
        is_active=True,
        priority='normal',
    )
    
    try:
        project = await create_project(
            session=db,
            payload=backend_payload,
            tenant_id=tenant_info["tenant_id"],  # Auto-set tenant_id
        )
        await db.commit()
        return project
    except (InvalidOperationError, ConfigurationError) as e:
        await db.rollback()
        error_msg = str(e)
        LOGGER.error(
            "create_project_error",
            extra={"error": error_msg, "tenant_id": tenant_info["tenant_id"], "project_id": project_id, "exception_type": type(e).__name__},
        )
        # Pass through InvalidOperationError/ConfigurationError messages (e.g., "Project with ID already exists")
        # Return 400 for business logic errors, 500 for unexpected errors
        if "already exists" in error_msg.lower() or "not found" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg,
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error_msg,
            )
    except Exception as e:
        await db.rollback()
        error_msg = str(e)
        LOGGER.error(
            "create_project_error",
            extra={"error": error_msg, "tenant_id": tenant_info["tenant_id"], "project_id": project_id, "exception_type": type(e).__name__},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create project: {error_msg}",
        )


@router.get("/projects/{project_id}/download")
async def download_project(
    project_id: str,
    tenant_info: dict = Depends(get_tenant_from_session),
    db: AsyncSession = Depends(get_db),
):
    """Download completed project as zip file.
    
    Requirements:
    - Project must belong to the authenticated tenant
    - Project must be completed (execution_status='completed')
    - Project must have an output_folder_path
    
    Returns:
    - ZIP file containing all project files from output folder
    - Created in memory to avoid file system locks
    """
    # Get project
    result = await db.execute(
        select(LLMProjectConfig).where(
            LLMProjectConfig.project_id == project_id,
            LLMProjectConfig.tenant_id == tenant_info["tenant_id"]
        )
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # QA_Engineer: Verify project is completed AND meets quality threshold (≥98%)
    if project.execution_status != 'completed':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Project is not completed. Current status: {project.execution_status}"
        )
    
    # QA_Engineer: Check quality threshold before allowing download
    from ..services.agent_task_service import calculate_project_progress
    task_stats = await calculate_project_progress(
        db,
        project_id,
        execution_started_at=project.execution_started_at
    )
    quality_percentage = task_stats.get('quality_percentage', 0.0)
    cancelled_tasks = task_stats.get('cancelled_tasks', 0)
    
    if quality_percentage < 98.0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Project quality below threshold: {quality_percentage:.2f}% (required: ≥98%). "
                f"Cancelled tasks: {cancelled_tasks}. "
                f"Project cannot be downloaded. Please restart or edit project to fix issues."
            )
        )
    
    # Verify project has output folder path
    if not project.output_folder_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project output folder not found. Project may not have been executed yet."
        )
    
    output_folder = Path(project.output_folder_path)
    
    # Verify output folder exists
    if not output_folder.exists() or not output_folder.is_dir():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project output folder does not exist: {output_folder}"
        )
    
    try:
        # Create zip file in memory to avoid file system locks
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Walk through the output folder and add all files
            for file_path in output_folder.rglob('*'):
                if file_path.is_file():
                    # Get relative path from output folder root
                    arcname = file_path.relative_to(output_folder)
                    
                    # Read file content and add to zip
                    try:
                        zip_file.write(file_path, arcname)
                    except (PermissionError, OSError) as e:
                        # Skip files that can't be read (locked files, etc.)
                        LOGGER.warning(
                            "download_skip_file",
                            extra={
                                "project_id": project_id,
                                "file_path": str(file_path),
                                "error": str(e),
                            }
                        )
                        continue
        
        # Get zip file size and reset buffer position
        zip_size = zip_buffer.tell()
        zip_buffer.seek(0)
        
        # Generate filename
        safe_project_name = "".join(c for c in (project.client_name or project.project_id) if c.isalnum() or c in (' ', '-', '_')).strip()
        filename = f"{safe_project_name}-{project.project_id}.zip"
        
        LOGGER.info(
            "project_download_initiated",
            extra={
                "project_id": project_id,
                "tenant_id": tenant_info["tenant_id"],
                "output_folder": str(output_folder),
                "zip_filename": filename,
                "zip_size_bytes": zip_size,
            }
        )
        
        # Return streaming response with zip file
        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Length": str(zip_size),
            }
        )
        
    except Exception as e:
        LOGGER.error(
            "project_download_failed",
            extra={
                "project_id": project_id,
                "tenant_id": tenant_info["tenant_id"],
                "error": str(e),
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create download archive: {str(e)}"
        )


@router.get("/projects/{project_id}", response_model=ProjectResponse)
async def get_tenant_project(
    project_id: str,
    tenant_info: dict = Depends(get_tenant_from_session),
    db: AsyncSession = Depends(get_db),
):
    """Get a project by ID (tenant-scoped).
    
    Returns 404 if project doesn't exist or doesn't belong to tenant.
    """
    try:
        project = await get_project(session=db, project_id=project_id, tenant_id=tenant_info["tenant_id"])
        return project
    except ConfigurationError as e:
        # Project not found or doesn't belong to tenant
        LOGGER.warning(
            "get_project_not_found",
            extra={
                "error": str(e),
                "tenant_id": tenant_info["tenant_id"],
                "project_id": project_id,
                "detail": e.detail if hasattr(e, 'detail') else None,
            },
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )
    except Exception as e:
        # Unexpected error - log with full details
        LOGGER.error(
            "get_project_error",
            extra={
                "error": str(e),
                "error_type": type(e).__name__,
                "tenant_id": tenant_info["tenant_id"],
                "project_id": project_id,
            },
            exc_info=True,  # Include full traceback
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while fetching the project",
        )


@router.patch("/projects/{project_id}/completion-modal-preference", response_model=dict)
async def update_completion_modal_preference(
    project_id: str,
    show_modal: bool = True,
    tenant_info: dict = Depends(get_tenant_from_session),
    db: AsyncSession = Depends(get_db),
):
    """Update the completion modal preference for a project.
    
    Args:
        project_id: The project ID
        show_modal: Query parameter (default: True) - whether to show the modal (true/false)
        tenant_info: Tenant information from session
        db: Database session
    
    Returns:
        Success message with updated preference
    """
    # Verify project belongs to tenant
    result = await db.execute(
        select(LLMProjectConfig).where(
            LLMProjectConfig.project_id == project_id,
            LLMProjectConfig.tenant_id == tenant_info["tenant_id"]
        )
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or access denied"
        )
    
    # Update the preference
    project.show_completion_modal = show_modal
    await db.commit()
    
    return {
        "success": True,
        "project_id": project_id,
        "show_completion_modal": show_modal,
        "message": f"Completion modal preference updated to {'show' if show_modal else 'hide'}"
    }


@router.put("/projects/{project_id}", response_model=ProjectResponse)
async def update_tenant_project(
    project_id: str,
    payload: ProjectUpdatePayload,
    tenant_info: dict = Depends(get_tenant_from_session),
    db: AsyncSession = Depends(get_db),
):
    """Update a project (tenant-scoped).
    
    Returns 404 if project doesn't exist or doesn't belong to tenant.
    """
    try:
        project = await update_project(
            session=db,
            project_id=project_id,
            payload=payload,
            tenant_id=tenant_info["tenant_id"],  # Verify ownership
        )
        await db.commit()
        return project
    except Exception as e:
        await db.rollback()
        LOGGER.error(
            "update_project_error",
            extra={"error": str(e), "tenant_id": tenant_info["tenant_id"], "project_id": project_id},
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or access denied",
        )


@router.delete("/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tenant_project(
    project_id: str,
    tenant_info: dict = Depends(get_tenant_from_session),
    db: AsyncSession = Depends(get_db),
):
    """Delete a project (tenant-scoped).
    
    Returns 404 if project doesn't exist or doesn't belong to tenant.
    """
    try:
        await delete_project(
            session=db,
            project_id=project_id,
            tenant_id=tenant_info["tenant_id"],  # Verify ownership
        )
        await db.commit()
    except Exception as e:
        await db.rollback()
        LOGGER.error(
            "delete_project_error",
            extra={"error": str(e), "tenant_id": tenant_info["tenant_id"], "project_id": project_id},
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or access denied",
        )


@router.post("/projects/{project_id}/assign-activation-code", response_model=ProjectResponse)
async def assign_activation_code_to_project(
    project_id: str,
    payload: ActivationCodeAssignPayload,
    tenant_info: dict = Depends(get_tenant_from_session),
    db: AsyncSession = Depends(get_db),
):
    """Assign an activation code to a project.
    
    Requirements:
    - Activation code must belong to the tenant
    - Activation code must be valid (not revoked, not expired, not fully used)
    - Project must belong to the tenant
    - Project must not already have an activation code assigned
    """
    def _hash_code(code: str) -> str:
        """Hash activation code for verification."""
        return hashlib.sha256((settings.ACTIVATION_CODE_PEPPER + code).encode()).hexdigest()
    
    # Get project
    result = await db.execute(
        select(LLMProjectConfig).where(
            LLMProjectConfig.project_id == project_id,
            LLMProjectConfig.tenant_id == tenant_info["tenant_id"]
        )
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Check if project already has an activation code
    if project.activation_code_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project already has an activation code assigned."
        )
    
    # Find and validate activation code
    # Normalize code: uppercase, remove spaces, keep dashes (matching generation format)
    normalized_code = payload.activation_code.upper().strip().replace(" ", "")
    
    # Get all codes for this tenant to check both hash and plain text
    all_codes_result = await db.execute(
        select(ActivationCode).where(
            ActivationCode.tenant_id == tenant_info["tenant_id"]
        )
    )
    all_codes = all_codes_result.scalars().all()
    
    code = None
    
    # First, try to find by matching normalized code_plain (most reliable)
    for ac in all_codes:
        if ac.code_plain:
            stored_normalized = ac.code_plain.upper().strip().replace(" ", "")
            if stored_normalized == normalized_code:
                # Found by plain text match - verify hash
                # Hash should be computed from the stored code_plain as-is
                expected_hash = _hash_code(ac.code_plain)
                if expected_hash == ac.code_hash:
                    code = ac
                    LOGGER.info(
                        "activation_code_found_by_plain_match",
                        extra={
                            "tenant_id": tenant_info["tenant_id"],
                            "code_provided": payload.activation_code,
                            "normalized_code": normalized_code,
                            "stored_code_plain": ac.code_plain,
                        }
                    )
                    break
    
    # If not found by plain text, try by hash (for codes without code_plain stored)
    if not code:
        code_hash = _hash_code(normalized_code)
        for ac in all_codes:
            if ac.code_hash == code_hash:
                code = ac
                LOGGER.info(
                    "activation_code_found_by_hash",
                    extra={
                        "tenant_id": tenant_info["tenant_id"],
                        "code_provided": payload.activation_code,
                        "normalized_code": normalized_code,
                    }
                )
                break
    
    # If still not found, log detailed error
    if not code:
        LOGGER.warning(
            "activation_code_not_found",
            extra={
                "tenant_id": tenant_info["tenant_id"],
                "code_provided": payload.activation_code,
                "normalized_code": normalized_code,
                "total_codes_for_tenant": len(all_codes),
                "available_code_plains": [ac.code_plain for ac in all_codes[:5]] if all_codes else [],
            }
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid activation code."
        )
    
    if code.revoked_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Activation code has been revoked."
        )
    
    if code.expires_at:
        # Handle both timezone-aware and timezone-naive datetimes
        now = datetime.now(timezone.utc)
        expires_at = code.expires_at
        # If expires_at is naive, assume it's UTC and make it aware
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at < now:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Activation code has expired."
            )
    
    if code.use_count >= code.max_uses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Activation code has already been used."
        )
    
    # Assign activation code to project
    project.activation_code_id = code.id
    
    # Increment activation code usage
    old_use_count = code.use_count
    code.use_count += 1
    if code.use_count == 1:  # First use - set used_at timestamp
        code.used_at = datetime.now(timezone.utc)
    
    await db.commit()
    
    # Explicitly refresh to ensure we have the latest data from database
    await db.refresh(project)
    await db.refresh(code)
    
    # Verify the update was persisted
    if code.use_count != old_use_count + 1:
        LOGGER.error(
            "activation_code_use_count_not_updated",
            extra={
                "code_id": code.id,
                "expected_count": old_use_count + 1,
                "actual_count": code.use_count,
            }
        )
    
    LOGGER.info(
        "activation_code_assigned_to_project",
        extra={
            "project_id": project_id,
            "tenant_id": tenant_info["tenant_id"],
            "activation_code_id": code.id,
            "use_count": code.use_count,
            "max_uses": code.max_uses,
            "used_at": code.used_at.isoformat() if code.used_at else None,
        }
    )
    
    # Return updated project
    from ..services.llm_config_service import get_project
    return await get_project(session=db, project_id=project_id, tenant_id=tenant_info["tenant_id"])


@router.post("/projects/{project_id}/run", response_model=dict)
async def run_tenant_project(
    project_id: str,
    tenant_info: dict = Depends(get_tenant_from_session),
    db: AsyncSession = Depends(get_db),
):
    """Run a project execution.
    
    Requirements:
    - Project must have activation code assigned
    - Project must have all required fields (ID, Name, Description, Objectives)
    - Tenant must have active subscription (or trialing with no other running projects)
    - For trialing subscriptions: only one project can be running at a time
    - Redirect to Status page on success
    """
    # Get project
    result = await db.execute(
        select(LLMProjectConfig).where(
            LLMProjectConfig.project_id == project_id,
            LLMProjectConfig.tenant_id == tenant_info["tenant_id"]
        )
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    try:
        # Execute project
        execution_info = await execute_project(
            session=db,
            project=project,
            tenant_id=tenant_info["tenant_id"],
        )
        
        LOGGER.info(
            "project_run_initiated",
            extra={
                "project_id": project_id,
                "tenant_id": tenant_info["tenant_id"],
                "execution_id": execution_info.get("execution_id"),
            }
        )
        
        return {
            "success": True,
            "message": "Project execution started successfully",
            "execution_id": execution_info.get("execution_id"),
            "status": execution_info.get("status"),
            "output_folder_path": execution_info.get("output_folder_path"),
        }
    except InvalidOperationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        LOGGER.error(
            "project_run_failed",
            extra={
                "project_id": project_id,
                "tenant_id": tenant_info["tenant_id"],
                "error": str(e),
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to run project: {str(e)}"
        )


@router.post("/projects/{project_id}/restart", response_model=dict)
async def restart_tenant_project(
    project_id: str,
    tenant_info: dict = Depends(get_tenant_from_session),
    db: AsyncSession = Depends(get_db),
):
    """Restart a failed project execution.
    
    Requirements:
    - Project must have execution_status='failed' (completed projects cannot be restarted)
    - Project must have activation code assigned
    - Project must have all required fields (ID, Name, Description, Objectives)
    - Tenant must have active subscription (or trialing with no other running projects)
    - For trialing subscriptions: only one project can be running at a time
    """
    # Get project
    result = await db.execute(
        select(LLMProjectConfig).where(
            LLMProjectConfig.project_id == project_id,
            LLMProjectConfig.tenant_id == tenant_info["tenant_id"]
        )
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    try:
        # Restart project (validates status and resets execution fields)
        execution_info = await restart_project(
            session=db,
            project=project,
            tenant_id=tenant_info["tenant_id"],
        )
        
        LOGGER.info(
            "project_restart_initiated",
            extra={
                "project_id": project_id,
                "tenant_id": tenant_info["tenant_id"],
                "execution_id": execution_info.get("execution_id"),
            }
        )
        
        return {
            "success": True,
            "message": "Project execution restarted successfully",
            "execution_id": execution_info.get("execution_id"),
            "status": execution_info.get("status"),
            "output_folder_path": execution_info.get("output_folder_path"),
        }
    except InvalidOperationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        LOGGER.error(
            "project_restart_failed",
            extra={
                "project_id": project_id,
                "tenant_id": tenant_info["tenant_id"],
                "error": str(e),
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to restart project: {str(e)}"
        )

