#!/usr/bin/env python3
"""
VoxBridge CLI Entry Point
Standalone executable entry point for VoxBridge CLI
"""

import sys
import os
from pathlib import Path

# Add the current directory to Python path for imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Import and run the CLI
from voxbridge.cli import main

if __name__ == "__main__":
    main()
