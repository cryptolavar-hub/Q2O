# ResearcherAgent - Web Research Guide
**Version**: 1.0  
**Date**: November 3, 2025  
**Agent Type**: Web Research & Information Gathering

---

## 🔍 **Overview**

The **ResearcherAgent** conducts web research to gather information, documentation, code examples, and best practices for project objectives and tasks. It intelligently determines when research is needed and provides synthesized findings to other agents.

---

## ✨ **Key Features**

### **1. Multi-Provider Web Search**
- **Primary**: Google Custom Search API (when configured)
- **Secondary**: Bing Search API (when configured)
- **Fallback**: DuckDuckGo (free, always available)
- **Automatic Fallback Chain**: Tries providers in order until successful

### **2. Intelligent Research Detection**
- **Smart Detection**: Automatically identifies when research is needed
- **Agent Requests**: Other agents can request research during execution
- **Keyword Based**: Detects research keywords in objectives

### **3. Adaptive Research Depth**
- **Quick**: Top 5-10 results for simple queries
- **Deep**: Extended search with multiple angles
- **Comprehensive**: Full content scraping and code extraction
- **Adaptive**: Adjusts depth based on task complexity

### **4. Knowledge Base & Caching**
- **90-Day Cache**: Avoids redundant searches
- **Cross-Project Sharing**: Research cached globally
- **Automatic Expiration**: Old results automatically removed
- **Fast Retrieval**: Instant access to cached results

### **5. Quality Validation**
- **Official Docs Preferred**: Prioritizes official documentation
- **Source Reputation**: Validates source credibility
- **Cross-Reference**: Compares multiple sources
- **Confidence Scoring**: Rates research quality (0-100)

### **6. Parallel Execution**
- **Non-Blocking**: Independent tasks run during research
- **Dependency Management**: Dependent tasks wait for research
- **Agent Communication**: Agents can request research anytime
- **Load Balanced**: Multiple researcher instances for high availability

---

## ⚙️ **Configuration**

### **Environment Variables**

Add to your `.env` file:

```bash
# Google Custom Search (Optional - Recommended)
GOOGLE_SEARCH_API_KEY=your_google_api_key_here
GOOGLE_SEARCH_CX=your_custom_search_engine_id

# Bing Search (Optional - Alternative)
BING_SEARCH_API_KEY=your_bing_api_key_here

# Research Configuration
RESEARCH_DAILY_LIMIT=100  # Max searches per day per provider (default: 100)
```

### **Getting API Keys**

#### **Google Custom Search**:
1. Visit: https://developers.google.com/custom-search/v1/overview
2. Get API key: https://console.cloud.google.com/apis/credentials
3. Create Custom Search Engine: https://programmablesearchengine.google.com/
4. Copy both API key and Search Engine ID (CX)

#### **Bing Search** (Azure):
1. Visit: https://azure.microsoft.com/en-us/services/cognitive-services/bing-web-search-api/
2. Create Bing Search resource
3. Copy subscription key

#### **DuckDuckGo**:
- No API key needed!
- Free and unlimited
- Used automatically as fallback

---

## 🚀 **Usage**

### **Automatic (Smart Detection)**

The orchestrator automatically creates research tasks when needed:

```python
# Example: This objective will trigger research
python main.py \
  --project "New Framework" \
  --objective "Explore best practices for Svelte integration" \
  --workspace ./output

# "Explore" and "best practices" keywords trigger research
# Research task created FIRST
# Other tasks depend on research completion
```

### **Manual (In Objective)**

Explicitly request research:

```python
# Config file
{
  "project_description": "API Integration",
  "objectives": [
    "Research latest OAuth 2.1 best practices",  # Research task
    "Implement OAuth based on research findings"  # Depends on research
  ]
}
```

### **Agent Request (During Execution)**

Other agents can request research:

```python
# Inside an agent's process_task method
if self.needs_external_info:
    # Send research request
    self.send_message(
        message_type="request_research",
        payload={
            "query": "FastAPI OAuth middleware patterns",
            "urgency": "high",
            "requesting_task_id": task.id
        },
        channel="research"
    )
```

---

## 📊 **Research Process**

### **Phase 1: Query Analysis**
- Extract research query from task
- Determine research depth needed
- Check cache for existing results

### **Phase 2: Web Search**
- Try Google Custom Search (if configured)
- Fall back to Bing Search (if configured)
- Ultimate fallback to DuckDuckGo (always available)
- Respect rate limits (fallback if exceeded)

### **Phase 3: Content Analysis**
- Identify official documentation URLs
- Extract relevant snippets
- Scrape top results (Level 2)
- Parse code examples

### **Phase 4: Synthesis**
- Identify key findings
- Extract best practices
- Summarize main concepts
- Calculate confidence score

