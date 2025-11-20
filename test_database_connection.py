#!/usr/bin/env python3
"""Test database connection and check for issues."""

from sqlalchemy import create_engine, inspect, text

# Use new password: Q2OPostgres2025(
DSN = 'postgresql+psycopg://q2o_user:Q2OPostgres2025(@localhost:5432/q2o'

print('=' * 60)
print('Testing Database Connection and Queries')
print('=' * 60)
print()

try:
    engine = create_engine(DSN)
    
    # Test basic connection
    with engine.connect() as conn:
        result = conn.execute(text('SELECT COUNT(*) FROM tenants'))
        tenant_count = result.scalar()
        print(f'✓ Connected successfully')
        print(f'✓ Tenants in database: {tenant_count}')
        print()
        
        # Test tenant query with relationships
        print('Testing tenant query with relationships...')
        result = conn.execute(text('''
            SELECT t.id, t.name, t.slug, t.email, t.phone_number,
                   s.status, p.name as plan_name
            FROM tenants t
            LEFT JOIN subscriptions s ON t.id = s.tenant_id
            LEFT JOIN plans p ON s.plan_id = p.id
            LIMIT 5
        '''))
        rows = result.fetchall()
        if rows:
            print(f'✓ Tenant query with relationships works: {len(rows)} rows')
            for row in rows[:3]:
                print(f'  - {row[1]} ({row[2]}) - Email: {row[3] or "N/A"}')
        else:
            print('⚠ No tenants found (this is OK if database is empty)')
        print()
        
        # Check platform_events table
        print('Checking platform_events table...')
        result = conn.execute(text('SELECT COUNT(*) FROM platform_events'))
        events_count = result.scalar()
        print(f'✓ platform_events table accessible: {events_count} events')
        print()
        
        # Check llm_project_config table
        print('Checking llm_project_config table...')
        result = conn.execute(text('SELECT COUNT(*) FROM llm_project_config'))
        projects_count = result.scalar()
        print(f'✓ llm_project_config table accessible: {projects_count} projects')
        print()
        
        # Check activation_codes table
        print('Checking activation_codes table...')
        result = conn.execute(text('SELECT COUNT(*) FROM activation_codes'))
        codes_count = result.scalar()
        print(f'✓ activation_codes table accessible: {codes_count} codes')
        print()
        
    print('=' * 60)
    print('✓ All database checks passed!')
    print('=' * 60)
    
except Exception as e:
    print(f'✗ Error: {e}')
    import traceback
    traceback.print_exc()

