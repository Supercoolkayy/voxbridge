#!/bin/bash
# scripts/install_dev.sh - Development environment setup for VoxBridge

set -e

echo "VoxBridge Development Setup"
echo "==========================="

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
if [[ ! -f "setup.py" ]] || [[ ! -d "voxbridge" ]]; then
    print_error "Please run this script from the VoxBridge project root directory"
    exit 1
fi

# Check Python version
print_info "Checking Python version..."
python_version=$(python3 --version 2>&1 | cut -d' ' -f2)

if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
    print_error "Python 3.8+ required. Found: $python_version"
    echo "Please install Python 3.8 or later:"
    echo "  - macOS: brew install python@3.11"
    echo "  - Ubuntu/Debian: sudo apt install python3.11 python3.11-venv"
    echo "  - Windows: Download from https://python.org"
    exit 1
fi

print_status "Python version OK: $python_version"

# Create virtual environment
if [[ -d "venv" ]]; then
    print_warning "Virtual environment already exists"
    read -p "Remove existing venv and create new one? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "Removing existing virtual environment..."
        rm -rf venv
    else
        print_info "Using existing virtual environment..."
    fi
fi

if [[ ! -d "venv" ]]; then
    print_info "Creating virtual environment..."
    python3 -m venv venv
    print_status "Virtual environment created"
fi

# Activate virtual environment
print_info "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
print_info "Upgrading pip..."
pip install --upgrade pip

# Create requirements-dev.txt if it doesn't exist
if [[ ! -f "requirements-dev.txt" ]]; then
    print_info "Creating requirements-dev.txt..."
    cat > requirements-dev.txt << 'EOF'
# Development dependencies for VoxBridge
pytest>=6.0
pytest-cov>=2.0
black>=21.0
flake8>=3.8
isort>=5.0
mypy>=0.910
build>=0.7.0
twine>=3.4.0

# Optional: Enhanced glTF processing
# pygltflib>=1.15.0
EOF
    print_status "Created requirements-dev.txt"
fi

# Install development dependencies
print_info "Installing development dependencies..."
pip install -r requirements-dev.txt

# Install VoxBridge in development mode
print_info "Installing VoxBridge in development mode..."
pip install -e .

# Verify installation
print_info "Verifying installation..."
if python -c "import voxbridge; print('VoxBridge imported successfully')" 2>/dev/null; then
    print_status "VoxBridge installed successfully"
else
    print_error "VoxBridge installation failed"
    exit 1
fi

# Test CLI command
if command -v voxbridge-cli &> /dev/null; then
    print_status "CLI command 'voxbridge-cli' is available"
    voxbridge-cli --version
else
    print_warning "CLI command not found in PATH. You may need to restart your shell."
fi

# Check for Blender
print_info "Checking for Blender installation..."
if command -v blender &> /dev/null; then
    blender_version=$(blender --version 2>/dev/null | head -n1 || echo "Blender (version unknown)")
    print_status "Blender found: $blender_version"
else
    print_warning "Blender not found in PATH"
    echo "  VoxBridge can still process .gltf files, but .glb files require Blender"
    echo "  Download Blender from: https://www.blender.org/download/"
    echo ""
    echo "  Installation locations:"
    echo "    macOS: /Applications/Blender.app/Contents/MacOS/Blender"
    echo "    Linux: /usr/bin/blender or /snap/bin/blender"
    echo "    Windows: C:\\Program Files\\Blender Foundation\\Blender X.X\\blender.exe"
fi

# Set up git hooks if .git exists
if [[ -d ".git" ]]; then
    print_info "Setting up git pre-commit hooks..."
    mkdir -p .git/hooks
    
    cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
# Pre-commit hook for VoxBridge

set -e

echo "Running pre-commit checks..."

# Check if we're in a virtual environment
if [[ -z "$VIRTUAL_ENV" ]]; then
    if [[ -f "venv/bin/activate" ]]; then
        source venv/bin/activate
    else
        echo "Warning: No virtual environment active"
    fi
fi

# Format code with black
if command -v black &> /dev/null; then
    echo "Formatting code with black..."
    black voxbridge/ tests/ --check --diff
else
    echo "Warning: black not installed, skipping formatting check"
fi

# Sort imports with isort
if command -v isort &> /dev/null; then
    echo "Checking import sorting..."
    isort voxbridge/ tests/ --check-only --diff
else
    echo "Warning: isort not installed, skipping import check"
fi

# Lint with flake8
if command -v flake8 &> /dev/null; then
    echo "Linting with flake8..."
    flake8 voxbridge/ tests/
else
    echo "Warning: flake8 not installed, skipping lint check"
fi

# Type checking with mypy
if command -v mypy &> /dev/null; then
    echo "Type checking with mypy..."
    mypy voxbridge/ --ignore-missing-imports
else
    echo "Warning: mypy not installed, skipping type check"
fi

echo "Pre-commit checks passed!"
EOF
    
    chmod +x .git/hooks/pre-commit
    print_status "Git pre-commit hook installed"
fi

