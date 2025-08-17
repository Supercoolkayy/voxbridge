# VoxBridge Optimization Benchmark Guide

## Overview

This guide documents the optimization features implemented in VoxBridge Milestone 2, including performance benchmarks, optimization techniques, and testing procedures.

## 🎯 **Milestone 2 Optimization Features**

### **1. Mesh Optimization**

- **Polygon Reduction**: Automatic face count reduction with configurable reduction factor (default: 30%)
- **Mesh Simplification**: Intelligent vertex merging and edge collapse
- **LOD Generation**: Level-of-detail mesh variants (Milestone 3)

### **2. Texture Optimization**

- **Texture Resizing**: Platform-specific size limits (Roblox: 1024px, Unity: 2048px)
- **Texture Atlas Generation**: Combines multiple textures into single atlas
- **Memory Optimization**: RGBA compression and format optimization

### **3. Material Optimization**

- **Unity Profile**: Full PBR materials with metallicRoughness workflow
- **Roblox Profile**: Simplified to diffuse/baseColor only
- **Extension Management**: Platform-specific extension support

## 📊 **Benchmark System**

### **Metrics Tracked**

- **File Size**: Before/after conversion comparison
- **Triangle Count**: Mesh complexity reduction
- **Texture Memory**: Memory usage optimization
- **Mesh Count**: Geometry consolidation
- **Material Count**: Material optimization
- **Node Count**: Scene hierarchy simplification

### **Benchmark Command**

```bash
# Run optimization benchmarks on test assets
python3 -m voxbridge.cli benchmark \
    --input-dir examples/input \
    --output-dir examples/benchmark_results \
    --target unity \
    --optimize-mesh \
    --verbose
```

### **Output Files**

- `benchmark_report.json`: Detailed JSON report with all metrics
- `{asset}_optimized.zip`: Optimized output for each test asset
- Console summary with improvement percentages

## 🧪 **Test Assets for Benchmarking**

### **Category 1: Avatar Models**

- **Purpose**: Test character model optimization
- **Expected Results**: 20-40% polygon reduction, 15-30% file size improvement
- **Test Files**: `avatar_rigged.glb`, `character_model.glb`

### **Category 2: Prop Models**

- **Purpose**: Test object model optimization
- **Expected Results**: 15-35% polygon reduction, 10-25% file size improvement
- **Test Files**: `furniture.glb`, `vehicle.glb`

### **Category 3: Building Models**

- **Purpose**: Test large scene optimization
- **Expected Results**: 25-45% polygon reduction, 20-35% file size improvement
- **Test Files**: `building.glb`, `environment.glb`

## 🔧 **Optimization Techniques**

### **Mesh Optimization Algorithm**

```python
def optimize_mesh(mesh_data, reduction_factor=0.3):
    """
    Reduces polygon count while preserving visual quality

    Parameters:
    - mesh_data: glTF mesh data
    - reduction_factor: Percentage of faces to remove (0.0-1.0)

    Returns:
    - Optimized mesh data with reduced polygon count
    """
    # 1. Analyze mesh topology
    # 2. Identify redundant vertices
    # 3. Merge similar faces
    # 4. Update indices and attributes
    # 5. Validate mesh integrity
```

### **Texture Atlas Generation**

```python
def generate_texture_atlas(image_paths, atlas_size=1024):
    """
    Combines multiple textures into a single atlas

    Parameters:
    - image_paths: List of texture file paths
    - atlas_size: Atlas dimensions (1024x1024 for Roblox, 2048x2048 for Unity)

    Returns:
    - Atlas image and UV mapping coordinates
    """
    # 1. Calculate optimal grid layout
    # 2. Resize textures to fit grid cells
    # 3. Generate UV coordinate mapping
    # 4. Update glTF material references
```

## 📈 **Performance Benchmarks**

### **Benchmark Results Example**

