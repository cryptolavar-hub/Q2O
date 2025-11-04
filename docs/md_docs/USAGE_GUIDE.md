# QuickOdoo Multi-Agent System - Usage Guide
**Comprehensive Guide for Developers**

---

## 🚀 **Quick Start (5 Minutes)**

### **1. Install**
```bash
git clone https://github.com/cryptolavar-hub/Q2O.git
cd Q2O
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### **2. Configure**
```bash
cp .env.example .env
# Edit .env with your API keys
```

### **3. Run**
```bash
python main.py --project "My Project" --objective "Create API" --workspace ./output
```

That's it! The system will generate your code automatically.

---

## 📚 **Table of Contents**

1. [Basic Usage](#basic-usage)
2. [Command Line Interface](#command-line-interface)
3. [Configuration Files](#configuration-files)
4. [Working with Agents](#working-with-agents)
5. [Templates & Customization](#templates--customization)
6. [Environment Variables](#environment-variables)
7. [Advanced Features](#advanced-features)
8. [Examples & Recipes](#examples--recipes)
9. [Troubleshooting](#troubleshooting)

---

## 📖 **Basic Usage**

### **Running with Command Line Arguments**

```bash
# Single objective
python main.py \
  --project "Multi-Platform Odoo Migration" \
  --objective "OAuth authentication" \
  --workspace ./my_project

# Multiple objectives
python main.py \
  --project "Full Stack App" \
  --objective "API endpoints" \
  --objective "Frontend UI" \
  --objective "Database models" \
  --workspace ./full_app
```

### **Running with Configuration File**

Create `config.json`:
```json
{
  "project_description": "Multi-Platform to Odoo Migration",
  "platforms": ["QuickBooks", "SAGE", "Wave"],
  "objectives": [
    "OAuth authentication for multiple platforms",
    "Odoo v18 integration",
    "Data synchronization workflow",
    "Next.js frontend dashboard"
  ]
}
```

Run:
```bash
python main.py --config config.json --workspace ./my_project
```

### **Logging Levels**

```bash
# Default (INFO)
python main.py --config config.json

# Debug mode
python main.py --config config.json --log-level DEBUG

# Quiet mode
python main.py --config config.json --log-level WARNING
```

---

## 💻 **Command Line Interface**

### **All Available Options**

```bash
python main.py [OPTIONS]

Options:
  --project TEXT         Project description
  --objective TEXT       Project objective (can use multiple times)
  --config TEXT          Path to JSON config file
  --workspace TEXT       Workspace directory (default: current directory)
  --log-level TEXT       Logging level: DEBUG, INFO, WARNING, ERROR
  --output TEXT          Path to save results JSON file

Examples:
  python main.py --project "API" --objective "User auth" --objective "CRUD"
  python main.py --config myconfig.json --workspace ./output
  python main.py --help
```

### **Output Options**

```bash
# Save results to JSON
python main.py --config config.json --output results.json

