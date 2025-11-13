# Tenant-Project Architecture Proposal
**Date**: November 12, 2025  
**Status**: Proposal for Implementation

---

## 🎯 **Current Understanding**

### **Workflow:**
1. **Q2O Admin** → Creates Tenant → Creates Initial Activation Codes (10% of plan quota/month)
2. **Tenant (IT Consultant)** → Uses Tenant Dashboard → Creates Client Projects → Uses Activation Codes to activate projects
3. **Client** → Pays Tenant → Gets Access Token → Starts project (via Tenant Dashboard or Mobile App)

### **Activation Codes Purpose:**
- **Access Credits** that must be purchased based on subscription plan limits
- Used to **activate client projects** on the system
- Each code represents a "project run credit"

---

## 🔧 **Required Changes**

### **1. Database Schema Updates**

#### **Add `tenant_id` to `LLMProjectConfig`**
```python
class LLMProjectConfig(Base):
    # ... existing fields ...
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)  # NEW
    activation_code_id = Column(Integer, ForeignKey("activation_codes.id"), nullable=True)  # NEW - tracks which code activated this project
    project_status = Column(String(20), default="pending")  # NEW: pending, active, completed, paused
    started_at = Column(DateTime, nullable=True)  # NEW
    completed_at = Column(DateTime, nullable=True)  # NEW
```

#### **Add `project_id` to `ActivationCode` (optional - for tracking)**
```python
class ActivationCode(Base):
    # ... existing fields ...
    project_id = Column(String(100), ForeignKey("llm_project_config.project_id"), nullable=True)  # NEW - which project this code activated
    code_type = Column(String(20), default="device")  # NEW: "device" or "project"
```

### **2. Tenant Dashboard Features**

#### **Project Management Page** (`/projects`)
- **List Projects**: Show all client projects for the logged-in tenant
- **Create Project**: Form to create new client project
  - Client Name
  - Project Description/Objectives
  - Select Activation Code (from tenant's available codes)
- **Activate Project**: Use activation code to start a project
- **View Project Status**: See running/completed projects
- **Link to Multi-Agent Dashboard**: View project metrics

#### **Activation Codes Page** (`/codes`)
- **View Available Codes**: Show tenant's activation codes
- **Purchase More Codes**: (Future - Stripe integration)
- **Code Usage**: See which projects used which codes

### **3. Multi-Agent Dashboard Updates**

#### **Project Selection Interface**
- **Tenant Login/Selection**: 
  - Tenant users: Auto-filter to their projects only
  - Admin users: See all projects, filter by tenant
- **Project Selector**: Dropdown/list to select active project
- **Project Details View**: Detailed metrics for selected project
- **Real-time Updates**: WebSocket filtered by selected project

#### **Admin View**
- **All Projects View**: See all projects across all tenants
- **Tenant Filter**: Filter projects by tenant
- **Project Details**: Click project to see detailed dashboard

### **4. API Endpoints Needed**

#### **Tenant Project Management**
```
POST   /api/tenant/projects              - Create client project
GET    /api/tenant/projects              - List tenant's projects
GET    /api/tenant/projects/{project_id} - Get project details
POST   /api/tenant/projects/{project_id}/activate - Activate project with code
PUT    /api/tenant/projects/{project_id} - Update project
DELETE /api/tenant/projects/{project_id} - Delete project
```

#### **Multi-Agent Dashboard**
```
GET    /api/dashboard/projects           - List projects (filtered by tenant if not admin)
GET    /api/dashboard/projects/{project_id} - Get project metrics
WS     /ws/dashboard/{project_id}        - WebSocket for specific project
```

### **5. Authentication & Authorization**

#### **Tenant Authentication**
- Tenant logs in with **tenant slug** + **password** (or API key)
- JWT token includes `tenant_id` and `role` (tenant/admin)
- API endpoints filter by `tenant_id` automatically

#### **Project Activation Flow**
1. Tenant creates project → Project status: `pending`
2. Tenant selects activation code → Validates code belongs to tenant
3. Code is used → `project_id` linked to code, project status: `active`
4. Project starts → Multi-Agent Dashboard shows project metrics

---

## 📋 **Implementation Priority**

### **Phase 1: Database & Backend** (Critical)
1. ✅ Add `tenant_id` to `LLMProjectConfig` (migration)
2. ✅ Add project activation endpoints
3. ✅ Update activation code logic to support project activation
4. ✅ Add tenant-scoped project queries

### **Phase 2: Tenant Dashboard** (High Priority)
1. ✅ Create Project Management page
2. ✅ Add project creation form
3. ✅ Add project activation workflow
4. ✅ Link to Multi-Agent Dashboard with project context

### **Phase 3: Multi-Agent Dashboard** (High Priority)
1. ✅ Add project selection interface
2. ✅ Add tenant filtering (for admin)
3. ✅ Filter WebSocket by selected project
4. ✅ Show project-specific metrics

### **Phase 4: Admin Enhancements** (Medium Priority)
1. ✅ Admin view of all projects
2. ✅ Tenant filtering in admin view
3. ✅ Project creation from admin portal

---

## 🔐 **Security Considerations**

1. **Tenant Isolation**: Projects must be strictly scoped to tenant
2. **Code Validation**: Activation codes must belong to tenant
3. **Admin Override**: Admin can see all but cannot modify tenant projects
4. **Project Access**: Only tenant who owns project can activate/manage it

---

## 📊 **Data Flow Example**

```
1. Q2O Admin creates Tenant "acme-consulting"
   → Creates 5 activation codes (10% of plan quota)

2. Tenant logs into Tenant Dashboard (slug: acme-consulting)
   → Sees 5 available activation codes
   → Creates project "Client ABC Migration"
   → Selects activation code "12RY-S55W-4MZR-KP2J"
   → Activates project

3. Project starts running
   → Multi-Agent Dashboard shows "Client ABC Migration"
   → Real-time metrics for this project
   → Tenant can monitor progress

4. Client pays Tenant for access
   → Tenant generates new activation code for client
   → Client uses code to access their project dashboard
```

---

## ✅ **Next Steps**

1. Review and approve this architecture
2. Create database migration for `tenant_id` in projects
3. Implement backend APIs for tenant project management
4. Build Tenant Dashboard project management UI
5. Update Multi-Agent Dashboard with project selection
6. Test end-to-end workflow

---

**Status**: Ready for implementation once approved

