"""
Standardized Exception Classes for the Multi-Agent System.
"""


class AgentError(Exception):
    """Base exception for all agent-related errors."""
    pass


class TemplateError(AgentError):
    """Raised when template rendering fails."""
    pass


class ValidationError(AgentError):
    """Raised when validation fails."""
    pass


class GenerationError(AgentError):
    """Raised when code generation fails."""
    pass


class ConfigurationError(AgentError):
    """Raised when configuration is invalid."""
    pass


class SecurityError(AgentError):
    """Raised when security checks fail."""
    pass

