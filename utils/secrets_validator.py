"""
Secrets Validator and .env.example Generator
Validates code for hardcoded secrets and generates .env.example files
"""

import re
import os
from typing import List, Set, Dict, Tuple, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class SecretsValidator:
    """Validates code for secrets and generates .env.example files."""
    
    # Common secret patterns (hardcoded secrets - these are BAD)
    HARDCODED_SECRET_PATTERNS = [
        # API keys and tokens
        (r'api[_-]?key\s*=\s*["\']([A-Za-z0-9_\-]{20,})["\']', 'Potential hardcoded API key'),
        (r'secret[_-]?key\s*=\s*["\']([A-Za-z0-9_\-]{20,})["\']', 'Potential hardcoded secret key'),
        (r'token\s*=\s*["\']([A-Za-z0-9_\-]{20,})["\']', 'Potential hardcoded token'),
        (r'password\s*=\s*["\']([^"\']{8,})["\']', 'Potential hardcoded password'),
        
        # AWS credentials
        (r'AKIA[0-9A-Z]{16}', 'Potential AWS Access Key ID'),
        (r'aws[_-]?secret[_-]?access[_-]?key\s*=\s*["\']([^"\']+)["\']', 'Potential AWS Secret'),
        
        # Private keys
        (r'-----BEGIN (RSA |DSA |EC )?PRIVATE KEY-----', 'Private key detected'),
        
        # Database URLs with credentials
        (r'(mysql|postgres|mongodb):\/\/[^:]+:[^@]+@', 'Database URL with credentials'),
    ]
    
    # Environment variable patterns (these are GOOD)
    ENV_VAR_PATTERNS = {
        'python': [
            r'os\.getenv\(["\']([A-Z_][A-Z0-9_]*)["\']',
            r'os\.environ\[["\']([A-Z_][A-Z0-9_]*)["\']',
            r'os\.environ\.get\(["\']([A-Z_][A-Z0-9_]*)["\']',
        ],
        'typescript': [
            r'process\.env\.([A-Z_][A-Z0-9_]*)',
            r'process\.env\[["\']([A-Z_][A-Z0-9_]*)["\']',
        ],
        'javascript': [
            r'process\.env\.([A-Z_][A-Z0-9_]*)',
            r'process\.env\[["\']([A-Z_][A-Z0-9_]*)["\']',
        ]
    }
    
    # Default values for common environment variables
    ENV_VAR_DESCRIPTIONS = {
        # Database
        'DATABASE_URL': 'Database connection URL',
        'DB_HOST': 'Database host',
        'DB_PORT': 'Database port',
        'DB_NAME': 'Database name',
        'DB_USER': 'Database username',
        'DB_PASSWORD': 'Database password',
        
        # QuickBooks
        'QBO_CLIENT_ID': 'QuickBooks Online Client ID',
        'QBO_CLIENT_SECRET': 'QuickBooks Online Client Secret',
        'QBO_REDIRECT_URI': 'QuickBooks OAuth redirect URI',
        'QBO_SCOPE': 'QuickBooks OAuth scope',
        
        # Odoo
        'ODOO_URL': 'Odoo instance URL',
        'ODOO_DB': 'Odoo database name',
        'ODOO_USERNAME': 'Odoo username',
        'ODOO_PASSWORD': 'Odoo password',
        'ODOO_API_KEY': 'Odoo API key',
        
        # Stripe
        'STRIPE_SECRET': 'Stripe secret key',
        'STRIPE_PUBLIC_KEY': 'Stripe publishable key',
        'STRIPE_WEBHOOK_SECRET': 'Stripe webhook secret',
        'STRIPE_PLAN_MAP': 'Stripe plan mapping JSON',
        
        # OAuth Providers
        'GOOGLE_ID': 'Google OAuth Client ID',
        'GOOGLE_SECRET': 'Google OAuth Client Secret',
        'OKTA_ID': 'Okta Client ID',
        'OKTA_SECRET': 'Okta Client Secret',
        'OKTA_ISSUER': 'Okta issuer URL',
        'AZURE_AD_CLIENT_ID': 'Azure AD Client ID',
        'AZURE_AD_CLIENT_SECRET': 'Azure AD Client Secret',
        'AZURE_AD_TENANT_ID': 'Azure AD Tenant ID',
        
        # NextAuth
        'NEXTAUTH_SECRET': 'NextAuth secret for JWT',
        'NEXTAUTH_URL': 'NextAuth URL',
        
        # Temporal
        'TEMPORAL_ADDRESS': 'Temporal server address',
        'TEMPORAL_NAMESPACE': 'Temporal namespace',
        'TEMPORAL_TASK_QUEUE': 'Temporal task queue name',
        
        # Application
        'SECRET_KEY': 'Application secret key',
        'JWT_SECRET': 'JWT signing secret',
        'ENCRYPTION_KEY': 'Encryption key',
        
        # URLs
        'BILLING_SUCCESS_URL': 'Billing success redirect URL',
        'BILLING_CANCEL_URL': 'Billing cancel redirect URL',
        'APP_URL': 'Application base URL',
        'API_URL': 'API base URL',
        
        # Research Agent (Web Search)
        'GOOGLE_SEARCH_API_KEY': 'Google Custom Search API key',
        'GOOGLE_SEARCH_CX': 'Google Custom Search Engine ID',
        'BING_SEARCH_API_KEY': 'Bing Search API key (Azure)',
        'RESEARCH_DAILY_LIMIT': 'Daily limit for research searches (default: 100)',
    }
    
    def __init__(self):
        self.found_secrets: List[Tuple[str, str, int]] = []
        self.env_vars: Set[str] = set()
    
    def scan_code_for_secrets(self, code: str, filename: str = "unknown") -> List[Dict]:
        """
        Scan code for hardcoded secrets.
        
        Args:
            code: Code content to scan
            filename: Name of the file being scanned
            
        Returns:
            List of issues found
        """
        issues = []
        lines = code.split('\n')
        
        for i, line in enumerate(lines, 1):
            for pattern, description in self.HARDCODED_SECRET_PATTERNS:
                matches = re.findall(pattern, line, re.IGNORECASE)
                if matches:
                    issues.append({
                        'file': filename,
                        'line': i,
                        'description': description,
                        'severity': 'HIGH',
                        'line_content': line.strip()
                    })
        
        return issues
    
    def extract_env_vars(self, code: str, language: str = 'python') -> Set[str]:
        """
        Extract environment variable names from code.
        
        Args:
            code: Code content to scan
            language: Programming language (python, typescript, javascript)
            
        Returns:
            Set of environment variable names
        """
        env_vars = set()
        
        patterns = self.ENV_VAR_PATTERNS.get(language, self.ENV_VAR_PATTERNS['python'])
        
        for pattern in patterns:
            matches = re.findall(pattern, code)
            env_vars.update(matches)
        
        return env_vars
    
    def scan_directory(self, directory: str) -> Dict[str, Set[str]]:
        """
        Scan entire directory for environment variables.
        
        Args:
            directory: Directory path to scan
            
        Returns:
            Dictionary mapping file extensions to environment variables found
        """
        all_env_vars = {}
        
        for root, dirs, files in os.walk(directory):
            # Skip common directories
            dirs[:] = [d for d in dirs if d not in {
                '__pycache__', 'node_modules', '.git', 'venv', 'env', 
                '.venv', 'dist', 'build', '.next'
            }]
            
            for file in files:
                file_path = os.path.join(root, file)
                ext = os.path.splitext(file)[1]
                
                # Determine language by extension
                language = None
                if ext in {'.py'}:
                    language = 'python'
                elif ext in {'.ts', '.tsx'}:
                    language = 'typescript'
                elif ext in {'.js', '.jsx'}:
                    language = 'javascript'
                else:
                    continue
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        code = f.read()
                        env_vars = self.extract_env_vars(code, language)
                        
                        if env_vars:
                            if language not in all_env_vars:
                                all_env_vars[language] = set()
                            all_env_vars[language].update(env_vars)
                            
                except Exception as e:
                    logger.warning(f"Error scanning {file_path}: {e}")
        
        return all_env_vars
    
    def generate_env_example(self, env_vars: Set[str], output_path: str = ".env.example"):
        """
        Generate .env.example file from environment variables.
        
        Args:
            env_vars: Set of environment variable names
            output_path: Path to write .env.example file
        """
        lines = [
            "# Environment Variables Configuration",
            "# Copy this file to .env and fill in the values",
            "#",
            "# Generated automatically - do not commit .env file!",
            "",
        ]
        
        # Group variables by category
        categorized = self._categorize_env_vars(env_vars)
        
        for category, vars_list in categorized.items():
            if vars_list:
                lines.append(f"# {category}")
                lines.append("#" + "=" * 50)
                
                for var in sorted(vars_list):
                    description = self.ENV_VAR_DESCRIPTIONS.get(var, f"{var} configuration")
                    lines.append(f"# {description}")
                    lines.append(f"{var}=")
                    lines.append("")
        
        content = '\n'.join(lines)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"Generated {output_path} with {len(env_vars)} environment variables")
    
    def _categorize_env_vars(self, env_vars: Set[str]) -> Dict[str, List[str]]:
        """Categorize environment variables by purpose."""
        categories = {
            'Database': [],
            'QuickBooks': [],
            'Odoo': [],
            'Stripe': [],
            'OAuth Providers': [],
            'NextAuth': [],
            'Temporal': [],
            'Research Agent': [],
            'Application': [],
            'URLs': [],
            'Other': []
        }
        
        for var in env_vars:
            if any(x in var for x in ['DB_', 'DATABASE']):
                categories['Database'].append(var)
            elif 'QBO' in var or 'QUICKBOOKS' in var:
                categories['QuickBooks'].append(var)
            elif 'ODOO' in var:
                categories['Odoo'].append(var)
            elif 'STRIPE' in var:
                categories['Stripe'].append(var)
            elif any(x in var for x in ['GOOGLE_SEARCH', 'BING_SEARCH', 'RESEARCH']):
                categories['Research Agent'].append(var)
            elif any(x in var for x in ['GOOGLE', 'OKTA', 'AZURE', 'OAUTH']):
                categories['OAuth Providers'].append(var)
            elif 'NEXTAUTH' in var:
                categories['NextAuth'].append(var)
            elif 'TEMPORAL' in var:
                categories['Temporal'].append(var)
            elif 'URL' in var or 'URI' in var:
                categories['URLs'].append(var)
            elif any(x in var for x in ['SECRET', 'KEY', 'PASSWORD', 'TOKEN']):
                categories['Application'].append(var)
            else:
                categories['Other'].append(var)
        
        return {k: v for k, v in categories.items() if v}


