"""
Test script for Multi-Agent Development System
Tests the system with a small subset of features
"""

import sys
import json
from pathlib import Path
from main import AgentSystem, setup_logging

def test_small():
    """Test with a small objective."""
    print("=" * 80)
    print("TESTING MULTI-AGENT SYSTEM - SMALL TEST")
    print("=" * 80)
    
    setup_logging("INFO")
    
    # Create test workspace
    test_workspace = Path("./test_workspace")
    test_workspace.mkdir(exist_ok=True)
    
    # Initialize system
    system = AgentSystem(workspace_path=str(test_workspace))
    
    # Run small test
    results = system.run_project(
        project_description="QuickBooks to Odoo - Small Test",
        objectives=["QuickBooks OAuth authentication"]
    )
    
    # Print results
    system.print_results(results)
    
    # Verify results
    print("\n" + "=" * 80)
    print("VERIFICATION")
    print("=" * 80)
    
    status = results["final_status"]
    print(f"✓ Tasks created: {status['total_tasks']}")
    print(f"✓ Tasks completed: {status['completed']}")
    print(f"✓ Completion: {status['completion_percentage']:.1f}%")
    
    # Check for created files
    print("\nChecking for created files...")
    workspace = Path(test_workspace)
    
    # Check for integration files
    qbo_oauth = workspace / "api" / "app" / "oauth_qbo.py"
    if qbo_oauth.exists():
        print(f"✓ Created: {qbo_oauth}")
    else:
        print(f"✗ Missing: {qbo_oauth}")
    
    # Check for infrastructure files (if created)
    infra_files = list(workspace.glob("infra/**/*.tf"))
    if infra_files:
        print(f"✓ Created {len(infra_files)} Terraform files")
    
    return results

def test_all_features():
    """Test with all features from config."""
    print("=" * 80)
    print("TESTING MULTI-AGENT SYSTEM - FULL TEST")
    print("=" * 80)
    
    # Load config
    with open("test_config.json", "r") as f:
        config = json.load(f)
    
    setup_logging("INFO")
    
    test_workspace = Path("./test_workspace_full")
    test_workspace.mkdir(exist_ok=True)
    
    system = AgentSystem(workspace_path=str(test_workspace))
    
    results = system.run_project(
        project_description=config["project_description"],
        objectives=config["objectives"]
    )
    
    system.print_results(results)
    
    return results

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "full":
        test_all_features()
    else:
        test_small()

