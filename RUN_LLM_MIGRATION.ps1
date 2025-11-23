# PowerShell script to run LLM configuration tables migration
# Ensures LLM system, project, and agent configuration can be stored in PostgreSQL

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Write-Host '========================================' -ForegroundColor Cyan
Write-Host 'Q2O LLM Configuration Migration' -ForegroundColor Cyan
Write-Host '========================================' -ForegroundColor Cyan
Write-Host ''

# Load .env from ROOT directory ONLY (C:\Q2O_Combined\.env)
$rootEnvPath = Join-Path $PSScriptRoot '.env'
if (Test-Path $rootEnvPath) {
    Write-Host 'Loading database connection from root .env...' -ForegroundColor Yellow
    Get-Content $rootEnvPath | ForEach-Object {
        if ($_ -match '^DB_DSN=(.+)$') {
            $env:DB_DSN = $matches[1]
        }
    }
} else {
    Write-Host 'WARNING: .env file not found in root directory!' -ForegroundColor Yellow
    Write-Host "Expected location: $rootEnvPath" -ForegroundColor Yellow
}

# Parse connection string
if ($env:DB_DSN -match 'postgresql\+psycopg://(.+):(.+)@(.+):(\d+)/(.+)') {
    $dbUser = $matches[1]
    $dbPassword = $matches[2]
    $dbHost = $matches[3]
    $dbPort = $matches[4]
    $dbName = $matches[5]
    
    Write-Host "Database: postgresql://$dbHost:$dbPort/$dbName" -ForegroundColor Green
    Write-Host "User: $dbUser" -ForegroundColor Green
    Write-Host ''
    
    $migrationFile = Join-Path $PSScriptRoot 'addon_portal' 'migrations_manual' '004_add_llm_config_tables.sql'
    
    if (-not (Test-Path $migrationFile)) {
        Write-Host 'ERROR: Migration file not found!' -ForegroundColor Red
        Write-Host "Expected: $migrationFile" -ForegroundColor Red
        exit 1
    }
    
    Write-Host 'Running migration...' -ForegroundColor Yellow
    
    $env:PGPASSWORD = $dbPassword
    psql -h $dbHost -p $dbPort -U $dbUser -d $dbName -f $migrationFile
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ''
        Write-Host '========================================' -ForegroundColor Green
        Write-Host 'Migration completed successfully!' -ForegroundColor Green
        Write-Host '========================================' -ForegroundColor Green
        Write-Host ''
        Write-Host 'LLM configuration tables created:' -ForegroundColor Cyan
        Write-Host '  - llm_system_config' -ForegroundColor White
        Write-Host '  - llm_project_config' -ForegroundColor White
        Write-Host '  - llm_agent_config' -ForegroundColor White
        Write-Host '  - llm_config_history' -ForegroundColor White
    } else {
        Write-Host ''
        Write-Host 'Migration failed!' -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host 'ERROR: DB_DSN not found or invalid format' -ForegroundColor Red
    Write-Host 'Expected format: postgresql+psycopg://user:password@host:port/database' -ForegroundColor Yellow
    Write-Host ''
    Write-Host "Please set DB_DSN in root .env file: $rootEnvPath" -ForegroundColor Yellow
    exit 1
}

