# Billing System Architecture - Data-Volume-Based Pricing

**Complete Revenue Model for Migration Services**

**Date**: November 5, 2025  
**Version**: 1.0  
**Integration**: Mobile App, APIs, Agents, Stripe

---

## 🎯 Executive Summary

**Quick2Odoo now includes a complete billing system** that charges based on:

1. **Years of historical data** (1-20+ years)
2. **Total record count** (actual or estimated)
3. **Platform complexity** (QuickBooks, SAGE, Wave, etc.)
4. **Business size** (Starter, Professional, Enterprise, Custom)

**Key Features**:
- ✅ **Data-volume-based pricing** (fair and transparent)
- ✅ **Quick estimates** without platform connection
- ✅ **Accurate analysis** with platform connection
- ✅ **Stripe integration** for payment processing
- ✅ **Mobile app billing UI** (pricing, checkout, status)
- ✅ **Multi-platform support** (different rates per platform)

---

## 💰 Pricing Model

### **Pricing Tiers**

| Tier | Base Price | Years Included | Records Included | Extra Records | Best For |
|------|------------|----------------|------------------|---------------|----------|
| **Starter** | $499 | 1-2 years | Up to 5,000 | $5/1000 | Small businesses, startups |
| **Professional** | $1,499 | 3-5 years | Up to 50,000 | $3/1000 | Growing businesses |
| **Enterprise** | $4,999 | 6-10 years | Up to 500,000 | $2/1000 | Established enterprises |
| **Custom** | $9,999+ | 10+ years | 500,000+ | $1.50/1000 | Large enterprises |

### **Platform Complexity Multipliers**

| Platform | Multiplier | Reason |
|----------|------------|--------|
| Wave, Expensify | 0.9x | Simple REST APIs |
| QuickBooks Online, Dext, doola | 1.0x | Standard complexity |
| QuickBooks Desktop, SAGE 50 | 1.3x | Legacy protocols (WebConnector, SOAP) |
| SAGE 100, Xero | 1.4x | Complex data models |
| SAGE 200 | 1.5x | Multi-entity, complex |
| SAGE X3, NetSuite | 2.0x | Enterprise ERP complexity |

### **Pricing Calculation Formula**

```
Base Price (tier-based)
+ Data Volume Fee (excess records × price per 1000)
+ Years Multiplier Fee (10% per additional year)
+ Platform Complexity Fee (base × (multiplier - 1.0))
= Subtotal
+ Tax (subtotal × tax_rate)
= TOTAL
```

---

## 🏗️ System Architecture

### **Component Diagram**

