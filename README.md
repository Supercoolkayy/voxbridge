# VoxBridge

**Professional VoxEdit to Unity/Roblox Asset Converter**

Convert VoxEdit glTF/GLB exports into optimized formats for Unity and Roblox. Supports mesh optimization, texture atlasing, and batch processing.

## Quick Start

### Installation

```bash
# Method 1: Using pipx (Recommended)
pipx install voxbridge

# Method 2: Using pip
pip install voxbridge

# Method 3: From source
git clone https://github.com/Supercoolkayy/voxbridge.git
cd voxbridge
bash scripts/install.sh
```

### Usage

```bash
# Convert a single file
voxbridge convert --input model.glb --target unity

# Batch process multiple files
voxbridge batch ./input_folder ./output_folder --target unity

# Launch GUI
voxbridge-gui

# System diagnostics
voxbridge doctor
```

### Troubleshooting

If you get "voxbridge command not found":

```bash
# Use module execution instead
python3 -m voxbridge.cli --help
python3 -m voxbridge.cli convert --input model.glb --target unity

# Or fix PATH
export PATH="$HOME/.local/bin:$PATH"
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
# Install pipx if you don't have it
python3 -m pip install --user pipx
python3 -m pipx ensurepath

# Install VoxBridge
pipx install voxbridge
```

### Alternative Installation

```bash
pip install voxbridge

# Add to PATH if needed
export PATH="$HOME/.local/bin:$PATH"
```

### From Source

```bash
git clone https://github.com/Supercoolkayy/voxbridge.git
cd voxbridge
bash scripts/install.sh
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

## Testing

### Run Import Tests

```bash
# Test Unity and Roblox import compatibility
python3 test_imports.py

# Run unit tests
python3 -m pytest tests/

# Run CLI tests
python3 test_cli.py
```

### Performance Analysis

See [docs/performance.md](docs/performance.md) for detailed performance characteristics and optimization results.

## Requirements

- Python 3.9+
- Blender (optional, for advanced processing)
- Supported file formats: glTF, GLB

## Documentation

### Core Guides

- [Installation Guide](docs/installation.md) - Detailed installation instructions
- [Usage Guide](docs/usage.md) - Comprehensive usage documentation
- [Performance Analysis](docs/performance.md) - Detailed performance characteristics
- [Milestone 1 & 2 Resolution Report](docs/MILESTONE_1_2_RESOLUTION_REPORT.md) - Complete analysis of all reported issues and their solutions
- [Current Status](docs/CURRENT_STATUS.md) - Quick overview of all milestones and current status

### Development & Planning

- [Feedback Survey](docs/feedback-survey.md) - Creator feedback collection template

### Additional Resources

- [Release Summary](RELEASE_SUMMARY.md) - Version history and release notes
- [GUI Implementation Report](GUI_IMPLEMENTATION_REPORT.md) - GUI development details
- [Examples Guide](examples/README.md) - Test files and usage examples

### Development Scripts

- `scripts/install.sh` - Automated installation script
- `scripts/test.sh` - Comprehensive test runner
- `scripts/build.sh` - Package building script

## Support

- **Issues**: https://github.com/Supercoolkayy/voxbridge/issues
- **Discussions**: https://github.com/Supercoolkayy/voxbridge/discussions

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

---