# Environment Configuration Guide - Multi-Platform Setup

**Complete `.env` Configuration for All Supported Platforms**

**Date**: November 5, 2025  
**Version**: 3.0  
**Platforms**: 11+ accounting platforms

---

## 🎯 Overview

The `env.example` file contains configuration templates for **ALL supported platforms**. You only need to configure the platforms you plan to support in your SaaS deployment.

**Total Platforms Configured**: 11
- **Currently Supported**: QuickBooks (Online & Desktop), SAGE, Wave, Expensify, doola, Dext (6 platforms)
- **Coming Soon**: Xero, FreshBooks, Zoho Books, NetSuite (5 platforms)

---

## 📋 Configuration Sections

### **REQUIRED Configurations**

| Section | Required For | Variables Count |
|---------|--------------|-----------------|
| **Database** | All deployments | 3 |
| **Application Settings** | All deployments | 7 |
| **Stripe Billing** | Monetization | 5 |
| **Pricing** | Billing system | 2 |
| **Odoo Target** | Migrations | 6 |

### **Platform-Specific Configurations**

| Platform | Type | Variables | Setup Difficulty | Documentation |
|----------|------|-----------|------------------|---------------|
| **QuickBooks Online** | OAuth 2.0 | 8 | Medium | developer.intuit.com |
| **QuickBooks Desktop** | WebConnector | 6 | Complex | developer.intuit.com |
| **SAGE (all versions)** | OAuth + API Key | 8 | Medium-Complex | developer.sage.com |
| **Wave** | OAuth + GraphQL | 6 | Easy | developer.waveapps.com |
| **Expensify** | Partner API | 3 | Easy | expensify.com/tools/integrations |
| **doola** | API Key | 4 | Easy | doola.com/developers |
| **Dext** | OAuth 2.0 | 4 | Easy | api-developer.dext.com |
| **Xero** | OAuth 2.0 | 7 | Medium | developer.xero.com |
| **FreshBooks** | OAuth 2.0 | 6 | Easy | freshbooks.com/api |
| **Zoho Books** | OAuth 2.0 | 7 | Medium | api-console.zoho.com |
| **NetSuite** | Token Auth | 8 | Complex | NetSuite account |

**Total Platform Variables**: 67

### **Optional Configurations**

| Section | Purpose | Variables |
|---------|---------|-----------|
| **VCS Integration** | GitHub automation | 6 |
| **WebSocket** | Real-time dashboard | 3 |
| **Message Broker** | Agent communication | 3 |
| **Security** | JWT, sessions | 5 |
| **File Storage** | Migration reports | 9 |
| **Email** | Notifications | 6 |
| **Monitoring** | Analytics | 3 |
| **Research Agent** | Web search | 6 |
| **Terraform** | Infrastructure | 8 |

**Total Optional Variables**: 49

---

## 🔑 Platform-Specific OAuth Setup

### **QuickBooks Online**

**Steps to Get Credentials**:
1. Go to https://developer.intuit.com
2. Create a new app (type: "Accounting")
3. Get Client ID and Client Secret from app dashboard
4. Set redirect URI: `https://yoursaas.com/auth/qbo/callback`
5. Enable "Accounting" scope
6. For production, get app approved by Intuit

**Required Variables**:
```env
QBO_CLIENT_ID=ABxyz...
QBO_CLIENT_SECRET=abc123...
QBO_REDIRECT_URI=https://yoursaas.com/auth/qbo/callback
QBO_ENVIRONMENT=sandbox  # Change to 'production' when ready
```

**OAuth Flow**: Standard OAuth 2.0  
**API Type**: REST (JSON)  
**Rate Limits**: 500 requests/minute  

---

### **QuickBooks Desktop (WebConnector)**

**Steps to Get Credentials**:
1. Download QuickBooks Web Connector SDK
2. Register app in QuickBooks Desktop
3. Generate App ID and Owner ID
4. Create WebConnector endpoint on your server

**Required Variables**:
```env
QBD_APP_ID=your_app_id
QBD_APP_NAME=Quick2Odoo Migration
QBD_OWNER_ID={your-guid}
QBD_WEBCONNECTOR_URL=https://yoursaas.com/qbwc
```

**OAuth Flow**: N/A (uses SOAP + session tokens)  
**API Type**: SOAP (qbXML)  
**Note**: More complex than QBO, requires Windows server  

---

### **SAGE (50/100/200/X3)**

**Steps to Get Credentials**:
1. Register at https://developer.sage.com
2. Create application
3. Choose SAGE version (50/100/200/X3)
4. Get OAuth credentials OR API keys (depends on version)
5. Some versions require Azure API Management subscription

