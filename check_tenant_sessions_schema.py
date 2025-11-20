#!/usr/bin/env python3
"""Check the actual schema of tenant_sessions table in the database."""

from sqlalchemy import create_engine, inspect, text

DSN = 'postgresql+psycopg://q2o_user:Q2OPostgres2025(@localhost:5432/q2o'

print('=' * 60)
print('Checking tenant_sessions table schema')
print('=' * 60)
print()

try:
    engine = create_engine(DSN)
    insp = inspect(engine)
    
    # Check if table exists
    tables = insp.get_table_names()
    if 'tenant_sessions' not in tables:
        print('✗ tenant_sessions table does NOT exist')
        print(f'Available tables: {", ".join(sorted(tables))}')
    else:
        print('✓ tenant_sessions table exists')
        print()
        
        # Get columns
        cols = insp.get_columns('tenant_sessions')
        print('Columns in tenant_sessions:')
        for col in cols:
            nullable = 'NULL' if col['nullable'] else 'NOT NULL'
            print(f'  - {col["name"]}: {col["type"]} ({nullable})')
        print()
        
        # Try to query OTPs
        print('Checking for OTPs in database...')
        with engine.connect() as conn:
            result = conn.execute(text('''
                SELECT id, tenant_id, otp_code, otp_expires_at, created_at 
                FROM tenant_sessions 
                WHERE otp_code IS NOT NULL 
                ORDER BY created_at DESC 
                LIMIT 5
            '''))
            rows = result.fetchall()
            if rows:
                print(f'Found {len(rows)} OTPs:')
                for row in rows:
                    print(f'  - Session ID: {row[0]}, Tenant ID: {row[1]}, OTP: {row[2]}, Expires: {row[3]}, Created: {row[4]}')
            else:
                print('  No active OTPs found in database')
        
except Exception as e:
    print(f'✗ Error: {e}')
    import traceback
    traceback.print_exc()

