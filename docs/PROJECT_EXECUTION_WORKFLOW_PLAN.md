# Project Execution Workflow - Implementation Plan

**Date:** November 19, 2025  
**Status:** Planning Phase  
**Priority:** High

## Overview

This document outlines the implementation plan for the complete project execution workflow, including activation code management, project execution, status monitoring, and billing integration.

---

## 1. Project Creation & Subscription Validation

### Requirements
- Only tenants with **active** subscriptions can create projects
- Subscription with a status of **trialing** can only run one project once (single project execution limit)
- Other subscription statuses (past_due, canceled, unpaid, suspended) should block project creation

### Implementation

**Backend (`addon_portal/api/routers/tenant_api.py`):**
```python
@router.post("/projects", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_tenant_project(
    payload: TenantProjectCreatePayload,
    tenant_info: dict = Depends(get_tenant_from_session),
    db: Session = Depends(get_db),
):
    """Create a new project for the authenticated tenant.
    
    Requirements:
    - Tenant must have active subscription (or trialing with no existing projects)
    - Project must have ID, Name, Description, and Objectives (all not null)
    """
    # Check subscription status
    tenant = db.query(Tenant).filter(Tenant.id == tenant_info["tenant_id"]).first()
    subscription = db.query(Subscription).filter(
        Subscription.tenant_id == tenant.id
    ).first()
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Subscription required to create projects. Please contact support."
        )
    
    # Check subscription state
    if subscription.state == SubscriptionState.trialing:
        # Trialing tenants can only have one project
        existing_projects = db.query(LLMProjectConfig).filter(
            LLMProjectConfig.tenant_id == tenant.id
        ).count()
        
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
    
    # ... rest of creation logic
```

**Frontend (`addon_portal/apps/tenant-portal/src/pages/projects/new.tsx`):**
- Add subscription status check before allowing form submission
- Display warning if subscription is not active

---

## 2. Activation Code Assignment System

### Requirements
- Projects must be assigned an activation code before running
- Activation codes are permanently attached to a project/device combination
- Each code can only be used once (`max_uses=1`)
- Codes are generated when tenant is created (10% of quota) or requested from admin
- Tenants can self-generate codes up to their plan's monthly quota

### Database Schema Updates

**Migration: `008_add_project_activation_fields.sql`**
```sql
-- Ensure activation_code_id exists in llm_project_configs
-- (Already exists, but verify)

-- Add project execution status tracking
ALTER TABLE llm_project_configs
ADD COLUMN IF NOT EXISTS execution_status VARCHAR(20) DEFAULT 'pending',
ADD COLUMN IF NOT EXISTS execution_started_at TIMESTAMP NULL,
ADD COLUMN IF NOT EXISTS execution_completed_at TIMESTAMP NULL,
ADD COLUMN IF NOT EXISTS execution_error TEXT NULL,
ADD COLUMN IF NOT EXISTS output_folder_path VARCHAR(500) NULL;

-- Add index for faster queries
CREATE INDEX IF NOT EXISTS ix_llm_projects_execution_status 
ON llm_project_configs(execution_status);

CREATE INDEX IF NOT EXISTS ix_llm_projects_activation_code 
ON llm_project_configs(activation_code_id);
```

### Activation Code Quota Tracking

**New Service: `addon_portal/api/services/activation_quota_service.py`**
```python
"""Service for managing activation code quotas and self-service generation."""

def get_tenant_activation_quota_info(session: Session, tenant_id: int) -> dict:
    """Get tenant's activation code quota information."""
    # Get subscription and plan
    # Count used codes this month
    # Calculate remaining quota
    # Return: total_quota, used_count, remaining_count, can_generate
```

### Self-Service Code Generation

**New Endpoint: `addon_portal/api/routers/tenant_api.py`**
```python
@router.post("/activation-codes/generate", response_model=ActivationCodeGenerateResponse)
async def generate_activation_codes_self_service(
    count: int = Query(1, ge=1, le=100),
    tenant_info: dict = Depends(get_tenant_from_session),
    db: Session = Depends(get_db),
):
    """Self-service activation code generation for tenants.
    
    Requirements:
    - Tenant must have active subscription
    - Cannot exceed monthly quota
    - Cannot generate more than remaining quota
    """
```

---

## 3. Project Execution System

### Requirements
- Projects trigger `main.py` with project attributes
- Project ID becomes folder name: `Tenant_Projects/{project_id}/`
- Projects must have activation code assigned before running
- All required fields (ID, Name, Description, Objectives) must be not null

