# Quick2Odoo - Multi-Platform Odoo Migration System

**AI-Powered Multi-Platform to Odoo v18 Migration SaaS Generator**

A sophisticated multi-agent development system that automates the creation of complete, production-ready SaaS applications for migrating data from **any accounting platform** to Odoo v18. Supports QuickBooks, SAGE, Wave, Expensify, doola, Dext, and more with an extensible architecture for unlimited platform integrations.

## 🚀 Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run with command-line arguments
python main.py --project "Multi-Platform Odoo Migration" --objective "OAuth authentication"

# Or use a configuration file
python main.py --config config_example.json --workspace ./my_project
```

## 📚 Documentation

### **📊 Business & Technical Analysis (NEW!)**
- **[Comprehensive Project Assessment](docs/COMPREHENSIVE_PROJECT_ASSESSMENT.md)** ⭐ - Complete business & technical analysis with ROI calculations, competitive analysis, and efficiency impact assessment (16,000+ words)
- **[Complete File System Structure](docs/FILE_SYSTEM_STRUCTURE.md)** - Detailed ASCII directory tree with 150+ files documented and annotated

### **Core Documentation**
- **[Complete HTML Documentation](docs/Quick2Odoo_Agentic_Scaffold_Document.html)** - Full user guide with 11 agents, ResearcherAgent, web search, template system, ProjectLayout, latest features (Updated Nov 2025)
- **[Agent System Overview](docs/md_docs/README_AGENTS.md)** - Detailed architecture for all 11 agents including ResearcherAgent
- **[Testing Guide](docs/md_docs/TESTING_GUIDE.md)** - How to test the system with pytest-cov and coverage reporting
- **[Implementation Roadmap](docs/md_docs/IMPLEMENTATION_ROADMAP_COMPLETE.md)** - Complete development roadmap with Phase 1-3 done, Phase 4-5 multi-platform expansion planned

### **Specialized Guides**
- **[ResearcherAgent Guide](docs/md_docs/RESEARCHER_AGENT_GUIDE.md)** - Web research capability, multi-provider search, caching
- **[Agent Communication Guide](docs/md_docs/AGENT_RESEARCH_COMMUNICATION.md)** - How agents request research from each other
- **[Usage Guide](docs/md_docs/USAGE_GUIDE.md)** - Comprehensive usage examples and best practices
- **[Deployment Checklist](docs/md_docs/DEPLOYMENT_CHECKLIST.md)** - Production deployment guide
- **[VCS Integration Guide](docs/md_docs/VCS_INTEGRATION_GUIDE.md)** - Git and GitHub automation setup

### **Additional Documentation**
📂 **[View All Documentation](docs/md_docs/)** - Complete collection of 62+ markdown documents including:
- Codebase reviews and verification reports
- Implementation summaries and progress reports
- Feature roadmaps and status updates
- Session summaries and completion reports
- GitHub sync instructions and guides
- Business analysis and ROI reports

## 🌐 Multi-Platform Support

**Migrate from ANY accounting platform to Odoo v18!**

### **Currently Supported Platforms:**
- 💼 **QuickBooks** (Online & Desktop via WebConnector)
- 📊 **SAGE** (50, 100, 200, X3)
- 🌊 **Wave** Accounting
- 💳 **Expensify**
- 🏢 **doola** 
- 📄 **Dext** (formerly Receipt Bank)

### **Extensible Architecture:**
Our multi-agent system automatically adapts to new platforms. Simply add platform-specific OAuth flows and API mappings - the agents handle code generation, testing, security, and deployment automatically!

### **Coming Soon:**
Xero, FreshBooks, Zoho Books, NetSuite, and more enterprise platforms.

---

## 📱 Mobile App (NEW!)

**Quick2Odoo Mobile Dashboard** - Full-featured React Native app for Android and iOS!

- 📊 **Real-time Dashboard**: Monitor projects, tasks, and agents on the go
- 🚀 **Project Initiation**: Start new migrations directly from your mobile device
- 📈 **Live Metrics**: System performance and analytics
- 🔔 **Instant Updates**: WebSocket-powered real-time notifications
- 🌐 **Multi-Platform Support**: Select and manage QuickBooks, SAGE, Wave, and more

**[View Mobile App Documentation →](mobile/README.md)**

---

## ✨ Features

### **Core Capabilities**
- **11 Specialized Agents**: Orchestrator, Coder, Testing, QA, Infrastructure, Integration, Frontend, Workflow, Security, **Researcher** ⭐, Node.js
- **Web Research (NEW!)** ⭐: Automated web search via Google/Bing/DuckDuckGo, 90-day caching, smart detection
- **Real-time Dashboard**: WebSocket-powered monitoring with live task tracking and metrics
- **Advanced Load Balancing**: High availability with agent redundancy, failover, and circuit breakers
- **Multi-Language Support**: Python, Node.js (20.x LTS), TypeScript, JavaScript, Terraform, Helm
- **VCS Integration**: Automatic Git commits, branch management, and GitHub PR creation

### **Agent Intelligence**
- **Agent Communication**: Message broker with pub/sub for inter-agent coordination and research requests
- **Smart Research Detection**: Automatically identifies when web research is needed for unknown tech
- **Adaptive Research Depth**: Quick, deep, or comprehensive research based on task complexity
- **Knowledge Caching**: 90-day cross-project research cache for instant retrieval

### **Code Quality & Security**
- **Static Analysis**: Integrated mypy, ruff, black, bandit, semgrep, safety
- **Test Coverage**: pytest-cov with automated HTML/JSON coverage reports
- **Secrets Management**: Automated .env.example generation, hardcoded secret detection
- **Template-Based Generation**: 14+ Jinja2 templates for FastAPI, Next.js, Terraform, Helm, Temporal, Express.js

### **Flexibility & Configuration**
- **Configurable Layouts**: Flexible project structure via ProjectLayout system (100% adoption)
- **Retry Mechanisms**: Exponential backoff with configurable retry policies per agent type
- **Multi-Platform Ready**: Extensible architecture for SAGE, Wave, Expensify, doola, Dext, and more

### **Production Ready**
- **CI/CD Pipeline**: GitHub Actions with automated testing and validation
- **Quality Assurance**: 97/100 QA score, 100% test pass rate, zero security issues
- **Production-Ready**: Generates deployable code with proper error handling and comprehensive documentation
- **Business Impact**: 85% development time reduction, 87.5% cost reduction, 10x scalability increase ([See full analysis](docs/COMPREHENSIVE_PROJECT_ASSESSMENT.md))

## 🏗️ Architecture

The system uses 11 specialized AI agents that work collaboratively:

- **Orchestrator Agent**: Breaks down projects into manageable tasks, manages load balancing
- **Researcher Agent**: Conducts web research, gathers documentation, extracts code examples (NEW!)
- **Coder Agent**: Generates FastAPI endpoints and SQLAlchemy models
- **Infrastructure Agent**: Creates Terraform and Helm configurations
- **Integration Agent**: Generates OAuth and API client code
- **Frontend Agent**: Creates Next.js/React components and dashboard UI
- **Workflow Agent**: Generates Temporal workflow definitions
- **Testing Agent**: Creates and executes pytest test suites with coverage reporting
- **QA Agent**: Performs code quality reviews using mypy, ruff, and black
- **Security Agent**: Audits code for security issues using bandit, semgrep, and safety
- **Node.js Agent**: Generates Node.js/Express applications with TypeScript support

### High Availability Features

- **Load Balancer**: Round-robin, least-busy, and priority-based task routing
- **Agent Redundancy**: Multiple instances per agent type for failover
- **Circuit Breakers**: Automatic failure detection and recovery
- **Health Monitoring**: Continuous agent health checks and auto-restart
- **Message Broker**: Redis/In-memory pub/sub for agent communication

## 📋 Requirements

- Python 3.10+
- pip
- Terraform 1.6.0+ (optional, for infrastructure validation)
- Helm 3.13.0+ (optional, for Helm validation)

## 📦 Installation

```bash
# Clone the repository
git clone https://github.com/cryptolavar-hub/Q2O.git
cd Q2O

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## 🔧 Usage

### Command Line

```bash
python main.py \
  --project "My Project" \
  --objective "Feature 1" \
  --objective "Feature 2" \
  --workspace ./output \
  --log-level INFO
```

### Configuration File

Create a JSON file:

```json
{
  "project_description": "Multi-Platform to Odoo Migration SaaS",
  "platforms": ["QuickBooks", "SAGE", "Wave", "Expensify"],
  "objectives": [
    "OAuth authentication for multiple platforms",
    "Cross-platform data synchronization",
    "Unified frontend dashboard"
  ]
}
```

Then run:
```bash
python main.py --config config.json --workspace ./my_project
```

## 🤝 Contributing

This project is part of the **Quick2Odoo** initiative - enabling seamless migration from any accounting platform to Odoo v18. We support QuickBooks, SAGE, Wave, Expensify, doola, Dext, and continuously expand to new platforms.

## 📄 License

Proprietary - QuickOdoo Project

## 🔗 Links

- Repository: https://github.com/cryptolavar-hub/Q2O
- Documentation: See `docs/Quick2Odoo_Agentic_Scaffold_Document.html`
