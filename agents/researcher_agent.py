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

The LLM service automatically handles provider/model fallback with retries,
ensuring maximum success rate before falling back to search.
"""

from typing import Dict, Any, List, Optional, Set
from agents.base_agent import BaseAgent, AgentType, Task, TaskStatus
from utils.project_layout import ProjectLayout, get_default_layout
from utils.event_loop_utils import create_compatible_event_loop
import os
import json
import logging
import time
import hashlib
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
import re

# LLM Integration (Phase 2 - with graceful fallback)
try:
    from utils.llm_service import get_llm_service, LLMService
    from utils.configuration_manager import get_configuration_manager, ConfigurationManager
    LLM_INTEGRATION_AVAILABLE = True
except ImportError as e:
    logging.warning(f"LLM integration not available for ResearcherAgent: {e}")
    LLM_INTEGRATION_AVAILABLE = False


class ResearchCache:
    """Cache for research results to avoid redundant searches."""
    
    def __init__(self, cache_dir: str = ".research_cache", ttl_days: int = 90):
        """
        Initialize research cache.
        
        Args:
            cache_dir: Directory to store cache files
            ttl_days: Time-to-live for cached results in days
        """
        self.cache_dir = cache_dir
        self.ttl_days = ttl_days
        os.makedirs(cache_dir, exist_ok=True)
        self.cache_index_file = os.path.join(cache_dir, "index.json")
        self.cache_index = self._load_cache_index()
    
    def _load_cache_index(self) -> Dict:
        """Load cache index from disk."""
        if os.path.exists(self.cache_index_file):
            try:
                with open(self.cache_index_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}
    
    def _save_cache_index(self):
        """Save cache index to disk."""
        with open(self.cache_index_file, 'w', encoding='utf-8') as f:
            json.dump(self.cache_index, f, indent=2)
    
    def _get_cache_key(self, query: str) -> str:
        """Generate cache key from query."""
        return hashlib.md5(query.lower().strip().encode()).hexdigest()
    
    def get(self, query: str) -> Optional[Dict]:
        """
        Get cached research results from PostgreSQL (or file cache as fallback).
        
        NEW: Checks PostgreSQL database first for scalability.
        Falls back to file cache for backward compatibility.
        
        Args:
            query: Research query
            
        Returns:
            Cached results or None if not found/expired
        """
        # FIRST: Check PostgreSQL database (SCALABLE!)
        try:
            from utils.research_database import get_research_database
            db = get_research_database()
            
            similar_research = db.find_similar_research(query, limit=1)
            if similar_research:
                logging.info(f"[OK] Found research in PostgreSQL for: {query}")
                return similar_research[0]
        except Exception as e:
            logging.debug(f"PostgreSQL check failed, trying file cache: {e}")
        
        # FALLBACK: Check file cache
        cache_key = self._get_cache_key(query)
        
        if cache_key not in self.cache_index:
            return None
        
        cache_entry = self.cache_index[cache_key]
        cached_time = datetime.fromisoformat(cache_entry['timestamp'])
        
        # Check if expired
        if datetime.now() - cached_time > timedelta(days=self.ttl_days):
            # Expired - remove from cache
            del self.cache_index[cache_key]
            self._save_cache_index()
            return None
        
        # Load cached results
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
        if os.path.exists(cache_file):
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        return None
    
    def set(self, query: str, results: Dict):
        """
        Cache research results.
        
        Args:
            query: Research query
            results: Research results to cache
        """
        cache_key = self._get_cache_key(query)
        
        # Save results
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)
        
        # Update index
        self.cache_index[cache_key] = {
            'query': query,
            'timestamp': datetime.now().isoformat(),
            'file': cache_file
        }
        self._save_cache_index()


class WebSearcher:
    """Handles web searches across multiple providers with fallback."""
    
    def __init__(self):
        """Initialize web searcher with API keys from environment."""
        self.google_api_key = os.getenv("GOOGLE_SEARCH_API_KEY")
        self.google_cx = os.getenv("GOOGLE_SEARCH_CX")  # Custom Search Engine ID
        self.bing_api_key = os.getenv("BING_SEARCH_API_KEY")
        
        # Rate limiting
        self.daily_limit = int(os.getenv("RESEARCH_DAILY_LIMIT", "100"))
        self.search_count_file = ".research_cache/search_count.json"
        self.search_counts = self._load_search_counts()
        
        self.logger = logging.getLogger(__name__)
    
    def _load_search_counts(self) -> Dict:
        """Load search counts for rate limiting."""
        if os.path.exists(self.search_count_file):
            try:
                with open(self.search_count_file, 'r') as f:
                    counts = json.load(f)
                    # Reset if it's a new day
                    if counts.get('date') != datetime.now().date().isoformat():
                        return {'date': datetime.now().date().isoformat(), 'google': 0, 'bing': 0, 'duckduckgo': 0}
                    return counts
            except Exception:
                pass
        return {'date': datetime.now().date().isoformat(), 'google': 0, 'bing': 0, 'duckduckgo': 0}
    
    def _save_search_counts(self):
        """Save search counts."""
        os.makedirs(os.path.dirname(self.search_count_file), exist_ok=True)
        with open(self.search_count_file, 'w') as f:
            json.dump(self.search_counts, f, indent=2)
    
    def _increment_count(self, source: str):
        """Increment search count for rate limiting."""
        self.search_counts[source] = self.search_counts.get(source, 0) + 1
        self._save_search_counts()
    
    def _check_rate_limit(self, source: str) -> bool:
        """Check if rate limit exceeded."""
        return self.search_counts.get(source, 0) < self.daily_limit
    
    def search(self, query: str, num_results: int = 10) -> List[Dict]:
        """
        Search web using available providers with fallback.
        
        Args:
            query: Search query
            num_results: Number of results to return
            
        Returns:
            List of search results
        """
        self.logger.info(f"Searching for: '{query}' (requesting {num_results} results)")
        
        # Try Google first (if API key available and within limit)
        if self.google_api_key and self.google_cx:
            if self._check_rate_limit('google'):
                try:
                    self.logger.info("Attempting Google search...")
                    results = self._search_google(query, num_results)
                    if results:
                        self._increment_count('google')
                        self.logger.info(f"[OK] Google returned {len(results)} results")
                        return results
                    else:
                        self.logger.warning("Google returned 0 results")
                except Exception as e:
                    self.logger.warning(f"Google search failed: {e}")
            else:
                self.logger.info("Google rate limit reached, skipping")
        else:
            self.logger.info("Google API not configured, skipping")
        
        # Try Bing second (if API key available and within limit)
        if self.bing_api_key:
            if self._check_rate_limit('bing'):
                try:
                    self.logger.info("Attempting Bing search...")
                    results = self._search_bing(query, num_results)
                    if results:
                        self._increment_count('bing')
                        self.logger.info(f"[OK] Bing returned {len(results)} results")
                        return results
                    else:
                        self.logger.warning("Bing returned 0 results")
                except Exception as e:
                    self.logger.warning(f"Bing search failed: {e}")
            else:
                self.logger.info("Bing rate limit reached, skipping")
        else:
            self.logger.info("Bing API not configured, skipping")
        
        # Fallback to DuckDuckGo (free, no API key needed)
        if self._check_rate_limit('duckduckgo'):
            try:
                self.logger.info("Falling back to DuckDuckGo search (free, no API key)...")
                results = self._search_duckduckgo(query, num_results)
                if results:
                    self._increment_count('duckduckgo')
                    self.logger.info(f"[OK] DuckDuckGo returned {len(results)} results")
                    return results
                else:
                    self.logger.warning("DuckDuckGo returned 0 results")
            except Exception as e:
                self.logger.error(f"DuckDuckGo search failed: {e}", exc_info=True)
        else:
            self.logger.warning("DuckDuckGo rate limit reached")
        
        self.logger.error(f"[ERROR] All search providers failed or rate limited for query: '{query}'")
        return []
    
    async def _search_google_async(self, query: str, num_results: int) -> List[Dict]:
        """Search using Google Custom Search API (async)."""
        try:
            import httpx
        except ImportError:
            self.logger.warning("httpx not installed. Install with: pip install httpx")
            return []
        
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            'key': self.google_api_key,
            'cx': self.google_cx,
            'q': query,
            'num': min(num_results, 10)  # Google max 10 per request
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
        
        results = []
        for item in data.get('items', []):
            results.append({
                'title': item.get('title', ''),
                'url': item.get('link', ''),
                'snippet': item.get('snippet', ''),
                'source': 'google'
            })
        
        return results
    
    def _search_google(self, query: str, num_results: int) -> List[Dict]:
        """Search using Google Custom Search API (sync wrapper)."""
        try:
            return asyncio.run(self._search_google_async(query, num_results))
        except RuntimeError:
            # If event loop is already running, create a new one in a thread
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, self._search_google_async(query, num_results))
                return future.result(timeout=15)
    
    async def _search_bing_async(self, query: str, num_results: int) -> List[Dict]:
        """Search using Bing Search API (async)."""
        try:
            import httpx
        except ImportError:
            self.logger.warning("httpx not installed. Install with: pip install httpx")
            return []
        
        url = "https://api.bing.microsoft.com/v7.0/search"
        headers = {
            'Ocp-Apim-Subscription-Key': self.bing_api_key
        }
        params = {
            'q': query,
            'count': num_results,
            'responseFilter': 'Webpages'
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
        
        results = []
        for item in data.get('webPages', {}).get('value', []):
            results.append({
                'title': item.get('name', ''),
                'url': item.get('url', ''),
                'snippet': item.get('snippet', ''),
                'source': 'bing'
            })
        
        return results
    
    def _search_bing(self, query: str, num_results: int) -> List[Dict]:
        """Search using Bing Search API (sync wrapper)."""
        try:
            return asyncio.run(self._search_bing_async(query, num_results))
        except RuntimeError:
            # If event loop is already running, create a new one in a thread
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, self._search_bing_async(query, num_results))
                return future.result(timeout=15)
    
    def _search_duckduckgo(self, query: str, num_results: int) -> List[Dict]:
        """Search using DuckDuckGo (free, no API key)."""
        try:
            from duckduckgo_search import DDGS
        except ImportError:
            self.logger.warning("duckduckgo-search not installed. Install with: pip install duckduckgo-search")
            return []
        
        results = []
        max_retries = 3
        base_delay = 2.0  # seconds
        
        for attempt in range(max_retries):
            try:
                # Add delay between attempts to avoid rate limiting
                if attempt > 0:
                    delay = base_delay * (attempt + 1)  # Exponential backoff
                    self.logger.info(f"Retry attempt {attempt + 1}/{max_retries} after {delay}s delay...")
                    # Note: DuckDuckGo search is sync, so we use time.sleep here
                    # If this method becomes async, change to await asyncio.sleep(delay)
                    time.sleep(delay)
                
                # duckduckgo-search 4.x API with timeout and region
                ddgs = DDGS(timeout=20)  # Increased timeout
                
                # Add region parameter to help with rate limiting
                search_results = ddgs.text(
                    keywords=query,
                    region='wt-wt',  # Global region
                    safesearch='moderate',
                    max_results=num_results
                )
                
                # Handle both generator and list responses
                if search_results:
                    for item in search_results:
                        results.append({
                            'title': item.get('title', ''),
                            'url': item.get('href', item.get('link', '')),  # Try both 'href' and 'link'
                            'snippet': item.get('body', item.get('snippet', '')),  # Try both 'body' and 'snippet'
                            'source': 'duckduckgo'
                        })
                        
                        # Safety check - don't process more than requested
                        if len(results) >= num_results:
                            break
                
                if results:
                    self.logger.info(f"[OK] DuckDuckGo returned {len(results)} results for: {query}")
                    return results
                else:
                    self.logger.warning(f"DuckDuckGo returned 0 results on attempt {attempt + 1}")
                    
            except Exception as e:
                error_msg = str(e)
                
                # Check if it's a rate limit error
                if 'Ratelimit' in error_msg or 'ratelimit' in error_msg.lower():
                    self.logger.warning(f"DuckDuckGo rate limit hit on attempt {attempt + 1}/{max_retries}")
                    if attempt < max_retries - 1:
                        continue  # Retry
                    else:
                        self.logger.error("DuckDuckGo rate limit: All retries exhausted")
                        self.logger.info("[TIP] Wait a few minutes or configure Google/Bing API keys for better reliability")
                else:
                    self.logger.error(f"DuckDuckGo search error: {e}", exc_info=True)
                
                # If this was the last attempt, return empty
                if attempt == max_retries - 1:
                    return []
        
        return results


class ResearcherAgent(BaseAgent):
    """
    Agent responsible for conducting web research to assist other agents.
    
    Enhanced with LLM synthesis (Phase 2):
    - Intelligently synthesizes research findings
    - Extracts actionable insights and recommendations
    - Identifies patterns and best practices
    """
    
    def __init__(self, agent_id: str = "researcher_main", workspace_path: str = ".",
                 project_layout: Optional[ProjectLayout] = None,
                 project_id: Optional[str] = None,
                 tenant_id: Optional[int] = None,
                 orchestrator: Optional[Any] = None):
        # CRITICAL: Pass workspace_path to super() to ensure BaseAgent validates it
        super().__init__(
            agent_id, 
            AgentType.RESEARCHER, 
            project_layout, 
            workspace_path=workspace_path,
            project_id=project_id, 
            tenant_id=tenant_id, 
            orchestrator=orchestrator
        )
        self.research_files: List[str] = []
        self.project_id = project_id
        
        # Initialize research cache (shared across projects)
        cache_dir = os.path.expanduser("~/.quickodoo/research_cache")
        self.cache = ResearchCache(cache_dir, ttl_days=90)
        
        # Initialize web searcher
        self.searcher = WebSearcher()
        
        # Research directory for this project
        self.research_dir = os.path.join(workspace_path, "research")
        os.makedirs(self.research_dir, exist_ok=True)
        
        # Track research requests
        self.research_requests: Dict[str, Dict] = {}
        
        # LLM Integration (Phase 2 - November 2025)
        self.use_llm = os.getenv("Q2O_USE_LLM", "true").lower() == "true"
        
        if LLM_INTEGRATION_AVAILABLE and self.use_llm:
            self.llm_service = get_llm_service()
            self.config_manager = get_configuration_manager()
            self.llm_enabled = True
            logging.info("[OK] ResearcherAgent: LLM synthesis enabled")
        else:
            self.llm_service = None
            self.config_manager = None
            self.llm_enabled = False
            if self.use_llm:
                logging.warning("[WARNING] ResearcherAgent: LLM requested but not available, basic synthesis only")
            else:
                logging.info("[INFO] ResearcherAgent: LLM disabled, basic synthesis only")
        
        # Subscribe to research channel for agent requests
        if hasattr(self, 'message_broker') and self.message_broker:
            def research_request_handler(msg):
                self._handle_research_request_message(msg)
            self.message_broker.subscribe("research", research_request_handler)
            self.logger.info("ResearcherAgent subscribed to research channel")
    
    def process_task(self, task: Task) -> Task:
        """
        Process a research task by conducting web research.
        
        Args:
            task: The research task to process
            
        Returns:
            The updated task with research results
        """
        try:
            self.logger.info(f"Processing research task: {task.title}")
            
            # Extract research query
            query = self._extract_research_query(task)
            
            # Check cache first
            cached_results = self.cache.get(query)
            if cached_results:
                self.logger.info(f"Using cached research for: {query}")
                research_results = cached_results
                research_results['cached'] = True
            else:
                # Conduct new research
                research_results = self._conduct_research(query, task)
                
                # Cache results
                self.cache.set(query, research_results)
                research_results['cached'] = False
            
            # Save research (PostgreSQL + files for backup)
            # Returns research_id (UUID) - already stored in PostgreSQL by _save_research_results
            research_id = self._save_research_results(query, research_results, task)
            
            # Prepare results for other agents
            task.metadata["research_results"] = research_results
            task.metadata["research_id"] = research_id  # Database ID (primary)
            task.metadata["global_research_id"] = research_id  # Backward compatibility
            task.metadata["research_query"] = query
            
            task.result = {
                "query": query,
                "research_id": research_id,  # Database ID
                "results_count": len(research_results.get('search_results', [])),
                "confidence_score": research_results.get('confidence_score', 0),
                "key_findings": research_results.get('key_findings', []),
                "status": "completed",
                "cached": research_results['cached']
            }
            
            # Broadcast research completion via message broker
            self._broadcast_research_complete(query, research_results, task)
            
            # QA_Engineer: Pass task object to complete_task for status synchronization (Solution 3)
            completed_task = self.complete_task(task.id, task.result, task=task)
            # Ensure task status is synchronized
            if completed_task:
                task.status = completed_task.status
                task.result = completed_task.result
            self.logger.info(f"Completed research task {task.id}")
            
        except Exception as e:
            error_msg = f"Error processing research task: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            # QA_Engineer: Pass task object to fail_task for status synchronization (Solution 3)
            failed_task = self.fail_task(task.id, error_msg, task=task)
            # Ensure task status is synchronized
            if failed_task:
                task.status = failed_task.status
                task.error = failed_task.error
        
        return task
    
    def _extract_research_query(self, task: Task) -> str:
        """
        Extract research query from task.
        
        CRITICAL FIX: Removes instructions and extracts actual research topic.
        
        Args:
            task: The research task
            
        Returns:
            Research query string (actual topic, not instructions)
        """
        # Check if explicitly provided
        if task.metadata.get("research_query"):
            query = task.metadata["research_query"]
            # Clean up if it contains instructions
            query = self._clean_research_query(query)
            return query
        
        # Extract from description
        description = task.description
        
        # Look for research patterns
        patterns = [
            r'research:\s*(.+?)(?:\n|$)',
            r'find information about:\s*(.+?)(?:\n|$)',
            r'learn about:\s*(.+?)(?:\n|$)',
            r'conduct.*research.*for:\s*(.+?)(?:\n|$)',
            r'research.*topic:\s*(.+?)(?:\n|$)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                query = match.group(1).strip()
                # Clean up if it contains instructions
                query = self._clean_research_query(query)
                return query
        
        # Fallback to objective or title, but clean it
        fallback = task.metadata.get("objective", task.title)
        return self._clean_research_query(fallback)
    
    def _clean_research_query(self, query: str) -> str:
        """
        Clean research query by removing instructions and extracting actual topic.
        
        Args:
            query: Raw query that may contain instructions
            
        Returns:
            Cleaned research topic
        """
        if not query:
            return query
        
        # Remove common instruction patterns
        instruction_patterns = [
            r'Follow every requirement below strictly\.?\s*',
            r'Produce outputs that are detailed, actionable.*?\.\s*',
            r'Do not skip or summarize sections unless instructed\.\s*',
            r'Include code, diagrams, and deployment plans\.\s*',
            r'Be architecturally sound, multistep\.\s*',
        ]
        
        cleaned = query
        for pattern in instruction_patterns:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE | re.DOTALL)
        
        # If query starts with instructions, try to find the actual topic
        # Look for patterns like "Research: <topic>" or "Topic: <topic>"
        topic_patterns = [
            r'(?:research|topic|subject|about):\s*(.+?)(?:\n|$)',
            r'research\s+(?:on|about|for)\s+(.+?)(?:\n|$)',
        ]
        
        for pattern in topic_patterns:
            match = re.search(pattern, cleaned, re.IGNORECASE)
            if match:
                cleaned = match.group(1).strip()
                break
        
        # Remove leading/trailing whitespace and newlines
        cleaned = cleaned.strip()
        
        # If cleaned query is too short or still looks like instructions, use original
        if len(cleaned) < 10 or cleaned.lower().startswith(('follow', 'produce', 'do not', 'include')):
            # Try to extract from context - look for the actual objective
            # Split by common separators and take the first substantial part
            parts = re.split(r'[.\n]', query)
            for part in parts:
                part = part.strip()
                if len(part) > 20 and not part.lower().startswith(('follow', 'produce', 'do not', 'include', 'be thorough')):
                    return part
        
        return cleaned if cleaned else query
    
    def _conduct_research(self, query: str, task: Task) -> Dict[str, Any]:
        """
        Conduct comprehensive research using LLM FIRST, then search as fallback.
        
        Priority:
        1. LLM research (tries all 3 providers with multiple models, 3 retries per model)
        2. Web search (only if ALL LLM attempts fail)
        
        Args:
            query: Research query
            task: The research task
            
        Returns:
            Research results dictionary
        """
        self.logger.info(f"Conducting research for: {query}")
        
        # Determine research depth
        depth = self._determine_research_depth(task)
        
        research_results = {
            'query': query,
            'timestamp': datetime.now().isoformat(),
            'depth': depth,
            'search_results': [],
            'key_findings': [],
            'documentation_urls': [],
            'code_examples': [],
            'best_practices': [],
            'confidence_score': 0,
            'sources_consulted': []
        }
        
        # PHASE 1: Try LLM FIRST with full fallback (3 providers, multiple models per provider, 3 retries per model)
        self.logger.info(f"Phase 1: Attempting LLM research (will try all 3 providers with multiple models and retries)...")
        llm_results = self._conduct_research_with_llm(query, task, depth)
        
        if llm_results:
            # LLM research succeeded - use it as primary source
            self.logger.info(f"[SUCCESS] LLM research completed successfully - using LLM results as primary source")
            research_results.update(llm_results)
            research_results['sources_consulted'].insert(0, 'llm_research_primary')  # Mark as primary source
            
            # Phase 2: Synthesize and validate LLM findings
            key_findings = self._synthesize_findings(research_results, query, task)
            research_results['key_findings'] = key_findings
            
            # Phase 3: Quality validation and confidence scoring
            confidence = self._calculate_confidence_score(research_results)
            research_results['confidence_score'] = confidence
            
            return research_results
        
        # PHASE 2: LLM failed - Fall back to web search as last resort
        self.logger.warning(f"[FALLBACK] All LLM attempts failed - falling back to web search as last resort")
        self.logger.info(f"Phase 2 (Fallback): Starting web search research...")
        
        # Quick search (top results)
        initial_results = 10 if depth == 'comprehensive' else 5
        quick_results = self.searcher.search(query, num_results=initial_results)
        research_results['search_results'].extend(quick_results)
        research_results['sources_consulted'].append('web_search_fallback')
        self.logger.info(f"Phase 2: Retrieved {len(quick_results)} initial search results")
        
        # Deep search if needed
        if depth in ['deep', 'adaptive', 'comprehensive']:
            # Search for specific aspects
            deep_queries = self._generate_deep_queries(query, task)
            deep_results_per_query = 5 if depth == 'comprehensive' else 3
            
            self.logger.info(f"Phase 2b: Conducting {len(deep_queries)} deep searches...")
            for deep_query in deep_queries:
                results = self.searcher.search(deep_query, num_results=deep_results_per_query)
                research_results['search_results'].extend(results)
                self.logger.debug(f"  Deep query '{deep_query[:50]}...' returned {len(results)} results")
            
            research_results['sources_consulted'].append('deep_search_fallback')
            self.logger.info(f"Phase 2b: Retrieved {len(research_results['search_results']) - len(quick_results)} additional results from deep search")
        
        # Phase 3: Extract documentation and code examples
        self.logger.info(f"Phase 3: Extracting official documentation...")
        official_docs = self._find_official_documentation(research_results['search_results'], query)
        research_results['documentation_urls'] = official_docs
        self.logger.info(f"Phase 3: Found {len(official_docs)} official documentation sources")
        
        # Phase 4: Recursive research (scrape content and follow links)
        if depth in ['deep', 'comprehensive']:
            self.logger.info(f"Phase 4: Starting recursive research (multi-level link following)...")
            
            # Use recursive researcher for deep content discovery
            try:
                from utils.recursive_researcher import RecursiveResearcher
                
                # Detect platform from query
                platform = self._detect_platform_from_query(query)
                
                # Configure recursion depth
                recursion_depth = 2 if depth == 'comprehensive' else 1
                
                researcher = RecursiveResearcher(
                    max_depth=recursion_depth,
                    max_links_per_page=10,
                    request_timeout=10
                )
                
                # Build focus keywords
                focus_keywords = ['api', 'documentation', 'reference', 'sdk', 'guide', 'examples']
                if platform:
                    focus_keywords.extend([platform, 'authentication', 'entities', 'data model'])
                
                # Perform recursive research
                recursive_data = researcher.recursive_research(
                    research_results['search_results'],
                    focus_keywords
                )
                
                # Merge results
                research_results['scraped_content'] = {
                    **recursive_data.get('level_1_content', {}),
                    **recursive_data.get('level_2_content', {})
                }
                research_results['code_examples'] = recursive_data.get('code_examples', [])
                research_results['api_endpoints'] = recursive_data.get('api_endpoints', [])
                research_results['github_repos'] = recursive_data.get('github_repos', [])
                research_results['discovered_links'] = recursive_data.get('discovered_links', [])
                research_results['sources_consulted'].append('recursive_research_fallback')
                
                self.logger.info(f"Phase 4: Recursive research complete - "
                               f"{recursive_data.get('total_pages_scraped', 0)} pages scraped, "
                               f"{len(research_results['code_examples'])} code examples, "
                               f"{len(research_results['api_endpoints'])} API endpoints discovered")
                
            except Exception as e:
                self.logger.warning(f"Recursive research failed, falling back to simple scraping: {e}")
                
                # Fallback to simple scraping
                scrape_count = 10 if depth == 'comprehensive' else 5
                scraped_content = self._scrape_top_results(research_results['search_results'][:scrape_count])
                research_results['scraped_content'] = scraped_content
                
                # Extract code examples
                code_examples = self._extract_code_examples(scraped_content)
                research_results['code_examples'] = code_examples
                research_results['sources_consulted'].append('content_scraping_fallback')
                self.logger.info(f"Phase 4 (fallback): Extracted {len(code_examples)} code examples from {len(scraped_content)} pages")
        
        # Phase 5: Synthesize findings
        key_findings = self._synthesize_findings(research_results, query, task)
        research_results['key_findings'] = key_findings
        
        # Phase 6: Quality validation and confidence scoring
        confidence = self._calculate_confidence_score(research_results)
        research_results['confidence_score'] = confidence
        
        return research_results
    
    def _conduct_research_with_llm(self, query: str, task: Task, depth: str) -> Optional[Dict[str, Any]]:
        """
        Conduct research using LLM as PRIMARY method.
        
        This method uses LLM to provide comprehensive research in a single call,
        including documentation URLs, code examples, best practices, and insights.
        
        Args:
            query: Research query
            task: The research task
            depth: Research depth level
            
        Returns:
            Research results dictionary or None if LLM fails
        """
        if not self.llm_service:
            return None
        
        try:
            # Check if we're already in async context
            try:
                loop = asyncio.get_running_loop()
                # Already in async - need to handle differently
                self.logger.warning("[LLM] Already in async context, cannot use LLM research synchronously")
                return None
            except RuntimeError:
                # No running loop - safe to create new one
                # Windows compatibility: Use SelectorEventLoop for psycopg async
                loop = create_compatible_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    llm_results = loop.run_until_complete(
                        self._conduct_research_with_llm_async(query, task, depth)
                    )
                    # CRITICAL: Wait for all pending tasks to complete before closing loop
                    pending = asyncio.all_tasks(loop)
                    if pending:
                        loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                    return llm_results
                finally:
                    # Only close loop after all tasks are complete
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
        except Exception as e:
            self.logger.error(f"[LLM] Error in LLM research: {e}", exc_info=True)
            return None
    
    async def _conduct_research_with_llm_async(self, query: str, task: Task, depth: str) -> Optional[Dict[str, Any]]:
        """
        Async method to conduct research using LLM.
        
        Args:
            query: Research query
            task: The research task
            depth: Research depth level
            
        Returns:
            Research results dictionary or None if LLM fails
        """
        if not self.llm_service:
            return None
        
        # Build comprehensive LLM prompt for research
        system_prompt = """You are an expert software researcher and technical analyst.

