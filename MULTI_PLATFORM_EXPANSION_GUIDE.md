# Multi-Platform Expansion Guide
**Supporting Multiple Accounting Platforms Beyond QuickBooks**  
**Version**: 1.0  
**Date**: November 3, 2025

---

## 🎯 **Vision**

Expand QuickOdoo from QuickBooks-only to supporting **10+ accounting platforms**, making it the universal accounting-to-Odoo migration solution.

---

## 📋 **Platforms to Support**

### **Current**:
1. ✅ QuickBooks Online (QBO)
2. ✅ QuickBooks Desktop (QBD via Web Connector)

### **Planned** (Phase 4):
3. 📋 **SAGE (Peachtree)** - Enterprise accounting
4. 📋 **doola** - Startup financial platform
5. 📋 **Expensify** - Expense management
6. 📋 **Dext** - Receipt processing & bookkeeping
7. 📋 **Sage 50cloud** - Cloud accounting
8. 📋 **Wave** - Free accounting for SMBs
9. 📋 **Pabbly** - Subscription billing
10. 📋 **Melio** - B2B payments

**Total**: 10 platforms supported

---

## 🏗️ **Architecture Approach**

### **Design Pattern: Platform Adapters**

```python
# Unified architecture for all platforms

┌────────────────────────────────────────┐
│      IntegrationManager                │
│  (Single entry point for all platforms)│
└───────────────┬────────────────────────┘
                │
     ┌──────────┴──────────┬─────────────┬──────────┐
     ▼                     ▼             ▼          ▼
┌─────────┐         ┌─────────┐    ┌─────────┐  ┌──────┐
│QuickBook│         │  SAGE   │    │ doola   │  │ Wave │
│ Adapter │         │ Adapter │    │ Adapter │  │Adapt.│
└────┬────┘         └────┬────┘    └────┬────┘  └───┬──┘
     │                   │              │           │
     └───────────────────┴──────────────┴───────────┘
                         │
                  ┌──────▼──────┐
                  │   Unified   │
                  │   Format    │
                  └──────┬──────┘
                         │
                  ┌──────▼──────┐
                  │   Odoo v18  │
                  │Transformation│
                  └──────┬──────┘
                         │
                  ┌──────▼──────┐
                  │  Odoo Sync  │
                  └─────────────┘
```

### **Key Principles**:

1. **One Adapter Per Platform** (Modular, isolated)
2. **Unified Data Format** (Platform → Unified → Odoo)
3. **Template-Based** (Consistent, maintainable)
4. **Research-Driven** (ResearcherAgent accelerates each integration)
5. **Incremental** (One platform at a time)

---

## 🔧 **HOW TO: Add a New Platform**

### **Complete Step-by-Step Guide**

---

### **PHASE 1: RESEARCH** (2-3 days)

#### **Day 1: Automated Research with ResearcherAgent** ⭐

**Why This is Powerful**: The ResearcherAgent does in minutes what used to take days!

```bash
# Step 1: Research API Documentation
python main.py \
  --project "SAGE Integration Research" \
  --objective "Research SAGE 50cloud API v3.1 complete documentation" \
  --workspace ./sage_research

# Output: research/sage_50cloud_api_20251103_*.md
# Contains: API docs, endpoints, rate limits, best practices

# Step 2: Research Authentication
python main.py \
  --project "SAGE OAuth Research" \
  --objective "Research SAGE 50cloud OAuth 2.0 authentication flow with code examples" \
  --workspace ./sage_research

# Output: OAuth flow documentation, code examples, gotchas

# Step 3: Research Data Models
python main.py \
  --project "SAGE Data Models" \
  --objective "Research SAGE customer, invoice, and item data structures and field mappings" \
  --workspace ./sage_research

# Step 4: Research Python Libraries
python main.py \
  --project "SAGE Python Client" \
  --objective "Find SAGE 50cloud Python client library examples and implementations" \
  --workspace ./sage_research

# Step 5: Research Limitations
python main.py \
  --project "SAGE Limitations" \
  --objective "Research SAGE API rate limits, known issues, and workarounds" \
  --workspace ./sage_research
```

