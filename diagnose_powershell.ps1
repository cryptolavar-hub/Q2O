# PowerShell Pager Diagnostic Script
# Run this to identify what's causing the pager issue

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "PowerShell Pager Diagnostic Tool" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# 1. Check Profile Path
Write-Host "[1] PowerShell Profile Location:" -ForegroundColor Yellow
Write-Host "    $PROFILE`n"

# 2. Check if Profile Exists
Write-Host "[2] Profile Exists:" -ForegroundColor Yellow
if (Test-Path $PROFILE) {
    Write-Host "    YES - Profile is loaded`n" -ForegroundColor Green
    
    Write-Host "[3] Profile Contents:" -ForegroundColor Yellow
    Write-Host "    ----------------------------------------"
    Get-Content $PROFILE | ForEach-Object {
        Write-Host "    $_"
    }
    Write-Host "    ----------------------------------------`n"
} else {
    Write-Host "    NO - No profile found`n" -ForegroundColor Red
}

# 3. Check Environment Variables
Write-Host "[4] Pager-related Environment Variables:" -ForegroundColor Yellow
Write-Host "    PAGER:       $env:PAGER"
Write-Host "    GIT_PAGER:   $env:GIT_PAGER"
Write-Host "    LESS:        $env:LESS`n"

# 4. Check for Git-related Aliases
Write-Host "[5] Git-related Aliases:" -ForegroundColor Yellow
$gitAliases = Get-Alias | Where-Object { 
    $_.Name -like "*git*" -or 
    $_.Definition -like "*git*" -or 
    $_.Definition -like "*less*" -or 
    $_.Definition -like "*more*"
}
if ($gitAliases) {
    $gitAliases | Format-Table Name, Definition -AutoSize
} else {
    Write-Host "    None found`n" -ForegroundColor Green
}

# 5. Check for Out-Default Override
Write-Host "[6] Checking for Out-Default Override:" -ForegroundColor Yellow
$outDefault = Get-Command Out-Default -ErrorAction SilentlyContinue
if ($outDefault.CommandType -eq "Function") {
    Write-Host "    WARNING: Out-Default is overridden (this causes pager issues)!" -ForegroundColor Red
    Write-Host "    Function definition:" -ForegroundColor Red
    Get-Command Out-Default | Select-Object -ExpandProperty Definition
} else {
    Write-Host "    OK - Out-Default is not overridden`n" -ForegroundColor Green
}

# 6. Check Git Config
Write-Host "[7] Git Configuration (pager settings):" -ForegroundColor Yellow
Write-Host "    core.pager (global): " -NoNewline
$globalPager = git config --global core.pager 2>$null
if ($globalPager) {
    Write-Host "$globalPager" -ForegroundColor Red
} else {
    Write-Host "Not set" -ForegroundColor Green
}

Write-Host "    core.pager (local):  " -NoNewline
$localPager = git config --local core.pager 2>$null
if ($localPager) {
    Write-Host "$localPager" -ForegroundColor Red
} else {
    Write-Host "Not set" -ForegroundColor Green
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Recommendations:" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

if (Test-Path $PROFILE) {
    Write-Host "1. Review your PowerShell profile above" -ForegroundColor Yellow
    Write-Host "2. Look for these problematic patterns:" -ForegroundColor Yellow
    Write-Host "   - Set-Alias for git, Out-Default, or Out-Host" -ForegroundColor White
    Write-Host "   - Functions wrapping git commands" -ForegroundColor White
    Write-Host "   - References to 'less', 'more', or other pagers" -ForegroundColor White
    Write-Host "   - Environment variable assignments (`$env:PAGER, `$env:GIT_PAGER)" -ForegroundColor White
    Write-Host "`n3. To edit your profile, run:" -ForegroundColor Yellow
    Write-Host "   notepad `$PROFILE" -ForegroundColor Cyan
}

Write-Host "`nPress any key to continue..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

