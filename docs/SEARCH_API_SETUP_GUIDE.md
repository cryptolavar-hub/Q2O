# Search API Setup Guide - ResearcherAgent

## 🎯 Problem: DuckDuckGo Rate Limiting

DuckDuckGo has **very aggressive rate limiting and bot detection**. While the `duckduckgo-search` library is free and requires no API keys, it frequently returns rate limit errors:

```
DuckDuckGoSearchException: Ratelimit
```

**This is NOT a bug** - DuckDuckGo actively blocks automated searches to prevent abuse.

---

## ✅ Solution: Configure Google or Bing API Keys

For **reliable, production-ready** research capabilities, configure paid search APIs:

| Provider | Free Tier | Paid Pricing | Setup Time | Reliability |
|----------|-----------|--------------|------------|-------------|
| **Google** | 100/day | $5 per 1000 | ~10 min | ⭐⭐⭐⭐⭐ Excellent |
| **Bing** | 1000/month | $3 per 1000 | ~5 min | ⭐⭐⭐⭐⭐ Excellent |
| DuckDuckGo | Unlimited | Free | 0 min | ⭐⭐ Poor (rate limited) |

---

## 🔧 Option 1: Google Custom Search API (Recommended)

### **Step 1: Get Google API Key**

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select existing)
3. Enable **Custom Search API**:
   - Navigate to **APIs & Services** → **Library**
   - Search for "Custom Search API"
   - Click **Enable**
4. Create API Key:
   - Go to **APIs & Services** → **Credentials**
   - Click **Create Credentials** → **API Key**
   - Copy the API key

### **Step 2: Create Custom Search Engine**

