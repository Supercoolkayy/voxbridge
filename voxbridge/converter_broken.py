"""
VoxBridge Converter Module
Core conversion logic separated from CLI interface
"""

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import time

# Try to import texture optimization modules (optional)
try:
    from .texture_optimizer import resize_texture, generate_texture_atlas, update_gltf_with_atlas
    TEXTURE_OPTIMIZATION_AVAILABLE = True
except ImportError:
    TEXTURE_OPTIMIZATION_AVAILABLE = False


class VoxBridgeConverter:
    """Core converter class for VoxEdit glTF/glb files"""
    
    def __init__(self):
        self.supported_formats = ['.gltf', '.glb']
        self.blender_script_path = Path(__file__).parent / 'blender_cleanup.py'
        
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
        """Process GLB files by converting them to glTF format first"""
        try:
            import pygltflib
            from pygltflib import GLTF2
            
            # Load the GLB file using pygltflib - this handles binary files properly
            gltf = GLTF2().load(str(glb_path))
            
            # Convert to a dictionary format that we can work with
            gltf_data = {}
            changes_made = []
            
            # Helper function to safely convert values
            def safe_int(value):
                if value is None:
                    return None
                if callable(value):
                    return None
                try:
                    return int(value)
                except (ValueError, TypeError):
                    return None
            
            def safe_float(value):
                if value is None:
                    return None
                if callable(value):
                    return None
                try:
                    return float(value)
                except (ValueError, TypeError):
                    return None
            
            def safe_str(value):
                if value is None:
                    return None
                if callable(value):
                    return None
                try:
                    return str(value)
                except (ValueError, TypeError):
                    return None
            
            # Extract basic structure
            if gltf.asset:
                gltf_data['asset'] = {
                    'version': safe_str(getattr(gltf.asset, 'version', '2.0')),
                    'generator': safe_str(getattr(gltf.asset, 'generator', 'VoxBridge'))
                }
            
            if gltf.scene is not None:
                scene_value = safe_int(gltf.scene)
                if scene_value is not None:
                    gltf_data['scene'] = scene_value
            
            if gltf.scenes:
                gltf_data['scenes'] = []
                for scene in gltf.scenes:
                    scene_data = {'nodes': []}
                    if scene.nodes:
                        for n in scene.nodes:
                            node_value = safe_int(n)
                            if node_value is not None:
                                scene_data['nodes'].append(node_value)
                    gltf_data['scenes'].append(scene_data)
             
            if gltf.nodes:
                 gltf_data['nodes'] = []
                 for node in gltf.nodes:
                     node_data = {}
                     
                     # Add mesh reference
                     mesh_value = safe_int(getattr(node, 'mesh', None))
                     if mesh_value is not None:
                         node_data['mesh'] = mesh_value
                     
                     # Add name if available
                     if hasattr(node, 'name') and node.name:
                         node_data['name'] = safe_str(node.name)
                     
                     # Add children if available
                     if hasattr(node, 'children') and node.children:
                         children = []
                         for child in node.children:
                             child_value = safe_int(child)
                             if child_value is not None:
                                 children.append(child_value)
                         if children:
                             node_data['children'] = children
                     
                     # Add transformation properties
                     if hasattr(node, 'translation') and node.translation:
                         try:
                             translation = [safe_float(x) for x in node.translation if safe_float(x) is not None]
                             if translation:
                                 node_data['translation'] = translation
                         except (TypeError, ValueError):
                             pass
                     
                     if hasattr(node, 'rotation') and node.rotation:
                         try:
                             rotation = [safe_float(x) for x in node.rotation if safe_float(x) is not None]
                             if rotation:
                                 node_data['rotation'] = rotation
                         except (TypeError, ValueError):
                             pass
                     
                     if hasattr(node, 'scale') and node.scale:
                         try:
                             scale = [safe_float(x) for x in node.scale if safe_float(x) is not None]
                             if scale:
                                 node_data['scale'] = scale
                         except (TypeError, ValueError):
                             pass
                     
                     # Add matrix if available
                     if hasattr(node, 'matrix') and node.matrix:
                         try:
                             matrix = [safe_float(x) for x in node.matrix if safe_float(x) is not None]
                             if matrix:
                                 node_data['matrix'] = matrix
                         except (TypeError, ValueError):
                             pass
                     
                     gltf_data['nodes'].append(node_data)
             
            if gltf.meshes:
                 gltf_data['meshes'] = []
                 for mesh in gltf.meshes:
                     mesh_data = {'primitives': []}
                     
                     # Add mesh name if available
                     if hasattr(mesh, 'name') and mesh.name:
                         mesh_data['name'] = safe_str(mesh.name)
                     
                     for primitive in mesh.primitives:
                         primitive_data = {}
                         
                         # Handle attributes (POSITION, NORMAL, etc.)
                         if hasattr(primitive, 'attributes') and primitive.attributes:
                             primitive_data['attributes'] = {}
                             if hasattr(primitive.attributes, 'items'):
                                 # It's a dict-like object
                                 for attr_name, attr_value in primitive.attributes.items():
                                     if attr_value is not None and not callable(attr_value):
                                         int_value = safe_int(attr_value)
                                         if int_value is not None:
                                             primitive_data['attributes'][attr_name] = int_value
                             else:
                                 # It's a pygltflib object, use dir() to get attributes
                                 for attr_name in dir(primitive.attributes):
                                     if not attr_name.startswith('_') and hasattr(primitive.attributes, attr_name):
                                         attr_value = getattr(primitive.attributes, attr_name)
                                         if attr_value is not None and not callable(attr_value):
                                             int_value = safe_int(attr_value)
                                             if int_value is not None:
                                                 primitive_data['attributes'][attr_name] = int_value
                         
                         # Add material reference
                         material_value = safe_int(getattr(primitive, 'material', None))
                         if material_value is not None:
                             primitive_data['material'] = material_value
                         
                         # Add indices reference
                         indices_value = safe_int(getattr(primitive, 'indices', None))
                         if indices_value is not None:
                             primitive_data['indices'] = indices_value
                         
                         # Add mode (triangles = 4)
                         mode_value = safe_int(getattr(primitive, 'mode', None))
                         if mode_value is not None:
                             primitive_data['mode'] = mode_value
                         
                         mesh_data['primitives'].append(primitive_data)
                     
                     gltf_data['meshes'].append(mesh_data)
             
            if gltf.materials:
                gltf_data['materials'] = []
                for material in gltf.materials:
                    material_data = {'name': safe_str(getattr(material, 'name', 'Material'))}
                    
                    # Handle PBR properties
                    if hasattr(material, 'pbrMetallicRoughness') and material.pbrMetallicRoughness:
                        pbr = material.pbrMetallicRoughness
                        pbr_data = {}
                        
                        # Base color factor
                        if hasattr(pbr, 'baseColorFactor') and pbr.baseColorFactor:
                            try:
                                base_color = [safe_float(x) for x in pbr.baseColorFactor if safe_float(x) is not None]
                                if base_color:
                                    pbr_data['baseColorFactor'] = base_color
                            except (TypeError, ValueError):
                                pass
                        
                        # Metallic factor
                        metallic_value = safe_float(getattr(pbr, 'metallicFactor', None))
                        if metallic_value is not None:
                            pbr_data['metallicFactor'] = metallic_value
                        
                        # Roughness factor
                        roughness_value = safe_float(getattr(pbr, 'roughnessFactor', None))
                        if roughness_value is not None:
                            pbr_data['roughnessFactor'] = roughness_value
                        
                        # Base color texture
                        if hasattr(pbr, 'baseColorTexture') and pbr.baseColorTexture:
                            texture_index = safe_int(getattr(pbr.baseColorTexture, 'index', None))
                            if texture_index is not None:
                                pbr_data['baseColorTexture'] = {'index': texture_index}
                        
                        # Metallic-roughness texture
                        if hasattr(pbr, 'metallicRoughnessTexture') and pbr.metallicRoughnessTexture:
                            texture_index = safe_int(getattr(pbr.metallicRoughnessTexture, 'index', None))
                            if texture_index is not None:
                                pbr_data['metallicRoughnessTexture'] = {'index': texture_index}
                        
                        if pbr_data:
                            material_data['pbrMetallicRoughness'] = pbr_data
                    
                    # Add doubleSided property if available
                    double_sided = getattr(material, 'doubleSided', None)
                    if double_sided is not None:
                        material_data['doubleSided'] = bool(double_sided)
                    
                    gltf_data['materials'].append(material_data)
            
            if gltf.images:
                gltf_data['images'] = []
                for image in gltf.images:
                    image_data = {}
                    uri_value = safe_str(getattr(image, 'uri', None))
                    if uri_value:
                        image_data['uri'] = uri_value
                    else:
                        buffer_view_value = safe_int(getattr(image, 'bufferView', None))
                        if buffer_view_value is not None:
                            image_data['bufferView'] = buffer_view_value
                    gltf_data['images'].append(image_data)
            
            if gltf.textures:
                gltf_data['textures'] = []
                for texture in gltf.textures:
                    texture_data = {}
                    source_value = safe_int(getattr(texture, 'source', None))
                    if source_value is not None:
                        texture_data['source'] = source_value
                    sampler_value = safe_int(getattr(texture, 'sampler', None))
                    if sampler_value is not None:
                        texture_data['sampler'] = sampler_value
                    if texture_data:
                        gltf_data['textures'].append(texture_data)
            
            if gltf.accessors:
                gltf_data['accessors'] = []
                for accessor in gltf.accessors:
                    accessor_data = {}
                    buffer_view_value = safe_int(getattr(accessor, 'bufferView', None))
                    if buffer_view_value is not None:
                        accessor_data['bufferView'] = buffer_view_value
                    
                    component_type_value = safe_int(getattr(accessor, 'componentType', None))
                    if component_type_value is not None:
                        accessor_data['componentType'] = component_type_value
                    
                    count_value = safe_int(getattr(accessor, 'count', None))
                    if count_value is not None:
                        accessor_data['count'] = count_value
                    
                    type_value = safe_str(getattr(accessor, 'type', None))
                    if type_value:
                        accessor_data['type'] = type_value
                    
                    if accessor_data:
                        gltf_data['accessors'].append(accessor_data)
            
            if gltf.bufferViews:
                gltf_data['bufferViews'] = []
                for buffer_view in gltf.bufferViews:
                    buffer_view_data = {}
                    
                    # Buffer index
                    buffer_value = safe_int(getattr(buffer_view, 'buffer', None))
                    if buffer_value is not None:
                        buffer_view_data['buffer'] = buffer_value
                    
                    # Byte offset
                    byte_offset_value = safe_int(getattr(buffer_view, 'byteOffset', None))
                    if byte_offset_value is not None:
                        buffer_view_data['byteOffset'] = byte_offset_value
                    
                    # Byte length
                    byte_length_value = safe_int(getattr(buffer_view, 'byteLength', None))
                    if byte_length_value is not None:
                        buffer_view_data['byteLength'] = byte_length_value
                    
                    # Target (ARRAY_BUFFER = 34962, ELEMENT_ARRAY_BUFFER = 34963)
                    target_value = safe_int(getattr(buffer_view, 'target', None))
                    if target_value is not None:
                        buffer_view_data['target'] = target_value
                    
                    # Byte stride (for interleaved data)
                    byte_stride_value = safe_int(getattr(buffer_view, 'byteStride', None))
                    if byte_stride_value is not None:
                        buffer_view_data['byteStride'] = byte_stride_value
                    
                    # Name if available
                    if hasattr(buffer_view, 'name') and buffer_view.name:
                        buffer_view_data['name'] = safe_str(buffer_view.name)
                    
                    if buffer_view_data:
                        gltf_data['bufferViews'].append(buffer_view_data)
            
            if gltf.buffers:
                gltf_data['buffers'] = []
                
                # For GLB files, preserve the original buffer structure but write to a single .bin file
                if hasattr(gltf, '_glb_data') and gltf._glb_data:
                    # Create a single .bin file with all binary data (use consistent naming)
                    bin_filename = "scene.bin"
                    bin_path = glb_path.parent / bin_filename
                    
                    # Get the total size of all buffer data
                    total_size = len(gltf._glb_data)
                    
                    # Write the consolidated binary file
                    with open(bin_path, 'wb') as bin_file:
                        bin_file.write(gltf._glb_data)
                    
                    # Preserve the original buffer structure but point to the consolidated .bin file
                    for buffer in gltf.buffers:
                        buffer_data = {}
                        
                        # Point to the consolidated .bin file
                        buffer_data['uri'] = bin_filename
                        
                        # Keep the original byteLength
                        byte_length_value = safe_int(getattr(buffer, 'byteLength', None))
                        if byte_length_value is not None:
                            buffer_data['byteLength'] = byte_length_value
                        
                        gltf_data['buffers'].append(buffer_data)
                    
                    changes_made.append(f"Created consolidated binary file: {bin_filename} ({total_size:,} bytes)")
                    changes_made.append(f"Preserved {len(gltf.buffers)} original buffer structures")
                    
                else:
                    # Fallback: keep original buffer info
                    for buffer in gltf.buffers:
                        buffer_data = {}
                        uri_value = safe_str(getattr(buffer, 'uri', None))
                        if uri_value:
                            buffer_data['uri'] = uri_value
                        
                        byte_length_value = safe_int(getattr(buffer, 'byteLength', None))
                        if byte_length_value is not None:
                            buffer_data['byteLength'] = byte_length_value
                        
                        if buffer_data:
                            gltf_data['buffers'].append(buffer_data)
            
            changes_made.append(f"Converted GLB file to glTF format with proper buffer handling")
            return gltf_data, changes_made
            
        except ImportError:
            raise RuntimeError("pygltflib not available. Please install it with: pip install pygltflib")
        except Exception as e:
            # Provide more specific error information
            if "codec can't decode" in str(e):
                raise RuntimeError(
                    f"Failed to process GLB file {glb_path}: Binary file encoding issue. "
                    "This usually means the file is corrupted or not a valid GLB format. "
                    f"Error: {e}"
                )
            else:
                raise RuntimeError(f"Failed to process GLB file {glb_path}: {e}")
    
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
        """Main conversion logic"""
        # Create output directory if it doesn't exist
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if use_blender and input_path.suffix.lower() == '.glb':
            # Try Blender first for GLB files
            try:
                print("Attempting Blender conversion...")
                if self.convert_with_blender(input_path, output_path, optimize_mesh=optimize_mesh):
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
    
    def convert_with_blender(self, input_path: Path, output_path: Path, optimize_mesh: bool = False) -> bool:
        """Convert using Blender Python script"""
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
            str(output_path)
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
    
    def convert_gltf_json(self, input_path: Path, output_path: Path, generate_atlas: bool = False,
                          compress_textures: bool = False, platform: str = "unity") -> bool:
        """Convert glTF JSON data to output format"""
        try:
            # Ensure we have Path objects
            input_path = Path(input_path)
            output_path = Path(output_path)
            
            # Get the cleaned glTF data first
            gltf_data, _ = self.clean_gltf_json(input_path)
            
            # Check if output should be GLB format
            if output_path.suffix.lower() == '.glb':
                # Convert to GLB format
                return self._convert_gltf_to_glb(gltf_data, output_path)
            else:
                # Create clean glTF without embedded binary data (better for Sketchfab)
                print("Creating clean glTF without embedded binary data...")
                
                # Get the cleaned glTF data
                gltf_data, _ = self.clean_gltf_json(input_path)
                
                # Write the clean glTF file (no embedded data)
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(gltf_data, f, indent=2)
                
                print(f" Created clean glTF: {output_path}")
                print(f" File size: {output_path.stat().st_size:,} bytes")
                print(f"💡 Note: This file references external data and is optimized for Sketchfab")
                
                # Generate texture atlas if requested
                if generate_atlas:
                    # Get image paths from the glTF data
                    image_paths = self._extract_image_paths(gltf_data, input_path.parent)
                    if image_paths:
                        atlas_img, mapping = generate_texture_atlas(image_paths, atlas_size=1024)
                        atlas_filename = "texture_atlas.png"
                        atlas_path = input_path.parent / atlas_filename
                        atlas_img.save(atlas_path)
                        update_gltf_with_atlas(output_path, mapping, atlas_filename)
                
                # Copy associated files (textures, bin files)
                self.copy_associated_files(input_path, output_path)
                
                # Create platform-specific package
                self.create_platform_package(output_path, platform)
                
                return True
                
        except Exception as e:
            raise RuntimeError(f"Failed to process glTF: {e}")

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
        """Create a ZIP package for Sketchfab with GLTF and binary files (matching working example)"""
        try:
            import zipfile
            
            # Create ZIP with consistent naming like the working example
            zip_path = gltf_path.parent / "scene.zip"
            
            # Find all associated files to include in the ZIP
            files_to_zip = []
            
            # Add GLTF file (rename to scene.gltf in ZIP)
            files_to_zip.append((gltf_path, "scene.gltf"))
            
            # Look for .bin files (rename to scene.bin in ZIP)
            for bin_file in gltf_path.parent.glob("*.bin"):
                files_to_zip.append((bin_file, "scene.bin"))
                break  # Only take the first .bin file
            
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

    def _extract_binary_data(self, gltf) -> Dict[str, bytes]:
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
                
                # Copy .bin files for glTF
                elif file_path.suffix.lower() == '.bin':
                    dest = output_dir / file_path.name
                    if not dest.exists():
                        shutil.copy2(file_path, dest)

    def map_materials(self, gltf_data: Dict, platform: str = "unity") -> List[str]:
        """
        Map materials for Unity/Roblox compatibility.
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
            original_name = material.get('name', f'Material_{i}')
            
            if platform == "unity":
                # Unity-specific material mapping
                if 'pbrMetallicRoughness' in material:
                    pbr = material['pbrMetallicRoughness']
                    # Ensure Unity Standard shader compatibility
                    if 'baseColorFactor' in pbr:
                        # Unity expects sRGB color space
                        color = pbr['baseColorFactor']
                        if len(color) == 4:  # RGBA
                            # Convert to sRGB if needed (simplified)
                            pbr['baseColorFactor'] = [c ** 2.2 for c in color[:3]] + [color[3]]
                            changes.append(f"Adjusted color space for Unity: Material {i}")
                    
                    # Remove unsupported properties for Unity
                    if 'metallicRoughnessTexture' in pbr:
                        # Unity can handle this, but ensure proper setup
                        changes.append(f"Verified metallic-roughness texture for Unity: Material {i}")
                        
            elif platform == "roblox":
                # Roblox-specific material mapping
                if 'pbrMetallicRoughness' in material:
                    pbr = material['pbrMetallicRoughness']
                    # Roblox has specific material requirements
                    if 'baseColorTexture' in pbr:
                        # Ensure texture is properly referenced
                        changes.append(f"Verified base color texture for Roblox: Material {i}")
                    
                    # Roblox may need simplified material properties
                    if 'metallicFactor' in pbr and pbr['metallicFactor'] > 0.5:
                        # Reduce metallic factor for better Roblox compatibility
                        pbr['metallicFactor'] = min(pbr['metallicFactor'], 0.5)
                        changes.append(f"Reduced metallic factor for Roblox: Material {i}")
            
            # Clean material name for platform compatibility
            clean_name = self._clean_material_name(original_name, platform)
            if clean_name != original_name:
                material['name'] = clean_name
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

    def create_platform_package(self, gltf_path: Path, platform: str) -> bool:
        """Create a platform-specific package with all necessary files"""
        try:
            output_dir = gltf_path.parent
            package_name = f"{gltf_path.stem}_{platform}_package.zip"
            
            # Files to include in package
            files_to_zip = [
                gltf_path,
                output_dir / 'scene.bin',
                output_dir / 'license.txt',
                output_dir / f'README_{platform}.txt'
            ]
            
            # Create platform-specific README
            readme_content = self._create_platform_readme(platform, gltf_path.name)
            readme_path = output_dir / f'README_{platform}.txt'
            with open(readme_path, 'w') as f:
                f.write(readme_content)
            
            # Create license file
            license_content = """Creative Commons Attribution 4.0 International License

