#!/usr/bin/env python3
"""
Simple test script to verify the fixes
"""

import json
import tempfile
from pathlib import Path
from voxbridge.converter import VoxBridgeConverter

def test_texture_path_cleaning():
    """Test texture path cleaning"""
    print("Testing texture path cleaning...")
    
    # Create test data
    test_data = {
        "images": [
            {"uri": "C:\\absolute\\path\\texture.png"},
            {"uri": "/unix/absolute/path/texture2.jpg"},
            {"uri": "relative_texture.png"}
        ]
    }
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.gltf', delete=False) as f:
        json.dump(test_data, f)
        gltf_path = Path(f.name)
    
    try:
        converter = VoxBridgeConverter()
        cleaned_data, changes = converter.clean_gltf_json(gltf_path)
        
        # Check results
        images = cleaned_data['images']
        assert images[0]['uri'] == 'texture.png', f"Expected 'texture.png', got '{images[0]['uri']}'"
        assert images[1]['uri'] == 'texture2.jpg', f"Expected 'texture2.jpg', got '{images[1]['uri']}'"
        assert images[2]['uri'] == 'relative_texture.png', f"Expected 'relative_texture.png', got '{images[2]['uri']}'"
        
        print("✅ Texture path cleaning test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Texture path cleaning test failed: {e}")
        return False
    finally:
        gltf_path.unlink()

def test_material_name_cleaning():
    """Test material name cleaning"""
    print("Testing material name cleaning...")
    
    # Create test data
    test_data = {
        "materials": [
            {"name": "Material #1 (Special!)"},
            {"name": "Another-Bad*Name"},
            {"name": "GoodName"},
            {"name": ""}  # Empty name
        ]
    }
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.gltf', delete=False) as f:
        json.dump(test_data, f)
        gltf_path = Path(f.name)
    
    try:
        converter = VoxBridgeConverter()
        cleaned_data, changes = converter.clean_gltf_json(gltf_path)
        
        # Check results
        materials = cleaned_data['materials']
        assert materials[0]['name'] == 'Material_1_Special', f"Expected 'Material_1_Special', got '{materials[0]['name']}'"
        assert materials[1]['name'] == 'Another_Bad_Name', f"Expected 'Another_Bad_Name', got '{materials[1]['name']}'"
        assert materials[2]['name'] == 'GoodName', f"Expected 'GoodName', got '{materials[2]['name']}'"
        assert materials[3]['name'] == 'Material', f"Expected 'Material', got '{materials[3]['name']}'"
        
        print("✅ Material name cleaning test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Material name cleaning test failed: {e}")
        return False
    finally:
        gltf_path.unlink()

def test_pil_compatibility():
    """Test PIL compatibility"""
    print("Testing PIL compatibility...")
    
    try:
        from PIL import Image
        from voxbridge.texture_optimizer import resize_texture
        
        # Create a test image
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            img = Image.new('RGBA', (100, 100), color=(255, 0, 0, 255))
            img.save(f.name)
            img_path = Path(f.name)
        
        try:
            # Test resize function
            result_path = resize_texture(img_path)
            assert result_path.exists(), "Resized image should exist"
            print("✅ PIL compatibility test passed!")
            return True
            
        finally:
            img_path.unlink()
            
    except Exception as e:
        print(f"❌ PIL compatibility test failed: {e}")
        return False

def main():
    print("🧪 Running fix verification tests...")
    print("=" * 50)
    
    tests = [
        test_texture_path_cleaning,
        test_material_name_cleaning,
        test_pil_compatibility
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The fixes are working.")
    else:
        print("⚠️  Some tests failed. Please check the issues above.")

if __name__ == "__main__":
    main() 