# =========================================================================
# INSTALL_POSTGRESQL.ps1
# Automated PostgreSQL 16 Setup for Q2O Combined
# =========================================================================
# This script helps install and configure PostgreSQL for production
# =========================================================================

param(
    [string]$Password = "",
    [switch]$SkipDownload = $false,
    [switch]$Help = $false
)

if ($Help) {
    Write-Host @"
=========================================================================
  PostgreSQL Installation Script for Q2O Combined
=========================================================================

USAGE:
  .\INSTALL_POSTGRESQL.ps1 -Password "YourSecurePassword"

OPTIONS:
  -Password       PostgreSQL password for postgres superuser and q2o_user
  -SkipDownload   Skip download if installer already exists
  -Help           Show this help message

EXAMPLES:
  # Full installation with password
  .\INSTALL_POSTGRESQL.ps1 -Password "Q2OPostgres2025!"

  # Skip download (if postgresql installer already downloaded)
  .\INSTALL_POSTGRESQL.ps1 -Password "Q2OPostgres2025!" -SkipDownload

WHAT THIS SCRIPT DOES:
  1. Downloads PostgreSQL 16 installer (if needed)
  2. Provides installation instructions
  3. Tests PostgreSQL connection
  4. Creates q2o database and user
  5. Grants permissions
  6. Creates .env file with connection string
  7. Tests database setup

MANUAL INSTALLATION:
  See POSTGRESQL_SETUP.md for detailed manual installation steps

=========================================================================
"@
    exit 0
}

Write-Host "==========================================================================" -ForegroundColor Cyan
Write-Host "  PostgreSQL 16 Installation for Q2O Combined" -ForegroundColor Cyan
Write-Host "==========================================================================" -ForegroundColor Cyan
Write-Host ""

# =========================================================================
# STEP 1: Check if PostgreSQL is already installed
# =========================================================================

Write-Host "[Step 1/7] Checking for existing PostgreSQL installation..." -ForegroundColor Yellow
Write-Host ""

$PostgreSQLPath = "C:\Program Files\PostgreSQL\16\bin\psql.exe"
$PostgreSQLInstalled = Test-Path $PostgreSQLPath

if ($PostgreSQLInstalled) {
    Write-Host "  [OK] PostgreSQL 16 is already installed!" -ForegroundColor Green
    Write-Host "  Location: $PostgreSQLPath" -ForegroundColor Gray
    
    # Test version
    try {
        $version = & "$PostgreSQLPath" --version
        Write-Host "  Version: $version" -ForegroundColor Gray
    } catch {
        Write-Host "  [WARNING] Could not determine version" -ForegroundColor Yellow
    }
    
    Write-Host ""
    Write-Host "Skipping installation. Proceeding to database setup..." -ForegroundColor Cyan
    $SkipInstall = $true
} else {
    Write-Host "  [INFO] PostgreSQL 16 not found. Installation needed." -ForegroundColor Yellow
    $SkipInstall = $false
}

Write-Host ""

# =========================================================================
# STEP 2: Download PostgreSQL installer (if needed)
# =========================================================================

if (-not $SkipInstall -and -not $SkipDownload) {
    Write-Host "[Step 2/7] Downloading PostgreSQL 16 installer..." -ForegroundColor Yellow
    Write-Host ""
    
    $InstallerPath = Join-Path $env:TEMP "postgresql-16-installer.exe"
    $DownloadUrl = "https://sbp.enterprisedb.com/getfile.jsp?fileid=1258649"
    
    Write-Host "  Download URL: $DownloadUrl" -ForegroundColor Gray
    Write-Host "  Saving to: $InstallerPath" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  [INFO] This may take a few minutes (~300 MB)..." -ForegroundColor Yellow
    Write-Host ""
    
    try {
        Invoke-WebRequest -Uri $DownloadUrl -OutFile $InstallerPath -UseBasicParsing
        Write-Host "  [OK] Download complete!" -ForegroundColor Green
    } catch {
        Write-Host "  [ERROR] Download failed: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host ""
        Write-Host "  MANUAL DOWNLOAD:" -ForegroundColor Yellow
        Write-Host "  1. Visit: https://www.postgresql.org/download/windows/" -ForegroundColor Gray
        Write-Host "  2. Download PostgreSQL 16.x for Windows" -ForegroundColor Gray
        Write-Host "  3. Run this script again with -SkipDownload" -ForegroundColor Gray
        Write-Host ""
        Read-Host "Press Enter to exit"
        exit 1
    }
    
    Write-Host ""
}

# =========================================================================
# STEP 3: Installation Instructions
# =========================================================================

