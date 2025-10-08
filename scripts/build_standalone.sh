#!/usr/bin/env bash
set -euo pipefail

# VoxBridge Standalone Build Script
# Creates proper 64-bit executables for Windows, Linux, and macOS

echo "VoxBridge Standalone Build Script"
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[OK] $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}[WARN] $1${NC}"
}

print_error() {
    echo -e "${RED}[ERROR] $1${NC}"
}

print_info() {
    echo -e "${BLUE}[INFO] $1${NC}"
}

# Check Python version
python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 9) else 1)"; then
    print_error "Python 3.9+ required. Found: $python_version"
    exit 1
fi

print_status "Python version check passed: $python_version"

# Detect platform
PLATFORM=$(uname -s)
ARCH=$(uname -m)

print_info "Building for platform: $PLATFORM ($ARCH)"

# Clean previous builds
print_status "Cleaning previous builds..."
rm -rf build/ dist/ *.egg-info/ release_builds/

# Install/upgrade PyInstaller
print_status "Installing/upgrading PyInstaller..."
python3 -m pip install --upgrade pip
python3 -m pip install --upgrade pyinstaller

# Create release_builds directory
mkdir -p release_builds

# Build CLI executable
print_status "Building CLI executable..."
pyinstaller \
    --onefile \
    --name voxbridge \
    --distpath dist \
    --workpath build \
    --specpath . \
    --clean \
    --noconfirm \
    --console \
    --target-arch x86_64 \
    --strip \
    --noupx \
    --add-data "voxbridge:voxbridge" \
    --hidden-import voxbridge.converter \
    --hidden-import voxbridge.platform_profiles \
    --hidden-import voxbridge.texture_optimizer \
    --hidden-import voxbridge.benchmark \
    --hidden-import voxbridge.gui.app \
    --hidden-import pygltflib \
    --hidden-import rich \
    --hidden-import typer \
    --hidden-import PIL \
    --hidden-import numpy \
    --hidden-import scipy \
    --hidden-import jsonschema \
    voxbridge/cli.py

# Build GUI executable
print_status "Building GUI executable..."
pyinstaller \
    --onefile \
    --name voxbridge-gui \
    --distpath dist \
    --workpath build \
    --specpath . \
    --clean \
    --noconfirm \
    --windowed \
    --target-arch x86_64 \
    --strip \
    --noupx \
    --add-data "voxbridge:voxbridge" \
    --hidden-import voxbridge.converter \
    --hidden-import voxbridge.platform_profiles \
    --hidden-import voxbridge.texture_optimizer \
    --hidden-import voxbridge.benchmark \
    --hidden-import voxbridge.gui.app \
    --hidden-import pygltflib \
    --hidden-import rich \
    --hidden-import typer \
    --hidden-import PIL \
    --hidden-import numpy \
    --hidden-import scipy \
    --hidden-import jsonschema \
    --hidden-import tkinter \
    --hidden-import tkinter.ttk \
    --hidden-import tkinter.filedialog \
    --hidden-import tkinter.messagebox \
    voxbridge/gui/app.py

# Verify executables were created
if [[ ! -f "dist/voxbridge" ]] || [[ ! -f "dist/voxbridge-gui" ]]; then
    print_error "Failed to create executables"
    exit 1
fi

# Set executable permissions on Linux/macOS
if [[ "$PLATFORM" == "Linux" ]] || [[ "$PLATFORM" == "Darwin" ]]; then
    print_status "Setting executable permissions..."
    chmod +x dist/voxbridge
    chmod +x dist/voxbridge-gui
fi

# Verify file types and architecture
print_status "Verifying executables..."

if [[ "$PLATFORM" == "Linux" ]]; then
    print_info "CLI file info:"
    file dist/voxbridge
    print_info "GUI file info:"
    file dist/voxbridge-gui
    
    # Check if they're 64-bit ELF binaries
    if ! file dist/voxbridge | grep -q "ELF 64-bit"; then
        print_error "CLI is not a 64-bit ELF binary"
        exit 1
    fi
    if ! file dist/voxbridge-gui | grep -q "ELF 64-bit"; then
        print_error "GUI is not a 64-bit ELF binary"
        exit 1
    fi
    print_status "Both executables are valid 64-bit ELF binaries"
    
