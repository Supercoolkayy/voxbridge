@echo off
REM VoxBridge Windows Build Script
REM Creates Windows executable with both CLI and GUI

echo 🚀 VoxBridge Windows Build Script
echo ================================

REM Check dependencies
echo 📋 Checking dependencies...

REM Check Node.js
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Node.js not found. Please install Node.js 18+
    exit /b 1
)

REM Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python not found. Please install Python 3.8+
    exit /b 1
)

REM Check pkg
pkg --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 📦 Installing pkg globally...
    npm install -g pkg
)

REM Check pyinstaller
python -c "import PyInstaller" >nul 2>&1
if %errorlevel% neq 0 (
    echo 📦 Installing PyInstaller...
    pip install pyinstaller
)

echo ✅ All dependencies found

REM Step 1: Build Node.js binary for Windows
echo.
echo 🔧 Step 1: Building Node.js binary for Windows...
cd node_scripts

REM Install dependencies
echo 📦 Installing Node.js dependencies...
npm install

REM Build Windows binary
echo 🔨 Compiling Node.js binary for Windows...
pkg index.js --targets node18-win-x64 --output ../build/voxbridge-node.exe

cd ..
echo ✅ Node.js binary created: build/voxbridge-node.exe

REM Step 2: Build Python CLI
echo.
echo 🔧 Step 2: Building Python CLI...
pyinstaller --onefile --name voxbridge-cli ^
    --add-data "voxbridge;voxbridge" ^
    --add-data "build/voxbridge-node.exe;voxbridge-node.exe" ^
    --hidden-import voxbridge.orchestrated_converter ^
    --hidden-import voxbridge.utils.detect ^
    --hidden-import voxbridge.trimesh_route ^
    --hidden-import voxbridge.converter ^
    --hidden-import voxbridge.platform_profiles ^
    --hidden-import trimesh ^
    --hidden-import pygltflib ^
    --hidden-import numpy ^
    --hidden-import rich ^
    --hidden-import typer ^
    voxbridge/cli.py

echo ✅ CLI executable created: dist/voxbridge-cli.exe

REM Step 3: Build Python GUI
echo.
echo 🔧 Step 3: Building Python GUI...
pyinstaller --onefile --windowed --name voxbridge-gui ^
    --add-data "voxbridge;voxbridge" ^
    --add-data "build/voxbridge-node.exe;voxbridge-node.exe" ^
    --hidden-import voxbridge.orchestrated_converter ^
    --hidden-import voxbridge.utils.detect ^
    --hidden-import voxbridge.trimesh_route ^
    --hidden-import voxbridge.converter ^
    --hidden-import voxbridge.platform_profiles ^
    --hidden-import voxbridge.gui.app ^
    --hidden-import tkinter ^
    --hidden-import trimesh ^
    --hidden-import pygltflib ^
    --hidden-import numpy ^
    voxbridge/gui/app.py

echo ✅ GUI executable created: dist/voxbridge-gui.exe

REM Step 4: Create release package
echo.
echo 🔧 Step 4: Creating release package...

REM Create release directory
if not exist "release\windows" mkdir "release\windows"

REM Copy executables
copy "dist\voxbridge-cli.exe" "release\windows\"
copy "dist\voxbridge-gui.exe" "release\windows\"
copy "build\voxbridge-node.exe" "release\windows\"

REM Create batch files for easy execution
echo @echo off > "release\windows\voxbridge.bat"
echo voxbridge-gui.exe %%* >> "release\windows\voxbridge.bat"

echo @echo off > "release\windows\voxbridge-cli.bat"
echo voxbridge-cli.exe %%* >> "release\windows\voxbridge-cli.bat"

REM Create README
echo Creating README...
(
echo VoxBridge Windows v2.0.0
echo ========================
echo.
echo Files:
echo   - voxbridge-gui.exe     : GUI application
echo   - voxbridge-cli.exe     : Command line interface
echo   - voxbridge-node.exe    : Node.js processor (internal)
echo   - voxbridge.bat         : Launch GUI
echo   - voxbridge-cli.bat     : Launch CLI
echo.
echo Usage:
echo   Double-click voxbridge.bat to launch GUI
echo   Or run voxbridge-cli.exe --help for CLI options
echo.
echo Requirements:
echo   - Windows 10 or later
echo   - No additional dependencies required
) > "release\windows\README.txt"

REM Create installer script
echo Creating installer...
(
echo @echo off
echo echo Installing VoxBridge...
echo if not exist "%PROGRAMFILES%\VoxBridge" mkdir "%PROGRAMFILES%\VoxBridge"
echo copy /Y voxbridge-gui.exe "%PROGRAMFILES%\VoxBridge\"
echo copy /Y voxbridge-cli.exe "%PROGRAMFILES%\VoxBridge\"
echo copy /Y voxbridge-node.exe "%PROGRAMFILES%\VoxBridge\"
echo copy /Y voxbridge.bat "%PROGRAMFILES%\VoxBridge\"
echo copy /Y voxbridge-cli.bat "%PROGRAMFILES%\VoxBridge\"
echo echo VoxBridge installed to %PROGRAMFILES%\VoxBridge
echo pause
) > "release\windows\install.bat"

REM Create ZIP package
echo.
echo 🔧 Step 5: Creating ZIP package...
cd release\windows
powershell Compress-Archive -Path * -DestinationPath ..\voxbridge-windows-x64.zip
cd ..\..

echo ✅ Windows package created: release/voxbridge-windows-x64.zip

REM Summary
echo.
echo 🎉 Windows Build Complete!
echo ========================
echo 📦 Files created:
echo   - release/windows/voxbridge-gui.exe (GUI)
echo   - release/windows/voxbridge-cli.exe (CLI)
echo   - release/windows/voxbridge-node.exe (Node.js processor)
echo   - release/voxbridge-windows-x64.zip (Release package)
echo.
echo 🚀 To run:
echo   Double-click voxbridge.bat for GUI
echo   Or run voxbridge-cli.exe --help for CLI

pause
