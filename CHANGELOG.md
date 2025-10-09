# Changelog

All notable changes to VoxBridge will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2025-01-10

### 🎉 Major Features

#### Platform-Specific Material Export (Fixes Gray Materials in Unity!)

- **NEW**: Added `-t` (target) flag with three export modes:
  - `unity` - Packs PBR textures into Unity's Standard Shader format
  - `roblox` - Simplifies materials for Roblox (BaseColor + Normal only)
  - `gltf` - Standard GLTF export (no modifications)

- **Unity Texture Packing**: Automatically remaps PBR channels to fix gray materials
  - R channel = Metallic (from GLTF's B channel)
  - G channel = Smoothness (inverted roughness from GLTF's G channel)
  - B channel = Ambient Occlusion
  - A channel = Gloss (same as Smoothness)
  - Creates `*_Unity_Packed.png` textures
  - Updates GLTF material references

- **Roblox Material Simplification**: Optimizes for Roblox's rendering engine
  - Keeps only BaseColor and Normal maps
  - Removes unused PBR textures (metallic, roughness, occlusion)
  - Reduces file size significantly
  - Sets default material properties

### Added

- `pack_unity_pbr_textures()` function in texture_optimizer.py
- `simplify_for_roblox()` function in texture_optimizer.py
- `StandardGLTFProfile` class for standard GLTF exports
- `UnityProfile.pack_textures_for_unity()` method
- `RobloxProfile.simplify_textures_for_roblox()` method
- `PlatformProfileManager.apply_post_processing()` method
- New documentation:
  - `docs/TEXTURE_PACKING_GUIDE.md` - Complete texture packing guide
  - `QUICK_REFERENCE_TEXTURE_PACKING.md` - Quick command reference
  - `TEXTURE_PACKING_IMPLEMENTATION_SUMMARY.md` - Technical details
- Test suite: `test_texture_packing.py`

### Changed

- Updated CLI to accept three targets: `unity`, `roblox`, `gltf`
- Enhanced `PlatformProfileManager` to support all three platforms
- Updated all documentation to reflect new features
- Improved help messages with platform-specific descriptions
- Updated README.md with "What's New" section
- Updated docs/usage.md with platform-specific examples
- Version bumped to 2.0.0

### Documentation

- **README.md**: Added "What's New in Version 2.0" section
- **README.md**: Updated command examples with new `-t` flag
- **README.md**: Added "Static vs Animated Model Handling" section
- **README.md**: Enhanced Node.js requirements section
- **docs/usage.md**: Added platform-specific material export explanations
- **docs/usage.md**: Added performance and Node.js requirements section
- **docs/usage.md**: Updated all examples with new commands
- All documentation now mentions texture packing feature

### Performance

- Platform-specific exports integrate seamlessly with existing pipeline
- No performance impact on standard conversions
- Texture packing happens after GLTF write (post-processing)

### Fixes

- **Gray Materials in Unity**: Completely fixed by packing PBR textures
- Material interpretation issues between GLTF viewers and Unity resolved
- Roblox imports now optimized with only necessary textures

## [1.0.8] - 2024-12-XX

### Previous Features

- Intelligent conversion system with automatic routing
- Static and complex model detection
- Standalone executables for all platforms
- GUI and CLI interfaces
- Mesh optimization
- Texture handling
- Cross-platform support (Windows, macOS, Linux)
- Node.js integration for complex processing
- Draco compression support

---

## Upgrade Guide: 1.0.8 → 2.0.0

### Breaking Changes

**None** - Version 2.0.0 is fully backward compatible!

### What You Need to Know

1. **New `-t` flag**: Defaults to `unity` if not specified
   ```bash
   # Old (still works, defaults to Unity)
   voxbridge convert -i model.glb -o output/
   
   # New (explicit target)
   voxbridge convert -i model.glb -o output/ -t unity
   voxbridge convert -i model.glb -o output/ -t roblox
   voxbridge convert -i model.glb -o output/ -t gltf
   ```

2. **Gray Materials Fixed**: Unity exports now include packed textures
   - Look for `*_Unity_Packed.png` files in output
   - Import entire output folder into Unity
   - Materials will work correctly immediately

3. **Roblox Optimized**: Smaller file sizes with simplified materials
   - Only BaseColor and Normal maps included
   - Metallic/roughness textures removed (not used by Roblox)

4. **Node.js Still Optional**: All new features work without Node.js
   - Texture packing works in Python-only mode
   - Complex models still benefit from Node.js
   - Install Node.js 18+ LTS for optimal performance

### Migration Examples

```bash
# Before (Unity users seeing gray materials)
voxbridge convert -i model.glb -o output/ --target unity

# After (Unity users with perfect materials)
voxbridge convert -i model.glb -o output/ -t unity

# Before (Roblox users with large files)
voxbridge convert -i model.glb -o output/ --target roblox

# After (Roblox users with optimized files)
voxbridge convert -i model.glb -o output/ -t roblox

# New (Standard GLTF for viewers)
voxbridge convert -i model.glb -o output/ -t gltf
```

### New Documentation

- Read `docs/TEXTURE_PACKING_GUIDE.md` for complete details
- Check `QUICK_REFERENCE_TEXTURE_PACKING.md` for quick commands
- See `TEXTURE_PACKING_IMPLEMENTATION_SUMMARY.md` for technical info

---

## Future Plans

- **Unreal Engine target** (`-t unreal`)
- **Godot target** (`-t godot`)
- **Custom texture channel mapping**
- **Material preview before export**
- **Batch processing with mixed targets**

---

**Questions or Issues?** Open an issue on [GitHub](https://github.com/Supercoolkayy/voxbridge/issues)

