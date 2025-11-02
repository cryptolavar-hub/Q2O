"""
Security Scanning Utilities using bandit, semgrep, and dependency scanners.
"""

import subprocess
import logging
from typing import List, Dict, Optional
import os

logger = logging.getLogger(__name__)


class SecurityScanner:
    """Security scanning utilities."""
    
    def __init__(self, workspace_path: str = "."):
        self.workspace_path = workspace_path
    
    def scan_with_bandit(self, file_path: str) -> List[Dict[str, any]]:
        """
        Scan a Python file with bandit.
        
        Args:
            file_path: Path to file to scan
            
        Returns:
            List of security issues found
        """
        issues = []
        
        if not os.path.exists(file_path):
            return issues
        
        try:
            result = subprocess.run(
                ["bandit", "-f", "json", "-q", file_path],
                capture_output=True,
                text=True,
                cwd=self.workspace_path,
                timeout=30
            )
            
            if result.returncode != 0:
                import json
                try:
                    output = json.loads(result.stdout)
                    issues = output.get("results", [])
                except json.JSONDecodeError:
                    logger.warning(f"Could not parse bandit output for {file_path}")
        
        except FileNotFoundError:
            logger.debug("bandit not installed, skipping security scan")
        except subprocess.TimeoutExpired:
            logger.warning(f"bandit scan timed out for {file_path}")
        except Exception as e:
            logger.error(f"Error running bandit on {file_path}: {str(e)}")
        
        return issues
    
    def scan_with_semgrep(self, file_path: str) -> List[Dict[str, any]]:
        """
        Scan a file with semgrep.
        
        Args:
            file_path: Path to file to scan
            
        Returns:
            List of security issues found
        """
        issues = []
        
        if not os.path.exists(file_path):
            return issues
        
        try:
            result = subprocess.run(
                ["semgrep", "--json", "--quiet", file_path],
                capture_output=True,
                text=True,
                cwd=self.workspace_path,
                timeout=30
            )
            
            if result.returncode == 0:
                import json
                try:
                    output = json.loads(result.stdout)
                    issues = output.get("results", [])
                except json.JSONDecodeError:
                    logger.warning(f"Could not parse semgrep output for {file_path}")
        
        except FileNotFoundError:
            logger.debug("semgrep not installed, skipping security scan")
        except subprocess.TimeoutExpired:
            logger.warning(f"semgrep scan timed out for {file_path}")
        except Exception as e:
            logger.error(f"Error running semgrep on {file_path}: {str(e)}")
        
        return issues
    
    def scan_dependencies(self) -> List[Dict[str, any]]:
        """
        Scan Python dependencies for vulnerabilities using safety.
        
        Returns:
            List of vulnerability reports
        """
        vulnerabilities = []
        
        try:
            result = subprocess.run(
                ["safety", "check", "--json"],
                capture_output=True,
                text=True,
                cwd=self.workspace_path,
                timeout=60
            )
            
            if result.returncode != 0:
                import json
                try:
                    output = json.loads(result.stdout)
                    vulnerabilities = output if isinstance(output, list) else [output]
                except json.JSONDecodeError:
                    logger.warning("Could not parse safety output")
        
        except FileNotFoundError:
            logger.debug("safety not installed, skipping dependency scan")
        except subprocess.TimeoutExpired:
            logger.warning("safety scan timed out")
        except Exception as e:
            logger.error(f"Error running safety: {str(e)}")
        
        return vulnerabilities


def get_scanner(workspace_path: str = ".") -> SecurityScanner:
    """Get a SecurityScanner instance."""
    return SecurityScanner(workspace_path)

