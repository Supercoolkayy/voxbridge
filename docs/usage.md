# VoxBridge Usage Guide

**How to use VoxBridge for converting VoxEdit models to Unity and Roblox**

## 🎉 Version 2.0 - Platform-Specific Material Export!

VoxBridge now supports **platform-specific texture packing** with the `-t` (target) flag:

- **`-t unity`**: Packs PBR textures for Unity's Standard Shader (fixes gray materials!)
- **`-t roblox`**: Simplifies materials for Roblox (keeps only BaseColor + Normal)
- **`-t gltf`**: Standard GLTF export (no modifications, universal compatibility)

See the [Texture Packing Guide](TEXTURE_PACKING_GUIDE.md) for complete details.

## 📋 Supported Formats

### ✅ Input Formats

- **GLB (GLTF Binary)** - Exported from The Sandbox VoxEdit
- **glTF** - Text-based GLTF files from VoxEdit

### ✅ Output Formats

- **glTF** - Optimized for Unity or Roblox
- **ZIP packages** - Automatic packaging of output files

### ❌ Not Supported

- **OBJ files** - Not supported at this stage
- **FBX files** - Not supported at this stage
- **Random 3D models** - Only VoxEdit exports work
- **Other formats** - Only GLB/glTF from VoxEdit

> ⚠️ **Important**: Always export your assets from The Sandbox VoxEdit in GLB format for best results.

## 🎮 Target Platforms

### Unity (`-t unity`) - Fixes Gray Materials!

- **Input**: VoxEdit .glb/.gltf files
- **Output**: Unity-optimized glTF with packed PBR textures
- **Material Handling**: Automatically packs separate PBR maps into Unity's Standard Shader format
  - R = Metallic, G = Smoothness, B = AO, A = Gloss
- **Fixes**: Gray material problem caused by Unity's different PBR interpretation
- **Works in**: Both Unity AND GLTF viewers

### Roblox (`-t roblox`) - Lightweight & Optimized

- **Input**: VoxEdit .glb/.gltf files
- **Output**: Roblox-compatible glTF with simplified materials
- **Material Handling**: Keeps only what Roblox uses (BaseColor + Normal)
- **Benefits**: Smaller files, faster imports, engine-optimized
- **Removes**: Metallic/roughness/occlusion textures (unused by Roblox)

### Standard GLTF (`-t gltf`) - Universal Compatibility

- **Input**: VoxEdit .glb/.gltf files
- **Output**: Standard GLTF with full PBR support
- **Material Handling**: No modifications, full GLTF spec compliance
- **Use for**: GLTF/GLB viewers, other game engines, maximum compatibility

## 🔧 Basic CLI Usage

### Single File Conversion

```bash
# Unity export (fixes gray materials with packed textures!)
voxbridge convert -i model.glb -o output/ -t unity

# Roblox export (lightweight, optimized materials)
voxbridge convert -i model.glb -o output/ -t roblox

# Standard GLTF export (universal compatibility)
voxbridge convert -i model.glb -o output/ -t gltf

# Unity with mesh optimization (requires Node.js)
voxbridge convert -i model.glb -o output/ -t unity --optimize-mesh

# Roblox in fast mode (no optimizations)
voxbridge convert -i model.glb -o output/ -t roblox --fast
```

### Static vs Animated Models

```bash
# Static model (fast, no Node.js needed)
# - Original skeleton removed
# - Optimized tri-mesh export
voxbridge convert -i building.glb -o output/ -t unity --force-static

# Animated model (requires Node.js)
# - Full rigging preserved
# - Skinning maintained
# - Static duplicates removed
voxbridge convert -i character.glb -o output/ -t unity --force-node

# Auto-detect (default - VoxBridge chooses best path)
voxbridge convert -i model.glb -o output/ -t unity
```

### Batch Processing

```bash
# Batch convert to Unity (with texture packing)
voxbridge batch ./input_folder -o ./output_folder -t unity

# Batch convert to Roblox (simplified materials)
voxbridge batch ./input_folder -o ./output_folder -t roblox

# Batch convert with optimization (requires Node.js)
voxbridge batch ./input_folder -o ./output_folder -t unity --optimize-mesh
```

## 🚀 Performance & Node.js Requirements

### Works Without Node.js

- ✅ Basic conversions (`-t unity`, `-t roblox`, `-t gltf`)
- ✅ Static model processing (`--force-static`)
- ✅ Simple models without animations
- ✅ GLB packing (`--pack-glb`)
- ✅ Platform-specific texture packing (Unity/Roblox)

### Requires Node.js (18+ LTS)

- ⚡ Complex model processing (animations, rigging)
- ⚡ Mesh optimization (`--optimize-mesh`)
- ⚡ Draco compression (`--use-draco`)
- ⚡ Texture resizing (`--texture-size`)
- ⚡ Quantization (`--quantize`)
- ⚡ Large file processing (>50MB)
- ⚡ 2-3x faster processing on complex assets

### Install Node.js

```bash
# Download from nodejs.org (LTS version recommended)
# https://nodejs.org/

# Verify installation
node --version
npm --version

# Check VoxBridge can find Node.js
voxbridge doctor
```

## ⚙️ Optimization Flags

### Mesh Optimization

- `--optimize-mesh` - Enable polygon reduction and mesh splitting (GLB only)
- Reduces file size and improves performance
- Recommended for most conversions

### Texture Optimization

- `--generate-atlas` - Generate a texture atlas for all textures (glTF only)
- `--compress-textures` - Compress and resize textures to 1024x1024 (glTF only)

