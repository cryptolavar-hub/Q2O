# Tenant Profile & Billing Pages - Implementation Roadmap

**Date**: November 19, 2025  
**Status**: Planning Phase  
**Priority**: High (Week 4-5 of Completion Plan)  
**Dependencies**: OTP Authentication ✅, Project Management ✅, Subscription System ✅

---

## 🎯 Overview

This roadmap details the implementation of two critical Tenant Portal pages:

1. **Tenant Profile Page** (`/profile`) - Branding, plan details, quota management
2. **Tenant Billing Page** (`/billing`) - Subscription renewal, plan upgrades, activation code purchases

These pages enable tenants to:
- Manage their profile and branding
- View subscription details and usage quotas
- Renew subscriptions and upgrade plans
- Purchase additional activation codes when quota is exhausted
- Track billing history

---

## 📋 Feature Requirements

### **1. Tenant Profile Page (`/profile`)**

#### **Display Requirements**
- **Tenant Information**:
  - Tenant name (editable)
  - Slug (read-only, permanent identifier)
  - Email address (editable)
  - Phone number (editable)
  - Logo URL (editable, for branding)
  - Primary color (editable, for branding)
  - Custom domain (editable, if applicable)

- **Subscription Details**:
  - Current subscription plan name (e.g., "Starter", "Pro", "Enterprise")
  - Plan status (active, trialing, past_due, canceled, unpaid, suspended)
  - Monthly run quota (e.g., 10, 50, unlimited)
  - Current month usage (projects run this month)
  - Usage percentage (visual progress bar)
  - Subscription start date
  - Next billing date
  - Auto-renewal status

- **Activation Code Quota**:
  - Total monthly quota (10% of monthly run quota)
  - Codes used this month
  - Codes remaining
  - Visual quota meter

- **Branding Preview**:
  - Preview of tenant logo
  - Preview of primary color applied to UI elements
  - Preview of custom domain (if set)

#### **Edit Functionality**
- Edit tenant name, email, phone number
- Upload/update logo (file upload or URL)
- Set primary color (color picker)
- Set custom domain (with validation)
- Save changes with validation
- Success/error notifications

#### **UI Components**
- Profile information card
- Subscription details card
- Quota usage card (with visual meters)
- Branding preview card
- Edit form (modal or inline)
- Save/Cancel buttons

---

### **2. Tenant Billing Page (`/billing`)**

#### **Display Requirements**
- **Current Subscription**:
  - Plan name and tier
  - Monthly/annual pricing
  - Plan features comparison
  - Current status badge
  - Next billing date
  - Auto-renewal toggle

- **Billing History**:
  - Table of past invoices
  - Invoice date, amount, status
  - Download invoice PDF
  - Payment method (last 4 digits)
  - Filter by date range

- **Usage & Quota**:
  - Current month project runs
  - Activation codes used/remaining
  - Visual quota meters
  - Warning when approaching limits

- **Plan Upgrade Options**:
  - Side-by-side plan comparison
  - Feature differences highlighted
  - Upgrade button for each plan
  - Pricing information

- **Activation Code Purchase**:
  - Current quota status
  - "Buy More Codes" button (if quota exhausted)
  - Purchase options:
    - Single code purchase
    - Bulk code purchase (5, 10, 20, 50)
    - Pricing per code
  - Stripe payment integration
  - Purchase confirmation

#### **Functionality**
- **Subscription Renewal**:
  - Renew current subscription
  - Update payment method
  - Enable/disable auto-renewal
  - Cancel subscription (with confirmation)

- **Plan Upgrade/Downgrade**:
  - Upgrade to higher tier
  - Downgrade to lower tier (with warnings)
  - Immediate plan change or at next billing cycle
  - Stripe checkout integration

- **Activation Code Purchase**:
  - Check quota status
  - Select quantity
  - Calculate total price
  - Process payment via Stripe
  - Generate codes after successful payment
  - Update quota immediately

- **Payment Management**:
  - Update credit card
  - View payment methods
  - Set default payment method
  - Remove payment methods

---

## 🏗️ Implementation Plan

### **Phase 1: Backend API Endpoints (Week 4, Days 1-2)**

#### **1.1 Profile Endpoints**

**GET `/api/tenant/profile`**
- Returns complete tenant profile with subscription and quota info
- Response includes:
  ```json
  {
    "tenant": {
      "id": "uuid",
      "name": "Tenant Name",
      "slug": "tenant-slug",
      "email": "tenant@example.com",
      "phone_number": "+1234567890",
      "logo_url": "https://...",
      "primary_color": "#3B82F6",
      "domain": "tenant.example.com"
    },
    "subscription": {
      "plan_name": "Pro",
      "status": "active",
      "monthly_run_quota": 50,
      "current_month_usage": 12,
      "usage_percentage": 24,
      "start_date": "2025-01-01",
      "next_billing_date": "2025-02-01",
      "auto_renewal": true
    },
    "activation_code_quota": {
      "monthly_quota": 5,
      "codes_used_this_month": 2,
      "codes_remaining": 3,
      "quota_percentage": 40
    }
  }
  ```

