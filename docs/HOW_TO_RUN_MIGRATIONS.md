# How to Run Migrations - Quick2Odoo

## ⚠️ **IMPORTANT: Understanding Quick2Odoo's Two Systems**

Quick2Odoo has **TWO different systems** that people often confuse:

| System | Purpose | Command | When to Use |
|--------|---------|---------|-------------|
| **1. Agent System** | Build NEW SaaS apps | `python main.py` | Building the platform (one-time) |
| **2. Migration System** | Migrate client data | `python run_*_migration.py` | Every client migration |

---

## ❌ **What You Did (Wrong for Your Goal)**

```bash
python main.py --project "SAGE to ODOO" --objective "Full Migration..."
```

**This command tells the agents to BUILD a new SaaS application from scratch.**

Result: The agents started writing code for a new project (test files, etc.)

---

## ✅ **What You Should Do (Correct)**

```bash
python run_sage_migration.py
```

**This command USES the existing migration system to migrate SAGE data to Odoo.**

Result: Actual data migration happens!

---

## 🎯 **The Correct Workflow for SAGE Migration**

### **Prerequisites** (One-time setup)

1. **SAGE API credentials** (from your SAGE account)
2. **Odoo instance** (running Odoo v18)
3. **Environment configured** (.env file)

---

### **Step 1: Create `.env` file** (if not already done)

```bash
# Copy the example
cp env.example .env

# Edit .env and add your credentials
```

Add these values to `.env`:

```bash
# SAGE Configuration
SAGE_BASE_URL=https://api.sage.com          # Or your SAGE API URL
SAGE_API_KEY=your_sage_api_key_here
SAGE_API_SECRET=your_sage_api_secret_here
SAGE_VERSION=50                              # Or 100, 200, X3

# Odoo Configuration
ODOO_URL=https://your-odoo-instance.com
ODOO_DB=your_database_name
ODOO_USERNAME=admin
ODOO_PASSWORD=your_odoo_password
```

---

### **Step 2: Create SAGE Client** (from template)

The template exists at `templates/integration/sage_client.j2`. You need to copy it to the actual client location:

```bash
# Create the clients directory if it doesn't exist
mkdir -p api/app/clients

# Copy the template (rename .j2 to .py and remove Jinja2 tags if any)
cp templates/integration/sage_client.j2 api/app/clients/sage.py
```

**OR** manually create `api/app/clients/sage.py` with the SAGE client code.

---

### **Step 3: Run the Migration**

```bash
# Make sure you're in the venv
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux

# Run the migration
python run_sage_migration.py
```

**Interactive Prompts**:
```
How many years of data to migrate? [1]: 2
Estimated cost: $245.00
Proceed with migration? (yes/no): yes
```

**What Happens**:
1. ✅ Connects to SAGE API
2. ✅ Connects to Odoo API
3. ✅ Extracts data from SAGE (Customers, Invoices, etc.)
4. ✅ Transforms data using `config/sage_to_odoo_mapping.json`
5. ✅ Loads data into Odoo
6. ✅ Validates data integrity
7. ✅ Generates migration report

---

## 📊 **What Gets Migrated** (SAGE → Odoo)

Based on `config/sage_to_odoo_mapping.json`:

| SAGE Entity | Odoo Model | Count (typical) |
|-------------|-----------|-----------------|
| Customers | `res.partner` | 100-1000 |
| Suppliers | `res.partner` | 50-500 |
| Products | `product.product` | 200-2000 |
| Nominal Accounts | `account.account` | 50-200 |
| Sales Invoices | `account.move` | 500-5000 |
| Purchase Invoices | `account.move` | 200-2000 |
| Payments | `account.payment` | 300-3000 |

**Total**: 35+ entity types mapped

---

## 🔧 **Migration Sequence** (Automatic)

The `MigrationOrchestrator` runs migrations in this order (to preserve relationships):

1. **Nominal Accounts** (Chart of Accounts) - must exist first
2. **Customers** - needed for invoices
3. **Suppliers** - needed for bills
4. **Products** - needed for invoice lines
5. **Sales Invoices** - references customers & products
6. **Purchase Invoices** - references suppliers & products
7. **Payments** - references invoices

---

## 📁 **Migration Output**

After migration, you'll get:

```
sage_migration_20251105_163000.log          # Detailed log file
migration_report_20251105_163000.json       # JSON report
migration_report_20251105_163000.html       # HTML report (human-readable)
```

