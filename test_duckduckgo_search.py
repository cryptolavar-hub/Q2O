"""
Quick test script to verify DuckDuckGo search is working.
Run this to test the ResearcherAgent's search functionality.
"""

import logging
import sys
from agents.researcher_agent import WebSearcher

# Set up logging to see what's happening
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_duckduckgo_search():
    """Test DuckDuckGo search directly."""
    print("="*70)
    print("Testing DuckDuckGo Search")
    print("="*70)
    
    # Create searcher (no API keys = will use DuckDuckGo)
    searcher = WebSearcher()
    
    # Test query
    query = "Stripe billing setup with pricing tiers"
    print(f"\nQuery: {query}")
    print("-"*70)
    
    # Perform search
    results = searcher.search(query, num_results=5)
    
    # Display results
    if results:
        print(f"\n✓ SUCCESS: Found {len(results)} results\n")
        for i, result in enumerate(results, 1):
            print(f"{i}. {result['title']}")
            print(f"   URL: {result['url']}")
            print(f"   Snippet: {result['snippet'][:100]}...")
            print(f"   Source: {result['source']}")
            print()
        return True
    else:
        print("\n❌ FAILED: No results returned")
        print("\nCheck the logs above for error messages.")
        return False

if __name__ == "__main__":
    success = test_duckduckgo_search()
    sys.exit(0 if success else 1)

