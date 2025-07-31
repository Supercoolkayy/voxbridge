#!/usr/bin/env python3
"""
Test script to verify the build process works locally
"""

import subprocess
import sys
import shutil
from pathlib import Path

def run_command(cmd, description):
    """Run a command and handle errors"""
    print(f"\n{description}...")
    print(f"Running: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("Success!")
        if result.stdout:
            print("Output:", result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed: {e}")
        if e.stdout:
            print("Stdout:", e.stdout)
        if e.stderr:
            print("Stderr:", e.stderr)
        return False

def main():
    print("Testing VoxBridge build process...")
    print("=" * 50)
    
    # Clean previous builds
    print("\nCleaning previous builds...")
    for path in ["dist", "build"]:
        if Path(path).exists():
            shutil.rmtree(path)
            print(f"Removed {path}/")
    
    # Test build
    if not run_command([sys.executable, "-m", "pip", "install", "build"], "Installing build tools"):
        return False
    
    if not run_command([sys.executable, "-m", "build"], "Building package"):
        return False
    
    if not run_command([sys.executable, "-m", "pip", "install", "twine"], "Installing twine"):
        return False
    
    if not run_command([sys.executable, "-m", "twine", "check", "dist/*"], "Checking package"):
        return False
    
    # List built files
    print("\n📦 Built files:")
    dist_dir = Path("dist")
    if dist_dir.exists():
        for file in dist_dir.glob("*"):
            print(f"  {file}")
    
    print("\n" + "=" * 50)
    print("🎉 Build test completed successfully!")
    print("✅ Ready to push to GitHub and create a release!")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 