### Platform-Specific

- `--platform [unity|roblox]` - Target platform for material mapping (default: unity)
- `--report` - Generate a performance summary report

## 📊 Example Commands

### For Unity (Fixes Gray Materials!)

```bash
# Basic Unity conversion with texture packing
voxbridge convert -i model.glb -o output/ -t unity

# Unity with all optimizations (requires Node.js)
voxbridge convert -i model.glb -o output/ -t unity --optimize-mesh --use-draco

# Unity for static model (fast, no Node.js)
voxbridge convert -i building.glb -o output/ -t unity --force-static

# Unity for animated character (requires Node.js)
voxbridge convert -i character.glb -o output/ -t unity --force-node

# Batch convert for Unity
voxbridge batch ./input_folder -o ./output_folder -t unity
```

### For Roblox (Optimized & Lightweight)

```bash
# Basic Roblox conversion (simplified materials)
voxbridge convert -i model.glb -o output/ -t roblox

# Roblox with Draco compression (requires Node.js)
voxbridge convert -i model.glb -o output/ -t roblox --use-draco

# Roblox fast mode (no optimizations)
voxbridge convert -i model.glb -o output/ -t roblox --fast

# Batch convert for Roblox
voxbridge batch ./input_folder -o ./output_folder -t roblox
```

### For Standard GLTF (Universal)

```bash
# Standard GLTF export (no modifications)
voxbridge convert -i model.glb -o output/ -t gltf

# Standard GLTF with Draco (requires Node.js)
voxbridge convert -i model.glb -o output/ -t gltf --use-draco
```

### Advanced Examples

```bash
# Unity with custom texture size (requires Node.js)
voxbridge convert -i model.glb -o output/ -t unity --texture-size 2048

# Roblox with verbose output
voxbridge convert -i model.glb -o output/ -t roblox --verbose

# Unity with debug info
voxbridge convert -i model.glb -o output/ -t unity --debug

# Full optimization for Unity (requires Node.js)
voxbridge convert -i model.glb -o output/ -t unity \
  --optimize-mesh --use-draco --quantize --texture-size 1024
```

## 📈 Performance Report

When using `--report`, VoxBridge generates a `performance_report.json` file containing:

- **File Statistics**: Size before/after, reduction percentage
- **Asset Metrics**: Triangle counts, texture info, mesh/material counts
- **Processing Info**: Timestamp, processing time, platform
- **Optimizations**: List of applied optimizations
- **Warnings**: Performance warnings and recommendations

### Example Report Structure

```json
{
  "input_file": "model.glb",
  "output_file": "model.gltf",
  "timestamp": "2024-01-15 14:30:25",
  "processing_time": 12.5,
  "file_size_before": 2048576,
  "file_size_after": 1536000,
  "size_reduction_percent": 25.0,
  "textures": 3,
  "meshes": 5,
  "materials": 2,
  "platform": "roblox",
  "optimizations_applied": ["Mesh optimization", "Texture compression"],
  "warnings": ["Large file size (>50MB) - consider further optimization"],
  "notes": ["GLB format - use Blender for detailed analysis"]
}
```

## 🎯 Platform-Specific Features

### Unity

- Material names cleaned for Unity compatibility
- Color space adjustments for Unity Standard shader
- Metallic-roughness texture verification
- Full PBR material support

### Roblox

- Stricter material naming (alphanumeric only, max 50 chars)
- Reduced metallic factors for better compatibility
- Simplified material properties
- Optimized for Roblox Studio import

## 🛠️ Troubleshooting

### Common Issues

**"Command not found"**

- Make sure you're in the VoxBridge folder
- Check that the executable exists
- Try using `./voxbridge` instead of `voxbridge`

**"Permission denied" (Linux/macOS)**

```bash
chmod +x voxbridge voxbridge-gui
```

**Conversion fails**

```bash
# Get detailed error info
voxbridge convert --input model.glb --output model.gltf --target roblox --verbose --debug
```

**File format errors**

- Ensure your input file is a valid GLB from VoxEdit
- Check that the file isn't corrupted
- Try re-exporting from VoxEdit

### Getting Help

```bash
# Get help
voxbridge --help

# Get help for specific command
voxbridge convert --help

# Check system status
voxbridge doctor
```

## 📚 Additional Resources

### Official Documentation

- **GLTF Specification**: [https://registry.khronos.org/glTF/](https://registry.khronos.org/glTF/)
- **Roblox Mesh Import**: [https://create.roblox.com/docs/art/modeling/meshes](https://create.roblox.com/docs/art/modeling/meshes)
- **Unity GLTF Import**: [https://docs.unity3d.com/Packages/com.unity.formats.gltf](https://docs.unity3d.com/Packages/com.unity.formats.gltf)
- **The Sandbox VoxEdit**: [https://www.sandbox.game/voxedit](https://www.sandbox.game/voxedit)

### VoxBridge Resources

- **Quick Start Guide**: [QUICK_START.md](QUICK_START.md)
- **Report Issues**: [GitHub Issues](https://github.com/Supercoolkayy/voxbridge/issues)
- **Ask Questions**: [GitHub Discussions](https://github.com/Supercoolkayy/voxbridge/discussions)

## ⚠️ Important Notes

- `--optimize-mesh` only applies to GLB files and requires Blender
- `--generate-atlas` and `--compress-textures` only apply to glTF files
- `--platform` affects material mapping and naming conventions
- `--report` generates a detailed JSON report in the output directory
- Always use GLB files exported from The Sandbox VoxEdit for best results
