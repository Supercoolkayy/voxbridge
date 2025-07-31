# VoxBridge

**Professional VoxEdit to Unity/Roblox Asset Converter**

Convert VoxEdit glTF/GLB exports into optimized formats for Unity and Roblox. Supports mesh optimization, texture atlasing, and batch processing.

## Quick Start

```bash
# Install globally
pipx install voxbridge

# Convert a single file
voxbridge convert --input model.glb --target unity

# Batch process multiple files
voxbridge batch ./input_folder ./output_folder --target unity

# Launch GUI
voxbridge-gui
```

## Features

- **Unity Export**: Optimized FBX and glTF files for Unity
- **Roblox Export**: Optimized mesh and texture formats for Roblox
- **Mesh Optimization**: Polygon reduction and mesh splitting
- **Texture Atlasing**: Combine multiple textures into single atlas
- **Batch Processing**: Convert multiple files at once
- **GUI Interface**: User-friendly graphical interface
- **Performance Reports**: Detailed conversion statistics

## Installation

### Global Installation (Recommended)

```bash
pipx install voxbridge
```

### Alternative Installation

```bash
pip install voxbridge
```

## Usage

### Command Line Interface

```bash
# Convert single file
voxbridge convert --input model.glb --target unity --optimize-mesh

# Convert for Roblox
voxbridge convert --input model.glb --target roblox --generate-atlas

# Batch processing
voxbridge batch ./input_folder ./output_folder --target unity --recursive

# System diagnostics
voxbridge doctor
```

### GUI Interface

```bash
voxbridge-gui
```

## Examples

```bash
# Basic Unity conversion
voxbridge convert --input character.glb --target unity

# Optimized Roblox conversion
voxbridge convert --input building.glb --target roblox --optimize-mesh --generate-atlas

# Batch process with compression
voxbridge batch ./models ./output --target unity --recursive
```

## Requirements

- Python 3.9+
- Blender (optional, for advanced processing)
- Supported file formats: glTF, GLB

## Documentation

For detailed documentation, visit: https://supercoolkayy.github.io/voxbridge/

## Support

- **Issues**: https://github.com/Supercoolkayy/voxbridge/issues
- **Discussions**: https://github.com/Supercoolkayy/voxbridge/discussions

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

---

**Made with by Dapps over Apps**
