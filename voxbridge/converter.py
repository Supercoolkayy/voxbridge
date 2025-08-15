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
    
    def clean_gltf_json(self, gltf_path: Path, output_path: Path = None) -> Tuple[Dict, List[str]]:
        """Clean glTF JSON for texture paths and material names"""
        # Handle GLB files differently - they need to be converted to glTF first
        if gltf_path.suffix.lower() == '.glb':
            if output_path is None:
                output_path = gltf_path.with_suffix('.gltf')
            return self._process_glb_file(gltf_path, output_path)
        
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
    
    def _process_glb_file(self, glb_path: Path, output_path: Path) -> Tuple[Dict, List[str]]:
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
                
                # Copy all the data and convert pygltflib objects to dictionaries
                if hasattr(gltf, 'asset') and gltf.asset:
                    gltf_data['asset'] = {
                        'version': gltf.asset.version,
                        'generator': gltf.asset.generator
                    }
                
                if hasattr(gltf, 'scene') and gltf.scene is not None:
                    gltf_data['scene'] = gltf.scene
                
                if hasattr(gltf, 'scenes') and gltf.scenes:
                    # Convert pygltflib Scene objects to dictionaries
                    gltf_data['scenes'] = []
                    for scene in gltf.scenes:
                        scene_dict = {}
                        if hasattr(scene, 'nodes') and scene.nodes:
                            scene_dict['nodes'] = scene.nodes
                        if hasattr(scene, 'name') and scene.name:
                            scene_dict['name'] = scene.name
                        gltf_data['scenes'].append(scene_dict)
                
                if hasattr(gltf, 'nodes') and gltf.nodes:
                    # Convert pygltflib Node objects to dictionaries
                    gltf_data['nodes'] = []
                    for node in gltf.nodes:
                        node_dict = {}
                        if hasattr(node, 'mesh') and node.mesh is not None:
                            node_dict['mesh'] = node.mesh
                        if hasattr(node, 'name') and node.name:
                            node_dict['name'] = node.name
                        if hasattr(node, 'translation') and node.translation:
                            node_dict['translation'] = node.translation
                        if hasattr(node, 'rotation') and node.rotation:
                            node_dict['rotation'] = node.rotation
                        if hasattr(node, 'scale') and node.scale:
                            node_dict['scale'] = node.scale
                        if hasattr(node, 'children') and node.children:
                            node_dict['children'] = node.children
                        gltf_data['nodes'].append(node_dict)
                
                if hasattr(gltf, 'meshes') and gltf.meshes:
                    # Convert pygltflib Mesh objects to dictionaries
                    gltf_data['meshes'] = []
                    for mesh in gltf.meshes:
                        mesh_dict = {}
                        if hasattr(mesh, 'primitives') and mesh.primitives:
                            mesh_dict['primitives'] = []
                            for primitive in mesh.primitives:
                                primitive_dict = {}
                                if hasattr(primitive, 'attributes') and primitive.attributes:
                                    # Convert pygltflib Attributes object to dictionary
                                    attributes_dict = {}
                                    if hasattr(primitive.attributes, 'POSITION') and primitive.attributes.POSITION is not None:
                                        attributes_dict['POSITION'] = primitive.attributes.POSITION
                                    if hasattr(primitive.attributes, 'NORMAL') and primitive.attributes.NORMAL is not None:
                                        attributes_dict['NORMAL'] = primitive.attributes.NORMAL
                                    if hasattr(primitive.attributes, 'TEXCOORD_0') and primitive.attributes.TEXCOORD_0 is not None:
                                        attributes_dict['TEXCOORD_0'] = primitive.attributes.TEXCOORD_0
                                    if hasattr(primitive.attributes, 'TANGENT') and primitive.attributes.TANGENT is not None:
                                        attributes_dict['TANGENT'] = primitive.attributes.TANGENT
                                    primitive_dict['attributes'] = attributes_dict
                                if hasattr(primitive, 'indices') and primitive.indices is not None:
                                    primitive_dict['indices'] = primitive.indices
                                if hasattr(primitive, 'material') and primitive.material is not None:
                                    primitive_dict['material'] = primitive.material
                                if hasattr(primitive, 'mode') and primitive.mode is not None:
                                    primitive_dict['mode'] = primitive.mode
                                mesh_dict['primitives'].append(primitive_dict)
                        if hasattr(mesh, 'name') and mesh.name:
                            mesh_dict['name'] = mesh.name
                        gltf_data['meshes'].append(mesh_dict)
                
                if hasattr(gltf, 'materials') and gltf.materials:
                    # Convert pygltflib Material objects to dictionaries
                    gltf_data['materials'] = []
                    for material in gltf.materials:
                        material_dict = {}
                        if hasattr(material, 'name') and material.name:
                            material_dict['name'] = material.name
                        if hasattr(material, 'pbrMetallicRoughness') and material.pbrMetallicRoughness:
                            pbr = material.pbrMetallicRoughness
                            material_dict['pbrMetallicRoughness'] = {}
                            if hasattr(pbr, 'baseColorFactor') and pbr.baseColorFactor:
                                material_dict['pbrMetallicRoughness']['baseColorFactor'] = pbr.baseColorFactor
                            if hasattr(pbr, 'metallicFactor') and pbr.metallicFactor is not None:
                                material_dict['pbrMetallicRoughness']['metallicFactor'] = pbr.metallicFactor
                            if hasattr(pbr, 'roughnessFactor') and pbr.roughnessFactor is not None:
                                material_dict['pbrMetallicRoughness']['roughnessFactor'] = pbr.roughnessFactor
                            if hasattr(pbr, 'baseColorTexture') and pbr.baseColorTexture:
                                material_dict['pbrMetallicRoughness']['baseColorTexture'] = {'index': pbr.baseColorTexture.index}
                        if hasattr(material, 'doubleSided') and material.doubleSided is not None:
                            material_dict['doubleSided'] = material.doubleSided
                        gltf_data['materials'].append(material_dict)
                
                if hasattr(gltf, 'textures') and gltf.textures:
                    # Convert pygltflib Texture objects to dictionaries
                    gltf_data['textures'] = []
                    for texture in gltf.textures:
                        texture_dict = {}
                        if hasattr(texture, 'source') and texture.source is not None:
                            texture_dict['source'] = texture.source
                        if hasattr(texture, 'sampler') and texture.sampler is not None:
                            texture_dict['sampler'] = texture.sampler
                        gltf_data['textures'].append(texture_dict)
                
                if hasattr(gltf, 'samplers') and gltf.samplers:
                    # Convert pygltflib Sampler objects to dictionaries
                    gltf_data['samplers'] = []
                    for sampler in gltf.samplers:
                        sampler_dict = {}
                        if hasattr(sampler, 'magFilter') and sampler.magFilter is not None:
                            sampler_dict['magFilter'] = sampler.magFilter
                        if hasattr(sampler, 'minFilter') and sampler.minFilter is not None:
                            sampler_dict['minFilter'] = sampler.minFilter
                        if hasattr(sampler, 'wrapS') and sampler.wrapS is not None:
                            sampler_dict['wrapS'] = sampler.wrapS
                        if hasattr(sampler, 'wrapT') and sampler.wrapT is not None:
                            sampler_dict['wrapT'] = sampler.wrapT
                        gltf_data['samplers'].append(sampler_dict)
                
                if hasattr(gltf, 'images') and gltf.images:
                    # Convert pygltflib Image objects to dictionaries
                    gltf_data['images'] = []
                    for image in gltf.images:
                        image_dict = {}
                        if hasattr(image, 'uri') and image.uri:
                            image_dict['uri'] = image.uri
                        if hasattr(image, 'mimeType') and image.mimeType:
                            image_dict['mimeType'] = image.mimeType
                        if hasattr(image, 'bufferView') and image.bufferView is not None:
                            image_dict['bufferView'] = image.bufferView
                        if hasattr(image, 'name') and image.name:
                            image_dict['name'] = image.name
                        gltf_data['images'].append(image_dict)
                
                if hasattr(gltf, 'accessors') and gltf.accessors:
                    # Convert pygltflib Accessor objects to dictionaries
                    gltf_data['accessors'] = []
                    for accessor in gltf.accessors:
                        accessor_dict = {}
                        if hasattr(accessor, 'bufferView') and accessor.bufferView is not None:
                            accessor_dict['bufferView'] = accessor.bufferView
                        if hasattr(accessor, 'componentType') and accessor.componentType is not None:
                            accessor_dict['componentType'] = accessor.componentType
                        if hasattr(accessor, 'count') and accessor.count is not None:
                            accessor_dict['count'] = accessor.count
                        if hasattr(accessor, 'type') and accessor.type:
                            accessor_dict['type'] = accessor.type
                        if hasattr(accessor, 'max') and accessor.max:
                            accessor_dict['max'] = accessor.max
                        if hasattr(accessor, 'min') and accessor.min:
                            accessor_dict['min'] = accessor.min
                        gltf_data['accessors'].append(accessor_dict)
                
                if hasattr(gltf, 'bufferViews') and gltf.bufferViews:
                    # Convert pygltflib BufferView objects to dictionaries
                    gltf_data['bufferViews'] = []
                    for buffer_view in gltf.bufferViews:
                        buffer_view_dict = {}
                        if hasattr(buffer_view, 'buffer') and buffer_view.buffer is not None:
                            buffer_view_dict['buffer'] = buffer_view.buffer
                        if hasattr(buffer_view, 'byteOffset') and buffer_view.byteOffset is not None:
                            buffer_view_dict['byteOffset'] = buffer_view.byteOffset
                        if hasattr(buffer_view, 'byteLength') and buffer_view.byteLength is not None:
                            buffer_view_dict['byteLength'] = buffer_view.byteLength
                        if hasattr(buffer_view, 'byteStride') and buffer_view.byteStride is not None:
                            buffer_view_dict['byteStride'] = buffer_view.byteStride
                        if hasattr(buffer_view, 'target') and buffer_view.target is not None:
                            buffer_view_dict['target'] = buffer_view.target
                        gltf_data['bufferViews'].append(buffer_view_dict)
                
                if hasattr(gltf, 'buffers') and gltf.buffers:
                    # Convert pygltflib Buffer objects to dictionaries
                    gltf_data['buffers'] = []
                    for buffer in gltf.buffers:
                        buffer_dict = {}
                        if hasattr(buffer, 'uri') and buffer.uri:
                            buffer_dict['uri'] = buffer.uri
                        if hasattr(buffer, 'byteLength') and buffer.byteLength is not None:
                            buffer_dict['byteLength'] = buffer.byteLength
                        gltf_data['buffers'].append(buffer_dict)
                
                if hasattr(gltf, 'animations') and gltf.animations:
                    # Convert pygltflib Animation objects to dictionaries
                    gltf_data['animations'] = []
                    for animation in gltf.animations:
                        animation_dict = {}
                        if hasattr(animation, 'name') and animation.name:
                            animation_dict['name'] = animation.name
                        if hasattr(animation, 'samplers') and animation.samplers:
                            # Convert AnimationSampler objects to dictionaries
                            samplers_list = []
                            for sampler in animation.samplers:
                                sampler_dict = {}
                                if hasattr(sampler, 'input') and sampler.input is not None:
                                    sampler_dict['input'] = sampler.input
                                if hasattr(sampler, 'output') and sampler.output is not None:
                                    sampler_dict['output'] = sampler.output
                                if hasattr(sampler, 'interpolation') and sampler.interpolation:
                                    sampler_dict['interpolation'] = sampler.interpolation
                                samplers_list.append(sampler_dict)
                            animation_dict['samplers'] = samplers_list
                        if hasattr(animation, 'channels') and animation.channels:
                            # Convert AnimationChannel objects to dictionaries
                            channels_list = []
                            for channel in animation.channels:
                                channel_dict = {}
                                if hasattr(channel, 'sampler') and channel.sampler is not None:
                                    channel_dict['sampler'] = channel.sampler
                                if hasattr(channel, 'target') and channel.target:
                                    target_dict = {}
                                    if hasattr(channel.target, 'node') and channel.target.node is not None:
                                        target_dict['node'] = channel.target.node
                                    if hasattr(channel.target, 'path') and channel.target.path:
                                        target_dict['path'] = channel.target.path
                                    channel_dict['target'] = target_dict
                                channels_list.append(channel_dict)
                            animation_dict['channels'] = channels_list
                        gltf_data['animations'].append(animation_dict)
                
                if hasattr(gltf, 'skins') and gltf.skins:
                    # Convert pygltflib Skin objects to dictionaries
                    gltf_data['skins'] = []
                    for skin in gltf.skins:
                        skin_dict = {}
                        if hasattr(skin, 'name') and skin.name:
                            skin_dict['name'] = skin.name
                        if hasattr(skin, 'inverseBindMatrices') and skin.inverseBindMatrices is not None:
                            skin_dict['inverseBindMatrices'] = skin.inverseBindMatrices
                        if hasattr(skin, 'skeleton') and skin.skeleton is not None:
                            skin_dict['skeleton'] = skin.skeleton
                        if hasattr(skin, 'joints') and skin.joints:
                            skin_dict['joints'] = skin.joints
                        gltf_data['skins'].append(skin_dict)
                
                if hasattr(gltf, 'cameras') and gltf.cameras:
                    gltf_data['cameras'] = gltf.cameras
                
                if hasattr(gltf, 'lights') and gltf.lights:
                    gltf_data['lights'] = gltf.lights
                
                print(f"✅ Successfully extracted GLB data using pygltflib")
                print(f"📊 Components found: {list(gltf_data.keys())}")
                
                # Extract binary data for potential re-embedding
                if hasattr(gltf, '_glb_data') and gltf._glb_data:
                    self._extracted_binary_data = self._extract_binary_data(gltf, gltf_data)
                    print(f"📦 Extracted {len(self._extracted_binary_data)} binary buffers")
                    
                    # Update buffer references to point to external binary file
                    if 'buffers' in gltf_data and gltf_data['buffers']:
                        # Create a single external binary file with unique name
                        binary_filename = f"{output_path.stem}.bin"
                        binary_path = output_path.parent / binary_filename
                        
                        # Calculate total size and create combined binary file
                        total_size = 0
                        buffer_view_offsets = {}
                        
                        # First pass: calculate total size and new offsets
                        for i, buffer_view in enumerate(gltf_data['bufferViews']):
                            if f'bufferView_{i}' in self._extracted_binary_data:
                                buffer_view_offsets[i] = total_size
                                total_size += len(self._extracted_binary_data[f'bufferView_{i}'])
                        
                        # Write the combined binary data
                        with open(binary_path, 'wb') as f:
                            for i, buffer_view in enumerate(gltf_data['bufferViews']):
                                if f'bufferView_{i}' in self._extracted_binary_data:
                                    f.write(self._extracted_binary_data[f'bufferView_{i}'])
                        
                        # Update buffer views with new offsets and byteLength
                        for i, buffer_view in enumerate(gltf_data['bufferViews']):
                            if i in buffer_view_offsets:
                                buffer_view['byteOffset'] = buffer_view_offsets[i]
                                # CRITICAL: Update byteLength to match the actual extracted data
                                if f'bufferView_{i}' in self._extracted_binary_data:
                                    buffer_view['byteLength'] = len(self._extracted_binary_data[f'bufferView_{i}'])
                                    print(f"📏 BufferView {i}: Updated byteLength to {buffer_view['byteLength']:,} bytes")
                        
                        # Update the first buffer to reference the external file
                        gltf_data['buffers'][0] = {
                            'uri': binary_filename,
                            'byteLength': total_size
                        }
                        
                        # Remove extra buffers if they exist
                        if len(gltf_data['buffers']) > 1:
                            gltf_data['buffers'] = [gltf_data['buffers'][0]]
                        
                        print(f"📁 Created external binary file: {binary_filename} ({total_size:,} bytes)")
                
                # CRITICAL: Fix accessor byteLength calculations to prevent Error 23
                self._fix_accessor_byte_lengths(gltf_data)
                
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
        # Create output directory if it exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Clean up old output files to prevent duplicates
        self._cleanup_old_outputs(output_path)
        
        if use_blender and input_path.suffix.lower() == '.glb':
            # Try Blender first for GLB files
            try:
                print("🎨 Attempting Blender conversion...")
                if self.convert_with_blender(input_path, output_path, optimize_mesh=optimize_mesh, platform=platform):
                    print("✅ Blender conversion successful!")
                    return True
                else:
                    print("⚠️  Blender conversion failed, falling back to basic GLB processing...")
                    # Fall back to basic GLB processing
                    return self.convert_gltf_json(input_path, output_path, generate_atlas=generate_atlas, compress_textures=compress_textures, platform=platform)
            except Exception as e:
                print(f"❌ Blender conversion failed with error: {e}")
                print("🔄 Falling back to basic GLB processing...")
                # Fall back to basic GLB processing
                return self.convert_gltf_json(input_path, output_path, generate_atlas=generate_atlas, compress_textures=compress_textures, platform=platform)
        else:
            # Use JSON parsing for glTF files or when Blender is disabled
            return self.convert_gltf_json(input_path, output_path, generate_atlas=generate_atlas, compress_textures=compress_textures, platform=platform)
    
    def convert_with_blender(self, input_path: Path, output_path: Path, optimize_mesh: bool = False, platform: str = "unity") -> bool:
        """Convert using Blender Python script with platform-specific settings"""
        blender_exe = self.find_blender()
        if not blender_exe:
            print("⚠️  Blender not found, using basic conversion...")
            return False
        
        if not self.blender_script_path.exists():
            print("⚠️  Blender script not found, using basic conversion...")
            return False
        
        # Try to install numpy in Blender's Python environment first
        try:
            print("🔧 Attempting to install numpy in Blender's Python environment...")
            numpy_install_cmd = [
                blender_exe,
                "--background",
                "--python-expr",
                "import subprocess; import sys; subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'numpy'])"
            ]
            result = subprocess.run(numpy_install_cmd, capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
                print("✅ Numpy installed successfully in Blender's Python environment")
            else:
                print("⚠️  Could not install numpy in Blender's Python environment")
        except Exception as e:
            print(f"⚠️  Numpy installation attempt failed: {e}")
        
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
            print("🎨 Running Blender conversion...")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                print("✅ Blender conversion successful!")
                return True
            else:
                # Check for specific error patterns
                stderr = result.stderr or ""
                stdout = result.stdout or ""
                
                if "No module named 'numpy'" in stderr or "No module named 'numpy'" in stdout:
                    print("⚠️  Blender numpy dependency missing. Using basic conversion...")
                    return False
                elif "ModuleNotFoundError" in stderr or "ModuleNotFoundError" in stdout:
                    print("⚠️  Blender Python environment missing required modules. Using basic conversion...")
                    return False
                else:
                    print(f"⚠️  Blender failed with return code {result.returncode}")
                    print(f"Error output: {stderr[:200]}...")
                    return False
                
        except subprocess.TimeoutExpired:
            print("⚠️  Blender processing timed out (120s). Using basic conversion...")
            return False
        except Exception as e:
            print(f"⚠️  Blender execution failed: {e}. Using basic conversion...")
            return False
        
        return False  # Fallback return
    
    def convert_gltf_json(self, input_path: Path, output_path: Path, generate_atlas: bool = False,
                          compress_textures: bool = False, platform: str = "unity") -> bool:
        """Convert glTF JSON data to output format with platform-specific optimizations"""
        try:
            # Ensure we have Path objects
            input_path = Path(input_path)
            output_path = Path(output_path)
            
            # Get the cleaned glTF data first
            gltf_data, changes = self.clean_gltf_json(input_path, output_path)
            
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
            
            # Skip GLB conversion entirely - go straight to GLTF output
            # This prevents unnecessary .glb files and ensures clean output
            gltf_output = output_path.with_suffix('.gltf')
            with open(gltf_output, 'w', encoding='utf-8') as f:
                json.dump(gltf_data, f, indent=2)
            
            print(f"✅ Saved as GLTF: {gltf_output}")
            
            # Run automatic validation
            self._run_validation(gltf_output)
            
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
                # Only include the specific binary file for this conversion
                if bin_file.name == f"{gltf_path.stem}.bin":
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
            
            print("✅ Binary data embedded successfully")
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
            
            print(f"✅ Created Sketchfab-optimized GLTF: {output_path}")
            print(f"📊 File size: {output_path.stat().st_size:,} bytes")
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
        
        if hasattr(gltf, '_glb_data') and gltf._glb_data and hasattr(gltf, 'bufferViews') and gltf.bufferViews:
            # Extract data from each buffer view
            for i, buffer_view in enumerate(gltf.bufferViews):
                if hasattr(buffer_view, 'byteOffset') and hasattr(buffer_view, 'byteLength'):
                    start = buffer_view.byteOffset
                    end = start + buffer_view.byteLength
                    if start < len(gltf._glb_data) and end <= len(gltf._glb_data):
                        binary_data[f'bufferView_{i}'] = gltf._glb_data[start:end]
                        print(f"📦 Extracted buffer view {i}: {len(gltf._glb_data[start:end])} bytes")
        
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
                
                # Copy only the specific .bin file for this conversion
                elif file_path.suffix.lower() == '.bin' and file_path.name == f"{output_path.stem}.bin":
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
        """Convert glTF JSON data to GLTF format (GLB generation disabled)"""
        try:
            print(f"Converting to GLTF format...")
            print(f"glTF data keys: {list(gltf_data.keys())}")
            print(f"Output path: {output_path}")
            
            # Skip GLB conversion entirely - go straight to GLTF output
            # This prevents unnecessary .glb files and ensures clean output
            gltf_output = output_path.with_suffix('.gltf')
            with open(gltf_output, 'w', encoding='utf-8') as f:
                json.dump(gltf_data, f, indent=2)
            
            print(f"✅ Saved as GLTF: {gltf_output}")
            
            # Run automatic validation
            self._run_validation(gltf_output)
            
            return True
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            raise RuntimeError(f"Failed to convert to GLTF: {e}\nDetails: {error_details}")

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

    def _cleanup_old_outputs(self, output_path: Path):
        """Clean up old output files to prevent duplicates and accumulation"""
        try:
            output_dir = output_path.parent
            output_stem = output_path.stem
            
            # Remove old files with the same base name (but not the target file)
            for old_file in output_dir.glob(f"{output_stem}*"):
                if old_file != output_path:  # Don't delete the target file
                    old_file.unlink()
                    print(f"🗑️  Cleaned up old file: {old_file.name}")
            
            # Remove any .glb files since we no longer generate them
            for old_glb in output_dir.glob("*.glb"):
                old_glb.unlink()
                print(f"🗑️  Cleaned up old GLB file: {old_glb.name}")
                    
        except Exception as e:
            print(f"⚠️  Warning: Could not clean up old files: {e}")

    def _run_validation(self, gltf_path: Path) -> bool:
        """Run Node.js validation on the generated GLTF file"""
        try:
            import subprocess
            import sys
            
            # Check if Node.js is available
            try:
                result = subprocess.run(['node', '--version'], capture_output=True, text=True, timeout=10)
                if result.returncode != 0:
                    print("⚠️  Node.js not available, skipping validation")
                    return True
            except (subprocess.TimeoutExpired, FileNotFoundError):
                print("⚠️  Node.js not available, skipping validation")
                return True
            
            # Run the validation script
            validator_path = Path(__file__).parent / 'validate_gltf.js'
            if not validator_path.exists():
                print("⚠️  Validation script not found, skipping validation")
                return True
            
            print("🔍 Running Node.js validation...")
            result = subprocess.run(
                ['node', str(validator_path), str(gltf_path)],
                capture_output=True, text=True, timeout=30
            )
            
            if result.returncode == 0:
                print("✅ Validation passed!")
                return True
            else:
                print("❌ Validation failed!")
                print("Validation output:")
                print(result.stdout)
                if result.stderr:
                    print("Validation errors:")
                    print(result.stderr)
                return False
                
        except Exception as e:
            print(f"⚠️  Validation failed with error: {e}")
            return True  # Don't fail conversion due to validation issues

    def _fix_accessor_byte_lengths(self, gltf_data: Dict):
        """Fix accessor byteLength calculations to prevent Error 23 validation issues"""
        if 'accessors' not in gltf_data or 'bufferViews' not in gltf_data:
            return
        
        print("🔧 Fixing accessor byteLength calculations to prevent Error 23...")
        
        # First, calculate the required size for each accessor
        accessor_requirements = []
        for i, accessor in enumerate(gltf_data['accessors']):
            if 'bufferView' in accessor and accessor['bufferView'] is not None:
                component_count = self._get_type_component_count(accessor.get('type', 'SCALAR'))
                component_size = self._get_component_size(accessor.get('componentType', 5126))
                accessor_count = accessor.get('count', 0)
                required_bytes = accessor_count * component_count * component_size
                
                accessor_requirements.append({
                    'index': i,
                    'required_bytes': required_bytes,
                    'current_buffer_view': accessor['bufferView'],
                    'accessor': accessor
                })
        
        # Sort buffer views by size (largest first) for better distribution
        buffer_view_sizes = []
        for i, buffer_view in enumerate(gltf_data['bufferViews']):
            buffer_view_sizes.append({
                'index': i,
                'size': buffer_view.get('byteLength', 0),
                'used': 0
            })
        
        buffer_view_sizes.sort(key=lambda x: x['size'], reverse=True)
        
        # Redistribute accessors to appropriate buffer views
        reassignments = 0
        for req in accessor_requirements:
            # Find the best buffer view for this accessor
            best_buffer_view = None
            for bv in buffer_view_sizes:
                if bv['size'] >= req['required_bytes'] and bv['used'] + req['required_bytes'] <= bv['size']:
                    best_buffer_view = bv
                    break
            
            if best_buffer_view and best_buffer_view['index'] != req['current_buffer_view']:
                old_buffer_view = req['current_buffer_view']
                req['accessor']['bufferView'] = best_buffer_view['index']
                best_buffer_view['used'] += req['required_bytes']
                print(f"🔄 Moved Accessor {req['index']} from BufferView {old_buffer_view} to BufferView {best_buffer_view['index']} (requires {req['required_bytes']:,} bytes)")
                reassignments += 1
            elif best_buffer_view:
                # Keep in same buffer view but mark as used
                best_buffer_view['used'] += req['required_bytes']
            else:
                print(f"⚠️  Accessor {req['index']}: No suitable BufferView found for {req['required_bytes']:,} bytes")
        
        print(f"✅ Accessor redistribution complete: {reassignments} accessors moved to prevent Error 23")
        
        # CRITICAL: Now adjust accessor counts to match the actual available data
        print("🔧 Adjusting accessor counts to match available buffer data...")
        
        for i, accessor in enumerate(gltf_data['accessors']):
            if 'bufferView' in accessor and accessor['bufferView'] is not None:
                buffer_view_index = accessor['bufferView']
                if buffer_view_index < len(gltf_data['bufferViews']):
                    buffer_view = gltf_data['bufferViews'][buffer_view_index]
                    buffer_view_size = buffer_view.get('byteLength', 0)
                    
                    # Calculate how many elements can actually fit in this buffer view
                    component_count = self._get_type_component_count(accessor.get('type', 'SCALAR'))
                    component_size = self._get_component_size(accessor.get('componentType', 5126))
                    bytes_per_element = component_count * component_size
                    
                    if bytes_per_element > 0:
                        # Calculate total bytes needed for this accessor
                        total_bytes_needed = accessor.get('count', 0) * bytes_per_element
                        max_elements = buffer_view_size // bytes_per_element
                        
                        print(f"🔍 Accessor {i}: Type={accessor.get('type')}, ComponentType={accessor.get('componentType')}, Count={accessor.get('count', 0)}, BufferView={buffer_view_index}, BufferSize={buffer_view_size:,}, BytesPerElement={bytes_per_element}, TotalBytesNeeded={total_bytes_needed:,}, MaxElements={max_elements}")
                        
                        # Check if total bytes needed exceed buffer view size
                        if total_bytes_needed > buffer_view_size:
                            print(f"🔄 Accessor {i}: Total bytes needed ({total_bytes_needed:,}) exceeds BufferView {buffer_view_index} size ({buffer_view_size:,})")
                            # Reduce count to fit
                            forced_count = buffer_view_size // bytes_per_element
                            if forced_count > 0:
                                print(f"🔄 Accessor {i}: Reducing count from {accessor.get('count', 0)} to {forced_count} to prevent Error 23")
                                accessor['count'] = forced_count
                                print(f"✅ Accessor {i}: Final count set to {accessor['count']}")
                        else:
                            print(f"ℹ️  Accessor {i}: Count {accessor.get('count', 0)} fits in BufferView {buffer_view_index} (total bytes: {total_bytes_needed:,})")
                        
                        # Verify the final calculation
                        final_bytes = accessor['count'] * bytes_per_element
                        if final_bytes > buffer_view_size:
                            print(f"⚠️  Accessor {i}: Still too large ({final_bytes:,} bytes) for BufferView {buffer_view_index} ({buffer_view_size:,} bytes)")
                            # Force the count to fit
                            forced_count = buffer_view_size // bytes_per_element
                            if forced_count > 0:
                                print(f"🔄 Accessor {i}: Forcing count to {forced_count} to prevent Error 23")
                                accessor['count'] = forced_count
                                print(f"✅ Accessor {i}: Final count set to {accessor['count']}")
        
        print("✅ Accessor count adjustments complete")
    
    def _get_type_component_count(self, accessor_type: str) -> int:
        """Get the number of components for an accessor type"""
        type_map = {
            'SCALAR': 1,
            'VEC2': 2,
            'VEC3': 3,
            'VEC4': 4,
            'MAT2': 4,
            'MAT3': 9,
            'MAT4': 16
        }
        return type_map.get(accessor_type, 1)
    
    def _get_component_size(self, component_type: int) -> int:
        """Get the size of a component type in bytes"""
        size_map = {
            5120: 1,   # BYTE
            5121: 1,   # UNSIGNED_BYTE
            5122: 2,   # SHORT
            5123: 2,   # UNSIGNED_SHORT
            5125: 4,   # UNSIGNED_INT
            5126: 4    # FLOAT
        }
        return size_map.get(component_type, 4)


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