elif [[ "$PLATFORM" == "Darwin" ]]; then
    print_info "CLI file info:"
    file dist/voxbridge
    print_info "GUI file info:"
    file dist/voxbridge-gui
    
    # Check if they're 64-bit Mach-O binaries
    if ! file dist/voxbridge | grep -q "Mach-O 64-bit"; then
        print_error "CLI is not a 64-bit Mach-O binary"
        exit 1
    fi
    if ! file dist/voxbridge-gui | grep -q "Mach-O 64-bit"; then
        print_error "GUI is not a 64-bit Mach-O binary"
        exit 1
    fi
    print_status "Both executables are valid 64-bit Mach-O binaries"
    
elif [[ "$PLATFORM" == "MINGW"* ]] || [[ "$PLATFORM" == "CYGWIN"* ]] || [[ "$PLATFORM" == "MSYS"* ]]; then
    print_info "CLI file info:"
    file dist/voxbridge
    print_info "GUI file info:"
    file dist/voxbridge-gui
    
    # Check if they're PE executables
    if ! file dist/voxbridge | grep -q "PE32+"; then
        print_error "CLI is not a 64-bit PE executable"
        exit 1
    fi
    if ! file dist/voxbridge-gui | grep -q "PE32+"; then
        print_error "GUI is not a 64-bit PE executable"
        exit 1
    fi
    print_status "Both executables are valid 64-bit PE executables"
fi

# Test executables
print_status "Testing executables..."

# Test CLI
print_info "Testing CLI --help..."
if ! dist/voxbridge --help > /dev/null 2>&1; then
    print_error "CLI --help test failed"
    exit 1
fi
print_status "CLI --help test passed"

# Test GUI (just check if it starts without crashing)
print_info "Testing GUI startup..."
timeout 5s dist/voxbridge-gui --help > /dev/null 2>&1 || true
print_status "GUI startup test completed"

# Create platform-specific packages
print_status "Creating platform-specific packages..."

if [[ "$PLATFORM" == "Linux" ]]; then
    # Create Linux package
    print_info "Creating Linux package..."
    tar -czf release_builds/voxbridge-linux.tar.gz -C dist voxbridge voxbridge-gui
    
    # Verify package
    print_info "Verifying Linux package..."
    tar -tzf release_builds/voxbridge-linux.tar.gz
    
elif [[ "$PLATFORM" == "Darwin" ]]; then
    # Create macOS package
    print_info "Creating macOS package..."
    tar -czf release_builds/voxbridge-macos.tar.gz -C dist voxbridge voxbridge-gui
    
    # Verify package
    print_info "Verifying macOS package..."
    tar -tzf release_builds/voxbridge-macos.tar.gz
    
elif [[ "$PLATFORM" == "MINGW"* ]] || [[ "$PLATFORM" == "CYGWIN"* ]] || [[ "$PLATFORM" == "MSYS"* ]]; then
    # Create Windows package
    print_info "Creating Windows package..."
    cd dist
    zip -r ../release_builds/voxbridge-windows.zip voxbridge voxbridge-gui
    cd ..
    
    # Verify package
    print_info "Verifying Windows package..."
    unzip -l release_builds/voxbridge-windows.zip
fi

# Generate checksums
print_status "Generating checksums..."
cd release_builds
sha256sum *.tar.gz *.zip > checksums.txt 2>/dev/null || true
cd ..

# Display final results
print_status "Build completed successfully!"
echo ""
echo " Built executables:"
ls -lh dist/
echo ""
echo " Release packages:"
ls -lh release_builds/
echo ""
echo " Checksums:"
cat release_builds/checksums.txt 2>/dev/null || echo "No checksums generated"
echo ""

# Instructions for testing
print_info "Testing instructions:"
echo ""
if [[ "$PLATFORM" == "Linux" ]]; then
    echo "To test on Linux:"
    echo "  tar -xzf release_builds/voxbridge-linux.tar.gz"
    echo "  ./voxbridge --help"
    echo "  ./voxbridge-gui"
elif [[ "$PLATFORM" == "Darwin" ]]; then
    echo "To test on macOS:"
    echo "  tar -xzf release_builds/voxbridge-macos.tar.gz"
    echo "  ./voxbridge --help"
    echo "  ./voxbridge-gui"
elif [[ "$PLATFORM" == "MINGW"* ]] || [[ "$PLATFORM" == "CYGWIN"* ]] || [[ "$PLATFORM" == "MSYS"* ]]; then
    echo "To test on Windows:"
    echo "  unzip release_builds/voxbridge-windows.zip"
    echo "  .\\voxbridge.exe --help"
    echo "  .\\voxbridge-gui.exe"
fi

print_status "Build script completed!"