### Project Execution Service

**New Service: `addon_portal/api/services/project_execution_service.py`**
```python
"""Service for executing projects via main.py."""

import subprocess
import os
from pathlib import Path
from ..models.llm_config import LLMProjectConfig
from ..core.logging import get_logger

LOGGER = get_logger(__name__)

# Root folder for all tenant projects
TENANT_PROJECTS_ROOT = Path(__file__).resolve().parents[3] / "Tenant_Projects"

def execute_project(
    session: Session,
    project: LLMProjectConfig,
    tenant_id: int,
) -> dict:
    """Execute a project by calling main.py with project attributes.
    
    Args:
        session: Database session
        project: Project configuration
        tenant_id: Tenant ID
    
    Returns:
        dict with execution_id, status, output_folder_path
    
    Requirements:
    - Project must have activation code assigned
    - Tenant must have active or trialing subscription
    - For trialing subscriptions: only one project can be running at a time
    """
    # Validate subscription status
    tenant = session.query(Tenant).filter(Tenant.id == tenant_id).first()
    subscription = session.query(Subscription).filter(
        Subscription.tenant_id == tenant_id
    ).first()
    
    if not subscription:
        raise InvalidOperationError("Subscription required to run projects.")
    
    if subscription.state == SubscriptionState.trialing:
        # Check if another project is already running
        running_projects = session.query(LLMProjectConfig).filter(
            LLMProjectConfig.tenant_id == tenant_id,
            LLMProjectConfig.execution_status == 'running'
        ).count()
        
        if running_projects >= 1:
            raise InvalidOperationError(
                "Trialing subscription allows only one running project at a time. "
                "Please wait for the current project to complete or upgrade your plan."
            )
    elif subscription.state != SubscriptionState.active:
        raise InvalidOperationError(
            f"{subscription.state.value.title()} subscription cannot run projects. Please renew your subscription."
        )
    
    # Validate project has activation code
    if not project.activation_code_id:
        raise InvalidOperationError("Project must be activated with an activation code before running.")
    
    # Validate required fields
    if not all([project.project_id, project.client_name, project.description, project.custom_instructions]):
        raise InvalidOperationError("Project ID, Name, Description, and Objectives are required.")
    
    # Create output folder: Tenant_Projects/{project_id}/
    output_folder = TENANT_PROJECTS_ROOT / project.project_id
    output_folder.mkdir(parents=True, exist_ok=True)
    
    # Update project status
    project.execution_status = 'running'
    project.execution_started_at = datetime.utcnow()
    project.output_folder_path = str(output_folder)
    session.commit()
    
    # Prepare main.py command
    # Assuming main.py is in the project root
    main_py_path = Path(__file__).resolve().parents[3] / "main.py"
    
    # Build command with project attributes
    cmd = [
        "python",
        str(main_py_path),
        "--project-id", project.project_id,
        "--project-name", project.client_name,
        "--description", project.description or "",
        "--objectives", project.custom_instructions or "",
        "--output-folder", str(output_folder),
        "--tenant-id", str(tenant_id),
    ]
    
    # Execute in background (non-blocking)
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=str(output_folder.parent),
    )
    
    LOGGER.info(
        "project_execution_started",
        extra={
            "project_id": project.project_id,
            "tenant_id": tenant_id,
            "process_id": process.pid,
            "output_folder": str(output_folder),
        }
    )
    
    return {
        "execution_id": process.pid,
        "status": "running",
        "output_folder_path": str(output_folder),
    }
```

### RUN PROJECT Endpoint

**New Endpoint: `addon_portal/api/routers/tenant_api.py`**
```python
@router.post("/projects/{project_id}/run", response_model=ProjectExecutionResponse)
async def run_tenant_project(
    project_id: str,
    tenant_info: dict = Depends(get_tenant_from_session),
    db: Session = Depends(get_db),
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
    # Validate subscription (active or trialing)
    # For trialing: check if another project is running
    # Validate activation code
    # Validate required fields
    # Execute project
    # Return execution info
```

---

## 4. Tenant Status Page

### Requirements
- Show all tenant's **ONLY active projects** in rows
- Pagination: 10 projects per page
- Search filter to narrow down to specific projects
- Each row is expandable to show progress bar
- Display project execution status (pending, running, completed, failed)
- Show progress percentage
- Filter by status (all, running, completed, failed)

### Implementation