# Create useful development scripts
print_info "Creating development shortcuts..."

# Create format script
cat > scripts/format.sh << 'EOF'
#!/bin/bash
# Format code with black and isort

if [[ -f "venv/bin/activate" ]]; then
    source venv/bin/activate
fi

echo "Formatting code with black..."
black voxbridge/ tests/

echo "Sorting imports with isort..."
isort voxbridge/ tests/

echo "Code formatting complete!"
EOF
chmod +x scripts/format.sh

# Create lint script
cat > scripts/lint.sh << 'EOF'
#!/bin/bash
# Run linting checks

if [[ -f "venv/bin/activate" ]]; then
    source venv/bin/activate
fi

echo "Linting with flake8..."
flake8 voxbridge/ tests/

echo "Type checking with mypy..."
mypy voxbridge/ --ignore-missing-imports

echo "Linting complete!"
EOF
chmod +x scripts/lint.sh

print_status "Development scripts created in scripts/"

# Create VS Code settings if not exists
if [[ ! -d ".vscode" ]]; then
    print_info "Creating VS Code workspace settings..."
    mkdir -p .vscode
    
    cat > .vscode/settings.json << 'EOF'
{
    "python.defaultInterpreterPath": "./venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.linting.mypyEnabled": true,
    "python.formatting.provider": "black",
    "python.sortImports.args": ["--profile", "black"],
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
        "source.organizeImports": true
    },
    "files.exclude": {
        "**/__pycache__": true,
        "**/*.pyc": true,
        "**/venv": true,
        "**/build": true,
        "**/dist": true,
        "**/*.egg-info": true
    },
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": [
        "tests"
    ]
}
EOF

    cat > .vscode/launch.json << 'EOF'
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "VoxBridge CLI",
            "type": "python",
            "request": "launch",
            "module": "voxbridge.cli",
            "args": [
                "examples/input/test.gltf",
                "examples/output/test_clean.gltf",
                "--verbose"
            ],
            "console": "integratedTerminal",
            "cwd": "${workspaceFolder}"
        },
        {
            "name": "Run Tests",
            "type": "python",
            "request": "launch",
            "module": "pytest",
            "args": [
                "tests/",
                "-v"
            ],
            "console": "integratedTerminal",
            "cwd": "${workspaceFolder}"
        }
    ]
}
EOF

    print_status "VS Code workspace configured"
fi

# Run initial tests to make sure everything works
print_info "Running initial tests..."
if python -m pytest tests/ -q; then
    print_status "Initial tests passed"
else
    print_warning "Some tests failed. This might be normal for a fresh setup."
fi

# Create example test files
print_info "Creating example test files..."
mkdir -p examples/input examples/output

cat > examples/input/simple_test.gltf << 'EOF'
{
  "asset": {"version": "2.0"},
  "scene": 0,
  "scenes": [{"nodes": [0]}],
  "nodes": [{"mesh": 0, "name": "Test Object #1"}],
  "meshes": [{"primitives": [{"attributes": {"POSITION": 0}, "material": 0}]}],
  "materials": [{"name": "Test Material (Red)!"}],
  "images": [{"uri": "/absolute/path/to/texture.png"}],
  "accessors": [{"bufferView": 0, "componentType": 5126, "count": 3, "type": "VEC3"}],
  "bufferViews": [{"buffer": 0, "byteLength": 36}],
  "buffers": [{"byteLength": 36, "uri": "test.bin"}]
}
EOF

echo "fake texture data" > examples/input/texture.png
echo "fake binary data for testing" > examples/input/test.bin

print_status "Example files created in examples/input/"

# Print final setup summary
echo ""
echo "🎉 Development Environment Setup Complete!"
echo "========================================"
echo ""
echo "📁 Project Structure:"
echo "  ├── voxbridge/          # Main package"
echo "  ├── tests/              # Unit tests"
echo "  ├── examples/           # Example files"
echo "  ├── scripts/            # Development scripts"
echo "  └── venv/               # Virtual environment"
echo ""
echo "🔧 Available Commands:"
echo "  voxbridge-cli           # Main CLI tool"
echo "  pytest tests/           # Run tests"
echo "  ./scripts/test.sh       # Full test suite"
echo "  ./scripts/build.sh      # Build package"
echo "  ./scripts/format.sh     # Format code"
echo "  ./scripts/lint.sh       # Lint code"
echo ""
echo "📖 Next Steps:"
echo "  1. Try: voxbridge-cli examples/input/simple_test.gltf examples/output/clean.gltf"
echo "  2. Run tests: ./scripts/test.sh"
echo "  3. Edit code in voxbridge/ directory"
echo "  4. Format code: ./scripts/format.sh"
echo "  5. Build package: ./scripts/build.sh"
echo ""

if [[ -z "$(command -v blender)" ]]; then
    echo "⚠️  Remember to install Blender for full GLB support:"
    echo "   https://www.blender.org/download/"
    echo ""
fi

echo "💡 Pro tip: Activate the virtual environment with:"
echo "   source venv/bin/activate"
echo ""
echo "Happy coding! 🚀"