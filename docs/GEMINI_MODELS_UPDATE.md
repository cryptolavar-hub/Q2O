# Gemini Models Update

**Date:** November 23, 2025  
**Status:** Updated to use actual available models from Google AI Studio

## Summary

Updated the LLM service to use the correct Gemini model names that are actually available in Google AI Studio, replacing outdated model names.

---

## Available Gemini Models (as of November 2025)

Based on Google AI Studio Usage and Billing page:

### Text-Out Models
- `gemini-2.0-flash` - Rate limits: 2K/4M
- `gemini-2.5-flash-lite` - Rate limits: 4K/4M
- `gemini-2.5-flash` - Rate limits: 1K/1M (Recommended default)
- `gemini-2.5-pro-exp` - Rate limits: 150/2M
- `gemini-2.5-pro` - Rate limits: 150/2M
- `gemini-3-pro` - Rate limits: 50/1M

### Multi-Modal Generative Models
- `gemini-2.5-flash-preview-image` - Rate limits: 500/500K
- `gemini-2.5-flash-tts` - Rate limits: 10/10K
- `gemini-2.5-pro-tts` - Rate limits: 10/10K
- `gemini-3-pro-image` - Rate limits: 20/100K

### Other Models
- `gemini-robotics-er-1.5-preview` - Rate limits: 1K/2M
- `gemma-3-12b` - Rate limits: 30/15K

---

## Changes Made

### 1. Updated `_init_gemini()` in `utils/llm_service.py`

**Before:**
```python
valid_models = [
    user_model,
    "gemini-1.5-pro-latest",
    "gemini-1.5-flash-latest",
    "gemini-pro",
    "gemini-1.5-pro"
]
```

**After:**
```python
valid_models = [
    user_model,  # Try user-specified first
    "gemini-2.5-flash",      # Fast, efficient (recommended default)
    "gemini-2.0-flash",      # Alternative flash model
    "gemini-2.5-pro",        # More capable, higher rate limits
    "gemini-3-pro",           # Latest pro model
    "gemini-2.5-flash-lite",  # Lightweight option
    "gemini-2.5-pro-exp",     # Experimental pro
    # Legacy models (may still work)
    "gemini-1.5-pro-latest",
    "gemini-1.5-flash-latest",
    "gemini-pro",
    "gemini-1.5-pro"
]
```

### 2. Updated `_try_gemini_models()` Runtime Fallback

**Before:**
```python
model_names.extend([
    "gemini-pro",
    "gemini-1.5-pro",
    "gemini-1.5-flash",
])
```

**After:**
```python
model_names.extend([
    "gemini-2.5-flash",      # Fast, efficient (recommended)
    "gemini-2.0-flash",      # Alternative flash model
    "gemini-2.5-pro",        # More capable
    "gemini-3-pro",           # Latest pro model
    "gemini-2.5-flash-lite",  # Lightweight option
    # Legacy models (fallback)
    "gemini-pro",
    "gemini-1.5-pro",
    "gemini-1.5-flash",
])
```

### 3. Updated Default Model

**Before:**
- Default: `gemini-1.5-pro-latest`
- `env.example.txt`: `GEMINI_MODEL=gemini-1.5-pro`

**After:**
- Default: `gemini-2.5-flash` (fast, efficient, good rate limits)
- `env.example.txt`: `GEMINI_MODEL=gemini-2.5-flash`

---

## Recommended Model Selection

### For General Use (Default)
**`gemini-2.5-flash`**
- Fast response times
- Good rate limits (1K requests/1M tokens per minute)
- Cost-effective
- Suitable for most research and code generation tasks

### For Complex Tasks
**`gemini-2.5-pro`** or **`gemini-3-pro`**
- More capable for complex reasoning
- Higher rate limits (150 requests/2M tokens per minute)
- Better for orchestrator task breakdown and complex research

### For High-Volume Operations
**`gemini-2.5-flash-lite`**
- Highest rate limits (4K requests/4M tokens per minute)
- Lightweight, fast
- Good for high-frequency operations

---

## Migration Notes

1. **Existing `.env` files**: Users should update `GEMINI_MODEL` to one of the new model names
2. **Automatic Fallback**: The service will automatically try new models if the specified one fails
3. **Legacy Support**: Old model names are still in the fallback list in case they still work
4. **No Breaking Changes**: The service will gracefully fall back through all available models

---

## Testing

After this update, the Research Agent test should work correctly with Gemini:

```bash
python test_research_agent_llm.py
```

Expected behavior:
- Should successfully initialize with `gemini-2.5-flash` (or first available model)
- Should complete LLM research calls without "model not found" errors
- Should log which model was successfully used

---

## Files Modified

1. `utils/llm_service.py` - Updated model lists in `_init_gemini()` and `_try_gemini_models()`
2. `addon_portal/env.example.txt` - Updated default `GEMINI_MODEL` value

---

**Last Updated:** November 23, 2025

