"""
GLTF/GLB complexity detection utilities
Detects whether a GLTF/GLB file is static or complex (animations, skins, morph targets)
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

def is_complex_gltf(input_path: Path) -> Dict[str, Any]:
    """
    Detect if a GLTF/GLB file is complex (has animations, skins, morph targets, etc.)
    
    Args:
        input_path: Path to the GLTF/GLB file
        
    Returns:
        Dict containing:
        - is_complex: bool - whether the file is complex
        - features: List[str] - list of complex features found
        - details: Dict - detailed analysis results
    """
    try:
        # Load the GLTF file
        if input_path.suffix.lower() == '.glb':
            gltf_data = _load_glb(input_path)
        else:
            gltf_data = _load_gltf(input_path)
        
        if not gltf_data:
            return {
                'is_complex': False,
                'features': [],
                'details': {'error': 'Failed to load GLTF file'}
            }
        
        features = []
        details = {}
        
        # Check for animations
        animations = gltf_data.get('animations', [])
        if animations:
            features.append('animations')
            details['animation_count'] = len(animations)
            details['animations'] = [anim.get('name', f'anim_{i}') for i, anim in enumerate(animations)]
        
        # Check for skins
        skins = gltf_data.get('skins', [])
        if skins:
            features.append('skins')
            details['skin_count'] = len(skins)
            details['skins'] = [skin.get('name', f'skin_{i}') for i, skin in enumerate(skins)]
        
        # Check for morph targets in primitives
        morph_targets = _check_morph_targets(gltf_data)
        if morph_targets:
            features.append('morph_targets')
            details['morph_target_count'] = morph_targets
        
        # Check for extensions
        extensions_used = gltf_data.get('extensionsUsed', [])
        extensions_required = gltf_data.get('extensionsRequired', [])
        
        complex_extensions = [
            'KHR_animation_pipeline',
            'KHR_draco_mesh_compression',
            'KHR_materials_pbrSpecularGlossiness',
            'KHR_materials_unlit',
            'KHR_texture_transform',
            'KHR_mesh_quantization',
            'EXT_meshopt_compression',
            'KHR_lights_punctual',
            'KHR_materials_clearcoat',
            'KHR_materials_emissive_strength',
            'KHR_materials_ior',
            'KHR_materials_iridescence',
            'KHR_materials_sheen',
            'KHR_materials_specular',
            'KHR_materials_transmission',
            'KHR_materials_volume',
            'KHR_texture_basisu',
            'KHR_texture_ktx2'
        ]
        
        found_extensions = []
        for ext in extensions_used + extensions_required:
            if ext in complex_extensions:
                found_extensions.append(ext)
        
        if found_extensions:
            features.append('complex_extensions')
            details['extensions'] = found_extensions
        
        # Check for complex materials
        materials = gltf_data.get('materials', [])
        complex_materials = _check_complex_materials(materials)
        if complex_materials:
            features.append('complex_materials')
            details['complex_material_count'] = complex_materials
        
        # Check for multiple scenes or complex scene structure
        scenes = gltf_data.get('scenes', [])
        if len(scenes) > 1:
            features.append('multiple_scenes')
            details['scene_count'] = len(scenes)
        
        # Check for cameras and lights (indicates complex scene)
        cameras = gltf_data.get('cameras', [])
        lights = gltf_data.get('extensions', {}).get('KHR_lights_punctual', {}).get('lights', [])
        
        if cameras or lights:
            features.append('scene_objects')
            details['camera_count'] = len(cameras)
            details['light_count'] = len(lights)
        
        # Determine if complex based on features found
        is_complex = len(features) > 0
        
        return {
            'is_complex': is_complex,
            'features': features,
            'details': details
        }
        
    except Exception as e:
        logger.error(f"Error detecting GLTF complexity: {e}")
        return {
            'is_complex': False,
            'features': [],
            'details': {'error': str(e)}
        }

def _load_glb(file_path: Path) -> Optional[Dict[str, Any]]:
    """Load a GLB file and extract the JSON part"""
    try:
        import pygltflib
        
        gltf = pygltflib.GLTF2().load(str(file_path))
        # Convert to dict format
        return gltf.to_dict()
    except Exception as e:
        logger.error(f"Error loading GLB file {file_path}: {e}")
        return None

def _load_gltf(file_path: Path) -> Optional[Dict[str, Any]]:
    """Load a GLTF file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading GLTF file {file_path}: {e}")
        return None

def _check_morph_targets(gltf_data: Dict[str, Any]) -> int:
    """Check for morph targets in primitives"""
    morph_count = 0
    
    meshes = gltf_data.get('meshes', [])
    for mesh in meshes:
        primitives = mesh.get('primitives', [])
        for primitive in primitives:
            targets = primitive.get('targets', [])
            if targets:
                morph_count += len(targets)
    
    return morph_count

def _check_complex_materials(materials: List[Dict[str, Any]]) -> int:
    """Check for complex materials (PBR, textures, etc.)"""
    complex_count = 0
    
    for material in materials:
        # Check for PBR material properties
        pbr = material.get('pbrMetallicRoughness', {})
        if pbr:
            # Check for textures
            if any(pbr.get(key) for key in ['baseColorTexture', 'metallicRoughnessTexture']):
                complex_count += 1
                continue
        
        # Check for other material properties
        if any(material.get(key) for key in ['normalTexture', 'occlusionTexture', 'emissiveTexture']):
            complex_count += 1
            continue
        
        # Check for extensions
        extensions = material.get('extensions', {})
        if extensions:
            complex_count += 1
    
    return complex_count

def get_file_stats(input_path: Path) -> Dict[str, Any]:
    """
    Get basic statistics about a GLTF/GLB file
    
    Args:
        input_path: Path to the GLTF/GLB file
        
    Returns:
        Dict containing file statistics
    """
    try:
        if input_path.suffix.lower() == '.glb':
            gltf_data = _load_glb(input_path)
        else:
            gltf_data = _load_gltf(input_path)
        
        if not gltf_data:
            return {'error': 'Failed to load GLTF file'}
        
        stats = {
            'file_size': input_path.stat().st_size,
            'meshes': len(gltf_data.get('meshes', [])),
            'materials': len(gltf_data.get('materials', [])),
            'textures': len(gltf_data.get('textures', [])),
            'nodes': len(gltf_data.get('nodes', [])),
            'scenes': len(gltf_data.get('scenes', [])),
            'animations': len(gltf_data.get('animations', [])),
            'skins': len(gltf_data.get('skins', [])),
            'cameras': len(gltf_data.get('cameras', [])),
            'extensions_used': len(gltf_data.get('extensionsUsed', [])),
            'extensions_required': len(gltf_data.get('extensionsRequired', []))
        }
        
        # Calculate triangle count
        total_triangles = 0
        meshes = gltf_data.get('meshes', [])
        for mesh in meshes:
            primitives = mesh.get('primitives', [])
            for primitive in primitives:
                # This is a rough estimate - actual count would require accessor analysis
                if 'indices' in primitive:
                    total_triangles += 1000  # Rough estimate
                else:
                    # Non-indexed geometry
                    positions = primitive.get('attributes', {}).get('POSITION')
                    if positions:
                        total_triangles += 1000  # Rough estimate
        
        stats['triangles_estimated'] = total_triangles
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting file stats: {e}")
        return {'error': str(e)}
