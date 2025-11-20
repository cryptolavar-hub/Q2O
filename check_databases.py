#!/usr/bin/env python3
"""Check what databases exist in PostgreSQL."""

from sqlalchemy import create_engine, text

# Connect to default 'postgres' database to list all databases
dsn = 'postgresql+psycopg://q2o_user:Q2OPostgres2025(@localhost:5432/postgres'

try:
    engine = create_engine(dsn)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT datname FROM pg_database WHERE datistemplate = false ORDER BY datname"))
        databases = [row[0] for row in result]
        
        print('=' * 60)
        print('Available PostgreSQL Databases:')
        print('=' * 60)
        for db in databases:
            print(f'  - {db}')
        print()
        
        # Check if quick2odoo exists
        if 'quick2odoo' in databases:
            print('✓ Database "quick2odoo" exists')
        else:
            print('✗ Database "quick2odoo" does NOT exist')
            print()
            print('Options:')
            print('  1. Create the database:')
            print('     CREATE DATABASE quick2odoo;')
            print('  2. Or update DB_DSN in .env to use an existing database')
            if databases:
                print(f'     Suggested: Use database "{databases[0]}"')
                
except Exception as e:
    print(f'✗ Failed to connect to PostgreSQL: {e}')
    print()
    print('Possible issues:')
    print('  - PostgreSQL server is not running')
    print('  - Wrong username/password')
    print('  - Wrong host/port')

