"""Tenant API router for authentication and project management."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from ..core.exceptions import ConfigurationError, InvalidOperationError, TenantNotFoundError
from ..models.licensing import Tenant, Subscription, SubscriptionState, ActivationCode
from ..models.llm_config import LLMProjectConfig
from ..services.project_execution_service import execute_project
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
    ActivationCodeAssignPayload,
)
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
    
    Raises:
        HTTPException: If session is invalid or expired.
    """
    try:
        return await validate_session(x_session_token, db)
    except InvalidOperationError as e:
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
    project_id = re.sub(r'[^a-z0-9]+', '-', payload.name.lower()).strip('-')[:100]
    if not project_id:
        project_id = f"project-{tenant_info['tenant_id']}-{int(datetime.now().timestamp())}"
    
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
        db.rollback()
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
    except Exception as e:
        LOGGER.error(
            "get_project_error",
            extra={"error": str(e), "tenant_id": tenant_info["tenant_id"], "project_id": project_id},
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )


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

