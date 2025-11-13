"""Tenant API router for authentication and project management."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy.orm import Session

from ..core.exceptions import InvalidOperationError, TenantNotFoundError
from ..core.logging import get_logger
from ..deps import get_db
from ..schemas.llm import (
    ProjectCollectionResponse,
    ProjectCreatePayload,
    ProjectResponse,
    ProjectUpdatePayload,
)
from ..schemas.tenant_auth import (
    OTPGenerateRequest,
    OTPGenerateResponse,
    OTPVerifyRequest,
    OTPVerifyResponse,
    SessionInfoResponse,
    SessionRefreshResponse,
)
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


def get_tenant_from_session(
    x_session_token: str = Header(..., alias="X-Session-Token"),
    db: Session = Depends(get_db),
) -> dict:
    """Dependency to extract tenant info from session token.
    
    Raises:
        HTTPException: If session is invalid or expired.
    """
    try:
        return validate_session(x_session_token, db)
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
    db: Session = Depends(get_db),
):
    """Generate OTP for tenant login.
    
    Rate limited: Maximum 3 OTPs per hour per tenant.
    OTP expires in 10 minutes.
    """
    try:
        otp_code = generate_otp(request.tenant_slug, db)
        db.commit()
        return OTPGenerateResponse(
            otp_code=otp_code,
            expires_in=600,  # 10 minutes
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
        db.rollback()
        LOGGER.error("otp_generation_error", extra={"error": str(e), "tenant_slug": request.tenant_slug})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate OTP",
        )


@router.post("/auth/otp/verify", response_model=OTPVerifyResponse, status_code=status.HTTP_200_OK)
async def verify_otp_endpoint(
    request: OTPVerifyRequest,
    db: Session = Depends(get_db),
):
    """Verify OTP and return session token.
    
    OTP is single-use and expires after 10 minutes.
    Session token expires after 24 hours or 30 minutes of inactivity.
    """
    try:
        session_token = verify_otp(request.tenant_slug, request.otp_code, db)
        
        # Get session info for response
        session_info = validate_session(session_token, db)
        db.commit()
        
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
        db.rollback()
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
    db: Session = Depends(get_db),
):
    """Refresh session expiration time."""
    try:
        refreshed = refresh_session(x_session_token, db)
        db.commit()
        
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
        db.rollback()
        LOGGER.error("session_refresh_error", extra={"error": str(e)})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to refresh session",
        )


@router.post("/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout_endpoint(
    x_session_token: str = Header(..., alias="X-Session-Token"),
    db: Session = Depends(get_db),
):
    """Logout and invalidate session."""
    try:
        logout(x_session_token, db)
        db.commit()
    except Exception as e:
        db.rollback()
        LOGGER.error("logout_error", extra={"error": str(e)})


# ============================================================================
# PROJECT MANAGEMENT ENDPOINTS (Tenant-Scoped)
# ============================================================================

@router.get("/projects", response_model=ProjectCollectionResponse)
async def list_tenant_projects(
    page: int = 1,
    page_size: int = 20,
    tenant_info: dict = Depends(get_tenant_from_session),
    db: Session = Depends(get_db),
):
    """List all projects for the authenticated tenant.
    
    Projects are automatically filtered by tenant_id from session.
    """
    try:
        return list_projects(
            session=db,
            page=page,
            page_size=page_size,
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
    payload: ProjectCreatePayload,
    tenant_info: dict = Depends(get_tenant_from_session),
    db: Session = Depends(get_db),
):
    """Create a new project for the authenticated tenant.
    
    tenant_id is automatically set from session.
    """
    try:
        project = create_project(
            session=db,
            payload=payload,
            tenant_id=tenant_info["tenant_id"],  # Auto-set tenant_id
        )
        db.commit()
        return project
    except Exception as e:
        db.rollback()
        LOGGER.error(
            "create_project_error",
            extra={"error": str(e), "tenant_id": tenant_info["tenant_id"], "project_id": payload.project_id},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create project",
        )


@router.get("/projects/{project_id}", response_model=ProjectResponse)
async def get_tenant_project(
    project_id: str,
    tenant_info: dict = Depends(get_tenant_from_session),
    db: Session = Depends(get_db),
):
    """Get a project by ID (tenant-scoped).
    
    Returns 404 if project doesn't exist or doesn't belong to tenant.
    """
    try:
        project = get_project(session=db, project_id=project_id, tenant_id=tenant_info["tenant_id"])
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
    db: Session = Depends(get_db),
):
    """Update a project (tenant-scoped).
    
    Returns 404 if project doesn't exist or doesn't belong to tenant.
    """
    try:
        project = update_project(
            session=db,
            project_id=project_id,
            payload=payload,
            tenant_id=tenant_info["tenant_id"],  # Verify ownership
        )
        db.commit()
        return project
    except Exception as e:
        db.rollback()
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
    db: Session = Depends(get_db),
):
    """Delete a project (tenant-scoped).
    
    Returns 404 if project doesn't exist or doesn't belong to tenant.
    """
    try:
        delete_project(
            session=db,
            project_id=project_id,
            tenant_id=tenant_info["tenant_id"],  # Verify ownership
        )
        db.commit()
    except Exception as e:
        db.rollback()
        LOGGER.error(
            "delete_project_error",
            extra={"error": str(e), "tenant_id": tenant_info["tenant_id"], "project_id": project_id},
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or access denied",
        )

