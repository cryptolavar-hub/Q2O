"""
Test ResearcherAgent functionality
"""

import pytest
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.researcher_agent import ResearcherAgent, ResearchCache, WebSearcher
from agents.base_agent import Task, AgentType, TaskStatus


def test_researcher_agent_import():
    """Test that ResearcherAgent can be imported."""
    from agents import ResearcherAgent
    assert ResearcherAgent is not None


def test_researcher_agent_initialization():
    """Test ResearcherAgent initialization."""
    agent = ResearcherAgent(workspace_path="./test_workspace")
    assert agent.agent_type == AgentType.RESEARCHER
    assert agent.agent_id == "researcher_main"
    assert agent.workspace_path == "./test_workspace"


def test_research_cache():
    """Test research caching functionality."""
    cache = ResearchCache(cache_dir=".test_cache", ttl_days=1)
    
    # Test set and get
    test_query = "FastAPI authentication"
    test_results = {
        "query": test_query,
        "results": ["result1", "result2"],
        "timestamp": "2025-11-03"
    }
    
    cache.set(test_query, test_results)
    cached = cache.get(test_query)
    
    assert cached is not None
    assert cached["query"] == test_query
    assert len(cached["results"]) == 2
    
    # Cleanup
    import shutil
    shutil.rmtree(".test_cache", ignore_errors=True)


def test_web_searcher_initialization():
    """Test WebSearcher initialization."""
    searcher = WebSearcher()
    assert searcher is not None
    
    # Check if DuckDuckGo fallback is available
    # (Google and Bing may not be configured in test environment)


def test_research_query_extraction():
    """Test research query extraction from task."""
    agent = ResearcherAgent(workspace_path="./test_workspace")
    
    task = Task(
        id="test_001",
        title="Research OAuth",
        description="Research: OAuth 2.0 best practices",
        agent_type=AgentType.RESEARCHER
    )
    
    query = agent._extract_research_query(task)
    assert "OAuth 2.0 best practices" in query


def test_research_depth_determination():
    """Test research depth determination logic."""
    agent = ResearcherAgent(workspace_path="./test_workspace")
    
    # Low complexity -> quick
    task_low = Task(
        id="test_002",
        title="Simple research",
        description="Simple query",
        agent_type=AgentType.RESEARCHER,
        metadata={"complexity": "low"}
    )
    depth = agent._determine_research_depth(task_low)
    assert depth == "quick"
    
    # High complexity -> comprehensive
    task_high = Task(
        id="test_003",
        title="Complex research",
        description="Complex query",
        agent_type=AgentType.RESEARCHER,
        metadata={"complexity": "high"}
    )
    depth = agent._determine_research_depth(task_high)
    assert depth == "comprehensive"


def test_official_documentation_detection():
    """Test detection of official documentation URLs."""
    agent = ResearcherAgent(workspace_path="./test_workspace")
    
    search_results = [
        {
            "title": "FastAPI Documentation",
            "url": "https://fastapi.tiangolo.com/",
            "snippet": "Official FastAPI documentation"
        },
        {
            "title": "Random Blog Post",
            "url": "https://example.com/blog",
            "snippet": "Some tutorial"
        },
        {
            "title": "OAuth 2.0 Spec",
            "url": "https://oauth.net/2/",
            "snippet": "Official OAuth 2.0 spec"
        }
    ]
    
    official_docs = agent._find_official_documentation(search_results, "FastAPI")
    
    # Should find at least the official docs
    assert len(official_docs) > 0
    assert any("fastapi" in url or "oauth.net" in url for url in official_docs)


def test_confidence_score_calculation():
    """Test confidence score calculation."""
    agent = ResearcherAgent(workspace_path="./test_workspace")
    
    # Good research results
    good_results = {
        "search_results": [{"title": "test", "url": "test", "snippet": "test"}] * 10,
        "documentation_urls": ["url1", "url2", "url3"],
        "code_examples": [{"code": "example"}]
    }
    
    score = agent._calculate_confidence_score(good_results)
    assert score >= 70  # Should have high confidence
    
    # Poor research results
    poor_results = {
        "search_results": [],
        "documentation_urls": [],
        "code_examples": []
    }
    
    score_poor = agent._calculate_confidence_score(poor_results)
    assert score_poor < 50  # Should have low confidence


if __name__ == "__main__":
    # Run tests
    print("Testing ResearcherAgent...")
    
    test_researcher_agent_import()
    print("[OK] Import test passed")
    
    test_researcher_agent_initialization()
    print("[OK] Initialization test passed")
    
    test_research_cache()
    print("[OK] Cache test passed")
    
    test_web_searcher_initialization()
    print("[OK] WebSearcher test passed")
    
    test_research_query_extraction()
    print("[OK] Query extraction test passed")
    
    test_research_depth_determination()
    print("[OK] Research depth test passed")
    
    test_official_documentation_detection()
    print("[OK] Documentation detection test passed")
    
    test_confidence_score_calculation()
    print("[OK] Confidence scoring test passed")
    
    print("\n[SUCCESS] All ResearcherAgent tests passed!")

