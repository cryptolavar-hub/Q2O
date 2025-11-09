"""
Code Validator - Validates LLM-generated code for quality and security.

Performs comprehensive validation:
- Syntax checking (Python compilation)
- Security scanning (dangerous patterns)
- Type hint verification
- Docstring checking
- Error handling verification
- Cross-LLM validation for critical code (payments, auth, webhooks)
"""

from typing import Dict, List, Optional, Set
import re
import ast
import logging


class ValidationResult:
    """Result of code validation."""
    
    def __init__(self):
        self.passed = True
        self.score = 0
        self.checks = {}
        self.errors = []
        self.warnings = []
        self.recommendations = []
    
    def add_check(self, name: str, passed: bool, message: str = ""):
        """Add a validation check result."""
        self.checks[name] = passed
        if not passed and message:
            self.errors.append(f"{name}: {message}")
    
    def add_warning(self, message: str):
        """Add a warning."""
        self.warnings.append(message)
    
    def add_recommendation(self, message: str):
        """Add a recommendation for improvement."""
        self.recommendations.append(message)
    
    def calculate_score(self) -> int:
        """Calculate overall quality score (0-100)."""
        if not self.checks:
            return 0
        
        passed_count = sum(1 for v in self.checks.values() if v)
        total_count = len(self.checks)
        self.score = int((passed_count / total_count) * 100)
        self.passed = self.score >= int(os.getenv("Q2O_LLM_MIN_QUALITY_SCORE", "95"))
        return self.score
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "passed": self.passed,
            "score": self.score,
            "checks": self.checks,
            "errors": self.errors,
            "warnings": self.warnings,
            "recommendations": self.recommendations
        }


