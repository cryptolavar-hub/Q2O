# Week 1 Implementation - Comprehensive Test Plan

**Date**: November 14, 2025  
**Status**: Ready for Testing  
**Component**: Tenant Portal - Authentication & Project Management

---

## 🎯 Test Objectives

Verify that all Week 1 features are working correctly:
1. ✅ OTP Authentication & Session Management
2. ✅ Project Management (CRUD operations)
3. ✅ Route Protection
4. ✅ Error Handling
5. ✅ Session Expiration

---

## 📋 Test Environment Setup

### **Prerequisites**

1. **Backend API Running**:
   ```bash
   cd addon_portal
   # Ensure .env file exists with DB_DSN configured
   # Start FastAPI server on port 8080
   ```

2. **Tenant Portal Running**:
   ```bash
   cd addon_portal/apps/tenant-portal
   npm install
   npm run dev
   # Should run on http://localhost:3000
   ```

3. **Database Setup**:
   - PostgreSQL running on localhost:5432
   - Database `q2o` exists
   - At least one tenant exists in database

4. **Test Tenant**:
   - Create a test tenant in database (or use existing)
   - Note the tenant slug (e.g., "demo", "test")

---

## 🧪 Test Cases

### **TEST GROUP 1: Authentication Flow**

#### **TC-1.1: Login Page Display**
**Steps**:
1. Navigate to `http://localhost:3000`
2. Should redirect to `/login`

**Expected**:
- ✅ Login page displays
- ✅ "Tenant Slug" input field visible
- ✅ "Request OTP" button visible
- ✅ Navigation menu visible
- ✅ Breadcrumb shows "Login"

**Status**: ⬜ Not Tested

---

#### **TC-1.2: OTP Generation - Valid Tenant**
**Steps**:
1. Navigate to `/login`
2. Enter valid tenant slug (e.g., "demo")
3. Click "Request OTP"

**Expected**:
- ✅ OTP code is generated
- ✅ Page transitions to OTP entry step
- ✅ OTP input field appears
- ✅ Countdown timer shows (10 minutes)
- ✅ "Back" button appears
- ✅ No error messages

**Status**: ⬜ Not Tested

---

#### **TC-1.3: OTP Generation - Invalid Tenant**
**Steps**:
1. Navigate to `/login`
2. Enter invalid tenant slug (e.g., "nonexistent")
3. Click "Request OTP"

**Expected**:
- ✅ Error message displays: "Tenant not found" or similar
- ✅ Stays on tenant slug entry step
- ✅ OTP input does not appear

**Status**: ⬜ Not Tested

---

#### **TC-1.4: OTP Verification - Valid OTP**
**Steps**:
1. Complete TC-1.2 (get OTP)
2. Enter the OTP code received
3. Click "Verify OTP"

**Expected**:
- ✅ OTP is verified successfully
- ✅ Session token is stored
- ✅ Redirects to `/projects` page
- ✅ User is authenticated
- ✅ Navigation shows authenticated state

**Status**: ⬜ Not Tested

---

#### **TC-1.5: OTP Verification - Invalid OTP**
**Steps**:
1. Complete TC-1.2 (get OTP)
2. Enter incorrect OTP code (e.g., "000000")
3. Click "Verify OTP"

**Expected**:
- ✅ Error message displays: "Invalid OTP code"
- ✅ Stays on OTP entry step
- ✅ Can retry with correct OTP
- ✅ OTP countdown continues

**Status**: ⬜ Not Tested

---

#### **TC-1.6: OTP Expiration**
**Steps**:
1. Complete TC-1.2 (get OTP)
2. Wait 10+ minutes (or manually expire OTP)
3. Try to verify expired OTP

**Expected**:
- ✅ Error message: "OTP expired"
- ✅ Redirects back to tenant slug entry
- ✅ Must request new OTP

**Status**: ⬜ Not Tested

---

#### **TC-1.7: Session Persistence**
**Steps**:
1. Complete TC-1.4 (successful login)
2. Refresh the page
3. Navigate to different pages

**Expected**:
- ✅ User remains authenticated after refresh
- ✅ Can navigate to `/projects` without re-login
- ✅ Session token persists in localStorage

**Status**: ⬜ Not Tested

---

#### **TC-1.8: Logout**
**Steps**:
1. Complete TC-1.4 (successful login)
2. Find and click logout button (if available)
3. Or manually clear session

**Expected**:
- ✅ Session is cleared
- ✅ Redirects to `/login`
- ✅ Cannot access protected routes
- ✅ localStorage is cleared

**Status**: ⬜ Not Tested

---

### **TEST GROUP 2: Route Protection**

