# ⚠️ Important Fixes Guide - Q2O Licensing Addon

**Purpose**: Fix important (non-critical) issues for production readiness.

**Estimated Time**: 2-3 hours  
**Difficulty**: Medium  
**Prerequisites**: Critical fixes completed, familiarity with Python packaging, database migrations

---

## 📋 OVERVIEW OF IMPORTANT ISSUES

| # | Issue | Impact | Priority | Time |
|---|-------|--------|----------|------|
| 4 | Missing Dependencies File | Can't install consistently | **HIGH** | 15 min |
| 5 | Missing Database Migrations | Tables won't exist | **HIGH** | 30 min |
| 6 | No Environment Examples | Users won't know what to configure | **HIGH** | 30 min |
| 7 | CLI Import Path Issue | CLI won't run directly | MEDIUM | 15 min |
| 8 | SQLAlchemy Deprecation | Future compatibility | MEDIUM | 10 min |
| 9 | Hardcoded Default Secrets | Security risk | **HIGH** | 20 min |

---

## ⚠️ IMPORTANT FIX #4: Missing Dependencies File

### **Problem**
No `requirements.txt` means:
- Users don't know what to install
- Version mismatches cause bugs
- Can't reproduce environment

### **Solution**

Create `addon_portal/requirements.txt`:

```txt
# Q2O Licensing Addon - Python Dependencies
# Compatible with Python 3.10-3.12

# Core Framework
fastapi>=0.110.0,<0.111.0
uvicorn[standard]>=0.27.0,<0.28.0

# Database
sqlalchemy>=2.0.25,<2.1.0
psycopg2-binary>=2.9.9,<3.0.0
alembic>=1.13.0,<1.14.0

# Data Validation
pydantic>=2.6.0,<3.0.0
pydantic-settings>=2.1.0,<3.0.0

# Payment Integration
stripe>=7.0.0,<8.0.0

# Authentication
pyjwt>=2.8.0,<3.0.0
Authlib>=1.3.0,<2.0.0

# Templates & Web
Jinja2>=3.1.3,<4.0.0
python-multipart>=0.0.6,<0.1.0

# Security
cryptography>=41.0.0,<42.0.0
```

### **Installation**

```bash
cd addon_portal
pip install -r requirements.txt
```

### **Verification**

```bash
pip list
# Check all packages are installed with correct versions
```

---

## ⚠️ IMPORTANT FIX #5: Missing Database Migrations

### **Problem**
No Alembic migrations = database tables don't exist on first run.

**Error you'll see**:
```
sqlalchemy.exc.ProgrammingError: relation "tenants" does not exist
```

### **Solution Options**

#### **Option A: Create Alembic Migrations** (Recommended)

**Step 1**: Initialize Alembic

```bash
cd addon_portal
alembic init migrations
```

**Step 2**: Configure `alembic.ini`

Edit `addon_portal/alembic.ini` line 63:

```ini
# Before:
sqlalchemy.url = driver://user:pass@localhost/dbname

# After:
sqlalchemy.url = postgresql+psycopg://user:pass@localhost:5432/q2o_licensing
```

**OR** use environment variable:

```ini
# Leave alembic.ini as-is, then in migrations/env.py:
```

**Step 3**: Update `migrations/env.py`

Replace the imports and config section:

```python
from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.core.db import Base
from api.core.settings import settings
from api.models.licensing import (
    Tenant, Plan, Subscription, Device, 
    UsageEvent, MonthlyUsageRollup, ActivationCode
)

# this is the Alembic Config object
config = context.config

# Override sqlalchemy.url with our settings
config.set_main_option('sqlalchemy.url', settings.DB_DSN)

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here for 'autogenerate' support
target_metadata = Base.metadata

# ... rest of the file stays the same
```

**Step 4**: Generate Initial Migration

```bash
alembic revision --autogenerate -m "Initial licensing schema"
```

