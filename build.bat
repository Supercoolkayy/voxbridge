@echo off
REM VoxBridge Windows Build Script
REM Builds standalone executables for Windows

echo 🚀 VoxBridge Windows Build Script
echo ========================================

REM Check if we're in the right directory
if not exist "pyproject.toml" (
    echo [ERROR] Please run this script from the VoxBridge root directory
    exit /b 1
)

REM Create output directories
echo [INFO] Creating output directories...
if not exist "dist\windows" mkdir dist\windows
if not exist "release_builds" mkdir release_builds

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.9+ from https://python.org
    echo Make sure to check "Add Python to PATH" during installation
    exit /b 1
)

REM Check if PyInstaller is available
python -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo [INFO] Installing PyInstaller...
    python -m pip install pyinstaller
    if errorlevel 1 (
        echo [ERROR] Failed to install PyInstaller
        exit /b 1
    )
)

REM Clean previous builds
echo [INFO] Cleaning previous builds...
if exist "build" rmdir /s /q build
if exist "dist" rmdir /s /q dist

REM Build CLI executable
echo [INFO] Building Windows CLI executable...
python -m PyInstaller ^
    --onefile ^
    --console ^
    --name voxbridge ^
    --distpath dist\windows ^
    --add-data "voxbridge;voxbridge" ^
    --hidden-import pygltflib ^
    --hidden-import PIL ^
    --hidden-import numpy ^
    --hidden-import scipy ^
    --hidden-import jsonschema ^
    --hidden-import rich ^
    --hidden-import typer ^
    cli_entry.py

if errorlevel 1 (
    echo [ERROR] Failed to build CLI executable
    exit /b 1
)
echo [SUCCESS] CLI executable built successfully

REM Build GUI executable
echo [INFO] Building Windows GUI executable...
python -m PyInstaller ^
    --onefile ^
    --windowed ^
    --name voxbridge-gui ^
    --distpath dist\windows ^
    --add-data "voxbridge;voxbridge" ^
    --hidden-import pygltflib ^
    --hidden-import PIL ^
    --hidden-import numpy ^
    --hidden-import scipy ^
    --hidden-import jsonschema ^
    --hidden-import rich ^
    --hidden-import typer ^
    --hidden-import tkinter ^
    gui_entry.py

if errorlevel 1 (
    echo [ERROR] Failed to build GUI executable
    exit /b 1
)
echo [SUCCESS] GUI executable built successfully

REM Create Windows package
echo [INFO] Creating Windows package...
cd dist\windows
powershell -Command "Compress-Archive -Path voxbridge.exe,voxbridge-gui.exe -DestinationPath ..\..\release_builds\voxbridge-win64.zip -Force"
cd ..\..

if errorlevel 1 (
    echo [ERROR] Failed to create Windows package
    exit /b 1
)

echo [SUCCESS] Windows package created: release_builds\voxbridge-win64.zip

REM Clean up build artifacts
echo [INFO] Cleaning up build artifacts...
if exist "build" rmdir /s /q build
for %%f in (*.spec) do del "%%f"

echo [SUCCESS] Build completed successfully!
echo [INFO] Distribution package is available in release_builds\

REM Show file sizes
echo [INFO] Package size:
dir release_builds\voxbridge-win64.zip

echo.
echo [INFO] To test the executables:
echo   CLI: dist\windows\voxbridge.exe --help
echo   GUI: dist\windows\voxbridge-gui.exe
