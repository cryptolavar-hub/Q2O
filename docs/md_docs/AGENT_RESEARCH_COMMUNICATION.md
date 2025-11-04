# Agent-to-ResearcherAgent Communication Guide
**For Agent Developers**  
**Version**: 1.0  
**Date**: November 3, 2025

---

## 🎯 **Purpose**

This guide shows **how any agent can request research** from the ResearcherAgent during task execution.

---

## ✅ **YES - All Agents Can Request Research!**

All agents inherit from `BaseAgent` which includes the `request_research()` method via MessagingMixin. **Every agent can request web research at any time during task execution.**

---

## 🚀 **Quick Answer**

### **How to Request Research** (One-Liner)

```python
# In any agent's process_task method:
self.request_research(query="JWT validation best practices Python", task_id=task.id, urgency="high")
```

**That's it!** The ResearcherAgent will:
1. Search the web (Google/Bing/DuckDuckGo)
2. Find documentation and code examples
3. Send results back to you
4. Save results for future use

---

## 📖 **Complete Examples**

### **Example 1: Simple Research Request**

```python
# In CoderAgent's process_task method
from agents.coder_agent import CoderAgent

class CoderAgent(BaseAgent):
    def process_task(self, task: Task) -> Task:
        description = task.description.lower()
        
        # Check if we need external information
        if "middleware" in description and "auth" in description:
            # Request research
            self.logger.info("Need research on auth middleware patterns")
            self.request_research(
                query="FastAPI authentication middleware patterns",
                task_id=task.id,
                urgency="normal"
            )
            # Continue processing or wait for research...
        
        # ... rest of your code
```

### **Example 2: Urgent Research (Blocking)**

```python
# In IntegrationAgent's process_task method
from agents.integration_agent import IntegrationAgent

class IntegrationAgent(BaseAgent):
    def process_task(self, task: Task) -> Task:
        # Encounter unknown API
        api_name = "Xero API"  # Unknown to us
        
        if api_name not in self.known_apis:
            self.logger.warning(f"Unknown API: {api_name}, requesting research")
            
            # Request urgent research
            self.request_research(
                query=f"{api_name} Python client library authentication",
                task_id=task.id,
                urgency="high",  # High urgency = immediate processing
                depth="comprehensive"  # Need deep research
            )
            
            # For high urgency, ResearcherAgent processes immediately
            # Results sent back via message broker
```

### **Example 3: Comprehensive Research**

```python
# In FrontendAgent's process_task method
class FrontendAgent(BaseAgent):
    def process_task(self, task: Task) -> Task:
        # New framework requested
        if "svelte" in task.description.lower():
            self.logger.info("Svelte detected - requesting comprehensive research")
            
            self.request_research(
                query="Svelte 5 with TypeScript best practices and patterns",
                task_id=task.id,
                urgency="normal",
                depth="comprehensive"  # Get everything: docs, examples, best practices
            )
```

### **Example 4: Quick Research**

```python
# In WorkflowAgent's process_task method
class WorkflowAgent(BaseAgent):
    def process_task(self, task: Task) -> Task:
        # Just need quick reference
        if self.needs_quick_info("error handling"):
            self.request_research(
                query="Temporal workflow error handling patterns",
                task_id=task.id,
                urgency="normal",
                depth="quick"  # Just top 5 results
            )
```

---

## 📋 **Method Signature**

```python
def request_research(
    self, 
    query: str,                    # Research query
    task_id: str = None,           # Your task ID (optional)
    urgency: str = "normal",       # "low", "normal", or "high"
    depth: str = "adaptive"        # "quick", "deep", "comprehensive", "adaptive"
):
    """Request research from ResearcherAgent."""
```

### **Parameters Explained**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | str | Required | What to research (e.g., "FastAPI OAuth patterns") |
| `task_id` | str | None | Your current task ID (for tracking) |
| `urgency` | str | "normal" | How urgent: "low", "normal", "high" |
| `depth` | str | "adaptive" | How deep: "quick", "deep", "comprehensive", "adaptive" |

### **Urgency Levels**

