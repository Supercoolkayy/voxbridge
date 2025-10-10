# VoxBridge

**Convert VoxEdit models to Unity and Roblox - Now with Platform-Specific Material Export!**

VoxBridge is a professional tool that converts 3D models exported from The Sandbox VoxEdit into optimized formats for Unity and Roblox game engines. It automatically handles mesh optimization, texture processing, and **platform-specific material conversion** to ensure your models work perfectly in your target platform.

## 🎉 What's New in Version 2.0.1

### ✅ Production-Ready Animated Model Support
- **Official GLTF Transform Library**: Now using `@gltf-transform/core` for bulletproof GLTF processing
- **Perfect Animation Preservation**: All animations, skins, and rigging fully preserved
- **Complete Asset Bundling**: Binary data, textures, and geometry all included
- **No Native Dependencies**: Pure JavaScript Node.js processing bundles perfectly
- **Client-Friendly Messages**: Shows duplicate detection, mesh quality, and optimization status

### Previous Features (Version 2.0)

### Platform-Specific Texture Packing (Fixes Gray Materials in Unity!)

- **Unity Target (`-t unity`)**: Automatically packs PBR textures into Unity's Standard Shader format
  - R = Metallic, G = Smoothness, B = AO, A = Gloss
  - **Fixes the gray material problem** by properly remapping texture channels
  - Works perfectly in GLTF viewers AND Unity!

- **Roblox Target (`-t roblox`)**: Simplified material export for Roblox
  - Keeps only BaseColor + Normal maps (what Roblox actually uses)
  - Removes unused PBR textures for smaller file sizes
  - Optimized for Roblox's rendering engine

- **Standard GLTF Target (`-t gltf`)**: Full GLTF compliance
  - No modifications, works in all GLTF/GLB viewers
  - Complete PBR support

### Improved Model Handling

- **Static Models**: Simple models exported as optimized tri-mesh (skeleton removed)
- **Animated Models**: Full rigging and animation preservation (skinned meshes)
- Automatic detection or manual control with `--force-static` / `--force-node`

### Enhanced Performance

- Standalone executables available in `/dist` folder
- No installation required - just run and convert!
- Node.js optional but recommended for:
  - Complex model processing (animations, large files)
  - Advanced optimizations (Draco, texture resizing)
  - 2-3x faster processing on complex assets

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
- **Node.js**: 18+ LTS (Optional but recommended)

### Node.js Dependency

**VoxBridge works without Node.js**, but for optimal performance:

- ✅ **Simple/Static Models**: Work fine without Node.js (basic conversion)
- ⚡ **Complex/Animated Models**: Require Node.js for:
  - Animation and rigging preservation
  - Large file processing (>50MB)
  - Advanced optimizations (Draco compression, texture resizing)
  - 2-3x faster processing speed

