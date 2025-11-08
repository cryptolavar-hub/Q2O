# Google Custom Search API Setup - Complete Guide

## 🐛 **Issue: 400 Bad Request Error**

**Error Message**:
```
Google search failed: 400 Client Error: Bad Request
URL: ...&cx=independent-tea-477321-d1&q=...
```

**Problem**: The `cx` parameter (`independent-tea-477321-d1`) is a Google Cloud **project ID**, not a **Custom Search Engine ID**.

---

## ✅ **Solution: Create a Custom Search Engine**

You have the **API key** (correct) but need to create a **Custom Search Engine** to get the **CX ID**.

---

## 📋 **Step-by-Step Fix**

### **Step 1: Verify Your API Key (Already Have This)**

You already have:
```
GOOGLE_SEARCH_API_KEY=AIzaSyBB-YY2DSZeqA0DHqO8G301gJNdtpTLlmA  ✓
```

This is correct! ✅

---

### **Step 2: Create a Custom Search Engine**

1. **Go to**: https://programmablesearchengine.google.com/

2. **Click**: "Add" or "Create" button

3. **Configure**:
   - **Sites to search**: Select **"Search the entire web"**
   - **Name**: Quick2Odoo Research (or any name)
   - **Language**: English

4. **Click**: "Create"

5. **Get your Search Engine ID**:
   - After creation, click on your search engine
   - Go to **"Setup"** or **"Basics"** tab
   - Look for **"Search engine ID"** 
   - It will look like: `0123456789abcdef0:abcdefghij`
   - **Copy this ID**

---

### **Step 3: Update .env File**

Replace the CX value in your `.env`:

```bash
# BEFORE (WRONG - This is a project ID)
GOOGLE_SEARCH_CX=independent-tea-477321-d1

# AFTER (CORRECT - This is a search engine ID)
GOOGLE_SEARCH_CX=0123456789abcdef0:abcdefghij  # Your actual CX from step 2
```

---

### **Step 4: Enable "Search the entire web"**

In the Programmable Search Engine settings:

1. Go to **"Setup"** tab
2. Scroll to **"Search the entire web"**
3. Make sure it's **ON** (enabled)
4. Click **"Update"**

---

### **Step 5: Test**

```bash
python test_duckduckgo_search.py
```

**Expected Output**:
```
INFO - Attempting Google search...
INFO - ✓ Google returned 5 results

✓ SUCCESS: Found 5 results

1. [Result from Google]
   Source: google
```

---

## 🔍 **What a Valid CX Looks Like**

### **Valid Custom Search Engine ID Formats**:
```
# Format 1 (with colon)
0123456789abcdef0:abcdefghij

# Format 2 (longer alphanumeric)
a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5

# Format 3 (with dashes, newer format)
012345678901234567890:abc-def-ghi_jkl
```

### **INVALID** (What you currently have):
```
independent-tea-477321-d1  ← This is a PROJECT ID, not CX
```

---

## 🎯 **Quick Verification**

### **Check if your CX is valid**:

Run this to test the API directly:

```bash
curl "https://www.googleapis.com/customsearch/v1?key=AIzaSyBB-YY2DSZeqA0DHqO8G301gJNdtpTLlmA&cx=YOUR_NEW_CX_HERE&q=test"
```

**If CX is valid**: You'll get JSON results  
**If CX is invalid**: You'll get 400 Bad Request

---

## 📖 **Detailed Instructions**

### **Creating the Search Engine (Screenshots)**

1. **Visit**: https://programmablesearchengine.google.com/controlpanel/all

2. **Click**: Blue **"Add"** button

3. **Fill in**:
   ```
   What do you want to search?
   ○ Search specific sites or pages
   ● Search the entire web                    ← SELECT THIS
   
   Name of the search engine:
   [Quick2Odoo Research]                      ← Any name
   ```

4. **Click**: **"Create"**

5. **Success Page**:
   ```
   Your search engine has been created!
   
   Search engine ID: 0123abc456def789:ghijklmno   ← COPY THIS!
   ```

6. **Copy the ID** and update `.env`:
   ```bash
   GOOGLE_SEARCH_CX=0123abc456def789:ghijklmno
   ```

---

## 🔧 **Alternative: Use Bing Instead**

If you can't get Google working, use Bing:

1. **Get Bing API key**: https://portal.azure.com
2. **Create Bing Search v7 resource**
3. **Copy API key**
4. **Add to .env**:
   ```bash
   BING_SEARCH_API_KEY=your_bing_key_here
   ```

Bing is easier (just one key, no CX needed) and has 1000 free queries/month!

---

## ✅ **Summary**

**Problem**: 
- You have a valid Google API key ✓
- But invalid Custom Search Engine ID ✗

**Solution**:
1. Go to https://programmablesearchengine.google.com/
2. Create a new search engine
3. Select "Search the entire web"
4. Copy the **Search engine ID**
5. Update `.env` with the real CX ID
6. Test again

**The CX should look like**: `0123456789abcdef0:abcdefghij` (with colon)  
**NOT**: `independent-tea-477321-d1` (project ID)

---

**Create the search engine and update your `.env` file!** 🎯

