"""
Main entry point for the Multi-Agent Development System.
Coordinates the orchestrator and all agent types to complete projects.
"""

import sys
import os

# Load environment variables FIRST (before anything else)
from dotenv import load_dotenv
from pathlib import Path

# CRITICAL: Load .env from root directory (C:\Q2O_Combined\.env)
# This ensures GOOGLE_API_KEY and other keys are found
# QA_Engineer: Ensure .env is loaded from root directory only
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path, override=True)
    # Verify .env was loaded (for debugging)
    if os.getenv("DEBUG_ENV_LOADING", "false").lower() == "true":
        print(f"[DEBUG] Loaded .env from: {env_path.resolve()}")
else:
    # Fallback to default behavior (current directory)
    load_dotenv()
    if os.getenv("DEBUG_ENV_LOADING", "false").lower() == "true":
        print(f"[WARNING] .env not found at {env_path.resolve()}, using default dotenv behavior")

# Check Python version FIRST (before any imports)
if sys.version_info < (3, 10):
    print("=" * 70)
    print("ERROR: Python 3.10 or higher is required!")
    print(f"Current version: Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    print()
    print("Quick2Odoo requires Python 3.10, 3.11, or 3.12")
    print()
    print("Please download Python 3.12 from:")
    print("https://www.python.org/downloads/release/python-31210/")
    print()
    print("Then create a new virtual environment:")
    print("  py -3.12 -m venv venv")
    print("  .\\venv\\Scripts\\activate")
    print("  pip install -r requirements.txt")
    print("=" * 70)
    sys.exit(1)

if sys.version_info >= (3, 14):
    print("=" * 70)
    print("WARNING: Python 3.14+ detected!")
    print(f"Current version: Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    print()
    print("Quick2Odoo is tested with Python 3.10, 3.11, 3.12, and 3.13.")
    print("Python 3.14+ may have compatibility issues with some dependencies.")
    print()
    print("Recommended: Use Python 3.12 or 3.13")
    print("Download from: https://www.python.org/downloads/")
    print()
    print("Create virtual environment with Python 3.12:")
    print("  py -3.12 -m venv venv")
    print("  .\\venv\\Scripts\\activate")
    print("  pip install -r requirements.txt")
    print("=" * 70)
    print()
    response = input("Continue anyway? (y/N): ")
    if response.lower() != 'y':
        sys.exit(1)

import argparse
import logging
import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

from agents import (
    OrchestratorAgent,
    CoderAgent,
    TestingAgent,
    QAAgent,
    InfrastructureAgent,
    IntegrationAgent,
    FrontendAgent,
    WorkflowAgent,
    SecurityAgent,
    ResearcherAgent,
    AgentType,
    TaskStatus
)

# Mobile Agent (12th agent - React Native mobile development)
try:
    from agents.mobile_agent import MobileAgent
    HAS_MOBILE_AGENT = True
except ImportError:
    MobileAgent = None
    HAS_MOBILE_AGENT = False

# Optional: NodeAgent for Node.js support
try:
    from agents.node_agent import NodeAgent
    HAS_NODE_AGENT = True
except ImportError:
    NodeAgent = None
    HAS_NODE_AGENT = False

from utils.load_balancer import get_load_balancer
from utils.project_layout import ProjectLayout, get_default_layout, load_layout_from_config


def setup_logging(log_level: str = "INFO"):
    """Setup logging configuration."""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def verify_environment():
    """Verify critical environment variables are loaded."""
    logger = logging.getLogger("main")
    
    # QA_Engineer: Check if main process logging is enabled (default: false for production)
    main_process_logging_enabled = os.getenv("MAIN_PROCESS_LOGGING_ENABLED", "false").lower() == "true"
    
    # Check if .env file exists
    env_path = Path(".env")
    if not env_path.exists():
        if main_process_logging_enabled:
            logger.warning("[WARNING] .env file not found! Create it from env.example")
            logger.info("Run: cp env.example .env")
        return False
    
    # Check Google Search API configuration
    google_key = os.getenv("GOOGLE_SEARCH_API_KEY")
    google_cx = os.getenv("GOOGLE_SEARCH_CX")
    
    if google_key and google_cx:
        masked_key = google_key[:10] + "..." if len(google_key) > 10 else "***"
        if main_process_logging_enabled:
            logger.info(f"[OK] Google Search API configured: {masked_key}")
    else:
        if main_process_logging_enabled:
            logger.warning("[WARNING] Google Search API not configured - will use DuckDuckGo (may have rate limits)")
            logger.info("To configure: Add GOOGLE_SEARCH_API_KEY and GOOGLE_SEARCH_CX to .env")
    
    # Check Bing API
    bing_key = os.getenv("BING_SEARCH_API_KEY")
    if bing_key and main_process_logging_enabled:
        logger.info(f"[OK] Bing Search API configured")
    
    return True


class AgentSystem:
    """Main system that coordinates all agents."""

    def __init__(
        self, 
        workspace_path: str = ".", 
        project_layout: ProjectLayout = None,
        project_id: Optional[str] = None,
        tenant_id: Optional[int] = None
    ):
        """
        Initialize the agent system.
        
        Args:
            workspace_path: Path to the workspace directory
            project_layout: Optional custom project layout
            project_id: Project ID for task tracking (from tenant portal)
            tenant_id: Tenant ID for task tracking (from tenant portal)
        """
        # CRITICAL: Validate workspace_path with hard security guarantees
        from utils.safe_file_writer import validate_workspace_path, WorkspaceSecurityError
        
        try:
            validated_workspace = validate_workspace_path(workspace_path, project_id)
            self.workspace_path = validated_workspace
            self.workspace_path.mkdir(parents=True, exist_ok=True)
        except WorkspaceSecurityError as e:
            # QA_Engineer: Use self.logger after it's initialized, or use print for critical errors
            print(f"CRITICAL SECURITY ERROR: {e}")
            raise
        except Exception as e:
            print(f"Failed to validate workspace_path '{workspace_path}': {e}")
            raise
        
        self.project_id = project_id
        self.tenant_id = tenant_id
        
        # Set environment variables for task tracking
        if project_id:
            os.environ["Q2O_PROJECT_ID"] = project_id
        if tenant_id:
            os.environ["Q2O_TENANT_ID"] = str(tenant_id)
        
        # Load project layout (from config file, custom, or default)
        if project_layout is None:
            config_path = self.workspace_path / "project_layout.json"
            if config_path.exists():
                project_layout = load_layout_from_config(str(config_path))
            else:
                project_layout = get_default_layout()
        self.project_layout = project_layout
        
        # Initialize load balancer for high availability
        self.load_balancer = get_load_balancer()
        
        # Initialize orchestrator - CRITICAL: Must pass workspace_path to ensure all files are saved correctly
        self.orchestrator = OrchestratorAgent(
            workspace_path=str(self.workspace_path),
            project_id=self.project_id,
            tenant_id=self.tenant_id
        )
        
        # Initialize specialized agents with project layout and load balancer
        # Multiple instances per type for redundancy and uptime
        # Pass project_id, tenant_id, and orchestrator to agents for task tracking and dependency access
        agent_kwargs = {
            "workspace_path": str(self.workspace_path),
            "project_layout": self.project_layout,
            "project_id": self.project_id,
            "tenant_id": self.tenant_id,
            "orchestrator": self.orchestrator  # Pass orchestrator reference for dependency access
        }
        
        self.coder_agents = [
            CoderAgent(**agent_kwargs),
            CoderAgent(agent_id="coder_backup", **agent_kwargs)  # CRITICAL: Include workspace_path for backup agents
        ]
        self.testing_agents = [
            TestingAgent(**agent_kwargs),
            TestingAgent(agent_id="testing_backup", **agent_kwargs)  # CRITICAL: Include workspace_path for backup agents
        ]
        self.qa_agents = [
            QAAgent(**{k: v for k, v in agent_kwargs.items() if k != "project_layout"}),
            QAAgent(agent_id="qa_backup", **{k: v for k, v in agent_kwargs.items() if k != "project_layout"})  # CRITICAL: Include workspace_path
        ]
        self.infrastructure_agents = [
            InfrastructureAgent(**agent_kwargs),
            InfrastructureAgent(agent_id="infrastructure_backup", **agent_kwargs)  # CRITICAL: Include workspace_path for backup agents
        ]
        self.integration_agents = [
            IntegrationAgent(**agent_kwargs),
            IntegrationAgent(agent_id="integration_backup", **agent_kwargs)  # CRITICAL: Include workspace_path for backup agents
        ]
        self.frontend_agents = [
            FrontendAgent(**agent_kwargs),
            FrontendAgent(agent_id="frontend_backup", **agent_kwargs)  # CRITICAL: Include workspace_path for backup agents
        ]
        self.workflow_agents = [
            WorkflowAgent(**agent_kwargs),
            WorkflowAgent(agent_id="workflow_backup", **agent_kwargs)  # CRITICAL: Include workspace_path for backup agents
        ]
        self.security_agents = [
            SecurityAgent(**{k: v for k, v in agent_kwargs.items() if k != "project_layout"}),
            SecurityAgent(agent_id="security_backup", **{k: v for k, v in agent_kwargs.items() if k != "project_layout"})  # CRITICAL: Include workspace_path
        ]
        self.researcher_agents = [
            ResearcherAgent(**agent_kwargs),
            ResearcherAgent(agent_id="researcher_backup", **agent_kwargs)  # CRITICAL: Include workspace_path for backup agents
        ]
        
        # Mobile agent (12th agent - React Native mobile development)
        self.mobile_agents = []
        if HAS_MOBILE_AGENT:
            self.mobile_agents = [
                MobileAgent(**agent_kwargs),
                MobileAgent(agent_id="mobile_backup", **agent_kwargs)  # CRITICAL: Include workspace_path for backup agents
            ]
        
        # Node.js agent (if available)
        self.node_agents = []
        if HAS_NODE_AGENT:
            self.node_agents = [
                NodeAgent(**agent_kwargs),
                NodeAgent(agent_id="node_backup", **agent_kwargs)  # CRITICAL: Include workspace_path for backup agents
            ]
        
        # Register all agents with load balancer
        all_agent_lists = [
            self.coder_agents, self.testing_agents, self.qa_agents,
            self.infrastructure_agents, self.integration_agents,
            self.frontend_agents, self.workflow_agents, self.security_agents,
            self.researcher_agents
        ]
        
        if HAS_MOBILE_AGENT:
            all_agent_lists.append(self.mobile_agents)
        
        if HAS_NODE_AGENT:
            all_agent_lists.append(self.node_agents)
        
        for agent_list in all_agent_lists:
            for agent in agent_list:
                self.load_balancer.register_agent(agent, capacity=5)
        
        # Register agents with orchestrator
        for agent in self.coder_agents:
            self.orchestrator.register_agent(agent)
        for agent in self.testing_agents:
            self.orchestrator.register_agent(agent)
        for agent in self.qa_agents:
            self.orchestrator.register_agent(agent)
        for agent in self.infrastructure_agents:
            self.orchestrator.register_agent(agent)
        for agent in self.integration_agents:
            self.orchestrator.register_agent(agent)
        for agent in self.frontend_agents:
            self.orchestrator.register_agent(agent)
        for agent in self.workflow_agents:
            self.orchestrator.register_agent(agent)
        for agent in self.security_agents:
            self.orchestrator.register_agent(agent)
        for agent in self.researcher_agents:
            self.orchestrator.register_agent(agent)
        # QA_Engineer: Mobile agents registration - CRITICAL FIX for mobile task failures
        if HAS_MOBILE_AGENT:
            for agent in self.mobile_agents:
                self.orchestrator.register_agent(agent)
        
        self.logger = logging.getLogger(__name__)
        
        # Initialize VCS integration if enabled
        self.vcs_enabled = os.getenv("VCS_ENABLED", "false").lower() == "true"
        # QA_Engineer: Add GIT_AUTO_COMMIT_ENABLED environment variable (default: false for production safety)
        git_auto_commit_enabled = os.getenv("GIT_AUTO_COMMIT_ENABLED", "false").lower() == "true"
        if self.vcs_enabled:
            from utils.git_manager import get_git_manager
            self.git_manager = get_git_manager(str(self.workspace_path), auto_commit=git_auto_commit_enabled)
            if git_auto_commit_enabled:
                self.logger.info("VCS integration enabled with auto-commit")
            else:
                self.logger.info("VCS integration enabled (auto-commit disabled)")
        else:
            self.git_manager = None

    def _handle_vcs_integration(self, project_description: str, objectives: List[str], results: Dict[str, Any]):
        """Handle VCS operations after project completion."""
        if not self.vcs_enabled or not self.git_manager:
            return
        
        try:
            from utils.vcs_integration import get_vcs_integration
            
            # Create feature branch
            branch_name = f"feature/{project_description.lower().replace(' ', '-')[:50]}"
            branch_name = branch_name.replace('/', '-').replace('_', '-')
            
            # Add timestamp to make unique
            import time
            branch_name = f"{branch_name}-{int(time.time())}"
            
            if self.git_manager.create_branch(branch_name):
                self.logger.info(f"Created feature branch: {branch_name}")
                
                # Push branch
                if self.git_manager.push_branch(branch_name):
                    self.logger.info(f"Pushed branch: {branch_name}")
                
                # Collect all files created from all agents' completed tasks
                all_files = []
                all_agents = (
                    self.coder_agents + self.testing_agents + self.qa_agents +
                    self.infrastructure_agents + self.integration_agents +
                    self.frontend_agents + self.workflow_agents + self.security_agents +
                    self.researcher_agents
                )
                if hasattr(self, 'mobile_agents'):
                    all_agents.extend(self.mobile_agents)
                if hasattr(self, 'node_agents'):
                    all_agents.extend(self.node_agents)
                
                for agent in all_agents:
                    # Check completed tasks
                    for completed_task in agent.completed_tasks:
                        if completed_task.result and isinstance(completed_task.result, dict):
                            # Try various file list keys
                            for key in ["files_created", "integration_files", "frontend_files", 
                                       "infrastructure_files", "workflow_files", "node_files"]:
                                files = completed_task.result.get(key, [])
                                if files:
                                    all_files.extend(files)
                
                # Create PR
                vcs = get_vcs_integration(str(self.workspace_path))
                pr = vcs.create_project_pr(
                    project_description=project_description,
                    objectives=objectives,
                    branch_name=branch_name,
                    files_created=all_files if all_files else None
                )
                
                if pr:
                    self.logger.info(f"Created PR #{pr.get('number')}: {pr.get('html_url')}")
                    results["pull_request"] = {
                        "number": pr.get("number"),
                        "url": pr.get("html_url"),
                        "branch": branch_name
                    }
        except Exception as e:
            self.logger.warning(f"VCS integration failed (optional feature): {e}")

    def run_project(self, project_description: str, objectives: List[str], platforms: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Run a complete project with all agents.
        
        Args:
            project_description: High-level project description
            objectives: List of objectives/features to implement
            platforms: Optional list of target platforms (e.g., ["QuickBooks", "SAGE", "Wave"])
            
        Returns:
            Dictionary with project results
        """
        self.logger.info("=" * 80)
        self.logger.info("Starting Multi-Agent Development Project")
        self.logger.info(f"Project: {project_description}")
        if platforms:
            self.logger.info(f"Target Platforms: {', '.join(platforms)}")
        self.logger.info(f"Objectives: {len(objectives)}")
        self.logger.info("=" * 80)
        
        # Emit dashboard project start event
        try:
            from api.dashboard.events import get_event_manager
            import asyncio
            
            event_manager = get_event_manager()
            # Check if we're in an async context
            try:
                loop = asyncio.get_running_loop()
                # We're in an async context - schedule the task
                asyncio.create_task(event_manager.emit_project_start(
                    project_description, 
                    objectives, 
                    platforms or []
                ))
            except RuntimeError:
                # No running loop - emit synchronously in background thread
                import threading
                def emit_in_background():
                    from utils.event_loop_utils import create_compatible_event_loop
                    loop = create_compatible_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        loop.run_until_complete(event_manager.emit_project_start(
                            project_description, 
                            objectives, 
                            platforms or []
                        ))
                    finally:
                        loop.close()
                        asyncio.set_event_loop(None)
                
                thread = threading.Thread(target=emit_in_background, daemon=True)
                thread.start()
        except Exception:
            pass  # Dashboard optional
        
        # Break down project into tasks
        tasks = self.orchestrator.break_down_project(project_description, objectives)
        
        self.logger.info(f"Created {len(tasks)} tasks")
        
        # Process tasks iteratively
        # QA_Engineer - Dynamic max iterations: 50 iterations per task (e.g., 50 x 50 tasks = 2500 iterations)
        max_iterations = 50 * len(tasks) if len(tasks) > 0 else 100
        iteration = 0
        
        # QA_Engineer: Check if main process logging is enabled (default: false for production)
        main_process_logging_enabled = os.getenv("MAIN_PROCESS_LOGGING_ENABLED", "false").lower() == "true"
        
        # QA_Engineer: Heartbeat mechanism - track last heartbeat time
        import time
        last_heartbeat_time = time.time()
        heartbeat_interval = int(os.getenv("PROCESS_HEARTBEAT_INTERVAL_SECONDS", "60"))  # Default: 60 seconds
        heartbeat_enabled = os.getenv("PROCESS_HEARTBEAT_ENABLED", "true").lower() == "true"
        
        if main_process_logging_enabled:
            self.logger.info(f"Main process logging enabled (DEBUG mode)")
            self.logger.info(f"Max iterations: {max_iterations}, Heartbeat interval: {heartbeat_interval}s")
        
        while iteration < max_iterations:
            iteration += 1
            
            # QA_Engineer: Conditional logging based on MAIN_PROCESS_LOGGING_ENABLED
            if main_process_logging_enabled:
                self.logger.info(f"\n--- Iteration {iteration} ---")
            
            # QA_Engineer: Heartbeat mechanism - emit periodic status updates
            current_time = time.time()
            if heartbeat_enabled and (current_time - last_heartbeat_time) >= heartbeat_interval:
                try:
                    # Emit heartbeat to database/API if available
                    from agents.task_tracking import update_project_heartbeat
                    import asyncio
                    try:
                        loop = asyncio.get_running_loop()
                        # Schedule heartbeat in async context
                        asyncio.create_task(update_project_heartbeat(self.project_id, self.tenant_id))
                    except RuntimeError:
                        # No async loop - run in background thread
                        import threading
                        def emit_heartbeat():
                            from utils.event_loop_utils import create_compatible_event_loop
                            loop = create_compatible_event_loop()
                            asyncio.set_event_loop(loop)
                            try:
                                loop.run_until_complete(update_project_heartbeat(self.project_id, self.tenant_id))
                            finally:
                                loop.close()
                                asyncio.set_event_loop(None)
                        thread = threading.Thread(target=emit_heartbeat, daemon=True)
                        thread.start()
                    last_heartbeat_time = current_time
                    if main_process_logging_enabled:
                        self.logger.debug(f"Heartbeat emitted at iteration {iteration}")
                except Exception as e:
                    # Heartbeat is optional - don't fail if it doesn't work
                    if main_process_logging_enabled:
                        self.logger.debug(f"Heartbeat failed (optional): {e}")
            
            # Distribute ready tasks
            self.orchestrator.distribute_tasks()
            
            # Process active tasks for each agent
            # QA_Engineer: Include mobile agents in main execution loop (critical bug fix)
            all_agents = (
                self.coder_agents + self.testing_agents + self.qa_agents +
                self.infrastructure_agents + self.integration_agents +
                self.frontend_agents + self.workflow_agents + self.security_agents +
                self.researcher_agents
            )
            # Add mobile agents if available (consistent with run_project method)
            if hasattr(self, 'mobile_agents') and self.mobile_agents:
                all_agents = list(all_agents) + self.mobile_agents
            # Add node agents if available
            if hasattr(self, 'node_agents') and self.node_agents:
                all_agents = list(all_agents) + self.node_agents
            
            for agent in all_agents:
                for task_id, task in list(agent.active_tasks.items()):
                    # QA_Engineer: Conditional logging based on MAIN_PROCESS_LOGGING_ENABLED
                    if main_process_logging_enabled:
                        self.logger.info(f"Agent {agent.agent_id} processing task {task_id}")
                    # Process task with automatic retry
                    try:
                        updated_task = agent.process_task_with_retry(task)
                        
                        # Update orchestrator
                        # QA_Engineer: complete_task/fail_task already called in process_task, just update orchestrator
                        if updated_task.status == TaskStatus.COMPLETED:
                            # Don't call complete_task again - already called in process_task
                            self.orchestrator.update_task_status(
                                task_id, TaskStatus.COMPLETED, updated_task.result
                            )
                        elif updated_task.status == TaskStatus.FAILED:
                            # Don't call fail_task again - already called in process_task
                            self.orchestrator.update_task_status(
                                task_id, TaskStatus.FAILED, None, updated_task.error
                            )
                    except Exception as e:
                        # Task processing raised exception after retries exhausted
                        error_msg = f"Task processing failed after retries: {str(e)}"
                        self.logger.error(f"Task {task_id}: {error_msg}")
                        agent.fail_task(task_id, error_msg)
                        self.orchestrator.update_task_status(task_id, TaskStatus.FAILED, None, error_msg)
            
            # Check if all tasks are completed
            status = self.orchestrator.get_project_status()
            # QA_Engineer: Conditional logging based on MAIN_PROCESS_LOGGING_ENABLED
            if main_process_logging_enabled:
                self.logger.info(f"Project status: {status}")
            
            if status["completion_percentage"] == 100:
                if main_process_logging_enabled:
                    self.logger.info("All tasks completed!")
                # QA_Engineer: Solution 2 - Batch Commits - Flush pending commits when project completes
                try:
                    from utils.git_manager import get_git_manager
                    git_manager = get_git_manager(str(self.workspace_path))
                    if git_manager.auto_commit:  # Only flush if auto-commit is enabled
                        git_manager.flush_pending_commits()
                        if main_process_logging_enabled:
                            self.logger.info("Flushed pending batch commits")
                except Exception as e:
                    if main_process_logging_enabled:
                        self.logger.debug(f"Failed to flush batch commits (optional): {e}")
                break
            
            # QA_Engineer: Check if iteration limit reached
            if iteration >= max_iterations:
                if main_process_logging_enabled:
                    self.logger.warning(f"Reached max_iterations limit: {max_iterations}")
                    self.logger.info(f"Project status at limit: {status}")
                    self.logger.info(f"Completion: {status.get('completion_percentage', 0)}%")
                    self.logger.info(f"Tasks: {status.get('completed', 0)}/{status.get('total_tasks', 0)} completed")
                    self.logger.info(f"In progress: {status.get('in_progress', 0)}, Pending: {status.get('pending', 0)}")
                break
            
            # Check if we're stuck (no progress possible)
            if status["pending"] == 0 and status["in_progress"] == 0:
                if status["blocked"] > 0:
                    if main_process_logging_enabled:
                        self.logger.warning("Some tasks are blocked - checking dependencies")
                elif status["failed"] > 0:
                    if main_process_logging_enabled:
                        self.logger.error("Some tasks failed - stopping")
                    break
                else:
                    break
        
        # Get final project status
        final_status = self.orchestrator.get_project_status()
        
        # QA_Engineer: Process exit logging - log final status and exit reason
        if main_process_logging_enabled:
            self.logger.info(f"Project execution completed. Final iteration: {iteration}/{max_iterations}")
            self.logger.info(f"Final status: {final_status}")
            if final_status.get("completion_percentage", 0) == 100:
                self.logger.info("Exit reason: All tasks completed successfully")
            elif iteration >= max_iterations:
                self.logger.warning(f"Exit reason: Reached max_iterations limit ({max_iterations})")
            elif final_status.get("failed", 0) > 0:
                self.logger.error(f"Exit reason: {final_status.get('failed', 0)} tasks failed")
            else:
                self.logger.info("Exit reason: Normal completion")
        
        # Emit dashboard project complete event
        try:
            from api.dashboard.events import get_event_manager
            import asyncio
            
            event_manager = get_event_manager()
            asyncio.run(event_manager.emit_project_complete({
                "project_description": project_description,
                "objectives": objectives,
                "final_status": final_status
            }))
        except Exception:
            pass  # Dashboard optional
        
        # Collect results first
        results = {
            "project_description": project_description,
            "objectives": objectives,
            "platforms": platforms or [],
            "final_status": final_status,
            "tasks": {
                task.id: {
                    "title": task.title,
                    "status": task.status.value,
                    "result": task.result,
                    "error": task.error
                }
                for task in self.orchestrator.project_tasks.values()
            },
            "agent_statuses": {
                "orchestrator": self.orchestrator.get_status(),
                "coders": [agent.get_status() for agent in self.coder_agents],
                "testers": [agent.get_status() for agent in self.testing_agents],
                "qa": [agent.get_status() for agent in self.qa_agents],
                "infrastructure": [agent.get_status() for agent in self.infrastructure_agents],
                "integration": [agent.get_status() for agent in self.integration_agents],
                "frontend": [agent.get_status() for agent in self.frontend_agents],
                "workflow": [agent.get_status() for agent in self.workflow_agents],
                "security": [agent.get_status() for agent in self.security_agents],
                "researcher": [agent.get_status() for agent in self.researcher_agents]
            }
        }
        
        # VCS Integration: Create feature branch and PR if enabled (after collecting results)
        self._handle_vcs_integration(project_description, objectives, results)
        
        return results

    def print_results(self, results: Dict[str, Any]):
        """Print project results in a formatted way."""
        print("\n" + "=" * 80)
        print("PROJECT RESULTS")
        print("=" * 80)
        
        status = results["final_status"]
        print(f"\nTotal Tasks: {status['total_tasks']}")
        print(f"Completed: {status['completed']}")
        print(f"In Progress: {status['in_progress']}")
        print(f"Failed: {status['failed']}")
        print(f"Blocked: {status['blocked']}")
        print(f"Pending: {status['pending']}")
        print(f"Completion: {status['completion_percentage']:.1f}%")
        
        print("\n" + "-" * 80)
        print("TASK DETAILS")
        print("-" * 80)
        
        for task_id, task_info in results["tasks"].items():
            # Use ASCII-safe symbols for Windows compatibility
            status_symbol = {
                "completed": "[OK]",
                "failed": "[FAIL]",
                "in_progress": "[...]",
                "blocked": "[BLOCKED]",
                "pending": "[ ]"
            }.get(task_info["status"], "[?]")
            
            try:
                print(f"{status_symbol} {task_id}: {task_info['title']}")
            except UnicodeEncodeError:
                # Fallback if still encoding issues
                print(f"{status_symbol} {task_id}: {task_info['title'].encode('ascii', 'ignore').decode('ascii')}")
            if task_info["status"] == "failed" and task_info.get("error"):
                print(f"  Error: {task_info['error']}")
        
        print("\n" + "-" * 80)
        print("AGENT STATUSES")
        print("-" * 80)
        
        for agent_type, statuses in results["agent_statuses"].items():
            if isinstance(statuses, list):
                for status in statuses:
                    print(f"{agent_type}: {status['agent_id']}")
                    print(f"  Active: {status['active_tasks']}, "
                          f"Completed: {status['completed_tasks']}, "
                          f"Failed: {status['failed_tasks']}")
            else:
                print(f"{agent_type}: {statuses['agent_id']}")
                print(f"  Active: {statuses['active_tasks']}, "
                      f"Completed: {statuses['completed_tasks']}, "
                      f"Failed: {statuses['failed_tasks']}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Multi-Agent Development System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run a project with objectives from command line
  python main.py --project "Web API" --objective "User authentication" --objective "Data CRUD"
  
  # Run from JSON config
  python main.py --config config.json
  
  # Set workspace directory
  python main.py --workspace ./my_project --project "My Project" --objective "Feature 1"
        """
    )
    
    parser.add_argument(
        "--project",
        type=str,
        help="Project description"
    )
    
    parser.add_argument(
        "--objective",
        action="append",
        dest="objectives",
        help="Project objective (can be specified multiple times)"
    )
    
    parser.add_argument(
        "--config",
        type=str,
        help="Path to JSON config file with project description and objectives"
    )
    
    parser.add_argument(
        "--workspace",
        type=str,
        default=".",
        help="Workspace directory path (default: current directory)"
    )
    
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: INFO)"
    )
    
    parser.add_argument(
        "--output",
        type=str,
        help="Path to save results JSON file"
    )
    
    parser.add_argument(
        "--project-id",
        type=str,
        help="Project ID for task tracking (from tenant portal)"
    )
    
    parser.add_argument(
        "--project-name",
        type=str,
        help="Project name (from tenant portal)"
    )
    
    parser.add_argument(
        "--description",
        type=str,
        default="",
        help="Project description (from tenant portal)"
    )
    
    parser.add_argument(
        "--objectives",
        type=str,
        default="",
        help="Project objectives/custom instructions (from tenant portal)"
    )
    
    parser.add_argument(
        "--output-folder",
        type=str,
        help="Output folder path for project results"
    )
    
    parser.add_argument(
        "--tenant-id",
        type=int,
        help="Tenant ID for task tracking (from tenant portal)"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level)
    
    # Verify environment configuration
    print("=" * 70)
    print("Environment Configuration Check")
    print("=" * 70)
    verify_environment()
    print("=" * 70)
    print()
    
    # Load project configuration
    # Priority: command line args (from tenant portal) > config file > interactive
    if args.project_id and args.objectives:
        # Called from tenant portal - use provided arguments
        project_description = args.project_name or args.description or "Project"
        # Parse objectives (can be comma-separated or newline-separated)
        if isinstance(args.objectives, str):
            objectives = [obj.strip() for obj in args.objectives.split('\n') if obj.strip()]
            if len(objectives) == 1 and ',' in objectives[0]:
                objectives = [obj.strip() for obj in objectives[0].split(',') if obj.strip()]
        else:
            objectives = args.objectives if isinstance(args.objectives, list) else []
        platforms = []
    elif args.config:
        with open(args.config, 'r') as f:
            config = json.load(f)
        project_description = config.get("project_description", "")
        objectives = config.get("objectives", [])
        platforms = config.get("platforms", [])
    elif args.project and args.objectives:
        project_description = args.project
        objectives = args.objectives if isinstance(args.objectives, list) else [args.objectives]
        platforms = []  # No platforms specified via command line
    else:
        # Interactive mode or example
        print("Multi-Agent Development System")
        print("=" * 80)
        
        if not args.project:
            project_description = input("Enter project description: ").strip()
        else:
            project_description = args.project
        
        if not args.objectives:
            print("Enter objectives (one per line, empty line to finish):")
            objectives = []
            while True:
                obj = input("> ").strip()
                if not obj:
                    break
                objectives.append(obj)
        else:
            objectives = args.objectives
        
        platforms = []  # No platforms in interactive mode
    
    if not project_description or not objectives:
        print("Error: Project description and at least one objective are required")
        sys.exit(1)
    
    # Initialize and run the system
    # Prioritize output_folder over workspace to ensure code files are saved correctly
    workspace_path = args.output_folder if args.output_folder else (args.workspace or ".")
    system = AgentSystem(
        workspace_path=workspace_path,
        project_id=args.project_id,
        tenant_id=args.tenant_id
    )
    results = system.run_project(project_description, objectives, platforms)
    
    # Print results
    system.print_results(results)
    
    # Save results if requested
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\nResults saved to {args.output}")
    
    # Exit with appropriate code
    if results["final_status"]["failed"] > 0:
        sys.exit(1)
    elif results["final_status"]["completion_percentage"] < 100:
        sys.exit(2)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()