This creates `migrations/versions/xxxx_initial_licensing_schema.py`

**Step 5**: Review Generated Migration

Check the generated file looks correct:

```python
"""Initial licensing schema

Revision ID: abc123def456
Revises: 
Create Date: 2025-11-06 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'abc123def456'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Creates all tables
    op.create_table('tenants',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('slug', sa.String(), nullable=False),
        # ... etc
    )
    # ... more tables

def downgrade() -> None:
    # Drops all tables
    op.drop_table('activation_codes')
    # ... etc
```

**Step 6**: Run Migration

```bash
alembic upgrade head
```

**Expected Output**:
```
INFO  [alembic.runtime.migration] Running upgrade  -> abc123def456, Initial licensing schema
```

#### **Option B: Direct Table Creation** (Quick & Dirty)

Create `addon_portal/create_tables.py`:

```python
"""
Direct table creation script (alternative to Alembic)
USE ONLY FOR DEVELOPMENT/TESTING
"""
from api.core.db import Base, engine
from api.models.licensing import (
    Tenant, Plan, Subscription, Device, 
    UsageEvent, MonthlyUsageRollup, ActivationCode
)

if __name__ == "__main__":
    print("Creating all tables...")
    Base.metadata.create_all(bind=engine)
    print("✓ Tables created successfully")
```

Run it:
```bash
cd addon_portal
python create_tables.py
```

### **Verification**

Connect to database and verify tables exist:

```bash
psql -U user -d q2o_licensing -c "\dt"
```

**Expected Output**:
```
                List of relations
 Schema |         Name          | Type  | Owner 
--------+-----------------------+-------+-------
 public | activation_codes      | table | user
 public | devices               | table | user
 public | monthly_usage_rollups | table | user
 public | plans                 | table | user
 public | subscriptions         | table | user
 public | tenants               | table | user
 public | usage_events          | table | user
(7 rows)
```

---

## ⚠️ IMPORTANT FIX #6: No Environment Configuration Examples

### **Problem**
Users don't know what environment variables to configure.

### **Solution**

Create `addon_portal/.env.example`:

