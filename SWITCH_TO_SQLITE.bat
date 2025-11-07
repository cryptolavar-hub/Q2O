@echo off
REM =========================================================================
REM Switch to SQLite Database
REM =========================================================================

echo.
echo =========================================================================
echo  Switching to SQLite
echo =========================================================================
echo.

cd addon_portal

REM Create .env with SQLite connection
(
echo # SQLite Configuration ^(Development^)
echo DB_DSN=sqlite:///./q2o_licensing.db
echo.
echo # Application
echo APP_NAME=Quick2Odoo
echo ENV=development
echo.
echo # JWT ^(Update these for production!^)
echo JWT_ISSUER=q2o-auth
echo JWT_AUDIENCE=q2o-clients
echo JWT_PRIVATE_KEY=CHANGE_ME_RSA_PRIV_PEM
echo JWT_PUBLIC_KEY=CHANGE_ME_RSA_PUB_PEM
echo JWT_ACCESS_TTL_SECONDS=900
echo JWT_REFRESH_TTL_SECONDS=1209600
echo.
echo # Stripe ^(Test mode^)
echo STRIPE_SECRET_KEY=sk_test_xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
echo STRIPE_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
echo.
echo # Activation Codes
echo ACTIVATION_CODE_PEPPER=dev_pepper_change_for_production
echo.
echo # CORS ^(JSON array format^)
echo ALLOWED_ORIGINS=["http://localhost:3000"]
echo.
echo # Session
echo SESSION_SECRET=dev_session_secret_change_for_production
) > .env

cd ..

echo.
echo [OK] Switched to SQLite
echo.
echo Database: addon_portal/q2o_licensing.db
echo Tenant: demo
echo Activation Codes:
echo   N5N5-V3RJ-G6ZD-KPK8
echo   K4P7-57B5-DGF5-99SE
echo   XPDG-H6NF-ULDS-DE5E
echo.
echo =========================================================================
echo.
pause

