"""
Multi-Agent Development System
Provides agents for orchestrating, coding, testing, QA, infrastructure, integration, frontend, workflow, and security.
"""

from agents.base_agent import BaseAgent, AgentType, Task, TaskStatus
from agents.orchestrator import OrchestratorAgent
from agents.coder_agent import CoderAgent
from agents.testing_agent import TestingAgent
from agents.qa_agent import QAAgent
from agents.infrastructure_agent import InfrastructureAgent
from agents.integration_agent import IntegrationAgent
from agents.frontend_agent import FrontendAgent
from agents.workflow_agent import WorkflowAgent
from agents.security_agent import SecurityAgent

# Optional NodeAgent import
try:
    from agents.node_agent import NodeAgent
except ImportError:
    NodeAgent = None

__all__ = [
    'BaseAgent',
    'AgentType',
    'Task',
    'TaskStatus',
    'OrchestratorAgent',
    'CoderAgent',
    'TestingAgent',
    'QAAgent',
    'InfrastructureAgent',
    'IntegrationAgent',
    'FrontendAgent',
    'WorkflowAgent',
    'SecurityAgent',
]

# Conditionally add NodeAgent to exports
if NodeAgent is not None:
    __all__.append('NodeAgent')