# Singleton instance
_validator: Optional[SecretsValidator] = None


def get_secrets_validator() -> SecretsValidator:
    """Get the singleton secrets validator instance."""
    global _validator
    if _validator is None:
        _validator = SecretsValidator()
    return _validator


def validate_no_secrets(code: str, filename: str = "unknown") -> List[Dict]:
    """
    Validate that code contains no hardcoded secrets.
    
    Args:
        code: Code to validate
        filename: Filename for error reporting
        
    Returns:
        List of issues found
    """
    validator = get_secrets_validator()
    return validator.scan_code_for_secrets(code, filename)


def extract_env_vars_from_code(code: str, language: str = 'python') -> Set[str]:
    """
    Extract environment variables from code.
    
    Args:
        code: Code to scan
        language: Programming language
        
    Returns:
        Set of environment variable names
    """
    validator = get_secrets_validator()
    return validator.extract_env_vars(code, language)


def generate_env_example_from_directory(directory: str, output_path: str = ".env.example"):
    """
    Scan directory and generate .env.example file.
    
    Args:
        directory: Directory to scan
        output_path: Output file path
    """
    validator = get_secrets_validator()
    all_env_vars_by_lang = validator.scan_directory(directory)
    
    # Combine all environment variables from all languages
    all_env_vars = set()
    for vars_set in all_env_vars_by_lang.values():
        all_env_vars.update(vars_set)
    
    if all_env_vars:
        output_full_path = os.path.join(directory, output_path)
        validator.generate_env_example(all_env_vars, output_full_path)
        logger.info(f"Found {len(all_env_vars)} unique environment variables")
        return output_full_path
    else:
        logger.info("No environment variables found")
        return None
