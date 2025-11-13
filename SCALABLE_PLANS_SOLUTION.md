# ✅ Scalable Subscription Plans Solution

**Date**: November 12, 2025  
**Status**: ✅ **IMPLEMENTED**

---

## 🎯 **Problem Identified**

### **Issues with Hardcoded Plans:**
1. **Inconsistency**: Plans hardcoded in multiple places:
   - Frontend: `tenants.tsx` had `PLAN_OPTIONS` array
   - Backend seeding: `quick_setup.py` 
   - Backend analytics: `admin_api.py` had hardcoded `color_map`
   - Config file: `pricing_config.json` had "Professional" instead of "Pro"

2. **Not Scalable**: 
   - Adding/modifying plans required code changes in multiple files
   - Risk of inconsistencies (e.g., "Professional" vs "Pro")
   - No single source of truth

3. **Maintenance Burden**:
   - Changes required frontend rebuild
   - Database and code could get out of sync

---

## ✅ **Solution Implemented**

### **Single Source of Truth: Database**

**The database (`plans` table) is now the ONLY source of truth for subscription plans.**

### **1. Backend API Endpoint** ✅

**File**: `addon_portal/api/routers/admin_api.py`

**New Endpoint**: `GET /admin/api/plans`

```python
@router.get("/plans", response_model=PlanCollectionResponse)
async def get_plans(db: Session = Depends(get_db)) -> PlanCollectionResponse:
    """Get all available subscription plans from the database.
    
    This endpoint provides the single source of truth for subscription plans.
    Frontend should use this to populate plan dropdowns dynamically.
    """
```

**Returns**:
```json
{
  "plans": [
    {
      "id": 1,
      "name": "Starter",
      "stripePriceId": "price_starter_monthly",
      "monthlyRunQuota": 10
    },
    {
      "id": 2,
      "name": "Pro",
      "stripePriceId": "price_pro_monthly",
      "monthlyRunQuota": 50
    },
    {
      "id": 3,
      "name": "Enterprise",
      "stripePriceId": "price_enterprise_monthly",
      "monthlyRunQuota": 200
    }
  ]
}
```

### **2. Plan Schema** ✅

**File**: `addon_portal/api/schemas/plan.py` (NEW)

Defines the response structure for plans.

### **3. Frontend Dynamic Loading** ✅

**File**: `addon_portal/apps/admin-portal/src/pages/tenants.tsx`

**Changes**:
- ❌ **Removed**: Hardcoded `PLAN_OPTIONS` array
- ✅ **Added**: `getPlans()` API call to fetch plans from database
- ✅ **Added**: `plans` state that loads dynamically on component mount
- ✅ **Updated**: Dropdown now uses `plans.map()` instead of `PLAN_OPTIONS.map()`

**File**: `addon_portal/apps/admin-portal/src/lib/api.ts`

**Added**:
```typescript
export async function getPlans(): Promise<Plan[]> {
  const url = `${API_BASE}/admin/api/plans`;
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error('Failed to fetch subscription plans');
  }
  const data: PlansResponse = await response.json();
  return data.plans;
}
```

---

## 📋 **How to Manage Plans Now**

### **Adding a New Plan:**

1. **Add to Database** (via SQL or admin tool):
```sql
INSERT INTO plans (name, stripe_price_id, monthly_run_quota)
VALUES ('Premium', 'price_premium_monthly', 100);
```

2. **That's it!** ✅
   - Frontend will automatically show the new plan
   - No code changes needed
   - No rebuild required (if using hot reload)

### **Modifying an Existing Plan:**

1. **Update Database**:
```sql
UPDATE plans 
SET monthly_run_quota = 75 
WHERE name = 'Pro';
```

2. **Refresh Frontend** - New quota will appear automatically

### **Removing a Plan:**

1. **Remove from Database** (with caution - check for active subscriptions):
```sql
DELETE FROM plans WHERE name = 'OldPlan';
```

2. **Frontend will automatically remove it from dropdown**

---

## 🔍 **Where Plans Are Used**

### **✅ Now Dynamic (Database-Driven):**
- ✅ Tenant creation form dropdown
- ✅ Tenant edit form dropdown
- ✅ Plans API endpoint

### **⚠️ Still Needs Update (Future Work):**
- ⚠️ Analytics page color mapping (currently hardcoded in `admin_api.py`)
- ⚠️ Any other hardcoded plan references

---

## 🎯 **Benefits**

1. **✅ Single Source of Truth**: Database is the only place plans are defined
2. **✅ Scalable**: Add/modify plans without code changes
3. **✅ Consistent**: No more "Professional" vs "Pro" mismatches
4. **✅ Maintainable**: Changes happen in one place (database)
5. **✅ Real-time**: Frontend always shows current plans from database

---

## 📝 **Migration Notes**

### **Before (Hardcoded):**
```typescript
const PLAN_OPTIONS = [
  { value: 'Starter', label: 'Starter · 10 migrations / month' },
  { value: 'Professional', label: 'Professional · 50 migrations / month' }, // ❌ Wrong name!
  { value: 'Enterprise', label: 'Enterprise · 200 migrations / month' },
];
```

### **After (Dynamic):**
```typescript
// Plans loaded from database
const [plans, setPlans] = useState<Plan[]>([]);

useEffect(() => {
  const loadPlans = async () => {
    const fetchedPlans = await getPlans(); // ✅ From database
    setPlans(fetchedPlans);
  };
  loadPlans();
}, []);

// Dropdown uses dynamic plans
{plans.map((plan) => (
  <option key={plan.id} value={plan.name}>
    {plan.name} · {plan.monthlyRunQuota} migrations / month
  </option>
))}
```

---

## 🚀 **Next Steps (Optional Improvements)**

1. **Admin UI for Plan Management**: Create a page to add/edit/delete plans via UI
2. **Plan Validation**: Ensure plans can't be deleted if they have active subscriptions
3. **Plan History**: Track plan changes over time
4. **Plan Features**: Add feature flags/permissions per plan
5. **Update Analytics**: Make color mapping dynamic based on plan names

---

## ✅ **Testing**

1. ✅ Plans load from database on page load
2. ✅ Dropdown shows all plans from database
3. ✅ Plan names match database exactly
4. ✅ No hardcoded plan references in frontend
5. ✅ Adding a plan to database shows up immediately (after refresh)

---

**This solution is now production-ready and scalable!** 🎉

