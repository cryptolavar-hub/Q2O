"""
LLM Service - Unified interface for multiple LLM providers.
Handles OpenAI, Gemini, Anthropic with automatic fallback and retry logic.

Features:
- Multi-provider support (Gemini, OpenAI, Claude)
- Automatic fallback on failures
- 3 retries per provider (9 total attempts)
- Cost tracking and monitoring
- Response caching (90-day TTL)
- Rate limiting and budget controls
- 7-level progressive cost alerts
"""

from typing import Dict, Any, Optional, List, Tuple
from enum import Enum
from dataclasses import dataclass, asdict
import os
import logging
import asyncio
import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
import sqlite3

# Optional imports with fallback
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logging.warning("google-generativeai not installed - Gemini unavailable")

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logging.warning("openai not installed - OpenAI unavailable")

try:
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    logging.warning("anthropic not installed - Claude unavailable")


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    GEMINI = "gemini"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


@dataclass
class LLMUsage:
    """Track token usage and costs for a single LLM call."""
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    input_cost: float
    output_cost: float
    total_cost: float
    timestamp: datetime
    cache_hit: bool = False
    duration_seconds: float = 0.0
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data


@dataclass
class LLMResponse:
    """Unified LLM response format."""
    content: str
    usage: Optional[LLMUsage]
    provider: str
    model: str
    success: bool
    error: Optional[str] = None
    cache_hit: bool = False
    attempts: int = 1
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "content": self.content,
            "usage": self.usage.to_dict() if self.usage else None,
            "provider": self.provider,
            "model": self.model,
            "success": self.success,
            "error": self.error,
            "cache_hit": self.cache_hit,
            "attempts": self.attempts
        }


class LLMCache:
    """Cache LLM responses to reduce costs and improve speed."""
    
    def __init__(self, cache_dir: str = ".llm_cache", ttl_days: int = 90):
        """
        Initialize LLM cache.
        
        Args:
            cache_dir: Directory to store cache files
            ttl_days: Time-to-live for cached responses
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.ttl_days = ttl_days
        self.db_path = self.cache_dir / "cache_index.db"
        self._init_database()
    
    def _init_database(self):
        """Initialize cache database."""
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("""
            CREATE TABLE IF NOT EXISTS llm_cache (
                cache_key TEXT PRIMARY KEY,
                provider TEXT,
                model TEXT,
                system_prompt_hash TEXT,
                user_prompt_hash TEXT,
                response_content TEXT,
                usage_json TEXT,
                created_at TIMESTAMP,
                last_accessed TIMESTAMP,
                access_count INTEGER DEFAULT 1
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_created_at ON llm_cache(created_at)
        """)
        conn.commit()
        conn.close()
    
    def _get_cache_key(self, provider: str, system_prompt: str, user_prompt: str) -> str:
        """Generate cache key from prompts."""
        combined = f"{provider}:{system_prompt}:{user_prompt}"
        return hashlib.sha256(combined.encode()).hexdigest()
    
    def get(self, provider: str, system_prompt: str, user_prompt: str) -> Optional[Dict]:
        """
        Get cached response if available and not expired.
        
        Returns:
            Cached response dict or None
        """
        cache_key = self._get_cache_key(provider, system_prompt, user_prompt)
        
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT response_content, usage_json, created_at, access_count
            FROM llm_cache
            WHERE cache_key = ?
        """, (cache_key,))
        
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return None
        
        response_content, usage_json, created_at_str, access_count = row
        created_at = datetime.fromisoformat(created_at_str)
        
        # Check if expired
        if datetime.now() - created_at > timedelta(days=self.ttl_days):
            # Expired - delete
            cursor.execute("DELETE FROM llm_cache WHERE cache_key = ?", (cache_key,))
            conn.commit()
            conn.close()
            return None
        
        # Update access count and timestamp
        cursor.execute("""
            UPDATE llm_cache
            SET last_accessed = ?, access_count = ?
            WHERE cache_key = ?
        """, (datetime.now().isoformat(), access_count + 1, cache_key))
        
        conn.commit()
        conn.close()
        
        logging.info(f"💾 Cache hit! (saved ${json.loads(usage_json)['total_cost']:.4f}, access #{access_count + 1})")
        
        return {
            "content": response_content,
            "usage": json.loads(usage_json),
            "cache_hit": True
        }
    
    def set(self, provider: str, system_prompt: str, user_prompt: str, 
            response: str, usage: Dict):
        """Cache an LLM response."""
        cache_key = self._get_cache_key(provider, system_prompt, user_prompt)
        
        conn = sqlite3.connect(str(self.db_path))
        
        # Check if already exists
        cursor = conn.cursor()
        cursor.execute("SELECT cache_key FROM llm_cache WHERE cache_key = ?", (cache_key,))
        
        if cursor.fetchone():
            # Update existing
            conn.execute("""
                UPDATE llm_cache
                SET response_content = ?, usage_json = ?, last_accessed = ?
                WHERE cache_key = ?
            """, (response, json.dumps(usage), datetime.now().isoformat(), cache_key))
        else:
            # Insert new
            system_hash = hashlib.md5(system_prompt.encode()).hexdigest()
            user_hash = hashlib.md5(user_prompt.encode()).hexdigest()
            
            conn.execute("""
                INSERT INTO llm_cache (
                    cache_key, provider, model, system_prompt_hash, user_prompt_hash,
                    response_content, usage_json, created_at, last_accessed, access_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
            """, (
                cache_key,
                provider,
                usage.get('model', ''),
                system_hash,
                user_hash,
                response,
                json.dumps(usage),
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))
        
        conn.commit()
        conn.close()
        
        logging.debug(f"💾 Cached response for {provider}")
    
    def get_stats(self) -> Dict:
        """Get cache statistics."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT
                COUNT(*) as total_entries,
                SUM(access_count) as total_accesses,
                AVG(access_count) as avg_reuse
            FROM llm_cache
        """)
        
        row = cursor.fetchone()
        conn.close()
        
        total_entries = row[0] or 0
        total_accesses = row[1] or 0
        avg_reuse = row[2] or 0.0
        
        return {
            "total_entries": total_entries,
            "total_accesses": total_accesses,
            "avg_reuse": round(avg_reuse, 2),
            "cache_hit_rate": round((total_accesses - total_entries) / total_accesses * 100, 1) if total_accesses > 0 else 0.0
        }


