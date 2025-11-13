# Tenant Dashboard Features & Capabilities
**Date**: November 12, 2025  
**Status**: Implementation Plan  
**Priority**: Core Feature Set

---

## 🎯 **Overview**

The Tenant Dashboard is the **primary interface** for tenants to manage their projects, clients, and activation codes. It is accessible to all tenants with an active subscription (Starter, Pro, or Enterprise plan).

---

## 🔐 **Authentication & Access**

### **OTP-Based Authentication**
- **Login Flow**: Tenant enters slug → Receives OTP → Enters OTP → Gets session token
- **Session Management**: 
  - 30-minute idle timeout
  - 24-hour maximum session lifetime
  - Auto-refresh on activity
  - Secure token storage

### **Access Requirements**
- ✅ **Active Subscription**: Must have active subscription (Starter, Pro, or Enterprise)
- ✅ **Tenant Slug**: Unique identifier for tenant organization
- ✅ **OTP Verification**: One-time password sent via configured channel

---

## 📋 **Core Features**

### **1. Project Management** (PRIMARY FEATURE)

#### **Create Projects**
- **Location**: Tenant Dashboard → Projects → Create New Project
- **Required Fields**:
  - Project ID (unique identifier)
  - Client Name
  - Description
  - Objectives
- **Activation**: Projects are activated using activation codes
  - One activation code = One project activation
  - Codes are consumed when used
  - Auto-linked to tenant's activation code pool
- **Plan Limits**:
  - Starter: Up to 10 active projects
  - Pro: Up to 50 active projects
  - Enterprise: Unlimited active projects

#### **View Projects**
- List all projects owned by tenant
- Filter by status (active, pending, completed, paused)
- Search by project ID or client name
- View project details, status, and metrics

#### **Edit Projects**
- Update project details
- Modify client information
- Change project status
- Update objectives and descriptions

#### **Delete Projects**
- Remove projects with confirmation
- Cascades to related data (agent configs, etc.)
- Audit trail maintained

---

### **2. Client Management**

#### **Manage Client Details**
- **Client Name**: Primary identifier
- **Company Name**: Organization name
- **Address**: Physical address
- **Contact Information**: Email, phone
- **Credentials**: Username, passwords (stored securely)
- **Link to Projects**: Associate clients with projects

#### **Client CRUD Operations**
- Create new clients
- View client list
- Edit client information
- Delete clients (with confirmation)

---

### **3. Activation Codes**

#### **View Activation Codes**
- **Read-Only Access**: Tenants can view their activation codes
- **Code Status**: See which codes are active, used, expired, or revoked
- **Project Linking**: See which projects are linked to which codes
- **Usage Tracking**: View code usage history

#### **Code Generation**
- ❌ **NOT AVAILABLE**: Code generation is Admin-only
- ✅ **View Only**: Tenants can only view codes assigned to them

---

### **4. Project Dashboard**

#### **Overview Metrics**
- Total projects
- Active projects
- Projects by status
- Recent activity

#### **Quick Actions**
- Create new project
- View project details
- Link to Multi-Agent Dashboard
- Manage clients

---

## 🔒 **Security & Access Control**

### **Tenant Isolation**
- ✅ All queries filtered by `tenant_id`
- ✅ Cannot access other tenants' projects
- ✅ Cannot modify other tenants' data
- ✅ Session-based access control

### **Data Protection**
- ✅ Secure credential storage
- ✅ Encrypted session tokens
- ✅ Rate limiting on OTP generation
- ✅ Audit logging for all operations

---

## 📊 **Plan Comparison**

| Feature | Starter | Pro | Enterprise |
|---------|---------|-----|------------|
| **Max Active Projects** | 10 | 50 | Unlimited |
| **Project Creation** | ✅ | ✅ | ✅ |
| **Client Management** | ✅ | ✅ | ✅ |
| **Activation Code Viewing** | ✅ | ✅ | ✅ |
| **Custom Branding** | ❌ | ✅ | ✅ |
| **API Access** | ❌ | ✅ | ✅ |
| **Support Level** | Standard | Priority | 24/7 Dedicated |
| **White-Label** | ❌ | ❌ | ✅ |
| **LLM Prompt Editing** | ❌ | ❌ | ⚠️ Future |

---

## 🚫 **What Tenants CANNOT Do**

### **Admin-Only Features**
- ❌ Generate activation codes (Admin Portal only)
- ❌ Create/manage other tenants
- ❌ Edit system prompts (Admin Portal only)
- ❌ Assign agent prompts (Admin Portal only)
- ❌ View system-wide analytics
- ❌ Manage subscriptions (contact Admin)

### **Security Restrictions**
- ❌ Cannot access other tenants' data
- ❌ Cannot modify subscription plans
- ❌ Cannot bypass project limits
- ❌ Cannot access Admin Portal features

---

## 🔄 **Workflow Summary**

### **Project Creation Workflow**
1. **Tenant** logs into Tenant Dashboard (OTP authentication)
2. **Tenant** navigates to Projects page
3. **Tenant** clicks "Create New Project"
4. **Tenant** fills in project details (ID, client name, description)
5. **Tenant** uses activation code to activate project
6. **System** links project to tenant and activation code
7. **Admin** can then assign agent prompts (via Admin Portal)

### **Activation Code Workflow**
1. **Admin** generates activation codes for tenant (via Admin Portal)
2. **Admin** assigns codes to tenant
3. **Tenant** views codes in Tenant Dashboard (read-only)
4. **Tenant** uses code to activate project
5. **System** marks code as used and links to project

---

## 📝 **Implementation Notes**

### **Database Integration**
- All project data stored in `llm_project_config` table
- Projects linked to tenants via `tenant_id` foreign key
- Activation codes linked via `activation_code_id` foreign key
- Client data stored securely (encrypted credentials)

### **API Endpoints**
- `POST /api/tenant/projects` - Create project (tenant-scoped)
- `GET /api/tenant/projects` - List tenant's projects
- `PUT /api/tenant/projects/{id}` - Update project (ownership verified)
- `DELETE /api/tenant/projects/{id}` - Delete project (ownership verified)

### **UI Components**
- Project list view with filtering/search
- Project creation form
- Project edit form
- Client management interface
- Activation code viewer (read-only)

---

## ✅ **Status**

- ✅ **Database Schema**: Complete (tenant_id added to projects)
- ✅ **Backend API**: Complete (tenant authentication + project CRUD)
- ⏳ **Tenant Dashboard UI**: In Progress
- ⏳ **Client Management**: Planned
- ⏳ **Activation Code Viewer**: Planned

---

**Last Updated**: November 12, 2025

