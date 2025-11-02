"""
Retry Policy Configuration for Agent Task Processing.
Defines configurable retry policies per agent type and task.
"""

from dataclasses import dataclass, field
from typing import Optional, Callable, List, Type
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class RetryStrategy(Enum):
    """Retry strategy types."""
    EXPONENTIAL = "exponential"  # Exponential backoff
    LINEAR = "linear"  # Linear backoff
    FIXED = "fixed"  # Fixed delay
    CUSTOM = "custom"  # Custom function


@dataclass
class RetryPolicy:
    """Configuration for retry behavior."""
    max_retries: int = 3
    initial_delay: float = 1.0
    max_delay: float = 60.0
    backoff_factor: float = 2.0
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL
    retryable_exceptions: tuple = (Exception,)  # Default: retry on all exceptions
    non_retryable_exceptions: tuple = ()  # Exceptions that should never be retried
    custom_backoff: Optional[Callable[[int], float]] = None  # Custom backoff function
    
    def get_delay(self, attempt: int) -> float:
        """
        Calculate delay for a specific retry attempt.
        
        Args:
            attempt: Retry attempt number (0-indexed, so attempt 1 = first retry)
            
        Returns:
            Delay in seconds
        """
        if attempt == 0:
            return self.initial_delay
        
        if self.strategy == RetryStrategy.EXPONENTIAL:
            delay = self.initial_delay * (self.backoff_factor ** attempt)
        elif self.strategy == RetryStrategy.LINEAR:
            delay = self.initial_delay + (self.initial_delay * attempt)
        elif self.strategy == RetryStrategy.FIXED:
            delay = self.initial_delay
        elif self.strategy == RetryStrategy.CUSTOM and self.custom_backoff:
            delay = self.custom_backoff(attempt)
        else:
            delay = self.initial_delay
        
        return min(delay, self.max_delay)
    
    def should_retry(self, exception: Exception, attempt: int) -> bool:
        """
        Determine if an exception should be retried.
        
        Args:
            exception: The exception that occurred
            attempt: Current retry attempt number
            
        Returns:
            True if should retry, False otherwise
        """
        # Check if we've exceeded max retries
        if attempt >= self.max_retries:
            return False
        
        # Check if exception is in non-retryable list
        if isinstance(exception, self.non_retryable_exceptions):
            return False
        
        # Check if exception is in retryable list (or retryable is catch-all)
        if self.retryable_exceptions == (Exception,):
            return True  # Catch-all: retry everything
        
        return isinstance(exception, self.retryable_exceptions)


class RetryPolicyManager:
    """Manages retry policies for different agent types and tasks."""
    
    def __init__(self):
        # Default policies per agent type
        self.default_policies: dict = {
            "coder": RetryPolicy(
                max_retries=3,
                initial_delay=1.0,
                backoff_factor=2.0,
                strategy=RetryStrategy.EXPONENTIAL
            ),
            "integration": RetryPolicy(
                max_retries=5,  # More retries for external API calls
                initial_delay=2.0,
                backoff_factor=2.0,
                strategy=RetryStrategy.EXPONENTIAL,
                max_delay=120.0  # Longer max delay for network issues
            ),
            "infrastructure": RetryPolicy(
                max_retries=2,  # Fewer retries for IaC (failures are usually deterministic)
                initial_delay=3.0,
                backoff_factor=1.5,
                strategy=RetryStrategy.LINEAR
            ),
            "testing": RetryPolicy(
                max_retries=2,
                initial_delay=0.5,
                backoff_factor=2.0,
                strategy=RetryStrategy.EXPONENTIAL
            ),
            "workflow": RetryPolicy(
                max_retries=4,
                initial_delay=2.0,
                backoff_factor=2.0,
                strategy=RetryStrategy.EXPONENTIAL
            ),
            "nodejs": RetryPolicy(
                max_retries=3,
                initial_delay=1.0,
                backoff_factor=2.0,
                strategy=RetryStrategy.EXPONENTIAL
            ),
            # Default for all other agents
            "default": RetryPolicy(
                max_retries=3,
                initial_delay=1.0,
                backoff_factor=2.0,
                strategy=RetryStrategy.EXPONENTIAL
            )
        }
        
        # Task-specific overrides (by task title/keyword)
        self.task_overrides: dict = {}
    
    def get_policy(self, agent_type: str, task_title: str = None) -> RetryPolicy:
        """
        Get retry policy for an agent type and optional task.
        
        Args:
            agent_type: Agent type identifier
            task_title: Optional task title for task-specific override
            
        Returns:
            RetryPolicy instance
        """
        # Check for task-specific override
        if task_title:
            for keyword, policy in self.task_overrides.items():
                if keyword.lower() in task_title.lower():
                    logger.debug(f"Using task-specific retry policy '{keyword}' for task '{task_title}'")
                    return policy
        
        # Get agent-specific policy or default
        policy = self.default_policies.get(agent_type.lower(), self.default_policies["default"])
        return policy
    
    def set_custom_policy(self, agent_type: str, policy: RetryPolicy):
        """Set a custom retry policy for an agent type."""
        self.default_policies[agent_type.lower()] = policy
        logger.info(f"Set custom retry policy for agent type '{agent_type}'")
    
    def set_task_override(self, keyword: str, policy: RetryPolicy):
        """Set a task-specific retry policy override."""
        self.task_overrides[keyword.lower()] = policy
        logger.info(f"Set task-specific retry policy for keyword '{keyword}'")


# Singleton instance
_policy_manager: Optional[RetryPolicyManager] = None


def get_policy_manager() -> RetryPolicyManager:
    """Get the singleton RetryPolicyManager instance."""
    global _policy_manager
    if _policy_manager is None:
        _policy_manager = RetryPolicyManager()
    return _policy_manager