Your task: Provide comprehensive research on a given topic, including:
1. Key findings and insights (5-10 actionable points)
2. Official documentation URLs (prioritize official sources)
3. Code examples (if applicable, in the requested language/framework)
4. Best practices and recommendations
5. Common pitfalls to avoid
6. Implementation patterns and approaches
7. Integration requirements (APIs, authentication, data formats)
8. Performance and security considerations

Return your research as JSON:
{
  "key_findings": [
    "Finding 1: Specific, actionable insight",
    "Finding 2: Another specific insight",
    ...
  ],
  "documentation_urls": [
    "https://official-docs.com/api",
    "https://developer.example.com/guide",
    ...
  ],
  "code_examples": [
    {
      "language": "python",
      "description": "Example: API authentication",
      "code": "import requests\\n\\ndef authenticate():\\n    ..."
    },
    ...
  ],
  "best_practices": [
    "Practice 1: Specific recommendation",
    "Practice 2: Another recommendation",
    ...
  ],
  "common_pitfalls": [
    "Pitfall 1: What to avoid and why",
    "Pitfall 2: Another common mistake",
    ...
  ],
  "implementation_patterns": [
    "Pattern 1: Description of approach",
    "Pattern 2: Alternative approach",
    ...
  ],
  "integration_requirements": {
    "authentication": "OAuth 2.0, API keys, etc.",
    "apis_required": ["API 1", "API 2"],
    "data_formats": ["JSON", "XML"]
  },
  "performance_considerations": [
    "Consideration 1: Performance tip",
    ...
  ],
  "security_considerations": [
    "Security tip 1: What to secure",
    ...
  ]
}

