# Quick2Odoo - Complete File System Structure

**Last Updated**: November 5, 2025  
**Total Files**: 150+ (excluding node_modules, __pycache__, generated files)

---

## 📂 Complete Directory Tree

```
/
│
├── 📁 .github\
│   └── workflows\
│       └── ci.yml                                # GitHub Actions CI/CD pipeline (192 lines)
│                                                 # - Matrix testing (Python 3.10, 3.11, 3.12)
│                                                 # - Linting (ruff, black, mypy, isort)
│                                                 # - Security scanning (bandit, safety)
│                                                 # - Infrastructure validation
│                                                 # - Integration tests
│                                                 # - Coverage reporting (Codecov)
│
├── 📁 agents\                                    # AI Agent System (11 specialized agents)
│   ├── __init__.py                              # Agent module exports (Task, TaskStatus, AgentType)
│   │
│   ├── base_agent.py                            # Base Agent Class (490 lines)
│   │                                            # - Task management (assign, complete, fail)
│   │                                            # - Messaging system integration
│   │                                            # - Retry policy integration
│   │                                            # - Dashboard event emission
│   │                                            # - VCS auto-commit support
│   │                                            # - Health status tracking
│   │
│   ├── orchestrator.py                          # Orchestrator Agent (552 lines)
│   │                                            # - Project breakdown into tasks
│   │                                            # - Domain-aware objective analysis
│   │                                            # - Smart research detection
│   │                                            # - Dependency graph management
│   │                                            # - Load balancer integration
│   │                                            # - Task distribution
│   │                                            # - Retry orchestration
│   │
│   ├── researcher_agent.py                      # Researcher Agent (938 lines)
│   │                                            # - Multi-provider web search (Google, Bing, DDG)
│   │                                            # - 90-day research cache
│   │                                            # - Content scraping (BeautifulSoup)
│   │                                            # - Code example extraction
│   │                                            # - Official documentation detection
│   │                                            # - Confidence scoring
│   │                                            # - Markdown report generation
│   │                                            # - Inter-agent research requests
│   │
│   ├── coder_agent.py                           # Coder Agent
│   │                                            # - FastAPI endpoint generation
│   │                                            # - SQLAlchemy ORM model generation
│   │                                            # - Pydantic schema generation
│   │                                            # - CRUD operation implementation
│   │                                            # - Template-based code generation
│   │
│   ├── integration_agent.py                     # Integration Agent (240 lines)
│   │                                            # - QuickBooks OAuth & API client
│   │                                            # - QuickBooks Desktop WebConnector
│   │                                            # - Odoo v18 JSON-RPC client
│   │                                            # - Stripe billing integration
│   │                                            # - OAuth 2.0 flow implementation
│   │                                            # - Webhook handler generation
│   │
│   ├── frontend_agent.py                        # Frontend Agent
│   │                                            # - Next.js page generation
│   │                                            # - React component creation
│   │                                            # - TypeScript interfaces
│   │                                            # - NextAuth.js setup
│   │                                            # - Responsive layouts
│   │                                            # - Dark mode support
│   │
│   ├── workflow_agent.py                        # Workflow Agent
│   │                                            # - Temporal workflow definitions
│   │                                            # - Activity implementations
│   │                                            # - Worker configuration
│   │                                            # - Backfill workflows
│   │                                            # - Entity sync workflows
│   │
│   ├── testing_agent.py                         # Testing Agent
│   │                                            # - pytest test generation
│   │                                            # - Test execution with pytest-cov
│   │                                            # - Coverage reporting (HTML, XML, JSON)
│   │                                            # - Integration test creation
│   │                                            # - Mock data generation
│   │
│   ├── qa_agent.py                              # QA Agent
│   │                                            # - mypy type checking
│   │                                            # - ruff linting
│   │                                            # - black formatting verification
│   │                                            # - isort import sorting
│   │                                            # - Quality metrics calculation
│   │                                            # - Code review checklist
│   │
│   ├── security_agent.py                        # Security Agent
│   │                                            # - bandit security scanning
│   │                                            # - safety dependency checking
│   │                                            # - Secrets detection
│   │                                            # - semgrep pattern matching
│   │                                            # - Security report generation
│   │
│   ├── infrastructure_agent.py                  # Infrastructure Agent
│   │                                            # - Terraform configuration (Azure)
│   │                                            # - Helm chart generation
│   │                                            # - Kubernetes manifests
│   │                                            # - WAF setup
│   │                                            # - Network security rules
│   │
│   ├── node_agent.py                            # Node.js Agent
│   │                                            # - Express.js application
│   │                                            # - TypeScript configuration
│   │                                            # - npm package.json
│   │                                            # - Middleware setup
│   │                                            # - Route definitions
│   │
│   └── messaging.py                             # Messaging Mixin
│                                                # - Message broker integration
│                                                # - Pub/sub communication
│                                                # - Inter-agent messaging
│                                                # - Research request handling
│
├── 📁 api\                                      # Backend API Layer
│   ├── app\                                     # FastAPI Application
│   │   ├── billing.py                          # Stripe billing integration
│   │   │                                       # - Customer creation
│   │   │                                       # - Subscription management
│   │   │                                       # - Webhook handling
│   │   │
│   │   ├── oauth_qbo.py                        # QuickBooks OAuth
│   │   │                                       # - Authorization URL generation
│   │   │                                       # - Token exchange
│   │   │                                       # - Token refresh
│   │   │                                       # - Secure token storage
│   │   │
│   │   └── clients\                            # External API Clients
│   │       ├── odoo.py                         # Odoo v18 JSON-RPC Client
│   │       │                                   # - Authentication
│   │       │                                   # - CRUD operations
│   │       │                                   # - Search/read/create/write/unlink
│   │       │                                   # - Batch operations
│   │       │
│   │       └── qbo.py                          # QuickBooks Online Client
│   │                                           # - Customer CRUD
│   │                                           # - Invoice CRUD
│   │                                           # - Payment processing
│   │                                           # - Error handling
│   │
│   └── dashboard\                              # Real-time Dashboard API
│       ├── __init__.py                         # Dashboard module initialization
│       │
│       ├── main.py                             # FastAPI + WebSocket Server (161 lines)
│       │                                       # - WebSocket endpoint (/ws/dashboard)
│       │                                       # - REST API endpoints
│       │                                       # - CORS middleware
│       │                                       # - Real-time event broadcasting
│       │
│       ├── events.py                           # Event Manager (178 lines)
│       │                                       # - WebSocket connection management
│       │                                       # - Event broadcasting
│       │                                       # - Task state tracking
│       │                                       # - Agent state tracking
│       │                                       # - System metrics aggregation
│       │                                       # - Event history (last 1000 events)
│       │
│       ├── metrics.py                          # Metrics Calculator
│       │                                       # - Security metrics
│       │                                       # - Quality metrics
│       │                                       # - Performance metrics
│       │                                       # - Aggregated statistics
│       │
│       └── models.py                           # Pydantic Models
│                                               # - DashboardStateModel
│                                               # - SystemMetricsModel
│                                               # - TaskModel
│                                               # - AgentModel
│
├── 📁 mobile\                                   # React Native Mobile App
│   ├── App.tsx                                 # Main Application Component
│   │                                           # - Theme provider
│   │                                           # - Dashboard context provider
│   │                                           # - Navigation setup
│   │
│   ├── package.json                            # npm Dependencies (54 lines)
│   │                                           # - React Native 0.72.6
│   │                                           # - Navigation libraries
│   │                                           # - Socket.IO client
│   │                                           # - Material Design (Paper)
│   │                                           # - Charts & icons
│   │
│   ├── index.js                                # App Entry Point
│   ├── app.json                                # App Configuration
│   ├── babel.config.js                         # Babel Configuration
│   ├── tsconfig.json                           # TypeScript Configuration
│   │
│   ├── 📁 src\
│   │   ├── 📁 components\                      # Reusable UI Components
│   │   │   ├── ConnectionStatus.tsx           # WebSocket connection indicator
│   │   │   ├── TaskCard.tsx                   # Task display card
│   │   │   └── AgentActivityFeed.tsx          # Real-time activity feed
│   │   │
│   │   ├── 📁 screens\                         # Application Screens
│   │   │   ├── DashboardScreen.tsx            # Main Dashboard (Real-time monitoring)
│   │   │   │                                  # - Project status
│   │   │   │                                  # - Task statistics
│   │   │   │                                  # - Recent tasks
│   │   │   │                                  # - Agent activity
│   │   │   │
│   │   │   ├── NewProjectScreen.tsx           # Project Initiation
│   │   │   │                                  # - Platform selection (8+ platforms)
│   │   │   │                                  # - Objective input
│   │   │   │                                  # - Form validation
│   │   │   │                                  # - Example projects
│   │   │   │
│   │   │   ├── MetricsScreen.tsx              # System Analytics
│   │   │   │                                  # - CPU & memory usage
│   │   │   │                                  # - Agent statistics
│   │   │   │                                  # - Task completion rates
│   │   │   │                                  # - Historical charts
│   │   │   │
│   │   │   ├── SettingsScreen.tsx             # Configuration
│   │   │   │                                  # - Server URL setup
│   │   │   │                                  # - Connection management
│   │   │   │                                  # - Theme selection (Light/Dark/Auto)
│   │   │   │                                  # - App info
│   │   │   │
│   │   │   └── ProjectDetailsScreen.tsx       # Project Detail View
│   │   │                                      # - Full project info
│   │   │                                      # - All objectives
│   │   │                                      # - Task list
│   │   │                                      # - Timeline
│   │   │
│   │   ├── 📁 services\                        # Backend Communication
│   │   │   ├── DashboardWebSocket.ts          # WebSocket Client
│   │   │   │                                  # - Socket.IO connection
│   │   │   │                                  # - Event listeners
│   │   │   │                                  # - Auto-reconnect
│   │   │   │
│   │   │   ├── ApiService.ts                  # REST API Client
│   │   │   │                                  # - Axios HTTP client
│   │   │   │                                  # - API endpoints
│   │   │   │                                  # - Error handling
│   │   │   │
│   │   │   ├── DashboardContext.tsx           # State Management
│   │   │   │                                  # - Global state
│   │   │   │                                  # - Real-time updates
│   │   │   │                                  # - Context provider
│   │   │   │
│   │   │   └── ThemeContext.tsx               # Theme Management
│   │   │                                      # - Light/Dark/Auto themes
│   │   │                                      # - AsyncStorage persistence
│   │   │                                      # - System theme detection
│   │   │
│   │   ├── 📁 navigation\
│   │   │   └── MainNavigator.tsx              # App Navigation
│   │   │                                      # - Bottom Tabs (phone)
│   │   │                                      # - Drawer (tablet)
│   │   │                                      # - Responsive switching
│   │   │
│   │   └── 📁 utils\                           # Utility Functions
│   │       ├── theme.ts                       # Theme Definitions
│   │       │                                  # - Light theme colors
│   │       │                                  # - Dark theme colors
│   │       │                                  # - Material Design 3 palette
│   │       │
│   │       ├── responsive.ts                  # Responsive Breakpoints
│   │       │                                  # - Phone: <768px
│   │       │                                  # - Tablet: 768-1024px
│   │       │                                  # - Large tablet: >1024px
│   │       │
│   │       ├── ResponsiveLayout.ts            # Layout Adapter
│   │       │                                  # - Grid columns (1/2/3)
│   │       │                                  # - Spacing multipliers
│   │       │                                  # - Font scaling
│   │       │
│   │       └── ThemeManager.ts                # Theme Persistence
│   │                                          # - Load from AsyncStorage
│   │                                          # - Save theme preference
│   │                                          # - System theme listener
│   │
│   ├── 📁 android\                             # Android Native Code
│   └── 📁 ios\                                 # iOS Native Code
│
├── 📁 utils\                                    # Utility Modules (14 files)
│   ├── __init__.py                             # Utility exports
│   │
│   ├── project_layout.py                       # Project Structure (156 lines)
│   │                                           # - Configurable directory layout
│   │                                           # - Path resolution
│   │                                           # - Layout from config file
│   │                                           # - Default layout
│   │
│   ├── load_balancer.py                        # High Availability (421 lines)
│   │                                           # - Agent pool management
│   │                                           # - Task routing algorithms
│   │                                           #   * Round-robin
│   │                                           #   * Least-busy
│   │                                           #   * Health-based
│   │                                           # - Circuit breakers
│   │                                           # - Health monitoring
│   │                                           # - Failover automation
│   │                                           # - Metrics & analytics
│   │
│   ├── message_broker.py                       # Messaging System
│   │                                           # - Redis pub/sub integration
│   │                                           # - In-memory fallback
│   │                                           # - Channel management
│   │                                           # - Message serialization
│   │
│   ├── message_protocol.py                     # Message Protocol
│   │                                           # - Message types enum
│   │                                           # - Message formatting
│   │                                           # - Payload validation
│   │
│   ├── retry_policy.py                         # Retry Strategies
│   │                                           # - Exponential backoff
│   │                                           # - Fixed delay
│   │                                           # - Linear backoff
│   │                                           # - Agent-specific policies
│   │                                           # - Max retries configuration
│   │
│   ├── retry.py                                # Retry Decorators
│   │                                           # - @retry decorator
│   │                                           # - Async retry support
│   │
│   ├── git_manager.py                          # Git Operations
│   │                                           # - Auto-commit on task completion
│   │                                           # - Branch creation
│   │                                           # - Commit message generation
│   │                                           # - Git status checking
│   │
│   ├── vcs_integration.py                      # GitHub Integration
│   │                                           # - Pull request creation
│   │                                           # - Branch management
│   │                                           # - PR description generation
│   │                                           # - GitHub API client
│   │
│   ├── template_renderer.py                    # Jinja2 Engine
│   │                                           # - Template loading
│   │                                           # - Variable substitution
│   │                                           # - Filter functions
│   │                                           # - Template caching
│   │
│   ├── language_detector.py                    # Language Detection
│   │                                           # - File extension mapping
│   │                                           # - Shebang detection
│   │                                           # - Content-based detection
│   │
│   ├── code_quality_scanner.py                 # Quality Analysis
│   │                                           # - Complexity calculation
│   │                                           # - Lint issue counting
│   │                                           # - Type coverage analysis
│   │
│   ├── security_scanner.py                     # Security Analysis
│   │                                           # - Vulnerability detection
│   │                                           # - CVE database lookup
│   │                                           # - Risk scoring
│   │
│   ├── secrets_validator.py                    # Secret Detection
│   │                                           # - Regex pattern matching
│   │                                           # - API key detection
│   │                                           # - Password detection
│   │
│   └── infrastructure_validator.py             # IaC Validation
│                                               # - Terraform syntax check
│                                               # - Terraform plan validation
│                                               # - Helm chart linting
│
├── 📁 templates\                                # Code Generation Templates (14+ templates)
│   ├── 📁 api\
│   │   ├── fastapi_endpoint.j2                 # FastAPI Route Template
│   │   │                                       # - CRUD endpoints
│   │   │                                       # - Pydantic schemas
│   │   │                                       # - Error handling
│   │   │
│   │   └── sqlalchemy_model.j2                 # SQLAlchemy Model
│   │                                           # - ORM model definition
│   │                                           # - Relationships
│   │                                           # - Constraints
│   │
│   ├── 📁 integration\
│   │   ├── qbo_oauth.j2                        # QuickBooks OAuth Flow
│   │   ├── qbo_client.j2                       # QuickBooks API Client
│   │   ├── odoo_client.j2                      # Odoo JSON-RPC Client
│   │   ├── qbd_webconnector.j2                 # QuickBooks Desktop WebConnector
│   │   └── stripe_billing.j2                   # Stripe Integration
│   │
│   ├── 📁 frontend_agent\
│   │   ├── onboarding_page.tsx.j2              # Next.js Onboarding Wizard
│   │   ├── mappings_page.tsx.j2                # Field Mapping UI
│   │   ├── jobs_page.tsx.j2                    # Migration Job Tracker
│   │   ├── errors_page.tsx.j2                  # Error Dashboard
│   │   ├── theme_toggle.tsx.j2                 # Dark Mode Toggle
│   │   └── nextauth_config.ts.j2               # NextAuth.js Config
│   │
│   ├── 📁 infrastructure\
│   │   ├── terraform_main.j2                   # Terraform Main Config
│   │   ├── terraform_variables.j2              # Terraform Variables
│   │   ├── terraform_waf.j2                    # Azure WAF Setup
│   │   ├── helm_chart.j2                       # Kubernetes Helm Chart
│   │   └── helm_values.j2                      # Helm Values
│   │
│   ├── 📁 workflow_agent\
│   │   ├── backfill_workflow.py.j2             # Temporal Backfill Workflow
│   │   ├── entity_activities.py.j2             # Temporal Activities
│   │   └── worker_main.py.j2                   # Temporal Worker
│   │
│   ├── 📁 nodejs\
│   │   ├── express_app.j2                      # Express.js App
│   │   └── package_json.j2                     # npm package.json
│   │
│   └── 📁 test\
│       └── pytest_test.j2                      # pytest Test Template
│
├── 📁 infra\                                    # Infrastructure as Code
│   └── terraform\
│       └── azure\
│           ├── main.tf                         # Azure Resources
│           ├── variables.tf                    # Configuration Variables
│           └── waf.tf                          # Web Application Firewall
│
├── 📁 shared\                                   # Shared Code
│   └── temporal_defs\
│       └── workflows\
│           └── backfill.py                     # Example Temporal Workflow
│
├── 📁 tests\                                    # Test Suite (10+ test files)
│   ├── test_oauth_authentication.py            # OAuth flow testing
│   ├── test_odoo_v18_integration.py            # Odoo integration testing
│   ├── test_quickbooks_oauth_authentication.py # QuickBooks OAuth testing
│   ├── test_researcher_agent.py                # Researcher agent testing
│   ├── test_stripe_billing_setup.py            # Stripe integration testing
│   ├── test_temporal_backfill_workflow.py      # Temporal workflow testing
│   ├── test_next.js_frontend.py                # Frontend generation testing
│   ├── test_onboarding_wizard_ui.py            # UI generation testing
│   └── test_odoo_v18_json-rpc_client.py       # Odoo client testing
│
├── 📁 tools\                                    # Development Tools
│   ├── generate_env_example.py                 # .env.example Generator
│   ├── migrate_templates_interactive.py        # Template Migration Tool
│   ├── quick_start.py                          # Quick Project Starter
│   ├── validate_migration.py                   # Migration Validator
│   └── restore_backup.ps1                      # Backup Restoration
│
├── 📁 docs\                                     # Documentation (64+ files)
│   ├── Quick2Odoo_Agentic_Scaffold_Document.html   # Complete HTML Guide
│   ├── AGENT_SYSTEM_RECOMMENDATIONS.md         # Agent System Best Practices
│   ├── COMPREHENSIVE_PROJECT_ASSESSMENT.md     # This Assessment Report
│   ├── FILE_SYSTEM_STRUCTURE.md                # This File
│   │
│   └── md_docs\                                # Detailed Documentation (62 files)
│       ├── README_AGENTS.md                    # Agent System Overview
│       ├── RESEARCHER_AGENT_GUIDE.md           # Research Agent Documentation
│       ├── TESTING_GUIDE.md                    # Testing Instructions
│       ├── USAGE_GUIDE.md                      # Usage Guide
│       ├── DEPLOYMENT_CHECKLIST.md             # Production Deployment
│       ├── VCS_INTEGRATION_GUIDE.md            # Git/GitHub Automation
│       ├── CI_CD_ANALYSIS.md                   # CI/CD Pipeline Analysis
│       ├── MOBILE_APP_SUMMARY.md               # Mobile App Summary
│       ├── FEATURE_ROADMAP.md                  # Feature Roadmap
│       ├── IMPLEMENTATION_COMPLETE.md          # Implementation Status
│       └── [52+ more documentation files]
│
├── 📁 web\                                      # Web Dashboard (Next.js)
│   └── dashboard\
│       └── pages\
│           └── index.tsx                       # Dashboard Home Page
│
├── 📁 config\                                   # Configuration
│   └── vcs_config.json.example                 # VCS Configuration Template
│
├── 📄 main.py                                   # Main Entry Point (568 lines)
│                                               # - CLI argument parsing
│                                               # - AgentSystem initialization
│                                               # - Project execution
│                                               # - Results output
│
├── 📄 requirements.txt                          # Python Dependencies (67 lines)
│                                               # - FastAPI, SQLAlchemy, Pydantic
│                                               # - Temporal, pytest, coverage
│                                               # - Security tools (bandit, safety)
│                                               # - Quality tools (ruff, black, mypy)
│                                               # - Research tools (DuckDuckGo, BeautifulSoup)
│
├── 📄 README.md                                 # Project README (201 lines)
│                                               # - Quick start guide
│                                               # - Feature overview
│                                               # - Architecture summary
│                                               # - Multi-platform support
│                                               # - Documentation links
│
├── 📄 config_example.json                       # Example Configuration
│                                               # - project_description
│                                               # - platforms (QuickBooks, SAGE, etc.)
│                                               # - objectives
│
├── 📄 test_agent_system.py                      # Integration Test Runner
│
├── 📄 .gitignore                                # Git Ignore Rules
│                                               # - Python artifacts
│                                               # - Node modules
│                                               # - Secrets & tokens
│                                               # - Temporary files
│
└── 📄 QuickOdoo.code-workspace                  # VS Code Workspace Config

```

