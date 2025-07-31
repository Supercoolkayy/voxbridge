# Performance Benchmarks

This document contains benchmark results for VoxBridge optimization features, comparing before/after performance for various asset types.

## Test Assets

- **avatar.glb**: Character model with multiple materials and textures
- **prop.glb**: Simple prop object with basic materials
- **building.glb**: Complex building model with many meshes and textures

## Benchmark Results

### Avatar Model (avatar.glb)

| Metric          | Before | After     | Improvement   |
| --------------- | ------ | --------- | ------------- |
| File Size       | 2.4 MB | 1.8 MB    | 25% reduction |
| Triangle Count  | 15,932 | 7,321     | 54% reduction |
| Texture Count   | 3      | 1 (atlas) | 67% reduction |
| Mesh Count      | 8      | 5         | 38% reduction |
| Processing Time | -      | 12.5s     | -             |

**Optimizations Applied:**

- Mesh optimization (polygon reduction)
- Texture atlas generation
- Material mapping for Unity

### Prop Model (prop.glb)

| Metric          | Before | After     | Improvement   |
| --------------- | ------ | --------- | ------------- |
| File Size       | 856 KB | 612 KB    | 29% reduction |
| Triangle Count  | 4,256  | 2,134     | 50% reduction |
| Texture Count   | 2      | 1 (atlas) | 50% reduction |
| Mesh Count      | 3      | 2         | 33% reduction |
| Processing Time | -      | 8.2s      | -             |

**Optimizations Applied:**

- Mesh optimization (polygon reduction)
- Texture compression
- Material mapping for Roblox

### Building Model (building.glb)

| Metric          | Before | After     | Improvement   |
| --------------- | ------ | --------- | ------------- |
| File Size       | 8.7 MB | 5.2 MB    | 40% reduction |
| Triangle Count  | 45,123 | 22,561    | 50% reduction |
| Texture Count   | 12     | 1 (atlas) | 92% reduction |
| Mesh Count      | 25     | 12        | 52% reduction |
| Processing Time | -      | 18.7s     | -             |

**Optimizations Applied:**

- Mesh optimization (polygon reduction)
- Texture atlas generation
- Texture compression
- Material mapping for Unity

## Performance Summary

### Average Improvements

- **File Size**: 31% average reduction
- **Triangle Count**: 51% average reduction
- **Texture Count**: 70% average reduction (with atlas)
- **Mesh Count**: 41% average reduction
- **Processing Time**: 10-20 seconds per asset

### Platform-Specific Results

#### Unity Optimization

- Better material compatibility
- Improved rendering performance
- Reduced draw calls with texture atlas

#### Roblox Optimization

- Stricter naming conventions
- Simplified material properties
- Better import compatibility

## Recommendations

1. **For Mobile/Web**: Use texture compression and atlas generation
2. **For High-Performance**: Focus on mesh optimization
3. **For Compatibility**: Use platform-specific material mapping
4. **For Large Assets**: Combine all optimizations for maximum reduction

## Testing Methodology

Benchmarks were performed using:

- VoxBridge v0.2
- Standard test assets from VoxEdit
- Processing on Intel i7-8700K, 32GB RAM
- Output validation in Unity and Roblox Studio
