# VoxBridge Texture Packing Guide

## The Problem

GLTF models export with separate PBR texture maps (BaseColor, Metallic/Roughness, Occlusion, Normal, etc.). While these work perfectly in GLTF viewers, Unity and Roblox engines interpret these textures differently, leading to:

- **Unity**: Gray or broken materials because Unity's Standard Shader expects packed textures
- **Roblox**: Unnecessary textures that don't affect rendering but increase file size

## The Solution

VoxBridge now supports **platform-specific material export** using the `-t` (target) flag.

## Usage

### Unity Export (`-t unity`)

**Fixes the gray texture problem in Unity!**

```bash
voxbridge convert model.glb -o output/ -t unity
```

**What it does:**
- Packs PBR textures into Unity's Standard Shader format:
  - **R channel** = Metallic (from GLTF's B channel)
  - **G channel** = Smoothness (inverted Roughness from GLTF's G channel)
  - **B channel** = Ambient Occlusion
  - **A channel** = Gloss (same as Smoothness)
- Applies Unity Texture Fixture (Wrap Mode=Clamp, Filter Mode=Point)
- Updates GLTF material references to use the packed texture

**Result:** No more gray materials in Unity! Textures import correctly with proper metallic/smoothness values.

### Roblox Export (`-t roblox`)

**Optimized for Roblox's simplified material system!**

```bash
voxbridge convert model.glb -o output/ -t roblox
```

**What it does:**
- Keeps only BaseColor (Albedo) and Normal maps
- Removes metallic/roughness textures (Roblox doesn't use them)
- Sets default material properties (metallic=0.0, roughness=1.0)
- Removes unused texture files to reduce file size

**Result:** Lighter imports with engine-friendly materials optimized for Roblox.

### Standard GLTF Export (`-t gltf`)

**For GLTF viewers and other engines!**

```bash
voxbridge convert model.glb -o output/ -t gltf
```

**What it does:**
- No modifications to materials or textures
- Full GLTF spec compliance
- Works perfectly in GLTF/GLB viewers

**Result:** Standard GLTF export that works everywhere.

## Technical Details

### Unity Texture Packing

Unity's Standard Shader expects a single packed texture for PBR properties:

| Channel | Unity Name | Source (GLTF) | Processing |
|---------|------------|---------------|------------|
| R | Metallic | B channel of metallicRoughness | Direct copy |
| G | Smoothness | G channel of metallicRoughness | Inverted (255 - roughness) |
| B | Occlusion | Separate AO texture | Direct copy or white |
| A | Gloss | Same as Smoothness | Duplicate of G channel |

### Roblox Material Simplification

Roblox's rendering engine only uses:
- **BaseColor (Albedo)**: Main diffuse color/texture
- **Normal Map**: Surface detail (optional)

All other PBR properties (metallic, roughness, occlusion, emissive) are either ignored or have minimal effect.

## Examples

### Before (Gray Materials in Unity)

```bash
# Standard conversion - works in viewers but breaks in Unity
voxbridge convert model.glb -o output/
```

**Result in Unity:** Gray materials because PBR channels aren't properly interpreted.

### After (Fixed Materials)

```bash
# Unity-optimized conversion
voxbridge convert model.glb -o output/ -t unity
```

**Result in Unity:** Perfect materials with correct metallic/smoothness/occlusion values!

## Command Line Reference

```bash
# Unity export with packed textures
voxbridge convert input.glb -o output/ -t unity

# Roblox export with simplified materials
voxbridge convert input.glb -o output/ -t roblox

# Standard GLTF export (no modifications)
voxbridge convert input.glb -o output/ -t gltf
```

## Platform Comparison

| Feature | Unity | Roblox | GLTF |
|---------|-------|--------|------|
| Texture Packing | ✅ Yes (RGBA packed) | ❌ No | ❌ No |
| Material Simplification | ❌ No | ✅ Yes (BaseColor+Normal) | ❌ No |
| Full PBR Support | ✅ Yes (packed) | ⚠️ Limited | ✅ Yes |
| File Size | Medium | Small | Medium |
| Viewer Compatibility | Unity only | Roblox only | Universal |

## Troubleshooting

### Unity Materials Still Gray?

1. Make sure you used `-t unity` flag
2. Check that packed textures were created (look for `*_Unity_Packed.png` files)
3. Verify the GLTF file references the packed texture
4. Import the entire output folder into Unity (not just the GLTF file)

### Roblox Textures Missing?

1. Make sure you used `-t roblox` flag
2. Check that only BaseColor and Normal textures remain
3. Verify unused textures were removed from the output

### GLTF Viewer Issues?

1. Use `-t gltf` for standard GLTF viewers
2. Unity/Roblox optimizations may not display correctly in standard viewers
3. For universal compatibility, export with `-t gltf`

## API Integration

If you're using VoxBridge programmatically:

```python
from voxbridge.platform_profiles import PlatformProfileManager
from pathlib import Path

# Initialize manager
manager = PlatformProfileManager(debug=True)

# Apply Unity texture packing
gltf_path = Path("output/model.gltf")
manager.apply_post_processing(gltf_path, 'unity')

# Apply Roblox simplification
manager.apply_post_processing(gltf_path, 'roblox')
```

## See Also

- [Quick Start Guide](QUICK_START.md)
- [Usage Guide](usage.md)
- [Performance Guide](performance.md)

