@echo off
set GIT_PAGER=
git add mobile/
git commit -m "feat: Implement Phase 1 - Dark Mode and Tablet Layouts for mobile app"
powershell -ExecutionPolicy Bypass -File push_with_token.ps1

