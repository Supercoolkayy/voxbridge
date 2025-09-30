#!/bin/bash
# Create Windows Source Package
# This script prepares a portable source package for Windows builds

set -e

echo "🚀 Creating Windows Source Package"
echo "=================================="

# Create Windows source directory
mkdir -p release/windows_source

# Step 1: Build Node.js binary for Windows (on Linux)
echo "🔧 Step 1: Building Node.js binary for Windows..."
cd node_scripts

# Install dependencies
echo "📦 Installing Node.js dependencies..."
npm install

# Build Windows binary
echo "🔨 Compiling Node.js binary for Windows..."
pkg index.js --targets node18-win-x64 --output ../build/voxbridge-node.exe

cd ..
echo "✅ Node.js binary created: build/voxbridge-node.exe"

# Step 2: Copy Python source files
echo ""
echo "🔧 Step 2: Copying Python source files..."

# Copy main Python files
cp -r voxbridge release/windows_source/
cp voxbridge/cli.py release/windows_source/
cp voxbridge/gui/app.py release/windows_source/
cp requirements.txt release/windows_source/

# Copy build files
cp build/voxbridge-node.exe release/windows_source/
cp voxbridge_cli.spec release/windows_source/
cp voxbridge_gui.spec release/windows_source/
cp build_windows.bat release/windows_source/

# Step 3: Create Windows-specific files
echo ""
echo "🔧 Step 3: Creating Windows-specific files..."

# Create Windows requirements
cat > release/windows_source/requirements-windows.txt << 'EOF'
# VoxBridge Windows Requirements
# Install with: pip install -r requirements-windows.txt

# Core dependencies
trimesh>=4.8.1
pygltflib>=1.15.0
numpy<2.0.0
rich>=13.0.0
typer>=0.9.0

# GUI dependencies
tkinter  # Usually included with Python

# Optional dependencies for better performance
# scipy>=1.9.0
# pillow>=9.0.0
EOF

# Create Windows setup script
cat > release/windows_source/setup_windows.bat << 'EOF'
@echo off
echo VoxBridge Windows Setup
echo ======================

echo Installing Python dependencies...
pip install -r requirements-windows.txt

echo.
echo Installing PyInstaller...
pip install pyinstaller

echo.
echo Installing pkg for Node.js...
npm install -g pkg

echo.
echo Setup complete! Run build_windows.bat to build executables.
pause
EOF

# Create README for Windows
cat > release/windows_source/README_WINDOWS.md << 'EOF'
# VoxBridge Windows Source Package

This package contains everything needed to build VoxBridge for Windows.

## Quick Start

1. **Install Prerequisites:**
   - Python 3.8+ (https://python.org)
   - Node.js 18+ (https://nodejs.org)
   - Git (optional, for development)

2. **Setup:**
   ```cmd
   setup_windows.bat
   ```

3. **Build:**
   ```cmd
   build_windows.bat
   ```

## Files Included

- `voxbridge/` - Python source code
- `cli.py` - CLI entry point
- `gui/app.py` - GUI entry point
- `voxbridge-node.exe` - Pre-built Node.js processor
- `voxbridge_cli.spec` - PyInstaller spec for CLI
- `voxbridge_gui.spec` - PyInstaller spec for GUI
- `build_windows.bat` - Build script
- `setup_windows.bat` - Setup script
- `requirements-windows.txt` - Python dependencies

## Building

The build process will create:
- `dist/voxbridge-cli.exe` - Command line interface
- `dist/voxbridge-gui.exe` - Graphical interface
- `release/windows/` - Final package directory

## Features

- **Smart Detection**: Automatically detects static vs animated files
- **Dual Processing**: Trimesh for static, Node.js for complex files
- **Speed Modes**: Fast (512px), Balanced (1024px), Full (2048px)
- **Platform Support**: Unity and Roblox optimization
- **GUI & CLI**: Both graphical and command-line interfaces

## Troubleshooting

- If PyInstaller fails, try: `pip install --upgrade pyinstaller`
- If pkg fails, try: `npm install -g pkg@latest`
- For large files, increase Windows temp directory size
- Antivirus may flag executables - add to exclusions if needed

## Support

For issues and updates, visit the VoxBridge repository.
EOF

# Step 4: Create ZIP package
echo ""
echo "🔧 Step 4: Creating ZIP package..."

cd release/windows_source
zip -r ../voxbridge_windows_source.zip *
cd ../..

echo "✅ Windows source package created: release/voxbridge_windows_source.zip"

# Step 5: Create Linux build script
echo ""
echo "🔧 Step 5: Creating Linux build script..."

cat > build_all.sh << 'EOF'
#!/bin/bash
# VoxBridge Complete Build Script
# Builds both Linux and Windows packages

set -e

echo "🚀 VoxBridge Complete Build"
echo "==========================="

# Build Linux
echo "🔧 Building Linux package..."
chmod +x build_linux.sh
./build_linux.sh

# Create Windows source
echo ""
echo "🔧 Creating Windows source package..."
chmod +x create_windows_source.sh
./create_windows_source.sh

echo ""
echo "🎉 Build Complete!"
echo "=================="
echo "📦 Linux: release/linux/voxbridge-x86_64.AppImage"
echo "📦 Windows Source: release/voxbridge_windows_source.zip"
echo ""
echo "🚀 Next steps:"
echo "  1. Test Linux AppImage locally"
echo "  2. Copy Windows source to Windows machine"
echo "  3. Run build_windows.bat on Windows"
EOF

chmod +x build_all.sh

# Summary
echo ""
echo "🎉 Windows Source Package Complete!"
echo "==================================="
echo "📦 Files created:"
echo "  - release/voxbridge_windows_source.zip (Windows source package)"
echo "  - build_all.sh (Complete build script)"
echo ""
echo "🚀 Next steps:"
echo "  1. Copy voxbridge_windows_source.zip to Windows machine"
echo "  2. Extract and run setup_windows.bat"
echo "  3. Run build_windows.bat to create executables"
