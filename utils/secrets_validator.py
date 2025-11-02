"""
Secrets Validation and .env.example Generation Utilities.
"""

import re
import os
import logging
from typing import List, Set, Dict, Optional

logger = logging.getLogger(__name__)

# Common secret patterns
SECRET_PATTERNS = [
    r'password\s*=\s*["\'][^"\']+["\']',
    r'api[_-]?key\s*=\s*["\'][^"\']+["\']',
    r'secret\s*=\s*["\'][^"\']+["\']',
    r'token\s*=\s*["\'][^"\']+["\']',
    r'aws[_-]?secret[_-]?access[_-]?key\s*=\s*["\'][^"\']+["\']',
    r'private[_-]?key\s*=\s*["\'][^"\']+["\']',
]

# Environment variable patterns
ENV_VAR_PATTERNS = [
    r'os\.getenv\(["\']([^"\']+)["\']',
    r'process\.env\.([A-Z_][A-Z0-9_]*)',
    r'os\.environ\[["\']([^"\']+)["\']',
    r'\$\{([A-Z_][A-Z0-9_]*)\}',
]


class SecretsValidator:
    """Secrets validation and environment variable extraction."""
    
    def validate_no_secrets(self, code: str, file_path: str = "") -> List[str]:
        """
        Check for hardcoded secrets in code.
        
        Args:
            code: Code content to check
            file_path: Optional file path for reporting
            
        Returns:
            List of potential secrets found
        """
        issues = []
        
        for pattern in SECRET_PATTERNS:
            matches = re.finditer(pattern, code, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                line_num = code[:match.start()].count('\n') + 1
                issues.append(
                    f"Potential hardcoded secret found at line {line_num} in {file_path}: {match.group(0)[:50]}"
                )
        
        return issues
    
    def extract_env_vars(self, code: str) -> Set[str]:
        """
        Extract environment variable names from code.
        
        Args:
            code: Code content to analyze
            
        Returns:
            Set of environment variable names
        """
        env_vars = set()
        
        for pattern in ENV_VAR_PATTERNS:
            matches = re.finditer(pattern, code, re.MULTILINE)
            for match in matches:
                var_name = match.group(1)
                env_vars.add(var_name)
        
        return env_vars
    
    def generate_env_example(self, env_vars: Set[str], file_path: str = ".env.example") -> str:
        """
        Generate .env.example file content.
        
        Args:
            env_vars: Set of environment variable names
            file_path: Output file path
            
        Returns:
            Generated .env.example content
        """
        lines = [
            "# Environment Variables",
            "# Copy this file to .env and fill in the values",
            "",
        ]
        
        # Common env vars with descriptions
        descriptions = {
            "DATABASE_URL": "Database connection string",
            "SECRET_KEY": "Secret key for encryption",
            "QBO_CLIENT_ID": "QuickBooks OAuth client ID",
            "QBO_CLIENT_SECRET": "QuickBooks OAuth client secret",
            "QBO_REDIRECT_URI": "QuickBooks OAuth redirect URI",
            "ODOO_URL": "Odoo instance URL",
            "ODOO_API_KEY": "Odoo API key",
            "STRIPE_SECRET": "Stripe secret key",
            "STRIPE_WEBHOOK_SECRET": "Stripe webhook secret",
            "NEXTAUTH_SECRET": "NextAuth.js secret",
            "GOOGLE_ID": "Google OAuth client ID",
            "GOOGLE_SECRET": "Google OAuth client secret",
        }
        
        # Sort for consistent output
        sorted_vars = sorted(env_vars)
        
        for var in sorted_vars:
            desc = descriptions.get(var, "Environment variable")
            lines.append(f"# {desc}")
            lines.append(f"{var}=")
            lines.append("")
        
        content = "\n".join(lines)
        
        # Write to file if path provided
        if file_path:
            try:
                dir_path = os.path.dirname(file_path)
                if dir_path:
                    os.makedirs(dir_path, exist_ok=True)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                logger.info(f"Generated .env.example at {file_path}")
            except Exception as e:
                logger.error(f"Error writing .env.example: {str(e)}")
        
        return content


def get_secrets_validator() -> SecretsValidator:
    """Get a SecretsValidator instance."""
    return SecretsValidator()

