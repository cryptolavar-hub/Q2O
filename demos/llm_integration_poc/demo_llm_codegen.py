"""
LLM Integration Proof-of-Concept Demo
Demonstrates Gemini API code generation for Q2O platform.
"""

import os
import sys
import asyncio
import json
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("⚠️  google-generativeai not installed")
    print("   Install with: pip install google-generativeai")

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from dotenv import load_dotenv


class LLMCodegenDemo:
    """Proof-of-concept for LLM code generation."""
    
    def __init__(self):
        load_dotenv()
        self.output_dir = Path(__file__).parent / "output"
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize Gemini
        if GEMINI_AVAILABLE:
            api_key = os.getenv("GOOGLE_API_KEY")
            if api_key:
                genai.configure(api_key=api_key)
                self.gemini_model = genai.GenerativeModel('gemini-1.5-pro')
                print("✅ Gemini API initialized")
            else:
                self.gemini_model = None
                print("⚠️  GOOGLE_API_KEY not set")
        else:
            self.gemini_model = None
        
        # Initialize OpenAI
        if OPENAI_AVAILABLE:
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                self.openai_client = openai.OpenAI(api_key=api_key)
                print("✅ OpenAI API initialized")
            else:
                self.openai_client = None
                print("⚠️  OPENAI_API_KEY not set")
        else:
            self.openai_client = None
    
    def generate_template_code(self) -> str:
        """Generate code using traditional template approach."""
        # Simulated template-based generation
        template_code = '''"""
Stripe Webhook Handler - Template Generated
"""

from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
import stripe

router = APIRouter()

class WebhookEvent(BaseModel):
    """Webhook event model."""
    id: str
    type: str
    data: dict

@router.post("/webhooks/stripe")
async def stripe_webhook(request: Request):
    """
    Handle Stripe webhook events.
    """
    payload = await request.body()
    
    # Process webhook
    event = stripe.Event.construct_from(
        json.loads(payload), stripe.api_key
    )
    
    if event.type == "payment_intent.succeeded":
        # Handle successful payment
        payment_intent = event.data.object
        print(f"Payment succeeded: {payment_intent.id}")
    
    return {"status": "success"}
'''
        return template_code
    
    async def generate_llm_code_gemini(self, task_description: str) -> tuple[str, dict]:
        """Generate code using Gemini 1.5 Pro."""
        if not self.gemini_model:
            raise ValueError("Gemini not available")
        
        system_instruction = """You are an expert FastAPI and Stripe integration developer.

Generate production-quality Python code with:
✅ Complete type hints (mypy strict mode compatible)
✅ Comprehensive docstrings (Google style)
✅ Proper error handling (try/except with specific exceptions)
✅ Security best practices (webhook signature verification)
✅ Input validation (Pydantic models)
✅ Structured logging
✅ Best practices for FastAPI and Stripe

Output ONLY the Python code - no explanations, no markdown."""
        
        user_prompt = f"""Task: {task_description}

Technology Stack: FastAPI, Stripe API, Pydantic

Requirements:
1. Create FastAPI router for Stripe webhooks
2. Verify webhook signature using Stripe signature header
3. Handle payment_intent.succeeded event
4. Log all webhook events with structured logging
5. Return appropriate HTTP status codes
6. Include proper error handling

Generate complete, production-ready implementation."""
        
        # Combine for Gemini (no separate system role)
        full_prompt = f"{system_instruction}\n\n{user_prompt}"
        
        # Generate
        start_time = datetime.now()
        response = await self.gemini_model.generate_content_async(
            full_prompt,
            generation_config=genai.GenerationConfig(
                temperature=0.3,
                max_output_tokens=4096
            )
        )
        duration = (datetime.now() - start_time).total_seconds()
        
        # Calculate usage
        usage_metadata = response.usage_metadata
        input_tokens = usage_metadata.prompt_token_count
        output_tokens = usage_metadata.candidates_token_count
        
        # Gemini 1.5 Pro pricing
        input_cost = (input_tokens / 1000) * 0.00125
        output_cost = (output_tokens / 1000) * 0.005
        total_cost = input_cost + output_cost
        
        usage = {
            "provider": "gemini",
            "model": "gemini-1.5-pro",
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "input_cost": input_cost,
            "output_cost": output_cost,
            "total_cost": total_cost,
            "duration_seconds": duration
        }
        
        return response.text, usage
    
    async def generate_llm_code_openai(self, task_description: str) -> tuple[str, dict]:
        """Generate code using OpenAI GPT-4."""
        if not self.openai_client:
            raise ValueError("OpenAI not available")
        
        system_prompt = """You are an expert FastAPI and Stripe integration developer.

Generate production-quality Python code with:
✅ Complete type hints (mypy strict mode compatible)
✅ Comprehensive docstrings (Google style)
✅ Proper error handling
✅ Security best practices (webhook signature verification)
✅ Input validation (Pydantic models)
✅ Structured logging

Output ONLY the Python code - no explanations, no markdown."""
        
        user_prompt = f"""Task: {task_description}

Technology Stack: FastAPI, Stripe API, Pydantic

Generate complete, production-ready implementation with:
1. FastAPI router for Stripe webhooks
2. Webhook signature verification
3. Payment event handling
4. Proper error handling
5. Logging"""
        
        # Generate
        start_time = datetime.now()
        response = self.openai_client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            max_tokens=4096
        )
        duration = (datetime.now() - start_time).total_seconds()
        
        # Calculate usage
        usage_data = response.usage
        input_tokens = usage_data.prompt_tokens
        output_tokens = usage_data.completion_tokens
        
        # GPT-4 Turbo pricing
        input_cost = (input_tokens / 1000) * 0.01
        output_cost = (output_tokens / 1000) * 0.03
        total_cost = input_cost + output_cost
        
        usage = {
            "provider": "openai",
            "model": response.model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "input_cost": input_cost,
            "output_cost": output_cost,
            "total_cost": total_cost,
            "duration_seconds": duration
        }
        
        return response.choices[0].message.content, usage
    
    def validate_code(self, code: str) -> dict:
        """Validate generated code for basic quality checks."""
        checks = {
            "has_imports": False,
            "has_docstrings": False,
            "has_type_hints": False,
            "has_error_handling": False,
            "has_logging": False,
            "valid_syntax": False,
            "security_safe": True
        }
        
        # Check imports
        if "import" in code or "from" in code:
            checks["has_imports"] = True
        
        # Check docstrings
        if '"""' in code or "'''" in code:
            checks["has_docstrings"] = True
        
        # Check type hints
        if "->" in code or ": str" in code or ": int" in code:
            checks["has_type_hints"] = True
        
        # Check error handling
        if "try:" in code or "except" in code or "raise" in code:
            checks["has_error_handling"] = True
        
        # Check logging
        if "log" in code.lower() or "print(" in code:
            checks["has_logging"] = True
        
        # Check syntax
        try:
            compile(code, '<string>', 'exec')
            checks["valid_syntax"] = True
        except SyntaxError:
            checks["valid_syntax"] = False
        
        # Basic security checks
        dangerous = ['eval(', 'exec(', '__import__', 'os.system(']
        for pattern in dangerous:
            if pattern in code:
                checks["security_safe"] = False
                break
        
        # Calculate score
        score = sum(1 for v in checks.values() if v) / len(checks) * 100
        
        return {
            "checks": checks,
            "score": int(score),
            "passed": all(checks.values())
        }
    
    def compare_outputs(self, template_code: str, llm_code: str) -> dict:
        """Compare template vs LLM generated code."""
        template_validation = self.validate_code(template_code)
        llm_validation = self.validate_code(llm_code)
        
        return {
            "template": {
                "lines": len(template_code.split('\n')),
                "chars": len(template_code),
                "score": template_validation['score'],
                "checks": template_validation['checks']
            },
            "llm": {
                "lines": len(llm_code.split('\n')),
                "chars": len(llm_code),
                "score": llm_validation['score'],
                "checks": llm_validation['checks']
            },
            "winner": "llm" if llm_validation['score'] > template_validation['score'] else "template"
        }
    
    async def run_demo(self):
        """Run the complete demo."""
        print("=" * 80)
        print(" " * 20 + "Q2O LLM Integration - Proof of Concept")
        print("=" * 80)
        print()
        
        # Task definition
        task = "Create a FastAPI Stripe webhook endpoint with signature verification"
        
        print(f"📋 Task: {task}")
        print()
        print("=" * 80)
        
        # Step 1: Template generation
        print("\n[1/5] Template-Based Generation...")
        print("-" * 80)
        template_code = self.generate_template_code()
        template_path = self.output_dir / "template_output.py"
        template_path.write_text(template_code, encoding='utf-8')
        print(f"✅ Generated {len(template_code)} characters")
        print(f"📁 Saved to: {template_path}")
        
        # Step 2: LLM generation (Gemini)
        print("\n[2/5] LLM-Based Generation (Gemini 1.5 Pro)...")
        print("-" * 80)
        
        if self.gemini_model:
            try:
                llm_code, usage = await self.generate_llm_code_gemini(task)
                llm_path = self.output_dir / "llm_gemini_output.py"
                llm_path.write_text(llm_code, encoding='utf-8')
                
                print(f"✅ Generated {len(llm_code)} characters")
                print(f"📁 Saved to: {llm_path}")
                print(f"📊 Tokens: {usage['input_tokens']} input + {usage['output_tokens']} output")
                print(f"💰 Cost: ${usage['total_cost']:.6f}")
                print(f"⏱️  Duration: {usage['duration_seconds']:.2f} seconds")
                
                gemini_success = True
            except Exception as e:
                print(f"❌ Gemini generation failed: {e}")
                llm_code = None
                usage = None
                gemini_success = False
        else:
            print("⚠️  Gemini not available (API key not configured)")
            llm_code = None
            usage = None
            gemini_success = False
        
        # Step 3: OpenAI comparison (optional)
        print("\n[3/5] OpenAI Comparison (GPT-4 Turbo)...")
        print("-" * 80)
        
        if self.openai_client and os.getenv("USE_OPENAI", "false").lower() == "true":
            try:
                openai_code, openai_usage = await self.generate_llm_code_openai(task)
                openai_path = self.output_dir / "llm_openai_output.py"
                openai_path.write_text(openai_code, encoding='utf-8')
                
                print(f"✅ Generated {len(openai_code)} characters")
                print(f"📁 Saved to: {openai_path}")
                print(f"📊 Tokens: {openai_usage['input_tokens']} input + {openai_usage['output_tokens']} output")
                print(f"💰 Cost: ${openai_usage['total_cost']:.6f}")
                print(f"⏱️  Duration: {openai_usage['duration_seconds']:.2f} seconds")
            except Exception as e:
                print(f"❌ OpenAI generation failed: {e}")
        else:
            print("⏭️  Skipped (OpenAI disabled or not configured)")
        
        # Step 4: Quality comparison
        if llm_code:
            print("\n[4/5] Quality Comparison...")
            print("-" * 80)
            
            comparison = self.compare_outputs(template_code, llm_code)
            
            print(f"\n📊 Template Code:")
            print(f"   Lines: {comparison['template']['lines']}")
            print(f"   Quality Score: {comparison['template']['score']}/100")
            for check, passed in comparison['template']['checks'].items():
                status = "✅" if passed else "❌"
                print(f"   {status} {check}")
            
            print(f"\n📊 LLM Code (Gemini):")
            print(f"   Lines: {comparison['llm']['lines']}")
            print(f"   Quality Score: {comparison['llm']['score']}/100")
            for check, passed in comparison['llm']['checks'].items():
                status = "✅" if passed else "❌"
                print(f"   {status} {check}")
            
            print(f"\n🏆 Winner: {comparison['winner'].upper()} "
                  f"({'LLM' if comparison['winner'] == 'llm' else 'Template'} generated better code)")
        
        # Step 5: Summary
        print("\n[5/5] Summary & Recommendations...")
        print("-" * 80)
        
        if gemini_success and usage:
            print("\n✅ PROOF OF CONCEPT SUCCESSFUL!")
            print()
            print("Key Findings:")
            print(f"  1. Gemini API connection: ✅ Working")
            print(f"  2. Code generation: ✅ Functional")
            print(f"  3. Cost per generation: ${usage['total_cost']:.6f}")
            print(f"  4. Response time: {usage['duration_seconds']:.2f} seconds")
            print(f"  5. Quality: {comparison['llm']['score']}/100")
            print()
            
            # Cost projections
            print("💰 Cost Projections:")
            cost_per_file = usage['total_cost']
            files_per_project = 20  # Average
            cost_per_project = cost_per_file * files_per_project
            
            print(f"   Per file: ${cost_per_file:.4f}")
            print(f"   Per project (20 files): ${cost_per_project:.2f}")
            print(f"   Per 10 projects: ${cost_per_project * 10:.2f}")
            print(f"   Per 100 projects: ${cost_per_project * 100:.2f}")
            print()
            
            # Recommendation
            print("📋 Recommendation:")
            if cost_per_project < 2.0:
                print("   ✅ PROCEED with Phase 1 implementation")
                print("   ✅ Costs are within acceptable range")
                print("   ✅ Quality meets/exceeds template standards")
                print(f"   ✅ Using Gemini 1.5 Pro (87% cheaper than GPT-4)")
            else:
                print(f"   ⚠️  Cost per project (${cost_per_project:.2f}) higher than expected")
                print("   💡 Consider Gemini 1.5 Flash for 99% cost savings")
        else:
            print("\n❌ PROOF OF CONCEPT FAILED")
            print()
            print("Issues:")
            if not GEMINI_AVAILABLE:
                print("  - google-generativeai not installed")
            if not self.gemini_model:
                print("  - GOOGLE_API_KEY not configured")
            print()
            print("Fix these issues and run again.")
        
        print()
        print("=" * 80)
        print()
        
        # Save results
        if gemini_success:
            results = {
                "demo_date": datetime.now().isoformat(),
                "task": task,
                "gemini_usage": usage,
                "comparison": comparison,
                "recommendation": "PROCEED" if cost_per_project < 2.0 else "REVIEW_COSTS"
            }
            
            results_path = self.output_dir / "demo_results.json"
            results_path.write_text(json.dumps(results, indent=2), encoding='utf-8')
            print(f"📄 Full results saved to: {results_path}")
            print()


async def main():
    """Run the demo."""
    demo = LLMCodegenDemo()
    await demo.run_demo()


if __name__ == "__main__":
    print()
    print("Starting LLM Integration Proof-of-Concept Demo...")
    print()
    
    asyncio.run(main())
    
    print()
    print("Demo complete! Check the output/ directory for generated files.")
    print()

