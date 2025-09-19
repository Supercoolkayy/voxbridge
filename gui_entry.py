#!/usr/bin/env python3
"""
VoxBridge GUI Entry Point
Standalone executable entry point for VoxBridge GUI
"""

import sys
import os
from pathlib import Path

# Add the current directory to Python path for imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Import and run the GUI
from voxbridge.gui.app import run

if __name__ == "__main__":
    sys.exit(run())