# Results include:
# - Tasks created and status
# - Files generated
# - Agent performance
# - QA scores
# - Security findings
```

---

## ⚙️ **Configuration Files**

### **Basic Configuration**

```json
{
  "project_description": "My Project",
  "objectives": [
    "Feature 1",
    "Feature 2"
  ]
}
```

### **Advanced Configuration with Project Layout**

Create `project_layout.json`:
```json
{
  "project_layout": {
    "api_app_dir": "backend/api",
    "web_pages_dir": "frontend/pages",
    "web_components_dir": "frontend/components",
    "tests_dir": "tests",
    "workflows_dir": "workflows",
    "worker_dir": "workers"
  }
}
```

Place in workspace root. System will auto-detect and use it.

### **Example Configurations**

#### **QuickBooks OAuth Only**
```json
{
  "project_description": "QuickBooks Authentication",
  "objectives": [
    "OAuth authentication with QuickBooks"
  ]
}
```

#### **Full Stack Application**
```json
{
  "project_description": "Complete SaaS Platform",
  "objectives": [
    "FastAPI backend with authentication",
    "Next.js frontend with dashboard",
    "PostgreSQL database integration",
    "Stripe billing setup",
    "Temporal workflows for background jobs",
    "Terraform infrastructure for Azure",
    "Kubernetes deployment with Helm"
  ]
}
```

#### **Microservices Architecture**
```json
{
  "project_description": "Microservices Platform",
  "objectives": [
    "User service with authentication",
    "Payment service with Stripe",
    "Notification service",
    "API Gateway with rate limiting",
    "Service mesh configuration"
  ]
}
```

---

## 🤖 **Working with Agents**

### **Available Agents**

| Agent | Purpose | Technologies |
|-------|---------|--------------|
| **OrchestratorAgent** | Task planning & distribution | N/A |
| **CoderAgent** | Backend code generation | FastAPI, SQLAlchemy, Python |
| **TestingAgent** | Test generation & execution | pytest, pytest-cov |
| **QAAgent** | Code quality review | mypy, ruff, black |
| **SecurityAgent** | Security scanning | bandit, semgrep |
| **InfrastructureAgent** | Infrastructure as code | Terraform, Helm |
| **IntegrationAgent** | API integrations | OAuth, REST, JSON-RPC |
| **FrontendAgent** | Frontend code generation | Next.js, React, TypeScript |
| **WorkflowAgent** | Background workflows | Temporal |
| **NodeAgent** | Node.js applications | Express.js, Node.js 20.x |

### **How Agents Work**

1. **Orchestrator** breaks project into tasks
2. **Load Balancer** routes tasks to available agents
3. **Agents** generate code using templates
4. **Testing Agent** creates and runs tests
5. **QA Agent** reviews code quality
6. **Security Agent** scans for vulnerabilities

### **Agent Redundancy**

- Each agent type has 2 instances (primary + backup)
- Automatic failover if primary fails
- Health checks every 60 seconds
- Circuit breaker prevents cascading failures

---

## 🎨 **Templates & Customization**

### **Template Locations**

```
templates/
├── api/                   # FastAPI templates
│   ├── fastapi_endpoint.j2
│   └── sqlalchemy_model.j2
├── test/                  # Test templates
│   └── pytest_test.j2
├── infrastructure/        # Terraform/Helm templates
│   ├── terraform_main.j2
│   └── helm_chart.j2
├── integration/           # OAuth/API client templates
│   ├── qbo_oauth.j2
│   └── odoo_client.j2
├── frontend_agent/        # Next.js templates
│   ├── onboarding_page.tsx.j2
│   └── mappings_page.tsx.j2
└── workflow_agent/        # Temporal templates
    └── backfill_workflow.py.j2
```

### **Customizing Templates**

Templates use Jinja2 syntax. Example:

```jinja2
"""
{{ description }}
Generated by {{ agent_name }}
"""

from fastapi import APIRouter, HTTPException
from typing import List

router = APIRouter()

@router.get("/{{ endpoint_name }}")
async def {{ function_name }}():
    """{{ docstring }}"""
    return {"status": "success"}
```

### **Using Custom Templates**

1. Copy template to your workspace `templates/` directory
2. Modify as needed
3. System will use your custom template automatically

### **Template Variables**

Common variables available in templates:
- `{{ project_name }}` - Project name
- `{{ description }}` - Task description
- `{{ agent_name }}` - Generating agent
- `{{ timestamp }}` - Generation timestamp

---

## 🔐 **Environment Variables**

### **Required Variables**

#### **Platform Integrations**

**QuickBooks:**
```bash
QBO_CLIENT_ID=your_client_id
QBO_CLIENT_SECRET=your_client_secret
QBO_REDIRECT_URI=http://localhost:5000/auth/qbo/callback
QBO_SCOPE=com.intuit.quickbooks.accounting
```

#### **Odoo Integration**
```bash
ODOO_URL=https://your-odoo-instance.com
ODOO_DB=database_name
ODOO_USERNAME=admin
ODOO_PASSWORD=your_password
# or
ODOO_API_KEY=your_api_key
```

#### **Stripe Billing**
```bash
STRIPE_SECRET=sk_test_...
STRIPE_PUBLIC_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

#### **Temporal Workflows**
```bash
TEMPORAL_ADDRESS=localhost:7233
TEMPORAL_NAMESPACE=default
TEMPORAL_TASK_QUEUE=q2o-sync
```

