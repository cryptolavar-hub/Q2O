# Tenant-Project Implementation Plan
**Date**: November 12, 2025  
**Status**: Ready for Implementation  
**Priority**: Security-First, Database-Driven, Minimal Breaking Changes

---

## 🎯 **Clarified Requirements**

### **Activation Codes** (CLARIFIED)
- ✅ **Activate PROJECTS** (one code = one project activation, codes are consumed)
- ✅ **Auto-generate 10% of plan quota** when creating a tenant
- ✅ Show Tenants and Projects in Codes page (filter/find only, NO CRUD)
- ✅ Minor UI changes to display tenant/project relationships

### **Projects & Tenant Scoping**
- ✅ **Add `tenant_id` to `LLMProjectConfig`** (for scoping)
- ✅ **LLM Prompts remain ADMIN-ONLY** (security - no tenant editing)
- ✅ Future: Enterprise subscription level may allow prompt editing

### **Tenant Dashboard** (CRITICAL: Project Creation Hub)
- ✅ **Full CRUD for Projects** (tenant-scoped only)
  - **CREATE**: Tenants create projects via Tenant Dashboard (NOT Admin Portal)
  - **READ**: View all projects owned by tenant
  - **UPDATE**: Edit project details, client information, objectives
  - **DELETE**: Remove projects (with confirmation)
- ✅ **OTP Authentication** to tenant slug
- ✅ **Session timeout** after idle period (not viewing live data = idle)
- ✅ **Project Management Interface**: Primary interface for tenant project lifecycle
- ✅ **Client Management**: Tenants manage their own clients (name, company, address, credentials)
- ⚠️ **IMPORTANT**: Admin Portal does NOT create projects - only manages agent prompts for existing projects

### **Multi-Agent Dashboard**
- ✅ **Project selection** interface
- ✅ **Tenant/Client authentication**
- ✅ **Admin sees all**, Tenant sees own projects only

### **Security**
- ✅ **Strict security boundaries** (Admin vs Tenant)
- ✅ **Database-driven** access control
- ✅ **Best practices** and security measures

---

## 📋 **Implementation Phases**

### **Phase 1: Database Schema Updates** (Critical - No Breaking Changes)

#### **1.1 Add `tenant_id` to `LLMProjectConfig`**
```sql
ALTER TABLE llm_project_config 
ADD COLUMN tenant_id INTEGER REFERENCES tenants(id) ON DELETE CASCADE;

-- Create index for performance
CREATE INDEX idx_project_tenant ON llm_project_config(tenant_id);

-- Update existing projects (if any) - set to NULL or default tenant
-- For now, existing projects without tenant_id remain accessible to admin only
```

#### **1.2 Add Project Status Fields** (Optional - for future use)
```sql
ALTER TABLE llm_project_config
ADD COLUMN project_status VARCHAR(20) DEFAULT 'active',
ADD COLUMN started_at TIMESTAMP NULL,
ADD COLUMN completed_at TIMESTAMP NULL;
```

#### **1.3 Create Tenant Sessions Table** (For OTP & Session Management)
```sql
CREATE TABLE tenant_sessions (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    otp_code VARCHAR(6),
    otp_expires_at TIMESTAMP,
    last_activity TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_session_token (session_token),
    INDEX idx_tenant_sessions (tenant_id)
);
```

---

### **Phase 2: Backend API Updates** (Security-First)

#### **2.1 Tenant Authentication Service**
```python
# addon_portal/api/services/tenant_auth_service.py
- generate_otp(tenant_slug: str) -> str
- verify_otp(tenant_slug: str, otp: str) -> SessionToken
- validate_session(session_token: str) -> TenantInfo
- refresh_session(session_token: str) -> SessionToken
- logout(session_token: str)
```

#### **2.2 Tenant Project Management API**
```python
# addon_portal/api/routers/tenant_api.py (NEW)
POST   /api/tenant/auth/otp/generate     - Generate OTP for tenant slug
POST   /api/tenant/auth/otp/verify       - Verify OTP, get session token
POST   /api/tenant/auth/refresh          - Refresh session
POST   /api/tenant/auth/logout           - Logout

GET    /api/tenant/projects              - List tenant's projects (filtered by tenant_id from session)
POST   /api/tenant/projects              - Create project (auto-set tenant_id from session)
GET    /api/tenant/projects/{project_id} - Get project (verify tenant ownership)
PUT    /api/tenant/projects/{project_id} - Update project (verify tenant ownership)
DELETE /api/tenant/projects/{project_id} - Delete project (verify tenant ownership)
```

#### **2.3 Update LLM Project Service**
```python
# addon_portal/api/services/llm_config_service.py
- Add tenant_id filtering to list_projects()
- Add tenant_id validation to create_project()
- Add tenant ownership check to update/delete operations
```

