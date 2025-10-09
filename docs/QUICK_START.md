# VoxBridge Quick Start Guide

**Get up and running with VoxBridge in under 5 minutes!**

## 🎯 What You Need

**Before you start, make sure you have:**

- A `.glb` file exported from The Sandbox VoxEdit
- VoxBridge downloaded and extracted
- Your target platform in mind (Roblox or Unity)

> ⚠️ **Important**: VoxBridge only works with GLB files from The Sandbox VoxEdit. Other formats like OBJ, FBX, or random 3D models won't work.
> 📌 **You can run the single executable in `/dist` with no install required.**
> For full performance (complex model handling, large assets, animations), Node.js must be installed. Simple/static models run fine without Node.js.

## 🖱️ Choose Your Method

**For Creators & Artists (Recommended):**

- Use the **GUI** - Just double-click and drag your files
- No terminal or command line knowledge needed
- Visual interface makes everything simple

**For Developers:**

- Use the **Command Line** - Full control and automation
- Perfect for batch processing and scripting

## 📥 Download VoxBridge

**Download All Platforms**: [Google Drive Folder](https://drive.google.com/drive/folders/1LNtXrmrB_U4lkpuX_5Gk5Ax1MiodIh1h?usp=sharing)

| Platform    | File Name              | Size   |
| ----------- | ---------------------- | ------ |
| **Windows** | voxbridge-windows.zip  | 135 MB |
| **Linux**   | voxbridge-linux.tar.gz | 135 MB |
| **macOS**   | voxbridge-macos.tar.gz | 135 MB |

## Installation

### Step 1: Extract Files

1. **Download** the package for your operating system
2. **Extract** the files to any folder (e.g., `C:\VoxBridge\` or `~/VoxBridge/`)

### Step 2: Verify Installation

- **Windows**: Look for `voxbridge.exe` and `voxbridge-gui.exe`
- **Linux/macOS**: Look for `voxbridge` and `voxbridge-gui`

**That's it!** No Python installation, no configuration needed.

## 🎮 Your First Conversion

### 🖱️ Method 1: GUI (Recommended for Beginners)

**Perfect for artists and creators - no terminal knowledge required!**

**Step 1: Launch the GUI**

- **Windows**: Double-click `voxbridge-gui.exe`
- **Linux/macOS**: Run `./voxbridge-gui` in Terminal

**Step 2: Load Your Model**

1. Click "Select Input File"
2. Choose your `.glb` file exported from VoxEdit
3. The file path will appear in the input field

**Step 3: Choose Target Platform**

- Select **Roblox** for Roblox Studio
- Select **Unity** for Unity Editor

**Step 4: Set Output Location**

1. Click "Select Output Folder"
2. Choose where to save your converted files
3. The output path will appear in the output field

**Step 5: Convert**

1. Click the "Convert" button
2. Watch the progress bar
3. When complete, find your converted files in a ZIP archive!

> 💡 **The GUI makes everything visual and simple - just drag, drop, and convert! No command line needed.**

### 💻 Method 2: Command Line (For Advanced Users)

**Step 1: Open Terminal/Command Prompt**

- **Windows**: Open Command Prompt (cmd.exe) in the VoxBridge folder
- **Linux/macOS**: Open Terminal in the VoxBridge folder

**Step 2: Run Conversion Command**

```bash
# Basic conversion for Roblox
./voxbridge convert --input model.glb --output model.gltf --target roblox

# Basic conversion for Unity
./voxbridge convert --input model.glb --output model.gltf --target unity

# With optimization (recommended)
./voxbridge convert --input model.glb --output model.gltf --target roblox --optimize-mesh
```

**Step 3: Find Your Results**

- Look for the output `.gltf` file in your specified location
- The file will be ready to import into your game engine

## 📋 Supported Formats

### ✅ What Works

- **Input**: `.glb` files exported from The Sandbox VoxEdit
- **Input**: `.gltf` files exported from The Sandbox VoxEdit
- **Output**: `.gltf` files optimized for Roblox or Unity

### ❌ What Doesn't Work (Yet)

- **OBJ files** - Not supported
- **FBX files** - Not supported
- **Random 3D models** - Only VoxEdit exports work
- **Other voxel editors** - Only The Sandbox VoxEdit

> 💡 **Always export from VoxEdit as GLB format for best results.**


## 🎯 Target Platforms & Export Logic

### For Roblox
- **Input**: VoxEdit .glb/.gltf files
- **Output**: Roblox-compatible glTF files
- **Features**: Simplified materials, Roblox-specific optimizations
- **Target flag (`--target roblox`)**: Lightweight materials, Roblox-specific optimizations.

### For Unity
- **Input**: VoxEdit .glb/.gltf files
- **Output**: Unity-optimized glTF files
- **Features**: Full PBR materials, mesh optimization
- **Target flag (`--target unity`)**: Remaps PBR channels for Unity’s shader format, fixes gray textures.

### Static vs. Animated Export Logic
- **Static Models**: Exported as tri-mesh; original skeleton is deleted. Fast processing, Node.js not required.
- **Animated/Skinned Models**: Exported with skinning; static duplicates are deleted. Animation/skin preserved, Node.js required for full feature support.

======


## 🔧 Common Commands

```bash
# Get help
./voxbridge --help

# Convert single file
./voxbridge convert --input model.glb --output model.gltf --target roblox

# Batch convert folder
./voxbridge batch ./input_folder --output-dir ./output_folder --target unity

# Check system
./voxbridge doctor

# Verbose output (for troubleshooting)
./voxbridge convert --input model.glb --output model.gltf --target roblox --verbose
```

## ⚠️ Common Mistakes

**Don't try these - they won't work:**

- ❌ Using OBJ or FBX files as input
- ❌ Dragging random 3D models from the internet
- ❌ Using models from other voxel editors
- ❌ Expecting other formats to work

**Do this instead:**

- ✅ Always export from The Sandbox VoxEdit as GLB
- ✅ Use the GUI for your first conversion
- ✅ Check the output ZIP file for your converted model

## 🛠️ Troubleshooting

### "Permission denied" (Linux/macOS)

```bash
chmod +x voxbridge voxbridge-gui
```

### "File not found" (Windows)

- Make sure you extracted the zip file
- Run from the extracted folder
- Check that `voxbridge.exe` exists

### Conversion fails

```bash
# Enable verbose mode for details
./voxbridge convert --input model.glb --output model.gltf --target roblox --verbose

# Enable debug mode for maximum detail
./voxbridge convert --input model.glb --output model.gltf --target roblox --debug
```

### GUI won't start

- Try running from command line to see error messages
- Check system requirements (2GB RAM minimum)
- Ensure you have display/graphics drivers installed

## 🔗 Learn More

### Official Documentation

- **GLTF Specification**: [https://registry.khronos.org/glTF/](https://registry.khronos.org/glTF/)
- **Roblox Mesh Import**: [https://create.roblox.com/docs/art/modeling/meshes](https://create.roblox.com/docs/art/modeling/meshes)
- **Unity GLTF Import**: [https://docs.unity3d.com/Packages/com.unity.formats.gltf](https://docs.unity3d.com/Packages/com.unity.formats.gltf)
- **The Sandbox VoxEdit**: [https://www.sandbox.game/voxedit](https://www.sandbox.game/voxedit)

### VoxBridge Resources

- **Full Documentation**: [Usage Guide](usage.md)
- **Report Issues**: [GitHub Issues](https://github.com/Supercoolkayy/voxbridge/issues)
- **Ask Questions**: [GitHub Discussions](https://github.com/Supercoolkayy/voxbridge/discussions)

## 🎉 You're Ready!

VoxBridge is now ready to convert your VoxEdit models to Unity and Roblox. Start with a simple conversion and explore the advanced features as you get comfortable.

**Happy converting!**
