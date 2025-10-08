#!/bin/bash
# VoxBridge Installation Script
# This script installs VoxBridge and ensures it's available in PATH

set -e

echo "VoxBridge Installation Script"
echo "============================="

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}[OK] $1${NC}"
}

print_info() {
    echo -e "${BLUE}[INFO] $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}[WARN] $1${NC}"
}

print_error() {
    echo -e "${RED}[ERROR] $1${NC}"
}

# Check if we're in the right directory
if [[ ! -f "pyproject.toml" ]]; then
    print_error "Please run this script from the VoxBridge project root directory"
    exit 1
fi

# Check Python version
print_info "Checking Python version..."
python_version=$(python3 --version 2>&1 | cut -d' ' -f2)

if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 9) else 1)"; then
    print_error "Python 3.9+ required. Found: $python_version"
    exit 1
fi

print_status "Python version OK: $python_version"

# Check if pipx is available (recommended for global installation)
if command -v pipx &> /dev/null; then
    print_info "pipx found - using for global installation"
    USE_PIPX=true
else
    print_warning "pipx not found - using pip for user installation"
    USE_PIPX=false
fi

# Clean previous builds
print_info "Cleaning previous builds..."
rm -rf build/ dist/ *.egg-info/

# Build package
print_info "Building package..."
python3 -m build

# Install package
if [[ "$USE_PIPX" == "true" ]]; then
    print_info "Installing with pipx..."
    pipx install dist/*.whl --force
    
    print_status "VoxBridge installed with pipx!"
    echo ""
    echo "You can now use:"
    echo "  voxbridge --help"
    echo "  voxbridge convert --input model.glb --target unity"
    echo "  voxbridge-gui"
    
else
    print_info "Installing with pip (user installation)..."
    python3 -m pip install --user dist/*.whl
    
    # Get user bin directory
    USER_BIN=$(python3 -m site --user-base)/bin
    
    print_status "VoxBridge installed with pip!"
    echo ""
    echo "To use VoxBridge, add this to your PATH:"
    echo "  export PATH=\"$USER_BIN:\$PATH\""
    echo ""
    echo "Or run directly with:"
    echo "  python3 -m voxbridge.cli --help"
    echo "  python3 -m voxbridge.cli convert --input model.glb --target unity"
    echo "  python3 -m voxbridge.gui.app"
fi

# Test installation
print_info "Testing installation..."
if [[ "$USE_PIPX" == "true" ]]; then
    if voxbridge --help > /dev/null 2>&1; then
        print_status "CLI command works!"
    else
        print_error "CLI command failed"
        exit 1
    fi
else
    if python3 -m voxbridge.cli --help > /dev/null 2>&1; then
        print_status "CLI module works!"
    else
        print_error "CLI module failed"
        exit 1
    fi
fi

print_status "Installation completed successfully!"
echo ""
echo "Next steps:"
echo "1. Test the CLI: voxbridge --help (or python3 -m voxbridge.cli --help)"
echo "2. Convert a file: voxbridge convert --input model.glb --target unity"
echo "3. Launch GUI: voxbridge-gui (or python3 -m voxbridge.gui.app)"
echo ""
echo "For help, visit: https://github.com/Supercoolkayy/voxbridge" 