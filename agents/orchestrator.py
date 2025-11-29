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
        self.pending_missing_tasks: List[Dict[str, Any]] = []  # QA_Engineer: Tasks to create from QA feedback
        self.project_structure_blueprint: Optional[Dict[str, Any]] = None  # QA_Engineer: Expected project structure from LLM breakdown
        
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
        
        # QA_Engineer: Setup QA feedback handlers for dynamic task creation
        # Register handler for COORDINATION messages from QA agent
        if self.enable_messaging:
            try:
                from utils.message_protocol import MessageType
                from utils.message_broker import get_default_broker
                
                # Ensure message_handlers dict exists
                if not hasattr(self, 'message_handlers'):
                    self.message_handlers = {}
                
                # Register handler for COORDINATION messages
                self.message_handlers[MessageType.COORDINATION] = self._handle_qa_feedback
                
                # Subscribe to orchestrator-specific channel (QA sends to "agents.orchestrator")
                if self.message_broker:
                    def orchestrator_message_handler(msg_dict):
                        self._handle_incoming_message(msg_dict)
                    
                    self.message_broker.subscribe("agents.orchestrator", orchestrator_message_handler)
                    self.logger.info("OrchestratorAgent subscribed to QA feedback channel: agents.orchestrator")
                
                self.logger.info("Registered QA feedback handler for dynamic task creation")
            except Exception as e:
                self.logger.warning(f"Failed to register QA feedback handler: {e}")

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
        
        # QA_Engineer: If blueprint was created during task breakdown, log it
        if self.project_structure_blueprint:
            blueprint_count = len(self.project_structure_blueprint)
            self.logger.info(
                f"[BLUEPRINT] Project structure blueprint available for QA agent "
                f"({blueprint_count} objective{'s' if blueprint_count > 1 else ''})"
            )
        
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
                    # Windows compatibility: Use SelectorEventLoop for psycopg async
                    from utils.event_loop_utils import create_compatible_event_loop
                    loop = create_compatible_event_loop()
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

**STEP 2: ANALYZE PROJECT STRUCTURE REQUIREMENTS**
Based on the objective type and tech stack, determine what COMPLETE project structure is needed:

For MOBILE_APP (React Native/Expo):
- ✅ Core files: App.tsx, package.json, tsconfig.json, AndroidManifest.xml, Info.plist
- ✅ Screens: All feature screens (authentication, profile, content posting, etc.)
- ✅ Components: Reusable UI components (Button, Input, Card, etc.)
- ✅ Navigation: Navigation setup (StackNavigator, TabNavigator, etc.)
- ✅ Services: API clients, Firebase services, storage services
- ✅ Hooks: Custom React hooks (useAuth, useApi, etc.)
- ✅ Store: State management (Redux/Zustand setup)
- ✅ Theme: Colors, typography, spacing configuration
- ✅ Types: TypeScript type definitions
- ✅ Utils: Helper functions, formatters, validators

For WEB_APP (Next.js/React):
- ✅ Pages: All route pages
- ✅ Components: Reusable UI components
- ✅ API Routes: Backend API endpoints
- ✅ Services: API clients, external service integrations
- ✅ Hooks: Custom React hooks
- ✅ Utils: Helper functions
- ✅ Types: TypeScript definitions
- ✅ Styles: CSS/styled-components configuration

For BACKEND_API (FastAPI/Python):
- ✅ API Routes: All endpoint files
- ✅ Models: Database models (SQLAlchemy)
- ✅ Services: Business logic services
- ✅ Schemas: Pydantic schemas
- ✅ Utils: Helper functions
- ✅ Config: Configuration management
- ✅ Middleware: Custom middleware

**STEP 3: CREATE COMPREHENSIVE TASK BREAKDOWN**
Based on your understanding, break down the objective into a sequence of implementation tasks.

CRITICAL: Include tasks for EVERY component of the project structure, not just the main features:
1. Project scaffolding (package.json, config files)
2. Core infrastructure (navigation, routing, state management setup)
3. Reusable components (even if not explicitly mentioned)
4. Service layer (API clients, external integrations)
5. Type definitions (TypeScript types, Pydantic schemas)
6. Utility functions (helpers, formatters, validators)
7. Theme/styling configuration
8. Testing infrastructure

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
      "file_type": "api",
      "dependencies": [0]
    },
    ...
  ]
}

