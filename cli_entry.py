#!/usr/bin/env python3
"""
VoxBridge CLI Entry Point
One-file executable entry point for CLI
"""

import sys
import os
from pathlib import Path

# Add the bundled voxbridge module to path
if getattr(sys, 'frozen', False):
    # Running as PyInstaller bundle
    bundle_dir = Path(sys._MEIPASS)
    voxbridge_path = bundle_dir / 'voxbridge'
    sys.path.insert(0, str(voxbridge_path))
else:
    # Running as script
    project_root = Path(__file__).parent
    sys.path.insert(0, str(project_root))

# Import and run CLI
from voxbridge.cli import main

if __name__ == "__main__":
    main()