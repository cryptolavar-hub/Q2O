"""
Template Learning Engine - Learns from successful LLM generations.
Automatically creates reusable templates to reduce future LLM costs.

This is Q2O's self-improving capability - the platform gets smarter with each project!
"""

from typing import Dict, List, Optional, Tuple
import json
import sqlite3
from datetime import datetime
from pathlib import Path
import hashlib
import logging
import re
import os
from dataclasses import dataclass, asdict


@dataclass
class LearnedTemplate:
    """A template learned from successful LLM generation."""
    template_id: str
    name: str
    description: str
    tech_stack: List[str]
    pattern_signature: str
    template_content: str
    source_llm: str
    quality_score: int
    usage_count: int
    created_at: datetime
    last_used: datetime
    metadata: Dict
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "template_id": self.template_id,
            "name": self.name,
            "description": self.description,
            "tech_stack": self.tech_stack,
            "pattern_signature": self.pattern_signature,
            "template_content": self.template_content,
            "source_llm": self.source_llm,
            "quality_score": self.quality_score,
            "usage_count": self.usage_count,
            "created_at": self.created_at.isoformat(),
            "last_used": self.last_used.isoformat(),
            "metadata": self.metadata
        }


@dataclass
class ParameterizationSuggestion:
    """Suggestion for parameterizing code into a template."""
    original_value: str
    parameter_name: str
    parameter_type: str  # string, int, url, class_name, etc.
    occurrences: int
    confidence: float  # 0.0-1.0
    reasoning: str