**Install Node.js**: Download the latest LTS version from [nodejs.org](https://nodejs.org/)

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
# Unity export (fixes gray materials with packed textures!)
./voxbridge convert --input model.glb --output-dir ./output -t unity

# Roblox export (lightweight, optimized materials)
./voxbridge convert --input model.glb --output-dir ./output -t roblox

# Standard GLTF export (works in all viewers)
./voxbridge convert --input model.glb --output-dir ./output -t gltf

# Static model (fast, Python-only - no Node.js needed)
./voxbridge convert --input static_model.glb --output-dir ./output -t unity --force-static

# Animated model (preserves rigging - requires Node.js)
./voxbridge convert --input animated_model.glb --output-dir ./output -t unity --force-node

# Batch processing
./voxbridge batch ./input_folder --output-dir ./output_folder -t unity
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

## 🎮 Target Platforms & Material Export

### Unity (`-t unity`)

- **Input**: VoxEdit .glb/.gltf files
- **Output**: Unity-optimized glTF with packed PBR textures
- **Material Handling**: Automatically packs textures into Unity's Standard Shader format
  - R channel = Metallic
  - G channel = Smoothness (inverted roughness)
  - B channel = Ambient Occlusion
  - A channel = Gloss
- **Fixes**: Gray material problem in Unity!
- **Works in**: Unity AND GLTF viewers

### Roblox (`-t roblox`)

- **Input**: VoxEdit .glb/.gltf files
- **Output**: Roblox-compatible glTF with simplified materials
- **Material Handling**: Keeps only what Roblox uses
  - BaseColor (Albedo) texture
  - Normal map (if present)
  - Removes metallic/roughness/occlusion (unused by Roblox)
- **Benefits**: Smaller file sizes, faster imports
- **Optimized for**: Roblox Studio

### Standard GLTF (`-t gltf`)

- **Input**: VoxEdit .glb/.gltf files
- **Output**: Standard GLTF with full PBR support
- **Material Handling**: No modifications, full GLTF spec compliance
- **Use for**: GLTF/GLB viewers, other game engines

## 📦 Static vs Animated Model Handling

VoxBridge intelligently handles different model types:

### Static Models (No Animation)

**Export Process:**
- Converted to optimized tri-mesh
- Original skeleton is removed (not needed)
- Faster processing, smaller file size
- Works without Node.js

**Use Case:**
- Buildings, props, decorations
- Non-moving objects
- Simple character models

**Example:**
```bash
./voxbridge convert --input building.glb -o output/ -t unity --force-static
```

### Animated/Skinned Models

**Export Process:**
- Full rigging and skinning preserved
- Animations maintained
- Static duplicates removed
- Requires Node.js for optimal results

**Use Case:**
- Characters with animations
- Rigged models
- Skinned meshes

**Example:**
```bash
./voxbridge convert --input character.glb -o output/ -t unity --force-node
```

> 💡 **Auto-Detection**: By default, VoxBridge automatically detects whether your model is static or animated and uses the appropriate processing path.

## 🔧 Common Commands

```bash
# Get help
./voxbridge --help

# ===== PLATFORM-SPECIFIC EXPORTS =====

# Unity export (fixes gray materials!)
./voxbridge convert -i model.glb -o output/ -t unity

# Roblox export (optimized, lightweight)
./voxbridge convert -i model.glb -o output/ -t roblox

# Standard GLTF export (universal)
./voxbridge convert -i model.glb -o output/ -t gltf

# ===== STATIC VS ANIMATED MODELS =====

# Static model (fast, no Node.js needed)
./voxbridge convert -i prop.glb -o output/ -t unity --force-static

# Animated model (requires Node.js)
./voxbridge convert -i character.glb -o output/ -t unity --force-node

# Auto-detect (default - chooses best path)
./voxbridge convert -i model.glb -o output/ -t unity

# ===== ADVANCED OPTIONS =====

# Unity with mesh optimization (requires Node.js)
./voxbridge convert -i model.glb -o output/ -t unity --optimize-mesh

# Roblox with Draco compression (requires Node.js)
./voxbridge convert -i model.glb -o output/ -t roblox --use-draco

# Full optimization (requires Node.js)
./voxbridge convert -i model.glb -o output/ -t unity \
  --optimize-mesh --texture-size 1024 --use-draco --quantize

# ===== BATCH PROCESSING =====

# Batch convert folder to Unity
./voxbridge batch ./input_folder -o ./output_folder -t unity

# Batch convert to Roblox
./voxbridge batch ./input_folder -o ./output_folder -t roblox

# ===== DIAGNOSTICS =====

# Check system and Node.js availability
./voxbridge doctor

# Verbose output for debugging
./voxbridge convert -i model.glb -o output/ -t unity --verbose
```

### 🎛️ CLI Flags

| Flag             | Description                             | Default     | Node.js Required |
| ---------------- | --------------------------------------- | ----------- | ---------------- |
| `-t, --target`   | Target platform: `unity`, `roblox`, `gltf` | `unity`     | No               |
| `-i, --input`    | Input GLB/GLTF file path                | Required    | No               |
| `-o, --output`   | Output directory path                   | Required    | No               |
| `--force-static` | Force static processing (tri-mesh)      | Auto-detect | No               |
| `--force-node`   | Force complex processing (animations)   | Auto-detect | Yes              |
| `--pack-glb`     | Pack output into single GLB file        | False       | No               |
| `--use-draco`    | Enable Draco compression                | True        | Yes              |
| `--no-draco`     | Disable Draco compression               | False       | No               |
| `--texture-size` | Maximum texture size (pixels)           | 1024        | Yes              |
| `--quantize`     | Enable quantization                     | True        | Yes              |
| `--optimize-mesh`| Enable mesh simplification              | False       | Yes              |
| `--verbose, -v`  | Verbose output                          | False       | No               |
| `--debug, -d`    | Debug output with full details          | False       | No               |

> 📖 **Need more command details?** See [Usage Guide](docs/usage.md) and [Texture Packing Guide](docs/TEXTURE_PACKING_GUIDE.md) for comprehensive documentation.

## ⚠️ Common Mistakes

**Don't try these - they won't work:**

- ❌ Using OBJ or FBX files as input
- ❌ Dragging random 3D models from the internet
- ❌ Using models from other voxel editors
- ❌ Expecting other formats to work
- ❌ Using complex processing flags without Node.js installed

**Do this instead:**

- ✅ Always export from The Sandbox VoxEdit as GLB
- ✅ Use the GUI for your first conversion (no terminal needed!)
- ✅ Check the output ZIP file for your converted model
- ✅ Install Node.js 18+ for full functionality with complex models

## 🔧 Node.js Requirements

**For Full Functionality:**
- **Node.js 18+** is required for complex model processing
- **Automatic Fallback**: If Node.js is not available, VoxBridge will use Python-only processing
- **Performance Impact**: Complex processing is 2-3x faster with Node.js

**What Requires Node.js:**
- Mesh simplification (`--optimize-mesh`)
- Draco compression (`--use-draco`)
- Texture resizing (`--texture-size`)
- Quantization (`--quantize`)
- Complex model processing (animations, rigging)

**What Works Without Node.js:**
- Basic conversion (`--force-static`)
- Simple model processing
- GLB packing (`--pack-glb`)
- Basic material conversion

## 🔗 Learn More

### VoxBridge Documentation

- **📖 Quick Start Guide**: [docs/QUICK_START.md](docs/QUICK_START.md) - Step-by-step getting started
- **📖 Texture Packing Guide**: [docs/TEXTURE_PACKING_GUIDE.md](docs/TEXTURE_PACKING_GUIDE.md) - **NEW!** Platform-specific material export
- **📖 Usage Guide**: [docs/usage.md](docs/usage.md) - Complete CLI documentation
- **📖 Installation Guide**: [docs/installation.md](docs/installation.md) - Detailed installation help
- **📖 Standalone Executables**: [docs/STANDALONE_EXECUTABLES.md](docs/STANDALONE_EXECUTABLES.md) - Platform-specific instructions
- **📖 Performance Analysis**: [docs/performance.md](docs/performance.md) - Benchmarks and performance metrics
- **📖 Current Status**: [docs/CURRENT_STATUS.md](docs/CURRENT_STATUS.md) - Project status and milestones

### Quick References

- **🎯 Texture Packing Quick Ref**: [QUICK_REFERENCE_TEXTURE_PACKING.md](QUICK_REFERENCE_TEXTURE_PACKING.md) - Commands at a glance
- **📊 Implementation Summary**: [TEXTURE_PACKING_IMPLEMENTATION_SUMMARY.md](TEXTURE_PACKING_IMPLEMENTATION_SUMMARY.md) - Technical details

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
./voxbridge convert --input model.glb --output-dir ./output --target roblox --verbose

# Check system status and Node.js availability
./voxbridge doctor
```

### Node.js not found or processing fails

If you see "Node.js runner not found" or "Complex processing failed":

**Solution 1: Install Node.js (Recommended)**
```bash
# Install Node.js 18+ from https://nodejs.org/
# Then restart your terminal and try again
./voxbridge convert --input model.glb --output-dir ./output --target unity --force-node
```

**Solution 2: Use Python-only processing**
```bash
# Force static processing (no Node.js required)
./voxbridge convert --input model.glb --output-dir ./output --target unity --force-static
```

**Solution 3: Check Node.js installation**
```bash
# Verify Node.js is installed and accessible
node --version
npm --version
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

**VoxBridge v2.0.0** - Professional Asset Conversion with Platform-Specific Material Export

Made with ❤️ by Dapps over Apps | MIT License
