#!/usr/bin/env python3
"""
VoxBridge GUI Entry Point
One-file executable entry point for GUI
"""

import sys
import os
import tkinter as tk
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

# Import and run GUI
from voxbridge.gui.app import VoxBridgeGUI

def main():
    """Main GUI entry point"""
    try:
        root = tk.Tk()
        app = VoxBridgeGUI(root)
        root.mainloop()
    except Exception as e:
        print(f"Error starting GUI: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()