# Create Database Instructions

## Problem
The database `quick2odoo` does not exist, causing **ALL API endpoints to fail** with:
```
FATAL: database "quick2odoo" does not exist
```

## Solution Options

### Option 1: Create Database Manually (Recommended)

Connect to PostgreSQL as a superuser (usually `postgres`) and create the database:

**Using psql command line:**
```bash
psql -U postgres -c "CREATE DATABASE quick2odoo;"
```

**Using pgAdmin:**
1. Connect to PostgreSQL server as `postgres` user
2. Right-click on "Databases" → "Create" → "Database..."
3. Name: `quick2odoo`
4. Click "Save"

**Using SQL:**
```sql
CREATE DATABASE quick2odoo;
```

### Option 2: Grant Permission to q2o_user

If you want `q2o_user` to be able to create databases:

```sql
ALTER USER q2o_user CREATEDB;
```

Then run `python create_database.py` again.

### Option 3: Use an Existing Database

If you already have a database you want to use, update the `DB_DSN` in `.env`:

1. List existing databases:
   ```sql
   SELECT datname FROM pg_database WHERE datistemplate = false;
   ```

2. Update `.env` file:
   ```
   DB_DSN=postgresql+psycopg://q2o_user:Q2OPostgres2025!@localhost:5432/YOUR_EXISTING_DB_NAME
   ```

## After Creating Database

Once the database is created:

1. **Run migrations** to create tables:
   - Migration 006: `platform_events` table
   - Migration 007: Tenant contact fields (already run)
   - Other migrations as needed

2. **Restart the backend API** to connect to the new database

3. **Test the Admin Portal** - all endpoints should now work

## Verification

Test the connection:
```bash
python -c "from sqlalchemy import create_engine, inspect; from addon_portal.api.core.settings import settings; engine = create_engine(settings.DB_DSN); insp = inspect(engine); tables = insp.get_table_names(); print(f'Connected! Found {len(tables)} tables')"
```

