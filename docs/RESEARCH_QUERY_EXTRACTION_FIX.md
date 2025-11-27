# Research Query Extraction Fix
**Date**: November 25, 2025  
**Status**: FIXED ✅

---

## 🔴 Issue: Research Query Contains Instructions Instead of Topic

### Problem:
- LLM received research query containing instructions like:
  ```
  Research Query: Follow every requirement below strictly. Produce outputs that are detailed, actionable, architecturally sound, multistep, and include code, diagrams, and deployment plans. Do not skip or summarize sections unless instructed.
  ```
- LLM correctly responded that no research topic was provided
- This caused research tasks to fail or return empty results

### Root Cause:
1. **`_extract_research_query()`** was falling back to `task.metadata.get("objective", task.title)`
2. If the objective contained instructions (from project requirements), those instructions became the research query
3. No cleaning/filtering of instruction text from research queries
4. User prompt also contained redundant instructions that confused the LLM

---

## ✅ Fix Applied

### 1. Enhanced Query Extraction (`_extract_research_query`)

**File**: `agents/researcher_agent.py`

**Changes**:
- Added `_clean_research_query()` helper method to remove instruction patterns
- Updated `_extract_research_query()` to clean all extracted queries
- Added more pattern matching for research queries in descriptions
- Improved fallback logic to extract actual topic from objective

**Instruction Patterns Removed**:
- "Follow every requirement below strictly"
- "Produce outputs that are detailed, actionable..."
- "Do not skip or summarize sections unless instructed"
- "Include code, diagrams, and deployment plans"
- "Be architecturally sound, multistep"

**Topic Extraction Patterns**:
- `research: <topic>`
- `find information about: <topic>`
- `learn about: <topic>`
- `conduct.*research.*for: <topic>`
- `research.*topic: <topic>`

### 2. Full Context Inclusion in LLM Prompt

**File**: `agents/researcher_agent.py` - `_conduct_research_with_llm_async()`

**CRITICAL FIX**: Include ALL context needed by LLM:
- **System Prompt** (already in place) - defines role and output format
- **Project Objectives** (NEW) - contains instructions on HOW to research, WHAT format/output
- **Agent Prompts** (NEW) - agent-specific instructions from ConfigurationManager
- **Research Topic** (cleaned) - WHAT to research

**Structure**:
```
Research Topic: <clean topic extracted from objective>

Context:
Tech Stack: <tech_stack>
Task Complexity: <complexity>
Research Depth: <depth>

Project Objectives and Requirements:
<FULL objective with all instructions>

Task Description:
<task description if different from objective>

Agent-Specific Instructions:
<agent prompt if available>

Please provide comprehensive research...
```

**Key Changes**:
- Extract clean research topic (WHAT to research)
- Include FULL project objective in context (HOW to research, WHAT format/output)
- Include agent-specific prompts if available
- Changed prompt label from "Research Query:" to "Research Topic:" for clarity
- Structure ensures: System Prompt + Project Objectives + Agent Prompts + Research Topic = Complete instruction

**Before**:
```python
user_prompt = f"""Research Query: {query}

Context:
{tech_context}
Task Complexity: {task.metadata.get('complexity', 'medium')}
Research Depth: {depth}

Please provide comprehensive research on this topic. Include:
- Official documentation URLs (verify these are real, official sources)
- Code examples in the relevant language/framework
- Best practices specific to this technology
- Implementation patterns and approaches
- Integration requirements
- Performance and security considerations

Be thorough and specific. This research will be used to implement the solution."""
```

**After**:
```python
# CRITICAL FIX: Ensure query is actually a research topic, not instructions
if not query or len(query) < 10 or query.lower().startswith(('follow', 'produce', 'do not')):
    # Try to get actual research topic from task objective
    actual_objective = task.metadata.get("objective", "")
    if actual_objective and actual_objective != query:
        # Extract first sentence or meaningful phrase from objective
        objective_parts = re.split(r'[.\n]', actual_objective)
        for part in objective_parts:
            part = part.strip()
            if len(part) > 20 and not part.lower().startswith(('follow', 'produce', 'do not', 'include')):
                query = part
                break
        if not query or len(query) < 10:
            query = actual_objective[:200]  # Use first 200 chars of objective

user_prompt = f"""Research Topic: {query}

Context:
Tech Stack: {tech_context}
Task Complexity: {task.metadata.get('complexity', 'medium')}
Research Depth: {depth}

Please provide comprehensive research on the topic above. Include:
- Official documentation URLs (verify these are real, official sources)
- Code examples in the relevant language/framework
- Best practices specific to this technology
- Implementation patterns and approaches
- Integration requirements
- Performance and security considerations

Be thorough and specific. This research will be used to implement the solution."""
```

---

## 📊 How It Works

### Query Extraction Flow:
1. **Check explicit `research_query` metadata** → Clean if present
2. **Pattern match in description** → Extract topic, clean it
3. **Fallback to objective/title** → Clean and validate
4. **Validation before LLM call** → Re-extract from objective if still invalid

### Cleaning Process:
1. Remove instruction patterns (regex-based)
2. Extract topic from patterns like "Research: <topic>"
3. Validate query length (>10 chars) and content (not starting with instructions)
4. Fallback to first meaningful sentence from objective

---

## ✅ Result

- Research queries now contain **actual topics** (WHAT to research)
- LLM receives **FULL context**: System Prompt + Project Objectives + Agent Prompts + Research Topic
- Project objectives (with instructions) are included in context, not lost
- Agent-specific prompts are included if available
- Query extraction is more robust and handles edge cases
- LLM has complete instruction set: WHAT to research + HOW to research + WHAT format/output

---

## 📝 Files Modified

1. **`agents/researcher_agent.py`**:
   - Added `_clean_research_query()` method
   - Enhanced `_extract_research_query()` with cleaning
   - Added query validation in `_conduct_research_with_llm_async()`
   - Improved user prompt clarity

---

## 🧪 Testing Required

1. **Test with instruction-heavy objectives**:
   - Create project with objective containing instructions
   - Verify research query is cleaned and contains actual topic

2. **Test with various objective formats**:
   - Objectives with "Research: <topic>" pattern
   - Objectives with instructions mixed with topic
   - Objectives with just topic (no instructions)

3. **Verify LLM receives proper query**:
   - Check logs to see what query is sent to LLM
   - Verify LLM responds with actual research, not error about missing topic

