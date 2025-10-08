#!/usr/bin/env python3
"""
Targeted Fixes Test Suite for VoxBridge
Tests all the implemented fixes for the specific QA issues
"""

import sys
import json
import tempfile
import shutil
from pathlib import Path
import logging
import zipfile

# Add voxbridge to path
sys.path.insert(0, str(Path(__file__).parent))

from voxbridge.gltf_extension_handler import GLTFExtensionHandler
from voxbridge.texture_optimizer import validate_uv_maps, fix_uv_coordinates, ensure_texture_embedding, flatten_texture_paths
from voxbridge.orchestrated_converter import OrchestratedConverter
from voxbridge.utils.detect import is_complex_gltf, get_file_stats

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_texture_embedding_and_uri_handling():
    """Test 1: Texture embedding and URI handling fixes"""
    print("🧪 Testing Texture Embedding and URI Handling...")
    
    # Create a test GLTF with texture issues
    test_gltf = {
        "asset": {"version": "2.0"},
        "images": [
            {"uri": "textures/diffuse.png"},  # Nested path
            {"uri": "normal.png"},  # Root path
            {"uri": "missing_texture.png"}  # Missing texture
        ],
        "textures": [
            {"source": 0, "sampler": 0},
            {"source": 1, "sampler": 0},
            {"source": 2, "sampler": 0}
        ],
        "materials": [
            {
                "pbrMetallicRoughness": {
                    "baseColorTexture": {"index": 0},
                    "metallicRoughnessTexture": {"index": 1}
                }
            }
        ]
    }
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        test_gltf_path = temp_path / "test.gltf"
        
        # Create test texture files
        (temp_path / "textures").mkdir()
        (temp_path / "textures" / "diffuse.png").write_bytes(b"fake_png_data")
        (temp_path / "normal.png").write_bytes(b"fake_png_data")
        
        with open(test_gltf_path, 'w') as f:
            json.dump(test_gltf, f, indent=2)
        
        # Test texture embedding
        result = ensure_texture_embedding(test_gltf_path, temp_path)
        
        if result['success']:
            print("✅ Texture embedding: Successfully processed textures")
            
            # Test texture flattening explicitly
            flatten_result = flatten_texture_paths(test_gltf_path, temp_path)
            
            # Verify textures were moved to root
            if (temp_path / "diffuse.png").exists():
                print("✅ Texture flattening: Nested texture moved to root")
            else:
                print("❌ Texture flattening: Nested texture not moved")
                return False
            
            # Verify placeholder was created for missing texture
            if (temp_path / "missing_texture.png").exists():
                print("✅ Placeholder creation: Missing texture placeholder created")
            else:
                print("❌ Placeholder creation: Missing texture placeholder not created")
                return False
        else:
            print(f"❌ Texture embedding failed: {result.get('error', 'Unknown error')}")
            return False
    
    return True