### **Phase 5: Delivery**
- Save results to JSON (structured data)
- Save results to Markdown (human-readable)
- Store in research/ directory
- Broadcast via message broker
- Add to task metadata

---

## 📁 **Output Structure**

### **Research Directory**

```
research/
├── explore_best_practices_20251103_140530.json
├── explore_best_practices_20251103_140530.md
├── oauth_authentication_20251103_141015.json
├── oauth_authentication_20251103_141015.md
└── ...
```

### **JSON Format** (For Agents)

```json
{
  "query": "OAuth best practices",
  "timestamp": "2025-11-03T14:05:30",
  "depth": "adaptive",
  "confidence_score": 85,
  "search_results": [
    {
      "title": "OAuth 2.0 Authorization Framework",
      "url": "https://oauth.net/2/",
      "snippet": "...",
      "source": "google"
    }
  ],
  "documentation_urls": [
    "https://oauth.net/2/",
    "https://tools.ietf.org/html/rfc6749"
  ],
  "code_examples": [
    {
      "code": "...",
      "source_url": "...",
      "source_title": "..."
    }
  ],
  "key_findings": [
    "Most mentioned concepts: oauth, token, authorization, scope, redirect",
    "Found 3 official documentation sources",
    "Extracted 5 code examples"
  ],
  "cached": false
}
```

### **Markdown Format** (For Humans)

```markdown
# Research Report: OAuth best practices
**Date**: 2025-11-03T14:05:30
**Confidence Score**: 85/100

## Key Findings
- Most mentioned concepts: oauth, token, authorization
- Found 3 official documentation sources
- Extracted 5 code examples

## Official Documentation
- https://oauth.net/2/
- https://tools.ietf.org/html/rfc6749

## Search Results
### 1. OAuth 2.0 Authorization Framework
**URL**: https://oauth.net/2/
**Snippet**: ...

### Code Examples
...
```

---

## 🎯 **When Research is Triggered**

### **Automatic Triggers** (Smart Detection)

Research is automatically triggered when:

1. **Research Keywords Detected**:
   - "latest", "best practices", "how to"
   - "explore", "find", "discover"
   - "research", "investigate", "learn about"
   - "compare", "evaluate", "new"
   - "emerging", "trends", "state of the art"

2. **Unknown Technology**:
   - Tech stack not in known list
   - New frameworks or libraries
   - Uncommon integration targets

3. **Complex Objectives**:
   - Long, detailed objectives (>10 words)
   - Multiple requirements in one objective

### **Examples**

**Triggers Research** ✅:
```
- "Research latest FastAPI authentication patterns"
- "Explore Svelte framework integration"
- "Find best practices for microservices architecture"
- "Investigate Redis caching strategies"
- "What's the latest approach to JWT validation"
```

**No Research Needed** ❌:
```
- "OAuth authentication with QuickBooks"  (known)
- "Create FastAPI endpoint"  (we have templates)
- "Next.js dashboard"  (we know this)
- "Terraform Azure setup"  (standard)
```

---

## 🔄 **Task Dependencies**

### **Research First, Then Execute**

When research is needed:

```
Task Flow:
1. task_0001_research: Research OAuth patterns
   Status: In Progress (ResearcherAgent)
   
2. task_0002_integration: Implement OAuth
   Status: Blocked (waiting for research)
   Dependencies: [task_0001_research]
   
3. task_0003_frontend: Create login page
   Status: In Progress (independent, can run in parallel)
   
4. task_0004_testing: Test OAuth
   Status: Blocked (waiting for task_0002)
   Dependencies: [task_0002_integration]
```

**Research and independent tasks run in parallel!**

---

## 💡 **Advanced Features**

### **1. Research Request from Agents**

Any agent can request research during task execution:

```python
# Example in CoderAgent
def process_task(self, task: Task) -> Task:
    # ... processing ...
    
    if self.needs_more_info:
        # Request research
        self.send_message(
            message_type="request_research",
            payload={
                "query": "FastAPI dependency injection patterns",
                "urgency": "high",
                "requesting_agent": self.agent_id,
                "requesting_task": task.id
            },
            channel="research"
        )
        
        # If urgent, ResearcherAgent processes immediately
        # Otherwise, queued via Orchestrator
```

### **2. Cache Management**

```python
# Research results cached for 90 days
# Cache location: ~/.quickodoo/research_cache/
# Shared across ALL projects

# Cache structure:
~/.quickodoo/research_cache/
├── index.json  # Cache index
├── a1b2c3d4.json  # Cached result 1
├── e5f6g7h8.json  # Cached result 2
└── ...
```

### **3. Rate Limiting**

