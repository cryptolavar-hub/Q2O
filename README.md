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

- **9 Specialized Agents**: Orchestrator, Coder, Testing, QA, Infrastructure, Integration, Frontend, Workflow, Security
- **Template-Based Generation**: Jinja2 templates for FastAPI, Next.js, Terraform, Helm, Temporal
- **Configurable Layouts**: Flexible project structure via ProjectLayout system
- **CI/CD Pipeline**: GitHub Actions with automated testing and validation
- **Production-Ready**: Generates deployable code with proper error handling and documentation

## 🏗️ Architecture

The system uses specialized AI agents that work collaboratively:

- **Orchestrator Agent**: Breaks down projects into manageable tasks
- **Coder Agent**: Generates FastAPI endpoints and SQLAlchemy models
- **Infrastructure Agent**: Creates Terraform and Helm configurations
- **Integration Agent**: Generates OAuth and API client code
- **Frontend Agent**: Creates Next.js/React components
- **Workflow Agent**: Generates Temporal workflow definitions
- **Testing Agent**: Creates and executes pytest test suites
- **QA Agent**: Performs code quality reviews
- **Security Agent**: Audits code for security issues

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
