"""
Research Database - PostgreSQL storage for research results.
Replaces file system storage with scalable database queries.
"""

import hashlib
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from pathlib import Path

# Database imports
try:
    from sqlalchemy.orm import Session
    from addon_portal.api.core.db import get_db
    from addon_portal.api.models.research import ResearchResult, ResearchAnalytics
    DB_AVAILABLE = True
except ImportError:
    logging.warning("Database not available for research storage, using file system")
    DB_AVAILABLE = False


class ResearchDatabase:
    """
    PostgreSQL-based research storage with intelligent querying.
    
    Replaces file system with scalable database storage.
    """
    
    def __init__(self):
        self.enabled = DB_AVAILABLE
        self.ttl_days = 90  # Research expires after 90 days
    
    def store_research(
        self,
        research_id: str,
        query: str,
        research_results: Dict[str, Any],
        project_name: str = None,
        project_id: str = None
    ) -> str:
        """
        Store research results in PostgreSQL.
        
        Args:
            research_id: Unique research identifier
            query: Original research query
            research_results: Complete research results dictionary
            project_name: Project name (optional)
            project_id: Project ID (optional)
        
        Returns:
            research_id
        """
        if not self.enabled:
            logging.warning("Database not available, research not stored")
            return research_id
        
        try:
            db = next(get_db())
            
            # Create query hash for deduplication
            query_hash = hashlib.md5(query.lower().strip().encode()).hexdigest()
            
            # Check if research already exists
            existing = db.query(ResearchResult).filter(
                ResearchResult.query_hash == query_hash
            ).first()
            
            if existing:
                # Update access count and last accessed
                existing.access_count += 1
                existing.last_accessed = datetime.now()
                db.commit()
                logging.info(f"Research already exists: {existing.research_id}, incrementing access count")
                return existing.research_id
            
            # Create full content for search
            full_content = self._create_searchable_content(query, research_results)
            
            # Create new research record
            research = ResearchResult(
                research_id=research_id,
                query=query,
                query_hash=query_hash,
                project_name=project_name,
                project_id=project_id,
                search_results=research_results.get('search_results', []),
                documentation_urls=research_results.get('documentation_urls', []),
                code_examples=research_results.get('code_examples', []),
                key_findings=research_results.get('key_findings', []),
                confidence_score=research_results.get('confidence_score', 0.0),
                results_count=len(research_results.get('search_results', [])),
                research_depth=research_results.get('depth', 'adaptive'),
                cached=research_results.get('cached', False),
                llm_synthesized=bool(research_results.get('llm_synthesized', False)),
                expires_at=datetime.now() + timedelta(days=self.ttl_days),
                access_count=1,
                full_content=full_content
            )
            
            db.add(research)
            db.commit()
            db.refresh(research)
            
            logging.info(f"✅ Stored research in PostgreSQL: {research_id}")
            
            return research_id
            
        except Exception as e:
            logging.error(f"Failed to store research in database: {e}")
            return research_id
    
    def find_similar_research(
        self,
        query: str,
        limit: int = 5,
        min_confidence: float = 30.0
    ) -> List[Dict]:
        """
        Find similar research results from PostgreSQL.
        
        Queries by:
        - Exact query hash match (best)
        - Similar queries (keyword overlap)
        - Full-text search
        
        Args:
            query: Search query
            limit: Maximum results to return
            min_confidence: Minimum confidence score threshold
        
        Returns:
            List of matching research results
        """
        if not self.enabled:
            return []
        
        try:
            db = next(get_db())
            
            # Strategy 1: Exact query hash match
            query_hash = hashlib.md5(query.lower().strip().encode()).hexdigest()
            exact_match = db.query(ResearchResult).filter(
                ResearchResult.query_hash == query_hash,
                ResearchResult.expires_at > datetime.now()
            ).first()
            
            if exact_match:
                # Increment access count
                exact_match.access_count += 1
                exact_match.last_accessed = datetime.now()
                db.commit()
                
                logging.info(f"✅ Found EXACT match for: {query}")
                return [self._result_to_dict(exact_match)]
            
            # Strategy 2: Similar queries (keyword-based)
            query_keywords = set(query.lower().split())
            
            candidates = db.query(ResearchResult).filter(
                ResearchResult.confidence_score >= min_confidence,
                ResearchResult.expires_at > datetime.now()
            ).order_by(
                ResearchResult.confidence_score.desc(),
                ResearchResult.created_at.desc()
            ).limit(limit * 3).all()  # Get more for filtering
            
            # Score by keyword overlap
            scored_results = []
            for candidate in candidates:
                candidate_keywords = set(candidate.query.lower().split())
                overlap = len(query_keywords & candidate_keywords)
                similarity = overlap / max(len(query_keywords), len(candidate_keywords))
                
                if similarity > 0.3:  # 30% keyword overlap threshold
                    scored_results.append((similarity, candidate))
            
            # Sort by similarity and return top matches
            scored_results.sort(reverse=True, key=lambda x: x[0])
            results = [self._result_to_dict(r[1]) for r in scored_results[:limit]]
            
            if results:
                logging.info(f"✅ Found {len(results)} similar research results for: {query}")
            else:
                logging.info(f"ℹ️ No similar research found for: {query}")
            
            return results
            
        except Exception as e:
            logging.error(f"Failed to query research database: {e}")
            return []
    
    def get_research_by_id(self, research_id: str) -> Optional[Dict]:
        """
        Get specific research by ID.
        
        Args:
            research_id: Research identifier
        
        Returns:
            Research results dictionary or None
        """
        if not self.enabled:
            return None
        
        try:
            db = next(get_db())
            
            research = db.query(ResearchResult).filter(
                ResearchResult.research_id == research_id
            ).first()
            
            if research:
                # Increment access count
                research.access_count += 1
                research.last_accessed = datetime.now()
                db.commit()
                
                return self._result_to_dict(research)
            
            return None
            
        except Exception as e:
            logging.error(f"Failed to get research by ID: {e}")
            return None
    
    def track_usage(
        self,
        research_id: str,
        agent_type: str,
        agent_id: str,
        task_id: str = None,
        was_helpful: bool = True,
        helpfulness_score: float = 80.0
    ):
        """
        Track research usage and effectiveness.
        
        Args:
            research_id: Research identifier
            agent_type: Type of agent using the research
            agent_id: Agent identifier
            task_id: Task identifier (optional)
            was_helpful: Whether research helped complete task
            helpfulness_score: How helpful (0-100)
        """
        if not self.enabled:
            return
        
        try:
            db = next(get_db())
            
            analytics = ResearchAnalytics(
                research_id=research_id,
                used_by_agent_type=agent_type,
                used_by_agent_id=agent_id,
                used_for_task_id=task_id,
                was_helpful=was_helpful,
                helpfulness_score=helpfulness_score
            )
            
            db.add(analytics)
            db.commit()
            
            logging.info(f"Tracked research usage: {research_id} by {agent_type}")
            
        except Exception as e:
            logging.error(f"Failed to track research usage: {e}")
    
    def search_research(
        self,
        search_term: str,
        project_id: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict]:
        """
        Search research results by content.
        
        Searches in:
        - Query text
        - Key findings
        - Full content
        
        Args:
            search_term: Text to search for
            project_id: Filter by project (optional)
            limit: Maximum results
        
        Returns:
            List of matching research results
        """
        if not self.enabled:
            return []
        
        try:
            db = next(get_db())
            
            search_lower = f"%{search_term.lower()}%"
            
            query = db.query(ResearchResult).filter(
                ResearchResult.expires_at > datetime.now()
            )
            
            # Filter by project if specified
            if project_id:
                query = query.filter(ResearchResult.project_id == project_id)
            
            # Search in query and full_content
            query = query.filter(
                (ResearchResult.query.ilike(search_lower)) |
                (ResearchResult.full_content.ilike(search_lower))
            )
            
            # Order by relevance (confidence, recent, access count)
            results = query.order_by(
                ResearchResult.confidence_score.desc(),
                ResearchResult.access_count.desc(),
                ResearchResult.created_at.desc()
            ).limit(limit).all()
            
            logging.info(f"Search for '{search_term}': {len(results)} results")
            
            return [self._result_to_dict(r) for r in results]
            
        except Exception as e:
            logging.error(f"Failed to search research: {e}")
            return []
    
    def get_research_stats(self, project_id: Optional[str] = None) -> Dict:
        """
        Get research statistics.
        
        Args:
            project_id: Filter by project (optional)
        
        Returns:
            Statistics dictionary
        """
        if not self.enabled:
            return {}
        
        try:
            db = next(get_db())
            
            query = db.query(ResearchResult)
            
            if project_id:
                query = query.filter(ResearchResult.project_id == project_id)
            
            total = query.count()
            llm_synthesized = query.filter(ResearchResult.llm_synthesized == True).count()
            
            # Average confidence
            avg_confidence = db.query(func.avg(ResearchResult.confidence_score)).scalar() or 0.0
            
            # Total access count
            total_accesses = db.query(func.sum(ResearchResult.access_count)).scalar() or 0
            
            return {
                "total_research": total,
                "llm_synthesized_count": llm_synthesized,
                "llm_synthesized_percent": (llm_synthesized / total * 100) if total > 0 else 0.0,
                "avg_confidence": float(avg_confidence),
                "total_accesses": total_accesses,
                "avg_reuse": (total_accesses / total) if total > 0 else 0.0
            }
            
        except Exception as e:
            logging.error(f"Failed to get research stats: {e}")
            return {}
    
    def cleanup_expired(self) -> int:
        """
        Remove expired research results.
        
        Returns:
            Number of records deleted
        """
        if not self.enabled:
            return 0
        
        try:
            db = next(get_db())
            
            deleted = db.query(ResearchResult).filter(
                ResearchResult.expires_at < datetime.now()
            ).delete()
            
            db.commit()
            
            logging.info(f"Cleaned up {deleted} expired research records")
            return deleted
            
        except Exception as e:
            logging.error(f"Failed to cleanup expired research: {e}")
            return 0
    
    def _result_to_dict(self, research: ResearchResult) -> Dict:
        """Convert SQLAlchemy model to dictionary."""
        return {
            "research_id": research.research_id,
            "query": research.query,
            "project_name": research.project_name,
            "project_id": research.project_id,
            "search_results": research.search_results or [],
            "documentation_urls": research.documentation_urls or [],
            "code_examples": research.code_examples or [],
            "key_findings": research.key_findings or [],
            "confidence_score": research.confidence_score,
            "results_count": research.results_count,
            "research_depth": research.research_depth,
            "cached": research.cached,
            "llm_synthesized": research.llm_synthesized,
            "created_at": research.created_at.isoformat() if research.created_at else None,
            "last_accessed": research.last_accessed.isoformat() if research.last_accessed else None,
            "access_count": research.access_count
        }
    
    def _create_searchable_content(self, query: str, research_results: Dict) -> str:
        """
        Create searchable full-text content from research results.
        
        Args:
            query: Research query
            research_results: Research results dictionary
        
        Returns:
            Concatenated searchable text
        """
        parts = [query]
        
        # Add key findings
        parts.extend(research_results.get('key_findings', []))
        
        # Add snippets from search results
        for result in research_results.get('search_results', [])[:10]:
            parts.append(result.get('title', ''))
            parts.append(result.get('snippet', ''))
        
        # Add documentation URLs (domains are searchable)
        parts.extend(research_results.get('documentation_urls', []))
        
        return " ".join(parts)


