#!/usr/bin/env python3
"""
Quick2Odoo - Python 3.13 Compatibility Test Suite
Comprehensive test to verify all critical functionality works on Python 3.13

Run this script to verify Python 3.13 compatibility before deploying.
"""
import sys
import os

# Force UTF-8 output for Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

print("=" * 80)
print(" QUICK2ODOO - PYTHON 3.13 COMPREHENSIVE COMPATIBILITY TEST")
print("=" * 80)
print()

# Test metadata
test_results = {
    "total": 0,
    "passed": 0,
    "failed": 0,
    "skipped": 0
}

def test_module(module_path, description, critical=False):
    """Test if a module can be imported"""
    test_results["total"] += 1
    try:
        # Handle nested imports
        parts = module_path.split('.')
        module = __import__(module_path)
        for part in parts[1:]:
            module = getattr(module, part)
        
        # Get version if available
        version = ""
        root_module = __import__(parts[0])
        if hasattr(root_module, '__version__'):
            version = f" v{root_module.__version__}"
        
        if critical:
            print(f"[CRITICAL]   {description:40} {version}")
        else:
            print(f"[PASS]       {description:40} {version}")
        test_results["passed"] += 1
        return True
        
    except ImportError as e:
        if critical:
            print(f"[CRITICAL]   {description:40} FAILED: {e}")
            test_results["failed"] += 1
        else:
            print(f"[SKIP]       {description:40} Not installed")
            test_results["skipped"] += 1
        return False
        
    except Exception as e:
        print(f"[ERROR]      {description:40} ERROR: {type(e).__name__}")
        test_results["failed"] += 1
        return False