**CRITICAL FOR CODER TASKS:**
- For CODER tasks, you MUST include a "file_type" field indicating the type of code file to generate
- Valid file_types: "api" (FastAPI endpoints), "model" (SQLAlchemy models), "service" (business logic), "component" (React/Next.js components), "page" (Next.js pages), "generic" (only if truly generic)
- Choose file_type based on what the task actually needs:
  * "api" - for REST endpoints, API handlers, HTTP routes
  * "model" - for database schemas, data models, ORM classes
  * "service" - for business logic, data processing, utility functions
  * "component" - for React/Next.js UI components
  * "page" - for Next.js page routes
  * "generic" - only as last resort if task doesn't fit any category
- Example: "Backend: Store User Theme Preferences" → file_type: "service" (stores preferences, business logic)
- Example: "Backend: Chat Message API" → file_type: "api" (REST endpoints for messages)
- Example: "Backend: User Profile Model" → file_type: "model" (database model)

**RULES:**
- Research tasks FIRST if needed for new/unfamiliar tech or complex domains
- Infrastructure tasks before dependent services
- Implementation tasks after research/infrastructure
- Testing tasks after implementation
- QA tasks at the end
- Security tasks after implementation
- Use dependency indices (0-based) to reference prior tasks
- **ALWAYS include scaffolding, infrastructure, and structural tasks**
- **ALWAYS include reusable components, services, hooks, types, utils**
- **Think about what a COMPLETE, PRODUCTION-READY project needs**
- **Don't just focus on feature screens - include all supporting infrastructure**
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
                
                # QA_Engineer: Extract and store project structure blueprint from LLM response
                # This blueprint defines what the COMPLETE project structure should be
                project_type = classification.get('type', 'unknown')
                tech_stack = classification.get('tech_stack', [])
                
                # Build structure blueprint based on project type and tech stack
                structure_blueprint = self._build_structure_blueprint(project_type, tech_stack, classification)
                
                # Store blueprint for QA agent to use (key by objective for multi-objective projects)
                if not self.project_structure_blueprint:
                    self.project_structure_blueprint = {}
                self.project_structure_blueprint[objective] = structure_blueprint
                
                self.logger.info(
                    f"[BLUEPRINT] Stored structure blueprint for {project_type} project "
                    f"with {len(structure_blueprint.get('expected_directories', []))} expected directories"
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
                
                # QA_Engineer: Add file_type to metadata for CODER tasks (determined by LLM)
                if agent_type == AgentType.CODER:
                    file_type = spec.get('file_type', None)
                    if file_type:
                        task_metadata["file_type"] = file_type
                        self.logger.debug(f"[LLM] Task {task_id} assigned file_type: {file_type}")
                    else:
                        # LLM didn't provide file_type - log warning but continue
                        self.logger.warning(f"[LLM] Task {task_id} (CODER) missing file_type - Coder Agent will infer")
                
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

    def _clear_completed_missing_tasks(self):
        """
        QA_Engineer: Remove completed/failed tasks from pending_missing_tasks.
        This prevents infinite loop warnings when tasks are already done.
        """
        if not self.pending_missing_tasks:
            return
        
        # Filter out completed/failed tasks
        remaining_tasks = [
            task for task in self.pending_missing_tasks
            if task.status not in [TaskStatus.COMPLETED, TaskStatus.FAILED]
        ]
        
        if len(remaining_tasks) != len(self.pending_missing_tasks):
            cleared_count = len(self.pending_missing_tasks) - len(remaining_tasks)
            self.logger.debug(f"Cleared {cleared_count} completed/failed tasks from pending_missing_tasks")
            self.pending_missing_tasks = remaining_tasks

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

        status = {
            "total_tasks": total_tasks,
            "completed": completed,
            "in_progress": in_progress,
            "failed": failed,
            "blocked": blocked,
            "pending": pending,
            "completion_percentage": (completed / total_tasks * 100) if total_tasks > 0 else 0
        }
        
        # QA_Engineer: Clear completed/failed tasks from pending_missing_tasks
        self._clear_completed_missing_tasks()
        
        # QA_Engineer: Check if we're near completion but have pending missing tasks
        if status["completion_percentage"] >= 90 and self.pending_missing_tasks:
            status["warning"] = f"{len(self.pending_missing_tasks)} missing components detected by QA"
        
        return status
    
    def _handle_qa_feedback(self, message_dict: Dict[str, Any]):
        """
        QA_Engineer: Handle incoming QA feedback regarding missing components or incomplete structure.
        Dynamically creates new tasks for missing components.
        
        Args:
            message_dict: Message dictionary from message broker
        """
        try:
            from utils.message_protocol import AgentMessage
            
            # Extract the actual message data
            msg_data = message_dict.get("data", message_dict)
            agent_msg = AgentMessage.from_dict(msg_data)
            
            # Verify this is a QA feedback message
            if agent_msg.message_type.value != "coordination":
                self.logger.debug(f"Ignoring non-coordination message: {agent_msg.message_type.value}")
                return
            
            payload = agent_msg.payload
            action = payload.get("action")
            
            if action != "missing_tasks_detected":
                self.logger.debug(f"Ignoring coordination message with action: {action}")
                return
            
            project_id = payload.get("project_id")
            missing_components = payload.get("missing_components", [])
            
            # Verify this message is for our project
            if project_id != self.project_id:
                self.logger.debug(f"Received QA feedback for different project {project_id}, ignoring")
                return
            
            if not missing_components:
                self.logger.debug("QA feedback has no missing components, ignoring")
                return
            
            self.logger.info(
                f"Received QA feedback: {len(missing_components)} missing components detected. "
                f"Creating dynamic tasks."
            )
            
            # Create new tasks for missing components
            new_tasks = self._create_tasks_for_missing_components(missing_components)
            
            if new_tasks:
                self.logger.info(f"Created {len(new_tasks)} new tasks for missing components")
                
                # Add tasks to project_tasks and task_queue
                for task in new_tasks:
                    self.project_tasks[task.id] = task
                    self.task_queue.append(task)
                    self.pending_missing_tasks.append(task)  # Track dynamically created tasks
                    
                    # Register task in global registry
                    try:
                        from utils.task_registry import register_task
                        register_task(task)
                    except ImportError:
                        pass
                    
                    self.logger.info(f"Added dynamic task: {task.title} (ID: {task.id})")
                
                # Redistribute tasks to include new ones
                self.distribute_tasks()
            else:
                self.logger.warning("Failed to create tasks for missing components")
                
        except Exception as e:
            self.logger.error(f"Error handling QA feedback: {e}", exc_info=True)
    
    def _create_tasks_for_missing_components(self, missing_components: List[str]) -> List[Task]:
        """
        QA_Engineer: Create tasks for missing project components detected by QA.
        
        Args:
            missing_components: List of missing component paths (e.g., ["src/components", "src/services"])
            
        Returns:
            List of new tasks created for missing components
        """
        new_tasks = []
        task_counter = len(self.project_tasks) + 1  # Start counter after existing tasks
        
        # Map component paths to agent types and task descriptions
        component_mapping = {
            "src/components": {
                "agent_type": AgentType.FRONTEND if any("nextjs" in str(t.tech_stack).lower() or "react" in str(t.tech_stack).lower() for t in self.project_tasks.values()) else AgentType.MOBILE,
                "title_prefix": "Frontend: " if any("nextjs" in str(t.tech_stack).lower() or "react" in str(t.tech_stack).lower() for t in self.project_tasks.values()) else "Mobile: ",
                "description": "Create reusable UI components"
            },
            "src/screens": {
                "agent_type": AgentType.MOBILE,
                "title_prefix": "Mobile: ",
                "description": "Create mobile app screens"
            },
            "src/services": {
                "agent_type": AgentType.CODER,
                "title_prefix": "Backend: ",
                "description": "Create service layer for API calls and business logic"
            },
            "src/hooks": {
                "agent_type": AgentType.FRONTEND if any("nextjs" in str(t.tech_stack).lower() or "react" in str(t.tech_stack).lower() for t in self.project_tasks.values()) else AgentType.MOBILE,
                "title_prefix": "Frontend: " if any("nextjs" in str(t.tech_stack).lower() or "react" in str(t.tech_stack).lower() for t in self.project_tasks.values()) else "Mobile: ",
                "description": "Create custom React hooks"
            },
            "src/store": {
                "agent_type": AgentType.FRONTEND if any("nextjs" in str(t.tech_stack).lower() or "react" in str(t.tech_stack).lower() for t in self.project_tasks.values()) else AgentType.MOBILE,
                "title_prefix": "Frontend: " if any("nextjs" in str(t.tech_stack).lower() or "react" in str(t.tech_stack).lower() for t in self.project_tasks.values()) else "Mobile: ",
                "description": "Set up state management store (Redux/Zustand)"
            },
            "src/theme": {
                "agent_type": AgentType.FRONTEND if any("nextjs" in str(t.tech_stack).lower() or "react" in str(t.tech_stack).lower() for t in self.project_tasks.values()) else AgentType.MOBILE,
                "title_prefix": "Frontend: " if any("nextjs" in str(t.tech_stack).lower() or "react" in str(t.tech_stack).lower() for t in self.project_tasks.values()) else "Mobile: ",
                "description": "Create theme configuration (colors, typography, spacing)"
            },
            "src/types": {
                "agent_type": AgentType.CODER,
                "title_prefix": "Backend: ",
                "description": "Create TypeScript type definitions"
            },
            "src/utils": {
                "agent_type": AgentType.CODER,
                "title_prefix": "Backend: ",
                "description": "Create utility functions and helpers"
            },
            "src/navigation": {
                "agent_type": AgentType.MOBILE,
                "title_prefix": "Mobile: ",
                "description": "Set up app navigation (StackNavigator, TabNavigator)"
            },
            "assets/images": {
                "agent_type": AgentType.FRONTEND if any("nextjs" in str(t.tech_stack).lower() or "react" in str(t.tech_stack).lower() for t in self.project_tasks.values()) else AgentType.MOBILE,
                "title_prefix": "Frontend: " if any("nextjs" in str(t.tech_stack).lower() or "react" in str(t.tech_stack).lower() for t in self.project_tasks.values()) else "Mobile: ",
                "description": "Set up assets/images directory structure"
            },
            "assets/fonts": {
                "agent_type": AgentType.FRONTEND if any("nextjs" in str(t.tech_stack).lower() or "react" in str(t.tech_stack).lower() for t in self.project_tasks.values()) else AgentType.MOBILE,
                "title_prefix": "Frontend: " if any("nextjs" in str(t.tech_stack).lower() or "react" in str(t.tech_stack).lower() for t in self.project_tasks.values()) else "Mobile: ",
                "description": "Set up assets/fonts directory structure"
            }
        }
        
        # Get tech stack from existing tasks (if any)
        tech_stack = []
        for task in self.project_tasks.values():
            if hasattr(task, 'tech_stack') and task.tech_stack:
                tech_stack.extend(task.tech_stack)
        tech_stack = list(set(tech_stack)) if tech_stack else ["TypeScript", "React"]  # Default
        
        # Create tasks for each missing component
        # QA_Engineer: missing_components is a list of dicts with keys: type, name, path, reason
        for component_info in missing_components:
            # Extract path from component dict (component_info is a dict, not a string)
            if isinstance(component_info, dict):
                component_path = component_info.get("path", "")
                component_name = component_info.get("name", component_path.split("/")[-1] if component_path else "unknown")
                component_type = component_info.get("type", "directory")
            else:
                # Fallback: if it's already a string (backward compatibility)
                component_path = str(component_info)
                component_name = component_path.split("/")[-1]
                component_type = "directory"
            
            if not component_path or component_path not in component_mapping:
                self.logger.warning(f"Unknown component path: {component_path}, skipping")
                continue
            
            mapping = component_mapping[component_path]
            agent_type = mapping["agent_type"]
            title_prefix = mapping["title_prefix"]
            description = mapping["description"]
            
            # Generate task title
            # Use component_name from dict if available, otherwise extract from path
            if component_name and component_name != "unknown":
                # Clean up component_name (remove " directory" or " file" suffix)
                clean_name = component_name.replace(" directory", "").replace(" file", "").replace("src/", "").replace("assets/", "")
                task_title = f"{title_prefix}{clean_name.title()}"
            else:
                task_title = f"{title_prefix}{component_path.split('/')[-1].title()}"
            
            # Determine dependencies (depend on implementation tasks)
            dependencies = [
                t.id for t in self.project_tasks.values()
                if t.agent_type in [AgentType.CODER, AgentType.INTEGRATION, AgentType.INFRASTRUCTURE]
                and t.status == TaskStatus.COMPLETED
            ]
            
            # Create task
            # QA_Engineer: Use sanitized component name for task ID
            clean_id_name = component_path.replace("/", "_").replace(".", "_").replace("-", "_")
            new_task = Task(
                id=f"task_{task_counter:04d}_dynamic_{component_type}_{clean_id_name}",
                title=task_title,
                description=f"{description} for component: {component_name} at path {component_path}",
                agent_type=agent_type,
                tech_stack=tech_stack,
                dependencies=dependencies,
                metadata={
                    "component_path": component_path,
                    "created_by": "qa_feedback",
                    "dynamic_task": True,
                    "component_type": component_type,
                    "component_name": component_name
                }
            )
            
            new_tasks.append(new_task)
            task_counter += 1
            
            self.logger.info(
                f"Created dynamic task for missing component: {component_name} at {component_path} "
                f"(Agent: {agent_type.value}, Title: {task_title})"
            )
        
        return new_tasks
    
    def _build_structure_blueprint(self, project_type: str, tech_stack: List[str], classification: Dict[str, Any]) -> Dict[str, Any]:
        """
        QA_Engineer: Build project structure blueprint based on project type and tech stack.
        
        This blueprint defines what directories and files should exist for a COMPLETE project.
        QA agent uses this blueprint to detect missing components.
        
        Args:
            project_type: Type of project (mobile_app, web_app, api_service, etc.)
            tech_stack: Technology stack list
            classification: Full objective classification from LLM
            
        Returns:
            Dictionary with expected structure:
            {
                "project_type": "mobile_app",
                "expected_directories": [
                    {"path": "src/components", "required": True, "description": "Reusable UI components"},
                    {"path": "src/screens", "required": True, "description": "Mobile app screens"},
                    ...
                ],
                "expected_files": [
                    {"path": "App.tsx", "required": True, "description": "Main app entry point"},
                    {"path": "package.json", "required": True, "description": "Dependencies and scripts"},
                    ...
                ],
                "tech_stack": ["React Native", "TypeScript"],
                "platforms": ["android", "ios"]
            }
        """
        blueprint = {
            "project_type": project_type,
            "tech_stack": tech_stack,
            "platforms": classification.get("platforms", []),
            "expected_directories": [],
            "expected_files": [],
            "key_features": classification.get("key_features", [])
        }
        
        tech_stack_str = " ".join(tech_stack).lower()
        
        # Build blueprint based on project type
        if project_type == "mobile_app" or "react native" in tech_stack_str or "expo" in tech_stack_str:
            blueprint["expected_directories"] = [
                {"path": "src/screens", "required": True, "description": "Mobile app screens/pages"},
                {"path": "src/components", "required": True, "description": "Reusable UI components"},
                {"path": "src/navigation", "required": True, "description": "Navigation setup (StackNavigator, TabNavigator)"},
                {"path": "src/services", "required": True, "description": "API clients, Firebase services, storage services"},
                {"path": "src/hooks", "required": True, "description": "Custom React hooks (useAuth, useApi, etc.)"},
                {"path": "src/store", "required": True, "description": "State management (Redux/Zustand setup)"},
                {"path": "src/theme", "required": True, "description": "Colors, typography, spacing configuration"},
                {"path": "src/types", "required": True, "description": "TypeScript type definitions"},
                {"path": "src/utils", "required": True, "description": "Helper functions, formatters, validators"},
                {"path": "assets/images", "required": False, "description": "Image assets"},
                {"path": "assets/fonts", "required": False, "description": "Font assets"}
            ]
            blueprint["expected_files"] = [
                {"path": "App.tsx", "required": True, "description": "Main app entry point"},
                {"path": "package.json", "required": True, "description": "Dependencies and scripts"},
                {"path": "tsconfig.json", "required": True, "description": "TypeScript configuration"},
                {"path": "android/app/src/main/AndroidManifest.xml", "required": False, "description": "Android manifest"},
                {"path": "ios/Info.plist", "required": False, "description": "iOS info plist"}
            ]
        
        elif project_type == "web_app" or "next.js" in tech_stack_str or ("react" in tech_stack_str and "next" in tech_stack_str):
            blueprint["expected_directories"] = [
                {"path": "src/pages", "required": True, "description": "Next.js route pages"},
                {"path": "src/components", "required": True, "description": "Reusable UI components"},
                {"path": "src/app/api", "required": False, "description": "Backend API endpoints"},
                {"path": "src/services", "required": True, "description": "API clients, external service integrations"},
                {"path": "src/hooks", "required": True, "description": "Custom React hooks"},
                {"path": "src/utils", "required": True, "description": "Helper functions"},
                {"path": "src/types", "required": True, "description": "TypeScript definitions"},
                {"path": "src/styles", "required": False, "description": "CSS/styled-components configuration"}
            ]
            blueprint["expected_files"] = [
                {"path": "package.json", "required": True, "description": "Dependencies and scripts"},
                {"path": "tsconfig.json", "required": True, "description": "TypeScript configuration"},
                {"path": "next.config.js", "required": False, "description": "Next.js configuration"}
            ]
        
        elif project_type == "api_service" or "fastapi" in tech_stack_str or ("python" in tech_stack_str and "api" in tech_stack_str):
            blueprint["expected_directories"] = [
                {"path": "src/api", "required": True, "description": "API route handlers"},
                {"path": "src/models", "required": True, "description": "Database models (SQLAlchemy)"},
                {"path": "src/schemas", "required": True, "description": "Pydantic schemas"},
                {"path": "src/services", "required": True, "description": "Business logic services"},
                {"path": "src/utils", "required": True, "description": "Helper functions"},
                {"path": "src/config", "required": True, "description": "Configuration management"},
                {"path": "src/middleware", "required": False, "description": "Custom middleware"}
            ]
            blueprint["expected_files"] = [
                {"path": "main.py", "required": True, "description": "FastAPI application entry point"},
                {"path": "requirements.txt", "required": True, "description": "Python dependencies"},
                {"path": ".env.example", "required": False, "description": "Environment variables template"}
            ]
        
        elif project_type == "saas_platform":
            # SaaS platforms typically have both frontend and backend
            blueprint["expected_directories"] = [
                {"path": "src/frontend/pages", "required": True, "description": "Frontend pages/routes"},
                {"path": "src/frontend/components", "required": True, "description": "Frontend UI components"},
                {"path": "src/frontend/services", "required": True, "description": "Frontend API clients"},
                {"path": "src/backend/api", "required": True, "description": "Backend API routes"},
                {"path": "src/backend/models", "required": True, "description": "Database models"},
                {"path": "src/backend/services", "required": True, "description": "Business logic services"},
                {"path": "src/shared/types", "required": True, "description": "Shared TypeScript types"},
                {"path": "src/shared/utils", "required": True, "description": "Shared utility functions"},
                {"path": "src/config", "required": True, "description": "Configuration files"},
                {"path": "src/migrations", "required": False, "description": "Database migrations"}
            ]
            blueprint["expected_files"] = [
                {"path": "package.json", "required": True, "description": "Dependencies and scripts"},
                {"path": "tsconfig.json", "required": True, "description": "TypeScript configuration"},
                {"path": "docker-compose.yml", "required": False, "description": "Docker Compose configuration"},
                {"path": ".env.example", "required": False, "description": "Environment variables template"}
            ]
        
        elif project_type == "data_pipeline":
            blueprint["expected_directories"] = [
                {"path": "src/pipelines", "required": True, "description": "Data pipeline definitions"},
                {"path": "src/operators", "required": True, "description": "Custom pipeline operators"},
                {"path": "src/transformations", "required": True, "description": "Data transformation logic"},
                {"path": "src/sources", "required": True, "description": "Data source connectors"},
                {"path": "src/sinks", "required": True, "description": "Data destination connectors"},
                {"path": "src/utils", "required": True, "description": "Utility functions"},
                {"path": "src/config", "required": True, "description": "Pipeline configuration"},
                {"path": "dags", "required": False, "description": "Airflow DAG definitions"},
                {"path": "data", "required": False, "description": "Sample data files"}
            ]
            blueprint["expected_files"] = [
                {"path": "requirements.txt", "required": True, "description": "Python dependencies"},
                {"path": "pipeline_config.yaml", "required": False, "description": "Pipeline configuration file"},
                {"path": ".env.example", "required": False, "description": "Environment variables template"}
            ]
        
        elif project_type == "microservice":
            blueprint["expected_directories"] = [
                {"path": "src/api", "required": True, "description": "API route handlers"},
                {"path": "src/models", "required": True, "description": "Data models"},
                {"path": "src/services", "required": True, "description": "Business logic services"},
                {"path": "src/repositories", "required": True, "description": "Data access layer"},
                {"path": "src/middleware", "required": False, "description": "Custom middleware"},
                {"path": "src/config", "required": True, "description": "Service configuration"},
                {"path": "src/utils", "required": True, "description": "Utility functions"},
                {"path": "deployments", "required": False, "description": "Deployment configurations"},
                {"path": "proto", "required": False, "description": "gRPC protocol definitions"}
            ]
            blueprint["expected_files"] = [
                {"path": "main.py", "required": True, "description": "Service entry point"},
                {"path": "requirements.txt", "required": True, "description": "Python dependencies"},
                {"path": "Dockerfile", "required": False, "description": "Docker container definition"},
                {"path": ".env.example", "required": False, "description": "Environment variables template"}
            ]
        
        elif project_type == "desktop_app":
            blueprint["expected_directories"] = [
                {"path": "src/main", "required": True, "description": "Main application code"},
                {"path": "src/renderer", "required": False, "description": "Renderer process (Electron)"},
                {"path": "src/components", "required": True, "description": "UI components"},
                {"path": "src/services", "required": True, "description": "Application services"},
                {"path": "src/utils", "required": True, "description": "Utility functions"},
                {"path": "src/types", "required": True, "description": "TypeScript type definitions"},
                {"path": "assets", "required": False, "description": "Application assets"},
                {"path": "resources", "required": False, "description": "Resource files"}
            ]
            blueprint["expected_files"] = [
                {"path": "package.json", "required": True, "description": "Dependencies and scripts"},
                {"path": "tsconfig.json", "required": True, "description": "TypeScript configuration"},
                {"path": "main.js", "required": False, "description": "Main process entry (Electron)"},
                {"path": "preload.js", "required": False, "description": "Preload script (Electron)"}
            ]
        
        elif project_type == "cli_tool":
            blueprint["expected_directories"] = [
                {"path": "src/commands", "required": True, "description": "CLI command implementations"},
                {"path": "src/utils", "required": True, "description": "Utility functions"},
                {"path": "src/config", "required": False, "description": "Configuration management"},
                {"path": "src/parsers", "required": False, "description": "Input parsers"},
                {"path": "src/formatters", "required": False, "description": "Output formatters"}
            ]
            blueprint["expected_files"] = [
                {"path": "main.py", "required": True, "description": "CLI entry point"},
                {"path": "requirements.txt", "required": True, "description": "Python dependencies"},
                {"path": "setup.py", "required": False, "description": "Package setup configuration"},
                {"path": "cli.py", "required": False, "description": "CLI interface definition"}
            ]
        
        elif project_type == "library":
            blueprint["expected_directories"] = [
                {"path": "src", "required": True, "description": "Library source code"},
                {"path": "src/types", "required": False, "description": "TypeScript type definitions"},
                {"path": "src/utils", "required": False, "description": "Utility functions"},
                {"path": "examples", "required": False, "description": "Usage examples"},
                {"path": "dist", "required": False, "description": "Built distribution files"}
            ]
            blueprint["expected_files"] = [
                {"path": "package.json", "required": True, "description": "Package configuration"},
                {"path": "tsconfig.json", "required": True, "description": "TypeScript configuration"},
                {"path": "README.md", "required": True, "description": "Library documentation"},
                {"path": "index.ts", "required": True, "description": "Main library entry point"},
                {"path": ".npmignore", "required": False, "description": "NPM ignore patterns"}
            ]
        
        elif project_type == "infrastructure":
            blueprint["expected_directories"] = [
                {"path": "terraform", "required": False, "description": "Terraform infrastructure code"},
                {"path": "kubernetes", "required": False, "description": "Kubernetes manifests"},
                {"path": "helm", "required": False, "description": "Helm charts"},
                {"path": "scripts", "required": True, "description": "Deployment scripts"},
                {"path": "config", "required": True, "description": "Infrastructure configuration"},
                {"path": "modules", "required": False, "description": "Reusable infrastructure modules"}
            ]
            blueprint["expected_files"] = [
                {"path": "main.tf", "required": False, "description": "Terraform main configuration"},
                {"path": "variables.tf", "required": False, "description": "Terraform variables"},
                {"path": "outputs.tf", "required": False, "description": "Terraform outputs"},
                {"path": "deploy.sh", "required": False, "description": "Deployment script"},
                {"path": ".terraform.lock.hcl", "required": False, "description": "Terraform lock file"}
            ]
        
        elif project_type == "blockchain_app":
            blueprint["expected_directories"] = [
                {"path": "contracts", "required": True, "description": "Smart contracts"},
                {"path": "src/frontend", "required": False, "description": "Frontend application"},
                {"path": "src/backend", "required": False, "description": "Backend services"},
                {"path": "scripts", "required": True, "description": "Deployment and migration scripts"},
                {"path": "tests", "required": True, "description": "Contract and application tests"},
                {"path": "migrations", "required": False, "description": "Contract migrations"},
                {"path": "artifacts", "required": False, "description": "Compiled contract artifacts"}
            ]
            blueprint["expected_files"] = [
                {"path": "hardhat.config.js", "required": False, "description": "Hardhat configuration"},
                {"path": "truffle-config.js", "required": False, "description": "Truffle configuration"},
                {"path": "package.json", "required": True, "description": "Dependencies and scripts"},
                {"path": ".env.example", "required": False, "description": "Environment variables template"}
            ]
        
        elif project_type == "ml_service":
            blueprint["expected_directories"] = [
                {"path": "src/models", "required": True, "description": "ML model definitions"},
                {"path": "src/training", "required": False, "description": "Model training scripts"},
                {"path": "src/inference", "required": True, "description": "Inference/prediction code"},
                {"path": "src/preprocessing", "required": True, "description": "Data preprocessing"},
                {"path": "src/features", "required": False, "description": "Feature engineering"},
                {"path": "data/raw", "required": False, "description": "Raw data files"},
                {"path": "data/processed", "required": False, "description": "Processed data files"},
                {"path": "notebooks", "required": False, "description": "Jupyter notebooks"},
                {"path": "src/utils", "required": True, "description": "Utility functions"},
                {"path": "models", "required": False, "description": "Saved model files"}
            ]
            blueprint["expected_files"] = [
                {"path": "requirements.txt", "required": True, "description": "Python dependencies"},
                {"path": "main.py", "required": True, "description": "Service entry point"},
                {"path": "train.py", "required": False, "description": "Training script"},
                {"path": "predict.py", "required": False, "description": "Prediction script"},
                {"path": ".env.example", "required": False, "description": "Environment variables template"}
            ]
        
        # Add common directories/files for all project types
        blueprint["expected_directories"].extend([
            {"path": "tests", "required": False, "description": "Test files"},
            {"path": "docs", "required": False, "description": "Documentation"}
        ])
        
        return blueprint
    
    def get_project_structure_blueprint(self) -> Optional[Dict[str, Any]]:
        """
        QA_Engineer: Get the project structure blueprint for QA agent.
        
        Returns:
            Dictionary with expected project structure, or None if not available
        """
        # Return the most recent blueprint (or merge all if multiple objectives)
        if self.project_structure_blueprint:
            # If multiple objectives, merge their blueprints
            if isinstance(self.project_structure_blueprint, dict) and len(self.project_structure_blueprint) > 0:
                # Return the first blueprint (or merge logic could be added)
                return list(self.project_structure_blueprint.values())[0]
        return None

