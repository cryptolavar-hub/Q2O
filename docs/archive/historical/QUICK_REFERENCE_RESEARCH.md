# Quick Reference - Agent Research Communication
**For Quick Copy-Paste**

---

## ✅ **Answer: YES, All Agents Can Request Research!**

Every agent has the `request_research()` method built-in. Here's how to use it:

---

## 🚀 **Quick Start (Copy-Paste)**

### **Basic Request**

```python
# In any agent's process_task method:
self.request_research(
    query="What you need to know",
    task_id=task.id
)
```

### **Urgent Request (Blocking)**

```python
self.request_research(
    query="Critical technical question",
    task_id=task.id,
    urgency="high"  # Processed immediately
)
```

### **Comprehensive Research**

```python
self.request_research(
    query="Unknown framework deep dive",
    task_id=task.id,
    urgency="high",
    depth="comprehensive"  # Get everything
)
```

---

## 📋 **Complete Example**

```python
def process_task(self, task: Task) -> Task:
    # Check if research needed
    if "latest" in task.description or self._is_unknown_tech(task):
        
        # Request research
        self.request_research(
            query=f"{task.title} best practices",
            task_id=task.id,
            urgency="high"
        )
    
    # Use research if available
    research = task.metadata.get("research_results")
    if research:
        confidence = research.get("confidence_score", 0)
        findings = research.get("key_findings", [])
        examples = research.get("code_examples", [])
        
        self.logger.info(f"Using research (confidence: {confidence})")
        # Apply research to your code...
    
    # Continue normal processing
    # ...
```

---

## 📊 **Parameters**

```python
request_research(
    query="...",           # What to research (required)
    task_id=task.id,       # Your task ID (optional)
    urgency="normal",      # "low", "normal", "high"
    depth="adaptive"       # "quick", "deep", "comprehensive", "adaptive"
)
```

---

## 🎯 **When to Use**

### **Request Research** ✅
- Unknown technology
- "Latest" or "best practices" keywords
- Unfamiliar API
- Complex patterns needed
- Need code examples

### **Don't Request** ❌
- Known patterns (we have templates)
- Simple CRUD
- Standard operations
- Already cached

---

## 📨 **What You Get Back**

```python
research_results = {
    "confidence_score": 85,          # 0-100 quality
    "key_findings": [...],           # Main points
    "documentation_urls": [...],     # Official docs
    "code_examples": [...],          # Code snippets
    "search_results": [...],         # All results
    "cached": False                  # True if from cache
}
```

---

## ⚡ **Key Facts**

1. ✅ **All agents have** `request_research()` method
2. ✅ **ResearcherAgent subscribes** to "research" channel
3. ✅ **Automatic caching** (90 days, cross-project)
4. ✅ **Multi-provider** (Google/Bing/DuckDuckGo)
5. ✅ **Parallel execution** (non-blocking)
6. ✅ **Quality scoring** (confidence 0-100)

---

## 📖 **Full Documentation**

- **Complete Guide**: `AGENT_RESEARCH_COMMUNICATION.md`
- **ResearcherAgent**: `RESEARCHER_AGENT_GUIDE.md`
- **Examples**: See above documents

---

**Yes, all agents know how to communicate with ResearcherAgent!** ✅

Just call: `self.request_research("your query", task_id=task.id)`

