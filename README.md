# Quick2Odoo - Multi-Agent Development System

**QuickBooks to Odoo Integration SaaS Platform Generator**

A sophisticated multi-agent development system designed to automate the creation of a complete SaaS application for migrating data from QuickBooks to Odoo v18.

## 🚀 Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run with command-line arguments
python main.py --project "QuickBooks to Odoo Integration" --objective "OAuth authentication"

# Or use a configuration file
python main.py --config config_example.json --workspace ./my_project
```

## 📚 Documentation

### **Core Documentation**
- **[Complete HTML Documentation](docs/Quick2Odoo_Agentic_Scaffold_Document.html)** - Full user guide with 11 agents, ResearcherAgent, web search, template system, ProjectLayout, latest features (Updated Nov 2025)
- **[Agent System Overview](README_AGENTS.md)** - Detailed architecture for all 11 agents including ResearcherAgent
- **[Testing Guide](TESTING_GUIDE.md)** - How to test the system with pytest-cov and coverage reporting
- **[Implementation Roadmap](IMPLEMENTATION_ROADMAP_COMPLETE.md)** - Complete development roadmap with Phase 1-3 done, Phase 4-5 multi-platform expansion planned

### **Specialized Guides**
- **[ResearcherAgent Guide](RESEARCHER_AGENT_GUIDE.md)** - Web research capability, multi-provider search, caching
- **[Agent Communication Guide](AGENT_RESEARCH_COMMUNICATION.md)** - How agents request research from each other
- **[Usage Guide](USAGE_GUIDE.md)** - Comprehensive usage examples and best practices
- **[Deployment Checklist](DEPLOYMENT_CHECKLIST.md)** - Production deployment guide
- **[VCS Integration Guide](VCS_INTEGRATION_GUIDE.md)** - Git and GitHub automation setup

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
  "project_description": "QuickBooks to Odoo Integration SaaS",
  "objectives": [
    "OAuth authentication",
    "Data synchronization",
    "Frontend dashboard"
  ]
}
```

Then run:
```bash
python main.py --config config.json --workspace ./my_project
```

## 🤝 Contributing

This project is part of the QuickBooks to Odoo migration initiative.

## 📄 License

Proprietary - QuickOdoo Project

## 🔗 Links

- Repository: https://github.com/cryptolavar-hub/Q2O
- Documentation: See `docs/Quick2Odoo_Agentic_Scaffold_Document.html`
