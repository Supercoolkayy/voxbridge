#!/bin/bash
# VoxBridge Simple Build Script
# Creates working executables without waiting for pkg compilation

set -e

echo "🚀 VoxBridge Simple Build Script"
echo "================================"

# Check dependencies
echo "📋 Checking dependencies..."

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found. Please install Python 3.8+"
    exit 1
fi

# Check pyinstaller
if ! python3 -c "import PyInstaller" &> /dev/null; then
    echo "📦 Installing PyInstaller..."
    pip3 install pyinstaller
fi

echo "✅ Dependencies ready"

# Step 1: Create a simple Node.js wrapper
echo ""
echo "🔧 Step 1: Creating Node.js wrapper..."

cat > build/voxbridge-node << 'EOF'
#!/bin/bash
# VoxBridge Node.js Wrapper
# This script runs the Node.js processing using the local installation

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NODE_SCRIPTS_DIR="$SCRIPT_DIR/../node_scripts"

if [ ! -d "$NODE_SCRIPTS_DIR" ]; then
    echo "❌ Node.js scripts directory not found: $NODE_SCRIPTS_DIR"
    exit 1
fi

cd "$NODE_SCRIPTS_DIR"
node index.js "$@"
EOF

chmod +x build/voxbridge-node
echo "✅ Node.js wrapper created: build/voxbridge-node"

# Step 2: Build Python CLI
echo ""
echo "🔧 Step 2: Building Python CLI..."
pyinstaller --onefile --name voxbridge-cli \
    --add-data "voxbridge:voxbridge" \
    --add-data "build/voxbridge-node:voxbridge-node" \
    --add-data "node_scripts:node_scripts" \
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
    --add-data "node_scripts:node_scripts" \
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

# Step 4: Create release package
echo ""
echo "🔧 Step 4: Creating release package..."

# Create release directory
mkdir -p release/simple

# Copy executables
cp dist/voxbridge-cli release/simple/
cp dist/voxbridge-gui release/simple/
cp build/voxbridge-node release/simple/

# Copy Node.js scripts
cp -r node_scripts release/simple/

# Create launcher scripts
cat > release/simple/voxbridge << 'EOF'
#!/bin/bash
# VoxBridge Launcher
cd "$(dirname "$0")"
./voxbridge-gui "$@"
EOF

cat > release/simple/voxbridge-cli << 'EOF'
#!/bin/bash
# VoxBridge CLI Launcher
cd "$(dirname "$0")"
./voxbridge-cli "$@"
EOF

chmod +x release/simple/voxbridge
chmod +x release/simple/voxbridge-cli

# Create README
cat > release/simple/README.md << 'EOF'
# VoxBridge Simple Build

This is a working VoxBridge build that includes both GUI and CLI.

## Files

- `voxbridge-gui` - Graphical interface
- `voxbridge-cli` - Command line interface  
- `voxbridge-node` - Node.js processor (wrapper script)
- `node_scripts/` - Node.js processing scripts
- `voxbridge` - GUI launcher
- `voxbridge-cli` - CLI launcher

## Usage

### GUI
```bash
./voxbridge
# or
./voxbridge-gui
```

### CLI
```bash
./voxbridge-cli convert --input file.glb --output output --target unity --fast
# or
./voxbridge-cli --help
```

## Requirements

- Linux system
- No additional dependencies required (all bundled)

## Features

- ✅ Smart file detection (static vs animated)
- ✅ Speed modes (fast, balanced, full)
- ✅ Texture optimization
- ✅ Unity and Roblox support
- ✅ Comprehensive reporting
- ✅ Clean ZIP packaging
EOF

# Create ZIP package
cd release/simple
zip -r ../voxbridge-simple-linux.zip *
cd ../..

echo "✅ Simple build package created: release/voxbridge-simple-linux.zip"

# Summary
echo ""
echo "🎉 Simple Build Complete!"
echo "========================"
echo "📦 Files created:"
echo "  - release/simple/voxbridge-gui (GUI executable)"
echo "  - release/simple/voxbridge-cli (CLI executable)"
echo "  - release/simple/voxbridge-node (Node.js wrapper)"
echo "  - release/simple/node_scripts/ (Node.js scripts)"
echo "  - release/voxbridge-simple-linux.zip (Complete package)"
echo ""
echo "🚀 To run:"
echo "  cd release/simple"
echo "  ./voxbridge          # GUI"
echo "  ./voxbridge-cli --help  # CLI"