**Results** (in `./sage_research/research/`):
- 5+ markdown reports with findings
- Official documentation URLs
- Code examples extracted from web
- Confidence scores for each research
- Cached for 90 days (reusable!)

#### **Day 2: Review Research Findings**

```bash
# Read all research reports
ls sage_research/research/*.md

# High-confidence findings (score 80+):
cat sage_research/research/*_api_*.md  # API docs
cat sage_research/research/*_oauth_*.md  # Auth flow
cat sage_research/research/*_data_*.md  # Data models

# Check confidence scores
grep "Confidence Score" sage_research/research/*.md

# Ideal: All scores 70+ = good quality research
```

**Extract Key Information**:
- ✅ Base API URL
- ✅ Authentication endpoints
- ✅ API version
- ✅ Rate limits
- ✅ Required scopes/permissions
- ✅ Common data fields
- ✅ Known gotchas

#### **Day 3: Design Adapter**

Create design document: `docs/integrations/SAGE_DESIGN.md`

```markdown
# SAGE Adapter Design

## Authentication
- Type: OAuth 2.0
- Auth URL: https://...
- Token URL: https://...
- Scopes: accounting, customers, invoices

## Endpoints
- Customers: GET /v3.1/companies/{id}/customers
- Invoices: GET /v3.1/companies/{id}/sales_invoices
- Items: GET /v3.1/companies/{id}/products

## Data Mapping
SAGE Customer → Unified → Odoo res.partner
- id → platform_id → x_sage_id
- name → name → name
- email → email → email
- ...

## Rate Limiting
- 100 requests/minute
- Implement exponential backoff
- Use rate limiter utility

## Known Issues
- [From research] Issue 1...
- [From research] Issue 2...
```

---

### **PHASE 2: IMPLEMENTATION** (5-7 days)

#### **Day 1: Create Adapter Class**

```python
# api/app/clients/sage_adapter.py

from .platform_adapter import AccountingPlatformAdapter
from typing import List, Dict, Optional
import requests
import time

class SageAdapter(AccountingPlatformAdapter):
    """
    SAGE 50cloud accounting platform adapter.
    
    Implements the unified platform interface for SAGE 50cloud.
    
    Documentation: https://developer.sage.com/
    API Version: v3.1
    """
    
    PLATFORM_NAME = "sage"
    API_VERSION = "v3.1"
    
    def __init__(self, api_key: str, company_id: str, environment: str = "production"):
        """
        Initialize SAGE adapter.
        
        Args:
            api_key: SAGE API key
            company_id: SAGE company ID
            environment: 'production' or 'sandbox'
        """
        self.api_key = api_key
        self.company_id = company_id
        self.base_url = self._get_base_url(environment)
        
        # Setup HTTP session
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 0.6  # 100/min = 0.6s between requests
    
    def _get_base_url(self, environment: str) -> str:
        """Get API base URL for environment."""
        if environment == "sandbox":
            return "https://api-sandbox.sage.com/v3.1"
        return "https://api.sage.com/v3.1"
    
    def _rate_limit(self):
        """Enforce rate limiting."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
        self.last_request_time = time.time()
    
    def _request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """Make rate-limited request."""
        self._rate_limit()
        url = f"{self.base_url}/companies/{self.company_id}/{endpoint}"
        response = self.session.request(method, url, **kwargs)
        response.raise_for_status()
        return response.json()
    
    def authenticate(self) -> Dict:
        """Validate authentication and get company info."""
        return self._request('GET', '')  # Company info
    
    def get_customers(self) -> List[Dict]:
        """Fetch all customers from SAGE."""
        sage_customers = self._request('GET', 'customers')
        items = sage_customers.get('items', [])
        return [self._transform_customer_to_unified(c) for c in items]
    
    def _transform_customer_to_unified(self, sage_customer: Dict) -> Dict:
        """Transform SAGE customer to unified format."""
        return {
            'id': str(sage_customer.get('id')),
            'name': sage_customer.get('name', ''),
            'email': sage_customer.get('email', ''),
            'phone': sage_customer.get('phone', ''),
            'address': {
                'street': sage_customer.get('main_address', {}).get('address_line_1', ''),
                'city': sage_customer.get('main_address', {}).get('city', ''),
                'state': sage_customer.get('main_address', {}).get('region', ''),
                'zip': sage_customer.get('main_address', {}).get('postal_code', ''),
                'country': sage_customer.get('main_address', {}).get('country_code', '')
            },
            'platform': 'sage',
            'platform_id': str(sage_customer.get('id')),
            'raw_data': sage_customer  # Keep for debugging
        }
    
    def transform_to_odoo(self, entity_type: str, unified_data: Dict) -> Dict:
        """Transform unified format to Odoo format."""
        if entity_type == 'customer':
            return {
                'name': unified_data['name'],
                'email': unified_data['email'] or False,
                'phone': unified_data['phone'] or False,
                'street': unified_data['address']['street'],
                'city': unified_data['address']['city'],
                'zip': unified_data['address']['zip'],
                # Odoo custom fields for source tracking
                'x_source_platform': 'sage',
                'x_source_id': unified_data['platform_id'],
                'x_sage_raw_data': json.dumps(unified_data['raw_data'])
            }
        
        # Handle other entity types (invoices, items, etc.)
        raise ValueError(f"Unknown entity type: {entity_type}")
    
    # Implement other required methods...
    def get_invoices(self, start_date: Optional[str] = None) -> List[Dict]:
        # Implementation
        pass
    
    def get_items(self) -> List[Dict]:
        # Implementation
        pass
```

