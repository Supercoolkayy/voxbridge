# VoxBridge Unity Tools

This folder contains Unity C# scripts to enhance your VoxBridge workflow.

---

## Included Scripts

### 1. UnityLODGenerator.cs
**Creates LOD prefabs for mobile optimization**

**Installation:**
1. Copy this file to your Unity project's `Assets/Editor/` folder
2. Unity will compile it automatically

**Usage:**
1. Import your VoxBridge model into Unity
2. Select the model in Project window  
3. Right-click → **VoxBridge → Generate LOD Prefab**
4. LOD prefab created with 3 levels (LOD0, LOD1, LOD2)

**What it does:**
- Creates LOD Group with 3 quality levels
- LOD0: 100% quality (close to camera)
- LOD1: 70% quality (medium distance)
- LOD2: 40% quality (far from camera)

**For best results:**
- Use VoxBridge to create 3 pre-simplified versions (see LOD_GENERATION_GUIDE.md)
- Or use with Unity Asset Store tools like UnityMeshSimplifier

---

### 2. VoxbridgeImport.cs
**Automatic import configuration for VoxBridge models**

**Installation:**
1. Copy this file to your Unity project's `Assets/Editor/` folder
2. Unity will compile it automatically

**What it does:**
- Detects VoxBridge models during import
- Automatically configures animation settings
- Sets up materials correctly
- Optimizes import settings

**No manual setup needed!** Just import your VoxBridge ZIP and it works.

---

## Documentation

- **LOD Generation Guide**: See `LOD_GENERATION_GUIDE.md` for complete LOD creation instructions
- **Why Triangles Stay Same**: See `WHY_TRIANGLES_STAY_SAME.md` in main folder for explanation of mesh preservation

---

## Support

For issues or questions about these scripts:
- **GitHub Issues**: https://github.com/Supercoolkayy/voxbridge/issues
- **Documentation**: See docs/ folder in release package

---

**VoxBridge v2.0.1** - Professional Unity Integration Tools

