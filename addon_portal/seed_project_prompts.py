"""
Seed Database with Sample Project Prompts
Run this to populate the database with test data for LLM Project & Agent Prompts
"""

import sys
from pathlib import Path

# Add parent directory to path
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

from sqlalchemy.orm import Session
from api.core.db import SessionLocal, engine
from api.models.llm_config import LLMProjectConfig, LLMAgentConfig
from api.models.licensing import Base

def seed_project_prompts():
    """Seed database with sample project prompts."""
    
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)
    
    # Get database session
    db = SessionLocal()
    
    try:
        # Check if data already exists
        existing = db.query(LLMProjectConfig).count()
        if existing > 0:
            print(f"Database already has {existing} project prompts. Skipping seed.")
            print("To re-seed, delete existing data first.")
            return
        
        print("Seeding database with sample Project Prompts...")
        
        # Sample Project 1: SAGE NetSuite Migration
        project1 = LLMProjectConfig(
            project_id="sage-netsuite-migration-001",
            client_name="Acme Corp",
            description="accounting-migration",
            custom_instructions="You are an expert in accounting system migrations. Focus on data integrity and Odoo v18 best practices. Ensure all financial data is accurately migrated from SAGE NetSuite to Odoo v18 with proper validation.",
            provider_override="gemini",
            is_active=True,
            priority="high"
        )
        db.add(project1)
        db.flush()  # Get the ID
        
        # Agent prompts for Project 1
        agent1_coder = LLMAgentConfig(
            project_id=project1.project_id,
            agent_type="coder",
            custom_instructions="Generate production-ready Python code for Odoo v18 with type hints and error handling. Use SQLAlchemy for database operations and follow Odoo coding standards.",
            enabled=True
        )
        db.add(agent1_coder)
        
        agent1_researcher = LLMAgentConfig(
            project_id=project1.project_id,
            agent_type="researcher",
            custom_instructions="Research SAGE NetSuite API documentation and Odoo v18 accounting modules. Focus on data mapping between SAGE fields and Odoo models. Provide detailed API endpoint documentation.",
            enabled=True
        )
        db.add(agent1_researcher)
        
        print(f"  [OK] Created project: {project1.project_id} with 2 agent prompts")
        
        # Sample Project 2: Mobile E-Commerce App
        project2 = LLMProjectConfig(
            project_id="mobile-ecommerce-app-002",
            client_name="TechStart Inc",
            description="mobile-ecommerce",
            custom_instructions="You are a React Native specialist. Build modern, performant mobile apps with excellent UX. Focus on clean architecture, proper state management, and native-like performance.",
            provider_override="openai",
            is_active=True,
            priority="normal"
        )
        db.add(project2)
        db.flush()
        
        # Agent prompts for Project 2
        agent2_mobile = LLMAgentConfig(
            project_id=project2.project_id,
            agent_type="mobile",
            custom_instructions="Create clean React Native screens with TypeScript, native navigation (React Navigation), and state management (Redux Toolkit). Follow iOS and Android design guidelines.",
            enabled=True
        )
        db.add(agent2_mobile)
        
        print(f"  [OK] Created project: {project2.project_id} with 1 agent prompt")
        
        # Sample Project 3: CRM SaaS Platform
        project3 = LLMProjectConfig(
            project_id="crm-saas-platform-003",
            client_name="SalesPro Solutions",
            description="saas-development",
            custom_instructions="Build a scalable multi-tenant CRM SaaS platform. Focus on security, data isolation, and enterprise-grade features. Implement proper authentication, authorization, and audit logging.",
            provider_override=None,  # Use system default
            is_active=True,
            priority="critical"
        )
        db.add(project3)
        db.flush()
        
        # Agent prompts for Project 3
        agent3_coder = LLMAgentConfig(
            project_id=project3.project_id,
            agent_type="coder",
            custom_instructions="Generate FastAPI backend code with PostgreSQL row-level security. Implement JWT authentication, multi-tenancy with schema isolation, and comprehensive API documentation.",
            enabled=True
        )
        db.add(agent3_coder)
        
        agent3_security = LLMAgentConfig(
            project_id=project3.project_id,
            agent_type="security",
            custom_instructions="Audit all code for security vulnerabilities. Check for SQL injection, XSS, CSRF, authentication bypass, and data leakage. Ensure proper input validation and sanitization.",
            enabled=True
        )
        db.add(agent3_security)
        
        agent3_qa = LLMAgentConfig(
            project_id=project3.project_id,
            agent_type="qa",
            custom_instructions="Generate comprehensive test cases including unit tests, integration tests, and end-to-end tests. Ensure 95%+ code coverage and test all edge cases.",
            enabled=True
        )
        db.add(agent3_qa)
        
        print(f"  [OK] Created project: {project3.project_id} with 3 agent prompts")
        
        # Commit all changes
        db.commit()
        
        print("\n[SUCCESS] Database seeded successfully!")
        print(f"   - 3 projects created")
        print(f"   - 6 agent prompts created")
        print(f"\nYou can now view these in the Admin Portal at:")
        print(f"   http://localhost:3002/llm")
        
    except Exception as e:
        db.rollback()
        print(f"\n[ERROR] Error seeding database: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 70)
    print("Q2O - Database Seed Script")
    print("Populating Project & Agent Prompts")
    print("=" * 70)
    print()
    
    seed_project_prompts()

