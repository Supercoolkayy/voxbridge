#!/usr/bin/env bash
set -euo pipefail

# VoxBridge Release Script
# This script automates the release process for GitHub and PyPI

echo "VoxBridge Release Script v1.0.0"
echo "================================="

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo "Error: pyproject.toml not found. Please run this script from the project root."
    exit 1
fi

# Check if git is available
if ! command -v git &> /dev/null; then
    echo "Error: git is not installed or not in PATH"
    exit 1
fi

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo "Error: Not in a git repository"
    exit 1
fi

# Check if we have uncommitted changes
if [ -n "$(git status --porcelain)" ]; then
    echo "Warning: You have uncommitted changes. Please commit or stash them first."
    git status --short
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Get current version from pyproject.toml
CURRENT_VERSION=$(grep '^version = ' pyproject.toml | cut -d'"' -f2)
echo "Current version: $CURRENT_VERSION"

# Check if tag already exists
if git tag -l | grep -q "v$CURRENT_VERSION"; then
    echo "Error: Tag v$CURRENT_VERSION already exists"
    exit 1
fi

echo ""
echo "Step 1: Building package..."
if [ -f "scripts/build_cli.sh" ]; then
    bash scripts/build_cli.sh
else
    echo "Warning: build_cli.sh not found, using default build"
    python -m build
fi

echo ""
echo "Step 2: Testing local installation..."
pip install -e . > /dev/null 2>&1 || {
    echo "Error: Local installation failed"
    exit 1
}

echo "Testing CLI commands..."
voxbridge --help > /dev/null 2>&1 || {
    echo "Error: voxbridge --help failed"
    exit 1
}

voxbridge doctor > /dev/null 2>&1 || {
    echo "Error: voxbridge doctor failed"
    exit 1
}

echo "✅ Local installation test passed"

echo ""
echo "Step 3: Preparing git commit..."
git add .

# Create commit message
COMMIT_MSG="v$CURRENT_VERSION: Universal CLI with enhanced help and GUI

- Enhanced CLI with subcommands: convert, doctor, batch, help
- Rich colored output and comprehensive help
- Tkinter GUI interface
- Automated PyPI publishing
- Professional documentation"

git commit -m "$COMMIT_MSG"

echo ""
echo "Step 4: Pushing to GitHub..."
git push origin main

echo ""
echo "Step 5: Creating and pushing release tag..."
git tag -a "v$CURRENT_VERSION" -m "Release v$CURRENT_VERSION"
git push origin "v$CURRENT_VERSION"

echo ""
echo "Step 6: Release Summary"
echo "======================="
echo "Version: v$CURRENT_VERSION"
echo "GitHub: https://github.com/Supercoolkayy/voxbridge"
echo "PyPI: https://pypi.org/project/voxbridge/"
echo ""
echo "Installation:"
echo "  pip install voxbridge"
echo ""
echo "Usage:"
echo "  voxbridge --help"
echo "  voxbridge convert --input model.glb --target unity"
echo "  voxbridge-gui"
echo ""
echo "The GitHub Actions workflow will automatically:"
echo "- Build the package"
echo "- Run tests"
echo "- Publish to PyPI"
echo "- Create GitHub Release"
echo ""
echo "Check the GitHub Actions tab for build status:"
echo "https://github.com/Supercoolkayy/voxbridge/actions"
echo ""
echo "Release process initiated successfully!" 