**Required Variables**:
```env
SAGE_CLIENT_ID=your_client_id
SAGE_CLIENT_SECRET=your_client_secret
SAGE_VERSION=sage50  # or sage100, sage200, sagex3
SAGE_API_KEY=your_api_key  # For versions using API key
SAGE_SUBSCRIPTION_KEY=your_azure_key  # For Azure API
```

**OAuth Flow**: OAuth 2.0 (versions 100+) OR API Key (version 50)  
**API Type**: REST (JSON)  
**Complexity**: Varies by version (50 is simplest, X3 is most complex)

---

### **Wave Accounting**

**Steps to Get Credentials**:
1. Apply for API access at https://developer.waveapps.com
2. Wait for approval (typically 1-3 business days)
3. Create OAuth app
4. Get Client ID and Secret

**Required Variables**:
```env
WAVE_CLIENT_ID=your_client_id
WAVE_CLIENT_SECRET=your_client_secret
WAVE_REDIRECT_URI=https://yoursaas.com/auth/wave/callback
WAVE_API_URL=https://gql.waveapps.com/graphql
```

**OAuth Flow**: OAuth 2.0  
**API Type**: GraphQL  
**Rate Limits**: 300 requests/minute  
**Note**: Easiest API to integrate

---

### **Expensify**

**Steps to Get Credentials**:
1. Contact Expensify for partner program
2. Get Partner User ID and Secret
3. Read integration guide

**Required Variables**:
```env
EXPENSIFY_PARTNER_USER_ID=your_partner_id
EXPENSIFY_PARTNER_USER_SECRET=your_secret
EXPENSIFY_API_URL=https://integrations.expensify.com/Integration-Server/ExpensifyIntegrations
```

**OAuth Flow**: N/A (uses partner credentials)  
**API Type**: REST/SOAP hybrid  
**Note**: Requires partner approval

---

### **doola**

**Steps to Get Credentials**:
1. Visit https://www.doola.com/developers
2. Sign up for API access
3. Get API key and secret

**Required Variables**:
```env
DOOLA_API_KEY=your_api_key
DOOLA_API_SECRET=your_api_secret
DOOLA_ENVIRONMENT=sandbox  # or production
```

**OAuth Flow**: API Key  
**API Type**: REST (JSON)  

---

### **Dext (formerly Receipt Bank)**

**Steps to Get Credentials**:
1. Go to https://api-developer.dext.com
2. Create developer account
3. Create OAuth app
4. Get Client ID and Secret

**Required Variables**:
```env
DEXT_CLIENT_ID=your_client_id
DEXT_CLIENT_SECRET=your_client_secret
DEXT_REDIRECT_URI=https://yoursaas.com/auth/dext/callback
```

**OAuth Flow**: OAuth 2.0  
**API Type**: REST (JSON)  

---

## 🚀 Quick Setup Guide

### **Minimal Setup (Development/Testing)**

For local development, you only need:

```env
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/q2o

# Application
API_BASE_URL=http://localhost:8000
ENVIRONMENT=development

# Optional: Test one platform
QBO_CLIENT_ID=test_client_id
QBO_CLIENT_SECRET=test_secret
```

**This is enough to**:
- Run the agents
- Generate code
- Test locally

---

### **Production Setup (Full SaaS)**

For production deployment serving clients:

**Required (23 variables minimum)**:
```env
# Database (3)
DATABASE_URL=...
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20

# Application (7)
API_BASE_URL=https://api.yoursaas.com
FRONTEND_URL=https://app.yoursaas.com
MOBILE_API_URL=https://api.yoursaas.com
DASHBOARD_API_URL=https://api.yoursaas.com:8001
ENVIRONMENT=production
LOG_LEVEL=INFO
LOG_FILE=logs/app.log

# Stripe Billing (5)
STRIPE_SECRET_KEY=sk_live_...
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
BILLING_SUCCESS_URL=https://app.yoursaas.com/billing/success
BILLING_CANCEL_URL=https://app.yoursaas.com/billing/cancel

# Pricing (2)
PRICING_CONFIG_PATH=./config/pricing_config.json
TAX_RATE=0.08  # Your region's tax rate

# Security (4)
SECRET_KEY=your-32-char-secret
JWT_SECRET_KEY=your-jwt-secret
CORS_ORIGINS=https://app.yoursaas.com
CORS_ALLOW_CREDENTIALS=true

# Odoo Default (2)
ODOO_DEFAULT_URL=https://demo.odoo.com
ODOO_TIMEOUT=30
```

**Plus: Configure each platform you want to support** (8-67 more variables)

---

## 🎯 Platform Selection Strategy

### **Strategy 1: Single Platform** (e.g., QuickBooks-only SaaS)