#### **TC-2.1: Protected Route - Not Authenticated**
**Steps**:
1. Ensure not logged in (clear localStorage)
2. Navigate directly to `/projects`

**Expected**:
- ✅ Redirects to `/login`
- ✅ Redirect parameter includes intended destination
- ✅ After login, redirects back to `/projects`

**Status**: ⬜ Not Tested

---

#### **TC-2.2: Protected Route - Authenticated**
**Steps**:
1. Complete TC-1.4 (successful login)
2. Navigate to `/projects`

**Expected**:
- ✅ Page loads successfully
- ✅ No redirect to login
- ✅ Projects list displays (or empty state)

**Status**: ⬜ Not Tested

---

#### **TC-2.3: Session Expiration - 30 Min Idle**
**Steps**:
1. Complete TC-1.4 (successful login)
2. Wait 30+ minutes without activity
3. Try to access `/projects`

**Expected**:
- ✅ Session expires
- ✅ Redirects to `/login`
- ✅ Error message: "Session expired"

**Status**: ⬜ Not Tested (Manual - requires waiting)

---

#### **TC-2.4: Session Expiration - 24 Hour Max**
**Steps**:
1. Complete TC-1.4 (successful login)
2. Manually set session expiration to past time
3. Try to access protected route

**Expected**:
- ✅ Session expires
- ✅ Redirects to `/login`
- ✅ Must re-authenticate

**Status**: ⬜ Not Tested (Manual - requires time manipulation)

---

### **TEST GROUP 3: Project Management - List**

#### **TC-3.1: Projects List - Empty State**
**Steps**:
1. Complete TC-1.4 (successful login)
2. Navigate to `/projects`
3. Ensure tenant has no projects

**Expected**:
- ✅ Projects list page loads
- ✅ Empty state message: "No projects found"
- ✅ "Create Your First Project" button visible
- ✅ Navigation and breadcrumbs visible

**Status**: ⬜ Not Tested

---

#### **TC-3.2: Projects List - With Projects**
**Steps**:
1. Complete TC-1.4 (successful login)
2. Create at least 3 projects (via TC-4.1)
3. Navigate to `/projects`

**Expected**:
- ✅ Projects list displays all projects
- ✅ Project cards show: name, client, status, dates
- ✅ Status badges have correct colors
- ✅ "View" and "Edit" buttons on each card
- ✅ Pagination works (if >20 projects)

**Status**: ⬜ Not Tested

---

#### **TC-3.3: Projects List - Search**
**Steps**:
1. Complete TC-3.2 (projects list with data)
2. Enter search term in search box
3. Click "Search" or press Enter

**Expected**:
- ✅ Results filter by search term
- ✅ Searches project name and client name
- ✅ Case-insensitive search
- ✅ Empty results show appropriate message

**Status**: ⬜ Not Tested

---

#### **TC-3.4: Projects List - Status Filter**
**Steps**:
1. Complete TC-3.2 (projects list with data)
2. Click status filter button (e.g., "Active")
3. Verify filtered results

**Expected**:
- ✅ Only projects with selected status display
- ✅ Filter button is highlighted
- ✅ "All" button clears filter
- ✅ Multiple status filters work correctly

**Status**: ⬜ Not Tested

---

#### **TC-3.5: Projects List - Pagination**
**Steps**:
1. Create 25+ projects
2. Navigate to `/projects`
3. Test pagination controls

**Expected**:
- ✅ Shows "Page 1 of X" correctly
- ✅ "Previous" button disabled on first page
- ✅ "Next" button disabled on last page
- ✅ Clicking "Next" loads next page
- ✅ Clicking "Previous" loads previous page
- ✅ Page size selector works (10/25/50)

**Status**: ⬜ Not Tested

---

### **TEST GROUP 4: Project Management - Create**

#### **TC-4.1: Create Project - Valid Data**
**Steps**:
1. Complete TC-1.4 (successful login)
2. Navigate to `/projects/new`
3. Fill in form:
   - Name: "Test Project"
   - Client: "Test Client"
   - Description: "Test description"
   - Objectives: "Test objectives"
4. Click "Create Project"

**Expected**:
- ✅ Project is created successfully
- ✅ Redirects to project detail page
- ✅ Project appears in projects list
- ✅ All fields saved correctly

**Status**: ⬜ Not Tested

---

#### **TC-4.2: Create Project - Required Field Validation**
**Steps**:
1. Navigate to `/projects/new`
2. Leave "Project Name" empty
3. Click "Create Project"

**Expected**:
- ✅ Form validation prevents submission
- ✅ Error message: "Project name is required"
- ✅ "Create Project" button disabled
- ✅ Can still fill in other fields