class TemplateLearningEngine:
    """
    Learns patterns from successful LLM generations.
    Creates reusable templates automatically for cost savings.
    
    This is Q2O's SECRET WEAPON - exponential cost reduction through learning!
    """
    
    def __init__(self, db_path: str = None):
        """
        Initialize template learning engine.
        
        Args:
            db_path: Path to learned templates database
        """
        self.db_path = db_path or os.getenv(
            "Q2O_LEARNED_TEMPLATES_DB",
            "learned_templates.db"
        )
        self.enabled = os.getenv("Q2O_TEMPLATE_LEARNING_ENABLED", "true").lower() == "true"
        self.min_quality = int(os.getenv("Q2O_TEMPLATE_MIN_QUALITY_TO_LEARN", "90"))
        self.match_threshold = float(os.getenv("Q2O_TEMPLATE_MATCH_THRESHOLD", "0.80"))
        
        if self.enabled:
            self._init_database()
            logging.info(f"✅ Template Learning Engine initialized (min quality: {self.min_quality}%)")
        else:
            logging.info("ℹ️  Template Learning disabled by configuration")
    
    def _init_database(self):
        """Initialize learned templates database."""
        conn = sqlite3.connect(self.db_path)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS learned_templates (
                template_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                tech_stack TEXT,  -- JSON array
                pattern_signature TEXT UNIQUE,
                template_content TEXT,
                source_llm TEXT,
                quality_score INTEGER,
                usage_count INTEGER DEFAULT 0,
                created_at TIMESTAMP,
                last_used TIMESTAMP,
                metadata TEXT  -- JSON
            )
        """)
        
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_pattern ON learned_templates(pattern_signature)
        """)
        
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_tech_stack ON learned_templates(tech_stack)
        """)
        
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_quality ON learned_templates(quality_score DESC)
        """)
        
        conn.commit()
        conn.close()
    
    def extract_pattern_signature(
        self,
        task_description: str,
        tech_stack: List[str],
        code: str
    ) -> str:
        """
        Extract an abstract pattern signature from task and code.
        
        Pattern includes:
        - Task type (API integration, CRUD, webhook, etc.)
        - Technology stack
        - Code structure (classes, functions, imports)
        
        Similar tasks will have similar signatures, enabling template reuse.
        
        Args:
            task_description: Original task description
            tech_stack: Technologies used
            code: Generated code
        
        Returns:
            Pattern signature hash
        """
        task_lower = task_description.lower()
        
        # Extract task type
        task_type = self._detect_task_type(task_lower)
        
        # Extract code structure
        structure = {
            "has_router": "APIRouter" in code or "@router" in code or "@app" in code,
            "has_model": "BaseModel" in code or "class" in code,
            "has_database": "Session" in code or "Database" in code or "engine" in code,
            "has_async": "async def" in code,
            "has_pydantic": "BaseModel" in code or "Field" in code,
            "has_fastapi": "FastAPI" in code or "APIRouter" in code,
            "has_sqlalchemy": "Column" in code or "relationship" in code,
            "has_auth": "token" in code.lower() or "auth" in code.lower(),
            "has_webhook": "webhook" in code.lower() or "signature" in code.lower()
        }
        
        # Count functions and classes
        function_count = len(re.findall(r'\ndef ', code))
        class_count = len(re.findall(r'\nclass ', code))
        
        # Create signature
        signature_data = {
            "task_type": task_type,
            "tech_stack": sorted(tech_stack),
            "structure": structure,
            "function_count": min(function_count, 10),  # Cap for grouping
            "class_count": min(class_count, 5)
        }
        
        # Hash for matching
        signature_str = json.dumps(signature_data, sort_keys=True)
        signature_hash = hashlib.md5(signature_str.encode()).hexdigest()
        
        return signature_hash
    
    def _detect_task_type(self, task_lower: str) -> str:
        """Detect task type from description."""
        task_types = {
            "webhook": ["webhook", "callback", "event handler"],
            "api_client": ["api client", "http client", "rest client", "api integration"],
            "crud": ["crud", "create read update delete", "database operations"],
            "authentication": ["auth", "login", "signin", "signup", "jwt", "oauth"],
            "payment": ["payment", "billing", "stripe", "checkout", "invoice"],
            "data_migration": ["migrate", "migration", "import data", "export data"],
            "graphql": ["graphql", "query", "mutation", "resolver"],
            "websocket": ["websocket", "ws", "real-time", "live update"],
            "background_job": ["celery", "task queue", "background", "async task"],
            "email": ["email", "smtp", "send mail", "notification"]
        }
        
        for task_type, keywords in task_types.items():
            if any(kw in task_lower for kw in keywords):
                return task_type
        
        return "general"
    
    def find_similar_template(
        self,
        task_description: str,
        tech_stack: List[str]
    ) -> Optional[LearnedTemplate]:
        """
        Find a learned template that matches this task.
        
        Uses pattern signature matching to find similar previously-learned templates.
        
        Args:
            task_description: What to build
            tech_stack: Technologies needed
        
        Returns:
            LearnedTemplate if match found, None otherwise
        """
        if not self.enabled:
            return None
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get all templates with exact tech stack match
        tech_stack_json = json.dumps(sorted(tech_stack))
        
        cursor.execute("""
            SELECT * FROM learned_templates
            WHERE tech_stack = ?
            ORDER BY usage_count DESC, quality_score DESC
            LIMIT 10
        """, (tech_stack_json,))
        
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            logging.debug(f"No learned templates found for tech stack: {tech_stack}")
            return None
        
        # TODO: Implement semantic similarity matching
        # For now, return the most-used, highest-quality template
        row = rows[0]
        
        template = self._row_to_template(row)
        
        logging.info(f"📚 Found learned template: {template.name} (used {template.usage_count} times)")
        
        return template
    
    def _row_to_template(self, row: tuple) -> LearnedTemplate:
        """Convert database row to LearnedTemplate object."""
        return LearnedTemplate(
            template_id=row[0],
            name=row[1],
            description=row[2],
            tech_stack=json.loads(row[3]),
            pattern_signature=row[4],
            template_content=row[5],
            source_llm=row[6],
            quality_score=row[7],
            usage_count=row[8],
            created_at=datetime.fromisoformat(row[9]),
            last_used=datetime.fromisoformat(row[10]),
            metadata=json.loads(row[11])
        )
    
    async def learn_from_generation(
        self,
        task_description: str,
        tech_stack: List[str],
        generated_code: str,
        source_llm: str,
        quality_score: int,
        metadata: Optional[Dict] = None
    ) -> Optional[str]:
        """
        Learn from successful LLM generation.
        Create reusable template for future similar tasks.
        
        This is THE KEY to cost reduction - after learning, similar tasks cost $0!
        
        Args:
            task_description: Original task
            tech_stack: Technologies used
            generated_code: LLM-generated code that passed validation
            source_llm: Which LLM generated it (gemini/openai/anthropic)
            quality_score: QA score (0-100)
            metadata: Additional context
        
        Returns:
            template_id if learned, None if not worth learning
        """
        if not self.enabled:
            return None
        
        # Only learn from high-quality generations
        if quality_score < self.min_quality:
            logging.debug(f"Quality {quality_score} < {self.min_quality}, not learning template")
            return None
        
        # Extract pattern signature
        pattern_sig = self.extract_pattern_signature(
            task_description, tech_stack, generated_code
        )
        
        # Check if we already have this pattern
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT template_id, quality_score FROM learned_templates
            WHERE pattern_signature = ?
        """, (pattern_sig,))
        
        existing = cursor.fetchone()
        
        if existing:
            existing_id, existing_quality = existing
            
            # If new code is better quality, update the template
            if quality_score > existing_quality:
                logging.info(f"✨ Updating template {existing_id} with higher quality code ({existing_quality} → {quality_score})")
                
                cursor.execute("""
                    UPDATE learned_templates
                    SET template_content = ?,
                        quality_score = ?,
                        source_llm = ?,
                        metadata = ?
                    WHERE template_id = ?
                """, (
                    generated_code,
                    quality_score,
                    source_llm,
                    json.dumps(metadata or {}),
                    existing_id
                ))
                
                conn.commit()
                conn.close()
                return existing_id
            else:
                logging.debug(f"Pattern already learned with similar/better quality: {existing_id}")
                conn.close()
                return existing_id
        
        # Create new learned template
        template_id = f"learned_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{pattern_sig[:8]}"
        name = self._generate_template_name(task_description, tech_stack)
        
        # Save to database (code as-is for now, parameterization comes later)
        cursor.execute("""
            INSERT INTO learned_templates (
                template_id, name, description, tech_stack,
                pattern_signature, template_content, source_llm,
                quality_score, usage_count, created_at, last_used, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?)
        """, (
            template_id,
            name,
            task_description[:200],  # Truncate long descriptions
            json.dumps(sorted(tech_stack)),
            pattern_sig,
            generated_code,
            source_llm,
            quality_score,
            datetime.now().isoformat(),
            datetime.now().isoformat(),
            json.dumps(metadata or {})
        ))
        
        conn.commit()
        conn.close()
        
        logging.info(f"✨ Learned new template: {template_id} '{name}' (from {source_llm}, quality: {quality_score}/100)")
        
        return template_id
    
    def _generate_template_name(self, task_description: str, tech_stack: List[str]) -> str:
        """
        Generate a descriptive name for the learned template.
        
        Args:
            task_description: Original task description
            tech_stack: Technologies used
        
        Returns:
            Human-readable template name
        """
        task_lower = task_description.lower()
        
        # Determine task type
        task_type = self._detect_task_type(task_lower)
        
        # Get primary technology
        primary_tech = tech_stack[0] if tech_stack else "Generic"
        
        # Map task types to readable names
        type_names = {
            "webhook": "Webhook Handler",
            "api_client": "API Client",
            "crud": "CRUD Operations",
            "authentication": "Authentication",
            "payment": "Payment Integration",
            "data_migration": "Data Migration",
            "graphql": "GraphQL API",
            "websocket": "WebSocket Handler",
            "background_job": "Background Job",
            "email": "Email Service",
            "general": "Integration"
        }
        
        type_name = type_names.get(task_type, "Integration")
        
        # Generate name
        name = f"{primary_tech} {type_name}"
        
        return name
    
    async def suggest_parameterization(
        self,
        code: str,
        task_description: str,
        llm_service: 'LLMService'
    ) -> List[ParameterizationSuggestion]:
        """
        Use LLM to suggest parameterization for the code.
        
        This is SEMI-AUTO mode - LLM suggests, consultant approves/edits.
        
        Args:
            code: Generated code to parameterize
            task_description: Original task
            llm_service: LLM service for generating suggestions
        
        Returns:
            List of parameterization suggestions
        """
        system_prompt = """You are a template parameterization expert.

