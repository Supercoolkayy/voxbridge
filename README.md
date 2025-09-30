# VoxBridge

**Convert VoxEdit models to Unity and Roblox**

VoxBridge is a professional tool that converts 3D models exported from The Sandbox VoxEdit into optimized formats for Unity and Roblox game engines. It automatically handles mesh optimization, texture processing, and material conversion to ensure your models work perfectly in your target platform.

## 📚 Quick Navigation

- **🚀 [Quick Start](#-quick-start)** - Get up and running in 5 minutes
- **📥 [Download](#-download)** - Get VoxBridge for your platform
- **📋 [Supported Formats](#-supported-formats)** - What works and what doesn't
- **🛠️ [Troubleshooting](#️-troubleshooting)** - Common issues and solutions
- **📖 [Documentation](#-learn-more)** - Detailed guides and references

## 🎯 What VoxBridge Does

**Input**: `.glb` files exported from The Sandbox VoxEdit  
**Output**: `.gltf` files optimized for Roblox or Unity  
**Purpose**: Bridge the gap between voxel art creation and game development

> ⚠️ **Important**: VoxBridge only works with GLB files exported from The Sandbox VoxEdit. Other formats like OBJ, FBX, or random 3D models are not supported at this stage.

## 🧠 Smart Conversion System

VoxBridge now features an intelligent conversion system that automatically detects the complexity of your 3D models and routes them through the optimal processing path:

**🔍 Automatic Detection:**

- **Static Models**: Simple models without animations, skins, or morph targets
- **Complex Models**: Models with animations, rigging, morph targets, or advanced materials

**⚡ Processing Paths:**

- **Static Path**: Fast Trimesh-based processing for simple models
- **Complex Path**: Full Node.js processing with glTF-Transform for advanced features

**🎛️ Manual Override:**

- `--force-static`: Force static processing (faster, but may lose complex features)
- `--force-node`: Force complex processing (slower, but preserves all features)

## 🖥️ Two Ways to Use VoxBridge

**For Creators (No Terminal Required):**

- Use the **GUI** - Just double-click and drag your files
- Perfect for artists and non-technical users
- Visual interface makes conversion simple

**For Developers:**

- Use the **Command Line** - Full control and automation
- Perfect for batch processing and scripting
- Advanced options and customization

## System Requirements

- **OS**: Windows 10+, macOS 10.14+, or Linux (x64)
- **RAM**: 2GB minimum, 4GB recommended
- **Storage**: 200MB free space
- **Graphics**: Basic graphics support for GUI

> 📖 **Need detailed installation help?** See [Installation Guide](docs/installation.md) for step-by-step instructions and troubleshooting.

## 🚀 Quick Start

### 🖱️ For Creators (GUI - Recommended)

**No terminal knowledge required! Perfect for artists and creators.**

1. **Download** the standalone executable for your platform
2. **Extract** the files to any folder
3. **Double-click** `voxbridge-gui.exe` (Windows) or `./voxbridge-gui` (Linux/macOS)
4. **Load** your `.glb` file exported from VoxEdit
5. **Choose** target platform (Roblox or Unity)
6. **Click** "Convert" and find your results in a ZIP file!

> 💡 **The GUI makes everything visual and simple - just drag, drop, and convert!**

### 💻 For Developers (CLI)

1. **Download** the standalone executable for your platform
2. **Extract** the files to any folder
3. **Open** Command Prompt/Terminal in that folder
4. **Run** conversion commands:

```bash
# Basic conversion
./voxbridge convert --input model.glb --output model.gltf --target roblox

# For Unity with optimization
./voxbridge convert --input model.glb --output model.gltf --target unity --optimize-mesh

# Batch processing
./voxbridge batch ./input_folder --output-dir ./output_folder --target roblox
```

## 📥 Download

**Download All Platforms**: [Google Drive Folder](https://drive.google.com/drive/folders/1LNtXrmrB_U4lkpuX_5Gk5Ax1MiodIh1h?usp=sharing)

| Platform    | File Name              | Size   |
| ----------- | ---------------------- | ------ |
| **Windows** | voxbridge-windows.zip  | 135 MB |
| **Linux**   | voxbridge-linux.tar.gz | 135 MB |
| **macOS**   | voxbridge-macos.tar.gz | 135 MB |

> 📖 **Need help with standalone executables?** See [Standalone Executables Guide](docs/STANDALONE_EXECUTABLES.md) for detailed platform-specific instructions.

## 📋 Supported Formats

### ✅ Supported Input

- **GLB (GLTF Binary)** - Exported from The Sandbox VoxEdit
- **glTF** - Text-based GLTF files from VoxEdit

### ✅ Supported Output

- **glTF** - Optimized for Unity or Roblox
- **ZIP packages** - Automatic packaging of output files

### ❌ Not Supported (Yet)

- **OBJ files** - Not supported at this stage
- **FBX files** - Not supported at this stage
- **Random 3D models** - Only VoxEdit exports work
- **Other formats** - Only GLB/glTF from VoxEdit

> 💡 **Always export your assets from VoxEdit in GLB format for best results.**

## 🎮 Target Platforms

### Unity

- **Input**: VoxEdit .glb/.gltf files
- **Output**: Optimized glTF files for Unity
- **Features**: Full PBR materials, mesh optimization, texture handling

### Roblox

- **Input**: VoxEdit .glb/.gltf files
- **Output**: Roblox-compatible glTF files
- **Features**: Simplified materials, Roblox-specific optimizations

## 🔧 Common Commands

```bash
# Get help
./voxbridge --help

# Convert single file (automatic routing)
./voxbridge convert --input model.glb --output-dir ./output --target roblox

# Force static processing (faster)
./voxbridge convert --input model.glb --output-dir ./output --target unity --force-static

# Force complex processing (preserves animations)
./voxbridge convert --input model.glb --output-dir ./output --target roblox --force-node

# Pack output into single GLB file
./voxbridge convert --input model.glb --output-dir ./output --target unity --pack-glb

# Advanced options
./voxbridge convert --input model.glb --output-dir ./output --target roblox \
  --optimize-mesh --texture-size 512 --use-draco --quantize

# Batch convert folder
./voxbridge batch ./input_folder --output-dir ./output_folder --target unity

# Check system
./voxbridge doctor

# Verbose output
./voxbridge convert --input model.glb --output-dir ./output --target unity --verbose
```

### 🎛️ New CLI Flags

| Flag             | Description                             | Default     |
| ---------------- | --------------------------------------- | ----------- |
| `--force-static` | Force static processing path (Trimesh)  | Auto-detect |
| `--force-node`   | Force complex processing path (Node.js) | Auto-detect |
| `--pack-glb`     | Pack output into single GLB file        | False       |
| `--use-draco`    | Enable Draco compression                | True        |
| `--no-draco`     | Disable Draco compression               | False       |
| `--texture-size` | Maximum texture size (pixels)           | 1024        |
| `--quantize`     | Enable quantization                     | True        |

> 📖 **Need more command details?** See [Usage Guide](docs/usage.md) for comprehensive CLI documentation and advanced options.

## ⚠️ Common Mistakes

**Don't try these - they won't work:**

- ❌ Using OBJ or FBX files as input
- ❌ Dragging random 3D models from the internet
- ❌ Using models from other voxel editors
- ❌ Expecting other formats to work

**Do this instead:**

- ✅ Always export from The Sandbox VoxEdit as GLB
- ✅ Use the GUI for your first conversion (no terminal needed!)
- ✅ Check the output ZIP file for your converted model

## 🔗 Learn More

### VoxBridge Documentation

- **📖 Quick Start Guide**: [docs/QUICK_START.md](docs/QUICK_START.md) - Step-by-step getting started
- **📖 Usage Guide**: [docs/usage.md](docs/usage.md) - Complete CLI documentation
- **📖 Installation Guide**: [docs/installation.md](docs/installation.md) - Detailed installation help
- **📖 Standalone Executables**: [docs/STANDALONE_EXECUTABLES.md](docs/STANDALONE_EXECUTABLES.md) - Platform-specific instructions
- **📖 Performance Analysis**: [docs/performance.md](docs/performance.md) - Benchmarks and performance metrics
- **📖 Current Status**: [docs/CURRENT_STATUS.md](docs/CURRENT_STATUS.md) - Project status and milestones

### Official Documentation

- **GLTF Specification**: [https://registry.khronos.org/glTF/](https://registry.khronos.org/glTF/)
- **Roblox Mesh Import**: [https://create.roblox.com/docs/art/modeling/meshes](https://create.roblox.com/docs/art/modeling/meshes)
- **Unity GLTF Import**: [https://docs.unity3d.com/Packages/com.unity.formats.gltf](https://docs.unity3d.com/Packages/com.unity.formats.gltf)
- **The Sandbox VoxEdit**: [https://www.sandbox.game/voxedit](https://www.sandbox.game/voxedit)

### Support & Community

- **Report Issues**: [GitHub Issues](https://github.com/Supercoolkayy/voxbridge/issues)
- **Ask Questions**: [GitHub Discussions](https://github.com/Supercoolkayy/voxbridge/discussions)

## 🛠️ Troubleshooting

### Windows: "File not recognized as executable"

If Windows asks how to open the file instead of running it:

**Solution 1: Use Command Prompt (Recommended)**

```cmd
# Open Command Prompt (cmd.exe), not PowerShell
cd C:\path\to\extracted\folder
voxbridge.exe --help
voxbridge-gui.exe
```

**Solution 2: PowerShell Alternative**

```powershell
# In PowerShell, use this syntax:
cd C:\path\to\extracted\folder
.\voxbridge.exe --help
& ".\voxbridge-gui.exe"
```

### Linux/macOS: "Permission denied"

```bash
chmod +x voxbridge voxbridge-gui
```

### Conversion fails

```bash
# Get detailed error info
./voxbridge convert --input model.glb --output model.gltf --target roblox --verbose --debug
```

### Windows Defender false positives

Some antivirus software may flag the executable as suspicious. This is a false positive because:

- The executable is built with PyInstaller
- It contains Python runtime and libraries
- No malicious code is present

**Solution**: Add an exception for the VoxBridge folder in Windows Defender.

> 📖 **Need more troubleshooting help?** See [Installation Guide](docs/installation.md) for detailed solutions and [Usage Guide](docs/usage.md) for command-specific help.

## 👨‍💻 Developer Notes

**For developers who want to build from source:**

> 📖 **Performance & Benchmarks**: See [Performance Analysis](docs/performance.md) for detailed benchmarks and [Current Status](docs/CURRENT_STATUS.md) for project milestones.

### Requirements

- **Python**: 3.12 (not 3.13) - required for compatibility
- **Dependencies**: Install from requirements.txt

### Build from Source

```bash
# Clone repository
git clone https://github.com/Supercoolkayy/voxbridge.git
cd voxbridge

# Create virtual environment
python3.12 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .

# Run tests
python -m pytest tests/

# Launch GUI for testing
python gui.py
```

### Building Standalone Executables

```bash
# Linux/macOS
./build.sh

# Windows (requires Windows machine)
build_windows.bat
```

> 📖 **Benchmarking**: See [Benchmark Guide](docs/BENCHMARK_GUIDE.md) for performance testing and optimization analysis.

## License

MIT License - see [LICENSE](LICENSE) for details.

---

**VoxBridge v1.0.8** - Professional Asset Conversion Made Simple
