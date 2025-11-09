"""
Research Database Migration Script
Migrates existing file-based research to PostgreSQL and creates tables.
"""

import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import os
import json
import logging
from datetime import datetime

# Load environment
from dotenv import load_dotenv
load_dotenv()

from addon_portal.api.core.settings import settings
from addon_portal.api.core.db import engine, Base
from addon_portal.api.models.research import ResearchResult, ResearchAnalytics

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_tables():
    """Create research tables in PostgreSQL."""
    logger.info("Creating research tables...")
    
    try:
        # Import models to ensure they're registered
        from addon_portal.api.models import research
        
        # Create tables
        Base.metadata.create_all(bind=engine, tables=[
            ResearchResult.__table__,
            ResearchAnalytics.__table__
        ])
        
        logger.info("✅ Research tables created successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create tables: {e}")
        return False


def migrate_file_research():
    """Migrate existing file-based research to database."""
    logger.info("Migrating file-based research to PostgreSQL...")
    
    # Find research cache directory
    research_cache = Path.home() / ".quickodoo" / "research_cache"
    
    if not research_cache.exists():
        logger.info("No existing research cache found to migrate")
        return 0
    
    from utils.research_database import get_research_database
    db = get_research_database()
    
    migrated = 0
    
    # Find all JSON research files
    json_files = list(research_cache.glob("*.json"))
    
    if not json_files:
        logger.info("No research files found in cache")
        return 0
    
    logger.info(f"Found {len(json_files)} research files to migrate")
    
    for json_file in json_files:
        if json_file.name == "index.json":
            continue  # Skip index file
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                research_data = json.load(f)
            
            # Store in database
            research_id = db.store_research(
                research_id=json_file.stem,
                query=research_data.get('query', 'unknown'),
                research_results=research_data,
                project_name=research_data.get('project_name')
            )
            
            migrated += 1
            logger.info(f"Migrated: {json_file.name}")
            
        except Exception as e:
            logger.error(f"Failed to migrate {json_file.name}: {e}")
    
    logger.info(f"✅ Migrated {migrated} research files to PostgreSQL")
    return migrated


def verify_migration():
    """Verify migration completed successfully."""
    logger.info("Verifying migration...")
    
    from utils.research_database import get_research_database
    db = get_research_database()
    
    stats = db.get_research_stats()
    
    logger.info("Migration verification:")
    logger.info(f"  Total research records: {stats.get('total_research', 0)}")
    logger.info(f"  LLM-synthesized: {stats.get('llm_synthesized_count', 0)}")
    logger.info(f"  Average confidence: {stats.get('avg_confidence', 0):.1f}")
    logger.info(f"  Total accesses: {stats.get('total_accesses', 0)}")
    
    return stats.get('total_research', 0) > 0


def main():
    """Main migration flow."""
    print("=" * 70)
    print(" " * 15 + "Research Database Migration")
    print("=" * 70)
    print()
    
    # Check database connection
    logger.info(f"Database: {settings.DB_DSN}")
    print()
    
    # Step 1: Create tables
    print("[1/3] Creating research tables in PostgreSQL...")
    if not create_tables():
        print("   [ERROR] Failed to create tables")
        return False
    print("   [OK] Tables created")
    print()
    
    # Step 2: Migrate existing research
    print("[2/3] Migrating existing research files...")
    migrated = migrate_file_research()
    print(f"   [OK] Migrated {migrated} research files")
    print()
    
    # Step 3: Verify
    print("[3/3] Verifying migration...")
    if verify_migration():
        print("   [OK] Migration successful")
    else:
        print("   [WARNING] No research found (this is OK for new installs)")
    print()
    
    print("=" * 70)
    print("   ✅ MIGRATION COMPLETE!")
    print("=" * 70)
    print()
    print("What's next:")
    print("  1. ResearcherAgent will now store results in PostgreSQL")
    print("  2. Queries are faster and more scalable")
    print("  3. Full-text search available")
    print("  4. Analytics and usage tracking enabled")
    print()
    print("Benefits:")
    print("  - Scalable (millions of research records)")
    print("  - Fast queries (indexed)")
    print("  - Analytics (track what's most useful)")
    print("  - No file system limits")
    print()
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

