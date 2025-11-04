# Testing Guide for Multi-Agent Development System

This guide explains how to test the multi-agent system with different scenarios.

## Quick Start Testing

### 1. Small Test (Recommended First)

Test with a single objective to verify the system works:

```bash
python test_agent_system.py
```

This will:
- Create a test workspace
- Run with "QuickBooks OAuth authentication" objective
- Show progress and results
- Verify files were created

### 2. Full Test

Test with multiple objectives:

```bash
python test_agent_system.py full
```

Or use the config file directly:

```bash
python main.py --config test_config.json --workspace ./test_workspace_full
```

### 3. Custom Test

Create your own test configuration:

```bash
# Create a JSON config file
cat > my_test.json << EOF
{
  "project_description": "My Test Project",
  "objectives": [
    "QuickBooks OAuth authentication",
    "Odoo client integration"
  ]
}
EOF

# Run it
python main.py --config my_test.json --workspace ./my_test_workspace
```

## Testing Different Agent Types

### Test Infrastructure Agent

```bash
python main.py \
  --project "Infrastructure Test" \
  --objective "Azure WAF configuration" \
  --objective "Helm chart setup" \
  --workspace ./test_infra
```

Expected output:
- `infra/terraform/azure/waf.tf`
- `infra/terraform/azure/variables.tf`
- `k8s/helm/q2o/values.yaml`

### Test Integration Agent

```bash
python main.py \
  --project "Integration Test" \
  --objective "QuickBooks OAuth authentication" \
  --objective "Odoo v18 JSON-RPC client" \
  --objective "Stripe billing integration" \
  --workspace ./test_integration
```

Expected output:
- `api/app/oauth_qbo.py`
- `api/app/clients/qbo.py`
- `api/app/clients/odoo.py`
- `api/app/billing.py`

### Test Frontend Agent

```bash
python main.py \
  --project "Frontend Test" \
  --objective "Onboarding wizard UI" \
  --objective "Mappings page with search" \
  --objective "Theme toggle component" \
  --workspace ./test_frontend
```

Expected output:
- `web/pages/onboarding.tsx`
- `web/pages/mappings.tsx`
- `web/components/ThemeToggle.tsx`

### Test Workflow Agent

```bash
python main.py \
  --project "Workflow Test" \
  --objective "Temporal backfill workflow" \
  --workspace ./test_workflow
```

Expected output:
- `shared/temporal_defs/workflows/backfill.py`
- `worker/temporal/activities/entities.py`
- `worker/run_worker.py`

### Test Security Agent

```bash
python main.py \
  --project "Security Test" \
  --objective "API authentication" \
  --workspace ./test_security
```

The Security Agent will review generated code for security issues.

## Testing Complete Feature Sets

### Test Feature 1: Branding & Infrastructure

```bash
python main.py \
  --project "Feature 1 Test" \
  --objective "Azure WAF configuration" \
  --objective "Helm chart setup" \
  --objective "Terraform infrastructure" \
  --workspace ./test_feature1
```

### Test Feature 4: QBO & Odoo Integration

```bash
python main.py \
  --project "Feature 4 Test" \
  --objective "QuickBooks OAuth authentication" \
  --objective "Odoo v18 JSON-RPC client" \
  --objective "Connection management" \
  --workspace ./test_feature4
```

### Test Feature 6: Temporal Workflow

```bash
python main.py \
  --project "Feature 6 Test" \
  --objective "Temporal backfill workflow" \
  --objective "Entity sync activities" \
  --objective "Rate limiting for QBO" \
  --workspace ./test_feature6
```

### Test Feature 8: Onboarding & UI

```bash
python main.py \
  --project "Feature 8 Test" \
  --objective "Onboarding wizard UI" \
  --objective "Theme toggle component" \
  --workspace ./test_feature8
```

## Verification Checklist

After running tests, verify:

### ✅ Files Created
- [ ] Infrastructure files (Terraform, Helm) in correct directories
- [ ] Integration code in `api/app/`
- [ ] Frontend files in `web/pages/` and `web/components/`
- [ ] Workflow files in `shared/` and `worker/`

