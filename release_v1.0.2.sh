#!/bin/bash
# Release script for VoxBridge v1.0.2

set -e

echo "VoxBridge Release v1.0.2"
echo "========================="
echo "Fixes:"
echo "- Fixed Blender export_colors parameter error"
echo "- Removed all emojis from output"
echo "- Improved error handling"

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf build/ dist/ *.egg-info/

# Build package
echo "Building package..."
python -m build

# Check build artifacts
echo "Build artifacts:"
ls -la dist/

# Upload to PyPI (requires twine)
echo "Uploading to PyPI..."
python -m twine upload dist/*

echo "Release v1.0.2 completed!"
echo ""
echo "Users can now upgrade with:"
echo "  pip install --upgrade voxbridge"
echo "  pipx upgrade voxbridge"
echo ""
echo "This fixes the Blender export_colors error!" 