**PUT `/api/tenant/profile`**
- Updates tenant profile fields
- Request body:
  ```json
  {
    "name": "Updated Name",
    "email": "newemail@example.com",
    "phone_number": "+1234567890",
    "logo_url": "https://...",
    "primary_color": "#3B82F6",
    "domain": "newdomain.example.com"
  }
  ```
- Validates email format
- Validates domain format (if provided)
- Validates color hex format
- Returns updated profile

**Files to Create/Update**:
- `addon_portal/api/routers/tenant_api.py` - Add endpoints
- `addon_portal/api/schemas/tenant.py` - Add `TenantProfileResponse`, `TenantProfileUpdatePayload`
- `addon_portal/api/services/tenant_service.py` - Add `get_tenant_profile`, `update_tenant_profile`

---

#### **1.2 Billing Endpoints**

**GET `/api/tenant/billing`**
- Returns billing information
- Response includes:
  ```json
  {
    "subscription": {
      "plan_name": "Pro",
      "plan_tier": "pro",
      "monthly_price": 99.00,
      "status": "active",
      "next_billing_date": "2025-02-01",
      "auto_renewal": true,
      "stripe_subscription_id": "sub_xxx",
      "stripe_customer_id": "cus_xxx"
    },
    "current_usage": {
      "project_runs_this_month": 12,
      "monthly_quota": 50,
      "activation_codes_used": 2,
      "activation_codes_remaining": 3,
      "activation_codes_monthly_quota": 5
    },
    "payment_method": {
      "type": "card",
      "last4": "4242",
      "brand": "visa",
      "exp_month": 12,
      "exp_year": 2025
    },
    "available_plans": [
      {
        "tier": "starter",
        "name": "Starter",
        "monthly_price": 29.00,
        "monthly_run_quota": 10,
        "features": ["10 projects/month", "Basic support"]
      },
      {
        "tier": "pro",
        "name": "Pro",
        "monthly_price": 99.00,
        "monthly_run_quota": 50,
        "features": ["50 projects/month", "Priority support", "Custom branding"]
      },
      {
        "tier": "enterprise",
        "name": "Enterprise",
        "monthly_price": 299.00,
        "monthly_run_quota": -1,
        "features": ["Unlimited projects", "Dedicated support", "Custom domain", "SLA"]
      }
    ]
  }
  ```

**GET `/api/tenant/billing/invoices`**
- Returns billing history
- Query parameters: `page`, `page_size`, `start_date`, `end_date`
- Response:
  ```json
  {
    "invoices": [
      {
        "id": "inv_xxx",
        "date": "2025-01-01",
        "amount": 99.00,
        "currency": "usd",
        "status": "paid",
        "description": "Pro Plan - January 2025",
        "pdf_url": "https://..."
      }
    ],
    "total": 10,
    "page": 1,
    "page_size": 20,
    "total_pages": 1
  }
  ```

**POST `/api/tenant/billing/upgrade`**
- Upgrades/downgrades subscription plan
- Request body:
  ```json
  {
    "plan_tier": "enterprise",
    "immediate": false
  }
  ```
- Creates Stripe checkout session
- Returns checkout URL
- Webhook handles subscription update

**POST `/api/tenant/billing/renew`**
- Renews current subscription
- Updates payment method if needed
- Returns confirmation

**PUT `/api/tenant/billing/auto-renewal`**
- Toggles auto-renewal
- Request body:
  ```json
  {
    "enabled": true
  }
  ```

**POST `/api/tenant/billing/cancel`**
- Cancels subscription
- Request body:
  ```json
  {
    "reason": "Too expensive",
    "cancel_immediately": false
    }
  ```
- Cancels at end of billing period (default) or immediately
- Returns confirmation

**POST `/api/tenant/activation-codes/purchase`**
- Purchases additional activation codes
- Request body:
  ```json
  {
    "quantity": 10,
    "payment_method_id": "pm_xxx"
  }
  ```