---

## 📊 Statistics

### **Code Distribution**

| Category | Files | Approx Lines | Percentage |
|----------|-------|--------------|------------|
| **Agents** | 13 | ~3,500 | 25% |
| **Utilities** | 14 | ~2,000 | 15% |
| **API/Dashboard** | 7 | ~1,000 | 7% |
| **Mobile App** | 20+ | ~3,000 | 22% |
| **Templates** | 14+ | ~1,500 | 11% |
| **Tests** | 10+ | ~1,000 | 7% |
| **Documentation** | 64+ | ~1,800 | 13% |
| **Total** | **142+** | **~13,800** | **100%** |

### **Language Distribution**

| Language | Files | Approx Lines | Primary Use |
|----------|-------|--------------|-------------|
| **Python** | 45+ | ~9,000 | Agents, utilities, API |
| **TypeScript/JavaScript** | 25+ | ~3,000 | Mobile app, templates |
| **Jinja2** | 14+ | ~1,500 | Code templates |
| **Markdown** | 64+ | ~1,800 | Documentation |
| **Terraform (HCL)** | 3 | ~300 | Infrastructure |
| **YAML** | 1 | ~200 | CI/CD |

### **Directory Depth**

- **Maximum Depth**: 5 levels (e.g., `mobile/src/components/...`)
- **Average Depth**: 3 levels
- **Root-level Directories**: 14

