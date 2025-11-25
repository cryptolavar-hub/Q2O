# Q2O Agentic System - Comprehensive Implementation Plan

**Date**: November 21, 2025  
**Status**: READY FOR EXECUTION  
**Total Issues**: 20 (12 bugs + 8 architectural issues)

---

## Executive Summary

This plan provides a **dependency-aware, impact-ordered** implementation strategy for fixing all identified bugs and architectural issues. Fixes are organized into **4 phases** with clear dependencies, enabling parallel work where possible while ensuring critical foundations are fixed first.

**Key Strategy**:
1. **Foundation First**: Fix event loop and database issues (blocks everything)
2. **Core Functionality**: Fix task distribution and tracking (enables other features)
3. **Enhancement**: Fix dependency access and event emission (improves reliability)
4. **Architecture**: Address architectural issues (long-term improvements)

---

## Dependency Analysis

### Critical Dependency Chain

```
Event Loop Conflicts (Bug #2)
    ↓ (blocks)
Task Tracking (Bug #1 - FIXED, but needs event loop fix)
    ↓ (enables)
Project Completion Status (Bug #6)
    ↓ (enables)
Dashboard Updates (Bug #4)

Coder Task Distribution (Bug #3)
    ↓ (enables)
Research Dependency Access (Bug #9)
    ↓ (enables)
Testing Agent File Discovery (Bug #10)
```

