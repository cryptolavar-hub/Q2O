# Q2O Licensing & Portal Addons (Bundle)

## Contents
- FastAPI licensing service routes, models, and admin UI (SSO-protected)
- Admin CLI for plans/tenants/activation-codes
- Next.js tenant portal scaffold with branding + usage + code generation

## Quick start
1. Install FastAPI deps:
   ```bash
   pip install fastapi uvicorn sqlalchemy psycopg alembic "pydantic>=2.7.1,<3" "stripe>=7,<10" pyjwt Authlib Jinja2 python-multipart cryptography
   ```
2. Configure `.env` (see `api/core/settings.py` for keys).
3. Run app:
   ```bash
   uvicorn api.main:app --host 0.0.0.0 --port 8080
   ```
4. Portal:
   ```bash
   cd apps/tenant-portal && npm i && npm run dev
   ```
   
   **Note:** All environment variables are configured in the root `.env` file (`C:\Q2O_Combined\.env`). 
   The tenant portal reads API configuration from the backend, which loads from the root `.env`.