Be specific, accurate, and actionable. Focus on what developers NEED to know."""
        
        # Build user prompt with FULL context: System Prompt + Project Objectives + Agent Prompts + Research Topic
        tech_stack = task.tech_stack or []
        tech_context = f"Tech Stack: {', '.join(tech_stack)}" if tech_stack else "No specific tech stack"
        
        # CRITICAL FIX: Extract clean research topic (WHAT to research)
        # But keep full objective for context (HOW to research, WHAT format/output)
        clean_research_topic = query
        if not query or len(query) < 10 or query.lower().startswith(('follow', 'produce', 'do not')):
            # Try to get actual research topic from task objective
            actual_objective = task.metadata.get("objective", "")
            if actual_objective and actual_objective != query:
                # Extract first sentence or meaningful phrase from objective
                objective_parts = re.split(r'[.\n]', actual_objective)
                for part in objective_parts:
                    part = part.strip()
                    if len(part) > 20 and not part.lower().startswith(('follow', 'produce', 'do not', 'include')):
                        clean_research_topic = part
                        break
                if not clean_research_topic or len(clean_research_topic) < 10:
                    clean_research_topic = actual_objective[:200]  # Use first 200 chars of objective
        
        # Get FULL project objective (contains instructions on HOW to research)
        full_objective = task.metadata.get("objective", "")
        task_description = task.description or ""
        
        # Get agent-specific prompts if available
        agent_prompt = ""
        if LLM_INTEGRATION_AVAILABLE:
            try:
                config_manager = get_configuration_manager()
                if config_manager:
                    # Get agent-specific prompt for this project
                    _, user_prompt_template = config_manager.get_prompt_for_task(
                        project_id=self.project_id,
                        agent_type=self.agent_type,
                        task_description=task_description,
                        tech_stack=tech_stack
                    )
                    if user_prompt_template and user_prompt_template != task_description:
                        agent_prompt = user_prompt_template
            except Exception as e:
                self.logger.debug(f"Could not get agent prompt: {e}")
        
        # Build comprehensive user prompt with ALL context
        user_prompt_parts = [
            f"Research Topic: {clean_research_topic}",
            "",
            "Context:",
            f"Tech Stack: {tech_context}",
            f"Task Complexity: {task.metadata.get('complexity', 'medium')}",
            f"Research Depth: {depth}",
        ]
        
        # Add project objective if available (contains important instructions)
        if full_objective and full_objective != clean_research_topic:
            user_prompt_parts.extend([
                "",
                "Project Objectives and Requirements:",
                full_objective
            ])
        
        # Add task description if it contains additional context
        if task_description and task_description != full_objective:
            user_prompt_parts.extend([
                "",
                "Task Description:",
                task_description
            ])
        
        # Add agent-specific prompt if available
        if agent_prompt:
            user_prompt_parts.extend([
                "",
                "Agent-Specific Instructions:",
                agent_prompt
            ])
        
        user_prompt_parts.extend([
            "",
            "Please provide comprehensive research on the topic above. Include:",
            "- Official documentation URLs (verify these are real, official sources)",
            "- Code examples in the relevant language/framework",
            "- Best practices specific to this technology",
            "- Implementation patterns and approaches",
            "- Integration requirements",
            "- Performance and security considerations",
            "",
            "Be thorough and specific. This research will be used to implement the solution."
        ])
        
        user_prompt = "\n".join(user_prompt_parts)
        
        # Generate research with LLM
        self.logger.info(f"[LLM] Requesting comprehensive research from LLM...")
        response = await self.llm_service.complete(
            system_prompt,
            user_prompt,
            temperature=0.3,  # Lower temperature for factual research
            max_tokens=4096  # Allow comprehensive responses
        )
        
        if not response.success:
            self.logger.warning(f"[LLM] LLM research failed: {response.error}")
            if hasattr(response, 'attempts'):
                self.logger.warning(f"[LLM] Attempts made: {response.attempts}")
            return None
        
        # Log LLM usage
        if response.usage:
            self.logger.info(
                f"[COST] LLM research cost: ${response.usage.total_cost:.4f} "
                f"({response.usage.input_tokens}+{response.usage.output_tokens} tokens, "
                f"provider: {response.provider})"
            )
        
        # CRITICAL FIX: Track LLM usage for dashboard
        self.track_llm_usage(task, response)
        
        # Parse JSON response with robust parsing
        try:
            from utils.json_parser import parse_json_robust
            
            # Use robust JSON parser to handle malformed responses
            result = parse_json_robust(
                response.content,
                required_fields=['key_findings']  # At minimum, we need findings
            )
            
            if not result:
                # Fall back to text parsing
                self.logger.warning("[LLM] JSON parsing failed, attempting text extraction")
                return self._parse_llm_research_from_text(response.content, query, depth)
            
            # Build research results structure
            research_results = {
                'query': query,
                'timestamp': datetime.now().isoformat(),
                'depth': depth,
                'search_results': [],  # Empty for LLM research
                'key_findings': result.get('key_findings', []),
                'documentation_urls': result.get('documentation_urls', []),
                'code_examples': result.get('code_examples', []),
                'best_practices': result.get('best_practices', []),
                'common_pitfalls': result.get('common_pitfalls', []),
                'implementation_patterns': result.get('implementation_patterns', []),
                'integration_requirements': result.get('integration_requirements', {}),
                'performance_considerations': result.get('performance_considerations', []),
                'security_considerations': result.get('security_considerations', []),
                'confidence_score': 95,  # High confidence for LLM research
                'sources_consulted': ['llm_research'],
                'llm_provider': response.provider,
                'llm_model': response.model
            }
            
            self.logger.info(
                f"[LLM] LLM research completed: {len(research_results['key_findings'])} findings, "
                f"{len(research_results['documentation_urls'])} docs, "
                f"{len(research_results['code_examples'])} code examples"
            )
            
            return research_results
            
        except Exception as e:
            self.logger.error(f"[LLM] Error processing LLM research: {e}", exc_info=True)
            # Try to extract structured information from plain text as fallback
            return self._parse_llm_research_from_text(response.content, query, depth)
    
    def _parse_llm_research_from_text(self, content: str, query: str, depth: str) -> Dict[str, Any]:
        """
        Parse LLM research from plain text if JSON parsing fails.
        
        Args:
            content: LLM response text
            query: Original query
            depth: Research depth
            
        Returns:
            Research results dictionary
        """
        research_results = {
            'query': query,
            'timestamp': datetime.now().isoformat(),
            'depth': depth,
            'search_results': [],
            'key_findings': [],
            'documentation_urls': [],
            'code_examples': [],
            'best_practices': [],
            'confidence_score': 80,  # Lower confidence for text parsing
            'sources_consulted': ['llm_research_text']
        }
        
        # Extract URLs
        url_pattern = r'https?://[^\s\)]+'
        urls = re.findall(url_pattern, content)
        research_results['documentation_urls'] = list(set(urls[:10]))  # Limit to 10 unique URLs
        
        # Extract findings (lines that look like insights)
        lines = content.split('\n')
        findings = []
        for line in lines:
            line = line.strip()
            # Look for lines that are insights (not headers, not too short, not URLs)
            if (len(line) > 30 and 
                not line.startswith('#') and 
                not line.startswith('http') and
                not line.startswith('*') and
                ':' in line):  # Usually insights have colons
                findings.append(line)
        
        research_results['key_findings'] = findings[:10]  # Top 10 findings
        
        # Extract code blocks
        code_pattern = r'```(\w+)?\n(.*?)```'
        code_matches = re.findall(code_pattern, content, re.DOTALL)
        for lang, code in code_matches:
            if len(code.strip()) > 20:  # Meaningful code blocks
                research_results['code_examples'].append({
                    'language': lang or 'unknown',
                    'description': 'Code example from LLM research',
                    'code': code.strip()[:1000]  # Limit length
                })
        
        self.logger.info(f"[LLM] Parsed text research: {len(findings)} findings, {len(urls)} URLs, {len(code_matches)} code examples")
        
        return research_results
    
    def _detect_platform_from_query(self, query: str) -> Optional[str]:
        """
        Detect platform name from research query.
        
        Args:
            query: Research query
            
        Returns:
            Platform name or None
        """
        query_lower = query.lower()
        
        platforms = {
            'sage': 'SAGE',
            'quickbooks': 'QuickBooks',
            'qbo': 'QuickBooks',
            'xero': 'Xero',
            'netsuite': 'NetSuite',
            'wave': 'Wave',
            'stripe': 'Stripe',
            'freshbooks': 'FreshBooks',
            'zoho': 'Zoho Books'
        }
        
        for keyword, platform_name in platforms.items():
            if keyword in query_lower:
                return platform_name
        
        return None
    
    def _determine_research_depth(self, task: Task) -> str:
        """
        Determine how deep the research should be.
        
        Args:
            task: The research task
            
        Returns:
            Depth level: 'quick', 'deep', 'comprehensive', 'adaptive'
        """
        complexity = task.metadata.get("complexity", "medium")
        
        # Explicit depth request
        if task.metadata.get("research_depth"):
            return task.metadata["research_depth"]
        
        # Adaptive based on complexity
        if complexity == "low":
            return "quick"
        elif complexity == "medium":
            return "deep"
        else:  # high complexity
            return "comprehensive"
    
    def _generate_deep_queries(self, base_query: str, task: Task) -> List[str]:
        """
        Generate additional queries for deep research.
        
        Args:
            base_query: Base research query
            task: The research task
            
        Returns:
            List of additional queries
        """
        queries = []
        tech_stack = task.tech_stack or []
        query_lower = base_query.lower()
        
        # Detect if this is a migration/platform research
        is_migration = any(kw in query_lower for kw in ['migration', 'platform', 'api', 'integration'])
        is_platform_specific = any(kw in query_lower for kw in ['sage', 'quickbooks', 'xero', 'netsuite', 'wave'])
        
        # Add tech-stack specific queries
        for tech in tech_stack:
            queries.append(f"{base_query} {tech} tutorial")
        
        # Add migration-specific deep queries
        if is_migration:
            queries.extend([
                f"{base_query} API documentation",
                f"{base_query} authentication guide",
                f"{base_query} code examples Python",
                f"{base_query} best practices",
                f"{base_query} entity types data model"
            ])
        
        # Add platform-specific deep queries
        if is_platform_specific:
            # Extract platform name
            for platform in ['sage', 'quickbooks', 'xero', 'netsuite', 'wave', 'stripe']:
                if platform in query_lower:
                    queries.extend([
                        f"{platform} API reference",
                        f"{platform} API entities",
                        f"{platform} OAuth 2.0 setup",
                        f"{platform} REST API examples",
                        f"{platform} data export"
                    ])
                    break
            queries.append(f"{base_query} {tech} best practices")
        
        # Add specific aspect queries
        queries.append(f"{base_query} documentation")
        queries.append(f"{base_query} code examples")
        queries.append(f"{base_query} latest version")
        
        return queries[:5]  # Limit to 5 additional queries
    
    def _find_official_documentation(self, search_results: List[Dict], query: str) -> List[str]:
        """
        Identify official documentation URLs from search results.
        
        Args:
            search_results: List of search results
            query: Original query
            
        Returns:
            List of official documentation URLs
        """
        official_docs = []
        
        # Patterns for official documentation
        official_patterns = [
            r'\.readthedocs\.io',
            r'docs\..*\.com',
            r'developer\..*\.com',
            r'api\..*\.com/docs',
            r'github\.com.*/(wiki|docs)',
            r'\.org/docs',
        ]
        
        # Keywords indicating official docs
        official_keywords = ['documentation', 'docs', 'api reference', 'developer guide', 'official']
        
        for result in search_results:
            url = result.get('url', '')
            title = result.get('title', '').lower()
            snippet = result.get('snippet', '').lower()
            
            # Check if URL matches official patterns
            is_official = any(re.search(pattern, url, re.IGNORECASE) for pattern in official_patterns)
            
            # Check if title/snippet indicates official docs
            has_official_keywords = any(keyword in title or keyword in snippet for keyword in official_keywords)
            
            if is_official or has_official_keywords:
                official_docs.append(url)
        
        return official_docs[:5]  # Top 5 official docs
    
    def _scrape_top_results(self, search_results: List[Dict]) -> List[Dict]:
        """
        Scrape content from top search results.
        
        Args:
            search_results: List of search results
            
        Returns:
            List of scraped content
        """
        scraped = []
        
        try:
            import httpx
            from bs4 import BeautifulSoup
        except ImportError:
            self.logger.warning("httpx or beautifulsoup4 not installed. Skipping content scraping.")
            return []
        
        # Use async HTTP for concurrent scraping
        async def scrape_url(result: Dict) -> Optional[Dict]:
            """Scrape a single URL asynchronously."""
            try:
                url = result.get('url', '')
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get(url, headers={
                        'User-Agent': 'QuickOdoo-ResearchAgent/1.0'
                    })
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content, 'html.parser')
                        
                        # Extract text content
                        # Remove scripts and styles
                        for script in soup(['script', 'style']):
                            script.decompose()
                        
                        text = soup.get_text()
                        lines = (line.strip() for line in text.splitlines())
                        text = '\n'.join(line for line in lines if line)
                        
                        return {
                            'url': url,
                            'title': result.get('title', ''),
                            'content': text[:5000],  # Limit to 5000 chars
                            'word_count': len(text.split())
                        }
            except Exception as e:
                self.logger.warning(f"Error scraping {result.get('url', 'unknown')}: {e}")
                return None
        
        # Scrape URLs concurrently
        async def scrape_all():
            tasks = [scrape_url(result) for result in search_results[:5]]  # Top 5 only
            results = await asyncio.gather(*tasks, return_exceptions=True)
            return [r for r in results if r is not None and not isinstance(r, Exception)]
        
        # Run async scraping
        try:
            scraped = asyncio.run(scrape_all())
        except RuntimeError:
            # If event loop is already running, create a new one in a thread
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, scrape_all())
                scraped = future.result(timeout=60)  # Longer timeout for multiple requests
        
        return scraped
    
    def _extract_code_examples(self, scraped_content: List[Dict]) -> List[Dict]:
        """
        Extract code examples from scraped content.
        
        Args:
            scraped_content: List of scraped content
            
        Returns:
            List of code examples
        """
        code_examples = []
        
        # Simple code block detection
        code_patterns = [
            r'```(.*?)```',  # Markdown code blocks
            r'<code>(.*?)</code>',  # HTML code tags
            r'<pre>(.*?)</pre>',  # HTML pre tags
        ]
        
        for content_item in scraped_content:
            content = content_item['content']
            
            for pattern in code_patterns:
                matches = re.findall(pattern, content, re.DOTALL)
                for match in matches:
                    if len(match) > 20:  # Filter out tiny snippets
                        code_examples.append({
                            'code': match.strip()[:1000],  # Limit length
                            'source_url': content_item['url'],
                            'source_title': content_item['title']
                        })
        
        return code_examples[:10]  # Top 10 examples
    
    def _synthesize_findings(self, research_results: Dict, query: str, task: Optional[Task] = None) -> List[str]:
        """
        Synthesize key findings from research (ENHANCED with LLM).
        
        Uses LLM to intelligently analyze and synthesize research findings.
        Falls back to basic synthesis if LLM unavailable.
        
        Args:
            research_results: Research results
            query: Original query
            task: Optional task object for LLM usage tracking
            
        Returns:
            List of key findings
        """
        # Try LLM synthesis first (if enabled)
        if self.llm_enabled:
            try:
                # Check if we're already in async context
                try:
                    loop = asyncio.get_running_loop()
                    # Already in async - fall back to basic synthesis to avoid conflicts
                    self.logger.warning("Already in async context, using basic synthesis")
                    return self._synthesize_findings_basic(research_results, query)
                except RuntimeError:
                    # No running loop - safe to create new one
                    # Windows compatibility: Use SelectorEventLoop for psycopg async
                    loop = create_compatible_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        llm_findings = loop.run_until_complete(
                            self._synthesize_findings_with_llm(research_results, query, task)
                        )
                        # CRITICAL: Wait for all pending tasks to complete before closing loop
                        pending = asyncio.all_tasks(loop)
                        if pending:
                            loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                        if llm_findings:
                            self.logger.info(f"[LLM] LLM synthesis: {len(llm_findings)} insights generated")
                            return llm_findings
                    finally:
                        # Only close loop after all tasks are complete
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
            except Exception as e:
                self.logger.warning(f"LLM synthesis failed, using basic synthesis: {e}")
        
        # Fallback to basic synthesis
        return self._synthesize_findings_basic(research_results, query)
    
    async def _synthesize_findings_with_llm(self, research_results: Dict, query: str, task: Optional[Task] = None) -> List[str]:
        """
        Use LLM to intelligently synthesize research findings.
        
        This is WHERE THE MAGIC HAPPENS - LLM reads all research and extracts
        actionable insights, patterns, best practices, and recommendations.
        
        Args:
            research_results: Research results with search results, docs, code examples
            query: Original research query
        
        Returns:
            List of synthesized insights (5-10 actionable findings)
        """
        if not self.llm_service:
            return []
        
        # Prepare research data for LLM
        search_snippets = []
        for idx, result in enumerate(research_results.get('search_results', [])[:10], 1):
            search_snippets.append(f"{idx}. {result.get('title', 'Untitled')}\n   {result.get('snippet', '')}\n   Source: {result.get('url', '')}")
        
        docs_list = research_results.get('documentation_urls', [])
        code_examples_list = research_results.get('code_examples', [])
        
        # Build comprehensive prompt
        system_prompt = """You are a senior software architect analyzing research findings.

