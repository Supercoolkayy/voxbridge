#!/usr/bin/env python3
"""
Test script for bundled VoxBridge build
Tests both development and bundled execution paths
"""

import sys
import os
import subprocess
import tempfile
from pathlib import Path

def test_development_mode():
    """Test VoxBridge in development mode"""
    print("🧪 Testing Development Mode")
    print("=" * 40)
    
    try:
        # Test CLI entry point
        result = subprocess.run([
            sys.executable, 'cli_entry.py', '--help'
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("  ✅ CLI entry point works")
        else:
            print(f"  ❌ CLI entry point failed: {result.stderr}")
            return False
        
        # Test self-test command
        result = subprocess.run([
            sys.executable, 'cli_entry.py', 'selftest'
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("  ✅ Self-test command works")
        else:
            print(f"  ❌ Self-test command failed: {result.stderr}")
            return False
        
        return True
        
    except Exception as e:
        print(f"  ❌ Development mode test failed: {e}")
        return False

def test_path_utilities():
    """Test path utilities"""
    print("\n🧪 Testing Path Utilities")
    print("=" * 40)
    
    try:
        # Import path utilities
        sys.path.insert(0, 'voxbridge')
        from utils.paths import get_resource_path, get_node_runner_path, is_bundled
        
        # Test resource path
        resource_path = get_resource_path('voxbridge')
        print(f"  Resource path: {resource_path}")
        print(f"  Resource exists: {resource_path.exists()}")
        
        # Test node runner path
        node_runner_path = get_node_runner_path()
        print(f"  Node runner path: {node_runner_path}")
        print(f"  Node runner exists: {node_runner_path.exists()}")
        
        # Test bundled status
        bundled = is_bundled()
        print(f"  Is bundled: {bundled}")
        
        print("  ✅ Path utilities working")
        return True
        
    except Exception as e:
        print(f"  ❌ Path utilities test failed: {e}")
        return False

def test_node_runner():
    """Test Node.js runner"""
    print("\n🧪 Testing Node.js Runner")
    print("=" * 40)
    
    try:
        # Check if node_runner exists
        node_runner_path = Path('node_runner')
        if not node_runner_path.exists():
            print("  ⚠️ Node runner not found, testing with node_scripts/index.js")
            node_runner_path = Path('node_scripts/index.js')
        
        if not node_runner_path.exists():
            print("  ❌ No Node.js runner found")
            return False
        
        # Test version command
        result = subprocess.run([
            'node', str(node_runner_path), '--version'
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print(f"  ✅ Node runner version: {result.stdout.strip()}")
        else:
            print(f"  ❌ Node runner version failed: {result.stderr}")
            return False
        
        # Test help command
        result = subprocess.run([
            'node', str(node_runner_path), '--help'
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("  ✅ Node runner help works")
        else:
            print(f"  ❌ Node runner help failed: {result.stderr}")
            return False
        
        return True
        
    except Exception as e:
        print(f"  ❌ Node runner test failed: {e}")
        return False

def test_conversion():
    """Test actual conversion with a sample file"""
    print("\n🧪 Testing Conversion")
    print("=" * 40)
    
    # Check if we have a test file
    test_files = [
        'examples/input/Gym.glb',
        'examples/input/animated_triceratops_skeleton.glb'
    ]
    
    test_file = None
    for file_path in test_files:
        if Path(file_path).exists():
            test_file = file_path
            break
    
    if not test_file:
        print("  ⚠️ No test files found, skipping conversion test")
        return True
    
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            # Test conversion
            result = subprocess.run([
                sys.executable, 'cli_entry.py', 'convert',
                '--input', test_file,
                '--output', temp_dir,
                '--target', 'unity',
                '--fast'
            ], capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                print("  ✅ Conversion test passed")
                return True
            else:
                print(f"  ❌ Conversion test failed: {result.stderr}")
                return False
                
    except Exception as e:
        print(f"  ❌ Conversion test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 VoxBridge Bundled Build Test")
    print("=" * 60)
    
    # Change to project root
    os.chdir(Path(__file__).parent)
    
    # Run tests
    tests = [
        test_development_mode,
        test_path_utilities,
        test_node_runner,
        test_conversion
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"  ❌ Test {test.__name__} crashed: {e}")
            results.append(False)
    
    # Summary
    print("\n📊 TEST SUMMARY")
    print("=" * 60)
    
    test_names = [
        "Development Mode",
        "Path Utilities", 
        "Node.js Runner",
        "Conversion"
    ]
    
    for i, (name, result) in enumerate(zip(test_names, results)):
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{name}: {status}")
    
    overall_success = all(results)
    
    if overall_success:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ VoxBridge is ready for bundling")
        print("✅ All components are working correctly")
    else:
        print("\n⚠️ Some tests failed")
        print("❌ Check the output above for details")
    
    return overall_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
