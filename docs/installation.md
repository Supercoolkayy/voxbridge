# VoxBridge Installation Guide

## Quick Start

### Method 1: Using pipx (Recommended)

```bash
# Install pipx if you don't have it
python3 -m pip install --user pipx
python3 -m pipx ensurepath

# Install VoxBridge
pipx install voxbridge

# Verify installation
voxbridge --help
```

### Method 2: Using pip

```bash
# Install VoxBridge
pip install voxbridge

# Add to PATH (if needed)
export PATH="$HOME/.local/bin:$PATH"

# Verify installation
voxbridge --help
```

### Method 3: From Source

```bash
# Clone the repository
git clone https://github.com/Supercoolkayy/voxbridge.git
cd voxbridge

# Run installation script
bash scripts/install.sh

# Or install manually
python3 -m build
pip install dist/*.whl
```

## Troubleshooting Installation Issues

### Issue: "voxbridge command not found"

This happens when the package isn't properly installed or isn't in your PATH.

**Solution 1: Use module execution**

```bash
# Instead of: voxbridge --help
python3 -m voxbridge.cli --help

# Instead of: voxbridge convert --input model.glb --target unity
python3 -m voxbridge.cli convert --input model.glb --target unity
```

**Solution 2: Fix PATH**

```bash
# Find where pip installed the package
python3 -m site --user-base

# Add to PATH (replace with actual path)
export PATH="$HOME/.local/bin:$PATH"

# Add to your shell profile (~/.bashrc, ~/.zshrc, etc.)
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

**Solution 3: Reinstall with pipx**

```bash
# Remove existing installation
pip uninstall voxbridge

# Install with pipx (ensures PATH is set)
pipx install voxbridge
```

### Issue: Rich Library Compatibility Error

If you see: `ProgressColumn._init_() got an unexpected keyword argument 'style'`

**Solution: Update dependencies**

```bash
# Reinstall with correct versions
pip uninstall rich typer
pip install "rich>=13.0.0,<14.0.0" "typer>=0.12.0,<1.0.0"
```

## Platform-Specific Instructions

### Ubuntu/Debian

```bash
# Install system dependencies
sudo apt update
sudo apt install python3 python3-pip python3-venv

# Install VoxBridge
pip3 install --user voxbridge

# Add to PATH
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### macOS

```bash
# Install Homebrew if needed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python and pipx
brew install python pipx
pipx ensurepath

# Install VoxBridge
pipx install voxbridge
```

### Windows

```bash
# Install Python from python.org
# Then install VoxBridge
pip install voxbridge

# Or use pipx
pip install pipx
pipx install voxbridge
```

### WSL (Windows Subsystem for Linux)

```bash
# Follow Ubuntu instructions above
# Ensure X11 forwarding is set up for GUI
export DISPLAY=:0

# Test GUI
voxbridge-gui
```

## Development Installation

For developers who want to work on VoxBridge:

```bash
# Clone repository
git clone https://github.com/Supercoolkayy/voxbridge.git
cd voxbridge

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install in development mode
pip install -e .

# Run tests
python -m pytest tests/

# Run CLI
python -m voxbridge.cli --help
```

## Verification

After installation, verify everything works:

```bash
# Test CLI
voxbridge --help
voxbridge doctor

# Test conversion (if you have a test file)
voxbridge convert --input test.glb --target unity --no-blender

# Test GUI
voxbridge-gui
```

## Common Commands

```bash
# Get help
voxbridge --help
voxbridge convert --help

# System check
voxbridge doctor

# Convert file
voxbridge convert --input model.glb --target unity
voxbridge convert --input model.glb --target roblox --optimize-mesh

# Batch processing
voxbridge batch ./input_folder ./output_folder --target unity

# Launch GUI
voxbridge-gui
```

## Support

If you encounter issues:

1. **Check the troubleshooting section above**
2. **Run diagnostics**: `voxbridge doctor`
3. **Check GitHub Issues**: https://github.com/Supercoolkayy/voxbridge/issues
4. **Use module execution**: `python3 -m voxbridge.cli --help`

## Next Steps

Once installed, see the [Usage Guide](usage.md) for detailed instructions on converting files and using the features.
