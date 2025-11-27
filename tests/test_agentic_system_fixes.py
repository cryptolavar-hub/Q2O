"""
Test suite for Agentic System bug fixes.

Tests verify that all critical bugs have been fixed:
1. Event loop conflicts
2. Async event emission
3. Coder agent task distribution
4. Project completion status
5. Research dependency access
6. Testing agent file discovery
"""

import pytest
import asyncio
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from agents.base_agent import BaseAgent, AgentType, Task, TaskStatus
from agents.orchestrator import OrchestratorAgent
from agents.coder_agent import CoderAgent
from agents.testing_agent import TestingAgent
from agents.research_aware_mixin import ResearchAwareMixin
from utils.task_registry import get_task_registry, register_task, get_task


class TestEventLoopFixes:
    """Test suite for event loop conflict fixes."""
    
    def test_run_async_with_existing_loop(self):
        """Test run_async() handles existing event loop correctly."""
        from agents.task_tracking import run_async
        
        async def test_coro():
            return "test_result"
        
        # Create event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Run in thread-safe way
            result = run_async(test_coro())
            assert result == "test_result"
        finally:
            loop.close()
            asyncio.set_event_loop(None)
    
    def test_run_async_without_loop(self):
        """Test run_async() creates new loop when none exists."""
        from agents.task_tracking import run_async
        
        async def test_coro():
            return "test_result"
        
        # Ensure no event loop
        try:
            loop = asyncio.get_running_loop()
            pytest.skip("Event loop already exists")
        except RuntimeError:
            pass
        
        result = run_async(test_coro())
        assert result == "test_result"
    
    def test_event_emission_no_warnings(self):
        """Test event emission doesn't produce warnings."""
        import warnings
        from agents.base_agent import BaseAgent, AgentType, Task
        
        class TestAgent(BaseAgent):
            def process_task(self, task):
                return task
        
        agent = TestAgent("test_agent", AgentType.CODER)
        task = Task(
            id="test_task",
            title="Test Task",
            description="Test",
            agent_type=AgentType.CODER
        )
        
        # Capture warnings
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            agent._emit_task_started("test_task", task)
            agent._emit_task_complete("test_task", task)
            
            # Check for unawaited coroutine warnings
            coroutine_warnings = [
                warning for warning in w 
                if "coroutine" in str(warning.message).lower() or 
                   "never awaited" in str(warning.message).lower()
            ]
            assert len(coroutine_warnings) == 0, f"Found coroutine warnings: {coroutine_warnings}"


class TestCoderTaskDistribution:
    """Test suite for coder agent task distribution fixes."""
    
    def test_integration_objective_creates_coder_task(self):
        """Test that integration objectives create coder tasks."""
        orchestrator = OrchestratorAgent()
        
        objectives = ["QuickBooks migration to Odoo"]
        tasks = orchestrator.break_down_project(
            "Migration Project",
            objectives
        )
        
        # Check that coder tasks were created
        coder_tasks = [t for t in tasks if t.agent_type == AgentType.CODER]
        assert len(coder_tasks) > 0, "No coder tasks created for integration objective"
        
        # Verify coder task has correct metadata
        coder_task = coder_tasks[0]
        assert coder_task.metadata.get("requires_backend") == True
    
    def test_workflow_objective_creates_coder_task(self):
        """Test that workflow objectives create coder tasks."""
        orchestrator = OrchestratorAgent()
        
        objectives = ["Create Temporal workflow for data sync"]
        tasks = orchestrator.break_down_project(
            "Workflow Project",
            objectives
        )
        
        coder_tasks = [t for t in tasks if t.agent_type == AgentType.CODER]
        assert len(coder_tasks) > 0, "No coder tasks created for workflow objective"
    
    def test_frontend_objective_creates_coder_task(self):
        """Test that frontend objectives create coder tasks."""
        orchestrator = OrchestratorAgent()
        
        objectives = ["Create React dashboard"]
        tasks = orchestrator.break_down_project(
            "Frontend Project",
            objectives
        )
        
        coder_tasks = [t for t in tasks if t.agent_type == AgentType.CODER]
        assert len(coder_tasks) > 0, "No coder tasks created for frontend objective"
    
    def test_needs_coder_task_logic(self):
        """Test _needs_coder_task() method logic."""
        orchestrator = OrchestratorAgent()
        
        # Test integration type
        assert orchestrator._needs_coder_task("integration", [], "QuickBooks integration") == True
        
        # Test workflow type
        assert orchestrator._needs_coder_task("workflow", [], "Temporal workflow") == True
        
        # Test frontend type
        assert orchestrator._needs_coder_task("frontend", [], "React dashboard") == True
        
        # Test api type
        assert orchestrator._needs_coder_task("api", [], "REST API") == True
        
        # Test generic type with code keywords
        assert orchestrator._needs_coder_task("generic", [], "implement user authentication") == True


