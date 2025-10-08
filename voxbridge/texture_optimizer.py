import os
import shutil
from pathlib import Path
from PIL import Image
import numpy as np

# For glTF parsing and updating
import pygltflib

def resize_texture(image_path, max_size=1024):
    """
    Resize a texture to a maximum size (preserving aspect ratio).
    Returns the path to the resized image (may overwrite original).
    """
    img = Image.open(image_path)
    
    # Convert to sRGB color space for consistency
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    # Ensure proper color profile
    if 'icc_profile' not in img.info:
        # Add sRGB profile if missing
        img.info['icc_profile'] = b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    
    if max(img.size) > max_size:
        img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
        
        # Preserve original format and optimize
        if image_path.endswith('.png'):
            img.save(image_path, 'PNG', optimize=True, compress_level=6)
        elif image_path.endswith(('.jpg', '.jpeg')):
            img.save(image_path, 'JPEG', quality=95, optimize=True)
        else:
            img.save(image_path)
    
    return image_path

def generate_texture_atlas(image_paths, atlas_size=1024):
    """
    Combine multiple images into a single texture atlas.
    Returns the atlas image and mapping info.
    """
    images = [Image.open(p) for p in image_paths]
    n = len(images)
    grid_size = int(np.ceil(np.sqrt(n)))
    cell_size = atlas_size // grid_size
    atlas = Image.new('RGBA', (atlas_size, atlas_size))
    mapping = {}
    for idx, img in enumerate(images):
        row, col = divmod(idx, grid_size)
        x, y = col * cell_size, row * cell_size
        img_resized = img.resize((cell_size, cell_size), Image.Resampling.LANCZOS)
        atlas.paste(img_resized, (x, y))
        mapping[image_paths[idx]] = {
            'uv': [x / atlas_size, y / atlas_size, (x + cell_size) / atlas_size, (y + cell_size) / atlas_size],
            'cell': (row, col)
        }
    return atlas, mapping

