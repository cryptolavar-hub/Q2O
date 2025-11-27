# OpenAI Model Update

## Change
Updated OpenAI model priority to use GPT-5 models as requested by user.

## Model Priority (Updated)
**File:** `utils/llm_service.py`

**Before:**
```python
OPENAI_MODELS = [
    "gpt-4o-mini",       # Latest efficient model
    "gpt-4-turbo",       # High capability
    "gpt-4o"             # Latest full model
]
```

**After:**
```python
OPENAI_MODELS = [
    "gpt-5-mini",        # Primary model (user requested)
    "gpt-5.1",           # Fallback (user requested)
    "gpt-4o-mini"        # Fallback (if gpt-5 models not available)
]
```

## Default Model
Updated default model from `gpt-4o` to `gpt-5-mini` in all references:
- `_init_openai()` - Initialization default
- `get_model_name()` - Model name getter
- `_openai_complete()` - Completion method
- Stats tracking - Default model reference

## Fallback Behavior
If `gpt-5-mini` is not available (404 error), the system will:
1. Try `gpt-5.1` (with 3 retries = 4 attempts)
2. If that fails, try `gpt-4o-mini` (with 3 retries = 4 attempts)
3. If all OpenAI models fail, move to next provider (Anthropic)

## Context
- OpenAI billing issue has been resolved
- User requested GPT-5 models as primary
- System will automatically detect if models are unavailable and fall back

## Date
2025-11-26

