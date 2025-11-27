# Research Agent: Complete LLM Instruction Context
**Date**: November 25, 2025  
**Status**: IMPLEMENTED ✅

---

## 🎯 Goal: Complete LLM Instruction Context

### AIM:
**System Prompt + Project Objectives + Agent Prompts + Research Topic = Total LLM Instruction**

### Previously:
**System Prompt + Extracted Topic = Incomplete LLM Instruction** ❌

---

## ✅ Solution: Structured Context Inclusion

### 1. Extract Clean Research Topic
- **Purpose**: Identify WHAT to research
- **Method**: Clean instructions from topic, extract actual research subject
- **Result**: Clear, focused research topic (e.g., "Stripe API integration")

### 2. Include Full Project Objectives
- **Purpose**: Provide instructions on HOW to research, WHAT format/output
- **Source**: `task.metadata.get("objective")`
- **Contains**: 
  - Requirements and constraints
  - Output format specifications
  - Quality standards
  - Implementation guidelines

### 3. Include Agent-Specific Prompts
- **Purpose**: Agent-level customization and instructions
- **Source**: `ConfigurationManager.get_prompt_for_task()`
- **Contains**:
  - Agent-specific research focus
  - Custom instructions per agent type
  - Project-level overrides

### 4. Include Task Description
- **Purpose**: Additional context if different from objective
- **Source**: `task.description`
- **Contains**: Task-specific details and requirements

---

## 📋 Prompt Structure

```
System Prompt (Defines Role & Output Format):
└─ You are an expert software researcher...
   └─ Return your research as JSON: {...}

User Prompt (Complete Context):
├─ Research Topic: <clean topic>
├─ Context:
│  ├─ Tech Stack: <tech_stack>
│  ├─ Task Complexity: <complexity>
│  └─ Research Depth: <depth>
├─ Project Objectives and Requirements:
│  └─ <FULL objective with all instructions>
├─ Task Description:
│  └─ <task description if different>
├─ Agent-Specific Instructions:
│  └─ <agent prompt if available>
└─ Please provide comprehensive research...
```

---

## 🔍 Example

### Input:
- **Objective**: "Follow every requirement below strictly. Produce outputs that are detailed, actionable, architecturally sound, multistep, and include code, diagrams, and deployment plans. Research Stripe API integration for payment processing."
- **Agent Prompt**: "Focus on security best practices and PCI compliance."

### Output Prompt:
```
Research Topic: Stripe API integration for payment processing

Context:
Tech Stack: Python, FastAPI
Task Complexity: high
Research Depth: adaptive

Project Objectives and Requirements:
Follow every requirement below strictly. Produce outputs that are detailed, actionable, architecturally sound, multistep, and include code, diagrams, and deployment plans. Research Stripe API integration for payment processing.

Agent-Specific Instructions:
Focus on security best practices and PCI compliance.

Please provide comprehensive research...
```

---

## ✅ Benefits

1. **Complete Context**: LLM receives all necessary information
2. **Clear Separation**: Topic (WHAT) vs Instructions (HOW)
3. **No Information Loss**: Project objectives preserved in context
4. **Agent Customization**: Agent-specific prompts included
5. **Robust Extraction**: Handles various objective formats

---

## 📝 Files Modified

1. **`agents/researcher_agent.py`**:
   - Enhanced `_extract_research_query()` to clean topic
   - Updated `_conduct_research_with_llm_async()` to include full context
   - Added agent prompt retrieval from ConfigurationManager
   - Structured user prompt with all context sections

---

## 🧪 Testing

1. **Test with instruction-heavy objectives**:
   - Verify clean topic extraction
   - Verify full objective included in context
   - Verify LLM receives complete instruction

2. **Test with agent-specific prompts**:
   - Set agent prompt in ConfigurationManager
   - Verify prompt included in context
   - Verify LLM follows agent-specific instructions

3. **Test with various objective formats**:
   - Objectives with instructions at start
   - Objectives with instructions at end
   - Objectives with mixed content