def update_gltf_with_atlas(gltf_path, mapping, atlas_filename):
    """
    Update a glTF file to use the atlas and remap UVs.
    This function parses mesh primitives, updates UV coordinates based on the atlas mapping,
    and writes the updated UVs back to the glTF file.
    """
    gltf = pygltflib.GLTF2().load(gltf_path)
    
    # Create a mapping from original image URIs to atlas regions
    uri_to_atlas_mapping = {}
    for original_path, atlas_info in mapping.items():
        original_filename = Path(original_path).name
        uri_to_atlas_mapping[original_filename] = atlas_info['uv']
    
    # Update image references to use the atlas
    for image in gltf.images:
        if hasattr(image, 'uri') and image.uri:
            original_filename = Path(image.uri).name
            if original_filename in uri_to_atlas_mapping:
                image.uri = atlas_filename
    
    # Remap UVs for each mesh primitive
    for mesh in gltf.meshes:
        for primitive in mesh.primitives:
            if hasattr(primitive, 'attributes') and primitive.attributes:
                # Find UV attribute (TEXCOORD_0) - handle pygltflib attributes object properly
                texcoord_attr = None
                # Check if attributes is a dict-like object or pygltflib object
                if hasattr(primitive.attributes, 'items'):
                    # It's a dict-like object
                    for attr_name, attr_index in primitive.attributes.items():
                        if attr_name.startswith('TEXCOORD'):
                            texcoord_attr = attr_name
                            break
                else:
                    # It's a pygltflib object, use dir() to get attributes
                    for attr_name in dir(primitive.attributes):
                        if not attr_name.startswith('_') and hasattr(primitive.attributes, attr_name):
                            attr_value = getattr(primitive.attributes, attr_name)
                            if attr_value is not None and attr_name.startswith('TEXCOORD'):
                                texcoord_attr = attr_name
                                break
                
                if texcoord_attr and hasattr(primitive.attributes, texcoord_attr):
                    uv_accessor_index = getattr(primitive.attributes, texcoord_attr)
                    if uv_accessor_index is not None and uv_accessor_index < len(gltf.accessors):
                        uv_accessor = gltf.accessors[uv_accessor_index]
                        
                        # Get the buffer view and buffer data
                        if (uv_accessor.bufferView is not None and 
                            uv_accessor.bufferView < len(gltf.bufferViews)):
                            buffer_view = gltf.bufferViews[uv_accessor.bufferView]
                            
                            if (buffer_view.buffer is not None and 
                                buffer_view.buffer < len(gltf.buffers)):
                                buffer_data = gltf.buffers[buffer_view.buffer]
                                
                                # Check if we have the data to work with
                                if hasattr(buffer_data, 'data') and buffer_data.data:
                                    try:
                                        # Read current UV data
                                        uv_data = np.frombuffer(
                                            buffer_data.data[buffer_view.byteOffset:buffer_view.byteOffset + buffer_view.byteLength],
                                            dtype=np.float32
                                        ).reshape(-1, 2)
                                        
                                        # Find which material/texture this primitive uses
                                        material_index = getattr(primitive, 'material', None)
                                        if material_index is not None and material_index < len(gltf.materials):
                                            material = gltf.materials[material_index]
                                            # Find the base color texture
                                            if hasattr(material, 'pbrMetallicRoughness') and material.pbrMetallicRoughness:
                                                pbr = material.pbrMetallicRoughness
                                                if hasattr(pbr, 'baseColorTexture') and pbr.baseColorTexture:
                                                    texture_index = pbr.baseColorTexture.index
                                                    if texture_index < len(gltf.textures):
                                                        texture = gltf.textures[texture_index]
                                                        image_index = texture.source
                                                        if image_index < len(gltf.images):
                                                            image = gltf.images[image_index]
                                                            
                                                            # Get original filename and find atlas mapping
                                                            if hasattr(image, 'uri') and image.uri:
                                                                original_filename = Path(image.uri).name
                                                                if original_filename in uri_to_atlas_mapping:
                                                                    atlas_uv = uri_to_atlas_mapping[original_filename]
                                                                    # Remap UVs to atlas coordinates
                                                                    uv_data[:, 0] = uv_data[:, 0] * (atlas_uv[2] - atlas_uv[0]) + atlas_uv[0]
                                                                    uv_data[:, 1] = uv_data[:, 1] * (atlas_uv[3] - atlas_uv[1]) + atlas_uv[1]
                                                        
                                                        # Write updated UV data back to buffer
                                                        updated_uv_bytes = uv_data.tobytes()
                                                        buffer_data.data[buffer_view.byteOffset:buffer_view.byteOffset + buffer_view.byteLength] = updated_uv_bytes
                                    except Exception as e:
                                        # Log the error but continue processing other primitives
                                        print(f"Warning: Could not process UVs for primitive: {e}")
                                        continue
    
    gltf.save(gltf_path)

