#!/bin/bash
# VoxBridge macOS Build Script
# Run this script on macOS to build macOS executables

set -e  # Exit on any error

echo "🍎 VoxBridge macOS Build Script"
echo "==============================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    print_error "This script must be run on macOS"
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    print_error "Please run this script from the VoxBridge root directory"
    exit 1
fi

# Create output directories
print_status "Creating output directories..."
mkdir -p dist/macos
mkdir -p release_builds

# Function to build executable
build_executable() {
    local platform=$1
    local output_dir=$2
    local executable_name=$3
    local extra_args=$4
    
    print_status "Building $platform CLI executable..."
    
    # Build with PyInstaller
    python3 -m PyInstaller \
        --onefile \
        --name "$executable_name" \
        --distpath "$output_dir" \
        --add-data "voxbridge:voxbridge" \
        --hidden-import "pygltflib" \
        --hidden-import "PIL" \
        --hidden-import "numpy" \
        --hidden-import "scipy" \
        --hidden-import "jsonschema" \
        --hidden-import "rich" \
        --hidden-import "typer" \
        --hidden-import "trimesh" \
        --hidden-import "trimesh.visual" \
        --hidden-import "trimesh.scene" \
        $extra_args \
        cli_entry.py
    
    if [ $? -eq 0 ]; then
        print_success "$platform CLI executable built successfully"
    else
        print_error "Failed to build $platform CLI executable"
        exit 1
    fi
}

# Function to build GUI
build_gui() {
    local platform=$1
    local output_dir=$2
    local executable_name=$3
    local extra_args=$4
    
    print_status "Building $platform GUI executable..."
    
    # Build with PyInstaller
    python3 -m PyInstaller \
        --onefile \
        --windowed \
        --name "$executable_name" \
        --distpath "$output_dir" \
        --add-data "voxbridge:voxbridge" \
        --hidden-import "pygltflib" \
        --hidden-import "PIL" \
        --hidden-import "numpy" \
        --hidden-import "scipy" \
        --hidden-import "jsonschema" \
        --hidden-import "rich" \
        --hidden-import "typer" \
        --hidden-import "trimesh" \
        --hidden-import "trimesh.visual" \
        --hidden-import "trimesh.scene" \
        --hidden-import "tkinter" \
        $extra_args \
        gui_entry.py
    
    if [ $? -eq 0 ]; then
        print_success "$platform GUI executable built successfully"
    else
        print_error "Failed to build $platform GUI executable"
        exit 1
    fi
}

print_status "Building for macOS..."

# Build CLI
build_executable "macOS" "dist/macos" "voxbridge" ""

# Build GUI
build_gui "macOS" "dist/macos" "voxbridge-gui" ""

# Make executables executable
chmod +x dist/macos/voxbridge
chmod +x dist/macos/voxbridge-gui

# Create macOS package
print_status "Creating macOS package..."
cd dist/macos
zip -r ../../release_builds/voxbridge-macos.zip voxbridge voxbridge-gui
cd ../..

print_success "macOS package created: release_builds/voxbridge-macos.zip"

# Clean up build artifacts
print_status "Cleaning up build artifacts..."
rm -rf build/
rm -f *.spec

print_success "Build completed successfully!"
print_status "Distribution packages are available in release_builds/"

# Show package sizes
print_status "Package sizes:"
ls -lh release_builds/voxbridge-macos.zip

echo ""
print_success "macOS build complete! 🍎"
echo "To test: ./dist/macos/voxbridge --help"
echo "To run GUI: ./dist/macos/voxbridge-gui"
