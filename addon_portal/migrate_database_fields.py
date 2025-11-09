"""
Database Migration: Add Missing Fields
Adds code_plain, usage_quota, and usage_current fields to existing database
"""

import sys
from pathlib import Path

# Add parent to path
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

from sqlalchemy import text
from api.core.db import engine

def run_migration():
    """Add missing fields to database."""
    
    print("=" * 70)
    print("Q2O - Database Migration")
    print("Adding Missing Fields to Tables")
    print("=" * 70)
    print()
    
    with engine.connect() as conn:
        try:
            # Start transaction
            trans = conn.begin()
            
            print("[1/3] Adding code_plain to activation_codes...")
            conn.execute(text("""
                ALTER TABLE activation_codes 
                ADD COLUMN IF NOT EXISTS code_plain VARCHAR
            """))
            
            # Update existing codes
            print("[2/3] Updating existing activation codes...")
            conn.execute(text("""
                UPDATE activation_codes 
                SET code_plain = code_hash 
                WHERE code_plain IS NULL
            """))
            
            print("[3/3] Adding usage fields to tenants...")
            conn.execute(text("""
                ALTER TABLE tenants 
                ADD COLUMN IF NOT EXISTS usage_quota INTEGER DEFAULT 10 NOT NULL
            """))
            
            conn.execute(text("""
                ALTER TABLE tenants 
                ADD COLUMN IF NOT EXISTS usage_current INTEGER DEFAULT 0 NOT NULL
            """))
            
            # Commit transaction
            trans.commit()
            
            print()
            print("[SUCCESS] Migration completed successfully!")
            print()
            print("Changes made:")
            print("  - activation_codes: Added code_plain column")
            print("  - tenants: Added usage_quota column")
            print("  - tenants: Added usage_current column")
            print()
            print("You can now restart the Licensing API!")
            
        except Exception as e:
            trans.rollback()
            print(f"\n[ERROR] Migration failed: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


if __name__ == "__main__":
    run_migration()

