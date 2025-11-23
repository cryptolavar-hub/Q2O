# Agent LLM Usage Review

**Date:** November 23, 2025  
**Status:** Complete Review

## Executive Summary

This document reviews all agents in the Q2O system to identify which agents use LLM services and in what execution order during project execution.

---

## Agents Using LLM

### 1. **OrchestratorAgent** (FIRST - Project Initialization)
**File:** `agents/orchestrator.py`

**LLM Usage:**
- **Purpose:** Intelligent task breakdown and project planning
- **Method:** `_analyze_objective_with_llm()`
- **When:** During `break_down_project()` - the FIRST step in project execution
- **What it does:**
  - Analyzes project objectives
  - Breaks down objectives into sequenced tasks
  - Determines agent assignments
  - Identifies dependencies
  - Estimates complexity
  - Suggests tech stack

**Execution Order:** **#1** (Before any other agent runs)

**LLM Prompt:**
- System prompt: Defines agent types and task breakdown structure
- User prompt: Project description, objectives, context

**Fallback:** Rules-based breakdown if LLM fails

---

### 2. **ResearcherAgent** (SECOND - Research Phase)
**File:** `agents/researcher_agent.py`

**LLM Usage:**
- **Purpose:** Comprehensive research (PRIMARY method as of November 2025)
- **Method:** `_conduct_research_with_llm_async()` (PRIMARY)
- **Secondary:** `_synthesize_findings_with_llm()` (for web search results)
- **When:** During `process_task()` when research is needed
- **What it provides:**
  - Key findings and insights
  - Official documentation URLs
  - Code examples
  - Best practices
  - Common pitfalls
  - Implementation patterns
  - Integration requirements
  - Performance and security considerations

**Execution Order:** **#2** (After Orchestrator, before implementation agents)

**LLM Priority:**
- **PRIMARY:** LLM research (single comprehensive call)
- **FALLBACK:** Web search (only if LLM fails)

**LLM Prompt:**
- System prompt: Expert researcher role, JSON structure for research results
- User prompt: Research query, tech stack context, complexity level

**Fallback:** Web search with LLM synthesis

---

### 3. **CoderAgent** (THIRD - Code Implementation)
**File:** `agents/coder_agent.py`

**LLM Usage:**
- **Purpose:** Code generation when templates are insufficient
- **Method:** `llm_service.generate_code()`
- **When:** During `_implement_code_async()` when:
  - No learned templates match
  - Traditional templates don't cover the requirement
  - Complex or novel implementation needed

**Execution Order:** **#3** (After research, during implementation phase)

**Hybrid Strategy:**
1. Check learned templates (free, instant)
2. Use traditional templates (fast, reliable)
3. **Generate with LLM** (adaptive, handles anything) ← LLM here
4. Learn from LLM successes (self-improving)

**LLM Prompt:**
- System prompt: Code generation guidelines, language-specific best practices
- User prompt: Task description, requirements, context, examples

**Fallback:** Template-based generation if LLM fails

---

### 4. **MobileAgent** (FOURTH - Mobile Development)
**File:** `agents/mobile_agent.py`

**LLM Usage:**
- **Purpose:** Mobile-specific code generation and platform guidance
- **Method:** `llm_service.complete()` for mobile code generation
- **When:** During mobile app development tasks

**Execution Order:** **#4** (After research, parallel with CoderAgent for mobile projects)

**LLM Prompt:**
- System prompt: Mobile development expert, platform-specific guidelines
- User prompt: Mobile requirements, platform (iOS/Android), features

**Fallback:** Template-based mobile code generation

---

## Agents NOT Using LLM

The following agents do **NOT** use LLM services:

1. **TestingAgent** - Uses test templates and frameworks
2. **QAAgent** - Uses rule-based quality checks
3. **SecurityAgent** - Uses security scanning tools and rule-based checks
4. **InfrastructureAgent** - Uses Terraform/CloudFormation templates
5. **IntegrationAgent** - Uses API templates and patterns (may request research)
6. **FrontendAgent** - Uses React/Next.js templates
7. **WorkflowAgent** - Uses workflow templates and patterns
8. **NodeAgent** - Uses Node.js templates

