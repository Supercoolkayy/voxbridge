import os
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
    if max(img.size) > max_size:
        img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
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