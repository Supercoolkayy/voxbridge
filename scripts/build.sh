#!/bin/bash
# scripts/build.sh - Build script for VoxBridge

set -e  # Exit on any error

echo "VoxBridge Build Script"
echo "====================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[OK] $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}[WARN] $1${NC}"
}

print_error() {
    echo -e "${RED}[ERROR] $1${NC}"
}

# Check Python version
python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
required_version="3.8"

if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
    print_error "Python 3.8+ required. Found: $python_version"
    exit 1
fi

print_status "Python version check passed: $python_version"

# Create virtual environment if it doesn't exist
if [[ ! -d "venv" ]]; then
    print_status "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
print_status "Upgrading pip..."
pip install --upgrade pip

# Install build dependencies
print_status "Installing build dependencies..."
pip install build twine wheel setuptools

# Install development dependencies
if [[ -f "requirements-dev.txt" ]]; then
    print_status "Installing development dependencies..."
    pip install -r requirements-dev.txt
fi

# Install package in development mode
print_status "Installing VoxBridge in development mode..."
pip install -e .

# Run tests if available
if [[ -d "tests" ]]; then
    print_status "Running tests..."
    python -m pytest tests/ -v --tb=short || {
        print_warning "Some tests failed, but continuing build..."
    }
fi

# Run linting if flake8 is available
if command -v flake8 &> /dev/null; then
    print_status "Running code quality checks..."
    flake8 voxbridge/ --count --select=E9,F63,F7,F82 --show-source --statistics || {
        print_warning "Code quality issues found, but continuing build..."
    }
fi

# Format code if black is available
if command -v black &> /dev/null; then
    print_status "Formatting code with black..."
    black voxbridge/ --check || {
        print_warning "Code formatting issues found. Run 'black voxbridge/' to fix."
    }
fi

# Clean previous builds
print_status "Cleaning previous builds..."
rm -rf build/ dist/ *.egg-info/

# Build package
print_status "Building package..."
python -m build

# Verify the build
print_status "Verifying build..."
if [[ -f "dist/"*.whl ]] && [[ -f "dist/"*.tar.gz ]]; then
    print_status "Build completed successfully!"
    echo ""
    echo "📦 Built packages:"
    ls -la dist/
    echo ""
    echo "🚀 To install locally: pip install dist/$(ls dist/*.whl | head -n1)"
    echo "📤 To upload to PyPI: twine upload dist/*"
else
    print_error "Build failed - no packages found in dist/"
    exit 1
fi

# Check if Blender is available for testing
print_status "Checking for Blender installation..."
if command -v blender &> /dev/null; then
    blender_version=$(blender --version 2>/dev/null | head -n1 || echo "Unknown")
    print_status "Blender found: $blender_version"
else
    print_warning "Blender not found in PATH. GLB processing will not work."
    echo "   Download from: https://www.blender.org/download/"
fi

print_status "Build script completed!"