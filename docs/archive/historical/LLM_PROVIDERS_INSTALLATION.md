# LLM Providers Installation Guide

## Current Status

The warnings you're seeing are **informational only** - they indicate that optional LLM provider packages are not installed:

```
"openai not installed - OpenAI unavailable"
"anthropic not installed - Claude unavailable"
```

**These are NOT errors** - the system works perfectly fine with just Gemini (the primary provider).

## Why These Warnings Appear

The Q2O platform supports **3 LLM providers** with automatic fallback:

1. **Gemini** (Primary) - ✅ Required
2. **OpenAI GPT-4** (Fallback) - ⚠️ Optional
3. **Anthropic Claude** (Tertiary) - ⚠️ Optional

The system checks for all three at startup and logs warnings if optional ones aren't installed. This is normal behavior.

## Should You Install Them?

### **You DON'T need to install them if:**
- ✅ You only want to use Gemini (recommended - 87% cheaper)
- ✅ You're in development/testing phase
- ✅ You want to minimize dependencies

### **You SHOULD install them if:**
- ✅ You want automatic fallback if Gemini fails
- ✅ You want premium quality from GPT-4 or Claude
- ✅ You're in production and need maximum reliability

## How to Install (Optional)

### Option 1: Install Both (Recommended for Production)

```powershell
cd C:\Q2O_Combined
pip install openai anthropic
```

### Option 2: Install Only OpenAI

```powershell
pip install openai
```

### Option 3: Install Only Anthropic

```powershell
pip install anthropic
```

## After Installation

1. **Add API Keys** to `.env` file (see `addon_portal/SETUP_LLM_KEYS.md`):
   ```bash
   OPENAI_API_KEY=sk-your-key-here
   ANTHROPIC_API_KEY=sk-ant-your-key-here
   ```

2. **Restart the API server** for changes to take effect

3. **Warnings will disappear** and providers will be available

## Cost Comparison

| Provider | Cost per Project | Quality |
|----------|------------------|---------|
| Gemini Pro | ~$0.50-1.00 | Excellent |
| GPT-4 | ~$4-8 | Premium |
| Claude | ~$3-6 | Premium |

**Recommendation**: Start with Gemini only. Add others if you need fallback or premium quality.

## Verification

After installation and adding API keys, check the logs on startup:

**Before** (warnings):
```
"openai not installed - OpenAI unavailable"
"anthropic not installed - Claude unavailable"
```

**After** (no warnings, providers initialized):
```
✅ OpenAI initialized
✅ Anthropic initialized
```

## Summary

- ✅ **Warnings are harmless** - system works fine without them
- ✅ **Installation is optional** - only needed for fallback providers
- ✅ **Gemini is sufficient** for most use cases
- ✅ **Install if you want** automatic fallback or premium quality