#### **Day 2: OAuth Handler** (if OAuth)

```python
# api/app/oauth_sage.py

from fastapi import APIRouter, HTTPException
import requests
import os

class SageOAuth:
    """SAGE OAuth 2.0 handler."""
    
    AUTH_URL = "https://www.sageone.com/oauth2/auth/central"
    TOKEN_URL = "https://oauth.sageone.com/oauth2/token"
    
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
    
    def get_authorization_url(self, state: str) -> str:
        """Generate authorization URL."""
        params = {
            'response_type': 'code',
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'scope': 'full_access',
            'state': state
        }
        return f"{self.AUTH_URL}?{'&'.join(f'{k}={v}' for k, v in params.items())}"
    
    def exchange_code_for_token(self, code: str) -> Dict:
        """Exchange auth code for access token."""
        # Implementation based on SAGE OAuth specs
        pass
```

#### **Day 3-4: Templates**

Create Jinja2 templates for code generation:

```jinja2
{# templates/integration/sage/client.j2 #}
"""
SAGE 50cloud API Client
Generated by IntegrationAgent
"""

import requests
from typing import List, Dict, Optional
import os

SAGE_API_KEY = os.getenv("SAGE_API_KEY")
SAGE_COMPANY_ID = os.getenv("SAGE_COMPANY_ID")
SAGE_ENVIRONMENT = os.getenv("SAGE_ENVIRONMENT", "production")

class SageClient:
    """SAGE 50cloud API client."""
    
    def __init__(self, api_key: str = None, company_id: str = None):
        self.api_key = api_key or SAGE_API_KEY
        self.company_id = company_id or SAGE_COMPANY_ID
        # ... (rest from adapter code)
```

#### **Day 5: Integration Agent Update**

