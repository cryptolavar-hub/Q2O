# GitHub Push Instructions - Personal Access Token Method

## Step 1: Generate Personal Access Token

1. Go to: https://github.com/settings/tokens
2. Click "Generate new token" → "Generate new token (classic)"
3. Give it a name: "Q2O Repository Access"
4. Select scopes:
   - ✅ `repo` (Full control of private repositories)
   - ✅ `workflow` (if you want to update GitHub Actions)
5. Click "Generate token"
6. **COPY THE TOKEN IMMEDIATELY** - you won't see it again!

## Step 2: Push Using Token

Once you have the token, run:

```bash
git push https://<YOUR_TOKEN>@github.com/cryptolavar-hub/Q2O.git main
```

**Example:**
```bash
git push https://ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx@github.com/cryptolavar-hub/Q2O.git main
```

## Alternative: Use Git Credential Helper (More Secure)

Instead of putting token in command, use credential helper:

```bash
# Configure credential helper
git config --global credential.helper wincred

# Push (will prompt for username and password/token)
git push -u origin main
# Username: cryptolavar-hub
# Password: <paste your token here>
```

## Important Notes

- Never commit or share your token
- Tokens have expiration dates - note when yours expires
- Can revoke tokens anytime at: https://github.com/settings/tokens
- Use fine-grained tokens for better security (GitHub's newer token type)