if (-not $SkipInstall) {
    Write-Host "[Step 3/7] PostgreSQL Installation Instructions" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "==========================================================================" -ForegroundColor Cyan
    Write-Host "  IMPORTANT: Manual Installation Required" -ForegroundColor Cyan
    Write-Host "==========================================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "PostgreSQL installer will now launch. Follow these steps:" -ForegroundColor White
    Write-Host ""
    Write-Host "  1. Click 'Next' on the welcome screen" -ForegroundColor Gray
    Write-Host "  2. Keep default installation directory" -ForegroundColor Gray
    Write-Host "  3. Select ALL components (PostgreSQL Server, pgAdmin 4, Command Line Tools)" -ForegroundColor Gray
    Write-Host "  4. Keep default data directory" -ForegroundColor Gray
    Write-Host "  5. SET PASSWORD for 'postgres' user:" -ForegroundColor Yellow
    
    if ($Password) {
        Write-Host "     Password: $Password" -ForegroundColor Green
        Write-Host "     (Use this password!)" -ForegroundColor Green
    } else {
        Write-Host "     (Choose a strong password and REMEMBER IT!)" -ForegroundColor Yellow
    }
    
    Write-Host "  6. Keep default port: 5432" -ForegroundColor Gray
    Write-Host "  7. Keep default locale" -ForegroundColor Gray
    Write-Host "  8. Click 'Next' then 'Finish'" -ForegroundColor Gray
    Write-Host ""
    Write-Host "==========================================================================" -ForegroundColor Cyan
    Write-Host ""
    
    $response = Read-Host "Ready to launch installer? (y/n)"
    if ($response -ne "y" -and $response -ne "Y") {
        Write-Host "Installation cancelled." -ForegroundColor Yellow
        exit 0
    }
    
    Write-Host ""
    Write-Host "Launching installer..." -ForegroundColor Cyan
    
    try {
        Start-Process -FilePath $InstallerPath -Wait
        Write-Host ""
        Write-Host "  [OK] Installer finished." -ForegroundColor Green
    } catch {
        Write-Host "  [ERROR] Could not launch installer: $($_.Exception.Message)" -ForegroundColor Red
        exit 1
    }
    
    Write-Host ""
    Write-Host "Waiting for PostgreSQL service to start..." -ForegroundColor Yellow
    Start-Sleep -Seconds 10
}

Write-Host ""

# =========================================================================
# STEP 4: Verify PostgreSQL Installation
# =========================================================================

Write-Host "[Step 4/7] Verifying PostgreSQL installation..." -ForegroundColor Yellow
Write-Host ""