#### **2.4 Multi-Agent Dashboard API**
```python
# addon_portal/api/routers/dashboard_api.py (NEW or update existing)
GET    /api/dashboard/projects            - List projects (filtered by tenant if not admin)
GET    /api/dashboard/projects/{project_id} - Get project metrics
WS     /ws/dashboard/{project_id}        - WebSocket filtered by project
```

#### **2.5 Update Activation Codes Endpoint**
```python
# addon_portal/api/routers/admin_api.py
GET    /admin/api/codes                  - Add project_id display (if code used for project)
# Show which projects (if any) are associated with tenant's codes
```

---

### **Phase 3: Tenant Dashboard Updates** (Project Management)

#### **3.1 Authentication Flow**
- **OTP Generation Page**: Tenant enters slug → Receives OTP
- **OTP Verification**: Enter OTP → Get session token → Store in localStorage/cookie
- **Session Management**: Auto-refresh on activity, timeout after idle
- **Protected Routes**: All pages require valid session

#### **3.2 Project Management Page** (`/projects`) - **PRIMARY PROJECT CREATION INTERFACE**
- **List Projects**: Show all projects for logged-in tenant
- **Create Project**: 
  - Form with project ID, client name, description, objectives
  - **Activation Code Required**: Projects are activated using activation codes
  - **One Code = One Project**: Each activation code activates one project
  - **Auto-link**: Project automatically linked to tenant's activation code
- **Edit Project**: Update project details, client information
- **Delete Project**: With confirmation (cascades to related data)
- **View Project**: Link to Multi-Agent Dashboard with project context
- **Client Management**: 
  - Manage client details (name, company name, address)
  - Store client credentials (username, passwords) securely
  - Link clients to projects

#### **3.3 Navigation Updates**
- Add "Projects" to navigation menu
- Add "Activation Codes" link (view only, no generation)
- Add logout button

---

### **Phase 4: Multi-Agent Dashboard Updates** (Project Selection)

#### **4.1 Authentication Interface**
- **Tenant Login**: Slug + OTP flow
- **Project Selector**: Dropdown/list of tenant's active projects
- **Admin Mode**: Admin can see all projects, filter by tenant

#### **4.2 Project Selection UI**
- **Project List**: Show available projects
- **Select Project**: Click to view project metrics
- **Real-time Updates**: WebSocket filtered by selected project

#### **4.3 Admin View**
- **All Projects**: See all projects across tenants
- **Tenant Filter**: Filter by tenant slug
- **Project Details**: Click for detailed dashboard

---

### **Phase 5: Security & Access Control**

#### **5.1 Middleware for Tenant Authentication**
```python
# addon_portal/api/middleware/tenant_auth.py
- Verify session token
- Extract tenant_id from session
- Add tenant_id to request state
- Handle session expiration
```

#### **5.2 Database-Level Security**
- **Row-Level Security**: All queries filter by tenant_id
- **Foreign Key Constraints**: Cascade deletes properly
- **Indexes**: Optimize tenant-scoped queries

#### **5.3 API Security**
- **Rate Limiting**: OTP generation limits
- **Session Expiration**: Configurable timeout
- **CSRF Protection**: For state-changing operations
- **Input Validation**: All inputs validated and sanitized

---

## 🔒 **Security Measures**

### **Authentication**
1. **OTP Generation**: Rate-limited (max 3 per hour per tenant)
2. **OTP Expiration**: 10-minute validity
3. **Session Tokens**: JWT with tenant_id, expiration, refresh mechanism
4. **Session Timeout**: 30 minutes idle, 24 hours max

### **Authorization**
1. **Tenant Isolation**: All queries filtered by tenant_id
2. **Project Ownership**: Verify tenant owns project before CRUD
3. **Admin Override**: Admin can view all but cannot modify tenant projects
4. **LLM Prompts**: Admin-only editing (security boundary)

### **Data Protection**
1. **SQL Injection**: Parameterized queries only
2. **XSS Protection**: Input sanitization
3. **CSRF Tokens**: For state-changing operations
4. **Audit Logging**: Track all project CRUD operations

---

## 📊 **Database Migration Plan**

### **Migration 1: Add tenant_id to projects**
```sql
-- Safe migration: Add nullable column first
ALTER TABLE llm_project_config ADD COLUMN tenant_id INTEGER NULL;

-- Add foreign key constraint
ALTER TABLE llm_project_config 
ADD CONSTRAINT fk_project_tenant 
FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE;

-- Create index
CREATE INDEX idx_project_tenant ON llm_project_config(tenant_id);

-- Update existing projects (set to NULL - admin-only access)
-- New projects will require tenant_id
```

### **Migration 2: Create tenant_sessions table**
```sql
CREATE TABLE tenant_sessions (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    otp_code VARCHAR(6),
    otp_expires_at TIMESTAMP,
    last_activity TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_session_token ON tenant_sessions(session_token);
CREATE INDEX idx_tenant_sessions ON tenant_sessions(tenant_id);
CREATE INDEX idx_session_expires ON tenant_sessions(expires_at);
```