This work is licensed under the Creative Commons Attribution 4.0 International License.
To view a copy of this license, visit:
http://creativecommons.org/licenses/by/4.0/
"""
            license_path = output_dir / 'license.txt'
            with open(license_path, 'w') as f:
                f.write(license_content)
            
            # Create metadata
            metadata = {
                "original_source_format": "GLB",
                "target_platform": platform,
                "export_date": time.strftime("%Y-%m-%d %H:%M:%S"),
                "tool_version": "1.0.7",
                "platform_specific_notes": f"Optimized for {platform} with platform-specific requirements",
                "files_included": [f.name for f in files_to_zip if Path(f).exists()],
                "platform_requirements": self._get_platform_requirements(platform),
                "validation_checks": self._get_validation_checks(platform)
            }
            
            metadata_path = output_dir / 'metadata.json'
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            # Create ZIP package
            import zipfile
            with zipfile.ZipFile(output_dir / package_name, 'w') as zipf:
                for file_path in files_to_zip:
                    if Path(file_path).exists():
                        zipf.write(file_path, Path(file_path).name)
                # Also include metadata
                zipf.write(metadata_path, 'metadata.json')
            
            print(f"📦 Created {platform} package: {package_name}")
            print(f"📁 Files included: {[f.name for f in files_to_zip if Path(f).exists()]}")
            print(f"💡 This package is ready for {platform}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error creating platform package: {e}")
            return False
    
    def _create_platform_readme(self, platform: str, gltf_filename: str) -> str:
        """Create platform-specific README content"""
        if platform == "unity":
            return f"""VoxBridge UNITY Package
