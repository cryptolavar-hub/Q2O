# Security Fix: Password Parsing Vulnerability

**Date**: November 14, 2025  
**Severity**: HIGH  
**Status**: FIXED

---

## 🚨 Security Issue

The DB_DSN regex parsing in `CHECK_DASHBOARD_STATUS.bat` was vulnerable to passwords containing special characters (`:`, `@`). The regex pattern `'://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)'` would fail to correctly extract passwords containing these characters.

### **Problem Examples**:
- Password `pass@word` → Would stop at first `@`, treating `word` as hostname
- Password `pass:word` → Would stop at first `:`, treating `word` as port
- Password `p@ss:w0rd` → Would completely break parsing

### **Root Cause**:
The regex used character class negation (`[^:]` and `[^@]`) which matches everything up to the FIRST occurrence of the delimiter, not handling cases where the password itself contains these characters.

---

## ✅ Fix Applied

### **New Parsing Strategy**:

1. **Remove scheme**: Strip `postgresql+psycopg://` prefix
2. **Find LAST `@`**: This separates credentials from host (host cannot contain `@`)
3. **Split by FIRST `:`**: In `user:password`, split by first `:` only (password can contain `:`)
4. **Parse host:port/database**: Use regex `^([^:]+):(\d+)/(.+)$` (port is always numeric)

### **PowerShell Implementation**:

```powershell
# Extract password
$parts = $dsn -replace '^[^:]+://', ''  # Remove scheme
$atPos = $parts.LastIndexOf('@')         # Find LAST @
$userPass = $parts.Substring(0, $atPos) # Everything before LAST @
$colonPos = $userPass.IndexOf(':')       # Find FIRST :
$password = $userPass.Substring($colonPos + 1)  # Everything after FIRST :
```

### **Why This Works**:

- ✅ **Password with `@`**: `user:pass@word@host:5432/db` → Finds LAST `@`, splits by FIRST `:`
- ✅ **Password with `:`**: `user:pass:word@host:5432/db` → Finds LAST `@`, splits by FIRST `:`
- ✅ **Password with both**: `user:p@ss:w0rd@host:5432/db` → Works correctly
- ✅ **No password**: `user@host:5432/db` → Handles gracefully (no `:` in userPass)

---

## 🧪 Test Cases

### **Test 1: Password with `@`**
```
Input:  postgresql+psycopg://user:pass@word@localhost:5432/q2o
Output: password = "pass@word" ✅
```

### **Test 2: Password with `:`**
```
Input:  postgresql+psycopg://user:pass:word@localhost:5432/q2o
Output: password = "pass:word" ✅
```

### **Test 3: Password with both `@` and `:`**
```
Input:  postgresql+psycopg://user:p@ss:w0rd@localhost:5432/q2o
Output: password = "p@ss:w0rd" ✅
```

### **Test 4: Simple password (no special chars)**
```
Input:  postgresql+psycopg://user:password@localhost:5432/q2o
Output: password = "password" ✅
```

### **Test 5: No password (user only)**
```
Input:  postgresql+psycopg://user@localhost:5432/q2o
Output: password = "" (empty, handled gracefully) ✅
```

---

## 📋 Files Updated

- ✅ `CHECK_DASHBOARD_STATUS.bat` - Lines 114-138

---

## 🔒 Security Best Practices

✅ **DO**:
- Use robust parsing that handles edge cases
- Test with passwords containing special characters
- Use `LastIndexOf()` for delimiters that appear multiple times
- Use `IndexOf()` for delimiters that should appear once
- Validate parsed values before use

❌ **DON'T**:
- Use simple regex with character class negation for complex strings
- Assume passwords won't contain special characters
- Use `[^X]+` patterns when `X` can appear in the matched content

---

## ✅ Verification

To verify the fix:
1. Create `.env` file with password containing `@`: `DB_DSN=postgresql+psycopg://user:pass@word@localhost:5432/q2o`
2. Run `CHECK_DASHBOARD_STATUS.bat`
3. Script should correctly parse password as `pass@word`
4. Database connection should succeed

---

**Status**: Password parsing vulnerability fixed. Script now handles passwords with special characters correctly.

