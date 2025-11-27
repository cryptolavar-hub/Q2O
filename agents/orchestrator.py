"""
Orchestrator Agent - Manages project breakdown and task distribution.
Breaks down projects into manageable tasks and assigns them to appropriate agents.

Enhanced with LLM task breakdown (Phase 2 - November 2025):
- Intelligently analyzes objectives using LLM
- Creates optimal task breakdown for ANY project type
- Determines agent assignments and dependencies
- Falls back to rules-based logic if LLM unavailable
"""

from typing import Dict, List, Optional, Any
from agents.base_agent import BaseAgent, AgentType, Task, TaskStatus
import uuid
import logging
import asyncio
import os

# LLM Integration (Phase 2 - with graceful fallback)
try:
    from utils.llm_service import get_llm_service, LLMService
    from utils.configuration_manager import get_configuration_manager, ConfigurationManager
    LLM_INTEGRATION_AVAILABLE = True
except ImportError as e:
    logging.warning(f"LLM integration not available for OrchestratorAgent: {e}")
    LLM_INTEGRATION_AVAILABLE = False


class OrchestratorAgent(BaseAgent):
    """
    Orchestrator agent that manages project breakdown and task distribution.
    
    Enhanced with LLM task breakdown (Phase 2):
    - Uses LLM to intelligently analyze objectives
    - Creates optimal task sequences
    - Determines proper agent assignments
    """

    def __init__(
        self, 
        agent_id: str = "orchestrator_main", 
        project_id: Optional[str] = None,
        workspace_path: Optional[str] = None,
        tenant_id: Optional[int] = None
    ):
        # CRITICAL: workspace_path is REQUIRED when project_id is set
        if project_id and not workspace_path:
            raise ValueError(
                f"CRITICAL: OrchestratorAgent requires workspace_path when project_id is set. "
                f"workspace_path must be set to Tenant_Projects/{{project_id}}/ to ensure all files are saved correctly."
            )
        
        super().__init__(
            agent_id, 
            AgentType.ORCHESTRATOR,
            workspace_path=workspace_path,
            project_id=project_id,
            tenant_id=tenant_id
        )
        self.project_tasks: Dict[str, Task] = {}
        self.agents: Dict[AgentType, List[BaseAgent]] = {}
        self.task_queue: List[Task] = []
        self.max_task_size: int = 100  # Maximum size/complexity for a single task
        self.project_id = project_id
        
        # LLM Integration (Phase 2 - November 2025)
        self.use_llm = os.getenv("Q2O_USE_LLM", "true").lower() == "true"
        
        if LLM_INTEGRATION_AVAILABLE and self.use_llm:
            self.llm_service = get_llm_service()
            self.config_manager = get_configuration_manager()
            self.llm_enabled = True
            logging.info("[OK] OrchestratorAgent: LLM task breakdown enabled")
        else:
            self.llm_service = None
            self.config_manager = None
            self.llm_enabled = False
            if self.use_llm:
                logging.warning("[WARNING] OrchestratorAgent: LLM requested but not available, using rules only")
            else:
                logging.info("[INFO] OrchestratorAgent: LLM disabled, using rules only")

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
            # Register task in global registry for cross-agent access
            try:
                from utils.task_registry import register_task
                register_task(task)
            except ImportError:
                # Task registry not available, continue without it
                pass

        self.logger.info(f"Created {len(tasks)} tasks from project breakdown")
        return tasks

    def _analyze_objective(self, objective: str, context: str, start_counter: int) -> List[Task]:
        """
        Analyze an objective and break it into tasks (ENHANCED with LLM).
        
        Uses LLM to intelligently break down objectives into optimal task sequences.
        Falls back to rules-based logic if LLM unavailable.
        
        Args:
            objective: The objective to analyze
            context: Project context
            start_counter: Starting task counter
            
        Returns:
            List of tasks for this objective
        """
        # Try LLM breakdown first (if enabled)
        if self.llm_enabled:
            try:
                # Check if we're already in async context
                try:
                    loop = asyncio.get_running_loop()
                    # Already in async - fall back to rules to avoid conflicts
                    self.logger.warning("Already in async context, using rules-based breakdown")
                    return self._analyze_objective_basic(objective, context, start_counter)
                except RuntimeError:
                    # No running loop - safe to create new one
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        llm_tasks = loop.run_until_complete(
                            self._analyze_objective_with_llm(objective, context, start_counter)
                        )
                        # CRITICAL: Wait for all pending tasks to complete before closing loop
                        # This ensures async operations (like Gemini API calls) finish properly
                        pending = asyncio.all_tasks(loop)
                        if pending:
                            loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                        
                        if llm_tasks:
                            self.logger.info(f"[LLM] LLM breakdown: {len(llm_tasks)} tasks created for '{objective}'")
                            return llm_tasks
                        else:
                            # LLM returned empty list - fall back to rules
                            self.logger.warning(f"[LLM] LLM breakdown returned empty list for '{objective}', falling back to rules-based breakdown")
                    finally:
                        # Only close loop after all tasks are complete
                        try:
                            # Cancel any remaining tasks
                            pending = asyncio.all_tasks(loop)
                            for task in pending:
                                task.cancel()
                            # Wait for cancellations
                            if pending:
                                loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                        except Exception:
                            pass
                        finally:
                            loop.close()
            except Exception as e:
                self.logger.warning(f"LLM breakdown failed, using rules: {e}")
        
        # Fallback to rules-based breakdown
        return self._analyze_objective_basic(objective, context, start_counter)
    
    async def _analyze_objective_with_llm(self, objective: str, context: str, start_counter: int) -> List[Task]:
        """
        Use LLM to intelligently break down objective into tasks.
        
        This is WHERE THE MAGIC HAPPENS - LLM analyzes the objective and determines
        the optimal sequence of tasks, agent assignments, and dependencies.
        
        Args:
            objective: The objective to implement
            context: Project context
            start_counter: Starting task counter
        
        Returns:
            List of tasks with proper sequencing and dependencies
        """
        if not self.llm_service:
            return []
        
        # Build comprehensive prompt with objective understanding
        system_prompt = """You are a senior project manager and software architect with deep understanding of software development.

**STEP 1: UNDERSTAND THE OBJECTIVE**
First, analyze and classify the objective to understand:
- What TYPE of system/app/service is being built? (mobile_app, web_app, saas_platform, api_service, data_pipeline, microservice, desktop_app, cli_tool, library, infrastructure, blockchain_app, ml_service, etc.)
- What PLATFORMS does it target? (android, ios, web, desktop, cloud, serverless, multi-platform, etc.)
- What DOMAIN/INDUSTRY? (finance, healthcare, ecommerce, education, productivity, supply_chain, etc.)
- What KEY FEATURES are mentioned? (authentication, payments, real-time, offline, collaboration, etc.)
- What TECHNOLOGIES are likely needed? (React Native, Python, FastAPI, Next.js, blockchain, ML frameworks, etc.)
- What COMPLEXITY level? (low, medium, high)

**STEP 2: CREATE INTELLIGENT TASK BREAKDOWN**
Based on your understanding, break down the objective into a sequence of implementation tasks.

Available Agent Types:
- RESEARCHER: Web research for documentation, best practices, code examples (use for new/unfamiliar technologies)
- INFRASTRUCTURE: Cloud infrastructure, Terraform, Kubernetes, Azure/AWS resources, deployment configs
- INTEGRATION: API integrations, OAuth flows, webhooks, external services, third-party APIs
- WORKFLOW: Business workflows, orchestration, Temporal workflows, data pipelines
- MOBILE: Mobile app development (React Native, iOS, Android, Flutter, native mobile code)
- FRONTEND: React/Next.js UI components, pages, dashboards, web interfaces
- CODER: Backend services, APIs, data models, business logic, server-side code
- TESTING: Unit tests, integration tests, test automation, test suites
- QA: Quality assurance, code review, validation, quality checks
- SECURITY: Security scanning, vulnerability checks, compliance, security reviews

**CRITICAL REQUIREMENTS:**
1. **UNDERSTAND FIRST**: Classify the objective type and understand its nature before creating tasks
2. **INTELLIGENT ASSIGNMENT**: Assign agents based on what the objective ACTUALLY needs, not just keywords
3. **PROPER SEQUENCING**: Research → Infrastructure → Integration → Implementation → Testing → QA → Security
4. **TECH STACK**: Identify appropriate technologies based on objective type and requirements
5. **CONCISE TITLES**: Task titles must be SHORT (max 60-70 chars) and descriptive
   - DO NOT use the full objective text as the title
   - Extract key concepts (technologies, actions, entities)
   - Examples: "Mobile: Fields Operations App" NOT "Build a mobile app in Android and iOS for the Use in the Fields Operations"
   - Format: "{AgentType}: {ConciseDescription}" (e.g., "Backend: QuickBooks API Check")

Return JSON:
{
  "objective_classification": {
    "type": "mobile_app" | "web_app" | "saas_platform" | "api_service" | etc.,
    "platforms": ["android", "ios"] | ["web"] | etc.,
    "domain": "finance" | "healthcare" | etc.,
    "complexity": "low" | "medium" | "high",
    "key_features": ["authentication", "payments", "real-time"],
    "tech_stack": ["React Native", "TypeScript"] | ["Python", "FastAPI"] | etc.
  },
  "tasks": [
    {
      "agent_type": "RESEARCHER",
      "title": "Research: Stripe API Integration",
      "description": "Research Stripe payment API, webhook handling, and security best practices",
      "tech_stack": ["Stripe API", "FastAPI", "Webhooks"],
      "complexity": "medium",
      "dependencies": []
    },
    {
      "agent_type": "CODER",
      "title": "Backend: Stripe API Client",
      "description": "Create Stripe API client with payment methods and webhook handlers",
      "tech_stack": ["Python", "Stripe API", "FastAPI"],
      "complexity": "high",
      "dependencies": [0]
    },
    ...
  ]
}

**RULES:**
- Research tasks FIRST if needed for new/unfamiliar tech or complex domains
- Infrastructure tasks before dependent services
- Implementation tasks after research/infrastructure
- Testing tasks after implementation
- QA tasks at the end
- Security tasks after implementation
- Use dependency indices (0-based) to reference prior tasks
- **Think beyond keywords** - understand the objective's true nature and requirements"""
        
        user_prompt = f"""Objective: {objective}

Project Context: {context}

**FIRST**: Classify and understand this objective - what type of system/app/service is being built? What platforms? What domain? What features?

**THEN**: Break this objective into a sequence of tasks with proper agent assignments and dependencies based on your understanding."""
        
        # Generate breakdown with LLM
        # Increased max_tokens to 4096 to prevent truncation (task breakdown can be large)
        response = await self.llm_service.complete(
            system_prompt,
            user_prompt,
            temperature=0.4,  # Moderate creativity for task planning
            max_tokens=4096  # Increased from 2048 to prevent MAX_TOKENS truncation
        )
        
        # CRITICAL FIX: Track LLM usage for task breakdown
        # Create a temporary task object for tracking (orchestrator doesn't have a task yet)
        # We'll track usage at the project level instead
        if response.success and response.usage:
            try:
                from agents.task_tracking import update_task_llm_usage_in_db, run_async
                # Note: Orchestrator doesn't have a specific task, so we track at project level
                # For now, we'll skip tracking here - individual agents will track their own usage
                self.logger.debug(
                    f"LLM task breakdown used {response.usage.total_tokens} tokens, "
                    f"${response.usage.total_cost:.4f} ({response.provider})"
                )
            except Exception as e:
                self.logger.debug(f"Could not track orchestrator LLM usage: {e}")
        
        if not response.success:
            self.logger.warning(f"LLM task breakdown failed: {response.error}")
            return []
        
        # Parse JSON response with robust parsing
        try:
            from utils.json_parser import parse_json_robust
            
            # Use robust JSON parser to handle malformed responses
            result = parse_json_robust(
                response.content,
                required_fields=['tasks']
            )
            
            if not result:
                self.logger.error("Failed to parse LLM task breakdown: Could not extract valid JSON")
                return []
            
            # Extract objective classification (if provided by LLM)
            classification = result.get('objective_classification', {})
            if classification:
                self.logger.info(
                    f"[LLM] Objective classified as: {classification.get('type', 'unknown')} "
                    f"(platforms: {classification.get('platforms', [])}, "
                    f"domain: {classification.get('domain', 'unknown')}, "
                    f"complexity: {classification.get('complexity', 'unknown')})"
                )
            
            task_specs = result.get('tasks', [])
            
            # Convert LLM task specs to actual Task objects
            tasks = []
            task_id_map = {}  # Map index to task ID
            
            for idx, spec in enumerate(task_specs):
                # Parse agent type
                agent_type_str = spec.get('agent_type', 'CODER').upper()
                try:
                    agent_type = AgentType[agent_type_str]
                except KeyError:
                    self.logger.warning(f"Unknown agent type: {agent_type_str}, using CODER")
                    agent_type = AgentType.CODER
                
                # Create task ID
                task_id = f"task_{start_counter + idx:04d}_{agent_type.value}"
                task_id_map[idx] = task_id
                
                # Parse dependencies (convert indices to task IDs)
                dep_indices = spec.get('dependencies', [])
                dependencies = [task_id_map[dep_idx] for dep_idx in dep_indices if dep_idx in task_id_map]
                
                # Generate concise title if not provided or if it's too long
                raw_title = spec.get('title', '')
                if not raw_title or len(raw_title) > 70:
                    from utils.name_generator import generate_task_title
                    title = generate_task_title(objective, agent_type_str, max_length=70)
                else:
                    title = raw_title
                
                # Create task
                task_metadata = {
                    "objective": objective,
                    "complexity": spec.get('complexity', 'medium'),
                    "llm_generated": True
                }
                
                # Add classification to metadata if available
                if classification:
                    task_metadata["objective_classification"] = classification
                
                task = Task(
                    id=task_id,
                    title=title,
                    description=spec.get('description', objective),
                    agent_type=agent_type,
                    tech_stack=spec.get('tech_stack', []),
                    dependencies=dependencies,
                    metadata=task_metadata
                )
                
                tasks.append(task)
            
            # Log LLM usage
            if response.usage:
                self.logger.info(
                    f"[COST] LLM breakdown cost: ${response.usage.total_cost:.4f} "
                    f"({response.usage.input_tokens}+{response.usage.output_tokens} tokens)"
                )
            
            return tasks
            
        except Exception as e:
            self.logger.error(f"Failed to process LLM task breakdown: {e}", exc_info=True)
            return []
    
    def _analyze_objective_basic(self, objective: str, context: str, start_counter: int) -> List[Task]:
        """
        Rules-based objective analysis (fallback when LLM unavailable).
        
        Uses if/else rules to determine task breakdown.
        
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
            from utils.name_generator import generate_task_title
            research_title = generate_task_title(objective, "RESEARCHER", max_length=70)
            research_task = Task(
                id=f"task_{start_counter:04d}_research",
                title=research_title,
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
            from utils.name_generator import generate_task_title
            infra_title = generate_task_title(objective, "INFRASTRUCTURE", max_length=70)
            infra_task = Task(
                id=f"task_{start_counter:04d}_infrastructure",
                title=infra_title,
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
            
            from utils.name_generator import generate_task_title
            integration_title = generate_task_title(objective, "INTEGRATION", max_length=70)
            integration_task = Task(
                id=f"task_{start_counter:04d}_integration",
                title=integration_title,
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
            
            from utils.name_generator import generate_task_title
            workflow_title = generate_task_title(objective, "WORKFLOW", max_length=70)
            workflow_task = Task(
                id=f"task_{start_counter:04d}_workflow",
                title=workflow_title,
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
        
        # Create mobile tasks (if needed) - Check BEFORE frontend since mobile is more specific
        if objective_type == "mobile":
            # Extract platforms from objective
            platforms = []
            if "android" in objective_lower:
                platforms.append("android")
            if "ios" in objective_lower or "iphone" in objective_lower:
                platforms.append("ios")
            if not platforms:
                platforms = ["android", "ios"]  # Default to both
            
            # Extract features from objective
            features = []
            if "field" in objective_lower or "operation" in objective_lower:
                features.append("field_operations")
            if "inventory" in objective_lower:
                features.append("inventory_management")
            if "finance" in objective_lower or "financial" in objective_lower:
                features.append("finance")
            
            # Mobile tasks depend on research and backend
            dependencies = [t.id for t in tasks if t.agent_type in [AgentType.RESEARCHER, AgentType.CODER]]
            
            from utils.name_generator import generate_task_title
            mobile_title = generate_task_title(objective, "MOBILE", max_length=70)
            mobile_task = Task(
                id=f"task_{start_counter:04d}_mobile",
                title=mobile_title,
                description=f"Build mobile app for: {objective}\n\nContext: {context}\n\nPlatforms: {', '.join(platforms)}\nFeatures: {', '.join(features) if features else 'General mobile app'}",
                agent_type=AgentType.MOBILE,
                tech_stack=["React Native", "TypeScript"] if "react native" in objective_lower else tech_stack + ["React Native", "TypeScript"],
                dependencies=dependencies,
                metadata={
                    "objective": objective,
                    "platforms": platforms,
                    "features": features,
                    "complexity": self._estimate_complexity(objective),
                    "mobile_type": "cross_platform" if len(platforms) > 1 else platforms[0] if platforms else "android"
                }
            )
            tasks.append(mobile_task)
            start_counter += 1
        
        # Create frontend tasks (if needed)
        if objective_type in ["frontend", "nextjs", "react", "ui", "page", "component", "onboarding", "mapping", "theme"]:
            from utils.name_generator import generate_task_title
            frontend_title = generate_task_title(objective, "FRONTEND", max_length=70)
            frontend_task = Task(
                id=f"task_{start_counter:04d}_frontend",
                title=frontend_title,
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
        
        # Create backend/coder tasks
        # CRITICAL FIX: Always create a coder task when code generation is needed
        # Integration, workflow, and frontend objectives ALWAYS need backend support
        needs_coder = self._needs_coder_task(objective_type, tasks, objective)
        
        if needs_coder:
            # Build dependencies: coder tasks depend on research, infrastructure, and integration tasks
            coder_dependencies = [
                t.id for t in tasks 
                if t.agent_type in [AgentType.INFRASTRUCTURE, AgentType.INTEGRATION, AgentType.RESEARCHER]
            ]
            
            from utils.name_generator import generate_task_title
            coder_title = generate_task_title(objective, "CODER", max_length=70)
            coder_task = Task(
                id=f"task_{start_counter:04d}_coder",
                title=coder_title,
                description=f"Implement backend functionality for: {objective}\n\nContext: {context}",
                agent_type=AgentType.CODER,
                tech_stack=tech_stack,
                dependencies=coder_dependencies,
                metadata={
                    "objective": objective,
                    "complexity": self._estimate_complexity(objective),
                    "requires_backend": True  # Mark as requiring backend
                }
            )
            tasks.append(coder_task)
            start_counter += 1

        # Create testing tasks (depends on implementation tasks)
        impl_tasks = [t for t in tasks if t.agent_type in [AgentType.CODER, AgentType.INTEGRATION, AgentType.WORKFLOW, AgentType.FRONTEND, AgentType.MOBILE]]
        if impl_tasks:
            from utils.name_generator import generate_task_title
            testing_title = generate_task_title(objective, "TESTING", max_length=70)
            testing_task = Task(
                id=f"task_{start_counter:04d}_testing",
                title=testing_title,
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
            from utils.name_generator import generate_task_title
            qa_title = generate_task_title(objective, "QA", max_length=70)
            qa_task = Task(
                id=f"task_{start_counter:04d}_qa",
                title=qa_title,
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
            from utils.name_generator import generate_task_title
            security_title = generate_task_title(objective, "SECURITY", max_length=70)
            security_task = Task(
                id=f"task_{start_counter:04d}_security",
                title=security_title,
                description=f"Perform security review for: {objective}\n\nContext: {context}",
                agent_type=AgentType.SECURITY,
                tech_stack=tech_stack,
                dependencies=[t.id for t in impl_tasks],
                metadata={"objective": objective}
            )
            tasks.append(security_task)

        return tasks

    def _needs_coder_task(self, objective_type: str, tasks: List[Task], objective: str) -> bool:
        """
        Determine if a coder task is needed for this objective.
        
        CRITICAL: Integration, workflow, and frontend objectives ALWAYS need backend code.
        This ensures coder agents receive tasks even when objectives are classified as
        integration/workflow/frontend types.
        
        Args:
            objective_type: Detected objective type
            tasks: List of tasks already created
            objective: Original objective string
            
        Returns:
            True if coder task is needed
        """
        # Always create coder task for explicit backend objectives
        if objective_type in ["api", "backend", "service", "model"]:
            return True
        
        # CRITICAL FIX: Integration/workflow/frontend/mobile objectives ALWAYS need backend code
        # This fixes the bug where coder agents don't receive tasks for integration/mobile objectives
        if objective_type in ["integration", "workflow", "frontend", "mobile"]:
            return True
        
        # If no tasks created, create generic coder task
        if not tasks:
            return True
        
        # Check if objective mentions code generation keywords
        code_keywords = ["code", "implement", "create", "build", "develop", "generate"]
        if any(keyword in objective.lower() for keyword in code_keywords):
            return True
        
        # Check if implementation tasks exist (integration/workflow/frontend/mobile)
        # These always need backend support
        impl_tasks_exist = any(
            t.agent_type in [AgentType.INTEGRATION, AgentType.WORKFLOW, AgentType.FRONTEND, AgentType.MOBILE] 
            for t in tasks
        )
        if impl_tasks_exist:
            return True
        
        return False

    def _detect_objective_type(self, objective: str) -> str:
        """Detect the type of objective for task breakdown."""
        if any(keyword in objective for keyword in ["terraform", "helm", "kubernetes", "k8s", "azure", "waf", "infrastructure"]):
            return "infrastructure"
        elif any(keyword in objective for keyword in ["quickbooks", "qbo", "odoo", "stripe", "oauth", "webhook", "integration"]):
            return "integration"
        elif any(keyword in objective for keyword in ["temporal", "workflow", "backfill", "sync"]):
            return "workflow"
        elif any(keyword in objective for keyword in ["mobile", "android", "ios", "react native", "react-native", "flutter", "mobile app", "mobile application", "app for", "app in"]):
            return "mobile"
        elif any(keyword in objective for keyword in ["nextjs", "react", "frontend", "page", "component", "ui", "onboarding", "mapping", "theme"]):
            return "frontend"
        elif any(keyword in objective for keyword in ["api", "backend", "service", "model"]):
            return "api"
        return "generic"

    def _detect_tech_stack(self, objective: str) -> List[str]:
        """Detect technology stack from objective."""
        tech_stack = []
        objective_lower = objective.lower()
        
        if any(keyword in objective_lower for keyword in ["python", "fastapi", "api"]):
            tech_stack.append("python")
        if any(keyword in objective_lower for keyword in ["nextjs", "react", "typescript", "frontend"]):
            tech_stack.append("nextjs")
        if any(keyword in objective_lower for keyword in ["mobile", "android", "ios", "react native", "react-native", "flutter"]):
            tech_stack.append("react-native")
            if "flutter" in objective_lower:
                tech_stack.append("flutter")
        if any(keyword in objective_lower for keyword in ["terraform", "infrastructure"]):
            tech_stack.append("terraform")
        if any(keyword in objective_lower for keyword in ["temporal", "workflow"]):
            tech_stack.append("temporal")
        if any(keyword in objective_lower for keyword in ["helm", "kubernetes", "k8s"]):
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
        # Expanded heuristic based on keywords and length
        keywords_high = [
            "api", "integration", "database", "authentication", "payment",
            "migration", "full migration", "data migration",  # Migration keywords
            "platform", "sage", "quickbooks", "xero", "netsuite",  # Platform keywords
            "oauth", "webhook", "sync", "orchestration",  # Integration keywords
            "billing", "stripe", "pricing"  # Complex business logic
        ]
        keywords_medium = ["form", "component", "service", "module", "crud", "endpoint"]
        
        objective_lower = objective.lower()
        
        # Check for high complexity keywords
        if any(keyword in objective_lower for keyword in keywords_high):
            return "high"
        # Check for medium complexity keywords
        elif any(keyword in objective_lower for keyword in keywords_medium):
            return "medium"
        # Check for multiple objectives or long descriptions (likely complex)
        elif len(objective) > 100 or "," in objective:
            return "high"
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
        
        # Update task in global registry to keep it in sync
        try:
            from utils.task_registry import register_task
            register_task(task)
        except ImportError:
            # Task registry not available, continue without it
            pass
        
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
                # Update task in global registry again after status change
                try:
                    from utils.task_registry import register_task
                    register_task(task)
                except ImportError:
                    pass
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

