#!/usr/bin/env bash
set -euo pipefail

echo "Building VoxBridge CLI package..."

# Clean previous builds
rm -rf dist build *.egg-info

# Upgrade pip and build tools
python -m pip install --upgrade pip build

# Build the package
python -m build

echo "Built artifacts:"
ls -lh dist

echo "Build complete!" 