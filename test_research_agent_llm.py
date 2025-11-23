"""
Test script to verify Research Agent uses LLM for research.
Tests with a simple query: "Give me a short random joke"
"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
project_root = Path(__file__).resolve().parent
env_path = project_root / ".env"
load_dotenv(dotenv_path=env_path, override=False)

print("=" * 70)
print("Research Agent LLM Test")
print("=" * 70)
print()

# Set up environment
os.environ["Q2O_USE_LLM"] = "true"

# Import after env is set
from agents.researcher_agent import ResearcherAgent
from agents.base_agent import Task, AgentType

# Create research agent
print("1. Initializing Research Agent...")
print("-" * 70)
agent = ResearcherAgent(
    agent_id="test_researcher",
    workspace_path=".",
    project_id="test-project",
    tenant_id=None
)

print(f"LLM Enabled: {agent.llm_enabled}")
print(f"LLM Service Available: {agent.llm_service is not None}")
print()

# Create a test task
print("2. Creating test research task...")
print("-" * 70)
test_query = "Give me a short random joke"
task = Task(
    id="test_research_001",
    title=f"Research: {test_query}",
    description=test_query,
    agent_type=AgentType.RESEARCHER,
    metadata={
        "research_query": test_query,
        "complexity": "low"
    }
)

print(f"Query: {test_query}")
print()

# Process the task
print("3. Processing research task...")
print("-" * 70)
try:
    result_task = agent.process_task(task)
    
    print()
    print("4. Results:")
    print("-" * 70)
    
    if result_task.result:
        print(f"Status: {result_task.result.get('status', 'unknown')}")
        print(f"Research ID: {result_task.result.get('research_id', 'N/A')}")
        print(f"Results Count: {result_task.result.get('results_count', 0)}")
        print(f"Confidence Score: {result_task.result.get('confidence_score', 0)}")
        print(f"Cached: {result_task.result.get('cached', False)}")
        print()
        
        # Check metadata for research results
        if result_task.metadata.get("research_results"):
            research_results = result_task.metadata["research_results"]
            sources = research_results.get('sources_consulted', [])
            print(f"Sources Consulted: {', '.join(sources)}")
            
            if 'llm_research' in sources or 'llm_research_text' in sources:
                print("[SUCCESS] LLM was used for research!")
                print()
                print("Key Findings:")
                findings = research_results.get('key_findings', [])
                for i, finding in enumerate(findings[:5], 1):
                    print(f"  {i}. {finding}")
                
                if research_results.get('llm_provider'):
                    print()
                    print(f"LLM Provider: {research_results.get('llm_provider')}")
                    print(f"LLM Model: {research_results.get('llm_model', 'N/A')}")
            else:
                print("[INFO] Web search was used (LLM may have failed or was not primary)")
                print()
                print("Search Results:")
                search_results = research_results.get('search_results', [])
                for i, result in enumerate(search_results[:3], 1):
                    print(f"  {i}. {result.get('title', 'No title')}")
                    print(f"     {result.get('url', 'No URL')}")
        else:
            print("[WARNING] No research results in metadata")
    else:
        print("[ERROR] Task processing failed or returned no result")
        
except Exception as e:
    print(f"[ERROR] Exception during research: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 70)

