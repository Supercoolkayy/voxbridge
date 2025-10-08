# Examples

This directory contains example input and output files for testing VoxBridge functionality.

## Directory Structure

```
examples/
├── input/          # Place your test glTF/glb files here
├── output/         # Processed files will be saved here
└── README.md       # This file
```

## Usage

### Adding Test Files

Place your test glTF/glb files in the `input/` directory:

- `voxel_house.glb` - Complex house model with multiple materials
- `character.glb` - Character model with textures
- `broken_paths.gltf` - File with absolute paths for testing fixes

### Running Examples

```bash
# Convert a GLB file
voxbridge-cli examples/input/voxel_house.glb examples/output/voxel_house_clean.glb

# Convert a glTF file
voxbridge-cli examples/input/broken_paths.gltf examples/output/broken_paths_clean.gltf

# With optimizations
voxbridge-cli examples/input/character.glb examples/output/character_opt.glb --optimize-mesh --platform unity
```

### Example Output

```
VoxBridge v0.2.0 - VoxEdit to Unity/Roblox Converter
=======================================================
[INPUT]  examples/input/voxel_house.glb
[OUTPUT] examples/output/voxel_house_clean.glb

[PROCESS] Using Blender for GLB cleanup...
[SUCCESS] Conversion completed successfully!

[STATS] Validation Results:
  [OK] File created: 2,445,234 bytes
  [INFO] GLB format - use Blender for detailed analysis

[READY] Ready for import into Unity and Roblox!

[COMPLETE] VoxBridge conversion complete!
```

## Validation

To validate the output files:

1. **Unity**: Import the cleaned files into Unity using the Khronos glTF importer
2. **Roblox**: Use the glTF Importer plugin in Roblox Studio
3. **Online Viewer**: Use online glTF viewers like three.js editor

## Batch Processing Example

```python
import os
from pathlib import Path
from voxbridge import VoxBridgeConverter

converter = VoxBridgeConverter()
input_dir = Path("examples/input")
output_dir = Path("examples/output")

for file_path in input_dir.glob("*.glb"):
    if file_path.is_file():
        print(f"\n[PROCESS] Converting {file_path.name}...")
        output_path = output_dir / f"clean_{file_path.name}"

        success = converter.convert_file(file_path, output_path)
        if success:
            print(f"[SUCCESS] {file_path.name} converted successfully")
        else:
            print(f"[ERROR] Failed to convert {file_path.name}")
```

## Notes

- The `input/` and `output/` directories are initially empty
- Add your own test files to `input/` to test VoxBridge functionality
- Processed files will be saved to `output/` after conversion
- Use the main README.md for detailed usage instructions