```python
# Daily limits per provider:
RESEARCH_DAILY_LIMIT=100  # default

# Tracking file: .research_cache/search_count.json
{
  "date": "2025-11-03",
  "google": 45,
  "bing": 0,
  "duckduckgo": 12
}

# Automatic reset at midnight
# Automatic fallback when limit reached
```

### **4. Quality Scoring**

Confidence score components:
- **Base (30 points)**: Results found
- **Official docs (25 points)**: Official documentation identified
- **Multiple sources (15 points)**: Multiple official sources
- **Code examples (15 points)**: Code examples extracted
- **Result count (10 points)**: 5+ results found
- **Recency (5 points)**: Recent results

**Total**: 0-100 score

---

## 🛠️ **Troubleshooting**

### **Issue**: No search results returned

**Causes**:
- All providers rate limited
- Network connectivity issues
- Invalid API keys

**Solutions**:
```bash
# Check API keys
echo $GOOGLE_SEARCH_API_KEY
echo $BING_SEARCH_API_KEY

# Check rate limits
cat .research_cache/search_count.json

# Test DuckDuckGo (fallback)
pip install duckduckgo-search

# Increase daily limit
export RESEARCH_DAILY_LIMIT=200
```

### **Issue**: Research taking too long

**Solutions**:
- Reduce research depth in task metadata
- Use cached results (check cache)
- Reduce num_results in searches

### **Issue**: Low confidence scores

**Causes**:
- Query too vague
- No official documentation found
- Few results returned

**Solutions**:
- Make query more specific
- Add tech stack context
- Manual research override

### **Issue**: Cache not working

**Check**:
```bash
# Cache location
ls ~/.quickodoo/research_cache/

# Cache index
cat ~/.quickodoo/research_cache/index.json

# Clear cache if needed
rm -rf ~/.quickodoo/research_cache/
```

---

## 📋 **Best Practices**

### **1. Write Specific Queries**

**Good**:
- "FastAPI OAuth 2.0 middleware implementation patterns"
- "Next.js 14 server actions with authentication"
- "Temporal workflow error handling best practices"

**Bad**:
- "Authentication" (too vague)
- "How to code" (not specific)
- "Integration" (what kind?)

### **2. Use Research Keywords**

Include keywords when you want research:
- "latest version of..."
- "best practices for..."
- "how to implement..."
- "compare approaches to..."

### **3. Monitor Cache Usage**

```bash
# Check cache stats
ls ~/.quickodoo/research_cache/*.json | wc -l

# View recent research
ls -lt research/*.md | head -5
```

### **4. Review Research Results**

Before using research-based code:
- Check confidence score (aim for 70+)
- Review official documentation links
- Verify code examples are recent
- Cross-reference findings

---

## 🔧 **Configuration Examples**

### **Minimal (DuckDuckGo Only)**

`.env`:
```bash
# No API keys needed
# DuckDuckGo used automatically
RESEARCH_DAILY_LIMIT=50
```

### **Google Search Enabled**

`.env`:
```bash
GOOGLE_SEARCH_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
GOOGLE_SEARCH_CX=0123456789abcdef:xxxxxxxxx
RESEARCH_DAILY_LIMIT=100
```

### **Full Setup (All Providers)**

`.env`:
```bash
# Google (Primary)
GOOGLE_SEARCH_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
GOOGLE_SEARCH_CX=0123456789abcdef:xxxxxxxxx

# Bing (Secondary)
BING_SEARCH_API_KEY=abcdef1234567890abcdef1234567890

# DuckDuckGo (Automatic Fallback)
# No configuration needed

# Limits
RESEARCH_DAILY_LIMIT=200
```

---

## 📖 **Usage Examples**

### **Example 1: Research Unknown Tech**

```bash
python main.py \
  --project "Svelte Integration" \
  --objective "Research Svelte 5 with FastAPI backend" \
  --workspace ./svelte_project
```

**Flow**:
1. Orchestrator detects "Svelte" (unknown tech)
2. Creates research task automatically
3. ResearcherAgent searches for "Svelte 5 FastAPI"
4. Finds documentation, examples, best practices
5. Other agents use research to generate code

### **Example 2: Explicit Research Request**

```json
{
  "project_description": "Modern Auth System",
  "objectives": [
    "Research latest OAuth 2.1 and OIDC best practices",
    "Implement OAuth 2.1 with PKCE",
    "Create frontend login with OAuth"
  ]
}
```

**Flow**:
1. Objective 1: Research task (explicit keyword)
2. Objective 2: Integration task (depends on research)
3. Objective 3: Frontend task (depends on integration)

### **Example 3: Parallel Research**

