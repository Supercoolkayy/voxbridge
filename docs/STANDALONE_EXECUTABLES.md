# VoxBridge Standalone Executables Guide

**No Python Installation Required!**

VoxBridge standalone executables are self-contained applications that include everything needed to run VoxBridge without installing Python, pip, or any dependencies.

## 🚀 Quick Start

### Download & Run

1. **Download** the appropriate package for your operating system
2. **Extract** the files
3. **Run** the executable - that's it!

No installation, no configuration, no dependencies!

**Download All Platforms**: [Google Drive Folder](https://drive.google.com/drive/folders/1LNtXrmrB_U4lkpuX_5Gk5Ax1MiodIh1h?usp=sharing)

## 📥 Available Downloads

| Platform    | Package                  | Size   | Download                         |
| ----------- | ------------------------ | ------ | -------------------------------- |
| **Windows** | `voxbridge-windows.zip`  | 135 MB | Available in Google Drive folder |
| **Linux**   | `voxbridge-linux.tar.gz` | 135 MB | Available in Google Drive folder |
| **macOS**   | `voxbridge-macos.tar.gz` | 135 MB | Available in Google Drive folder |

### File Integrity Verification

Verify your download using these SHA256 checksums:

```
38232962fb07dddc76b25060b37911ca5681c6dc8d41ccd2928515bd239b9889  voxbridge-linux.tar.gz
38232962fb07dddc76b25060b37911ca5681c6dc8d41ccd2928515bd239b9889  voxbridge-macos.tar.gz
79ffe2845730ea1ba4a70894b0b905f50c84daf7e1e9fd1b817c3660e66d7a90  voxbridge-windows.zip
```

## 🎮 Platform-Specific Instructions

### Windows

1. **Download** `voxbridge-windows.zip`
2. **Extract** the zip file to any folder
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

## 🔧 Usage Examples

### Command Line Interface (CLI)

```bash
# Basic conversion
./voxbridge convert --input model.glb --output model.gltf --target roblox

# Roblox conversion with optimization
./voxbridge convert --input model.glb --output model.gltf --target roblox --optimize-mesh

# Batch processing
./voxbridge batch ./input_folder --output-dir ./output_folder --target unity

# System diagnostics
./voxbridge doctor

# Get help
./voxbridge --help
```

### Graphical Interface (GUI)

```bash
# Launch the GUI
./voxbridge-gui
```

**GUI Features:**

- **Single File Mode**: Convert one file at a time
- **Batch Mode**: Convert multiple files
- **Output Selection**: Choose where to save results
- **Real-time Progress**: See conversion status
- **Log Display**: View detailed conversion logs

## 📋 What's Included

Each standalone package contains:

- **`voxbridge`** - CLI executable (69 MB)
- **`voxbridge-gui`** - GUI executable (73 MB)

**All dependencies included:**

- Python runtime
- All required libraries
- Platform-specific binaries

## ⚡ Performance & Best Practices

- Simple/static models run fine without Node.js.
- Complex/animated/large models require Node.js for stable performance.

=======

## ⚖️ Standalone vs Python Installation

| Feature          | Standalone           | Python Installation     |
| ---------------- | -------------------- | ----------------------- |
| **Setup**        | Download & extract   | Install Python + pip    |
| **Dependencies** | All included         | Auto-installed          |
| **Size**         | ~135 MB              | ~50 MB + Python         |
| **Updates**      | Download new version | `pip install --upgrade` |
| **Portability**  | Fully portable       | Requires Python         |
| **Offline**      | Works offline        | Works offline           |

## 🛠️ Troubleshooting

### Common Issues

#### **"Permission denied" (Linux/macOS)**

```bash
chmod +x voxbridge voxbridge-gui
```

#### **"File not found" (Windows)**

- Make sure you extracted the zip file
- Run from the extracted folder
- Check that `voxbridge.exe` exists

#### **GUI won't start**

- Try running from command line to see error messages
- Check system requirements (2GB RAM minimum)
- Ensure you have display/graphics drivers installed

#### **Conversion fails**

```bash
# Enable verbose mode for details
./voxbridge convert --input model.glb --output model.gltf --target roblox --verbose

# Enable debug mode for maximum detail
./voxbridge convert --input model.glb --output model.gltf --target roblox --debug
```

### System Requirements

- **OS**: Windows 10+, macOS 10.14+, or Linux (x64)
- **RAM**: 2GB minimum, 4GB recommended
- **Storage**: 200MB free space
- **Graphics**: Basic graphics support for GUI

## 📁 File Structure

After extraction, you'll have:

```
voxbridge-standalone/
├── voxbridge          # CLI executable
├── voxbridge-gui      # GUI executable
└── (platform-specific files)
```

## 🔄 Updates

To update to a newer version:

1. **Download** the new package
2. **Replace** the old executables
3. **No configuration needed** - everything is self-contained

## 🔗 Getting Help

- **Documentation**: Check the main [README.md](../README.md)
- **Quick Start**: [QUICK_START.md](QUICK_START.md)
- **Issues**: [GitHub Issues](https://github.com/Supercoolkayy/voxbridge/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Supercoolkayy/voxbridge/discussions)

## 💡 Why Choose Standalone?

**Zero Setup** - Download and run  
**No Dependencies** - Everything included  
**Portable** - Run from any folder  
**Fast** - Optimized for performance  
**Secure** - Verified checksums included
