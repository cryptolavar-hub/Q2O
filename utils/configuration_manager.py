"""
Configuration Manager - 3-Level Cascading Configuration System.

Manages System → Project → Agent configuration hierarchy for:
- LLM provider selection
- Prompt templates
- Budget allocation
- Quality thresholds

This enables maximum flexibility for IT consultants to customize per client.
"""

from typing import Dict, Any, Optional, List, Tuple
from enum import Enum
import json
import os
import logging
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime
from agents.base_agent import AgentType

# Import after ensuring it exists
try:
    from utils.llm_service import LLMProvider
except ImportError:
    # Fallback if not yet available
    class LLMProvider(str, Enum):
        GEMINI = "gemini"
        OPENAI = "openai"
        ANTHROPIC = "anthropic"


@dataclass
class LLMConfig:
    """LLM configuration at any level (system/project/agent)."""
    provider: Optional[str] = None  # gemini | openai | anthropic
    model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    system_prompt: Optional[str] = None
    custom_instructions: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dict, excluding None values."""
        return {k: v for k, v in asdict(self).items() if v is not None}
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'LLMConfig':
        """Create from dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})


@dataclass
class ProjectConfig:
    """Project-level configuration."""
    project_id: str
    project_name: str
    client_name: str
    llm_config: LLMConfig
    agent_overrides: Dict[str, LLMConfig]  # AgentType -> LLMConfig
    budget_limit: Optional[float] = None
    quality_threshold: Optional[int] = None
    metadata: Optional[Dict] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "project_id": self.project_id,
            "project_name": self.project_name,
            "client_name": self.client_name,
            "llm_config": self.llm_config.to_dict(),
            "agent_overrides": {k: v.to_dict() for k, v in self.agent_overrides.items()},
            "budget_limit": self.budget_limit,
            "quality_threshold": self.quality_threshold,
            "metadata": self.metadata or {}
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ProjectConfig':
        """Create from dictionary."""
        return cls(
            project_id=data['project_id'],
            project_name=data['project_name'],
            client_name=data['client_name'],
            llm_config=LLMConfig.from_dict(data['llm_config']),
            agent_overrides={
                k: LLMConfig.from_dict(v) 
                for k, v in data.get('agent_overrides', {}).items()
            },
            budget_limit=data.get('budget_limit'),
            quality_threshold=data.get('quality_threshold'),
            metadata=data.get('metadata', {})
        )


