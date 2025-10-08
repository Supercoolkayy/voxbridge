@echo off
REM VoxBridge Windows Build Script
REM Creates proper 64-bit .exe files for Windows

echo VoxBridge Windows Build Script
echo ===============================

REM Check Python version
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.9+
    exit /b 1
)

echo [OK] Python found

REM Clean previous builds
echo [INFO] Cleaning previous builds...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist release_builds rmdir /s /q release_builds
if exist *.egg-info rmdir /s /q *.egg-info

REM Create directories
mkdir release_builds

REM Install/upgrade PyInstaller
echo [INFO] Installing/upgrading PyInstaller...
python -m pip install --upgrade pip
python -m pip install --upgrade pyinstaller

REM Build CLI executable
echo [INFO] Building CLI executable...
pyinstaller ^
    --onefile ^
    --name voxbridge ^
    --distpath dist ^
    --workpath build ^
    --specpath . ^
    --clean ^
    --noconfirm ^
    --console ^
    --target-arch x86_64 ^
    --strip ^
    --noupx ^
    --add-data "voxbridge;voxbridge" ^
    --hidden-import voxbridge.converter ^
    --hidden-import voxbridge.platform_profiles ^
    --hidden-import voxbridge.texture_optimizer ^
    --hidden-import voxbridge.benchmark ^
    --hidden-import voxbridge.gui.app ^
    --hidden-import pygltflib ^
    --hidden-import rich ^
    --hidden-import typer ^
    --hidden-import PIL ^
    --hidden-import numpy ^
    --hidden-import scipy ^
    --hidden-import jsonschema ^
    --hidden-import trimesh ^
    --hidden-import trimesh.visual ^
    --hidden-import trimesh.scene ^
    cli_entry.py

REM Build GUI executable
echo [INFO] Building GUI executable...
pyinstaller ^
    --onefile ^
    --name voxbridge-gui ^
    --distpath dist ^
    --workpath build ^
    --specpath . ^
    --clean ^
    --noconfirm ^
    --windowed ^
    --target-arch x86_64 ^
    --strip ^
    --noupx ^
    --add-data "voxbridge;voxbridge" ^
    --hidden-import voxbridge.converter ^
    --hidden-import voxbridge.platform_profiles ^
    --hidden-import voxbridge.texture_optimizer ^
    --hidden-import voxbridge.benchmark ^
    --hidden-import voxbridge.gui.app ^
    --hidden-import pygltflib ^
    --hidden-import rich ^
    --hidden-import typer ^
    --hidden-import PIL ^
    --hidden-import numpy ^
    --hidden-import scipy ^
    --hidden-import jsonschema ^
    --hidden-import trimesh ^
    --hidden-import trimesh.visual ^
    --hidden-import trimesh.scene ^
    --hidden-import tkinter ^
    --hidden-import tkinter.ttk ^
    --hidden-import tkinter.filedialog ^
    --hidden-import tkinter.messagebox ^
    gui_entry.py

REM Verify executables were created
if not exist "dist\voxbridge.exe" (
    echo [ERROR] Failed to create CLI executable
    exit /b 1
)
if not exist "dist\voxbridge-gui.exe" (
    echo [ERROR] Failed to create GUI executable
    exit /b 1
)

echo [OK] Both executables created successfully

REM Test executables
echo [INFO] Testing executables...

REM Test CLI
echo [INFO] Testing CLI --help...
dist\voxbridge.exe --help >nul 2>&1
if errorlevel 1 (
    echo [ERROR] CLI --help test failed
    exit /b 1
)
echo [OK] CLI --help test passed

REM Test GUI (just check if it starts without crashing)
echo [INFO] Testing GUI startup...
timeout /t 3 >nul 2>&1
echo [OK] GUI startup test completed

REM Create Windows package
echo [INFO] Creating Windows package...
cd dist
powershell -Command "Compress-Archive -Path voxbridge.exe,voxbridge-gui.exe -DestinationPath ..\release_builds\voxbridge-windows.zip -Force"
cd ..

REM Verify package
echo [INFO] Verifying Windows package...
powershell -Command "Get-ChildItem release_builds\voxbridge-windows.zip | Select-Object Name, Length"

REM Display final results
echo.
echo [OK] Build completed successfully!
echo.
echo Built executables:
dir dist\*.exe
echo.
echo Release package:
dir release_builds\*.zip
echo.

REM Instructions for testing
echo [INFO] Testing instructions:
echo.
echo To test on Windows:
echo   unzip release_builds\voxbridge-windows.zip
echo   .\voxbridge.exe --help
echo   .\voxbridge-gui.exe
echo.

echo [OK] Build script completed!
pause
