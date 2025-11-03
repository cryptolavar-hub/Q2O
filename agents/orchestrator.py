"""
Orchestrator Agent - Manages project breakdown and task distribution.
Breaks down projects into manageable tasks and assigns them to appropriate agents.
"""

from typing import Dict, List, Optional, Any
from agents.base_agent import BaseAgent, AgentType, Task, TaskStatus
import uuid
import logging


class OrchestratorAgent(BaseAgent):
    """Orchestrator agent that manages project breakdown and task distribution."""

    def __init__(self, agent_id: str = "orchestrator_main"):
        super().__init__(agent_id, AgentType.ORCHESTRATOR)
        self.project_tasks: Dict[str, Task] = {}
        self.agents: Dict[AgentType, List[BaseAgent]] = {}
        self.task_queue: List[Task] = []
        self.max_task_size: int = 100  # Maximum size/complexity for a single task

    def register_agent(self, agent: BaseAgent):
        """
        Register an agent with the orchestrator.
        
        Args:
            agent: The agent to register
        """
        if agent.agent_type not in self.agents:
            self.agents[agent.agent_type] = []
        self.agents[agent.agent_type].append(agent)
        self.logger.info(f"Registered agent {agent.agent_id} of type {agent.agent_type.value}")

    def break_down_project(self, project_description: str, objectives: List[str]) -> List[Task]:
        """
        Break down a project into manageable tasks.
        
        Args:
            project_description: High-level description of the project
            objectives: List of objectives or features to implement
            
        Returns:
            List of tasks created from the project breakdown
        """
        self.logger.info(f"Breaking down project: {project_description}")
        
        tasks = []
        task_counter = 1

        # Analyze objectives and create tasks
        for objective in objectives:
            objective_tasks = self._analyze_objective(objective, project_description, task_counter)
            tasks.extend(objective_tasks)
            task_counter += len(objective_tasks)

        # Store all tasks
        for task in tasks:
            self.project_tasks[task.id] = task
            self.task_queue.append(task)

        self.logger.info(f"Created {len(tasks)} tasks from project breakdown")
        return tasks

    def _analyze_objective(self, objective: str, context: str, start_counter: int) -> List[Task]:
        """
        Analyze an objective and break it into tasks by agent type.
        Domain-aware breakdown for QuickBooks-to-Odoo project.
        
        Args:
            objective: The objective to analyze
            context: Project context
            start_counter: Starting task counter
            
        Returns:
            List of tasks for this objective
        """
        tasks = []
        objective_lower = objective.lower()
        
        # Detect objective type for domain-aware task creation
        objective_type = self._detect_objective_type(objective_lower)
        tech_stack = self._detect_tech_stack(objective_lower)
        
        # SMART DETECTION: Check if research is needed FIRST
        needs_research = self._needs_research(objective_lower, objective_type, tech_stack, context)
        
        if needs_research:
            research_task = Task(
                id=f"task_{start_counter:04d}_research",
                title=f"Research: {objective}",
                description=f"Conduct web research for: {objective}\n\nContext: {context}\n\nResearch needed to gather information about implementation approaches, best practices, and code examples.",
                agent_type=AgentType.RESEARCHER,
                tech_stack=tech_stack,
                metadata={
                    "objective": objective,
                    "research_query": objective,
                    "complexity": self._estimate_complexity(objective),
                    "research_depth": "adaptive"
                }
            )
            tasks.append(research_task)
            start_counter += 1
        
        # Create infrastructure tasks first (if needed)
        if objective_type in ["infrastructure", "terraform", "helm", "kubernetes", "k8s", "waf", "azure"]:
            infra_task = Task(
                id=f"task_{start_counter:04d}_infrastructure",
                title=f"Infrastructure: {objective}",
                description=f"Create infrastructure configuration for: {objective}\n\nContext: {context}",
                agent_type=AgentType.INFRASTRUCTURE,
                tech_stack=tech_stack,
                metadata={
                    "objective": objective,
                    "infrastructure_type": objective_type,
                    "complexity": self._estimate_complexity(objective)
                }
            )
            tasks.append(infra_task)
            start_counter += 1
        
        # Create integration tasks (if needed)
        if objective_type in ["integration", "quickbooks", "qbo", "odoo", "stripe", "oauth", "webhook"]:
            # Add research dependency if research task exists
            dependencies = [t.id for t in tasks if t.agent_type in [AgentType.INFRASTRUCTURE, AgentType.RESEARCHER]]
            
            integration_task = Task(
                id=f"task_{start_counter:04d}_integration",
                title=f"Integration: {objective}",
                description=f"Implement integration for: {objective}\n\nContext: {context}",
                agent_type=AgentType.INTEGRATION,
                tech_stack=tech_stack,
                dependencies=dependencies,
                metadata={
                    "objective": objective,
                    "integration_type": self._detect_integration_type(objective_lower),
                    "complexity": self._estimate_complexity(objective)
                }
            )
            tasks.append(integration_task)
            start_counter += 1
        
        # Create workflow tasks (if needed)
        if objective_type in ["workflow", "temporal", "backfill", "sync"]:
            # Add research dependency if research task exists
            dependencies = [t.id for t in tasks if t.agent_type in [AgentType.INTEGRATION, AgentType.RESEARCHER]]
            
            workflow_task = Task(
                id=f"task_{start_counter:04d}_workflow",
                title=f"Workflow: {objective}",
                description=f"Create Temporal workflow for: {objective}\n\nContext: {context}",
                agent_type=AgentType.WORKFLOW,
                tech_stack=tech_stack,
                dependencies=dependencies,
                metadata={
                    "objective": objective,
                    "workflow_type": objective_type,
                    "complexity": self._estimate_complexity(objective)
                }
            )
            tasks.append(workflow_task)
            start_counter += 1
        
        # Create frontend tasks (if needed)
        if objective_type in ["frontend", "nextjs", "react", "ui", "page", "component", "onboarding", "mapping", "theme"]:
            frontend_task = Task(
                id=f"task_{start_counter:04d}_frontend",
                title=f"Frontend: {objective}",
                description=f"Create frontend for: {objective}\n\nContext: {context}",
                agent_type=AgentType.FRONTEND,
                tech_stack=tech_stack,
                dependencies=[t.id for t in tasks if t.agent_type == AgentType.INTEGRATION or t.agent_type == AgentType.CODER],
                metadata={
                    "objective": objective,
                    "frontend_type": objective_type,
                    "complexity": self._estimate_complexity(objective)
                }
            )
            tasks.append(frontend_task)
            start_counter += 1
        
        # Create backend/coder tasks (if needed - for non-specialized code)
        if objective_type in ["api", "backend", "service", "model"] or not tasks:
            coder_task = Task(
                id=f"task_{start_counter:04d}_coder",
                title=f"Backend: {objective}",
                description=f"Implement backend functionality for: {objective}\n\nContext: {context}",
                agent_type=AgentType.CODER,
                tech_stack=tech_stack,
                dependencies=[t.id for t in tasks if t.agent_type in [AgentType.INFRASTRUCTURE, AgentType.INTEGRATION]],
                metadata={
                    "objective": objective,
                    "complexity": self._estimate_complexity(objective)
                }
            )
            tasks.append(coder_task)
            start_counter += 1

        # Create testing tasks (depends on implementation tasks)
        impl_tasks = [t for t in tasks if t.agent_type in [AgentType.CODER, AgentType.INTEGRATION, AgentType.WORKFLOW, AgentType.FRONTEND]]
        if impl_tasks:
            testing_task = Task(
                id=f"task_{start_counter:04d}_testing",
                title=f"Test: {objective}",
                description=f"Write and execute tests for: {objective}\n\nContext: {context}",
                agent_type=AgentType.TESTING,
                tech_stack=tech_stack,
                dependencies=[t.id for t in impl_tasks],
                metadata={"objective": objective, "test_coverage_target": 80}
            )
            tasks.append(testing_task)
            start_counter += 1

        # Create QA task (depends on testing task)
        if impl_tasks:
            qa_task = Task(
                id=f"task_{start_counter:04d}_qa",
                title=f"QA Review: {objective}",
                description=f"Perform quality assurance review for: {objective}\n\nContext: {context}",
                agent_type=AgentType.QA,
                tech_stack=tech_stack,
                dependencies=[t.id for t in tasks if t.agent_type == AgentType.TESTING],
                metadata={"objective": objective, "review_checklist": self._get_review_checklist()}
            )
            tasks.append(qa_task)
            start_counter += 1

        # Create security task (depends on implementation tasks)
        if impl_tasks:
            security_task = Task(
                id=f"task_{start_counter:04d}_security",
                title=f"Security Review: {objective}",
                description=f"Perform security review for: {objective}\n\nContext: {context}",
                agent_type=AgentType.SECURITY,
                tech_stack=tech_stack,
                dependencies=[t.id for t in impl_tasks],
                metadata={"objective": objective}
            )
            tasks.append(security_task)

        return tasks

    def _detect_objective_type(self, objective: str) -> str:
        """Detect the type of objective for task breakdown."""
        if any(keyword in objective for keyword in ["terraform", "helm", "kubernetes", "k8s", "azure", "waf", "infrastructure"]):
            return "infrastructure"
        elif any(keyword in objective for keyword in ["quickbooks", "qbo", "odoo", "stripe", "oauth", "webhook", "integration"]):
            return "integration"
        elif any(keyword in objective for keyword in ["temporal", "workflow", "backfill", "sync"]):
            return "workflow"
        elif any(keyword in objective for keyword in ["nextjs", "react", "frontend", "page", "component", "ui", "onboarding", "mapping", "theme"]):
            return "frontend"
        elif any(keyword in objective for keyword in ["api", "backend", "service", "model"]):
            return "api"
        return "generic"

    def _detect_tech_stack(self, objective: str) -> List[str]:
        """Detect technology stack from objective."""
        tech_stack = []
        
        if any(keyword in objective for keyword in ["python", "fastapi", "api"]):
            tech_stack.append("python")
        if any(keyword in objective for keyword in ["nextjs", "react", "typescript", "frontend"]):
            tech_stack.append("nextjs")
        if any(keyword in objective for keyword in ["terraform", "infrastructure"]):
            tech_stack.append("terraform")
        if any(keyword in objective for keyword in ["temporal", "workflow"]):
            tech_stack.append("temporal")
        if any(keyword in objective for keyword in ["helm", "kubernetes", "k8s"]):
            tech_stack.append("kubernetes")
        
        return tech_stack if tech_stack else ["python"]  # Default

    def _detect_integration_type(self, objective: str) -> str:
        """Detect integration type."""
        if "quickbooks" in objective or "qbo" in objective:
            return "quickbooks"
        elif "odoo" in objective:
            return "odoo"
        elif "stripe" in objective:
            return "stripe"
        elif "oauth" in objective:
            return "oauth"
        elif "webhook" in objective:
            return "webhook"
        return "generic"

    def _needs_research(self, objective: str, objective_type: str, tech_stack: List[str], context: str) -> bool:
        """
        Smart detection: Determine if research is needed for this objective.
        
        Args:
            objective: The objective string
            objective_type: Detected objective type
            tech_stack: Detected tech stack
            context: Project context
            
        Returns:
            True if research is needed, False otherwise
        """
        # Keywords that indicate research is needed
        research_keywords = [
            'latest', 'best practices', 'how to', 'explore', 'find', 'discover',
            'research', 'investigate', 'learn about', 'compare', 'evaluate',
            'new', 'emerging', 'trends', 'state of the art'
        ]
        
        # Check for research keywords
        if any(keyword in objective for keyword in research_keywords):
            return True
        
        # Unknown or uncommon tech stack - needs research
        known_tech = {'python', 'fastapi', 'nextjs', 'react', 'typescript', 'javascript',
                     'terraform', 'helm', 'kubernetes', 'temporal', 'quickbooks', 'odoo', 'stripe'}
        
        unknown_tech = [tech for tech in tech_stack if tech.lower() not in known_tech]
        if unknown_tech:
            self.logger.info(f"Unknown tech detected: {unknown_tech} - research needed")
            return True
        
        # Complex objectives that might benefit from research
        if len(objective.split()) > 10:  # Long, complex objective
            return True
        
        # Otherwise, no research needed (we have templates and knowledge)
        return False
    
    def _estimate_complexity(self, objective: str) -> str:
        """
        Estimate the complexity of an objective.
        
        Args:
            objective: The objective to analyze
            
        Returns:
            Complexity level (low, medium, high)
        """
        # Simple heuristic based on keywords and length
        keywords_high = ["api", "integration", "database", "authentication", "payment"]
        keywords_medium = ["form", "component", "service", "module"]
        
        objective_lower = objective.lower()
        
        if any(keyword in objective_lower for keyword in keywords_high):
            return "high"
        elif any(keyword in objective_lower for keyword in keywords_medium):
            return "medium"
        else:
            return "low"

    def _get_review_checklist(self) -> List[str]:
        """Get a standard QA review checklist."""
        return [
            "Code follows project standards",
            "Tests pass and coverage is adequate",
            "No obvious bugs or errors",
            "Documentation is updated",
            "Performance is acceptable",
            "Security considerations addressed"
        ]

    def assign_task_to_agent(self, task: Task) -> bool:
        """
        Assign a task to an appropriate agent.
        
        Args:
            task: The task to assign
            
        Returns:
            True if assignment was successful
        """
        agent_type = task.agent_type
        
        if agent_type not in self.agents or not self.agents[agent_type]:
            self.logger.error(f"No agents available for type {agent_type.value}")
            return False

        # Check if task dependencies are met
        if not self._check_dependencies(task):
            task.status = TaskStatus.BLOCKED
            self.logger.warning(f"Task {task.id} is blocked by dependencies")
            return False

        # Use load balancer if available, otherwise fallback to round-robin
        try:
            from utils.load_balancer import get_load_balancer, TaskPriority
            
            load_balancer = get_load_balancer()
            priority = TaskPriority.NORMAL  # Could be determined from task metadata
            
            instance = load_balancer.route_task(task, priority=priority, routing_algorithm="least_busy")
            
            if instance and instance.agent.assign_task(task):
                task.status = TaskStatus.IN_PROGRESS
                
                # Initialize retry metadata if not present
                if "retry_count" not in task.metadata:
                    task.metadata["retry_count"] = 0
                
                self.logger.info(f"Assigned task {task.id} to {instance.agent_id} via load balancer")
                return True
        except Exception as e:
            self.logger.warning(f"Load balancer not available, using fallback: {e}")
        
        # Fallback: Try to assign to available agents (round-robin)
        available_agents = self.agents[agent_type]
        for agent in available_agents:
            if agent.assign_task(task):
                task.status = TaskStatus.IN_PROGRESS
                
                # Initialize retry metadata if not present
                if "retry_count" not in task.metadata:
                    task.metadata["retry_count"] = 0
                
                self.logger.info(f"Assigned task {task.id} to {agent.agent_id}")
                return True

        return False

    def _check_dependencies(self, task: Task) -> bool:
        """
        Check if all dependencies for a task are completed.
        
        Args:
            task: The task to check
            
        Returns:
            True if all dependencies are completed
        """
        for dep_id in task.dependencies:
            if dep_id not in self.project_tasks:
                return False
            
            dep_task = self.project_tasks[dep_id]
            if dep_task.status != TaskStatus.COMPLETED:
                return False

        return True

    def process_task(self, task: Task) -> Task:
        """
        Process a task - for orchestrator, this means coordinating task assignment.
        
        Args:
            task: The task to process
            
        Returns:
            The updated task
        """
        # Orchestrator doesn't process tasks directly, it assigns them
        if task.status == TaskStatus.PENDING:
            if self.assign_task_to_agent(task):
                task.status = TaskStatus.IN_PROGRESS
            else:
                if task.status == TaskStatus.BLOCKED:
                    pass  # Already handled
                else:
                    task.status = TaskStatus.FAILED
                    task.error = "Failed to assign task to agent"

        return task

    def get_ready_tasks(self) -> List[Task]:
        """
        Get tasks that are ready to be assigned (dependencies met).
        
        Returns:
            List of ready tasks
        """
        ready_tasks = []
        
        for task in self.task_queue:
            if task.status == TaskStatus.PENDING:
                if self._check_dependencies(task):
                    ready_tasks.append(task)
        
        return ready_tasks

    def distribute_tasks(self):
        """Distribute ready tasks to appropriate agents."""
        ready_tasks = self.get_ready_tasks()
        
        for task in ready_tasks:
            self.assign_task_to_agent(task)

    def update_task_status(self, task_id: str, status: TaskStatus, result: Any = None, error: str = None):
        """
        Update the status of a task.
        
        Args:
            task_id: ID of the task
            status: New status
            result: Optional result
            error: Optional error message
        """
        if task_id not in self.project_tasks:
            self.logger.warning(f"Task {task_id} not found")
            return

        task = self.project_tasks[task_id]
        task.status = status
        
        if status == TaskStatus.COMPLETED:
            task.complete(result)
            # Check if any blocked tasks can now be assigned
            self.distribute_tasks()
        elif status == TaskStatus.FAILED:
            task.fail(error or "Unknown error")
            
            # Auto-retry logic: Check if task should be retried
            from utils.retry_policy import get_policy_manager
            
            policy_manager = get_policy_manager()
            policy = policy_manager.get_policy(task.agent_type.value, task.title)
            
            # Check if task has retries remaining (stored in metadata)
            retry_count = task.metadata.get("retry_count", 0)
            
            if retry_count < policy.max_retries:
                self.logger.info(
                    f"Task {task_id} failed, scheduling retry ({retry_count + 1}/{policy.max_retries})"
                )
                task.metadata["retry_count"] = retry_count + 1
                task.status = TaskStatus.PENDING  # Reset to pending for retry
                # Task will be picked up by distribute_tasks() on next iteration
            else:
                self.logger.error(f"Task {task_id} failed after {retry_count} retries, giving up")

    def get_project_status(self) -> Dict[str, Any]:
        """
        Get overall project status.
        
        Returns:
            Dictionary with project status information
        """
        total_tasks = len(self.project_tasks)
        completed = sum(1 for t in self.project_tasks.values() if t.status == TaskStatus.COMPLETED)
        in_progress = sum(1 for t in self.project_tasks.values() if t.status == TaskStatus.IN_PROGRESS)
        failed = sum(1 for t in self.project_tasks.values() if t.status == TaskStatus.FAILED)
        blocked = sum(1 for t in self.project_tasks.values() if t.status == TaskStatus.BLOCKED)
        pending = sum(1 for t in self.project_tasks.values() if t.status == TaskStatus.PENDING)

        return {
            "total_tasks": total_tasks,
            "completed": completed,
            "in_progress": in_progress,
            "failed": failed,
            "blocked": blocked,
            "pending": pending,
            "completion_percentage": (completed / total_tasks * 100) if total_tasks > 0 else 0
        }

