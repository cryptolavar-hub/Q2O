# LLM Tracking and Logs Implementation

## Overview
This document details the implementation of LLM usage tracking with actual model names, LLM usage logs, and template learning dashboard integration.

## Implementation Date
November 25, 2025

## Issues Addressed

### 1. LLM Usage Tracking with Actual Model Names ✅
**Problem**: Dashboard showed hardcoded model names (Gemini 1.5 Pro, GPT-4 Turbo, Claude 3.5 Sonnet) instead of actual models in use (e.g., Gemini 2.5 Flash).

**Solution**:
- Modified `utils/llm_service.py` to store actual model names during initialization:
  - `self.gemini_model_name` - stores actual Gemini model (default: "gemini-2.5-flash")
  - `self.openai_model_name` - stores actual OpenAI model (default: "gpt-4-turbo")
  - `self.anthropic_model_name` - stores actual Anthropic model
- Updated `get_usage_stats()` to track models per provider in nested structure
- Modified `addon_portal/api/routers/llm_management.py` to return model names in provider breakdown
- Updated frontend `addon_portal/apps/admin-portal/src/pages/llm/index.tsx` to display actual model names using `formatModelName()` helper

**Files Modified**:
- `utils/llm_service.py`
- `addon_portal/api/routers/llm_management.py`
- `addon_portal/apps/admin-portal/src/pages/llm/index.tsx`

### 2. LLM Usage Logs ✅
**Problem**: No way to view detailed logs of individual LLM API calls.

**Solution**:
- Created database model `addon_portal/api/models/llm_usage.py` (`LLMUsageLog`)
- Created API endpoint `/api/llm/logs` with filtering capabilities:
  - Date range: 1day, 7days, 30days, all
  - Agent type filter
  - Provider filter
  - Status filter: success, error, cached
  - Pagination support
- Created `utils/llm_logger.py` for async logging (non-blocking)
- Integrated logging into `utils/llm_service.py` to log each LLM call automatically

**Files Created**:
- `addon_portal/api/models/llm_usage.py`
- `utils/llm_logger.py`

**Files Modified**:
- `addon_portal/api/routers/llm_management.py`
- `utils/llm_service.py`

### 3. Template Learning Dashboard ⚠️ (Needs Verification)
**Status**: Template learning engine exists (`utils/template_learning_engine.py`) but needs verification and integration testing.

**Next Steps**:
- Verify template learning is working
- Test template generation and storage
- Ensure templates appear in dashboard

## Database Migration Required

### Migration: Create `llm_usage_logs` Table

**File**: `addon_portal/api/alembic/versions/XXXX_create_llm_usage_logs.py`

**Table Schema**:
```sql
CREATE TABLE llm_usage_logs (
    id SERIAL PRIMARY KEY,
    request_id VARCHAR(255) UNIQUE NOT NULL,
    project_id VARCHAR(255),
    task_id VARCHAR(255),
    agent_type VARCHAR(100) NOT NULL,
    agent_id VARCHAR(255),
    provider VARCHAR(50) NOT NULL,
    model VARCHAR(100) NOT NULL,
    input_tokens INTEGER DEFAULT 0,
    output_tokens INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0,
    input_cost FLOAT DEFAULT 0.0,
    output_cost FLOAT DEFAULT 0.0,
    total_cost FLOAT DEFAULT 0.0,
    duration_seconds FLOAT DEFAULT 0.0,
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    cache_hit BOOLEAN DEFAULT FALSE,
    system_prompt_hash VARCHAR(64),
    user_prompt_hash VARCHAR(64),
    response_preview TEXT,
    metadata JSON,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_llm_usage_logs_request_id ON llm_usage_logs(request_id);
CREATE INDEX idx_llm_usage_logs_project_id ON llm_usage_logs(project_id);
CREATE INDEX idx_llm_usage_logs_task_id ON llm_usage_logs(task_id);
CREATE INDEX idx_llm_usage_logs_agent_type ON llm_usage_logs(agent_type);
CREATE INDEX idx_llm_usage_logs_provider ON llm_usage_logs(provider);
CREATE INDEX idx_llm_usage_logs_model ON llm_usage_logs(model);
CREATE INDEX idx_llm_usage_logs_success ON llm_usage_logs(success);
CREATE INDEX idx_llm_usage_logs_cache_hit ON llm_usage_logs(cache_hit);
CREATE INDEX idx_llm_usage_logs_created_at ON llm_usage_logs(created_at);
CREATE INDEX idx_llm_logs_provider_model ON llm_usage_logs(provider, model);
CREATE INDEX idx_llm_logs_project_agent ON llm_usage_logs(project_id, agent_type);
CREATE INDEX idx_llm_logs_success_cache ON llm_usage_logs(success, cache_hit);
```

## Testing Checklist

### Model Names Display
- [ ] Dashboard shows "Gemini 2.5 Flash" (or actual model) instead of "Gemini 1.5 Pro"
- [ ] Provider cards display correct model names
- [ ] Provider usage details table shows correct model names
- [ ] Model names update correctly when different models are used

### LLM Usage Logs
- [ ] `/api/llm/logs` endpoint returns logs
- [ ] Date range filtering works (1day, 7days, 30days, all)
- [ ] Agent type filtering works
- [ ] Provider filtering works
- [ ] Status filtering works (success, error, cached)
- [ ] Pagination works correctly
- [ ] Logs page displays logs correctly
- [ ] Logs are being saved to database when LLM calls are made

### LLM Service Integration
- [ ] LLM calls are logged automatically
- [ ] Logging doesn't block LLM calls (async/non-blocking)
- [ ] Failed LLM calls are logged with error messages
- [ ] Cache hits are marked correctly in logs

## Next Steps After Testing

1. **If Testing Successful**:
   - Create and run database migration
   - Verify template learning engine
   - Complete template learning dashboard integration

2. **If Issues Found**:
   - Document issues
   - Fix bugs
   - Re-test

## Integration with Agentic System Implementation Plan

These fixes are foundational and should not interfere with the Agentic System Implementation Plan. They provide:
- Better observability (actual model names, usage logs)
- Cost tracking accuracy
- Debugging capabilities

All changes are backward compatible and non-breaking.

## Files Changed Summary

### Created:
- `addon_portal/api/models/llm_usage.py` - Database model for LLM usage logs
- `utils/llm_logger.py` - Async logging helper
- `docs/LLM_TRACKING_AND_LOGS_IMPLEMENTATION.md` - This document

### Modified:
- `utils/llm_service.py` - Store model names, integrate logging
- `addon_portal/api/routers/llm_management.py` - Add logs endpoint, fix provider breakdown
- `addon_portal/apps/admin-portal/src/pages/llm/index.tsx` - Display actual model names
- `agents/base_agent.py` - Resolved merge conflicts

### Merge Conflicts Resolved:
- `addon_portal/api/routers/llm_management.py` - Resolved datetime import conflict
- `agents/base_agent.py` - Resolved event emission conflicts

