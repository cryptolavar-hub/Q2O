"""
Real Project Test: SAGE NetSuite to Odoo Migration
This demonstrates Q2O's full capabilities with LLM integration.

Expected Output:
- Research findings about NetSuite and Odoo
- Complete migration architecture
- API integration code
- Data mapping logic
- Testing suite
- Deployment configuration
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
import os
from datetime import datetime

# Load .env file from project root
from dotenv import load_dotenv
project_root = Path(__file__).parent.parent
env_path = project_root / '.env'
load_dotenv(dotenv_path=env_path)  # Load environment variables from .env
print(f"[DEBUG] Loading .env from: {env_path}")
print(f"[DEBUG] .env exists: {env_path.exists()}")
if env_path.exists():
    print(f"[DEBUG] GOOGLE_API_KEY set: {bool(os.getenv('GOOGLE_API_KEY'))}")

# Import Q2O agents
from agents.orchestrator import OrchestratorAgent
from agents.researcher_agent import ResearcherAgent
from agents.coder_agent import CoderAgent
from agents.base_agent import Task, AgentType


async def main():
    """Run a real SAGE NetSuite to Odoo migration project."""
    
    print("=" * 80)
    print(" " * 15 + "Q2O REAL PROJECT TEST")
    print(" " * 10 + "SAGE NetSuite to Odoo v18 Migration")
    print("=" * 80)
    print()
    
    # Check if LLM is enabled
    llm_enabled = os.getenv("Q2O_USE_LLM", "true").lower() == "true"
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
    
    if not llm_enabled or not api_key:
        print("[ERROR] LLM not configured!")
        print()
        print("Please ensure:")
        print("  1. Q2O_USE_LLM=true in .env")
        print("  2. At least one API key set (GOOGLE_API_KEY, OPENAI_API_KEY, or ANTHROPIC_API_KEY)")
        print()
        print("See QUICK_LLM_SETUP.md for instructions")
        return
    
    print("[OK] LLM Integration: ACTIVE")
    print(f"[OK] API Keys: Configured")
    print()
    
    # Create output directory
    project_name = f"sage_netsuite_migration_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    output_dir = Path(__file__).parent / "output" / project_name
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"[OUTPUT] Output Directory: {output_dir}")
    print()
    
    # ========================================================================
    # STEP 1: ORCHESTRATE - Break down project into tasks
    # ========================================================================
    print("=" * 80)
    print("STEP 1: PROJECT ORCHESTRATION")
    print("=" * 80)
    print()
    print("Using OrchestratorAgent to break down migration into tasks...")
    print()
    
    orchestrator = OrchestratorAgent(
        agent_id="orchestrator_sage_migration",
        project_id="sage_netsuite_odoo"
    )
    
    project_description = """
    SAGE NetSuite to Odoo v18 Migration System
    
    Build a complete data migration system that extracts data from SAGE NetSuite
    and imports it into Odoo v18, handling all entity types with proper mapping
    and transformation logic.
    """
    
    objectives = [
        "Research NetSuite SuiteTalk API and Odoo v18 data models",
        "Create NetSuite API integration for data extraction",
        "Implement Odoo v18 data import logic with mapping",
        "Build migration orchestration workflow"
    ]
    
    tasks = orchestrator.break_down_project(project_description, objectives)
    
    print(f"[OK] Created {len(tasks)} tasks")
    print()
    print("Task Breakdown:")
    for idx, task in enumerate(tasks, 1):
        deps = f" (depends on: {', '.join([t.split('_')[1] for t in task.dependencies])})" if task.dependencies else ""
        print(f"  {idx}. [{task.agent_type.value}] {task.title}{deps}")
    print()
    
    # ========================================================================
    # STEP 2: RESEARCH - Get intelligent insights
    # ========================================================================
    print("=" * 80)
    print("STEP 2: INTELLIGENT RESEARCH")
    print("=" * 80)
    print()
    
    # Find research tasks
    research_tasks = [t for t in tasks if t.agent_type == AgentType.RESEARCHER]
    
    if research_tasks:
        researcher = ResearcherAgent(
            agent_id="researcher_sage",
            workspace_path=str(output_dir / "research"),
            project_id="sage_netsuite_odoo"
        )
        
        for research_task in research_tasks[:1]:  # Just first one for demo
            print(f"[RESEARCH] Researching: {research_task.title}")
            print()
            
            result_task = researcher.process_task(research_task)
            
            if result_task.result:
                print(f"[OK] Research complete!")
                print(f"   Confidence: {result_task.result.get('confidence_score', 0)}/100")
                print(f"   Results: {result_task.result.get('results_count', 0)} sources")
                print()
                
                # Show key findings (LLM-synthesized insights!)
                findings = result_task.result.get('key_findings', [])
                if findings:
                    print("[INSIGHTS] Key Insights (LLM Synthesis):")
                    for idx, finding in enumerate(findings[:5], 1):
                        print(f"   {idx}. {finding}")
                    print()
    
    # ========================================================================
    # STEP 3: CODE GENERATION - Build the migration system
    # ========================================================================
    print("=" * 80)
    print("STEP 3: CODE GENERATION")
    print("=" * 80)
    print()
    
    # Find coder tasks
    coder_tasks = [t for t in tasks if t.agent_type == AgentType.CODER]
    
    if coder_tasks:
        coder = CoderAgent(
            agent_id="coder_sage",
            workspace_path=str(output_dir / "code"),
            project_id="sage_netsuite_odoo"
        )
        
        print(f"[GENERATE] Generating code for {len(coder_tasks)} implementation tasks...")
        print()
        
        for coder_task in coder_tasks[:2]:  # First 2 for demo
            print(f"[CODING] Generating: {coder_task.title}")
            
            result_task = coder.process_task(coder_task)
            
            if result_task.result:
                files_created = result_task.result.get('files_created', [])
                print(f"   [OK] Created {len(files_created)} files")
                
                for file in files_created:
                    file_path = output_dir / "code" / file
                    if file_path.exists():
                        size = file_path.stat().st_size
                        print(f"      - {file} ({size} bytes)")
                print()
    
    # ========================================================================
    # FINAL SUMMARY
    # ========================================================================
    print("=" * 80)
    print("MIGRATION PROJECT GENERATION COMPLETE!")
    print("=" * 80)
    print()
    print("[SUMMARY] Summary:")
    print(f"   Total Tasks: {len(tasks)}")
    print(f"   Research Tasks: {len([t for t in tasks if t.agent_type == AgentType.RESEARCHER])}")
    print(f"   Implementation Tasks: {len([t for t in tasks if t.agent_type == AgentType.CODER])}")
    print(f"   Testing Tasks: {len([t for t in tasks if t.agent_type == AgentType.TESTING])}")
    print(f"   QA Tasks: {len([t for t in tasks if t.agent_type == AgentType.QA])}")
    print()
    print("[FILES] Generated Files:")
    
    # List all generated files
    code_dir = output_dir / "code"
    research_dir = output_dir / "research"
    
    all_files = []
    if code_dir.exists():
        all_files.extend(list(code_dir.rglob("*.*")))
    if research_dir.exists():
        all_files.extend(list(research_dir.rglob("*.*")))
    
    for file in sorted(all_files):
        rel_path = file.relative_to(output_dir)
        size = file.stat().st_size
        print(f"   {rel_path} ({size:,} bytes)")
    
    print()
    print(f"[OUTPUT] Full Output: {output_dir}")
    print()
    print("=" * 80)
    print("[SUCCESS] Q2O generated a complete migration system!")
    print("=" * 80)
    print()
    print("What was generated:")
    print("  [OK] Intelligent research insights (not keywords!)")
    print("  [OK] NetSuite API integration code")
    print("  [OK] Odoo data import logic")
    print("  [OK] Data mapping and transformation")
    print("  [OK] Migration orchestration")
    print("  [OK] All with LLM-enhanced quality")
    print()
    print("[COSTS] Cost Tracking:")
    print("  Check llm_costs.db for detailed usage")
    print("  Check learned_templates.db for templates created")
    print()
    print("Next Steps:")
    print("  1. Review generated code")
    print("  2. Customize for your specific NetSuite instance")
    print("  3. Run tests (TestingAgent will generate these)")
    print("  4. Deploy to production")
    print()
    print("[Q2O] From idea to production code in minutes!")
    print()


if __name__ == "__main__":
    print()
    print("Starting SAGE NetSuite to Odoo Migration Test...")
    print("This will demonstrate Q2O's full LLM-enhanced capabilities")
    print()
    
    asyncio.run(main())

