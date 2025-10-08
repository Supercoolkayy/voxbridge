#!/usr/bin/env python3
"""
VoxBridge GUI Launcher
Run this file to launch the VoxBridge GUI application
"""

import sys
from pathlib import Path

# Add the voxbridge package to the path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from voxbridge.gui.app import run
    sys.exit(run())
except ImportError as e:
    print(f"Error: Could not import VoxBridge GUI: {e}")
    print("Make sure you're running this from the VoxBridge root directory")
    sys.exit(1)
except Exception as e:
    print(f"Error launching GUI: {e}")
    sys.exit(1)
