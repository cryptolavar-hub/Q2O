# LLM API Keys Setup Guide

## 🔑 **How to Add API Keys to See Them in Configuration Page**

The Configuration page at `http://localhost:3002/llm/configuration` is working correctly, but showing "Not configured" because the API keys haven't been added to the `.env` file yet.

---

## 📝 **Step-by-Step Instructions**

### **Step 1: Open the `.env` File**

```powershell
cd C:\Q2O_Combined\addon_portal
notepad .env
```

### **Step 2: Add These Lines**

Copy and paste these into your `.env` file (replace with your actual keys):

```bash
# ============================================================================
# LLM API KEYS
# ============================================================================

# Google Gemini Pro (Primary - Recommended)
GOOGLE_API_KEY=AIzaSy_YOUR_ACTUAL_GOOGLE_API_KEY_HERE

# OpenAI GPT-4 (Fallback)
OPENAI_API_KEY=sk-YOUR_ACTUAL_OPENAI_API_KEY_HERE

# Anthropic Claude (Tertiary)
ANTHROPIC_API_KEY=sk-ant-YOUR_ACTUAL_ANTHROPIC_API_KEY_HERE

# ============================================================================
# SYSTEM PROMPT
# ============================================================================

Q2O_LLM_SYSTEM_PROMPT="You are an expert software architect and developer for the Q2O platform. Generate production-ready, well-documented code following industry best practices. Prioritize code quality, maintainability, security, and performance. Include proper error handling, type hints, and comprehensive documentation."
```

### **Step 3: Get Your API Keys**

#### **Google Gemini Pro** (Recommended - 87% cheaper than GPT-4)
1. Go to: https://makersuite.google.com/app/apikey
2. Click "Create API Key"
3. Copy the key (starts with `AIzaSy...`)

#### **OpenAI GPT-4** (Optional - Premium quality)
1. Go to: https://platform.openai.com/api-keys
2. Click "+ Create new secret key"
3. Copy the key (starts with `sk-...`)

#### **Anthropic Claude** (Optional - Alternative premium)
1. Go to: https://console.anthropic.com/settings/keys
2. Click "Create Key"
3. Copy the key (starts with `sk-ant-...`)

---

## ✅ **Step 4: Restart Licensing API**

After adding keys to `.env`, restart the Licensing API to load them:

**In your START_ALL menu, press:**
```
3 - Restart Licensing API
```

---

## 🎉 **Step 5: Refresh Configuration Page**

Go to: `http://localhost:3002/llm/configuration`

**You'll now see:**
- ✅ **Google Gemini Pro** with masked key (`AIzaSy...` ✅ Active)
- ✅ **OpenAI GPT-4** with masked key (if added)
- ✅ **Anthropic Claude** with masked key (if added)
- ✅ **System Prompt** populated in read-only box

---

## 💡 **Notes**

**Minimum Requirement:**
- Only **GOOGLE_API_KEY** is required (Gemini is primary provider)
- OpenAI and Claude are optional (fallback providers)

**Cost Estimates:**
- **Gemini Pro**: ~$0.50-1.00 per project
- **GPT-4**: ~$4-8 per project
- **Claude**: ~$3-6 per project

**Recommendation:** Start with Gemini only, add others later if needed!

---

## 🔍 **Verification**

After restart, you can verify the API is reading your keys:

```bash
curl http://localhost:8080/api/llm/config
```

Should return JSON with:
```json
{
  "providers": {
    "gemini": {
      "enabled": true,
      "apiKey": "AIzaSy...123...",
      "model": "gemini-1.5-pro"
    }
  }
}
```

