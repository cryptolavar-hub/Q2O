# Environment Configuration File Location

## Single Source of Truth

**The `.env` file for the entire Q2O project is located at the ROOT of the project:**
```
C:\Q2O_Combined\.env
```

**This is the ONLY .env file used by the entire Q2O system.**

## Why Only One .env File?

- **Simplified Administration**: One file to manage, one location to secure
- **Consistency**: All components (Admin Portal, Tenant Portal, Backend API) read from the same source
- **Security**: Easier to protect and audit a single file
- **Deployment**: Single file to configure in production

## Setup Instructions

1. **Copy the example file to the ROOT:**
   ```bash
   # Windows (from project root: C:\Q2O_Combined)
   copy addon_portal\env.example.txt .env
   
   # Linux/Mac (from project root)
   cp addon_portal/env.example.txt .env
   ```

2. **Edit `.env` in the ROOT directory (`C:\Q2O_Combined\.env`) and update:**
   - `DB_DSN` - Your PostgreSQL connection string
   - `SMTP_*` settings - For OTP email delivery
   - `JWT_*` keys - For authentication
   - `STRIPE_*` keys - For billing (if enabled)
   - Other settings as needed

3. **Never commit `.env` to git** - It contains secrets!

## SMTP Configuration for OTP Delivery

To enable OTP email delivery when creating tenants, configure in `.env`:

```env
SMTP_ENABLED=True
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
SMTP_FROM_EMAIL=noreply@q2o.com
SMTP_FROM_NAME=Q2O Platform
SMTP_USE_TLS=True
```

## Important Notes

- **Location**: `.env` must be in the project root: `C:\Q2O_Combined\.env`
- **Backend API**: Uses **absolute path** to root `.env` - works from any directory
- **Settings Source**: Defined in `addon_portal/api/core/settings.py` (uses `Path(__file__).resolve().parents[3] / '.env'`)
- **Example File**: Reference template is at `addon_portal/env.example.txt`
- **No Working Directory Requirement**: Backend API can be run from any directory - it uses absolute path

## Running the Backend API

**Can be run from any directory** - the backend uses an absolute path to find the root `.env`:

```bash
# Windows (from any directory)
python -m uvicorn addon_portal.api.main:app --host 127.0.0.1 --port 8080

# Or use the provided batch scripts
```

## Complete Variable Reference

See `ENV_VARIABLES_COMPLETE_REFERENCE.md` for a complete list of ALL environment variables that should be in the root `.env` file.

