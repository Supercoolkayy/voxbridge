"""
Enhanced Error Handling and Fallback System for VoxBridge
Provides comprehensive error reporting and fallback mechanisms
"""

import json
import logging
import traceback
import platform
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class VoxBridgeErrorHandler:
    """Enhanced error handling with detailed reporting and fallback mechanisms"""
    
    def __init__(self):
        self.error_log = []
        self.fallback_attempts = []
        self.platform_info = self._get_platform_info()
    
    def _get_platform_info(self) -> Dict[str, Any]:
        """Get comprehensive platform information"""
        return {
            'system': platform.system(),
            'platform': platform.platform(),
            'architecture': platform.architecture(),
            'python_version': platform.python_version(),
            'machine': platform.machine(),
            'processor': platform.processor(),
            'node': platform.node(),
            'release': platform.release(),
            'version': platform.version()
        }
    
    def log_error(self, error_type: str, error_message: str, context: Dict[str, Any] = None, 
                  fallback_attempted: bool = False, fallback_success: bool = False) -> Dict[str, Any]:
        """
        Log an error with comprehensive context information
        
        Args:
            error_type: Type of error (e.g., 'GLTF_EXTENSION', 'TEXTURE_PROCESSING', 'NODE_RUNTIME')
            error_message: Error message
            context: Additional context information
            fallback_attempted: Whether a fallback was attempted
            fallback_success: Whether the fallback was successful
            
        Returns:
            Error log entry
        """
        error_entry = {
            'timestamp': datetime.now().isoformat(),
            'error_type': error_type,
            'error_message': error_message,
            'context': context or {},
            'platform_info': self.platform_info,
            'fallback_attempted': fallback_attempted,
            'fallback_success': fallback_success,
            'traceback': traceback.format_exc()
        }
        
        self.error_log.append(error_entry)
        
        # Log to standard logger
        if fallback_success:
            logger.warning(f"{error_type}: {error_message} (Fallback successful)")
        elif fallback_attempted:
            logger.error(f"{error_type}: {error_message} (Fallback failed)")
        else:
            logger.error(f"{error_type}: {error_message}")
        
        return error_entry
    
    def attempt_fallback(self, fallback_type: str, original_error: str, 
                        fallback_function, *args, **kwargs) -> Dict[str, Any]:
        """
        Attempt a fallback operation with comprehensive logging
        
        Args:
            fallback_type: Type of fallback (e.g., 'BLENDER_FALLBACK', 'ASSIMP_FALLBACK')
            original_error: Original error message
            fallback_function: Function to call for fallback
            *args, **kwargs: Arguments for the fallback function
            
        Returns:
            Fallback result with success status and details
        """
        fallback_entry = {
            'timestamp': datetime.now().isoformat(),
            'fallback_type': fallback_type,
            'original_error': original_error,
            'attempted': True,
            'success': False,
            'error': None,
            'context': {}
        }
        
        try:
            logger.info(f"Attempting {fallback_type} fallback for: {original_error}")
            
            # Attempt the fallback
            result = fallback_function(*args, **kwargs)
            
            if result and (isinstance(result, dict) and result.get('success', False)):
                fallback_entry['success'] = True
                fallback_entry['context'] = result
                logger.info(f"{fallback_type} fallback successful")
            else:
                fallback_entry['error'] = "Fallback function returned unsuccessful result"
                logger.warning(f"{fallback_type} fallback unsuccessful")
                
        except Exception as e:
            fallback_entry['error'] = str(e)
            fallback_entry['traceback'] = traceback.format_exc()
            logger.error(f"{fallback_type} fallback failed: {e}")
        
        self.fallback_attempts.append(fallback_entry)
        return fallback_entry
    
    def handle_gltf_extension_error(self, extension_name: str, gltf_path: Path, 
                                   target_platform: str) -> Dict[str, Any]:
        """Handle GLTF extension errors with fallback"""
        error_msg = f"Missing required extension: {extension_name}"
        context = {
            'extension': extension_name,
            'gltf_path': str(gltf_path),
            'target_platform': target_platform
        }
        
        # Log the error
        error_entry = self.log_error('GLTF_EXTENSION', error_msg, context)
        
        # Attempt fallback based on extension type
        fallback_result = None
        if extension_name == 'KHR_materials_pbrSpecularGlossiness':
            fallback_result = self.attempt_fallback(
                'SPECULAR_GLOSSINESS_FALLBACK',
                error_msg,
                self._fallback_specular_glossiness,
                gltf_path, target_platform
            )
        elif extension_name == 'KHR_texture_transform':
            fallback_result = self.attempt_fallback(
                'TEXTURE_TRANSFORM_FALLBACK',
                error_msg,
                self._fallback_texture_transform,
                gltf_path, target_platform
            )
        elif extension_name == 'KHR_lights_punctual':
            fallback_result = self.attempt_fallback(
                'LIGHTS_PUNCTUAL_FALLBACK',
                error_msg,
                self._fallback_lights_punctual,
                gltf_path, target_platform
            )
        
        # Update error entry with fallback result
        if fallback_result:
            error_entry['fallback_attempted'] = True
            error_entry['fallback_success'] = fallback_result['success']
            error_entry['fallback_details'] = fallback_result
        
        return error_entry
    
    def handle_texture_error(self, texture_path: Path, error_message: str, 
                           gltf_path: Path) -> Dict[str, Any]:
        """Handle texture processing errors with fallback"""
        context = {
            'texture_path': str(texture_path),
            'gltf_path': str(gltf_path)
        }
        
        error_entry = self.log_error('TEXTURE_PROCESSING', error_message, context)
        
        # Attempt texture fallback
        fallback_result = self.attempt_fallback(
            'TEXTURE_FALLBACK',
            error_message,
            self._fallback_texture_processing,
            texture_path, gltf_path
        )
        
        error_entry['fallback_attempted'] = True
        error_entry['fallback_success'] = fallback_result['success']
        error_entry['fallback_details'] = fallback_result
        
        return error_entry
    
    def handle_node_runtime_error(self, error_message: str, node_runner_path: Path) -> Dict[str, Any]:
        """Handle Node.js runtime errors with fallback"""
        context = {
            'node_runner_path': str(node_runner_path),
            'platform': self.platform_info['system']
        }
        
        error_entry = self.log_error('NODE_RUNTIME', error_message, context)
        
        # Attempt Node.js fallback
        fallback_result = self.attempt_fallback(
            'NODE_RUNTIME_FALLBACK',
            error_message,
            self._fallback_node_runtime,
            node_runner_path
        )
        
        error_entry['fallback_attempted'] = True
        error_entry['fallback_success'] = fallback_result['success']
        error_entry['fallback_details'] = fallback_result
        
        return error_entry
    
    def generate_error_report(self, output_path: Path) -> Dict[str, Any]:
        """Generate comprehensive error report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'platform_info': self.platform_info,
            'error_summary': {
                'total_errors': len(self.error_log),
                'total_fallbacks': len(self.fallback_attempts),
                'successful_fallbacks': sum(1 for f in self.fallback_attempts if f['success']),
                'failed_fallbacks': sum(1 for f in self.fallback_attempts if not f['success'])
            },
            'errors': self.error_log,
            'fallbacks': self.fallback_attempts,
            'error_types': self._categorize_errors(),
            'recommendations': self._generate_recommendations()
        }
        
        # Save report to file
        report_path = output_path / 'voxbridge_error_report.json'
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"Error report saved to: {report_path}")
        return report
    
    def _categorize_errors(self) -> Dict[str, int]:
        """Categorize errors by type"""
        categories = {}
        for error in self.error_log:
            error_type = error['error_type']
            categories[error_type] = categories.get(error_type, 0) + 1
        return categories
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on errors encountered"""
        recommendations = []
        
        # Analyze error patterns
        error_types = self._categorize_errors()
        
        if 'GLTF_EXTENSION' in error_types:
            recommendations.append(
                "Consider updating GLTF processing to handle missing extensions automatically"
            )
        
        if 'NODE_RUNTIME' in error_types:
            recommendations.append(
                "Ensure Node.js runtime is properly bundled or install Node.js 18+ on the system"
            )
        
        if 'TEXTURE_PROCESSING' in error_types:
            recommendations.append(
                "Check texture file formats and ensure proper UV mapping"
            )
        
        # Platform-specific recommendations
        if self.platform_info['system'] == 'Windows':
            recommendations.append(
                "On Windows, ensure all required Visual C++ redistributables are installed"
            )
        elif self.platform_info['system'] == 'Linux':
            recommendations.append(
                "On Linux, ensure all required system libraries are installed (libgl1-mesa-glx, etc.)"
            )
        
        return recommendations
    
    # Fallback implementations
    def _fallback_specular_glossiness(self, gltf_path: Path, target_platform: str) -> Dict[str, Any]:
        """Fallback for KHR_materials_pbrSpecularGlossiness"""
        try:
            # Import the extension handler
            from .gltf_extension_handler import GLTFExtensionHandler
            handler = GLTFExtensionHandler()
            result = handler.process_gltf_file(gltf_path, target_platform)
            return result
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _fallback_texture_transform(self, gltf_path: Path, target_platform: str) -> Dict[str, Any]:
        """Fallback for KHR_texture_transform"""
        try:
            # Simple fallback: remove the extension
            import json
            with open(gltf_path, 'r') as f:
                gltf_data = json.load(f)
            
            # Remove texture transform extensions
            materials = gltf_data.get('materials', [])
            for material in materials:
                if 'extensions' in material and 'KHR_texture_transform' in material['extensions']:
                    del material['extensions']['KHR_texture_transform']
            
            with open(gltf_path, 'w') as f:
                json.dump(gltf_data, f, indent=2)
            
            return {'success': True, 'message': 'Removed KHR_texture_transform extensions'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _fallback_lights_punctual(self, gltf_path: Path, target_platform: str) -> Dict[str, Any]:
        """Fallback for KHR_lights_punctual"""
        try:
            # Simple fallback: remove the extension
            import json
            with open(gltf_path, 'r') as f:
                gltf_data = json.load(f)
            
            # Remove lights extension
            if 'extensions' in gltf_data and 'KHR_lights_punctual' in gltf_data['extensions']:
                del gltf_data['extensions']['KHR_lights_punctual']
            
            with open(gltf_path, 'w') as f:
                json.dump(gltf_data, f, indent=2)
            
            return {'success': True, 'message': 'Removed KHR_lights_punctual extension'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _fallback_texture_processing(self, texture_path: Path, gltf_path: Path) -> Dict[str, Any]:
        """Fallback for texture processing errors"""
        try:
            # Try to fix the texture
            from .texture_optimizer import resize_texture, fix_uv_coordinates
            
            # Resize texture to standard size
            resize_texture(str(texture_path), 1024)
            
            # Fix UV coordinates in GLTF
            uv_result = fix_uv_coordinates(str(gltf_path))
            
            return {
                'success': True,
                'message': 'Applied texture processing fallback',
                'uv_fixes': uv_result.get('fixed_count', 0)
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _fallback_node_runtime(self, node_runner_path: Path) -> Dict[str, Any]:
        """Fallback for Node.js runtime errors"""
        try:
            # Try to use system Node.js as fallback
            import subprocess
            result = subprocess.run(['node', '--version'], capture_output=True, text=True)
            
            if result.returncode == 0:
                return {
                    'success': True,
                    'message': 'Using system Node.js as fallback',
                    'node_version': result.stdout.strip()
                }
            else:
                return {'success': False, 'error': 'System Node.js not available'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
