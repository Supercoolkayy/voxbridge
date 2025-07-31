#!/usr/bin/env python3
"""
Build script for VoxBridge PyPI package
"""

import subprocess
import sys
import shutil
from pathlib import Path

def clean_build():
    """Clean previous build artifacts"""
    print("🧹 Cleaning previous builds...")
    
    # Remove dist directory
    if Path("dist").exists():
        shutil.rmtree("dist")
    
    # Remove egg-info directories
    for egg_info in Path(".").glob("*.egg-info"):
        shutil.rmtree(egg_info)
    
    # Remove build directory
    if Path("build").exists():
        shutil.rmtree("build")
    
    print("✅ Cleaned build artifacts")

def build_package():
    """Build the package"""
    print("🔨 Building package...")
    
    try:
        # Install build tools if not available
        subprocess.run([sys.executable, "-m", "pip", "install", "build"], check=True)
        
        # Build the package
        result = subprocess.run([sys.executable, "-m", "build"], check=True, capture_output=True, text=True)
        print("✅ Package built successfully!")
        
        # List the built files
        dist_dir = Path("dist")
        if dist_dir.exists():
            print("\n📦 Built files:")
            for file in dist_dir.glob("*"):
                print(f"   {file}")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed: {e.stderr}")
        return False

def check_package():
    """Check the built package"""
    print("🔍 Checking package...")
    
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "twine"], check=True)
        result = subprocess.run([sys.executable, "-m", "twine", "check", "dist/*"], check=True, capture_output=True, text=True)
        print("✅ Package check passed!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Package check failed: {e.stderr}")
        return False

def main():
    print("=" * 60)
    print("🚀 Building VoxBridge for PyPI")
    print("=" * 60)
    
    # Clean previous builds
    clean_build()
    
    # Build package
    if not build_package():
        return
    
    # Check package
    if not check_package():
        return
    
    print("\n" + "=" * 60)
    print("🎉 Package ready for upload!")
    print("=" * 60)
    
    print("\n📋 Next steps:")
    print("1. Upload to TestPyPI: python -m twine upload --repository testpypi dist/*")
    print("2. Upload to PyPI: python -m twine upload dist/*")
    print("3. Test installation: pip install dist/voxbridge-1.0.0.tar.gz")

if __name__ == "__main__":
    main() 