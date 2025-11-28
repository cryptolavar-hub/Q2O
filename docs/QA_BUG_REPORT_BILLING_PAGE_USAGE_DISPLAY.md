# 🐛 QA Bug Report: Billing Page Usage Display Mismatch

**Date**: November 28, 2025  
**Status**: ✅ **FIXED**  
**Reported By**: User  
**Fixed By**: QA_Engineer — Bug Hunter

---

## 📋 **Issue Description**

Both the **Billing page** and **Profile page** display incorrect usage metrics:

1. **Monthly Run Quota**: Shows 0% usage (0 / 50) even when projects have been executed
2. **Activation Codes**: Shows all-time totals instead of monthly issued/used counts
3. **Graphs not matching numbers**: Progress bars don't reflect actual usage

**User Observation**:
> "This look odd, why the graphs not matching the numbers right. Activation Codes is what is issued in the month and used, while a Quota is the plan's allocation, yet not seeing any reflection of use of Quota."
> 
> "Same for profile page..."

---

## 🔍 **Root Cause Analysis**

### **Problem 1: Monthly Run Quota Showing 0%**

**Root Cause**: The billing endpoint was using static fields from the `Tenant` model:
- `tenant.usage_current` - Static field that doesn't update automatically
- `tenant.usage_quota` - Static field, not the plan's actual quota

**Expected Behavior**:
- Should use `MonthlyUsageRollup.runs` for current month usage
- Should use `subscription.plan.monthly_run_quota` for quota
- Fallback to counting project executions from `LLMProjectConfig.execution_started_at` if `MonthlyUsageRollup` doesn't exist

### **Problem 2: Activation Codes Showing All-Time Totals**

**Root Cause**: The billing endpoint was calculating all-time totals:
- `activation_codes_total` - All codes ever created for tenant
- `activation_codes_used` - All codes ever used for tenant

**Expected Behavior**:
- Should show codes **issued this month** (filtered by `created_at`)
- Should show codes **used this month** (codes created this month with `use_count > 0`)

---

## ✅ **Solution Implemented**

### **Fix 1: Use Actual Usage Data for Monthly Run Quota**

**File**: `addon_portal/api/routers/tenant_api.py`

**Changes**:
1. Query `MonthlyUsageRollup` for current month usage
2. Fallback to counting project executions from `LLMProjectConfig.execution_started_at` if rollup doesn't exist
3. Use `subscription.plan.monthly_run_quota` instead of `tenant.usage_quota`

**Code**:
```python
# QA_Engineer: Calculate actual current month usage from MonthlyUsageRollup (not static tenant.usage_current)
today = now_in_server_tz()
usage_result = await db.execute(
    select(MonthlyUsageRollup).where(
        MonthlyUsageRollup.tenant_id == tenant_info["tenant_id"],
        MonthlyUsageRollup.year == today.year,
        MonthlyUsageRollup.month == today.month
    )
)
usage_rollup = usage_result.scalar_one_or_none()

if usage_rollup:
    current_month_usage = usage_rollup.runs
else:
    # Fallback: Count project executions this month from LLMProjectConfig
    project_executions_result = await db.execute(
        select(func.count(LLMProjectConfig.id)).where(
            LLMProjectConfig.tenant_id == tenant_info["tenant_id"],
            LLMProjectConfig.execution_started_at.isnot(None),
            extract('year', LLMProjectConfig.execution_started_at) == today.year,
            extract('month', LLMProjectConfig.execution_started_at) == today.month
        )
    )
    current_month_usage = project_executions_result.scalar() or 0

# QA_Engineer: Use plan's monthly_run_quota (not tenant.usage_quota which is static)
monthly_run_quota = subscription.plan.monthly_run_quota if subscription and subscription.plan else 0
```

### **Fix 2: Calculate Monthly Activation Code Stats**

**File**: `addon_portal/api/routers/tenant_api.py`

**Changes**:
1. Filter activation codes by `created_at` year/month for current month
2. Count codes issued this month
3. Count codes used this month (codes created this month with `use_count > 0`)

**Code**:
```python
# QA_Engineer: Calculate activation codes issued/used THIS MONTH (not all-time)
# Activation codes issued this month
codes_issued_this_month_result = await db.execute(
    select(func.count(ActivationCode.id)).where(
        ActivationCode.tenant_id == tenant_info["tenant_id"],
        extract('year', ActivationCode.created_at) == today.year,
        extract('month', ActivationCode.created_at) == today.month
    )
)
activation_codes_total = codes_issued_this_month_result.scalar() or 0

# Activation codes used this month (codes created this month that have use_count > 0)
codes_used_this_month_result = await db.execute(
    select(func.count(ActivationCode.id)).where(
        ActivationCode.tenant_id == tenant_info["tenant_id"],
        ActivationCode.use_count > 0,
        extract('year', ActivationCode.created_at) == today.year,
        extract('month', ActivationCode.created_at) == today.month
    )
)
activation_codes_used = codes_used_this_month_result.scalar() or 0
```

### **Fix 3: Updated Imports**

**File**: `addon_portal/api/routers/tenant_api.py`

**Changes**:
- Added `extract` to SQLAlchemy imports
- Added `LLMProjectConfig` import for fallback counting

---

## 📊 **Expected Results**

After the fix:

1. **Monthly Run Quota**:
   - ✅ Shows actual project executions for current month
   - ✅ Uses plan's `monthly_run_quota` (e.g., 50 for Pro plan)
   - ✅ Progress bar reflects actual usage percentage
   - ✅ Example: If 5 projects executed this month → "5 / 50" → 10% progress bar

2. **Activation Codes**:
   - ✅ Shows codes issued this month only
   - ✅ Shows codes used this month only
   - ✅ Progress bar reflects monthly usage
   - ✅ Example: If 12 codes issued this month, 12 used → "12 / 12" → 100% progress bar

---

## 🧪 **Testing Checklist**

- [ ] Verify Monthly Run Quota shows actual project executions
- [ ] Verify Monthly Run Quota uses plan's quota (not tenant.usage_quota)
- [ ] Verify Activation Codes shows monthly stats (not all-time)
- [ ] Verify progress bars match the numbers displayed
- [ ] Test with multiple projects executed this month
- [ ] Test with activation codes issued/used this month
- [ ] Test edge cases (no projects, no codes, etc.)

---

## 📝 **Files Modified**

1. `addon_portal/api/routers/tenant_api.py`
   - Updated `/billing` endpoint to use actual usage data
   - Added fallback for project execution counting
   - Changed activation code calculation to monthly stats
   - Added `extract` to SQLAlchemy imports

2. `addon_portal/api/services/tenant_service.py`
   - Updated `_load_subscription_details()` function (used by `/profile` endpoint)
   - Changed to use `MonthlyUsageRollup` for current month usage
   - Added fallback to count project executions from `LLMProjectConfig`
   - Changed to use plan's `monthly_run_quota` instead of static `tenant.usage_quota`
   - Changed activation code calculation to monthly stats (issued/used this month)
   - Added `extract` to SQLAlchemy imports
   - Added `MonthlyUsageRollup` to model imports

---

## ✅ **Status**

**Fixed**: November 28, 2025  
**Ready for Testing**: Yes

---

**Fixed By**: QA_Engineer — Bug Hunter  
**Date**: November 28, 2025