### ✅ Task Dependencies
- [ ] Infrastructure tasks complete before integration tasks
- [ ] Integration tasks complete before frontend tasks
- [ ] Testing tasks depend on implementation tasks
- [ ] QA tasks depend on testing tasks

### ✅ Agent Assignment
- [ ] Infrastructure tasks → Infrastructure Agent
- [ ] Integration tasks → Integration Agent
- [ ] Frontend tasks → Frontend Agent
- [ ] Workflow tasks → Workflow Agent
- [ ] Security review → Security Agent

### ✅ Code Quality
- [ ] Generated code follows project structure
- [ ] Code includes proper imports
- [ ] Code has docstrings
- [ ] FastAPI patterns used for Python APIs
- [ ] TypeScript used for frontend

## Debugging

### Enable Debug Logging

```bash
python main.py \
  --config test_config.json \
  --workspace ./test_workspace \
  --log-level DEBUG
```

### Check Task Status

The system prints task status at each iteration. Look for:
- `PENDING` - Waiting for dependencies
- `IN_PROGRESS` - Being processed
- `COMPLETED` - Finished successfully
- `FAILED` - Error occurred
- `BLOCKED` - Dependencies not met

### Common Issues

1. **Tasks stuck in BLOCKED**
   - Check if dependencies completed
   - Verify task IDs in dependencies match actual task IDs

2. **No files created**
   - Check workspace path is correct
   - Verify agent processed the task (check logs)
   - Ensure task completed successfully

3. **Wrong agent assigned**
   - Check objective keywords match agent detection
   - Review orchestrator's `_detect_objective_type` method

## Advanced Testing

### Test with Real Feature List

Create a config from the features document:

```python
import json

features = [
    "Branding, domains, and TLS",
    "Authentication & SSO",
    "Tenancy & billing (Stripe)",
    "QuickBooks Online & Odoo v18 integrations",
    "QBO Desktop starter",
    "Backfill, incremental & Temporal wiring",
    "Mappings & search (UI + API)",
    "Onboarding wizard + Theme",
    "Real-time jobs/errors (SSE)",
    "Observability & audit",
    "Security & WAF",
    "Deployment: Helm + CI/CD"
]

config = {
    "project_description": "QuickBooks 2 Odoo Online - Full Feature Set",
    "objectives": features
}

with open("full_features.json", "w") as f:
    json.dump(config, f, indent=2)
```

Then run:
```bash
python main.py --config full_features.json --workspace ./full_test
```

### Performance Testing

Test with many objectives:

```bash
python main.py \
  --project "Performance Test" \
  --objective "Feature 1" \
  --objective "Feature 2" \
  --objective "Feature 3" \
  --objective "Feature 4" \
  --objective "Feature 5" \
  --workspace ./perf_test \
  --log-level WARNING
```

## Next Steps

1. **Start Small**: Run `python test_agent_system.py` first
2. **Verify Output**: Check that files are created correctly
3. **Test Each Agent**: Run individual agent type tests
4. **Full Feature Test**: Test with complete feature list
5. **Refine**: Adjust agent behavior based on results

## Example Output

```
================================================================================
Starting Multi-Agent Development Project
Project: Multi-Platform to Odoo v18 Migration - Test Project
Platforms: QuickBooks, SAGE, Wave
Objectives: 5
================================================================================
2024-01-01 10:00:00 - orchestrator.orchestrator_main - INFO - Breaking down project: ...
2024-01-01 10:00:01 - orchestrator.orchestrator_main - INFO - Created 15 tasks from project breakdown

--- Iteration 1 ---
2024-01-01 10:00:02 - infrastructure.infrastructure_main - INFO - Processing infrastructure task: ...
2024-01-01 10:00:03 - integration.integration_main - INFO - Processing integration task: ...

================================================================================
PROJECT RESULTS
================================================================================

Total Tasks: 15
Completed: 15
In Progress: 0
Failed: 0
Completion: 100.0%
```