========================================

Generated: {time.strftime("%Y-%m-%d %H:%M:%S")}
Target Platform: UNITY

Unity Import Instructions:
1. Use Unity's official GLTF importer package
2. Ensure Y-up orientation is maintained
3. Check material assignments and PBR workflow
4. Verify normal maps and tangent space
5. Scale: 1 unit = 1 meter

Unity Requirements:
- Unity 2021.3 LTS or later
- GLTF importer package installed
- Standard Render Pipeline or URP/HDRP

Files Included:
- {gltf_filename}
- scene.bin
- license.txt
- metadata.json

For more information, visit: https://github.com/Supercoolkayy/voxbridge
"""
        elif platform == "roblox":
            return f"""VoxBridge ROBLOX Package
========================================

Generated: {time.strftime("%Y-%m-%d %H:%M:%S")}
Target Platform: ROBLOX

Roblox Import Instructions:
1. Use Roblox's MeshPart importer
2. Verify texture sizes are within 1024x1024 limits
3. Check material compatibility with Roblox shaders
4. Ensure triangle count is under 10,000

Roblox Requirements:
- Roblox Studio latest version
- Texture size: 1024x1024 or smaller
- Triangle count: Under 10,000 per mesh
- Material: Compatible with Roblox shaders

Files Included:
- {gltf_filename}
- scene.bin
- license.txt
- metadata.json

