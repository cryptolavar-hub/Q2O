# Next Steps: Profile & Billing Pages Implementation

**Date**: November 20, 2025  
**Status**: Ready to Start  
**Priority**: High (Week 4-5 of Completion Plan)

---

## 📊 Current Status

### ✅ Completed
- OTP Authentication
- Project Management (CRUD, search, filter)
- Status Page (Tenant View with GraphQL)
- Task Tracking System
- Activation Code Assignment

### ❌ Not Yet Implemented
- **Tenant Profile Page** (`/profile`)
- **Tenant Billing Page** (`/billing`)
- Profile/Billing API endpoints
- Stripe integration for plan upgrades and code purchases

---

## 🎯 Next Steps (In Order)

### **Step 1: Backend API - Profile Endpoints** (Priority: HIGH)

**Location**: `addon_portal/api/routers/tenant_api.py`

**Endpoints to Create**:

1. **GET `/api/tenant/profile`**
   - Returns complete tenant profile with subscription and quota info
   - Response includes:
     - Tenant info (name, slug, email, phone, logo, color, domain)
     - Subscription details (plan, status, quota, usage, billing dates)
     - Activation code quota (monthly quota, used, remaining)

2. **PUT `/api/tenant/profile`**
   - Updates tenant profile fields
   - Validates email, domain, color format
   - Returns updated profile

**Files to Update**:
- `addon_portal/api/routers/tenant_api.py` - Add endpoints
- `addon_portal/api/schemas/tenant.py` - Add `TenantProfileResponse`, `TenantProfileUpdatePayload`
- `addon_portal/api/services/tenant_service.py` - Add `get_tenant_profile()`, `update_tenant_profile()`

**Estimated Time**: 4-6 hours

---

### **Step 2: Backend API - Billing Endpoints** (Priority: HIGH)

**Location**: `addon_portal/api/routers/tenant_api.py`

**Endpoints to Create**:

1. **GET `/api/tenant/billing`**
   - Returns billing information (subscription, usage, payment method, available plans)

2. **GET `/api/tenant/billing/invoices`**
   - Returns billing history with pagination

3. **POST `/api/tenant/billing/upgrade`**
   - Upgrades/downgrades subscription plan
   - Creates Stripe checkout session

4. **POST `/api/tenant/billing/renew`**
   - Renews current subscription

5. **PUT `/api/tenant/billing/auto-renewal`**
   - Toggles auto-renewal

6. **POST `/api/tenant/billing/cancel`**
   - Cancels subscription

7. **POST `/api/tenant/activation-codes/purchase`**
   - Purchases additional activation codes
   - Processes payment via Stripe

8. **GET `/api/tenant/activation-codes/purchase-options`**
   - Returns purchase options and pricing

**Files to Update**:
- `addon_portal/api/routers/tenant_api.py` - Add billing endpoints
- `addon_portal/api/schemas/tenant.py` - Add billing schemas
- `addon_portal/api/services/billing_service.py` - **NEW** - Billing operations
- `addon_portal/api/services/activation_code_service.py` - Add purchase functionality

**Estimated Time**: 8-12 hours

---

### **Step 3: Frontend - Profile Page** (Priority: HIGH)

**Location**: `addon_portal/apps/tenant-portal/src/pages/profile/index.tsx`

**Components to Create**:
- `ProfileInfoCard.tsx` - Displays tenant information
- `SubscriptionCard.tsx` - Displays subscription details
- `QuotaCard.tsx` - Displays quota usage with visual meters
- `BrandingPreviewCard.tsx` - Shows branding preview
- `EditProfileModal.tsx` - Modal for editing profile

**Features**:
- Fetch profile data on page load
- Display all information in cards
- Edit button opens modal
- Form validation (email, domain, color)
- File upload for logo (or URL input)
- Color picker for primary color
- Save changes with loading state
- Success/error notifications

**Files to Create**:
```
addon_portal/apps/tenant-portal/src/
├── pages/
│   └── profile/
│       └── index.tsx
├── components/
│   ├── ProfileInfoCard.tsx
│   ├── SubscriptionCard.tsx
│   ├── QuotaCard.tsx
│   ├── BrandingPreviewCard.tsx
│   └── EditProfileModal.tsx
└── lib/
    └── profile.ts (API client)
```

**Estimated Time**: 8-10 hours

---

### **Step 4: Frontend - Billing Page** (Priority: HIGH)

**Location**: `addon_portal/apps/tenant-portal/src/pages/billing/index.tsx`

**Components to Create**:
- `CurrentSubscriptionCard.tsx` - Current plan display
- `BillingHistoryTable.tsx` - Invoice history
- `UsageQuotaCard.tsx` - Usage and quota meters
- `PlanComparisonCard.tsx` - Plan upgrade options
- `ActivationCodePurchaseCard.tsx` - Code purchase interface
- `PaymentMethodCard.tsx` - Payment method management
- `UpgradeModal.tsx` - Plan upgrade modal
- `PurchaseCodesModal.tsx` - Code purchase modal

