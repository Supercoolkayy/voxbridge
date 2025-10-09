#!/usr/bin/env python3
"""
Universal VoxBridge Build Script
Automatically detects platform and runs the appropriate build script
"""

import os
import sys
import platform
import subprocess
import shutil
from pathlib import Path

def print_header():
    """Print build script header"""
    print("🚀 VoxBridge Universal Build Script v2.0")
    print("======================================")
    print()

def detect_platform():
    """Detect the current platform"""
    system = platform.system().lower()
    if system == "windows":
        return "windows"
    elif system == "linux":
        return "linux"
    elif system == "darwin":
        return "macos"
    else:
        return "unknown"

def check_dependencies():
    """Check if required dependencies are available"""
    print("📋 Checking build environment...")
    
    # Check Python
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
        print("❌ Python 3.8+ required")
        return False
    print(f"✅ Python {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    # Node.js and npm global checks removed
    print("ℹ️ Using built-in Node.js processing (no system Node required). Bundled node runner will be used.")
    return True

def run_windows_build():
    """Run Windows build script"""
    print("🔧 Running Windows build...")
    
    # Check if PowerShell is available
    if not shutil.which("powershell"):
        print("❌ PowerShell not found")
        return False
    
    # Run the PowerShell script
    try:
        result = subprocess.run([
            "powershell", "-ExecutionPolicy", "Bypass", "-File", "build_windows.ps1"
        ], timeout=3600)  # 1 hour timeout
        
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print("❌ Windows build timed out")
        return False
    except Exception as e:
        print(f"❌ Windows build failed: {e}")
        return False

def run_linux_build():
    """Run Linux build script"""
    print("🔧 Running Linux build...")
    
    # Make sure the script is executable
    try:
        os.chmod("build_linux.sh", 0o755)
    except Exception:
        pass
    
    # Run the bash script
    try:
        result = subprocess.run(["./build_linux.sh"], timeout=3600)  # 1 hour timeout
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print("❌ Linux build timed out")
        return False
    except Exception as e:
        print(f"❌ Linux build failed: {e}")
        return False

def run_macos_build():
    """Run macOS build script (fallback to Linux script)"""
    print("🔧 Running macOS build (using Linux script)...")
    return run_linux_build()

def validate_build():
    """Validate the build outputs"""
    print("\n📋 Validating build outputs...")
    
    dist_dir = Path("dist")
    if not dist_dir.exists():
        print("❌ dist/ directory not found")
        return False
    
    # Expected executables based on platform
    platform_name = detect_platform()
    if platform_name == "windows":
        expected_files = [
            ("voxbridge.exe", "CLI"),
            ("voxbridge-gui.exe", "GUI"),
            ("node_runner.exe", "Node Runner")
        ]
    else:
        expected_files = [
            ("voxbridge", "CLI"),
            ("voxbridge-gui", "GUI"),
            ("node_runner", "Node Runner")
        ]
    
    all_valid = True
    for filename, description in expected_files:
        filepath = dist_dir / filename
        if filepath.exists() and filepath.stat().st_size > 0:
            size_mb = filepath.stat().st_size / (1024 * 1024)
            print(f"✅ {description}: {filename} ({size_mb:.2f} MB)")
        else:
            print(f"❌ {description}: {filename} - NOT FOUND OR EMPTY")
            all_valid = False
    
    return all_valid

def create_dist_structure():
    """Ensure dist directory structure is set up"""
    dist_dir = Path("dist")
    dist_dir.mkdir(exist_ok=True)
    
    # Create README for dist directory
    readme_content = """# VoxBridge Executables

This directory contains the built VoxBridge executables.

## Files

- voxbridge(.exe) - Command line interface
- voxbridge-gui(.exe) - Graphical user interface  
- node_runner(.exe) - Node.js processor (internal use)

## Usage

### Windows
- Double-click voxbridge-gui.exe to launch the GUI
- Run voxbridge.exe --help for CLI options
- Run node_runner.exe --help for Node.js processor

### Linux/macOS
- Run ./voxbridge-gui to launch the GUI
- Run ./voxbridge --help for CLI options
- Run ./node_runner --help for Node.js processor

## Requirements

- No additional dependencies required
- All executables are self-contained
"""
    
    readme_path = dist_dir / "README.md"
    readme_path.write_text(readme_content)

def main():
    """Main build function"""
    print_header()
    
    # Detect platform
    platform_name = detect_platform()
    print(f"🖥️  Detected platform: {platform_name}")
    
    if platform_name == "unknown":
        print("❌ Unknown platform. Cannot proceed with build.")
        sys.exit(1)
    
    # Check dependencies
    if not check_dependencies():
        print("❌ Missing required dependencies. Please install them and try again.")
        sys.exit(1)
    
    # Create dist structure
    create_dist_structure()
    
    # Run appropriate build script
    build_success = False
    
    if platform_name == "windows":
        build_success = run_windows_build()
    elif platform_name == "linux":
        build_success = run_linux_build()
    elif platform_name == "macos":
        build_success = run_macos_build()
    
    if not build_success:
        print("\n❌ Build failed!")
        sys.exit(1)
    
    # Validate build
    if not validate_build():
        print("\n❌ Build validation failed!")
        sys.exit(1)
    
    # Success message
    print("\n🎉 Build completed successfully!")
    print("=============================")
    print("📦 Executables are ready in the dist/ directory")
    print("🚀 You can now run the VoxBridge applications")
    
    # Platform-specific usage instructions
    if platform_name == "windows":
        print("\n💡 Windows Usage:")
        print("   • Double-click voxbridge-gui.exe for GUI")
        print("   • Run voxbridge.exe --help for CLI options")
    else:
        print("\n💡 Linux/macOS Usage:")
        print("   • Run ./voxbridge-gui for GUI")
        print("   • Run ./voxbridge --help for CLI options")

if __name__ == "__main__":
    main()
