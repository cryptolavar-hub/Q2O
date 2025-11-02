# Multi-Agent Development System

A sophisticated multi-agent system for managing software development projects. The system consists of specialized agents that work together to break down, implement, test, and quality-assure development tasks.

## Architecture

### Agents

1. **Orchestrator Agent** (`OrchestratorAgent`)
   - Breaks down projects into manageable tasks
   - Distributes tasks to appropriate agents
   - Manages dependencies between tasks
   - Tracks project progress and status

2. **Coder Agent** (`CoderAgent`)
   - Implements code based on task requirements
   - Generates code structure (APIs, models, services, components)
   - Creates files following best practices
   - Tracks implemented files

3. **Testing Agent** (`TestingAgent`)
   - Writes comprehensive test suites
   - Executes tests and collects results
   - Generates test reports
   - Ensures code testability

4. **QA Agent** (`QAAgent`)
   - Performs quality assurance reviews
   - Checks code quality metrics
   - Identifies security issues
   - Provides improvement recommendations

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

## Features

- **Automatic Project Breakdown**: Intelligent task creation from objectives
- **Dependency Management**: Automatic dependency resolution
- **Code Generation**: Multiple code patterns (APIs, models, services, components)
- **Test Generation**: Comprehensive test suites with unittest
- **Quality Assurance**: Multi-metric code quality reviews
- **Progress Tracking**: Real-time project status
- **Extensible**: Easy to add new agent types or capabilities

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

## Limitations

- Currently uses simplified code generation templates
- Test execution requires the generated code to be importable
- QA checks are heuristic-based (not full static analysis)
- Single workspace per system instance

## Future Enhancements

- Integration with real static analysis tools
- Support for multiple programming languages
- Agent communication protocols
- Task retry mechanisms
- Advanced load balancing for agents
- Integration with version control systems
- Real-time progress dashboard

## License

This project is part of QuickOdoo.