**Status**: ⬜ Not Tested

---

#### **TC-4.3: Create Project - Cancel**
**Steps**:
1. Navigate to `/projects/new`
2. Fill in some data
3. Click "Cancel"

**Expected**:
- ✅ Redirects to `/projects` list
- ✅ No project is created
- ✅ Form data is not saved

**Status**: ⬜ Not Tested

---

#### **TC-4.4: Create Project - Session Expired**
**Steps**:
1. Start creating project
2. Manually expire session (clear token)
3. Submit form

**Expected**:
- ✅ Error message: "Session expired"
- ✅ Redirects to `/login`
- ✅ No project created

**Status**: ⬜ Not Tested

---

### **TEST GROUP 5: Project Management - Detail**

#### **TC-5.1: Project Detail - Display**
**Steps**:
1. Complete TC-4.1 (create project)
2. Click "View" on project card
3. Or navigate to `/projects/{id}`

**Expected**:
- ✅ Project detail page loads
- ✅ All project information displays:
  - Name, client, status, description, objectives
  - Created/updated timestamps
  - Activation code ID (if linked)
- ✅ "Edit" and "Delete" buttons visible
- ✅ Breadcrumb shows: Projects > Project Name

**Status**: ⬜ Not Tested

---

#### **TC-5.2: Project Detail - Not Found**
**Steps**:
1. Complete TC-1.4 (successful login)
2. Navigate to `/projects/invalid-id-12345`

**Expected**:
- ✅ Error message: "Project not found"
- ✅ "Back to Projects" button visible
- ✅ No crash or error page

**Status**: ⬜ Not Tested

---

### **TEST GROUP 6: Project Management - Edit**

#### **TC-6.1: Edit Project - Update Fields**
**Steps**:
1. Complete TC-4.1 (create project)
2. Navigate to project detail
3. Click "Edit"
4. Update fields:
   - Change name
   - Change status to "active"
   - Update description
5. Click "Save Changes"

**Expected**:
- ✅ Form pre-fills with existing data
- ✅ Updates save successfully
- ✅ Redirects to project detail page
- ✅ Updated data displays correctly
- ✅ Updated timestamp changes

**Status**: ⬜ Not Tested

---

#### **TC-6.2: Edit Project - Cancel**
**Steps**:
1. Navigate to edit page
2. Make changes
3. Click "Cancel"

**Expected**:
- ✅ Redirects to project detail page
- ✅ No changes saved
- ✅ Original data unchanged

**Status**: ⬜ Not Tested

---

#### **TC-6.3: Edit Project - Validation**
**Steps**:
1. Navigate to edit page
2. Clear "Project Name" field
3. Click "Save Changes"

**Expected**:
- ✅ Form validation prevents submission
- ✅ Error message: "Project name is required"
- ✅ "Save Changes" button disabled

**Status**: ⬜ Not Tested

---

### **TEST GROUP 7: Project Management - Delete**

#### **TC-7.1: Delete Project - With Confirmation**
**Steps**:
1. Complete TC-4.1 (create project)
2. Navigate to project detail
3. Click "Delete"
4. Confirm deletion in dialog

**Expected**:
- ✅ Confirmation dialog appears
- ✅ Shows project name in dialog
- ✅ "Cancel" and "Delete" buttons visible
- ✅ Project is deleted after confirmation
- ✅ Redirects to `/projects` list
- ✅ Project no longer appears in list

**Status**: ⬜ Not Tested

---

#### **TC-7.2: Delete Project - Cancel**
**Steps**:
1. Navigate to project detail
2. Click "Delete"
3. Click "Cancel" in dialog

**Expected**:
- ✅ Dialog closes
- ✅ Project is NOT deleted
- ✅ Stays on project detail page
- ✅ Project still exists

**Status**: ⬜ Not Tested

---

#### **TC-7.3: Delete Project - Error Handling**
**Steps**:
1. Navigate to project detail
2. Manually expire session
3. Try to delete project

**Expected**:
- ✅ Error message: "Session expired"
- ✅ Redirects to `/login`
- ✅ Project is NOT deleted

**Status**: ⬜ Not Tested

---

### **TEST GROUP 8: Error Handling & Edge Cases**

#### **TC-8.1: Network Error**
**Steps**:
1. Complete TC-1.4 (successful login)
2. Stop backend API
3. Try to access `/projects`

**Expected**:
- ✅ Error message displays
- ✅ User-friendly error (not technical)
- ✅ Page doesn't crash
- ✅ Can retry after backend restarts

**Status**: ⬜ Not Tested

---

#### **TC-8.2: Invalid API Response**
**Steps**:
1. Mock backend to return invalid JSON
2. Try to load projects list

