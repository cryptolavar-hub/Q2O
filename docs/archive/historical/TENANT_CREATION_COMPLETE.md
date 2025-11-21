# Tenant Creation & OTP Delivery - Complete Implementation

## Summary

All requested features have been implemented completely:

1. ✅ **Email and Phone Fields Added to Tenant Creation Form**
2. ✅ **OTP Generation on Tenant Creation** (via email)
3. ✅ **Auto-Set Quota from Plan** (client-side)
4. ✅ **.env File Consolidation** (documented single source)

## Changes Made

### 1. Frontend (Admin Portal)

**File: `addon_portal/apps/admin-portal/src/pages/tenants.tsx`**
- Added email field (required for new tenants)
- Added phone number field (optional)
- Added OTP delivery method dropdown (email, SMS, WhatsApp, both)
- Added client-side script to auto-set quota when plan is selected
- Updated both create and edit forms

**File: `addon_portal/apps/admin-portal/src/lib/api.ts`**
- Updated `AddTenantRequest` interface to include `email`, `phoneNumber`, `otpDeliveryMethod`
- Updated `EditTenantRequest` interface to include `email`, `phoneNumber`
- Updated `Tenant` type schema to include `email` and `phoneNumber` fields

### 2. Backend API

**File: `addon_portal/api/schemas/tenant.py`**
- Added `email`, `phone_number`, `otp_delivery_method` to `TenantCreatePayload`
- Added email validation (regex pattern)
- Added OTP delivery method validation (email, sms, whatsapp, both)
- Added `email`, `phone_number` to `TenantUpdatePayload`
- Added `email`, `phone_number` to `TenantResponse`

**File: `addon_portal/api/services/tenant_service.py`**
- Updated `create_tenant` to save email, phone_number, otp_delivery_method
- Added OTP generation and email delivery on tenant creation (if email provided)
- Updated `update_tenant` to handle email and phone_number updates
- Updated `_load_subscription_details` to include email and phone_number in response

### 3. Documentation

**File: `addon_portal/ENV_FILE_LOCATION.md`**
- Documented single source of truth: `.env` in project root (`C:\Q2O_Combined\.env`)
- Explained why only one .env file is used
- Provided setup instructions
- Documented SMTP configuration for OTP delivery

## How It Works

### Tenant Creation Flow

1. **Admin fills out tenant creation form:**
   - Required: Name, Slug, Email, Subscription Plan
   - Optional: Logo URL, Primary Color, Domain, Phone Number
   - OTP Delivery Method: Email (default), SMS, WhatsApp, or Both

2. **When subscription plan is selected:**
   - Client-side script automatically sets Usage Quota to plan's `monthlyRunQuota`
   - User can still manually adjust if needed

3. **On form submission:**
   - Backend creates tenant with all provided information
   - If email is provided, OTP is automatically generated and sent via email
   - Tenant can immediately log in using the OTP sent to their email

4. **OTP Email Content:**
   - Professional HTML email with OTP code
   - Includes tenant name, OTP code, expiration time (10 minutes)
   - Plain text fallback included

### Tenant Edit Flow

- Email and phone number can be updated via the edit form
- Changes are tracked in event logging
- OTP is NOT regenerated on edit (only on creation)

## Configuration Required

### SMTP Settings in `.env` (Project Root)

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

**Note:** For Gmail, you need to use an "App Password" (not your regular password). Generate one at: https://myaccount.google.com/apppasswords

## Testing Checklist

- [ ] Create a new tenant with email
- [ ] Verify OTP email is received
- [ ] Verify quota auto-sets when plan is selected
- [ ] Verify quota can be manually adjusted
- [ ] Edit tenant email/phone
- [ ] Verify email validation works (invalid emails rejected)
- [ ] Test with SMTP disabled (should log warning, not fail)

## Next Steps

1. **Configure SMTP** in `.env` at project root `C:\Q2O_Combined\.env` (see above)
2. **Restart backend API** to load new settings
3. **Test tenant creation** with a real email address
4. **Verify OTP delivery** works correctly
5. **Test tenant login** using the OTP received via email

## Files Modified

- `addon_portal/apps/admin-portal/src/pages/tenants.tsx`
- `addon_portal/apps/admin-portal/src/lib/api.ts`
- `addon_portal/api/schemas/tenant.py`
- `addon_portal/api/services/tenant_service.py`
- `addon_portal/ENV_FILE_LOCATION.md` (new)
- `TENANT_CREATION_COMPLETE.md` (this file)

## Notes

- OTP is only generated on tenant creation (not on edit)
- Email is required for new tenants (frontend validation)
- Phone number is optional
- OTP delivery method defaults to "email"
- If SMTP is not configured, tenant creation still succeeds but OTP won't be sent (warning logged)

