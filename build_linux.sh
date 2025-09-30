#!/bin/bash
# VoxBridge Linux Build Script
# Creates AppImage with both CLI and GUI

set -e

echo "🚀 VoxBridge Linux Build Script"
echo "================================"

# Check dependencies
echo "📋 Checking dependencies..."

# Check Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found. Please install Node.js 18+"
    exit 1
fi

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found. Please install Python 3.8+"
    exit 1
fi

# Check pkg
if ! command -v pkg &> /dev/null; then
    echo "📦 Installing pkg globally..."
    npm install -g pkg
fi

# Check pyinstaller
if ! python3 -c "import PyInstaller" &> /dev/null; then
    echo "📦 Installing PyInstaller..."
    pip3 install pyinstaller
fi

# Check appimagetool
if ! command -v appimagetool &> /dev/null; then
    echo "📦 Installing appimagetool..."
    wget -q https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage
    chmod +x appimagetool-x86_64.AppImage
    sudo mv appimagetool-x86_64.AppImage /usr/local/bin/appimagetool
fi

echo "✅ All dependencies found"

# Step 1: Build Node.js binary
echo ""
echo "🔧 Step 1: Building Node.js binary..."
cd node_scripts

# Install dependencies
echo "📦 Installing Node.js dependencies..."
npm install

# Build Linux binary
echo "🔨 Compiling Node.js binary for Linux..."
pkg index.js --targets node18-linux-x64 --output ../build/voxbridge-node

cd ..
echo "✅ Node.js binary created: build/voxbridge-node"

# Step 2: Build Python CLI
echo ""
echo "🔧 Step 2: Building Python CLI..."
pyinstaller --onefile --name voxbridge-cli \
    --add-data "voxbridge:voxbridge" \
    --add-data "build/voxbridge-node:voxbridge-node" \
    --hidden-import voxbridge.orchestrated_converter \
    --hidden-import voxbridge.utils.detect \
    --hidden-import voxbridge.trimesh_route \
    --hidden-import voxbridge.converter \
    --hidden-import voxbridge.platform_profiles \
    --hidden-import trimesh \
    --hidden-import pygltflib \
    --hidden-import numpy \
    --hidden-import rich \
    --hidden-import typer \
    voxbridge/cli.py

echo "✅ CLI executable created: dist/voxbridge-cli"

# Step 3: Build Python GUI
echo ""
echo "🔧 Step 3: Building Python GUI..."
pyinstaller --onefile --windowed --name voxbridge-gui \
    --add-data "voxbridge:voxbridge" \
    --add-data "build/voxbridge-node:voxbridge-node" \
    --hidden-import voxbridge.orchestrated_converter \
    --hidden-import voxbridge.utils.detect \
    --hidden-import voxbridge.trimesh_route \
    --hidden-import voxbridge.converter \
    --hidden-import voxbridge.platform_profiles \
    --hidden-import voxbridge.gui.app \
    --hidden-import tkinter \
    --hidden-import trimesh \
    --hidden-import pygltflib \
    --hidden-import numpy \
    voxbridge/gui/app.py

echo "✅ GUI executable created: dist/voxbridge-gui"

# Step 4: Create AppImage structure
echo ""
echo "🔧 Step 4: Creating AppImage structure..."

# Create AppImage directory
mkdir -p release/linux/voxbridge.AppDir/usr/bin
mkdir -p release/linux/voxbridge.AppDir/usr/share/voxbridge
mkdir -p release/linux/voxbridge.AppDir/usr/share/applications
mkdir -p release/linux/voxbridge.AppDir/usr/share/icons

# Copy executables
cp dist/voxbridge-cli release/linux/voxbridge.AppDir/usr/bin/
cp dist/voxbridge-gui release/linux/voxbridge.AppDir/usr/bin/
cp build/voxbridge-node release/linux/voxbridge.AppDir/usr/share/voxbridge/

# Create AppImage metadata
cat > release/linux/voxbridge.AppDir/AppRun << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
exec ./usr/bin/voxbridge-gui "$@"
EOF

chmod +x release/linux/voxbridge.AppDir/AppRun

# Create desktop file
cat > release/linux/voxbridge.AppDir/usr/share/applications/voxbridge.desktop << 'EOF'
[Desktop Entry]
Name=VoxBridge
Comment=VoxEdit to Unity/Roblox Converter
Exec=voxbridge-gui
Icon=voxbridge
Type=Application
Categories=Graphics;3DGraphics;
EOF

# Create AppImage spec
cat > release/linux/voxbridge.AppDir/voxbridge.desktop << 'EOF'
[Desktop Entry]
Name=VoxBridge
Comment=VoxEdit to Unity/Roblox Converter
Exec=voxbridge-gui
Icon=voxbridge
Type=Application
Categories=Graphics;3DGraphics;
EOF

# Create icon (simple placeholder)
echo "Creating icon..."
# This would normally be a proper icon file

# Step 5: Build AppImage
echo ""
echo "🔧 Step 5: Building AppImage..."
cd release/linux
appimagetool voxbridge.AppDir voxbridge-x86_64.AppImage

echo "✅ AppImage created: release/linux/voxbridge-x86_64.AppImage"

# Step 6: Create CLI-only AppImage
echo ""
echo "🔧 Step 6: Creating CLI-only AppImage..."

# Create CLI AppImage directory
mkdir -p voxbridge-cli.AppDir/usr/bin
mkdir -p voxbridge-cli.AppDir/usr/share/voxbridge
mkdir -p voxbridge-cli.AppDir/usr/share/applications

# Copy CLI executable
cp voxbridge.AppDir/usr/bin/voxbridge-cli voxbridge-cli.AppDir/usr/bin/
cp voxbridge.AppDir/usr/share/voxbridge/voxbridge-node voxbridge-cli.AppDir/usr/share/voxbridge/

# Create CLI AppRun
cat > voxbridge-cli.AppDir/AppRun << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
exec ./usr/bin/voxbridge-cli "$@"
EOF

chmod +x voxbridge-cli.AppDir/AppRun

# Create CLI desktop file
cat > voxbridge-cli.AppDir/voxbridge-cli.desktop << 'EOF'
[Desktop Entry]
Name=VoxBridge CLI
Comment=VoxEdit to Unity/Roblox Converter (Command Line)
Exec=voxbridge-cli
Icon=voxbridge
Type=Application
Categories=Graphics;3DGraphics;
Terminal=true
EOF

# Build CLI AppImage
appimagetool voxbridge-cli.AppDir voxbridge-cli-x86_64.AppImage

echo "✅ CLI AppImage created: release/linux/voxbridge-cli-x86_64.AppImage"

cd ../..

# Step 7: Create release package
echo ""
echo "🔧 Step 7: Creating release package..."

cd release/linux
tar -czf voxbridge-linux-x86_64.tar.gz voxbridge-x86_64.AppImage voxbridge-cli-x86_64.AppImage
cd ../..

echo "✅ Release package created: release/linux/voxbridge-linux-x86_64.tar.gz"

# Summary
echo ""
echo "🎉 Linux Build Complete!"
echo "========================"
echo "📦 Files created:"
echo "  - release/linux/voxbridge-x86_64.AppImage (GUI + CLI)"
echo "  - release/linux/voxbridge-cli-x86_64.AppImage (CLI only)"
echo "  - release/linux/voxbridge-linux-x86_64.tar.gz (Release package)"
echo ""
echo "🚀 To run:"
echo "  ./voxbridge-x86_64.AppImage"
echo "  ./voxbridge-cli-x86_64.AppImage --help"
