"""
Test script for the Multi-Agent Development System
Tests individual agents and the full system integration.
"""

import sys
import os
from pathlib import Path
import json
import logging

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from agents import (
    OrchestratorAgent,
    CoderAgent,
    TestingAgent,
    QAAgent,
    InfrastructureAgent,
    IntegrationAgent,
    FrontendAgent,
    WorkflowAgent,
    SecurityAgent,
    AgentType,
    Task,
    TaskStatus
)


def setup_test_logging():
    """Setup logging for tests."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def test_individual_agents():
    """Test each agent individually."""
    print("\n" + "=" * 80)
    print("TESTING INDIVIDUAL AGENTS")
    print("=" * 80)
    
    workspace = "./test_workspace"
    os.makedirs(workspace, exist_ok=True)
    
    # Test Infrastructure Agent
    print("\n1. Testing Infrastructure Agent...")
    infra_agent = InfrastructureAgent(workspace_path=workspace)
    infra_task = Task(
        id="test_infra_001",
        title="Infrastructure: Azure WAF Configuration",
        description="Create Azure Front Door WAF configuration with OWASP ruleset",
        agent_type=AgentType.INFRASTRUCTURE,
        metadata={"infrastructure_type": "terraform", "objective": "Azure WAF"}
    )
    result = infra_agent.process_task(infra_task)
    print(f"   Status: {result.status.value}")
    if result.result:
        print(f"   Files created: {len(result.result.get('files_created', []))}")
    
    # Test Integration Agent
    print("\n2. Testing Integration Agent...")
    integration_agent = IntegrationAgent(workspace_path=workspace)
    integration_task = Task(
        id="test_integration_001",
        title="Integration: QuickBooks OAuth",
        description="Implement QuickBooks Online OAuth integration",
        agent_type=AgentType.INTEGRATION,
        metadata={"integration_type": "quickbooks", "objective": "QBO OAuth"}
    )
    result = integration_agent.process_task(integration_task)
    print(f"   Status: {result.status.value}")
    if result.result:
        print(f"   Files created: {len(result.result.get('files_created', []))}")
    
    # Test Frontend Agent
    print("\n3. Testing Frontend Agent...")
    frontend_agent = FrontendAgent(workspace_path=workspace)
    frontend_task = Task(
        id="test_frontend_001",
        title="Frontend: Onboarding Page",
        description="Create Next.js onboarding wizard page",
        agent_type=AgentType.FRONTEND,
        metadata={"objective": "Onboarding wizard"}
    )
    result = frontend_agent.process_task(frontend_task)
    print(f"   Status: {result.status.value}")
    if result.result:
        print(f"   Files created: {len(result.result.get('files_created', []))}")
    
    # Test Workflow Agent
    print("\n4. Testing Workflow Agent...")
    workflow_agent = WorkflowAgent(workspace_path=workspace)
    workflow_task = Task(
        id="test_workflow_001",
        title="Workflow: Backfill Workflow",
        description="Create Temporal backfill workflow for entity sync",
        agent_type=AgentType.WORKFLOW,
        metadata={"objective": "Backfill workflow"}
    )
    result = workflow_agent.process_task(workflow_task)
    print(f"   Status: {result.status.value}")
    if result.result:
        print(f"   Files created: {len(result.result.get('files_created', []))}")
    
    # Test Coder Agent
    print("\n5. Testing Coder Agent...")
    coder_agent = CoderAgent(workspace_path=workspace)
    coder_task = Task(
        id="test_coder_001",
        title="Backend: Search API",
        description="Implement search endpoints for mappings UI",
        agent_type=AgentType.CODER,
        tech_stack=["python"],
        metadata={"objective": "Search API"}
    )
    result = coder_agent.process_task(coder_task)
    print(f"   Status: {result.status.value}")
    if result.result:
        print(f"   Files created: {len(result.result.get('files_created', []))}")
    
    print("\n[OK] Individual agent tests completed")


def test_orchestrator_breakdown():
    """Test orchestrator task breakdown."""
    print("\n" + "=" * 80)
    print("TESTING ORCHESTRATOR TASK BREAKDOWN")
    print("=" * 80)
    
    orchestrator = OrchestratorAgent()
    
    # Register test agents
    test_workspace = "./test_workspace"
    orchestrator.register_agent(InfrastructureAgent(workspace_path=test_workspace))
    orchestrator.register_agent(IntegrationAgent(workspace_path=test_workspace))
    orchestrator.register_agent(FrontendAgent(workspace_path=test_workspace))
    orchestrator.register_agent(WorkflowAgent(workspace_path=test_workspace))
    orchestrator.register_agent(CoderAgent(workspace_path=test_workspace))
    orchestrator.register_agent(TestingAgent(workspace_path=test_workspace))
    orchestrator.register_agent(QAAgent(workspace_path=test_workspace))
    orchestrator.register_agent(SecurityAgent(workspace_path=test_workspace))
    
    # Test with sample objectives from the features document
    test_objectives = [
        "QuickBooks Online OAuth integration",
        "Odoo v18 JSON-RPC client",
        "Azure WAF configuration",
        "Onboarding wizard with QBO and Odoo connections",
        "Temporal backfill workflow",
        "Mappings UI with live search"
    ]
    
    print(f"\nBreaking down {len(test_objectives)} objectives...")
    tasks = orchestrator.break_down_project(
        project_description="Multi-Platform to Odoo migration SaaS",
        objectives=test_objectives
    )
    
    print(f"\nCreated {len(tasks)} tasks")
    
    # Group by agent type
    tasks_by_type = {}
    for task in tasks:
        agent_type = task.agent_type.value
        if agent_type not in tasks_by_type:
            tasks_by_type[agent_type] = []
        tasks_by_type[agent_type].append(task)
    
    print("\nTask breakdown by agent type:")
    for agent_type, agent_tasks in sorted(tasks_by_type.items()):
        print(f"  {agent_type}: {len(agent_tasks)} tasks")
        for task in agent_tasks[:3]:  # Show first 3
            print(f"    - {task.id}: {task.title}")
        if len(agent_tasks) > 3:
            print(f"    ... and {len(agent_tasks) - 3} more")
    
    # Check dependencies
    print("\nDependency analysis:")
    tasks_with_deps = [t for t in tasks if t.dependencies]
    print(f"  Tasks with dependencies: {len(tasks_with_deps)}")
    for task in tasks_with_deps[:5]:
        print(f"    {task.id} depends on: {', '.join(task.dependencies)}")
    
    print("\n[OK] Orchestrator breakdown test completed")
    return orchestrator, tasks


def test_full_system_small():
    """Test full system with a small, manageable project."""
    print("\n" + "=" * 80)
    print("TESTING FULL SYSTEM (SMALL PROJECT)")
    print("=" * 80)
    
    from main import AgentSystem
    
    # Create test workspace
    test_workspace = "./test_workspace"
    os.makedirs(test_workspace, exist_ok=True)
    
    # Initialize system
    system = AgentSystem(workspace_path=test_workspace)
    
    # Run small project
    print("\nRunning small test project...")
    print("Objectives: QuickBooks OAuth, Odoo connection, Mappings UI")
    
    results = system.run_project(
        project_description="Multi-Platform to Odoo integration test",
        objectives=[
            "Multi-platform OAuth (QuickBooks example)",
            "Odoo connection save",
            "Mappings search UI"
        ]
    )
    
    # Print summary
    print("\n" + "-" * 80)
    print("RESULTS SUMMARY")
    print("-" * 80)
    
    status = results["final_status"]
    print(f"Total Tasks: {status['total_tasks']}")
    print(f"Completed: {status['completed']}")
    print(f"In Progress: {status['in_progress']}")
    print(f"Failed: {status['failed']}")
    print(f"Blocked: {status['blocked']}")
    print(f"Pending: {status['pending']}")
    print(f"Completion: {status['completion_percentage']:.1f}%")
    
    # Show sample files created
    print("\nSample files created:")
    file_count = 0
    for task_id, task_info in list(results["tasks"].items())[:5]:
        if task_info["status"] == "completed" and task_info.get("result"):
            files = task_info["result"].get("files_created", [])
            if files:
                print(f"  {task_id}:")
                for file in files[:2]:
                    print(f"    - {file}")
                    file_count += 1
                if len(files) > 2:
                    print(f"    ... and {len(files) - 2} more")
    
    print(f"\n[OK] Full system test completed (created {file_count} files)")


def test_with_features_document():
    """Test with objectives extracted from the features document."""
    print("\n" + "=" * 80)
    print("TESTING WITH FEATURES DOCUMENT OBJECTIVES")
    print("=" * 80)
    
    # Sample objectives from the PDF features document
    feature_objectives = [
        "Branding, domains, and TLS configuration",
        "Authentication & SSO with NextAuth",
        "Tenancy & billing with Stripe",
        "QuickBooks Online OAuth refresh",
        "Odoo v18 JSON-RPC client",
        "QBO Desktop Web Connector generator",
        "Temporal backfill workflow wiring",
        "Mappings & search UI with live search",
        "Onboarding wizard + Theme toggle",
        "Real-time jobs/errors with SSE"
    ]
    
    print(f"\nTesting with {len(feature_objectives)} objectives from features document...")
    print("(This will create a comprehensive task breakdown)")
    
    orchestrator = OrchestratorAgent()
    test_workspace = "./test_workspace"
    
    # Register agents
    orchestrator.register_agent(InfrastructureAgent(workspace_path=test_workspace))
    orchestrator.register_agent(IntegrationAgent(workspace_path=test_workspace))
    orchestrator.register_agent(FrontendAgent(workspace_path=test_workspace))
    orchestrator.register_agent(WorkflowAgent(workspace_path=test_workspace))
    orchestrator.register_agent(CoderAgent(workspace_path=test_workspace))
    
    tasks = orchestrator.break_down_project(
        project_description="QuickBooks 2 Odoo Online - Full Feature Set",
        objectives=feature_objectives
    )
    
    print(f"\n✓ Created {len(tasks)} tasks from {len(feature_objectives)} objectives")
    
    # Show breakdown
    tasks_by_agent = {}
    for task in tasks:
        agent_type = task.agent_type.value
        tasks_by_agent[agent_type] = tasks_by_agent.get(agent_type, 0) + 1
    
    print("\nTask distribution:")
    for agent_type, count in sorted(tasks_by_agent.items(), key=lambda x: x[1], reverse=True):
        print(f"  {agent_type}: {count} tasks")
    
    print("\n[OK] Features document breakdown test completed")
    return orchestrator, tasks


def verify_files_created():
    """Verify that generated files exist and have content."""
    print("\n" + "=" * 80)
    print("VERIFYING GENERATED FILES")
    print("=" * 80)
    
    test_workspace = Path("./test_workspace")
    
    if not test_workspace.exists():
        print("No test workspace found. Run tests first.")
        return
    
    # Count files by directory
    file_counts = {}
    total_files = 0
    
    for root, dirs, files in os.walk(test_workspace):
        for file in files:
            if file.endswith(('.py', '.tsx', '.tf', '.yaml', '.yml')):
                rel_path = Path(root).relative_to(test_workspace)
                dir_name = str(rel_path) if rel_path != Path('.') else 'root'
                file_counts[dir_name] = file_counts.get(dir_name, 0) + 1
                total_files += 1
    
    print(f"\nTotal files generated: {total_files}")
    print("\nFiles by directory:")
    for directory, count in sorted(file_counts.items()):
        print(f"  {directory}: {count} files")
    
    # Show sample file paths
    print("\nSample file paths:")
    sample_count = 0
    for root, dirs, files in os.walk(test_workspace):
        for file in files[:2]:  # First 2 files per directory
            if file.endswith(('.py', '.tsx', '.tf')):
                rel_path = Path(root) / file
                print(f"  {rel_path.relative_to(test_workspace)}")
                sample_count += 1
                if sample_count >= 10:
                    break
        if sample_count >= 10:
            break
    
    print("\n[OK] File verification completed")


def main():
    """Run all tests."""
    print("=" * 80)
    print("MULTI-AGENT SYSTEM TEST SUITE")
    print("=" * 80)
    
    setup_test_logging()
    
    try:
        # Test 1: Individual agents
        test_individual_agents()
        
        # Test 2: Orchestrator breakdown
        test_orchestrator_breakdown()
        
        # Test 3: Full system (small)
        test_full_system_small()
        
        # Test 4: Features document objectives
        test_with_features_document()
        
        # Test 5: Verify files
        verify_files_created()
        
        print("\n" + "=" * 80)
        print("ALL TESTS COMPLETED SUCCESSFULLY")
        print("=" * 80)
        print("\nTest workspace: ./test_workspace/")
        print("Review generated files to verify agent outputs.")
        
    except Exception as e:
        print(f"\n[ERROR] Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