class CostMonitor:
    """Monitor LLM costs with 7-level progressive alerts."""
    
    ALERT_THRESHOLDS = [0.50, 0.70, 0.80, 0.90, 0.95, 0.99, 1.00]
    
    def __init__(self, monthly_budget: float = 1000.0):
        """
        Initialize cost monitor.
        
        Args:
            monthly_budget: Monthly budget in USD
        """
        self.monthly_budget = monthly_budget
        self.monthly_spent = 0.0
        self.daily_spent = 0.0
        self.alerts_triggered = set()
        self.last_reset = datetime.now()
        
        # Load from persistent storage
        self._load_state()
    
    def _load_state(self):
        """Load monthly spending from file."""
        state_file = Path(".llm_cost_state.json")
        if state_file.exists():
            try:
                with open(state_file, 'r') as f:
                    state = json.load(f)
                    
                    # Check if we need to reset (new month)
                    last_reset = datetime.fromisoformat(state['last_reset'])
                    if last_reset.month != datetime.now().month:
                        # New month - reset
                        self.monthly_spent = 0.0
                        self.daily_spent = 0.0
                        self.alerts_triggered = set()
                        self.last_reset = datetime.now()
                    else:
                        self.monthly_spent = state.get('monthly_spent', 0.0)
                        self.daily_spent = state.get('daily_spent', 0.0)
                        self.alerts_triggered = set(state.get('alerts_triggered', []))
                        self.last_reset = last_reset
            except Exception as e:
                logging.error(f"Error loading cost state: {e}")
    
    def _save_state(self):
        """Save monthly spending to file."""
        state = {
            "monthly_spent": self.monthly_spent,
            "daily_spent": self.daily_spent,
            "alerts_triggered": list(self.alerts_triggered),
            "last_reset": self.last_reset.isoformat(),
            "monthly_budget": self.monthly_budget
        }
        
        with open(".llm_cost_state.json", 'w') as f:
            json.dump(state, f, indent=2)
    
    def check_budget(self, estimated_cost: float) -> Tuple[bool, List[str]]:
        """
        Check if we can afford this call and generate alerts.
        
        Args:
            estimated_cost: Estimated cost of the LLM call
        
        Returns:
            (allowed, alerts) tuple
        """
        projected_spent = self.monthly_spent + estimated_cost
        percentage = projected_spent / self.monthly_budget
        
        # Generate alerts for newly crossed thresholds
        new_alerts = []
        for threshold in self.ALERT_THRESHOLDS:
            threshold_int = int(threshold * 100)
            if percentage >= threshold and threshold_int not in self.alerts_triggered:
                alert_msg = self._format_alert(threshold, projected_spent)
                new_alerts.append(alert_msg)
                self.alerts_triggered.add(threshold_int)
                logging.warning(alert_msg)
        
        # Determine if call is allowed
        allowed = projected_spent <= self.monthly_budget
        
        if not allowed:
            logging.error(f"🛑 Budget exceeded: ${projected_spent:.2f} > ${self.monthly_budget}")
        
        return allowed, new_alerts
    
    def _format_alert(self, threshold: float, spent: float) -> str:
        """Format alert message based on threshold."""
        percentage = int(threshold * 100)
        remaining = self.monthly_budget - spent
        
        alerts = {
            50: f"[ALERT-50%] Budget Alert: 50% used (${spent:.2f} of ${self.monthly_budget:.2f}, ${remaining:.2f} remaining)",
            70: f"[ALERT-70%] Budget Alert: 70% used (${spent:.2f} of ${self.monthly_budget:.2f}, ${remaining:.2f} remaining)",
            80: f"[ALERT-80%] Budget Alert: 80% used (${spent:.2f} of ${self.monthly_budget:.2f}, ${remaining:.2f} remaining)",
            90: f"[ALERT-90%] Budget Alert: 90% used (${spent:.2f} of ${self.monthly_budget:.2f}) - Consider template-only mode",
            95: f"[ALERT-95%] Budget Alert: 95% used (${spent:.2f} of ${self.monthly_budget:.2f}) - Approaching limit!",
            99: f"[ALERT-99%] Budget Alert: 99% used (${spent:.2f} of ${self.monthly_budget:.2f}) - CRITICAL!",
            100: f"[LIMIT] Budget Exceeded: ${spent:.2f} of ${self.monthly_budget:.2f} - LLM disabled, templates only"
        }
        
        return alerts.get(percentage, f"Budget: {percentage}% (${spent:.2f})")
    
    def record_cost(self, cost: float, provider: str):
        """
        Record actual cost incurred.
        
        Args:
            cost: Cost in USD
            provider: Provider name
        """
        self.monthly_spent += cost
        self.daily_spent += cost
        self._save_state()
        
        percentage = (self.monthly_spent / self.monthly_budget) * 100
        
        logging.info(
            f"💰 Cost recorded: ${cost:.4f} ({provider}) - "
            f"Monthly: ${self.monthly_spent:.2f} / ${self.monthly_budget:.2f} ({percentage:.1f}%)"
        )
    
    def get_budget_status(self) -> Dict:
        """Get current budget status."""
        percentage = (self.monthly_spent / self.monthly_budget) * 100
        
        return {
            "monthly_budget": self.monthly_budget,
            "monthly_spent": round(self.monthly_spent, 2),
            "monthly_remaining": round(self.monthly_budget - self.monthly_spent, 2),
            "percentage_used": round(percentage, 1),
            "daily_spent": round(self.daily_spent, 2),
            "alerts_triggered": list(self.alerts_triggered),
            "budget_exceeded": self.monthly_spent >= self.monthly_budget
        }