### Independent Fixes (Can be done in parallel)
- Unicode Encoding (Bug #7) ✅ FIXED
- Workspace Path (Bug #5) ✅ FIXED
- Database Connection Leaks (Bug #1) ✅ FIXED
- Load Balancer Health Checks (Bug #11)
- Message Broker Configuration (Bug #12)

---

## PHASE 1: FOUNDATION FIXES (CRITICAL - Days 1-2)

**Goal**: Fix fundamental infrastructure issues that block all other functionality

### Fix #1.1: Complete Event Loop Conflict Resolution ⚠️ PARTIAL → ✅ COMPLETE

**Priority**: CRITICAL (SEVERITY: 9/10)  
**Dependencies**: None (foundational)  
**Blocks**: Task tracking, event emission, project completion  
**Estimated Time**: 4-6 hours

**Current Status**: Partially fixed but still has issues with existing loops

**Problem**:
- `run_async()` creates new event loop when one exists
- Database connection pool bound to wrong event loop
- Causes `RuntimeError: is bound to a different event loop`

**Solution**:
```python
# File: agents/task_tracking.py:301-356
# IMPROVE: Better event loop handling with proper thread safety

def run_async(coro):
    """Run async function synchronously with proper event loop handling."""
    import platform
    import selectors
    import concurrent.futures
    import threading
    
    # Try to use existing event loop first
    try:
        loop = asyncio.get_running_loop()
        # Use thread-safe approach for existing loop
        future = concurrent.futures.Future()
        
        def run_in_thread():
            try:
                result = asyncio.run_coroutine_threadsafe(coro, loop).result(timeout=30)
                future.set_result(result)
            except Exception as e:
                future.set_exception(e)
        
        thread = threading.Thread(target=run_in_thread, daemon=True)
        thread.start()
        thread.join(timeout=35)  # Slightly longer than coro timeout
        
        if thread.is_alive():
            raise TimeoutError("Task tracking operation timed out after 35 seconds")
        
        return future.result()
        
    except RuntimeError:
        # No running loop - create a new one
        if platform.system() == "Windows":
            loop = asyncio.SelectorEventLoop(selectors.SelectSelector())
        else:
            loop = asyncio.new_event_loop()
        
        asyncio.set_event_loop(loop)
        
        try:
            # IMPORTANT: Create new database session factory for this loop
            # This ensures connection pool is bound to correct loop
            global _task_tracking_engine, _task_tracking_session_factory
            
            # Reset session factory to create new connections
            _task_tracking_session_factory = None
            
            return loop.run_until_complete(coro)
        finally:
            loop.close()
            # Clean up event loop reference
            try:
                asyncio.set_event_loop(None)
            except:
                pass
```

**Testing**:
- [ ] Test with existing event loop (from FastAPI)
- [ ] Test without event loop (standalone execution)
- [ ] Test concurrent task tracking calls
- [ ] Verify no "bound to different event loop" errors
- [ ] Verify database connections properly closed

**Success Criteria**:
- No event loop errors in logs
- Task tracking works reliably
- Database connections properly managed

---

### Fix #1.2: Fix Async Event Emission ⚠️ PARTIAL → ✅ COMPLETE

**Priority**: HIGH (SEVERITY: 7/10)  
**Dependencies**: Fix #1.1 (event loop)  
**Blocks**: Dashboard updates, real-time monitoring  
**Estimated Time**: 3-4 hours

**Current Status**: Partially fixed but coroutines never awaited

**Problem**:
- `asyncio.create_task()` called from sync code
- Coroutines never awaited
- Runtime warnings flood logs
- Memory leaks from unawaited coroutines

**Solution**:
```python
# File: agents/base_agent.py:278-384
# FIX: Properly await coroutines or use fire-and-forget with background thread

def _emit_task_started(self, task_id: str, task: Task):
    """Emit dashboard event for task started."""
    try:
        from api.dashboard.events import get_event_manager
        import asyncio
        import threading
        
        event_manager = get_event_manager()
        
        def emit_in_background():
            """Emit events in background thread with its own event loop."""
            try:
                # Create new event loop for this thread
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                try:
                    loop.run_until_complete(event_manager.emit_task_update(
                        task_id=task_id,
                        status="in_progress",
                        title=task.title,
                        agent_id=self.agent_id,
                        agent_type=self.agent_type.value,
                        started_at=task.started_at.isoformat() if task.started_at else None,
                        dependencies=task.dependencies,
                        progress=0
                    ))
                finally:
                    loop.close()
            except Exception as e:
                self.logger.debug(f"Failed to emit task started event: {e}")
        
        # Run in background thread (fire-and-forget)
        thread = threading.Thread(target=emit_in_background, daemon=True)
        thread.start()
        
    except Exception:
        # Fail silently if dashboard not available
        pass

def _emit_task_complete(self, task_id: str, task: Task):
    """Emit dashboard event for task completed."""
    try:
        from api.dashboard.events import get_event_manager
        import asyncio
        import threading
        
        event_manager = get_event_manager()
        
        # Calculate duration
        duration = None
        if task.started_at and task.completed_at:
            duration = (task.completed_at - task.started_at).total_seconds()
        
        def emit_in_background():
            """Emit events in background thread with its own event loop."""
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                try:
                    # Emit task update
                    loop.run_until_complete(event_manager.emit_task_update(
                        task_id=task_id,
                        status="completed",
                        title=task.title,
                        agent_id=self.agent_id,
                        agent_type=self.agent_type.value,
                        started_at=task.started_at.isoformat() if task.started_at else None,
                        completed_at=task.completed_at.isoformat() if task.completed_at else None,
                        duration=duration,
                        progress=100
                    ))
                    
                    # Emit agent activity
                    loop.run_until_complete(event_manager.emit_agent_activity(
                        agent_id=self.agent_id,
                        agent_type=self.agent_type.value,
                        activity="task_completed",
                        task_id=task_id,
                        status="idle" if len(self.active_tasks) == 0 else "active"
                    ))
                finally:
                    loop.close()
            except Exception as e:
                self.logger.debug(f"Failed to emit task complete event: {e}")
        
        # Run in background thread (fire-and-forget)
        thread = threading.Thread(target=emit_in_background, daemon=True)
        thread.start()
        
    except Exception:
        # Fail silently if dashboard not available
        pass

def _emit_task_failed(self, task_id: str, task: Task, error: str):
    """Emit dashboard event for task failed."""
    # Similar implementation to _emit_task_complete
    # ... (same pattern)
```

**Testing**:
- [ ] Verify no RuntimeWarning about unawaited coroutines
- [ ] Verify events appear in dashboard
- [ ] Test with multiple concurrent events
- [ ] Verify no memory leaks
- [ ] Test with dashboard unavailable (should fail gracefully)

**Success Criteria**:
- No runtime warnings
- Dashboard events emitted successfully
- No memory leaks

---

## PHASE 2: CORE FUNCTIONALITY FIXES (CRITICAL - Days 2-3)

**Goal**: Fix core task distribution and project completion issues

### Fix #2.1: Fix Coder Agent Task Distribution ❌ NOT FIXED → ✅ COMPLETE

**Priority**: CRITICAL (SEVERITY: 9/10)  
**Dependencies**: None (can be done in parallel with Phase 1)  
**Blocks**: Backend code generation, project completion  
**Estimated Time**: 2-3 hours

**Current Status**: Orchestrator logic prevents coder tasks for integration objectives

**Problem**:
- Orchestrator only creates coder tasks for `["api", "backend", "service", "model"]` objectives
- Integration objectives (e.g., "QuickBooks migration") don't trigger coder tasks
- Coder agents remain idle while integration agents work

**Solution**:
```python
# File: agents/orchestrator.py:421-451
# FIX: Always create coder tasks when code generation is needed

# BEFORE (BUGGY):
needs_coder = (
    objective_type in ["api", "backend", "service", "model"] or 
    not tasks or 
    impl_tasks_exist  # This condition is wrong!
)

# AFTER (FIXED):
# CRITICAL FIX: Always create coder tasks for objectives that require backend code
# Integration, workflow, and frontend tasks ALWAYS need backend support
needs_coder = (
    objective_type in ["api", "backend", "service", "model"] or 
    objective_type in ["integration", "workflow", "frontend"] or  # ADD THIS LINE
    not tasks  # Fallback: if no tasks created, create generic coder task
)

# IMPROVED VERSION: More explicit logic
def _needs_coder_task(self, objective_type: str, tasks: List[Task], objective: str) -> bool:
    """
    Determine if a coder task is needed for this objective.
    
    Args:
        objective_type: Detected objective type
        tasks: List of tasks already created
        objective: Original objective string
        
    Returns:
        True if coder task is needed
    """
    # Always create coder task for explicit backend objectives
    if objective_type in ["api", "backend", "service", "model"]:
        return True
    
    # Integration/workflow/frontend objectives ALWAYS need backend code
    if objective_type in ["integration", "workflow", "frontend"]:
        return True
    
    # If no tasks created, create generic coder task
    if not tasks:
        return True
    
    # Check if objective mentions code generation keywords
    code_keywords = ["code", "implement", "create", "build", "develop", "generate"]
    if any(keyword in objective.lower() for keyword in code_keywords):
        return True
    
    return False

# Update the code:
needs_coder = self._needs_coder_task(objective_type, tasks, objective)

if needs_coder:
    # Build dependencies: coder tasks depend on research, infrastructure, and integration tasks
    coder_dependencies = [
        t.id for t in tasks 
        if t.agent_type in [AgentType.INFRASTRUCTURE, AgentType.INTEGRATION, AgentType.RESEARCHER]
    ]
    
    coder_task = Task(
        id=f"task_{start_counter:04d}_coder",
        title=f"Backend: {objective}",
        description=f"Implement backend functionality for: {objective}\n\nContext: {context}",
        agent_type=AgentType.CODER,
        tech_stack=tech_stack,
        dependencies=coder_dependencies,
        metadata={
            "objective": objective,
            "complexity": self._estimate_complexity(objective),
            "requires_backend": True  # Mark as requiring backend
        }
    )
    tasks.append(coder_task)
    start_counter += 1
```

**Testing**:
- [ ] Test with integration objective ("QuickBooks migration")
- [ ] Test with workflow objective ("Temporal workflow")
- [ ] Test with frontend objective ("React dashboard")
- [ ] Verify coder tasks created
- [ ] Verify coder agents receive tasks
- [ ] Verify backend code generated

**Success Criteria**:
- Coder tasks created for all code generation objectives
- Coder agents receive and process tasks
- Backend code generated successfully

---

### Fix #2.2: Fix Project Completion Status ❌ NOT FIXED → ✅ COMPLETE

**Priority**: HIGH (SEVERITY: 8/10)  
**Dependencies**: Fix #1.1 (event loop), Fix #1.2 (event emission)  
**Blocks**: Dashboard metrics, project status visibility  
**Estimated Time**: 4-5 hours

**Current Status**: Subprocess monitoring not implemented

**Problem**:
- Subprocess launched but never monitored
- `execution_status` stays "running" forever
- Dashboard shows projects as always running

**Solution**:
```python
# File: addon_portal/api/services/project_execution_service.py
# ADD: Background task to monitor subprocess completion

import asyncio
from asyncio import create_task
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

async def _monitor_process(
    process_id: int, 
    project_id: str, 
    session: AsyncSession,
    check_interval: int = 5
):
    """
    Monitor subprocess and update status when complete.
    
    Args:
        process_id: Process ID from subprocess.Popen
        project_id: Project ID to update
        session: Database session
        check_interval: Seconds between status checks
    """
    import psutil
    
    try:
        # Get process object
        try:
            process = psutil.Process(process_id)
        except psutil.NoSuchProcess:
            # Process already finished
            await _update_project_status(project_id, "completed", session)
            return
        
        # Monitor until process completes
        while True:
            try:
                # Check if process is still running
                if not process.is_running():
                    # Process completed - check exit code
                    exit_code = process.returncode
                    
                    if exit_code == 0:
                        await _update_project_status(project_id, "completed", session)
                    else:
                        await _update_project_status(project_id, "failed", session)
                    
                    break
                
                # Wait before next check
                await asyncio.sleep(check_interval)
                
            except psutil.NoSuchProcess:
                # Process finished between checks
                await _update_project_status(project_id, "completed", session)
                break
            except Exception as e:
                logger.error(f"Error monitoring process {process_id}: {e}")
                # Mark as failed on monitoring error
                await _update_project_status(project_id, "failed", session)
                break
                
    except Exception as e:
        logger.error(f"Failed to monitor process {process_id}: {e}")
        await _update_project_status(project_id, "failed", session)

async def _update_project_status(
    project_id: str, 
    status: str, 
    session: AsyncSession
):
    """Update project execution status in database."""
    from addon_portal.api.models.projects import Project
    
    try:
        result = await session.execute(
            select(Project).where(Project.project_id == project_id)
        )
        project = result.scalar_one_or_none()
        
        if project:
            project.execution_status = status
            project.updated_at = datetime.now()
            await session.commit()
            logger.info(f"Updated project {project_id} status to {status}")
    except Exception as e:
        logger.error(f"Failed to update project status: {e}")
        await session.rollback()

# In execute_project() function:
async def execute_project(
    project_id: str,
    project_name: str,
    description: str,
    objectives: str,
    output_folder: str,
    tenant_id: int,
    db: AsyncSession
):
    """Execute a project with subprocess monitoring."""
    # ... existing code ...
    
    # Launch subprocess
    process = subprocess.Popen(
        [sys.executable, "main.py", ...],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=output_folder
    )
    
    # Store process ID
    process_id = process.pid
    
    # Start background monitoring task
    monitoring_task = create_task(
        _monitor_process(process_id, project_id, db)
    )
    
    # Store monitoring task reference (for cancellation if needed)
    # ... store in project metadata or task registry ...
    
    return {"status": "running", "process_id": process_id}
```

**Alternative Solution** (if psutil not available):
```python
# Simpler solution using subprocess.Popen.poll()
async def _monitor_process_simple(
    process: subprocess.Popen,
    project_id: str,
    session: AsyncSession,
    check_interval: int = 5
):
    """Monitor subprocess using poll() method."""
    while True:
        return_code = process.poll()
        
        if return_code is not None:
            # Process completed
            if return_code == 0:
                await _update_project_status(project_id, "completed", session)
            else:
                await _update_project_status(project_id, "failed", session)
            break
        
        await asyncio.sleep(check_interval)
```

**Testing**:
- [ ] Test successful project completion
- [ ] Test failed project (non-zero exit code)
- [ ] Test process monitoring with long-running projects
- [ ] Test process monitoring cancellation
- [ ] Verify status updates in database
- [ ] Verify dashboard shows correct status

**Success Criteria**:
- Project status updates to "completed" when done
- Project status updates to "failed" on error
- Dashboard shows correct project status
- No processes left running indefinitely

---

## PHASE 3: DEPENDENCY AND ACCESS FIXES (HIGH - Days 3-4)

**Goal**: Fix dependency access and improve task result sharing

### Fix #3.1: Fix Research Dependency Access ⚠️ PARTIAL → ✅ COMPLETE

**Priority**: HIGH (SEVERITY: 5/10)  
**Dependencies**: Fix #2.1 (coder task distribution)  
**Blocks**: Research utilization, code quality  
**Estimated Time**: 3-4 hours

**Current Status**: Agents can't access orchestrator to get dependency tasks

**Problem**:
- `_get_dependency_task()` tries to access orchestrator but agents don't have reference
- Falls back to global task registry (may not exist)
- Research results not accessible to dependent agents

**Solution**:
```python
# File: main.py:131-276 (AgentSystem.__init__)
# ADD: Pass orchestrator reference to agents

class AgentSystem:
    def __init__(self, ...):
        # ... existing code ...
        
        # Initialize orchestrator
        self.orchestrator = OrchestratorAgent()
        
        # Initialize agents with orchestrator reference
        agent_kwargs = {
            "workspace_path": str(self.workspace_path),
            "project_layout": self.project_layout,
            "project_id": self.project_id,
            "tenant_id": self.tenant_id,
            "orchestrator": self.orchestrator  # ADD THIS
        }
        
        # ... rest of agent initialization ...

# File: agents/base_agent.py:84-125
# ADD: Store orchestrator reference

class BaseAgent(ABC):
    def __init__(
        self, 
        agent_id: str, 
        agent_type: AgentType, 
        project_layout: Optional[ProjectLayout] = None, 
        enable_messaging: bool = True,
        project_id: Optional[str] = None,
        tenant_id: Optional[int] = None,
        orchestrator: Optional[Any] = None  # ADD THIS
    ):
        # ... existing code ...
        self.orchestrator = orchestrator  # ADD THIS

# File: agents/research_aware_mixin.py:70-83
# FIX: Use orchestrator reference

def _get_dependency_task(self, dep_id: str):
    """Get dependency task from orchestrator or registry."""
    # Try to get from orchestrator (now available!)
    if hasattr(self, 'orchestrator') and self.orchestrator:
        task = self.orchestrator.project_tasks.get(dep_id)
        if task:
            return task
    
    # Fallback: Try to get from global task registry (if available)
    try:
        from utils.task_registry import get_task
        return get_task(dep_id)
    except ImportError:
        pass
    
    return None
```

**Alternative Solution** (Global Task Registry):
```python
# File: utils/task_registry.py (NEW FILE)
# CREATE: Global task registry singleton

from typing import Dict, Optional
from agents.base_agent import Task
import threading

class TaskRegistry:
    """Global task registry for cross-agent task access."""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._tasks: Dict[str, Task] = {}
        return cls._instance
    
    def register_task(self, task: Task):
        """Register a task in the registry."""
        self._tasks[task.id] = task
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task from the registry."""
        return self._tasks.get(task_id)
    
    def clear(self):
        """Clear all tasks (for testing)."""
        self._tasks.clear()

def get_task_registry() -> TaskRegistry:
    """Get the global task registry instance."""
    return TaskRegistry()

def register_task(task: Task):
    """Register a task in the global registry."""
    get_task_registry().register_task(task)

def get_task(task_id: str) -> Optional[Task]:
    """Get a task from the global registry."""
    return get_task_registry().get_task(task_id)

# File: agents/orchestrator.py
# REGISTER tasks in registry when created

from utils.task_registry import register_task

def break_down_project(self, ...):
    # ... existing code ...
    
    for task in tasks:
        self.project_tasks[task.id] = task
        self.task_queue.append(task)
        register_task(task)  # ADD THIS - register in global registry
```

**Testing**:
- [ ] Test research dependency access
- [ ] Test with orchestrator reference
- [ ] Test with global registry fallback
- [ ] Verify research results accessible to dependent agents
- [ ] Test with multiple projects

**Success Criteria**:
- Agents can access dependency tasks
- Research results passed to dependent agents
- Code generation uses research context

---

### Fix #3.2: Fix Testing Agent File Discovery ⚠️ WORKAROUND → ✅ COMPLETE

**Priority**: MEDIUM (SEVERITY: 5/10)  
**Dependencies**: Fix #3.1 (dependency access)  
**Blocks**: Test generation, code quality  
**Estimated Time**: 2-3 hours

**Current Status**: Uses heuristics to find files, unreliable

**Problem**:
- `_get_implemented_files()` uses heuristics to find files
- No reliable way to get files from dependency tasks
- Tests created for non-existent files

**Solution**:
```python
# File: agents/testing_agent.py:84-118
# FIX: Get actual file paths from dependency task results

def _get_implemented_files(self, task: Task) -> List[str]:
    """
    Get list of implemented files to test.
    Gets actual file paths from dependency task results.
    
    Args:
        task: The testing task
        
    Returns:
        List of file paths to test
    """
    implemented_files = []
    
    # Get files from dependency tasks (coder, integration, workflow, frontend)
    for dep_id in task.dependencies:
        dep_task = self._get_dependency_task(dep_id)
        
        if dep_task and dep_task.status == TaskStatus.COMPLETED:
            # Get files from task result
            if dep_task.result and isinstance(dep_task.result, dict):
                # Try various file list keys
                files = (
                    dep_task.result.get("files_created", []) or
                    dep_task.result.get("integration_files", []) or
                    dep_task.result.get("frontend_files", []) or
                    dep_task.result.get("workflow_files", []) or
                    dep_task.result.get("node_files", [])
                )
                
                if files:
                    # Convert relative paths to absolute if needed
                    for file_path in files:
                        if not os.path.isabs(file_path):
                            full_path = os.path.join(self.workspace_path, file_path)
                        else:
                            full_path = file_path
                        
                        if os.path.exists(full_path):
                            implemented_files.append(full_path)
                        else:
                            self.logger.warning(f"File from dependency not found: {full_path}")
    
    # Fallback: Check task metadata for file references
    if not implemented_files:
        metadata_files = task.metadata.get("files_to_test", [])
        for file_path in metadata_files:
            full_path = os.path.join(self.workspace_path, file_path)
            if os.path.exists(full_path):
                implemented_files.append(full_path)
    
    # Last resort: Search workspace for Python files
    if not implemented_files:
        self.logger.warning(f"No implemented files found via dependencies, searching workspace")
        # Search for Python files in common locations
        search_dirs = [
            os.path.join(self.workspace_path, "src"),
            os.path.join(self.workspace_path, "api"),
            os.path.join(self.workspace_path, "app"),
            self.workspace_path
        ]
        
        for search_dir in search_dirs:
            if os.path.exists(search_dir):
                for root, dirs, files in os.walk(search_dir):
                    # Skip test directories
                    if "test" in root.lower() or "__pycache__" in root:
                        continue
                    
                    for file in files:
                        if file.endswith(".py") and not file.startswith("test_"):
                            file_path = os.path.join(root, file)
                            implemented_files.append(file_path)
                
                if implemented_files:
                    break
    
    self.logger.info(f"Found {len(implemented_files)} implemented files to test")
    return implemented_files

def _get_dependency_task(self, dep_id: str):
    """Get dependency task (uses orchestrator or registry)."""
    # Use orchestrator if available
    if hasattr(self, 'orchestrator') and self.orchestrator:
        return self.orchestrator.project_tasks.get(dep_id)
    
    # Fallback to global registry
    try:
        from utils.task_registry import get_task
        return get_task(dep_id)
    except ImportError:
        pass
    
    return None
```

**Testing**:
- [ ] Test with coder task dependencies
- [ ] Test with integration task dependencies
- [ ] Test with multiple file types
- [ ] Test fallback file search
- [ ] Verify tests created for actual files
- [ ] Verify test execution works

**Success Criteria**:
- Testing agent finds actual implemented files
- Tests created for correct files
- Test execution successful

---

## PHASE 4: ARCHITECTURAL IMPROVEMENTS (MEDIUM - Days 4-5)

**Goal**: Address architectural issues for long-term reliability

### Fix #4.1: Add Task Result Storage

**Priority**: MEDIUM  
**Dependencies**: Fix #1.1 (event loop)  
**Estimated Time**: 4-5 hours

**Solution**: Store task results in database for recovery and audit

---

### Fix #4.2: Improve Dependency Resolution

**Priority**: MEDIUM  
**Dependencies**: Fix #3.1 (dependency access)  
**Estimated Time**: 3-4 hours

**Solution**: Add dependency result validation and retry logic

---

### Fix #4.3: Add Agent Failure Recovery

**Priority**: MEDIUM  
**Dependencies**: None  
**Estimated Time**: 4-5 hours

**Solution**: Implement agent health monitoring and automatic recovery

---

## IMPLEMENTATION ORDER SUMMARY

### Week 1: Critical Fixes

**Day 1-2: Foundation**
1. ✅ Fix #1.1: Complete Event Loop Conflict Resolution (4-6h)
2. ✅ Fix #1.2: Fix Async Event Emission (3-4h)
3. ✅ Fix #2.1: Fix Coder Agent Task Distribution (2-3h) - Can do in parallel

**Day 3: Core Functionality**
4. ✅ Fix #2.2: Fix Project Completion Status (4-5h)

**Day 4-5: Dependencies**
5. ✅ Fix #3.1: Fix Research Dependency Access (3-4h)
6. ✅ Fix #3.2: Fix Testing Agent File Discovery (2-3h)

### Week 2: Architectural Improvements

**Day 6-7: Architecture**
7. Fix #4.1: Add Task Result Storage (4-5h)
8. Fix #4.2: Improve Dependency Resolution (3-4h)
9. Fix #4.3: Add Agent Failure Recovery (4-5h)

### Week 3: Polish and Testing

**Day 8-10: Testing and Validation**
10. Comprehensive testing of all fixes
11. Performance testing
12. Integration testing
13. Documentation updates

---

## PARALLEL WORK OPPORTUNITIES

**Can be done in parallel with Phase 1**:
- Fix #2.1 (Coder Task Distribution) - Independent
- Bug #11 (Load Balancer Health Checks) - Independent
- Bug #12 (Message Broker Configuration) - Independent

**Can be done in parallel with Phase 2**:
- Fix #3.1 (Research Dependency Access) - After Fix #2.1
- Architectural improvements - Independent

---

## TESTING STRATEGY

### Unit Tests
- Test each fix independently
- Mock dependencies where needed
- Verify fix behavior

### Integration Tests
- Test full project execution
- Test agent coordination
- Test database operations

### End-to-End Tests
- Test complete project lifecycle
- Test failure recovery
- Test dashboard updates

### Performance Tests
- Test with 100+ tasks
- Test database connection pool
- Test memory usage

---

## SUCCESS METRICS

### Phase 1 Success
- ✅ No event loop errors
- ✅ Task tracking works reliably
- ✅ Dashboard events emitted
- ✅ No memory leaks

### Phase 2 Success
- ✅ Coder agents receive tasks
- ✅ Backend code generated
- ✅ Project status updates correctly
- ✅ Dashboard shows correct status

### Phase 3 Success
- ✅ Research results accessible
- ✅ Testing agent finds files
- ✅ Tests execute successfully
- ✅ Code quality improved

### Phase 4 Success
- ✅ Task results stored
- ✅ Dependency resolution robust
- ✅ Agent recovery working
- ✅ System reliability improved

---

## RISK MITIGATION

### High Risk Areas
1. **Event Loop Fixes**: May break existing functionality
   - **Mitigation**: Comprehensive testing, gradual rollout
   
2. **Database Changes**: May affect existing projects
   - **Mitigation**: Backward compatibility, migration scripts

3. **Task Distribution**: May change task creation logic
   - **Mitigation**: Test with various objective types

### Rollback Plan
- Keep original code in version control
- Feature flags for new functionality
- Gradual rollout with monitoring

---

**Implementation Plan Complete**  
**Ready for Execution**

