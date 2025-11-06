# ⚡ Quick Reference - Q2O Licensing Addon Fixes

**Purpose**: Quick copy-paste reference for all fixes  
**Use**: When you know what to fix and just need the code

---

## 🔴 CRITICAL FIX #1: Pydantic v2 (10 min)

**File**: `addon_portal/api/core/settings.py`

### **Line 1 - Change Import**
```python
# OLD:
from pydantic import BaseSettings, AnyHttpUrl

# NEW:
from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl
```

### **Lines 39-40 - Change Config**
```python
# OLD:
    class Config:
        env_file = ".env"

# NEW:
    model_config = {"env_file": ".env"}
```

### **Install Dependency**
```bash
pip install pydantic-settings>=2.1.0
```

---

## 🔴 CRITICAL FIX #2: UsageMeter Color (2 min)

**File**: `addon_portal/apps/tenant-portal/src/components/UsageMeter.tsx`

### **Line 10 - Add Background**
```tsx
// OLD:
<div style={{ width:`${pct}%`, height:8, borderRadius:999 }} />

// NEW:
<div style={{ 
  width:`${pct}%`, 
  height:8, 
  borderRadius:999,
  background: pct >= 90 ? '#ef4444' : pct >= 75 ? '#f59e0b' : '#3b82f6'
}} />
```

---

## 🔴 CRITICAL FIX #3: Type Hints (5 min)

**File**: `addon_portal/api/routers/admin_pages.py`

### **Add Import at Top**
```python
from typing import Optional
```

### **Line 31 - Fix Type Hints**
```python
# OLD:
async def gen_codes_action(request: Request, user = Depends(require_admin),
    tenant_slug: str = Form(...), count: int = Form(1), 
    ttl_days: int | None = Form(None), 
    label: str | None = Form(None),
    max_uses: int = Form(1), db: Session = Depends(get_db)):

# NEW:
async def gen_codes_action(request: Request, user = Depends(require_admin),
    tenant_slug: str = Form(...), count: int = Form(1), 
    ttl_days: Optional[int] = Form(None), 
    label: Optional[str] = Form(None),
    max_uses: int = Form(1), db: Session = Depends(get_db)):
```

---

## ⚠️ IMPORTANT: Create requirements.txt

**File**: `addon_portal/requirements.txt`

```txt
fastapi>=0.110.0,<0.111.0
uvicorn[standard]>=0.27.0,<0.28.0
sqlalchemy>=2.0.25,<2.1.0
psycopg2-binary>=2.9.9,<3.0.0
alembic>=1.13.0,<1.14.0
pydantic>=2.6.0,<3.0.0
pydantic-settings>=2.1.0,<3.0.0
stripe>=7.0.0,<8.0.0
pyjwt>=2.8.0,<3.0.0
Authlib>=1.3.0,<2.0.0
Jinja2>=3.1.3,<4.0.0
python-multipart>=0.0.6,<0.1.0
cryptography>=41.0.0,<42.0.0
```

---

## ⚠️ IMPORTANT: Create .env.example

**File**: `addon_portal/.env.example`

```bash
APP_NAME=Q2O
ENV=production
DB_DSN=postgresql+psycopg://q2o_user:CHANGE_PASSWORD@localhost:5432/q2o_licensing

JWT_ISSUER=q2o-auth
JWT_AUDIENCE=q2o-clients
JWT_ACCESS_TTL_SECONDS=900
JWT_REFRESH_TTL_SECONDS=1209600
JWT_PRIVATE_KEY="-----BEGIN RSA PRIVATE KEY-----\nCHANGE_ME\n-----END RSA PRIVATE KEY-----"
JWT_PUBLIC_KEY="-----BEGIN PUBLIC KEY-----\nCHANGE_ME\n-----END PUBLIC KEY-----"

STRIPE_SECRET_KEY=sk_test_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx

ACTIVATION_CODE_PEPPER=CHANGE_ME_32_CHAR_STRING
SESSION_SECRET=CHANGE_ME_32_CHAR_STRING

OIDC_ISSUER=
OIDC_CLIENT_ID=
OIDC_CLIENT_SECRET=
OIDC_REDIRECT_URL=

ALLOWED_ORIGINS=["http://localhost:3000","http://localhost:8080"]
BRANDING_CDN_BASE=
```

---

## ⚠️ IMPORTANT: Create Frontend .env

**File**: `addon_portal/apps/tenant-portal/.env.local.example`

```bash
NEXT_PUBLIC_LIC_API=http://localhost:8080
```

---

## ⚠️ IMPORTANT: Generate Secrets

**File**: `addon_portal/generate_secrets.py`

