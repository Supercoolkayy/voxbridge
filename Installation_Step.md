# VoxBridge Installation Guide

This document provides a complete step‑by‑step setup for Linux/WSL, macOS, and Windows.  
It ensures VoxBridge runs correctly, with all dependencies installed and the PATH configured.

---

## 1. Prerequisites

- **Python**: version 3.9+ (check with `python --version`)
- **pip**: package installer for Python (check with `pip --version`)
- **git**: required if installing directly from GitHub
- **Node.js** (optional, for asset pipelines)
- **Blender** (optional, for preview/export testing)
- **Assimp** (optional, for model conversions)

---

## 2. Installation Methods

### Option A — Install from PyPI (if available)
```bash
pip install voxbridge
```

### Option B — Install from GitHub (latest version)
```bash
git clone https://github.com/Supercoolkayy/voxbridge.gitcd voxbridge
pip install .
```

### Option C — Development Install (editable mode)
```bash
git clone https://github.com/Supercoolkayy/voxbridge.git
cd voxbridge
pip install -e .
```

---

## 3. Platform‑Specific Setup

### Linux / WSL
1. Ensure Python and pip are installed:
   ```bash
   sudo apt update
   sudo apt install python3 python3-pip git -y
   ```
2. Install VoxBridge using one of the methods above.
3. Add `~/.local/bin` to your PATH if not already set:
   ```bash
   echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
   source ~/.bashrc
   ```

### macOS
1. Install Homebrew if not already installed:
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```
2. Install Python and git:
   ```bash
   brew install python git
   ```
3. Install VoxBridge using one of the methods above.

### Windows
1. Install [Python](https://www.python.org/downloads/) (check “Add to PATH” during installation).
2. Install [Git for Windows](https://git-scm.com/download/win).
3. Open **PowerShell** and install VoxBridge using one of the methods above.

---

## 4. Upgrading VoxBridge
```bash
pip install --upgrade voxbridge
```

If installed from GitHub:
```bash
cd voxbridge
git pull origin main
pip install --upgrade .
```

---

## 5. Uninstalling VoxBridge
```bash
pip uninstall voxbridge
```

---

## 6. Quick Test
Run this command after installation to confirm VoxBridge works:
```bash
voxbridge --help
```

If the command is not found, try:
```bash
python -m voxbridge.cli --help
```

---

## 7. Troubleshooting
- **Command not found** → Add Python’s scripts folder to PATH:
  - Linux/WSL: `~/.local/bin`
  - macOS: `~/Library/Python/<version>/bin`
  - Windows: `C:\Users\<YourName>\AppData\Roaming\Python\Python<version>\Scripts`
- **Permission issues** → Use `pip install --user ...` instead of global install.
- **Blender not detected in WSL** → Install Blender natively on Windows or macOS.

---

## 8. Optional Tools
- **Blender**: for verifying imports/exports visually.
- **Node.js**: for running asset pipelines.
- **Assimp**: if additional conversions are required.

---

You’re now ready to use VoxBridge!