| Level | Behavior | Use When |
|-------|----------|----------|
| `"low"` | Queued for later | Nice to have, not blocking |
| `"normal"` | Queued, processed in order | Standard request |
| `"high"` | Processed immediately | Blocking your task, need now |

### **Depth Levels**

| Depth | Results | Time | Use When |
|-------|---------|------|----------|
| `"quick"` | Top 5 results | ~2-5s | Just need a quick reference |
| `"deep"` | 10+ results + scraping | ~10-20s | Need thorough understanding |
| `"comprehensive"` | All sources + code examples | ~30-60s | New tech, need everything |
| `"adaptive"` | Based on complexity | Varies | Let system decide |

---

## 📨 **How Messages Flow**

### **Request Flow**

```
1. Your Agent:
   self.request_research("FastAPI OAuth")
   
2. Message Broker:
   Routes to "research" channel
   
3. ResearcherAgent:
   - Receives message
   - Checks cache (instant if cached)
   - If not cached:
     * High urgency: Process immediately
     * Normal/Low: Queue for orchestrator
   
4. ResearcherAgent (after research):
   - Conducts web search
   - Saves results to research/ directory
   - Sends results back via share_result()
   
5. Your Agent:
   - Receives research_results message
   - Can access results from task metadata
   - Uses findings in code generation
```

### **Response Flow**

```python
# ResearcherAgent sends back results via:
self.share_result(
    result_type="research_results",
    data=research_results,
    target_agent_id=requesting_agent_id
)

# Your agent receives via message handler
# Results also available in task metadata if dependencies set correctly
```

---

## 💡 **Practical Usage Patterns**

### **Pattern 1: Check Before Requesting**

```python
def process_task(self, task: Task) -> Task:
    # Check if research already done
    if task.metadata.get("research_results"):
        research = task.metadata["research_results"]
        self.logger.info(f"Using existing research (confidence: {research.get('confidence_score')})")
        # Use research...
    else:
        # Need research
        if self.needs_external_info():
            self.request_research(
                query="What I need to know",
                task_id=task.id
            )
```

### **Pattern 2: Conditional Research**

```python
def process_task(self, task: Task) -> Task:
    tech_stack = task.tech_stack or []
    
    # Only request research for unknown tech
    for tech in tech_stack:
        if tech not in self.known_technologies:
            self.logger.info(f"Unknown tech: {tech}, requesting research")
            self.request_research(
                query=f"{tech} with {self.primary_language} best practices",
                task_id=task.id,
                urgency="high"
            )
```

### **Pattern 3: Multiple Research Queries**

```python
def process_task(self, task: Task) -> Task:
    # Can request multiple researches
    if self.needs_multiple_topics:
        # Topic 1
        self.request_research(
            query="OAuth 2.1 PKCE flow",
            task_id=task.id,
            urgency="high",
            depth="deep"
        )
        
        # Topic 2  
        self.request_research(
            query="JWT token validation Python",
            task_id=task.id,
            urgency="normal",
            depth="quick"
        )
```

---

## 📊 **When to Request Research**

### **✅ Good Use Cases**

- **Unknown technology**: Encountering tech not in templates
- **Latest practices**: Need current best practices
- **API documentation**: Unfamiliar API integration
- **Complex patterns**: Need examples of implementation patterns
- **Error resolution**: Stuck on implementation approach

### **❌ When NOT to Request**

- **Known patterns**: We have templates for common tasks
- **Simple operations**: Basic CRUD, standard endpoints
- **Already cached**: ResearcherAgent checks cache automatically
- **Not code-related**: Non-technical questions

---

## 🎯 **Complete Working Example**

### **CoderAgent with Research Integration**

