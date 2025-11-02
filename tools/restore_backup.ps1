# 1) Save current working tree (optional)
#git status --porcelain
#git add -A
#git commit -m "WIP: save current migration results (review before revert)" || Write-Host "No changes to commit"

# 2) Restore .bak files to overwrite broken files
Get-ChildItem .\agents\*.bak | ForEach-Object {
  $bak = $_.FullName
  $orig = $bak.Substring(0, $bak.Length - 4)   # remove .bak
  Write-Host "Restoring $orig from $bak"
  Move-Item -Path $bak -Destination $orig -Force
}

# 3) Verify syntax after restore
python -m py_compile .\agents\*.py
# Or run the validator you have:
python .\tools\validate_migration.py