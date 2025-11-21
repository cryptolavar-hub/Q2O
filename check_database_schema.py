#!/usr/bin/env python3
"""Check current database schema to see what tables and columns exist."""

from sqlalchemy import create_engine, inspect, text

# Use new password: Q2OPostgres2025(
DSN = 'postgresql+psycopg://q2o_user:Q2OPostgres2025(@localhost:5432/q2o'

print('=' * 60)
print('Checking q2o Database Schema')
print('=' * 60)
print()

try:
    engine = create_engine(DSN)
    insp = inspect(engine)
    
    # Get all tables
    tables = sorted(insp.get_table_names())
    print(f'Found {len(tables)} tables:')
    for table in tables:
        print(f'  - {table}')
    print()
    
    # Check tenants table specifically
    if 'tenants' in tables:
        print('Tenants table columns:')
        cols = insp.get_columns('tenants')
        col_names = [c['name'] for c in cols]
        for col in cols:
            print(f'  - {col["name"]}: {col["type"]}')
        print()
        
        # Check for required columns from migration 007
        required_cols = ['email', 'phone_number', 'otp_delivery_method']
        missing_cols = [c for c in required_cols if c not in col_names]
        if missing_cols:
            print(f'⚠ Missing columns in tenants table: {missing_cols}')
        else:
            print('✓ All required tenant contact columns present')
    else:
        print('✗ tenants table does not exist')
    print()
    
    # Check platform_events table
    if 'platform_events' in tables:
        print('✓ platform_events table exists')
    else:
        print('⚠ platform_events table does NOT exist (migration 006 needed)')
    print()
    
    # Check other critical tables
    critical_tables = ['activation_codes', 'devices', 'subscriptions', 'plans', 
                      'llm_project_config', 'llm_system_config']
    for table in critical_tables:
        if table in tables:
            print(f'✓ {table} exists')
        else:
            print(f'✗ {table} MISSING')
    
except Exception as e:
    print(f'✗ Error: {e}')
    import traceback
    traceback.print_exc()

