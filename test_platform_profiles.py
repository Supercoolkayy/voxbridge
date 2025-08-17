#!/usr/bin/env python3
"""
Test script for VoxBridge Platform Profiles
Tests Unity and Roblox export profiles
"""

import sys
from pathlib import Path

# Add the voxbridge package to the path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from voxbridge.platform_profiles import PlatformProfileManager, UnityProfile, RobloxProfile
    print("✅ Platform profiles imported successfully")
except ImportError as e:
    print(f"❌ Failed to import platform profiles: {e}")
    sys.exit(1)

def test_unity_profile():
    """Test Unity profile optimizations"""
    print("\n🧪 Testing Unity Profile...")
    
    # Sample glTF data
    sample_gltf = {
        "asset": {"version": "2.0"},
        "scene": 0,
        "materials": [
            {
                "name": "TestMaterial",
                "pbrMetallicRoughness": {
                    "baseColorFactor": [1.0, 0.0, 0.0, 1.0],
                    "metallicFactor": 0.5,
                    "roughnessFactor": 0.3
                }
            }
        ],
        "images": [
            {"uri": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="}
        ],
        "extensionsUsed": ["KHR_materials_pbrSpecularGlossiness", "UNSUPPORTED_EXTENSION"]
    }
    
    profile = UnityProfile(debug=True)
    optimized = profile.optimize_gltf(sample_gltf, Path("test_output"))
    
    # Check optimizations
    assert "materials" in optimized
    assert "pbrMetallicRoughness" in optimized["materials"][0]
    assert "extensionsUsed" in optimized
    assert "UNSUPPORTED_EXTENSION" not in optimized["extensionsUsed"]
    
    print("✅ Unity profile optimizations passed")

def test_roblox_profile():
    """Test Roblox profile optimizations"""
    print("\n🧪 Testing Roblox Profile...")
    
    # Sample glTF data
    sample_gltf = {
        "asset": {"version": "2.0"},
        "scene": 0,
        "materials": [
            {
                "name": "TestMaterial",
                "pbrMetallicRoughness": {
                    "baseColorFactor": [1.0, 0.0, 0.0, 1.0],
                    "metallicFactor": 0.5,
                    "roughnessFactor": 0.3
                },
                "extensions": {"some_extension": {}}
            }
        ],
        "images": [
            {"uri": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="}
        ],
        "nodes": [
            {"name": "VeryLongNodeNameThatExceedsRobloxLimitsAndShouldBeTruncated"}
        ]
    }
    
    profile = RobloxProfile(debug=True)
    optimized = profile.optimize_gltf(sample_gltf, Path("test_output"))
    
    # Check optimizations
    assert "materials" in optimized
    material = optimized["materials"][0]
    assert "pbrMetallicRoughness" in material
    assert "metallicFactor" not in material["pbrMetallicRoughness"]  # Should be removed
    assert "extensions" not in material  # Should be removed
    assert "extensionsUsed" in optimized
    assert len(optimized["extensionsUsed"]) == 0  # Should be empty
    
    # Check node name truncation
    assert len(optimized["nodes"][0]["name"]) <= 32
    
    print("✅ Roblox profile optimizations passed")

def test_profile_manager():
    """Test profile manager functionality"""
    print("\n🧪 Testing Profile Manager...")
    
    manager = PlatformProfileManager(debug=True)
    
    # Test profile selection
    unity_profile = manager.get_profile("unity")
    roblox_profile = manager.get_profile("roblox")
    default_profile = manager.get_profile("unknown")
    
    assert unity_profile.profile_name == "unity"
    assert roblox_profile.profile_name == "roblox"
    assert default_profile.profile_name == "unity"  # Should default to Unity
    
    print("✅ Profile manager tests passed")

def main():
    """Run all tests"""
    print("🚀 VoxBridge Platform Profiles Test Suite")
    print("=" * 50)
    
    try:
        test_unity_profile()
        test_roblox_profile()
        test_profile_manager()
        
        print("\n🎉 All tests passed!")
        print("Platform profiles are working correctly.")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
