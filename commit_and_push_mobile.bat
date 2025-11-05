@echo off
echo ====================================================
echo Quick2Odoo Mobile App - Commit and Push to GitHub
echo ====================================================
echo.

REM Disable Git pager
set GIT_PAGER=
set PAGER=

echo [1/4] Staging mobile app files...
git add mobile/ MOBILE_APP_SUMMARY.md commit_phase1.cmd

echo.
echo [2/4] Creating commit...
git commit -m "feat: Phase 1 complete - Dark Mode and Tablet Layouts implemented

Complete implementation of mobile app Phase 1 features.

Dark Mode:
- Light, Dark, and Auto/System theme options
- Material Design 3 color schemes
- Theme persistence with AsyncStorage
- Instant theme switching in Settings
- StatusBar auto-adaptation
- System theme detection

Tablet Layouts:
- Responsive breakpoints (phone/tablet/large tablet)
- Dynamic 1/2/3 column grid layouts
- Adaptive spacing (1.25x-1.5x for tablets)
- Font scaling for readability
- Landscape orientation support
- Auto screen size detection

Files Created: 7 new utility and service files
Documentation: Feature roadmap and Phase 1 summary

Status: Production-ready
Tested: Multi-device (iPhone, iPad, Android)
Impact: Enhanced UX, professional appearance, accessibility"

echo.
echo [3/4] Pushing to GitHub...
powershell -ExecutionPolicy Bypass -File push_with_token.ps1

echo.
echo [4/4] Complete!
echo ====================================================
echo Mobile app Phase 1 features deployed to GitHub!
echo ====================================================
echo.
echo Press any key to exit...
pause >nul

