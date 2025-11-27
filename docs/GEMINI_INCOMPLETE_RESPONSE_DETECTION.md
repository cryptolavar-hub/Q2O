# Gemini Incomplete Response Detection

## Issue
Gemini sometimes returns incomplete responses when hitting the `MAX_TOKENS` limit. The response shows `"finishReason": "MAX_TOKENS"` which indicates the response was truncated mid-generation.

## Impact
- Incomplete JSON responses that cannot be parsed
- Poor quality responses that fail downstream processing
- Wasted API calls that don't produce usable results

## Solution
Implemented comprehensive detection for incomplete responses with automatic retry logic.

## Changes Made

### 1. Finish Reason Detection (`utils/llm_service.py`)
**File:** `utils/llm_service.py` - `_gemini_complete()` method

**Detection Logic:**
- Checks `response.candidates[0].finish_reason` (or `finishReason`)
- If `finish_reason == "MAX_TOKENS"` or `finish_reason == 2`, treats as failure
- Raises `ValueError` to trigger retry logic

**Code:**
```python
# CRITICAL: Check if response is incomplete (truncated due to MAX_TOKENS)
finish_reason = None
if response.candidates and len(response.candidates) > 0:
    candidate = response.candidates[0]
    finish_reason = getattr(candidate, 'finish_reason', None) or getattr(candidate, 'finishReason', None)
    
    if finish_reason == "MAX_TOKENS" or finish_reason == 2:  # 2 is MAX_TOKENS enum value
        error_msg = f"Gemini response truncated (finish_reason: {finish_reason}) - response incomplete, retrying with different model"
        logging.warning(f"[WARNING] {error_msg}")
        raise ValueError(error_msg)
```

### 2. JSON Completeness Validation (`utils/llm_service.py`)
**File:** `utils/llm_service.py` - `_gemini_complete()` method

**Detection Logic:**
- Checks if response looks like JSON (starts with `{` or `[`)
- Validates JSON structure is complete (ends with `}` or `]`)
- Attempts to parse JSON - if it fails, treats as incomplete
- Handles markdown code blocks (` ```json `)

**Code:**
```python
# Additional check: Validate response quality for JSON responses
response_text = response.text if hasattr(response, 'text') else str(response)
if response_text:
    text_stripped = response_text.strip()
    
    # Remove markdown code blocks if present
    if "```json" in text_stripped:
        text_stripped = text_stripped.split("```json")[1].split("```")[0].strip()
    elif "```" in text_stripped:
        text_stripped = text_stripped.split("```")[1].split("```")[0].strip()
    
    # If response looks like JSON, validate it's complete
    if text_stripped.startswith('{') or text_stripped.startswith('['):
        # Check if JSON appears incomplete
        is_incomplete = False
        if text_stripped.startswith('{') and not text_stripped.rstrip().endswith('}'):
            is_incomplete = True
        elif text_stripped.startswith('[') and not text_stripped.rstrip().endswith(']'):
            is_incomplete = True
        
        if is_incomplete:
            try:
                json.loads(text_stripped)
            except json.JSONDecodeError as json_error:
                # JSON is definitely incomplete - treat as failure
                error_msg = f"Gemini response contains incomplete JSON - response truncated: {str(json_error)[:100]}"
                logging.warning(f"[WARNING] {error_msg}")
                raise ValueError(error_msg)
```

### 3. Increased Max Tokens for Task Breakdown (`agents/orchestrator.py`)
**File:** `agents/orchestrator.py` - `_analyze_objective_with_llm()` method

**Change:**
- Increased `max_tokens` from `2048` to `4096` for task breakdown
- Prevents truncation for large task breakdowns

**Code:**
```python
# Generate breakdown with LLM
# Increased max_tokens to 4096 to prevent truncation (task breakdown can be large)
response = await self.llm_service.complete(
    system_prompt,
    user_prompt,
    temperature=0.4,  # Moderate creativity for task planning
    max_tokens=4096  # Increased from 2048 to prevent MAX_TOKENS truncation
)
```

## Retry Behavior

When an incomplete response is detected:
1. **Raises `ValueError`** - This triggers the retry logic in `_try_provider_with_retries()`
2. **Retries with same model** - Up to 3 retries (4 total attempts) per model
3. **Falls back to next model** - If all retries fail, tries next model in `GEMINI_MODELS` list
4. **Falls back to next provider** - If all Gemini models fail, tries OpenAI, then Anthropic

## Example Error Flow

**Before Fix:**
```
1. Gemini returns incomplete JSON (finishReason: MAX_TOKENS)
2. System tries to parse incomplete JSON
3. JSON parsing fails
4. Falls back to rules-based breakdown (poor quality)
```

**After Fix:**
```
1. Gemini returns incomplete JSON (finishReason: MAX_TOKENS)
2. System detects finishReason: MAX_TOKENS
3. Raises ValueError immediately
4. Retries with gemini-2.5-pro (next model)
5. If that fails, retries with gemini-3-pro
6. If all Gemini models fail, tries OpenAI (gpt-5-mini)
7. If OpenAI fails, tries Anthropic
8. Only falls back to rules-based if ALL providers fail
```

## Benefits

1. **Quality Assurance**: Incomplete responses are caught immediately
2. **Automatic Recovery**: System automatically tries better models/providers
3. **Better Results**: Higher chance of getting complete, usable responses
4. **Cost Efficiency**: Avoids wasting time processing incomplete responses

## Testing

To test this fix:
1. Create a project with a complex objective (will generate large task breakdown)
2. Monitor logs for `[WARNING] Gemini response truncated` messages
3. Verify system retries with different models/providers
4. Confirm final response is complete and parseable

## Date
2025-11-26

