# LLM Implementation Testing Guide

## Quick Testing Checklist

### 1. Model Names Display Test
**Goal**: Verify dashboard shows actual model names (e.g., "Gemini 2.5 Flash" instead of "Gemini 1.5 Pro")

**Steps**:
1. Start the API server
2. Navigate to `/llm` (LLM Management Overview)
3. Check the provider cards:
   - Gemini card should show actual model name (likely "Gemini 2.5 Flash")
   - OpenAI card should show actual model name
   - Claude card should show actual model name
4. Check the "Provider Usage Details" table - model names should match

**Expected Result**: 
- Model names reflect actual configured models
- Names are formatted nicely (e.g., "Gemini 2.5 Flash" not "gemini-2.5-flash")

**If Failed**: Check browser console for errors, verify API response includes `model` field in `providerBreakdown`

---

### 2. LLM Usage Logs Endpoint Test
**Goal**: Verify `/api/llm/logs` endpoint works (even if empty)

**Steps**:
1. Start the API server
2. Test endpoint directly:
   ```bash
   curl http://localhost:8080/api/llm/logs?range=7days
   ```
   Or use browser: `http://localhost:8080/api/llm/logs?range=7days`
3. Should return JSON with structure:
   ```json
   {
     "logs": [],
     "total": 0,
     "page": 1,
     "page_size": 50,
     "total_pages": 0
   }
   ```

**Expected Result**: 
- Endpoint returns 200 OK
- JSON structure is correct
- No errors in API logs

**If Failed**: Check API logs, verify database connection, check if table exists

---

### 3. Database Migration Test
**Goal**: Verify migration can be run successfully

**Steps**:
1. Navigate to `addon_portal` directory
2. Check current migration status:
   ```bash
   cd addon_portal
   alembic current
   ```
3. Run migration:
   ```bash
   alembic upgrade head
   ```
4. Verify table was created:
   ```sql
   -- Connect to PostgreSQL
   \dt llm_usage_logs
   -- Should show the table
   ```

**Expected Result**: 
- Migration runs without errors
- Table `llm_usage_logs` exists in database
- All indexes are created

**If Failed**: Check database connection, verify Alembic config, check migration file syntax

---

### 4. LLM Call Logging Test
**Goal**: Verify LLM calls are logged to database

**Steps**:
1. Trigger an LLM call (run a project or make an agent call)
2. Wait a few seconds for async logging
3. Check database:
   ```sql
   SELECT * FROM llm_usage_logs ORDER BY created_at DESC LIMIT 10;
   ```
4. Or check via API:
   ```bash
   curl http://localhost:8080/api/llm/logs
   ```

**Expected Result**: 
- Logs appear in database
- Each log entry has correct fields (provider, model, tokens, cost, etc.)
- Logging doesn't block LLM calls

**If Failed**: Check `utils/llm_logger.py` imports, verify async task creation, check database connection

---

### 5. Frontend Logs Page Test
**Goal**: Verify logs page displays correctly

**Steps**:
1. Navigate to `/llm/logs` in browser
2. Check page loads without errors
3. Verify filters work:
   - Date range dropdown
   - Agent filter
   - Provider filter
   - Status filter
4. Check stats cards show correct values

**Expected Result**: 
- Page loads successfully
- Filters work correctly
- Stats are accurate
- Table displays logs (if any)

**If Failed**: Check browser console, verify API endpoint works, check frontend code

---

## Common Issues and Solutions

### Issue: Model names still show hardcoded values
**Solution**: 
- Check `.env` file has correct `GEMINI_MODEL` set
- Verify `utils/llm_service.py` stores model names correctly
- Check API response includes `model` field

### Issue: `/api/llm/logs` returns 503 Service Unavailable
**Solution**: 
- Check `LLM_AVAILABLE` flag in `llm_management.py`
- Verify LLM service imports work
- Check API logs for import errors

### Issue: Migration fails
**Solution**: 
- Verify database connection string in `.env`
- Check Alembic config in `alembic.ini`
- Ensure `env.py` imports `LLMUsageLog` model
- Check PostgreSQL is running

### Issue: Logs not appearing in database
**Solution**: 
- Check `utils/llm_logger.py` can import database models
- Verify async task is created (check logs for errors)
- Check database connection in background task
- Verify `Q2O_PROJECT_ID` and `Q2O_AGENT_TYPE` env vars are set

### Issue: Frontend shows errors
**Solution**: 
- Check browser console for JavaScript errors
- Verify API endpoints return correct structure
- Check CORS settings
- Verify Next.js dev server is running

---

## After Successful Testing

Once all tests pass:

1. **Run Migration**:
   ```bash
   cd addon_portal
   alembic upgrade head
   ```

2. **Verify Template Learning**:
   - Check `utils/template_learning_engine.py` is working
   - Test template generation
   - Verify templates appear in dashboard

3. **Document Any Issues**:
   - Note any bugs found
   - Document workarounds
   - Update implementation docs

4. **Continue with Agentic System Implementation Plan**:
   - These fixes are foundational
   - They provide better observability
   - No conflicts with planned improvements

---

## Success Criteria

✅ Model names display correctly in dashboard  
✅ `/api/llm/logs` endpoint works  
✅ Database migration runs successfully  
✅ LLM calls are logged to database  
✅ Frontend logs page works correctly  
✅ No blocking errors or crashes  

Once all criteria are met, proceed with remaining implementation tasks.