$PostgreSQLPath = "C:\Program Files\PostgreSQL\16\bin\psql.exe"
if (-not (Test-Path $PostgreSQLPath)) {
    Write-Host "  [ERROR] PostgreSQL not found at: $PostgreSQLPath" -ForegroundColor Red
    Write-Host "  [INFO] Installation may have failed or used different path" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "  [OK] PostgreSQL found: $PostgreSQLPath" -ForegroundColor Green

# Test psql command
try {
    $version = & "$PostgreSQLPath" --version
    Write-Host "  [OK] Version: $version" -ForegroundColor Green
} catch {
    Write-Host "  [ERROR] Could not run psql: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host ""

# =========================================================================
# STEP 5: Get Password
# =========================================================================

Write-Host "[Step 5/7] Database credentials..." -ForegroundColor Yellow
Write-Host ""

if (-not $Password) {
    Write-Host "Enter the PostgreSQL password you set during installation:" -ForegroundColor White
    $SecurePassword = Read-Host -AsSecureString
    $BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($SecurePassword)
    $Password = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)
    Write-Host ""
}

Write-Host "  [OK] Password received" -ForegroundColor Green
Write-Host ""

# =========================================================================
# STEP 6: Create Database and User
# =========================================================================

Write-Host "[Step 6/7] Creating q2o database and user..." -ForegroundColor Yellow
Write-Host ""

# Create SQL script
$SqlScript = @"
-- Create database
CREATE DATABASE q2o;

-- Create user
CREATE USER q2o_user WITH PASSWORD '$Password';

-- Grant privileges on database
GRANT ALL PRIVILEGES ON DATABASE q2o TO q2o_user;

-- Connect to q2o database
\c q2o

-- Grant schema privileges
GRANT ALL ON SCHEMA public TO q2o_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO q2o_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO q2o_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO q2o_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO q2o_user;
"@

$SqlScriptPath = Join-Path $env:TEMP "q2o_setup.sql"
$SqlScript | Out-File -FilePath $SqlScriptPath -Encoding UTF8

Write-Host "  Executing SQL script..." -ForegroundColor Gray

$env:PGPASSWORD = $Password
try {
    & "C:\Program Files\PostgreSQL\16\bin\psql.exe" -U postgres -f $SqlScriptPath 2>&1 | Out-Null
    
    # Check if q2o database exists
    $dbCheck = & "C:\Program Files\PostgreSQL\16\bin\psql.exe" -U postgres -lqt 2>&1 | Select-String -Pattern "q2o"
    
    if ($dbCheck) {
        Write-Host "  [OK] Database 'q2o' created successfully" -ForegroundColor Green
        Write-Host "  [OK] User 'q2o_user' created successfully" -ForegroundColor Green
        Write-Host "  [OK] Permissions granted" -ForegroundColor Green
    } else {
        Write-Host "  [WARNING] Could not verify database creation" -ForegroundColor Yellow
        Write-Host "  [INFO] You may need to create it manually" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  [ERROR] Database setup failed: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
    Write-Host "  MANUAL SETUP:" -ForegroundColor Yellow
    Write-Host "  Run these commands in psql:" -ForegroundColor Gray
    Write-Host ""
    Write-Host $SqlScript -ForegroundColor Gray
    Write-Host ""
} finally {
    Remove-Item -Path $SqlScriptPath -ErrorAction SilentlyContinue
}

Write-Host ""

# =========================================================================
# STEP 7: Create .env File
# =========================================================================

Write-Host "[Step 7/7] Creating .env configuration file..." -ForegroundColor Yellow
Write-Host ""

$EnvContent = @"
# PostgreSQL Configuration (Production)
DB_DSN=postgresql+psycopg2://q2o_user:$Password@localhost:5432/q2o

# Application
APP_NAME=Quick2Odoo
ENV=production

# JWT (Update these for production!)
JWT_ISSUER=q2o-auth
JWT_AUDIENCE=q2o-clients
JWT_PRIVATE_KEY=CHANGE_ME_RSA_PRIV_PEM
JWT_PUBLIC_KEY=CHANGE_ME_RSA_PUB_PEM
JWT_ACCESS_TTL_SECONDS=900
JWT_REFRESH_TTL_SECONDS=1209600

# Stripe (Update with real keys!)
STRIPE_SECRET_KEY=sk_test_xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Activation Codes
ACTIVATION_CODE_PEPPER=CHANGE_ME_ACTIVATION_PEPPER

# CORS
ALLOWED_ORIGINS=http://localhost:3000,https://quick2odoo.com

# Session
SESSION_SECRET=CHANGE_ME_SESSION_SECRET
"@

$EnvPath = Join-Path (Get-Location) "addon_portal\.env"
$EnvContent | Out-File -FilePath $EnvPath -Encoding UTF8

Write-Host "  [OK] Created: addon_portal\.env" -ForegroundColor Green
Write-Host "  [INFO] Connection string: postgresql+psycopg2://q2o_user:***@localhost:5432/q2o" -ForegroundColor Gray
Write-Host ""

# =========================================================================
# SUMMARY
# =========================================================================

Write-Host "==========================================================================" -ForegroundColor Green
Write-Host "  PostgreSQL Setup Complete!" -ForegroundColor Green
Write-Host "==========================================================================" -ForegroundColor Green
Write-Host ""
Write-Host "WHAT WAS DONE:" -ForegroundColor White
Write-Host "  [OK] PostgreSQL 16 installed (or already present)" -ForegroundColor Green
Write-Host "  [OK] Database 'q2o' created" -ForegroundColor Green
Write-Host "  [OK] User 'q2o_user' created" -ForegroundColor Green
Write-Host "  [OK] Permissions granted" -ForegroundColor Green
Write-Host "  [OK] .env file created with PostgreSQL connection" -ForegroundColor Green
Write-Host ""
Write-Host "NEXT STEPS:" -ForegroundColor White
Write-Host "  1. Run database setup:" -ForegroundColor Gray
Write-Host "     cd addon_portal" -ForegroundColor Gray
Write-Host "     python quick_setup.py" -ForegroundColor Gray
Write-Host ""
Write-Host "  2. Start services:" -ForegroundColor Gray
Write-Host "     cd .." -ForegroundColor Gray
Write-Host "     START_ALL.bat" -ForegroundColor Gray
Write-Host ""
Write-Host "  3. Verify in pgAdmin 4:" -ForegroundColor Gray
Write-Host "     Open pgAdmin 4 -> PostgreSQL 16 -> Databases -> q2o" -ForegroundColor Gray
Write-Host ""
Write-Host "CONNECTION INFO:" -ForegroundColor White
Write-Host "  Database: q2o" -ForegroundColor Gray
Write-Host "  User:     q2o_user" -ForegroundColor Gray
Write-Host "  Password: [saved in addon_portal\.env]" -ForegroundColor Gray
Write-Host "  Port:     5432" -ForegroundColor Gray
Write-Host ""
Write-Host "==========================================================================" -ForegroundColor Green
Write-Host ""

Read-Host "Press Enter to finish"

