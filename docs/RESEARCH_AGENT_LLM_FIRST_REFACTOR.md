# Research Agent LLM-First Refactoring

**Date:** November 26, 2025  
**Status:** ✅ COMPLETED  
**Priority:** HIGH

## Problem Statement

The Research Agent was using a "Search First, LLM Second" approach, which was inefficient and not aligned with the user's requirements. The user specified that:
1. **LLM should be tried FIRST** with full provider/model fallback
2. **Search should only be used as a LAST RESORT** if all LLM attempts fail
3. LLM should try **3 providers** with **multiple models per provider** and **3 retries per model** to ensure maximum success rate

## Previous Behavior

**Old Flow:**
1. Phase 1: Quick web search (top results)
2. Phase 2: Deep web search (if needed)
3. Phase 3: Extract documentation
4. Phase 4: Recursive research (scrape content)
5. Phase 5: Synthesize findings (may use LLM)
6. Phase 6: Quality validation

**Issues:**
- Web search was always executed first
- LLM was only used for synthesis, not primary research
- Inefficient use of resources
- Slower research completion

## New Behavior

**New Flow:**
1. **Phase 1: LLM Research (PRIMARY)**
   - Tries all 3 providers: Gemini → OpenAI → Anthropic
   - Multiple models per provider with fallback
   - 3 retries per model (4 total attempts per model)
   - Comprehensive research in a single call
   - High confidence results (95% confidence score)
   - **If successful: Return LLM results immediately**

2. **Phase 2: Web Search (FALLBACK - Last Resort)**
   - Only executed if ALL LLM attempts fail
   - Multi-provider search (Google, Bing, DuckDuckGo)
   - Recursive content scraping
   - Documentation extraction
   - Code example discovery

## Implementation Details

### 1. Refactored `_conduct_research()` Method

**File:** `agents/researcher_agent.py`

**Changes:**
- Reordered research phases to try LLM first
- Added early return if LLM research succeeds
- Moved all web search logic to fallback section
- Added clear logging to indicate LLM-first approach

**Key Code:**
```python
def _conduct_research(self, query: str, task: Task) -> Dict[str, Any]:
    # PHASE 1: Try LLM FIRST with full fallback
    self.logger.info(f"Phase 1: Attempting LLM research (will try all 3 providers with multiple models and retries)...")
    llm_results = self._conduct_research_with_llm(query, task, depth)
    
    if llm_results:
        # LLM research succeeded - use it as primary source
        self.logger.info(f"[SUCCESS] LLM research completed successfully - using LLM results as primary source")
        research_results.update(llm_results)
        research_results['sources_consulted'].insert(0, 'llm_research_primary')
        # ... synthesize and return
    
    # PHASE 2: LLM failed - Fall back to web search as last resort
    self.logger.warning(f"[FALLBACK] All LLM attempts failed - falling back to web search as last resort")
    # ... web search logic
```

### 2. Enhanced LLM Service Retry Configuration

**File:** `utils/llm_service.py`

**Changes:**
- Updated `MAX_RETRIES_PER_MODEL` from 2 to 3 (3 retries = 4 total attempts per model)
- Updated retry loop to `range(1, MAX_RETRIES_PER_MODEL + 2)` for 4 total attempts
- Updated logging to reflect correct attempt counts

**Configuration:**
```python
MAX_RETRIES_PER_MODEL = 3  # Retries per model (3 retries = 4 total attempts: initial + 3 retries)
```

**Retry Logic:**
```python
# Try this model with retries (3 retries = 4 total attempts: initial + 3 retries)
for attempt in range(1, self.MAX_RETRIES_PER_MODEL + 2):
    # ... attempt LLM call
    # ... handle errors with exponential backoff
```

### 3. Updated Documentation

**File:** `agents/researcher_agent.py`

**Changes:**
- Updated module docstring to reflect LLM-first approach
- Added detailed explanation of research priority
- Documented fallback strategy

