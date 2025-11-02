"""
Main entry point for the Multi-Agent Development System.
Coordinates the orchestrator and all agent types to complete projects.
"""

import argparse
import logging
import sys
import os
import json
from pathlib import Path
from typing import List, Dict, Any

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
    AgentType,
    TaskStatus
)

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


class AgentSystem:
    """Main system that coordinates all agents."""

    def __init__(self, workspace_path: str = ".", project_layout: ProjectLayout = None):
        """
        Initialize the agent system.
        
        Args:
            workspace_path: Path to the workspace directory
            project_layout: Optional custom project layout
        """
        self.workspace_path = Path(workspace_path)
        self.workspace_path.mkdir(parents=True, exist_ok=True)
        
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
        
        # Initialize orchestrator
        self.orchestrator = OrchestratorAgent()
        
        # Initialize specialized agents with project layout and load balancer
        # Multiple instances per type for redundancy and uptime
        self.coder_agents = [
            CoderAgent(workspace_path=str(self.workspace_path), project_layout=self.project_layout),
            CoderAgent(agent_id="coder_backup", workspace_path=str(self.workspace_path), project_layout=self.project_layout)
        ]
        self.testing_agents = [
            TestingAgent(workspace_path=str(self.workspace_path), project_layout=self.project_layout),
            TestingAgent(agent_id="testing_backup", workspace_path=str(self.workspace_path), project_layout=self.project_layout)
        ]
        self.qa_agents = [
            QAAgent(workspace_path=str(self.workspace_path)),
            QAAgent(agent_id="qa_backup", workspace_path=str(self.workspace_path))
        ]
        self.infrastructure_agents = [
            InfrastructureAgent(workspace_path=str(self.workspace_path), project_layout=self.project_layout),
            InfrastructureAgent(agent_id="infrastructure_backup", workspace_path=str(self.workspace_path), project_layout=self.project_layout)
        ]
        self.integration_agents = [
            IntegrationAgent(workspace_path=str(self.workspace_path), project_layout=self.project_layout),
            IntegrationAgent(agent_id="integration_backup", workspace_path=str(self.workspace_path), project_layout=self.project_layout)
        ]
        self.frontend_agents = [
            FrontendAgent(workspace_path=str(self.workspace_path), project_layout=self.project_layout),
            FrontendAgent(agent_id="frontend_backup", workspace_path=str(self.workspace_path), project_layout=self.project_layout)
        ]
        self.workflow_agents = [
            WorkflowAgent(workspace_path=str(self.workspace_path), project_layout=self.project_layout),
            WorkflowAgent(agent_id="workflow_backup", workspace_path=str(self.workspace_path), project_layout=self.project_layout)
        ]
        self.security_agents = [
            SecurityAgent(workspace_path=str(self.workspace_path)),
            SecurityAgent(agent_id="security_backup", workspace_path=str(self.workspace_path))
        ]
        
        # Node.js agent (if available)
        self.node_agents = []
        if HAS_NODE_AGENT:
            self.node_agents = [
                NodeAgent(workspace_path=str(self.workspace_path), project_layout=self.project_layout),
                NodeAgent(agent_id="node_backup", workspace_path=str(self.workspace_path), project_layout=self.project_layout)
            ]
        
        # Register all agents with load balancer
        all_agent_lists = [
            self.coder_agents, self.testing_agents, self.qa_agents,
            self.infrastructure_agents, self.integration_agents,
            self.frontend_agents, self.workflow_agents, self.security_agents
        ]
        
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
        
        self.logger = logging.getLogger(__name__)
        
        # Initialize VCS integration if enabled
        self.vcs_enabled = os.getenv("VCS_ENABLED", "false").lower() == "true"
        if self.vcs_enabled:
            from utils.git_manager import get_git_manager
            self.git_manager = get_git_manager(str(self.workspace_path), auto_commit=True)
            self.logger.info("VCS integration enabled")
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
                    self.frontend_agents + self.workflow_agents + self.security_agents
                )
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

    def run_project(self, project_description: str, objectives: List[str]) -> Dict[str, Any]:
        """
        Run a complete project with all agents.
        
        Args:
            project_description: High-level project description
            objectives: List of objectives/features to implement
            
        Returns:
            Dictionary with project results
        """
        self.logger.info("=" * 80)
        self.logger.info("Starting Multi-Agent Development Project")
        self.logger.info(f"Project: {project_description}")
        self.logger.info(f"Objectives: {len(objectives)}")
        self.logger.info("=" * 80)
        
        # Emit dashboard project start event
        try:
            from api.dashboard.events import get_event_manager
            import asyncio
            
            event_manager = get_event_manager()
            asyncio.create_task(event_manager.emit_project_start(project_description, objectives))
        except Exception:
            pass  # Dashboard optional
        
        # Break down project into tasks
        tasks = self.orchestrator.break_down_project(project_description, objectives)
        
        self.logger.info(f"Created {len(tasks)} tasks")
        
        # Process tasks iteratively
        max_iterations = 100  # Safety limit
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            self.logger.info(f"\n--- Iteration {iteration} ---")
            
            # Distribute ready tasks
            self.orchestrator.distribute_tasks()
            
            # Process active tasks for each agent
            all_agents = (
                self.coder_agents + self.testing_agents + self.qa_agents +
                self.infrastructure_agents + self.integration_agents +
                self.frontend_agents + self.workflow_agents + self.security_agents
            )
            
            for agent in all_agents:
                for task_id, task in list(agent.active_tasks.items()):
                    self.logger.info(f"Agent {agent.agent_id} processing task {task_id}")
                    # Process task with automatic retry
                    try:
                        updated_task = agent.process_task_with_retry(task)
                        
                        # Update orchestrator
                        if updated_task.status == TaskStatus.COMPLETED:
                            agent.complete_task(task_id, updated_task.result)
                            self.orchestrator.update_task_status(
                                task_id, TaskStatus.COMPLETED, updated_task.result
                            )
                        elif updated_task.status == TaskStatus.FAILED:
                            agent.fail_task(task_id, updated_task.error or "Unknown error")
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
            self.logger.info(f"Project status: {status}")
            
            if status["completion_percentage"] == 100:
                self.logger.info("All tasks completed!")
                break
            
            # Check if we're stuck (no progress possible)
            if status["pending"] == 0 and status["in_progress"] == 0:
                if status["blocked"] > 0:
                    self.logger.warning("Some tasks are blocked - checking dependencies")
                elif status["failed"] > 0:
                    self.logger.error("Some tasks failed - stopping")
                    break
                else:
                    break
        
        # Get final project status
        final_status = self.orchestrator.get_project_status()
        
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
                "security": [agent.get_status() for agent in self.security_agents]
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
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level)
    
    # Load project configuration
    if args.config:
        with open(args.config, 'r') as f:
            config = json.load(f)
        project_description = config.get("project_description", "")
        objectives = config.get("objectives", [])
    elif args.project and args.objectives:
        project_description = args.project
        objectives = args.objectives
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
    
    if not project_description or not objectives:
        print("Error: Project description and at least one objective are required")
        sys.exit(1)
    
    # Initialize and run the system
    system = AgentSystem(workspace_path=args.workspace)
    results = system.run_project(project_description, objectives)
    
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