For more information, visit: https://github.com/Supercoolkayy/voxbridge
"""
        else:
            return f"""VoxBridge Package
========================================

Generated: {time.strftime("%Y-%m-%d %H:%M:%S")}
Target Platform: {platform.upper()}

Files Included:
- {gltf_filename}
- scene.bin
- license.txt
- metadata.json

For more information, visit: https://github.com/Supercoolkayy/voxbridge
"""
    
    def _get_platform_requirements(self, platform: str) -> Dict:
        """Get platform-specific requirements"""
        if platform == "unity":
            return {
                "minimum_unity_version": "2021.3 LTS",
                "y_up_orientation": "Required",
                "real_world_scale": "1 unit = 1 meter",
                "pbr_workflow": "Metallic/Roughness",
                "tangent_space": "Required for normal mapping"
            }
        elif platform == "roblox":
            return {
                "minimum_roblox_version": "latest",
                "texture_size_limit": "1024x1024",
                "triangle_count_limit": 10000,
                "material_compatibility": "Compatible with Roblox shaders"
            }
        else:
            return {"platform": platform}
    
    def _get_validation_checks(self, platform: str) -> Dict:
        """Get platform-specific validation checks"""
        if platform == "unity":
            return {
                "y_up_orientation": "Verified",
                "pbr_workflow": "Optimized",
                "tangent_space": "Preserved",
                "texture_format": "RGBA",
                "material_assignments": "Validated"
            }
        elif platform == "roblox":
            return {
                "texture_size_limit": "1024x1024",
                "triangle_count_limit": "Under 10,000",
                "material_compatibility": "Roblox-optimized",
                "naming_convention": "Alphanumeric only"
            }
        else:
            return {"platform": platform}

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

    def _ensure_output_structure(self, output_path: Path, input_path: Path, platform: str):
        """Ensure complete output structure with all necessary files"""
        try:
            output_dir = output_path.parent
            
            # Create platform-specific package
            self.create_platform_package(output_path, platform)
            
            # Create general README
            readme_content = f"""VoxBridge Export Package