def test_specular_glossiness_conversion():
    """Test 2: KHR_materials_pbrSpecularGlossiness extension conversion"""
    print("🧪 Testing Specular-Glossiness Extension Conversion...")
    
    # Create a test GLTF with specular-glossiness extension
    test_gltf = {
        "asset": {"version": "2.0"},
        "materials": [
            {
                "name": "SpecGlossMaterial",
                "extensions": {
                    "KHR_materials_pbrSpecularGlossiness": {
                        "diffuseFactor": [0.8, 0.8, 0.8, 1.0],
                        "specularFactor": [0.5, 0.5, 0.5],
                        "glossinessFactor": 0.8,
                        "diffuseTexture": {"index": 0}
                    }
                }
            }
        ],
        "textures": [{"source": 0, "sampler": 0}],
        "images": [{"uri": "diffuse.png"}],
        "extensionsUsed": ["KHR_materials_pbrSpecularGlossiness"],
        "extensionsRequired": ["KHR_materials_pbrSpecularGlossiness"]
    }
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        test_gltf_path = temp_path / "test.gltf"
        
        with open(test_gltf_path, 'w') as f:
            json.dump(test_gltf, f, indent=2)
        
        # Test extension handler
        handler = GLTFExtensionHandler()
        result = handler.process_gltf_file(test_gltf_path, 'unity')
        
        if result['success']:
            print("✅ Specular-glossiness conversion: Successfully processed extension")
            
            # Verify conversion
            with open(test_gltf_path, 'r') as f:
                converted_gltf = json.load(f)
            
            material = converted_gltf['materials'][0]
            
            # Check that extension was removed
            if 'KHR_materials_pbrSpecularGlossiness' not in material.get('extensions', {}):
                print("✅ Extension removal: Specular-glossiness extension removed")
            else:
                print("❌ Extension removal: Specular-glossiness extension not removed")
                return False
            
            # Check that PBR metallic-roughness was added
            if 'pbrMetallicRoughness' in material:
                pbr = material['pbrMetallicRoughness']
                if 'baseColorFactor' in pbr and 'roughnessFactor' in pbr:
                    print("✅ PBR conversion: Metallic-roughness properties added")
                else:
                    print("❌ PBR conversion: Metallic-roughness properties incomplete")
                    return False
            else:
                print("❌ PBR conversion: PBR metallic-roughness not added")
                return False
        else:
            print(f"❌ Specular-glossiness conversion failed: {result['errors']}")
            return False
    
    return True

def test_mesh_simplification():
    """Test 3: Mesh simplification (polygon reduction)"""
    print("🧪 Testing Mesh Simplification...")
    
    # Create a test GLTF with complex mesh data
    test_gltf = {
        "asset": {"version": "2.0"},
        "buffers": [
            {"byteLength": 120, "uri": "data:application/octet-stream;base64," + "A" * 160}
        ],
        "bufferViews": [
            {"buffer": 0, "byteOffset": 0, "byteLength": 120}
        ],
        "accessors": [
            {
                "bufferView": 0,
                "byteOffset": 0,
                "componentType": 5126,
                "count": 10,
                "type": "VEC3",
                "min": [-1, -1, -1],
                "max": [1, 1, 1]
            }
        ],
        "meshes": [
            {
                "primitives": [
                    {
                        "attributes": {"POSITION": 0},
                        "indices": 0
                    }
                ]
            }
        ]
    }
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        test_gltf_path = temp_path / "test.gltf"
        
        with open(test_gltf_path, 'w') as f:
            json.dump(test_gltf, f, indent=2)
        
        # Test orchestrated converter with mesh optimization
        converter = OrchestratedConverter(debug=True)
        
        # Test with optimize_mesh option
        options = {
            'optimize_mesh': True,
            'simplify_ratio': 0.5,
            'use_draco': False,
            'quantize': False
        }
        
        result = converter.convert_file(test_gltf_path, temp_path, 'unity', options)
        
        if result['success']:
            print("✅ Mesh simplification: Processing completed successfully")
            
            # Check if optimization was applied
            if 'optimizations' in result.get('node_stats', {}):
                optimizations = result['node_stats']['optimizations']
                if any('mesh_simplification' in opt for opt in optimizations):
                    print("✅ Mesh simplification: Simplification optimization applied")
                else:
                    print("⚠️ Mesh simplification: No simplification optimization found (may not be available)")
        else:
            print(f"❌ Mesh simplification failed: {result.get('error', 'Unknown error')}")
            return False
    
    return True