**New Docstring:**
```python
"""
Researcher Agent - Conducts research for project objectives and tasks.
Uses LLM FIRST, then web search as fallback.

Research Priority (November 2025):
1. LLM Research (PRIMARY):
   - Tries all 3 providers (Gemini, OpenAI, Anthropic)
   - Multiple models per provider (e.g., gemini-3-pro -> gemini-2.5-pro -> gemini-2.5-flash)
   - 3 retries per model (3 total attempts per model)
   - Comprehensive research in a single call
   - High confidence results (95% confidence score)
   
2. Web Search (FALLBACK - Last Resort):
   - Only executed if ALL LLM attempts fail
   - Multi-provider search (Google, Bing, DuckDuckGo)
   - Recursive content scraping
   - Documentation extraction
   - Code example discovery
"""
```

## LLM Fallback Strategy

### Provider Chain
1. **Gemini** (Primary - Cheapest)
   - Models: `gemini-3-pro` → `gemini-2.5-pro` → `gemini-2.5-flash`
   - 3 retries per model = 4 attempts per model
   - Total: Up to 12 attempts for Gemini

2. **OpenAI** (Secondary - Premium)
   - Models: `gpt-4o-mini` → `gpt-4-turbo` → `gpt-4o`
   - 3 retries per model = 4 attempts per model
   - Total: Up to 12 attempts for OpenAI

3. **Anthropic** (Tertiary - Alternative)
   - Models: `claude-3-5-sonnet-20250219`
   - 3 retries per model = 4 attempts per model
   - Total: Up to 4 attempts for Anthropic

**Maximum Total Attempts:** Up to 28 LLM attempts before falling back to web search

### Retry Logic
- **Exponential Backoff:** 2^attempt seconds between retries
- **Model-Specific Errors:** If model returns 404 or "not found", immediately skip to next model
- **Provider Unavailable:** If provider not configured, skip to next provider

## Benefits

### Performance
- ✅ **Faster research:** LLM provides comprehensive results in a single call
- ✅ **Reduced API calls:** Web search only used when necessary
- ✅ **Higher success rate:** 28 total LLM attempts before fallback

### Quality
- ✅ **Higher confidence:** LLM results have 95% confidence score
- ✅ **More comprehensive:** LLM provides structured research with documentation URLs, code examples, best practices
- ✅ **Better context:** LLM understands project objectives and tech stack

### Cost Efficiency
- ✅ **LLM-first is cheaper:** Single LLM call vs. multiple web searches
- ✅ **Fallback only when needed:** Web search only if LLM completely fails
- ✅ **Caching:** LLM responses are cached for 90 days

## Testing

### Test Case 1: LLM Success
```python
# Should use LLM results, skip web search
research_results = agent._conduct_research("Python async best practices", task)
assert research_results['sources_consulted'] == ['llm_research_primary']
assert research_results['confidence_score'] == 95
```

### Test Case 2: LLM Failure, Web Search Fallback
```python
# Mock LLM to fail, should fall back to web search
with patch('agent.llm_service') as mock_llm:
    mock_llm.complete.return_value = LLMResponse(success=False, error="All providers failed")
    research_results = agent._conduct_research("Python async best practices", task)
    assert 'web_search_fallback' in research_results['sources_consulted']
    assert research_results['confidence_score'] < 95
```

### Test Case 3: Retry Logic
```python
# Verify 3 retries per model (4 total attempts)
# Check logs for: "attempt 1/4", "attempt 2/4", "attempt 3/4", "attempt 4/4"
```

## Files Modified

1. `agents/researcher_agent.py`
   - Refactored `_conduct_research()` method
   - Updated module docstring
   - Added LLM-first logic with fallback

2. `utils/llm_service.py`
   - Updated `MAX_RETRIES_PER_MODEL` from 2 to 3
   - Updated retry loop range
   - Updated logging messages

## Related Documentation

- `docs/LLM_MULTI_MODEL_FALLBACK_IMPLEMENTATION.md` - LLM fallback strategy details
- `docs/ASYNC_CONVERSION_IMPLEMENTATION.md` - Async research methods

## Notes

- The LLM service automatically handles all provider/model fallback logic
- Web search is now truly a "last resort" - only used if all 28 LLM attempts fail
- Research results include `sources_consulted` field to track whether LLM or web search was used
- LLM research results have higher confidence scores (95%) compared to web search results

