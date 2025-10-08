#!/usr/bin/env bash
set -euo pipefail

echo "Building VoxBridge standalone binaries..."

# Install PyInstaller
python -m pip install --upgrade pyinstaller

# Build CLI binary
pyinstaller -n voxbridge --onefile voxbridge/cli.py

# Build GUI binary
pyinstaller -n voxbridge-gui --onefile voxbridge/gui/app.py

echo "Binaries in dist/"
ls -lh dist/

echo "Build complete!" 