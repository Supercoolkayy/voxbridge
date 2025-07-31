# Setting Up PyPI API Token for GitHub Actions

## Prerequisites

1. **PyPI Account**: You need a PyPI account to publish packages
2. **GitHub Repository**: Your repository should be on GitHub
3. **Repository Admin Access**: You need admin access to set repository secrets

## Step 1: Create PyPI Account

1. Go to https://pypi.org/account/register/
2. Create a new account
3. Verify your email address

## Step 2: Generate API Token

1. **Log in to PyPI**: https://pypi.org/account/login/
2. **Go to Account Settings**: Click on your username → "Account settings"
3. **API Tokens**: Click on "API tokens" in the left sidebar
4. **Add API Token**: Click "Add API token"
5. **Configure Token**:
   - **Token name**: `voxbridge-github-actions`
   - **Scope**: Select "Entire account (all projects)"
   - **Expires**: Choose expiration (recommend 1 year)
6. **Create Token**: Click "Create token"
7. **Copy Token**: Copy the generated token (you won't see it again!)

## Step 3: Add Token to GitHub Repository

1. **Go to GitHub Repository**: https://github.com/Supercoolkayy/voxbridge
2. **Settings**: Click on "Settings" tab
3. **Secrets and Variables**: Click on "Secrets and variables" → "Actions"
4. **New Repository Secret**: Click "New repository secret"
5. **Configure Secret**:
   - **Name**: `PYPI_API_TOKEN`
   - **Value**: Paste the PyPI API token you copied
6. **Add Secret**: Click "Add secret"

## Step 4: Verify Setup

1. **Check Secret**: The secret should appear in the list (value will be hidden)
2. **Test Workflow**: The GitHub Actions workflow will use this token automatically

## Step 5: Test Release

1. **Create Tag**: When you push a tag, the workflow will run
2. **Monitor Actions**: Check the "Actions" tab in your repository
3. **Verify PyPI**: Check https://pypi.org/project/voxbridge/ after successful release

## Troubleshooting

### Token Not Working

- Ensure the token has the correct scope (Entire account)
- Check that the token hasn't expired
- Verify the secret name is exactly `PYPI_API_TOKEN`

### Workflow Fails

- Check the Actions tab for error messages
- Ensure the repository has Actions enabled
- Verify the workflow file is in `.github/workflows/release.yml`

### Package Already Exists

- If the package name is taken, you'll need to choose a different name
- Update `pyproject.toml` with a new package name
- Consider using a namespace like `dappsoverapps-voxbridge`

## Security Notes

- **Never commit the token** to your repository
- **Use repository secrets** only, not environment secrets
- **Rotate tokens regularly** (recommend yearly)
- **Limit token scope** if possible (though PyPI requires account-wide scope)

## Alternative: Manual Upload

If you prefer manual upload instead of GitHub Actions:

```bash
# Install twine
pip install twine

# Build package
python -m build

# Upload to PyPI
twine upload dist/*

# You'll be prompted for username and password/token
```

## Next Steps

Once the token is set up:

1. **Test in WSL Ubuntu**:

   ```bash
   wsl
   cd /home/emmzycode/voxbridge
   voxbridge --help
   ```

2. **Run Release Script**:

   ```bash
   bash scripts/release.sh
   ```

3. **Monitor Release**:
   - Check GitHub Actions tab
   - Verify PyPI publication
   - Test installation: `pip install voxbridge`

## Support

If you encounter issues:

- **PyPI Help**: https://pypi.org/help/
- **GitHub Actions**: https://docs.github.com/en/actions
- **Repository Issues**: https://github.com/Supercoolkayy/voxbridge/issues