**Report Contents**:
- Migration summary (total records, duration, status)
- Entity-by-entity breakdown
- Entity mapping (SAGE ID → Odoo ID)
- Validation results
- Errors and warnings
- Data quality metrics

---

## 🐛 **Troubleshooting**

### **"SAGEClient not found"**

**Problem**: `api/app/clients/sage.py` doesn't exist

**Solution**:
```bash
# Copy the template
cp templates/integration/sage_client.j2 api/app/clients/sage.py
```

---

### **"Missing environment variables"**

**Problem**: `.env` file not configured

**Solution**:
```bash
# Copy example
cp env.example .env

# Edit .env and add your SAGE and Odoo credentials
```

---

### **"SAGE API connection failed: 401"**

**Problem**: Invalid SAGE API credentials

**Solution**:
- Check `SAGE_API_KEY` and `SAGE_API_SECRET` in `.env`
- Verify credentials in your SAGE account
- Ensure API access is enabled in SAGE

---

### **"Odoo authentication failed"**

**Problem**: Invalid Odoo credentials or wrong database

**Solution**:
- Check `ODOO_URL`, `ODOO_DB`, `ODOO_USERNAME`, `ODOO_PASSWORD` in `.env`
- Verify you can log in to Odoo web interface with these credentials
- Ensure the database name is correct (often just "odoo" or "your_company")

---

### **"Migration failed: mapping not found"**

**Problem**: Entity mapping missing

**Solution**:
- Check `config/sage_to_odoo_mapping.json` exists
- Verify it has mappings for the entities you're migrating
- If you need custom entities, add them to the mapping file

---

## 🔄 **Re-running Migrations**

### **Fresh Start (Delete Odoo Data)**

If you want to start over:

1. In Odoo, delete migrated records:
   - Go to each module (Contacts, Invoices, etc.)
   - Use filters to find imported records
   - Delete them

2. Re-run the migration:
   ```bash
   python run_sage_migration.py
   ```

---

### **Incremental Migration (Add New Data)**

The migration system supports incremental migrations:

```python
# In run_sage_migration.py, modify to use modified_since
from datetime import datetime, timedelta

# Only migrate data from last 7 days
since_date = datetime.now() - timedelta(days=7)
result = orchestrator.run_incremental_migration(modified_since=since_date)
```

---

## 🆚 **When to Use Each System**

### **Use `python main.py` when:**
- ❌ Never for client migrations
- ✅ Building a NEW custom SaaS application
- ✅ Generating boilerplate code
- ✅ Creating project scaffolding

**Example**:
```bash
# Building a new HR management SaaS
python main.py --project "HR SaaS" --objective "Employee onboarding"
```

---

### **Use `python run_*_migration.py` when:**
- ✅ Migrating client data (SAGE, QuickBooks, etc.)
- ✅ Running actual production migrations
- ✅ Testing migrations with real data
- ✅ Generating migration reports

**Example**:
```bash
# Migrating client's SAGE data to Odoo
python run_sage_migration.py

# Migrating client's QuickBooks data to Odoo
python run_quickbooks_migration.py
```

---

## 📚 **Related Documentation**

- **[COMPLETE_SYSTEM_WORKFLOW.md](COMPLETE_SYSTEM_WORKFLOW.md)** - Understanding Phase 1 vs Phase 2
- **[FULL_MIGRATION_ARCHITECTURE.md](FULL_MIGRATION_ARCHITECTURE.md)** - How the migration system works
- **[SAGE mapping](../config/sage_to_odoo_mapping.json)** - Field mappings
- **[ENVIRONMENT_CONFIGURATION_GUIDE.md](ENVIRONMENT_CONFIGURATION_GUIDE.md)** - Setting up .env

---

## ✅ **Quick Reference**

```bash
# WRONG (for migrations)
python main.py --project "SAGE to Odoo" --objective "Migration"

# CORRECT (for migrations)
python run_sage_migration.py
```

---

## 💡 **Summary**

1. **Quick2Odoo has TWO systems**: Agents (build SaaS) and Migration (migrate data)
2. **For client migrations**: Use `run_*_migration.py`
3. **Migration system**: Already built, ready to use
4. **Just configure**: Set up `.env` with credentials
5. **Run**: `python run_sage_migration.py`

**The migration templates, orchestrator, mapper, and clients are ALREADY BUILT. You don't need to generate them with agents!**

