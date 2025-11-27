# How to Change LLM Provider Order

**Question**: How do I change the order of LLM providers used by the agents?

---

## Current Provider Order

The default provider fallback chain is defined in `utils/llm_service.py`:

```python
PROVIDER_CHAIN = [
    LLMProvider.OPENAI,      # 1st - Primary (premium quality)
    LLMProvider.GEMINI,      # 2nd - Fallback (cost-effective)
    LLMProvider.ANTHROPIC    # 3rd - Tertiary (alternative)
]
```

**Current Flow**:
1. Try OpenAI (with all its models)
2. If OpenAI fails → Try Gemini (with all its models)
3. If Gemini fails → Try Anthropic (with all its models)

---

## Method 1: Modify Code Directly (Permanent Change)

**Location**: `utils/llm_service.py` lines 435-439

### Steps:

1. **Open the file**:
   ```powershell
   cd C:\Q2O_Combined
   notepad utils\llm_service.py
   ```

2. **Find the PROVIDER_CHAIN** (around line 435):
   ```python
   PROVIDER_CHAIN = [
       LLMProvider.GEMINI,
       LLMProvider.OPENAI,
       LLMProvider.ANTHROPIC
   ]
   ```

3. **Reorder the providers** as desired:

   **Example: Make OpenAI primary**:
   ```python
   PROVIDER_CHAIN = [
       LLMProvider.OPENAI,      # 1st - Primary
       LLMProvider.GEMINI,      # 2nd - Fallback
       LLMProvider.ANTHROPIC    # 3rd - Tertiary
   ]
   ```

   **Example: Make Anthropic primary**:
   ```python
   PROVIDER_CHAIN = [
       LLMProvider.ANTHROPIC,   # 1st - Primary
       LLMProvider.OPENAI,      # 2nd - Fallback
       LLMProvider.GEMINI       # 3rd - Tertiary
   ]
   ```

   **Example: Use only OpenAI and Gemini**:
   ```python
   PROVIDER_CHAIN = [
       LLMProvider.OPENAI,
       LLMProvider.GEMINI
       # Anthropic removed
   ]
   ```

4. **Save the file** - Changes take effect immediately (no restart needed for new processes)

---

## Method 2: Environment Variable (Primary Provider Only)

**Note**: This only changes which provider is tried FIRST, but doesn't change the fallback order.

**Environment Variable**: `Q2O_LLM_PRIMARY`

### Steps:

1. **Add to `.env` file** (in `C:\Q2O_Combined\.env`):
   ```bash
   # Set primary provider (gemini, openai, or anthropic)
   Q2O_LLM_PRIMARY=openai
   ```

2. **How it works**:
   - If `Q2O_LLM_PRIMARY=openai`, it will try OpenAI FIRST
   - But the fallback order is still: OpenAI → Gemini → Anthropic
   - This doesn't change the `PROVIDER_CHAIN` order

**Limitation**: This only affects the "primary" provider preference, not the full chain order.

---

## Method 3: Programmatic Override (For Custom Code)

If you're writing custom code that uses `LLMService`, you can override the provider chain:

### Example:

```python
from utils.llm_service import LLMService, LLMProvider

# Create service instance
llm_service = LLMService()

# Override the provider chain for this instance
llm_service.PROVIDER_CHAIN = [
    LLMProvider.OPENAI,      # Try OpenAI first
    LLMProvider.ANTHROPIC,   # Then Anthropic
    LLMProvider.GEMINI       # Finally Gemini
]

# Now use it
response = await llm_service.generate(
    system_prompt="...",
    user_prompt="...",
    temperature=0.7,
    max_tokens=2000
)
```

**Note**: This only affects that specific instance, not the global default.

---

## Method 4: Modify Provider Chain via Configuration Manager (Future Enhancement)

Currently, the `ConfigurationManager` doesn't support changing the provider chain order, only selecting a single provider. This could be enhanced in the future.

---

## Understanding Provider Chain Behavior

### How It Works:

1. **For each provider in chain** (in order):
   - Try all models for that provider (with retries)
   - If all models fail → Move to next provider

