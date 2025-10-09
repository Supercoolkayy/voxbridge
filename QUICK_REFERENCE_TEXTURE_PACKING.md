# Quick Reference: Texture Packing Feature

## The Fix for Gray Materials in Unity! 🎯

### Problem
Your models look perfect in GLTF viewers but show **gray/broken materials** in Unity because Unity interprets PBR textures differently.

### Solution
Use VoxBridge's new **platform-specific export** with the `-t` flag!

---

## Three Commands You Need

### 1. Unity Export (Fixes Gray Materials!)
```bash
voxbridge convert model.glb -o output/ -t unity
```
**What it does:** Packs PBR textures into Unity's Standard Shader format (R=Metallic, G=Smoothness, B=AO, A=Gloss)

**Result:** ✅ Perfect materials in Unity - no more gray!

---

### 2. Roblox Export (Optimized!)
```bash
voxbridge convert model.glb -o output/ -t roblox
```
**What it does:** Keeps only BaseColor + Normal maps, removes unused textures

**Result:** ✅ Lighter, faster imports for Roblox

---

### 3. Standard GLTF Export
```bash
voxbridge convert model.glb -o output/ -t gltf
```
**What it does:** No modifications, full GLTF compliance

**Result:** ✅ Works in all GLTF/GLB viewers

---

## How It Works

### Unity Texture Packing

**Before:**
- ❌ Separate textures: BaseColor, Metallic/Roughness, AO, Normal
- ❌ Unity can't interpret them correctly
- ❌ Result: Gray materials

**After:**
- ✅ Packed RGBA texture: R=Metallic, G=Smoothness, B=AO, A=Gloss
- ✅ Unity reads it perfectly
- ✅ Result: Correct materials!

### Roblox Simplification

**Before:**
- ❌ All PBR textures included (metallic, roughness, AO, etc.)
- ❌ Roblox doesn't use most of them
- ❌ Larger file size

**After:**
- ✅ Only BaseColor + Normal maps
- ✅ Optimized for Roblox's rendering
- ✅ Smaller file size

---

## Complete Example

```bash
# Convert a model for Unity (with texture packing)
voxbridge convert character.glb -o unity_output/ -t unity

# Convert the same model for Roblox (simplified)
voxbridge convert character.glb -o roblox_output/ -t roblox

# Convert for standard GLTF viewers
voxbridge convert character.glb -o gltf_output/ -t gltf
```

---

## With Other Flags

All existing VoxBridge features still work:

```bash
# Unity export with mesh optimization and Draco compression
voxbridge convert model.glb -o output/ -t unity --optimize-mesh --use-draco

# Roblox export in fast mode
voxbridge convert model.glb -o output/ -t roblox --fast

# GLTF export with full quality
voxbridge convert model.glb -o output/ -t gltf --full
```

---

## Output Files

### Unity Export
```
output/
├── model.gltf                           # Modified GLTF with packed texture references
├── model.bin                            # Geometry data
├── model_BaseColor.png                  # Original base color texture
├── model_Normal.png                     # Original normal map
├── model_material0_Unity_Packed.png     # ⭐ NEW: Packed RGBA texture for Unity
└── voxbridge_report.json               # Conversion report
```

### Roblox Export
```
output/
├── model.gltf                  # Simplified GLTF (BaseColor + Normal only)
├── model.bin                   # Geometry data
├── model_BaseColor.png         # Base color texture
├── model_Normal.png            # Normal map (if exists)
└── voxbridge_report.json      # Conversion report
```

---

## Troubleshooting

### Unity Materials Still Gray?
1. ✅ Make sure you used `-t unity` flag
2. ✅ Check for `*_Unity_Packed.png` files in output
3. ✅ Import the entire output folder into Unity
4. ✅ Assign materials to your mesh if needed

### Roblox Textures Missing?
1. ✅ Make sure you used `-t roblox` flag
2. ✅ Only BaseColor and Normal should remain (this is correct!)
3. ✅ Metallic/roughness textures are intentionally removed

### GLTF Viewer Issues?
1. ✅ Use `-t gltf` for standard viewers
2. ✅ Unity/Roblox optimizations may not display correctly in viewers
3. ✅ For universal compatibility, always export with `-t gltf`

---

## Default Behavior

If you don't specify `-t`, VoxBridge defaults to **Unity** export:

```bash
voxbridge convert model.glb -o output/
# Same as: voxbridge convert model.glb -o output/ -t unity
```

---

## Documentation

For more details, see:
- `docs/TEXTURE_PACKING_GUIDE.md` - Complete guide
- `TEXTURE_PACKING_IMPLEMENTATION_SUMMARY.md` - Technical details
- `docs/usage.md` - General usage guide

---

## Summary

🎯 **Unity users**: Use `-t unity` to fix gray materials
🎯 **Roblox users**: Use `-t roblox` for optimized imports
🎯 **GLTF users**: Use `-t gltf` for standard compliance

**That's it! Your material exports are now correctly adjusted for each platform!** ✅