### **Key Directories by Function**

| Directory | Purpose | Critical Files |
|-----------|---------|----------------|
| `agents/` | AI agent implementations | 11 agent files |
| `utils/` | Shared utilities | Load balancer, retry policies |
| `api/dashboard/` | Real-time monitoring | WebSocket server, events |
| `mobile/src/` | Mobile app source | Screens, services, components |
| `templates/` | Code generation | 14+ Jinja2 templates |
| `tests/` | Test suites | 10+ pytest files |
| `docs/` | Documentation | 64+ markdown files |

---

## 🔗 Critical File Relationships

### **Dependency Map**

```
main.py
  ├──> agents/__init__.py
  │     ├──> agents/orchestrator.py
  │     │     └──> agents/base_agent.py
  │     ├──> agents/researcher_agent.py
  │     ├──> agents/coder_agent.py
  │     ├──> agents/integration_agent.py
  │     ├──> agents/frontend_agent.py
  │     ├──> agents/workflow_agent.py
  │     ├──> agents/testing_agent.py
  │     ├──> agents/qa_agent.py
  │     ├──> agents/security_agent.py
  │     ├──> agents/infrastructure_agent.py
  │     └──> agents/node_agent.py
  │
  ├──> utils/load_balancer.py
  ├──> utils/project_layout.py
  ├──> utils/retry_policy.py
  ├──> utils/message_broker.py
  └──> api/dashboard/events.py
```

