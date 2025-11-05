# PowerShell Pager Fix Script
# This script will help you fix the pager issue

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "PowerShell Pager Fix Tool" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

$profileExists = Test-Path $PROFILE

if (-not $profileExists) {
    Write-Host "No PowerShell profile found. The pager issue might be from:" -ForegroundColor Yellow
    Write-Host "1. Global git configuration" -ForegroundColor White
    Write-Host "2. System-wide environment variables`n" -ForegroundColor White
    
    Write-Host "Checking and fixing git configuration..." -ForegroundColor Yellow
    
    # Clear git pager settings
    git config --global --unset core.pager 2>$null
    git config --local --unset core.pager 2>$null
    
    Write-Host "Git pager settings cleared!`n" -ForegroundColor Green
    
} else {
    Write-Host "PowerShell profile found at:" -ForegroundColor Yellow
    Write-Host "$PROFILE`n" -ForegroundColor Cyan
    
    Write-Host "Backing up current profile..." -ForegroundColor Yellow
    $backupPath = "$PROFILE.backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
    Copy-Item $PROFILE $backupPath
    Write-Host "Backup created: $backupPath`n" -ForegroundColor Green
    
    Write-Host "Reading profile..." -ForegroundColor Yellow
    $content = Get-Content $PROFILE -Raw
    
    # Patterns to look for
    $problematicPatterns = @(
        'Out-Default',
        'Out-Host.*less',
        'Out-Host.*more',
        '\$env:PAGER',
        '\$env:GIT_PAGER',
        'Set-Alias.*git',
        'function.*git\s*{',
        'less',
        'more\s+'
    )
    
    $foundIssues = @()
    foreach ($pattern in $problematicPatterns) {
        if ($content -match $pattern) {
            $foundIssues += $pattern
        }
    }
    
    if ($foundIssues.Count -gt 0) {
        Write-Host "Found potential issues:" -ForegroundColor Red
        $foundIssues | ForEach-Object { Write-Host "  - $_" -ForegroundColor Yellow }
        Write-Host "`n"
        
        Write-Host "Would you like to:" -ForegroundColor Cyan
        Write-Host "1. View the profile in Notepad (to manually edit)" -ForegroundColor White
        Write-Host "2. Create a clean profile (removes ALL customizations)" -ForegroundColor White
        Write-Host "3. Just clear pager-related environment variables for this session" -ForegroundColor White
        Write-Host "4. Exit (do nothing)" -ForegroundColor White
        Write-Host "`n"
        
        $choice = Read-Host "Enter choice (1-4)"
        
        switch ($choice) {
            "1" {
                Write-Host "Opening profile in Notepad..." -ForegroundColor Yellow
                notepad $PROFILE
                Write-Host "After editing, restart PowerShell for changes to take effect." -ForegroundColor Green
            }
            "2" {
                Write-Host "Creating clean profile..." -ForegroundColor Yellow
                @"
# PowerShell Profile - Clean Version
# Backup saved at: $backupPath

# Add your custom settings here
# Avoid using pagers like 'less' or 'more'

"@ | Set-Content $PROFILE
                Write-Host "Clean profile created! Restart PowerShell." -ForegroundColor Green
            }
            "3" {
                Write-Host "Clearing environment variables for this session..." -ForegroundColor Yellow
                $env:PAGER = $null
                $env:GIT_PAGER = $null
                Write-Host "Environment variables cleared for this session." -ForegroundColor Green
                Write-Host "Note: This is temporary. Profile will reload on next session." -ForegroundColor Yellow
            }
            default {
                Write-Host "No changes made." -ForegroundColor Yellow
            }
        }
    } else {
        Write-Host "No obvious pager issues found in profile.`n" -ForegroundColor Green
        Write-Host "The issue might be from:" -ForegroundColor Yellow
        Write-Host "1. Global git configuration" -ForegroundColor White
        Write-Host "2. System environment variables`n" -ForegroundColor White
    }
}

# Always clear git config pager
Write-Host "`nClearing git pager configuration..." -ForegroundColor Yellow
git config --global --unset core.pager 2>$null
git config --local --unset core.pager 2>$null
Write-Host "Done!`n" -ForegroundColor Green

# Clear environment variables for current session
$env:PAGER = $null
$env:GIT_PAGER = $null

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Quick Test" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan
Write-Host "Testing git status..." -ForegroundColor Yellow

# Test git status
git status --short

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "If the above output appeared directly (not in a pager)," -ForegroundColor Green
Write-Host "the issue is fixed for this session!" -ForegroundColor Green
Write-Host "`nIf you still see a pager, restart PowerShell and run this script again." -ForegroundColor Yellow
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