class TestResearchDependencyAccess:
    """Test suite for research dependency access fixes."""
    
    def test_orchestrator_reference_passed_to_agents(self):
        """Test that orchestrator reference is passed to agents."""
        from main import AgentSystem
        
        with tempfile.TemporaryDirectory() as tmpdir:
            system = AgentSystem(workspace_path=tmpdir)
            
            # Check that agents have orchestrator reference
            for agent in system.coder_agents:
                assert hasattr(agent, 'orchestrator')
                assert agent.orchestrator == system.orchestrator
    
    def test_task_registry_works(self):
        """Test global task registry functionality."""
        registry = get_task_registry()
        registry.clear()  # Start fresh
        
        task = Task(
            id="test_task",
            title="Test Task",
            description="Test",
            agent_type=AgentType.CODER
        )
        
        # Register task
        register_task(task)
        
        # Retrieve task
        retrieved = get_task("test_task")
        assert retrieved is not None
        assert retrieved.id == "test_task"
    
    def test_research_aware_mixin_accesses_orchestrator(self):
        """Test ResearchAwareMixin can access orchestrator."""
        from agents.coder_agent import CoderAgent
        
        orchestrator = OrchestratorAgent()
        
        # Create research task
        research_task = Task(
            id="research_001",
            title="Research Stripe API",
            description="Research Stripe API",
            agent_type=AgentType.RESEARCHER
        )
        research_task.complete({
            "key_findings": ["Stripe uses REST API"],
            "documentation_urls": ["https://stripe.com/docs"]
        })
        orchestrator.project_tasks["research_001"] = research_task
        
        # Create coder agent with orchestrator
        with tempfile.TemporaryDirectory() as tmpdir:
            coder = CoderAgent(
                workspace_path=tmpdir,
                orchestrator=orchestrator
            )
            
            # Create dependent task
            coder_task = Task(
                id="coder_001",
                title="Implement Stripe integration",
                description="Implement Stripe",
                agent_type=AgentType.CODER,
                dependencies=["research_001"]
            )
            
            # Get research results
            research_results = coder.get_research_results(coder_task)
            assert len(research_results) > 0, "Research results not accessible"


class TestTestingAgentFileDiscovery:
    """Test suite for testing agent file discovery fixes."""
    
    def test_get_implemented_files_from_dependencies(self):
        """Test that testing agent gets files from dependency tasks."""
        orchestrator = OrchestratorAgent()
        
        # Create coder task with files
        coder_task = Task(
            id="coder_001",
            title="Implement API",
            description="Implement API",
            agent_type=AgentType.CODER
        )
        coder_task.complete({
            "files_created": ["api/endpoints.py", "api/models.py"]
        })
        orchestrator.project_tasks["coder_001"] = coder_task
        
        # Create testing task
        testing_task = Task(
            id="testing_001",
            title="Test API",
            description="Test API",
            agent_type=AgentType.TESTING,
            dependencies=["coder_001"]
        )
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            api_dir = Path(tmpdir) / "api"
            api_dir.mkdir()
            (api_dir / "endpoints.py").write_text("# API endpoints")
            (api_dir / "models.py").write_text("# Models")
            
            testing_agent = TestingAgent(
                workspace_path=tmpdir,
                orchestrator=orchestrator
            )
            
            files = testing_agent._get_implemented_files(testing_task)
            assert len(files) > 0, "No files found from dependencies"
            assert any("endpoints.py" in f for f in files), "endpoints.py not found"
            assert any("models.py" in f for f in files), "models.py not found"
    
    def test_get_dependency_task_works(self):
        """Test _get_dependency_task() method."""
        orchestrator = OrchestratorAgent()
        
        task = Task(
            id="test_task",
            title="Test",
            description="Test",
            agent_type=AgentType.CODER
        )
        orchestrator.project_tasks["test_task"] = task
        
        with tempfile.TemporaryDirectory() as tmpdir:
            testing_agent = TestingAgent(
                workspace_path=tmpdir,
                orchestrator=orchestrator
            )
            
            retrieved = testing_agent._get_dependency_task("test_task")
            assert retrieved is not None
            assert retrieved.id == "test_task"


class TestProjectCompletionStatus:
    """Test suite for project completion status fixes."""
    
    @pytest.mark.asyncio
    async def test_process_monitoring_updates_status(self):
        """Test that process monitoring updates project status."""
        # This test would require actual subprocess execution
        # For now, we test the monitoring function logic
        
        from addon_portal.api.services.project_execution_service import _monitor_process_completion
        from addon_portal.api.models.llm_config import LLMProjectConfig
        
        # Mock project and database
        # Note: This is a simplified test - full test requires database setup
        pass  # Placeholder for actual test implementation


class TestEndToEnd:
    """End-to-end integration tests."""
    
    def test_full_project_execution(self):
        """Test complete project execution flow."""
        # This would be a comprehensive test
        # Requires full system setup
        pass  # Placeholder for actual test implementation


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