**Note:** These agents may **request research** from ResearcherAgent, which uses LLM.

---

## Execution Order During Project Run

Based on `main.py` and `AgentSystem.run_project()`:

```
1. ORCHESTRATOR (LLM)
   └─> break_down_project()
       └─> _analyze_objective_with_llm() [LLM CALL #1]
           └─> Creates task list with dependencies

2. TASK DISTRIBUTION
   └─> orchestrator.distribute_tasks()
       └─> Assigns tasks to agents based on agent_type

3. ITERATIVE PROCESSING (in order):
   
   a. RESEARCHER (LLM) - If research tasks exist
      └─> process_task()
          └─> _conduct_research()
              └─> _conduct_research_with_llm_async() [LLM CALL #2]
                  └─> Returns comprehensive research
   
   b. INFRASTRUCTURE - If infrastructure tasks exist
      └─> process_task()
          └─> Creates cloud resources (no LLM)
   
   c. INTEGRATION - If integration tasks exist
      └─> process_task()
          └─> May request research (which uses LLM)
          └─> Creates API integrations (no LLM)
   
   d. CODER (LLM) - If code implementation tasks exist
      └─> process_task()
          └─> _implement_code_async()
              └─> llm_service.generate_code() [LLM CALL #3]
                  └─> Generates code files
   
   e. MOBILE (LLM) - If mobile tasks exist
      └─> process_task()
          └─> llm_service.complete() [LLM CALL #4]
              └─> Generates mobile code
   
   f. FRONTEND - If frontend tasks exist
      └─> process_task()
          └─> Uses templates (no LLM)
   
   g. WORKFLOW - If workflow tasks exist
      └─> process_task()
          └─> Uses templates (no LLM)
   
   h. TESTING - If testing tasks exist
      └─> process_task()
          └─> Uses test templates (no LLM)
   
   i. QA - If QA tasks exist
      └─> process_task()
          └─> Rule-based checks (no LLM)
   
   j. SECURITY - If security tasks exist
      └─> process_task()
          └─> Security scanning (no LLM)

4. ITERATION CONTINUES
   └─> Until all tasks complete or max iterations reached
```

---

## LLM Call Summary

| Agent | LLM Method | Execution Order | Purpose |
|-------|-----------|----------------|---------|
| **OrchestratorAgent** | `_analyze_objective_with_llm()` | **#1** (First) | Task breakdown and planning |
| **ResearcherAgent** | `_conduct_research_with_llm_async()` | **#2** (Early) | Comprehensive research (PRIMARY) |
| **ResearcherAgent** | `_synthesize_findings_with_llm()` | **#2b** (If web search used) | Synthesize web search results |
| **CoderAgent** | `llm_service.generate_code()` | **#3** (Implementation) | Code generation |
| **MobileAgent** | `llm_service.complete()` | **#4** (Mobile) | Mobile code generation |

---

## Key Insights

1. **Orchestrator runs FIRST** - Uses LLM to intelligently plan the entire project
2. **Researcher runs EARLY** - Uses LLM as PRIMARY method (new as of Nov 2025)
3. **Coder runs DURING implementation** - Uses LLM when templates insufficient
4. **Mobile runs for mobile projects** - Uses LLM for platform-specific code
5. **Other agents use templates/patterns** - No direct LLM calls, but may request research

---

## Dependencies

- **Orchestrator** → Creates tasks for all other agents
- **Researcher** → Provides research to other agents (via ResearchAwareMixin)
- **Coder** → May depend on Researcher for implementation guidance
- **Mobile** → May depend on Researcher for mobile-specific research
- **All agents** → Depend on Orchestrator for task assignment

---

## Notes

- LLM usage is controlled by `Q2O_USE_LLM` environment variable
- All LLM-enabled agents have fallback mechanisms (templates, rules, web search)
- LLM calls are tracked for cost monitoring and budget alerts
- LLM responses are cached (90-day TTL) to reduce costs
- Provider fallback chain: Gemini → OpenAI → Anthropic (9 total attempts)

---

**Last Updated:** November 23, 2025