### **Optional Variables**

```bash
# VCS Integration
VCS_ENABLED=true
GITHUB_TOKEN=ghp_...
GITHUB_REPO=owner/repo

# Dashboard
NEXT_PUBLIC_DASHBOARD_WS_URL=ws://localhost:8000/ws

# Billing URLs
BILLING_SUCCESS_URL=https://app.example.com/success
BILLING_CANCEL_URL=https://app.example.com/cancel
```

### **Generating .env.example**

```bash
# Scan your project
python tools/generate_env_example.py --directory ./my_project

# Check for hardcoded secrets
python tools/generate_env_example.py --check-secrets

# Output to custom file
python tools/generate_env_example.py --output .env.production
```

---

## 🚀 **Advanced Features**

### **1. VCS Auto-Commit**

Enable automatic Git commits:

```bash
export VCS_ENABLED=true
export GITHUB_TOKEN=your_token
export GITHUB_REPO=owner/repo

python main.py --config config.json
```

Features:
- Auto-commit after each task
- Feature branch creation
- Automatic PR creation
- Meaningful commit messages

See `VCS_INTEGRATION_GUIDE.md` for details.

### **2. Real-time Dashboard**

Start the dashboard:

```bash
# Start FastAPI dashboard server
python -m uvicorn api.dashboard.main:app --reload

# Access at: http://localhost:8000
# WebSocket: ws://localhost:8000/ws
```

Features:
- Live task monitoring
- Agent activity feed
- Performance metrics
- Real-time logs

### **3. Load Balancing Algorithms**

Configure in code (or future config file):

```python
# Round-robin (default)
load_balancer.set_algorithm('round_robin')

# Least busy
load_balancer.set_algorithm('least_busy')

# Priority-based
load_balancer.set_algorithm('priority')
```

### **4. Retry Policies**

Built-in retry with exponential backoff:

```python
# Per-agent retry configuration
IntegrationAgent: 5 retries, exponential backoff
TestingAgent: 2 retries, exponential backoff
SecurityAgent: 3 retries, exponential backoff
QAAgent: 3 retries, exponential backoff
```

Automatic - no configuration needed!

### **5. Test Coverage Reporting**

Automatic coverage reports generated in `.coverage_reports/`:

```bash
# View HTML coverage report
open .coverage_reports/htmlcov/index.html

# JSON coverage data
cat .coverage_reports/coverage.json
```

---

## 📖 **Examples & Recipes**

### **Example 1: QuickBooks OAuth**

```bash
python main.py \
  --project "Multi-Platform Odoo Migration" \
  --objective "OAuth authentication for QuickBooks and SAGE" \
  --workspace ./migration_project
```

**Generated Files**:
- `api/app/oauth_qbo.py` - OAuth handler
- `api/app/clients/qbo.py` - QBO API client
- `tests/test_quickbooks_oauth.py` - Tests

### **Example 2: Full Stack SaaS**

```json
{
  "project_description": "Quick2Odoo SaaS Platform",
  "objectives": [
    "QuickBooks OAuth authentication",
    "Odoo v18 integration",
    "Stripe billing setup",
    "Next.js frontend with dashboard",
    "Temporal backfill workflow",
    "Terraform Azure infrastructure"
  ]
}
```

```bash
python main.py --config full_saas.json --workspace ./saas_platform
```

**Generated Structure**:
```
saas_platform/
├── api/
│   └── app/
│       ├── oauth_qbo.py
│       ├── billing.py
│       └── clients/
│           ├── qbo.py
│           └── odoo.py
├── web/
│   ├── pages/
│   │   ├── onboarding.tsx
│   │   └── mappings.tsx
│   └── components/
│       └── ThemeToggle.tsx
├── infra/
│   └── terraform/
│       └── azure/
│           ├── main.tf
│           └── waf.tf
├── shared/
│   └── temporal_defs/
│       └── workflows/
│           └── backfill.py
└── tests/
    ├── test_oauth.py
    └── test_odoo.py
```

### **Example 3: Node.js Microservice**

```bash
python main.py \
  --project "User Service" \
  --objective "Express.js REST API with authentication" \
  --workspace ./user_service
```