**Expected**:
- ✅ Error handling catches invalid response
- ✅ Error message displays
- ✅ Page doesn't crash

**Status**: ⬜ Not Tested

---

#### **TC-8.3: Concurrent Requests**
**Steps**:
1. Complete TC-1.4 (successful login)
2. Rapidly click multiple buttons
3. Make multiple API calls simultaneously

**Expected**:
- ✅ No race conditions
- ✅ All requests complete correctly
- ✅ UI updates appropriately
- ✅ No duplicate data

**Status**: ⬜ Not Tested

---

### **TEST GROUP 9: UI/UX**

#### **TC-9.1: Navigation Menu**
**Steps**:
1. Navigate through all pages
2. Check navigation menu on each page

**Expected**:
- ✅ Navigation menu visible on all pages
- ✅ Links work correctly
- ✅ Active page highlighted
- ✅ Responsive on mobile

**Status**: ⬜ Not Tested

---

#### **TC-9.2: Breadcrumbs**
**Steps**:
1. Navigate through all pages
2. Check breadcrumb trail

**Expected**:
- ✅ Breadcrumbs visible on all pages
- ✅ Correct hierarchy displayed
- ✅ Clickable links work
- ✅ Current page shown as non-link

**Status**: ⬜ Not Tested

---

#### **TC-9.3: Loading States**
**Steps**:
1. Navigate to pages that load data
2. Observe loading indicators

**Expected**:
- ✅ Loading spinner/text appears during API calls
- ✅ Loading state clears when data loads
- ✅ No flickering or layout shifts

**Status**: ⬜ Not Tested

---

#### **TC-9.4: Responsive Design**
**Steps**:
1. Test on desktop (1920x1080)
2. Test on tablet (768x1024)
3. Test on mobile (375x667)

**Expected**:
- ✅ Layout adapts to screen size
- ✅ All buttons/inputs accessible
- ✅ Text readable
- ✅ No horizontal scrolling

**Status**: ⬜ Not Tested

---

## 📊 Test Execution Checklist

### **Pre-Test Setup**
- [ ] Backend API running on port 8080
- [ ] Tenant Portal running on port 3000
- [ ] Database accessible
- [ ] Test tenant exists in database
- [ ] Browser console open (for errors)

### **Test Execution**
- [ ] Complete all Test Group 1 (Authentication)
- [ ] Complete all Test Group 2 (Route Protection)
- [ ] Complete all Test Group 3 (Project List)
- [ ] Complete all Test Group 4 (Project Create)
- [ ] Complete all Test Group 5 (Project Detail)
- [ ] Complete all Test Group 6 (Project Edit)
- [ ] Complete all Test Group 7 (Project Delete)
- [ ] Complete all Test Group 8 (Error Handling)
- [ ] Complete all Test Group 9 (UI/UX)

### **Post-Test**
- [ ] Document any bugs found
- [ ] Verify all critical paths work
- [ ] Check browser console for errors
- [ ] Verify no sensitive data in console logs

---

## 🐛 Bug Reporting Template

If bugs are found, document using this template:

```
**Bug ID**: BUG-001
**Test Case**: TC-X.X
**Severity**: Critical / High / Medium / Low
**Steps to Reproduce**:
1. ...
2. ...
3. ...

**Expected Behavior**:
...

**Actual Behavior**:
...

**Screenshots**:
(if applicable)

**Browser/OS**:
...

**Console Errors**:
...
```

---

## ✅ Pass Criteria

Week 1 implementation **PASSES** if:
- ✅ All Test Groups 1-7 pass (critical functionality)
- ✅ No critical bugs (data loss, security issues)
- ✅ Authentication flow works end-to-end
- ✅ All CRUD operations work correctly
- ✅ Error handling works appropriately
- ✅ UI is functional (minor styling issues acceptable)

Week 1 implementation **FAILS** if:
- ❌ Authentication doesn't work
- ❌ Projects cannot be created/edited/deleted
- ❌ Session management broken
- ❌ Critical security issues
- ❌ Data loss occurs

---

## 📝 Test Results Summary

**Test Date**: _______________  
**Tester**: _______________  
**Environment**: _______________

**Results**:
- Total Test Cases: 35
- Passed: ___
- Failed: ___
- Blocked: ___
- Not Tested: ___

**Critical Bugs Found**: ___
**High Priority Bugs**: ___
**Medium Priority Bugs**: ___
**Low Priority Bugs**: ___

**Overall Status**: ⬜ PASS ⬜ FAIL ⬜ NEEDS FIXES

**Notes**:
_________________________________________________
_________________________________________________
_________________________________________________

---

**End of Test Plan**

