# VoxBridge CI/CD Automation Guide

## Automatic Builds

Your VoxBridge project now has automated CI/CD that builds executables for all platforms!

## How to Trigger Builds

### Method 1: Create a Version Tag (Recommended)
```bash
# Tag your current version
git tag v2.0.0

# Push the tag to GitHub
git push origin v2.0.0
```

This will automatically:
1. Build executables for Linux, macOS, and Windows
2. Bundle Node.js processing
3. Include all dependencies
4. Create a GitHub Release with downloadable files

### Method 2: Manual Trigger
1. Go to GitHub: `https://github.com/Supercoolkayy/voxbridge/actions`
2. Click "Build and Release VoxBridge"
3. Click "Run workflow"
4. Select branch and click "Run workflow"

## What Gets Built

Each build creates:
- **voxbridge** - CLI executable
- **voxbridge-gui** - GUI executable  
- **node_scripts/** - Node.js processing scripts
- **build/node_binary/** - Bundled Node.js runner
- **docs/** - Documentation
- **examples/** - Example files

## Download Locations

After the build completes (about 10-15 minutes):

1. **GitHub Releases** (for tagged builds):
   - Go to: `https://github.com/Supercoolkayy/voxbridge/releases`
   - Download platform-specific package:
     - `voxbridge-linux-x64.tar.gz`
     - `voxbridge-macos-x64.tar.gz`
     - `voxbridge-windows-x64.zip`

2. **GitHub Actions** (for all builds):
   - Go to: `https://github.com/Supercoolkayy/voxbridge/actions`
   - Click on the latest workflow run
   - Scroll to "Artifacts" section
   - Download the package for your platform

## Using the Executables

### Linux/macOS:
```bash
# Extract
tar -xzf voxbridge-linux-x64.tar.gz
cd voxbridge

# Run CLI
./voxbridge convert -i input.glb -o output/ -t unity

# Run GUI
./voxbridge-gui
```

### Windows:
```powershell
# Extract voxbridge-windows-x64.zip
cd voxbridge

# Run CLI
.\voxbridge.exe convert -i input.glb -o output/ -t unity

# Run GUI
.\voxbridge-gui.exe
```

## Version Tagging Best Practices

```bash
# For major releases
git tag v1.0.0

# For minor updates
git tag v1.1.0

# For patches
git tag v1.0.1

# Always push tags
git push origin --tags
```

## What's Included in Each Build

- ✅ Standalone executables (no Python installation needed)
- ✅ Bundled Node.js runner (process_complex.js)
- ✅ All node_modules dependencies
- ✅ Complete documentation
- ✅ Example models
- ✅ Cross-platform compatibility

## No Manual Building Required!

You no longer need to:
- Run PyInstaller manually
- Build Node.js binaries locally
- Package files yourself
- Create platform-specific builds

Just push a tag and let GitHub Actions do everything!

