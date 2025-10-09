# VoxBridge Build Instructions

This document provides comprehensive instructions for building VoxBridge executables for Windows and Linux platforms.

## Quick Start

### Automatic Build (Recommended)

The easiest way to build VoxBridge is using the universal build script:

**Windows:**

```cmd
build.bat
```

**Linux/macOS:**

```bash
./build.sh
```

**Cross-platform:**

```bash
python build_all.py
```

### Manual Build

If you prefer to run platform-specific builds manually:

**Windows:**

```powershell
powershell -ExecutionPolicy Bypass -File build_windows.ps1
```

**Linux:**

```bash
./build_linux.sh
```

## Build Requirements

### System Requirements

- **Python 3.8+** (with pip)
- **Node.js 18+** (with npm)
- **Git** (for cloning the repository)

### Windows Specific

- **PowerShell 5.0+** (for running the build script)
- **Visual Studio Build Tools** (recommended for some Python packages)

### Linux Specific

- **build-essential** package (gcc, make, etc.)
- **Python3-dev** package
- **bc** (for calculations in build script)

## Build Outputs

All build outputs are placed in the `dist/` directory:

### Windows

- `voxbridge.exe` - Main CLI application
- `voxbridge-gui.exe` - GUI application
- `node_runner.exe` - Node.js processor (internal)

### Linux/macOS

- `voxbridge` - Main CLI application
- `voxbridge-gui` - GUI application
- `node_runner` - Node.js processor (internal)

## Build Process Details

### Node.js Build Process

The Node.js executable (`node_runner`) is built using multiple fallback methods:

1. **pkg-fetch** (Preferred)

   - Downloads Node.js binary and bundles with application code
   - Creates single self-contained executable

2. **nexe** (Fallback 1)

   - Alternative Node.js packaging tool
   - Handles complex dependencies better in some cases

3. **@vercel/ncc + Node Binary** (Fallback 2)

   - Bundles code with ncc
   - Concatenates with Node.js binary
   - Creates portable executable

4. **esbuild** (Fallback 3)
   - Fast bundling with esbuild
   - Creates wrapper script with Node.js

### Python Build Process

Python executables are built using multiple fallback methods:

#### CLI Application (voxbridge/voxbridge.exe)

1. **PyInstaller** (Preferred)

   - Single-file executable
   - Includes all dependencies
   - Cross-platform support

2. **Nuitka** (Fallback 1)

   - Compiles Python to C++
   - Faster execution
   - Smaller file size

3. **py2exe** (Windows only, Fallback 2)

   - Windows-specific packaging
   - Alternative to PyInstaller

4. **cx_Freeze** (Fallback 3)
   - Cross-platform packaging
   - Good for complex dependencies

#### GUI Application (voxbridge-gui/voxbridge-gui.exe)

Same methods as CLI, but with GUI-specific settings:

- `--windowed` flag for PyInstaller (no console window)
- `--disable-console` for Nuitka
- GUI-specific hidden imports (tkinter, etc.)

## Build Script Features

### Automatic Fallback Handling

- If one build method fails, automatically tries the next
- Comprehensive error reporting
- Validation of final executables

### Dependency Management

- Automatic installation of build tools
- Version checking for required software
- Platform-specific dependency handling

### Validation

- File size validation (ensures non-empty executables)
- Execution testing (runs `--help` to verify functionality)
- Comprehensive error reporting

### Cleanup

- Automatic cleanup of build artifacts
- Organized output structure
- Convenience scripts for easy execution

## Troubleshooting

### Common Issues

**"Node.js not found"**

- Install Node.js 18+ from [nodejs.org](https://nodejs.org/)
- Ensure npm is also installed

**"Python not found"**

- Install Python 3.8+ from [python.org](https://python.org/)
- Ensure pip is installed and in PATH

**"Permission denied" (Linux)**

```bash
chmod +x build_linux.sh
chmod +x build.sh
```

**"Execution policy" (Windows)**

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**"Build timeout"**

- Some builds may take 30-60 minutes
- Ensure stable internet connection for downloading dependencies
- Close other resource-intensive applications

### Build Failures

If all build methods fail:

1. **Check dependencies:**

   ```bash
   python --version
   node --version
   npm --version
   ```

2. **Clean build environment:**

   ```bash
   rm -rf dist/ build/ node_modules/
   ```

3. **Reinstall dependencies:**

   ```bash
   pip install -r requirements.txt
   cd node_scripts && npm install && cd ..
   ```

4. **Try manual build:**
   - Run individual build scripts with verbose output
   - Check error messages for specific issues

### Platform-Specific Issues

**Windows:**

- Ensure Windows Defender doesn't block the build process
- Run PowerShell as Administrator if needed
- Install Visual Studio Build Tools for C++ extensions

**Linux:**

- Install development packages: `sudo apt-get install build-essential python3-dev`
- Ensure sufficient disk space (builds can be large)
- Check file permissions on build scripts

## Advanced Usage

### Custom Build Options

**Skip dependency installation:**

```bash
./build_linux.sh --skip-deps
```

**Verbose output:**

```bash
./build_linux.sh --verbose
```

**Windows with custom PowerShell:**

```powershell
powershell -ExecutionPolicy Bypass -File build_windows.ps1 -Verbose
```

### Environment Variables

**Custom Node.js version:**

```bash
export NODE_VERSION=18.17.0
./build_linux.sh
```

**Custom Python path:**

```bash
export PYTHON_PATH=/usr/local/bin/python3
./build_linux.sh
```

## Build Script Architecture

### File Structure

```
├── build_all.py          # Universal build script
├── build_windows.ps1     # Windows-specific build
├── build_linux.sh        # Linux-specific build
├── build.bat             # Windows convenience script
├── build.sh              # Linux convenience script
├── BUILD_INSTRUCTIONS.md # This file
└── dist/                 # Build outputs directory
```

### Error Handling

- Comprehensive try-catch blocks
- Graceful fallback between build methods
- Detailed error reporting
- Validation at each step

### Modularity

- Separate functions for each build method
- Reusable validation functions
- Platform-specific optimizations
- Easy to extend with new build methods

## Contributing

To add new build methods or improve existing ones:

1. **Add new build method:**

   - Create function with descriptive name
   - Include proper error handling
   - Add validation step
   - Update fallback chain

2. **Improve error handling:**

   - Add specific error messages
   - Include troubleshooting hints
   - Log detailed information

3. **Add platform support:**
   - Create new platform-specific script
   - Update universal build script
   - Add platform detection logic

## Support

For build issues:

1. Check this documentation first
2. Run with verbose output to see detailed logs
3. Check the GitHub issues page
4. Create new issue with build logs and system information
