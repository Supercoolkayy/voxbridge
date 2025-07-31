#!/usr/bin/env python3
"""
Test script for VoxBridge CLI functionality
"""

import sys
import subprocess
from pathlib import Path

def test_cli_help():
    """Test CLI help command"""
    print("Testing CLI help...")
    try:
        result = subprocess.run([sys.executable, "-m", "voxbridge.cli", "--help"], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("CLI help works")
            return True
        else:
            print(f"CLI help failed: {result.stderr}")
            return False
    except Exception as e:
                    print(f"CLI help error: {e}")
        return False

def test_cli_doctor():
    """Test CLI doctor command"""
    print("Testing CLI doctor...")
    try:
        result = subprocess.run([sys.executable, "-m", "voxbridge.cli", "doctor"], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("CLI doctor works")
            return True
        else:
            print(f"CLI doctor failed: {result.stderr}")
            return False
    except Exception as e:
                    print(f"CLI doctor error: {e}")
        return False

def test_cli_convert_help():
    """Test CLI convert help"""
    print("Testing CLI convert help...")
    try:
        result = subprocess.run([sys.executable, "-m", "voxbridge.cli", "convert", "--help"], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("CLI convert help works")
            return True
        else:
            print(f"❌ CLI convert help failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ CLI convert help error: {e}")
        return False

def test_cli_convert_args():
    """Test CLI convert with arguments (should fail gracefully)"""
    print("Testing CLI convert with invalid arguments...")
    try:
        result = subprocess.run([sys.executable, "-m", "voxbridge.cli", "convert", "--input", "nonexistent.glb", "--target", "unity"], 
                              capture_output=True, text=True, timeout=10)
        # Should fail gracefully with error code 1
        if result.returncode == 1:
            print("✅ CLI convert handles invalid input gracefully")
            return True
        else:
            print(f"❌ CLI convert should have failed but didn't: {result.stdout}")
            return False
    except Exception as e:
        print(f"❌ CLI convert error: {e}")
        return False

def test_gui_import():
    """Test GUI module import"""
    print("Testing GUI module import...")
    try:
        from voxbridge.gui.app import run, VoxBridgeGUI
        print("✅ GUI module imports successfully")
        return True
    except Exception as e:
        print(f"❌ GUI module import error: {e}")
        return False

def main():
    """Run all tests"""
    print("VoxBridge CLI and GUI Test Suite")
    print("=" * 40)
    
    tests = [
        test_cli_help,
        test_cli_doctor,
        test_cli_convert_help,
        test_cli_convert_args,
        test_gui_import,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 