1. Go to [Programmable Search Engine](https://programmablesearchengine.google.com/)
2. Click **Add** to create a new search engine
3. Configure:
   - **Sites to search**: Select "Search the entire web"
   - **Name**: Quick2Odoo Research
4. Click **Create**
5. Copy the **Search engine ID** (cx parameter)

### **Step 3: Add to .env**

```bash
# .env
GOOGLE_SEARCH_API_KEY=AIzaSyAbCdEfGhIjKlMnOpQrStUvWxYz1234567
GOOGLE_SEARCH_CX=0123456789abcdefg:hijklmnop
```

### **Pricing**

- **Free Tier**: 100 queries per day
- **Paid**: $5 per 1,000 queries (after free tier)
- **Good for**: Development, testing, production

---

## 🔧 Option 2: Bing Search API

### **Step 1: Get Bing API Key**

1. Go to [Azure Portal](https://portal.azure.com/)
2. Create a new **Bing Search v7** resource:
   - Search for "Bing Search"
   - Click **Create**
   - Select **Bing Search v7**
3. Configure:
   - **Resource group**: Create new or use existing
   - **Region**: Choose closest to you
   - **Pricing tier**: F1 (Free) or S1 ($3/1000 queries)
4. Click **Create**
5. After deployment, go to resource → **Keys and Endpoint**
6. Copy **Key 1** or **Key 2**

### **Step 2: Add to .env**

```bash
# .env
BING_SEARCH_API_KEY=1234567890abcdef1234567890abcdef
```

### **Pricing**

- **Free Tier (F1)**: 1,000 transactions per month
- **S1**: $3 per 1,000 transactions
- **Good for**: Production, high volume

---

## 🔧 Option 3: DuckDuckGo (Free but Unreliable)

### **Configuration**

No configuration needed - this is the **default fallback**.

### **Pros**
- ✅ Free
- ✅ No API key required
- ✅ No registration

### **Cons**
- ❌ Frequent rate limiting
- ❌ IP-based blocking
- ❌ Unreliable for production
- ❌ May fail completely

### **When to Use**
- Quick testing
- Personal development
- Low-volume usage
- When API costs are a concern

### **Rate Limit Mitigation (Already Implemented)**

We've added retry logic to help with DuckDuckGo:
- **3 retry attempts** with exponential backoff
- **2-6 second delays** between retries
- **Increased timeout** to 20 seconds
- **Region parameter** to reduce bot detection

**However**, this only helps slightly. You'll still hit rate limits frequently.

---

## 🚀 Testing Your Configuration

### **Test Script**

```bash
# After configuring API keys in .env
python test_duckduckgo_search.py
```

### **Expected Results**

#### **With Google/Bing Configured** ✅
```
======================================================================
Testing DuckDuckGo Search
======================================================================

Query: Stripe billing setup with pricing tiers
----------------------------------------------------------------------
INFO - Searching for: 'Stripe billing setup with pricing tiers' (requesting 5 results)
INFO - Attempting Google search...
INFO - ✓ Google returned 5 results

✓ SUCCESS: Found 5 results

1. Stripe Pricing - Billing and subscription management
   URL: https://stripe.com/docs/billing
   Source: google
...
```

#### **With Only DuckDuckGo (Free)** ⚠️
```
INFO - Google API not configured, skipping
INFO - Bing API not configured, skipping
INFO - Falling back to DuckDuckGo search (free, no API key)...
WARNING - DuckDuckGo rate limit hit on attempt 1/3
INFO - Retry attempt 2/3 after 4s delay...
WARNING - DuckDuckGo rate limit hit on attempt 2/3
INFO - Retry attempt 3/3 after 6s delay...
ERROR - DuckDuckGo rate limit: All retries exhausted
💡 Tip: Configure Google/Bing API keys for better reliability

❌ FAILED: No results returned
```

---

## 💡 Recommendations

### **For Development**
- Use **Google Free Tier** (100 queries/day)
- Sufficient for testing and development
- Cost: $0

### **For Production**
- Use **Google or Bing Paid Tier**
- Reliable, fast, no rate limits
- Cost: ~$5-15/month (typical usage)

### **For Budget-Conscious**
- Use **Bing Free Tier** (1,000/month)
- Supplement with DuckDuckGo as fallback
- Cost: $0

### **Multi-Provider Strategy (Best)**
Configure ALL three:
1. **Google** (primary, fast, reliable)
2. **Bing** (secondary, good failover)
3. **DuckDuckGo** (last resort, free)

The ResearcherAgent will automatically use them in order of preference.

---

## 📊 Cost Comparison

### **Monthly Usage Estimate**

| Usage Level | Queries/Month | Google Cost | Bing Cost | DDG Cost |
|-------------|---------------|-------------|-----------|----------|
| **Light** (50/day) | 1,500 | $0 (free tier) | $0 (free tier) | $0 |
| **Medium** (200/day) | 6,000 | $25 | $15 | $0* |
| **Heavy** (1000/day) | 30,000 | $145 | $87 | $0* |

*DuckDuckGo will likely fail frequently at higher volumes

---

## 🔐 Security Best Practices

### **Protect Your API Keys**

1. **NEVER commit .env to Git**
   ```bash
   # .gitignore already includes:
   .env
   .env.local
   ```

2. **Use environment variables in production**
   ```bash
   # In production server
   export GOOGLE_SEARCH_API_KEY="your_key_here"
   export GOOGLE_SEARCH_CX="your_cx_here"
   ```

3. **Rotate keys regularly**
   - Every 90 days (recommended)
   - Immediately if exposed

4. **Restrict API key usage**
   - In Google Cloud Console: Add IP restrictions
   - In Azure: Use managed identities when possible

---

## 🐛 Troubleshooting

### **"Google search failed: 403"**
- **Cause**: API key not valid or API not enabled
- **Fix**: Check API key, ensure Custom Search API is enabled

### **"Bing search failed: 401"**
- **Cause**: Invalid API key
- **Fix**: Verify key from Azure portal, check it's not expired

### **"DuckDuckGo Ratelimit"**
- **Cause**: Too many requests or IP blocked
- **Fix**: 
  - Wait 10-30 minutes
  - Use VPN (temporary)
  - Configure Google/Bing API keys (permanent)

### **"All search providers failed"**
- **Cause**: All APIs are rate limited or misconfigured
- **Fix**: 
  - Check .env file is loaded (`python-dotenv`)
  - Verify API keys are correct
  - Check network connectivity
  - Review logs for specific errors

---

## 📚 Additional Resources

### **Google Custom Search**
- [Overview](https://developers.google.com/custom-search/v1/overview)
- [Pricing](https://developers.google.com/custom-search/v1/overview#pricing)
- [API Reference](https://developers.google.com/custom-search/v1/reference/rest/v1/cse/list)

### **Bing Search API**
- [Overview](https://www.microsoft.com/en-us/bing/apis/bing-web-search-api)
- [Pricing](https://www.microsoft.com/en-us/bing/apis/pricing)
- [Documentation](https://learn.microsoft.com/en-us/bing/search-apis/bing-web-search/overview)

### **DuckDuckGo Search**
- [Library GitHub](https://github.com/deedy5/duckduckgo_search)
- [Known Issues](https://github.com/deedy5/duckduckgo_search/issues)

---

## ✅ Quick Setup Checklist

- [ ] Decide on search provider (Google/Bing/Both)
- [ ] Create API keys (Google and/or Bing)
- [ ] Copy `env.example` to `.env`
- [ ] Add API keys to `.env`
- [ ] Test with `python test_duckduckgo_search.py`
- [ ] Verify successful search results
- [ ] Configure billing alerts (for paid tiers)
- [ ] Set up key rotation schedule

---

**Recommendation**: Start with Google free tier (100/day) for development, then upgrade to paid or add Bing for production. Avoid relying solely on DuckDuckGo for anything beyond testing.

