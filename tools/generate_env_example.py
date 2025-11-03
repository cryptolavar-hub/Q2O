#!/usr/bin/env python3
"""
Generate .env.example File
CLI tool to scan project and generate .env.example file
"""

import argparse
import sys
import os
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.secrets_validator import generate_env_example_from_directory, get_secrets_validator

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description="Generate .env.example file by scanning project for environment variables",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate .env.example in current directory
  python tools/generate_env_example.py
  
  # Generate in specific directory
  python tools/generate_env_example.py --directory ./my_project
  
  # Specify custom output filename
  python tools/generate_env_example.py --output .env.template
  
  # Scan and show variables without generating file
  python tools/generate_env_example.py --dry-run
        """
    )
    
    parser.add_argument(
        '--directory', '-d',
        type=str,
        default='.',
        help='Directory to scan (default: current directory)'
    )
    
    parser.add_argument(
        '--output', '-o',
        type=str,
        default='.env.example',
        help='Output filename (default: .env.example)'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show found variables without creating file'
    )
    
    parser.add_argument(
        '--check-secrets',
        action='store_true',
        help='Also scan for hardcoded secrets (security check)'
    )
    
    args = parser.parse_args()
    
    # Validate directory
    if not os.path.isdir(args.directory):
        logger.error(f"Directory not found: {args.directory}")
        sys.exit(1)
    
    logger.info(f"Scanning directory: {os.path.abspath(args.directory)}")
    
    # Scan for environment variables
    validator = get_secrets_validator()
    all_env_vars_by_lang = validator.scan_directory(args.directory)
    
    # Combine all environment variables
    all_env_vars = set()
    for lang, vars_set in all_env_vars_by_lang.items():
        logger.info(f"Found {len(vars_set)} environment variables in {lang} files")
        all_env_vars.update(vars_set)
    
    if not all_env_vars:
        logger.warning("No environment variables found!")
        return
    
    logger.info(f"\nTotal unique environment variables found: {len(all_env_vars)}")
    
    # Show found variables
    print("\nEnvironment variables found:")
    print("=" * 60)
    for var in sorted(all_env_vars):
        print(f"  {var}")
    print("=" * 60)
    
    # Check for hardcoded secrets if requested
    if args.check_secrets:
        logger.info("\nScanning for hardcoded secrets...")
        secret_issues = []
        
        for root, dirs, files in os.walk(args.directory):
            # Skip common directories
            dirs[:] = [d for d in dirs if d not in {
                '__pycache__', 'node_modules', '.git', 'venv', 'env', 
                '.venv', 'dist', 'build', '.next'
            }]
            
            for file in files:
                if file.endswith(('.py', '.js', '.ts', '.tsx', '.jsx')):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            code = f.read()
                            issues = validator.scan_code_for_secrets(code, file_path)
                            secret_issues.extend(issues)
                    except Exception as e:
                        logger.warning(f"Error scanning {file_path}: {e}")
        
        if secret_issues:
            print("\n⚠️  WARNING: Potential hardcoded secrets found!")
            print("=" * 60)
            for issue in secret_issues:
                print(f"  {issue['file']}:{issue['line']}")
                print(f"    {issue['description']}")
                print(f"    {issue['line_content']}")
                print()
            print("=" * 60)
            logger.error(f"Found {len(secret_issues)} potential hardcoded secrets!")
        else:
            logger.info("✓ No hardcoded secrets detected")
    
    # Generate .env.example file
    if args.dry_run:
        logger.info("\nDry run mode - no file created")
    else:
        output_path = os.path.join(args.directory, args.output)
        validator.generate_env_example(all_env_vars, output_path)
        logger.info(f"\n✓ Generated: {output_path}")
        logger.info("Remember to:")
        logger.info("  1. Copy .env.example to .env")
        logger.info("  2. Fill in actual values in .env")
        logger.info("  3. Add .env to .gitignore")
        logger.info("  4. Never commit .env file!")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\nInterrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        sys.exit(1)

