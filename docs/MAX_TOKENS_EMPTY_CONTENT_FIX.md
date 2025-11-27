# MAX_TOKENS with Empty Content - Additional Fix
**Date**: November 26, 2025  
**Role**: QA_Engineer / Bug Fix  
**Status**: ✅ Fixed

---

## 🐛 Additional Issue Found

**User Report**: Example of failed LLM response from Gemini where:
- `finishReason: "MAX_TOKENS"` 
- But `content` is completely empty (no `parts` array, no text)

**Example Response**:
```json
{
  "candidates": [
    {
      "content": {
        "role": "model"
      },
      "finishReason": "MAX_TOKENS"
    }
  ],
  "usageMetadata": {
    "promptTokenCount": 1153,
    "totalTokenCount": 3200,
    "thoughtsTokenCount": 2047
  }
}
```

**Problem**: The response has `MAX_TOKENS` finish reason but contains **no actual text content** - the `content` object only has `role: "model"` but no `parts` array with text.

---

## ✅ Fix Implementation

### Improved Content Detection

**Before**: Relied on `response.text` which might not handle empty content correctly.

**After**: More robust detection that:
1. **First checks** `candidate.content.parts` directly (most reliable)
2. **Then tries** `response.text` property (with error handling)
3. **Finally** sets empty string if no text found
4. **Explicitly checks** `candidate_has_text` flag before length check

### Code Changes

**File**: `utils/llm_service.py` lines 942-968

**Improved Logic**:
```python
# Get response text first to check content quality
response_text = None
candidate_has_text = False

if response.candidates and len(response.candidates) > 0:
    candidate = response.candidates[0]
    
    # Check candidate.content.parts directly - most reliable way
    if hasattr(candidate, 'content') and candidate.content:
        if hasattr(candidate.content, 'parts') and candidate.content.parts:
            # Check if any part has actual text content
            for part in candidate.content.parts:
                if hasattr(part, 'text') and part.text and len(part.text.strip()) > 0:
                    candidate_has_text = True
                    response_text = part.text
                    break
    
    # Fallback: Try response.text property
    if not response_text:
        if hasattr(response, 'text'):
            try:
                response_text = response.text
                if response_text and len(response_text.strip()) > 0:
                    candidate_has_text = True
            except (AttributeError, ValueError):
                # response.text raises error if content.parts is empty
                response_text = None
                candidate_has_text = False

# Final fallback
if not response_text:
    response_text = ""
```

### Failure Detection

**File**: `utils/llm_service.py` lines 979-986

**Logic**:
```python
if finish_reason == "MAX_TOKENS" or finish_reason == 2:
    # First check if candidate has any text parts at all
    if not candidate_has_text or not response_text:
        # No text content at all - definitely a failure
        error_msg = f"Gemini response has MAX_TOKENS finish reason but contains no text content - response empty, retrying with different model"
        logging.warning(f"[WARNING] {error_msg}")
        raise ValueError(error_msg)
    
    # Then check response length (for cases with some content but not enough)
    response_length = len(response_text.strip()) if response_text else 0
    if response_length < MIN_SIGNIFICANT_LENGTH:
        # Insufficient content - treat as failure
        ...
```

---

## 🎯 Detection Flow for Empty Content Case

### User's Example:
```
1. Response has candidates[0].content = {"role": "model"} (no parts array)
2. Check candidate.content.parts → None or empty
3. candidate_has_text = False (no parts with text found)
4. Try response.text → May raise error or return empty
5. response_text = "" (empty string)
6. Check: if not candidate_has_text or not response_text:
   → if True or True → True
7. ✅ Correctly detected as failure
8. Raises ValueError to trigger retry
```

---

## 📊 Test Cases

### Test Case 1: Empty Content with MAX_TOKENS (User's Example)
**Input**: 
- `finishReason: "MAX_TOKENS"`
- `content: {"role": "model"}` (no parts)
- No text content

**Expected**: ❌ Treated as failure, retry triggered

**Actual**: ✅ Correctly detected as failure

### Test Case 2: MAX_TOKENS with Substantial Content
**Input**: 
- `finishReason: "MAX_TOKENS"`
- `content.parts[0].text = "This is a long response..."` (200+ chars)

**Expected**: ✅ Treated as success

**Actual**: ✅ Correctly treated as success

### Test Case 3: MAX_TOKENS with Short Content
**Input**: 
- `finishReason: "MAX_TOKENS"`
- `content.parts[0].text = "Hi"` (< 50 chars)

**Expected**: ❌ Treated as failure (insufficient content)

**Actual**: ✅ Correctly treated as failure

---

## 🔧 Additional Fix

**File**: `utils/llm_service.py` line 1071

**Before**:
```python
return LLMResponse(
    content=response.text,  # Might raise error if empty
    ...
)
```

**After**:
```python
# Use extracted response_text instead of response.text
final_content = response_text if response_text else ""

return LLMResponse(
    content=final_content,  # Safe - uses extracted text
    ...
)
```

**Reason**: Prevents potential errors when returning empty responses.

---

## ✅ Verification

**Status**: ✅ Fixed  
**Linter Errors**: 0  
**Handles Empty Content**: ✅ Yes  
**Handles Substantial Content**: ✅ Yes  
**Backward Compatible**: ✅ Yes

---

## 📝 Summary

**Issue**: Empty content responses with `MAX_TOKENS` weren't being detected correctly.

**Fix**: 
1. Improved content extraction to check `candidate.content.parts` directly
2. Added explicit `candidate_has_text` flag
3. Check for empty content BEFORE checking length
4. Use extracted `response_text` instead of `response.text` in return statement

**Result**: Empty content responses are now correctly detected as failures and trigger retries.

---

**Role**: QA_Engineer  
**Date**: November 26, 2025  
**Related**: `docs/MAX_TOKENS_FIX.md`

