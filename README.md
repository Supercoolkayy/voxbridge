# VoxBridge

**Professional VoxEdit to Unity/Roblox Asset Converter**

Convert VoxEdit glTF/GLB exports into optimized formats for Unity and Roblox. Features a robust fallback conversion system, automatic ZIP packaging, and both CLI and GUI interfaces.

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

### Important: PATH Setup After Installation

After installing with `pipx install voxbridge`, you need to add the pipx binary directory to your PATH:

```bash
# Add pipx to PATH (add this to your ~/.bashrc or ~/.zshrc)
export PATH="$HOME/.local/bin:$PATH"

# Or use the pipx command to add it automatically
pipx ensurepath

# Restart your terminal or reload shell configuration
source ~/.bashrc  # or source ~/.zshrc
```

### Usage

```bash
# Convert a single file
voxbridge convert --input model.glb --target unity

# Batch process multiple files
voxbridge batch ./input_folder --output-dir ./output_folder --target unity

# Launch GUI
python3 gui.py

# System diagnostics
voxbridge doctor
```

### 🔧 Troubleshooting: Command Not Found

If you get "voxbridge command not found" after installation:

```bash
# Option 1: Use module execution (always works)
python3 -m voxbridge.cli convert --input model.glb --target unity

# Option 2: Fix PATH and restart terminal
export PATH="$HOME/.local/bin:$PATH"
# Then restart your terminal

# Option 3: Check pipx installation
pipx list
pipx ensurepath
```

## Features

### **Core Conversion**

- **Unity Export**: Optimized glTF files for Unity
- **Roblox Export**: Optimized glTF files for Roblox
- **Mesh Optimization**: Automatic mesh cleanup and optimization
- **ZIP Packaging**: Automatic packaging of output files

### **Advanced Processing**

- **Layered Fallback System**: Blender → Assimp → Trimesh → Basic Converter
- **Automatic Error Recovery**: Continues processing even if advanced tools fail
- **Batch Processing**: Convert multiple files efficiently
- **Progress Tracking**: Real-time conversion progress

### **User Interfaces**

- **Command Line Interface**: Full-featured CLI with verbose/debug options
- **Graphical Interface**: User-friendly GUI for easy file selection and conversion
- **Cross-Platform**: Works on Windows, macOS, and Linux/WSL

## Installation

### **Global Installation (Recommended)**

```bash
# Install pipx if you don't have it
python3 -m pip install --user pipx
python3 -m pipx ensurepath

# Install VoxBridge
pipx install voxbridge

# Verify installation
voxbridge --version
```

### **Alternative Installation**

```bash
# Direct pip install
pip install voxbridge

# Add to PATH if needed
export PATH="$HOME/.local/bin:$PATH"
```

### **From Source**

```bash
git clone https://github.com/Supercoolkayy/voxbridge.git
cd voxbridge
bash scripts/install.sh
```

## Usage

### **Command Line Interface**

#### **Single File Conversion**

```bash
# Basic conversion
voxbridge convert --input model.glb --target unity

# With optimization
voxbridge convert --input model.glb --target roblox --optimize-mesh

# Verbose output
voxbridge convert --input model.glb --target unity --verbose

# Debug mode
voxbridge convert --input model.glb --target unity --debug

# Skip Blender (use fallback converters)
voxbridge convert --input model.glb --target unity --no-blender
```

#### **Batch Processing**

```bash
# Convert all files in a folder
voxbridge batch ./input_folder --output-dir ./output_folder --target unity

# With optimization
voxbridge batch ./input_folder --output-dir ./output_folder --target roblox --optimize-mesh
```

#### **System Diagnostics**

```bash
# Check system compatibility
voxbridge doctor

# Check available converters
voxbridge doctor --verbose
```

### **Graphical Interface**

```bash
# Launch GUI from project root
python3 gui.py

# Or from anywhere (if voxbridge is in PATH)
voxbridge-gui
```

#### **GUI Features**

- **Single File Mode**: Select one .glb/.gltf file for conversion
- **Batch Mode**: Select multiple files for batch processing
- **Output Folder Selection**: Choose where converted files are saved
- **Real-time Progress**: See conversion progress and status
- **Log Display**: View detailed conversion logs
- **System Check**: Verify Blender and other dependencies

## Conversion Process

### **Fallback Chain**

VoxBridge uses a sophisticated fallback system to ensure conversions always succeed:

1. **Blender Conversion** (if available): Advanced mesh cleanup and optimization
2. **Assimp Conversion** (if available): Professional 3D format conversion
3. **Trimesh Conversion** (if available): Pure Python mesh processing
4. **Basic Converter**: Reliable fallback for all platforms

### **Output Packaging**