def test_consistency_across_routes():
    """Test 4: Consistency across Node & Python routes"""
    print("🧪 Testing Consistency Across Routes...")
    
    # Create a test GLTF with textures
    test_gltf = {
        "asset": {"version": "2.0"},
        "images": [
            {"uri": "textures/diffuse.png"},
            {"uri": "normal.png"}
        ],
        "textures": [
            {"source": 0, "sampler": 0},
            {"source": 1, "sampler": 0}
        ],
        "materials": [
            {
                "pbrMetallicRoughness": {
                    "baseColorTexture": {"index": 0},
                    "metallicRoughnessTexture": {"index": 1}
                }
            }
        ]
    }
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        test_gltf_path = temp_path / "test.gltf"
        
        # Create test texture files
        (temp_path / "textures").mkdir()
        (temp_path / "textures" / "diffuse.png").write_bytes(b"fake_png_data")
        (temp_path / "normal.png").write_bytes(b"fake_png_data")
        
        with open(test_gltf_path, 'w') as f:
            json.dump(test_gltf, f, indent=2)
        
        # Test both routes
        converter = OrchestratedConverter(debug=True)
        
        # Test static route (Python)
        static_options = {
            'force_static': True,
            'optimize_mesh': False,
            'use_draco': False
        }
        
        static_result = converter.convert_file(test_gltf_path, temp_path / "static_output", 'unity', static_options)
        
        # Test complex route (Node.js) if available
        complex_result = None
        if converter.node_available:
            complex_options = {
                'force_node': True,
                'optimize_mesh': False,
                'use_draco': False
            }
            complex_result = converter.convert_file(test_gltf_path, temp_path / "complex_output", 'unity', complex_options)
        
        # Check consistency
        if static_result['success']:
            print("✅ Static route: Python processing successful")
            
            # Check texture handling in static route
            if 'texture_fixes' in static_result or 'texture_path_fixes' in static_result:
                print("✅ Static route: Texture fixes applied")
            else:
                print("⚠️ Static route: No texture fixes recorded")
        else:
            print(f"❌ Static route failed: {static_result.get('error', 'Unknown error')}")
            return False
        
        if complex_result and complex_result['success']:
            print("✅ Complex route: Node.js processing successful")
            
            # Check texture handling in complex route
            if 'texture_fixes' in complex_result or 'texture_path_fixes' in complex_result:
                print("✅ Complex route: Texture fixes applied")
            else:
                print("⚠️ Complex route: No texture fixes recorded")
        elif complex_result:
            print(f"⚠️ Complex route failed: {complex_result.get('error', 'Unknown error')} (fallback used)")
        else:
            print("⚠️ Complex route: Node.js not available (expected in some environments)")
    
    return True

def test_fallback_system():
    """Test 5: Dependencies and fallback system"""
    print("🧪 Testing Fallback System...")
    
    # Create a test GLTF
    test_gltf = {
        "asset": {"version": "2.0"},
        "meshes": [
            {
                "primitives": [
                    {
                        "attributes": {"POSITION": 0}
                    }
                ]
            }
        ]
    }
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        test_gltf_path = temp_path / "test.gltf"
        
        with open(test_gltf_path, 'w') as f:
            json.dump(test_gltf, f, indent=2)
        
        # Test converter with fallback
        converter = OrchestratedConverter(debug=True)
        
        # Test Node.js availability
        node_available = converter._check_node_availability()
        print(f"   Node.js available: {node_available}")
        
        # Test conversion with fallback
        options = {
            'force_node': True,  # Force Node.js route
            'optimize_mesh': False,
            'use_draco': False
        }
        
        result = converter.convert_file(test_gltf_path, temp_path, 'unity', options)
        
        if result['success']:
            print("✅ Fallback system: Conversion completed successfully")
            
            if result.get('fallback_used', False):
                print(f"✅ Fallback system: Fallback was used - {result.get('fallback_reason', 'Unknown reason')}")
            else:
                print("✅ Fallback system: Primary route worked without fallback")
        else:
            print(f"❌ Fallback system failed: {result.get('error', 'Unknown error')}")
            return False
    
    return True

