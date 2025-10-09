#!/bin/bash
# VoxBridge Cross-Platform Build Script
# Builds standalone executables for Linux and macOS

set -e  # Exit on any error

echo "🚀 VoxBridge Cross-Platform Build Script"
echo "========================================"

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

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    print_error "Please run this script from the VoxBridge root directory"
    exit 1
fi

# Detect platform
PLATFORM=$(uname -s)
ARCH=$(uname -m)

print_status "Detected platform: $PLATFORM $ARCH"

# Create output directories
print_status "Creating output directories..."
mkdir -p dist/linux
mkdir -p dist/macos
mkdir -p release_builds

# Install PyInstaller if not available
if ! command -v pyinstaller &> /dev/null; then
    print_status "Installing PyInstaller..."
    pip3 install pyinstaller
fi

# Build function
build_executable() {
    local platform=$1
    local output_dir=$2
    local executable_name=$3
    local extra_args=$4
    
    print_status "Building $platform executable..."
    
    # Clean previous builds
    rm -rf build/ dist/
    
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
        print_success "$platform executable built successfully"
    else
        print_error "Failed to build $platform executable"
        exit 1
    fi
}

# Build GUI function
build_gui() {
    local platform=$1
    local output_dir=$2
    local executable_name=$3
    local extra_args=$4
    
    print_status "Building $platform GUI executable..."
    
    # Build GUI with PyInstaller
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

# Build based on platform
if [ "$PLATFORM" = "Linux" ]; then
    print_status "Building for Linux..."
    
    # Build CLI
    build_executable "Linux" "dist/linux" "voxbridge" ""
    
    # Build GUI
    build_gui "Linux" "dist/linux" "voxbridge-gui" ""
    
    # Make executables executable
    chmod +x dist/linux/voxbridge
    chmod +x dist/linux/voxbridge-gui
    
    # Create Linux package
    print_status "Creating Linux package..."
    cd dist/linux
    tar -czf ../../release_builds/voxbridge-linux64.tar.gz voxbridge voxbridge-gui
    cd ../..
    
    print_success "Linux package created: release_builds/voxbridge-linux64.tar.gz"
    
elif [ "$PLATFORM" = "Darwin" ]; then
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
    
else
    print_error "Unsupported platform: $PLATFORM"
    print_warning "This script only supports Linux and macOS"
    print_warning "For Windows builds, use build.bat on a Windows machine"
    exit 1
fi

# Clean up build artifacts
print_status "Cleaning up build artifacts..."
rm -rf build/ *.spec

print_success "Build completed successfully!"
print_status "Distribution packages are available in release_builds/"

# Show file sizes
print_status "Package sizes:"
ls -lh release_builds/
