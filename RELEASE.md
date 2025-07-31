# VoxBridge Release Guide

## Pre-Release Checklist

1. **Update Version**: Ensure version is set to `1.0.0` in:

   - `pyproject.toml`
   - `voxbridge/__init__.py`
   - `voxbridge/gui/__init__.py`

2. **Test Build**: Run local build and test

   ```bash
   bash scripts/build_cli.sh
   pipx install --force ./dist/voxbridge-1.0.0-py3-none-any.whl
   voxbridge --help
   voxbridge doctor
   ```

3. **Test PyPI Upload** (Optional):

   ```bash
   # Test upload to TestPyPI first
   python -m twine upload --repository testpypi dist/*

   # Test installation from TestPyPI
   pip install --index-url https://test.pypi.org/simple/ voxbridge
   ```

## Release Process

### 1. Create and Push Tag

```bash
# Create annotated tag
git tag -a v1.0.0 -m "Release v1.0.0"

# Push tag to trigger GitHub Actions
git push origin v1.0.0
```

### 2. GitHub Actions Workflow

The `.github/workflows/release.yml` workflow will automatically:

1. Build the package using `python -m build`
2. Upload to PyPI (if tag starts with `refs/tags/`)
3. Create a GitHub Release with built artifacts

### 3. Set PyPI API Token

1. Go to [PyPI Account Settings](https://pypi.org/manage/account/)
2. Create an API token
3. Add the token as a GitHub Secret:
   - Go to your repository settings
   - Navigate to Secrets and Variables > Actions
   - Create a new secret named `PYPI_API_TOKEN`
   - Paste your PyPI API token

## Post-Release Verification

1. **Check PyPI**: Verify package appears on [PyPI](https://pypi.org/project/voxbridge/)
2. **Test Installation**:
   ```bash
   pipx install voxbridge
   voxbridge --help
   ```
3. **Test GUI**:
   ```bash
   voxbridge-gui
   ```
4. **Test Doctor**:
   ```bash
   voxbridge doctor
   ```

## Manual Release (If GitHub Actions Fails)

If the automated workflow fails, you can manually release:

```bash
# Build package
python -m build

# Upload to PyPI
python -m twine upload dist/*

# Create GitHub Release manually
# Go to GitHub > Releases > Create new release
# Upload dist/* files as assets
```

## Version Management

For future releases:

1. Update version in `pyproject.toml` and `voxbridge/__init__.py`
2. Create new tag: `git tag -a v1.1.0 -m "Release v1.1.0"`
3. Push tag: `git push origin v1.1.0`

## Troubleshooting

### Build Issues

- Ensure all dependencies are installed: `pip install -e .[dev]`
- Check Python version compatibility (3.9+)
- Verify `pyproject.toml` syntax

### PyPI Upload Issues

- Verify API token is correct
- Check package name availability
- Ensure version number is unique

### GitHub Actions Issues

- Check workflow logs in Actions tab
- Verify secrets are properly configured
- Ensure tag format matches workflow trigger