# Singleton instance
_research_db = None

def get_research_database() -> ResearchDatabase:
    """Get singleton research database instance."""
    global _research_db
    if _research_db is None:
        _research_db = ResearchDatabase()
    return _research_db


# Convenience functions (backward compatible with old file-based system)

def store_research(
    research_results: Dict,
    project_name: str = None,
    project_id: str = None
) -> str:
    """
    Store research results in database.
    
    Args:
        research_results: Research results dictionary
        project_name: Project name
        project_id: Project ID
    
    Returns:
        research_id
    """
    import uuid
    
    research_id = str(uuid.uuid4())
    query = research_results.get('query', 'unknown')
    
    db = get_research_database()
    return db.store_research(research_id, query, research_results, project_name, project_id)


def query_research(query: str, limit: int = 5) -> List[Dict]:
    """
    Query research database for similar past research.
    
    Args:
        query: Search query
        limit: Maximum results
    
    Returns:
        List of matching research results
    """
    db = get_research_database()
    return db.find_similar_research(query, limit=limit)


def get_research_by_id(research_id: str) -> Optional[Dict]:
    """
    Get research by ID.
    
    Args:
        research_id: Research identifier
    
    Returns:
        Research results or None
    """
    db = get_research_database()
    return db.get_research_by_id(research_id)