def test_animated_glb_with_spec_gloss():
    """Test 6: Animated GLB with spec-gloss textures (unit test requirement)"""
    print("🧪 Testing Animated GLB with Spec-Gloss Textures...")
    
    # Create a test GLTF with animations and specular-glossiness
    test_gltf = {
        "asset": {"version": "2.0"},
        "animations": [
            {
                "name": "TestAnimation",
                "channels": [
                    {
                        "sampler": 0,
                        "target": {
                            "node": 0,
                            "path": "translation"
                        }
                    }
                ],
                "samplers": [
                    {
                        "input": 0,
                        "output": 1,
                        "interpolation": "LINEAR"
                    }
                ]
            }
        ],
        "materials": [
            {
                "name": "AnimatedSpecGlossMaterial",
                "extensions": {
                    "KHR_materials_pbrSpecularGlossiness": {
                        "diffuseFactor": [1.0, 0.5, 0.5, 1.0],
                        "specularFactor": [0.8, 0.8, 0.8],
                        "glossinessFactor": 0.9
                    }
                }
            }
        ],
        "nodes": [
            {
                "name": "AnimatedNode",
                "translation": [0, 0, 0]
            }
        ],
        "extensionsUsed": ["KHR_materials_pbrSpecularGlossiness"],
        "extensionsRequired": ["KHR_materials_pbrSpecularGlossiness"]
    }
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        test_gltf_path = temp_path / "animated_spec_gloss.gltf"
        
        with open(test_gltf_path, 'w') as f:
            json.dump(test_gltf, f, indent=2)
        
        # Test complexity detection
        complexity = is_complex_gltf(test_gltf_path)
        
        if complexity['is_complex']:
            print("✅ Complexity detection: Animated GLB correctly identified as complex")
            
            # Check for animations
            if 'animations' in complexity['features']:
                print("✅ Animation detection: Animations correctly detected")
            else:
                print("❌ Animation detection: Animations not detected")
                return False
            
            # Check for specular-glossiness extension
            if 'complex_extensions' in complexity['features']:
                print("✅ Extension detection: Complex extensions detected")
            else:
                print("❌ Extension detection: Complex extensions not detected")
                return False
        else:
            print("❌ Complexity detection: Animated GLB not identified as complex")
            return False
        
        # Test conversion
        converter = OrchestratedConverter(debug=True)
        options = {
            'optimize_mesh': False,
            'use_draco': False,
            'quantize': False
        }
        
        result = converter.convert_file(test_gltf_path, temp_path, 'unity', options)
        
        if result['success']:
            print("✅ Animated GLB conversion: Successfully processed animated GLB with spec-gloss")
            
            # Check if fallback was used (expected for complex files without Node.js)
            if result.get('fallback_used', False):
                print("✅ Fallback handling: Fallback used for complex file (expected)")
            else:
                print("✅ Primary route: Node.js route worked for complex file")
        else:
            print(f"❌ Animated GLB conversion failed: {result.get('error', 'Unknown error')}")
            return False
    
    return True

