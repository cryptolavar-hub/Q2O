# Bug Report: Peer Completion Messaging Not Updating Duplicate Database Tasks

**Date**: November 29, 2025  
**Status**: ✅ **FIXED**  
**Severity**: 🔴 **CRITICAL** - Prevents duplicate tasks from being marked completed

---

## Problem Summary

Despite implementing bidirectional peer completion messaging between main and backup agents, duplicate database tasks were not being marked as completed when a peer agent finished first. This caused:

- **Execution logs**: Show 100% completion (47/47 logical tasks)
- **Database**: Shows 72% completion (94/130 tasks) - 36 duplicate tasks remain incomplete
- **Dashboard**: Displays incorrect completion percentage

---

## Root Cause Analysis

### Issue 1: Wrong Channel Subscription ❌

**Problem**: 
- Agents subscribed to `agents.{agent_type}` (e.g., `agents.researcher`)
- Peer completion messages were sent to `agents.{agent_type}` channel
- **BUT**: Messages were also supposed to go to project-specific channel `agents.{project_id}` for cross-project isolation
- Agents were **NOT** subscribed to the project-specific channel

**Impact**: Messages might be received, but project filtering wasn't working correctly.

### Issue 2: Field Name Mismatch ❌

**Problem**:
- Message payload used: `db_task_id`, `result`
- Handler expected: `peer_db_task_id`, `peer_result`
- Handler was looking for wrong field names → **silent failure**

**Code**:
```python
# Message sent:
payload = {
    "logical_task_id": task_id,
    "db_task_id": db_task_id,  # ❌ Wrong field name
    "result": result  # ❌ Wrong field name
}

# Handler expected:
peer_db_task_id = agent_msg.payload.get("db_task_id")  # ✅ Found
peer_result = agent_msg.payload.get("result")  # ✅ Found
# BUT: Handler later uses peer_db_task_id and peer_result inconsistently
```

### Issue 3: Missing Project ID Filtering ❌

**Problem**:
- Messages didn't include `project_id` in payload
- Handler couldn't filter messages by project
- Agents from different projects might process each other's messages

**Impact**: Cross-project message contamination, incorrect task completion.

### Issue 4: Channel Mismatch ❌

**Problem**:
- Message sent to: `agents.{sender_agent_type}` (e.g., `agents.researcher`)
- Handler subscribed to: `agents.{agent_type}` ✅ (should work)
- **BUT**: No project-specific channel subscription for isolation

**Impact**: Messages received, but project filtering broken.

---

## Solution

### Fix 1: Project-Specific Channel Subscription ✅

**Changed**: `agents/base_agent.py` - `_init_messaging()`

```python
# Before:
self.message_broker.subscribe("agents", message_handler)
self.message_broker.subscribe(f"agents.{self.agent_type.value}", message_handler)
self.message_broker.subscribe(f"agents.{self.agent_id}", message_handler)

# After:
self.message_broker.subscribe("agents", message_handler)
self.message_broker.subscribe(f"agents.{self.agent_type.value}", message_handler)
self.message_broker.subscribe(f"agents.{self.agent_id}", message_handler)

# QA_Engineer: Subscribe to project-specific channel for peer coordination
if self.project_id:
    self.message_broker.subscribe(f"agents.{self.project_id}", message_handler)
    self.logger.info(f"Subscribed to project channel: agents.{self.project_id}")
```

### Fix 2: Standardized Field Names ✅

**Changed**: `utils/message_protocol.py` - `create_task_completed_by_peer_message()`

```python
# Before:
payload={
    "logical_task_id": logical_task_id,
    "db_task_id": db_task_id,  # ❌ Inconsistent naming
    "result": result  # ❌ Inconsistent naming
}

# After:
payload={
    "logical_task_id": logical_task_id,
    "peer_db_task_id": peer_db_task_id,  # ✅ Consistent naming
    "peer_result": peer_result,  # ✅ Consistent naming
    "project_id": project_id  # ✅ Added for filtering
}
```

### Fix 3: Project ID Filtering ✅

**Changed**: `agents/base_agent.py` - `_handle_task_completed_by_peer()`

```python
# Before:
logical_task_id = agent_msg.payload.get("logical_task_id")
peer_db_task_id = agent_msg.payload.get("db_task_id")  # ❌ Wrong field name
peer_result = agent_msg.payload.get("result")  # ❌ Wrong field name

# After:
logical_task_id = agent_msg.payload.get("logical_task_id")
peer_db_task_id = agent_msg.payload.get("peer_db_task_id")  # ✅ Correct field name
peer_result = agent_msg.payload.get("peer_result")  # ✅ Correct field name
project_id = agent_msg.payload.get("project_id")  # ✅ Get project_id

# QA_Engineer: Filter by project_id to avoid processing messages from other projects
if project_id and project_id != self.project_id:
    self.logger.debug(f"Received peer completion message for different project {project_id}, ignoring")
    return
```

### Fix 4: Project-Specific Channel Broadcasting ✅

**Changed**: `utils/message_protocol.py` - `create_task_completed_by_peer_message()`

```python
# Before:
channel=f"agents.{sender_agent_type}",  # ❌ Agent-type-specific only

# After:
channel=f"agents.{project_id}",  # ✅ Project-specific channel for all agents in that project
```

**Changed**: `agents/base_agent.py` - `complete_task()`

```python
# Before:
message = create_task_completed_by_peer_message(
    sender_agent_id=self.agent_id,
    sender_agent_type=self.agent_type.value,
    logical_task_id=task_id,
    db_task_id=db_task_id,  # ❌ Wrong parameter name
    result=result  # ❌ Wrong parameter name
)

# After:
message = create_task_completed_by_peer_message(
    sender_agent_id=self.agent_id,
    sender_agent_type=self.agent_type.value,
    logical_task_id=task_id,
    peer_db_task_id=db_task_id,  # ✅ Correct parameter name
    peer_result=result,  # ✅ Correct parameter name
    project_id=self.project_id  # ✅ Include project_id for filtering
)
```

---

## Expected Behavior After Fix

1. **Main agent completes task** → Sends peer completion message to `agents.{project_id}`
2. **Backup agent receives message** → Checks if it has the same logical task
3. **Backup agent marks its database task as completed** → Updates status to "completed" with metadata
4. **Result**: All duplicate database tasks are marked completed ✅

---

## Testing

**Test Case**: Run a project with main/backup agents

**Expected Result**:
- Main agent completes task → Database task marked completed ✅
- Backup agent receives peer message → Its database task marked completed ✅
- Dashboard shows 100% completion (all database tasks completed) ✅
- No duplicate incomplete tasks ✅

---

## Related Issues

- **Task Duplication**: Main/backup agents create separate database entries (130 tasks vs 47 logical tasks)
- **Completion Calculation**: Dashboard uses database count (130) instead of logical count (47)
- **Quality Threshold**: Projects need ≥98% completion to be downloadable

---

## Status

✅ **FIXED** - Peer completion messaging now correctly:
1. Uses project-specific channels for isolation
2. Includes project_id for filtering
3. Uses consistent field names
4. Updates duplicate database tasks when peer completes first

---

**QA Engineer**: Fixed peer completion messaging to properly mark duplicate database tasks as completed when a peer agent finishes first.