```python
# agents/integration_agent.py

def _detect_platform(self, description: str) -> str:
    """Detect which platform to integrate."""
    description = description.lower()
    
    platforms = {
        'quickbooks': ['quickbooks', 'qbo', 'qbd'],
        'sage': ['sage', 'peachtree', 'sage50'],
        'doola': ['doola'],
        'expensify': ['expensify'],
        'dext': ['dext', 'receipt bank'],
        'wave': ['wave'],
        'pabbly': ['pabbly'],
        'melio': ['melio']
    }
    
    for platform, keywords in platforms.items():
        if any(kw in description for kw in keywords):
            return platform
    
    return 'unknown'

def _create_platform_integration(self, task: Task) -> List[str]:
    """Create integration for detected platform."""
    platform = self._detect_platform(task.description)
    
    platform_handlers = {
        'quickbooks': self._create_quickbooks_integration,
        'sage': self._create_sage_integration,
        'doola': self._create_doola_integration,
        # ... add more
    }
    
    handler = platform_handlers.get(platform)
    if handler:
        return handler(task)
    else:
        # Unknown platform - request research!
        if hasattr(self, 'request_research'):
            self.request_research(
                query=f"{platform} accounting API Python integration",
                task_id=task.id,
                urgency="high"
            )
        raise ValueError(f"Unknown platform: {platform}")
```

---

### **PHASE 3: TESTING** (3-4 days)

#### **Day 1: Unit Tests**

```python
# tests/test_sage_adapter.py

import pytest
from api.app.clients.sage_adapter import SageAdapter

class TestSageAdapter:
    """Test SAGE adapter functionality."""
    
    @pytest.fixture
    def sage_adapter(self):
        """Create SAGE adapter for testing."""
        return SageAdapter(
            api_key="test_key",
            company_id="test_company",
            environment="sandbox"
        )
    
    def test_initialization(self, sage_adapter):
        """Test adapter initializes correctly."""
        assert sage_adapter.platform_name == "sage"
        assert sage_adapter.api_version == "v3.1"
    
    def test_get_customers(self, sage_adapter, mocker):
        """Test customer fetching."""
        # Mock API response
        mock_response = {
            'items': [
                {'id': 1, 'name': 'Test Customer', 'email': 'test@example.com'}
            ]
        }
        mocker.patch.object(sage_adapter, '_request', return_value=mock_response)
        
        customers = sage_adapter.get_customers()
        
        assert len(customers) == 1
        assert customers[0]['name'] == 'Test Customer'
        assert customers[0]['platform'] == 'sage'
    
    def test_transform_to_odoo(self, sage_adapter):
        """Test transformation to Odoo format."""
        unified_data = {
            'name': 'Test Company',
            'email': 'test@example.com',
            'platform_id': '123'
        }
        
        odoo_data = sage_adapter.transform_to_odoo('customer', unified_data)
        
        assert odoo_data['name'] == 'Test Company'
        assert odoo_data['x_source_platform'] == 'sage'
        assert odoo_data['x_source_id'] == '123'
```

#### **Day 2: Integration Tests**

```python
# tests/integration/test_sage_to_odoo.py

def test_sage_to_odoo_customer_sync():
    """Test complete customer sync from SAGE to Odoo."""
    # Requires SAGE sandbox + Odoo test instance
    
    # 1. Fetch from SAGE
    sage_adapter = SageAdapter(...)
    customers = sage_adapter.get_customers()
    
    # 2. Transform to Odoo
    odoo_client = OdooClient(...)
    for customer in customers:
        odoo_data = sage_adapter.transform_to_odoo('customer', customer)
        
        # 3. Sync to Odoo
        odoo_id = odoo_client.create('res.partner', odoo_data)
        
        assert odoo_id > 0
```

#### **Day 3: Sandbox Testing**

Manual testing checklist:
- [ ] Create SAGE sandbox account
- [ ] Generate API credentials
- [ ] Test OAuth flow manually
- [ ] Verify data fetches correctly
- [ ] Check rate limiting works
- [ ] Validate Odoo sync
- [ ] Test error scenarios

---

### **PHASE 4: DOCUMENTATION** (1-2 days)

#### **Create Integration Guide**

