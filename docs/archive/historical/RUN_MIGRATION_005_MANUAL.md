# How to Run Migration 005: Add Tenant Scoping to Projects

## Option 1: Using Command Prompt (Windows)

### Prerequisites
- PostgreSQL installed and `psql` in your PATH
- Database credentials from your `.env` file

### Step-by-Step

1. **Open Command Prompt** (CMD) or PowerShell

2. **Navigate to project root**:
   ```cmd
   cd C:\Q2O_Combined
   ```

3. **Run the batch script**:
   ```cmd
   .\RUN_MIGRATION_005.bat
   ```
   
   OR manually:
   ```cmd
   psql -h localhost -p 5432 -U q2o_user -d q2o -f addon_portal\migrations_manual\005_add_tenant_scoping_to_projects.sql
   ```

4. **Enter your database password** when prompted

---

## Option 2: Using pgAdmin (GUI)

1. **Open pgAdmin**
2. **Connect to your PostgreSQL server**
3. **Right-click on your database** (`q2o`) → **Query Tool**
4. **Open the migration file**:
   - File → Open → Navigate to `addon_portal/migrations_manual/005_add_tenant_scoping_to_projects.sql`
5. **Click Execute** (F5) or press the play button

---

## Option 3: Using psql Command Line (Direct)

### If you know your connection details:

```cmd
psql -h localhost -p 5432 -U q2o_user -d q2o -f addon_portal\migrations_manual\005_add_tenant_scoping_to_projects.sql
```

### With password in connection string (less secure):

```cmd
set PGPASSWORD=your_password_here
psql -h localhost -p 5432 -U q2o_user -d q2o -f addon_portal\migrations_manual\005_add_tenant_scoping_to_projects.sql
```

---

## Option 4: Using Python Script (If psql not available)

Create a file `run_migration_005.py`:

```python
import sys
from pathlib import Path
from sqlalchemy import text
from addon_portal.api.core.db import engine

def run_migration():
    migration_file = Path(__file__).parent / "addon_portal" / "migrations_manual" / "005_add_tenant_scoping_to_projects.sql"
    
    with open(migration_file, 'r') as f:
        sql = f.read()
    
    with engine.connect() as conn:
        # Split by semicolons and execute each statement
        statements = [s.strip() for s in sql.split(';') if s.strip() and not s.strip().startswith('--')]
        
        for statement in statements:
            if statement:
                try:
                    conn.execute(text(statement))
                    conn.commit()
                    print(f"✓ Executed: {statement[:50]}...")
                except Exception as e:
                    print(f"✗ Error: {e}")
                    print(f"  Statement: {statement[:100]}...")
                    conn.rollback()
                    raise
    
    print("\n✅ Migration completed successfully!")

if __name__ == "__main__":
    run_migration()
```

Then run:
```cmd
cd C:\Q2O_Combined
python run_migration_005.py
```

---

## Verify Migration Success

After running the migration, verify it worked:

```sql
-- Check tenant_id column exists
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'llm_project_config' AND column_name = 'tenant_id';

-- Check activation_code_id column exists
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'llm_project_config' AND column_name = 'activation_code_id';

-- Check tenant_sessions table exists
SELECT table_name FROM information_schema.tables WHERE table_name = 'tenant_sessions';

-- Check indexes
SELECT indexname FROM pg_indexes WHERE tablename = 'llm_project_config' AND indexname LIKE '%tenant%';
```

---

## Troubleshooting

### Error: "psql: command not found"
- **Solution**: Add PostgreSQL `bin` directory to your PATH, or use pgAdmin GUI

### Error: "password authentication failed"
- **Solution**: Check your `.env` file for correct `DB_DSN` or enter correct password

### Error: "database does not exist"
- **Solution**: Create the database first or check your database name in `.env`

### Error: "relation already exists"
- **Solution**: Migration may have already been run. Check if columns exist using verification queries above.

### Error: "permission denied"
- **Solution**: Ensure your database user has CREATE, ALTER, and INDEX permissions

---

## Quick Reference

**Migration File**: `addon_portal/migrations_manual/005_add_tenant_scoping_to_projects.sql`

**What it does**:
- Adds `tenant_id` to `llm_project_config`
- Adds `activation_code_id` to `llm_project_config`
- Adds project status fields
- Creates `tenant_sessions` table
- Creates necessary indexes and foreign keys

**Safe to run multiple times**: Yes (uses `IF NOT EXISTS` clauses)