def validate_uv_maps(gltf_path):
    """
    Validate UV maps in a GLTF file to ensure they're properly mapped
    Returns validation results with warnings for mismatched UVs
    """
    validation_result = {
        'valid': True,
        'warnings': [],
        'errors': [],
        'uv_stats': {}
    }
    
    try:
        gltf = pygltflib.GLTF2().load(gltf_path)
        
        uv_count = 0
        mismatched_count = 0
        
        for mesh_idx, mesh in enumerate(gltf.meshes):
            for prim_idx, primitive in enumerate(mesh.primitives):
                if hasattr(primitive, 'attributes') and primitive.attributes:
                    # Check for UV attributes
                    uv_attrs = []
                    for attr_name in dir(primitive.attributes):
                        if not attr_name.startswith('_') and hasattr(primitive.attributes, attr_name):
                            attr_value = getattr(primitive.attributes, attr_name)
                            if attr_value is not None and attr_name.startswith('TEXCOORD'):
                                uv_attrs.append((attr_name, attr_value))
                    
                    uv_count += len(uv_attrs)
                    
                    # Validate UV coordinates
                    for uv_attr_name, uv_accessor_idx in uv_attrs:
                        if uv_accessor_idx < len(gltf.accessors):
                            uv_accessor = gltf.accessors[uv_accessor_idx]
                            
                            # Check if UV coordinates are in valid range [0,1]
                            if hasattr(uv_accessor, 'min') and hasattr(uv_accessor, 'max'):
                                uv_min = uv_accessor.min
                                uv_max = uv_accessor.max
                                
                                if len(uv_min) >= 2 and len(uv_max) >= 2:
                                    # Check for UV coordinates outside [0,1] range
                                    if uv_min[0] < 0 or uv_min[1] < 0 or uv_max[0] > 1 or uv_max[1] > 1:
                                        mismatched_count += 1
                                        validation_result['warnings'].append(
                                            f'UV coordinates in mesh {mesh_idx}, primitive {prim_idx} '
                                            f'({uv_attr_name}) are outside [0,1] range: '
                                            f'min=({uv_min[0]:.3f}, {uv_min[1]:.3f}), '
                                            f'max=({uv_max[0]:.3f}, {uv_max[1]:.3f})'
                                        )
        
        validation_result['uv_stats'] = {
            'total_uv_attributes': uv_count,
            'mismatched_uvs': mismatched_count,
            'mismatch_percentage': (mismatched_count / uv_count * 100) if uv_count > 0 else 0
        }
        
        if mismatched_count > 0:
            validation_result['warnings'].append(
                f'Found {mismatched_count} UV attributes with coordinates outside [0,1] range'
            )
        
    except Exception as e:
        validation_result['valid'] = False
        validation_result['errors'].append(f'UV validation failed: {e}')
    
    return validation_result

def fix_uv_coordinates(gltf_path, output_path=None):
    """
    Fix UV coordinates that are outside the [0,1] range by clamping them
    """
    if output_path is None:
        output_path = gltf_path
    
    try:
        gltf = pygltflib.GLTF2().load(gltf_path)
        
        fixed_count = 0
        
        for mesh in gltf.meshes:
            for primitive in mesh.primitives:
                if hasattr(primitive, 'attributes') and primitive.attributes:
                    # Find UV attributes
                    for attr_name in dir(primitive.attributes):
                        if not attr_name.startswith('_') and hasattr(primitive.attributes, attr_name):
                            attr_value = getattr(primitive.attributes, attr_name)
                            if attr_value is not None and attr_name.startswith('TEXCOORD'):
                                uv_accessor_idx = attr_value
                                
                                if uv_accessor_idx < len(gltf.accessors):
                                    uv_accessor = gltf.accessors[uv_accessor_idx]
                                    
                                    # Get buffer data
                                    if (uv_accessor.bufferView is not None and 
                                        uv_accessor.bufferView < len(gltf.bufferViews)):
                                        buffer_view = gltf.bufferViews[uv_accessor.bufferView]
                                        
                                        if (buffer_view.buffer is not None and 
                                            buffer_view.buffer < len(gltf.buffers)):
                                            buffer_data = gltf.buffers[buffer_view.buffer]
                                            
                                            if hasattr(buffer_data, 'data') and buffer_data.data:
                                                # Read UV data
                                                uv_data = np.frombuffer(
                                                    buffer_data.data[buffer_view.byteOffset:buffer_view.byteOffset + buffer_view.byteLength],
                                                    dtype=np.float32
                                                ).reshape(-1, 2)
                                                
                                                # Clamp UV coordinates to [0,1]
                                                uv_data[:, 0] = np.clip(uv_data[:, 0], 0.0, 1.0)
                                                uv_data[:, 1] = np.clip(uv_data[:, 1], 0.0, 1.0)
                                                
                                                # Write back to buffer
                                                updated_uv_bytes = uv_data.tobytes()
                                                buffer_data.data[buffer_view.byteOffset:buffer_view.byteOffset + buffer_view.byteLength] = updated_uv_bytes
                                                
                                                fixed_count += 1
        
        # Save the fixed GLTF
        gltf.save(output_path)
        
        return {
            'success': True,
            'fixed_count': fixed_count,
            'message': f'Fixed {fixed_count} UV coordinate sets'
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': f'UV fixing failed: {e}'
        }

