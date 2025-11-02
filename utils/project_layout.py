"""
Project Layout Configuration - Configurable directory structure for generated projects.
"""

from dataclasses import dataclass, field
from typing import Dict, Optional
from pathlib import Path
import os


@dataclass
class ProjectLayout:
    """Configurable project layout structure."""
    
    # API/Backend paths
    api_dir: str = "api"
    api_app_dir: str = "api/app"
    api_models_dir: str = "api/app"
    api_clients_dir: str = "api/app/clients"
    
    # Frontend paths
    web_dir: str = "web"
    web_pages_dir: str = "web/pages"
    web_components_dir: str = "web/components"
    web_api_dir: str = "web/pages/api"
    
    # Infrastructure paths
    infra_dir: str = "infra"
    terraform_dir: str = "infra/terraform"
    terraform_azure_dir: str = "infra/terraform/azure"
    
    # Kubernetes paths
    k8s_dir: str = "k8s"
    helm_dir: str = "k8s/helm"
    helm_q2o_dir: str = "k8s/helm/q2o"
    helm_templates_dir: str = "k8s/helm/q2o/templates"
    
    # Shared/Temporal paths
    shared_dir: str = "shared"
    temporal_dir: str = "shared/temporal_defs"
    workflows_dir: str = "shared/temporal_defs/workflows"
    activities_dir: str = "shared/temporal_defs/activities"
    
    # Test paths
    tests_dir: str = "tests"
    
    # Configuration paths
    config_dir: str = "config"
    
    @classmethod
    def from_dict(cls, config: Dict[str, str]) -> 'ProjectLayout':
        """Create ProjectLayout from dictionary."""
        return cls(**config)
    
    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary."""
        return {
            'api_dir': self.api_dir,
            'api_app_dir': self.api_app_dir,
            'api_models_dir': self.api_models_dir,
            'api_clients_dir': self.api_clients_dir,
            'web_dir': self.web_dir,
            'web_pages_dir': self.web_pages_dir,
            'web_components_dir': self.web_components_dir,
            'web_api_dir': self.web_api_dir,
            'infra_dir': self.infra_dir,
            'terraform_dir': self.terraform_dir,
            'terraform_azure_dir': self.terraform_azure_dir,
            'k8s_dir': self.k8s_dir,
            'helm_dir': self.helm_dir,
            'helm_q2o_dir': self.helm_q2o_dir,
            'helm_templates_dir': self.helm_templates_dir,
            'shared_dir': self.shared_dir,
            'temporal_dir': self.temporal_dir,
            'workflows_dir': self.workflows_dir,
            'activities_dir': self.activities_dir,
            'tests_dir': self.tests_dir,
            'config_dir': self.config_dir,
        }
    
    def get_path(self, key: str, *parts: str) -> str:
        """
        Get a path from the layout.
        
        Args:
            key: Layout key (e.g., 'api_app_dir')
            *parts: Additional path parts to append
            
        Returns:
            Combined path string
        """
        base_path = getattr(self, key, key)
        if parts:
            return os.path.join(base_path, *parts)
        return base_path
    
    def get_full_path(self, workspace_path: str, key: str, *parts: str) -> str:
        """
        Get full absolute path.
        
        Args:
            workspace_path: Base workspace directory
            key: Layout key
            *parts: Additional path parts
            
        Returns:
            Full absolute path
        """
        rel_path = self.get_path(key, *parts)
        return os.path.join(workspace_path, rel_path)


# Global default layout instance
_default_layout: Optional[ProjectLayout] = None


def get_default_layout() -> ProjectLayout:
    """Get the default project layout."""
    global _default_layout
    if _default_layout is None:
        _default_layout = ProjectLayout()
    return _default_layout


def set_default_layout(layout: ProjectLayout):
    """Set the default project layout."""
    global _default_layout
    _default_layout = layout


def load_layout_from_config(config_path: str) -> ProjectLayout:
    """
    Load project layout from JSON configuration file.
    
    Args:
        config_path: Path to JSON configuration file
        
    Returns:
        ProjectLayout instance
    """
    import json
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    layout_config = config.get('project_layout', {})
    return ProjectLayout.from_dict(layout_config)

