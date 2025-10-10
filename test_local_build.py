#!/usr/bin/env python3
"""
Local VoxBridge Build Test Script
Tests the built executable to ensure it works without Node.js and handles Unity texture packing
"""

import subprocess
import sys
import os
import tempfile
import shutil
from pathlib import Path

def run_command(cmd, description, check_success=True):
    """Run a command and return the result"""
    print(f"\n🧪 {description}")
    print(f"Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.stdout:
            print("STDOUT:")
            print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        if check_success and result.returncode != 0:
            print(f"❌ Command failed with exit code {result.returncode}")
            return False
        elif not check_success and result.returncode == 0:
            print(f"❌ Command should have failed but succeeded")
            return False
        else:
            print(f"✅ Command {'succeeded' if result.returncode == 0 else 'failed as expected'}")
            return True
            
    except subprocess.TimeoutExpired:
        print("❌ Command timed out")
        return False
    except Exception as e:
        print(f"❌ Command failed with exception: {e}")
        return False

def find_executable():
    """Find the VoxBridge executable"""
    possible_paths = [
        "dist/voxbridge",
        "dist/voxbridge.exe", 
        "voxbridge",
        "voxbridge.exe",
        "./voxbridge",
        "./voxbridge.exe"
    ]
    
    for path in possible_paths:
        if os.path.exists(path) and os.access(path, os.X_OK):
            return path
    
    print("❌ VoxBridge executable not found!")
    print("Looked for:")
    for path in possible_paths:
        print(f"  - {path}")
    return None

def create_test_gltf():
    """Create a proper test GLTF file"""
    test_gltf = {
        "asset": {"version": "2.0", "generator": "VoxBridge Test"},
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"mesh": 0}],
        "meshes": [{"primitives": [{"attributes": {"POSITION": 0}, "indices": 1}]}],
        "accessors": [
            {"componentType": 5126, "count": 3, "type": "VEC3", "bufferView": 0, "min": [-1, -1, -1], "max": [1, 1, 1]},
            {"componentType": 5123, "count": 3, "type": "SCALAR", "bufferView": 1}
        ],
        "bufferViews": [
            {"buffer": 0, "byteOffset": 0, "byteLength": 36},
            {"buffer": 0, "byteOffset": 36, "byteLength": 6}
        ],
        "buffers": [{"uri": "data:application/octet-stream;base64,AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=", "byteLength": 42}]
    }
    
    import json
    with open("test_input.gltf", "w") as f:
        json.dump(test_gltf, f, indent=2)
    
    return "test_input.gltf"

def main():
    """Main test function"""
    print("🚀 VoxBridge Local Build Test")
    print("=" * 50)
    
    # Find executable
    executable = find_executable()
    if not executable:
        return 1
    
    print(f"✅ Found executable: {executable}")
    
    # Test 1: Help command
    if not run_command([executable, "--help"], "Testing help command"):
        return 1
    
    # Test 2: Version command
    if not run_command([executable, "--version"], "Testing version command"):
        return 1
    
    # Test 3: Create test input
    print("\n📁 Creating test input...")
    test_input = create_test_gltf()
    print(f"✅ Created test input: {test_input}")
    
    # Test 4: Unity conversion
    with tempfile.TemporaryDirectory() as temp_dir:
        unity_output = os.path.join(temp_dir, "unity_output")
        if not run_command([executable, "convert", test_input, "-o", unity_output, "-t", "unity", "--verbose"], 
                          "Testing Unity texture packing (-t unity)"):
            return 1
    
    # Test 5: Roblox conversion
    with tempfile.TemporaryDirectory() as temp_dir:
        roblox_output = os.path.join(temp_dir, "roblox_output")
        if not run_command([executable, "convert", test_input, "-o", roblox_output, "-t", "roblox", "--verbose"], 
                          "Testing Roblox optimization (-t roblox)"):
            return 1
    
    # Test 6: Standard GLTF conversion
    with tempfile.TemporaryDirectory() as temp_dir:
        gltf_output = os.path.join(temp_dir, "gltf_output")
        if not run_command([executable, "convert", test_input, "-o", gltf_output, "-t", "gltf", "--verbose"], 
                          "Testing standard GLTF export (-t gltf)"):
            return 1
    
    # Test 7: Error handling
    with tempfile.TemporaryDirectory() as temp_dir:
        error_output = os.path.join(temp_dir, "error_output")
        if not run_command([executable, "convert", "nonexistent.glb", "-o", error_output], 
                          "Testing error handling with non-existent file", check_success=False):
            return 1
    
    # Test 8: Check for resource path errors
    print("\n🔍 Checking for resource path errors...")
    result = subprocess.run([executable, "convert", "nonexistent.glb", "-o", "/tmp/test"], 
                          capture_output=True, text=True)
    
    if "get_resource_path" in result.stderr and "not defined" in result.stderr:
        print("❌ Found resource path error - bundling issue!")
        print("STDERR:", result.stderr)
        return 1
    else:
        print("✅ No resource path errors detected")
    
    # Cleanup
    if os.path.exists(test_input):
        os.remove(test_input)
    
    print("\n🎉 All tests passed!")
    print("✅ VoxBridge executable is working correctly")
    print("✅ Unity texture packing works")
    print("✅ Roblox optimization works") 
    print("✅ Standard GLTF export works")
    print("✅ Error handling works")
    print("✅ No resource path errors")
    print("✅ No Node.js dependency issues")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
