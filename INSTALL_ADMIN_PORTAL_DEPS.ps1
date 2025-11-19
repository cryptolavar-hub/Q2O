# PowerShell helper to install admin portal dependencies safely.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# Save original directory and restore it after execution
$originalLocation = Get-Location

try {
    Write-Host 'Installing admin portal dependencies...' -ForegroundColor Cyan
    Push-Location -Path 'addon_portal\apps\admin-portal'
    npm install
    Write-Host 'Dependency installation complete.' -ForegroundColor Green
} finally {
    # Always restore the original directory, even if npm install fails
    Pop-Location
    # Verify we're back to the original location
    if ((Get-Location).Path -ne $originalLocation.Path) {
        Set-Location -Path $originalLocation
    }
}
