"""
Security Agent - Performs security and compliance reviews.
Focuses on security-specific checks beyond general QA.
"""

from typing import Dict, Any, List
from agents.base_agent import BaseAgent, AgentType, Task, TaskStatus
from agents.qa_agent import QAAgent
import os
import logging
import re


class SecurityAgent(BaseAgent):
    """Agent responsible for security and compliance reviews."""

    def __init__(self, agent_id: str = "security_main", workspace_path: str = "."):
        super().__init__(agent_id, AgentType.SECURITY)
        self.workspace_path = workspace_path
        self.reviewed_files: List[str] = []
        self.security_reports: Dict[str, Dict[str, Any]] = {}

    def process_task(self, task: Task) -> Task:
        """
        Process a security task by reviewing code for security issues.
        
        Args:
            task: The security task to process
            
        Returns:
            The updated task
        """
        try:
            self.logger.info(f"Processing security task: {task.title}")
            
            files_to_review = self._get_files_to_review(task)
            
            security_results = {}
            critical_issues = []
            warnings = []
            
            for file_path in files_to_review:
                result = self._review_file_security(file_path, task)
                security_results[file_path] = result
                
                critical_issues.extend(result.get("critical_issues", []))
                warnings.extend(result.get("warnings", []))
            
            security_report = {
                "files_reviewed": files_to_review,
                "critical_issues": critical_issues,
                "warnings": warnings,
                "results": security_results,
                "overall_assessment": "passed" if not critical_issues else "failed"
            }
            
            task.metadata["security_report"] = security_report
            task.result = security_report
            self.complete_task(task.id, task.result)
            self.logger.info(f"Completed security task {task.id}")
            
        except Exception as e:
            error_msg = f"Error processing security task: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            self.fail_task(task.id, error_msg)
            
        return task

    def _get_files_to_review(self, task: Task) -> List[str]:
        """Get list of files to review."""
        files = []
        description = task.description.lower()
        
        # Look for Python files
        if "api" in description or "python" in description:
            for root, dirs, filenames in os.walk(os.path.join(self.workspace_path, "api")):
                for filename in filenames:
                    if filename.endswith('.py'):
                        rel_path = os.path.relpath(os.path.join(root, filename), self.workspace_path)
                        files.append(rel_path)
                        if len(files) >= 10:  # Limit to 10 files
                            break
        
        return files[:10]

    def _review_file_security(self, file_path: str, task: Task) -> Dict[str, Any]:
        """Review file for security issues."""
        full_path = os.path.join(self.workspace_path, file_path)
        
        result = {
            "file": file_path,
            "critical_issues": [],
            "warnings": [],
            "security_score": 100
        }
        
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for dangerous functions
            dangerous_patterns = {
                'eval(': ('Use of eval() is dangerous', 20),
                'exec(': ('Use of exec() is dangerous', 20),
                'os.system(': ('os.system() can be dangerous', 10),
                'subprocess.call': ('subprocess without shell=False may be dangerous', 10),
                'pickle.loads': ('pickle.loads() can execute arbitrary code', 20),
            }
            
            for pattern, (message, score) in dangerous_patterns.items():
                if pattern in content:
                    result["critical_issues"].append(f"{message} in {file_path}")
                    result["security_score"] -= score
            
            # Check for hardcoded secrets
            secret_patterns = [
                (r'password\s*=\s*["\'][^"\']+["\']', 'Potential hardcoded password', 15),
                (r'api_key\s*=\s*["\'][^"\']+["\']', 'Potential hardcoded API key', 15),
                (r'secret\s*=\s*["\'][^"\']+["\']', 'Potential hardcoded secret', 15),
                (r'token\s*=\s*["\'][^"\']+["\']', 'Potential hardcoded token', 10),
            ]
            
            for pattern, message, score in secret_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    result["critical_issues"].append(f"{message} in {file_path}")
                    result["security_score"] -= score
            
            # Check for SQL injection risks
            if re.search(r'execute\s*\([^)]*\+', content):
                result["warnings"].append(f"Potential SQL injection risk in {file_path}")
                result["security_score"] -= 5
            
            # Check for insecure HTTP
            if re.search(r'http://', content) and 'localhost' not in content:
                result["warnings"].append(f"Insecure HTTP connection in {file_path}")
                result["security_score"] -= 5
            
            # Check for authentication issues
            if 'oauth' in file_path.lower() or 'auth' in file_path.lower():
                if not re.search(r'state\s*=', content, re.IGNORECASE):
                    result["warnings"].append(f"OAuth flow may be missing state parameter in {file_path}")
                    result["security_score"] -= 5
            
            result["security_score"] = max(0, result["security_score"])
            
        except Exception as e:
            result["critical_issues"].append(f"Error reviewing file: {str(e)}")
            result["security_score"] = 0
        
        self.security_reports[file_path] = result
        return result

