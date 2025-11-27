"""
Recursive Research System
Multi-level research that follows links to discover deep documentation
"""

import os
import re
import time
import logging
import asyncio
from typing import Dict, List, Set, Optional
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

# Try to import httpx for async HTTP, fallback to requests if not available
try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    import requests
    HTTPX_AVAILABLE = False

logger = logging.getLogger(__name__)


class RecursiveResearcher:
    """
    Performs multi-level recursive research by following links.
    
    Level 0: Initial search results
    Level 1: Scrape top results, extract important links
    Level 2: Follow and scrape those links (API docs, SDKs, examples)
    Level 3: (Optional) Follow GitHub repos, code examples
    """
    
    def __init__(self, max_depth: int = 2, max_links_per_page: int = 10,
                 request_timeout: int = 10):
        """
        Initialize recursive researcher.
        
        Args:
            max_depth: Maximum recursion depth (1-3)
            max_links_per_page: Maximum links to follow from each page
            request_timeout: HTTP request timeout in seconds
        """
        self.max_depth = max_depth
        self.max_links_per_page = max_links_per_page
        self.request_timeout = request_timeout
        self.visited_urls: Set[str] = set()
        self.scraped_content: Dict[str, Dict] = {}
    
    def recursive_research(self, initial_results: List[Dict], 
                          focus_keywords: List[str] = None) -> Dict:
        """
        Perform recursive research starting from initial search results.
        
        Args:
            initial_results: Initial search results from Google/Bing
            focus_keywords: Keywords to prioritize (e.g., ['API', 'documentation', 'reference'])
            
        Returns:
            Comprehensive research data with multi-level content
        """
        focus_keywords = focus_keywords or ['api', 'documentation', 'reference', 'guide', 'sdk']
        
        research_data = {
            'level_0_results': initial_results,
            'level_1_content': {},  # Scraped from initial results
            'level_2_content': {},  # Scraped from links found in level 1
            'discovered_links': [],
            'documentation_urls': [],
            'github_repos': [],
            'code_examples': [],
            'api_endpoints': [],
            'total_pages_scraped': 0
        }
        
        logger.info(f"Starting recursive research with {len(initial_results)} initial results, max depth {self.max_depth}")
        
        # LEVEL 1: Scrape top initial results
        level_1_urls = self._select_most_relevant(initial_results, focus_keywords, limit=5)
        logger.info(f"Level 1: Scraping {len(level_1_urls)} most relevant URLs...")
        
        for url_data in level_1_urls:
            url = url_data['url']
            content = self._scrape_page(url)
            
            if content:
                self.scraped_content[url] = content
                research_data['level_1_content'][url] = content
                research_data['total_pages_scraped'] += 1
                
                # Extract important links from this page
                important_links = self._extract_important_links(
                    content, 
                    url, 
                    focus_keywords
                )
                research_data['discovered_links'].extend(important_links)
                
                # Categorize links
                for link in important_links:
                    if 'github.com' in link['url']:
                        research_data['github_repos'].append(link)
                    elif any(kw in link['text'].lower() for kw in ['documentation', 'api', 'reference']):
                        research_data['documentation_urls'].append(link['url'])
        
        logger.info(f"Level 1: Scraped {len(research_data['level_1_content'])} pages, found {len(research_data['discovered_links'])} links")
        
        # LEVEL 2: Follow discovered links (if depth allows)
        if self.max_depth >= 2 and research_data['discovered_links']:
            level_2_links = self._prioritize_links(research_data['discovered_links'], limit=15)
            logger.info(f"Level 2: Following {len(level_2_links)} discovered links...")
            
            for link_data in level_2_links:
                url = link_data['url']
                
                # Avoid re-scraping
                if url in self.visited_urls:
                    continue
                
                content = self._scrape_page(url)
                
                if content:
                    self.scraped_content[url] = content
                    research_data['level_2_content'][url] = content
                    research_data['total_pages_scraped'] += 1
                    
                    # Extract code examples
                    code_examples = self._extract_code_from_content(content)
                    research_data['code_examples'].extend(code_examples)
                    
                    # Extract API endpoints
                    endpoints = self._extract_api_endpoints(content)
                    research_data['api_endpoints'].extend(endpoints)
                
                # Rate limiting (sync context, so use time.sleep)
                # Note: If this method becomes async, change to await asyncio.sleep(0.5)
                time.sleep(0.5)
        
        logger.info(f"Recursive research complete: {research_data['total_pages_scraped']} pages scraped, "
                   f"{len(research_data['code_examples'])} code examples, "
                   f"{len(research_data['api_endpoints'])} API endpoints")
        
        return research_data
    
    def _select_most_relevant(self, results: List[Dict], keywords: List[str], 
                             limit: int = 5) -> List[Dict]:
        """
        Select most relevant results based on keywords in title and snippet.
        
        Args:
            results: Search results
            keywords: Keywords to prioritize
            limit: Maximum results to return
            
        Returns:
            Top N most relevant results
        """
        scored_results = []
        
        for result in results:
            score = 0
            title = result.get('title', '').lower()
            snippet = result.get('snippet', '').lower()
            url = result.get('url', '').lower()
            
            # Score based on keywords
            for keyword in keywords:
                if keyword.lower() in title:
                    score += 3  # Title match is most important
                if keyword.lower() in snippet:
                    score += 1
                if keyword.lower() in url:
                    score += 2
            
            # Boost official sources
            domain = urlparse(result.get('url', '')).netloc
            if 'github.com' in domain:
                score += 5
            if any(official in domain for official in ['developer.', 'docs.', 'api.']):
                score += 4
            
            scored_results.append((score, result))
        
        # Sort by score descending
        scored_results.sort(key=lambda x: x[0], reverse=True)
        
        return [result for score, result in scored_results[:limit]]
    
    async def _scrape_page_async(self, url: str) -> Optional[Dict]:
        """
        Scrape a single page asynchronously.
        
        Args:
            url: URL to scrape
            
        Returns:
            Dictionary with page content and metadata
        """
        if url in self.visited_urls:
            return None
        
        self.visited_urls.add(url)
        
        try:
            if HTTPX_AVAILABLE:
                async with httpx.AsyncClient(timeout=self.request_timeout) as client:
                    response = await client.get(url, headers={
                        'User-Agent': 'Mozilla/5.0 (compatible; Quick2OdooBot/1.0; +https://github.com/cryptolavar-hub/Q2O)'
                    })
                    response.raise_for_status()
                    content = response.text
            else:
                # Fallback to sync requests if httpx not available
                response = requests.get(url, timeout=self.request_timeout, headers={
                    'User-Agent': 'Mozilla/5.0 (compatible; Quick2OdooBot/1.0; +https://github.com/cryptolavar-hub/Q2O)'
                })
                response.raise_for_status()
                content = response.text
            
            soup = BeautifulSoup(content, 'html.parser')
            
            # Remove script and style elements
            for element in soup(['script', 'style', 'nav', 'footer', 'header']):
                element.decompose()
            
            # Get text content
            text = soup.get_text(separator='\n', strip=True)
            
            return {
                'url': url,
                'title': soup.title.string if soup.title else '',
                'text': text,
                'html': str(soup),
                'links': [a.get('href') for a in soup.find_all('a', href=True)]
            }
        except Exception as e:
            logger.warning(f"Error scraping {url}: {e}")
            return None
    
    def _scrape_page(self, url: str) -> Optional[Dict]:
        """
        Scrape a single page (sync wrapper).
        
        Args:
            url: URL to scrape
            
        Returns:
            Dictionary with page content and metadata
        """
        try:
            return asyncio.run(self._scrape_page_async(url))
        except RuntimeError:
            # If event loop is already running, create a new one in a thread
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, self._scrape_page_async(url))
                return future.result(timeout=self.request_timeout + 5)
            
        except Exception as e:
            logger.warning(f"Could not scrape {url}: {e}")
            return None
    
    def _extract_important_links(self, content: Dict, base_url: str, 
                                keywords: List[str]) -> List[Dict]:
        """
        Extract important links from scraped content.
        
        Args:
            content: Scraped page content
            base_url: Base URL for resolving relative links
            keywords: Keywords to prioritize
            
        Returns:
            List of important links with metadata
        """
        important_links = []
        soup = BeautifulSoup(content['html'], 'html.parser')
        
        for a_tag in soup.find_all('a', href=True):
            href = a_tag.get('href')
            text = a_tag.get_text(strip=True)
            
            # Resolve relative URLs
            full_url = urljoin(base_url, href)
            
            # Skip anchors, javascript, mailto, etc.
            if full_url.startswith(('javascript:', 'mailto:', '#')):
                continue
            
            # Check if link text contains keywords
            text_lower = text.lower()
            relevance_score = 0
            
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    relevance_score += 1
            
            # Prioritize certain link patterns
            if any(pattern in full_url.lower() for pattern in ['/api/', '/docs/', '/reference/', '/guide/']):
                relevance_score += 3
            
            if any(pattern in text_lower for pattern in ['documentation', 'api reference', 'getting started', 'sdk']):
                relevance_score += 2
            
            if relevance_score > 0:
                important_links.append({
                    'url': full_url,
                    'text': text,
                    'relevance': relevance_score
                })
        
        # Sort by relevance and limit
        important_links.sort(key=lambda x: x['relevance'], reverse=True)
        return important_links[:self.max_links_per_page]
    
    def _prioritize_links(self, links: List[Dict], limit: int = 15) -> List[Dict]:
        """
        Prioritize links for Level 2 scraping.
        
        Args:
            links: List of discovered links
            limit: Maximum links to return
            
        Returns:
            Prioritized links
        """
        # Remove duplicates
        unique_links = {}
        for link in links:
            url = link['url']
            if url not in unique_links:
                unique_links[url] = link
            else:
                # Keep higher relevance score
                if link['relevance'] > unique_links[url]['relevance']:
                    unique_links[url] = link
        
        # Sort by relevance
        sorted_links = sorted(unique_links.values(), key=lambda x: x['relevance'], reverse=True)
        
        return sorted_links[:limit]
    
    def _extract_code_from_content(self, content: Dict) -> List[Dict]:
        """
        Extract code blocks from page content.
        
        Args:
            content: Scraped page content
            
        Returns:
            List of code examples
        """
        code_examples = []
        soup = BeautifulSoup(content['html'], 'html.parser')
        
        # Find code blocks (pre, code tags)
        for pre_tag in soup.find_all(['pre', 'code']):
            code_text = pre_tag.get_text(strip=True)
            
            # Only include substantial code (more than 2 lines)
            if len(code_text) > 50 and '\n' in code_text:
                code_examples.append({
                    'code': code_text,
                    'source_url': content['url'],
                    'source_title': content['title']
                })
        
        return code_examples
    
    def _extract_api_endpoints(self, content: Dict) -> List[str]:
        """
        Extract API endpoints from content.
        
        Args:
            content: Scraped page content
            
        Returns:
            List of API endpoints
        """
        endpoints = []
        text = content['text']
        
        # Common API endpoint patterns
        patterns = [
            r'https?://[a-zA-Z0-9.-]+/api/[a-zA-Z0-9/_-]+',
            r'/api/[a-zA-Z0-9/_-]+',
            r'GET|POST|PUT|DELETE\s+/[a-zA-Z0-9/_-]+'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            endpoints.extend(matches)
        
        # Deduplicate
        return list(set(endpoints))


def perform_recursive_research(initial_results: List[Dict], 
                               platform: str = None,
                               max_depth: int = 2) -> Dict:
    """
    Convenience function to perform recursive research.
    
    Args:
        initial_results: Initial search results from Google/Bing
        platform: Platform name (SAGE, QuickBooks, etc.) for focused keywords
        max_depth: Maximum recursion depth
        
    Returns:
        Comprehensive research data
    """
    # Build focus keywords based on platform
    focus_keywords = ['api', 'documentation', 'reference', 'guide', 'sdk', 'examples']
    
    if platform:
        focus_keywords.extend([
            platform.lower(),
            f"{platform.lower()} api",
            'authentication',
            'entities',
            'data model'
        ])
    
    researcher = RecursiveResearcher(max_depth=max_depth, max_links_per_page=10)
    return researcher.recursive_research(initial_results, focus_keywords)

