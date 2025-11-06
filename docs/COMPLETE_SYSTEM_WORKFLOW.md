# Complete System Workflow - End-to-End Clarity

**CRITICAL DOCUMENT**: Understanding the Two-Phase Nature of Quick2Odoo

**Date**: November 5, 2025  
**Purpose**: Eliminate all ambiguity about how the system works

---

## 📌 **IMPORTANT: This Describes What Agents Build**

This document explains the complete workflow of Quick2Odoo's **agent-driven system**:

- **Phase 1**: Agents **BUILD** the SaaS application dynamically (described in this doc)
- **Phase 2**: End users **USE** the agent-built SaaS to migrate their data

**The configurations, clients, APIs, and components described here are what the AGENTS GENERATE based on your objectives - not pre-built solutions.**

When you run:
```bash
python main.py --project "SAGE Migration" --objective "Full migration"
```

The agents research SAGE API, generate all necessary code, and produce a complete working system. This document explains that process.

---

## 🎯 **CRITICAL DISTINCTION**

Quick2Odoo operates in **TWO DISTINCT PHASES**:

```
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 1: BUILD THE SAAS APPLICATION                            │
│  (One-time per SaaS product)                                     │
│  Duration: Hours to Days                                         │
│  Who: Developer/Consultant                                       │
│  Payment: N/A (internal development)                             │
│                                                                   │
│  Quick2Odoo Agents → Generate Code → Deploy SaaS                │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 2: USE THE SAAS TO MIGRATE CLIENT DATA                   │
│  (Multiple times - once per client migration)                    │
│  Duration: Minutes to Hours                                      │
│  Who: End Client                                                 │
│  Payment: YES - Based on data volume                             │
│                                                                   │
│  Client → Pay → Connect Platform → Migrate Data                 │
└─────────────────────────────────────────────────────────────────┘
```

**The billing system charges for PHASE 2, not PHASE 1.**

---

## 📋 **PHASE 1: Building the SaaS Application**

### **1.1 Prerequisites**

**Before running Quick2Odoo agents**, you need:

| Requirement | Description | Example |
|-------------|-------------|---------|
| **Python Environment** | Python 3.10+ installed | `python --version` |
| **Dependencies** | All packages installed | `pip install -r requirements.txt` |
| **Configuration File** | Project definition | `config.json` |
| **Workspace** | Output directory | `./my_saas_project` |
| **Optionally**: |||
| - Odoo instance | For integration testing | `https://odoo.example.com` |
| - QuickBooks sandbox | For OAuth testing | Intuit developer account |
| - Stripe test keys | For billing testing | Stripe dashboard |

---

### **1.2 Configuration: config.json**

**This file defines WHAT SaaS to build**:

```json
{
  "project_description": "Multi-Platform to Odoo v18 Migration SaaS",
  
  "platforms": [
    "QuickBooks",
    "SAGE",
    "Wave",
    "Expensify",
    "doola",
    "Dext"
  ],
  
  "objectives": [
    "OAuth authentication for all platforms",
    "Full data extraction (40+ QuickBooks entities, 35+ SAGE entities, etc.)",
    "Universal platform-to-Odoo mapping system",
    "Data-volume-based billing with Stripe",
    "Real-time migration monitoring dashboard",
    "Mobile app for migration initiation",
    "Automated testing and QA",
    "Security scanning and hardening",
    "Terraform infrastructure for Azure",
    "Kubernetes deployment with Helm"
  ],
  
  "workspace": "./generated_saas",
  
  "deployment": {
    "target": "Azure App Service",
    "environment": "production"
  }
}
```

---

### **1.3 Running the Agents**

**Command to build the SaaS**:

```bash
python main.py --config config.json --workspace ./my_saas_project
```

**What happens (PHASE 1 - Building)**:

