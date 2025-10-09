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
    Return the path to the bundled node runner (voxbridge_node.js)
    """
    return get_resource_path("build/node_binary/voxbridge_node.js")

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