Your task: Synthesize research results into actionable insights for developers.

Extract:
1. Key capabilities and features
2. Best practices and recommended approaches
3. Common pitfalls and gotchas to avoid
4. Implementation patterns
5. Integration requirements (auth, APIs, data formats)
6. Performance and security considerations

Return 5-10 concise, actionable insights as a JSON array:
{
  "insights": [
    "Insight 1: Brief, specific, actionable finding",
    "Insight 2: Another finding with specifics",
    ...
  ]
}

Be specific. Avoid vague statements. Focus on what developers NEED to know."""
        
        user_prompt = f"""Research Query: {query}

Search Results:
{chr(10).join(search_snippets)}

Official Documentation: {len(docs_list)} sources found
{chr(10).join([f"- {url}" for url in docs_list[:5]])}

Code Examples Found: {len(code_examples_list)}

Please synthesize these findings into 5-10 actionable insights."""
        
        # Generate synthesis with LLM
        response = await self.llm_service.complete(
            system_prompt,
            user_prompt,
            temperature=0.3,  # Lower for analytical synthesis
            max_tokens=1024
        )
        
        if not response.success:
            self.logger.warning(f"LLM synthesis failed: {response.error}")
            return []
        
        # CRITICAL: Track LLM usage for dashboard
        if task:
            self.track_llm_usage(task, response)
        
        # Parse JSON response
        try:
            import json
            content = response.content
            
            # Extract JSON if wrapped in markdown
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            result = json.loads(content.strip())
            insights = result.get('insights', [])
            
            # Log LLM usage
            if response.usage:
                self.logger.info(
                    f"[COST] LLM synthesis cost: ${response.usage.total_cost:.4f} "
                    f"({response.usage.input_tokens}+{response.usage.output_tokens} tokens)"
                )
            
            return insights
            
        except Exception as e:
            self.logger.error(f"Failed to parse LLM synthesis: {e}")
            # Try to extract insights from plain text if JSON parsing fails
            lines = response.content.split('\n')
            insights = [line.strip() for line in lines if line.strip() and len(line.strip()) > 20]
            return insights[:10] if insights else []
    
    def _synthesize_findings_basic(self, research_results: Dict, query: str) -> List[str]:
        """
        Basic synthesis (fallback when LLM unavailable).
        
        Simple keyword-based analysis.
        
        Args:
            research_results: Research results
            query: Original query
            
        Returns:
            List of basic findings
        """
        findings = []
        
        # Extract common themes from snippets
        snippets = [r['snippet'] for r in research_results['search_results']]
        
        # Count important terms
        important_terms = {}
        for snippet in snippets:
            words = snippet.lower().split()
            for word in words:
                if len(word) > 4:  # Meaningful words only
                    important_terms[word] = important_terms.get(word, 0) + 1
        
        # Find most mentioned terms
        top_terms = sorted(important_terms.items(), key=lambda x: x[1], reverse=True)[:5]
        
        if top_terms:
            findings.append(f"Most mentioned concepts: {', '.join([t[0] for t in top_terms])}")
        
        # Count official documentation
        if research_results['documentation_urls']:
            findings.append(f"Found {len(research_results['documentation_urls'])} official documentation sources")
        
        # Code examples
        if research_results.get('code_examples'):
            findings.append(f"Extracted {len(research_results['code_examples'])} code examples")
        
        # Best sources
        if research_results['search_results']:
            top_source = research_results['search_results'][0]
            findings.append(f"Top result: {top_source['title']} ({top_source['url']})")
        
        return findings
    
    def _calculate_confidence_score(self, research_results: Dict) -> float:
        """
        Calculate confidence score for research results.
        
        Args:
            research_results: Research results
            
        Returns:
            Confidence score (0-100)
        """
        score = 0
        
        # Base score for having results
        if research_results['search_results']:
            score += 30
        
        # Official documentation bonus
        if research_results['documentation_urls']:
            score += 25
            # Extra points for multiple official sources
            score += min(len(research_results['documentation_urls']) * 5, 15)
        
        # Code examples bonus
        if research_results.get('code_examples'):
            score += 15
        
        # Multiple sources bonus (cross-referencing)
        if len(research_results['search_results']) >= 5:
            score += 10
        
        # Recent results bonus (if we can determine)
        score += 5
        
        return min(score, 100)
    
    def _save_research_results(self, query: str, results: Dict, task: Task) -> str:
        """
        Save research results to PostgreSQL database (and files as backup).
        
        NEW: Stores in PostgreSQL for scalability and fast querying.
        Also saves files for backward compatibility and reference.
        
        Args:
            query: Research query
            results: Research results
            task: The research task
            
        Returns:
            research_id (unique identifier)
        """
        import uuid
        
        # Generate research ID
        research_id = str(uuid.uuid4())
        
        # Get project info
        project_name = task.metadata.get("project_name", "unknown")
        project_id = self.project_id
        
        # Store in PostgreSQL (PRIMARY storage)
        try:
            from utils.research_database import get_research_database
            db = get_research_database()
            
            # Add metadata to results
            results['research_id'] = research_id
            results['query'] = query
            
            # Store in database
            db.store_research(
                research_id=research_id,
                query=query,
                research_results=results,
                project_name=project_name,
                project_id=project_id
            )
            
            self.logger.info(f"[OK] Stored research in PostgreSQL: {research_id}")
            
        except Exception as e:
            self.logger.warning(f"Could not store in PostgreSQL, using files only: {e}")
        
        # Also save files (BACKUP storage for reference)
        # Generate concise filename instead of using full query
        from utils.name_generator import generate_concise_name
        from utils.name_sanitizer import sanitize_for_filename
        
        # Generate a concise name from the query (max 50 chars for filename)
        concise_name = generate_concise_name(query, agent_type="RESEARCHER", max_length=50)
        # Sanitize for filesystem (removes invalid chars, limits length)
        safe_filename = sanitize_for_filename(concise_name, max_length=50)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save JSON using safe file writer (HARD GUARANTEE)
        json_filename = f"{safe_filename}_{timestamp}.json"
        json_relative_path = os.path.join("research", json_filename)
        
        try:
            self.safe_write_file(json_relative_path, json.dumps(results, indent=2))
        except Exception as e:
            self.logger.error(f"[ERROR] Failed to write research JSON file: {e}")
            raise
        
        # Save Markdown report using safe file writer
        md_filename = f"{safe_filename}_{timestamp}.md"
        md_relative_path = os.path.join("research", md_filename)
        
        markdown_content = self._generate_markdown_report(query, results, task)
        try:
            self.safe_write_file(md_relative_path, markdown_content)
        except Exception as e:
            self.logger.error(f"[ERROR] Failed to write research Markdown file: {e}")
            raise
        
        # Update paths for return value (use relative paths)
        json_path = json_relative_path
        md_path = md_relative_path
        
        self.research_files.append(json_path)
        self.research_files.append(md_path)
        
        self.logger.info(f"[FILES] Backup files: {json_filename}, {md_filename}")
        
        return research_id
    
    def _generate_markdown_report(self, query: str, results: Dict, task: Task) -> str:
        """
        Generate markdown research report.
        
        Args:
            query: Research query
            results: Research results
            task: The research task
            
        Returns:
            Markdown formatted report
        """
        lines = [
            f"# Research Report: {query}",
            f"**Date**: {results['timestamp']}",
            f"**Task**: {task.id} - {task.title}",
            f"**Depth**: {results['depth']}",
            f"**Confidence Score**: {results['confidence_score']}/100",
            f"**Cached**: {'Yes' if results.get('cached') else 'No'}",
            "",
            "---",
            "",
            "## Summary",
            "",
        ]
        
        # Key findings
        if results['key_findings']:
            lines.append("### Key Findings")
            lines.append("")
            for finding in results['key_findings']:
                lines.append(f"- {finding}")
            lines.append("")
        
        # Official documentation
        if results['documentation_urls']:
            lines.append("### Official Documentation")
            lines.append("")
            for url in results['documentation_urls']:
                lines.append(f"- {url}")
            lines.append("")
        
        # Search results
        lines.append("### Search Results")
        lines.append("")
        for i, result in enumerate(results['search_results'][:10], 1):
            lines.append(f"#### {i}. {result['title']}")
            lines.append(f"**URL**: {result['url']}")
            lines.append(f"**Source**: {result['source']}")
            lines.append(f"**Snippet**: {result['snippet']}")
            lines.append("")
        
        # Code examples
        if results.get('code_examples'):
            lines.append("### Code Examples")
            lines.append("")
            for i, example in enumerate(results['code_examples'][:5], 1):
                lines.append(f"#### Example {i}")
                # Handle optional fields - LLM responses may not have source_title/source_url
                source_title = example.get('source_title') or example.get('description', 'Code Example')
                source_url = example.get('source_url', 'N/A')
                language = example.get('language', '')
                
                if source_title:
                    lines.append(f"**Source**: {source_title}")
                if source_url and source_url != 'N/A':
                    lines.append(f"**URL**: {source_url}")
                if language:
                    lines.append(f"**Language**: {language}")
                lines.append(f"```{language}")
                lines.append(example.get('code', ''))
                lines.append("```")
                lines.append("")
        
        # Footer
        lines.extend([
            "---",
            "",
            f"*Research conducted by ResearcherAgent ({self.agent_id})*",
            f"*Sources consulted: {', '.join(results['sources_consulted'])}*"
        ])
        
        return '\n'.join(lines)
    
    def _broadcast_research_complete(self, query: str, results: Dict, task: Task):
        """
        Broadcast research completion to other agents via message broker.
        
        Args:
            query: Research query
            results: Research results
            task: The research task
        """
        try:
            import uuid
            from utils.message_protocol import AgentMessage, MessageType
            
            # Create proper AgentMessage object
            message = AgentMessage(
                message_id=str(uuid.uuid4()),
                message_type=MessageType.TASK_UPDATE,
                sender_agent_id=self.agent_id,
                sender_agent_type=self.agent_type.value,
                channel="research",
                payload={
                    "event": "research_complete",
                    "query": query,
                    "task_id": task.id,
                    "confidence_score": results['confidence_score'],
                    "key_findings": results['key_findings'],
                    "documentation_urls": results['documentation_urls'],
                    "results_count": len(results['search_results'])
                }
            )
            
            # Send via message broker
            if hasattr(self, 'send_message'):
                self.send_message(message)
                self.logger.debug(f"Broadcast research completion for: {query}")
        except Exception as e:
            self.logger.debug(f"Could not broadcast research completion: {e}")
    
    def handle_research_request(self, requesting_agent_id: str, query: str, 
                               urgency: str = "normal") -> Optional[Dict]:
        """
        Handle research request from another agent during task execution.
        
        Args:
            requesting_agent_id: ID of the agent requesting research
            query: Research query
            urgency: Urgency level (low, normal, high)
            
        Returns:
            Research results or None if queued
        """
        self.logger.info(f"Research request from {requesting_agent_id}: {query}")
        
        # Check cache first (fast path)
        cached = self.cache.get(query)
        if cached:
            self.logger.info(f"Returning cached research to {requesting_agent_id}")
            # Send cached results back to requesting agent
            if hasattr(self, 'share_result'):
                self.share_result("research_results", cached, target_agent_id=requesting_agent_id)
            return cached
        
        # If not cached and urgency is high, conduct research immediately
        if urgency == "high" and len(self.active_tasks) < 3:
            # Create adhoc research task
            research_task = Task(
                id=f"research_adhoc_{int(time.time())}",
                title=f"Research: {query}",
                description=f"Research request from {requesting_agent_id}:\n{query}",
                agent_type=AgentType.RESEARCHER,
                metadata={
                    "research_query": query,
                    "requested_by": requesting_agent_id,
                    "urgency": urgency
                }
            )
            
            # Process immediately
            self.process_task(research_task)
            
            # Send results back to requesting agent
            if hasattr(self, 'share_result'):
                self.share_result("research_results", research_task.result, target_agent_id=requesting_agent_id)
            
            return research_task.result
        
        # Otherwise, queue for orchestrator
        self.logger.info(f"Research request queued for orchestrator: {query}")
        return None
    
    def _handle_research_request_message(self, message: Dict[str, Any]):
        """
        Handle incoming research request message from other agents.
        
        Args:
            message: Message from message broker
        """
        try:
            payload = message.get("payload", message)
            
            # Extract request details
            query = payload.get("query")
            requesting_agent = payload.get("requesting_agent")
            urgency = payload.get("urgency", "normal")
            
            if not query:
                self.logger.warning("Research request missing query")
                return
            
            # Process request
            self.logger.info(f"Processing research request from {requesting_agent}: {query}")
            self.handle_research_request(requesting_agent, query, urgency)
            
        except Exception as e:
            self.logger.error(f"Error handling research request message: {e}", exc_info=True)
