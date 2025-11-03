#!/usr/bin/env python3
"""
Quick Start Helper
Interactive setup wizard for QuickOdoo Multi-Agent System
"""

import os
import sys
import json
from pathlib import Path

def print_banner():
    """Print welcome banner."""
    print("=" * 70)
    print("  QuickOdoo Multi-Agent System - Quick Start Wizard")
    print("=" * 70)
    print()

def check_requirements():
    """Check if requirements are installed."""
    print("[1/5] Checking requirements...")
    
    try:
        import fastapi
        import jinja2
        print("✓ Core dependencies installed")
        return True
    except ImportError:
        print("✗ Dependencies not installed!")
        print()
        print("Please run: pip install -r requirements.txt")
        return False

def check_env_file():
    """Check if .env file exists."""
    print("\n[2/5] Checking environment configuration...")
    
    if os.path.exists('.env'):
        print("✓ .env file found")
        return True
    elif os.path.exists('.env.example'):
        print("⚠ .env file not found (but .env.example exists)")
        
        response = input("Create .env from .env.example? (y/n): ").strip().lower()
        if response == 'y':
            with open('.env.example', 'r') as src:
                with open('.env', 'w') as dst:
                    dst.write(src.read())
            print("✓ Created .env file")
            print("⚠ Please edit .env with your actual values")
            return True
    else:
        print("✗ No .env.example found!")
        print("Run: python tools/generate_env_example.py")
        return False

def run_quick_test():
    """Run quick verification test."""
    print("\n[3/5] Running verification tests...")
    
    try:
        result = os.system('python quick_test.py')
        if result == 0:
            print("✓ All tests passed!")
            return True
        else:
            print("⚠ Some tests failed (see above)")
            return False
    except Exception as e:
        print(f"✗ Error running tests: {e}")
        return False

def create_sample_project():
    """Offer to create a sample project."""
    print("\n[4/5] Sample project setup...")
    
    response = input("Create a sample project to see the system in action? (y/n): ").strip().lower()
    if response != 'y':
        print("Skipping sample project")
        return True
    
    print("\nCreating sample project...")
    print("Project: QuickBooks OAuth Example")
    print("Workspace: ./sample_project")
    
    try:
        cmd = (
            'python main.py '
            '--project "QuickBooks OAuth Example" '
            '--objective "OAuth authentication with QuickBooks" '
            '--workspace ./sample_project '
            '--log-level INFO'
        )
        result = os.system(cmd)
        
        if result == 0:
            print("\n✓ Sample project created successfully!")
            print("\nGenerated files in: ./sample_project")
            print("  - api/app/oauth_qbo.py")
            print("  - api/app/clients/qbo.py")
            print("  - tests/test_*.py")
            return True
        else:
            print("\n⚠ Sample project creation had issues")
            return False
    except Exception as e:
        print(f"\n✗ Error creating sample: {e}")
        return False

def show_next_steps():
    """Show what to do next."""
    print("\n[5/5] Setup complete! Next steps:")
    print()
    print("Quick Start:")
    print("  1. Edit .env with your API keys")
    print("  2. Run: python main.py --help")
    print("  3. Try: python main.py --config config_example.json")
    print()
    print("Documentation:")
    print("  - README.md - Quick start guide")
    print("  - USAGE_GUIDE.md - Comprehensive usage examples")
    print("  - DEPLOYMENT_CHECKLIST.md - Production deployment")
    print("  - docs/Quick2Odoo_Agentic_Scaffold_Document.html - Full docs")
    print()
    print("Example Commands:")
    print("  # Simple project")
    print('  python main.py --project "My App" --objective "API endpoints"')
    print()
    print("  # With config file")
    print("  python main.py --config myconfig.json --workspace ./output")
    print()
    print("  # Generate .env.example")
    print("  python tools/generate_env_example.py --check-secrets")
    print()
    print("Need help? Check USAGE_GUIDE.md or README.md")
    print()

def main():
    """Main setup wizard."""
    print_banner()
    
    # Check we're in the right directory
    if not os.path.exists('requirements.txt'):
        print("Error: Please run this script from the project root directory")
        print("Current directory:", os.getcwd())
        sys.exit(1)
    
    # Run checks
    checks = []
    
    checks.append(check_requirements())
    
    if checks[-1]:  # Only continue if dependencies installed
        checks.append(check_env_file())
        checks.append(run_quick_test())
        checks.append(create_sample_project())
    
    # Show results
    print("\n" + "=" * 70)
    print("Setup Results:")
    print("-" * 70)
    print(f"Dependencies: {'✓' if checks[0] else '✗'}")
    if len(checks) > 1:
        print(f"Environment:  {'✓' if checks[1] else '⚠'}")
    if len(checks) > 2:
        print(f"Tests:        {'✓' if checks[2] else '⚠'}")
    if len(checks) > 3:
        print(f"Sample:       {'✓' if checks[3] else '⚠'}")
    print("=" * 70)
    
    # Next steps
    show_next_steps()
    
    # Exit code
    if all(checks[:2]):  # Dependencies and env are critical
        print("✓ Setup successful! You're ready to use QuickOdoo.")
        sys.exit(0)
    else:
        print("⚠ Setup incomplete. Please fix issues above.")
        sys.exit(1)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nSetup interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

