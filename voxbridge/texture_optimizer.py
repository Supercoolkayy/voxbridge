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
        img.thumbnail((max_size, max_size), Image.ANTIALIAS)
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
        img_resized = img.resize((cell_size, cell_size), Image.ANTIALIAS)
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
                # Find UV attribute (TEXCOORD_0)
                texcoord_attr = None
                for attr_name, attr_index in primitive.attributes.items():
                    if attr_name.startswith('TEXCOORD'):
                        texcoord_attr = attr_name
                        break
                
                if texcoord_attr and texcoord_attr in primitive.attributes:
                    uv_accessor_index = primitive.attributes[texcoord_attr]
                    uv_accessor = gltf.accessors[uv_accessor_index]
                    
                    # Get the buffer view and buffer data
                    buffer_view = gltf.bufferViews[uv_accessor.bufferView]
                    buffer_data = gltf.buffers[buffer_view.buffer]
                    
                    # Read current UV data
                    uv_data = np.frombuffer(
                        buffer_data.data[buffer_view.byteOffset:buffer_view.byteOffset + buffer_view.byteLength],
                        dtype=np.float32
                    ).reshape(-1, 2)
                    
                    # Find which material/texture this primitive uses
                    material_index = primitive.material if hasattr(primitive, 'material') else None
                    if material_index is not None:
                        material = gltf.materials[material_index]
                        # Find the base color texture
                        if hasattr(material, 'pbrMetallicRoughness') and material.pbrMetallicRoughness:
                            pbr = material.pbrMetallicRoughness
                            if hasattr(pbr, 'baseColorTexture') and pbr.baseColorTexture:
                                texture_index = pbr.baseColorTexture.index
                                texture = gltf.textures[texture_index]
                                image_index = texture.source
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
    
    gltf.save(gltf_path) 