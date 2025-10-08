"""
Resource path utilities for bundled executables
Handles path resolution for both development and PyInstaller bundle environments
"""

import sys
import os
from pathlib import Path
from typing import Union, Optional

def get_resource_path(relative_path: Union[str, Path]) -> Path:
    """
    Get the absolute path to a resource, works for both dev and PyInstaller bundle
    
    Args:
        relative_path: Path relative to the project root
        
    Returns:
        Absolute path to the resource
    """
    if getattr(sys, 'frozen', False):
        # Running as PyInstaller bundle
        bundle_dir = Path(sys._MEIPASS)
        return bundle_dir / relative_path
    else:
        # Running as script
        project_root = Path(__file__).parent.parent.parent
        return project_root / relative_path

def get_node_runner_path() -> Path:
    """
    Get the path to the node_runner binary
    
    Returns:
        Path to the node_runner executable
    """
    if getattr(sys, 'frozen', False):
        # Running as PyInstaller bundle
        bundle_dir = Path(sys._MEIPASS)
        
        # Check for voxbridge_node.js (our bundled Node.js binary)
        voxbridge_node_path = bundle_dir / "node_binary" / "voxbridge_node.js"
        if voxbridge_node_path.exists():
            try:
                import stat
                if sys.platform != 'win32':
                    voxbridge_node_path.chmod(voxbridge_node_path.stat().st_mode | stat.S_IEXEC)
            except Exception:
                pass
            return voxbridge_node_path
        
        # Check if node-bundle exists (this is our bundled Node.js code)
        node_bundle_path = bundle_dir / "node-bundle" / "index.js"
        if node_bundle_path.exists():
            # Create a working wrapper script
            wrapper_path = bundle_dir / "node_runner_wrapper"
            wrapper_content = f"""#!/bin/bash
# VoxBridge Node Runner Wrapper
SCRIPT_DIR="$(cd "$(dirname "${{BASH_SOURCE[0]}}")" && pwd)"

# Set up environment for sharp
export SHARP_IGNORE_GLOBAL_LIBVIPS=1
export SHARP_LIBVIPS_VERSION="8.14.5"

# Run the bundled Node.js application
exec node "$SCRIPT_DIR/node-bundle/index.js" "$@"
"""
            try:
                wrapper_path.write_text(wrapper_content)
                wrapper_path.chmod(0o755)
                return wrapper_path
            except Exception as e:
                # If we can't create wrapper, return the bundle path directly
                return node_bundle_path
        
        # Fallback: check for original node_runner
        for ext in ['', '.exe']:
            node_runner = bundle_dir / f"node_runner{ext}"
            if node_runner.exists():
                try:
                    import stat
                    if sys.platform != 'win32':
                        node_runner.chmod(node_runner.stat().st_mode | stat.S_IEXEC)
                except Exception:
                    pass
                return node_runner
                
        # Final fallback
        return bundle_dir / "node_runner"
    else:
        # Running as script - look for node_runner in project root
        project_root = Path(__file__).parent.parent.parent
        
        # Check for voxbridge_node.js in build directory
        voxbridge_node_path = project_root / "build" / "node_binary" / "voxbridge_node.js"
        if voxbridge_node_path.exists():
            return voxbridge_node_path
        
        # Check for node_runner in project root
        for ext in ['', '.exe']:
            node_runner = project_root / f"node_runner{ext}"
            if node_runner.exists():
                return node_runner
        # Fallback to node_scripts/index.js
        return project_root / "node_scripts" / "index.js"

def get_voxbridge_module_path() -> Path:
    """
    Get the path to the voxbridge module
    
    Returns:
        Path to the voxbridge module directory
    """
    if getattr(sys, 'frozen', False):
        # Running as PyInstaller bundle
        bundle_dir = Path(sys._MEIPASS)
        return bundle_dir / 'voxbridge'
    else:
        # Running as script
        return Path(__file__).parent.parent

def ensure_executable(path: Path) -> bool:
    """
    Ensure a file is executable (Unix systems)
    
    Args:
        path: Path to the file
        
    Returns:
        True if executable or made executable, False if failed
    """
    try:
        if not path.exists():
            return False
        
        # Make executable on Unix systems
        if os.name != 'nt':  # Not Windows
            os.chmod(path, 0o755)
        
        return True
    except Exception:
        return False

def get_platform_specific_path(base_path: Path, filename: str) -> Path:
    """
    Get platform-specific path for a file
    
    Args:
        base_path: Base directory path
        filename: Filename without extension
        
    Returns:
        Platform-specific path
    """
    if sys.platform == "win32":
        return base_path / f"{filename}.exe"
    else:
        return base_path / filename

def is_bundled() -> bool:
    """
    Check if running as a PyInstaller bundle
    
    Returns:
        True if bundled, False if running as script
    """
    return getattr(sys, 'frozen', False)