```
Step 1: Orchestrator Agent
  ↓ Reads config.json
  ↓ Breaks down objectives into tasks
  ↓ Creates task queue (50-100 tasks)

Step 2: Agent Execution (Parallel)
  ├─→ ResearcherAgent: Researches OAuth best practices for each platform
  ├─→ IntegrationAgent: Generates QB/SAGE/Wave API clients (using templates)
  ├─→ CoderAgent: Generates FastAPI endpoints
  ├─→ FrontendAgent: Generates Next.js UI pages
  ├─→ WorkflowAgent: Generates Temporal workflows
  ├─→ InfrastructureAgent: Generates Terraform + Helm configs
  ├─→ TestingAgent: Generates pytest tests for all code
  ├─→ QAAgent: Runs mypy, ruff, black on generated code
  └─→ SecurityAgent: Runs bandit, safety scans

Step 3: Output - Complete SaaS Application
  📁 my_saas_project/
    ├── api/          (FastAPI backend)
    ├── web/          (Next.js frontend)
    ├── mobile/       (React Native app)
    ├── infra/        (Terraform + Helm)
    ├── tests/        (pytest test suite)
    └── config/       (Environment configs)
```

**Duration**: 2-8 hours (depending on complexity)

**Output**: **Deployable SaaS application** ready for production

---

### **1.4 Deploying the SaaS**

**After agents complete, you must deploy**:

```bash
# Option 1: Local deployment (testing)
cd my_saas_project
docker-compose up -d

# Option 2: Azure deployment (production)
cd my_saas_project/infra/terraform/azure
terraform init
terraform apply

# Option 3: Kubernetes deployment
cd my_saas_project
helm install q2o ./k8s/helm/q2o
```

**Result**: **SaaS application is now RUNNING**

The SaaS includes:
- ✅ FastAPI backend (port 8000)
- ✅ Dashboard API with WebSocket (port 8001)
- ✅ Next.js frontend (port 3000)
- ✅ Database (PostgreSQL)
- ✅ Mobile app backend endpoints

---

### **1.5 Configuration Files for the SaaS**

**The deployed SaaS needs configuration**:

**`.env` file**:
```env
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/q2o

# Stripe (for billing)
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...

# OAuth Credentials (for each platform)
# QuickBooks
QBO_CLIENT_ID=your_qb_client_id
QBO_CLIENT_SECRET=your_qb_client_secret
QBO_REDIRECT_URI=https://yoursaas.com/auth/qbo/callback

# SAGE
SAGE_API_KEY=your_sage_api_key
SAGE_API_SECRET=your_sage_secret

# Wave
WAVE_API_TOKEN=your_wave_token

# Odoo Target
ODOO_URL=https://odoo.clientcompany.com
ODOO_DATABASE=production
ODOO_ADMIN_USER=admin

# Application Settings
API_BASE_URL=https://api.yoursaas.com
FRONTEND_URL=https://app.yoursaas.com
MOBILE_API_URL=https://api.yoursaas.com

# Pricing Configuration
PRICING_CONFIG_PATH=./config/pricing_config.json
```

**These configurations are PREREQUISITES for Phase 2!**

---

## 📋 **PHASE 2: Using the SaaS to Migrate Client Data**

### **2.1 Prerequisites (MUST BE IN PLACE)**

**Before a client can migrate, the following MUST be configured**:

