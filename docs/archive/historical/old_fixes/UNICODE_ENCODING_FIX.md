# Unicode Encoding Fix - Windows Console Compatibility

## Issue
Windows console (cp1252 encoding) cannot handle Unicode characters like checkmarks (✓) and warning symbols (⚠) in log messages, causing `UnicodeEncodeError` during API startup.

## Error
```
UnicodeEncodeError: 'charmap' codec can't encode character '\u2713' in position 101: character maps to <undefined>
```

## Root Cause
Python log messages and print statements contained Unicode characters that Windows console cannot encode.

## Fixes Applied

### Files Fixed

#### 1. `addon_portal/api/main.py`
- Line 58: `✓` → `[OK]`
- Line 69: `✓` → `[OK]`
- Line 110: `✓` → `[OK]`
- Line 112: `⚠` → `[WARNING]`
- Line 119: `✓` → `[OK]`

#### 2. `addon_portal/start_api_windows.py`
- Line 21: `✓` → `[OK]`
- Line 95: `✓` → `[OK]`

#### 3. `addon_portal/start_api_windows_dual_stack.py`
- Line 19: `✓` → `[OK]`
- Line 87: `✓` → `[OK]`

### Replacement Strategy
- `✓` (checkmark) → `[OK]`
- `⚠` (warning) → `[WARNING]`

## Note on Frontend Files
Frontend files (React/TSX) contain Unicode characters in UI elements (e.g., `✓ Copied!` in `llm/configuration.tsx`). These are **intentionally left unchanged** because:
1. They render in the browser (which supports Unicode)
2. They are not logged to Windows console
3. They are user-facing UI elements, not code/logs

## Testing
After this fix:
- ✅ API should start without UnicodeEncodeError
- ✅ Log messages should display correctly in Windows console
- ✅ No encoding errors in subprocess output

## Prevention
**Rule**: Never use Unicode characters (emojis, symbols) in Python log messages or print statements that output to Windows console. Use ASCII-safe alternatives like `[OK]`, `[WARNING]`, `[ERROR]`, etc.