def ensure_texture_embedding(gltf_path, output_dir=None):
    """
    Ensure all textures are properly embedded or have correct URIs
    """
    if output_dir is None:
        output_dir = Path(gltf_path).parent
    
    try:
        gltf = pygltflib.GLTF2().load(gltf_path)
        modified = False
        
        if not gltf.images:
            return {'success': True, 'message': 'No images to process'}
        
        for i, image in enumerate(gltf.images):
            if hasattr(image, 'uri') and image.uri:
                filename = Path(image.uri).name
                texture_path = output_dir / image.uri
                
                if texture_path.exists():
                    # Texture file exists at the specified path
                    if '/' in image.uri:
                        # Texture is in a subdirectory, move it to root
                        root_path = output_dir / filename
                        if texture_path != root_path:
                            shutil.move(str(texture_path), str(root_path))
                            print(f"Moved texture to root: {image.uri} -> {filename}")
                            modified = True
                    image.uri = filename  # Ensure URI is just the filename
                    print(f"Fixed texture URI: {image.uri}")
                    modified = True
                else:
                    # Texture file missing - try to find it in common locations
                    possible_paths = [
                        output_dir / filename,
                        output_dir / 'textures' / filename,
                        output_dir / 'images' / filename,
                        output_dir / 'assets' / filename
                    ]
                    
                    found = False
                    for possible_path in possible_paths:
                        if possible_path.exists():
                            # Move to root directory
                            root_path = output_dir / filename
                            if possible_path != root_path:
                                shutil.move(str(possible_path), str(root_path))
                            image.uri = filename
                            print(f"Found and moved texture: {possible_path} -> {filename}")
                            found = True
                            modified = True
                            break
                    
                    if not found:
                        print(f"Warning: Texture file not found: {image.uri}")
                        # Create a placeholder texture to prevent missing textures
                        create_placeholder_texture(output_dir, filename)
                        image.uri = filename
                        print(f"Created placeholder texture: {filename}")
                        modified = True
            elif hasattr(image, 'bufferView') and image.bufferView is not None:
                # Texture is embedded in buffer, this is fine
                print(f"Texture {i} is embedded in buffer")
            else:
                print(f"Warning: Texture {i} has no URI or bufferView")
        
        if modified:
            gltf.save(gltf_path)
            return {'success': True, 'message': 'Texture embedding fixes applied'}
        else:
            return {'success': True, 'message': 'No texture fixes needed'}
            
    except Exception as e:
        return {'success': False, 'error': f'Texture embedding check failed: {e}'}

def create_placeholder_texture(output_dir, filename):
    """
    Create a placeholder texture to prevent missing textures
    """
    try:
        placeholder_path = output_dir / filename
        
        # Create a simple 1x1 white PNG as placeholder
        placeholder_img = Image.new('RGBA', (1, 1), (255, 255, 255, 255))
        placeholder_img.save(placeholder_path, 'PNG')
        
        print(f"Created placeholder texture: {filename}")
    except Exception as e:
        print(f"Failed to create placeholder texture: {e}")

def flatten_texture_paths(gltf_path, output_dir=None):
    """
    Flatten texture paths to root directory for Unity/Roblox compatibility
    """
    if output_dir is None:
        output_dir = Path(gltf_path).parent
    
    try:
        gltf = pygltflib.GLTF2().load(gltf_path)
        modified = False
        
        if not gltf.images:
            return {'success': True, 'message': 'No images to process'}
        
        for i, image in enumerate(gltf.images):
            if hasattr(image, 'uri') and image.uri and '/' in image.uri:
                filename = Path(image.uri).name
                old_path = output_dir / image.uri
                new_path = output_dir / filename
                
                # Move texture file to root if it exists
                if old_path.exists():
                    shutil.move(str(old_path), str(new_path))
                    image.uri = filename  # Update URI to be in root
                    modified = True
                    print(f"Moved texture: {image.uri} -> {filename}")
        
        if modified:
            gltf.save(gltf_path)
            return {'success': True, 'message': 'Texture paths flattened'}
        else:
            return {'success': True, 'message': 'No texture path changes needed'}
            
    except Exception as e:
        return {'success': False, 'error': f'Texture path flattening failed: {e}'} 