class ConfigurationManager:
    """
    Manages 3-level cascading configuration: System → Project → Agent.
    
    Configuration precedence (highest to lowest):
    1. Agent-level (most specific)
    2. Project-level (client-specific)
    3. System-level (global defaults)
    
    Example:
        System: Gemini Pro for all agents
        Project ACME: GPT-4 for all agents (override)
        ACME CoderAgent: GPT-4 (inherited)
        ACME ResearcherAgent: Gemini Pro (override - save $$$)
    """
    
    def __init__(self, config_dir: str = "config", use_database: bool = True):
        """
        Initialize configuration manager.
        
        NEW: Checks PostgreSQL database first for scalability (multi-host).
        Falls back to file-based config if database unavailable.
        
        Args:
            config_dir: Directory to store configuration files (fallback)
            use_database: Try to use PostgreSQL first (default: True)
        """
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        
        # Configuration files (fallback storage)
        self.system_config_file = self.config_dir / "system_llm_config.json"
        self.projects_config_file = self.config_dir / "projects_llm_config.json"
        
        # Database availability
        self.use_database = use_database and self._check_database_available()
        
        if self.use_database:
            logging.info("✅ Using PostgreSQL for configuration (scalable!)")
        else:
            logging.info("ℹ️  Using file-based configuration (fallback)")
        
        # Load configurations
        self.system_config = self._load_system_config()
        self.projects = self._load_projects_config()
        
        logging.info("✅ ConfigurationManager initialized")
    
    def _check_database_available(self) -> bool:
        """
        Check if PostgreSQL database is available for configuration storage.
        
        NOTE: Imports are LAZY (inside method) to avoid circular imports.
        """
        try:
            # Lazy imports to avoid circular dependency
            import sys
            from pathlib import Path
            
            # Try to import database components
            from addon_portal.api.core.db import get_db
            from addon_portal.api.models.llm_config import LLMSystemConfig
            
            # Try to query database
            db = next(get_db())
            result = db.query(LLMSystemConfig).first()
            db.close()
            
            return True
        except ImportError as e:
            logging.debug(f"Database models not available: {e}")
            return False
        except Exception as e:
            logging.debug(f"Database not available for configuration: {e}")
            return False
    
    def _load_system_config(self) -> LLMConfig:
        """Load system-level configuration."""
        if self.system_config_file.exists():
            try:
                with open(self.system_config_file, 'r') as f:
                    data = json.load(f)
                    return LLMConfig.from_dict(data)
            except Exception as e:
                logging.error(f"Error loading system config: {e}")
        
        # Default system configuration from environment
        return LLMConfig(
            provider=os.getenv("Q2O_LLM_PRIMARY", "gemini"),
            model=None,  # Will use provider-specific default
            temperature=float(os.getenv("Q2O_LLM_TEMPERATURE", "0.7")),
            max_tokens=int(os.getenv("Q2O_LLM_MAX_TOKENS", "4096")),
            system_prompt=self._get_default_system_prompt(),
            custom_instructions=""
        )
    
    def _get_default_system_prompt(self) -> str:
        """
        Get default system prompt for code generation.
        
        Reads from .env (Q2O_LLM_SYSTEM_PROMPT) or uses fallback.
        """
        # Try to load from .env first
        env_prompt = os.getenv("Q2O_LLM_SYSTEM_PROMPT")
        if env_prompt:
            return env_prompt
        
        # Fallback to hardcoded prompt
        return """You are an expert software developer.

Generate production-quality code with:
✅ Complete type hints (mypy strict mode)
✅ Comprehensive docstrings (Google style)
✅ Proper error handling (specific exceptions)
✅ Input validation (Pydantic where applicable)
✅ Security best practices
✅ Structured logging
✅ Best practices for the technology stack

Output ONLY the code - no explanations, no markdown."""
    
    def _load_projects_config(self) -> Dict[str, ProjectConfig]:
        """Load all project configurations."""
        if self.projects_config_file.exists():
            try:
                with open(self.projects_config_file, 'r') as f:
                    data = json.load(f)
                    return {
                        project_id: ProjectConfig.from_dict(project_data)
                        for project_id, project_data in data.items()
                    }
            except Exception as e:
                logging.error(f"Error loading projects config: {e}")
        
        return {}
    
    def save_system_config(self, config: LLMConfig):
        """Save system-level configuration."""
        with open(self.system_config_file, 'w') as f:
            json.dump(config.to_dict(), f, indent=2)
        
        self.system_config = config
        logging.info("💾 System configuration saved")
    
    def save_project_config(self, project: ProjectConfig):
        """Save project-level configuration."""
        self.projects[project.project_id] = project
        
        # Save all projects
        projects_data = {
            project_id: project.to_dict()
            for project_id, project in self.projects.items()
        }
        
        with open(self.projects_config_file, 'w') as f:
            json.dump(projects_data, f, indent=2)
        
        logging.info(f"💾 Project configuration saved: {project.project_name}")
    
    def get_llm_provider_for_task(
        self,
        project_id: Optional[str],
        agent_type: AgentType
    ) -> str:
        """
        Get LLM provider for a specific task using cascading logic.
        
        Precedence: Agent-level → Project-level → System-level
        
        Args:
            project_id: Project identifier (None for system default)
            agent_type: Type of agent requesting LLM
        
        Returns:
            Provider name (gemini, openai, anthropic)
        """
        # Try agent-level override
        if project_id and project_id in self.projects:
            project = self.projects[project_id]
            agent_key = agent_type.value
            
            if agent_key in project.agent_overrides:
                agent_config = project.agent_overrides[agent_key]
                if agent_config.provider:
                    logging.debug(f"Using agent-level provider: {agent_config.provider} ({agent_type.value})")
                    return agent_config.provider
            
            # Try project-level
            if project.llm_config.provider:
                logging.debug(f"Using project-level provider: {project.llm_config.provider} ({project.project_name})")
                return project.llm_config.provider
        
        # Fall back to system-level
        provider = self.system_config.provider or "gemini"
        logging.debug(f"Using system-level provider: {provider}")
        return provider
    
    def get_prompt_for_task(
        self,
        project_id: Optional[str],
        agent_type: AgentType,
        task_description: str,
        tech_stack: List[str]
    ) -> Tuple[str, str]:
        """
        Get system and user prompts for a task using cascading logic.
        
        Merges prompts from all levels: System + Agent + Project
        Priority: Agent-specific (.env) → Project-specific → System
        
        Args:
            project_id: Project identifier
            agent_type: Type of agent
            task_description: What to build
            tech_stack: Technologies
        
        Returns:
            (system_prompt, user_prompt) tuple
        """
        # Start with system-level prompt
        system_prompt = self.system_config.system_prompt or self._get_default_system_prompt()
        custom_instructions = []
        
        # Check for agent-specific prompt in .env (HIGHEST PRIORITY for agent)
        agent_env_key = f"Q2O_LLM_PROMPT_{agent_type.value.upper()}"
        agent_prompt_from_env = os.getenv(agent_env_key)
        if agent_prompt_from_env:
            # Replace system prompt with agent-specific one from .env
            system_prompt = agent_prompt_from_env
            logging.debug(f"Using agent-specific prompt from .env: {agent_env_key}")
        
        # Add system-level custom instructions
        if self.system_config.custom_instructions:
            custom_instructions.append(self.system_config.custom_instructions)
        
        # Add project-level customizations from .env
        if project_id:
            project_env_key = f"Q2O_LLM_PROMPT_PROJECT_{project_id.upper()}"
            project_prompt_from_env = os.getenv(project_env_key)
            if project_prompt_from_env:
                custom_instructions.append(f"\n📋 Project-Specific Requirements:\n{project_prompt_from_env}")
        
        # Add project-level customizations from config file
        if project_id and project_id in self.projects:
            project = self.projects[project_id]
            
            if project.llm_config.custom_instructions:
                custom_instructions.append(f"\n📋 {project.client_name} Requirements:\n{project.llm_config.custom_instructions}")
            
            # Add agent-level customizations from project config
            agent_key = agent_type.value
            if agent_key in project.agent_overrides:
                agent_config = project.agent_overrides[agent_key]
                if agent_config.custom_instructions:
                    custom_instructions.append(f"\n🤖 {agent_type.value} Specific:\n{agent_config.custom_instructions}")
        
        # Merge custom instructions into system prompt
        if custom_instructions:
            system_prompt += "\n\n" + "\n".join(custom_instructions)
        
        # Build user prompt
        user_prompt = f"""Task: {task_description}

Technology Stack: {', '.join(tech_stack)}

Generate complete, production-ready implementation."""
        
        return system_prompt, user_prompt
    
    def get_temperature_for_task(
        self,
        project_id: Optional[str],
        agent_type: AgentType
    ) -> float:
        """Get temperature setting using cascading logic."""
        # Try agent-level
        if project_id and project_id in self.projects:
            project = self.projects[project_id]
            agent_key = agent_type.value
            
            if agent_key in project.agent_overrides:
                temp = project.agent_overrides[agent_key].temperature
                if temp is not None:
                    return temp
            
            # Try project-level
            if project.llm_config.temperature is not None:
                return project.llm_config.temperature
        
        # System-level
        return self.system_config.temperature or 0.7
    
    def get_quality_threshold(self, project_id: Optional[str]) -> int:
        """Get quality threshold for a project."""
        if project_id and project_id in self.projects:
            project = self.projects[project_id]
            if project.quality_threshold is not None:
                return project.quality_threshold
        
        # System default
        return int(os.getenv("Q2O_LLM_MIN_QUALITY_SCORE", "95"))
    
    def create_project(
        self,
        project_id: str,
        project_name: str,
        client_name: str,
        llm_provider: Optional[str] = None,
        custom_prompt_additions: Optional[str] = None
    ) -> ProjectConfig:
        """
        Create a new project configuration.
        
        Args:
            project_id: Unique project identifier
            project_name: Human-readable project name
            client_name: Client company name
            llm_provider: Override system LLM provider
            custom_prompt_additions: Client-specific prompt additions
        
        Returns:
            Created ProjectConfig
        """
        project = ProjectConfig(
            project_id=project_id,
            project_name=project_name,
            client_name=client_name,
            llm_config=LLMConfig(
                provider=llm_provider,
                custom_instructions=custom_prompt_additions
            ),
            agent_overrides={},
            metadata={"created_at": datetime.now().isoformat()}
        )
        
        self.save_project_config(project)
        
        logging.info(f"✅ Created project config: {project_name} ({client_name})")
        
        return project
    
    def set_agent_override(
        self,
        project_id: str,
        agent_type: AgentType,
        provider: Optional[str] = None,
        custom_instructions: Optional[str] = None,
        temperature: Optional[float] = None
    ):
        """
        Set agent-level override for a project.
        
        Args:
            project_id: Project to configure
            agent_type: Agent to override
            provider: LLM provider for this agent
            custom_instructions: Agent-specific prompt additions
            temperature: Agent-specific temperature
        """
        if project_id not in self.projects:
            raise ValueError(f"Project not found: {project_id}")
        
        project = self.projects[project_id]
        agent_key = agent_type.value
        
        agent_config = LLMConfig(
            provider=provider,
            custom_instructions=custom_instructions,
            temperature=temperature
        )
        
        project.agent_overrides[agent_key] = agent_config
        self.save_project_config(project)
        
        logging.info(f"✅ Set agent override: {project.project_name} / {agent_type.value}")
    
    def get_project_config(self, project_id: str) -> Optional[ProjectConfig]:
        """Get project configuration by ID."""
        return self.projects.get(project_id)
    
    def list_projects(self) -> List[ProjectConfig]:
        """Get all project configurations."""
        return list(self.projects.values())
    
    def delete_project(self, project_id: str) -> bool:
        """Delete a project configuration."""
        if project_id in self.projects:
            del self.projects[project_id]
            
            # Save updated projects
            projects_data = {
                pid: project.to_dict()
                for pid, project in self.projects.items()
            }
            
            with open(self.projects_config_file, 'w') as f:
                json.dump(projects_data, f, indent=2)
            
            logging.info(f"🗑️  Deleted project config: {project_id}")
            return True
        
        return False
    
    def get_effective_config(
        self,
        project_id: Optional[str],
        agent_type: AgentType
    ) -> Dict[str, Any]:
        """
        Get the effective configuration for a task after cascading.
        
        This shows what will actually be used after all overrides.
        
        Args:
            project_id: Project identifier
            agent_type: Agent type
        
        Returns:
            Dictionary with all effective settings
        """
        provider = self.get_llm_provider_for_task(project_id, agent_type)
        temperature = self.get_temperature_for_task(project_id, agent_type)
        quality = self.get_quality_threshold(project_id)
        
        # Get model for provider
        model_map = {
            "gemini": os.getenv("GEMINI_MODEL", "gemini-1.5-pro"),
            "openai": os.getenv("OPENAI_MODEL", "gpt-4-turbo"),
            "anthropic": os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
        }
        
        model = model_map.get(provider, "unknown")
        
        # Get effective prompt (would need task details for full prompt)
        prompt_source = "system"
        if project_id and project_id in self.projects:
            project = self.projects[project_id]
            if agent_type.value in project.agent_overrides:
                prompt_source = f"agent ({agent_type.value})"
            elif project.llm_config.custom_instructions:
                prompt_source = f"project ({project.project_name})"
        
        return {
            "provider": provider,
            "model": model,
            "temperature": temperature,
            "quality_threshold": quality,
            "prompt_source": prompt_source,
            "cascade_path": self._get_cascade_path(project_id, agent_type)
        }
    
    def _get_cascade_path(self, project_id: Optional[str], agent_type: AgentType) -> List[str]:
        """Get the configuration cascade path for debugging."""
        path = ["system"]
        
        if project_id and project_id in self.projects:
            project = self.projects[project_id]
            path.append(f"project:{project.project_name}")
            
            if agent_type.value in project.agent_overrides:
                path.append(f"agent:{agent_type.value}")
        
        return path
    
    def export_configuration(self, project_id: Optional[str] = None) -> Dict:
        """
        Export configuration for documentation or backup.
        
        Args:
            project_id: Export specific project, or None for all
        
        Returns:
            Configuration dictionary
        """
        if project_id:
            if project_id not in self.projects:
                raise ValueError(f"Project not found: {project_id}")
            
            return {
                "system": self.system_config.to_dict(),
                "project": self.projects[project_id].to_dict()
            }
        else:
            return {
                "system": self.system_config.to_dict(),
                "projects": {
                    pid: project.to_dict()
                    for pid, project in self.projects.items()
                }
            }
    
    def import_configuration(self, config_data: Dict):
        """
        Import configuration from backup or another system.
        
        Args:
            config_data: Configuration dictionary
        """
        if "system" in config_data:
            self.system_config = LLMConfig.from_dict(config_data["system"])
            self.save_system_config(self.system_config)
        
        if "projects" in config_data:
            for project_data in config_data["projects"].values():
                project = ProjectConfig.from_dict(project_data)
                self.save_project_config(project)
        
        logging.info("✅ Configuration imported successfully")


