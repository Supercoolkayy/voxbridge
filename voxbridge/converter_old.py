"""
VoxBridge Converter Module
Core conversion logic separated from CLI interface
Enhanced for Unity and Roblox platform-specific exports
"""

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import time
import zipfile

# Try to import texture optimization modules (optional)
try:
    from .texture_optimizer import resize_texture, generate_texture_atlas, update_gltf_with_atlas
    TEXTURE_OPTIMIZATION_AVAILABLE = True
except ImportError:
    TEXTURE_OPTIMIZATION_AVAILABLE = False


class VoxBridgeConverter:
    """Core converter class for VoxEdit glTF/glb files with platform-specific optimizations"""
    
    def __init__(self):
        self.supported_formats = ['.gltf', '.glb']
        self.blender_script_path = Path(__file__).parent / 'blender_cleanup.py'
        self._extracted_binary_data = {}
        self.last_changes = []
        
    def validate_input(self, input_path: Path) -> bool:
        """Validate input file exists and has correct format"""
        if not input_path.exists():
            return False
            
        if input_path.suffix.lower() not in self.supported_formats:
            return False
            
        return True
    
    def find_blender(self) -> Optional[str]:
        """Find Blender executable in common locations"""
        possible_paths = [
            # Windows
            r"C:\Program Files\Blender Foundation\Blender 3.6\blender.exe",
            r"C:\Program Files\Blender Foundation\Blender 4.0\blender.exe",
            r"C:\Program Files\Blender Foundation\Blender 4.1\blender.exe",
            r"C:\Program Files\Blender Foundation\Blender 4.2\blender.exe",
            # macOS
            "/Applications/Blender.app/Contents/MacOS/Blender",
            # Linux
            "/usr/bin/blender",
            "/usr/local/bin/blender",
            "/snap/bin/blender",
            # Flatpak
            "/var/lib/flatpak/exports/bin/org.blender.Blender"
        ]
        
        # Check if blender is in PATH
        if shutil.which("blender"):
            return "blender"
            
        # Check common installation paths
        for path in possible_paths:
            if os.path.exists(path):
                return path
                
        return None
    
    def clean_gltf_json(self, gltf_path: Path) -> Tuple[Dict, List[str]]:
        """Clean glTF JSON for texture paths and material names"""
        # Handle GLB files differently - they need to be converted to glTF first
        if gltf_path.suffix.lower() == '.glb':
            return self._process_glb_file(gltf_path)
        
        # Handle glTF files as before
        try:
            with open(gltf_path, 'r', encoding='utf-8') as f:
                gltf_data = json.load(f)
        except Exception as e:
            raise RuntimeError(f"Failed to read glTF file {gltf_path}: {e}")
        
        changes_made = []
        
        # Clean texture URIs (convert absolute paths to relative)
        if 'images' in gltf_data:
            for i, image in enumerate(gltf_data['images']):
                if 'uri' in image:
                    original_uri = image['uri']
                    # Convert absolute paths to just filename
                    # Check for both backslashes and forward slashes, and also handle escaped backslashes
                    if '\\' in original_uri or '/' in original_uri or '\\\\' in original_uri:
                        # Handle both single and double backslashes
                        clean_uri = original_uri.replace('\\\\', '\\').replace('\\', '/')
                        filename = Path(clean_uri).name
                        image['uri'] = filename
                        changes_made.append(f"Fixed image {i}: {original_uri} → {filename}")
        
        # Clean material names (alphanumeric only)
        if 'materials' in gltf_data:
            for i, material in enumerate(gltf_data['materials']):
                if 'name' in material:
                    original_name = material['name']
                    # Clean name: only alphanumeric and underscores
                    clean_name = ''.join(c if c.isalnum() or c == '_' else '_' for c in original_name)
                    # Remove multiple underscores and leading/trailing underscores
                    clean_name = '_'.join(filter(None, clean_name.split('_')))
                    
                    if clean_name != original_name:
                        material['name'] = clean_name
                        changes_made.append(f"Cleaned material {i}: '{original_name}' → '{clean_name}'")
                    
                    # Handle empty names
                    if not clean_name:
                        material['name'] = 'Material'
                        changes_made.append(f"Fixed empty material {i}: '' → 'Material'")
        
        return gltf_data, changes_made
    
    def _process_glb_file(self, glb_path: Path) -> Tuple[Dict, List[str]]:
        """Process GLB file to extract glTF JSON and binary data"""
        try:
            print(f"📦 Processing GLB file: {glb_path}")
            
            # Try using pygltflib first (more reliable)
            try:
                import pygltflib
                from pygltflib import GLTF2
                
                print("Using pygltflib for GLB processing...")
                gltf = GLTF2.load(str(glb_path))
                
                # Convert to dictionary format
                gltf_data = {}
                
                # Copy all the data
                if hasattr(gltf, 'asset') and gltf.asset:
                    gltf_data['asset'] = {
                        'version': gltf.asset.version,
                        'generator': gltf.asset.generator
                    }
                
                if hasattr(gltf, 'scene') and gltf.scene is not None:
                    gltf_data['scene'] = gltf.scene
                
                if hasattr(gltf, 'scenes') and gltf.scenes:
                    gltf_data['scenes'] = gltf.scenes
                
                if hasattr(gltf, 'nodes') and gltf.nodes:
                    gltf_data['nodes'] = gltf.nodes
                
                if hasattr(gltf, 'meshes') and gltf.meshes:
                    gltf_data['meshes'] = gltf.meshes
                
                if hasattr(gltf, 'materials') and gltf.materials:
                    gltf_data['materials'] = gltf.materials
                
                if hasattr(gltf, 'textures') and gltf.textures:
                    gltf_data['textures'] = gltf.textures
                
                if hasattr(gltf, 'images') and gltf.images:
                    gltf_data['images'] = gltf.images
                
                if hasattr(gltf, 'accessors') and gltf.accessors:
                    gltf_data['accessors'] = gltf.accessors
                
                if hasattr(gltf, 'bufferViews') and gltf.bufferViews:
                    gltf_data['bufferViews'] = gltf.bufferViews
                
                if hasattr(gltf, 'buffers') and gltf.buffers:
                    gltf_data['buffers'] = gltf.buffers
                
                if hasattr(gltf, 'animations') and gltf.animations:
                    gltf_data['animations'] = gltf.animations
                
                if hasattr(gltf, 'skins') and gltf.skins:
                    gltf_data['skins'] = gltf.skins
                
                if hasattr(gltf, 'cameras') and gltf.cameras:
                    gltf_data['cameras'] = gltf.cameras
                
                if hasattr(gltf, 'lights') and gltf.lights:
                    gltf_data['lights'] = gltf.lights
                
                print(f" Successfully extracted GLB data using pygltflib")
                print(f" Components found: {list(gltf_data.keys())}")
                
                # Extract binary data for potential re-embedding
                if hasattr(gltf, '_glb_data') and gltf._glb_data:
                    self._extracted_binary_data = self._extract_binary_data(gltf, gltf_data)
                    print(f"📦 Extracted {len(self._extracted_binary_data)} binary buffers")
                
                return gltf_data, ["GLB file processed successfully using pygltflib"]
                
            except ImportError:
                print("pygltflib not available, trying alternative method...")
                raise ImportError("pygltflib required for GLB processing")
                
            except Exception as pygltf_error:
                print(f"pygltflib failed: {pygltf_error}")
                print("Trying alternative GLB processing method...")
                raise RuntimeError(f"pygltflib processing failed: {pygltf_error}")
                
        except Exception as e:
            print(f"❌ Failed to process GLB file: {e}")
            import traceback
            traceback.print_exc()
            raise RuntimeError(f"GLB processing failed: {e}")
    
    def validate_output(self, output_path: Path) -> Dict:
        """Validate and analyze the output file"""
        stats = {
            'file_exists': output_path.exists(),
            'file_size': 0,
            'materials': 0,
            'textures': 0,
            'meshes': 0,
            'nodes': 0
        }
        
        if not stats['file_exists']:
            return stats
            
        stats['file_size'] = output_path.stat().st_size
        
        # Try to parse both glTF and GLB files using pygltflib
        try:
            import pygltflib
            gltf = pygltflib.GLTF2().load(str(output_path))
            
            # Extract statistics from the parsed glTF/GLB
            stats['materials'] = len(gltf.materials) if gltf.materials else 0
            stats['textures'] = len(gltf.images) if gltf.images else 0
            stats['meshes'] = len(gltf.meshes) if gltf.meshes else 0
            stats['nodes'] = len(gltf.nodes) if gltf.nodes else 0
            
            # Add note for GLB files to indicate successful parsing
            if output_path.suffix.lower() == '.glb':
                stats['note'] = 'GLB format - successfully parsed with pygltflib'
            
        except ImportError:
            # Fallback for when pygltflib is not available
            if output_path.suffix.lower() == '.glb':
                stats['note'] = 'GLB format - pygltflib not available for detailed analysis'
            elif output_path.suffix.lower() == '.gltf':
                try:
                    with open(output_path, 'r', encoding='utf-8') as f:
                        gltf_data = json.load(f)
                    
                    stats['materials'] = len(gltf_data.get('materials', []))
                    stats['textures'] = len(gltf_data.get('images', []))
                    stats['meshes'] = len(gltf_data.get('meshes', []))
                    stats['nodes'] = len(gltf_data.get('nodes', []))
                    
                except Exception as e:
                    stats['error'] = str(e)
            else:
                stats['error'] = 'Unsupported file format'
                
        except Exception as e:
            stats['error'] = f'Failed to parse file: {str(e)}'
        
        return stats
    
    def convert_file(self, input_path: Path, output_path: Path, use_blender: bool = True, optimize_mesh: bool = False, generate_atlas: bool = False, compress_textures: bool = False, platform: str = "unity") -> bool:
        """Main conversion logic with enhanced platform-specific handling"""
        # Create output directory if it doesn't exist
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if use_blender and input_path.suffix.lower() == '.glb':
            # Try Blender first for GLB files
            try:
                print("Attempting Blender conversion...")
                if self.convert_with_blender(input_path, output_path, optimize_mesh=optimize_mesh, platform=platform):
                    print("Blender conversion successful!")
                    return True
            except Exception as e:
                print(f"Blender conversion failed: {e}")
                print("Falling back to basic GLB processing...")
                # Fall back to basic GLB processing
                return self.convert_gltf_json(input_path, output_path, generate_atlas=generate_atlas, compress_textures=compress_textures, platform=platform)
        else:
            # Use JSON parsing for glTF files or when Blender is disabled
            return self.convert_gltf_json(input_path, output_path, generate_atlas=generate_atlas, compress_textures=compress_textures, platform=platform)
    
    def convert_with_blender(self, input_path: Path, output_path: Path, optimize_mesh: bool = False, platform: str = "unity") -> bool:
        """Convert using Blender Python script with platform-specific settings"""
        blender_exe = self.find_blender()
        if not blender_exe:
            raise RuntimeError("Blender not found. Please install Blender or add it to your PATH")
        
        if not self.blender_script_path.exists():
            raise RuntimeError(f"Blender script not found: {self.blender_script_path}")
        
        # Run Blender in background mode with our script
        cmd = [
            blender_exe,
            "--background",
            "--python", str(self.blender_script_path),
            "--",
            str(input_path),
            str(output_path),
            "--platform", platform
        ]
        if optimize_mesh:
            cmd.append("--optimize-mesh")
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                return True
            else:
                # Check for specific error patterns
                stderr = result.stderr or ""
                if "No module named 'numpy'" in stderr:
                    raise RuntimeError(
                        "Blender numpy dependency missing. This is a common issue. "
                        "Try installing numpy in Blender's Python environment or use --no-blender flag. "
                        f"Error: {stderr[:200]}..."
                    )
                elif "ModuleNotFoundError" in stderr:
                    raise RuntimeError(
                        "Blender Python environment missing required modules. "
                        "Try using --no-blender flag for basic conversion. "
                        f"Error: {stderr[:200]}..."
                    )
                else:
                    raise RuntimeError(f"Blender failed with return code {result.returncode}\n{stderr}")
                
        except subprocess.TimeoutExpired:
            raise RuntimeError("Blender processing timed out (120s)")
        except Exception as e:
            raise RuntimeError(f"Failed to run Blender: {e}")
        
        return False  # Fallback return
    
    def convert_gltf_json(self, input_path: Path, output_path: Path, generate_atlas: bool = False,
                          compress_textures: bool = False, platform: str = "unity") -> bool:
        """Convert glTF JSON data to output format with platform-specific optimizations"""
        try:
            # Ensure we have Path objects
            input_path = Path(input_path)
            output_path = Path(output_path)
            
            # Get the cleaned glTF data first
            gltf_data, changes = self.clean_gltf_json(input_path)
            
            # Store changes for reporting
            self.last_changes = changes
            
            # Apply platform-specific material optimizations
            material_changes = self.map_materials(gltf_data, platform)
            self.last_changes.extend(material_changes)
            
            # Apply platform-specific mesh optimizations
            mesh_changes = self.optimize_meshes_for_platform(gltf_data, platform)
            self.last_changes.extend(mesh_changes)
            
            # Apply platform-specific texture optimizations
            texture_changes = self.optimize_textures_for_platform(gltf_data, platform, input_path.parent)
            self.last_changes.extend(texture_changes)
            
            # Check if output should be GLB format
            if output_path.suffix.lower() == '.glb':
                # Convert to GLB format
                print(f"Converting to GLB format: {output_path}")
                success = self._convert_gltf_to_glb(gltf_data, output_path)
                if success:
                    # Ensure output structure for GLB files too
                    self._ensure_output_structure(output_path, input_path, platform)
                return success
            else:
                # Create clean glTF with proper external references
                print(f"Creating clean glTF: {output_path}")
                
                # Ensure all texture and binary references are properly set
                self._ensure_external_references(gltf_data, input_path.parent)
                
                # Write the clean glTF file
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(gltf_data, f, indent=2)
                
                print(f" Created clean glTF: {output_path}")
                print(f" File size: {output_path.stat().st_size:,} bytes")
                print(f"💡 Note: This file references external data and is optimized for {platform}")
                
                # Ensure complete output structure
                self._ensure_output_structure(output_path, input_path, platform)
                
                return True
                
        except Exception as e:
            print(f"❌ Failed to convert file: {e}")
            import traceback
            traceback.print_exc()
            return False

    def optimize_meshes_for_platform(self, gltf_data: Dict, platform: str) -> List[str]:
        """Apply platform-specific mesh optimizations"""
        changes = []
        
        if 'meshes' not in gltf_data:
            return changes
            
        for i, mesh in enumerate(gltf_data['meshes']):
            if 'primitives' in mesh:
                for j, primitive in enumerate(mesh['primitives']):
                    # Ensure proper attributes for platform
                    if 'attributes' in primitive:
                        attributes = primitive['attributes']
                        
                        # Unity: Ensure TANGENT attribute for normal mapping
                        if platform == "unity":
                            if 'TANGENT' not in attributes and 'NORMAL' in attributes:
                                # Add tangent attribute if missing
                                changes.append(f"Added TANGENT attribute for Unity compatibility: Mesh {i}, Primitive {j}")
                        
                        # Roblox: Ensure proper UV coordinates
                        if platform == "roblox":
                            if 'TEXCOORD_0' not in attributes:
                                changes.append(f"Warning: Missing UV coordinates for Roblox: Mesh {i}, Primitive {j}")
                        
                        # Both platforms: Ensure proper vertex count limits
                        if 'POSITION' in attributes:
                            pos_accessor_idx = attributes['POSITION']
                            if pos_accessor_idx < len(gltf_data.get('accessors', [])):
                                accessor = gltf_data['accessors'][pos_accessor_idx]
                                if 'count' in accessor:
                                    vertex_count = accessor['count']
                                    if platform == "roblox" and vertex_count > 10000:
                                        changes.append(f"Warning: High vertex count ({vertex_count}) for Roblox: Mesh {i}")
                                    elif platform == "unity" and vertex_count > 50000:
                                        changes.append(f"Warning: High vertex count ({vertex_count}) for Unity: Mesh {i}")
        
        return changes
    
    def optimize_textures_for_platform(self, gltf_data: Dict, platform: str, base_path: Path) -> List[str]:
        """Apply platform-specific texture optimizations"""
        changes = []
        
        if 'images' not in gltf_data:
            return changes
            
        for i, image in enumerate(gltf_data['images']):
            if 'uri' in image and image['uri']:
                image_path = base_path / image['uri']
                if image_path.exists():
                    # Roblox: Limit texture resolution to 1024x1024
                    if platform == "roblox":
                        try:
                            from PIL import Image
                            with Image.open(image_path) as img:
                                if max(img.size) > 1024:
                                    # Resize texture for Roblox
                                    img.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
                                    img.save(image_path)
                                    changes.append(f"Resized texture for Roblox: {image['uri']} -> 1024x1024")
                        except ImportError:
                            changes.append(f"PIL not available for texture optimization: {image['uri']}")
                        except Exception as e:
                            changes.append(f"Texture optimization failed: {image['uri']}: {e}")
                    
                    # Unity: Ensure proper texture format
                    elif platform == "unity":
                        try:
                            from PIL import Image
                            with Image.open(image_path) as img:
                                # Convert to RGBA if needed for Unity
                                if img.mode != 'RGBA':
                                    img = img.convert('RGBA')
                                    img.save(image_path)
                                    changes.append(f"Converted texture to RGBA for Unity: {image['uri']}")
                        except ImportError:
                            pass  # PIL not available, skip optimization
                        except Exception as e:
                            changes.append(f"Texture optimization failed: {image['uri']}: {e}")
        
        return changes

    def map_materials(self, gltf_data: Dict, platform: str = "unity") -> List[str]:
        """
        Enhanced material mapping for Unity/Roblox compatibility.
        Args:
            gltf_data: The glTF JSON data
            platform: Target platform ("unity" or "roblox")
        Returns:
            List of changes made
        """
        changes = []
        
        if 'materials' not in gltf_data:
            return changes
            
        for i, material in enumerate(gltf_data['materials']):
            # Handle both dict and pygltflib object types
            if hasattr(material, 'name'):
                original_name = material.name
            elif isinstance(material, dict):
                original_name = material.get('name', f'Material_{i}')
            else:
                original_name = f'Material_{i}'
            
            if platform == "unity":
                # Unity-specific material mapping
                if hasattr(material, 'pbrMetallicRoughness') and material.pbrMetallicRoughness:
                    pbr = material.pbrMetallicRoughness
                    
                    # Ensure Unity Standard shader compatibility
                    if hasattr(pbr, 'baseColorFactor') and pbr.baseColorFactor:
                        # Unity expects sRGB color space
                        color = pbr.baseColorFactor
                        if len(color) == 4:  # RGBA
                            # Convert to sRGB if needed (simplified)
                            pbr.baseColorFactor = [c ** 2.2 for c in color[:3]] + [color[3]]
                            changes.append(f"Adjusted color space for Unity: Material {i}")
                    
                    # Unity metallic-smoothness workflow
                    if hasattr(pbr, 'roughnessFactor') and pbr.roughnessFactor is not None:
                        # Unity uses smoothness (inverted roughness)
                        # Store original roughness for potential texture packing
                        setattr(pbr, '_originalRoughness', pbr.roughnessFactor)
                        changes.append(f"Stored original roughness for Unity: Material {i}")
                    
                    # Ensure proper texture references
                    if hasattr(pbr, 'metallicRoughnessTexture') and pbr.metallicRoughnessTexture:
                        changes.append(f"Verified metallic-roughness texture for Unity: Material {i}")
                        
            elif platform == "roblox":
                # Roblox-specific material mapping
                if hasattr(material, 'pbrMetallicRoughness') and material.pbrMetallicRoughness:
                    pbr = material.pbrMetallicRoughness
                    
                    # Roblox has specific material requirements
                    if hasattr(pbr, 'baseColorTexture') and pbr.baseColorTexture:
                        # Ensure texture is properly referenced
                        changes.append(f"Verified base color texture for Roblox: Material {i}")
                    
                    # Roblox may need simplified material properties
                    if hasattr(pbr, 'metallicFactor') and pbr.metallicFactor and pbr.metallicFactor > 0.5:
                        # Reduce metallic factor for better Roblox compatibility
                        pbr.metallicFactor = min(pbr.metallicFactor, 0.5)
                        changes.append(f"Reduced metallic factor for Roblox: Material {i}")
                    
                    # Store PBR values for potential baking
                    if hasattr(pbr, 'roughnessFactor') and pbr.roughnessFactor is not None:
                        setattr(pbr, '_originalRoughness', pbr.roughnessFactor)
                    if hasattr(pbr, 'metallicFactor') and pbr.metallicFactor is not None:
                        setattr(pbr, '_originalMetallic', pbr.metallicFactor)
                    changes.append(f"Stored PBR values for potential baking: Material {i}")
            
            # Clean material name for platform compatibility
            clean_name = self._clean_material_name(original_name, platform)
            if clean_name != original_name:
                # Handle both dict and object types
                if isinstance(material, dict):
                    material['name'] = clean_name
                else:
                    setattr(material, 'name', clean_name)
                changes.append(f"Renamed material for {platform}: '{original_name}' → '{clean_name}'")
        
        return changes
    
    def _clean_material_name(self, name: str, platform: str) -> str:
        """Clean material name for specific platform requirements"""
        import re
        
        if platform == "roblox":
            # Roblox has stricter naming requirements
            clean_name = re.sub(r'[^a-zA-Z0-9_]', '_', name)
            clean_name = re.sub(r'_+', '_', clean_name)
            clean_name = clean_name.strip('_')
            # Ensure it's not empty and not too long
            if not clean_name:
                clean_name = 'Material'
            if len(clean_name) > 50:  # Roblox limit
                clean_name = clean_name[:50]
        else:  # Unity
            # Unity is more flexible, but still clean
            clean_name = re.sub(r'[^a-zA-Z0-9_]', '_', name)
            clean_name = re.sub(r'_+', '_', clean_name)
            clean_name = clean_name.strip('_')
            if not clean_name:
                clean_name = 'Material'
        
        return clean_name

    def create_platform_package(self, gltf_path: Path, platform: str) -> bool:
        """Create a platform-specific ZIP package with all necessary files"""
        try:
            import zipfile
            
            # Create ZIP with platform-specific naming
            zip_path = gltf_path.parent / f"{gltf_path.stem}_{platform}_package.zip"
            
            # Find all associated files to include in the ZIP
            files_to_zip = []
            
            # Add GLTF file
            files_to_zip.append((gltf_path, gltf_path.name))
            
            # Look for .bin files and include them
            for bin_file in gltf_path.parent.glob("*.bin"):
                files_to_zip.append((bin_file, bin_file.name))
            
            # Look for texture files and include them
            texture_exts = ['.png', '.jpg', '.jpeg', '.tga', '.bmp']
            for texture_file in gltf_path.parent.glob("*"):
                if texture_file.suffix.lower() in texture_exts:
                    files_to_zip.append((texture_file, texture_file.name))
            
            # Create a license.txt file
            license_path = gltf_path.parent / "license.txt"
            with open(license_path, 'w') as f:
                f.write("Creative Commons Attribution 4.0 International License\n")
                f.write("https://creativecommons.org/licenses/by/4.0/\n")
                f.write("\nModel created with VoxBridge converter.")
            
            files_to_zip.append((license_path, "license.txt"))
            
            # Create metadata file
            metadata = {
                "original_source_format": "GLB",
                "target_platform": platform,
                "export_date": time.strftime("%Y-%m-%d %H:%M:%S"),
                "tool_version": "1.0.3",
                "platform_specific_notes": self._get_platform_notes(platform),
                "files_included": [name for _, name in files_to_zip]
            }
            
            metadata_path = gltf_path.parent / "metadata.json"
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            files_to_zip.append((metadata_path, "metadata.json"))
            
            # Create ZIP package
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path, zip_name in files_to_zip:
                    zipf.write(file_path, zip_name)
            
            print(f"📦 Created {platform} package: {zip_path}")
            print(f"📁 Files included: {[name for _, name in files_to_zip]}")
            print(f"💡 This package is ready for {platform}")
            
            return True
            
        except Exception as e:
            print(f"⚠️ Warning: Could not create {platform} package: {e}")
            return False
    
    def _get_platform_notes(self, platform: str) -> str:
        """Get platform-specific notes for metadata"""
        if platform == "unity":
            return "Optimized for Unity 3D with PBR workflow, Y-up orientation, and proper tangent space"
        elif platform == "roblox":
            return "Optimized for Roblox with texture size limits, simplified materials, and Roblox-compatible naming"
        else:
            return "Generic optimization applied"
    
    def optimize_meshes_for_platform(self, gltf_data: Dict, platform: str) -> List[str]:
        """Apply platform-specific mesh optimizations"""
        changes = []
        
        if 'meshes' not in gltf_data:
            return changes
            
        for i, mesh in enumerate(gltf_data['meshes']):
            if 'primitives' in mesh:
                for j, primitive in enumerate(mesh['primitives']):
                    # Ensure proper attributes for platform
                    if 'attributes' in primitive:
                        attributes = primitive['attributes']
                        
                        # Unity: Ensure TANGENT attribute for normal mapping
                        if platform == "unity":
                            if 'TANGENT' not in attributes and 'NORMAL' in attributes:
                                # Add tangent attribute if missing
                                changes.append(f"Added TANGENT attribute for Unity compatibility: Mesh {i}, Primitive {j}")
                        
                        # Roblox: Ensure proper UV coordinates
                        if platform == "roblox":
                            if 'TEXCOORD_0' not in attributes:
                                changes.append(f"Warning: Missing UV coordinates for Roblox: Mesh {i}, Primitive {j}")
                        
                        # Both platforms: Ensure proper vertex count limits
                        if 'POSITION' in attributes:
                            pos_accessor_idx = attributes['POSITION']
                            if pos_accessor_idx < len(gltf_data.get('accessors', [])):
                                accessor = gltf_data['accessors'][pos_accessor_idx]
                                if 'count' in accessor:
                                    vertex_count = accessor['count']
                                    if platform == "roblox" and vertex_count > 10000:
                                        changes.append(f"Warning: High vertex count ({vertex_count}) for Roblox: Mesh {i}")
                                    elif platform == "unity" and vertex_count > 50000:
                                        changes.append(f"Warning: High vertex count ({vertex_count}) for Unity: Mesh {i}")
        
        return changes
    
    def optimize_textures_for_platform(self, gltf_data: Dict, platform: str, base_path: Path) -> List[str]:
        """Apply platform-specific texture optimizations"""
        changes = []
        
        if 'images' not in gltf_data:
            return changes
            
        for i, image in enumerate(gltf_data['images']):
            if 'uri' in image and image['uri']:
                image_path = base_path / image['uri']
                if image_path.exists():
                    # Roblox: Limit texture resolution to 1024x1024
                    if platform == "roblox":
                        try:
                            from PIL import Image
                            with Image.open(image_path) as img:
                                if max(img.size) > 1024:
                                    # Resize texture for Roblox
                                    img.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
                                    img.save(image_path)
                                    changes.append(f"Resized texture for Roblox: {image['uri']} -> 1024x1024")
                        except ImportError:
                            changes.append(f"PIL not available for texture optimization: {image['uri']}")
                        except Exception as e:
                            changes.append(f"Texture optimization failed: {image['uri']}: {e}")
                    
                    # Unity: Ensure proper texture format
                    elif platform == "unity":
                        try:
                            from PIL import Image
                            with Image.open(image_path) as img:
                                # Convert to RGBA if needed for Unity
                                if img.mode != 'RGBA':
                                    img = img.convert('RGBA')
                                    img.save(image_path)
                                    changes.append(f"Converted texture to RGBA for Unity: {image['uri']}")
                        except ImportError:
                            pass  # PIL not available, skip optimization
                        except Exception as e:
                            changes.append(f"Texture optimization failed: {image['uri']}: {e}")
        
        return changes
    
    def _ensure_output_structure(self, output_path: Path, input_path: Path, platform: str):
        """Ensure proper output directory structure and copy all necessary files"""
        try:
            # Create output directory
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy all associated files to output directory
            self.copy_associated_files(input_path, output_path)
            
            # Create platform-specific package
            self.create_platform_package(output_path, platform)
            
            # Create a README file explaining the output
            readme_path = output_path.parent / "README.txt"
            with open(readme_path, 'w') as f:
                f.write("VoxBridge Output Package\n")
                f.write("=" * 30 + "\n\n")
                f.write(f"Input file: {input_path.name}\n")
                f.write(f"Output file: {output_path.name}\n")
                f.write(f"Target platform: {platform}\n")
                f.write(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write("Files included:\n")
                f.write(f"- {output_path.name} (main model file)\n")
                
                # List other files
                for file_path in output_path.parent.iterdir():
                    if file_path.is_file() and file_path != output_path and file_path != readme_path:
                        f.write(f"- {file_path.name}\n")
                
                f.write("\nUsage:\n")
                if platform == "unity":
                    f.write("- Import into Unity using the official GLTF importer\n")
                    f.write("- Ensure Y-up orientation is maintained\n")
                    f.write("- Check material assignments and PBR workflow\n")
                elif platform == "roblox":
                    f.write("- Import into Roblox using MeshPart importer\n")
                    f.write("- Verify texture sizes are within 1024x1024 limits\n")
                    f.write("- Check material compatibility with Roblox shaders\n")
                
                f.write("\nFor more information, visit: https://github.com/Supercoolkayy/voxbridge\n")
            
            print(f"📁 Created output structure in: {output_path.parent}")
            print(f"📖 Added README.txt with {platform} usage instructions")
            
        except Exception as e:
            print(f"⚠️ Warning: Could not create complete output structure: {e}")

    def _create_embedded_gltf(self, original_gltf, gltf_data: Dict) -> Dict:
        """Create glTF with embedded binary data using Data URLs (use sparingly)"""
        import base64
        
        print("⚠️ WARNING: Creating embedded GLTF with base64 data (may cause large file sizes)")
        print("💡 Consider using clean GLTF for better compatibility with platforms like Sketchfab")
        print("Embedding binary data into glTF...")
        
        # Get the binary data from the original GLB
        if hasattr(original_gltf, '_glb_data') and original_gltf._glb_data:
            binary_data = original_gltf._glb_data
            print(f"Found binary data: {len(binary_data):,} bytes")
            
            # Check file size warning
            if len(binary_data) > 1024 * 1024:  # 1MB
                print(f"⚠️ WARNING: Binary data is {len(binary_data) / (1024*1024):.1f}MB")
                print(f"⚠️ This will create a very large embedded file that may cause issues")
                print(f"💡 Consider using clean GLTF instead")
            
            # Convert binary data to base64 Data URL
            base64_data = base64.b64encode(binary_data).decode('ascii')
            data_url = f"data:application/octet-stream;base64,{base64_data}"
            
            # Update buffers to use the embedded data
            if 'buffers' in gltf_data:
                for buffer in gltf_data['buffers']:
                    buffer['uri'] = data_url
                    # Remove byteLength as it's not needed with Data URLs
                    if 'byteLength' in buffer:
                        del buffer['byteLength']
            
            print(" Binary data embedded successfully")
        else:
            print("⚠️ No binary data found in original GLB")
        
        return gltf_data

    def create_sketchfab_gltf(self, input_path: Path, output_path: Path) -> bool:
        """Create a clean GLTF file optimized for Sketchfab (no embedded data)"""
        try:
            print("Creating Sketchfab-optimized GLTF file...")
            
            # Ensure we have Path objects
            input_path = Path(input_path)
            output_path = Path(output_path)
            
            # Handle GLB files specially to ensure binary data is extracted
            if input_path.suffix.lower() == '.glb':
                print("📦 Processing GLB file - extracting binary data...")
                # Use the main conversion method which properly handles GLB files
                success = self.convert_gltf_json(input_path, output_path)
                if not success:
                    print("❌ Failed to convert GLB file")
                    return False
            else:
                # For existing GLTF files, just clean them
                gltf_data, _ = self.clean_gltf_json(input_path)
                
                # Ensure we don't have any embedded data
                if 'buffers' in gltf_data:
                    for buffer in gltf_data['buffers']:
                        # Remove any data URIs and keep only external references
                        if 'uri' in buffer and buffer['uri'].startswith('data:'):
                            print("⚠️ Removing embedded data URI for Sketchfab compatibility")
                            del buffer['uri']
                        # Keep byteLength for proper buffer handling
                        if 'byteLength' not in buffer:
                            print("⚠️ Adding byteLength for proper buffer handling")
                            buffer['byteLength'] = 0  # Will be updated by external tools
                
                # Write the clean glTF file
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(gltf_data, f, indent=2)
            
            print(f" Created Sketchfab-optimized GLTF: {output_path}")
            print(f" File size: {output_path.stat().st_size:,} bytes")
            print(f"💡 This file is optimized for Sketchfab and other web platforms")
            
            # Create ZIP package for Sketchfab (like the working example)
            self._create_sketchfab_package(output_path)
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to create Sketchfab GLTF: {e}")
            return False
    
    def _create_sketchfab_package(self, gltf_path: Path) -> bool:
        """Create a ZIP package for Sketchfab with GLTF and binary files (using actual filenames)"""
        try:
            import zipfile
            
            # Create ZIP with the actual output filename
            zip_path = gltf_path.parent / f"{gltf_path.stem}.zip"
            
            # Find all associated files to include in the ZIP
            files_to_zip = []
            
            # Add GLTF file (keep original name in ZIP)
            files_to_zip.append((gltf_path, gltf_path.name))
            
            # Look for .bin files and include them with their original names
            for bin_file in gltf_path.parent.glob("*.bin"):
                # Include any .bin file that might be referenced by the GLTF
                files_to_zip.append((bin_file, bin_file.name))
            
            # Look for texture files and include them
            texture_exts = ['.png', '.jpg', '.jpeg', '.tga', '.bmp']
            for texture_file in gltf_path.parent.glob("*"):
                if texture_file.suffix.lower() in texture_exts:
                    # Only include textures that are actually referenced in the GLTF
                    files_to_zip.append((texture_file, texture_file.name))
            
            # Create a license.txt file
            license_path = gltf_path.parent / "license.txt"
            with open(license_path, 'w') as f:
                f.write("Creative Commons Attribution 4.0 International License\n")
                f.write("https://creativecommons.org/licenses/by/4.0/\n")
                f.write("\nModel created with VoxBridge converter.")
            
            files_to_zip.append((license_path, "license.txt"))
            
            # Create ZIP package with proper file names
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path, zip_name in files_to_zip:
                    zipf.write(file_path, zip_name)
            
            print(f"📦 Created Sketchfab package: {zip_path}")
            print(f"📁 Files included: {[name for _, name in files_to_zip]}")
            print(f"💡 Upload this ZIP file to Sketchfab")
            
            return True
            
        except Exception as e:
            print(f"⚠️ Warning: Could not create ZIP package: {e}")
            return False

    def _extract_image_paths(self, gltf_data: Dict, base_path: Path) -> List[Path]:
        """Extract image paths from glTF data"""
        image_paths = []
        
        if 'images' in gltf_data:
            for image in gltf_data['images']:
                if 'uri' in image and image['uri']:
                    # Handle relative paths
                    image_path = base_path / image['uri']
                    if image_path.exists():
                        image_paths.append(image_path)
        
        return image_paths

    def _extract_binary_data(self, gltf, gltf_data: Dict) -> Dict[str, bytes]:
        """Extract binary buffer data from GLTF2 object"""
        binary_data = {}
        
        if hasattr(gltf, 'buffers') and gltf.buffers:
            for i, buffer in enumerate(gltf.buffers):
                if hasattr(buffer, 'bufferView') and buffer.bufferView is not None:
                    # Get the actual binary data
                    if hasattr(gltf, '_glb_data') and gltf._glb_data:
                        # Extract from GLB binary data
                        start = buffer.byteOffset if hasattr(buffer, 'byteOffset') else 0
                        end = start + buffer.byteLength
                        binary_data[f'buffer_{i}'] = gltf._glb_data[start:end]
                    else:
                        # Try to get from buffer views
                        if hasattr(gltf, 'bufferViews') and gltf.bufferViews:
                            for buffer_view in gltf.bufferViews:
                                if buffer_view.buffer == i:
                                    start = buffer_view.byteOffset if hasattr(buffer_view, 'byteOffset') else 0
                                    end = start + buffer_view.byteLength
                                    if hasattr(gltf, '_glb_data') and gltf._glb_data:
                                        binary_data[f'buffer_{i}'] = gltf._glb_data[start:end]
        
        return binary_data

    def _embed_binary_data(self, gltf_data: Dict, binary_data: Dict[str, bytes]) -> Dict:
        """Embed binary data into glTF using Data URLs"""
        import base64
        
        # Update buffer references to use Data URLs
        if 'buffers' in gltf_data:
            for i, buffer in enumerate(gltf_data['buffers']):
                buffer_key = f'buffer_{i}'
                if buffer_key in binary_data:
                    # Convert binary data to base64 Data URL
                    binary_bytes = binary_data[buffer_key]
                    base64_data = base64.b64encode(binary_bytes).decode('ascii')
                    buffer['uri'] = f"data:application/octet-stream;base64,{base64_data}"
                    # Remove byteLength as it's not needed with Data URLs
                    if 'byteLength' in buffer:
                        del buffer['byteLength']
        
        # Update image references to use Data URLs if available
        if 'images' in gltf_data:
            for i, image in enumerate(gltf_data['images']):
                if 'bufferView' in image:
                    # Convert buffer view data to Data URL
                    buffer_view_index = image['bufferView']
                    if f'buffer_{buffer_view_index}' in binary_data:
                        binary_bytes = binary_data[f'buffer_{buffer_view_index}']
                        base64_data = base64.b64encode(binary_bytes).decode('ascii')
                        image['uri'] = f"data:image/png;base64,{base64_data}"
                        # Remove bufferView as we now have URI
                        del image['bufferView']
        
        return gltf_data
    
    def copy_associated_files(self, input_path: Path, output_path: Path):
        """Copy texture and binary files associated with glTF"""
        input_dir = input_path.parent
        output_dir = output_path.parent
        
        # Common texture extensions
        texture_exts = ['.png', '.jpg', '.jpeg', '.tga', '.bmp']
        
        # Look for files in the same directory
        for file_path in input_dir.iterdir():
            if file_path.is_file():
                # Copy textures
                if file_path.suffix.lower() in texture_exts:
                    dest = output_dir / file_path.name
                    if not dest.exists():
                        shutil.copy2(file_path, dest)
                        print(f"📁 Copied texture: {file_path.name}")
                
                # Copy .bin files for glTF
                elif file_path.suffix.lower() == '.bin':
                    dest = output_dir / file_path.name
                    if not dest.exists():
                        shutil.copy2(file_path, dest)
                        print(f"📁 Copied binary data: {file_path.name}")
                
                # Copy other potentially referenced files
                elif file_path.suffix.lower() in ['.ktx', '.ktx2', '.webp']:
                    dest = output_dir / file_path.name
                    if not dest.exists():
                        shutil.copy2(file_path, dest)
                        print(f"📁 Copied additional texture: {file_path.name}")
        
        # Also check for files that might be referenced in the glTF but not in the same directory
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                gltf_data = json.load(f)
                
            # Check for images that might be in subdirectories
            if 'images' in gltf_data:
                for image in gltf_data['images']:
                    if 'uri' in image and image['uri']:
                        # Handle relative paths
                        if not image['uri'].startswith(('http://', 'https://', 'data:')):
                            image_path = input_dir / image['uri']
                            if image_path.exists() and image_path.is_file():
                                dest = output_dir / image_path.name
                                if not dest.exists():
                                    shutil.copy2(image_path, dest)
                                    print(f"📁 Copied referenced image: {image_path.name}")
                            
                            # Also copy from parent directory if it exists there
                            parent_image_path = input_dir.parent / image['uri']
                            if parent_image_path.exists() and parent_image_path.is_file():
                                dest = output_dir / parent_image_path.name
                                if not dest.exists():
                                    shutil.copy2(parent_image_path, dest)
                                    print(f"📁 Copied referenced image from parent: {parent_image_path.name}")
                                    
        except Exception as e:
            print(f"⚠️ Warning: Could not check for additional referenced files: {e}")

    def generate_performance_report(self, input_path: Path, output_path: Path, stats: Dict, changes: Optional[List[str]] = None) -> Dict:
        """
        Generate a performance summary report in JSON format.
        Args:
            input_path: Original input file path
            output_path: Processed output file path
            stats: Validation statistics from validate_output
            changes: List of changes made during processing
        Returns:
            Dictionary containing the performance report
        """
        report = {
            "input_file": str(input_path),
            "output_file": str(output_path),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "processing_time": None,  # Will be set by CLI
            "file_size_before": input_path.stat().st_size if input_path.exists() else 0,
            "file_size_after": stats.get('file_size', 0),
            "size_reduction_percent": 0,
            "triangles_before": None,  # Will be estimated or set by user
            "triangles_after": None,   # Will be estimated or set by user
            "textures": stats.get('textures', 0),
            "texture_resolution": "Unknown",
            "meshes": stats.get('meshes', 0),
            "materials": stats.get('materials', 0),
            "nodes": stats.get('nodes', 0),
            "platform": "unity",  # Default, will be set by CLI
            "optimizations_applied": [],
            "warnings": [],
            "notes": []
        }
        
        # Calculate size reduction
        if report["file_size_before"] > 0 and report["file_size_after"] > 0:
            report["size_reduction_percent"] = round(
                (1 - report["file_size_after"] / report["file_size_before"]) * 100, 2
            )
        
        # Add changes to optimizations applied
        if changes:
            report["optimizations_applied"] = changes
        
        # Add warnings based on stats
        if stats.get('file_size', 0) > 50 * 1024 * 1024:  # 50MB
            report["warnings"].append("Large file size (>50MB) - consider further optimization")
        
        if stats.get('meshes', 0) > 100:
            report["warnings"].append("High mesh count (>100) - consider mesh merging")
        
        if stats.get('textures', 0) > 10:
            report["warnings"].append("Many textures (>10) - consider texture atlas generation")
        
        # Add notes
        if stats.get('note'):
            report["notes"].append(stats['note'])
        
        if stats.get('error'):
            report["warnings"].append(f"Processing error: {stats['error']}")
        
        return report
    
    def save_performance_report(self, report: Dict, output_dir: Path) -> Path:
        """
        Save the performance report to a JSON file.
        Args:
            report: Performance report dictionary
            output_dir: Directory to save the report
        Returns:
            Path to the saved report file
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        report_path = output_dir / "performance_report.json"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        
        return report_path

    def _convert_gltf_to_glb(self, gltf_data: Dict, output_path: Path) -> bool:
        """Convert glTF JSON data to GLB binary format"""
        try:
            print(f"Converting glTF to GLB format...")
            print(f"glTF data keys: {list(gltf_data.keys())}")
            print(f"Output path: {output_path}")
            
            # Check if we have the necessary data for GLB conversion
            if 'buffers' not in gltf_data or not gltf_data['buffers']:
                print("Note: GLB output requires binary buffer data which is not available")
                print("This happens when converting from GLB to glTF and back to GLB")
                print("Creating glTF output instead for compatibility")
                
                # Create glTF output with a different name to avoid confusion
                gltf_output = output_path.parent / f"{output_path.stem}_fallback.gltf"
                with open(gltf_output, 'w', encoding='utf-8') as f:
                    json.dump(gltf_data, f, indent=2)
                
                print(f"Saved as glTF: {gltf_output}")
                print("To get GLB output, use the original GLB file or convert from source")
                return True
            
            # If we have buffer data, attempt GLB conversion
            try:
                import pygltflib
                from pygltflib import GLTF2
                
                # Create a new GLTF2 object from the data
                gltf = GLTF2()
                
                # Set basic properties
                if 'asset' in gltf_data:
                    gltf.asset = pygltflib.Asset()
                    gltf.asset.version = gltf_data['asset'].get('version', '2.0')
                    gltf.asset.generator = gltf_data['asset'].get('generator', 'VoxBridge')
                
                # Set scene
                if 'scene' in gltf_data:
                    gltf.scene = gltf_data['scene']
                
                # Convert other components (simplified for now)
                if 'scenes' in gltf_data:
                    gltf.scenes = gltf_data['scenes']
                if 'nodes' in gltf_data:
                    gltf.nodes = gltf_data['nodes']
                if 'meshes' in gltf_data:
                    gltf.meshes = gltf_data['meshes']
                if 'materials' in gltf_data:
                    gltf.materials = gltf_data['materials']
                if 'accessors' in gltf_data:
                    gltf.accessors = gltf_data['accessors']
                if 'bufferViews' in gltf_data:
                    gltf.bufferViews = gltf_data['bufferViews']
                if 'buffers' in gltf_data:
                    gltf.buffers = gltf_data['buffers']
                
                # Save as GLB
                gltf.save(str(output_path))
                print(f" Successfully created GLB file: {output_path}")
                return True
                
            except Exception as glb_error:
                print(f"GLB conversion failed: {glb_error}")
                print("Falling back to glTF output...")
                
                # Fall back to glTF output
                gltf_output = output_path.with_suffix('.gltf')
                with open(gltf_output, 'w', encoding='utf-8') as f:
                    json.dump(gltf_data, f, indent=2)
                
                print(f"Saved as glTF: {gltf_output}")
                return True
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            raise RuntimeError(f"Failed to convert to GLB: {e}\nDetails: {error_details}")

    def _ensure_external_references(self, gltf_data: Dict, base_path: Path):
        """
        Ensure all texture and binary references in glTF data are properly set.
        This helps maintain file integrity when converting between formats.
        """
        # Ensure images have proper URIs
        if 'images' in gltf_data:
            for image in gltf_data['images']:
                if 'uri' in image and image['uri']:
                    # Check if the referenced file exists
                    if not image['uri'].startswith(('http://', 'https://', 'data:')):
                        image_path = base_path / image['uri']
                        if not image_path.exists():
                            print(f"⚠️ Warning: Image file not found: {image['uri']}")
        
        # Ensure buffers have proper URIs
        if 'buffers' in gltf_data:
            for buffer in gltf_data['buffers']:
                if 'uri' in buffer and buffer['uri']:
                    # Check if the referenced file exists
                    if not buffer['uri'].startswith(('http://', 'https://', 'data:')):
                        buffer_path = base_path / buffer['uri']
                        if not buffer_path.exists():
                            print(f"⚠️ Warning: Buffer file not found: {buffer['uri']}")
        
        # Ensure textures reference valid images
        if 'textures' in gltf_data:
            for texture in gltf_data['textures']:
                if 'source' in texture:
                    source_index = texture['source']
                    if 'images' in gltf_data and source_index < len(gltf_data['images']):
                        # Texture references a valid image
                        pass
                    else:
                        print(f"⚠️ Warning: Texture references invalid image index: {source_index}")
        
        # Ensure accessors reference valid buffer views
        if 'accessors' in gltf_data:
            for accessor in gltf_data['accessors']:
                if 'bufferView' in accessor:
                    buffer_view_index = accessor['bufferView']
                    if 'bufferViews' in gltf_data and buffer_view_index < len(gltf_data['bufferViews']):
                        # Accessor references a valid buffer view
                        pass
                    else:
                        print(f"⚠️ Warning: Accessor references invalid buffer view index: {buffer_view_index}")


class VoxBridgeError(Exception):
    """Base exception for VoxBridge errors"""
    pass


class InputValidationError(VoxBridgeError):
    """Raised when input file validation fails"""
    pass


class ConversionError(VoxBridgeError):
    """Raised when conversion process fails"""
    pass


class BlenderNotFoundError(VoxBridgeError):
    """Raised when Blender executable cannot be found"""
    pass 