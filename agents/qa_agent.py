"""
QA Agent - Performs quality assurance reviews on code and tests.
"""

from typing import Dict, Any, List, Optional
from agents.base_agent import BaseAgent, AgentType, Task, TaskStatus
from utils.code_quality_scanner import get_quality_scanner
import os
import logging
import re


class QAAgent(BaseAgent):
    """Agent responsible for quality assurance reviews."""

    def __init__(self, agent_id: str = "qa_main", workspace_path: str = ".",
                 project_id: Optional[str] = None,
                 tenant_id: Optional[int] = None):
        super().__init__(agent_id, AgentType.QA, project_id=project_id, tenant_id=tenant_id)
        self.workspace_path = workspace_path
        self.reviewed_files: List[str] = []
        self.qa_reports: Dict[str, Dict[str, Any]] = {}
        self.quality_scanner = get_quality_scanner(workspace_path)

    def process_task(self, task: Task) -> Task:
        """
        Process a QA task by reviewing code and tests.
        
        Args:
            task: The QA task to process
            
        Returns:
            The updated task
        """
        try:
            self.logger.info(f"Processing QA task: {task.title}")
            
            # Get files to review
            files_to_review = self._get_files_to_review(task)
            
            if not files_to_review:
                self.logger.warning(f"No files found to review for task {task.id}")
                task.metadata["warning"] = "No files to review"
            
            # Perform QA review
            qa_results = {}
            overall_score = 0
            total_files = len(files_to_review)
            
            for file_path in files_to_review:
                review_result = self._review_file(file_path, task)
                qa_results[file_path] = review_result
                overall_score += review_result.get("score", 0)
                self.reviewed_files.append(file_path)
            
            avg_score = overall_score / total_files if total_files > 0 else 0
            
            # Generate overall QA report
            qa_report = self._generate_qa_report(qa_results, task)
            
            # Update task metadata
            task.metadata["qa_results"] = qa_results
            task.metadata["qa_report"] = qa_report
            task.result = {
                "files_reviewed": files_to_review,
                "qa_results": qa_results,
                "overall_score": avg_score,
                "qa_report": qa_report,
                "status": "passed" if avg_score >= 70 else "needs_improvement"
            }

            self.complete_task(task.id, task.result)
            self.logger.info(f"Completed QA task {task.id} with score {avg_score:.2f}")
            
        except Exception as e:
            error_msg = f"Error processing QA task: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            self.fail_task(task.id, error_msg)
            
        return task

    def _get_files_to_review(self, task: Task) -> List[str]:
        """
        Get list of files to review (code and tests).
        
        Args:
            task: The QA task
            
        Returns:
            List of file paths to review
        """
        files_to_review = []
        
        # Check task dependencies for implemented files and test files
        objective = task.metadata.get("objective", task.title)
        
        # Look for source files
        potential_source = f"src/{objective.lower().replace(' ', '_')}.py"
        full_source_path = os.path.join(self.workspace_path, potential_source)
        if os.path.exists(full_source_path):
            files_to_review.append(potential_source)
        
        # Look for test files
        test_file = f"tests/test_{objective.lower().replace(' ', '_')}.py"
        full_test_path = os.path.join(self.workspace_path, test_file)
        if os.path.exists(full_test_path):
            files_to_review.append(test_file)
        
        # Search for Python files in workspace if nothing specific found
        if not files_to_review:
            for root, dirs, files in os.walk(self.workspace_path):
                # Skip common non-source directories
                if any(skip in root for skip in ['.git', '__pycache__', 'venv', '.venv', 'node_modules']):
                    continue
                
                for file in files:
                    if file.endswith('.py') and not file.startswith('test_'):
                        rel_path = os.path.relpath(os.path.join(root, file), self.workspace_path)
                        files_to_review.append(rel_path)
                        if len(files_to_review) >= 5:  # Limit to 5 files for performance
                            break
                
                if len(files_to_review) >= 5:
                    break
        
        return files_to_review[:5]  # Limit to 5 files

    def _review_file(self, file_path: str, task: Task) -> Dict[str, Any]:
        """
        Review a single file for quality issues.
        
        Args:
            file_path: Path to the file to review
            task: The QA task
            
        Returns:
            Dictionary with review results
        """
        full_path = os.path.join(self.workspace_path, file_path)
        
        review_result = {
            "file": file_path,
            "score": 100,
            "issues": [],
            "strengths": [],
            "recommendations": []
        }
        
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Perform various checks
            checks = [
                self._check_documentation,
                self._check_code_style,
                self._check_error_handling,
                self._check_complexity,
                self._check_naming_conventions,
                self._check_security
            ]
            
            for check in checks:
                result = check(content, file_path)
                if result.get("issues"):
                    review_result["issues"].extend(result["issues"])
                    review_result["score"] -= result.get("score_deduction", 0)
                if result.get("strengths"):
                    review_result["strengths"].extend(result["strengths"])
                if result.get("recommendations"):
                    review_result["recommendations"].extend(result["recommendations"])
            
            # Run external quality scanners for Python files
            if file_path.endswith('.py'):
                # mypy type checking
                mypy_errors = self.quality_scanner.check_types_with_mypy(full_path)
                if mypy_errors:
                    review_result["issues"].extend([f"mypy: {err}" for err in mypy_errors[:5]])  # Limit to 5
                    review_result["score"] -= min(len(mypy_errors) * 2, 20)
                
                # ruff linting
                ruff_issues = self.quality_scanner.lint_with_ruff(full_path)
                if ruff_issues:
                    review_result["issues"].extend([f"ruff: {issue}" for issue in ruff_issues[:5]])  # Limit to 5
                    review_result["score"] -= min(len(ruff_issues), 15)
                
                # black formatting
                black_issues = self.quality_scanner.check_format_with_black(full_path)
                if black_issues:
                    review_result["recommendations"].append("Code formatting issues detected - run 'black' to fix")
                    review_result["score"] -= 5
            
            # Ensure score doesn't go below 0
            review_result["score"] = max(0, review_result["score"])
            
            # Generate overall assessment
            if review_result["score"] >= 90:
                review_result["assessment"] = "excellent"
            elif review_result["score"] >= 70:
                review_result["assessment"] = "good"
            elif review_result["score"] >= 50:
                review_result["assessment"] = "acceptable"
            else:
                review_result["assessment"] = "needs_improvement"
            
        except Exception as e:
            review_result["issues"].append(f"Error reviewing file: {str(e)}")
            review_result["score"] = 0
            self.logger.error(f"Error reviewing {file_path}: {str(e)}")
        
        self.qa_reports[file_path] = review_result
        return review_result

    def _check_documentation(self, content: str, file_path: str) -> Dict[str, Any]:
        """Check for documentation."""
        result = {
            "issues": [],
            "strengths": [],
            "score_deduction": 0,
            "recommendations": []
        }
        
        # Check for module docstring
        if not content.strip().startswith('"""') and not content.strip().startswith("'''"):
            result["issues"].append("Missing module-level docstring")
            result["score_deduction"] += 5
        else:
            result["strengths"].append("Has module-level docstring")
        
        # Check for class/function docstrings
        class_pattern = r'class\s+\w+'
        function_pattern = r'def\s+\w+\s*\('
        
        classes = re.findall(class_pattern, content)
        functions = re.findall(function_pattern, content)
        
        # Simplified check - look for docstrings after definitions
        if classes or functions:
            # Check if there are docstrings
            docstring_pattern = r'""".*?"""'
            docstring_pattern2 = r"'''.*?'''"
            docstrings = len(re.findall(docstring_pattern, content, re.DOTALL))
            docstrings += len(re.findall(docstring_pattern2, content, re.DOTALL))
            
            total_definitions = len(classes) + len(functions)
            if docstrings < total_definitions * 0.7:  # 70% should have docstrings
                result["issues"].append(f"Missing docstrings for some classes/functions ({docstrings}/{total_definitions})")
                result["score_deduction"] += 5
            else:
                result["strengths"].append("Good documentation coverage")
        
        return result

    def _check_code_style(self, content: str, file_path: str) -> Dict[str, Any]:
        """Check code style."""
        result = {
            "issues": [],
            "strengths": [],
            "score_deduction": 0,
            "recommendations": []
        }
        
        lines = content.split('\n')
        
        # Check line length
        long_lines = [i+1 for i, line in enumerate(lines) if len(line) > 120]
        if long_lines:
            result["issues"].append(f"Lines exceeding 120 characters: {len(long_lines)} lines")
            result["score_deduction"] += 2
        
        # Check for trailing whitespace
        trailing_ws = sum(1 for line in lines if line.rstrip() != line and line.strip())
        if trailing_ws > 0:
            result["issues"].append(f"Trailing whitespace found in {trailing_ws} lines")
            result["score_deduction"] += 1
        
        # Check imports organization
        import_lines = [i for i, line in enumerate(lines) if line.strip().startswith('import') or line.strip().startswith('from')]
        if import_lines:
            # Check if imports are at the top
            non_empty_before_imports = sum(1 for i in range(import_lines[0]) if lines[i].strip())
            if non_empty_before_imports > 0:
                result["issues"].append("Imports should be at the top of the file")
                result["score_deduction"] += 2
        
        return result

    def _check_error_handling(self, content: str, file_path: str) -> Dict[str, Any]:
        """Check for error handling."""
        result = {
            "issues": [],
            "strengths": [],
            "score_deduction": 0,
            "recommendations": []
        }
        
        # Check for try-except blocks
        try_blocks = len(re.findall(r'\btry\s*:', content))
        except_blocks = len(re.findall(r'\bexcept\b', content))
        
        # Check for functions that might need error handling
        function_pattern = r'def\s+(\w+)\s*\('
        functions = re.findall(function_pattern, content)
        
        # Files with external operations should have error handling
        has_external_ops = any(keyword in content.lower() for keyword in ['open(', 'request', 'fetch', 'sql', 'api'])
        
        if has_external_ops and try_blocks == 0:
            result["issues"].append("Missing error handling for external operations")
            result["score_deduction"] += 10
        elif try_blocks > 0:
            result["strengths"].append("Good error handling with try-except blocks")
        
        return result

    def _check_complexity(self, content: str, file_path: str) -> Dict[str, Any]:
        """Check code complexity."""
        result = {
            "issues": [],
            "strengths": [],
            "score_deduction": 0,
            "recommendations": []
        }
        
        # Simple complexity check - count nested levels
        lines = content.split('\n')
        max_indent = max((len(line) - len(line.lstrip())) for line in lines if line.strip()) if lines else 0
        
        if max_indent > 20:  # More than 5 levels of nesting (assuming 4 spaces per level)
            result["issues"].append("High nesting complexity detected")
            result["score_deduction"] += 3
            result["recommendations"].append("Consider refactoring to reduce nesting levels")
        
        # Check for very long functions
        function_pattern = r'def\s+\w+\s*\([^)]*\):\s*'
        functions = list(re.finditer(function_pattern, content))
        
        for i, func_match in enumerate(functions):
            start_pos = func_match.end()
            end_pos = functions[i+1].start() if i+1 < len(functions) else len(content)
            func_content = content[start_pos:end_pos]
            func_lines = func_content.split('\n')
            # Count actual code lines (not empty or comments)
            code_lines = sum(1 for line in func_lines if line.strip() and not line.strip().startswith('#'))
            
            if code_lines > 50:
                result["issues"].append(f"Function with {code_lines} lines - consider breaking into smaller functions")
                result["score_deduction"] += 2
        
        return result

    def _check_naming_conventions(self, content: str, file_path: str) -> Dict[str, Any]:
        """Check naming conventions."""
        result = {
            "issues": [],
            "strengths": [],
            "score_deduction": 0,
            "recommendations": []
        }
        
        # Check class names (should be PascalCase)
        class_pattern = r'class\s+([a-z_]\w+)'
        class_names = re.findall(class_pattern, content)
        for class_name in class_names:
            if not class_name[0].isupper():
                result["issues"].append(f"Class name '{class_name}' should be PascalCase")
                result["score_deduction"] += 1
        
        # Check function names (should be snake_case)
        function_pattern = r'def\s+([A-Z]\w+)\s*\('
        function_names = re.findall(function_pattern, content)
        for func_name in function_names:
            if func_name[0].isupper() and not func_name.startswith('__'):
                result["issues"].append(f"Function name '{func_name}' should be snake_case")
                result["score_deduction"] += 1
        
        return result

    def _check_security(self, content: str, file_path: str) -> Dict[str, Any]:
        """Check for security issues."""
        result = {
            "issues": [],
            "strengths": [],
            "score_deduction": 0,
            "recommendations": []
        }
        
        # Check for common security issues
        security_patterns = {
            'eval(': 'Use of eval() is dangerous - security risk',
            'exec(': 'Use of exec() is dangerous - security risk',
            'os.system(': 'Use of os.system() can be dangerous - prefer subprocess',
            'pickle.loads': 'Use of pickle.loads() can be unsafe - security risk',
        }
        
        for pattern, message in security_patterns.items():
            if pattern in content:
                result["issues"].append(message)
                result["score_deduction"] += 10
                result["recommendations"].append(f"Review use of {pattern} for security implications")
        
        # Check for hardcoded credentials
        if re.search(r'password\s*=\s*["\'][^"\']+["\']', content, re.IGNORECASE):
            result["issues"].append("Potential hardcoded password detected")
            result["score_deduction"] += 15
        
        return result

    def _generate_qa_report(self, qa_results: Dict[str, Dict[str, Any]], task: Task) -> Dict[str, Any]:
        """
        Generate overall QA report.
        
        Args:
            qa_results: Results from file reviews
            task: The QA task
            
        Returns:
            Dictionary with QA report
        """
        total_files = len(qa_results)
        total_issues = sum(len(result.get("issues", [])) for result in qa_results.values())
        avg_score = sum(result.get("score", 0) for result in qa_results.values()) / total_files if total_files > 0 else 0
        
        all_issues = []
        all_strengths = []
        all_recommendations = []
        
        for result in qa_results.values():
            all_issues.extend(result.get("issues", []))
            all_strengths.extend(result.get("strengths", []))
            all_recommendations.extend(result.get("recommendations", []))
        
        report = {
            "overall_assessment": "passed" if avg_score >= 70 else "needs_improvement",
            "average_score": avg_score,
            "total_files_reviewed": total_files,
            "total_issues_found": total_issues,
            "critical_issues": len([i for i in all_issues if "security" in i.lower() or "dangerous" in i.lower()]),
            "summary": {
                "issues": all_issues[:10],  # Top 10 issues
                "strengths": list(set(all_strengths)),
                "recommendations": list(set(all_recommendations))[:5]  # Top 5 recommendations
            }
        }
        
        return report

