"""
Test script for task tracking integration.

This script tests that:
1. Database connection works
2. Tasks can be created
3. Tasks can be updated
4. Progress calculation works
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "addon_portal"))

# Set environment variables for database connection
os.environ.setdefault("DB_DSN", "postgresql+psycopg://q2o_user:Q2OPostgres2025(@localhost:5432/q2o")
os.environ.setdefault("Q2O_PROJECT_ID", "test-project-123")
os.environ.setdefault("Q2O_TENANT_ID", "1")
os.environ.setdefault("ENABLE_TASK_TRACKING", "true")

async def test_task_tracking():
    """Test task tracking functionality."""
    print("=" * 80)
    print("Testing Task Tracking Integration")
    print("=" * 80)
    print()
    
    db = None
    try:
        from addon_portal.api.services.agent_task_service import (
            create_task,
            update_task_status,
            calculate_project_progress,
            get_project_tasks
        )
        from addon_portal.api.core.db import AsyncSessionLocal
        
        # Create database session
        db = AsyncSessionLocal()
        
        print("✓ Database session created")
        
        # Test 1: Create a task (without tenant_id since it's optional)
        print("\n[Test 1] Creating a task...")
        task = await create_task(
            db=db,
            project_id="test-project-123",
            agent_type="coder",
            task_name="Test Task: Generate API endpoint",
            task_description="This is a test task to verify task tracking works",
            task_type="code_generation",
            agent_id="test-agent-1",
            priority=1,
            tenant_id=None,  # tenant_id is optional
        )
        print(f"✓ Task created: {task.task_id}")
        task_id = task.task_id
        
        # Test 2: Update task status to running
        print("\n[Test 2] Updating task status to 'running'...")
        await update_task_status(
            db=db,
            task_id=task_id,
            status="running",
            progress_percentage=25.0,
        )
        print("✓ Task status updated to 'running'")
        
        # Test 3: Update progress
        print("\n[Test 3] Updating task progress to 50%...")
        await update_task_status(
            db=db,
            task_id=task_id,
            status="running",
            progress_percentage=50.0,
        )
        print("✓ Task progress updated to 50%")
        
        # Test 4: Update LLM usage
        print("\n[Test 4] Updating LLM usage...")
        from addon_portal.api.services.agent_task_service import update_task_llm_usage
        await update_task_llm_usage(
            db=db,
            task_id=task_id,
            llm_calls_count=3,
            llm_tokens_used=1500,
            llm_cost_usd=0.05,
        )
        print("✓ LLM usage updated")
        
        # Test 5: Complete the task
        print("\n[Test 5] Completing the task...")
        await update_task_status(
            db=db,
            task_id=task_id,
            status="completed",
            progress_percentage=100.0,
            execution_metadata={"files_created": ["test_file.py"], "outputs": {"status": "success"}},
        )
        print("✓ Task completed")
        
        # Test 6: Calculate project progress
        print("\n[Test 6] Calculating project progress...")
        progress = await calculate_project_progress(db, "test-project-123")
        print(f"✓ Progress calculated:")
        print(f"  - Total tasks: {progress['total_tasks']}")
        print(f"  - Completed: {progress['completed_tasks']}")
        print(f"  - Failed: {progress['failed_tasks']}")
        print(f"  - Completion: {progress['completion_percentage']:.1f}%")
        
        # Test 7: Get project tasks
        print("\n[Test 7] Getting project tasks...")
        tasks = await get_project_tasks(db, "test-project-123")
        print(f"✓ Found {len(tasks)} task(s)")
        for task in tasks:
            print(f"  - {task.task_name}: {task.status} ({task.progress_percentage}%)")
        
        # Close session
        await db.close()
        
        print("\n" + "=" * 80)
        print("✓ All tests passed!")
        print("=" * 80)
        return True
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Ensure database session is closed
        if db:
            await db.close()


if __name__ == "__main__":
    # Windows compatibility: Use SelectorEventLoop for psycopg async
    import platform
    if platform.system() == "Windows":
        import selectors
        loop = asyncio.SelectorEventLoop(selectors.SelectSelector())
        asyncio.set_event_loop(loop)
        success = loop.run_until_complete(test_task_tracking())
        loop.close()
    else:
        success = asyncio.run(test_task_tracking())
    sys.exit(0 if success else 1)

