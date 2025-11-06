@echo off
REM Clear research cache and test with fresh Google search

echo.
echo Clearing research cache...
if exist .research_cache rmdir /S /Q .research_cache
echo ✓ Cache cleared

echo.
echo Clearing global research database (forcing fresh research)...
if exist "%USERPROFILE%\.quickodoo\research_cache" rmdir /S /Q "%USERPROFILE%\.quickodoo\research_cache"
echo ✓ Global cache cleared

echo.
echo Testing fresh Google search...
python test_duckduckgo_search.py

echo.
echo Done! Cache cleared and test completed.
pause