```python
from agents.base_agent import BaseAgent, AgentType, Task
from typing import Dict, Any

class CoderAgent(BaseAgent):
    """Enhanced coder agent with research capability."""
    
    def __init__(self, agent_id: str = "coder_main", workspace_path: str = "."):
        super().__init__(agent_id, AgentType.CODER)
        self.workspace_path = workspace_path
        self.known_patterns = ["oauth", "crud", "rest", "graphql"]  # What we know
    
    def process_task(self, task: Task) -> Task:
        try:
            self.logger.info(f"Processing coding task: {task.title}")
            
            # Extract requirements
            description = task.description.lower()
            tech_stack = task.tech_stack or []
            
            # CHECK: Do we need research?
            needs_research = False
            research_query = None
            
            # Check 1: Unknown technology
            unknown_tech = [t for t in tech_stack if t.lower() not in self.known_patterns]
            if unknown_tech:
                needs_research = True
                research_query = f"{unknown_tech[0]} with Python implementation patterns"
            
            # Check 2: Latest/best practices requested
            if any(keyword in description for keyword in ["latest", "best practices", "modern"]):
                needs_research = True
                research_query = f"{task.title} latest best practices"
            
            # REQUEST RESEARCH if needed
            if needs_research and research_query:
                self.logger.info(f"Requesting research: {research_query}")
                
                self.request_research(
                    query=research_query,
                    task_id=task.id,
                    urgency="high",  # Blocking task
                    depth="deep"
                )
                
                # Note: For high urgency, ResearcherAgent processes immediately
                # Results will be sent back via message broker
                # You can also check task.metadata["research_results"] if set
            
            # USE RESEARCH if available
            research_results = task.metadata.get("research_results")
            if research_results:
                self.logger.info(f"Using research (confidence: {research_results.get('confidence_score')})")
                
                # Extract useful info
                key_findings = research_results.get("key_findings", [])
                code_examples = research_results.get("code_examples", [])
                official_docs = research_results.get("documentation_urls", [])
                
                self.logger.info(f"Research findings: {len(key_findings)} key points")
                self.logger.info(f"Code examples: {len(code_examples)}")
                self.logger.info(f"Official docs: {len(official_docs)}")
                
                # Use in code generation
                # ... your implementation using research ...
            
            # GENERATE CODE (with or without research)
            # ... your normal code generation logic ...
            
            task.result = {"status": "completed", "files_created": []}
            self.complete_task(task.id, task.result)
            
        except Exception as e:
            self.fail_task(task.id, str(e))
        
        return task
```

---

## 📚 **Research Result Format**

### **What You Get Back**

```python
research_results = {
    "query": "FastAPI OAuth patterns",
    "confidence_score": 85,  # 0-100 quality score
    "search_results": [
        {
            "title": "FastAPI OAuth Documentation",
            "url": "https://fastapi.tiangolo.com/...",
            "snippet": "...",
            "source": "google"
        }
        # ... more results
    ],
    "documentation_urls": [
        "https://fastapi.tiangolo.com/...",
        "https://oauth.net/2/"
    ],
    "code_examples": [
        {
            "code": "from fastapi import Depends...",
            "source_url": "...",
            "source_title": "..."
        }
    ],
    "key_findings": [
        "Most mentioned concepts: oauth, token, fastapi",
        "Found 3 official documentation sources",
        "Extracted 5 code examples"
    ],
    "cached": False,  # True if from cache
    "timestamp": "2025-11-03T14:30:00"
}
```

### **How to Access**

```python
# Method 1: From task metadata (if research was a dependency)
research = task.metadata.get("research_results")

# Method 2: Listen for share_result message
def _handle_share_result(self, message):
    if message.payload.get("result_type") == "research_results":
        research = message.payload.get("data")
        # Use research...
```

---

## 🔧 **Implementation Checklist for Your Agent**

### **Step 1: Identify When Research Is Needed**

```python
def _needs_research(self, task: Task) -> bool:
    """Determine if task needs research."""
    # Check for unknown tech
    # Check for "latest" keywords
    # Check complexity
    return needs_research_bool
```

### **Step 2: Request Research**

```python
if self._needs_research(task):
    self.request_research(
        query=self._build_research_query(task),
        task_id=task.id,
        urgency="high" if blocking else "normal"
    )
```

### **Step 3: Use Research Results**

```python
research = task.metadata.get("research_results")
if research and research.get("confidence_score", 0) > 70:
    # Good quality research - use it!
    self._apply_research_findings(research, task)
else:
    # Low quality or no research - use fallback
    self._use_default_approach(task)
```

---

## 💬 **Communication Examples**

### **Example 1: CoderAgent Requests Research**