- **Automatic ZIP Creation**: All output files are packaged into ZIP archives
- **Clean Organization**: No scattered .bin files or temporary files
- **Batch Support**: Each converted file gets its own ZIP

## Examples

### **Basic Conversions**

```bash
# Unity conversion
voxbridge convert --input character.glb --target unity

# Roblox conversion with optimization
voxbridge convert --input building.glb --target roblox --optimize-mesh

# Skip Blender (use fallback)
voxbridge convert --input model.glb --target unity --no-blender
```

### **Batch Processing**

```bash
# Convert all models in a folder
voxbridge batch ./models ./output --target unity

# With optimization
voxbridge batch ./models ./output --target roblox --optimize-mesh
```

### **GUI Usage**

```bash
# Launch GUI
python3 gui.py

# Select files and output folder
# Click "Convert" to start processing
# Monitor progress in real-time
# Find results in ZIP files
```

## Testing

### **Test the Installation**

```bash
# Test CLI
voxbridge --help
voxbridge convert --help

# Test GUI
python3 gui.py

# Test conversion with sample file
voxbridge convert --input examples/input/4_cubes.glb --target unity --output examples/output/test
```

### **Run Import Tests**

```bash
# Test Unity and Roblox import compatibility
python3 test_imports.py

# Run unit tests
python3 -m pytest tests/

# Run CLI tests
python3 test_cli.py
```

## Requirements

### **System Requirements**

- **Python**: 3.9 or higher
- **OS**: Windows, macOS, or Linux (including WSL)
- **Memory**: 2GB RAM minimum, 4GB recommended
- **Storage**: 100MB free space

### **Optional Dependencies**

- **Blender**: For advanced mesh processing (auto-detected)
- **Assimp**: For professional 3D conversion (auto-detected)
- **Trimesh**: For Python-based mesh processing (auto-detected)

### **Supported Input Formats**

- **GLB**: Binary glTF files (primary format)
- **GLTF**: glTF files with external resources

### **Output Formats**

- **GLTF**: Clean glTF files with external .bin files
- **ZIP**: Packaged archives containing all necessary files

## Documentation

### **Core Guides**

- [Installation Guide](docs/installation.md) - Detailed installation instructions
- [Usage Guide](docs/usage.md) - Comprehensive usage documentation
- [Performance Analysis](docs/performance.md) - Detailed performance characteristics
- [Milestone 1 & 2 Resolution Report](docs/MILESTONE_1_2_RESOLUTION_REPORT.md) - Complete analysis of all reported issues and their solutions
- [Current Status](docs/CURRENT_STATUS.md) - Quick overview of all milestones and current status

### **Development & Planning**

- [Feedback Survey](docs/feedback-survey.md) - Creator feedback collection template

### **Additional Resources**

- [Release Summary](RELEASE_SUMMARY.md) - Version history and release notes
- [GUI Implementation Report](GUI_IMPLEMENTATION_REPORT.md) - GUI development details
- [Examples Guide](examples/README.md) - Test files and usage examples

### **Development Scripts**

- `scripts/install.sh` - Automated installation script
- `scripts/test.sh` - Comprehensive test runner
- `scripts/build.sh` - Package building script

## Support & Troubleshooting

### **Common Issues**

#### **"voxbridge command not found"**

```bash
# Solution 1: Use module execution
python3 -m voxbridge.cli --help

# Solution 2: Fix PATH
export PATH="$HOME/.local/bin:$PATH"
# Add to ~/.bashrc or ~/.zshrc for permanent fix

# Solution 3: Reinstall with pipx
pipx uninstall voxbridge
pipx install voxbridge
pipx ensurepath
```

#### **Blender Conversion Fails**

```bash
# Use fallback conversion
voxbridge convert --input model.glb --target unity --no-blender

# Or install numpy in Blender's Python
# (See detailed error messages for instructions)
```

#### **Conversion Errors**

```bash
# Enable verbose mode for details
voxbridge convert --input model.glb --target unity --verbose

# Enable debug mode for maximum detail
voxbridge convert --input model.glb --target unity --debug
```

### **Getting Help**

- **Issues**: https://github.com/Supercoolkayy/voxbridge/issues
- **Discussions**: https://github.com/Supercoolkayy/voxbridge/discussions
- **Documentation**: Check the docs/ folder for detailed guides

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### **Development Setup**

```bash
# Clone the repository
git clone https://github.com/Supercoolkayy/voxbridge.git
cd voxbridge

# Install in development mode
pip install -e .

# Run tests
python3 -m pytest tests/

# Launch GUI for testing
python3 gui.py
```

---

**VoxBridge v1.0.7** - Professional Asset Conversion Made Simple