Analyze code and identify values that should be parameterized for reuse:
- Entity names (Customer, Product, Order, etc.)
- API endpoints and URLs
- Service names
- Function/class names specific to one use case
- Configuration values
- Business logic identifiers

DO NOT parameterize:
- Standard library imports
- Framework conventions (FastAPI, SQLAlchemy patterns)
- Language keywords
- Type hints
- Common variable names (request, response, etc.)

Return JSON array of suggestions:
```json
[
  {
    "original_value": "stripe_webhook",
    "parameter_name": "webhook_name",
    "parameter_type": "string",
    "occurrences": 5,
    "reasoning": "Specific to Stripe, should be generic"
  }
]
```"""
        
        user_prompt = f"""Task: {task_description}

Code to parameterize:
```python
{code}
```

Analyze and return JSON array of parameterization suggestions."""
        
        response = await llm_service.complete(
            system_prompt,
            user_prompt,
            temperature=0.2,  # Low for analytical task
            max_tokens=2048
        )
        
        if not response.success:
            logging.warning("LLM parameterization suggestion failed, returning empty list")
            return []
        
        # Parse JSON response
        try:
            # Extract JSON from response (might be wrapped in markdown)
            content = response.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            suggestions_data = json.loads(content.strip())
            
            suggestions = []
            for s in suggestions_data:
                suggestions.append(ParameterizationSuggestion(
                    original_value=s['original_value'],
                    parameter_name=s['parameter_name'],
                    parameter_type=s.get('parameter_type', 'string'),
                    occurrences=s.get('occurrences', 1),
                    confidence=s.get('confidence', 0.8),
                    reasoning=s.get('reasoning', '')
                ))
            
            logging.info(f"💡 Generated {len(suggestions)} parameterization suggestions")
            return suggestions
            
        except Exception as e:
            logging.error(f"Error parsing parameterization suggestions: {e}")
            return []
    
    def apply_parameterization(
        self,
        code: str,
        parameters: List[Dict]
    ) -> str:
        """
        Apply consultant-approved parameters to code.
        
        Args:
            code: Original code
            parameters: List of parameters to apply (from consultant edits)
        
        Returns:
            Parameterized template code
        """
        parameterized = code
        
        for param in parameters:
            original = param['original_value']
            param_name = param['parameter_name']
            
            # Replace all occurrences
            parameterized = parameterized.replace(original, f"{{{{{param_name}}}}}")
        
        return parameterized
    
    def increment_usage(self, template_id: str):
        """
        Track template usage for analytics.
        
        Args:
            template_id: Template to track
        """
        if not self.enabled:
            return
        
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            UPDATE learned_templates
            SET usage_count = usage_count + 1,
                last_used = ?
            WHERE template_id = ?
        """, (datetime.now().isoformat(), template_id))
        conn.commit()
        conn.close()
        
        logging.debug(f"📊 Template usage incremented: {template_id}")
    
    def get_learning_stats(self) -> Dict:
        """
        Get statistics on template learning.
        
        Returns comprehensive metrics about learned templates and cost savings.
        """
        if not self.enabled:
            return {
                "enabled": False,
                "total_templates": 0,
                "total_uses": 0,
                "cost_saved": 0.0
            }
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT
                COUNT(*) as total_templates,
                SUM(usage_count) as total_uses,
                AVG(quality_score) as avg_quality,
                SUM(CASE WHEN source_llm = 'gemini' THEN 1 ELSE 0 END) as from_gemini,
                SUM(CASE WHEN source_llm = 'openai' THEN 1 ELSE 0 END) as from_gpt4,
                SUM(CASE WHEN source_llm = 'claude' THEN 1 ELSE 0 END) as from_claude
            FROM learned_templates
        """)
        
        row = cursor.fetchone()
        conn.close()
        
        # Handle empty table (SQL aggregates return None)
        total_templates = row[0] or 0
        total_uses = row[1] or 0
        avg_quality = row[2] or 0.0
        from_gemini = row[3] or 0
        from_gpt4 = row[4] or 0
        from_claude = row[5] or 0
        
        # Calculate cost savings
        # Average Gemini cost per generation: $0.52
        # Each template use saves one LLM call
        cost_saved = round(total_uses * 0.52, 2)
        
        return {
            "enabled": True,
            "total_templates": total_templates,
            "total_uses": total_uses,
            "avg_quality": round(avg_quality, 1),
            "by_source": {
                "gemini": from_gemini,
                "gpt4": from_gpt4,
                "claude": from_claude
            },
            "cost_saved": cost_saved,
            "avg_reuse": round(total_uses / total_templates, 1) if total_templates > 0 else 0.0
        }
    
    def get_template_by_id(self, template_id: str) -> Optional[LearnedTemplate]:
        """Get a specific learned template by ID."""
        if not self.enabled:
            return None
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM learned_templates
            WHERE template_id = ?
        """, (template_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        return self._row_to_template(row)
    
    def get_all_templates(
        self,
        limit: int = 100,
        sort_by: str = "usage_count"
    ) -> List[LearnedTemplate]:
        """
        Get all learned templates.
        
        Args:
            limit: Maximum number of templates to return
            sort_by: Sort field (usage_count, quality_score, created_at)
        
        Returns:
            List of learned templates
        """
        if not self.enabled:
            return []
        
        valid_sorts = ["usage_count", "quality_score", "created_at"]
        if sort_by not in valid_sorts:
            sort_by = "usage_count"
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(f"""
            SELECT * FROM learned_templates
            ORDER BY {sort_by} DESC
            LIMIT ?
        """, (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [self._row_to_template(row) for row in rows]
    
    def delete_template(self, template_id: str) -> bool:
        """
        Delete a learned template.
        
        Args:
            template_id: Template to delete
        
        Returns:
            True if deleted, False if not found
        """
        if not self.enabled:
            return False
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            DELETE FROM learned_templates
            WHERE template_id = ?
        """, (template_id,))
        
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        if deleted:
            logging.info(f"🗑️  Deleted learned template: {template_id}")
        
        return deleted


# Convenience function
_template_engine_instance = None

def get_template_learning_engine() -> TemplateLearningEngine:
    """Get singleton template learning engine instance."""
    global _template_engine_instance
    if _template_engine_instance is None:
        _template_engine_instance = TemplateLearningEngine()
    return _template_engine_instance