```python
#!/usr/bin/env python3
import secrets
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

def generate_pepper():
    return secrets.token_urlsafe(32)

def generate_rsa_keypair():
    private_key = rsa.generate_private_key(
        public_exponent=65537, key_size=2048, backend=default_backend()
    )
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption()
    ).decode('utf-8')
    public_key = private_key.public_key()
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode('utf-8')
    return private_pem, public_pem

if __name__ == "__main__":
    print("🔐 Generating secrets...\n")
    pepper = generate_pepper()
    session_secret = generate_pepper()
    private_key, public_key = generate_rsa_keypair()
    
    print(f"ACTIVATION_CODE_PEPPER={pepper}")
    print(f"SESSION_SECRET={session_secret}\n")
    print('JWT_PRIVATE_KEY="' + private_key.replace('\n', '\\n') + '"\n')
    print('JWT_PUBLIC_KEY="' + public_key.replace('\n', '\\n') + '"')
    print("\n✅ Done! Copy to .env file")
```

**Run it**:
```bash
cd addon_portal
python generate_secrets.py > secrets.txt
nano .env  # Paste secrets
```

---

## ⚠️ IMPORTANT: Database Setup

### **Option A: Alembic (Recommended)**

```bash
cd addon_portal
alembic init migrations

# Edit migrations/env.py - add imports:
from api.core.db import Base
from api.core.settings import settings
from api.models.licensing import *

# Set URL:
config.set_main_option('sqlalchemy.url', settings.DB_DSN)
target_metadata = Base.metadata

# Generate migration:
alembic revision --autogenerate -m "Initial schema"
alembic upgrade head
```

### **Option B: Direct Creation**

**File**: `addon_portal/create_tables.py`

```python
from api.core.db import Base, engine
from api.models.licensing import *

if __name__ == "__main__":
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)
    print("✓ Done")
```

```bash
python create_tables.py
```

---

## 🚀 STARTUP COMMANDS

### **Backend**
```bash
cd addon_portal
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn api.main:app --host 0.0.0.0 --port 8080 --reload
```

### **Frontend**
```bash
cd addon_portal/apps/tenant-portal
cp .env.local.example .env.local
npm install
npm run dev
```

### **CLI**
```bash
cd addon_portal

# Seed plan:
python -m scripts.admin_cli seed-plan \
  --name "Pro" \
  --price-id "price_xxx" \
  --quota 1000

# Add tenant:
python -m scripts.admin_cli add-tenant \
  --name "Acme Corp" \
  --slug "acme" \
  --logo-url "https://acme.com/logo.png" \
  --color "#ff6600"

# Link subscription:
python -m scripts.admin_cli link-sub \
  --tenant "acme" \
  --customer "cus_xxx" \
  --sub "sub_xxx" \
  --state "active" \
  --plan "Pro"

# Generate codes:
python -m scripts.admin_cli gen-codes \
  --tenant "acme" \
  --count 10 \
  --ttl-days 30 \
  --label "batch-nov-2025"

# List codes:
python -m scripts.admin_cli list-codes --tenant "acme"
```

---

## ✅ VERIFICATION

### **Backend Running**
```bash
curl http://localhost:8080/docs
# Expected: OpenAPI docs load
```

### **Frontend Running**
```bash
curl http://localhost:3000
# Expected: HTML loads
```

### **Database Tables**
```bash
psql -U user -d q2o_licensing -c "\dt"
# Expected: 7 tables listed
```

### **Test Activation Flow**
```python
import requests

# 1. Get branding
r = requests.get("http://localhost:8080/licenses/branding/acme")
print(r.json())  # {'logo_url': '...', 'primary_color': '...', 'domain': '...'}

# 2. Activate device
r = requests.post("http://localhost:8080/authz/activate", json={
    "tenant_slug": "acme",
    "activation_code": "XXXX-XXXX-XXXX-XXXX",
    "hw_fingerprint": "my-device-123"
})
tokens = r.json()
print(tokens['access_token'])

# 3. Get policy
headers = {"Authorization": f"Bearer {tokens['access_token']}"}
r = requests.get("http://localhost:8080/licenses/policy", headers=headers)
print(r.json())  # {'plan_name': 'Pro', 'monthly_run_quota': 1000, ...}
```

---

## 🆘 QUICK TROUBLESHOOTING

| Error | Fix |
|-------|-----|
| `ImportError: BaseSettings` | Install pydantic-settings |
| `relation "tenants" does not exist` | Run database migrations |
| `Invalid token format` | Check JWT keys are configured |
| `OIDC not configured` | Leave OIDC vars empty or set them |
| Progress bar invisible | Add background color to UsageMeter |
| CLI import error | Run as `python -m scripts.admin_cli` |

---

## 📊 CHECKLIST

### **Critical Fixes** (30 min)
- [ ] Fix Pydantic import
- [ ] Add UsageMeter background
- [ ] Fix type hints
- [ ] Create .env file
- [ ] Test app starts

### **Important Setup** (2 hours)
- [ ] Create requirements.txt
- [ ] Create .env.example
- [ ] Generate secrets
- [ ] Setup database
- [ ] Run migrations
- [ ] Seed initial data

### **Deployment** (1 hour)
- [ ] Start backend
- [ ] Start frontend
- [ ] Create first tenant
- [ ] Generate activation codes
- [ ] Test activation flow

---

**Document Version**: 1.0  
**Last Updated**: November 6, 2025  
**For**: Quick copy-paste reference

