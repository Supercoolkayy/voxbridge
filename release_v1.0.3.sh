#!/bin/bash
# Release script for VoxBridge v1.0.3

set -e

echo "VoxBridge Release v1.0.3"
echo "========================="
echo "Fixes:"
echo "- Fixed validation results showing 0 for GLB files"
echo "- Enhanced validate_output function to parse GLB files using pygltflib"
echo "- Now shows actual material, texture, mesh, and node counts for GLB files"
echo "- Improved error handling for file parsing"

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

echo "Release v1.0.3 completed!"
echo ""
echo "Users can now upgrade with:"
echo "  pip install --upgrade voxbridge"
echo "  pipx upgrade voxbridge"
echo ""
echo "This fixes the validation results showing 0 for GLB files!" 