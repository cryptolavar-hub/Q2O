# PowerShell helper to install admin portal dependencies safely.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Write-Host 'Installing admin portal dependencies...' -ForegroundColor Cyan
Set-Location -Path 'addon_portal\apps\admin-portal'
npm install
Write-Host 'Dependency installation complete.' -ForegroundColor Green
