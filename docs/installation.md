# VoxBridge Installation Guide

**Get VoxBridge up and running on your system**

## 🚀 Quick Start (Recommended)

### Standalone Executables (No Python Required)

**For most users, this is the easiest way to get started:**

1. **Download** the standalone package for your platform
2. **Extract** the files to any folder
3. **Run** the executable - that's it!

**Download All Platforms**: [Google Drive Folder](https://drive.google.com/drive/folders/1LNtXrmrB_U4lkpuX_5Gk5Ax1MiodIh1h?usp=sharing)

| Platform    | File Name              | Size   |
| ----------- | ---------------------- | ------ |
| **Windows** | voxbridge-windows.zip  | 135 MB |
| **Linux**   | voxbridge-linux.tar.gz | 135 MB |
| **macOS**   | voxbridge-macos.tar.gz | 135 MB |

**No installation, no configuration, no dependencies!**

## 📥 Platform-Specific Instructions

### Windows

1. **Download** `voxbridge-windows.zip`
2. **Extract** the zip file to any folder (e.g., `C:\VoxBridge\`)
3. **Run** the executables:
   - `voxbridge.exe` - Command line interface
   - `voxbridge-gui.exe` - Graphical interface

**Example:**

```cmd
# Extract to C:\VoxBridge\
# Open Command Prompt in that folder
voxbridge.exe --help
voxbridge-gui.exe
```

### Linux

1. **Download** `voxbridge-linux.tar.gz`
2. **Extract** the archive:
   ```bash
   tar -xzf voxbridge-linux.tar.gz
   ```
3. **Make executable** (if needed):
   ```bash
   chmod +x voxbridge voxbridge-gui
   ```
4. **Run** the executables:
   ```bash
   ./voxbridge --help
   ./voxbridge-gui
   ```

### macOS

1. **Download** `voxbridge-macos.tar.gz`
2. **Extract** the archive:
   ```bash
   tar -xzf voxbridge-macos.tar.gz
   ```
3. **Make executable** (if needed):
   ```bash
   chmod +x voxbridge voxbridge-gui
   ```
4. **Run** the executables:
   ```bash
   ./voxbridge --help
   ./voxbridge-gui
   ```

## 🐍 Python Installation (For Developers)

**Only use this if you need to modify VoxBridge or build from source.**

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

## 🛠️ Troubleshooting Installation Issues

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

## 🔧 System Requirements

### Minimum Requirements

- **OS**: Windows 10+, macOS 10.14+, or Linux (x64)
- **RAM**: 2GB minimum, 4GB recommended
- **Storage**: 200MB free space
- **Graphics**: Basic graphics support for GUI

### For Python Installation

- **Python**: 3.12 (not 3.13) - required for compatibility
- **pip**: Latest version recommended

## ✅ Verification

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

## 🎯 Next Steps

Once installed, see the [Quick Start Guide](QUICK_START.md) for detailed instructions on converting files and using the features.

## 🔗 Additional Resources

- **Quick Start Guide**: [QUICK_START.md](QUICK_START.md)
- **Usage Guide**: [usage.md](usage.md)
- **Report Issues**: [GitHub Issues](https://github.com/Supercoolkayy/voxbridge/issues)
- **Ask Questions**: [GitHub Discussions](https://github.com/Supercoolkayy/voxbridge/discussions)

## 💡 Tips

- **For most users**: Use the standalone executables - no Python required
- **For developers**: Use Python installation for customization
- **For troubleshooting**: Use module execution (`python3 -m voxbridge.cli`)
- **For updates**: Download new standalone packages or use `pip install --upgrade voxbridge`