**New Page: `addon_portal/apps/tenant-portal/src/pages/status.tsx`**
```typescript
// Enhanced Status page for tenant view
// - List only active tenant projects (is_active=true)
// - Pagination: 10 projects per page
// - Search filter to narrow down projects
// - Expandable rows with progress bars
// - Real-time updates via WebSocket or polling
// - Filter by execution status (all, running, completed, failed)
```

**Backend Endpoint: `addon_portal/api/routers/tenant_api.py`**
```python
@router.get("/projects/status", response_model=ProjectStatusCollectionResponse)
async def get_tenant_projects_status(
    tenant_info: dict = Depends(get_tenant_from_session),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    search: Optional[str] = Query(None, max_length=200),
    status: Optional[str] = None,  # Filter: all, running, completed, failed
):
    """Get all active tenant projects with execution status.
    
    Only returns projects where is_active=True.
    Supports pagination (10 per page) and search filtering.
    """
    # Query only active projects
    query = db.query(LLMProjectConfig).filter(
        LLMProjectConfig.tenant_id == tenant_info["tenant_id"],
        LLMProjectConfig.is_active == True  # Only active projects
    )
    
    # Apply search filter
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (LLMProjectConfig.client_name.ilike(search_pattern)) |
            (LLMProjectConfig.project_id.ilike(search_pattern)) |
            (LLMProjectConfig.description.ilike(search_pattern))
        )
    
    # Apply execution status filter
    if status and status != 'all':
        if status == 'running':
            query = query.filter(LLMProjectConfig.execution_status == 'running')
        elif status == 'completed':
            query = query.filter(LLMProjectConfig.execution_status == 'completed')
        elif status == 'failed':
            query = query.filter(LLMProjectConfig.execution_status == 'failed')
        elif status == 'pending':
            query = query.filter(LLMProjectConfig.execution_status == 'pending')
    
    # Get total count before pagination
    total = query.count()
    
    # Apply pagination
    offset = (page - 1) * page_size
    projects = query.order_by(LLMProjectConfig.execution_started_at.desc()).offset(offset).limit(page_size).all()
    
    # ... format response
```

---

## 5. Multi-Agent Dashboard Status Page (Client View)

### Requirements
- Activation code login (no OTP required)
- View single project assigned to activation code
- Show project lifecycle and progress
- Download completed project as zip (7z)

### Implementation

**New Endpoint: `addon_portal/api/routers/public_api.py` (or new router)**
```python
@router.post("/public/activate-project", response_model=ProjectActivationResponse)
async def activate_project_with_code(
    activation_code: str = Form(...),
    db: Session = Depends(get_db),
):
    """Activate project view using activation code.
    
    Returns project details and execution status.
    No authentication required - activation code is the key.
    """
    # Validate activation code
    # Find project with this activation code
    # Return project info
```

**New Page: `addon_portal/apps/multi-agent-dashboard/src/pages/status/[code].tsx`**
```typescript
// Status page for clients
// - Activation code input
// - Single project view
// - Progress monitoring
// - Download button for completed projects
```

### Project Download Feature

**New Endpoint: `addon_portal/api/routers/public_api.py`**
```python
@router.get("/public/projects/{project_id}/download")
async def download_project(
    project_id: str,
    activation_code: str = Query(...),
    db: Session = Depends(get_db),
):
    """Download completed project as zip file.
    
    Requirements:
    - Project must be completed
    - Activation code must match project
    - Use 7z or zipfile to create archive
    """
    import zipfile
    import shutil
    
    # Validate activation code
    # Get project output folder
    # Create zip archive
    # Return file download
```

---

## 6. Tenant Profile Page

**📋 Detailed Roadmap**: See `docs/TENANT_PROFILE_BILLING_ROADMAP.md` for complete implementation details.

### Requirements
- Display tenant branding (logo, primary color)
- **Allow tenant to edit profile wherever applicable** (name, logo, primary color, email, phone, etc.)
- Show plan details (name, quota, usage)
- Display subscription status
- Show activation code quota info

### Implementation

**New Page: `addon_portal/apps/tenant-portal/src/pages/profile.tsx`**
```typescript
// Tenant profile page
// - Branding display (editable)
// - Profile information (editable: name, email, phone, logo, primary color)
// - Plan information (read-only)
// - Subscription status (read-only)
// - Activation code quota (read-only)
// - Save/Update button for editable fields
```