```bash
#═══════════════════════════════════════════════════════════════
# Q2O Licensing Addon - Environment Configuration
#═══════════════════════════════════════════════════════════════

# Application
APP_NAME=Q2O
ENV=production  # dev, staging, production

#───────────────────────────────────────────────────────────────
# Database Configuration
#───────────────────────────────────────────────────────────────
# Format: postgresql+psycopg://user:password@host:port/database
DB_DSN=postgresql+psycopg://q2o_user:CHANGE_ME_DB_PASSWORD@localhost:5432/q2o_licensing

#───────────────────────────────────────────────────────────────
# JWT Configuration (RS256 - Asymmetric Keys)
#───────────────────────────────────────────────────────────────
# Generate RSA keys with:
#   ssh-keygen -t rsa -b 2048 -m PEM -f jwt.key
#   openssl rsa -in jwt.key -pubout -outform PEM -out jwt.key.pub
#
# Then paste the contents (with \n for newlines):

JWT_ISSUER=q2o-auth
JWT_AUDIENCE=q2o-clients
JWT_ACCESS_TTL_SECONDS=900
JWT_REFRESH_TTL_SECONDS=1209600

# Private key (keep secret!)
JWT_PRIVATE_KEY="-----BEGIN RSA PRIVATE KEY-----\nMIIEpAIBAAKCAQEA...\n-----END RSA PRIVATE KEY-----"

# Public key (can be shared)
JWT_PUBLIC_KEY="-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA...\n-----END PUBLIC KEY-----"

#───────────────────────────────────────────────────────────────
# Stripe Configuration
#───────────────────────────────────────────────────────────────
# Get from: https://dashboard.stripe.com/apikeys
STRIPE_SECRET_KEY=sk_test_51xxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Webhook secret from: https://dashboard.stripe.com/webhooks
STRIPE_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

#───────────────────────────────────────────────────────────────
# Security Configuration
#───────────────────────────────────────────────────────────────
# Generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"

# Pepper for activation codes (never change in production!)
ACTIVATION_CODE_PEPPER=CHANGE_ME_TO_RANDOM_32_CHAR_STRING_xxxxxxxxxxxxx

# Session secret for admin UI
SESSION_SECRET=CHANGE_ME_TO_RANDOM_32_CHAR_STRING_xxxxxxxxxxxxx

#───────────────────────────────────────────────────────────────
# OIDC/SSO Configuration (Optional - for Admin Auth)
#───────────────────────────────────────────────────────────────
# Leave empty to disable SSO authentication
OIDC_ISSUER=
OIDC_CLIENT_ID=
OIDC_CLIENT_SECRET=
OIDC_REDIRECT_URL=

# Example for Auth0:
# OIDC_ISSUER=https://your-tenant.auth0.com
# OIDC_CLIENT_ID=your_client_id_from_auth0
# OIDC_CLIENT_SECRET=your_client_secret_from_auth0
# OIDC_REDIRECT_URL=http://localhost:8080/auth/callback

# Example for Keycloak:
# OIDC_ISSUER=https://keycloak.example.com/realms/q2o
# OIDC_CLIENT_ID=q2o-licensing
# OIDC_CLIENT_SECRET=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
# OIDC_REDIRECT_URL=http://localhost:8080/auth/callback

#───────────────────────────────────────────────────────────────
# CORS Configuration
#───────────────────────────────────────────────────────────────
# Comma-separated list of allowed origins
ALLOWED_ORIGINS=["http://localhost:3000","http://localhost:8080"]

# Production example:
# ALLOWED_ORIGINS=["https://portal.q2o.com","https://app.q2o.com"]

#───────────────────────────────────────────────────────────────
# CDN Configuration (Optional - for Tenant Branding Assets)
#───────────────────────────────────────────────────────────────
# Base URL for tenant logos and assets
BRANDING_CDN_BASE=

# Example:
# BRANDING_CDN_BASE=https://cdn.q2o.com/branding
```

Create `addon_portal/apps/tenant-portal/.env.local.example`:

```bash
#═══════════════════════════════════════════════════════════════
# Q2O Tenant Portal - Environment Configuration
#═══════════════════════════════════════════════════════════════

# API Base URL
NEXT_PUBLIC_LIC_API=http://localhost:8080

# Production example:
# NEXT_PUBLIC_LIC_API=https://api-licensing.q2o.com
```

### **Usage**

```bash
# Backend
cd addon_portal
cp .env.example .env
nano .env  # Edit with your values

# Frontend
cd apps/tenant-portal
cp .env.local.example .env.local
nano .env.local  # Edit with your values
```

### **Generate Secrets Script**

Create `addon_portal/generate_secrets.py`:

```python
#!/usr/bin/env python3
"""
Generate secure secrets for .env file
"""
import secrets
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

def generate_pepper():
    """Generate 32-byte URL-safe secret"""
    return secrets.token_urlsafe(32)

def generate_rsa_keypair():
    """Generate RSA-2048 keypair for JWT"""
    # Generate private key
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    
    # Serialize private key
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption()
    ).decode('utf-8')
    
    # Generate public key
    public_key = private_key.public_key()
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode('utf-8')
    
    return private_pem, public_pem

if __name__ == "__main__":
    print("🔐 Generating secure secrets for Q2O Licensing Addon\n")
    print("="*70)
    
    # Generate secrets
    pepper = generate_pepper()
    session_secret = generate_pepper()
    private_key, public_key = generate_rsa_keypair()
    
    # Output
    print("\n📋 Copy these to your .env file:\n")
    print(f"ACTIVATION_CODE_PEPPER={pepper}")
    print(f"SESSION_SECRET={session_secret}")
    print()
    print('JWT_PRIVATE_KEY="' + private_key.replace('\n', '\\n') + '"')
    print()
    print('JWT_PUBLIC_KEY="' + public_key.replace('\n', '\\n') + '"')
    print()
    print("="*70)
    print("\n✅ Secrets generated successfully!")
    print("\n⚠️  IMPORTANT: Keep JWT_PRIVATE_KEY secret! Never commit to git!")
```

