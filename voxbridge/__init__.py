"""
VoxBridge - Convert VoxEdit glTF/glb files for Unity and Roblox

A lightweight command-line tool that converts .glTF or .glb files exported 
from VoxEdit (The Sandbox) into clean, platform-ready formats for Unity 
and Roblox game engines.

Main functionality:
- Cleans up texture paths (absolute → relative)
- Normalizes material names (alphanumeric format)
- Validates output files
- Ensures compatibility with Unity and Roblox glTF importers
- Optimizes meshes (polygon reduction, mesh splitting)
- Generates texture atlases and compresses textures
- Platform-specific material mapping (Unity/Roblox)
- Performance reporting and benchmarking

Usage:
    from voxbridge import VoxBridgeConverter
    
    converter = VoxBridgeConverter()
    success = converter.convert_file(input_path, output_path)

CLI Usage:
    voxbridge input.glb output.glb
    voxbridge input.gltf output.gltf --optimize-mesh --generate-atlas --platform unity
"""

__version__ = "1.0.6"
__author__ = "Abdulkareem Oyeneye/Dapps over Apps."
__email__ = "team@dappsoverapps.com"
__license__ = "MIT"

from .converter import VoxBridgeConverter

__all__ = ["VoxBridgeConverter", "__version__"] 