**Backend Endpoints: `addon_portal/api/routers/tenant_api.py`**
```python
@router.get("/profile", response_model=TenantProfileResponse)
async def get_tenant_profile(
    tenant_info: dict = Depends(get_tenant_from_session),
    db: Session = Depends(get_db),
):
    """Get tenant profile information."""
    tenant = db.query(Tenant).filter(Tenant.id == tenant_info["tenant_id"]).first()
    subscription = db.query(Subscription).filter(
        Subscription.tenant_id == tenant.id
    ).first()
    
    return {
        "tenant": {
            "id": tenant.id,
            "name": tenant.name,
            "slug": tenant.slug,
            "logo_url": tenant.logo_url,
            "primary_color": tenant.primary_color,
            "email": tenant.email,
            "phone_number": tenant.phone_number,
            "domain": tenant.domain,
        },
        "subscription": {
            "plan_name": subscription.plan.name if subscription and subscription.plan else None,
            "state": subscription.state.value if subscription else None,
            "monthly_run_quota": subscription.plan.monthly_run_quota if subscription and subscription.plan else 0,
        },
        "activation_codes": {
            "total": db.query(ActivationCode).filter(ActivationCode.tenant_id == tenant.id).count(),
            "used": db.query(ActivationCode).filter(
                ActivationCode.tenant_id == tenant.id,
                ActivationCode.use_count >= ActivationCode.max_uses
            ).count(),
            "available": db.query(ActivationCode).filter(
                ActivationCode.tenant_id == tenant.id,
                ActivationCode.revoked_at.is_(None),
                ActivationCode.use_count < ActivationCode.max_uses
            ).count(),
        }
    }

@router.put("/profile", response_model=TenantProfileResponse)
async def update_tenant_profile(
    payload: TenantProfileUpdatePayload,
    tenant_info: dict = Depends(get_tenant_from_session),
    db: Session = Depends(get_db),
):
    """Update tenant profile information.
    
    Allows editing: name, email, phone_number, logo_url, primary_color, domain
    Slug cannot be changed (it's permanent).
    """
    tenant = db.query(Tenant).filter(Tenant.id == tenant_info["tenant_id"]).first()
    
    # Update editable fields
    if payload.name is not None:
        tenant.name = payload.name
    if payload.email is not None:
        tenant.email = payload.email
    if payload.phone_number is not None:
        tenant.phone_number = payload.phone_number
    if payload.logo_url is not None:
        tenant.logo_url = payload.logo_url
    if payload.primary_color is not None:
        tenant.primary_color = payload.primary_color
    if payload.domain is not None:
        tenant.domain = payload.domain
    
    tenant.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(tenant)
    
    # Return updated profile
    return await get_tenant_profile(tenant_info, db)
```

**New Schema: `addon_portal/api/schemas/tenant_auth.py`**
```python
class TenantProfileUpdatePayload(BaseModel):
    """Payload for updating tenant profile."""
    name: Optional[str] = None
    email: Optional[str] = None
    phone_number: Optional[str] = None
    logo_url: Optional[str] = None
    primary_color: Optional[str] = None
    domain: Optional[str] = None
```

---

## 7. Tenant Billing Page

**📋 Detailed Roadmap**: See `docs/TENANT_PROFILE_BILLING_ROADMAP.md` for complete implementation details.

### Requirements
- Display current subscription and plan
- Show billing history
- Allow plan upgrades via Stripe
- Show activation code quota and usage
- **Purchase additional activation codes when quota is exhausted**
- Renewal management

### Implementation

**New Page: `addon_portal/apps/tenant-portal/src/pages/billing.tsx`**
```typescript
// Billing page
// - Current plan display
// - Upgrade options
// - Billing history
// - Stripe integration
```

**Backend Endpoint: `addon_portal/api/routers/tenant_api.py`**
```python
@router.get("/billing", response_model=TenantBillingResponse)
async def get_tenant_billing(
    tenant_info: dict = Depends(get_tenant_from_session),
    db: Session = Depends(get_db),
):
    """Get tenant billing information."""

@router.post("/billing/upgrade")
async def upgrade_tenant_plan(
    plan_id: int,
    tenant_info: dict = Depends(get_tenant_from_session),
    db: Session = Depends(get_db),
):
    """Upgrade tenant plan via Stripe."""
```

---

## 8. Auto-Pause Projects on Subscription Inactive

### Requirements
- When tenant subscription becomes inactive, pause all running projects
- Prevent new project creation
- Prevent project execution

### Implementation

