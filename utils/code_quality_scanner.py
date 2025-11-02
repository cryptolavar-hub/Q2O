"""
Code Quality Scanning Utilities using mypy, ruff, and black.
"""

import subprocess
import logging
from typing import List, Dict, Optional
import os

logger = logging.getLogger(__name__)


class CodeQualityScanner:
    """Code quality scanning utilities."""
    
    def __init__(self, workspace_path: str = "."):
        self.workspace_path = workspace_path
    
    def check_types_with_mypy(self, file_path: str) -> List[str]:
        """
        Type-check a file with mypy.
        
        Args:
            file_path: Path to file to check
            
        Returns:
            List of type errors
        """
        errors = []
        
        if not os.path.exists(file_path):
            return errors
        
        try:
            result = subprocess.run(
                ["mypy", "--no-error-summary", file_path],
                capture_output=True,
                text=True,
                cwd=self.workspace_path,
                timeout=30
            )
            
            if result.returncode != 0:
                errors = [line.strip() for line in result.stdout.split('\n') if line.strip()]
        
        except FileNotFoundError:
            logger.debug("mypy not installed, skipping type checking")
        except subprocess.TimeoutExpired:
            logger.warning(f"mypy check timed out for {file_path}")
        except Exception as e:
            logger.error(f"Error running mypy on {file_path}: {str(e)}")
        
        return errors
    
    def lint_with_ruff(self, file_path: str) -> List[str]:
        """
        Lint a file with ruff.
        
        Args:
            file_path: Path to file to lint
            
        Returns:
            List of linting issues
        """
        issues = []
        
        if not os.path.exists(file_path):
            return issues
        
        try:
            result = subprocess.run(
                ["ruff", "check", "--output-format", "text", file_path],
                capture_output=True,
                text=True,
                cwd=self.workspace_path,
                timeout=30
            )
            
            if result.returncode != 0:
                issues = [line.strip() for line in result.stdout.split('\n') if line.strip()]
        
        except FileNotFoundError:
            logger.debug("ruff not installed, skipping linting")
        except subprocess.TimeoutExpired:
            logger.warning(f"ruff lint timed out for {file_path}")
        except Exception as e:
            logger.error(f"Error running ruff on {file_path}: {str(e)}")
        
        return issues
    
    def check_format_with_black(self, file_path: str) -> List[str]:
        """
        Check if file is formatted correctly with black.
        
        Args:
            file_path: Path to file to check
            
        Returns:
            List of formatting issues
        """
        issues = []
        
        if not os.path.exists(file_path):
            return issues
        
        try:
            result = subprocess.run(
                ["black", "--check", "--diff", file_path],
                capture_output=True,
                text=True,
                cwd=self.workspace_path,
                timeout=30
            )
            
            if result.returncode != 0:
                issues = [line.strip() for line in result.stdout.split('\n') if line.strip()]
        
        except FileNotFoundError:
            logger.debug("black not installed, skipping format check")
        except subprocess.TimeoutExpired:
            logger.warning(f"black format check timed out for {file_path}")
        except Exception as e:
            logger.error(f"Error running black on {file_path}: {str(e)}")
        
        return issues


def get_quality_scanner(workspace_path: str = ".") -> CodeQualityScanner:
    """Get a CodeQualityScanner instance."""
    return CodeQualityScanner(workspace_path)