class LLMService:
    """
    Unified LLM service for Q2O agents.
    
    Features:
    - Multiple provider support (Gemini, OpenAI, Anthropic)
    - Automatic fallback with retry logic
    - Cost tracking and budget monitoring
    - Response caching (90-day TTL)
    - Rate limiting
    - 7-level progressive cost alerts
    
    Provider Chain:
    1. Gemini 1.5 Pro (3 attempts) - Primary (cheapest)
    2. OpenAI GPT-4 (3 attempts) - Fallback (premium)
    3. Anthropic Claude (3 attempts) - Tertiary (alternative)
    Total: 9 attempts before complete failure
    """
    
    PROVIDER_CHAIN = [
        LLMProvider.GEMINI,
        LLMProvider.OPENAI,
        LLMProvider.ANTHROPIC
    ]
    
    MAX_RETRIES_PER_PROVIDER = 3
    
    def __init__(
        self,
        primary: Optional[LLMProvider] = None,
        monthly_budget: float = None,
        cache_enabled: bool = None
    ):
        """
        Initialize LLM service.
        
        Args:
            primary: Primary provider (overrides env config)
            monthly_budget: Monthly budget in USD (overrides env)
            cache_enabled: Enable caching (overrides env)
        """
        # Configuration from environment
        self.primary = primary or LLMProvider(os.getenv("Q2O_LLM_PRIMARY", "gemini"))
        self.use_llm = os.getenv("Q2O_USE_LLM", "true").lower() == "true"
        
        # Budget monitoring
        budget = monthly_budget or float(os.getenv("Q2O_LLM_MONTHLY_BUDGET", "1000.0"))
        self.cost_monitor = CostMonitor(monthly_budget=budget)
        
        # Caching
        cache_enabled = cache_enabled if cache_enabled is not None else os.getenv("Q2O_LLM_CACHE_ENABLED", "true").lower() == "true"
        if cache_enabled:
            cache_dir = os.getenv("Q2O_LLM_CACHE_DIR", ".llm_cache")
            cache_ttl = int(os.getenv("Q2O_LLM_CACHE_TTL_DAYS", "90"))
            self.cache = LLMCache(cache_dir=cache_dir, ttl_days=cache_ttl)
        else:
            self.cache = None
        
        # Usage tracking
        self.usage_log: List[LLMUsage] = []
        self.total_calls = 0
        self.successful_calls = 0
        self.failed_calls = 0
        self.cache_hits = 0
        
        # Model names (will be set during initialization)
        self.gemini_model_name = None
        self.openai_model_name = None
        self.anthropic_model_name = None
        
        # Initialize providers
        self._init_gemini()
        self._init_openai()
        self._init_anthropic()
        
        logging.info(f"[OK] LLMService initialized (primary: {self.primary}, budget: ${budget}/month)")
    
    def _init_gemini(self):
        """Initialize Gemini client."""
        if not GEMINI_AVAILABLE:
            self.gemini_model = None
            return
        
        api_key = os.getenv("GOOGLE_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
            model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
            self.gemini_model = genai.GenerativeModel(model_name)
            self.gemini_model_name = model_name  # Store actual model name
            logging.info(f"[OK] Gemini initialized ({model_name})")
        else:
            self.gemini_model = None
            self.gemini_model_name = None
            logging.warning("[WARNING] GOOGLE_API_KEY not set - Gemini unavailable")
    
    def _init_openai(self):
        """Initialize OpenAI client."""
        if not OPENAI_AVAILABLE:
            self.openai_client = None
            return
        
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            self.openai_client = openai.OpenAI(api_key=api_key)
            self.openai_model_name = os.getenv("OPENAI_MODEL", "gpt-4-turbo")  # Store actual model name
            logging.info(f"[OK] OpenAI initialized ({self.openai_model_name})")
        else:
            self.openai_client = None
            self.openai_model_name = None
            logging.warning("[WARNING] OPENAI_API_KEY not set - OpenAI unavailable")
    
    def _init_anthropic(self):
        """Initialize Anthropic client."""
        if not ANTHROPIC_AVAILABLE:
            self.anthropic_client = None
            return
        
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if api_key:
            self.anthropic_client = Anthropic(api_key=api_key)
            self.anthropic_model_name = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")  # Store actual model name
            logging.info(f"[OK] Anthropic initialized ({self.anthropic_model_name})")
        else:
            self.anthropic_client = None
            self.anthropic_model_name = None
            logging.debug("[INFO] ANTHROPIC_API_KEY not set - Claude unavailable (optional)")
    
    def _is_provider_available(self, provider: LLMProvider) -> bool:
        """Check if a provider is configured and available."""
        if provider == LLMProvider.GEMINI:
            return self.gemini_model is not None
        elif provider == LLMProvider.OPENAI:
            return self.openai_client is not None
        elif provider == LLMProvider.ANTHROPIC:
            return self.anthropic_client is not None
        return False
    
    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        provider: Optional[LLMProvider] = None
    ) -> LLMResponse:
        """
        Generate completion using provider chain with retries.
        
        Flow:
        1. Check cache first
        2. Check budget
        3. Try primary provider (3 retries with exponential backoff)
        4. If all fail, try secondary provider (3 retries)
        5. If all fail, try tertiary provider (3 retries)
        6. If all 9 attempts fail, return error
        
        Args:
            system_prompt: System instruction
            user_prompt: User query
            temperature: Randomness (0.0-1.0)
            max_tokens: Maximum output tokens
            provider: Force specific provider (None = use chain)
        
        Returns:
            LLMResponse with content and metadata
        """
        self.total_calls += 1
        
        # Check cache first
        if self.cache:
            provider_str = str(provider or self.primary)
            cached = self.cache.get(provider_str, system_prompt, user_prompt)
            if cached:
                self.cache_hits += 1
                return LLMResponse(
                    content=cached['content'],
                    usage=LLMUsage(**cached['usage']),
                    provider=provider_str,
                    model=cached['usage']['model'],
                    success=True,
                    cache_hit=True
                )
        
        # Estimate cost for budget check
        estimated_tokens = len(system_prompt) / 4 + len(user_prompt) / 4 + max_tokens
        estimated_cost = (estimated_tokens / 1000) * 0.01  # Rough estimate
        
        # Check budget
        allowed, alerts = self.cost_monitor.check_budget(estimated_cost)
        if not allowed:
            logging.error("🛑 Budget exceeded - LLM call blocked")
            return LLMResponse(
                content="",
                usage=None,
                provider="",
                model="",
                success=False,
                error="Monthly budget exceeded - LLM disabled, use templates only"
            )
        
        # Try provider chain with retries
        if provider:
            # Single provider specified
            response = await self._try_provider_with_retries(
                provider, system_prompt, user_prompt, temperature, max_tokens
            )
        else:
            # Try full chain
            response = await self._try_chain(
                system_prompt, user_prompt, temperature, max_tokens
            )
        
        # Update stats
        if response.success:
            self.successful_calls += 1
            
            # Record actual cost
            if response.usage:
                self.cost_monitor.record_cost(response.usage.total_cost, response.provider)
                
                # Cache successful response
                if self.cache:
                    self.cache.set(
                        response.provider,
                        system_prompt,
                        user_prompt,
                        response.content,
                        response.usage.to_dict()
                    )
                
                # Log to database (background task, non-blocking)
                try:
                    import uuid
                    from utils.llm_logger import log_llm_usage_background
                    import os
                    
                    request_id = str(uuid.uuid4())
                    log_llm_usage_background(
                        request_id=request_id,
                        provider=response.provider,
                        model=response.model,
                        usage=response.usage,
                        duration_seconds=response.usage.duration_seconds,
                        success=True,
                        cache_hit=response.cache_hit,
                        project_id=os.getenv("Q2O_PROJECT_ID"),
                        agent_type=os.getenv("Q2O_AGENT_TYPE", "unknown"),
                        agent_id=os.getenv("Q2O_AGENT_ID"),
                        system_prompt=system_prompt,
                        user_prompt=user_prompt,
                        response_content=response.content[:500] if response.content else None,
                    )
                except Exception as e:
                    # Logging failure shouldn't break LLM calls
                    logging.debug(f"Failed to log LLM usage: {e}")
        else:
            self.failed_calls += 1
            
            # Log failed call
            try:
                import uuid
                from utils.llm_logger import log_llm_usage_background
                import os
                
                request_id = str(uuid.uuid4())
                log_llm_usage_background(
                    request_id=request_id,
                    provider=response.provider,
                    model=response.model or "unknown",
                    usage=None,
                    duration_seconds=0.0,
                    success=False,
                    error_message=response.error,
                    project_id=os.getenv("Q2O_PROJECT_ID"),
                    agent_type=os.getenv("Q2O_AGENT_TYPE", "unknown"),
                    agent_id=os.getenv("Q2O_AGENT_ID"),
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                )
            except Exception as e:
                logging.debug(f"Failed to log failed LLM call: {e}")
        
        return response
    
    async def _try_chain(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_tokens: int
    ) -> LLMResponse:
        """Try all providers in chain with retries."""
        total_attempts = 0
        
        for provider in self.PROVIDER_CHAIN:
            if not self._is_provider_available(provider):
                logging.debug(f"Skipping {provider} (not configured)")
                continue
            
            logging.info(f"Trying {provider} (up to {self.MAX_RETRIES_PER_PROVIDER} attempts)")
            
            response = await self._try_provider_with_retries(
                provider, system_prompt, user_prompt, temperature, max_tokens
            )
            
            total_attempts += response.attempts
            
            if response.success:
                response.attempts = total_attempts
                return response
        
        # All providers failed
        logging.error(f"❌ All providers failed after {total_attempts} attempts")
        
        return LLMResponse(
            content="",
            usage=None,
            provider="none",
            model="",
            success=False,
            error=f"All LLM providers exhausted ({total_attempts} attempts)",
            attempts=total_attempts
        )
    
    async def _try_provider_with_retries(
        self,
        provider: LLMProvider,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_tokens: int
    ) -> LLMResponse:
        """Try a single provider with exponential backoff retries."""
        for attempt in range(1, self.MAX_RETRIES_PER_PROVIDER + 1):
            try:
                start_time = datetime.now()
                
                if provider == LLMProvider.GEMINI:
                    response = await self._gemini_complete(
                        system_prompt, user_prompt, temperature, max_tokens
                    )
                elif provider == LLMProvider.OPENAI:
                    response = await self._openai_complete(
                        system_prompt, user_prompt, temperature, max_tokens
                    )
                elif provider == LLMProvider.ANTHROPIC:
                    response = await self._anthropic_complete(
                        system_prompt, user_prompt, temperature, max_tokens
                    )
                else:
                    raise ValueError(f"Unknown provider: {provider}")
                
                duration = (datetime.now() - start_time).total_seconds()
                response.usage.duration_seconds = duration
                response.attempts = attempt
                
                logging.info(f"✅ {provider} succeeded on attempt {attempt} ({duration:.2f}s, ${response.usage.total_cost:.4f})")
                
                return response
                
            except Exception as e:
                logging.warning(f"⚠️  {provider} attempt {attempt}/{self.MAX_RETRIES_PER_PROVIDER} failed: {e}")
                
                if attempt < self.MAX_RETRIES_PER_PROVIDER:
                    # Exponential backoff: 2^attempt seconds
                    delay = 2 ** attempt
                    logging.debug(f"   Retrying in {delay} seconds...")
                    await asyncio.sleep(delay)
        
        # All retries exhausted for this provider
        return LLMResponse(
            content="",
            usage=None,
            provider=str(provider),
            model="",
            success=False,
            error=f"{provider} failed after {self.MAX_RETRIES_PER_PROVIDER} attempts",
            attempts=self.MAX_RETRIES_PER_PROVIDER
        )
    
    async def _gemini_complete(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_tokens: int
    ) -> LLMResponse:
        """Generate completion using Gemini."""
        if not self.gemini_model:
            raise ValueError("Gemini not available")
        
        # Gemini doesn't have separate system/user roles, combine them
        full_prompt = f"{system_prompt}\n\n{user_prompt}"
        
        response = await self.gemini_model.generate_content_async(
            full_prompt,
            generation_config=genai.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens
            )
        )
        
        # Calculate usage and cost
        input_tokens = response.usage_metadata.prompt_token_count
        output_tokens = response.usage_metadata.candidates_token_count
        total_tokens = input_tokens + output_tokens
        
        # Gemini 1.5 Pro pricing (November 2025)
        input_cost = (input_tokens / 1000) * 0.00125
        output_cost = (output_tokens / 1000) * 0.005
        total_cost = input_cost + output_cost
        
        # Get actual model name from the model object or stored name
        actual_model_name = self.gemini_model_name or os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        
        usage = LLMUsage(
            provider="gemini",
            model=actual_model_name,  # Use actual model name
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            input_cost=input_cost,
            output_cost=output_cost,
            total_cost=total_cost,
            timestamp=datetime.now()
        )
        
        self.usage_log.append(usage)
        
        return LLMResponse(
            content=response.text,
            usage=usage,
            provider="gemini",
            model=usage.model,
            success=True
        )
    
    async def _openai_complete(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_tokens: int
    ) -> LLMResponse:
        """Generate completion using OpenAI."""
        if not self.openai_client:
            raise ValueError("OpenAI not available")
        
        # Get actual model name from stored name or env
        model = self.openai_model_name or os.getenv("OPENAI_MODEL", "gpt-4-turbo")
        
        response = self.openai_client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        # Calculate usage and cost
        input_tokens = response.usage.prompt_tokens
        output_tokens = response.usage.completion_tokens
        total_tokens = response.usage.total_tokens
        
        # GPT-4 Turbo pricing (November 2025)
        input_cost = (input_tokens / 1000) * 0.01
        output_cost = (output_tokens / 1000) * 0.03
        total_cost = input_cost + output_cost
        
        # Use actual model name from response (may differ from requested)
        actual_model_name = response.model or model
        
        usage = LLMUsage(
            provider="openai",
            model=actual_model_name,  # Use actual model name from response
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            input_cost=input_cost,
            output_cost=output_cost,
            total_cost=total_cost,
            timestamp=datetime.now()
        )
        
        self.usage_log.append(usage)
        
        return LLMResponse(
            content=response.choices[0].message.content,
            usage=usage,
            provider="openai",
            model=response.model,
            success=True
        )
    
    async def _anthropic_complete(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_tokens: int
    ) -> LLMResponse:
        """Generate completion using Anthropic Claude."""
        if not self.anthropic_client:
            raise ValueError("Anthropic not available")
        
        # Get actual model name from stored name or env
        model = self.anthropic_model_name or os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
        
        response = self.anthropic_client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_prompt,
            messages=[{
                "role": "user",
                "content": user_prompt
            }]
        )
        
        # Calculate usage and cost
        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens
        total_tokens = input_tokens + output_tokens
        
        # Claude 3.5 Sonnet pricing (November 2025)
        input_cost = (input_tokens / 1000) * 0.003
        output_cost = (output_tokens / 1000) * 0.015
        total_cost = input_cost + output_cost
        
        usage = LLMUsage(
            provider="anthropic",
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            input_cost=input_cost,
            output_cost=output_cost,
            total_cost=total_cost,
            timestamp=datetime.now()
        )
        
        self.usage_log.append(usage)
        
        return LLMResponse(
            content=response.content[0].text,
            usage=usage,
            provider="anthropic",
            model=model,
            success=True
        )
    
    async def generate_code(
        self,
        task_description: str,
        tech_stack: List[str],
        research_context: Optional[Dict] = None,
        temperature: float = None,
        language: str = "python"
    ) -> LLMResponse:
        """
        Specialized method for code generation.
        
        Args:
            task_description: What to build
            tech_stack: Technologies to use
            research_context: Research findings from ResearcherAgent
            temperature: Creativity (None = use Q2O_LLM_CODE_TEMPERATURE)
            language: Programming language
        
        Returns:
            LLMResponse with generated code
        """
        # Use code-specific temperature (lower = more deterministic)
        if temperature is None:
            temperature = float(os.getenv("Q2O_LLM_CODE_TEMPERATURE", "0.3"))
        
        # Build system prompt for code generation
        tech_stack_str = ', '.join(tech_stack)
        
        system_prompt = f"""You are an expert {tech_stack_str} developer.

Generate production-quality {language} code with:
✅ Complete type hints (mypy strict mode compatible)
✅ Comprehensive docstrings (Google style)
✅ Proper error handling (try/except with specific exceptions)
✅ Input validation (Pydantic models if applicable)
✅ Security best practices (no SQL injection, XSS, eval, exec)
✅ Structured logging with context
✅ Best practices for {tech_stack_str}
✅ Clean, readable, maintainable code

{self._format_research_context(research_context) if research_context else ''}

Output ONLY the code - no explanations, no markdown formatting, no comments outside the code."""
        
        user_prompt = f"""Task: {task_description}

Technology Stack: {tech_stack_str}

Generate complete, production-ready implementation."""
        
        return await self.complete(
            system_prompt,
            user_prompt,
            temperature=temperature,
            max_tokens=8192  # Longer for code generation
        )
    
    def _format_research_context(self, research: Dict) -> str:
        """Format research context for inclusion in prompt."""
        if not research:
            return ""
        
        context = "\n\n📚 Research Context:\n"
        
        if research.get('key_findings'):
            context += "Key Findings:\n"
            for finding in research['key_findings'][:5]:  # Top 5
                context += f"- {finding}\n"
        
        if research.get('code_examples'):
            context += "\nCode Examples Found:\n"
            for example in research['code_examples'][:3]:  # Top 3
                context += f"- {example.get('description', 'Example')}\n"
        
        if research.get('best_practices'):
            context += "\nBest Practices:\n"
            for practice in research['best_practices'][:5]:
                context += f"- {practice}\n"
        
        return context
    
    def get_usage_stats(self) -> Dict:
        """Get comprehensive usage statistics."""
        cache_stats = self.cache.get_stats() if self.cache else {}
        budget_status = self.cost_monitor.get_budget_status()
        
        # Group by provider and model, tracking actual model names
        by_provider = {}
        for usage in self.usage_log:
            provider_key = usage.provider
            model_key = usage.model or "unknown"
            
            if provider_key not in by_provider:
                by_provider[provider_key] = {
                    "calls": 0,
                    "total_cost": 0.0,
                    "total_tokens": 0,
                    "models": {}  # Nested dictionary: {model_name: {calls, total_cost}}
                }
            
            by_provider[provider_key]["calls"] += 1
            by_provider[provider_key]["total_cost"] += usage.total_cost
            by_provider[provider_key]["total_tokens"] += usage.total_tokens
            
            # Track by model
            if model_key not in by_provider[provider_key]["models"]:
                by_provider[provider_key]["models"][model_key] = {
                    "calls": 0,
                    "total_cost": 0.0,
                    "total_tokens": 0
                }
            
            by_provider[provider_key]["models"][model_key]["calls"] += 1
            by_provider[provider_key]["models"][model_key]["total_cost"] += usage.total_cost
            by_provider[provider_key]["models"][model_key]["total_tokens"] += usage.total_tokens
        
        # Round costs and format
        for provider in by_provider:
            by_provider[provider]["total_cost"] = round(by_provider[provider]["total_cost"], 2)
            # Round model costs
            for model_data in by_provider[provider]["models"].values():
                model_data["total_cost"] = round(model_data["total_cost"], 2)
            # Calculate avg cost
            calls = by_provider[provider]["calls"]
            by_provider[provider]["avg_cost"] = round(by_provider[provider]["total_cost"] / calls, 4) if calls > 0 else 0.0
        
        # Add providers with no usage yet (use configured model names)
        if "gemini" not in by_provider:
            gemini_model = self.gemini_model_name or os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
            by_provider["gemini"] = {
                "calls": 0,
                "total_cost": 0.0,
                "total_tokens": 0,
                "avg_cost": 0.0,
                "models": {gemini_model: {"calls": 0, "total_cost": 0.0, "total_tokens": 0}}
            }
        
        if "openai" not in by_provider:
            openai_model = self.openai_model_name or os.getenv("OPENAI_MODEL", "gpt-4-turbo")
            by_provider["openai"] = {
                "calls": 0,
                "total_cost": 0.0,
                "total_tokens": 0,
                "avg_cost": 0.0,
                "models": {openai_model: {"calls": 0, "total_cost": 0.0, "total_tokens": 0}}
            }
        
        if "anthropic" not in by_provider:
            anthropic_model = self.anthropic_model_name or os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
            by_provider["anthropic"] = {
                "calls": 0,
                "total_cost": 0.0,
                "total_tokens": 0,
                "avg_cost": 0.0,
                "models": {anthropic_model: {"calls": 0, "total_cost": 0.0, "total_tokens": 0}}
            }
        
        return {
            "total_calls": self.total_calls,
            "successful_calls": self.successful_calls,
            "failed_calls": self.failed_calls,
            "cache_hits": self.cache_hits,
            "cache_hit_rate": round((self.cache_hits / self.total_calls * 100), 1) if self.total_calls > 0 else 0.0,
            "by_provider": by_provider,
            "cache_stats": cache_stats,
            "budget_status": budget_status
        }
    
    def reset_daily_stats(self):
        """Reset daily statistics (call at midnight)."""
        self.cost_monitor.daily_spent = 0.0
        logging.info("🔄 Daily LLM stats reset")


# Convenience function for agents
_llm_service_instance = None

def get_llm_service() -> LLMService:
    """Get singleton LLM service instance."""
    global _llm_service_instance
    if _llm_service_instance is None:
        _llm_service_instance = LLMService()
    return _llm_service_instance