2. **Model fallback within each provider**:
   - **Gemini**: `gemini-2.5-flash` → `gemini-2.5-pro` → `gemini-3-pro`
   - **OpenAI**: `gpt-5-mini` → `gpt-5.1` → `gpt-4o-mini`
   - **Anthropic**: `claude-3-5-sonnet-20250219`

3. **Retries**: Each model gets 3 retries (4 total attempts) before moving to next model

### Example Flow (Current Default Order):

```
1. Try OpenAI:
   ├─ gpt-5-mini (4 attempts)
   ├─ gpt-5.1 (4 attempts)
   └─ gpt-4o-mini (4 attempts)
   ↓ If all fail
2. Try Gemini:
   ├─ gemini-2.5-flash (4 attempts)
   ├─ gemini-2.5-pro (4 attempts)
   └─ gemini-3-pro (4 attempts)
   ↓ If all fail
3. Try Anthropic:
   └─ claude-3-5-sonnet-20250219 (4 attempts)
   ↓ If all fail
4. Return error
```

---

## Recommended Changes

### Current Default (Quality-Focused):
```python
PROVIDER_CHAIN = [
    LLMProvider.OPENAI,      # Best quality (current primary)
    LLMProvider.GEMINI,      # Cost-effective fallback
    LLMProvider.ANTHROPIC    # Alternative
]
```

### For Cost Optimization (Recommended for High Volume):
```python
PROVIDER_CHAIN = [
    LLMProvider.GEMINI,      # Cheapest ($0.52/100K tokens) - 87% cheaper!
    LLMProvider.OPENAI,      # Premium ($4.00/100K tokens)
    LLMProvider.ANTHROPIC    # Alternative (~$3.00/100K tokens)
]
```

### For Maximum Quality:
```python
PROVIDER_CHAIN = [
    LLMProvider.OPENAI,      # Best quality
    LLMProvider.ANTHROPIC,   # High quality alternative
    LLMProvider.GEMINI       # Cost-effective fallback
]
```

### For Speed Optimization:
```python
PROVIDER_CHAIN = [
    LLMProvider.GEMINI,      # Fastest (gemini-2.5-flash)
    LLMProvider.OPENAI,      # Fast (gpt-5-mini)
    LLMProvider.ANTHROPIC    # Slower but reliable
]
```

---

## Verification

After changing the provider order, verify it's working:

1. **Check logs** when agents run:
   ```bash
   # Look for log messages like:
   # "Trying gemini (up to 3 attempts)"
   # "Trying openai (up to 3 attempts)"
   ```

2. **Monitor which provider succeeds**:
   - Check `LLMResponse.provider` field
   - Check cost tracking logs
   - Check `.llm_cost_state.json` file

---

## Important Notes

1. **API Keys Required**: Make sure you have API keys configured for the providers you want to use
   - `GOOGLE_API_KEY` for Gemini
   - `OPENAI_API_KEY` for OpenAI
   - `ANTHROPIC_API_KEY` for Anthropic

2. **Provider Availability**: The system automatically skips providers that aren't configured (no API key)

3. **Cost Impact**: Changing order affects which provider is used most, which impacts costs

4. **Restart Not Required**: Code changes take effect for new processes (existing processes keep old order)

---

## Summary

**To change provider order**:
- ✅ **Method 1**: Edit `utils/llm_service.py` line 435-439 (recommended for permanent change)
- ⚠️ **Method 2**: Set `Q2O_LLM_PRIMARY` env var (only changes primary, not full order)
- ✅ **Method 3**: Override `PROVIDER_CHAIN` in your code (for custom implementations)

**Current Default Order**: OpenAI → Gemini → Anthropic  
**Note**: Currently OpenAI is primary (quality-focused). For cost optimization, consider switching to Gemini first (87% cheaper than GPT-4).

---

**File Location**: `utils/llm_service.py` lines 435-439  
**Related Files**: 
- `utils/configuration_manager.py` (for per-project/provider config)
- `.env` (for API keys and primary provider setting)

