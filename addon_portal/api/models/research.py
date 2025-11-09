"""
Research Data Models - PostgreSQL storage for research results
Replaces file system storage with scalable database storage.
"""

from sqlalchemy import Column, String, Integer, Float, DateTime, Text, JSON, Index, Boolean
from sqlalchemy.sql import func
from .licensing import Base


class ResearchResult(Base):
    """
    Research results stored in PostgreSQL for scalability and querying.
    
    Replaces file system storage for research findings.
    """
    __tablename__ = "research_results"
    
    # Primary identification
    id = Column(Integer, primary_key=True, index=True)
    research_id = Column(String(64), unique=True, index=True, nullable=False)  # UUID
    
    # Research query and metadata
    query = Column(Text, nullable=False, index=True)
    query_hash = Column(String(64), index=True, nullable=False)  # MD5 hash for dedup
    project_name = Column(String(255), index=True)
    project_id = Column(String(64), index=True)
    
    # Research content (JSON fields for flexibility)
    search_results = Column(JSON)  # List of search results with title, snippet, url
    documentation_urls = Column(JSON)  # List of official documentation URLs
    code_examples = Column(JSON)  # List of code examples found
    key_findings = Column(JSON)  # List of synthesized findings (LLM-generated!)
    
    # Quality metrics
    confidence_score = Column(Float, default=0.0)
    results_count = Column(Integer, default=0)
    
    # Research metadata
    research_depth = Column(String(50))  # "quick", "deep", "comprehensive", "adaptive"
    cached = Column(Boolean, default=False)
    llm_synthesized = Column(Boolean, default=False)  # Was synthesis done by LLM?
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    last_accessed = Column(DateTime(timezone=True), onupdate=func.now())
    expires_at = Column(DateTime(timezone=True), index=True)  # TTL for cache
    
    # Usage tracking
    access_count = Column(Integer, default=0)
    
    # Full text search
    full_content = Column(Text)  # Concatenated content for full-text search
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_research_query_hash', 'query_hash'),
        Index('idx_research_project', 'project_id', 'project_name'),
        Index('idx_research_created', 'created_at'),
        Index('idx_research_expires', 'expires_at'),
    )


class ResearchAnalytics(Base):
    """
    Analytics for research usage and effectiveness.
    Tracks which research is most valuable.
    """
    __tablename__ = "research_analytics"
    
    id = Column(Integer, primary_key=True, index=True)
    research_id = Column(String(64), index=True, nullable=False)
    
    # Usage metrics
    used_by_agent_type = Column(String(50))
    used_by_agent_id = Column(String(100))
    used_for_task_id = Column(String(100))
    
    # Effectiveness tracking
    was_helpful = Column(Boolean)  # Did it help complete the task?
    helpfulness_score = Column(Float)  # 0-100
    
    # Timestamp
    used_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_analytics_research', 'research_id'),
        Index('idx_analytics_agent', 'used_by_agent_type', 'used_by_agent_id'),
    )