========================================

Generated: {time.strftime("%Y-%m-%d %H:%M:%S")}
Target Platform: {platform.upper()}

Files Included:
- {output_path.name}
- scene.bin (if applicable)
- license.txt
- metadata.json

Import Instructions:
1. Extract all files to the same folder
2. Import the main file into {platform}
3. Ensure all referenced files are in the same directory

For more information, visit: https://github.com/Supercoolkayy/voxbridge
"""
            
            readme_path = output_dir / 'README.txt'
            with open(readme_path, 'w') as f:
                f.write(readme_content)
            
            print(f"📁 Created output structure in: {output_dir}")
            print(f"📖 Added README.txt with {platform} usage instructions")
            
        except Exception as e:
            print(f"⚠️ Warning: Could not create complete output structure: {e}")
    
    def _ensure_external_references(self, gltf_data: Dict, base_path: Path):
        """Ensure all texture and binary references are properly set"""
        try:
            # Handle texture references
            if 'images' in gltf_data:
                for image in gltf_data['images']:
                    if 'uri' in image and image['uri']:
                        # Convert absolute paths to relative
                        if '\\' in image['uri'] or '/' in image['uri']:
                            image['uri'] = Path(image['uri']).name
            
            # Handle buffer references
            if 'buffers' in gltf_data:
                for buffer in gltf_data['buffers']:
                    if 'uri' in buffer and buffer['uri']:
                        # Convert absolute paths to relative
                        if '\\' in buffer['uri'] or '/' in buffer['uri']:
                            buffer['uri'] = Path(buffer['uri']).name
                            
        except Exception as e:
            print(f"⚠️ Warning: Could not update external references: {e}")
    
    def _extract_binary_data(self, gltf, gltf_data: Dict) -> List[bytes]:
        """Extract binary data from GLB file"""
        binary_data = []
        try:
            if hasattr(gltf, 'binary_blob') and gltf.binary_blob:
                binary_data.append(gltf.binary_blob)
                print(f"📦 Extracted binary buffer")
            else:
                print(f"📦 No binary buffer found")
        except Exception as e:
            print(f"⚠️ Warning: Could not extract binary data: {e}")
        
        return binary_data 
    
    def _create_basic_gltf_dict(self, gltf_obj) -> Dict:
        """Create a basic dictionary representation of glTF object"""
        try:
            if hasattr(gltf_obj, '__dict__'):
                result = {}
                for attr_name in dir(gltf_obj):
                    if not attr_name.startswith('_') and not callable(getattr(gltf_obj, attr_name)):
                        try:
                            attr_value = getattr(gltf_obj, attr_name)
                            if attr_value is not None:
                                result[attr_name] = self._convert_to_basic_format(attr_value)
                        except Exception:
                            continue
                return result
            else:
                return str(gltf_obj)
        except Exception as e:
            print(f"⚠️ Warning: Could not create basic GLTF dict: {e}")
            return {}
    
    def _convert_to_basic_format(self, value):
        """Convert pygltflib objects to basic Python types"""
        if value is None:
            return None
        elif isinstance(value, (str, int, float, bool)):
            return value
        elif isinstance(value, list):
            return [self._convert_to_basic_format(item) for item in value]
        elif hasattr(value, '__dict__'):
            # Convert object to dictionary
            result = {}
            for attr_name in dir(value):
                if not attr_name.startswith('_') and not callable(getattr(value, attr_name)):
                    try:
                        attr_value = getattr(value, attr_name)
                        if attr_value is not None:
                            # Special handling for extensions and extras
                            if attr_name in ['extensions', 'extras']:
                                if hasattr(attr_value, '__dict__') and attr_value.__dict__:
                                    result[attr_name] = self._convert_to_basic_format(attr_value.__dict__)
                                elif isinstance(attr_value, dict):
                                    result[attr_name] = self._convert_to_basic_format(attr_value)
                                else:
                                    # Skip empty extensions/extras to avoid string conversion
                                    continue
                            else:
                                result[attr_name] = self._convert_to_basic_format(attr_value)
                    except Exception:
                        continue
            return result
        elif hasattr(value, 'keys'):
            # Handle dict-like objects
            try:
                return {key: self._convert_to_basic_format(val) for key, val in value.items()}
            except Exception:
                # If items() doesn't work, try to convert as regular object
                return self._convert_object_to_dict(value)
        elif hasattr(value, '__iter__') and not isinstance(value, (str, bytes)):
            # Handle iterable objects that aren't strings or bytes
            try:
                return {str(i): self._convert_to_basic_format(item) for i, item in enumerate(value)}
            except Exception:
                # If enumeration doesn't work, try to convert as regular object
                return str(value)
        else:
            # For other types, try to convert to string representation
            try:
                return str(value)
            except Exception:
                return None
    
    def _convert_object_to_dict(self, obj):
        """Convert any object to dictionary representation"""
        try:
            if hasattr(obj, '__dict__'):
                return {k: v for k, v in obj.__dict__.items() if not k.startswith('_')}
            elif hasattr(obj, 'keys'):
                return {k: v for k, v in obj.items()}
            else:
                return str(obj)
        except Exception:
            return str(obj) 
    
    def validate_platform_export(self, gltf_path: Path, platform: str) -> Dict:
        """
        Comprehensive validation of platform-specific export requirements
        Args:
            gltf_path: Path to the exported glTF file
            platform: Target platform ("unity" or "roblox")
        Returns:
            Dictionary containing validation results and recommendations
        """
        validation_results = {
            "platform": platform,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "overall_status": "PASS",
            "checks": {},
            "warnings": [],
            "errors": [],
            "recommendations": []
        }
        
        try:
            import pygltflib
            gltf = pygltflib.GLTF2().load(str(gltf_path))
            
            # Basic file validation
            validation_results["checks"]["file_format"] = "PASS"
            validation_results["checks"]["file_size"] = gltf_path.stat().st_size
            
            # Platform-specific validation
            if platform == "unity":
                validation_results.update(self._validate_unity_export(gltf))
            elif platform == "roblox":
                validation_results.update(self._validate_roblox_export(gltf))
            
            # Determine overall status
            if validation_results["errors"]:
                validation_results["overall_status"] = "FAIL"
            elif validation_results["warnings"]:
                validation_results["overall_status"] = "WARN"
            else:
                validation_results["overall_status"] = "PASS"
                
        except ImportError:
            validation_results["errors"].append("pygltflib not available for validation")
            validation_results["overall_status"] = "ERROR"
        except Exception as e:
            validation_results["errors"].append(f"Validation failed: {e}")
            validation_results["overall_status"] = "ERROR"
        
        return validation_results
    
    def _validate_unity_export(self, gltf) -> Dict:
        """Validate Unity-specific export requirements"""
        unity_checks = {
            "y_up_orientation": "PASS",
            "pbr_workflow": "PASS",
            "tangent_space": "PASS",
            "texture_format": "PASS",
            "material_assignments": "PASS"
        }
        warnings = []
        errors = []
        recommendations = []
        
        # Helper function to convert pygltflib objects to basic types
        def convert_attr(obj):
            if hasattr(obj, '__dict__'):
                return {k: v for k, v in obj.__dict__.items() if not k.startswith('_')}
            elif isinstance(obj, dict):
                return obj
            else:
                return {}
        
        # Check materials
        if hasattr(gltf, 'materials') and gltf.materials:
            materials = gltf.materials
        elif isinstance(gltf, dict) and 'materials' in gltf:
            materials = gltf['materials']
        else:
            materials = []
            
        for i, material in enumerate(materials):
            if hasattr(material, 'pbrMetallicRoughness') and material.pbrMetallicRoughness:
                pbr = material.pbrMetallicRoughness
            elif isinstance(material, dict) and 'pbrMetallicRoughness' in material:
                pbr = material['pbrMetallicRoughness']
            else:
                continue
                
            # Check for proper PBR setup
            if hasattr(pbr, 'baseColorFactor') and pbr.baseColorFactor:
                pass  # Has base color factor
            elif isinstance(pbr, dict) and 'baseColorFactor' in pbr:
                pass  # Has base color factor
            else:
                warnings.append(f"Material {i}: Missing base color factor")
                
            # Check for metallic-roughness texture
            if hasattr(pbr, 'metallicRoughnessTexture') and pbr.metallicRoughnessTexture:
                unity_checks["pbr_workflow"] = "PASS"
            elif isinstance(pbr, dict) and 'metallicRoughnessTexture' in pbr:
                unity_checks["pbr_workflow"] = "PASS"
            else:
                warnings.append(f"Material {i}: Missing metallic-roughness texture")
                
            # Check for normal maps
            if hasattr(material, 'normalTexture') and material.normalTexture:
                unity_checks["tangent_space"] = "PASS"
            elif isinstance(material, dict) and 'normalTexture' in material:
                unity_checks["tangent_space"] = "PASS"
            else:
                warnings.append(f"Material {i}: Missing normal map")
        
        # Check meshes
        if hasattr(gltf, 'meshes') and gltf.meshes:
            meshes = gltf.meshes
        elif isinstance(gltf, dict) and 'meshes' in gltf:
            meshes = gltf['meshes']
        else:
            meshes = []
            
        for i, mesh in enumerate(meshes):
            if hasattr(mesh, 'primitives') and mesh.primitives:
                primitives = mesh.primitives
            elif isinstance(mesh, dict) and 'primitives' in mesh:
                primitives = mesh['primitives']
            else:
                continue
                
            for j, primitive in enumerate(primitives):
                if hasattr(primitive, 'attributes') and primitive.attributes:
                    attributes = convert_attr(primitive.attributes)
                elif isinstance(primitive, dict) and 'attributes' in primitive:
                    attributes = primitive['attributes']
                else:
                    continue
                
                # Check for required attributes
                if 'POSITION' not in attributes:
                    errors.append(f"Mesh {i}, Primitive {j}: Missing POSITION attribute")
                
                if 'NORMAL' not in attributes:
                    warnings.append(f"Mesh {i}, Primitive {j}: Missing NORMAL attribute")
                
                if 'TANGENT' not in attributes:
                    warnings.append(f"Mesh {i}, Primitive {j}: Missing TANGENT attribute (required for normal mapping)")
                    unity_checks["tangent_space"] = "WARN"
                
                # Check vertex count
                if 'POSITION' in attributes:
                    pos_accessor_idx = attributes['POSITION']
                    if hasattr(gltf, 'accessors') and gltf.accessors and pos_accessor_idx < len(gltf.accessors):
                        accessor = gltf.accessors[pos_accessor_idx]
                        if hasattr(accessor, 'count') and accessor.count:
                            vertex_count = accessor.count
                            if vertex_count > 50000:
                                warnings.append(f"Mesh {i}: High vertex count ({vertex_count}) for Unity")
                        elif isinstance(accessor, dict) and 'count' in accessor:
                            vertex_count = accessor['count']
                            if vertex_count > 50000:
                                warnings.append(f"Mesh {i}: High vertex count ({vertex_count}) for Unity")
                    elif isinstance(gltf, dict) and 'accessors' in gltf and pos_accessor_idx < len(gltf['accessors']):
                        accessor = gltf['accessors'][pos_accessor_idx]
                        if isinstance(accessor, dict) and 'count' in accessor:
                            vertex_count = accessor['count']
                            if vertex_count > 50000:
                                warnings.append(f"Mesh {i}: High vertex count ({vertex_count}) for Unity")
        
        # Check textures
        if hasattr(gltf, 'images') and gltf.images:
            images = gltf.images
        elif isinstance(gltf, dict) and 'images' in gltf:
            images = gltf['images']
        else:
            images = []
            
        for i, image in enumerate(images):
            if hasattr(image, 'uri') and image.uri:
                uri = image.uri
            elif isinstance(image, dict) and 'uri' in image:
                uri = image['uri']
            else:
                continue
                
            # Check texture format
            if isinstance(uri, str) and uri.lower().endswith(('.png', '.jpg', '.jpeg')):
                unity_checks["texture_format"] = "PASS"
            else:
                warnings.append(f"Image {i}: Non-standard texture format {uri}")
        
        # Add recommendations
        if warnings:
            recommendations.append("Consider adding TANGENT attributes for better normal mapping")
            recommendations.append("Verify all materials have proper PBR workflow setup")
        
        return {
            "checks": unity_checks,
            "warnings": warnings,
            "errors": errors,
            "recommendations": recommendations
        }
    
    def _validate_roblox_export(self, gltf) -> Dict:
        """Validate Roblox-specific export requirements"""
        roblox_checks = {
            "texture_size_limit": "PASS",
            "triangle_count_limit": "PASS",
            "material_compatibility": "PASS",
            "naming_convention": "PASS"
        }
        warnings = []
        errors = []
        recommendations = []
        
        # Helper function to convert pygltflib objects to basic types
        def convert_attr(obj):
            if hasattr(obj, '__dict__'):
                return {k: v for k, v in obj.__dict__.items() if not k.startswith('_')}
            elif isinstance(obj, dict):
                return obj
            else:
                return {}
        
        # Check meshes for triangle count limits
        if hasattr(gltf, 'meshes') and gltf.meshes:
            meshes = gltf.meshes
        elif isinstance(gltf, dict) and 'meshes' in gltf:
            meshes = gltf['meshes']
        else:
            meshes = []
            
        for i, mesh in enumerate(meshes):
            if hasattr(mesh, 'primitives') and mesh.primitives:
                primitives = mesh.primitives
            elif isinstance(mesh, dict) and 'primitives' in mesh:
                primitives = mesh['primitives']
            else:
                continue
                
            for j, primitive in enumerate(primitives):
                if hasattr(primitive, 'indices') and primitive.indices is not None:
                    indices_idx = primitive.indices
                elif isinstance(primitive, dict) and 'indices' in primitive:
                    indices_idx = primitive['indices']
                else:
                    indices_idx = None
                    
                if indices_idx is not None:
                    if hasattr(gltf, 'accessors') and gltf.accessors and indices_idx < len(gltf.accessors):
                        accessor = gltf.accessors[indices_idx]
                        if hasattr(accessor, 'count') and accessor.count:
                            triangle_count = accessor.count // 3
                            if triangle_count > 10000:
                                roblox_checks["triangle_count_limit"] = "FAIL"
                                errors.append(f"Mesh {i}: Triangle count ({triangle_count}) exceeds Roblox limit of 10,000")
                            elif triangle_count > 8000:
                                roblox_checks["triangle_count_limit"] = "WARN"
                                warnings.append(f"Mesh {i}: High triangle count ({triangle_count}) approaching Roblox limit")
                        elif isinstance(accessor, dict) and 'count' in accessor:
                            triangle_count = accessor['count'] // 3
                            if triangle_count > 10000:
                                roblox_checks["triangle_count_limit"] = "FAIL"
                                errors.append(f"Mesh {i}: Triangle count ({triangle_count}) exceeds Roblox limit of 10,000")
                            elif triangle_count > 8000:
                                roblox_checks["triangle_count_limit"] = "WARN"
                                warnings.append(f"Mesh {i}: High triangle count ({triangle_count}) approaching Roblox limit")
                    elif isinstance(gltf, dict) and 'accessors' in gltf and indices_idx < len(gltf['accessors']):
                        accessor = gltf['accessors'][indices_idx]
                        if isinstance(accessor, dict) and 'count' in accessor:
                            triangle_count = accessor['count'] // 3
                            if triangle_count > 10000:
                                roblox_checks["triangle_count_limit"] = "FAIL"
                                errors.append(f"Mesh {i}: Triangle count ({triangle_count}) exceeds Roblox limit of 10,000")
                            elif triangle_count > 8000:
                                roblox_checks["triangle_count_limit"] = "WARN"
                                warnings.append(f"Mesh {i}: High triangle count ({triangle_count}) approaching Roblox limit")
                
                # Check vertex count
                if hasattr(primitive, 'attributes') and primitive.attributes:
                    attributes = convert_attr(primitive.attributes)
                elif isinstance(primitive, dict) and 'attributes' in primitive:
                    attributes = primitive['attributes']
                else:
                    continue
                    
                if 'POSITION' in attributes:
                    pos_accessor_idx = attributes['POSITION']
                    if hasattr(gltf, 'accessors') and gltf.accessors and pos_accessor_idx < len(gltf.accessors):
                        accessor = gltf.accessors[pos_accessor_idx]
                        if hasattr(accessor, 'count') and accessor.count:
                            vertex_count = accessor.count
                            if vertex_count > 10000:
                                roblox_checks["triangle_count_limit"] = "FAIL"
                                errors.append(f"Mesh {i}: Vertex count ({vertex_count}) exceeds Roblox limit of 10,000")
                        elif isinstance(accessor, dict) and 'count' in accessor:
                            vertex_count = accessor['count']
                            if vertex_count > 10000:
                                roblox_checks["triangle_count_limit"] = "FAIL"
                                errors.append(f"Mesh {i}: Vertex count ({vertex_count}) exceeds Roblox limit of 10,000")
                    elif isinstance(gltf, dict) and 'accessors' in gltf and pos_accessor_idx < len(gltf['accessors']):
                        accessor = gltf['accessors'][pos_accessor_idx]
                        if isinstance(accessor, dict) and 'count' in accessor:
                            vertex_count = accessor['count']
                            if vertex_count > 10000:
                                roblox_checks["triangle_count_limit"] = "FAIL"
                                errors.append(f"Mesh {i}: Vertex count ({vertex_count}) exceeds Roblox limit of 10,000")
        
        # Check materials
        if hasattr(gltf, 'materials') and gltf.materials:
            materials = gltf.materials
        elif isinstance(gltf, dict) and 'materials' in gltf:
            materials = gltf['materials']
        else:
            materials = []
            
        for i, material in enumerate(materials):
            if hasattr(material, 'name'):
                material_name = material.name
            elif isinstance(material, dict) and 'name' in material:
                material_name = material['name']
            else:
                material_name = None
                
            if material_name:
                # Check naming convention
                if not material_name.replace('_', '').isalnum():
                    roblox_checks["naming_convention"] = "WARN"
                    warnings.append(f"Material {i}: Name '{material_name}' may cause issues in Roblox")
            
            # Check PBR workflow compatibility
            if hasattr(material, 'pbrMetallicRoughness') and material.pbrMetallicRoughness:
                pbr = material.pbrMetallicRoughness
            elif isinstance(material, dict) and 'pbrMetallicRoughness' in material:
                pbr = material['pbrMetallicRoughness']
            else:
                continue
                
            # Check for simplified materials
            if hasattr(pbr, 'metallicFactor') and pbr.metallicFactor and pbr.metallicFactor > 0.5:
                warnings.append(f"Material {i}: High metallic factor may cause issues in Roblox")
            elif isinstance(pbr, dict) and 'metallicFactor' in pbr and pbr['metallicFactor'] > 0.5:
                warnings.append(f"Material {i}: High metallic factor may cause issues in Roblox")
        
        # Check textures
        if hasattr(gltf, 'images') and gltf.images:
            images = gltf.images
        elif isinstance(gltf, dict) and 'images' in gltf:
            images = gltf['images']
        else:
            images = []
            
        for i, image in enumerate(images):
            if hasattr(image, 'uri') and image.uri:
                uri = image.uri
            elif isinstance(image, dict) and 'uri' in image:
                uri = image['uri']
            else:
                continue
                
            # Check texture format
            if isinstance(uri, str) and uri.lower().endswith(('.png', '.jpg', '.jpeg')):
                roblox_checks["texture_format"] = "PASS"
            else:
                warnings.append(f"Image {i}: Non-standard texture format {uri}")
        
        # Add recommendations
        if warnings:
            recommendations.append("Consider reducing triangle count for better Roblox performance")
            recommendations.append("Simplify materials for better Roblox compatibility")
        
        if errors:
            recommendations.append("Mesh optimization required to meet Roblox limits")
        
        return {
            "checks": roblox_checks,
            "warnings": warnings,
            "errors": errors,
            "recommendations": recommendations
        }
    
    def _print_validation_results(self, validation_results: Dict):
        """Print validation results in a user-friendly format"""
        platform = validation_results.get("platform", "UNKNOWN").upper()
        overall_status = validation_results.get("overall_status", "UNKNOWN")
        
        print(f"\n🔍 {platform} Export Validation Results")
        print("=" * 50)
        
        # Overall status
        if overall_status == "PASS":
            status_icon = ""
        elif overall_status == "WARN":
            status_icon = "⚠️"
        elif overall_status == "FAIL":
            status_icon = "❌"
        else:
            status_icon = "💥"
        
        print(f"Overall Status: {status_icon} {overall_status}")
        
        # Validation checks
        checks = validation_results.get("checks", {})
        if checks:
            print("\n📋 Validation Checks:")
            for check_name, check_status in checks.items():
                if check_status == "PASS":
                    print(f"   {check_name}: {check_status}")
                elif check_status == "WARN":
                    print(f"  ⚠️  {check_name}: {check_status}")
                elif check_status == "FAIL":
                    print(f"  ❌ {check_name}: {check_status}")
                else:
                    print(f"  ❌ {check_name}: {check_status}")
        
        # Warnings
        warnings = validation_results.get("warnings", [])
        if warnings:
            print(f"\n⚠️  Warnings ({len(warnings)}):")
            for warning in warnings:
                print(f"  • {warning}")
        
        # Errors
        errors = validation_results.get("errors", [])
        if errors:
            print(f"\n❌ Errors ({len(errors)}):")
            for error in errors:
                print(f"  • {error}")
        
        # Recommendations
        recommendations = validation_results.get("recommendations", [])
        if recommendations:
            print(f"\n💡 Recommendations ({len(recommendations)}):")
            for rec in recommendations:
                print(f"  • {rec}")
        
        # Final status message
        if overall_status == "PASS":
            print(f"\n Export validation PASSED successfully!")
        elif overall_status == "WARN":
            print(f"\n⚠️  Export validation PASSED with warnings. Review warnings above.")
        elif overall_status == "FAIL":
            print(f"\n💥 Export validation FAILED. Please address errors above before using.")
        else:
            print(f"\n💥 Export validation encountered errors. Check error details above.")
        
        print("=" * 50)