### **Template Usage Flow**

```
Agent (e.g., integration_agent.py)
  └──> utils/template_renderer.py
        └──> templates/integration/qbo_oauth.j2
              └──> Generated: api/app/oauth_qbo.py
```

### **Mobile App Architecture**

```
App.tsx
  ├──> src/navigation/MainNavigator.tsx
  │     ├──> src/screens/DashboardScreen.tsx
  │     ├──> src/screens/NewProjectScreen.tsx
  │     ├──> src/screens/MetricsScreen.tsx
  │     └──> src/screens/SettingsScreen.tsx
  │
  ├──> src/services/DashboardContext.tsx
  │     ├──> src/services/DashboardWebSocket.ts
  │     └──> src/services/ApiService.ts
  │
  └──> src/services/ThemeContext.tsx
        └──> src/utils/theme.ts
```

---

## 📁 Environment-Specific Files

### **Development**
- `config_example.json` - Example configuration
- `test_*.py` - Test files
- `.gitignore` - Git ignore rules
- `QuickOdoo.code-workspace` - VS Code workspace

### **Production**
- `.github/workflows/ci.yml` - CI/CD pipeline
- `infra/terraform/` - Infrastructure code
- `requirements.txt` - Production dependencies
- `api/dashboard/` - Production dashboard

### **Mobile Development**
- `mobile/package.json` - npm dependencies
- `mobile/android/` - Android build
- `mobile/ios/` - iOS build

---

**Last Updated**: November 5, 2025  
**Maintained By**: QuickOdoo Development Team