```json
{
  "project_description": "Multi-Feature App",
  "objectives": [
    "Research latest GraphQL best practices",
    "Create REST API endpoints",  # Independent - runs in parallel
    "Implement GraphQL based on research",  # Depends on research
    "Create database models"  # Independent - runs in parallel
  ]
}
```

**Execution**:
- Task 1 (Research): Runs immediately
- Task 2 (REST API): Runs in parallel with research
- Task 3 (GraphQL): Waits for research to complete
- Task 4 (Database): Runs in parallel with all

---

## 🎯 **Research Output**

### **What You Get**

For each research query, you receive:

1. **JSON File** (structured data for agents)
   - Search results with URLs
   - Official documentation links
   - Code examples
   - Key findings
   - Confidence score

2. **Markdown File** (human-readable report)
   - Summary of findings
   - Top search results
   - Code examples with source attribution
   - Official documentation links

3. **Task Metadata** (in memory)
   - Attached to dependent tasks
   - Accessible by all agents
   - Available in final project results

---

## 📊 **Performance Metrics**

### **Typical Research Times**

- **Cache Hit**: <0.1 seconds ⚡
- **Quick Search**: 2-5 seconds
- **Deep Research**: 10-20 seconds
- **Comprehensive**: 30-60 seconds

### **Rate Limits**

```
Google Custom Search:
  Free tier: 100 searches/day
  Paid: 10,000 searches/day

Bing Search:
  Free tier: 1,000 searches/month
  Paid: Higher limits

DuckDuckGo:
  No official limits
  Best effort basis
```

### **Cost Estimates**

- **DuckDuckGo**: Free ✅
- **Google**: $5 per 1,000 searches (above free tier)
- **Bing**: Varies by plan

**Recommendation**: Start with DuckDuckGo, add paid APIs if needed.

---

## 🔒 **Security & Privacy**

### **API Key Security**

- ✅ API keys in .env file (not committed)
- ✅ .env in .gitignore
- ✅ No keys in research results
- ✅ Secrets validator checks all code

### **Search Privacy**

- Research queries sent to search providers
- No sensitive data should be in queries
- Results cached locally
- Cache in user home directory (private)

### **Rate Limit Protection**

- Automatic daily reset
- Per-provider tracking
- Prevents over-usage
- Cost protection

---

## 🎓 **Best Practices**

### **1. Use Caching**

Research once, use many times:
```bash
# First time: Web search
# Subsequent: Instant cache retrieval (90 days)
```

### **2. Specific Queries**

Better results with specific queries:
- Include version numbers
- Specify language/framework
- Add context (e.g., "with Python", "for Azure")

### **3. Monitor Rate Limits**

```bash
# Check today's usage
cat .research_cache/search_count.json

# Output:
{
  "date": "2025-11-03",
  "google": 45,  # 45 of 100 used
  "bing": 0,     # 0 of 100 used
  "duckduckgo": 12  # 12 of 100 used
}
```

### **4. Review Before Using**

- Check confidence score (>70 is good)
- Review official docs
- Validate code examples
- Test before production use

---

## 🔗 **Integration with Other Agents**

### **CoderAgent**

Receives research results in task metadata:
```python
research_results = task.metadata.get("research_results")
if research_results:
    best_practices = research_results.get("key_findings")
    code_examples = research_results.get("code_examples")
    # Use in code generation
```

### **IntegrationAgent**

Uses documentation URLs:
```python
research_results = task.metadata.get("research_results")
if research_results:
    official_docs = research_results.get("documentation_urls")
    # Reference in generated code comments
```

### **TestingAgent**

Uses code examples for test cases:
```python
research_results = task.metadata.get("research_results")
if research_results:
    examples = research_results.get("code_examples")
    # Generate tests based on examples
```

---

## 📝 **Changelog**

### **Version 1.0** (November 3, 2025)
- Initial implementation
- Multi-provider search (Google, Bing, DuckDuckGo)
- 90-day caching
- Smart detection
- Agent request handling
- Quality validation
- Confidence scoring
- Parallel execution support

---

## 📞 **Support**

**Issues**: https://github.com/cryptolavar-hub/Q2O/issues  
**Documentation**: See `README.md` and `USAGE_GUIDE.md`  
**Dependencies**: See `requirements.txt`  

---

## ⚡ **Quick Start**

```bash
# 1. Install dependencies
pip install duckduckgo-search beautifulsoup4

# 2. (Optional) Add API keys to .env
GOOGLE_SEARCH_API_KEY=your_key
GOOGLE_SEARCH_CX=your_cx

# 3. Run with research-triggering objective
python main.py \
  --project "Test" \
  --objective "Research latest FastAPI patterns" \
  --workspace ./test

# 4. Check research results
ls research/
cat research/*.md
```

---

**ResearcherAgent is ready to help your agents build better code with web research!** 🔍✨