**New Service: `addon_portal/api/services/subscription_service.py`**
```python
def handle_subscription_state_change(
    session: Session,
    tenant_id: int,
    new_state: SubscriptionState,
):
    """Handle subscription state changes.
    
    If subscription becomes inactive:
    - Pause all running projects
    - Prevent new project creation
    - Prevent project execution
    """
    if new_state not in [SubscriptionState.active, SubscriptionState.trialing]:
        # Pause all running projects
        projects = session.query(LLMProjectConfig).filter(
            LLMProjectConfig.tenant_id == tenant_id,
            LLMProjectConfig.execution_status == 'running'
        ).all()
        
        for project in projects:
            project.execution_status = 'paused'
            project.is_active = False
        
        session.commit()
```

**Stripe Webhook Handler: `addon_portal/api/routers/billing_stripe.py`**
```python
@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    """Handle Stripe webhook events."""
    # On subscription.canceled, subscription.past_due, etc.
    # Call handle_subscription_state_change
```

---

## 9. Roadmap Updates

### Updated Roadmap Sections

1. **Week 2-3: Payment Overlay & Project Execution**
   - ✅ Payment overlay before code generation
   - ✅ Project execution system
   - ✅ Activation code assignment
   - ✅ Status monitoring

2. **Week 4-5: Billing & Self-Service**
   - ✅ Tenant billing page
   - ✅ Self-service activation code generation
   - ✅ Plan upgrades via Stripe
   - ✅ Quota tracking

3. **Week 6-7: Multi-Agent Dashboard (Client View)**
   - ✅ Activation code login
   - ✅ Single project status view
   - ✅ Project download feature

4. **Week 8-9: Tenant Profile & Polish**
   - ✅ Tenant profile page
   - ✅ Enhanced status page
   - ✅ Auto-pause on subscription inactive

---

## 10. Database Migrations Required

1. **Migration 008: Project Execution Fields**
   - Add `execution_status`, `execution_started_at`, `execution_completed_at`, `execution_error`, `output_folder_path` to `llm_project_configs`

2. **Migration 009: Activation Code Quota Tracking**
   - Add monthly quota tracking table
   - Track code generation per month per tenant

---

## 11. File System Structure

```
C:\Q2O_Combined\
├── Tenant_Projects\
│   ├── project-id-1\
│   │   ├── generated_files\
│   │   ├── logs\
│   │   └── output\
│   ├── project-id-2\
│   │   └── ...
│   └── ...
├── addon_portal\
├── main.py
└── ...
```

---

## 12. Implementation Priority

### Phase 1 (Critical - Week 1-2)
1. ✅ Subscription validation on project creation
2. ✅ Activation code assignment to projects
3. ✅ RUN PROJECT button and endpoint
4. ✅ Project execution service (main.py integration)

### Phase 2 (High - Week 3-4)
5. ✅ Tenant Status page (all projects view)
6. ✅ Self-service activation code generation
7. ✅ Quota tracking and validation

### Phase 3 (Medium - Week 5-6)
8. ✅ Multi-Agent Dashboard activation code login
9. ✅ Single project status view for clients
10. ✅ Project download feature

### Phase 4 (Nice-to-Have - Week 7-8)
11. ✅ Tenant Profile page
12. ✅ Tenant Billing page
13. ✅ Auto-pause on subscription inactive

---

## 13. Testing Requirements

1. **Project Creation:**
   - Test with active subscription ✅
   - Test with inactive subscription ❌
   - Test with missing required fields ❌

2. **Activation Code Assignment:**
   - Test code assignment to project
   - Test code usage validation
   - Test quota enforcement

3. **Project Execution:**
   - Test RUN PROJECT with valid activation code
   - Test RUN PROJECT without activation code ❌
   - Test folder creation
   - Test main.py integration

4. **Status Monitoring:**
   - Test tenant status page
   - Test client status page with activation code
   - Test progress updates

5. **Billing:**
   - Test plan upgrade flow
   - Test quota display
   - Test subscription renewal

---

## 14. Security Considerations

1. **Activation Code Security:**
   - Codes are hashed in database
   - Codes are single-use (max_uses=1)
   - Codes are permanently attached to project/device

2. **Project Execution:**
   - Validate tenant ownership
   - Validate subscription status
   - Sanitize project attributes before passing to main.py

3. **File System:**
   - Ensure proper folder permissions
   - Prevent directory traversal
   - Validate output folder paths

---

## Next Steps

1. Review and approve this plan
2. Create database migrations
3. Implement Phase 1 features
4. Test and iterate
5. Deploy to staging
6. User acceptance testing

---

**Document Status:** Ready for Implementation  
**Last Updated:** November 19, 2025

