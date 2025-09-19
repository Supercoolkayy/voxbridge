# VoxBridge Usage Guide

**How to use VoxBridge for converting VoxEdit models to Unity and Roblox**

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

### Unity

- **Input**: VoxEdit .glb/.gltf files
- **Output**: Optimized glTF files for Unity
- **Features**: Full PBR materials, mesh optimization, texture handling

### Roblox

- **Input**: VoxEdit .glb/.gltf files
- **Output**: Roblox-compatible glTF files
- **Features**: Simplified materials, Roblox-specific optimizations

## 🔧 Basic CLI Usage

### Single File Conversion

```bash
# Basic conversion for Roblox
voxbridge convert --input model.glb --output model.gltf --target roblox

# Basic conversion for Unity
voxbridge convert --input model.glb --output model.gltf --target unity

# With optimization (recommended)
voxbridge convert --input model.glb --output model.gltf --target roblox --optimize-mesh
```

### Batch Processing

```bash
# Convert all GLB files in a folder
voxbridge batch ./input_folder --output-dir ./output_folder --target roblox

# Convert with optimization
voxbridge batch ./input_folder --output-dir ./output_folder --target unity --optimize-mesh
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

### For Roblox

```bash
# Basic Roblox conversion
voxbridge convert --input model.glb --output model.gltf --target roblox

# Optimized Roblox conversion
voxbridge convert --input model.glb --output model.gltf --target roblox --optimize-mesh

# Batch convert for Roblox
voxbridge batch ./input_folder --output-dir ./output_folder --target roblox --optimize-mesh
```

### For Unity

```bash
# Basic Unity conversion
voxbridge convert --input model.glb --output model.gltf --target unity

# Optimized Unity conversion
voxbridge convert --input model.glb --output model.gltf --target unity --optimize-mesh

# Batch convert for Unity
voxbridge batch ./input_folder --output-dir ./output_folder --target unity --optimize-mesh
```

### Advanced Examples

```bash
# Generate performance report
voxbridge convert --input model.glb --output model.gltf --target roblox --report

# Combine all optimizations for Unity
voxbridge convert --input model.glb --output model.gltf --target unity --optimize-mesh --generate-atlas --compress-textures --report

# Verbose output for troubleshooting
voxbridge convert --input model.glb --output model.gltf --target roblox --verbose --debug
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