class CodeValidator:
    """
    Validates generated code for quality, security, and best practices.
    
    Minimum quality threshold: 95% (configurable via Q2O_LLM_MIN_QUALITY_SCORE)
    """
    
    # Dangerous patterns that should never appear in generated code
    DANGEROUS_PATTERNS = [
        'eval(',
        'exec(',
        '__import__',
        'os.system(',
        'subprocess.call(',
        'subprocess.run(',
        'compile(',
        'open(' # Without context manager can be dangerous
    ]
    
    # Critical code keywords that trigger cross-LLM validation
    CRITICAL_KEYWORDS = [
        'payment', 'billing', 'stripe', 'charge',
        'auth', 'login', 'password', 'token', 'jwt',
        'webhook', 'signature', 'verify',
        'admin', 'privilege', 'permission',
        'sql', 'query', 'execute', 'database'
    ]
    
    def __init__(self, llm_service: Optional['LLMService'] = None):
        """
        Initialize code validator.
        
        Args:
            llm_service: LLM service for cross-validation (optional)
        """
        self.llm_service = llm_service
        self.min_quality = int(os.getenv("Q2O_LLM_MIN_QUALITY_SCORE", "95"))
        self.cross_validate_enabled = os.getenv("Q2O_LLM_CROSS_VALIDATION", "true").lower() == "true"
        
        logging.info(f"Code Validator initialized (min quality: {self.min_quality}%, cross-validate: {self.cross_validate_enabled})")
    
    def validate(self, code: str, task_description: str = "") -> ValidationResult:
        """
        Perform comprehensive code validation.
        
        Args:
            code: Code to validate
            task_description: Original task (for determining if critical)
        
        Returns:
            ValidationResult with score and details
        """
        result = ValidationResult()
        
        # Check 1: Syntax validation
        syntax_valid = self._check_syntax(code, result)
        
        # Check 2: Security scanning
        self._check_security(code, result)
        
        # Check 3: Type hints
        self._check_type_hints(code, result)
        
        # Check 4: Docstrings
        self._check_docstrings(code, result)
        
        # Check 5: Error handling
        self._check_error_handling(code, result)
        
        # Check 6: Imports
        self._check_imports(code, result)
        
        # Check 7: Logging
        self._check_logging(code, result)
        
        # Calculate score
        final_score = result.calculate_score()
        
        logging.info(f"Validation complete: {final_score}/100 ({len([v for v in result.checks.values() if v])}/{len(result.checks)} checks passed)")
        
        if not result.passed:
            logging.warning(f"Code quality below minimum ({final_score}% < {self.min_quality}%)")
            for error in result.errors:
                logging.warning(f"  - {error}")
        
        return result
    
    def _check_syntax(self, code: str, result: ValidationResult) -> bool:
        """Check if code has valid Python syntax."""
        try:
            compile(code, '<string>', 'exec')
            result.add_check("syntax", True)
            return True
        except SyntaxError as e:
            result.add_check("syntax", False, f"Syntax error at line {e.lineno}: {e.msg}")
            return False
    
    def _check_security(self, code: str, result: ValidationResult):
        """Check for dangerous security patterns."""
        found_dangerous = []
        
        for pattern in self.DANGEROUS_PATTERNS:
            if pattern in code:
                # Exception: 'open(' with 'with' statement is safe
                if pattern == 'open(' and 'with open(' in code:
                    continue
                found_dangerous.append(pattern)
        
        if found_dangerous:
            result.add_check(
                "security",
                False,
                f"Dangerous patterns found: {', '.join(found_dangerous)}"
            )
        else:
            result.add_check("security", True)
    
    def _check_type_hints(self, code: str, result: ValidationResult):
        """Check if functions have type hints."""
        # Look for function definitions
        func_pattern = r'def\s+\w+\s*\([^)]*\)'
        functions = re.findall(func_pattern, code)
        
        if not functions:
            # No functions to check
            result.add_check("type_hints", True)
            return
        
        # Check if type hints are present
        has_hints = '->' in code or ': str' in code or ': int' in code or ': Dict' in code or ': List' in code
        
        if has_hints:
            result.add_check("type_hints", True)
        else:
            result.add_check("type_hints", False, "Missing type hints on functions")
            result.add_recommendation("Add type hints to all functions for better code quality")
    
    def _check_docstrings(self, code: str, result: ValidationResult):
        """Check if code has docstrings."""
        # Check for module docstring or function docstrings
        has_docstrings = '"""' in code or "'''" in code
        
        if has_docstrings:
            result.add_check("docstrings", True)
        else:
            result.add_check("docstrings", False, "Missing docstrings")
            result.add_recommendation("Add docstrings to improve code documentation")
    
    def _check_error_handling(self, code: str, result: ValidationResult):
        """Check if code has proper error handling."""
        # Look for try/except or raise statements
        has_error_handling = 'try:' in code or 'except' in code or 'raise' in code
        
        if has_error_handling:
            result.add_check("error_handling", True)
        else:
            # Check if it's simple code that might not need error handling
            is_simple = 'def' not in code or code.count('\n') < 20
            
            if is_simple:
                result.add_check("error_handling", True)
                result.add_warning("Simple code - error handling optional")
            else:
                result.add_check("error_handling", False, "Missing error handling")
                result.add_recommendation("Add try/except blocks for robust error handling")
    
    def _check_imports(self, code: str, result: ValidationResult):
        """Check if code has necessary imports."""
        # Basic check - does it have imports?
        has_imports = 'import' in code or 'from' in code
        
        if has_imports:
            result.add_check("imports", True)
        else:
            # Might be just a code snippet
            result.add_check("imports", True)
            result.add_warning("No imports found - might be incomplete code")
    
    def _check_logging(self, code: str, result: ValidationResult):
        """Check if code has logging."""
        # Look for logging statements
        has_logging = ('logging.' in code or 
                      'logger.' in code or 
                      'log.' in code or
                      'print(' in code)  # Print is acceptable for simple code
        
        if has_logging:
            result.add_check("logging", True)
        else:
            # Optional for very simple code
            is_simple = code.count('\n') < 15
            if is_simple:
                result.add_check("logging", True)
            else:
                result.add_check("logging", False, "Missing logging")
                result.add_recommendation("Add logging for better observability")
    
    def needs_cross_validation(self, task_description: str) -> bool:
        """
        Determine if task needs cross-LLM validation.
        
        Critical tasks (payments, auth, webhooks) should be validated
        by a second LLM for additional security.
        
        Args:
            task_description: Original task description
        
        Returns:
            True if cross-validation recommended
        """
        if not self.cross_validate_enabled:
            return False
        
        task_lower = task_description.lower()
        
        # Check if any critical keywords present
        return any(keyword in task_lower for keyword in self.CRITICAL_KEYWORDS)
    
    async def cross_validate(
        self,
        code: str,
        task_description: str,
        original_provider: str
    ) -> Dict:
        """
        Use a DIFFERENT LLM to review the code.
        
        This provides an independent second opinion for critical code.
        
        Args:
            code: Code to review
            task_description: What it's supposed to do
            original_provider: Which LLM generated it
        
        Returns:
            Review results from secondary LLM
        """
        if not self.llm_service:
            logging.warning("Cross-validation requested but no LLM service available")
            return {"skipped": True, "reason": "No LLM service"}
        
        logging.info(f"[CROSS-VALIDATE] Using secondary LLM to review code from {original_provider}")
        
        # Choose different provider for review
        review_providers = {
            "gemini": "openai",
            "openai": "anthropic",
            "anthropic": "gemini"
        }
        review_provider = review_providers.get(original_provider, "openai")
        
        system_prompt = """You are a senior code security and quality reviewer.

Analyze this code for:
1. Security vulnerabilities (SQL injection, XSS, insecure patterns)
2. Logic errors or bugs
3. Performance issues
4. Best practice violations
5. Edge cases not handled
6. Type safety issues

Be thorough but fair. Code doesn't have to be perfect, but must be secure and functional.

Return JSON:
{
  "issues": [
    {"severity": "critical|high|medium|low", "description": "..."}
  ],
  "overall_severity": "none|low|medium|high|critical",
  "recommendation": "approve|fix|reject",
  "score": 0-100,
  "summary": "Brief assessment"
}"""
        
        user_prompt = f"""Task: {task_description}

Code to review:
```python
{code}
```

Provide security and quality assessment in JSON format."""
        
        try:
            from utils.llm_service import LLMProvider
            response = await self.llm_service.complete(
                system_prompt,
                user_prompt,
                temperature=0.2,  # Low for analytical review
                max_tokens=2048,
                provider=LLMProvider(review_provider) if hasattr(LLMProvider, review_provider.upper()) else None
            )
            
            if not response.success:
                return {"skipped": True, "reason": f"Review LLM failed: {response.error}"}
            
            # Parse JSON from response
            import json
            content = response.content
            
            # Extract JSON if wrapped in markdown
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            review_result = json.loads(content.strip())
            
            logging.info(f"[CROSS-VALIDATE] Review complete: {review_result.get('recommendation', 'unknown')} (score: {review_result.get('score', 0)}/100)")
            
            return {
                "review_provider": review_provider,
                "review_result": review_result,
                "cost": response.usage.total_cost if response.usage else 0.0
            }
            
        except Exception as e:
            logging.error(f"Cross-validation failed: {e}")
            return {"skipped": True, "reason": f"Exception: {str(e)}"}
    
    def validate_with_cross_check(
        self,
        code: str,
        task_description: str,
        original_provider: str
    ) -> ValidationResult:
        """
        Validate code with optional cross-LLM check for critical tasks.
        
        Args:
            code: Code to validate
            task_description: Original task
            original_provider: Which LLM generated it
        
        Returns:
            ValidationResult with cross-check results if applicable
        """
        # Standard validation first
        result = self.validate(code, task_description)
        
        # Determine if cross-check needed
        if self.needs_cross_validation(task_description) and result.passed:
            logging.info(f"[CRITICAL] Task involves: {self._get_critical_aspects(task_description)}")
            logging.info(f"[CROSS-CHECK] Requesting secondary LLM review...")
            
            # Run cross-validation asynchronously
            import asyncio
            loop = asyncio.get_event_loop()
            cross_check = loop.run_until_complete(
                self.cross_validate(code, task_description, original_provider)
            )
            
            if not cross_check.get('skipped'):
                review = cross_check['review_result']
                
                # Check review recommendation
                if review.get('recommendation') == 'reject':
                    result.passed = False
                    result.errors.append(f"Cross-validation REJECTED: {review.get('summary', 'Critical issues found')}")
                    logging.warning(f"[REJECT] Cross-validation rejected code")
                
                elif review.get('overall_severity') in ['high', 'critical']:
                    result.passed = False
                    result.errors.append(f"Cross-validation found {review['overall_severity']} severity issues")
                    logging.warning(f"[REJECT] High severity issues found")
                
                else:
                    logging.info(f"[APPROVED] Cross-validation passed (score: {review.get('score', 0)}/100)")
                
                # Add cross-check details to result
                result.checks['cross_validation'] = review.get('recommendation') == 'approve'
                
                # Log cost
                if cross_check.get('cost'):
                    logging.info(f"[CROSS-CHECK] Cost: ${cross_check['cost']:.4f}")
        
        return result
    
    def _get_critical_aspects(self, task_description: str) -> List[str]:
        """Identify which critical aspects are in the task."""
        task_lower = task_description.lower()
        found = []
        
        if any(kw in task_lower for kw in ['payment', 'billing', 'stripe']):
            found.append("payments")
        if any(kw in task_lower for kw in ['auth', 'login', 'password']):
            found.append("authentication")
        if 'webhook' in task_lower:
            found.append("webhooks")
        if any(kw in task_lower for kw in ['admin', 'privilege']):
            found.append("admin")
        if any(kw in task_lower for kw in ['sql', 'database', 'query']):
            found.append("database")
        
        return found


# Import os at module level
import os


# Convenience function
_validator_instance = None

def get_code_validator(llm_service: Optional['LLMService'] = None) -> CodeValidator:
    """Get singleton code validator instance."""
    global _validator_instance
    if _validator_instance is None:
        _validator_instance = CodeValidator(llm_service=llm_service)
    return _validator_instance

