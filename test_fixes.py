#!/usr/bin/env python3
"""
Test script to validate VoxBridge fixes
Tests all the implemented fixes for the QA issues
"""

import sys
import json
import tempfile
import shutil
from pathlib import Path
import logging

# Add voxbridge to path
sys.path.insert(0, str(Path(__file__).parent))

from voxbridge.gltf_extension_handler import GLTFExtensionHandler
from voxbridge.texture_optimizer import validate_uv_maps, fix_uv_coordinates
from voxbridge.error_handler import VoxBridgeErrorHandler
from voxbridge.cross_platform import CrossPlatformManager
from voxbridge.orchestrated_converter import OrchestratedConverter

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_gltf_extension_handler():
    """Test GLTF extension handler"""
    print("🧪 Testing GLTF Extension Handler...")
    
    handler = GLTFExtensionHandler()
    
    # Create a test GLTF with missing extensions
    test_gltf = {
        "asset": {"version": "2.0"},
        "materials": [
            {
                "extensions": {
                    "KHR_materials_pbrSpecularGlossiness": {
                        "diffuseFactor": [1.0, 1.0, 1.0, 1.0],
                        "specularFactor": [0.5, 0.5, 0.5],
                        "glossinessFactor": 0.8
                    }
                }
            }
        ],
        "extensionsUsed": ["KHR_materials_pbrSpecularGlossiness"],
        "extensionsRequired": ["KHR_materials_pbrSpecularGlossiness"]
    }
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        test_gltf_path = temp_path / "test.gltf"
        
        with open(test_gltf_path, 'w') as f:
            json.dump(test_gltf, f, indent=2)
        
        # Test extension processing
        result = handler.process_gltf_file(test_gltf_path, 'unity')
        
        if result['success']:
            print("✅ GLTF Extension Handler: Successfully processed extensions")
            if result['fallbacks_applied']:
                print(f"   Applied fallbacks: {result['fallbacks_applied']}")
        else:
            print(f"❌ GLTF Extension Handler: Failed - {result['errors']}")
            return False
    
    return True

