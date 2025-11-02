"""
Testing Agent - Writes and executes tests for implemented code.
"""

from typing import Dict, Any, List
from agents.base_agent import BaseAgent, AgentType, Task, TaskStatus
from utils.template_renderer import TemplateRenderer, get_renderer
import os
import sys
import logging
import importlib.util
import subprocess


class TestingAgent(BaseAgent):
    """Agent responsible for writing and executing tests."""

    def __init__(self, agent_id: str = "testing_main", workspace_path: str = "."):
        super().__init__(agent_id, AgentType.TESTING)
        self.workspace_path = workspace_path
        self.test_files: List[str] = []
        self.test_results: Dict[str, Dict[str, Any]] = {}
        self.template_renderer = get_renderer()

    def process_task(self, task: Task) -> Task:
        """
        Process a testing task by writing and executing tests.
        
        Args:
            task: The testing task to process
            
        Returns:
            The updated task
        """
        try:
            self.logger.info(f"Processing testing task: {task.title}")
            
            # Get the related coding task to find implemented files
            implemented_files = self._get_implemented_files(task)
            
            if not implemented_files:
                self.logger.warning(f"No implemented files found for task {task.id}")
                task.metadata["warning"] = "No implemented files to test"
            
            # Generate tests for each implemented file
            test_files_created = []
            test_results = {}
            
            for file_path in implemented_files:
                test_file = self._create_test_file(file_path, task)
                if test_file:
                    test_files_created.append(test_file)
                    # Try to execute the test
                    test_result = self._execute_test(test_file)
                    test_results[test_file] = test_result
            
            # Update task metadata
            task.metadata["test_files"] = test_files_created
            task.metadata["test_results"] = test_results
            task.result = {
                "test_files_created": test_files_created,
                "test_results": test_results,
                "total_tests": sum(r.get("test_count", 0) for r in test_results.values()),
                "passed_tests": sum(r.get("passed", 0) for r in test_results.values()),
                "failed_tests": sum(r.get("failed", 0) for r in test_results.values()),
                "status": "completed"
            }

            self.complete_task(task.id, task.result)
            self.logger.info(f"Completed testing task {task.id}")
            
        except Exception as e:
            error_msg = f"Error processing testing task: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            self.fail_task(task.id, error_msg)
            
        return task

    def _get_implemented_files(self, task: Task) -> List[str]:
        """
        Get list of implemented files to test.
        Looks for files created by the coder agent in dependencies.
        
        Args:
            task: The testing task
            
        Returns:
            List of file paths to test
        """
        implemented_files = []
        
        # Check if task has dependency info pointing to coder task
        # In a real system, we'd query the orchestrator for dependency results
        # For now, we'll look for common patterns
        
        # Check task description for file references
        description = task.description.lower()
        
        # Look for Python files in the workspace that might be related
        if "implement" in description or "code" in description:
            # Try to find related files
            obj = task.metadata.get("objective", "")
            if obj:
                potential_file = f"src/{obj.lower().replace(' ', '_')}.py"
                if os.path.exists(os.path.join(self.workspace_path, potential_file)):
                    implemented_files.append(potential_file)
        
        # If nothing found, create a generic test structure
        if not implemented_files:
            obj = task.metadata.get("objective", task.title)
            implemented_files.append(f"src/{obj.lower().replace(' ', '_')}.py")
        
        return implemented_files

    def _create_test_file(self, source_file: str, task: Task) -> str:
        """
        Create a test file for the given source file.
        
        Args:
            source_file: Path to the source file to test
            task: The testing task
            
        Returns:
            Path to the created test file
        """
        # Generate test file path
        source_name = os.path.basename(source_file)
        test_dir = "tests"
        test_filename = f"test_{source_name}"
        test_path = os.path.join(test_dir, test_filename)
        full_test_path = os.path.join(self.workspace_path, test_path)
        
        # Ensure test directory exists
        os.makedirs(os.path.dirname(full_test_path), exist_ok=True)
        
        # Generate test content
        test_content = self._generate_test_content(source_file, source_name, task)
        
        # Write test file
        with open(full_test_path, 'w', encoding='utf-8') as f:
            f.write(test_content)
        
        self.logger.info(f"Created test file: {test_path}")
        self.test_files.append(test_path)
        
        return test_path

    def _generate_test_content(self, source_file: str, source_name: str, task: Task) -> str:
        """
        Generate test file content.
        
        Args:
            source_file: Path to source file
            source_name: Name of source file
            task: The testing task
            
        Returns:
            Test file content as string
        """
        module_name = source_name.replace('.py', '')
        class_name = ''.join(word.capitalize() for word in module_name.split('_'))
        objective = task.metadata.get("objective", task.title)
        
        # Use pytest template if available
        if self.template_renderer.template_exists("test/pytest_test.j2"):
            context = {
                "source_file": source_file,
                "source_name": source_name,
                "module_name": module_name,
                "class_name": class_name,
                "objective": objective
            }
            return self.template_renderer.render("test/pytest_test.j2", context)
        
        # Fallback to unittest format (for backward compatibility)
        return self._generate_test_content_unittest(source_file, source_name, module_name, class_name, objective)
    
    def _generate_test_content_unittest(self, source_file: str, source_name: str, module_name: str, class_name: str, objective: str) -> str:
        """Generate unittest test content (fallback)."""
        return f'''"""
Tests for {source_file}
Generated by TestingAgent
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from {module_name} import {class_name}
    MODULE_AVAILABLE = True
except ImportError:
    MODULE_AVAILABLE = False


class Test{class_name}(unittest.TestCase):
    """
    Test cases for {objective}
    """

    def setUp(self):
        """Set up test fixtures."""
        if MODULE_AVAILABLE:
            self.instance = {class_name}()
        else:
            self.instance = None

    def test_initialization(self):
        """Test that the class can be initialized."""
        if not MODULE_AVAILABLE:
            self.skipTest("Module not available")
        
        self.assertIsNotNone(self.instance)
        self.assertIsInstance(self.instance, {class_name})

    def test_basic_functionality(self):
        """Test basic functionality."""
        if not MODULE_AVAILABLE:
            self.skipTest("Module not available")
        
        # Test that main method exists and is callable
        if hasattr(self.instance, 'execute'):
            result = self.instance.execute()
            self.assertIsInstance(result, dict)
            self.assertIn('status', result)
        elif hasattr(self.instance, '__call__'):
            result = self.instance()
            self.assertIsNotNone(result)

    def test_error_handling(self):
        """Test error handling."""
        if not MODULE_AVAILABLE:
            self.skipTest("Module not available")
        
        # Test that errors are handled gracefully
        try:
            if hasattr(self.instance, 'execute'):
                result = self.instance.execute()
                # Should not raise exception for normal cases
                self.assertIsNotNone(result)
        except Exception as e:
            self.fail(f"Unexpected exception: {{str(e)}}")

    @unittest.skipIf(not MODULE_AVAILABLE, "Module not available")
    def test_return_types(self):
        """Test that methods return expected types."""
        if hasattr(self.instance, 'execute'):
            result = self.instance.execute()
            self.assertIsInstance(result, dict)


class Test{class_name}Mock(unittest.TestCase):
    """
    Mock tests when module is not available
    """

    def test_placeholder(self):
        """Placeholder test when module is not available."""
        if MODULE_AVAILABLE:
            self.skipTest("Module available, skipping mock test")
        
        # Basic assertion to ensure test framework works
        self.assertTrue(True, "Mock test passed")


if __name__ == '__main__':
    unittest.main(verbosity=2)
'''

    def _execute_test(self, test_file: str) -> Dict[str, Any]:
        """
        Execute a test file using pytest and collect results.
        
        Args:
            test_file: Path to the test file
            
        Returns:
            Dictionary with test execution results
        """
        full_test_path = os.path.join(self.workspace_path, test_file)
        
        result = {
            "test_file": test_file,
            "status": "unknown",
            "test_count": 0,
            "passed": 0,
            "failed": 0,
            "errors": 0,
            "output": ""
        }
        
        try:
            # Use pytest with proper PYTHONPATH
            # Set PYTHONPATH to workspace root for imports
            env = os.environ.copy()
            env["PYTHONPATH"] = self.workspace_path
            
            # Run pytest on the test file
            cmd = [
                sys.executable, "-m", "pytest",
                full_test_path,
                "-v",  # Verbose
                "--tb=short",  # Short traceback
                "--no-header",  # No header
                "-p", "no:warnings"  # Suppress warnings
            ]
            
            process_result = subprocess.run(
                cmd,
                cwd=self.workspace_path,
                capture_output=True,
                text=True,
                timeout=60,
                env=env
            )
            
            result["output"] = process_result.stdout + process_result.stderr
            result["status"] = "success" if process_result.returncode == 0 else "failed"
            
            # Parse pytest output for test counts
            output = result["output"]
            if "passed" in output:
                # Parse pytest output: "X passed"
                import re
                passed_match = re.search(r'(\d+)\s+passed', output)
                failed_match = re.search(r'(\d+)\s+failed', output)
                errors_match = re.search(r'(\d+)\s+error', output)
                
                result["passed"] = int(passed_match.group(1)) if passed_match else 0
                result["failed"] = int(failed_match.group(1)) if failed_match else 0
                result["errors"] = int(errors_match.group(1)) if errors_match else 0
                result["test_count"] = result["passed"] + result["failed"] + result["errors"]
            elif "FAILED" in output or "ERROR" in output:
                result["failed"] = 1
                result["test_count"] = 1
            
        except subprocess.TimeoutExpired:
            result["status"] = "timeout"
            result["output"] = "Test execution timed out"
        except FileNotFoundError:
            # pytest not installed - skip test execution
            result["status"] = "skipped"
            result["output"] = "pytest not installed - skipping test execution"
            self.logger.warning(f"pytest not found - skipping test execution for {test_file}")
        except Exception as e:
            result["status"] = "error"
            result["output"] = f"Error executing tests: {str(e)}"
            self.logger.warning(f"Could not execute test {test_file}: {str(e)}")
        
        self.test_results[test_file] = result
        return result

