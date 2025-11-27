"""
Coder Agent - Implements coding tasks and generates code based on requirements.

Enhanced with LLM integration for adaptive code generation:
- Checks learned templates first (free!)
- Uses traditional templates (fast)
- Falls back to LLM for novel/complex tasks (adaptive)
- Learns from successful LLM generations (self-improving)
"""

from typing import Dict, Any, List, Optional
import os
import logging
import asyncio

from agents.base_agent import BaseAgent, AgentType, Task, TaskStatus
from agents.research_aware_mixin import ResearchAwareMixin
from utils.template_renderer import TemplateRenderer, get_renderer
from utils.project_layout import ProjectLayout, get_default_layout
from utils.name_sanitizer import sanitize_objective, sanitize_for_filename, sanitize_for_class_name
from utils.name_generator import generate_component_name, generate_concise_name

# LLM Integration (with graceful fallback if not available)
try:
    from utils.llm_service import get_llm_service, LLMService
    from utils.template_learning_engine import get_template_learning_engine, TemplateLearningEngine
    from utils.configuration_manager import get_configuration_manager, ConfigurationManager
    LLM_INTEGRATION_AVAILABLE = True
except ImportError as e:
    logging.warning(f"LLM integration not available: {e}")
    LLM_INTEGRATION_AVAILABLE = False


