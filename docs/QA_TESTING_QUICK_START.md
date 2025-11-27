# QA Testing Quick Start Guide
**Role**: QA_Engineer  
**Date**: November 26, 2025

---

## 🚀 Quick Start Testing

### Current Status
- ✅ **Tenant Portal Dev Server**: Running on http://localhost:3000 (PID: 23808)
- ⬜ **Backend API**: Check if running on http://localhost:8080

---

## Step 1: Verify Backend API

```powershell
# Check if backend is running
netstat -ano | findstr ":8080"

# If not running, start it:
cd addon_portal
python -m uvicorn api.main:app --port 8080
```

**Expected**: Backend API should be accessible at http://localhost:8080/docs

---

## Step 2: Open Tenant Portal

1. Open browser: http://localhost:3000
2. Open DevTools (F12)
3. Navigate to Console tab
4. Navigate to Network tab → WS (WebSocket) filter

---

## Step 3: Quick Test Checklist

### ✅ Test 1: Page Loads Without Errors
- [ ] Navigate to http://localhost:3000/status
- [ ] Check console for errors
- [ ] Verify page renders

### ✅ Test 2: No Emojis Visible (BUG-006)
- [ ] Check Agent card - should show "Agent" text, not 🤖
- [ ] Check Completed card - should show "Complete" text, not ✅
- [ ] Check Chart card - should show "Chart" text, not 📊
- [ ] Check Active card - should show "Active" text, not ⚡
- [ ] Check section headers - no emojis

### ✅ Test 3: Project Selection Works (BUG-003)
- [ ] Select a project from dropdown
- [ ] Verify no React Hook warnings in console
- [ ] Switch to different project
- [ ] Verify projects reload correctly

### ✅ Test 4: Task List Clears on Project Change (BUG-007)
- [ ] Select Project A
- [ ] Note tasks in Task Timeline
- [ ] Switch to Project B
- [ ] Verify Task Timeline shows only Project B's tasks
- [ ] No tasks from Project A should remain

### ✅ Test 5: Scroll Position Preserved (BUG-001)
- [ ] Scroll down the page
- [ ] Wait for real-time updates
- [ ] Verify scroll position doesn't jump to top
- [ ] Navigate away and back
- [ ] Check for memory leak warnings

### ✅ Test 6: Subscription Filtering (BUG-004)
- [ ] Open Network tab → WS filter
- [ ] Select a project
- [ ] Verify WebSocket messages include `projectId`
- [ ] Switch projects
- [ ] Verify messages change to new project

### ✅ Test 7: Error Handling (BUG-008)
- [ ] Keep console open
- [ ] Stop backend API (if running separately)
- [ ] Verify error messages logged with "QA_Engineer:" prefix
- [ ] Restart backend
- [ ] Verify subscriptions reconnect

### ✅ Test 8: Status Normalization (BUG-005)
- [ ] Select project with tasks
- [ ] Verify task status badges display correctly
- [ ] Check for any "undefined" or "unknown" statuses
- [ ] Verify status colors are correct

---

## Step 4: Manual Testing Commands

### Check Console for Errors
```javascript
// In browser console, check for:
// 1. No React Hook warnings
// 2. No memory leak warnings
// 3. Subscription errors logged with "QA_Engineer:" prefix
```

### Check Network Tab
```
1. Open DevTools → Network
2. Filter by "WS" (WebSocket)
3. Click on WebSocket connection
4. Check "Messages" tab
5. Verify projectId in subscription variables
```

### Check React DevTools (if installed)
```
1. Install React DevTools extension
2. Open Components tab
3. Select StatusPage component
4. Check for memory leaks
5. Verify hooks dependencies
```

---

## Step 5: Document Results

Fill out test results in: `docs/QA_TEST_PLAN_SESSION_1.md`

---

## Common Issues & Solutions

### Issue: Page shows "Loading..." forever
**Solution**: Check if backend API is running on port 8080

### Issue: WebSocket connection fails
**Solution**: 
- Verify backend supports WebSocket subscriptions
- Check GraphQL endpoint configuration
- Verify projectId is being sent correctly

### Issue: Tasks not clearing on project change
**Solution**: Check console for errors, verify useEffect dependency array

### Issue: Scroll jumps to top
**Solution**: Check scroll position preservation logic, verify useLayoutEffect

---

## Next Steps After Testing

1. ✅ Document all test results
2. ✅ Fix any issues found
3. ✅ Retest fixes
4. ✅ Continue bug hunting in other files

---

**Role**: QA_Engineer  
**Status**: Ready for Testing

