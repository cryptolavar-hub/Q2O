"""
Metrics calculation and aggregation for dashboard.
Integrates static analysis results with system metrics.
"""

from typing import Dict, Any, List
from datetime import datetime, timedelta
from collections import defaultdict

from utils.security_scanner import get_scanner
from utils.code_quality_scanner import get_quality_scanner


class MetricsCalculator:
    """Calculate and aggregate metrics for dashboard."""
    
    def __init__(self, workspace_path: str = "."):
        self.workspace_path = workspace_path
        self.security_scanner = get_scanner(workspace_path)
        self.quality_scanner = get_quality_scanner(workspace_path)
        
        # Aggregated metrics
        self.static_analysis_results: Dict[str, Any] = {
            "security_issues": [],
            "quality_issues": [],
            "last_scan": None
        }
    
    def calculate_security_metrics(self, file_path: str) -> Dict[str, Any]:
        """
        Calculate security metrics for a file.
        
        Args:
            file_path: Path to file to analyze
            
        Returns:
            Security metrics dictionary
        """
        metrics = {
            "bandit_issues": [],
            "semgrep_issues": [],
            "total_security_issues": 0,
            "critical_issues": 0,
            "high_issues": 0,
            "medium_issues": 0
        }
        
        if file_path.endswith('.py'):
            # Run bandit scan
            bandit_issues = self.security_scanner.scan_with_bandit(file_path)
            metrics["bandit_issues"] = bandit_issues
            metrics["total_security_issues"] += len(bandit_issues)
            
            # Categorize by severity
            for issue in bandit_issues:
                severity = issue.get("issue_severity", "MEDIUM").upper()
                if severity in ["CRITICAL"]:
                    metrics["critical_issues"] += 1
                elif severity in ["HIGH"]:
                    metrics["high_issues"] += 1
                else:
                    metrics["medium_issues"] += 1
            
            # Run semgrep scan
            semgrep_issues = self.security_scanner.scan_with_semgrep(file_path)
            metrics["semgrep_issues"] = semgrep_issues
            metrics["total_security_issues"] += len(semgrep_issues)
            
            # Update aggregated results
            self.static_analysis_results["security_issues"].extend(bandit_issues)
            self.static_analysis_results["security_issues"].extend(semgrep_issues)
        
        return metrics
    
    def calculate_quality_metrics(self, file_path: str) -> Dict[str, Any]:
        """
        Calculate code quality metrics for a file.
        
        Args:
            file_path: Path to file to analyze
            
        Returns:
            Quality metrics dictionary
        """
        metrics = {
            "mypy_errors": [],
            "ruff_issues": [],
            "black_issues": [],
            "total_quality_issues": 0,
            "type_errors": 0,
            "lint_errors": 0,
            "format_issues": 0
        }
        
        if file_path.endswith('.py'):
            # Run mypy
            mypy_errors = self.quality_scanner.check_types_with_mypy(file_path)
            metrics["mypy_errors"] = mypy_errors[:10]  # Limit to 10
            metrics["type_errors"] = len(mypy_errors)
            metrics["total_quality_issues"] += len(mypy_errors)
            
            # Run ruff
            ruff_issues = self.quality_scanner.lint_with_ruff(file_path)
            metrics["ruff_issues"] = ruff_issues[:10]  # Limit to 10
            metrics["lint_errors"] = len(ruff_issues)
            metrics["total_quality_issues"] += len(ruff_issues)
            
            # Run black
            black_issues = self.quality_scanner.check_format_with_black(file_path)
            metrics["black_issues"] = black_issues[:10]  # Limit to 10
            metrics["format_issues"] = len(black_issues)
            metrics["total_quality_issues"] += len(black_issues)
            
            # Update aggregated results
            self.static_analysis_results["quality_issues"].extend(mypy_errors)
            self.static_analysis_results["quality_issues"].extend(ruff_issues)
        
        return metrics
    
    def get_aggregated_metrics(self) -> Dict[str, Any]:
        """Get aggregated static analysis metrics."""
        return {
            "total_security_issues": len(self.static_analysis_results["security_issues"]),
            "total_quality_issues": len(self.static_analysis_results["quality_issues"]),
            "last_scan": self.static_analysis_results["last_scan"],
            "security_breakdown": self._categorize_security_issues(),
            "quality_breakdown": self._categorize_quality_issues()
        }
    
    def _categorize_security_issues(self) -> Dict[str, int]:
        """Categorize security issues by severity."""
        breakdown = defaultdict(int)
        for issue in self.static_analysis_results["security_issues"]:
            severity = issue.get("issue_severity", "MEDIUM").upper()
            breakdown[severity] += 1
        return dict(breakdown)
    
    def _categorize_quality_issues(self) -> Dict[str, int]:
        """Categorize quality issues by type."""
        breakdown = {
            "type_errors": 0,
            "lint_errors": 0,
            "format_issues": 0
        }
        # This would be calculated from quality_issues if we store type info
        return breakdown


def get_metrics_calculator(workspace_path: str = ".") -> MetricsCalculator:
    """Get a MetricsCalculator instance."""
    return MetricsCalculator(workspace_path)

