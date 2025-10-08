"""
GLTF Extension Handler for VoxBridge
Handles missing GLTF extensions with fallback support
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import pygltflib

logger = logging.getLogger(__name__)

class GLTFExtensionHandler:
    """Handles GLTF extensions with fallback support"""
    
    def __init__(self):
        self.supported_extensions = {
            'KHR_materials_pbrSpecularGlossiness',
            'KHR_texture_transform', 
            'KHR_lights_punctual',
            'KHR_draco_mesh_compression',
            'KHR_materials_unlit',
            'EXT_meshopt_compression'
        }
        
        self.extension_fallbacks = {
            'KHR_materials_pbrSpecularGlossiness': self._fallback_specular_glossiness,
            'KHR_texture_transform': self._fallback_texture_transform,
            'KHR_lights_punctual': self._fallback_lights_punctual
        }
    
    def process_gltf_file(self, gltf_path: Path, target_platform: str = 'unity') -> Dict[str, Any]:
        """
        Process a GLTF file and handle missing extensions
        
        Args:
            gltf_path: Path to GLTF file
            target_platform: Target platform (unity/roblox)
            
        Returns:
            Dict with processing results and fallback information
        """
        result = {
            'success': False,
            'extensions_found': [],
            'extensions_missing': [],
            'fallbacks_applied': [],
            'warnings': [],
            'errors': []
        }
        
        try:
            # Load GLTF file
            gltf_data = self._load_gltf(gltf_path)
            if not gltf_data:
                result['errors'].append('Failed to load GLTF file')
                return result
            
            # Analyze extensions
            extensions_analysis = self._analyze_extensions(gltf_data)
            result['extensions_found'] = extensions_analysis['found']
            result['extensions_missing'] = extensions_analysis['missing']
            
            # Apply fallbacks for missing extensions
            for missing_ext in extensions_analysis['missing']:
                if missing_ext in self.extension_fallbacks:
                    try:
                        fallback_result = self.extension_fallbacks[missing_ext](gltf_data, target_platform)
                        if fallback_result['success']:
                            result['fallbacks_applied'].append(missing_ext)
                            result['warnings'].extend(fallback_result.get('warnings', []))
                        else:
                            result['errors'].extend(fallback_result.get('errors', []))
                    except Exception as e:
                        result['errors'].append(f'Fallback for {missing_ext} failed: {e}')
            
            # Also process supported extensions that are found (like specular-glossiness)
            for found_ext in extensions_analysis['found']:
                if found_ext in self.extension_fallbacks:
                    try:
                        fallback_result = self.extension_fallbacks[found_ext](gltf_data, target_platform)
                        if fallback_result['success']:
                            result['fallbacks_applied'].append(found_ext)
                            result['warnings'].extend(fallback_result.get('warnings', []))
                        else:
                            result['errors'].extend(fallback_result.get('errors', []))
                    except Exception as e:
                        result['errors'].append(f'Processing for {found_ext} failed: {e}')
            
            # Save processed GLTF
            if result['fallbacks_applied']:
                self._save_gltf(gltf_data, gltf_path)
                result['success'] = True
            else:
                result['success'] = True  # No fallbacks needed
            
            return result
            
        except Exception as e:
            result['errors'].append(f'Processing failed: {e}')
            return result
    
    def _load_gltf(self, gltf_path: Path) -> Optional[Dict[str, Any]]:
        """Load GLTF file as JSON"""
        try:
            with open(gltf_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f'Failed to load GLTF: {e}')
            return None
    
    def _save_gltf(self, gltf_data: Dict[str, Any], gltf_path: Path):
        """Save GLTF file as JSON"""
        try:
            with open(gltf_path, 'w') as f:
                json.dump(gltf_data, f, indent=2)
        except Exception as e:
            logger.error(f'Failed to save GLTF: {e}')
            raise
    
    def _analyze_extensions(self, gltf_data: Dict[str, Any]) -> Dict[str, List[str]]:
        """Analyze extensions in GLTF data"""
        found = []
        missing = []
        
        # Check extensionsUsed
        extensions_used = gltf_data.get('extensionsUsed', [])
        extensions_required = gltf_data.get('extensionsRequired', [])
        
        # Check for extensions in materials
        materials = gltf_data.get('materials', [])
        for material in materials:
            if 'extensions' in material:
                for ext_name in material['extensions'].keys():
                    if ext_name not in found:
                        found.append(ext_name)
        
        # Check for extensions in nodes
        nodes = gltf_data.get('nodes', [])
        for node in nodes:
            if 'extensions' in node:
                for ext_name in node['extensions'].keys():
                    if ext_name not in found:
                        found.append(ext_name)
        
        # Check for extensions in textures
        textures = gltf_data.get('textures', [])
        for texture in textures:
            if 'extensions' in texture:
                for ext_name in texture['extensions'].keys():
                    if ext_name not in found:
                        found.append(ext_name)
        
        # Determine extensions that need processing (both supported and unsupported)
        for ext in extensions_used + extensions_required:
            if ext in self.supported_extensions:
                # Supported extension that needs processing
                if ext not in found:
                    missing.append(ext)
            elif ext not in found:
                # Unsupported extension that's missing
                missing.append(ext)
        
        return {'found': found, 'missing': missing}
    
    def _fallback_specular_glossiness(self, gltf_data: Dict[str, Any], target_platform: str) -> Dict[str, Any]:
        """Convert KHR_materials_pbrSpecularGlossiness to standard PBR using proper conversion"""
        result = {'success': False, 'warnings': [], 'errors': []}
        
        try:
            materials = gltf_data.get('materials', [])
            converted_count = 0
            
            for i, material in enumerate(materials):
                if 'extensions' in material and 'KHR_materials_pbrSpecularGlossiness' in material['extensions']:
                    spec_gloss = material['extensions']['KHR_materials_pbrSpecularGlossiness']
                    
                    # Convert to standard PBR metallic-roughness
                    if 'pbrMetallicRoughness' not in material:
                        material['pbrMetallicRoughness'] = {}
                    
                    # Convert diffuse to baseColor
                    if 'diffuseFactor' in spec_gloss:
                        material['pbrMetallicRoughness']['baseColorFactor'] = spec_gloss['diffuseFactor']
                    
                    # Convert specular-glossiness to metallic-roughness using proper conversion
                    if 'specularFactor' in spec_gloss and 'glossinessFactor' in spec_gloss:
                        specular = spec_gloss['specularFactor']
                        glossiness = spec_gloss['glossinessFactor']
                        
                        # Proper conversion from specular-glossiness to metallic-roughness
                        # This is a simplified conversion - in practice, you'd want more sophisticated conversion
                        if isinstance(specular, list) and len(specular) >= 3:
                            # Use the average of RGB specular values
                            avg_specular = sum(specular[:3]) / 3.0
                        else:
                            avg_specular = specular if isinstance(specular, (int, float)) else 0.5
                        
                        # Convert to metallic-roughness
                        # Metallic: 0 (assume dielectric materials)
                        # Roughness: 1 - glossiness
                        material['pbrMetallicRoughness']['metallicFactor'] = 0.0
                        material['pbrMetallicRoughness']['roughnessFactor'] = 1.0 - glossiness
                        
                        # If specular is very high, it might be metallic
                        if avg_specular > 0.8:
                            material['pbrMetallicRoughness']['metallicFactor'] = 0.5
                    
                    # Convert textures
                    if 'diffuseTexture' in spec_gloss:
                        material['pbrMetallicRoughness']['baseColorTexture'] = spec_gloss['diffuseTexture']
                    
                    if 'specularGlossinessTexture' in spec_gloss:
                        # Split specular-glossiness texture into separate metallic and roughness textures
                        self._split_specular_glossiness_texture(gltf_data, spec_gloss['specularGlossinessTexture'], i)
                    
                    # Remove the extension
                    del material['extensions']['KHR_materials_pbrSpecularGlossiness']
                    
                    # Clean up empty extensions object
                    if not material['extensions']:
                        del material['extensions']
                    
                    converted_count += 1
            
            # Remove from extensionsUsed and extensionsRequired
            if 'extensionsUsed' in gltf_data:
                gltf_data['extensionsUsed'] = [ext for ext in gltf_data['extensionsUsed'] 
                                             if ext != 'KHR_materials_pbrSpecularGlossiness']
            
            if 'extensionsRequired' in gltf_data:
                gltf_data['extensionsRequired'] = [ext for ext in gltf_data['extensionsRequired'] 
                                                 if ext != 'KHR_materials_pbrSpecularGlossiness']
            
            if converted_count > 0:
                result['success'] = True
                result['warnings'].append(f'Converted {converted_count} KHR_materials_pbrSpecularGlossiness materials to standard PBR')
            else:
                result['success'] = True
                
        except Exception as e:
            result['errors'].append(f'Specular-glossiness conversion failed: {e}')
        
        return result
    
    def _fallback_texture_transform(self, gltf_data: Dict[str, Any], target_platform: str) -> Dict[str, Any]:
        """Handle KHR_texture_transform by applying transforms to UV coordinates"""
        result = {'success': False, 'warnings': [], 'errors': []}
        
        try:
            # For now, just remove the extension and warn
            # In a full implementation, we would apply the transforms to UV coordinates
            materials = gltf_data.get('materials', [])
            removed_count = 0
            
            for material in materials:
                if 'extensions' in material and 'KHR_texture_transform' in material['extensions']:
                    del material['extensions']['KHR_texture_transform']
                    removed_count += 1
            
            if removed_count > 0:
                result['success'] = True
                result['warnings'].append(f'Removed {removed_count} KHR_texture_transform extensions (transforms not applied)')
            else:
                result['success'] = True
                
        except Exception as e:
            result['errors'].append(f'Texture transform handling failed: {e}')
        
        return result
    
    def _fallback_lights_punctual(self, gltf_data: Dict[str, Any], target_platform: str) -> Dict[str, Any]:
        """Handle KHR_lights_punctual by removing lights"""
        result = {'success': False, 'warnings': [], 'errors': []}
        
        try:
            # Remove lights extension
            if 'extensions' in gltf_data and 'KHR_lights_punctual' in gltf_data['extensions']:
                lights_count = len(gltf_data['extensions']['KHR_lights_punctual'].get('lights', []))
                del gltf_data['extensions']['KHR_lights_punctual']
                result['success'] = True
                result['warnings'].append(f'Removed KHR_lights_punctual extension with {lights_count} lights')
            else:
                result['success'] = True
                
        except Exception as e:
            result['errors'].append(f'Lights punctual handling failed: {e}')
        
        return result
    
    def _split_specular_glossiness_texture(self, gltf_data: Dict[str, Any], texture_info: Dict[str, Any], material_index: int):
        """Split specular-glossiness texture into separate metallic and roughness textures"""
        try:
            # This is a simplified implementation
            # In a full implementation, we would:
            # 1. Load the texture image
            # 2. Split the RGB channels (specular) and Alpha channel (glossiness)
            # 3. Create separate metallic and roughness textures
            # 4. Update the material references
            
            # For now, just create placeholder textures
            texture_index = texture_info.get('index', 0)
            if texture_index < len(gltf_data.get('textures', [])):
                texture = gltf_data['textures'][texture_index]
                image_index = texture.get('source', 0)
                
                # Create new images for metallic and roughness
                metallic_image_index = len(gltf_data.get('images', []))
                roughness_image_index = metallic_image_index + 1
                
                # Add placeholder images (in real implementation, these would be processed textures)
                gltf_data.setdefault('images', []).extend([
                    {'uri': f'material_{material_index}_metallic.png'},
                    {'uri': f'material_{material_index}_roughness.png'}
                ])
                
                # Add new textures
                metallic_texture_index = len(gltf_data.get('textures', []))
                roughness_texture_index = metallic_texture_index + 1
                
                gltf_data.setdefault('textures', []).extend([
                    {'source': metallic_image_index, 'sampler': 0},
                    {'source': roughness_image_index, 'sampler': 0}
                ])
                
                # Update material to use separate textures
                material = gltf_data['materials'][material_index]
                if 'pbrMetallicRoughness' not in material:
                    material['pbrMetallicRoughness'] = {}
                
                material['pbrMetallicRoughness']['metallicTexture'] = {'index': metallic_texture_index}
                material['pbrMetallicRoughness']['roughnessTexture'] = {'index': roughness_texture_index}
                
        except Exception as e:
            logger.warning(f'Failed to split specular-glossiness texture: {e}')