```python
class CoderAgent(BaseAgent):
    def process_task(self, task: Task) -> Task:
        # Scenario: Building Stripe integration but unsure of best approach
        
        self.logger.info("Requesting research on Stripe webhook handling")
        
        self.request_research(
            query="Stripe webhook signature verification Python FastAPI",
            task_id=task.id,
            urgency="high",
            depth="deep"
        )
        
        # ResearcherAgent will:
        # 1. Search web
        # 2. Find Stripe docs
        # 3. Extract code examples
        # 4. Send back results
        
        # You'll receive via share_result message
        # Or check task.metadata["research_results"]
```

### **Example 2: IntegrationAgent During Execution**

```python
class IntegrationAgent(BaseAgent):
    def _create_api_client(self, api_name: str, task: Task):
        if api_name not in ["quickbooks", "odoo", "stripe"]:
            # Unknown API - need research!
            self.logger.info(f"Unknown API: {api_name}")
            
            self.request_research(
                query=f"{api_name} REST API Python client authentication",
                task_id=task.id,
                urgency="high"  # Blocking - need this to continue
            )
            
            # For high urgency, wait briefly for response
            # Or queue task and let orchestrator handle dependency
```

### **Example 3: FrontendAgent Needs Component Examples**

```python
class FrontendAgent(BaseAgent):
    def _create_custom_component(self, component_type: str, task: Task):
        # Need examples of modern component patterns
        
        self.request_research(
            query=f"React {component_type} component patterns with TypeScript hooks",
            task_id=task.id,
            urgency="normal",
            depth="deep"
        )
        
        # Continue with other work while research happens
```

---

## 🎓 **Best Practices**

### **1. Be Specific in Queries**

**Good**:
```python
self.request_research("FastAPI OAuth 2.1 PKCE implementation example")
```

**Bad**:
```python
self.request_research("authentication")  # Too vague
```

### **2. Set Appropriate Urgency**

```python
# High: Blocking your task
self.request_research(query="...", urgency="high")

# Normal: Can continue with other work
self.request_research(query="...", urgency="normal")

# Low: Nice to have, not critical
self.request_research(query="...", urgency="low")
```

### **3. Check Confidence Score**

```python
research = task.metadata.get("research_results")
if research:
    score = research.get("confidence_score", 0)
    
    if score >= 80:
        # High quality - use confidently
        self._use_research(research)
    elif score >= 60:
        # Medium quality - use with caution
        self._use_research_carefully(research)
    else:
        # Low quality - fallback to default
        self._use_default_approach()
```

### **4. Leverage Caching**

```python
# Don't worry about duplicate requests!
# ResearcherAgent automatically checks 90-day cache
# Subsequent identical requests return instantly

# First call: Web search (~5s)
self.request_research("FastAPI OAuth")

# Second call (same query, within 90 days): Cache hit (<0.1s)
self.request_research("FastAPI OAuth")  # Instant!
```

---

## 🔍 **Message Protocol Details**

### **Under the Hood**

When you call `request_research()`, here's what happens:

```python
# 1. Your agent sends message
message = {
    "message_type": "REQUEST_HELP",
    "sender_agent_id": "coder_main",
    "target_agent_type": "researcher",
    "channel": "research",
    "payload": {
        "help_type": "research",
        "query": "FastAPI OAuth",
        "urgency": "high",
        "task_id": "task_0001"
    }
}

# 2. Message broker publishes to "research" channel

# 3. ResearcherAgent (subscribed to "research" channel) receives

# 4. ResearcherAgent processes:
result = researcher.handle_research_request(...)

# 5. ResearcherAgent sends back:
researcher.share_result(
    result_type="research_results",
    data=result,
    target_agent_id="coder_main"
)

# 6. Your agent receives research_results
```

---

## 🛠️ **Advanced: Custom Message Handling**

### **If You Want to Handle Research Results Directly**

```python
class MyAgent(BaseAgent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add custom handler for research results
        if hasattr(self, 'message_handlers'):
            from utils.message_protocol import MessageType
            self.message_handlers[MessageType.SHARE_RESULT] = self._handle_research_result
    
    def _handle_research_result(self, message):
        """Handle research results from ResearcherAgent."""
        if message.payload.get("result_type") == "research_results":
            research_data = message.payload.get("data")
            self.logger.info(f"Received research: {research_data.get('query')}")
            
            # Store for current task
            # Or process immediately
            self._process_research_data(research_data)
```