```json
{
  "benchmark_summary": {
    "total_assets_tested": 3,
    "overall_improvements": {
      "file_size_improvement_pct": {
        "average": 28.5,
        "min": 15.2,
        "max": 42.1
      },
      "total_triangles_improvement_pct": {
        "average": 32.7,
        "min": 18.9,
        "max": 48.3
      }
    }
  },
  "asset_results": {
    "avatar_rigged": {
      "original_stats": {
        "file_size": 2048576,
        "total_triangles": 15432,
        "texture_memory": 1048576
      },
      "optimized_stats": {
        "file_size": 1473920,
        "total_triangles": 10432,
        "texture_memory": 786432
      },
      "improvements": {
        "file_size_improvement_pct": 28.1,
        "total_triangles_improvement_pct": 32.4
      }
    }
  }
}
```

## 🚀 **Running Benchmarks**

### **Step 1: Prepare Test Assets**

```bash
# Create test directory structure
mkdir -p examples/benchmark_assets
mkdir -p examples/benchmark_results

# Copy test GLB files
cp examples/input/*.glb examples/benchmark_assets/
```

### **Step 2: Run Benchmark Suite**

```bash
# Unity optimization benchmark
python3 -m voxbridge.cli benchmark \
    --input-dir examples/benchmark_assets \
    --output-dir examples/benchmark_results \
    --target unity \
    --optimize-mesh \
    --verbose

# Roblox optimization benchmark
python3 -m voxbridge.cli benchmark \
    --input-dir examples/benchmark_assets \
    --output-dir examples/benchmark_results \
    --target roblox \
    --optimize-mesh \
    --verbose
```

### **Step 3: Analyze Results**

```bash
# View benchmark report
cat examples/benchmark_results/benchmark_report.json | python3 -m json.tool

# Check optimized outputs
ls -la examples/benchmark_results/*.zip
```

## 📋 **Benchmark Checklist**

### **Before Running**

- [ ] Test assets are valid GLB files
- [ ] Output directory has write permissions
- [ ] VoxBridge is properly installed
- [ ] Dependencies are available (PIL, numpy)

### **During Benchmark**

- [ ] Monitor console output for errors
- [ ] Verify optimization settings are applied
- [ ] Check intermediate file generation
- [ ] Validate output file integrity

### **After Benchmark**

- [ ] Review benchmark report
- [ ] Verify optimization improvements
- [ ] Test optimized models in target platforms
- [ ] Document any issues or anomalies

## 🔍 **Troubleshooting**

### **Common Issues**

1. **Texture Atlas Generation Fails**

   - Check PIL/Pillow installation
   - Verify image file formats (PNG/JPG)
   - Ensure sufficient memory for large textures

2. **Mesh Optimization Errors**

   - Validate input GLB file integrity
   - Check mesh topology complexity
   - Verify reduction factor is reasonable (0.1-0.5)

3. **Benchmark Data Missing**
   - Enable debug mode for detailed logging
   - Check file permissions and paths
   - Verify benchmark module import

### **Performance Tips**

- Use SSD storage for faster I/O
- Close other applications during large benchmarks
- Monitor system memory usage
- Run benchmarks during low system load

## 📚 **References**

- **glTF 2.0 Specification**: https://www.khronos.org/gltf/
- **Unity GLTF Importer**: https://github.com/KhronosGroup/UnityGLTF
- **Roblox Model Guidelines**: https://developer.roblox.com/en-us/articles/3D-Modeling-Guidelines
- **Texture Atlas Best Practices**: https://docs.unity3d.com/Manual/TextureAtlas.html

## 🎉 **Success Criteria**

### **Milestone 2 Completion**

- [ ] All optimization features implemented and tested
- [ ] Benchmark system generates accurate metrics
- [ ] 3 test assets processed successfully
- [ ] Performance improvements documented
- [ ] Unity and Roblox compatibility verified

### **Performance Targets**

- **File Size**: 15-40% reduction
- **Triangle Count**: 20-50% reduction
- **Texture Memory**: 10-30% reduction
- **Conversion Time**: <60 seconds per asset
- **Output Quality**: Visual quality maintained

---

_This benchmark guide is part of VoxBridge Milestone 2 documentation. For questions or issues, please refer to the main README or create an issue on GitHub._