class CoderAgent(BaseAgent, ResearchAwareMixin):
    """
    Agent responsible for implementing code based on task requirements.
    
    Enhanced with hybrid generation strategy:
    1. Check learned templates (free, instant)
    2. Use traditional templates (fast, reliable)
    3. Generate with LLM (adaptive, handles anything)
    4. Learn from LLM successes (self-improving)
    """

    def __init__(self, agent_id: str = "coder_main", workspace_path: str = ".", 
                 project_layout: Optional[ProjectLayout] = None,
                 project_id: Optional[str] = None,
                 tenant_id: Optional[int] = None,
                 orchestrator: Optional[Any] = None):
        # CRITICAL: Pass workspace_path to super() to ensure BaseAgent validates it
        super().__init__(
            agent_id, 
            AgentType.CODER, 
            project_layout, 
            workspace_path=workspace_path,
            project_id=project_id, 
            tenant_id=tenant_id, 
            orchestrator=orchestrator
        )
        self.implemented_files: List[str] = []
        self.template_renderer = get_renderer()
        self.project_id = project_id
        
        # LLM Integration (Phase 1 - November 2025)
        self.use_llm = os.getenv("Q2O_USE_LLM", "true").lower() == "true"
        
        if LLM_INTEGRATION_AVAILABLE and self.use_llm:
            self.llm_service = get_llm_service()
            self.template_learning = get_template_learning_engine()
            self.config_manager = get_configuration_manager()
            self.llm_enabled = True
            logging.info("[OK] CoderAgent: LLM integration enabled (hybrid mode)")
        else:
            self.llm_service = None
            self.template_learning = None
            self.config_manager = None
            self.llm_enabled = False
            if self.use_llm:
                logging.warning("[WARNING] CoderAgent: LLM requested but not available, template-only mode")
            else:
                logging.info("[INFO] CoderAgent: LLM disabled, template-only mode")

    def process_task(self, task: Task) -> Task:
        """
        Process a coding task by generating and implementing code.
        
        Enhanced with LLM integration for hybrid generation.
        
        Args:
            task: The coding task to process
            
        Returns:
            The updated task
        """
        try:
            self.logger.info(f"Processing coding task: {task.title}")
            
            # Load research results from dependencies
            research_results = self.get_research_results(task)
            
            # Extract useful information from research
            if research_results:
                api_info = self.extract_api_info_from_research(research_results)
                task.metadata['research_context'] = api_info
                self.logger.info(f"Enriched task with research: {len(api_info.get('key_findings', []))} findings, "
                               f"{len(api_info.get('code_examples', []))} examples")
            
            # Extract task information
            description = task.description
            metadata = task.metadata
            complexity = metadata.get("complexity", "medium")
            objective = metadata.get("objective", task.title)
            tech_stack = task.tech_stack or []

            # Generate code structure (with tech stack awareness)
            code_structure = self._plan_code_structure(description, objective, complexity, tech_stack)
            
            # Implement the code (handles async if LLM enabled)
            if self.llm_enabled:
                # Run async implementation with proper event loop handling
                try:
                    # Check if we're already in async context
                    loop = asyncio.get_running_loop()
                    # Already in async - use run_coroutine_threadsafe or nest_asyncio
                    # For now, fall back to sync mode to avoid conflicts
                    self.logger.warning("Already in async context, using template-only mode for this call")
                    implemented_files = self._implement_code(code_structure, task)
                except RuntimeError:
                    # No running loop - safe to create new one
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        implemented_files = loop.run_until_complete(
                            self._implement_code_async(code_structure, task)
                        )
                        # CRITICAL: Wait for all pending tasks to complete before closing loop
                        pending = asyncio.all_tasks(loop)
                        if pending:
                            loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                    finally:
                        # Only close loop after all tasks are complete
                        try:
                            pending = asyncio.all_tasks(loop)
                            for task in pending:
                                task.cancel()
                            if pending:
                                loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                        except Exception:
                            pass
                        finally:
                            loop.close()
            else:
                # Traditional synchronous implementation
                implemented_files = self._implement_code(code_structure, task)
            
            # Update task metadata
            task.metadata["implemented_files"] = implemented_files
            task.metadata["code_structure"] = code_structure
            task.result = {
                "files_created": implemented_files,
                "complexity": complexity,
                "status": "completed"
            }

            self.complete_task(task.id, task.result)
            self.logger.info(f"Completed coding task {task.id}")
            
        except Exception as e:
            error_msg = f"Error processing coding task: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            self.fail_task(task.id, error_msg)
            
        return task

    def _plan_code_structure(self, description: str, objective: str, complexity: str, tech_stack: List[str] = None) -> Dict[str, Any]:
        """
        Plan the code structure based on task requirements and tech stack.
        
        Args:
            description: Task description
            objective: Objective to achieve
            complexity: Complexity level
            tech_stack: Technology stack (from task)
            
        Returns:
            Dictionary describing the code structure
        """
        tech_stack = tech_stack or []
        description_lower = description.lower()
        
        # Analyze requirements and determine structure
        structure = {
            "objective": objective,
            "complexity": complexity,
            "tech_stack": tech_stack,
            "files": [],
            "dependencies": [],
            "main_components": []
        }

        # Technology-aware file planning
        # For Python/FastAPI projects
        if "python" in tech_stack or not tech_stack:
            if "api" in description_lower or "endpoint" in description_lower:
                structure["files"].append({
                    "type": "fastapi",
                    "path": os.path.join(self.project_layout.api_app_dir, "endpoints.py"),
                    "description": "FastAPI endpoints implementation"
                })
            
            if "model" in description_lower or "database" in description_lower:
                structure["files"].append({
                    "type": "model",
                    "path": os.path.join(self.project_layout.api_app_dir, "models.py"),
                    "description": "SQLAlchemy data models"
                })

            if "service" in description_lower or "business logic" in description_lower:
                structure["files"].append({
                    "type": "service",
                    "path": os.path.join(self.project_layout.api_app_dir, "services.py"),
                    "description": "Business logic service"
                })
            
            if "search" in description_lower:
                structure["files"].append({
                    "type": "api",
                    "path": os.path.join(self.project_layout.api_app_dir, "search.py"),
                    "description": "Search endpoints"
                })
            
            if "mapping" in description_lower:
                structure["files"].append({
                    "type": "api",
                    "path": os.path.join(self.project_layout.api_app_dir, "mappings.py"),
                    "description": "Mappings endpoints"
                })
            
            if "sse" in description_lower or "stream" in description_lower:
                structure["files"].append({
                    "type": "api",
                    "path": os.path.join(self.project_layout.api_app_dir, "sse_sign.py"),
                    "description": "SSE signing"
                })
                structure["files"].append({
                    "type": "api",
                    "path": os.path.join(self.project_layout.api_app_dir, "ops_stream.py"),
                    "description": "SSE stream endpoint"
                })
            
            if "ops" in description_lower or "admin" in description_lower:
                structure["files"].append({
                    "type": "api",
                    "path": os.path.join(self.project_layout.api_app_dir, "ops_admin.py"),
                    "description": "Admin operations endpoints"
                })
            
            if "audit" in description_lower:
                structure["files"].append({
                    "type": "api",
                    "path": os.path.join(self.project_layout.api_app_dir, "audit.py"),
                    "description": "Audit logging"
                })
            
            if "entities" in description_lower or "backfill" in description_lower:
                structure["files"].append({
                    "type": "api",
                    "path": os.path.join(self.project_layout.api_app_dir, "entities.py"),
                    "description": "Entity sync endpoints"
                })

        # For Next.js/React projects
        if "nextjs" in tech_stack:
            if "page" in description_lower:
                # Generate concise name first, then sanitize
                concise_name = generate_concise_name(objective, max_length=40)
                page_name = sanitize_for_filename(concise_name)
                structure["files"].append({
                    "type": "page",
                    "path": os.path.join(self.project_layout.web_pages_dir, f"{page_name}.tsx"),
                    "description": f"Next.js page for {objective}"
                })
            
            if "component" in description_lower:
                # Generate concise name first, then sanitize
                concise_name = generate_concise_name(objective, max_length=40)
                component_name = sanitize_for_class_name(concise_name)
                structure["files"].append({
                    "type": "component",
                    "path": os.path.join(self.project_layout.web_components_dir, f"{component_name}.tsx"),
                    "description": f"React component for {objective}"
                })

        # If no specific files identified, create a generic implementation
        if not structure["files"]:
            # Generate concise name first, then sanitize
            concise_name = generate_concise_name(objective, max_length=40)
            filename = sanitize_for_filename(concise_name)
            if "python" in tech_stack:
                structure["files"].append({
                    "type": "generic",
                    "path": os.path.join(self.project_layout.api_app_dir, f"{filename}.py"),
                    "description": f"Implementation for {objective}"
                })
            else:
                structure["files"].append({
                    "type": "generic",
                    "path": f"src/{filename}.py",
                    "description": f"Implementation for {objective}"
                })

        return structure

    async def _implement_code_async(self, code_structure: Dict[str, Any], task: Task) -> List[str]:
        """
        Implement code using HYBRID approach with LLM integration.
        
        Strategy (in order):
        1. Check learned templates (FREE, instant)
        2. Use traditional templates (fast, reliable)
        3. Generate with LLM (adaptive, handles anything)
        4. Learn from successful LLM generations
        
        Args:
            code_structure: Planned code structure
            task: The task being implemented
            
        Returns:
            List of file paths created
        """
        implemented_files = []
        objective = code_structure["objective"]
        files_to_create = code_structure["files"]
        tech_stack = task.tech_stack or []

        for file_info in files_to_create:
            file_path = file_info["path"]
            file_type = file_info["type"]
            full_path = os.path.join(self.workspace_path, file_path)
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            # HYBRID GENERATION: Try multiple strategies
            code_content = await self._generate_code_hybrid(
                file_type, file_info, objective, task, tech_stack
            )
            
            # Write file using safe file writer (HARD GUARANTEE)
            try:
                self.safe_write_file(file_path, code_content)
                implemented_files.append(file_path)
                self.logger.info(f"[OK] Created file: {file_path}")
            except Exception as e:
                self.logger.error(f"[ERROR] Failed to write file {file_path}: {e}")
                raise

        return implemented_files
    
    async def _generate_code_hybrid(
        self,
        file_type: str,
        file_info: Dict[str, Any],
        objective: str,
        task: Task,
        tech_stack: List[str]
    ) -> str:
        """
        HYBRID code generation with learning.
        
        Flow:
        1. Check learned templates (from previous LLM generations)
        2. Use traditional templates (built-in)
        3. Generate with LLM (if enabled and needed)
        4. Learn from successful LLM generation
        
        Args:
            file_type: Type of file (api, model, service, etc.)
            file_info: File metadata
            objective: What we're building
            task: The task
            tech_stack: Technologies being used
        
        Returns:
            Generated code content
        """
        task_desc = f"{file_type}: {file_info.get('description', objective)}"
        
        # STEP 1: Check learned templates (FREE!)
        if self.template_learning:
            learned_template = self.template_learning.find_similar_template(
                task_desc, tech_stack
            )
            if learned_template:
                self.logger.info(f"[TEMPLATE] Using learned template: {learned_template.name} (saved ${0.52:.2f}!)")
                self.template_learning.increment_usage(learned_template.template_id)
                return learned_template.template_content
        
        # STEP 2: Try traditional template (FAST)
        try:
            code_content = self._generate_code_content(file_type, file_info, objective, task)
            self.logger.info(f"[TEMPLATE] Used traditional template for {file_type}")
            return code_content
        except Exception as template_error:
            self.logger.debug(f"Traditional template not available: {template_error}")
        
        # STEP 3: Generate with LLM (ADAPTIVE)
        if not self.llm_service:
            # No LLM available and no template - fail
            raise ValueError(f"No template for {file_type} and LLM not available")
        
        self.logger.info(f"[LLM] Generating with LLM for {file_type} (no template available)")
        
        # Get configuration for this task
        system_prompt, user_prompt = self.config_manager.get_prompt_for_task(
            self.project_id, AgentType.CODER, task_desc, tech_stack
        )
        
        # Get research context
        research_context = task.metadata.get('research_context')
        
        # Generate with LLM
        response = await self.llm_service.generate_code(
            task_description=task_desc,
            tech_stack=tech_stack,
            research_context=research_context
        )
        
        if not response.success:
            raise ValueError(f"LLM generation failed: {response.error}")
        
        code_content = response.content
        
        # Log usage
        if response.usage:
            self.logger.info(
                f"[COST] LLM cost: ${response.usage.total_cost:.4f} "
                f"({response.usage.input_tokens}+{response.usage.output_tokens} tokens, "
                f"{response.usage.duration_seconds:.2f}s)"
            )
        
        # CRITICAL: Track LLM usage for dashboard
        self.track_llm_usage(task, response)
        
        # STEP 4: Learn from successful generation (for future cost savings)
        if self.template_learning and response.success:
            # TODO: Add quality scoring
            quality_score = 95  # Placeholder - will add proper validation
            
            template_id = await self.template_learning.learn_from_generation(
                task_description=task_desc,
                tech_stack=tech_stack,
                generated_code=code_content,
                source_llm=response.provider,
                quality_score=quality_score,
                metadata={
                    "file_type": file_type,
                    "objective": objective,
                    "task_id": task.id
                }
            )
            
            if template_id:
                self.logger.info(f"[LEARNED] Learned new template: {template_id} (future similar tasks will be FREE!)")
        
        return code_content
    
    def _implement_code(self, code_structure: Dict[str, Any], task: Task) -> List[str]:
        """
        Implement code based on the planned structure (TRADITIONAL MODE).
        
        This is the original implementation without LLM integration.
        Used when LLM is disabled or not available.
        
        Args:
            code_structure: Planned code structure
            task: The task being implemented
            
        Returns:
            List of file paths created
        """
        implemented_files = []
        objective = code_structure["objective"]
        files_to_create = code_structure["files"]

        for file_info in files_to_create:
            file_path = file_info["path"]
            file_type = file_info["type"]
            full_path = os.path.join(self.workspace_path, file_path)
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            # Generate code based on type
            code_content = self._generate_code_content(file_type, file_info, objective, task)
            
            # Write file
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(code_content)
            
            implemented_files.append(file_path)
            self.logger.info(f"Created file: {file_path}")

        return implemented_files

    def _generate_code_content(self, file_type: str, file_info: Dict[str, Any], 
                              objective: str, task: Task) -> str:
        """
        Generate code content based on file type.
        
        Args:
            file_type: Type of file to generate
            file_info: File information
            objective: Objective being implemented
            task: The task
            
        Returns:
            Generated code content as string
        """
        if file_type == "api":
            return self._generate_api_code(objective, task)
        elif file_type == "model":
            return self._generate_model_code(objective, task)
        elif file_type == "service":
            return self._generate_service_code(objective, task)
        elif file_type == "component":
            return self._generate_component_code(objective, task)
        else:
            return self._generate_generic_code(objective, task)

    def _generate_api_code(self, objective: str, task: Task) -> str:
        """Generate FastAPI endpoint code using template."""
        # Generate concise name first, then sanitize
        concise_name = generate_concise_name(objective, max_length=40)
        sanitized = sanitize_objective(concise_name)
        module_name = sanitized['filename']
        endpoint_path = f"/api/{module_name}"
        class_name = sanitized['class_name']
        
        # Use template if available, otherwise fallback to inline generation
        if self.template_renderer.template_exists("api/fastapi_endpoint.j2"):
            context = {
                "objective": objective,
                "module_name": module_name,
                "endpoint_path": endpoint_path,
                "class_name": class_name
            }
            return self.template_renderer.render("api/fastapi_endpoint.j2", context)
        
        # Fallback to inline generation (for backward compatibility)
        return self._generate_api_code_inline(objective, module_name, endpoint_path, class_name)
    
    def _generate_api_code_inline(self, objective: str, module_name: str, endpoint_path: str, class_name: str) -> str:
        """Generate FastAPI endpoint code inline (fallback)."""
        
        return f'''"""
FastAPI endpoints for {objective}
Generated by CoderAgent
"""

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(prefix="{endpoint_path}", tags=["{module_name}"])
security = HTTPBearer()


class {class_name}Request(BaseModel):
    """Request model for {objective}"""
    pass


class {class_name}Response(BaseModel):
    """Response model for {objective}"""
    status: str = Field(..., description="Operation status")
    message: Optional[str] = Field(None, description="Status message")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


@router.get("/", response_model={class_name}Response, status_code=status.HTTP_200_OK)
async def get_{module_name}(
    skip: int = 0,
    limit: int = 100,
    token: str = Depends(security)
) -> {class_name}Response:
    """
    GET endpoint for {objective}
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        token: Bearer token for authentication
        
    Returns:
        Response with {objective} data
    """
    try:
        logger.info(f"GET request for {objective} - skip={{skip}}, limit={{limit}}")
        return {class_name}Response(
            status="success",
            message="GET request for {objective}",
            data={{"skip": skip, "limit": limit}}
        )
    except Exception as e:
        logger.error(f"Error in get_{module_name}: {{str(e)}}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {{str(e)}}"
        )


@router.post("/", response_model={class_name}Response, status_code=status.HTTP_201_CREATED)
async def create_{module_name}(
    request: {class_name}Request,
    token: str = Depends(security)
) -> {class_name}Response:
    """
    POST endpoint for {objective}
    
    Args:
        request: Request body with {objective} data
        token: Bearer token for authentication
        
    Returns:
        Response with created {objective} data
    """
    try:
        logger.info(f"POST request received for {objective}: {{request}}")
        return {class_name}Response(
            status="success",
            message="POST request for {objective} processed",
            data={{"request": request.dict()}}
        )
    except Exception as e:
        logger.error(f"Error in create_{module_name}: {{str(e)}}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {{str(e)}}"
        )


@router.put("/{{item_id}}", response_model={class_name}Response, status_code=status.HTTP_200_OK)
async def update_{module_name}(
    item_id: int,
    request: {class_name}Request,
    token: str = Depends(security)
) -> {class_name}Response:
    """
    PUT endpoint for updating {objective}
    
    Args:
        item_id: ID of the item to update
        request: Request body with updated data
        token: Bearer token for authentication
        
    Returns:
        Response with updated {objective} data
    """
    try:
        logger.info(f"PUT request received for {objective} {{item_id}}: {{request}}")
        return {class_name}Response(
            status="success",
            message=f"{objective} {{item_id}} updated",
            data={{"id": item_id, "request": request.dict()}}
        )
    except Exception as e:
        logger.error(f"Error in update_{module_name}: {{str(e)}}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {{str(e)}}"
        )


@router.delete("/{{item_id}}", response_model={class_name}Response, status_code=status.HTTP_200_OK)
async def delete_{module_name}(
    item_id: int,
    token: str = Depends(security)
) -> {class_name}Response:
    """
    DELETE endpoint for {objective}
    
    Args:
        item_id: ID of the item to delete
        token: Bearer token for authentication
        
    Returns:
        Response confirming deletion
    """
    try:
        logger.info(f"DELETE request received for {objective} {{item_id}}")
        return {class_name}Response(
            status="success",
            message=f"{objective} {{item_id}} deleted",
            data={{"id": item_id}}
        )
    except Exception as e:
        logger.error(f"Error in delete_{module_name}: {{str(e)}}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {{str(e)}}"
        )
'''

    def _generate_model_code(self, objective: str, task: Task) -> str:
        """Generate SQLAlchemy data model code using template."""
        # Generate concise name first, then sanitize
        concise_name = generate_concise_name(objective, max_length=40)
        sanitized = sanitize_objective(concise_name)
        class_name = sanitized['class_name']
        table_name = sanitized['filename']
        
        # Use template if available
        if self.template_renderer.template_exists("api/sqlalchemy_model.j2"):
            context = {
                "objective": objective,
                "class_name": class_name,
                "table_name": table_name
            }
            return self.template_renderer.render("api/sqlalchemy_model.j2", context)
        
        # Fallback to inline generation
        return self._generate_model_code_inline(objective, class_name, table_name)
    
    def _generate_model_code_inline(self, objective: str, class_name: str, table_name: str) -> str:
        """Generate SQLAlchemy data model code inline (fallback)."""
        return f'''"""
SQLAlchemy data models for {objective}
Generated by CoderAgent
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Dict, Any

Base = declarative_base()


class {class_name}(Base):
    """
    SQLAlchemy model representing {objective}
    """
    __tablename__ = '{table_name}'

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String(255), nullable=False, index=True)  # Multi-tenant support
    name = Column(String(255), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f'<{class_name}(id={{self.id}}, name={{self.name}})>'

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {{
            'id': self.id,
            'tenant_id': self.tenant_id,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """Create model instance from dictionary."""
        return cls(
            tenant_id=data.get('tenant_id'),
            name=data.get('name'),
            description=data.get('description')
        )
'''

    def _generate_service_code(self, objective: str, task: Task) -> str:
        """Generate service/business logic code."""
        # Generate concise name first, then sanitize
        concise_name = generate_concise_name(objective, max_length=40)
        sanitized = sanitize_objective(concise_name)
        class_name = sanitized['class_name'] + "Service"
        method_name = sanitized['function_name']
        return f'''"""
Service layer for {objective}
Generated by CoderAgent
"""

from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class {class_name}:
    """
    Service class for handling {objective} business logic
    """

    def __init__(self):
        """Initialize the service."""
        self.logger = logger

    def {method_name}(self, *args, **kwargs) -> Dict[str, Any]:
        """
        Main method for {objective}
        
        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Dictionary with result
        """
        try:
            self.logger.info(f"Processing {objective}")
            # Implement business logic here
            result = {{"status": "success", "message": f"{objective} processed"}}
            return result
        except Exception as e:
            self.logger.error(f"Error in {method_name}: {{str(e)}}")
            raise

    def validate(self, data: Dict[str, Any]) -> bool:
        """
        Validate input data.
        
        Args:
            data: Data to validate
            
        Returns:
            True if valid
        """
        # Implement validation logic
        return True
'''

    def _generate_component_code(self, objective: str, task: Task) -> str:
        """Generate UI component code."""
        # Generate concise name first, then sanitize
        concise_name = generate_concise_name(objective, max_length=40)
        sanitized = sanitize_objective(concise_name)
        class_name = sanitized['class_name'] + "Component"
        return f'''"""
UI Component for {objective}
Generated by CoderAgent
"""

from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class {class_name}:
    """
    Component class for {objective}
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the component.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {{}}
        self.logger = logger

    def render(self) -> str:
        """
        Render the component.
        
        Returns:
            Rendered HTML/UI string
        """
        # Implement rendering logic
        return f"<div class='{class_name.lower()}'>{objective}</div>"

    def update(self, data: Dict[str, Any]) -> None:
        """
        Update component state.
        
        Args:
            data: Data to update component with
        """
        self.logger.info(f"Updating {class_name} with data: {{data}}")
        # Implement update logic
'''

    def _generate_generic_code(self, objective: str, task: Task) -> str:
        """Generate generic implementation code."""
        # Generate concise name first, then sanitize
        concise_name = generate_concise_name(objective, max_length=40)
        sanitized = sanitize_objective(concise_name)
        module_name = sanitized['filename']
        class_name = sanitized['class_name']
        display_name = sanitized['display_name']
        
        # Get research context if available
        research_context = task.metadata.get('research_context', {})
        api_docs = research_context.get('documentation_urls', [])
        
        # Add API documentation comments if available
        doc_comment = ""
        if api_docs:
            doc_comment = f"\n\nAPI Documentation:\n" + "\n".join(f"- {url}" for url in api_docs[:3])
        
        return f'''"""
Implementation for {display_name}.

Generated by CoderAgent - Quick2Odoo Multi-Agent System{doc_comment}

This module provides the implementation for {display_name}.
All type hints, error handling, and logging are included for production use.
"""

from typing import Dict, Any
import logging

# Configure logging for standalone use
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class {class_name}:
    """
    Implementation class for {display_name}.

    This class handles the business logic for {display_name}.
    Includes comprehensive error handling and logging.

    Attributes:
        logger: Logger instance for this class
    """

    def __init__(self) -> None:
        """Initialize the implementation."""
        self.logger = logger
        self.logger.info("Initialized {class_name}")

    def execute(self, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute the main functionality.

        Args:
            data: Optional input data dictionary containing execution parameters

        Returns:
            Dict[str, Any]: Result dictionary with the following structure:
                - status (str): 'success' or 'error'
                - message (str): Human-readable result message
                - data (dict): Output data or empty dict

        Raises:
            Exception: Re-raises any exceptions after logging
        """
        try:
            self.logger.info("Executing {display_name}")

            # Validate input data
            if data is not None and not isinstance(data, dict):
                raise ValueError("Data parameter must be a dictionary")

            # TODO: Implement functionality here
            # Add your business logic below
            # Example:
            #   result_data = self._process_data(data)
            #   return {{"status": "success", "data": result_data}}

            return {{
                "status": "success",
                "message": "{display_name} executed successfully",
                "data": data or {{}}
            }}

        except Exception as e:
            self.logger.error("Error executing {display_name}: %s", str(e), exc_info=True)
            raise


def main() -> Dict[str, Any]:
    """
    Main function for testing.

    Returns:
        Dict[str, Any]: Execution result dictionary
    """
    implementation = {class_name}()
    result = implementation.execute()
    print(result)
    return result


if __name__ == "__main__":
    main()
'''

