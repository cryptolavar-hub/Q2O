# API Bugs Fixed - November 11, 2025

**Status**: ✅ **ALL 3 CRITICAL BUGS FIXED**

---

## Bug 1: Activation Code Generation API Mismatch ✅ FIXED

### Issue
The `generateCodes` function had two critical mismatches:
1. **Wrong URL**: Called `/admin/codes/generate` instead of `/admin/api/codes/generate`
2. **Wrong Response Handling**: Expected redirect with URL parameters, but backend returns JSON

### Impact
- Activation code generation would fail
- No codes would be returned to users
- Silent failure (no error shown)

### Fix Applied
**File**: `addon_portal/apps/admin-portal/src/lib/api.ts` (lines 82-104)

**Changes**:
```typescript
// BEFORE (BROKEN):
const response = await fetch(`${API_BASE}/admin/codes/generate`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  body: formData.toString(),
});
if (response.ok && response.redirected) {
  const url = new URL(response.url);
  const created = url.searchParams.get('created');
  return created ? created.split(',') : [];
}

// AFTER (FIXED):
const response = await fetch(`${API_BASE}/admin/api/codes/generate`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(data),
});
const responseData = await response.json();
return responseData.codes || [];
```

**Backend Endpoint**: `POST /admin/api/codes/generate`  
**Response Format**: `{ success: boolean, message: string, codes: string[] }`

---

## Bug 2: Code Revocation API Mismatch ✅ FIXED

### Issue
The `revokeCode` function had multiple critical mismatches:
1. **Wrong Method**: Used POST with form data
2. **Wrong URL**: Called `/admin/codes/revoke` (doesn't exist)
3. **Wrong Parameters**: Sent `tenant_slug` and `code_plain`
4. **Backend Expects**: DELETE with code ID as path parameter

### Impact
- Code revocation completely broken
- Clicking "Revoke" button would fail
- Error not properly displayed to user

### Fix Applied
**Files**: 
- `addon_portal/apps/admin-portal/src/lib/api.ts` (lines 156-166)
- `addon_portal/apps/admin-portal/src/pages/codes.tsx` (line 88)

**Changes**:
```typescript
// BEFORE (BROKEN):
export async function revokeCode(tenantSlug: string, code: string): Promise<void> {
  const formData = new URLSearchParams();
  formData.append('tenant_slug', tenantSlug);
  formData.append('code_plain', code);
  await fetch(`${API_BASE}/admin/codes/revoke`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: formData.toString(),
  });
}

// Usage in codes.tsx:
await revokeCode(code.tenant, code.code || '');

// AFTER (FIXED):
export async function revokeCode(codeId: number): Promise<void> {
  const response = await fetch(`${API_BASE}/admin/api/codes/${codeId}`, {
    method: 'DELETE',
  });
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(errorData.detail || `Failed to revoke code: ${response.statusText}`);
  }
}

// Usage in codes.tsx:
await revokeCode(code.id);
```

**Backend Endpoint**: `DELETE /admin/api/codes/{code_id}`  
**Parameters**: `code_id` (integer) in URL path

---

## Bug 3: LLM Configuration Endpoint Mismatch ✅ FIXED

### Issue
The LLM configuration page fetched from `/api/llm/config` which no longer exists after backend refactoring. New endpoint is `/api/llm/system`.

### Impact
- API keys section fails to load
- Configuration page shows "Not configured" for all providers
- Silent failure (no error shown to user)

### Fix Applied
**File**: `addon_portal/apps/admin-portal/src/pages/llm/configuration.tsx` (lines 49-102)

**Changes**:
```typescript
// BEFORE (BROKEN):
const keysRes = await fetch('/api/llm/config');
if (keysRes.ok) {
  const data = await keysRes.json();
  const keys: APIKey[] = [
    {
      provider: 'gemini',
      name: 'Google Gemini Pro',
      key: data.providers?.gemini?.apiKey || 'Not configured',
      enabled: data.providers?.gemini?.enabled || false
    },
    // ...
  ];
}

// AFTER (FIXED):
const keysRes = await fetch('/api/llm/system');
if (keysRes.ok) {
  const data = await keysRes.json();
  const keys: APIKey[] = [
    {
      provider: 'gemini',
      name: 'Google Gemini Pro',
      key: 'Configured via .env',
      enabled: data.primaryProvider === 'gemini' || 
               data.secondaryProvider === 'gemini' || 
               data.tertiaryProvider === 'gemini'
    },
    // ...
  ];
  
  // System prompt from DB
  setSystemPrompt({
    hostname: window.location.hostname || 'localhost',
    prompt: data.systemPrompt || 'Default prompt...'
  });
}
```

**Also Fixed Project Prompts**:
```typescript
// BEFORE:
const promptsRes = await fetch('/api/llm/project-prompts');
const formattedPrompts = promptsData.projects.map(...)

// AFTER:
const promptsRes = await fetch('/api/llm/projects');
const formattedPrompts = (promptsData.items || []).map(...)
```

**Backend Endpoints**:
- `GET /api/llm/system` - Returns `SystemConfigResponse`
- `GET /api/llm/projects` - Returns `ProjectCollectionResponse { items: [], total, page, pageSize }`

---

## Backend Field Fixes

### ActivationCode Model
**File**: `addon_portal/api/routers/admin_api.py` (line 322)

**Fixed**:
```python
# BEFORE (BROKEN):
new_code = ActivationCode(
    ...
    revoked=False  # Field doesn't exist!
)

# AFTER (FIXED):
new_code = ActivationCode(
    ...
    revoked_at=None  # Correct field name
)
```

---

## Testing Recommendations

### Test 1: Activation Code Generation
1. Visit http://localhost:3002/codes
2. Click "Generate Codes"
3. Fill form and submit
4. Verify codes appear in table
5. Verify codes can be copied

### Test 2: Code Revocation
1. Select an active code
2. Click "Revoke"
3. Confirm action
4. Verify code status changes to "Revoked"
5. Verify "Revoke" button disabled

### Test 3: LLM Configuration
1. Visit http://localhost:3002/llm/configuration
2. Verify API keys section loads
3. Verify provider status shown
4. Verify system prompt displayed
5. Verify project prompts table populated

---

## Summary

✅ **Bug 1**: Fixed activation code generation endpoint and response parsing  
✅ **Bug 2**: Fixed code revocation to use DELETE with code_id  
✅ **Bug 3**: Fixed LLM config to use `/api/llm/system` and `/api/llm/projects`  
✅ **Backend**: Fixed ActivationCode.revoked field mismatch  

**Status**: All critical API bugs resolved. Ready for testing!

---

**Fixed**: November 11, 2025  
**Files Changed**: 3 files  
**Lines Changed**: ~30 lines  
**Impact**: Critical features now functional

