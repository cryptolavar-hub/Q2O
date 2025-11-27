# LLM Multi-Model Fallback Implementation

**Date**: November 26, 2025  
**Status**: IMPLEMENTED ✅

---

## Executive Summary

Implemented a comprehensive multi-level fallback system for LLM providers to ensure maximum reliability and availability. The system now supports:

1. **Provider-level fallback**: Gemini → OpenAI → Anthropic → Rules-based
2. **Model-level fallback within each provider**: Multiple models per provider with automatic fallback
3. **Model-specific error detection**: Automatically skips unavailable models (404 errors)

---

## Problem Statement

### Issues Identified:
1. **LLM Provider Failures**: Projects were failing when primary LLM provider was unavailable
2. **Model Not Found Errors**: Using outdated/invalid model names (e.g., `gemini-1.5-pro`, `gpt-5.mini`)
3. **No Fallback Strategy**: System would fail completely if primary model was unavailable
4. **Event Loop Errors**: "Event loop is closed" errors when LLM calls failed

### User Requirements:
- Sequential fallback: `gemini-3-pro` → `gemini-2.5-pro` → `gemini-2.5-flash` → `gpt-4o-mini` → `gpt-4-turbo` → `gpt-4o` → `claude-3-5-sonnet-20250219` → Rules-based

---

## Solution Architecture

### 1. Multi-Model Fallback Lists

Each provider now has a prioritized list of models:

```python
GEMINI_MODELS = ["gemini-3-pro", "gemini-2.5-pro", "gemini-2.5-flash"]
OPENAI_MODELS = ["gpt-4o-mini", "gpt-4-turbo", "gpt-4o"]
ANTHROPIC_MODELS = ["claude-3-5-sonnet-20250219", "claude-3-5-sonnet-20241022"]
```

**Priority Order:**
- Most capable models first (better quality)
- Faster/cheaper models as fallback (better availability)
- Older versions as last resort (maximum compatibility)

### 2. Model-Specific Error Detection

The system now detects model-specific errors and immediately skips to the next model:

```python
is_model_error = (
    "404" in error_msg or 
    "not found" in error_msg.lower() or 
    "does not exist" in error_msg.lower() or
    "model_not_found" in error_msg.lower()
)
```

**Benefits:**
- No wasted retries on unavailable models
- Faster fallback to working models
- Better error handling

### 3. Retry Logic Per Model

- **2 retries per model** (exponential backoff: 2s, 4s)
- **Immediate skip** if model not found (404 errors)
- **Total attempts tracked** across all models

---

## Implementation Details

### Files Modified

#### 1. `utils/llm_service.py`

**Changes:**
- Added `GEMINI_MODELS`, `OPENAI_MODELS`, `ANTHROPIC_MODELS` constants
- Modified `_try_provider_with_retries()` to iterate through model lists
- Added `_get_model_fallback_list()` helper method
- Updated `_gemini_complete()`, `_openai_complete()`, `_anthropic_complete()` to accept `model_name` parameter
- Added model-specific error detection logic

**Key Code:**
```python
async def _try_provider_with_retries(
    self,
    provider: LLMProvider,
    system_prompt: str,
    user_prompt: str,
    temperature: float,
    max_tokens: int
) -> LLMResponse:
    """Try a single provider with exponential backoff retries and model fallback."""
    model_list = self._get_model_fallback_list(provider)
    total_attempts = 0
    
    for model_name in model_list:
        for attempt in range(1, self.MAX_RETRIES_PER_MODEL + 1):
            try:
                # ... LLM call with model_name ...
                if is_model_error:
                    break  # Skip remaining retries, try next model
            except Exception as e:
                # ... error handling ...
    
    return LLMResponse(...)  # Failed after all models
```

#### 2. `utils/configuration_manager.py`

**Changes:**
- Updated internal `model_map` defaults:
  - `gemini_model`: `"gemini-2.5-flash"` (primary)
  - `openai_model`: `"gpt-4o"` (primary)
  - `anthropic_model`: `"claude-3-5-sonnet-20250219"` (primary)

#### 3. `addon_portal/api/models/llm_config.py`

**Changes:**
- Updated `LLMSystemConfig` default values:
  - `gemini_model`: `"gemini-2.5-flash"`
  - `openai_model`: `"gpt-4o"`
  - `anthropic_model`: `"claude-3-5-sonnet-20250219"`

#### 4. `.env` File