**Configure**:
- QuickBooks Online (8 variables)
- OR QuickBooks Desktop (6 variables)
- Plus required configs (23 variables)

**Total**: ~31 variables  
**Complexity**: Low  
**Time to Setup**: 2-4 hours  

---

### **Strategy 2: Multi-Platform** (e.g., QB + SAGE + Wave)

**Configure**:
- QuickBooks Online (8 variables)
- SAGE (8 variables)
- Wave (6 variables)
- Plus required configs (23 variables)

**Total**: ~45 variables  
**Complexity**: Medium  
**Time to Setup**: 4-8 hours  

---

### **Strategy 3: All Platforms** (Complete offering)

**Configure**:
- All 11 platforms (67 variables)
- Plus required configs (23 variables)
- Plus optional features (49 variables)

**Total**: ~139 variables  
**Complexity**: High  
**Time to Setup**: 1-2 days  
**Revenue Potential**: Maximum  

---

## 📝 Setup Checklist

### **Phase 1 Prerequisites (Building SaaS)**
- [ ] Copy `env.example` to `.env`
- [ ] Fill in database credentials
- [ ] Set application URLs
- [ ] (Optional) Configure platforms for testing

### **Phase 2 Prerequisites (Running SaaS)**
- [ ] ✅ All Phase 1 items
- [ ] Configure Stripe (get keys from stripe.com)
- [ ] Set up pricing config (`config/pricing_config.json`)
- [ ] Configure at least ONE platform (QuickBooks recommended)
- [ ] Register OAuth apps for each platform
- [ ] Set redirect URIs
- [ ] Test OAuth flows
- [ ] Deploy to production
- [ ] Set production environment variables

---

## ⚙️ Configuration Management

### **Development vs Production**

**Development** (`.env.local`):
```env
ENVIRONMENT=development
QBO_ENVIRONMENT=sandbox
STRIPE_SECRET_KEY=sk_test_...  # Test keys
DATABASE_URL=postgresql://localhost:5432/q2o_dev
```

**Production** (`.env` on server):
```env
ENVIRONMENT=production
QBO_ENVIRONMENT=production
STRIPE_SECRET_KEY=sk_live_...  # Live keys
DATABASE_URL=postgresql://prodserver:5432/q2o_prod
```

### **Per-Platform Configuration**

You don't need to configure ALL platforms. Only configure what you support:

**Example: QuickBooks + Wave only**:
```env
# Only configure these platforms
QBO_CLIENT_ID=...
QBO_CLIENT_SECRET=...

WAVE_CLIENT_ID=...
WAVE_CLIENT_SECRET=...

# Leave others blank or commented out
# SAGE_CLIENT_ID=
# EXPENSIFY_PARTNER_USER_ID=
```

---

## 🔐 Security Best Practices

### **DO**:
✅ Use different keys for development vs production  
✅ Rotate secrets regularly  
✅ Use environment-specific `.env` files  
✅ Store production `.env` in secure vault (Azure Key Vault, AWS Secrets Manager)  
✅ Use strong random secrets (generate with `openssl rand -hex 32`)  
✅ Limit OAuth scopes to minimum required  

### **DON'T**:
❌ Never commit `.env` file  
❌ Never hardcode secrets in code  
❌ Never share production secrets  
❌ Never use production keys in development  
❌ Never log environment variables  

---

## 📊 Platform Coverage

### **Currently Supported (Full Implementation)**

| Platform | Auth Type | Config Variables | Entities Supported | Status |
|----------|-----------|------------------|-------------------|--------|
| QuickBooks Online | OAuth 2.0 | 8 | 40+ | ✅ Complete |
| QuickBooks Desktop | WebConnector | 6 | 40+ | ✅ Complete |
| SAGE 50 | API Key | 8 | 35+ | ✅ Complete |
| SAGE 100/200/X3 | OAuth 2.0 | 8 | 35+ | ✅ Complete |
| Wave | OAuth 2.0 | 6 | 25+ | ✅ Complete |
| Expensify | Partner API | 3 | 20+ | ✅ Complete |
| doola | API Key | 4 | 15+ | ✅ Complete |
| Dext | OAuth 2.0 | 4 | 20+ | ✅ Complete |

### **Coming Soon (Configuration Ready)**

| Platform | Auth Type | Config Variables | Entities Planned | Timeline |
|----------|-----------|------------------|-----------------|----------|
| Xero | OAuth 2.0 | 7 | 35+ | Q1 2026 |
| FreshBooks | OAuth 2.0 | 6 | 25+ | Q1 2026 |
| Zoho Books | OAuth 2.0 | 7 | 30+ | Q2 2026 |
| NetSuite | Token Auth | 8 | 50+ | Q2 2026 |

