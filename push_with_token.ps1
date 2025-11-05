# GitHub Push Script - Personal Access Token Method
# Set your token as an environment variable: $env:GITHUB_TOKEN = "your_token_here"
# Or use: git credential manager

if ($env:GITHUB_TOKEN) {
    $token = $env:GITHUB_TOKEN
    git push https://${token}@github.com/cryptolavar-hub/Q2O.git main
} else {
    Write-Host "ERROR: GITHUB_TOKEN environment variable not set!" -ForegroundColor Red
    Write-Host "Set it with: `$env:GITHUB_TOKEN = 'your_token_here'" -ForegroundColor Yellow
    Write-Host "Or just use: git push" -ForegroundColor Yellow
    git push
}

