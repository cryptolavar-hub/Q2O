# Next Features Implementation Plan - Priorities 4, 5, and 7

## Summary

After successful commit of Priority 2, 3, and 6 features, we're ready to implement and test:
- **Priority 4**: Agent Communication Protocols
- **Priority 5**: Task Retry Mechanisms (enhancement)
- **Priority 7**: VCS Integration

---

## Priority 4: Agent Communication Protocols

### Implementation Plan

1. **Message Broker Abstraction**
   - Create `utils/message_broker.py` with abstract interface
   - Support Redis and in-memory (for testing/development)
   - Pub/Sub pattern implementation

2. **Message Format & Protocol**
   - Standardized JSON message schema
   - Message types: `task_complete`, `request_help`, `share_result`, `task_failed`
   - Agent discovery mechanism

3. **Integration into Agents**
   - Update `BaseAgent` to support messaging
   - Add methods: `send_message()`, `subscribe_to_messages()`, `request_help()`
   - Update `OrchestratorAgent` to coordinate messages

4. **Collaboration Features**
   - Agents can request help from peers
   - Share intermediate results
   - Coordinate on complex multi-agent tasks

### Files to Create
- `utils/message_broker.py` - Message broker abstraction
- `utils/message_protocol.py` - Message format definitions
- `agents/messaging.py` - Agent messaging mixin

---

## Priority 5: Task Retry Mechanisms (Enhancement)

### Current Status
- ✅ `utils/retry.py` exists with exponential backoff
- ⚠️ Not integrated into agent task processing

### Implementation Plan

1. **Agent Integration**
   - Update `BaseAgent.process_task()` to use retry decorator
   - Add retry configuration per agent type
   - Integrate with load balancer (retry on different agent)

2. **Retry Policies**
   - Configurable retry counts per agent type
   - Different backoff strategies (exponential, linear, fixed)
   - Max retry delay configuration

3. **Advanced Features**
   - Retry with different agent instance (via load balancer)
   - Partial failure recovery
   - Circuit breaker integration (from Priority 6)

### Files to Update
- `agents/base_agent.py` - Add retry to `process_task()`
- `agents/orchestrator.py` - Handle retry coordination
- `utils/retry.py` - Add more retry strategies

---

## Priority 7: VCS Integration

### Implementation Plan

1. **Git Integration**
   - Create `utils/git_manager.py` for Git operations
   - Auto-commit after successful task completion
   - Branch management for feature branches

2. **Auto-Commit Features**
   - Commit messages generated from task descriptions
   - File staging (only changed files)
   - Configurable commit frequency (per task, per agent, per project)

3. **Pull Request Creation**
   - Auto-create PRs for feature branches
   - PR description from project objectives
   - Integration with GitHub API

4. **Integration Points**
   - Hook into task completion in `BaseAgent`
   - Option to enable/disable in configuration
   - Respect `.gitignore` patterns

### Files to Create
- `utils/git_manager.py` - Git operations wrapper
- `utils/vcs_integration.py` - VCS abstraction (Git, future: SVN, Mercurial)
- `config/vcs_config.json` - VCS configuration

---

## Testing Strategy

### For Priority 4 (Agent Communication)
1. Test direct agent-to-agent messaging
2. Test pub/sub pattern with multiple subscribers
3. Test agent discovery mechanism
4. Test help request workflow
5. Test result sharing between agents

### For Priority 5 (Task Retry)
1. Test automatic retry on failure
2. Test retry with different agent instance
3. Test exponential backoff timing
4. Test retry policy configuration
5. Test circuit breaker integration

### For Priority 7 (VCS Integration)
1. Test auto-commit after task completion
2. Test branch creation for features
3. Test PR creation via GitHub API
4. Test `.gitignore` respect
5. Test configuration enable/disable

---

## Implementation Order

1. **Priority 5** (Retry) - Enhances existing functionality, quick win
2. **Priority 4** (Communication) - Foundation for future collaboration
3. **Priority 7** (VCS) - Requires external API setup, most complex

---

## Success Criteria

- ✅ Agents can communicate directly without Orchestrator
- ✅ Tasks automatically retry on failure with exponential backoff
- ✅ System auto-commits code changes to Git
- ✅ PRs created automatically for feature branches
- ✅ All features testable and documented

