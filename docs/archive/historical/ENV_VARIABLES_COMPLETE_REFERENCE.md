# Complete Environment Variables Reference

## Single Source of Truth

**ALL environment variables for the entire Q2O project are stored in ONE file:**
```
C:\Q2O_Combined\.env
```

**This is the ONLY `.env` file used by the entire Q2O system.**

## All Variables Defined in Root `.env`

The following is a complete list of ALL environment variables that should be in your root `.env` file (`C:\Q2O_Combined\.env`):

### Database Configuration
```env
DB_DSN=postgresql+psycopg://q2o_user:YOUR_PASSWORD_HERE@localhost:5432/q2o
```

### Application Settings
```env
APP_NAME=Q2O
ENV=production  # or 'dev' for development
```

### JWT Authentication
```env
JWT_ISSUER=q2o-auth
JWT_AUDIENCE=q2o-clients
JWT_PRIVATE_KEY=CHANGE_ME_RSA_PRIV_PEM
JWT_PUBLIC_KEY=CHANGE_ME_RSA_PUB_PEM
JWT_ACCESS_TTL_SECONDS=900
JWT_REFRESH_TTL_SECONDS=1209600
```

### Stripe Billing
```env
STRIPE_SECRET_KEY=sk_test_REPLACE_WITH_YOUR_ACTUAL_STRIPE_KEY_HERE
STRIPE_WEBHOOK_SECRET=whsec_REPLACE_WITH_YOUR_ACTUAL_WEBHOOK_SECRET_HERE
```

### Activation Codes
```env
ACTIVATION_CODE_PEPPER=CHANGE_ME_TO_RANDOM_64_CHAR_HEX_STRING
```

### CORS Configuration
```env
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001,http://localhost:3002,http://127.0.0.1:3000,http://127.0.0.1:3001,http://127.0.0.1:3002
```

### Branding CDN (Optional)
```env
BRANDING_CDN_BASE=
```

### Session Management
```env
SESSION_SECRET=CHANGE_ME_TO_RANDOM_64_CHAR_HEX_STRING
```

### OIDC/SSO Authentication (Optional)
```env
OIDC_ISSUER=
OIDC_CLIENT_ID=
OIDC_CLIENT_SECRET=
OIDC_REDIRECT_URL=http://localhost:8080/auth/callback
```

### Logging Configuration
```env
LOG_ENABLED=True
LOG_LEVEL=INFO
```

### Timezone Configuration
```env
TIME_ZONE=UTC
```

### LLM System Prompt (Managed by LLM Management Service)
```env
LLM_SYSTEM_PROMPT=
```

### SMTP Configuration (for OTP Email Delivery)
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

### SMS Configuration (for SMS/WhatsApp OTP Delivery - Placeholder)
```env
SMS_ENABLED=False
SMS_PROVIDER=
SMS_API_KEY=
SMS_API_SECRET=
SMS_FROM_NUMBER=
```

## How Variables Are Loaded

### Backend API (`addon_portal/api/core/settings.py`)
- **Uses absolute path** to root `.env`: `C:\Q2O_Combined\.env`
- **Works regardless of working directory** - no need to run from root
- All variables defined in `Settings` class are loaded from root `.env`

### LLM Config Service (`addon_portal/api/services/llm_config_service.py`)
- **Uses absolute path** to root `.env`: `C:\Q2O_Combined\.env`
- Reads/writes `LLM_SYSTEM_PROMPT` to root `.env`

### Frontend Applications (Admin Portal, Tenant Portal)
- Use `process.env.NEXT_PUBLIC_*` variables (if needed)
- Backend API configuration comes from root `.env`
- No separate `.env.local` or `.env` files needed in frontend apps

## Setup Instructions

1. **Copy the example file to root:**
   ```bash
   # Windows (from project root: C:\Q2O_Combined)
   copy addon_portal\env.example.txt .env
   ```

2. **Edit `.env` in the ROOT directory** and update all `CHANGE_ME` values

3. **Never commit `.env` to git** - It contains secrets!

## Verification

To verify all variables are in the root `.env`:

1. Check that `C:\Q2O_Combined\.env` exists
2. Verify it contains all variables listed above
3. Backend API will automatically load from this file (absolute path)
4. No other `.env` files should exist in subdirectories

## Important Notes

- ✅ **Single Source**: All variables in `C:\Q2O_Combined\.env`
- ✅ **Absolute Path**: Backend uses absolute path, works from any directory
- ✅ **No Duplicates**: No `.env` files in `addon_portal/` or subdirectories
- ✅ **No Frontend .env**: Frontend apps don't need separate `.env` files
- ✅ **Consolidated**: All Q2O system variables in one place

## Migration from Multiple .env Files

If you previously had `.env` files in multiple locations:

1. **Collect all variables** from:
   - `addon_portal/.env` (if it existed)
   - `addon_portal/apps/tenant-portal/.env.local` (if it existed)
   - Any other `.env` files

2. **Merge into root `.env`**: `C:\Q2O_Combined\.env`

3. **Delete old `.env` files** from subdirectories

4. **Verify**: Restart backend API and test all functionality

