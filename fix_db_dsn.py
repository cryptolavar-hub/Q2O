#!/usr/bin/env python3
"""Fix incomplete DB_DSN in .env file."""

from pathlib import Path
import re

ENV_PATH = Path(r'C:\Q2O_Combined\.env')
# Updated password: Q2OPostgres2025( (no special character issues)
# Using existing q2o database
CORRECT_DSN = 'DB_DSN=postgresql+psycopg://q2o_user:Q2OPostgres2025(@localhost:5432/q2o'

def fix_db_dsn():
    """Fix the DB_DSN line in .env file."""
    if not ENV_PATH.exists():
        print(f'✗ .env file not found at {ENV_PATH}')
        return False
    
    # Read the file
    try:
        content = ENV_PATH.read_text(encoding='utf-8')
    except Exception as e:
        print(f'✗ Failed to read .env file: {e}')
        return False
    
    # Check if DB_DSN exists and is incomplete
    lines = content.split('\n')
    db_dsn_found = False
    new_lines = []
    
    for line in lines:
        if line.strip().startswith('DB_DSN='):
            db_dsn_found = True
            # Check if it points to wrong database (quick2odoo instead of q2o)
            if '/quick2odoo' in line:
                print(f'Found DB_DSN pointing to non-existent database: {line[:60]}...')
                new_lines.append(CORRECT_DSN)
                print('✓ Updated to use existing q2o database')
            elif '/q2o' in line and '@localhost' in line:
                # Already correct
                new_lines.append(line)
                print('✓ DB_DSN already points to q2o database')
            elif '@localhost' not in line:
                # Incomplete
                print(f'Found incomplete DB_DSN: {line[:50]}...')
                new_lines.append(CORRECT_DSN)
                print('✓ Replaced with complete DB_DSN')
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)
    
    # If DB_DSN not found, add it
    if not db_dsn_found:
        print('DB_DSN not found, adding it...')
        new_lines.append(CORRECT_DSN)
        print('✓ Added DB_DSN')
    
    # Write back
    try:
        ENV_PATH.write_text('\n'.join(new_lines), encoding='utf-8')
        print(f'✓ .env file updated successfully')
        return True
    except Exception as e:
        print(f'✗ Failed to write .env file: {e}')
        return False

if __name__ == '__main__':
    print('=' * 60)
    print('Fixing DB_DSN in .env file')
    print('=' * 60)
    print()
    
    if fix_db_dsn():
        print()
        print('Verifying fix...')
        from addon_portal.api.core.settings import settings
        dsn = settings.DB_DSN
        if '@localhost' in dsn and '/q2o' in dsn:
            print(f'✓ DB_DSN is now correct: {dsn[:60]}...')
        else:
            print(f'⚠ DB_DSN may be incorrect: {dsn}')
    else:
        print('✗ Fix failed')