def test_texture_optimizer():
    """Test texture optimizer with UV validation"""
    print("🧪 Testing Texture Optimizer...")
    
    # Create a test GLTF with UV data
    test_gltf = {
        "asset": {"version": "2.0"},
        "buffers": [
            {"byteLength": 24, "uri": "data:application/octet-stream;base64,AAAAAAAAAAAAAAAAAAAAAAAA"}
        ],
        "bufferViews": [
            {"buffer": 0, "byteOffset": 0, "byteLength": 24}
        ],
        "accessors": [
            {
                "bufferView": 0,
                "byteOffset": 0,
                "componentType": 5126,
                "count": 4,
                "type": "VEC2",
                "min": [0.0, 0.0],
                "max": [1.0, 1.0]
            }
        ],
        "meshes": [
            {
                "primitives": [
                    {
                        "attributes": {
                            "POSITION": 0,
                            "TEXCOORD_0": 0
                        }
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
        
        # Test UV validation
        uv_result = validate_uv_maps(test_gltf_path)
        
        if uv_result['valid']:
            print("✅ Texture Optimizer: UV validation successful")
            print(f"   UV stats: {uv_result['uv_stats']}")
        else:
            print(f"❌ Texture Optimizer: UV validation failed - {uv_result['errors']}")
            return False
        
        # Test UV fixing
        fix_result = fix_uv_coordinates(test_gltf_path)
        
        if fix_result['success']:
            print("✅ Texture Optimizer: UV fixing successful")
            print(f"   Fixed {fix_result['fixed_count']} UV coordinate sets")
        else:
            print(f"❌ Texture Optimizer: UV fixing failed - {fix_result['error']}")
            return False
    
    return True

def test_error_handler():
    """Test error handler"""
    print("🧪 Testing Error Handler...")
    
    handler = VoxBridgeErrorHandler()
    
    # Test error logging
    error_entry = handler.log_error(
        'TEST_ERROR',
        'Test error message',
        {'test_context': 'test_value'},
        fallback_attempted=True,
        fallback_success=True
    )
    
    if error_entry and error_entry['error_type'] == 'TEST_ERROR':
        print("✅ Error Handler: Error logging successful")
    else:
        print("❌ Error Handler: Error logging failed")
        return False
    
    # Test fallback attempt
    def test_fallback():
        return {'success': True, 'message': 'Test fallback successful'}
    
    fallback_result = handler.attempt_fallback(
        'TEST_FALLBACK',
        'Test fallback error',
        test_fallback
    )
    
    if fallback_result['success']:
        print("✅ Error Handler: Fallback mechanism successful")
    else:
        print(f"❌ Error Handler: Fallback mechanism failed - {fallback_result['error']}")
        return False
    
    # Test error report generation
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        report = handler.generate_error_report(temp_path)
        
        if report and 'error_summary' in report:
            print("✅ Error Handler: Error report generation successful")
            print(f"   Total errors: {report['error_summary']['total_errors']}")
            print(f"   Total fallbacks: {report['error_summary']['total_fallbacks']}")
        else:
            print("❌ Error Handler: Error report generation failed")
            return False
    
    return True

def test_cross_platform_manager():
    """Test cross-platform manager"""
    print("🧪 Testing Cross-Platform Manager...")
    
    manager = CrossPlatformManager()
    
    # Test path normalization
    test_path = "C:\\Users\\Test\\model.gltf"
    normalized = manager.normalize_paths(test_path)
    
    if normalized == "C:/Users/Test/model.gltf":
        print("✅ Cross-Platform Manager: Path normalization successful")
    else:
        print(f"❌ Cross-Platform Manager: Path normalization failed - {normalized}")
        return False
    
    # Test GLTF path normalization
    test_gltf = {
        "images": [
            {"uri": "textures\\diffuse.png"},
            {"uri": "textures\\normal.png"}
        ],
        "buffers": [
            {"uri": "data\\model.bin"}
        ]
    }
    
    normalized_gltf = manager.normalize_gltf_paths(test_gltf)
    
    if (normalized_gltf['images'][0]['uri'] == "textures/diffuse.png" and
        normalized_gltf['images'][1]['uri'] == "textures/normal.png" and
        normalized_gltf['buffers'][0]['uri'] == "data/model.bin"):
        print("✅ Cross-Platform Manager: GLTF path normalization successful")
    else:
        print("❌ Cross-Platform Manager: GLTF path normalization failed")
        return False
    
    # Test consistency validation
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        test_gltf_path = temp_path / "test.gltf"
        
        with open(test_gltf_path, 'w') as f:
            json.dump(normalized_gltf, f, indent=2)
        
        consistency_result = manager.validate_cross_platform_consistency(test_gltf_path)
        
        if consistency_result['consistent']:
            print("✅ Cross-Platform Manager: Consistency validation successful")
        else:
            print(f"❌ Cross-Platform Manager: Consistency validation found issues: {consistency_result['issues']}")
        
        # Test consistency fixes
        fix_result = manager.fix_cross_platform_issues(test_gltf_path)
        
        if fix_result['success']:
            print("✅ Cross-Platform Manager: Consistency fixes successful")
            print(f"   Fixes applied: {fix_result['fixes_applied']}")
        else:
            print(f"❌ Cross-Platform Manager: Consistency fixes failed - {fix_result['errors']}")
            return False
    
    return True

def test_orchestrated_converter():
    """Test orchestrated converter with all fixes integrated"""
    print("🧪 Testing Orchestrated Converter...")
    
    converter = OrchestratedConverter(debug=True)
    
    # Test that all components are initialized
    if (converter.extension_handler and 
        converter.error_handler and 
        converter.cross_platform_manager):
        print("✅ Orchestrated Converter: All components initialized successfully")
    else:
        print("❌ Orchestrated Converter: Component initialization failed")
        return False
    
    # Test Node.js availability check
    node_available = converter._check_node_availability()
    print(f"   Node.js available: {node_available}")
    
    print("✅ Orchestrated Converter: Basic functionality test successful")
    return True

def main():
    """Run all tests"""
    print("🚀 VoxBridge Fixes Test Suite")
    print("=============================")
    
    tests = [
        ("GLTF Extension Handler", test_gltf_extension_handler),
        ("Texture Optimizer", test_texture_optimizer),
        ("Error Handler", test_error_handler),
        ("Cross-Platform Manager", test_cross_platform_manager),
        ("Orchestrated Converter", test_orchestrated_converter)
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
        print("🎉 All tests passed! VoxBridge fixes are working correctly.")
        return 0
    else:
        print("❌ Some tests failed. Please check the implementation.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
