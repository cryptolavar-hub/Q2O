@echo off
REM =========================================================================
REM Switch to PostgreSQL 18 Database
REM =========================================================================

echo.
echo =========================================================================
echo  Switching to PostgreSQL 18
echo =========================================================================
echo.

cd addon_portal

REM Create .env with PostgreSQL connection
(
echo # PostgreSQL 18 Configuration ^(Test Server^)
echo DB_DSN=postgresql+psycopg2://q2o_user:Q2OPostgres2025!@localhost:5432/q2o
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
echo [OK] Switched to PostgreSQL 18
echo.
echo Database: postgresql://localhost:5432/q2o
echo Tenant: demo
echo Activation Codes:
echo   8PL4-M5HA-QP3E-MPCT
echo   ND7V-A9B5-ACP7-85KW
echo   5EFZ-7CHR-QLKS-JQMJ
echo.
echo =========================================================================
echo.
pause