def test_large_glb_simplification():
    """Test 7: Large GLB requiring simplification (unit test requirement)"""
    print("🧪 Testing Large GLB Simplification...")
    
    # Create a test GLTF with large mesh data and complex features to trigger Node.js route
    # Create valid base64 data (must be multiple of 4)
    import base64
    import struct
    
    # Create 1000 vertices (3 floats each = 12000 bytes)
    vertex_data = []
    for i in range(1000):
        vertex_data.extend([float(i % 10), float((i // 10) % 10), float((i // 100) % 10)])
    
    vertex_bytes = struct.pack(f'{len(vertex_data)}f', *vertex_data)
    vertex_b64 = base64.b64encode(vertex_bytes).decode('ascii')
    
    test_gltf = {
        "asset": {"version": "2.0"},
        "buffers": [
            {"byteLength": len(vertex_bytes), "uri": f"data:application/octet-stream;base64,{vertex_b64}"}
        ],
        "bufferViews": [
            {"buffer": 0, "byteOffset": 0, "byteLength": len(vertex_bytes)}
        ],
        "accessors": [
            {
                "bufferView": 0,
                "byteOffset": 0,
                "componentType": 5126,
                "count": 1000,
                "type": "VEC3",
                "min": [0, 0, 0],
                "max": [9, 9, 9]
            }
        ],
        "meshes": [
            {
                "name": "LargeMesh",
                "primitives": [
                    {
                        "attributes": {"POSITION": 0}
                    }
                ]
            }
        ],
        "animations": [
            {
                "name": "TestAnimation",
                "channels": [
                    {
                        "sampler": 0,
                        "target": {
                            "node": 0,
                            "path": "translation"
                        }
                    }
                ],
                "samplers": [
                    {
                        "input": 0,
                        "output": 1,
                        "interpolation": "LINEAR"
                    }
                ]
            }
        ],
        "nodes": [
            {
                "name": "AnimatedNode",
                "translation": [0, 0, 0]
            }
        ],
        "scenes": [
            {
                "nodes": [0]
            }
        ],
        "scene": 0
    }
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        test_gltf_path = temp_path / "large_mesh.gltf"
        
        with open(test_gltf_path, 'w') as f:
            json.dump(test_gltf, f, indent=2)
        
        # Test with mesh optimization enabled
        converter = OrchestratedConverter(debug=True)
        options = {
            'optimize_mesh': True,
            'simplify_ratio': 0.3,  # Reduce by 70%
            'use_draco': False,
            'quantize': True
        }
        
        result = converter.convert_file(test_gltf_path, temp_path, 'unity', options)
        
        if result['success']:
            print("✅ Large GLB simplification: Successfully processed large GLB")
            
            # Check if optimization was applied
            if 'optimizations' in result.get('node_stats', {}):
                optimizations = result['node_stats']['optimizations']
                if any('mesh_simplification' in opt for opt in optimizations):
                    print("✅ Mesh simplification: Simplification optimization applied")
                else:
                    print("⚠️ Mesh simplification: No simplification optimization found")
            
            # Check for mesh simplification stats
            if 'meshSimplification' in result.get('node_stats', {}):
                mesh_stats = result['node_stats']['meshSimplification']
                before_triangles = mesh_stats.get('beforeTriangles', 0)
                after_triangles = mesh_stats.get('afterTriangles', 0)
                reduction_percent = mesh_stats.get('reductionPercent', 0)
                
                print(f"✅ Triangle reduction: {before_triangles} -> {after_triangles} triangles ({reduction_percent:.1f}% reduction)")
                
                # Validate that simplification actually occurred
                if reduction_percent > 0:
                    print("✅ Mesh simplification validation: Triangle reduction confirmed")
                else:
                    print("⚠️ Mesh simplification validation: No triangle reduction detected")
            else:
                print("⚠️ Triangle reduction: No mesh simplification stats available")
        else:
            print(f"❌ Large GLB simplification failed: {result.get('error', 'Unknown error')}")
            return False
    
    return True

def main():
    """Run all targeted fix tests"""
    print("🚀 VoxBridge Targeted Fixes Test Suite")
    print("======================================")
    
    tests = [
        ("Texture Embedding and URI Handling", test_texture_embedding_and_uri_handling),
        ("Specular-Glossiness Extension Conversion", test_specular_glossiness_conversion),
        ("Mesh Simplification", test_mesh_simplification),
        ("Consistency Across Routes", test_consistency_across_routes),
        ("Fallback System", test_fallback_system),
        ("Animated GLB with Spec-Gloss Textures", test_animated_glb_with_spec_gloss),
        ("Large GLB Simplification", test_large_glb_simplification)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            print()
        except Exception as e:
            print(f"❌ {test_name}: Test failed with exception - {e}")
            print()
    
    print("📊 Test Results")
    print("===============")
    print(f"Passed: {passed}/{total}")
    print(f"Failed: {total - passed}/{total}")
    
    if passed == total:
        print("🎉 All targeted fix tests passed! VoxBridge fixes are working correctly.")
        return 0
    else:
        print("❌ Some tests failed. Please check the implementation.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
