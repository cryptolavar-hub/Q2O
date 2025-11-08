# Quick Start Testing Guide

This guide explains the best ways to test the Multi-Agent Development System.

## Testing Options

### 1. **Quick Test Script** (Recommended to Start)

Run the comprehensive test script that exercises all components:

```bash
python test_agents.py
```

This will:
- Test each agent individually
- Test orchestrator task breakdown
- Run a small full-system test
- Test with features document objectives
- Verify generated files

**Output**: Check `./test_workspace/` for generated files.

---

### 2. **Test Individual Agents**

Test specific agents one at a time:

```python
from agents import InfrastructureAgent, AgentType, Task

agent = InfrastructureAgent(workspace_path="./test")
task = Task(
    id="test_001",
    title="Test: Azure WAF",
    description="Create WAF configuration",
    agent_type=AgentType.INFRASTRUCTURE,
    metadata={"infrastructure_type": "terraform"}
)
result = agent.process_task(task)
print(result.status.value)
```

---

### 3. **Test with Sample Configuration**

Use the test configuration file:

```bash
python main.py --config test_config.json
```

Or manually:

```bash
python main.py \
  --project "Multi-Platform Odoo Migration Test" \
  --objective "Multi-platform OAuth (QuickBooks, SAGE)" \
  --objective "Odoo v18 client" \
  --workspace ./test_workspace
```

---

### 4. **Test with Features Document Objectives**

Create a config file based on the PDF features:

```json
{
  "project_description": "QuickBooks 2 Odoo Online - Full Feature Set",
  "objectives": [
    "Branding, domains, and TLS configuration",
    "Authentication & SSO with NextAuth",
    "Tenancy & billing with Stripe",
    "QuickBooks Online OAuth refresh",
    "Odoo v18 JSON-RPC client",
    "Temporal backfill workflow wiring",
    "Mappings & search UI with live search",
    "Onboarding wizard + Theme toggle"
  ]
}
```

Then run:
```bash
python main.py --config features_test.json
```

---

## What to Check After Testing

### ✅ Generated Files

Check the workspace directory structure:

```
test_workspace/
├── api/
│   └── app/
│       ├── clients/
│       │   ├── qbo.py          # QuickBooks client
│       │   └── odoo.py         # Odoo client
│       ├── oauth_qbo.py         # OAuth handler
│       ├── billing.py           # Stripe integration
│       └── ...
├── web/
│   ├── pages/
│   │   ├── onboarding.tsx      # Onboarding page
│   │   ├── mappings.tsx         # Mappings UI
│   │   └── ...
│   └── components/
│       └── ThemeToggle.tsx      # Theme component
├── worker/
│   ├── run_worker.py            # Temporal worker
│   └── temporal/
│       └── activities/
│           └── entities.py     # Sync activities
├── shared/
│   └── temporal_defs/
│       └── workflows/
│           └── backfill.py     # Workflow definition
└── infra/
    └── terraform/
        └── azure/
            ├── waf.tf           # WAF configuration
            ├── appinsights.tf    # Monitoring
            └── ...
```

### ✅ Code Quality

- **FastAPI**: Check for proper async/await, Pydantic models
- **Next.js**: Check for TypeScript types, proper component structure
- **Terraform**: Check for proper resource definitions
- **Temporal**: Check for proper workflow/activity decorators

### ✅ Task Dependencies

Verify that:
- Infrastructure tasks run before integration tasks
- Integration tasks run before frontend/workflow tasks
- Testing tasks depend on implementation tasks
- QA/Security tasks depend on testing tasks

---

## Testing Workflow

### Step 1: Start Small

```bash
# Test one agent type
python test_agents.py
```

### Step 2: Test Full System

```bash
# Use small test config
python main.py --config test_config.json
```

### Step 3: Test with Real Objectives

```bash
# Use features from document
python main.py --config features_full.json
```

### Step 4: Verify Output

```bash
# Check generated files
ls -R test_workspace/
```

---

## Common Issues & Solutions

### Issue: No files generated

**Solution**: Check workspace path exists and is writable:
```python
os.makedirs("./test_workspace", exist_ok=True)
```

### Issue: Tasks not assigned

**Solution**: Verify agents are registered:
```python
orchestrator.register_agent(agent)
```

### Issue: Dependencies not met

**Solution**: Check task dependencies are in correct order:
```python
# Infrastructure → Integration → Frontend/Backend → Testing → QA
```

---

## Performance Testing

Test with different project sizes:

```python
# Small: 1-3 objectives
# Medium: 5-10 objectives  
# Large: 15+ objectives (from features document)
```

Monitor:
- Task creation time
- Agent processing time
- File generation time
- Memory usage

---

## Integration Testing

Test the full workflow:

1. **Orchestrator** breaks down objectives → creates tasks
2. **Specialized agents** process tasks → generate files
3. **Testing agent** creates tests
4. **QA agent** reviews code
5. **Security agent** checks security

Verify each step produces expected output.

---

## Next Steps

After basic testing:

1. **Customize templates**: Modify agent code generation to match your exact needs
2. **Add more patterns**: Extend agents with additional code patterns
3. **Enhance QA checks**: Add domain-specific quality checks
4. **Improve task detection**: Enhance orchestrator's objective analysis

---

## Debugging Tips

Enable debug logging:
```bash
python main.py --log-level DEBUG --config test_config.json
```

Check agent status:
```python
print(agent.get_status())
print(orchestrator.get_project_status())
```

Review task metadata:
```python
for task in orchestrator.project_tasks.values():
    print(f"{task.id}: {task.metadata}")
```

