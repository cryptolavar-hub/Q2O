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
                 tenant_id: Optional[int] = None,
                 orchestrator: Optional[Any] = None):
        # CRITICAL: Pass workspace_path to super() to ensure BaseAgent validates it
        super().__init__(
            agent_id, 
            AgentType.QA, 
            workspace_path=workspace_path,
            project_id=project_id, 
            tenant_id=tenant_id, 
            orchestrator=orchestrator
        )
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
            
            # QA_Engineer: Analyze project structure completeness
            structure_analysis = self._analyze_project_structure(task)
            
            # Update task metadata
            task.metadata["qa_results"] = qa_results
            task.metadata["qa_report"] = qa_report
            task.metadata["structure_analysis"] = structure_analysis
            
            task.result = {
                "files_reviewed": files_to_review,
                "qa_results": qa_results,
                "overall_score": avg_score,
                "qa_report": qa_report,
                "structure_analysis": structure_analysis,
                "status": "passed" if avg_score >= 70 else "needs_improvement"
            }
            
            # If structure is incomplete, notify Orchestrator
            if structure_analysis.get("missing_components"):
                self._notify_orchestrator_missing_tasks(structure_analysis, task)

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
    
    def _analyze_project_structure(self, task: Task) -> Dict[str, Any]:
        """
        Analyze if project structure is complete based on tech stack and objective.
        
        QA_Engineer: This method checks if all expected directories and files exist
        for a complete project structure. It detects missing components, services,
        hooks, types, utils, etc.
        
        **ENHANCED**: Now uses project structure blueprint from Orchestrator if available.
        This is like an inspector having the blueprint before checking the work site.
        
        Args:
            task: The QA task
        
        Returns:
            {
                "is_complete": bool,
                "missing_components": [
                    {"type": "component", "name": "Button", "path": "src/components/Button.tsx"},
                    {"type": "service", "name": "authService", "path": "src/services/authService.ts"},
                    ...
                ],
                "existing_components": [...],
                "recommendations": [...]
            }
        """
        structure_analysis = {
            "is_complete": True,
            "missing_components": [],
            "existing_components": [],
            "recommendations": []
        }
        
        # QA_Engineer: Get project structure blueprint from Orchestrator (if available)
        # This is the "blueprint" that tells us what SHOULD exist
        structure_blueprint = None
        if self.orchestrator and hasattr(self.orchestrator, 'get_project_structure_blueprint'):
            try:
                structure_blueprint = self.orchestrator.get_project_structure_blueprint()
                if structure_blueprint:
                    self.logger.info(
                        f"[BLUEPRINT] Using structure blueprint for {structure_blueprint.get('project_type', 'unknown')} project"
                    )
            except Exception as e:
                self.logger.debug(f"Could not get structure blueprint from Orchestrator: {e}")
        
        # Determine expected structure based on tech stack
        tech_stack = task.metadata.get("tech_stack", [])
        objective_type = task.metadata.get("objective_type", "unknown")
        project_metadata = task.metadata.get("project_metadata", {})
        objective_classification = project_metadata.get("objective_classification", {})
        
        # Get objective type from classification if available
        if objective_classification:
            objective_type = objective_classification.get("type", objective_type)
            tech_stack = objective_classification.get("tech_stack", tech_stack)
        
        # QA_Engineer: Use blueprint if available, otherwise fall back to hardcoded expectations
        if structure_blueprint:
            # Use blueprint to check structure
            expected_dirs = structure_blueprint.get("expected_directories", [])
            expected_files = structure_blueprint.get("expected_files", [])
            
            self.logger.info(
                f"[BLUEPRINT] Checking {len(expected_dirs)} directories and {len(expected_files)} files "
                f"from blueprint"
            )
            
            # Check directories from blueprint
            for dir_spec in expected_dirs:
                dir_path = dir_spec.get("path", "")
                required = dir_spec.get("required", True)
                description = dir_spec.get("description", "")
                
                full_path = os.path.join(self.workspace_path, dir_path)
                if os.path.exists(full_path):
                    try:
                        files = [f for f in os.listdir(full_path) 
                                if os.path.isfile(os.path.join(full_path, f)) and not f.startswith('.')]
                        if not files:
                            # QA_Engineer: Check if files exist in wrong location (e.g., web/components instead of src/components)
                            wrong_location = self._check_wrong_location(dir_path)
                            if wrong_location:
                                structure_analysis["missing_components"].append({
                                    "type": dir_path.split("/")[-1],
                                    "name": f"{dir_path} directory",
                                    "path": dir_path,
                                    "reason": f"Directory exists but is empty. Files found in wrong location: {wrong_location}",
                                    "required": required,
                                    "wrong_location": wrong_location
                                })
                            else:
                                structure_analysis["missing_components"].append({
                                    "type": dir_path.split("/")[-1],
                                    "name": f"{dir_path} directory",
                                    "path": dir_path,
                                    "reason": f"Directory exists but is empty ({description})",
                                    "required": required
                                })
                            if required:
                                structure_analysis["is_complete"] = False
                        else:
                            structure_analysis["existing_components"].append({
                                "type": dir_path.split("/")[-1],
                                "path": dir_path,
                                "file_count": len(files),
                                "description": description
                            })
                    except Exception as e:
                        self.logger.debug(f"Error checking directory {dir_path}: {e}")
                else:
                    structure_analysis["missing_components"].append({
                        "type": dir_path.split("/")[-1],
                        "name": f"{dir_path} directory",
                        "path": dir_path,
                        "reason": f"Directory does not exist ({description})",
                        "required": required
                    })
                    if required:
                        structure_analysis["is_complete"] = False
            
            # Check files from blueprint
            for file_spec in expected_files:
                file_path = file_spec.get("path", "")
                required = file_spec.get("required", True)
                description = file_spec.get("description", "")
                
                full_path = os.path.join(self.workspace_path, file_path)
                if not os.path.exists(full_path):
                    structure_analysis["missing_components"].append({
                        "type": "file",
                        "name": file_path.split("/")[-1],
                        "path": file_path,
                        "reason": f"File does not exist ({description})",
                        "required": required
                    })
                    if required:
                        structure_analysis["is_complete"] = False
                else:
                    structure_analysis["existing_components"].append({
                        "type": "file",
                        "path": file_path,
                        "description": description
                    })
            
            # Use blueprint-based analysis
            return structure_analysis
        
        # Check for React Native mobile app
        if "React Native" in str(tech_stack) or "Expo" in str(tech_stack) or objective_type == "mobile_app":
            expected_dirs = {
                "components": "src/components/",
                "services": "src/services/",
                "hooks": "src/hooks/",
                "store": "src/store/",
                "theme": "src/theme/",
                "types": "src/types/",
                "utils": "src/utils/"
            }
            
            for dir_name, dir_path in expected_dirs.items():
                full_path = os.path.join(self.workspace_path, dir_path)
                if os.path.exists(full_path):
                    # Check if directory is empty
                    try:
                        files = [f for f in os.listdir(full_path) 
                                if os.path.isfile(os.path.join(full_path, f)) and not f.startswith('.')]
                        if not files:
                            structure_analysis["missing_components"].append({
                                "type": dir_name,
                                "name": f"{dir_name} directory",
                                "path": dir_path,
                                "reason": "Directory exists but is empty"
                            })
                            structure_analysis["is_complete"] = False
                        else:
                            structure_analysis["existing_components"].append({
                                "type": dir_name,
                                "path": dir_path,
                                "file_count": len(files)
                            })
                    except Exception as e:
                        self.logger.debug(f"Error checking directory {dir_path}: {e}")
                else:
                    structure_analysis["missing_components"].append({
                        "type": dir_name,
                        "name": f"{dir_name} directory",
                        "path": dir_path,
                        "reason": "Directory does not exist"
                    })
                    structure_analysis["is_complete"] = False
        
        # Check for Next.js web app
        elif "Next.js" in str(tech_stack) or ("React" in str(tech_stack) and objective_type == "web_app"):
            expected_dirs = {
                "components": "src/components/",
                "services": "src/services/",
                "hooks": "src/hooks/",
                "utils": "src/utils/",
                "types": "src/types/",
                "styles": "src/styles/"
            }
            
            for dir_name, dir_path in expected_dirs.items():
                full_path = os.path.join(self.workspace_path, dir_path)
                if os.path.exists(full_path):
                    try:
                        files = [f for f in os.listdir(full_path) 
                                if os.path.isfile(os.path.join(full_path, f)) and not f.startswith('.')]
                        if not files:
                            structure_analysis["missing_components"].append({
                                "type": dir_name,
                                "name": f"{dir_name} directory",
                                "path": dir_path,
                                "reason": "Directory exists but is empty"
                            })
                            structure_analysis["is_complete"] = False
                    except Exception:
                        pass
                else:
                    structure_analysis["missing_components"].append({
                        "type": dir_name,
                        "name": f"{dir_name} directory",
                        "path": dir_path,
                        "reason": "Directory does not exist"
                    })
                    structure_analysis["is_complete"] = False
        
        # Check for Python backend
        elif "FastAPI" in str(tech_stack) or ("Python" in str(tech_stack) and objective_type == "api_service"):
            expected_dirs = {
                "services": "src/services/",
                "models": "src/models/",
                "schemas": "src/schemas/",
                "utils": "src/utils/",
                "config": "src/config/"
            }
            
            for dir_name, dir_path in expected_dirs.items():
                full_path = os.path.join(self.workspace_path, dir_path)
                if os.path.exists(full_path):
                    try:
                        files = [f for f in os.listdir(full_path) 
                                if os.path.isfile(os.path.join(full_path, f)) and not f.startswith('.')]
                        if not files:
                            structure_analysis["missing_components"].append({
                                "type": dir_name,
                                "name": f"{dir_name} directory",
                                "path": dir_path,
                                "reason": "Directory exists but is empty"
                            })
                            structure_analysis["is_complete"] = False
                    except Exception:
                        pass
                else:
                    structure_analysis["missing_components"].append({
                        "type": dir_name,
                        "name": f"{dir_name} directory",
                        "path": dir_path,
                        "reason": "Directory does not exist"
                    })
                    structure_analysis["is_complete"] = False
        
        # Generate recommendations
        if structure_analysis["missing_components"]:
            structure_analysis["recommendations"].append(
                f"Project structure is incomplete. Missing {len(structure_analysis['missing_components'])} components. "
                "Consider creating tasks to generate missing components, services, hooks, types, and utilities."
            )
        
        return structure_analysis
    
    def _check_wrong_location(self, expected_path: str) -> Optional[str]:
        """
        QA_Engineer: Check if files exist in wrong location (e.g., web/components instead of src/components).
        
        This helps identify when tasks created files but in the wrong directory structure.
        
        Args:
            expected_path: The expected directory path (e.g., "src/components")
            
        Returns:
            Path where files were found (if wrong location), None otherwise
        """
        try:
            # Common wrong location patterns
            wrong_locations = []
            
            # If expecting src/components, check web/components
            if "src/components" in expected_path:
                wrong_locations.append("web/components")
            if "src/hooks" in expected_path:
                wrong_locations.append("web/components")  # Hooks might be in web/components
            if "src/store" in expected_path:
                wrong_locations.append("web/components")  # Store might be in web/components
            if "src/theme" in expected_path:
                wrong_locations.append("web/components")  # Theme might be in web/components
            
            # Check each wrong location
            for wrong_path in wrong_locations:
                full_wrong_path = os.path.join(self.workspace_path, wrong_path)
                if os.path.exists(full_wrong_path):
                    try:
                        files = [f for f in os.listdir(full_wrong_path) 
                                if os.path.isfile(os.path.join(full_wrong_path, f)) and not f.startswith('.')]
                        if files:
                            # Found files in wrong location
                            self.logger.warning(
                                f"[QA] Found {len(files)} files in wrong location: {wrong_path} "
                                f"(expected: {expected_path})"
                            )
                            return wrong_path
                    except Exception:
                        pass
            
            return None
        except Exception as e:
            self.logger.debug(f"Error checking wrong location for {expected_path}: {e}")
            return None
    
    def _notify_orchestrator_missing_tasks(self, structure_analysis: Dict, task: Task):
        """
        Notify Orchestrator about missing tasks that need to be created.
        
        QA_Engineer: When QA detects missing components, it sends a message to
        the Orchestrator to create tasks for generating those components.
        
        Args:
            structure_analysis: Structure analysis results
            task: The QA task
        """
        try:
            from utils.message_protocol import MessageType, AgentMessage
            from utils.message_broker import get_default_broker
            import uuid
            
            if not self.enable_messaging:
                self.logger.debug("Messaging disabled, skipping Orchestrator notification")
                return
            
            message = AgentMessage(
                message_id=str(uuid.uuid4()),
                message_type=MessageType.COORDINATION,
                sender_agent_id=self.agent_id,
                sender_agent_type=self.agent_type.value,
                payload={
                    "action": "missing_tasks_detected",
                    "project_id": self.project_id,
                    "missing_components": structure_analysis.get("missing_components", []),
                    "task_id": task.id,
                    "recommendations": structure_analysis.get("recommendations", [])
                },
                target_agent_type="orchestrator",
                channel="agents.orchestrator"
            )
            
            broker = get_default_broker()
            broker.publish(message.channel, message.to_dict())
            
            self.logger.info(
                f"Notified Orchestrator of {len(structure_analysis.get('missing_components', []))} "
                f"missing components for project {self.project_id}"
            )
        except Exception as e:
            self.logger.error(f"Failed to notify Orchestrator: {e}", exc_info=True)