**Changes:**
```bash
GEMINI_MODEL=gemini-3-pro              # Primary: most capable. Auto-fallback: gemini-2.5-pro -> gemini-2.5-flash
OPENAI_MODEL=gpt-4o-mini               # Primary: efficient. Auto-fallback: gpt-4-turbo -> gpt-4o
ANTHROPIC_MODEL=claude-3-5-sonnet-20250219  # Latest Claude 3.5 Sonnet version
```

**Note:** The `.env` file sets the PRIMARY model, but the system will automatically fall back to other models in the list if the primary fails.

---

## Fallback Sequence

### Complete Fallback Chain:

1. **Gemini Provider:**
   - `gemini-3-pro` (primary - most capable)
   - ↓ (if fails)
   - `gemini-2.5-pro` (fallback - capable)
   - ↓ (if fails)
   - `gemini-2.5-flash` (fallback - fast)

2. **OpenAI Provider:**
   - `gpt-4o-mini` (primary - efficient)
   - ↓ (if fails)
   - `gpt-4-turbo` (fallback - capable)
   - ↓ (if fails)
   - `gpt-4o` (fallback - most capable)

3. **Anthropic Provider:**
   - `claude-3-5-sonnet-20250219` (primary - latest)
   - ↓ (if fails)
   - `claude-3-5-sonnet-20241022` (fallback - previous version)

4. **Rules-Based Fallback:**
   - If all LLM providers fail, system falls back to rules-based task breakdown
   - Ensures project execution continues even without LLM availability

---

## Benefits

### 1. **Maximum Availability**
- System continues working even if primary model is unavailable
- Multiple fallback layers ensure high reliability

### 2. **Cost Optimization**
- Primary models are cost-effective (e.g., `gpt-4o-mini`, `gemini-2.5-flash`)
- More expensive models only used if needed

### 3. **Quality Preservation**
- Most capable models tried first
- Quality maintained while ensuring availability

### 4. **Error Resilience**
- Model-specific errors detected and handled gracefully
- No wasted retries on unavailable models

### 5. **Automatic Recovery**
- No manual intervention required
- System automatically finds working model

---

## Testing

### Test Scenarios:

1. **Primary Model Available**: Should use primary model (e.g., `gemini-3-pro`)
2. **Primary Model Unavailable (404)**: Should immediately skip to fallback (e.g., `gemini-2.5-pro`)
3. **All Models Unavailable**: Should fall back to rules-based breakdown
4. **Temporary Errors**: Should retry with exponential backoff before moving to next model
5. **Provider Failure**: Should fall back to next provider (Gemini → OpenAI → Anthropic)

### Expected Behavior:

- **Fast Fallback**: Model-specific errors (404) skip immediately
- **Retry Logic**: Network errors retry 2 times per model
- **Graceful Degradation**: Falls back to rules-based if all LLMs fail
- **Logging**: Clear logs showing which model/provider succeeded

---

## Logging

The system now logs:
- Which model is being tried
- Success/failure for each model
- Total attempts across all models
- Final model/provider used

**Example Log:**
```
[INFO] Trying Gemini (gemini-3-pro)...
[WARNING] Gemini model 'gemini-3-pro' not available: 404 Model not found
[INFO] Model gemini-3-pro failed, trying next model in Gemini fallback list...
[INFO] Trying Gemini (gemini-2.5-pro)...
[OK] Gemini (gemini-2.5-pro) succeeded on attempt 1 (2.34s, $0.0012)
```

---

## Migration Notes

### For Existing Projects:

- **No action required**: System automatically uses new fallback logic
- **Model names updated**: Old model names in database will be replaced with new defaults on next project run
- **Backward compatible**: Old model names still work if they exist

### For New Projects:

- **Automatic**: New projects use the new fallback system by default
- **Configuration**: Can override in project-level LLM config if needed

---

## Related Documentation

- **`docs/RECENT_IMPROVEMENTS_SUMMARY.md`** - Quick reference for all improvements
- **`docs/ASYNC_CONVERSION_IMPLEMENTATION.md`** - Async HTTP/file I/O improvements
- **`docs/TASK_CREATION_DATABASE_FIX.md`** - Database session management fixes

---

## Future Enhancements

### Potential Improvements:

1. **Dynamic Model Discovery**: Query available models from provider APIs
2. **Cost-Based Selection**: Choose models based on cost/quality tradeoff
3. **Performance Metrics**: Track which models work best for different task types
4. **User Configuration**: Allow users to customize fallback order per project

---

**Status**: ✅ **COMPLETE**  
**Last Updated**: November 26, 2025