- Validates quota (can't purchase if not exhausted)
- Calculates price (e.g., $5 per code)
- Processes payment via Stripe
- Generates codes after successful payment
- Updates quota
- Returns generated codes

**GET `/api/tenant/activation-codes/purchase-options`**
- Returns purchase options and pricing
- Response:
  ```json
  {
    "pricing": {
      "single_code": 5.00,
      "bulk_discounts": {
        "5": 4.50,
        "10": 4.00,
        "20": 3.50,
        "50": 3.00
      }
    },
    "current_quota_status": {
      "monthly_quota": 5,
      "codes_used": 5,
      "codes_remaining": 0,
      "can_purchase": true
    }
  }
  ```

**Files to Create/Update**:
- `addon_portal/api/routers/tenant_api.py` - Add billing endpoints
- `addon_portal/api/schemas/tenant.py` - Add billing schemas
- `addon_portal/api/services/billing_service.py` - New service for billing operations
- `addon_portal/api/services/activation_code_service.py` - Add purchase functionality

---

### **Phase 2: Frontend Profile Page (Week 4, Days 3-4)**

#### **2.1 Profile Page Implementation**

**File**: `addon_portal/apps/tenant-portal/src/pages/profile/index.tsx`

**Components**:
- `ProfileInfoCard` - Displays tenant information
- `SubscriptionCard` - Displays subscription details
- `QuotaCard` - Displays quota usage with visual meters
- `BrandingPreviewCard` - Shows branding preview
- `EditProfileModal` - Modal for editing profile

**Features**:
- Fetch profile data on page load
- Display all information in cards
- Edit button opens modal
- Form validation (email, domain, color)
- File upload for logo (or URL input)
- Color picker for primary color
- Save changes with loading state
- Success/error notifications
- Refresh data after save

**API Integration**:
- `GET /api/tenant/profile` - Fetch profile
- `PUT /api/tenant/profile` - Update profile

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

---

### **Phase 3: Frontend Billing Page (Week 5, Days 1-3)**

#### **3.1 Billing Page Implementation**

**File**: `addon_portal/apps/tenant-portal/src/pages/billing/index.tsx`

**Components**:
- `CurrentSubscriptionCard` - Current plan display
- `BillingHistoryTable` - Invoice history
- `UsageQuotaCard` - Usage and quota meters
- `PlanComparisonCard` - Plan upgrade options
- `ActivationCodePurchaseCard` - Code purchase interface
- `PaymentMethodCard` - Payment method management
- `UpgradeModal` - Plan upgrade modal
- `PurchaseCodesModal` - Code purchase modal

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

**API Integration**:
- `GET /api/tenant/billing` - Fetch billing info
- `GET /api/tenant/billing/invoices` - Fetch invoices
- `POST /api/tenant/billing/upgrade` - Upgrade plan
- `POST /api/tenant/billing/renew` - Renew subscription
- `PUT /api/tenant/billing/auto-renewal` - Toggle auto-renewal
- `POST /api/tenant/billing/cancel` - Cancel subscription
- `GET /api/tenant/activation-codes/purchase-options` - Get purchase options
- `POST /api/tenant/activation-codes/purchase` - Purchase codes

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

---

### **Phase 4: Stripe Integration (Week 5, Days 4-5)**

#### **4.1 Stripe Checkout Integration**

**Plan Upgrade Flow**:
1. User clicks "Upgrade to Enterprise"
2. Frontend calls `POST /api/tenant/billing/upgrade`
3. Backend creates Stripe Checkout Session
4. Backend returns checkout URL
5. Frontend redirects to Stripe Checkout
6. User completes payment
7. Stripe webhook updates subscription
8. Frontend redirects back to billing page
9. Display success message

**Activation Code Purchase Flow**:
1. User clicks "Buy More Codes"
2. Frontend shows purchase modal
3. User selects quantity
4. Frontend calculates total
5. User confirms purchase
6. Frontend calls `POST /api/tenant/activation-codes/purchase`
7. Backend processes payment via Stripe
8. Backend generates codes after successful payment
9. Backend updates quota
10. Frontend displays success with generated codes

**Webhook Handlers** (Update existing):
- `subscription.updated` - Handle plan changes
- `invoice.payment_succeeded` - Handle successful payments
- `invoice.payment_failed` - Handle failed payments
- `customer.subscription.deleted` - Handle cancellations

**Files to Update**:
- `addon_portal/api/routers/billing_stripe.py` - Add webhook handlers
- `addon_portal/api/services/billing_service.py` - Add Stripe integration

---

## 🧪 Testing Requirements

### **Profile Page Testing**
- [ ] Profile data loads correctly
- [ ] Subscription details display accurately
- [ ] Quota meters display correctly
- [ ] Edit form validation works
- [ ] Email validation works
- [ ] Domain validation works
- [ ] Color picker works
- [ ] Logo upload works (file and URL)
- [ ] Save changes works
- [ ] Error handling works
- [ ] Loading states display correctly

### **Billing Page Testing**
- [ ] Billing data loads correctly
- [ ] Current subscription displays accurately
- [ ] Billing history loads with pagination
- [ ] Invoice download works
- [ ] Plan comparison displays correctly
- [ ] Upgrade flow works end-to-end
- [ ] Downgrade flow works (with warnings)
- [ ] Activation code purchase works
- [ ] Payment method update works
- [ ] Auto-renewal toggle works
- [ ] Cancel subscription works (with confirmation)
- [ ] Stripe checkout integration works
- [ ] Webhook handlers process correctly
- [ ] Error handling works
- [ ] Loading states display correctly

### **Integration Testing**
- [ ] Profile update updates billing page
- [ ] Plan upgrade updates profile page
- [ ] Code purchase updates quota on profile page
- [ ] Subscription cancellation updates both pages
- [ ] Payment failures handled gracefully
- [ ] Webhook events update UI correctly

---

## 📊 Database Schema Requirements

### **Existing Tables** (Verify/Update)
- `tenants` - Already has: `name`, `slug`, `email`, `phone_number`, `logo_url`, `primary_color`, `domain`
- `subscriptions` - Already has: `plan_id`, `status`, `stripe_subscription_id`, `stripe_customer_id`
- `activation_codes` - Already has: `tenant_id`, `code_hash`, `max_uses`, `used_count`

### **New Tables** (If Needed)
- `billing_invoices` - Store invoice history
  ```sql
  CREATE TABLE billing_invoices (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
      stripe_invoice_id VARCHAR(255) UNIQUE,
      amount DECIMAL(10, 2) NOT NULL,
      currency VARCHAR(3) DEFAULT 'usd',
      status VARCHAR(50) NOT NULL,
      description TEXT,
      invoice_date TIMESTAMP NOT NULL,
      pdf_url TEXT,
      created_at TIMESTAMP DEFAULT NOW(),
      INDEX idx_billing_invoices_tenant_id (tenant_id),
      INDEX idx_billing_invoices_date (invoice_date)
  );
  ```

- `activation_code_purchases` - Track code purchases
  ```sql
  CREATE TABLE activation_code_purchases (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
      quantity INTEGER NOT NULL,
      price_per_code DECIMAL(10, 2) NOT NULL,
      total_amount DECIMAL(10, 2) NOT NULL,
      stripe_payment_intent_id VARCHAR(255),
      purchase_date TIMESTAMP DEFAULT NOW(),
      INDEX idx_activation_code_purchases_tenant_id (tenant_id)
  );
  ```

---

## 🚀 Deployment Checklist

### **Backend**
- [ ] All API endpoints implemented
- [ ] Database migrations run
- [ ] Stripe webhooks configured
- [ ] Environment variables set (Stripe keys)
- [ ] Error handling implemented
- [ ] Logging implemented
- [ ] API documentation updated

### **Frontend**
- [ ] Profile page implemented
- [ ] Billing page implemented
- [ ] Stripe checkout integration
- [ ] Error handling implemented
- [ ] Loading states implemented
- [ ] Responsive design
- [ ] Accessibility (WCAG 2.1 AA)
- [ ] Navigation updated (add Profile and Billing links)

### **Testing**
- [ ] Unit tests written
- [ ] Integration tests written
- [ ] E2E tests written
- [ ] Manual testing completed
- [ ] Cross-browser testing
- [ ] Mobile testing

---

## 📝 Documentation Requirements

### **User Guides**
- **Tenant Portal User Guide** - Add sections:
  - Managing Your Profile
  - Understanding Your Subscription
  - Upgrading Your Plan
  - Purchasing Activation Codes
  - Managing Billing

### **Technical Documentation**
- **API Reference** - Document all new endpoints
- **Stripe Integration Guide** - Document checkout flows
- **Database Schema** - Document new tables

---

## 🎯 Success Criteria

### **Profile Page**
- [ ] All tenant information displays correctly
- [ ] Subscription details accurate
- [ ] Quota meters functional
- [ ] Edit functionality works
- [ ] Branding preview works
- [ ] Responsive design
- [ ] No console errors

### **Billing Page**
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

## 📅 Timeline

**Week 4**:
- Days 1-2: Backend API endpoints (Profile & Billing)
- Days 3-4: Frontend Profile page
- Day 5: Testing & bug fixes

**Week 5**:
- Days 1-3: Frontend Billing page
- Days 4-5: Stripe integration & testing

**Total**: 10 days (2 weeks)

---

## 🔗 Related Documents

- `docs/COMPLETE_SOLUTION_COMPLETION_PLAN_REVISED.md` - Overall completion plan
- `docs/PROJECT_EXECUTION_WORKFLOW_PLAN.md` - Project execution workflow
- `docs/BILLING_SYSTEM_ARCHITECTURE.md` - Billing system architecture

---

**End of Roadmap**

*Document: TENANT_PROFILE_BILLING_ROADMAP.md*  
*Date: November 19, 2025*  
*Version: 1.0*  
*Status: Ready for Implementation*

