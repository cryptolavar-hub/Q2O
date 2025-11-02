"""
Infrastructure Validator - Validates Terraform and Helm configurations.
Provides validation for infrastructure as code before deployment.
"""

import os
import subprocess
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

logger = logging.getLogger(__name__)


class InfrastructureValidator:
    """Validates Terraform and Helm configurations."""
    
    def __init__(self, workspace_path: str = "."):
        """
        Initialize infrastructure validator.
        
        Args:
            workspace_path: Path to workspace directory
        """
        self.workspace_path = Path(workspace_path)
        self.terraform_available = self._check_terraform_available()
        self.helm_available = self._check_helm_available()
        
        logger.info(f"Infrastructure validator initialized")
        logger.info(f"Terraform available: {self.terraform_available}")
        logger.info(f"Helm available: {self.helm_available}")
    
    def _check_terraform_available(self) -> bool:
        """Check if Terraform is available in PATH."""
        try:
            result = subprocess.run(
                ["terraform", "version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    def _check_helm_available(self) -> bool:
        """Check if Helm is available in PATH."""
        try:
            result = subprocess.run(
                ["helm", "version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    def validate_terraform(self, terraform_dir: Optional[str] = None) -> Dict[str, Any]:
        """
        Validate Terraform configuration.
        
        Args:
            terraform_dir: Directory containing Terraform files. If None, searches for .tf files.
            
        Returns:
            Dictionary with validation results
        """
        result = {
            "status": "skipped",
            "valid": False,
            "errors": [],
            "warnings": [],
            "output": ""
        }
        
        if not self.terraform_available:
            result["status"] = "skipped"
            result["output"] = "Terraform not available - skipping validation"
            logger.warning("Terraform not available - skipping validation")
            return result
        
        # Find Terraform directory
        if terraform_dir is None:
            terraform_dir = self._find_terraform_directory()
        
        if terraform_dir is None:
            result["status"] = "skipped"
            result["output"] = "No Terraform files found"
            return result
        
        terraform_path = Path(terraform_dir)
        
        try:
            # Run terraform fmt -check (formatting check)
            fmt_result = subprocess.run(
                ["terraform", "fmt", "-check", "-recursive"],
                cwd=terraform_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if fmt_result.returncode != 0:
                result["warnings"].append("Terraform files not formatted correctly")
                result["output"] += fmt_result.stdout + fmt_result.stderr
            
            # Run terraform init
            init_result = subprocess.run(
                ["terraform", "init", "-backend=false"],
                cwd=terraform_path,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if init_result.returncode != 0:
                result["errors"].append("Terraform init failed")
                result["output"] += init_result.stdout + init_result.stderr
                result["status"] = "failed"
                return result
            
            # Run terraform validate
            validate_result = subprocess.run(
                ["terraform", "validate"],
                cwd=terraform_path,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if validate_result.returncode == 0:
                result["status"] = "success"
                result["valid"] = True
                result["output"] = validate_result.stdout
            else:
                result["status"] = "failed"
                result["errors"].append("Terraform validation failed")
                result["output"] += validate_result.stdout + validate_result.stderr
            
        except subprocess.TimeoutExpired:
            result["status"] = "timeout"
            result["errors"].append("Terraform validation timed out")
        except Exception as e:
            result["status"] = "error"
            result["errors"].append(f"Error validating Terraform: {str(e)}")
            logger.error(f"Error validating Terraform: {str(e)}", exc_info=True)
        
        return result
    
    def validate_helm(self, chart_dir: Optional[str] = None) -> Dict[str, Any]:
        """
        Validate Helm chart.
        
        Args:
            chart_dir: Directory containing Helm chart. If None, searches for Chart.yaml.
            
        Returns:
            Dictionary with validation results
        """
        result = {
            "status": "skipped",
            "valid": False,
            "errors": [],
            "warnings": [],
            "output": ""
        }
        
        if not self.helm_available:
            result["status"] = "skipped"
            result["output"] = "Helm not available - skipping validation"
            logger.warning("Helm not available - skipping validation")
            return result
        
        # Find Helm chart directory
        if chart_dir is None:
            chart_dir = self._find_helm_chart_directory()
        
        if chart_dir is None:
            result["status"] = "skipped"
            result["output"] = "No Helm chart found"
            return result
        
        chart_path = Path(chart_dir)
        
        try:
            # Run helm lint
            lint_result = subprocess.run(
                ["helm", "lint", str(chart_path)],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if lint_result.returncode == 0:
                result["status"] = "success"
                result["valid"] = True
                result["output"] = lint_result.stdout
            else:
                result["status"] = "failed"
                # Parse helm lint output for errors/warnings
                output = lint_result.stdout + lint_result.stderr
                result["output"] = output
                
                # Parse errors and warnings from helm lint output
                if "ERROR" in output:
                    result["errors"].append("Helm chart has errors")
                if "WARNING" in output:
                    result["warnings"].append("Helm chart has warnings")
            
        except subprocess.TimeoutExpired:
            result["status"] = "timeout"
            result["errors"].append("Helm lint timed out")
        except Exception as e:
            result["status"] = "error"
            result["errors"].append(f"Error validating Helm chart: {str(e)}")
            logger.error(f"Error validating Helm chart: {str(e)}", exc_info=True)
        
        return result
    
    def _find_terraform_directory(self) -> Optional[Path]:
        """Find Terraform directory by searching for .tf files."""
        for root, dirs, files in os.walk(self.workspace_path):
            # Skip hidden directories and common excludes
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['venv', 'node_modules']]
            
            # Check if directory contains .tf files
            if any(f.endswith('.tf') for f in files):
                return Path(root)
        
        return None
    
    def _find_helm_chart_directory(self) -> Optional[Path]:
        """Find Helm chart directory by searching for Chart.yaml."""
        for root, dirs, files in os.walk(self.workspace_path):
            # Skip hidden directories
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            
            # Check if directory contains Chart.yaml
            if 'Chart.yaml' in files:
                return Path(root)
        
        return None
    
    def validate_all(self) -> Dict[str, Any]:
        """
        Validate all infrastructure in workspace.
        
        Returns:
            Dictionary with all validation results
        """
        results = {
            "terraform": self.validate_terraform(),
            "helm": self.validate_helm()
        }
        
        overall_valid = all(
            r.get("valid", False) or r.get("status") == "skipped"
            for r in results.values()
        )
        
        return {
            "overall_valid": overall_valid,
            "results": results
        }


# Global validator instance
_validator_instance: Optional[InfrastructureValidator] = None


def get_validator(workspace_path: str = ".") -> InfrastructureValidator:
    """Get the global infrastructure validator instance."""
    global _validator_instance
    if _validator_instance is None:
        _validator_instance = InfrastructureValidator(workspace_path)
    return _validator_instance


def set_validator(validator: InfrastructureValidator):
    """Set the global infrastructure validator instance."""
    global _validator_instance
    _validator_instance = validator

