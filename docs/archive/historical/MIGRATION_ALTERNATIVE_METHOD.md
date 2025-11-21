# Alternative Migration Methods
**Date**: November 12, 2025

---

## 🔧 **If psql.exe is Not Found**

If the migration script cannot find `psql.exe`, you have several options:

### **Option 1: Run SQL Manually (Easiest)**

1. **Open pgAdmin** (or any PostgreSQL client)
2. **Connect** to your database (`q2o` database, `q2o_user` user)
3. **Open** the SQL file: `addon_portal\migrations_manual\006_create_platform_events_table.sql`
4. **Execute** the script (F5 or Execute button)
5. **Verify** by running:
   ```sql
   SELECT column_name FROM information_schema.columns 
   WHERE table_name = 'platform_events';
   ```

### **Option 2: Set PSQL_PATH Environment Variable**

Before running the migration script, set the path:

```batch
set PSQL_PATH=C:\Program Files\PostgreSQL\16\bin\psql.exe
.\RUN_MIGRATION_006.bat
```

Or set it permanently in Windows:
1. Open System Properties → Environment Variables
2. Add new User Variable:
   - Name: `PSQL_PATH`
   - Value: `C:\Program Files\PostgreSQL\16\bin\psql.exe` (adjust version/path as needed)

### **Option 3: Add PostgreSQL to PATH**

1. Find your PostgreSQL installation (usually `C:\Program Files\PostgreSQL\XX\bin`)
2. Add that directory to your Windows PATH environment variable
3. Restart your terminal/command prompt
4. Run the migration script again

### **Option 4: Use Python Script Instead**

If you prefer Python, you can run the migration using SQLAlchemy:

```python
# run_migration_006.py
from sqlalchemy import create_engine, text
from addon_portal.api.core.settings import settings

engine = create_engine(settings.DB_DSN)

with open('addon_portal/migrations_manual/006_create_platform_events_table.sql', 'r') as f:
    sql = f.read()

with engine.connect() as conn:
    conn.execute(text(sql))
    conn.commit()

print("Migration 006 completed successfully!")
```

Run with: `python run_migration_006.py`

---

## 📝 **Quick Reference**

**Migration File**: `addon_portal\migrations_manual\006_create_platform_events_table.sql`

**What it does**: Creates `platform_events` table for database-backed event logging

**Database**: `q2o`  
**User**: `q2o_user`  
**Password**: Check `addon_portal\.env` file (DB_DSN)

---

**Note**: The migration script will prompt you for the psql path if it's not found automatically.

