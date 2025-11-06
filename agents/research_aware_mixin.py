"""
Research-Aware Mixin for Agents
Helps agents access and utilize research results from dependencies and past projects
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class ResearchAwareMixin:
    """
    Mixin to help agents use research results from dependencies and global research database.
    
    Usage:
        class MyAgent(BaseAgent, ResearchAwareMixin):
            def process_task(self, task):
                # Get research from dependencies
                research = self.get_research_results(task)
                
                # Or query global research database
                past_research = self.query_global_research("Stripe API")
    """
    
    def get_research_results(self, task) -> List[Dict]:
        """
        Get research results from dependency tasks.
        
        Args:
            task: Current task with dependencies
            
        Returns:
            List of research results from all research dependencies
        """
        from agents.base_agent import AgentType, TaskStatus
        
        research_results = []
        
        if not task.dependencies:
            return research_results
        
        for dep_id in task.dependencies:
            dep_task = self._get_dependency_task(dep_id)
            
            if dep_task and dep_task.agent_type == AgentType.RESEARCHER:
                if dep_task.status == TaskStatus.COMPLETED:
                    # Get from metadata
                    research_data = dep_task.metadata.get("research_results", {})
                    if research_data:
                        research_results.append(research_data)
                    
                    # Also try to load from file if available
                    research_file = dep_task.metadata.get("research_file")
                    if research_file and os.path.exists(research_file):
                        try:
                            with open(research_file, 'r', encoding='utf-8') as f:
                                file_data = json.load(f)
                                research_results.append(file_data)
                        except Exception as e:
                            logger.warning(f"Could not load research file {research_file}: {e}")
        
        logger.info(f"Retrieved {len(research_results)} research results from dependencies")
        return research_results
    
    def _get_dependency_task(self, dep_id: str):
        """Get dependency task from orchestrator or registry."""
        # Try to get from orchestrator
        if hasattr(self, 'orchestrator') and self.orchestrator:
            return self.orchestrator.project_tasks.get(dep_id)
        
        # Try to get from global task registry (if available)
        try:
            from utils.task_registry import get_task
            return get_task(dep_id)
        except ImportError:
            pass
        
        return None
    
    def extract_api_info_from_research(self, research_results: List[Dict]) -> Dict:
        """
        Extract API-specific information from research results.
        
        Args:
            research_results: List of research result dictionaries
            
        Returns:
            Dictionary with extracted API information
        """
        api_info = {
            "documentation_urls": [],
            "base_urls": [],
            "auth_methods": [],
            "code_examples": [],
            "entities": [],
            "key_findings": [],
            "api_endpoints": []
        }
        
        for research in research_results:
            # Documentation URLs
            api_info["documentation_urls"].extend(research.get("documentation_urls", []))
            
            # Code examples
            api_info["code_examples"].extend(research.get("code_examples", []))
            
            # Key findings
            api_info["key_findings"].extend(research.get("key_findings", []))
            
            # Parse search results for additional info
            for result in research.get("search_results", []):
                snippet = result.get("snippet", "").lower()
                url = result.get("url", "")
                
                # Extract base URLs (API endpoints)
                if "api." in url or "/api/" in url:
                    if url not in api_info["base_urls"]:
                        api_info["base_urls"].append(url)
                
                # Detect authentication methods
                if "oauth" in snippet:
                    if "OAuth 2.0" not in api_info["auth_methods"]:
                        api_info["auth_methods"].append("OAuth 2.0")
                elif "api key" in snippet or "api_key" in snippet:
                    if "API Key" not in api_info["auth_methods"]:
                        api_info["auth_methods"].append("API Key")
                elif "bearer token" in snippet or "jwt" in snippet:
                    if "Bearer Token" not in api_info["auth_methods"]:
                        api_info["auth_methods"].append("Bearer Token")
                
                # Extract entity mentions (common data types)
                entity_keywords = ["customer", "invoice", "payment", "product", "order", "account", "user"]
                for keyword in entity_keywords:
                    if keyword in snippet:
                        entity_name = keyword.capitalize()
                        if entity_name not in api_info["entities"]:
                            api_info["entities"].append(entity_name)
        
        # Deduplicate
        api_info["documentation_urls"] = list(set(api_info["documentation_urls"]))
        api_info["base_urls"] = list(set(api_info["base_urls"]))
        
        logger.info(f"Extracted API info: {len(api_info['documentation_urls'])} docs, "
                   f"{len(api_info['auth_methods'])} auth methods, "
                   f"{len(api_info['entities'])} entities")
        
        return api_info
    
    def query_global_research(self, query: str, limit: int = 5) -> List[Dict]:
        """
        Query the global research database for past research on similar topics.
        
        Args:
            query: Search query (e.g., "Stripe API", "OAuth 2.0", "QuickBooks")
            limit: Maximum number of results to return
            
        Returns:
            List of past research results matching the query
        """
        from utils.research_database import query_research
        
        try:
            results = query_research(query, limit=limit)
            logger.info(f"Found {len(results)} past research results for query: {query}")
            return results
        except Exception as e:
            logger.warning(f"Could not query global research database: {e}")
            return []
    
    def get_research_summary(self, research_results: List[Dict]) -> str:
        """
        Generate a human-readable summary of research results.
        
        Args:
            research_results: List of research result dictionaries
            
        Returns:
            Markdown-formatted summary string
        """
        if not research_results:
            return "No research results available."
        
        lines = ["# Research Summary", ""]
        
        for i, research in enumerate(research_results, 1):
            lines.append(f"## Research {i}: {research.get('query', 'Unknown')}")
            lines.append("")
            
            # Key findings
            if research.get('key_findings'):
                lines.append("**Key Findings:**")
                for finding in research['key_findings'][:5]:
                    lines.append(f"- {finding}")
                lines.append("")
            
            # Documentation
            if research.get('documentation_urls'):
                lines.append("**Documentation:**")
                for url in research['documentation_urls'][:3]:
                    lines.append(f"- {url}")
                lines.append("")
            
            # Confidence
            confidence = research.get('confidence_score', 0)
            lines.append(f"**Confidence Score:** {confidence}/100")
            lines.append("")
        
        return "\n".join(lines)
    
    def enrich_template_context_with_research(self, base_context: Dict, 
                                             research_results: List[Dict]) -> Dict:
        """
        Enrich template rendering context with research findings.
        
        Args:
            base_context: Base template context dictionary
            research_results: Research results to incorporate
            
        Returns:
            Enhanced context dictionary
        """
        # Extract API info
        api_info = self.extract_api_info_from_research(research_results)
        
        # Merge into context
        enriched = base_context.copy()
        enriched.update({
            "api_documentation_urls": api_info["documentation_urls"],
            "api_base_urls": api_info["base_urls"],
            "auth_methods": api_info["auth_methods"],
            "detected_entities": api_info["entities"],
            "research_key_findings": api_info["key_findings"],
            "code_examples": api_info["code_examples"][:5],  # Top 5
            "has_research": True,
            "research_timestamp": datetime.now().isoformat()
        })
        
        logger.info(f"Enriched template context with research data")
        return enriched


def research_guided(method):
    """
    Decorator to make agent methods research-aware.
    Automatically loads research from dependencies and enriches context.
    
    Usage:
        @research_guided
        def process_task(self, task):
            # task.metadata will have 'research_context' added
            research_context = task.metadata.get('research_context', {})
    """
    def wrapper(self, task, *args, **kwargs):
        # Load research if agent has the mixin
        if isinstance(self, ResearchAwareMixin):
            research_results = self.get_research_results(task)
            
            if research_results:
                # Add research context to task metadata
                api_info = self.extract_api_info_from_research(research_results)
                task.metadata['research_context'] = api_info
                task.metadata['research_summary'] = self.get_research_summary(research_results)
                
                logger.info(f"Task {task.id} enriched with research context")
        
        # Call original method
        return method(self, task, *args, **kwargs)
    
    return wrapper

