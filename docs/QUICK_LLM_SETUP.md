# Quick LLM Setup Guide

**Get your LLM integration working in 5 minutes!**

---

## Step 1: Get API Keys

### **Gemini (Recommended - Cheapest!)**

1. Go to: https://makersuite.google.com/app/apikey
2. Click "Create API Key"
3. Copy the key (starts with `AIzaSy...`)
4. **Cost**: $0.52 per 100K tokens (87% cheaper than GPT-4!)

### **OpenAI GPT-4 (Optional - Premium Quality)**

1. Go to: https://platform.openai.com/api-keys
2. Click "Create new secret key"
3. Copy the key (starts with `sk-...`)
4. **Cost**: $4.00 per 100K tokens

### **Anthropic Claude (Optional - Alternative)**

1. Go to: https://console.anthropic.com/account/keys
2. Click "Create Key"
3. Copy the key (starts with `sk-ant-...`)
4. **Cost**: ~$3.00 per 100K tokens

**Recommendation**: Start with **Gemini only** - it's cheapest and works great!

---

## Step 2: Configure Q2O

### **Option A: Create .env file** (Recommended)

```bash
# In Q2O_Combined folder
cd C:\Q2O_Combined

# Copy example config
copy env.llm.example.txt .env

# Edit .env and add your keys
notepad .env
```

**Add to .env**:
```bash
# LLM API Keys (add at least one)
GOOGLE_API_KEY=AIzaSy...your_actual_gemini_key_here
# OPENAI_API_KEY=sk-...your_openai_key  # Optional
# ANTHROPIC_API_KEY=sk-ant-...your_claude_key  # Optional

# Enable LLM Integration
Q2O_USE_LLM=true

# Budget (default: $1000/month)
Q2O_LLM_MONTHLY_BUDGET=1000

# Primary Provider (gemini, openai, or anthropic)
Q2O_LLM_PRIMARY_PROVIDER=gemini
```

### **Option B: Set Environment Variables** (Windows)

```powershell
$env:GOOGLE_API_KEY="AIzaSy...your_key"
$env:Q2O_USE_LLM="true"
$env:Q2O_LLM_PRIMARY_PROVIDER="gemini"
$env:Q2O_LLM_MONTHLY_BUDGET="1000"
```

---

## Step 3: Test It!

### **Quick Connection Test**

```bash
python utils/test_llm_connections.py
```

**Expected Output**:
```
Testing LLM API Connections
============================
[OK] Gemini: Connected successfully!
[OK] Configuration loaded
[OK] Ready to generate!
```

### **Simple Generation Test**

```bash
python demos/test_llm_generation.py
```

This will:
1. Generate a simple Python function using LLM
2. Validate the code (95%+ quality)
3. Show cost and tokens used
4. Learn a template for future use!

---

## Step 4: Verify Learning

After running the test, check:

```bash
# Check learned templates database
python -c "from utils.template_learning_engine import get_template_learning_engine; engine = get_template_learning_engine(); print(engine.get_learning_stats())"
```

**Output**:
```python
{
  'total_templates': 1,
  'total_uses': 1,
  'cost_saved': 0.0,  # Will increase as templates are reused!
  'avg_quality': 95.0
}
```

---

## Troubleshooting

### **"GOOGLE_API_KEY not set"**
- Make sure `.env` file is in `Q2O_Combined` folder
- Check no typos in key
- Restart terminal/PowerShell

### **"Invalid API key"**
- Verify key is correct
- Check key has permissions enabled in Google Cloud Console
- For OpenAI: Make sure you have credits

### **"Module not found: google.generativeai"**
```bash
pip install google-generativeai openai anthropic
```

---

## What's Next?

Once LLM is working:

1. **Use CoderAgent** - Generates code for ANY technology
2. **Watch it learn** - Templates auto-created, costs drop to $0
3. **Monitor costs** - Check `llm_costs.db` for spending
4. **Explore Phase 2** - Enhance other agents (Researcher, Orchestrator)
5. **Phase 3** - Admin Dashboard UI for visual management

---

## Cost Expectations

### **First Month** (Learning Phase)
```
10 projects × $0.52 = $5.20
Templates learned: 8-10
```

### **Month 2+** (Reuse Phase)
```
50 projects:
- 40 use learned templates = $0
- 10 new tech = $5.20
Total: $5.20 (vs $26 without learning!)
```

### **Month 6+** (Mature Phase)
```
100 projects:
- 95 use learned templates = $0
- 5 new tech = $2.60
Total: $2.60 (vs $52 without learning!)
Savings: 95%!
```

---

## Security Notes

- ✅ Never commit `.env` file to Git (already in `.gitignore`)
- ✅ API keys are encrypted in memory
- ✅ Cost monitoring prevents runaway spending
- ✅ Budget limits auto-disable LLM at threshold

---

**You're ready to generate code for ANY technology!** 🚀

Need help? Check `docs/LLM_INTEGRATION_PHASE1_COMPLETE.md` for full details.

