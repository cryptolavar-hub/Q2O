"""
Template Renderer using Jinja2.
Provides centralized template rendering for all agents.
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
from jinja2 import Environment, FileSystemLoader, TemplateNotFound
import logging

logger = logging.getLogger(__name__)


class TemplateRenderer:
    """Jinja2-based template renderer for code generation."""
    
    def __init__(self, template_dir: Optional[str] = None):
        """
        Initialize template renderer.
        
        Args:
            template_dir: Directory containing templates. If None, uses default.
        """
        # Determine template directory
        if template_dir is None:
            # Default to templates/ in project root
            current_file = Path(__file__).parent
            template_dir = current_file.parent / "templates"
        else:
            template_dir = Path(template_dir)
        
        self.template_dir = template_dir
        self.template_dir.mkdir(parents=True, exist_ok=True)
        
        # Create Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=True
        )
        
        # Add custom filters
        self._add_custom_filters()
        
        logger.info(f"Template renderer initialized with template dir: {self.template_dir}")
    
    def _add_custom_filters(self):
        """Add custom Jinja2 filters."""
        
        def snake_case(value: str) -> str:
            """Convert string to snake_case."""
            import re
            s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', value)
            return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
        
        def camel_case(value: str) -> str:
            """Convert string to CamelCase."""
            components = value.split('_')
            return ''.join(word.capitalize() for word in components)
        
        def pascal_case(value: str) -> str:
            """Convert string to PascalCase (same as camel_case)."""
            return camel_case(value)
        
        def kebab_case(value: str) -> str:
            """Convert string to kebab-case."""
            return value.replace('_', '-').lower()
        
        self.env.filters['snake_case'] = snake_case
        self.env.filters['camel_case'] = camel_case
        self.env.filters['pascal_case'] = pascal_case
        self.env.filters['kebab_case'] = kebab_case
    
    def render(self, template_name: str, context: Dict[str, Any]) -> str:
        """
        Render a template with the given context.
        
        Args:
            template_name: Name of the template file (relative to template_dir)
            context: Dictionary of variables to pass to template
            
        Returns:
            Rendered template as string
            
        Raises:
            TemplateNotFound: If template doesn't exist
        """
        try:
            template = self.env.get_template(template_name)
            return template.render(**context)
        except TemplateNotFound as e:
            logger.error(f"Template not found: {template_name}")
            raise
        except Exception as e:
            logger.error(f"Error rendering template {template_name}: {str(e)}", exc_info=True)
            raise
    
    def render_string(self, template_string: str, context: Dict[str, Any]) -> str:
        """
        Render a template string directly.
        
        Args:
            template_string: Template as string
            context: Dictionary of variables to pass to template
            
        Returns:
            Rendered template as string
        """
        try:
            template = self.env.from_string(template_string)
            return template.render(**context)
        except Exception as e:
            logger.error(f"Error rendering template string: {str(e)}", exc_info=True)
            raise
    
    def get_template_path(self, template_name: str) -> Path:
        """
        Get full path to a template file.
        
        Args:
            template_name: Name of the template file
            
        Returns:
            Path object to template file
        """
        return self.template_dir / template_name
    
    def template_exists(self, template_name: str) -> bool:
        """
        Check if a template exists.
        
        Args:
            template_name: Name of the template file
            
        Returns:
            True if template exists
        """
        return (self.template_dir / template_name).exists()


# Global template renderer instance
_renderer_instance: Optional[TemplateRenderer] = None


def get_renderer() -> TemplateRenderer:
    """Get the global template renderer instance."""
    global _renderer_instance
    if _renderer_instance is None:
        _renderer_instance = TemplateRenderer()
    return _renderer_instance


def set_renderer(renderer: TemplateRenderer):
    """Set the global template renderer instance."""
    global _renderer_instance
    _renderer_instance = renderer

