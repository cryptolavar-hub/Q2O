#!/usr/bin/env python3
"""
Create the quick2odoo database if it doesn't exist.

This script connects to the default 'postgres' database to create the application database.
"""

from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

# Connect to default 'postgres' database to create new database
# Updated password: Q2OPostgres2025( (no special character issues)
DSN_POSTGRES = 'postgresql+psycopg://q2o_user:Q2OPostgres2025(@localhost:5432/postgres'
DB_NAME = 'quick2odoo'

print('=' * 60)
print('Creating PostgreSQL Database')
print('=' * 60)
print()

try:
    # Connect to postgres database with autocommit isolation level
    # CREATE DATABASE cannot run inside a transaction block
    engine = create_engine(DSN_POSTGRES, isolation_level="AUTOCOMMIT")
    
    with engine.connect() as conn:
        # Check if database exists
        result = conn.execute(text(f"SELECT 1 FROM pg_database WHERE datname = '{DB_NAME}'"))
        exists = result.fetchone() is not None
        
        if exists:
            print(f'✓ Database "{DB_NAME}" already exists')
        else:
            print(f'Creating database "{DB_NAME}"...')
            try:
                conn.execute(text(f'CREATE DATABASE {DB_NAME}'))
                print(f'✓ Database "{DB_NAME}" created successfully')
            except OperationalError as e:
                if 'already exists' in str(e).lower():
                    print(f'✓ Database "{DB_NAME}" already exists (created by another process)')
                else:
                    raise
    
    # Test connection to new database
    print()
    print('Testing connection to new database...')
    test_dsn = f'postgresql+psycopg://q2o_user:Q2OPostgres2025(@localhost:5432/{DB_NAME}'
    test_engine = create_engine(test_dsn)
    with test_engine.connect() as conn:
        result = conn.execute(text('SELECT current_database(), version()'))
        current_db, version = result.fetchone()
        print(f'✓ Successfully connected to database: {current_db}')
        print(f'  PostgreSQL version: {version[:60]}...')
    
    print()
    print('=' * 60)
    print('SUCCESS: Database is ready')
    print('=' * 60)
    print()
    print('Next steps:')
    print('  1. Run database migrations to create tables')
    print('  2. Restart the backend API')
    print('  3. Test the Admin Portal')
    
except OperationalError as e:
    print(f'✗ Database connection error: {e}')
    print()
    print('Possible issues:')
    print('  - PostgreSQL server is not running')
    print('  - Wrong username/password')
    print('  - Wrong host/port')
    import traceback
    traceback.print_exc()
except Exception as e:
    error_str = str(e)
    if 'permission denied' in error_str.lower() or 'InsufficientPrivilege' in error_str:
        print(f'✗ Permission denied: User "q2o_user" cannot create databases')
        print()
        print('SOLUTION OPTIONS:')
        print()
        print('Option 1: Create database manually as postgres superuser')
        print('  Run this command in psql or pgAdmin:')
        print(f'    CREATE DATABASE {DB_NAME};')
        print('  Or use command line:')
        print(f'    psql -U postgres -c "CREATE DATABASE {DB_NAME};"')
        print()
        print('Option 2: Grant CREATE DATABASE permission to q2o_user')
        print('  Run as postgres superuser:')
        print('    ALTER USER q2o_user CREATEDB;')
        print('  Then run this script again.')
        print()
        print('Option 3: Use an existing database')
        print('  List existing databases:')
        try:
            engine = create_engine(DSN_POSTGRES, isolation_level="AUTOCOMMIT")
            with engine.connect() as conn:
                result = conn.execute(text("SELECT datname FROM pg_database WHERE datistemplate = false ORDER BY datname"))
                dbs = [row[0] for row in result]
                print('  Available databases:')
                for db in dbs:
                    print(f'    - {db}')
                if dbs:
                    print()
                    print(f'  Update DB_DSN in .env to use one of these databases')
                    print(f'  Example: DB_DSN=postgresql+psycopg://q2o_user:Q2OPostgres2025(@localhost:5432/{dbs[0]}')
        except:
            pass
    else:
        print(f'✗ Unexpected error: {e}')
        import traceback
        traceback.print_exc()

