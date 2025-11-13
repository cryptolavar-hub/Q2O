# Q2O Multi-Agent Development System

**Last Updated**: November 13, 2025

A sophisticated multi-agent system for AI-powered software development. The system consists of **12 specialized agents** with **LLM integration** that work together to research, break down, implement, test, quality-assure, and deploy complete production-ready applications.

## Architecture

### 12 Specialized Agents ⭐ **Updated November 2025**

1. **Orchestrator Agent** (`OrchestratorAgent`)
   - Breaks down projects into manageable tasks
   - Distributes tasks to appropriate agents using load balancing
   - Manages dependencies between tasks
   - Tracks project progress and status
   - Integrates with load balancer for high availability
   - Manages retry policies for failed tasks

2. **Coder Agent** (`CoderAgent`)
   - Implements code based on task requirements
   - Generates FastAPI endpoints and SQLAlchemy models
   - Creates backend services and business logic
   - Uses Jinja2 templates for consistent code generation
   - Integrates with ProjectLayout for configurable file structure
   - Tracks implemented files

3. **Testing Agent** (`TestingAgent`)
   - Writes comprehensive pytest test suites
   - Executes tests and collects results
   - Generates test coverage reports using pytest-cov
   - Ensures code testability and quality
   - Validates generated code functionality

4. **QA Agent** (`QAAgent`)
   - Performs comprehensive code quality reviews
   - Integrates real static analysis tools:
     - **mypy**: Type checking for Python
     - **ruff**: Fast Python linter
     - **black**: Code formatting verification
   - Checks code quality metrics (complexity, maintainability)
   - Provides detailed improvement recommendations
   - Fixed duplicate status key bug for reliable reporting

5. **Infrastructure Agent** (`InfrastructureAgent`)
   - Generates Terraform configurations for cloud infrastructure
   - Creates Helm charts for Kubernetes deployments
   - Validates infrastructure code syntax
   - Supports Azure, AWS, and GCP
   - Manages WAF, Key Vault, and other cloud resources

6. **Integration Agent** (`IntegrationAgent`)
   - Generates OAuth 2.0 authentication flows
   - Creates API clients (QuickBooks, Odoo, Stripe)
   - Builds integration connectors (QuickBooks Desktop Web Connector)
   - Uses templates for consistent integration patterns
   - Handles third-party API integrations

7. **Frontend Agent** (`FrontendAgent`)
   - Creates Next.js/React components
   - Generates TypeScript frontend code
   - Builds responsive UI components
   - Creates dashboard interfaces
   - Implements modern UX patterns

8. **Workflow Agent** (`WorkflowAgent`)
   - Generates Temporal workflow definitions
   - Creates data backfill workflows
   - Manages long-running processes
   - Handles distributed task orchestration
   - Uses ProjectLayout for workflow organization

9. **Security Agent** (`SecurityAgent`)
   - Performs comprehensive security audits
   - Integrates real security scanning tools:
     - **bandit**: Python security linter
     - **semgrep**: Pattern-based security scanning
     - **safety**: Dependency vulnerability scanning
   - Detects hardcoded secrets using SecretsValidator
   - Generates .env.example files for environment variables
   - Provides security recommendations and fixes

10. **Researcher Agent** (`ResearcherAgent`) ⭐ NEW
   - Conducts automated web research for project objectives
   - Multi-provider search (Google Custom Search, Bing, DuckDuckGo with automatic fallback)
   - Smart detection of when research is needed (unknown tech, "latest" keywords, complex objectives)
   - 90-day knowledge caching across all projects (~/.q2o/research_cache/)
   - Adaptive research depth (quick, deep, comprehensive, adaptive)
   - Code example extraction from documentation
   - Official documentation discovery and prioritization
   - Quality validation with confidence scoring (0-100)
   - Web scraping capabilities (Level 1-2: search + documentation)
   - Handles research requests from other agents via message broker
   - Parallel execution (independent tasks run during research)
   - Rate limiting protection (configurable daily limits per provider)
   - Outputs: JSON (for agents) + Markdown (for humans) saved to research/ directory
   - Integration with all agents via `request_research()` method

11. **Node.js Agent** (`NodeAgent`)
    - Generates Node.js/Express.js applications
    - Creates TypeScript-based Node.js projects
    - Supports Node.js 20.x LTS (latest stable)
    - Generates package.json with proper dependencies
    - Uses templates for Express apps and API endpoints
    - Detects and validates Node.js project structure

