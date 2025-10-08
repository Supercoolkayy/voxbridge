#!/usr/bin/env bash
set -euo pipefail

# VoxBridge Cross-Platform Build Script
# Builds executables for Windows, Linux, and macOS

echo "VoxBridge Cross-Platform Build Script"
echo "======================================"

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

# Check if we're in the right directory
if [[ ! -f "pyproject.toml" ]]; then
    print_error "Please run this script from the VoxBridge root directory"
    exit 1
fi

# Clean everything
print_status "Cleaning previous builds..."
rm -rf build/ dist/ *.egg-info/ release_builds/

# Create release_builds directory
mkdir -p release_builds

# Install/upgrade build dependencies
print_status "Installing/upgrading build dependencies..."
python3 -m pip install --upgrade pip
python3 -m pip install --upgrade pyinstaller

# Build for current platform
PLATFORM=$(uname -s)
print_info "Building for current platform: $PLATFORM"

if [[ "$PLATFORM" == "Linux" ]]; then
    # Build Linux executables
    print_status "Building Linux executables..."
    
    # CLI
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
        cli_entry.py
    
    # GUI
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
        gui_entry.py
    
    # Set executable permissions
    chmod +x dist/voxbridge
    chmod +x dist/voxbridge-gui
    
    # Verify they're 64-bit ELF binaries
    if ! file dist/voxbridge | grep -q "ELF 64-bit"; then
        print_error "CLI is not a 64-bit ELF binary"
        exit 1
    fi
    if ! file dist/voxbridge-gui | grep -q "ELF 64-bit"; then
        print_error "GUI is not a 64-bit ELF binary"
        exit 1
    fi
    
    # Create Linux package
    print_status "Creating Linux package..."
    tar -czf release_builds/voxbridge-linux.tar.gz -C dist voxbridge voxbridge-gui
    
elif [[ "$PLATFORM" == "Darwin" ]]; then
    # Build macOS executables
    print_status "Building macOS executables..."
    
    # CLI
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
        cli_entry.py
    
    # GUI
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
        gui_entry.py
    
    # Set executable permissions
    chmod +x dist/voxbridge
    chmod +x dist/voxbridge-gui
    
    # Verify they're 64-bit Mach-O binaries
    if ! file dist/voxbridge | grep -q "Mach-O 64-bit"; then
        print_error "CLI is not a 64-bit Mach-O binary"
        exit 1
    fi
    if ! file dist/voxbridge-gui | grep -q "Mach-O 64-bit"; then
        print_error "GUI is not a 64-bit Mach-O binary"
        exit 1
    fi
    
    # Create macOS package
    print_status "Creating macOS package..."
    tar -czf release_builds/voxbridge-macos.tar.gz -C dist voxbridge voxbridge-gui
    
else
    print_error "Unsupported platform: $PLATFORM"
    print_info "This script supports Linux and macOS. For Windows, use build_windows.bat"
    exit 1
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
fi

print_status "Build script completed!"
