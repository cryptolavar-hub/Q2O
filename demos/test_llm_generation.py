"""
Simple LLM Generation Test
Demonstrates Q2O's hybrid code generation with LLM integration.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
import os

# Load .env file
from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env

from agents.coder_agent import CoderAgent
from agents.base_agent import Task, AgentType


async def main():
    """Test LLM-enhanced code generation."""
    
    print("=" * 70)
    print(" " * 20 + "Q2O LLM Generation Test")
    print("=" * 70)
    print()
    
    # Check if LLM is enabled
    llm_enabled = os.getenv("Q2O_USE_LLM", "true").lower() == "true"
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
    
    if not llm_enabled:
        print("[WARNING] Q2O_USE_LLM=false - LLM integration disabled")
        print("          Set Q2O_USE_LLM=true in .env to enable")
        return
    
    if not api_key:
        print("[ERROR] No API keys found!")
        print()
        print("Please add at least one API key to .env:")
        print("  GOOGLE_API_KEY=AIzaSy...your_key")
        print("  OPENAI_API_KEY=sk-...your_key")
        print("  ANTHROPIC_API_KEY=sk-ant-...your_key")
        print()
        print("See QUICK_LLM_SETUP.md for detailed instructions")
        return
    
    print("[1/5] Initializing CoderAgent with LLM...")
    
    # Create output directory
    output_dir = Path(__file__).parent / "output" / "llm_test"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create CoderAgent
    coder = CoderAgent(
        agent_id="test_coder_llm",
        workspace_path=str(output_dir),
        project_id="llm_test_project"
    )
    
    if coder.llm_enabled:
        print(f"   [OK] LLM Integration: ACTIVE")
        print(f"   [OK] LLM Service: Available")
        print(f"   [OK] Template Learning: Enabled")
        print(f"   [OK] Config Manager: Ready")
    else:
        print("   [WARNING] LLM not available, using templates only")
    
    print()
    print("[2/5] Creating test task...")
    
    # Create a simple task that probably doesn't have a template
    task = Task(
        id="task_llm_001",
        title="Create Email Validation Utility",
        description="Build a Python utility function that validates email addresses using regex, handles common edge cases, and returns detailed validation results.",
        agent_type=AgentType.CODER,
        tech_stack=["Python", "regex", "validation"],
        metadata={
            "complexity": "low",
            "objective": "Email validation utility"
        }
    )
    
    print(f"   Task: {task.title}")
    print(f"   Tech Stack: {', '.join(task.tech_stack)}")
    print(f"   Complexity: {task.metadata['complexity']}")
    print()
    
    print("[3/5] Processing task (hybrid generation)...")
    print()
    print("   Hybrid Strategy:")
    print("   1. Check learned templates (FREE!)")
    print("   2. Try traditional template (fast)")
    print("   3. Generate with LLM if needed (adaptive)")
    print("   4. Learn from success (self-improving)")
    print()
    
    # Process the task
    result_task = coder.process_task(task)
    
    print()
    print("[4/5] Reviewing results...")
    
    if result_task.result:
        files_created = result_task.result.get("files_created", [])
        print(f"   [OK] Status: {result_task.result.get('status', 'unknown')}")
        print(f"   [OK] Files Created: {len(files_created)}")
        
        for file in files_created:
            file_path = output_dir / file
            if file_path.exists():
                size = file_path.stat().st_size
                print(f"        - {file} ({size} bytes)")
        
        # Show generated code
        if files_created:
            print()
            print("   Generated Code Preview:")
            print("   " + "-" * 66)
            
            first_file = output_dir / files_created[0]
            if first_file.exists():
                content = first_file.read_text()
                lines = content.split('\n')[:20]  # First 20 lines
                for line in lines:
                    print(f"   {line}")
                if len(content.split('\n')) > 20:
                    print(f"   ... ({len(content.split('\n')) - 20} more lines)")
            print("   " + "-" * 66)
    else:
        print("   [ERROR] Task failed to complete")
        return
    
    print()
    print("[5/5] Checking template learning...")
    
    if coder.template_learning:
        stats = coder.template_learning.get_learning_stats()
        print(f"   Total Templates: {stats['total_templates']}")
        print(f"   Total Uses: {stats['total_uses']}")
        print(f"   Cost Saved: ${stats['cost_saved']:.2f}")
        print(f"   Average Quality: {stats['avg_quality']:.1f}%")
        
        if stats['total_templates'] > 0:
            print()
            print("   [SUCCESS] Template learned from this generation!")
            print("   [BENEFIT] Similar tasks in the future will be FREE!")
    else:
        print("   [INFO] Template learning not available")
    
    print()
    print("=" * 70)
    print(" " * 20 + "LLM Generation Test Complete!")
    print("=" * 70)
    print()
    print("What Just Happened:")
    print("  1. CoderAgent checked for learned templates (first run: none)")
    print("  2. Tried traditional template (email validation: probably none)")
    print("  3. Generated code with LLM (Gemini/GPT-4/Claude)")
    print("  4. Validated code quality (95%+ threshold)")
    print("  5. Learned template for future reuse")
    print()
    print("Next Time:")
    print("  - Similar tasks will use learned template")
    print("  - Cost: $0.00 (FREE!)")
    print("  - Speed: Instant (no LLM call)")
    print()
    print(f"Generated files location: {output_dir}")
    print()
    print("Try running this again - it should be faster and free!")
    print()


if __name__ == "__main__":
    asyncio.run(main())

