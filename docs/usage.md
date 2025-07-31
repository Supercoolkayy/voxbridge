# Usage

VoxBridge can be used from the command line to clean, optimize, and prepare glTF/glb files for Unity and Roblox.

## Basic CLI Usage

```bash
voxbridge-cli input.glb output.glb
voxbridge-cli input.gltf output.gltf
```

## Optimization Flags

- `--optimize-mesh` : Enable polygon reduction and mesh splitting in Blender (GLB only)
- `--generate-atlas` : Generate a texture atlas for all textures (glTF only)
- `--compress-textures` : Compress and resize textures to 1024x1024 (glTF only)
- `--platform [unity|roblox]` : Target platform for material mapping (default: unity)
- `--report` : Generate a performance summary report (performance_report.json)

## Example Commands

```bash
# Clean and optimize a GLB file (polygon reduction)
voxbridge-cli input.glb output.glb --optimize-mesh

# Clean and generate a texture atlas for a glTF file
voxbridge-cli input.gltf output.gltf --generate-atlas

# Clean and compress all textures in a glTF file
voxbridge-cli input.gltf output.gltf --compress-textures

# Optimize for Unity (default)
voxbridge-cli input.gltf output.gltf --platform unity

# Optimize for Roblox
voxbridge-cli input.gltf output.gltf --platform roblox

# Generate a performance report
voxbridge-cli input.gltf output.gltf --report

# Combine all optimizations for Unity with performance report
voxbridge-cli input.glb output.glb --optimize-mesh --generate-atlas --compress-textures --platform unity --report

# Combine all optimizations for Roblox with performance report
voxbridge-cli input.glb output.glb --optimize-mesh --generate-atlas --compress-textures --platform roblox --report
```

## Performance Report

When using `--report`, VoxBridge generates a `performance_report.json` file containing:

- **File Statistics**: Size before/after, reduction percentage
- **Asset Metrics**: Triangle counts, texture info, mesh/material counts
- **Processing Info**: Timestamp, processing time, platform
- **Optimizations**: List of applied optimizations
- **Warnings**: Performance warnings and recommendations
- **Notes**: Additional processing notes

Example report structure:

```json
{
  "input_file": "input.glb",
  "output_file": "output.glb",
  "timestamp": "2024-01-15 14:30:25",
  "processing_time": 12.5,
  "file_size_before": 2048576,
  "file_size_after": 1536000,
  "size_reduction_percent": 25.0,
  "textures": 3,
  "meshes": 5,
  "materials": 2,
  "platform": "unity",
  "optimizations_applied": ["Mesh optimization", "Texture compression"],
  "warnings": ["Large file size (>50MB) - consider further optimization"],
  "notes": ["GLB format - use Blender for detailed analysis"]
}
```

## Platform-Specific Features

### Unity

- Material names cleaned for Unity compatibility
- Color space adjustments for Unity Standard shader
- Metallic-roughness texture verification

### Roblox

- Stricter material naming (alphanumeric only, max 50 chars)
- Reduced metallic factors for better compatibility
- Simplified material properties

## Notes

- `--optimize-mesh` only applies to GLB files and requires Blender.
- `--generate-atlas` and `--compress-textures` only apply to glTF files and require Pillow, numpy, and pygltflib.
- `--platform` affects material mapping and naming conventions for the target platform.
- `--report` generates a detailed JSON report in the output directory.
