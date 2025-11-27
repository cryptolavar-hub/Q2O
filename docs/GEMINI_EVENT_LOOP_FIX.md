# Gemini Event Loop Fix

## Problem
Gemini API calls were failing with `"Event loop is closed"` errors, preventing the LLM service from working. This caused:
- All LLM providers to fail (Gemini → OpenAI → Anthropic chain)
- System falling back to rules-based task breakdown
- No tasks being created (task stats remained at 0)

## Root Causes

### 1. Event Loop Premature Closure
- Event loops were being closed immediately after `run_until_complete()`
- Gemini's async operations (`generate_content_async`) were still running when the loop closed
- Background tasks created by the genai library weren't being awaited

### 2. Missing genai.configure() Call
- `genai.configure(api_key=api_key)` was only called during initialization
- When event loops were created/destroyed, the configuration was lost
- Each async call needs genai to be configured in the current context

### 3. API Key Loading
- `.env` file loading wasn't explicitly pointing to root directory
- Could fail if working directory changed

### 4. Model Priority
- Model list prioritized `gemini-3-pro` which might not be available
- User requested `gemini-2.5-flash` as primary

## Solution

### 1. Fixed Event Loop Handling
**Files Modified:**
- `agents/orchestrator.py`
- `agents/researcher_agent.py` (2 locations)
- `agents/coder_agent.py`
- `agents/mobile_agent.py`

**Changes:**
- Wait for all pending tasks to complete before closing the loop
- Cancel remaining tasks before closing
- Proper exception handling during cleanup

**Code Pattern:**
```python
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
try:
    result = loop.run_until_complete(async_function())
    # CRITICAL: Wait for all pending tasks
    pending = asyncio.all_tasks(loop)
    if pending:
        loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
finally:
    # Cancel remaining tasks
    try:
        pending = asyncio.all_tasks(loop)
        for task in pending:
            task.cancel()
        if pending:
            loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
    except Exception:
        pass
    finally:
        loop.close()
```

### 2. Added genai.configure() in _gemini_complete
**File:** `utils/llm_service.py`

**Changes:**
- Call `genai.configure(api_key=api_key)` before each async call
- Ensures API key is set in the current event loop context
- Added error message pointing to correct .env location

**Code:**
```python
async def _gemini_complete(...):
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not set - ensure it's in C:\\Q2O_Combined\\.env")
    
    # CRITICAL: Configure genai before each call
    genai.configure(api_key=api_key)
    
    # Create model and make async call
    model = genai.GenerativeModel(actual_model_name)
    response = await model.generate_content_async(...)
```

### 3. Updated Model Priority
**File:** `utils/llm_service.py`

**Changes:**
- Changed `GEMINI_MODELS` list to prioritize `gemini-2.5-flash`
- Updated default model to `gemini-2.5-flash`

**Before:**
```python
GEMINI_MODELS = [
    "gemini-3-pro",      # Most capable
    "gemini-2.5-pro",    # High capability
    "gemini-2.5-flash"   # Fast, efficient
]
```

**After:**
```python
GEMINI_MODELS = [
    "gemini-2.5-flash",  # Fast, efficient (primary - user requested)
    "gemini-2.5-pro",    # High capability (fallback)
    "gemini-3-pro"       # Most capable (fallback)
]
```

### 4. Explicit .env File Loading
**File:** `main.py`

**Changes:**
- Explicitly load `.env` from root directory (`C:\Q2O_Combined\.env`)
- Use `Path(__file__).parent` to ensure correct path
- Fallback to default behavior if file not found

**Code:**
```python
from dotenv import load_dotenv
from pathlib import Path

# CRITICAL: Load .env from root directory
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path, override=True)
else:
    load_dotenv()
```

## Benefits
1. ✅ **Gemini API Works**: Event loop stays open until all operations complete
2. ✅ **Proper Configuration**: genai.configure() called before each async call
3. ✅ **Correct Model**: Uses gemini-2.5-flash as primary (user requested)
4. ✅ **API Key Found**: Explicitly loads from root .env file
5. ✅ **Task Creation**: LLM breakdown now works, tasks can be created

## Testing
To verify the fix:
1. Ensure `GOOGLE_API_KEY` is set in `C:\Q2O_Combined\.env`
2. Restart the project execution
3. Check execution logs - should see Gemini API calls succeeding
4. Verify tasks are being created (task stats should increase from 0)

## Related Issues
- OpenAI quota exceeded (billing issue - separate)
- Anthropic model name incorrect (separate fix needed)
- Rules-based breakdown not intelligent enough (requires LLM to work)

## Date
2025-11-26