Run it:
```bash
cd addon_portal
python generate_secrets.py
```

---

## ⚠️ IMPORTANT FIX #7: CLI Import Path Issue

### **Problem**
CLI script uses relative imports `from ..api.core.db` which only work when run as a module.

**Error you'll see**:
```
ImportError: attempted relative import with no known parent package
```

### **Solution Options**

#### **Option A: Run as Module** (Recommended)

Always run CLI as a module:

```bash
# ✓ Works
python -m scripts.admin_cli seed-plan --name Pro --price-id price_xxx --quota 1000

# ✗ Fails
python scripts/admin_cli.py seed-plan --name Pro --price-id price_xxx --quota 1000
```

#### **Option B: Add Path Manipulation**

Add to top of `scripts/admin_cli.py`:

```python
import argparse, sys, secrets, string, hashlib
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Now these imports will work
from api.core.db import SessionLocal
from api.core.settings import settings
from api.models.licensing import Plan, Tenant, Subscription, SubscriptionState, ActivationCode
```

#### **Option C: Create Shell Wrapper**

Create `addon_portal/admin`:

```bash
#!/bin/bash
# Q2O Licensing Admin CLI Wrapper
cd "$(dirname "$0")"
python -m scripts.admin_cli "$@"
```

Make it executable:
```bash
chmod +x addon_portal/admin
```

Use it:
```bash
./admin seed-plan --name Pro --price-id price_xxx --quota 1000
```

### **Recommendation**

Use **Option B + Option C** together:
1. Fix the script to work both ways
2. Provide shell wrapper for convenience

---

## ⚠️ IMPORTANT FIX #8: SQLAlchemy Deprecation

### **Problem**
Using old-style `declarative_base()` instead of SQLAlchemy 2.0 style.

**Future Warning**:
```
SADeprecationWarning: The declarative_base() function is deprecated
```

### **Solution**

**File**: `addon_portal/api/core/db.py`

**Current Code** (lines 2-3):
```python
from sqlalchemy.orm import sessionmaker, declarative_base

Base = declarative_base()
```

**Fixed Code**:
```python
from sqlalchemy.orm import sessionmaker, DeclarativeBase

class Base(DeclarativeBase):
    pass
```

**Complete Fixed File**:

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from .settings import settings