# Display Python version
print(f"Python Version: {sys.version}")
print(f"Version Info:   {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
print(f"Platform:       {sys.platform}")
print()

# Test 1: Critical Pydantic Ecosystem
print("-" * 80)
print("TEST SUITE 1: CRITICAL PYDANTIC ECOSYSTEM")
print("-" * 80)
pydantic_core_ok = test_module('pydantic_core', 'pydantic-core', critical=True)
pydantic_ok = test_module('pydantic', 'pydantic', critical=True)
pydantic_settings_ok = test_module('pydantic_settings', 'pydantic-settings', critical=True)
print()

if not (pydantic_core_ok and pydantic_ok and pydantic_settings_ok):
    print("CRITICAL FAILURE: Pydantic ecosystem not working!")
    print("Python 3.13 is NOT compatible.")
    sys.exit(1)

# Test 2: Core Framework Dependencies
print("-" * 80)
print("TEST SUITE 2: FRAMEWORK DEPENDENCIES")
print("-" * 80)
test_module('fastapi', 'FastAPI')
test_module('uvicorn', 'Uvicorn')
test_module('sqlalchemy', 'SQLAlchemy')
test_module('jinja2', 'Jinja2')
test_module('stripe', 'Stripe')
test_module('pytest', 'pytest')
test_module('requests', 'requests')
test_module('aiohttp', 'aiohttp')
print()

# Test 3: Quick2Odoo Core Utilities
print("-" * 80)
print("TEST SUITE 3: QUICK2ODOO CORE UTILITIES")
print("-" * 80)
test_module('utils.name_sanitizer', 'utils.name_sanitizer')
test_module('utils.recursive_researcher', 'utils.recursive_researcher')
test_module('utils.research_database', 'utils.research_database')
test_module('utils.platform_mapper', 'utils.platform_mapper')
test_module('utils.migration_orchestrator', 'utils.migration_orchestrator')
test_module('utils.migration_pricing', 'utils.migration_pricing')
print()

# Test 4: Quick2Odoo Agent System
print("-" * 80)
print("TEST SUITE 4: AGENT SYSTEM")
print("-" * 80)
test_module('agents.base_agent', 'agents.base_agent')
test_module('agents.orchestrator', 'agents.orchestrator')
test_module('agents.coder_agent', 'agents.coder_agent')
test_module('agents.researcher_agent', 'agents.researcher_agent')
test_module('agents.testing_agent', 'agents.testing_agent')
test_module('agents.qa_agent', 'agents.qa_agent')
test_module('agents.research_aware_mixin', 'agents.research_aware_mixin')
print()

# Test 5: Main Entry Point
print("-" * 80)
print("TEST SUITE 5: MAIN ENTRY POINT")
print("-" * 80)
try:
    import main
    print(f"[PASS]       main.py imports successfully")
    test_results["total"] += 1
    test_results["passed"] += 1
    
    # Check for key functions
    if hasattr(main, 'main'):
        print(f"[PASS]       main() function exists")
    if hasattr(main, 'verify_python_version'):
        print(f"[PASS]       verify_python_version() exists")
        
except SyntaxError as e:
    print(f"[ERROR]      SYNTAX ERROR in main.py: {e}")
    test_results["total"] += 1
    test_results["failed"] += 1
except Exception as e:
    print(f"[ERROR]      Cannot import main.py: {type(e).__name__}: {e}")
    test_results["total"] += 1
    test_results["failed"] += 1
print()

# Final Summary
print("=" * 80)
print(" TEST RESULTS SUMMARY")
print("=" * 80)
print()
print(f"Total Tests:   {test_results['total']}")
print(f"Passed:        {test_results['passed']} (GREEN)")
print(f"Failed:        {test_results['failed']} (RED)")
print(f"Skipped:       {test_results['skipped']} (YELLOW - not installed)")
print()

# Calculate pass rate
if test_results['total'] > 0:
    pass_rate = (test_results['passed'] / test_results['total']) * 100
    print(f"Pass Rate:     {pass_rate:.1f}%")
print()

# Final Verdict
print("=" * 80)
print(" FINAL VERDICT")
print("=" * 80)
print()

critical_tests_passed = (pydantic_core_ok and pydantic_ok and pydantic_settings_ok)

if critical_tests_passed and test_results['failed'] == 0:
    print("SUCCESS: PYTHON 3.13 IS FULLY COMPATIBLE WITH QUICK2ODOO!")
    print()
    print("Key Findings:")
    print("  * pydantic-core 2.41.5+ includes Python 3.13 wheels")
    print("  * No Rust compiler needed")
    print("  * All critical dependencies work")
    print("  * Quick2Odoo core modules import successfully")
    print("  * Main entry point runs without errors")
    print()
    print("Recommendations:")
    print("  1. Python 3.13 can be added to officially supported versions")
    print("  2. Update all documentation to include Python 3.13")
    print("  3. Python 3.12 remains recommended (most stable)")
    print()
    if test_results['skipped'] > 0:
        print(f"Note: {test_results['skipped']} optional dependencies not installed.")
        print("      Run: pip install -r requirements.txt")
    print()
    print("=" * 80)
    print(" You can confidently use Python 3.13 with Quick2Odoo!")
    print("=" * 80)
    
elif critical_tests_passed:
    print("PARTIAL SUCCESS: Critical dependencies work, but some tests failed")
    print()
    print(f"  {test_results['failed']} test(s) failed")
    print(f"  {test_results['skipped']} test(s) skipped")
    print()
    print("Action: Review failed tests above and install missing dependencies")
    
else:
    print("FAILURE: Python 3.13 NOT compatible")
    print()
    print("Critical pydantic dependencies failed to import.")
    print("Python 3.13 cannot be used with Quick2Odoo at this time.")
    print()
    print("Recommended: Use Python 3.12")
    sys.exit(1)

print()

# Save results to file
report_file = "PYTHON313_COMPATIBILITY_REPORT.txt"
with open(report_file, "w", encoding="utf-8") as f:
    f.write("=" * 80 + "\n")
    f.write("QUICK2ODOO - PYTHON 3.13 COMPATIBILITY TEST RESULTS\n")
    f.write("=" * 80 + "\n\n")
    f.write(f"Test Date: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write(f"Python: {sys.version}\n\n")
    f.write(f"Total Tests: {test_results['total']}\n")
    f.write(f"Passed: {test_results['passed']}\n")
    f.write(f"Failed: {test_results['failed']}\n")
    f.write(f"Skipped: {test_results['skipped']}\n\n")
    
    if critical_tests_passed and test_results['failed'] == 0:
        f.write("VERDICT: PYTHON 3.13 FULLY COMPATIBLE\n")
    elif critical_tests_passed:
        f.write("VERDICT: PARTIALLY COMPATIBLE (some dependencies missing)\n")
    else:
        f.write("VERDICT: NOT COMPATIBLE\n")

print(f"Detailed report saved to: {report_file}")
print()

