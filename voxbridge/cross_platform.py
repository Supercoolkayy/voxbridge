"""
Cross-Platform Consistency Module for VoxBridge
Ensures identical outputs across Linux and Windows platforms
"""

import os
import platform
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import hashlib

logger = logging.getLogger(__name__)

class CrossPlatformManager:
    """Manages cross-platform consistency for VoxBridge"""
    
    def __init__(self):
        self.platform_info = self._get_platform_info()
        self.consistency_checks = []
    
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
            'version': platform.version(),
            'path_separator': os.sep,
            'line_ending': os.linesep
        }
    
    def normalize_paths(self, path_string: str) -> str:
        """Normalize paths for cross-platform consistency"""
        # Convert to forward slashes for consistency
        normalized = path_string.replace('\\', '/')
        
        # Remove any duplicate slashes
        while '//' in normalized:
            normalized = normalized.replace('//', '/')
        
        return normalized
    
    def normalize_gltf_paths(self, gltf_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize all paths in GLTF data for cross-platform consistency"""
        try:
            # Normalize image URIs
            if 'images' in gltf_data:
                for image in gltf_data['images']:
                    if 'uri' in image and image['uri']:
                        image['uri'] = self.normalize_paths(image['uri'])
            
            # Normalize buffer URIs
            if 'buffers' in gltf_data:
                for buffer in gltf_data['buffers']:
                    if 'uri' in buffer and buffer['uri']:
                        buffer['uri'] = self.normalize_paths(buffer['uri'])
            
            # Normalize any other URI fields
            self._normalize_uris_recursive(gltf_data)
            
            return gltf_data
            
        except Exception as e:
            logger.warning(f"Path normalization failed: {e}")
            return gltf_data
    
    def _normalize_uris_recursive(self, data: Any):
        """Recursively normalize URI fields"""
        if isinstance(data, dict):
            for key, value in data.items():
                if key == 'uri' and isinstance(value, str):
                    data[key] = self.normalize_paths(value)
                else:
                    self._normalize_uris_recursive(value)
        elif isinstance(data, list):
            for item in data:
                self._normalize_uris_recursive(item)
    
    def ensure_consistent_line_endings(self, file_path: Path) -> bool:
        """Ensure consistent line endings across platforms"""
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            
            # Normalize to Unix line endings (LF)
            normalized_content = content.replace(b'\r\n', b'\n').replace(b'\r', b'\n')
            
            if normalized_content != content:
                with open(file_path, 'wb') as f:
                    f.write(normalized_content)
                logger.debug(f"Normalized line endings in {file_path}")
                return True
            
            return False
            
        except Exception as e:
            logger.warning(f"Line ending normalization failed for {file_path}: {e}")
            return False
    
    def validate_cross_platform_consistency(self, gltf_path: Path, 
                                          reference_platform: str = None) -> Dict[str, Any]:
        """Validate cross-platform consistency of GLTF file"""
        result = {
            'consistent': True,
            'issues': [],
            'platform_info': self.platform_info,
            'checks_performed': []
        }
        
        try:
            # Load GLTF data
            with open(gltf_path, 'r') as f:
                gltf_data = json.load(f)
            
            # Check 1: Path consistency
            path_check = self._check_path_consistency(gltf_data)
            result['checks_performed'].append('path_consistency')
            if not path_check['consistent']:
                result['consistent'] = False
                result['issues'].extend(path_check['issues'])
            
            # Check 2: Line ending consistency
            line_ending_check = self._check_line_ending_consistency(gltf_path)
            result['checks_performed'].append('line_ending_consistency')
            if not line_ending_check['consistent']:
                result['consistent'] = False
                result['issues'].extend(line_ending_check['issues'])
            
            # Check 3: JSON formatting consistency
            json_check = self._check_json_formatting_consistency(gltf_data)
            result['checks_performed'].append('json_formatting_consistency')
            if not json_check['consistent']:
                result['consistent'] = False
                result['issues'].extend(json_check['issues'])
            
            # Check 4: Extension handling consistency
            extension_check = self._check_extension_consistency(gltf_data)
            result['checks_performed'].append('extension_consistency')
            if not extension_check['consistent']:
                result['consistent'] = False
                result['issues'].extend(extension_check['issues'])
            
            # Check 5: Material consistency
            material_check = self._check_material_consistency(gltf_data)
            result['checks_performed'].append('material_consistency')
            if not material_check['consistent']:
                result['consistent'] = False
                result['issues'].extend(material_check['issues'])
            
            return result
            
        except Exception as e:
            result['consistent'] = False
            result['issues'].append(f"Validation failed: {e}")
            return result
    
    def _check_path_consistency(self, gltf_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check path consistency in GLTF data"""
        result = {'consistent': True, 'issues': []}
        
        # Check for Windows-style paths
        def check_paths_recursive(data, path=""):
            if isinstance(data, dict):
                for key, value in data.items():
                    if key == 'uri' and isinstance(value, str):
                        if '\\' in value:
                            result['consistent'] = False
                            result['issues'].append(f"Windows-style path found in {path}.{key}: {value}")
                    else:
                        check_paths_recursive(value, f"{path}.{key}")
            elif isinstance(data, list):
                for i, item in enumerate(data):
                    check_paths_recursive(item, f"{path}[{i}]")
        
        check_paths_recursive(gltf_data)
        return result
    
    def _check_line_ending_consistency(self, file_path: Path) -> Dict[str, Any]:
        """Check line ending consistency"""
        result = {'consistent': True, 'issues': []}
        
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            
            # Check for mixed line endings
            has_crlf = b'\r\n' in content
            has_cr = b'\r' in content and not has_crlf
            has_lf = b'\n' in content
            
            if has_crlf and has_cr:
                result['consistent'] = False
                result['issues'].append("Mixed line endings detected (CRLF and CR)")
            elif has_crlf and has_lf:
                result['consistent'] = False
                result['issues'].append("Mixed line endings detected (CRLF and LF)")
            elif has_cr and has_lf:
                result['consistent'] = False
                result['issues'].append("Mixed line endings detected (CR and LF)")
            
        except Exception as e:
            result['consistent'] = False
            result['issues'].append(f"Line ending check failed: {e}")
        
        return result
    
    def _check_json_formatting_consistency(self, gltf_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check JSON formatting consistency"""
        result = {'consistent': True, 'issues': []}
        
        # Check for consistent indentation and formatting
        try:
            # Re-serialize and check for consistency
            formatted_json = json.dumps(gltf_data, indent=2, sort_keys=True)
            reparsed_data = json.loads(formatted_json)
            
            # Check if data is identical after re-parsing
            if json.dumps(gltf_data, sort_keys=True) != json.dumps(reparsed_data, sort_keys=True):
                result['consistent'] = False
                result['issues'].append("JSON data inconsistency detected")
            
        except Exception as e:
            result['consistent'] = False
            result['issues'].append(f"JSON formatting check failed: {e}")
        
        return result
    
    def _check_extension_consistency(self, gltf_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check extension handling consistency"""
        result = {'consistent': True, 'issues': []}
        
        # Check for consistent extension handling
        extensions_used = set(gltf_data.get('extensionsUsed', []))
        extensions_required = set(gltf_data.get('extensionsRequired', []))
        
        # Check if required extensions are in used extensions
        missing_required = extensions_required - extensions_used
        if missing_required:
            result['consistent'] = False
            result['issues'].append(f"Required extensions not in used extensions: {missing_required}")
        
        # Check for platform-specific extensions
        platform_extensions = {
            'KHR_materials_pbrSpecularGlossiness',
            'KHR_texture_transform',
            'KHR_lights_punctual'
        }
        
        unsupported_extensions = extensions_used & platform_extensions
        if unsupported_extensions:
            result['issues'].append(f"Platform-specific extensions found: {unsupported_extensions}")
        
        return result
    
    def _check_material_consistency(self, gltf_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check material consistency across platforms"""
        result = {'consistent': True, 'issues': []}
        
        materials = gltf_data.get('materials', [])
        for i, material in enumerate(materials):
            # Check for consistent material properties
            if 'pbrMetallicRoughness' in material:
                pbr = material['pbrMetallicRoughness']
                
                # Check for consistent factor values
                for factor_name in ['baseColorFactor', 'metallicFactor', 'roughnessFactor']:
                    if factor_name in pbr:
                        factor_value = pbr[factor_name]
                        if isinstance(factor_value, list) and len(factor_value) == 4:
                            # Check for valid color values
                            if any(val < 0 or val > 1 for val in factor_value):
                                result['consistent'] = False
                                result['issues'].append(f"Material {i}: Invalid {factor_name} values")
                        elif isinstance(factor_value, (int, float)):
                            # Check for valid factor values
                            if factor_value < 0 or factor_value > 1:
                                result['consistent'] = False
                                result['issues'].append(f"Material {i}: Invalid {factor_name} value")
        
        return result
    
    def generate_consistency_report(self, gltf_path: Path, output_dir: Path) -> Dict[str, Any]:
        """Generate comprehensive consistency report (returns data without saving)"""
        report = {
            'timestamp': self.platform_info,
            'platform_info': self.platform_info,
            'file_path': str(gltf_path),
            'consistency_check': self.validate_cross_platform_consistency(gltf_path),
            'recommendations': self._generate_consistency_recommendations(gltf_path)
        }
        
        # Don't save separate file - will be consolidated
        return report
    
    def _generate_consistency_recommendations(self, gltf_path: Path) -> List[str]:
        """Generate recommendations for improving cross-platform consistency"""
        recommendations = []
        
        try:
            with open(gltf_path, 'r') as f:
                gltf_data = json.load(f)
            
            # Check for Windows-style paths
            if any('\\' in str(value) for value in self._extract_all_strings(gltf_data)):
                recommendations.append("Use forward slashes (/) for all paths instead of backslashes (\\)")
            
            # Check for platform-specific extensions
            extensions_used = gltf_data.get('extensionsUsed', [])
            platform_extensions = {
                'KHR_materials_pbrSpecularGlossiness',
                'KHR_texture_transform',
                'KHR_lights_punctual'
            }
            
            if any(ext in extensions_used for ext in platform_extensions):
                recommendations.append("Consider converting platform-specific extensions to standard PBR materials")
            
            # Check for material consistency
            materials = gltf_data.get('materials', [])
            if materials:
                recommendations.append("Ensure all materials use consistent PBR metallic-roughness workflow")
            
        except Exception as e:
            recommendations.append(f"Could not analyze file for recommendations: {e}")
        
        return recommendations
    
    def _extract_all_strings(self, data: Any) -> List[str]:
        """Extract all string values from nested data structure"""
        strings = []
        
        if isinstance(data, dict):
            for value in data.values():
                strings.extend(self._extract_all_strings(value))
        elif isinstance(data, list):
            for item in data:
                strings.extend(self._extract_all_strings(item))
        elif isinstance(data, str):
            strings.append(data)
        
        return strings
    
    def fix_cross_platform_issues(self, gltf_path: Path) -> Dict[str, Any]:
        """Fix cross-platform consistency issues"""
        result = {
            'success': True,
            'fixes_applied': [],
            'errors': []
        }
        
        try:
            # Check if file exists and is readable
            if not gltf_path.exists():
                result['errors'].append(f"File does not exist: {gltf_path}")
                result['success'] = False
                return result
            
            # Check if it's a GLB file (binary) - skip cross-platform fixes for GLB
            if gltf_path.suffix.lower() == '.glb':
                logger.info("Skipping cross-platform fixes for GLB file (binary format)")
                result['fixes_applied'].append('skipped_glb_binary')
                return result
            
            # Check file size - skip if too large or empty
            file_size = gltf_path.stat().st_size
            if file_size == 0:
                result['errors'].append("File is empty")
                result['success'] = False
                return result
            
            if file_size > 100 * 1024 * 1024:  # 100MB limit
                logger.warning(f"File too large for cross-platform fixes: {file_size} bytes")
                result['fixes_applied'].append('skipped_large_file')
                return result
            
            # Try to read as JSON with proper encoding handling
            try:
                with open(gltf_path, 'r', encoding='utf-8') as f:
                    gltf_data = json.load(f)
            except (UnicodeDecodeError, json.JSONDecodeError) as e:
                # Try with different encodings
                for encoding in ['latin-1', 'cp1252', 'iso-8859-1']:
                    try:
                        with open(gltf_path, 'r', encoding=encoding) as f:
                            gltf_data = json.load(f)
                        logger.info(f"Successfully read file with {encoding} encoding")
                        break
                    except (UnicodeDecodeError, json.JSONDecodeError):
                        continue
                else:
                    # If all encodings fail, skip cross-platform fixes
                    logger.warning(f"Could not read GLTF file with any encoding, skipping cross-platform fixes: {e}")
                    result['fixes_applied'].append('skipped_unreadable_file')
                    return result
            
            # Fix 1: Normalize paths
            original_data = json.dumps(gltf_data, sort_keys=True)
            gltf_data = self.normalize_gltf_paths(gltf_data)
            if json.dumps(gltf_data, sort_keys=True) != original_data:
                result['fixes_applied'].append('normalized_paths')
            
            # Fix 2: Ensure consistent JSON formatting
            with open(gltf_path, 'w', encoding='utf-8') as f:
                json.dump(gltf_data, f, indent=2, sort_keys=True, ensure_ascii=False)
            result['fixes_applied'].append('normalized_json_formatting')
            
            # Fix 3: Normalize line endings
            if self.ensure_consistent_line_endings(gltf_path):
                result['fixes_applied'].append('normalized_line_endings')
            
            logger.info(f"Applied {len(result['fixes_applied'])} cross-platform fixes")
            
        except Exception as e:
            result['success'] = False
            result['errors'].append(str(e))
            logger.error(f"Cross-platform fixes failed: {e}")
        
        return result