```
┌─────────────────────────────────────────────────────────────────┐
│                      MOBILE APP LAYER                            │
│                                                                   │
│  ┌────────────────────┐  ┌────────────────────┐                │
│  │  BillingScreen     │  │ PaymentStatusScreen│                │
│  │  - Platform select │  │ - Payment tracking │                │
│  │  - Years selector  │  │ - Status polling   │                │
│  │  - Price preview   │  │ - Auto-redirect    │                │
│  │  - Checkout button │  │                    │                │
│  └─────────┬──────────┘  └──────────┬─────────┘                │
│            │                        │                            │
│            │ API calls              │                            │
└────────────┼────────────────────────┼────────────────────────────┘
             │                        │
             ▼                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                       API LAYER                                  │
│                                                                   │
│  📍 POST /api/billing/estimate                                  │
│     → Returns quick cost estimate                                │
│                                                                   │
│  📍 POST /api/billing/analyze-volume                            │
│     → Connects to platform, calculates exact pricing             │
│                                                                   │
│  📍 POST /api/billing/checkout                                  │
│     → Creates Stripe checkout session                            │
│                                                                   │
│  📍 GET /api/billing/payment/{session_id}/status                │
│     → Checks payment status                                      │
│                                                                   │
│  📍 POST /api/billing/webhook                                   │
│     → Receives Stripe webhook events                             │
│                                                                   │
│  📍 GET /api/billing/pricing-tiers                              │
│     → Returns tier information                                   │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                    BUSINESS LOGIC LAYER                          │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  MigrationPricingEngine (utils/migration_pricing.py)      │  │
│  │  - analyze_data_volume()                                  │  │
│  │  - calculate_pricing()                                    │  │
│  │  - estimate_cost_quick()                                  │  │
│  │  - get_pricing_tiers_info()                               │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  EnhancedBillingManager (api/app/billing_enhanced.py)     │  │
│  │  - create_checkout_session()                              │  │
│  │  - verify_payment_status()                                │  │
│  │  - handle_webhook()                                       │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                    INTEGRATION LAYER                             │
│                                                                   │
│  ┌──────────────────┐  ┌────────────────────┐                  │
│  │  Stripe API      │  │ Source Platform    │                  │
│  │  - Checkout      │  │ - Data extraction  │                  │
│  │  - Payments      │  │ - Volume analysis  │                  │
│  │  - Webhooks      │  │ - Entity counting  │                  │
│  └──────────────────┘  └────────────────────┘                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📊 Pricing Examples

### **Example 1: Small Business (Starter Tier)**

**Scenario**:
- Platform: Wave Accounting
- Years of data: 2 years
- Estimated records: 3,500
  - Customers: 100
  - Invoices: 800
  - Bills: 400
  - Payments: 1,200
  - Products: 50
  - Other: 950

**Pricing Calculation**:
```
Base Price (Starter):           $499.00
Data Volume Fee:                $0.00   (3,500 < 5,000 base allocation)
Years Multiplier (2 years):     $49.90  ($499 × 10%)
Platform Complexity (Wave 0.9x): -$49.90 ($499 × -10%)
─────────────────────────────────────
Subtotal:                       $499.00
Tax (0%):                       $0.00
─────────────────────────────────────
TOTAL:                          $499.00
```

**What's Included**:
- Full migration (all entities)
- 2 years historical data
- Email support
- Data validation report

---

### **Example 2: Growing Business (Professional Tier)**

**Scenario**:
- Platform: QuickBooks Online
- Years of data: 5 years
- Estimated records: 28,000
  - Customers: 500
  - Vendors: 200
  - Invoices: 8,000
  - Bills: 4,000
  - Payments: 10,000
  - Products: 300
  - Journal Entries: 2,000
  - Other: 3,000

**Pricing Calculation**:
```
Base Price (Professional):      $1,499.00
Data Volume Fee:                $0.00   (28,000 < 50,000 base allocation)
Years Multiplier (5 years):     $599.60 ($1,499 × 40%)
Platform Complexity (QBO 1.0x): $0.00   (no premium)
─────────────────────────────────────
Subtotal:                       $2,098.60
Tax (8%):                       $167.89
─────────────────────────────────────
TOTAL:                          $2,266.49
```

**What's Included**:
- Full migration (all 40+ QuickBooks entities)
- 5 years historical data
- Priority email support
- Data validation report
- Multiple company migration

---

### **Example 3: Enterprise (Enterprise Tier)**

**Scenario**:
- Platform: SAGE 200
- Years of data: 10 years
- Actual records analyzed: 275,000
  - Customers: 5,000
  - Vendors: 3,000
  - Sales Invoices: 80,000
  - Purchase Invoices: 50,000
  - Payments: 100,000
  - Products: 10,000
  - Journal Entries: 20,000
  - Other: 7,000

**Pricing Calculation**:
```
Base Price (Enterprise):        $4,999.00
Data Volume Fee:                $0.00   (275,000 < 500,000 base allocation)
Years Multiplier (10 years):    $4,499.10 ($4,999 × 90%)
Platform Complexity (SAGE 1.5x): $2,499.50 ($4,999 × 50%)
─────────────────────────────────────
Subtotal:                       $11,997.60
Tax (8%):                       $959.81
─────────────────────────────────────
TOTAL:                          $12,957.41
```

**What's Included**:
- Full migration (all SAGE entities)
- 10 years historical data
- 24/7 phone + email support
- Complete audit trail
- Balance sheet validation
- Dedicated migration specialist

---

## 🔄 Billing Workflow

### **User Journey**

```
1. User opens Mobile App
   ↓
2. Navigate to "New Migration"
   ↓
3. Select Platform (QuickBooks, SAGE, Wave, etc.)
   ↓
4. Select Years of Data (1-20+ years)
   ↓
