@echo off
REM Q2O Service Manager - Quick Access
REM Usage:
REM   MANAGE_SERVICES.bat               → Interactive menu
REM   MANAGE_SERVICES.bat status        → Show service status
REM   MANAGE_SERVICES.bat restart licensing → Restart Licensing API
REM   MANAGE_SERVICES.bat stop admin    → Stop Admin Portal

powershell.exe -ExecutionPolicy Bypass -File "%~dp0MANAGE_SERVICES.ps1" %*

