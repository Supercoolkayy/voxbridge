#!/bin/bash
# VoxBridge Universal Build Script for Linux/macOS
# This script runs the Python build script which detects the platform automatically

echo "Starting VoxBridge build process..."
echo

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python3 not found. Please install Python 3.8+ and try again."
    exit 1
fi

# Run the Python build script
python3 build_all.py