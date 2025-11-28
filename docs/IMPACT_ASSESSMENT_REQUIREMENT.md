# Impact Assessment Requirement - Process Documentation

**Date**: November 27, 2025  
**Role**: QA_Engineer - Process Improvement  
**Status**: ✅ **DOCUMENTED**

---

## 📋 **Requirement**

**User Requirement**: Before implementing any code changes, an **Impact Assessment** must be performed to:
1. Identify potential side effects
2. Analyze dependencies
3. Assess risks
4. Prevent regressions
5. Document pros, cons, and impact

**Rationale**: "Fixing one thing led to another failure somewhere else" - changes must be thoroughly analyzed before implementation to prevent cascading failures.

---

## ⚠️ **Recent Violation**

### **Issue**: Syntax Error in `llm_management.py`

**What Happened**:
- Added templates API endpoint with pagination
- Introduced duplicate code and syntax error
- Error: `SyntaxError: unmatched ')'` at line 471
- **Impact**: API server failed to start, breaking the entire backend

**Root Cause**:
- No impact assessment performed before adding the endpoint
- Duplicate code blocks were accidentally created during editing
- No verification that the file was syntactically correct

**Fix Applied**:
- Removed duplicate code blocks
- Fixed syntax error
- Verified file compiles correctly

---

## ✅ **Impact Assessment Process**

### **Step 1: Identify Change Scope**
- What files will be modified?
- What functions/classes are affected?
- What dependencies exist?

### **Step 2: Analyze Dependencies**
- What other code depends on the changed code?
- What imports/exports are affected?
- Are there any circular dependencies?

### **Step 3: Assess Risks**
- What could break if this change is made?
- Are there edge cases to consider?
- What tests need to be updated?

### **Step 4: Document Impact**
- **Pros**: What benefits does this change provide?
- **Cons**: What are the drawbacks or limitations?
- **Impact**: What systems/components are affected?
- **Risk Level**: Low / Medium / High

### **Step 5: Verify Before Implementation**
- Check syntax/linting
- Review imports and dependencies
- Ensure backward compatibility (if required)
- Plan rollback strategy

---

## 📝 **Impact Assessment Template**

```markdown
## Impact Assessment: [Change Description]

### Change Scope
- **Files Modified**: [list files]
- **Functions/Classes Affected**: [list]
- **Dependencies**: [list]

### Analysis
- **Dependencies**: [what depends on this]
- **Imports/Exports**: [what's imported/exported]
- **Circular Dependencies**: [yes/no, details]

### Risk Assessment
- **Potential Breakage**: [what could break]
- **Edge Cases**: [edge cases to consider]
- **Tests Needed**: [what tests need updating]

### Impact Documentation
- **Pros**: [benefits]
- **Cons**: [drawbacks]
- **Impact**: [affected systems]
- **Risk Level**: [Low/Medium/High]

### Verification Plan
- [ ] Syntax check
- [ ] Linting check
- [ ] Import verification
- [ ] Dependency check
- [ ] Backward compatibility check
- [ ] Rollback plan
```

---

## 🔧 **Implementation Checklist**

Before making ANY code change:

- [ ] **Perform Impact Assessment** using the template above
- [ ] **Document the assessment** in a markdown file or comment
- [ ] **Review dependencies** and potential side effects
- [ ] **Check for syntax errors** before committing
- [ ] **Run linting** to catch issues early
- [ ] **Verify imports** are correct
- [ ] **Test the change** in isolation if possible
- [ ] **Plan rollback** strategy if needed

---

## 📚 **Lessons Learned**

### **From Recent Incident**:
1. ✅ Always verify syntax before moving to next task
2. ✅ Check for duplicate code blocks after edits
3. ✅ Run linting/compilation checks immediately after changes
4. ✅ Perform impact assessment BEFORE implementation
5. ✅ Review entire function/class after editing, not just the changed lines

### **Best Practices**:
- Use IDE/editor features to catch syntax errors immediately
- Run `python -m py_compile` or similar before committing
- Use `read_lints` tool after every code change
- Review the entire modified section, not just the diff
- Test imports and function calls after changes

---

## ✅ **Status**

- ✅ **Requirement Documented**: November 27, 2025
- ✅ **Process Established**: Impact Assessment Template created
- ✅ **Checklist Created**: Pre-implementation verification steps
- ✅ **Lessons Learned**: Documented from recent incident

---

**Documented By**: QA_Engineer - Process Improvement  
**Date**: November 27, 2025  
**Priority**: 🔴 **CRITICAL** - Must be followed for all future changes