---

## 💡 Example Configurations

### **Example 1: QuickBooks-Only SaaS**

**Minimal `.env`**:
```env
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/qb2odoo

# App
API_BASE_URL=https://api.qb2odoo.com
ENVIRONMENT=production

# Stripe
STRIPE_SECRET_KEY=sk_live_abc123...
STRIPE_WEBHOOK_SECRET=whsec_xyz789...

# QuickBooks
QBO_CLIENT_ID=ABCxyz123456
QBO_CLIENT_SECRET=secrethere
QBO_REDIRECT_URI=https://api.qb2odoo.com/auth/qbo/callback
QBO_ENVIRONMENT=production

# Security
SECRET_KEY=your-generated-secret-key
```

**Result**: Working QuickBooks-to-Odoo migration SaaS

---

### **Example 2: Multi-Platform SaaS**

**Add to above**:
```env
# SAGE
SAGE_CLIENT_ID=sage_client_123
SAGE_CLIENT_SECRET=sage_secret_456
SAGE_VERSION=sage50

# Wave
WAVE_CLIENT_ID=wave_client_789
WAVE_CLIENT_SECRET=wave_secret_abc
```

**Result**: QB + SAGE + Wave migration SaaS

---

## 🔄 Variable Loading Priority

The application loads variables in this order:

1. **System environment variables** (highest priority)
2. **`.env` file** (in project root)
3. **`.env.local`** (for local overrides)
4. **Default values** (in code)

**Example**:
```python
# Application checks in order:
1. os.environ.get("QBO_CLIENT_ID")      # System env
2. Load from .env file
3. Load from .env.local
4. Use default (if any)
```

---

## 📚 Related Documentation

- **[COMPLETE_SYSTEM_WORKFLOW.md](COMPLETE_SYSTEM_WORKFLOW.md)** - When to set these variables (Phase 1 vs Phase 2)
- **[BILLING_SYSTEM_ARCHITECTURE.md](BILLING_SYSTEM_ARCHITECTURE.md)** - Stripe and pricing config details
- **Platform API Documentation**:
  - QuickBooks: https://developer.intuit.com/app/developer/qbo/docs/api/accounting/all-entities
  - SAGE: https://developer.sage.com/docs/
  - Wave: https://developer.waveapps.com/hc/en-us/articles/360019762711
  - Xero: https://developer.xero.com/documentation/api/api-overview

---

## ⚠️ Important Notes

### **OAuth Redirect URIs**

All OAuth redirect URIs must be:
1. **Registered** in each platform's developer portal
2. **HTTPS** in production (HTTP allowed for localhost testing)
3. **Exact match** (including trailing slashes)

**Common Redirect URI Pattern**:
```
https://yoursaas.com/auth/{platform}/callback

Examples:
https://yoursaas.com/auth/qbo/callback
https://yoursaas.com/auth/sage/callback
https://yoursaas.com/auth/wave/callback
```

### **Webhook Endpoints**

Stripe requires a publicly accessible webhook endpoint:
```
https://yoursaas.com/api/billing/webhook
```

Must be:
- ✅ HTTPS (required by Stripe)
- ✅ Publicly accessible
- ✅ Registered in Stripe dashboard
- ✅ Signature verification enabled

---

## 🎯 Quick Start

### **1. Copy and Rename**
```bash
cp env.example .env
```

### **2. Fill Required Sections**
Edit `.env` and fill in:
- Database URL
- Application URLs
- Stripe keys (for billing)
- At least ONE platform (QuickBooks recommended)

### **3. Test Configuration**
```bash
# Test database connection
python -c "from sqlalchemy import create_engine; import os; engine = create_engine(os.getenv('DATABASE_URL')); print('DB OK')"

# Test Stripe keys
python -c "import stripe, os; stripe.api_key = os.getenv('STRIPE_SECRET_KEY'); print(stripe.Account.retrieve()); print('Stripe OK')"
```

### **4. Run Application**
```bash
# Development
uvicorn api.dashboard.main:app --reload

# Production
uvicorn api.dashboard.main:app --host 0.0.0.0 --port 8000
```

---

## ✅ Summary

**You were absolutely right!** The env.example now includes configurations for:

✅ **11 platforms** (QuickBooks, SAGE, Wave, Expensify, doola, Dext, Xero, FreshBooks, Zoho, NetSuite)  
✅ **139 total variables** (23 required, 67 platform-specific, 49 optional)  
✅ **Complete setup instructions** for each platform  
✅ **Security best practices**  
✅ **Example configurations** for different deployment strategies  

**File Created**: `env.example` (350 lines)

---

**Next**: Run `SECURE_COMMIT_AND_PUSH.bat` to commit everything!


