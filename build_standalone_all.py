#!/usr/bin/env python3
"""
Build standalone executables for Windows, Linux, and Mac
Creates executables that work without Python installed
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(cmd, description):
    """Run a command and return success status"""
    print(f"\n🔨 {description}")
    print(f"Command: {' '.join(cmd)}")
    print("-" * 50)
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode == 0:
            print("✅ SUCCESS")
            return True
        else:
            print("❌ FAILED")
            if result.stderr:
                print(f"Error: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("⏰ TIMEOUT")
        return False
    except Exception as e:
        print(f"💥 EXCEPTION: {e}")
        return False

def build_cli_executable():
    """Build CLI executable"""
    print("\n🚀 Building CLI Executable")
    print("=" * 50)
    
    # Build CLI executable
    cmd = [
        "python3", "-m", "PyInstaller",
        "--onefile",
        "--name", "voxbridge",
        "--console",
        "--add-data", "voxbridge:voxbridge",
        "cli_entry.py"
    ]
    
    return run_command(cmd, "Building CLI executable")

def build_gui_executable():
    """Build GUI executable"""
    print("\n🚀 Building GUI Executable")
    print("=" * 50)
    
    # Build GUI executable
    cmd = [
        "python3", "-m", "PyInstaller",
        "--onefile",
        "--name", "voxbridge-gui",
        "--windowed",
        "--add-data", "voxbridge:voxbridge",
        "gui_entry.py"
    ]
    
    return run_command(cmd, "Building GUI executable")

def create_platform_packages():
    """Create platform-specific packages"""
    print("\n📦 Creating Platform Packages")
    print("=" * 50)
    
    # Create output directories
    platforms = ["windows", "linux", "macos"]
    
    for platform in platforms:
        platform_dir = Path(f"voxbridge-{platform}")
        platform_dir.mkdir(exist_ok=True)
        
        # Copy executables
        if platform == "windows":
            # Windows executables
            if Path("dist/voxbridge.exe").exists():
                shutil.copy2("dist/voxbridge.exe", platform_dir / "voxbridge.exe")
            if Path("dist/voxbridge-gui.exe").exists():
                shutil.copy2("dist/voxbridge-gui.exe", platform_dir / "voxbridge-gui.exe")
        else:
            # Linux/Mac executables
            if Path("dist/voxbridge").exists():
                shutil.copy2("dist/voxbridge", platform_dir / "voxbridge")
                os.chmod(platform_dir / "voxbridge", 0o755)
            if Path("dist/voxbridge-gui").exists():
                shutil.copy2("dist/voxbridge-gui", platform_dir / "voxbridge-gui")
                os.chmod(platform_dir / "voxbridge-gui", 0o755)
        
        # Copy documentation
        docs_to_copy = ["README.md", "docs/QUICK_START.md", "docs/STANDALONE_EXECUTABLES.md"]
        for doc in docs_to_copy:
            if Path(doc).exists():
                shutil.copy2(doc, platform_dir / Path(doc).name)
        
        # Copy example files
        if Path("examples").exists():
            shutil.copytree("examples", platform_dir / "examples", dirs_exist_ok=True)
        
        print(f"✅ Created {platform} package: {platform_dir}")
    
    return True

def create_zip_packages():
    """Create ZIP packages for distribution"""
    print("\n📦 Creating ZIP Packages")
    print("=" * 50)
    
    import zipfile
    
    platforms = ["windows", "linux", "macos"]
    
    for platform in platforms:
        platform_dir = Path(f"voxbridge-{platform}")
        zip_file = f"voxbridge-{platform}.zip"
        
        if platform_dir.exists():
            with zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path in platform_dir.rglob('*'):
                    if file_path.is_file():
                        arcname = file_path.relative_to(platform_dir)
                        zipf.write(file_path, arcname)
            
            print(f"✅ Created {zip_file}")
        else:
            print(f"❌ Platform directory not found: {platform_dir}")
    
    return True

def main():
    """Main build process"""
    print("🚀 VoxBridge Standalone Executable Builder")
    print("=" * 60)
    print("Building executables for Windows, Linux, and Mac")
    print("=" * 60)
    
    # Check if PyInstaller is available
    try:
        import PyInstaller
        print(f"✅ PyInstaller version: {PyInstaller.__version__}")
    except ImportError:
        print("❌ PyInstaller not found. Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"])
    
    # Build executables
    cli_success = build_cli_executable()
    gui_success = build_gui_executable()
    
    if not (cli_success and gui_success):
        print("\n❌ Build failed!")
        return False
    
    # Create platform packages
    package_success = create_platform_packages()
    
    if not package_success:
        print("\n❌ Package creation failed!")
        return False
    
    # Create ZIP packages
    zip_success = create_zip_packages()
    
    if not zip_success:
        print("\n❌ ZIP creation failed!")
        return False
    
    print("\n🎉 BUILD COMPLETE!")
    print("=" * 60)
    print("Standalone executables created:")
    print("  - voxbridge-windows.zip")
    print("  - voxbridge-linux.zip") 
    print("  - voxbridge-macos.zip")
    print("\nThese can be distributed to users without Python installed!")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)