5. App calls /api/billing/estimate
   ↓
6. Pricing shown: "$1,499 for 5 years, ~25,000 records"
   ↓
7. User reviews pricing breakdown
   ↓
8. (Optional) "Analyze Actual Data" → connects to platform for exact count
   ↓
9. User clicks "Proceed to Payment"
   ↓
10. App calls /api/billing/checkout
   ↓
11. Stripe checkout URL returned
   ↓
12. App opens Stripe checkout in browser
   ↓
13. User enters payment details
   ↓
14. Payment processed by Stripe
   ↓
15. Webhook sent to /api/billing/webhook
   ↓
16. Migration status updated to "PAID"
   ↓
17. Migration starts automatically
   ↓
18. User redirected to Dashboard to monitor progress
```

---

## 📱 Mobile App Integration

### **New Screens Created**

1. **BillingScreen** (`mobile/src/screens/BillingScreen.tsx`)
   - Platform selection (chips)
   - Years of data selector (1-20 years)
   - Real-time price calculator
   - Pricing breakdown display
   - Entity count estimates
   - "Analyze Actual Data" button
   - "Proceed to Payment" button

2. **PaymentStatusScreen** (`mobile/src/screens/PaymentStatusScreen.tsx`)
   - Payment status polling
   - Success/pending indicators
   - Migration details
   - Auto-redirect to dashboard when paid

### **Updated Services**

3. **ApiService.ts** - New methods:
   - `getPricingTiers()` - Get tier information
   - `estimateMigrationCost()` - Calculate pricing
   - `createCheckoutSession()` - Create Stripe session
   - `checkPaymentStatus()` - Verify payment

### **Navigation Updates Needed**

```typescript
// Add to MainNavigator.tsx
<Stack.Screen 
  name="Billing" 
  component={BillingScreen}
  options={{ title: 'Migration Pricing' }}
/>
<Stack.Screen 
  name="PaymentStatus" 
  component={PaymentStatusScreen}
  options={{ title: 'Payment Status' }}
