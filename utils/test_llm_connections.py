"""
Test LLM API Connections
Verifies that API keys are configured correctly and providers are accessible.
"""

import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Check for dependencies
DEPENDENCIES = {
    'google.generativeai': 'google-generativeai',
    'openai': 'openai',
    'anthropic': 'anthropic'
}

missing_deps = []
for module, package in DEPENDENCIES.items():
    try:
        __import__(module)
    except ImportError:
        missing_deps.append(package)

if missing_deps:
    print("❌ Missing dependencies:")
    for dep in missing_deps:
        print(f"   pip install {dep}")
    print()
    sys.exit(1)

import google.generativeai as genai
import openai
from anthropic import Anthropic


async def test_gemini():
    """Test Gemini API connection."""
    print("\n[1/3] Testing Gemini 1.5 Pro API...")
    print("-" * 60)
    
    api_key = os.getenv("GOOGLE_API_KEY")
    
    if not api_key:
        print("❌ GOOGLE_API_KEY not set in .env")
        return False
    
    if not api_key.startswith("AIzaSy"):
        print("⚠️  API key doesn't start with 'AIzaSy' - might be invalid")
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-pro')
        
        # Test with simple request
        response = await model.generate_content_async(
            "Say 'Gemini API working!' if you can read this."
        )
        
        print(f"✅ Connection successful!")
        print(f"   Response: {response.text}")
        print(f"   Tokens: {response.usage_metadata.prompt_token_count} input, "
              f"{response.usage_metadata.candidates_token_count} output")
        
        # Calculate cost
        input_cost = (response.usage_metadata.prompt_token_count / 1000) * 0.00125
        output_cost = (response.usage_metadata.candidates_token_count / 1000) * 0.005
        total_cost = input_cost + output_cost
        print(f"   Cost: ${total_cost:.6f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False


async def test_openai():
    """Test OpenAI API connection."""
    print("\n[2/3] Testing OpenAI GPT-4 Turbo API...")
    print("-" * 60)
    
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print("❌ OPENAI_API_KEY not set in .env")
        return False
    
    if not api_key.startswith("sk-"):
        print("⚠️  API key doesn't start with 'sk-' - might be invalid")
    
    try:
        client = openai.OpenAI(api_key=api_key)
        
        # Test with simple request
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[{
                "role": "user",
                "content": "Say 'OpenAI API working!' if you can read this."
            }],
            max_tokens=20
        )
        
        print(f"✅ Connection successful!")
        print(f"   Response: {response.choices[0].message.content}")
        print(f"   Model: {response.model}")
        print(f"   Tokens: {response.usage.prompt_tokens} input, "
              f"{response.usage.completion_tokens} output")
        
        # Calculate cost
        input_cost = (response.usage.prompt_tokens / 1000) * 0.01
        output_cost = (response.usage.completion_tokens / 1000) * 0.03
        total_cost = input_cost + output_cost
        print(f"   Cost: ${total_cost:.6f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False


async def test_anthropic():
    """Test Anthropic Claude API connection."""
    print("\n[3/3] Testing Anthropic Claude API...")
    print("-" * 60)
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    
    if not api_key:
        print("⚠️  ANTHROPIC_API_KEY not set in .env (optional)")
        return None  # Not required
    
    if not api_key.startswith("sk-ant-"):
        print("⚠️  API key doesn't start with 'sk-ant-' - might be invalid")
    
    try:
        client = Anthropic(api_key=api_key)
        
        # Test with simple request
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=20,
            messages=[{
                "role": "user",
                "content": "Say 'Claude API working!' if you can read this."
            }]
        )
        
        print(f"✅ Connection successful!")
        print(f"   Response: {response.content[0].text}")
        print(f"   Model: {response.model}")
        print(f"   Tokens: {response.usage.input_tokens} input, "
              f"{response.usage.output_tokens} output")
        
        return True
        
    except Exception as e:
        print(f"⚠️  Connection failed: {e} (optional provider)")
        return None


async def main():
    """Run all connection tests."""
    print("=" * 60)
    print(" " * 15 + "Q2O LLM API Connection Test")
    print("=" * 60)
    
    results = await asyncio.gather(
        test_gemini(),
        test_openai(),
        test_anthropic(),
        return_exceptions=True
    )
    
    print("\n" + "=" * 60)
    print("  CONNECTION TEST SUMMARY")
    print("=" * 60)
    
    gemini_ok = results[0] if not isinstance(results[0], Exception) else False
    openai_ok = results[1] if not isinstance(results[1], Exception) else False
    claude_ok = results[2] if not isinstance(results[2], Exception) else None
    
    print(f"\n✅ Gemini 1.5 Pro: {'READY' if gemini_ok else 'NOT CONFIGURED'}")
    print(f"✅ OpenAI GPT-4:   {'READY' if openai_ok else 'NOT CONFIGURED'}")
    print(f"{'✅' if claude_ok else '⚠️ '} Anthropic Claude: {'READY' if claude_ok else 'NOT CONFIGURED (optional)'}")
    
    print()
    
    if gemini_ok and openai_ok:
        print("🎉 ALL REQUIRED PROVIDERS READY!")
        print()
        print("✅ Gemini configured (Primary - 87% cheaper)")
        print("✅ OpenAI configured (Fallback - Premium quality)")
        print()
        print("Next steps:")
        print("  1. Review configuration in env.llm.example.txt")
        print("  2. Begin Phase 1 implementation (LLMService + CoderAgent)")
        print("  3. Expected completion: 7-9 days")
        print()
        return 0
    
    elif gemini_ok:
        print("⚠️  Partial Configuration")
        print()
        print("✅ Gemini configured (works alone, but no fallback)")
        print("❌ OpenAI not configured (fallback won't work)")
        print()
        print("Recommendation: Configure OpenAI for production reliability")
        print()
        return 1
    
    else:
        print("❌ PROVIDERS NOT CONFIGURED")
        print()
        print("Required API keys missing. Please:")
        print("  1. Get Gemini key: https://makersuite.google.com/app/apikey")
        print("  2. Get OpenAI key: https://platform.openai.com/api-keys")
        print("  3. Add to .env file")
        print("  4. Run this test again")
        print()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