**Generated Files**:
- `server.js` - Express application
- `package.json` - Dependencies
- `routes/auth.js` - Auth routes

### **Example 4: Infrastructure Only**

```bash
python main.py \
  --project "Cloud Infrastructure" \
  --objective "Terraform setup for Azure with WAF" \
  --objective "Kubernetes Helm charts" \
  --workspace ./infrastructure
```

**Generated Files**:
- `infra/terraform/azure/main.tf`
- `infra/terraform/azure/waf.tf`
- `k8s/helm/q2o/Chart.yaml`
- `k8s/helm/q2o/values.yaml`

---

## 🐛 **Troubleshooting**

### **Common Issues**

#### **Issue: ModuleNotFoundError**

```bash
# Solution: Install dependencies
pip install -r requirements.txt

# Verify installation
pip list | grep fastapi
```

#### **Issue: Templates not found**

```bash
# Verify templates directory exists
ls templates/

# Check current directory
pwd

# Should be in project root
```

#### **Issue: Environment variables not loaded**

```bash
# Check .env file
cat .env

# Load manually
python -c "from dotenv import load_dotenv; load_dotenv(); import os; print(os.getenv('QBO_CLIENT_ID'))"
```

#### **Issue: Tests failing**

```bash
# Check pytest installed
pip list | grep pytest

# Install if missing
pip install pytest pytest-cov

# Run tests manually
pytest tests/ -v
```

#### **Issue: Permission denied (Windows)**

```bash
# Run PowerShell as Administrator
# Or use WSL (Windows Subsystem for Linux)
```

### **Debug Mode**

```bash
# Enable debug logging
python main.py --config config.json --log-level DEBUG

# This will show:
# - Detailed agent actions
# - Template rendering
# - Task routing decisions
# - Load balancer activity
```

### **Getting Help**

1. Check documentation: `docs/Quick2Odoo_Agentic_Scaffold_Document.html`
2. See `TESTING_GUIDE.md`
3. See `README.md`
4. GitHub Issues: https://github.com/cryptolavar-hub/Q2O/issues

---

## 🎓 **Best Practices**

### **1. Start Small**

```bash
# Start with simple test
python main.py --project "Test" --objective "Simple API" --workspace ./test

# Verify it works
cd test && ls -la
```

### **2. Use Configuration Files**

Better than long command lines:
```json
{
  "project_description": "My Project",
  "objectives": ["Feature 1", "Feature 2"]
}
```

### **3. Review Generated Code**

- Check QA scores (aim for 90+)
- Review security findings
- Run tests before deploying
- Customize as needed

### **4. Use Version Control**

```bash
# Initialize Git in workspace
cd ./my_workspace
git init
git add .
git commit -m "Initial commit from QuickOdoo"

# Or enable VCS auto-commit
export VCS_ENABLED=true
```

### **5. Iterate and Refine**

- Start with basic objectives
- Review generated code
- Add more specific objectives
- Customize templates as needed

---

## 📊 **Performance Tips**

### **1. Workspace Organization**

```bash
# Keep workspaces separate
project1/  # One workspace per project
project2/
project3/
```

### **2. Objective Specificity**

Good:
- "FastAPI OAuth authentication with JWT"
- "Next.js dashboard with dark mode"
- "Terraform AWS setup with VPC and RDS"

Bad:
- "Authentication"
- "Frontend"
- "Infrastructure"

### **3. Monitor Agent Performance**

- Check task completion times
- Review QA scores
- Monitor memory usage
- Watch for failed tasks

---

## 🎯 **Success Metrics**

### **Expected Performance**

- Task Completion Rate: 95-100%
- Average Task Time: 2-5 seconds
- QA Score: 90-100
- Security Issues: 0 critical
- Test Coverage: 70%+ (if pytest-cov installed)

### **Quality Indicators**

✅ Good:
- All tasks complete
- QA score 95+
- No security issues
- Tests pass

⚠️ Review Needed:
- QA score < 80
- Security warnings found
- Some tests failing
- Task completion < 90%

---

**Usage Guide Version**: 1.0  
**Last Updated**: November 3, 2025  
**For More**: See complete documentation in `docs/` directory