12. **Mobile Agent** (`MobileAgent`) ⭐ **NEW - November 2025**
    - Generates React Native applications for iOS and Android
    - Hybrid generation: Templates + LLM fallback
    - Creates cross-platform mobile apps
    - Supports Expo SDK for rapid development
    - Generates navigation, state management, and API integration
    - Template learning from successful LLM generations

## LLM Integration ⭐ **Added November 2025**

### Multi-Provider Support

The Q2O agent system now includes **LLM integration** with multi-provider support:

**Supported Providers**:
1. **Google Gemini** (gemini-1.5-pro) - Primary provider
2. **OpenAI** (gpt-4-turbo) - Fallback provider #1
3. **Anthropic** (claude-3.5-sonnet) - Fallback provider #2

**Features**:
- **Hybrid Code Generation**: Templates-first with LLM fallback for maximum reliability
- **Self-Learning System**: Creates new templates from successful LLM outputs (cost reduction)
- **Multi-Provider Chain**: 3 providers × 3 retries each = 99.9% reliability
- **Cost Monitoring**: 7-level progressive alerts (50% → 100% budget)
- **Budget Management**: Auto-allocation across projects
- **Quality Validation**: Ensures 95-100% code quality from LLM generations

### How LLM Integration Works

```python
# Agents can request LLM assistance for complex/unknown tasks
result = await agent.generate_with_llm(
    prompt="Generate React component for user authentication",
    context={"framework": "Next.js", "auth": "JWT"}
)

# LLM response is:
# 1. Quality validated
# 2. Used in code generation
# 3. Learned as template for future reuse (cost savings)
```

### Template Learning Engine

The platform automatically learns from successful LLM generations:

```
First Project (Unknown Tech):
  Template not found → LLM generates → $0.52 cost → Template saved

Next 99 Projects:
  Template found → Instant reuse → $0.00 cost!

Result: Platform gets smarter and cheaper with every project
```

## Usage

### Basic Usage

```bash
# Run with command-line arguments
python main.py --project "My Project" --objective "Feature 1" --objective "Feature 2"

# Run with configuration file
python main.py --config config_example.json

# Set workspace directory
python main.py --workspace ./my_project --project "My Project" --objective "Feature"
```

### Configuration File Format

Create a JSON file with the following structure:

```json
{
  "project_description": "Description of your project",
  "objectives": [
    "Objective 1",
    "Objective 2",
    "Objective 3"
  ]
}
```

### Programmatic Usage

```python
from main import AgentSystem

# Initialize the system
system = AgentSystem(workspace_path="./my_workspace")

# Run a project
results = system.run_project(
    project_description="My awesome project",
    objectives=[
        "User authentication",
        "Data API",
        "Admin dashboard"
    ]
)

# Access results
print(f"Completion: {results['final_status']['completion_percentage']}%")
```

## How It Works

1. **Project Breakdown**: The Orchestrator analyzes the project description and objectives, breaking them into tasks by agent type:
   - **Coder tasks**: Implementation requirements
   - **Testing tasks**: Test creation (depends on coder tasks)
   - **QA tasks**: Quality review (depends on testing tasks)

2. **Task Distribution**: The Orchestrator assigns ready tasks to appropriate agents based on:
   - Task type matching agent capabilities
   - Dependency resolution
   - Agent availability

3. **Task Processing**: Each agent processes its assigned tasks:
   - **Coder**: Generates and writes code files
   - **Testing**: Creates and runs test suites
   - **QA**: Reviews code quality and provides reports

4. **Progress Tracking**: The system tracks:
   - Task status (pending, in_progress, completed, failed, blocked)
   - Agent workloads
   - Project completion percentage
   - Issues and recommendations

## Task Dependencies

Tasks have automatic dependencies:
- Testing tasks depend on their corresponding Coder tasks
- QA tasks depend on their corresponding Testing tasks

This ensures proper workflow: Code → Test → Review

## Output Structure

The system generates files in the workspace directory:

```
workspace/
├── src/              # Source code files (from Coder Agent)
├── tests/            # Test files (from Testing Agent)
├── api/              # API endpoints (if applicable)
├── models/           # Data models (if applicable)
├── services/         # Business logic (if applicable)
└── components/       # UI components (if applicable)
```

## Advanced Features

### High Availability & Load Balancing
- **Load Balancer** (`LoadBalancer`): Advanced task routing with multiple strategies
  - Round-robin distribution
  - Least-busy agent selection
  - Priority-based routing
  - Health-based routing (avoids unhealthy agents)