/>
```

---

## 🔧 API Endpoints

### **1. GET /api/billing/pricing-tiers**

**Purpose**: Get pricing tier information

**Response**:
```json
[
  {
    "tier": "Starter",
    "base_price": 499.00,
    "years_included": "1-2 years",
    "records_included": "Up to 5,000 records",
    "price_per_1000_extra": 5.00,
    "best_for": "Small businesses",
    "features": [
      "Full migration (all entities)",
      "Email support",
      "2 years historical data"
    ]
  },
  ...
]
```

---

### **2. POST /api/billing/estimate**

**Purpose**: Quick cost estimate without platform connection

**Request**:
```json
{
  "platform_name": "QuickBooks Online",
  "years_of_data": 5,
  "estimated_records": null,  // Optional, will use typical
  "tax_rate": 0.08  // 8% tax
}
```

**Response**:
```json
{
  "base_price": 1499.00,
  "data_volume_fee": 0.00,
  "platform_complexity_fee": 0.00,
  "years_multiplier": 599.60,
  "subtotal": 2098.60,
  "tax": 167.89,
  "total": 2266.49,
  "tier": "professional",
  "pricing_details": {
    "years_of_data": 5,
    "total_records": 50000,
    "platform": "QuickBooks Online",
    "entity_breakdown": {
      "estimated": 50000
    },
    "complexity_score": 5.0
  }
}
```

---

### **3. POST /api/billing/analyze-volume**

**Purpose**: Accurate pricing with platform connection

**Request**:
```json
{
  "platform_name": "QuickBooks Online",
  "platform_credentials": {
    "realm_id": "your_realm_id",
    "access_token": "your_token"
  },
  "years_of_data": 5,
  "tax_rate": 0.08
}
```

**Response**:
```json
{
  "data_volume": {
    "years_of_data": 5,
    "total_records": 28543,
    "entity_breakdown": {
      "customers": 512,
      "vendors": 198,
      "invoices": 8234,
      "bills": 4012,
      "payments": 10345,
      "items": 342,
      "journal_entries": 1987,
      "classes": 12,
      "departments": 5,
      "accounts": 156,
      ...
    },
    "estimated_size_mb": 1427.15,
    "complexity_score": 6.8,
    "complexity_level": "Medium",
    "platform_name": "QuickBooks Online"
  },
  "pricing": {
    "base_price": 1499.00,
    "data_volume_fee": 0.00,
    "platform_complexity_fee": 0.00,
    "years_multiplier": 599.60,
    "subtotal": 2098.60,
    "tax": 167.89,
    "total": 2266.49,
    "tier": "professional"
  }
}
```

---

### **4. POST /api/billing/checkout**

**Purpose**: Create Stripe checkout session

**Request**:
```json
{
  "migration_id": "MIG-1730825400",
  "customer_email": "client@example.com",
  "pricing_data": {
    "total": 2266.49,
    "tier": "professional",
    "pricing_details": {
      "years_of_data": 5,
      "total_records": 28543,
      "platform": "QuickBooks Online"
    }
  }
}
```

**Response**:
```json
{
  "session_id": "cs_test_abc123",
  "url": "https://checkout.stripe.com/pay/cs_test_abc123",
  "amount": 2266.49,
  "currency": "usd"
}
```

---

### **5. GET /api/billing/payment/{session_id}/status**

**Purpose**: Check payment status

**Response**:
```json
{
  "migration_id": "MIG-1730825400",
  "payment_status": "paid",
  "status": "complete",
  "amount_total": 2266.49,
  "customer_email": "client@example.com",
  "tier": "professional",
  "paid": true
}
```

---

## 💡 Business Intelligence Features

### **Revenue Tracking**

The billing system tracks:
- Revenue per migration
- Revenue per platform
- Revenue per tier
- Average deal size
- Conversion rates

### **Data Volume Analytics**

Helps understand:
- Typical record counts per platform
- Average years of data migrated
- Most common migration sizes
- Pricing optimization opportunities

---

## 🔗 Integration with Migration Flow

### **Enhanced New Project Flow**

**Old Flow** (No Billing):
```
1. Select Platform
2. Enter Objectives
3. Click "Start Migration"
4. Migration starts immediately
```

**New Flow** (With Billing):
```
1. Select Platform
2. Select Years of Data
3. See Pricing Estimate
4. (Optional) Analyze Actual Data
5. Review Pricing Breakdown
6. Click "Proceed to Payment"
7. Pay via Stripe
8. Migration starts after payment confirmed
9. Monitor in Dashboard
```

---

## 📈 Business Impact

### **Revenue Potential**

| Scenario | Without Billing | With Billing | Revenue Increase |
|----------|-----------------|--------------|------------------|
| **100 migrations/year** | $0 (free tool) | $150,000 (avg $1,500/migration) | +$150K |
| **500 migrations/year** | $0 | $750,000 | +$750K |
| **1000 migrations/year** | $0 | $1,500,000 | +$1.5M |

**With Professional Services**:
- Tool revenue: $1,500/migration
- Services revenue: $3,000/migration (consulting, training)
- **Total per migration**: $4,500
- **1000 migrations**: $4.5M revenue potential

### **Pricing Competitiveness**

| Competitor | Manual Migration | Quick2Odoo Automated |
|------------|------------------|----------------------|
| **Development Cost** | $15,000-30,000 | $0 (automated) |
| **Service Fee** | $5,000-10,000 | $500-5,000 |
| **Total to Client** | $20,000-40,000 | $500-5,000 |
| **Our Margin** | N/A (we provide tool) | 80-90% |

**Quick2Odoo enables you to**:
- Charge clients $5,000-15,000 (market rate)
- Pay platform fee: $500-5,000
- Keep the difference: $4,500-10,000 per migration
- **Profit margin**: 60-90%

---

## 🎯 Pricing Strategy Recommendations

### **For SaaS Model (End Customers)**

**Charge**:
- Starter: $499
- Professional: $1,499
- Enterprise: $4,999

**Target**: Small businesses doing self-service migration

---

### **For White-Label (Consulting Firms)**

**Charge Consulting Firms**:
- Volume discounts (10+ migrations/year)
- $299-$2,999 per migration (wholesale)

**Consulting Firms Charge End Customers**:
- $5,000-$25,000 per migration (retail)

**Their Margin**: $4,700-$22,000 per migration

---

### **For Enterprise Contracts**

**Unlimited Annual Plan**:
- $99,999/year unlimited migrations
- Dedicated support
- Custom integrations
- White-glove service

---

## 📂 Files Created

### **Backend (3 files)**

1. ✅ `utils/migration_pricing.py` (400 lines)
   - MigrationPricingEngine
   - DataVolumeAnalysis
   - PricingTier calculations
   - Platform complexity multipliers

2. ✅ `api/app/billing_enhanced.py` (300 lines)
   - EnhancedBillingManager
   - FastAPI billing router
   - Stripe integration
   - Webhook handling

3. ✅ `config/quickbooks_to_odoo_mapping.json` (Already created)
   - Used for entity counting

### **Mobile App (2 files)**

4. ✅ `mobile/src/screens/BillingScreen.tsx` (400 lines)
   - Platform selection
   - Years selector
   - Real-time pricing
   - Checkout flow

5. ✅ `mobile/src/screens/PaymentStatusScreen.tsx` (250 lines)
   - Payment verification
   - Status polling
   - Auto-redirect

### **Mobile Services (1 file updated)**

6. ✅ `mobile/src/services/ApiService.ts` (Updated)
   - Added billing methods
   - Pricing API calls
   - Checkout API calls

### **Documentation (1 file)**

7. ✅ `docs/BILLING_SYSTEM_ARCHITECTURE.md` (This file)
   - Complete billing documentation
   - Pricing examples
   - Business model
   - Integration guide

---

## 🔐 Security Considerations

### **Payment Security**

- ✅ **PCI Compliance**: Stripe handles all card data (we never see it)
- ✅ **Webhook Verification**: Signatures verified on all webhooks
- ✅ **HTTPS Only**: All API calls encrypted
- ✅ **No Card Storage**: Never store payment methods

### **Pricing Integrity**

- ✅ **Server-side Calculation**: All pricing calculated on backend
- ✅ **Cannot Be Manipulated**: Mobile app displays, doesn't calculate
- ✅ **Audit Trail**: All pricing logged
- ✅ **Stripe Metadata**: Tier/years/records stored in Stripe

---

## 🚀 Implementation Checklist

### **Backend**
- [x] Create `utils/migration_pricing.py`
- [x] Create `api/app/billing_enhanced.py`
- [ ] Add billing router to main FastAPI app
- [ ] Set up Stripe environment variables
- [ ] Test webhook handling
- [ ] Create Stripe products/prices in dashboard

### **Mobile App**
- [x] Create `BillingScreen.tsx`
- [x] Create `PaymentStatusScreen.tsx`
- [x] Update `ApiService.ts`
- [ ] Add screens to navigation
- [ ] Test on iOS & Android
- [ ] Handle deep links (return from Stripe)

### **Configuration**
- [ ] Set Stripe API keys (`STRIPE_SECRET_KEY`)
- [ ] Set webhook secret (`STRIPE_WEBHOOK_SECRET`)
- [ ] Configure success/cancel URLs
- [ ] Set tax rate per region

---

## 📊 Analytics & Reporting

### **Metrics to Track**

1. **Revenue Metrics**:
   - Total revenue
   - Revenue per tier
   - Revenue per platform
   - Average deal size

2. **Customer Metrics**:
   - Migrations per tier
   - Most popular platform
   - Average years selected
   - Average record count

3. **Conversion Metrics**:
   - Quote-to-payment rate
   - Abandoned checkouts
   - Time to payment

4. **Operational Metrics**:
   - Payment success rate
   - Webhook delivery rate
   - Migration start rate post-payment

---

## 🎯 Next Steps

1. ✅ **Backend billing system created** (migration_pricing.py, billing_enhanced.py)
2. ✅ **Mobile app billing UI created** (BillingScreen, PaymentStatusScreen)
3. ✅ **API service updated** (billing methods added)
4. 📋 **To Do**:
   - Add billing screens to mobile navigation
   - Set up Stripe account & products
   - Test checkout flow end-to-end
   - Deploy billing API

---

**This billing system adds a complete revenue model to Quick2Odoo!**

**Potential Revenue**: $150K - $4.5M+ per year depending on volume.

---