---

## 📝 **Complete Communication Template**

### **Add This to Your Agent**

```python
from agents.base_agent import BaseAgent, Task, AgentType

class YourAgent(BaseAgent):
    """Your agent with research capability."""
    
    def __init__(self, agent_id: str = "your_main", workspace_path: str = "."):
        super().__init__(agent_id, AgentType.YOUR_TYPE)
        self.workspace_path = workspace_path
    
    def process_task(self, task: Task) -> Task:
        """Process task with optional research."""
        try:
            # STEP 1: Check if research needed
            if self._should_request_research(task):
                query = self._build_research_query(task)
                
                # STEP 2: Request research
                self.logger.info(f"Requesting research: {query}")
                self.request_research(
                    query=query,
                    task_id=task.id,
                    urgency="high" if self._is_blocking(task) else "normal",
                    depth="adaptive"
                )
            
            # STEP 3: Use research if available
            research = task.metadata.get("research_results")
            if research:
                self._use_research(research, task)
            else:
                self._use_default_approach(task)
            
            # STEP 4: Complete task
            self.complete_task(task.id, task.result)
            
        except Exception as e:
            self.fail_task(task.id, str(e))
        
        return task
    
    def _should_request_research(self, task: Task) -> bool:
        """Determine if research needed."""
        # Your logic here
        return False
    
    def _build_research_query(self, task: Task) -> str:
        """Build research query from task."""
        return f"{task.title} best practices"
    
    def _is_blocking(self, task: Task) -> bool:
        """Is this task blocked without research?"""
        return True  # or your logic
    
    def _use_research(self, research: Dict, task: Task):
        """Use research findings."""
        findings = research.get("key_findings", [])
        examples = research.get("code_examples", [])
        # Apply to your task...
    
    def _use_default_approach(self, task: Task):
        """Fallback when no research."""
        # Use templates/default logic
        pass
```

---

## ✅ **Verification**

### **Test Your Agent's Research Capability**

```python
# Quick test
from agents.your_agent import YourAgent
from agents.base_agent import Task, AgentType

agent = YourAgent()

# Check if method exists
assert hasattr(agent, 'request_research'), "Agent should have request_research method"

# Test calling it
task = Task(id="test", title="Test", description="Test", agent_type=AgentType.CODER)
agent.request_research("Test query", task_id=task.id)

# Should log: "Requested research from your_agent: Test query (urgency: normal)"
```

---

## 📞 **Quick Reference Card**

```python
# SIMPLE REQUEST
self.request_research("What I need to know", task_id=task.id)

# WITH URGENCY
self.request_research("Critical info", task_id=task.id, urgency="high")

# WITH DEPTH
self.request_research("Deep dive topic", task_id=task.id, depth="comprehensive")

# FULL OPTIONS
self.request_research(
    query="Specific technical question",
    task_id=task.id,
    urgency="high",  # "low", "normal", "high"
    depth="deep"     # "quick", "deep", "comprehensive", "adaptive"
)
```

---

## 🎯 **Summary**

### **YES - All Agents Know How to Communicate with ResearcherAgent!**

**Every agent has**:
- ✅ `request_research()` method (inherited from BaseAgent/MessagingMixin)
- ✅ Message broker access
- ✅ Subscription to channels
- ✅ Research channel communication

**ResearcherAgent has**:
- ✅ Subscription to "research" channel
- ✅ Message handler for research requests
- ✅ Response mechanism (share_result)
- ✅ Cache checking
- ✅ Urgency-based prioritization

**Communication flow**:
1. Agent calls `self.request_research(...)`
2. Message sent to "research" channel
3. ResearcherAgent receives and processes
4. Results sent back via `share_result()`
5. Requesting agent receives results

---

**All agents can now intelligently request and receive web research!** 🔍✨

**For more**: See `RESEARCHER_AGENT_GUIDE.md` for complete ResearcherAgent documentation.

