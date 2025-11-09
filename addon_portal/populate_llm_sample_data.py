"""
Populate LLM configuration tables with sample data for testing.
Run this script to create sample project prompts and agent prompts.

Usage:
    cd addon_portal
    python populate_llm_sample_data.py
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from addon_portal.api.core.database import engine, SessionLocal
from addon_portal.api.models.llm_config import LLMProjectConfig, LLMAgentConfig, Base


def populate_sample_data():
    """Create sample project and agent prompts."""
    
    # Create tables if they don't exist
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)
    
    # Create session
    db: Session = SessionLocal()
    
    try:
        # Check if data already exists
        existing_count = db.query(LLMProjectConfig).count()
        if existing_count > 0:
            print(f"Sample data already exists ({existing_count} projects). Skipping.")
            print("Delete existing data first if you want to recreate samples.")
            return
        
        print("Creating sample project prompts...")
        
        # Project 1: SAGE NetSuite Migration
        project1 = LLMProjectConfig(
            project_id="sage-netsuite-migration-001",
            client_name="Acme Corp",
            description="accounting-migration",
            custom_instructions=(
                "You are an expert in accounting system migrations. "
                "Focus on data integrity and Odoo v18 best practices. "
                "Ensure all financial data is accurately mapped from SAGE NetSuite to Odoo. "
                "Validate GL accounts, chart of accounts, and transaction history."
            ),
            provider_override=None,
            is_active=True,
            priority="high"
        )
        db.add(project1)
        db.flush()  # Get the ID
        
        # Agent prompts for project 1
        agent1_coder = LLMAgentConfig(
            project_id=project1.project_id,
            agent_type="coder",
            custom_instructions=(
                "Generate production-ready Python code for Odoo v18 with type hints and error handling. "
                "Use SQLAlchemy ORM for database operations. "
                "Include comprehensive logging and transaction management. "
                "Follow Odoo coding standards and best practices."
            ),
            provider_override=None,
            is_enabled=True
        )
        
        agent1_researcher = LLMAgentConfig(
            project_id=project1.project_id,
            agent_type="researcher",
            custom_instructions=(
                "Research SAGE NetSuite API documentation and Odoo v18 accounting modules. "
                "Focus on finding official API endpoints for financial data export. "
                "Look for migration case studies and common pitfalls. "
                "Identify field mappings between SAGE and Odoo accounting modules."
            ),
            provider_override=None,
            is_enabled=True
        )
        
        db.add(agent1_coder)
        db.add(agent1_researcher)
        
        # Project 2: Mobile E-Commerce App
        project2 = LLMProjectConfig(
            project_id="mobile-ecommerce-app-002",
            client_name="TechStart Inc",
            description="mobile-ecommerce",
            custom_instructions=(
                "You are a React Native specialist. "
                "Build modern, performant mobile apps with excellent UX. "
                "Use TypeScript for type safety. "
                "Implement smooth animations and transitions. "
                "Ensure offline-first architecture with local data caching."
            ),
            provider_override=None,
            is_active=True,
            priority="normal"
        )
        db.add(project2)
        db.flush()
        
        # Agent prompt for project 2
        agent2_mobile = LLMAgentConfig(
            project_id=project2.project_id,
            agent_type="mobile",
            custom_instructions=(
                "Create clean React Native screens with TypeScript, native navigation, and state management. "
                "Use React Navigation for routing. "
                "Implement Redux Toolkit for global state. "
                "Use React Query for API data fetching and caching. "
                "Follow mobile UX best practices (thumb-friendly zones, loading states, error boundaries)."
            ),
            provider_override=None,
            is_enabled=True
        )
        db.add(agent2_mobile)
        
        # Project 3: HR Management SaaS
        project3 = LLMProjectConfig(
            project_id="hr-management-saas-003",
            client_name="PeopleFirst Solutions",
            description="hr-saas-platform",
            custom_instructions=(
                "Build a comprehensive HR management SaaS platform. "
                "Focus on employee lifecycle management, payroll integration, and compliance. "
                "Implement role-based access control (RBAC) for different HR roles. "
                "Ensure GDPR and data privacy compliance for employee information."
            ),
            provider_override="openai",  # Use GPT-4 for this complex project
            is_active=True,
            priority="critical"
        )
        db.add(project3)
        db.flush()
        
        # Agents for project 3
        agent3_coder = LLMAgentConfig(
            project_id=project3.project_id,
            agent_type="coder",
            custom_instructions=(
                "Generate secure, scalable Python/FastAPI code for HR platform backend. "
                "Implement multi-tenancy with tenant isolation. "
                "Use PostgreSQL with row-level security (RLS). "
                "Add comprehensive audit logging for all HR data changes."
            ),
            provider_override="openai",
            is_enabled=True
        )
        
        agent3_security = LLMAgentConfig(
            project_id=project3.project_id,
            agent_type="security",
            custom_instructions=(
                "Conduct security audits focused on HR data protection. "
                "Verify PII encryption at rest and in transit. "
                "Check for SQL injection, XSS, and CSRF vulnerabilities. "
                "Ensure proper authentication and authorization on all HR endpoints. "
                "Validate GDPR compliance for employee data handling."
            ),
            provider_override=None,
            is_enabled=True
        )
        
        db.add(agent3_coder)
        db.add(agent3_security)
        
        # Commit all changes
        db.commit()
        
        print("\n✅ Sample data created successfully!")
        print(f"\nCreated {3} projects:")
        print("  1. SAGE NetSuite Migration (Acme Corp) - 2 agent prompts")
        print("  2. Mobile E-Commerce App (TechStart Inc) - 1 agent prompt")
        print("  3. HR Management SaaS (PeopleFirst Solutions) - 2 agent prompts")
        print(f"\nTotal: 5 agent prompts across 3 projects")
        
    except Exception as e:
        print(f"\n❌ Error creating sample data: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 70)
    print("Q2O LLM Configuration - Sample Data Population")
    print("=" * 70)
    print()
    
    populate_sample_data()
    
    print()
    print("You can now view the sample data at:")
    print("  http://localhost:3002/llm")
    print("  http://localhost:3002/llm/configuration")
    print()

