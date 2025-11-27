"""
Configuration Database Service - PostgreSQL storage for scalable configuration.
Replaces file-based configuration with database storage for multi-host deployments.
"""

import logging
from typing import Dict, Optional, List, Any
from datetime import datetime

# Database imports
try:
    from sqlalchemy.orm import Session
    from addon_portal.api.core.db import get_db
    from addon_portal.api.models.llm_config import (
        SystemLLMConfig,
        ProjectLLMConfig, 
        AgentLLMConfig,
        LLMUsageLog
    )
    DB_AVAILABLE = True
except ImportError:
    logging.warning("Database not available for configuration storage, using files")
    DB_AVAILABLE = False


class ConfigDatabase:
    """
    PostgreSQL-based configuration storage.
    
    Benefits:
    - Scalable across multiple application hosts
    - No file system dependencies
    - Atomic updates
    - Audit trail
    - Fast queries
    """
    
    def __init__(self):
        self.enabled = DB_AVAILABLE
    
    # ========================================================================
    # SYSTEM CONFIGURATION
    # ========================================================================
    
    def get_system_config(self) -> Optional[Dict]:
        """Get system-level LLM configuration."""
        if not self.enabled:
            return None
        
        try:
            db = next(get_db())
            
            config = db.query(SystemLLMConfig).filter(SystemLLMConfig.id == 1).first()
            
            if not config:
                # Create default
                config = SystemLLMConfig(id=1)
                db.add(config)
                db.commit()
                db.refresh(config)
            
            return {
                "primary_provider": config.primary_provider,
                "secondary_provider": config.secondary_provider,
                "tertiary_provider": config.tertiary_provider,
                "default_temperature": config.default_temperature,
                "default_max_tokens": config.default_max_tokens,
                "default_retries": config.default_retries,
                "default_monthly_budget": config.default_monthly_budget,
                "system_prompt": config.system_prompt,
                "llm_enabled": config.llm_enabled,
                "template_learning_enabled": config.template_learning_enabled,
                "cross_validation_enabled": config.cross_validation_enabled
            }
            
        except Exception as e:
            logging.error(f"Failed to get system config: {e}")
            return None
    
    def update_system_config(self, updates: Dict) -> bool:
        """Update system-level configuration."""
        if not self.enabled:
            return False
        
        try:
            db = next(get_db())
            
            config = db.query(SystemLLMConfig).filter(SystemLLMConfig.id == 1).first()
            
            if not config:
                config = SystemLLMConfig(id=1)
                db.add(config)
            
            # Update fields
            for key, value in updates.items():
                if hasattr(config, key):
                    setattr(config, key, value)
            
            config.updated_at = datetime.now()
            db.commit()
            
            logging.info("[OK] System config updated in PostgreSQL")
            return True
            
        except Exception as e:
            logging.error(f"Failed to update system config: {e}")
            return False
    
    # ========================================================================
    # PROJECT CONFIGURATION
    # ========================================================================
    
    def get_project_config(self, project_id: str) -> Optional[Dict]:
        """Get project-level LLM configuration."""
        if not self.enabled:
            return None
        
        try:
            db = next(get_db())
            
            project = db.query(ProjectLLMConfig).filter(
                ProjectLLMConfig.project_id == project_id,
                ProjectLLMConfig.is_active == True
            ).first()
            
            if not project:
                return None
            
            return {
                "project_id": project.project_id,
                "client_name": project.client_name,
                "project_type": project.project_type,
                "llm_provider": project.llm_provider,
                "llm_model": project.llm_model,
                "temperature": project.temperature,
                "max_tokens": project.max_tokens,
                "monthly_budget": project.monthly_budget,
                "alert_threshold": project.alert_threshold,
                "system_prompt_override": project.system_prompt_override,
                "custom_instructions": project.custom_instructions,
                "template_learning_enabled": project.template_learning_enabled,
                "cross_validation_enabled": project.cross_validation_enabled
            }
            
        except Exception as e:
            logging.error(f"Failed to get project config: {e}")
            return None
    
    def get_all_projects(self) -> List[Dict]:
        """Get all project configurations."""
        if not self.enabled:
            return []
        
        try:
            db = next(get_db())
            
            projects = db.query(ProjectLLMConfig).filter(
                ProjectLLMConfig.is_active == True
            ).order_by(ProjectLLMConfig.client_name).all()
            
            return [{
                "project_id": p.project_id,
                "client_name": p.client_name,
                "project_type": p.project_type,
                "llm_provider": p.llm_provider,
                "monthly_budget": p.monthly_budget,
                "custom_instructions": p.custom_instructions
            } for p in projects]
            
        except Exception as e:
            logging.error(f"Failed to get all projects: {e}")
            return []
    
    def create_project_config(
        self,
        project_id: str,
        client_name: str,
        **kwargs
    ) -> bool:
        """Create new project configuration."""
        if not self.enabled:
            return False
        
        try:
            db = next(get_db())
            
            project = ProjectLLMConfig(
                project_id=project_id,
                client_name=client_name,
                **kwargs
            )
            
            db.add(project)
            db.commit()
            
            logging.info(f"[OK] Created project config: {project_id} ({client_name})")
            return True
            
        except Exception as e:
            logging.error(f"Failed to create project config: {e}")
            return False
    
    def update_project_config(self, project_id: str, updates: Dict) -> bool:
        """Update project configuration."""
        if not self.enabled:
            return False
        
        try:
            db = next(get_db())
            
            project = db.query(ProjectLLMConfig).filter(
                ProjectLLMConfig.project_id == project_id
            ).first()
            
            if not project:
                return False
            
            # Update fields
            for key, value in updates.items():
                if hasattr(project, key):
                    setattr(project, key, value)
            
            project.updated_at = datetime.now()
            db.commit()
            
            logging.info(f"[OK] Updated project config: {project_id}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to update project config: {e}")
            return False
    
    # ========================================================================
    # AGENT CONFIGURATION
    # ========================================================================
    
    def get_agent_config(self, project_id: str, agent_type: str) -> Optional[Dict]:
        """Get agent-specific configuration for a project."""
        if not self.enabled:
            return None
        
        try:
            db = next(get_db())
            
            agent = db.query(AgentLLMConfig).filter(
                AgentLLMConfig.project_id == project_id,
                AgentLLMConfig.agent_type == agent_type,
                AgentLLMConfig.enabled == True
            ).first()
            
            if not agent:
                return None
            
            return {
                "agent_type": agent.agent_type,
                "llm_provider": agent.llm_provider,
                "llm_model": agent.llm_model,
                "temperature": agent.temperature,
                "max_tokens": agent.max_tokens,
                "system_prompt_override": agent.system_prompt_override,
                "custom_instructions": agent.custom_instructions
            }
            
        except Exception as e:
            logging.error(f"Failed to get agent config: {e}")
            return None
    
    def set_agent_config(
        self,
        project_id: str,
        agent_type: str,
        **kwargs
    ) -> bool:
        """Create or update agent configuration."""
        if not self.enabled:
            return False
        
        try:
            db = next(get_db())
            
            agent = db.query(AgentLLMConfig).filter(
                AgentLLMConfig.project_id == project_id,
                AgentLLMConfig.agent_type == agent_type
            ).first()
            
            if agent:
                # Update existing
                for key, value in kwargs.items():
                    if hasattr(agent, key):
                        setattr(agent, key, value)
                agent.updated_at = datetime.now()
            else:
                # Create new
                agent = AgentLLMConfig(
                    project_id=project_id,
                    agent_type=agent_type,
                    **kwargs
                )
                db.add(agent)
            
            db.commit()
            
            logging.info(f"[OK] Saved agent config: {project_id}/{agent_type}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to save agent config: {e}")
            return False
    
    # ========================================================================
    # USAGE LOGGING
    # ========================================================================
    
    def log_llm_usage(
        self,
        request_id: str,
        project_id: Optional[str],
        agent_type: str,
        provider: str,
        **kwargs
    ):
        """Log LLM API usage for analytics."""
        if not self.enabled:
            return
        
        try:
            db = next(get_db())
            
            log_entry = LLMUsageLog(
                request_id=request_id,
                project_id=project_id,
                agent_type=agent_type,
                provider=provider,
                **kwargs
            )
            
            db.add(log_entry)
            db.commit()
            
        except Exception as e:
            logging.error(f"Failed to log LLM usage: {e}")


# Singleton
_config_db = None

def get_config_database() -> ConfigDatabase:
    """Get singleton configuration database instance."""
    global _config_db
    if _config_db is None:
        _config_db = ConfigDatabase()
    return _config_db