```markdown
# docs/integrations/SAGE_INTEGRATION.md

## SAGE 50cloud Integration Guide

### Overview
Integrate SAGE 50cloud accounting data with Odoo v18.

### Prerequisites
- SAGE 50cloud account
- SAGE API credentials
- Odoo v18 instance

### Setup

#### Step 1: Get SAGE API Credentials

1. Log into SAGE Developer Portal: https://developer.sage.com/
2. Create new application
3. Copy Client ID and Client Secret
4. Set redirect URI: https://your-app.com/auth/sage/callback

#### Step 2: Configure Environment

Add to `.env`:
```bash
SAGE_API_KEY=your_api_key_here
SAGE_COMPANY_ID=your_company_id
SAGE_CLIENT_ID=your_client_id
SAGE_CLIENT_SECRET=your_client_secret
SAGE_ENVIRONMENT=sandbox  # or 'production'
```

#### Step 3: Run Integration

```bash
python main.py \
  --project "SAGE to Odoo Sync" \
  --objective "SAGE integration with OAuth" \
  --workspace ./sage_integration
```

### Data Mapping

| SAGE Field | Unified Field | Odoo Field |
|------------|---------------|------------|
| id | platform_id | x_sage_id |
| name | name | name |
| email | email | email |
| phone | phone | phone |

### Troubleshooting

**Issue**: Authentication fails
**Solution**: Check API credentials, verify redirect URI

**Issue**: Rate limit exceeded
**Solution**: System automatically handles with backoff

### API Limitations
- Rate limit: 100 requests/minute
- No bulk operations
- Pagination required for >100 records

### Support
- SAGE API Docs: https://developer.sage.com/
- Issue Tracker: https://github.com/cryptolavar-hub/Q2O/issues
```

---

## 🔄 **Repeat for Each Platform**

### **Per-Platform Timeline**

| Week | Activity | Output |
|------|----------|--------|
| Week 1 | Research + Design | Research reports + design doc |
| Week 2 | Implementation | Adapter + OAuth + Templates |
| Week 3 | Testing + Docs | Tests passing + Integration guide |

**Total**: 3 weeks per platform

### **Cumulative Timeline**

```
Month 1 (Jan 2026):  Platform Architecture + SAGE
Month 2 (Feb 2026):  doola + Wave (2 platforms)
Month 3 (Mar 2026):  Expensify + Dext (2 platforms)
Month 4 (Apr 2026):  Sage 50cloud + Pabbly (2 platforms)
Month 5 (May 2026):  Melio + Testing
Month 6 (Jun 2026):  Dashboard + Final Polish

Total: 6 months for 8 new platforms
```

---

## 🎯 **Configuration Per Platform**

### **Environment Variables Structure**

```bash
# .env example with all platforms

# ============================================================
# QuickBooks (Existing)
# ============================================================
QBO_CLIENT_ID=
QBO_CLIENT_SECRET=
QBO_REDIRECT_URI=

# ============================================================
# SAGE 50cloud
# ============================================================
SAGE_API_KEY=
SAGE_COMPANY_ID=
SAGE_CLIENT_ID=
SAGE_CLIENT_SECRET=
SAGE_ENVIRONMENT=production

# ============================================================
# doola
# ============================================================
DOOLA_CLIENT_ID=
DOOLA_CLIENT_SECRET=
DOOLA_WEBHOOK_SECRET=

# ============================================================
# Wave
# ============================================================
WAVE_ACCESS_TOKEN=
WAVE_BUSINESS_ID=

# ============================================================
# Expensify
# ============================================================
EXPENSIFY_PARTNER_USER_ID=
EXPENSIFY_PARTNER_USER_SECRET=

# ============================================================
# Dext (Receipt Bank)
# ============================================================
DEXT_API_KEY=
DEXT_CLIENT_ID=

# ============================================================
# Sage 50cloud
# ============================================================
SAGE50_CLIENT_ID=
SAGE50_CLIENT_SECRET=

# ============================================================
# Pabbly
# ============================================================
PABBLY_API_KEY=

# ============================================================
# Melio
# ============================================================
MELIO_CLIENT_ID=
MELIO_CLIENT_SECRET=
```

---

## 🎓 **Best Practices**

### **1. Research First, Code Second** ⭐