class DynamicBudgetAllocator:
    """
    Dynamically allocate monthly budget across agents based on usage patterns.
    
    Auto-adjusts allocation each month based on actual usage.
    """
    
    def __init__(self, total_budget: float = 1000.0):
        """
        Initialize budget allocator.
        
        Args:
            total_budget: Total monthly budget in USD
        """
        self.total_budget = total_budget
        self.allocations = {}
        self.usage_history = []
    
    def calculate_allocation(self) -> Dict[str, float]:
        """
        Calculate budget allocation for each agent based on historical usage.
        
        Algorithm:
        1. If no history: Equal split
        2. With history: Allocate based on % of calls made by each agent
        3. Reserve 10% for unexpected usage
        
        Returns:
            Dict mapping agent_type to allocated budget
        """
        if not self.usage_history:
            # No history - equal split among common agents
            common_agents = ["coder", "researcher", "orchestrator", "testing", "qa"]
            allocated_budget = self.total_budget * 0.9  # 90%, reserve 10%
            per_agent = allocated_budget / len(common_agents)
            
            self.allocations = {agent: per_agent for agent in common_agents}
            self.allocations["reserve"] = self.total_budget * 0.1
            
            logging.info("📊 Initial budget allocation (equal split)")
            return self.allocations
        
        # Calculate based on usage
        total_calls = sum(h['calls'] for h in self.usage_history)
        if total_calls == 0:
            return self.calculate_allocation()  # Recursive, uses equal split
        
        # Group by agent
        by_agent = {}
        for entry in self.usage_history:
            agent = entry['agent_type']
            if agent not in by_agent:
                by_agent[agent] = 0
            by_agent[agent] += entry['calls']
        
        # Calculate percentages
        allocated_budget = self.total_budget * 0.9  # Reserve 10%
        
        self.allocations = {}
        for agent, calls in by_agent.items():
            percentage = calls / total_calls
            self.allocations[agent] = allocated_budget * percentage
        
        self.allocations["reserve"] = self.total_budget * 0.1
        
        logging.info(f"📊 Dynamic budget allocation (based on {total_calls} historical calls)")
        return self.allocations
    
    def record_usage(self, agent_type: str, calls: int, cost: float):
        """Record usage for future allocation calculations."""
        self.usage_history.append({
            "agent_type": agent_type,
            "calls": calls,
            "cost": cost,
            "timestamp": datetime.now().isoformat()
        })
    
    def get_remaining_budget(self, agent_type: str) -> float:
        """Get remaining budget for an agent."""
        if agent_type not in self.allocations:
            self.calculate_allocation()
        
        allocated = self.allocations.get(agent_type, 0)
        # TODO: Track actual spend per agent
        return allocated


# Singleton instances
_config_manager_instance = None
_budget_allocator_instance = None

def get_configuration_manager() -> ConfigurationManager:
    """Get singleton configuration manager instance."""
    global _config_manager_instance
    if _config_manager_instance is None:
        _config_manager_instance = ConfigurationManager()
    return _config_manager_instance

def get_budget_allocator() -> DynamicBudgetAllocator:
    """Get singleton budget allocator instance."""
    global _budget_allocator_instance
    if _budget_allocator_instance is None:
        budget = float(os.getenv("Q2O_LLM_MONTHLY_BUDGET", "1000.0"))
        _budget_allocator_instance = DynamicBudgetAllocator(total_budget=budget)
    return _budget_allocator_instance

