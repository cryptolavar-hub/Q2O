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

- **[Complete HTML Documentation](docs/Quick2Odoo_Agentic_Scaffold_Document.html)** - Full user guide with troubleshooting and glossary
- **[Agent System Overview](README_AGENTS.md)** - Detailed agent architecture
- **[Testing Guide](TESTING_GUIDE.md)** - How to test the system
- **[Implementation Plan](IMPLEMENTATION_PLAN.md)** - Development roadmap

## ✨ Features

- **10 Specialized Agents**: Orchestrator, Coder, Testing, QA, Infrastructure, Integration, Frontend, Workflow, Security, Node.js
- **Real-time Dashboard**: WebSocket-powered monitoring with live task tracking and metrics
- **Advanced Load Balancing**: High availability with agent redundancy, failover, and circuit breakers
- **Multi-Language Support**: Python, Node.js (20.x LTS), TypeScript, JavaScript, Terraform, Helm
- **VCS Integration**: Automatic Git commits, branch management, and GitHub PR creation
- **Agent Communication**: Message broker with pub/sub for inter-agent coordination
- **Static Analysis**: Integrated mypy, ruff, black, bandit, semgrep, safety
- **Template-Based Generation**: Jinja2 templates for FastAPI, Next.js, Terraform, Helm, Temporal, Express.js
- **Configurable Layouts**: Flexible project structure via ProjectLayout system
- **Retry Mechanisms**: Exponential backoff with configurable retry policies
- **CI/CD Pipeline**: GitHub Actions with automated testing and validation
- **Production-Ready**: Generates deployable code with proper error handling and documentation

## 🏗️ Architecture

The system uses 10 specialized AI agents that work collaboratively:

- **Orchestrator Agent**: Breaks down projects into manageable tasks, manages load balancing
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