| # | Prerequisite | Set By | Location | Status Required |
|---|--------------|--------|----------|-----------------|
| 1 | **SaaS Deployed** | Developer | Cloud/Server | ✅ Running |
| 2 | **Database Connected** | Developer | .env | ✅ Accessible |
| 3 | **Stripe Configured** | Developer | .env | ✅ Keys valid |
| 4 | **Platform OAuth Apps** | Developer | Each platform | ✅ Registered |
| 5 | **Pricing Config** | Admin | pricing_config.json | ✅ Loaded |
| 6 | **Mapping Configs** | System | config/*.json | ✅ Present |
| 7 | **API Endpoints Live** | System | /api/* | ✅ Responding |
| 8 | **Mobile App Deployed** | Developer | App Store/Play | ✅ Published |

**Only when ALL prerequisites are met can Phase 2 begin.**

---

### **2.2 Complete Client Migration Sequence**

**Now let's clarify the EXACT sequence when a client migrates:**

```
┌────────────────────────────────────────────────────────────────────┐
│  STEP 1: CLIENT DISCOVERS SAAS                                     │
│  - Client visits your website/app store                            │
│  - Downloads mobile app OR accesses web app                        │
│  - Creates account (email + password)                              │
│                                                                     │
│  Prerequisites: ✅ SaaS deployed, ✅ Mobile app published          │
└────────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────────┐
│  STEP 2: CLIENT SELECTS MIGRATION PARAMETERS                       │
│  (Mobile App: New Migration Screen)                                │
│                                                                     │
│  Client selects:                                                   │
│  - Source Platform: "QuickBooks Online"                            │
│  - Years of Data: 5 years                                          │
│  - (Optional) Number of companies: 1                               │
│                                                                     │
│  Prerequisites: ✅ Pricing config loaded                           │
└────────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────────┐
│  STEP 3: SYSTEM CALCULATES PRICING                                 │
│  (API: POST /api/billing/estimate)                                 │
│                                                                     │
│  Backend:                                                          │
│  1. Reads pricing_config.json                                      │
│  2. Determines tier based on years (5 years = Professional)        │
│  3. Gets platform multiplier (QB = 1.0x)                           │
│  4. Estimates records (~50,000 for 5 years)                        │
│  5. Calculates:                                                    │
│     Base: $1,499 (Professional)                                    │
│     Years multiplier: +$600 (40% for 4 extra years)                │
│     Platform: +$0 (QB = 1.0x)                                      │
│     Total: $2,099                                                  │
│                                                                     │
│  Prerequisites: ✅ pricing_config.json exists and loaded           │
└────────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────────┐
│  STEP 4: CLIENT REVIEWS PRICING                                    │
│  (Mobile App: Billing Screen)                                      │
│                                                                     │
│  Display shows:                                                    │
│  - Tier: Professional                                              │
│  - Base Price: $1,499                                              │
│  - Years Multiplier: $600                                          │
│  - Estimated Records: 50,000                                       │
│  - Total: $2,099                                                   │
│                                                                     │
│  Client can:                                                       │
│  - Adjust years (recalculates automatically)                       │
│  - Click "Analyze Actual Data" (connects to QB for exact count)    │
│  - Click "Proceed to Payment"                                      │
│                                                                     │
│  Prerequisites: ✅ Mobile app connected to API                     │
└────────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────────┐
│  STEP 5: (OPTIONAL) ACCURATE DATA VOLUME ANALYSIS                  │
│  (API: POST /api/billing/analyze-volume)                           │
│                                                                     │
│  If client clicks "Analyze Actual Data":                           │
│  1. Client authorizes QuickBooks OAuth                             │
│  2. Backend connects to QuickBooks                                 │
│  3. QBOFullClient.get_all_entities() runs                          │
│  4. Counts ACTUAL records:                                         │
│     - Customers: 512                                               │
│     - Vendors: 198                                                 │
│     - Invoices: 8,234                                              │
│     - Bills: 4,012                                                 │
│     - Total: 28,543 (not 50,000 estimate!)                        │
│  5. Recalculates pricing with actual count                        │
│  6. May adjust price: $2,099 → $1,899 (lower due to fewer records)│
│                                                                     │
│  Prerequisites: ✅ QB OAuth app configured in .env                 │
│                ✅ qbo_client_full.j2 template available            │
└────────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────────┐
│  STEP 6: CLIENT CREATES PAYMENT                                    │
│  (API: POST /api/billing/checkout)                                 │
│                                                                     │
│  Backend:                                                          │
│  1. Creates Stripe Checkout Session                                │
│  2. Stores metadata:                                               │
│     - migration_id: MIG-1730825400                                 │
│     - platform: QuickBooks Online                                  │
│     - years: 5                                                     │
│     - records: 28,543                                              │
│     - tier: professional                                           │
│     - amount: $1,899                                               │
│  3. Returns Stripe checkout URL                                    │
│                                                                     │
│  Mobile App:                                                       │
│  1. Opens Stripe checkout URL in browser                           │
│  2. Client enters payment details                                  │
│  3. Navigates to PaymentStatusScreen                               │
│                                                                     │
│  Prerequisites: ✅ Stripe secret key in .env                       │
│                ✅ Stripe webhook endpoint accessible               │
└────────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────────┐
│  STEP 7: PAYMENT PROCESSING                                        │
│  (Stripe → Client → Stripe → Webhook)                              │
│                                                                     │
│  Stripe:                                                           │
│  1. Processes payment                                              │
│  2. Charges credit card                                            │
│  3. Sends webhook to: POST /api/billing/webhook                    │
│                                                                     │
│  Backend (receives webhook):                                       │
│  1. Verifies signature                                             │
│  2. Extracts event: "checkout.session.completed"                   │
│  3. Gets migration_id from metadata                                │
│  4. Updates database:                                              │
│     - migration_status = "PAID"                                    │
│     - payment_confirmed_at = now()                                 │
│     - stripe_session_id = session_id                               │
│                                                                     │
│  Prerequisites: ✅ Webhook secret configured                       │
│                ✅ Database writable                                │
└────────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────────┐
│  STEP 8: MIGRATION SETUP (Still NOT Migrating Yet!)                │
│  (System prepares migration job)                                   │
│                                                                     │
│  Backend:                                                          │
│  1. Retrieves migration record from database                       │
│  2. Client must now connect their platforms:                       │
│     - QuickBooks: OAuth authorization                              │
│     - Odoo: Provide target URL, credentials                        │
│  3. System validates connections                                   │
│  4. Stores OAuth tokens securely                                   │
│  5. Migration status → "READY"                                     │
│                                                                     │
│  Mobile/Web UI:                                                    │
│  - Shows "Connect QuickBooks" button                               │
│  - Shows "Connect Odoo" button                                     │
│  - Both must be green before migration can start                   │
│                                                                     │
│  Prerequisites: ✅ Client has QB/Odoo credentials                  │
│                ✅ OAuth apps registered                            │
│                ✅ Client authorizes access                         │
└────────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────────┐
│  STEP 9: MIGRATION EXECUTION ("Automatic" Starts Here)             │
│  (Migration Orchestrator runs)                                     │
│                                                                     │
│  This is what "automatic" means:                                   │
│                                                                     │
│  Backend automatically:                                            │
│  1. Initializes QBOFullClient with client's OAuth token            │
│  2. Initializes OdooMigrationClient with client's Odoo credentials │
│  3. Initializes QuickBooksToOdooMapper                             │
│  4. Creates MigrationOrchestrator                                  │
│  5. Calls orchestrator.execute_full_migration()                    │
│                                                                     │
│  Orchestrator executes:                                            │
│  ├─→ Phase 1: Extract ALL QB data (40+ entities)                  │
│  ├─→ Phase 2: Transform to Odoo format (using mappings)           │
│  ├─→ Phase 3: Load into Odoo (creates records)                    │
│  └─→ Phase 4: Validate (counts match, trial balance)              │
│                                                                     │
│  Real-time updates via WebSocket:                                  │
│  - "Extracting customers... 512 found"                             │
│  - "Creating customers in Odoo... 512/512 complete"                │
│  - "Extracting invoices... 8,234 found"                            │
│  - "Creating invoices in Odoo... 8,234/8,234 complete"             │
│  - ...                                                              │
│                                                                     │
│  Prerequisites: ✅ payment_status = "PAID"                         │
│                ✅ qb_oauth_token present                           │
│                ✅ odoo_credentials present                         │
│                ✅ All mapping configs readable                     │
│                ✅ Platform clients initialized                     │
└────────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────────┐
│  STEP 10: MIGRATION MONITORING                                     │
│  (Mobile App: Dashboard)                                           │
│                                                                     │
│  Client sees in real-time:                                         │
│  - Migration progress: 45% complete                                │
│  - Current task: "Migrating invoices (6,234/8,234)"                │
│  - Estimated time remaining: 15 minutes                            │
│  - Entities completed:                                             │
│    ✓ Customers (512)                                               │
│    ✓ Vendors (198)                                                 │
│    ✓ Accounts (156)                                                │
│    ⏳ Invoices (6,234/8,234)                                       │
│    ⏸ Bills (pending)                                               │
│                                                                     │
│  Prerequisites: ✅ WebSocket connection active                     │
│                ✅ Dashboard API running                            │
└────────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────────┐
│  STEP 11: MIGRATION COMPLETION                                     │
│  (System finalizes and validates)                                  │
│                                                                     │
│  Backend:                                                          │
│  1. Validates entity counts match                                  │
│  2. Validates trial balance                                        │
│  3. Generates migration report                                     │
│  4. Sends completion email                                         │
│  5. Updates status → "COMPLETED"                                   │
│                                                                     │
│  Mobile App shows:                                                 │
│  ✓ Migration Complete!                                             │
│  ✓ 28,543 records migrated                                         │
│  ✓ Trial balance: MATCHED                                          │
│  ✓ Download migration report                                       │
│                                                                     │
│  Prerequisites: ✅ All entities migrated                           │
│                ✅ Validation passed                                │
└────────────────────────────────────────────────────────────────────┘
```

---

## 🔄 **Complete End-to-End Timeline**

### **Consultant/Developer Perspective (One-Time Setup)**

```
DAY 1-2: Build SaaS Application (Phase 1)
├─ Hour 1: Define objectives in config.json
├─ Hour 2: Run: python main.py --config config.json
├─ Hour 3-8: Agents generate code (automatic)
├─ Hour 9-12: Review generated code
├─ Hour 13-16: Configure .env (Stripe, OAuth apps)
└─ Hour 17-20: Deploy to Azure/AWS

DAY 3: Test & Configure
├─ Test OAuth flows
├─ Test billing calculations
├─ Test migration with sandbox data
└─ Publish mobile app to stores

RESULT: SaaS is LIVE and ready for clients
```

### **Client Perspective (Per Migration - Repeatable)**

```
MINUTE 1-5: Account Setup
├─ Download mobile app
├─ Create account
└─ Verify email

MINUTE 6-10: Select Migration Options
├─ Select platform: QuickBooks Online
├─ Select years: 5 years
├─ See pricing: $2,099
└─ (Optional) Analyze actual data

MINUTE 11-15: Payment
├─ Click "Proceed to Payment"
├─ Enter payment details in Stripe
├─ Payment processes
└─ Return to app

MINUTE 16: Platform Authorization
├─ Connect QuickBooks (OAuth)
├─ Connect Odoo (provide credentials)
└─ Both connections verified ✅

MINUTE 17-120: Automatic Migration
├─ Backend extracts all QB data (15-30 min)
├─ Backend transforms data (5-10 min)
├─ Backend loads into Odoo (30-60 min)
└─ Backend validates (5-10 min)

MINUTE 121: Completion
├─ Migration complete notification
├─ Download migration report
└─ Start using Odoo!
```

**Total Client Time**: ~2 hours (mostly waiting for automatic processing)

---

## 🎯 **What "Automatic Migration" Actually Means**

### **NOT Automatic Until:**

❌ Client hasn't selected platform  
❌ Client hasn't selected years of data  
❌ Client hasn't paid  
❌ Client hasn't connected QuickBooks OAuth  
❌ Client hasn't provided Odoo credentials  

### **Becomes Automatic After:**

✅ Platform selected: QuickBooks  
✅ Years selected: 5 years  
✅ **Payment confirmed: $2,099 paid**  
✅ QuickBooks OAuth: Connected  
✅ Odoo credentials: Provided  

**THEN** the migration runs **automatically** without further human intervention:
1. Extract (automatic)
2. Transform (automatic)
3. Load (automatic)
4. Validate (automatic)
5. Report (automatic)

---

## 📋 **Configuration Checklist - MUST BE IN PLACE**

### **Backend Configuration Files**

```
config/
├── pricing_config.json              ← MUST EXIST (pricing tiers)
├── quickbooks_to_odoo_mapping.json  ← MUST EXIST (QB entity mappings)
├── sage_to_odoo_mapping.json        ← MUST EXIST (SAGE mappings)
├── wave_to_odoo_mapping.json        ← MUST EXIST (Wave mappings)
└── vcs_config.json.example          ← Optional (VCS integration)
```

### **Environment Variables (.env)**

```env
# ============ PHASE 1 REQUIREMENTS (Build SaaS) ============
# (These are for running the agents to build the SaaS)
# None required - agents run locally

# ============ PHASE 2 REQUIREMENTS (Run SaaS) ============
# (These are for the deployed SaaS to operate)

# Database
DATABASE_URL=postgresql://user:pass@host:5432/db

# Stripe (REQUIRED for billing)
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...

# QuickBooks OAuth (REQUIRED for QB migrations)
QBO_CLIENT_ID=...
QBO_CLIENT_SECRET=...
QBO_REDIRECT_URI=https://yoursaas.com/auth/qbo/callback

# SAGE OAuth (REQUIRED for SAGE migrations)
SAGE_API_KEY=...
SAGE_API_SECRET=...

# Wave (REQUIRED for Wave migrations)
WAVE_API_TOKEN=...

# Application URLs
API_BASE_URL=https://api.yoursaas.com
FRONTEND_URL=https://app.yoursaas.com

# Pricing
PRICING_CONFIG_PATH=./config/pricing_config.json
```

### **Template Files Required**

```
templates/integration/
├── qbo_client_full.j2              ← MUST EXIST
├── odoo_migration_client.j2        ← MUST EXIST
├── qbo_oauth.j2                    ← MUST EXIST
└── [other platform templates]
```

### **Utility Modules Required**

```
utils/
├── migration_pricing.py            ← MUST EXIST
├── platform_mapper.py              ← MUST EXIST
├── migration_orchestrator.py       ← MUST EXIST
└── [other utilities]
```

---

## 🔧 **Making Pricing Configurable**

### **How Pricing is Configured**

**File**: `config/pricing_config.json`

**To Change Prices**:

```json
{
  "tiers": {
    "professional": {
      "base_price": 1499.00,    ← CHANGE THIS
      "years_max": 5,           ← CHANGE THIS
      "records_included": 50000, ← CHANGE THIS
      "price_per_1000_extra_records": 3.00 ← CHANGE THIS
    }
  },
  "platform_multipliers": {
    "QuickBooks Online": 1.0,   ← CHANGE THIS
    "SAGE 200": 1.5             ← CHANGE THIS
  },
  "years_multiplier": {
    "rate_per_year": 0.10       ← CHANGE THIS (10% per year)
  }
}
```

**No code changes needed** - just edit JSON and restart API.

### **Loading Configurable Pricing in Code**

**Updated `utils/migration_pricing.py`** to load from config:

```python
class MigrationPricingEngine:
    def __init__(self, config_path: str = None):
        if config_path is None:
            config_path = os.getenv(
                "PRICING_CONFIG_PATH", 
                "./config/pricing_config.json"
            )
        
        # Load pricing from config file
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        # Use config values instead of hardcoded
        self.BASE_PRICES = {
            tier: data["base_price"]
            for tier, data in self.config["tiers"].items()
        }
```

---

## 📊 **Deployment Architecture - Complete Picture**

```
┌─────────────────────────────────────────────────────────────────────┐
│                    DEVELOPMENT ENVIRONMENT                           │
│  (Where Quick2Odoo agents run to BUILD the SaaS)                    │
│                                                                      │
│  Developer's Laptop:                                                 │
│  ├── Quick2Odoo codebase (this repo)                                │
│  ├── Python 3.10+                                                    │
│  ├── config.json (defines SaaS to build)                             │
│  └── Runs: python main.py --config config.json                      │
│                                                                      │
│  Agents generate code → Output to ./generated_saas/                 │
└─────────────────────────────────────────────────────────────────────┘
                              ↓ (deploy)
┌─────────────────────────────────────────────────────────────────────┐
│                    PRODUCTION ENVIRONMENT                            │
│  (Where the BUILT SaaS runs to serve clients)                       │
│                                                                      │
│  Cloud Server (Azure/AWS):                                           │
│  ├── FastAPI Backend (port 8000)                                     │
│  │   ├── /api/billing/*        ← Pricing & Stripe                   │
│  │   ├── /api/migration/*      ← Migration execution                │
│  │   └── /api/oauth/*          ← Platform OAuth                     │
│  │                                                                   │
│  ├── Dashboard API (port 8001)                                       │
│  │   └── WebSocket for real-time updates                            │
│  │                                                                   │
│  ├── PostgreSQL Database                                             │
│  │   ├── migrations table      ← Tracks migration jobs              │
│  │   ├── users table           ← Client accounts                    │
│  │   └── payments table        ← Stripe payment records             │
│  │                                                                   │
│  ├── Configuration Files:                                            │
│  │   ├── .env                  ← Environment variables              │
│  │   ├── pricing_config.json   ← PRICING CONFIGURATION              │
│  │   ├── quickbooks_to_odoo_mapping.json ← Entity mappings          │
│  │   └── sage_to_odoo_mapping.json       ← Entity mappings          │
│  │                                                                   │
│  └── Template Files:                                                 │
│      ├── qbo_client_full.j2    ← QuickBooks extraction             │
│      └── odoo_migration_client.j2 ← Odoo loading                    │
└─────────────────────────────────────────────────────────────────────┘
                              ↕ (clients connect)
┌─────────────────────────────────────────────────────────────────────┐
│                       CLIENT LAYER                                   │
│                                                                      │
│  ├── Mobile App (iOS/Android)                                        │
│  │   ├── Connects to: https://api.yoursaas.com                      │
│  │   ├── Billing Screen (select platform, years, pay)               │
│  │   └── Dashboard (monitor migration)                              │
│  │                                                                   │
│  └── Web App (Browser)                                               │
│      ├── Connects to: https://app.yoursaas.com                      │
│      └── Same features as mobile                                    │
└─────────────────────────────────────────────────────────────────────┘
```

---

## ⚙️ **Complete Configuration Requirements**

### **For Phase 1 (Building SaaS) - One Time**

| File | Required | Purpose |
|------|----------|---------|
| `config.json` | ✅ YES | Defines what SaaS to build |
| `requirements.txt` | ✅ YES | Python dependencies |
| `main.py` | ✅ YES | Agent orchestrator entry point |

**Command**: `python main.py --config config.json --workspace ./my_saas`

---

### **For Phase 2 (Running SaaS) - Persistent**

| File/Setting | Required | Purpose | Where Set |
|--------------|----------|---------|-----------|
| `.env` | ✅ YES | All secrets & URLs | Production server |
| `pricing_config.json` | ✅ YES | Pricing tiers | `config/` directory |
| `*_to_odoo_mapping.json` | ✅ YES | Entity mappings | `config/` directory |
| **Stripe Account** | ✅ YES | Payment processing | stripe.com |
| **QB OAuth App** | ✅ YES (if supporting QB) | QuickBooks integration | developer.intuit.com |
| **SAGE OAuth App** | ✅ YES (if supporting SAGE) | SAGE integration | developer.sage.com |
| **Database** | ✅ YES | Store migration records | PostgreSQL/MySQL |
| **Deployed Backend** | ✅ YES | API server | Cloud server |
| **Published Mobile App** | ⚠️ OPTIONAL | Mobile access | App Store/Play Store |

---

## 🎯 **Clarified: What "Automatic Migration" Means**

### **BEFORE Payment - Manual Steps Required**

```
Client Actions Required:
1. ✋ Select platform
2. ✋ Select years of data
3. ✋ Review pricing
4. ✋ Enter payment details
5. ✋ Authorize QuickBooks OAuth
6. ✋ Provide Odoo credentials
7. ✋ Click "Start Migration"

System Actions (Not Automatic):
- Calculate pricing (on demand)
- Create checkout session (when requested)
- Wait for payment (manual trigger)
- Wait for OAuth (manual trigger)
```

### **AFTER Payment Confirmed - Fully Automatic**

```
NO Client Actions Required:

System Automatically:
1. ✅ Detects payment confirmation (webhook)
2. ✅ Validates OAuth tokens present
3. ✅ Initializes platform clients
4. ✅ Extracts ALL data from QuickBooks
5. ✅ Transforms using mapping configs
6. ✅ Loads into Odoo
7. ✅ Validates data integrity
8. ✅ Sends completion notification
9. ✅ Updates status to COMPLETED

Client Only Needs To:
- Watch progress in mobile app (optional)
- Receive completion email (automatic)
```

**"Automatic" = No human intervention needed after payment+OAuth authorization**

---

## 📋 **Database Schema Required**

**The SaaS needs a database to track migrations**:

```sql
-- Migrations table
CREATE TABLE migrations (
    id VARCHAR(50) PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL,
    platform_name VARCHAR(100) NOT NULL,
    years_of_data INTEGER NOT NULL,
    total_records INTEGER,
    tier VARCHAR(50),
    amount_paid DECIMAL(10,2),
    
    -- Status tracking
    status VARCHAR(50) DEFAULT 'PENDING',
    -- PENDING → PAID → CONNECTING → READY → RUNNING → COMPLETED/FAILED
    
    payment_status VARCHAR(50),
    stripe_session_id VARCHAR(200),
    payment_confirmed_at TIMESTAMP,
    
    -- Platform connections
    source_oauth_token TEXT,
    source_oauth_expires_at TIMESTAMP,
    target_odoo_url VARCHAR(500),
    target_odoo_database VARCHAR(100),
    target_odoo_credentials TEXT,  -- Encrypted
    
    -- Migration execution
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    entities_migrated JSONB,
    errors JSONB,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Users table
CREATE TABLE users (
    id VARCHAR(50) PRIMARY KEY,
    email VARCHAR(200) UNIQUE NOT NULL,
    company_name VARCHAR(200),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Payments table
CREATE TABLE payments (
    id VARCHAR(50) PRIMARY KEY,
    migration_id VARCHAR(50) REFERENCES migrations(id),
    stripe_session_id VARCHAR(200),
    stripe_payment_intent_id VARCHAR(200),
    amount DECIMAL(10,2),
    currency VARCHAR(3) DEFAULT 'USD',
    status VARCHAR(50),
    paid_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);
```

**This database schema is REQUIRED for Phase 2 to function!**

---

## 🔄 **Updated Migration Status Flow**

```
Migration Lifecycle States:

1. DRAFT
   ↓ (client selects platform + years)
2. PRICED
   ↓ (pricing calculated and shown)
3. PENDING_PAYMENT
   ↓ (client clicks "Proceed to Payment")
4. PAYMENT_PROCESSING
   ↓ (Stripe processes payment)
5. PAID ✅
   ↓ (payment confirmed via webhook)
6. CONNECTING
   ↓ (client authorizes QB OAuth + provides Odoo credentials)
7. READY ✅
   ↓ (both connections verified)
8. RUNNING 🔄
   ↓ (automatic extraction→transformation→loading)
9. VALIDATING
   ↓ (automatic validation checks)
10. COMPLETED ✅
    OR
    FAILED ❌ (with error details)
```

**Key Insight**: Migration only becomes "RUNNING" (automatic) after reaching "READY" state!

---

## 🚀 **Updated SECURE_COMMIT_AND_PUSH.bat**

Now includes the pricing config file. Let me update it:

```batch
git add config/pricing_config.json
```

Let me update the batch file now.

---

## 📚 **Documentation Created for Clarity**

| Document | Purpose | Clarifies |
|----------|---------|-----------|
| `COMPLETE_SYSTEM_WORKFLOW.md` (NEW!) | End-to-end sequence | Phase 1 vs Phase 2, prerequisites, exact steps |
| `BILLING_SYSTEM_ARCHITECTURE.md` | Billing details | Pricing, tiers, Stripe integration |
| `FULL_MIGRATION_ARCHITECTURE.md` | Migration details | How data flows, entity mapping |
| `QUICKBOOKS_FULL_MIGRATION_GUIDE.md` | QB specifics | All 40+ entities, field mappings |

---

**Creating the complete workflow document and updating files now...**

