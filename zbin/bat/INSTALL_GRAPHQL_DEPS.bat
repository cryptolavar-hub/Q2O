@echo off
REM Install GraphQL dependencies for backend API

echo ========================================
echo Installing GraphQL Dependencies
echo ========================================
echo.

cd /d "%~dp0\addon_portal"

echo Installing strawberry-graphql and related packages...
python -m pip install "strawberry-graphql[fastapi]>=0.236.0" "aiodataloader>=0.4.0" "graphql-core>=3.2.0" "sse-starlette>=1.8.2"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo ✓ GraphQL dependencies installed successfully
    echo ========================================
    echo.
    echo Next steps:
    echo   1. Restart the backend API
    echo   2. GraphQL endpoint will be available at: http://localhost:8080/graphql
    echo   3. GraphiQL playground: http://localhost:8080/graphql (GET request)
    echo.
) else (
    echo.
    echo ========================================
    echo ✗ Installation failed
    echo ========================================
    echo.
    echo Please check the error messages above.
    echo.
)

pause