- **Agent Redundancy**: Multiple instances per agent type
- **Failover Mechanism**: Automatic task rerouting to healthy agents
- **Circuit Breaker**: Prevents cascading failures
- **Health Monitoring**: Continuous agent health checks

### Agent Communication
- **Message Broker** (`MessageBroker`): Pub/sub pattern for agent communication
  - In-memory broker for development
  - Redis broker for production
- **Standardized Protocol** (`AgentMessage`): Type-safe inter-agent messaging
- **MessagingMixin**: Easy integration for all agents

### Retry Mechanisms
- **Retry Policies** (`RetryPolicy`): Configurable retry strategies
  - Exponential backoff
  - Fixed delay
  - No retry option
- **RetryPolicyManager**: Per-agent retry configuration
- **Automatic Retry**: Failed tasks automatically retried based on policy

### VCS Integration
- **Git Manager** (`GitManager`): Automated Git operations
  - Auto-commit generated code
  - Branch creation and management
  - Push to remote repositories
- **GitHub Integration** (`VCSIntegration`): Pull request automation
  - Automatic PR creation
  - Customizable PR templates
  - Branch-based workflows

### Real-time Dashboard
- **WebSocket API**: Live task and agent monitoring
- **Event Manager**: Real-time event broadcasting
- **Metrics API**: Static analysis and performance metrics
- **React Dashboard**: Beautiful web UI for monitoring

### Multi-Language Support
- **Language Detection** (`LanguageDetector`): Auto-detect project languages
- **Framework Detection**: Identify frameworks (Express, FastAPI, etc.)
- **Package Manager Detection**: Detect npm, pnpm, pip, poetry
- **Template System**: Language-specific code generation

### Code Quality & Security
- **Static Analysis Integration**: Real tools, not just regex
  - Python: mypy, ruff, black
  - Security: bandit, semgrep, safety
- **Secrets Management** (`SecretsValidator`): Detect and prevent secret leaks
- **Environment Generation**: Auto-generate .env.example files

## Configuration

### Logging

Control logging verbosity:

```bash
python main.py --log-level DEBUG ...
```

Options: `DEBUG`, `INFO`, `WARNING`, `ERROR`

### Output

Save results to a JSON file:

```bash
python main.py --output results.json ...
```

## Extending the System

### Adding a New Agent Type

1. Create a new agent class inheriting from `BaseAgent`
2. Implement the `process_task()` method
3. Register the agent type in `AgentType` enum
4. Register agents with the orchestrator

### Customizing Code Generation

Modify the code generation methods in `CoderAgent`:
- `_generate_api_code()`
- `_generate_model_code()`
- `_generate_service_code()`
- `_generate_component_code()`

### Customizing QA Checks

Extend `QAAgent` with additional check methods:
- `_check_performance()`
- `_check_accessibility()`
- `_check_compliance()`

## System Components

### Base Agent (`BaseAgent`)
All agents inherit from `BaseAgent`, which provides:
- Event emission for dashboard integration
- Retry logic with `process_task_with_retry`
- VCS integration hooks (`_auto_commit_task`)
- Messaging capabilities via `MessagingMixin`
- Standardized task processing workflow

### Utility Modules (14 Total)
1. **project_layout.py**: Configurable project directory structure
2. **template_renderer.py**: Jinja2 template rendering
3. **exceptions.py**: Standardized exception hierarchy
4. **retry.py**: Exponential backoff decorator
5. **retry_policy.py**: Configurable retry strategies
6. **security_scanner.py**: Bandit, semgrep, safety integration
7. **code_quality_scanner.py**: mypy, ruff, black integration
8. **secrets_validator.py**: Secret detection and .env generation
9. **language_detector.py**: Language and framework detection
10. **load_balancer.py**: High availability load balancing
11. **message_broker.py**: Pub/sub message broker abstraction
12. **message_protocol.py**: Standardized agent messaging protocol
13. **git_manager.py**: Git operations automation
14. **vcs_integration.py**: GitHub API integration

## Production Readiness

✅ **All Priority Features Implemented**:
- ✅ Real-time progress dashboard
- ✅ Integration with real static analysis tools
- ✅ Support for multiple programming languages (Python, Node.js, TypeScript)
- ✅ Agent communication protocols
- ✅ Task retry mechanisms
- ✅ Advanced load balancing for agents
- ✅ Integration with version control systems

## License

This project is part of Q2O (Quick to Objective).