**Features**:
- Fetch billing data on page load
- Display current subscription
- Show billing history with pagination
- Display usage quotas with visual meters
- Show plan comparison
- Upgrade/downgrade functionality
- Purchase activation codes (if quota exhausted)
- Update payment method
- Toggle auto-renewal
- Cancel subscription (with confirmation)
- Stripe checkout integration

**Files to Create**:
```
addon_portal/apps/tenant-portal/src/
├── pages/
│   └── billing/
│       └── index.tsx
├── components/
│   ├── CurrentSubscriptionCard.tsx
│   ├── BillingHistoryTable.tsx
│   ├── UsageQuotaCard.tsx
│   ├── PlanComparisonCard.tsx
│   ├── ActivationCodePurchaseCard.tsx
│   ├── PaymentMethodCard.tsx
│   ├── UpgradeModal.tsx
│   └── PurchaseCodesModal.tsx
└── lib/
    └── billing.ts (API client)
```

**Estimated Time**: 12-16 hours

---

### **Step 5: Stripe Integration** (Priority: MEDIUM)

**Location**: `addon_portal/api/routers/billing_stripe.py` (or update existing)

**Features**:
- Stripe Checkout Session creation for plan upgrades
- Payment processing for activation code purchases
- Webhook handlers:
  - `subscription.updated` - Handle plan changes
  - `invoice.payment_succeeded` - Handle successful payments
  - `invoice.payment_failed` - Handle failed payments
  - `customer.subscription.deleted` - Handle cancellations

**Files to Update**:
- `addon_portal/api/routers/billing_stripe.py` - Add webhook handlers
- `addon_portal/api/services/billing_service.py` - Add Stripe integration

**Estimated Time**: 6-8 hours

---

### **Step 6: Update Navigation** (Priority: LOW)

**Location**: `addon_portal/apps/tenant-portal/src/components/Navigation.tsx`

**Action**: Uncomment Profile and Billing links

```typescript
const navItems: NavItem[] = [
  { href: '/projects', label: 'Projects', icon: '📁' },
  { href: '/status', label: 'Status', icon: '📊' },
  { href: '/profile', label: 'Profile', icon: '👤' },  // Uncomment
  { href: '/billing', label: 'Billing', icon: '💳' },  // Add
];
```

**Estimated Time**: 5 minutes

---

## 📋 Implementation Order (Recommended)

1. **Backend Profile API** (Step 1) - 4-6 hours
2. **Frontend Profile Page** (Step 3) - 8-10 hours
3. **Backend Billing API** (Step 2) - 8-12 hours
4. **Frontend Billing Page** (Step 4) - 12-16 hours
5. **Stripe Integration** (Step 5) - 6-8 hours
6. **Update Navigation** (Step 6) - 5 minutes

**Total Estimated Time**: 38-52 hours (5-7 days)

---

## 🔍 Key Dependencies

### Database Schema
- ✅ `tenants` table - Already has: `name`, `slug`, `email`, `phone_number`, `logo_url`, `primary_color`, `domain`
- ✅ `subscriptions` table - Already has: `plan_id`, `status`, `stripe_subscription_id`, `stripe_customer_id`
- ✅ `activation_codes` table - Already has: `tenant_id`, `code_hash`, `max_uses`, `used_count`
- ❓ `billing_invoices` table - **May need to create** (check if exists)
- ❓ `activation_code_purchases` table - **May need to create** (check if exists)

### Environment Variables
- `STRIPE_SECRET_KEY` - Stripe API key
- `STRIPE_WEBHOOK_SECRET` - Stripe webhook secret
- `STRIPE_PUBLISHABLE_KEY` - For frontend (if needed)

---

## 📚 Reference Documents

- **Detailed Roadmap**: `docs/TENANT_PROFILE_BILLING_ROADMAP.md`
- **Completion Plan**: `docs/COMPLETE_SOLUTION_COMPLETION_PLAN_REVISED.md`
- **Project Execution**: `docs/PROJECT_EXECUTION_WORKFLOW_PLAN.md`

---

## ✅ Success Criteria

### Profile Page
- [ ] All tenant information displays correctly
- [ ] Subscription details accurate
- [ ] Quota meters functional
- [ ] Edit functionality works
- [ ] Branding preview works
- [ ] Responsive design
- [ ] No console errors

### Billing Page
- [ ] Current subscription displays correctly
- [ ] Billing history loads
- [ ] Plan upgrade works
- [ ] Activation code purchase works
- [ ] Payment method update works
- [ ] Auto-renewal toggle works
- [ ] Cancel subscription works
- [ ] Stripe integration works
- [ ] Responsive design
- [ ] No console errors

---

**Ready to start? Begin with Step 1: Backend Profile API endpoints.**