```bash
# ALWAYS start with ResearcherAgent
python main.py --objective "Research [Platform] API" --workspace ./research

# This finds:
# - Official documentation
# - Code examples  
# - Known issues
# - Best practices

# Saves DAYS of manual research!
```

### **2. Follow the Adapter Pattern**

- ✅ All platforms implement same interface
- ✅ Unified data format
- ✅ Consistent error handling
- ✅ Standard rate limiting

### **3. Test with Sandbox First**

- ✅ Use sandbox/test accounts
- ✅ Never test with production data
- ✅ Validate thoroughly before production

### **4. Document Everything**

- ✅ API quirks and gotchas
- ✅ Field mappings
- ✅ Rate limits
- ✅ Known issues

### **5. Leverage Existing Code**

- ✅ Copy QuickBooks adapter as template
- ✅ Reuse OAuth patterns
- ✅ Reuse transformation logic
- ✅ ~60% code reuse possible

---

## 📊 **Effort Estimates**

### **Per Platform**:

| Task | Time | Difficulty |
|------|------|------------|
| Research (with ResearcherAgent) | 1-2 days | Easy |
| Design | 1 day | Medium |
| Adapter Implementation | 2-3 days | Medium-Hard |
| OAuth (if needed) | 1-2 days | Hard |
| Templates | 1 day | Easy |
| Testing | 2-3 days | Medium |
| Documentation | 1 day | Easy |
| **Total** | **9-13 days** | **Medium** |

**With Experience**: 2-3 weeks per platform  
**First Platform**: 3-4 weeks (learning curve)

### **Total for 8 Platforms**:

- **Optimistic**: 16 weeks (4 months)
- **Realistic**: 24 weeks (6 months)
- **Conservative**: 32 weeks (8 months)

**Recommendation**: **6 months** with buffer

---

## 🚀 **Platform Priority & Rationale**

### **Priority 1: SAGE (Peachtree)**
**Why**: Large enterprise user base, mature API, high demand  
**Timeline**: Q1 2026  
**Complexity**: Medium-High  

### **Priority 2: doola**
**Why**: Growing startup platform, modern API, good documentation  
**Timeline**: Q1 2026  
**Complexity**: Medium  

### **Priority 3: Wave**
**Why**: Free platform, huge SMB user base, unique GraphQL API  
**Timeline**: Q2 2026  
**Complexity**: Medium (GraphQL learning curve)  

### **Priority 4: Expensify**
**Why**: Dominant expense management platform  
**Timeline**: Q2 2026  
**Complexity**: Medium  

### **Priority 5-8: Remaining Platforms**
**Timeline**: Q2-Q3 2026  
**Approach**: Based on customer demand and feedback  

---

## ✅ **Success Criteria**

### **Per Platform**:
- ✅ Adapter passes all unit tests
- ✅ OAuth flow working (if applicable)
- ✅ Data sync with Odoo verified
- ✅ Rate limiting respected
- ✅ Error handling robust
- ✅ Documentation complete
- ✅ Security scan passing

### **Overall Multi-Platform**:
- ✅ 10+ platforms supported
- ✅ Unified architecture
- ✅ Consistent user experience
- ✅ Platform selection UI
- ✅ Multi-tenant support
- ✅ All platforms tested

---

## 📞 **Resources**

**Implementation Guides**:
- `IMPLEMENTATION_ROADMAP_COMPLETE.md` - Complete roadmap
- `IMPLEMENTATION_PLAN_V2.md` - This document
- `RESEARCHER_AGENT_GUIDE.md` - How to use research

**Code Examples**:
- `api/app/clients/qbo.py` - QuickBooks adapter (reference)
- `api/app/oauth_qbo.py` - OAuth implementation (reference)
- `templates/integration/` - Integration templates

**Tools**:
- ResearcherAgent - Automated API research
- Template System - Code generation
- Testing Suite - Validation

---

**Ready to expand to 10+ accounting platforms with intelligent, automated integration!** 🚀

---

**Plan Version**: 2.0  
**Last Updated**: November 3, 2025  
**Status**: Foundation Complete, Ready for Multi-Platform Phase