engine = create_engine(settings.DB_DSN, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

class Base(DeclarativeBase):
    pass
```

### **Note**
This change is **cosmetic** - both work identically in SQLAlchemy 2.0. But the new style:
- ✅ No deprecation warnings
- ✅ Better type inference
- ✅ Future-proof

---

## ⚠️ IMPORTANT FIX #9: Hardcoded Default Secrets

### **Problem**
Settings has insecure default values that users might accidentally deploy.

**Risk**: If user forgets to create `.env`, app runs with:
```python
JWT_PRIVATE_KEY: str = "CHANGE_ME_RSA_PRIV_PEM"  # ❌ Not secure!
ACTIVATION_CODE_PEPPER: str = "CHANGE_ME_ACTIVATION_PEPPER"  # ❌ Not secure!
```

### **Solution**

Add validation to `Settings` class:

**File**: `addon_portal/api/core/settings.py`

Add after the class definition, before `settings = Settings()`:

```python
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import AnyHttpUrl, model_validator
from typing import Optional, List

class Settings(BaseSettings):
    # ... all existing fields ...
    
    model_config = SettingsConfigDict(env_file=".env")
    
    @model_validator(mode='after')
    def validate_secrets(self):
        """Ensure production secrets are configured"""
        if self.ENV == "production":
            # Check JWT keys
            if "CHANGE_ME" in self.JWT_PRIVATE_KEY:
                raise ValueError(
                    "JWT_PRIVATE_KEY must be configured for production! "
                    "Run: python generate_secrets.py"
                )
            if "CHANGE_ME" in self.JWT_PUBLIC_KEY:
                raise ValueError("JWT_PUBLIC_KEY must be configured for production!")
            
            # Check activation pepper
            if "CHANGE_ME" in self.ACTIVATION_CODE_PEPPER:
                raise ValueError(
                    "ACTIVATION_CODE_PEPPER must be configured for production! "
                    "Use: python -c \"import secrets; print(secrets.token_urlsafe(32))\""
                )
            
            # Check session secret
            if "CHANGE_ME" in self.SESSION_SECRET:
                raise ValueError("SESSION_SECRET must be configured for production!")
            
            # Check Stripe keys
            if self.STRIPE_SECRET_KEY.startswith("sk_test_"):
                raise ValueError("STRIPE_SECRET_KEY must be production key (sk_live_...)")
        
        return self

settings = Settings()
```

### **Result**

Now if someone tries to run in production without configuring:

```bash
ENV=production uvicorn api.main:app
```

They get:
```
ValueError: JWT_PRIVATE_KEY must be configured for production! Run: python generate_secrets.py
```

### **Development Mode**

For development, secrets can be insecure:
```bash
ENV=dev uvicorn api.main:app  # ✓ Works with default secrets
```

---

## ✅ POST-FIX VERIFICATION CHECKLIST

After applying all important fixes:

### **1. Dependencies Installed**
```bash
pip list | grep -E "(fastapi|sqlalchemy|pydantic-settings|stripe|alembic)"
```

Expected: All packages with correct versions

### **2. Database Tables Exist**
```bash
psql -U user -d q2o_licensing -c "\dt" | wc -l
```

Expected: `7` tables (plus header)

### **3. Environment Configured**
```bash
cd addon_portal
python -c "from api.core.settings import settings; print(settings.APP_NAME)"
```

Expected: No errors, prints "Q2O"

### **4. CLI Works**
```bash
python -m scripts.admin_cli --help
```

Expected: Help text displays

### **5. Secrets Validated (Production)**
```bash
ENV=production python -c "from api.core.settings import settings"
```

Expected: ValueError if secrets not configured (good!)

### **6. Frontend Environment**
```bash
cd apps/tenant-portal
cat .env.local | grep NEXT_PUBLIC_LIC_API
```

Expected: Shows configured API URL

---

## 📊 SUMMARY

### **Files Created**: 5

| File | Purpose |
|------|---------|
| `requirements.txt` | Python dependencies |
| `.env.example` | Backend environment template |
| `apps/tenant-portal/.env.local.example` | Frontend environment template |
| `generate_secrets.py` | Secret generation tool |
| `create_tables.py` (optional) | Direct table creation |

### **Files Modified**: 2

| File | Changes |
|------|---------|
| `api/core/settings.py` | Added secret validation |
| `api/core/db.py` | Updated to SQLAlchemy 2.0 style |

### **Alembic Setup**: 1

- Initialized migrations
- Generated initial migration
- Ran migration

### **Total Time**: 2-3 hours

---

## 🚀 NEXT STEPS

1. ✅ **Important fixes complete** - Production-ready environment
2. ⏭️ **Review minor fixes** in `MINOR_FIXES_GUIDE.md` (optional)
3. ⏭️ **Set up first tenant** using `ADDON_SETUP_GUIDE.md`
4. ⏭️ **Integrate with Quick2Odoo** using `ADDON_INTEGRATION_GUIDE.md`

---

**Document Version**: 1.0  
**Last Updated**: November 6, 2025  
**Applies To**: Q2O Licensing Addon v0.1.0