---

## 🎨 **UI/UX Updates**

### **Tenant Dashboard**
1. **Login Page**: Slug input → OTP generation → OTP verification
2. **Projects Page**: Full CRUD interface with tenant branding
3. **Activation Codes Page**: View-only, shows tenant's codes
4. **Session Indicator**: Show remaining session time, logout button

### **Multi-Agent Dashboard**
1. **Login/Project Selection**: Tenant login → Project selector
2. **Project Context**: Show selected project name, tenant info
3. **Admin Mode**: Toggle to see all projects, tenant filter

### **Admin Portal**
1. **Codes Page**: Minor update to show tenant/project relationships
2. **Projects View**: Can see all projects, filter by tenant (READ-ONLY for tenant projects)
3. **Agent Prompts Management**: 
   - Admin assigns/manages agent-specific prompts for existing projects
   - **DOES NOT CREATE PROJECTS** - Projects are created by tenants via Tenant Dashboard
   - Projects must exist before agent prompts can be assigned

---

## ✅ **Implementation Checklist**

### **Database**
- [ ] Create migration for `tenant_id` in `llm_project_config`
- [ ] Create migration for `tenant_sessions` table
- [ ] Add indexes for performance
- [ ] Test migrations on dev database

### **Backend**
- [ ] Create `tenant_auth_service.py` (OTP, sessions)
- [ ] Create `tenant_api.py` router (auth + projects)
- [ ] Update `llm_config_service.py` (tenant filtering)
- [ ] Update `admin_api.py` (codes display)
- [ ] Create `dashboard_api.py` (project selection)
- [ ] Add tenant authentication middleware
- [ ] Add security middleware (rate limiting, CSRF)

### **Tenant Dashboard**
- [ ] Create OTP login flow
- [ ] Add session management
- [ ] Create Projects CRUD page
- [ ] Update navigation
- [ ] Add session timeout handling

### **Multi-Agent Dashboard**
- [ ] Add tenant authentication
- [ ] Add project selection UI
- [ ] Filter WebSocket by project
- [ ] Add admin mode toggle
- [ ] Update header with project context

### **Security**
- [ ] Implement rate limiting for OTP
- [ ] Add session expiration logic
- [ ] Add tenant isolation checks
- [ ] Add audit logging
- [ ] Security testing

---

## 📋 **Subscription Plan Features**

### **All Plans Include Tenant Dashboard Access**
All subscription plans (Starter, Pro, Enterprise) include access to the Tenant Dashboard with the following features:

#### **Core Features (All Plans)**
- ✅ **Project Creation & Management**: Create, view, edit, and delete projects
- ✅ **OTP Authentication**: Secure login via tenant slug + OTP
- ✅ **Project Dashboard**: View all tenant's projects
- ✅ **Activation Code Viewing**: View tenant's activation codes (read-only)
- ✅ **Client Management**: Manage client details (name, company, address, credentials)
- ✅ **Session Management**: Secure sessions with timeout protection

#### **Plan-Specific Features**

**Starter Plan:**
- ✅ Up to 10 active projects
- ✅ Basic project management
- ✅ Standard support

**Pro Plan:**
- ✅ Up to 50 active projects
- ✅ Advanced project management
- ✅ Priority support
- ✅ Custom branding

**Enterprise Plan:**
- ✅ Unlimited active projects
- ✅ Full project management suite
- ✅ 24/7 dedicated support
- ✅ White-label option
- ✅ Full API access
- ⚠️ **Future**: May include LLM prompt editing (currently Admin-only)

### **Admin Portal Features (Admin Only)**
- ✅ **Agent Prompts Management**: Assign/manage agent-specific prompts for existing projects
- ✅ **System Configuration**: Manage LLM providers, API keys, system prompts
- ✅ **Tenant Management**: Create tenants, manage subscriptions, generate activation codes
- ✅ **Analytics & Reporting**: View system-wide analytics and tenant usage
- ❌ **DOES NOT CREATE PROJECTS**: Projects are created by tenants via Tenant Dashboard

---

## 🚨 **Important Notes**

1. **No Breaking Changes**: Existing functionality remains intact
2. **Gradual Rollout**: Can deploy phases incrementally
3. **Backward Compatible**: Existing projects without tenant_id remain admin-accessible
4. **Security First**: All changes include security measures
5. **Database-Driven**: All access control via database queries
6. **⚠️ CRITICAL WORKFLOW**: 
   - **Tenants** create projects via Tenant Dashboard (requires active subscription)
   - **Admin** manages agent prompts for existing projects (via Admin Portal)
   - **Projects** are activated using activation codes (one code = one project)
   - **Activation codes** are generated by Admin and assigned to tenants

---

**Status**: Ready to implement Phase 1 (Database Schema)

