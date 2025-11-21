# Profile Page Testing Checklist

**Date**: November 20, 2025  
**Feature**: Tenant Profile Page (`/profile`)  
**Status**: Ready for Testing

---

## ✅ Pre-Testing Requirements

- [ ] Backend API is running on port 8080
- [ ] Tenant Portal is running on port 3000
- [ ] You have a valid tenant account with OTP authentication
- [ ] You are logged in to the Tenant Portal

---

## 🧪 Testing Checklist

### **1. Navigation & Access**

- [ ] Profile link appears in navigation menu (desktop)
- [ ] Profile link appears in mobile menu
- [ ] Clicking Profile link navigates to `/profile`
- [ ] Logout button appears in navigation (desktop)
- [ ] Logout button appears in mobile menu
- [ ] Page loads without errors

### **2. Profile Display (Read-Only Mode)**

- [ ] Tenant name is displayed correctly
- [ ] Slug is displayed (read-only, grayed out)
- [ ] Email is displayed (or "Not set" if empty)
- [ ] Phone number is displayed (or "Not set" if empty)
- [ ] Subscription plan name is displayed
- [ ] Subscription status badge is displayed with correct color:
  - [ ] Green for "active"
  - [ ] Blue for "trialing"
  - [ ] Yellow for "past_due"
  - [ ] Red for "canceled"/"unpaid"/"suspended"
- [ ] Monthly run quota progress bar displays correctly
  - [ ] Shows usage/quota numbers
  - [ ] Progress bar color: green (<70%), yellow (70-90%), red (≥90%)
  - [ ] Percentage is calculated correctly
- [ ] Activation codes progress bar displays correctly
  - [ ] Shows used/total numbers
  - [ ] Shows remaining codes count
  - [ ] Progress bar color: blue (<70%), yellow (70-90%), red (≥90%)
- [ ] Branding preview section appears (if logo or color is set)
  - [ ] Logo displays correctly (or hides if broken URL)
  - [ ] Primary color preview shows correct color
  - [ ] Color hex code is displayed

### **3. Edit Functionality**

- [ ] "Edit Profile" button is visible
- [ ] Clicking "Edit Profile" switches to edit mode
- [ ] In edit mode:
  - [ ] Tenant name field is editable
  - [ ] Email field is editable
  - [ ] Phone number field is editable
  - [ ] Logo URL field appears and is editable
  - [ ] Primary color picker appears and works
  - [ ] Primary color text input accepts hex codes
  - [ ] Custom domain field appears and is editable
  - [ ] Slug field remains read-only (grayed out)
- [ ] "Save Changes" and "Cancel" buttons appear
- [ ] Making changes and clicking "Save Changes":
  - [ ] Loading state shows ("Saving...")
  - [ ] Success: Profile updates and returns to read-only mode
  - [ ] Updated values are displayed correctly
  - [ ] No errors occur
- [ ] Making changes and clicking "Cancel":
  - [ ] Returns to read-only mode
  - [ ] Changes are discarded
  - [ ] Original values are restored

### **4. Validation & Error Handling**

- [ ] Empty tenant name shows validation error (if required)
- [ ] Invalid email format shows validation error
- [ ] Invalid color hex code shows validation error
- [ ] Network errors are displayed to user
- [ ] API errors are displayed in error message box
- [ ] Error messages are user-friendly

### **5. Logout Functionality**

- [ ] Clicking "Logout" button:
  - [ ] Session is invalidated on backend
  - [ ] Local storage is cleared
  - [ ] User is redirected to `/login`
  - [ ] Cannot access `/profile` after logout (redirects to login)

### **6. Session Protection**

- [ ] Accessing `/profile` without session redirects to login
- [ ] Expired session redirects to login
- [ ] SessionGuard component works correctly

### **7. Responsive Design**

- [ ] Desktop view displays correctly (all cards visible)
- [ ] Mobile view displays correctly (stacked layout)
- [ ] Mobile menu works correctly
- [ ] All buttons are clickable on mobile
- [ ] Forms are usable on mobile

### **8. Edge Cases**

- [ ] Profile with no email/phone displays "Not set"
- [ ] Profile with no logo/color hides branding preview
- [ ] Profile with 0 quota shows 0% usage
- [ ] Profile with 100% usage shows red progress bar
- [ ] Profile with no activation codes shows 0/0

---

## 🐛 Known Issues / Notes

- None currently

---

## 📝 Test Results

**Tester**: _________________  
**Date**: _________________  
**Status**: ⬜ Pass ⬜ Fail ⬜ Partial

**Issues Found**:
1. 
2. 
3. 

**Notes**:
- 

---

## 🔄 Next Steps After Testing

1. Fix any issues found during testing
2. Proceed to Billing page implementation
3. Add Stripe integration for payments

