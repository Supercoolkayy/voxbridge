"""
VoxBridge Platform Export Profiles
Handles platform-specific optimizations for Unity and Roblox
"""

import json
import subprocess
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import base64


class PlatformProfile:
    """Base class for platform-specific export profiles"""
    
    def __init__(self, debug: bool = False):
        self.debug = debug
        self.profile_name = "base"
    
    def optimize_gltf(self, gltf_data: Dict, output_path: Path) -> Dict:
        """Apply platform-specific optimizations to glTF data"""
        raise NotImplementedError("Subclasses must implement optimize_gltf")
    
    def validate_output(self, gltf_path: Path) -> Tuple[bool, List[str]]:
        """Validate the output glTF file for platform compatibility"""
        raise NotImplementedError("Subclasses must implement validate_output")


class UnityProfile(PlatformProfile):
    """Unity-optimized export profile"""
    
    def __init__(self, debug: bool = False):
        super().__init__(debug)
        self.profile_name = "unity"
    
    def optimize_gltf(self, gltf_data: Dict, output_path: Path) -> Dict:
        """Optimize glTF for Unity compatibility"""
        if self.debug:
            print("Applying Unity optimization profile...")
        
        # Keep full PBR material definitions
        if 'materials' in gltf_data:
            for material in gltf_data['materials']:
                # Ensure metallicRoughness workflow
                if 'pbrMetallicRoughness' not in material:
                    material['pbrMetallicRoughness'] = {}
                
                pbr = material['pbrMetallicRoughness']
                
                # Set default values if missing
                if 'baseColorFactor' not in pbr:
                    pbr['baseColorFactor'] = [1.0, 1.0, 1.0, 1.0]
                if 'metallicFactor' not in pbr:
                    pbr['metallicFactor'] = 1.0
                if 'roughnessFactor' not in pbr:
                    pbr['roughnessFactor'] = 1.0
                
                # Ensure baseColorTexture is properly referenced
                if 'baseColorTexture' in pbr and 'index' in pbr['baseColorTexture']:
                    # Keep external texture references
                    pass
        
        # Ensure textures are external (not embedded)
        if 'images' in gltf_data:
            for image in gltf_data['images']:
                if 'uri' in image:
                    # Remove any data URIs (embedded textures)
                    if image['uri'].startswith('data:'):
                        if self.debug:
                            print("Removing embedded texture for Unity compatibility")
                        del image['uri']
        
        # Keep standard extensions that Unity supports
        supported_extensions = [
            'KHR_materials_pbrSpecularGlossiness',
            'KHR_materials_unlit',
            'KHR_texture_transform'
        ]
        
        # Remove unsupported extensions
        if 'extensionsUsed' in gltf_data:
            gltf_data['extensionsUsed'] = [
                ext for ext in gltf_data['extensionsUsed']
                if ext in supported_extensions
            ]
        
        # Ensure proper node hierarchy for Unity
        if 'nodes' in gltf_data:
            for node in gltf_data['nodes']:
                # Ensure nodes have proper names for Unity
                if 'name' not in node:
                    node['name'] = f"Node_{id(node)}"
        
        if self.debug:
            print("Unity optimization complete")
        
        return gltf_data
    
    def validate_output(self, gltf_path: Path) -> Tuple[bool, List[str]]:
        """Validate glTF for Unity compatibility"""
        errors = []
        warnings = []
        
        try:
            with open(gltf_path, 'r', encoding='utf-8') as f:
                gltf_data = json.load(f)
            
            # Check for required components
            if 'asset' not in gltf_data:
                errors.append("Missing asset information")
            
            if 'scene' not in gltf_data:
                errors.append("Missing scene definition")
            
            # Check materials
            if 'materials' in gltf_data:
                for i, material in enumerate(gltf_data['materials']):
                    if 'pbrMetallicRoughness' not in material:
                        warnings.append(f"Material {i} missing PBR definition")
            
            # Check for embedded textures (should be external for Unity)
            if 'images' in gltf_data:
                for i, image in enumerate(gltf_data['images']):
                    if 'uri' in image and image['uri'].startswith('data:'):
                        warnings.append(f"Image {i} is embedded (should be external for Unity)")
            
            # Run glTF validator if available
            validation_result = self._run_gltf_validator(gltf_path)
            if validation_result:
                is_valid, validator_errors = validation_result
                if not is_valid:
                    errors.extend(validator_errors)
            
        except Exception as e:
            errors.append(f"Validation failed: {e}")
        
        return len(errors) == 0, errors + warnings
    
    def _run_gltf_validator(self, gltf_path: Path) -> Optional[Tuple[bool, List[str]]]:
        """Run glTF-Validator if available"""
        try:
            # Check if gltf-validator is available
            if shutil.which("gltf-validator"):
                result = subprocess.run(
                    ["gltf-validator", str(gltf_path)],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode == 0:
                    return True, []
                else:
                    # Parse validation errors
                    errors = []
                    for line in result.stderr.split('\n'):
                        if 'ERROR' in line:
                            errors.append(line.strip())
                    return False, errors
            
        except Exception as e:
            if self.debug:
                print(f"glTF validator not available: {e}")
        
        return None


class RobloxProfile(PlatformProfile):
    """Roblox-optimized export profile"""
    
    def __init__(self, debug: bool = False):
        super().__init__(debug)
        self.profile_name = "roblox"
    
    def optimize_gltf(self, gltf_data: Dict, output_path: Path) -> Dict:
        """Optimize glTF for Roblox compatibility"""
        if self.debug:
            print("Applying Roblox optimization profile...")
        
        # Simplify materials to diffuse/baseColor only
        if 'materials' in gltf_data:
            for material in gltf_data['materials']:
                # Keep only essential material properties
                simplified_material = {
                    'name': material.get('name', 'Material'),
                    'pbrMetallicRoughness': {}
                }
                
                # Copy only baseColor information
                if 'pbrMetallicRoughness' in material:
                    pbr = material['pbrMetallicRoughness']
                    if 'baseColorFactor' in pbr:
                        simplified_material['pbrMetallicRoughness']['baseColorFactor'] = pbr['baseColorFactor']
                    if 'baseColorTexture' in pbr:
                        simplified_material['pbrMetallicRoughness']['baseColorTexture'] = pbr['baseColorTexture']
                
                # Replace the material completely
                material.clear()
                material.update(simplified_material)
        
        # Ensure textures are external PNG/JPG
        if 'images' in gltf_data:
            for image in gltf_data['images']:
                if 'uri' in image:
                    # Remove any data URIs (embedded textures)
                    if image['uri'].startswith('data:'):
                        if self.debug:
                            print("Removing embedded texture for Roblox compatibility")
                        del image['uri']
                    
                    # Ensure external texture format
                    elif not image['uri'].lower().endswith(('.png', '.jpg', '.jpeg')):
                        if self.debug:
                            print(f"Converting texture format for Roblox: {image['uri']}")
                        # Keep the texture but note the format requirement
        
        # Simplify node hierarchy
        if 'nodes' in gltf_data:
            for node in gltf_data['nodes']:
                # Remove complex transformations
                for prop in ['translation', 'rotation', 'scale']:
                    if prop in node:
                        # Keep only if it's not identity
                        if prop == 'translation' and node[prop] == [0, 0, 0]:
                            del node[prop]
                        elif prop == 'rotation' and node[prop] == [0, 0, 0, 1]:
                            del node[prop]
                        elif prop == 'scale' and node[prop] == [1, 1, 1]:
                            del node[prop]
                
                # Ensure nodes have simple names
                if 'name' in node:
                    # Simplify complex names
                    name = node['name']
                    if len(name) > 32:  # Roblox name length limit
                        node['name'] = name[:32]
        
        # Remove unsupported extensions
        if 'extensionsUsed' not in gltf_data:
            gltf_data['extensionsUsed'] = []
        # Roblox supports very few extensions
        gltf_data['extensionsUsed'] = []
        
        # Remove extensions from materials
        if 'materials' in gltf_data:
            for material in gltf_data['materials']:
                if 'extensions' in material:
                    del material['extensions']
        
        if self.debug:
            print("Roblox optimization complete")
        
        return gltf_data
    
    def validate_output(self, gltf_path: Path) -> Tuple[bool, List[str]]:
        """Validate glTF for Roblox compatibility"""
        errors = []
        warnings = []
        
        try:
            with open(gltf_path, 'r', encoding='utf-8') as f:
                gltf_data = json.load(f)
            
            # Check for required components
            if 'asset' not in gltf_data:
                errors.append("Missing asset information")
            
            if 'scene' not in gltf_data:
                errors.append("Missing scene definition")
            
            # Check materials (should be simplified)
            if 'materials' in gltf_data:
                for i, material in enumerate(gltf_data['materials']):
                    if 'pbrMetallicRoughness' not in material:
                        errors.append(f"Material {i} missing PBR definition")
                    
                    # Check for unsupported material properties
                    pbr = material.get('pbrMetallicRoughness', {})
                    if 'metallicFactor' in pbr or 'roughnessFactor' in pbr:
                        warnings.append(f"Material {i} has metallic/roughness (may not work in Roblox)")
            
            # Check for embedded textures (should be external for Roblox)
            if 'images' in gltf_data:
                for i, image in enumerate(gltf_data['images']):
                    if 'uri' in image and image['uri'].startswith('data:'):
                        errors.append(f"Image {i} is embedded (Roblox requires external textures)")
            
            # Check node names (Roblox has length limits)
            if 'nodes' in gltf_data:
                for i, node in enumerate(gltf_data['nodes']):
                    if 'name' in node and len(node['name']) > 32:
                        warnings.append(f"Node {i} name too long for Roblox: {node['name']}")
            
            # Run glTF validator if available
            validation_result = self._run_gltf_validator(gltf_path)
            if validation_result:
                is_valid, validator_errors = validation_result
                if not is_valid:
                    errors.extend(validator_errors)
            
        except Exception as e:
            errors.append(f"Validation failed: {e}")
        
        return len(errors) == 0, errors + warnings
    
    def _run_gltf_validator(self, gltf_path: Path) -> Optional[Tuple[bool, List[str]]]:
        """Run glTF-Validator if available"""
        try:
            # Check if gltf-validator is available
            if shutil.which("gltf-validator"):
                result = subprocess.run(
                    ["gltf-validator", str(gltf_path)],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode == 0:
                    return True, []
                else:
                    # Parse validation errors
                    errors = []
                    for line in result.stderr.split('\n'):
                        if 'ERROR' in line:
                            errors.append(line.strip())
                    return False, errors
            
        except Exception as e:
            if self.debug:
                print(f"glTF validator not available: {e}")
        
        return None


class PlatformProfileManager:
    """Manages platform-specific export profiles"""
    
    def __init__(self, debug: bool = False):
        self.debug = debug
        self.profiles = {
            'unity': UnityProfile(debug),
            'roblox': RobloxProfile(debug)
        }
    
    def get_profile(self, platform: str) -> PlatformProfile:
        """Get the appropriate profile for the platform"""
        platform_lower = platform.lower()
        if platform_lower in self.profiles:
            return self.profiles[platform_lower]
        else:
            if self.debug:
                print(f"Unknown platform '{platform}', using Unity profile")
            return self.profiles['unity']
    
    def apply_profile(self, gltf_data: Dict, output_path: Path, platform: str) -> Dict:
        """Apply platform-specific optimizations"""
        profile = self.get_profile(platform)
        return profile.optimize_gltf(gltf_data, output_path)
    
    def validate_output(self, gltf_path: Path, platform: str) -> Tuple[bool, List[str]]:
        """Validate output for platform compatibility"""
        profile = self.get_profile(platform)
        return profile.validate_output(gltf_path)
    
    def create_platform_specific_outputs(self, gltf_data: Dict, base_output_path: Path, platform: str) -> List[Path]:
        """Create platform-specific output files"""
        outputs = []
        
        # Create platform-specific filename
        platform_output = base_output_path.parent / f"{base_output_path.stem}_{platform}.gltf"
        
        # Apply platform optimizations
        optimized_data = self.apply_profile(gltf_data, platform_output, platform)
        
        # Write optimized glTF
        with open(platform_output, 'w', encoding='utf-8') as f:
            json.dump(optimized_data, f, indent=2)
        
        outputs.append(platform_output)
        
        # Validate the output
        is_valid, validation_messages = self.validate_output(platform_output, platform)
        
        if self.debug:
            if is_valid:
                print(f"{platform.capitalize()} output validated successfully")
            else:
                print(f"{platform.capitalize()} validation issues:")
                for msg in validation_messages:
                    print(f"  - {msg}")
        
        return outputs


def run_gltf_pipeline(gltf_path: Path, output_path: Path, options: List[str] = None) -> bool:
    """Run glTF-Pipeline for additional processing"""
    try:
        if not shutil.which("gltf-pipeline"):
            return False
        
        cmd = ["gltf-pipeline", "-i", str(gltf_path), "-o", str(output_path)]
        if options:
            cmd.extend(options)
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        return result.returncode == 0
        
    except Exception as e:
        print(f"glTF-Pipeline error: {e}")
        return False


def run_gltf_validator(gltf_path: Path) -> Tuple[bool, List[str]]:
    """Run glTF-Validator for comprehensive validation"""
    try:
        if not shutil.which("gltf-validator"):
            return True, ["glTF-Validator not available"]
        
        result = subprocess.run(
            ["gltf-validator", str(gltf_path)],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            return True, []
        else:
            # Parse validation output
            errors = []
            for line in result.stderr.split('\n'):
                if 'ERROR' in line:
                    errors.append(line.strip())
            return False, errors
            
    except Exception as e:
        return False, [f"Validation error: {e}"]


def create_fbx2gltf_fallback(input_path: Path, output_path: Path) -> bool:
    """Create FBX2glTF fallback if Blender is not available"""
    try:
        if not shutil.which("fbx2gltf"):
            return False
        
        result = subprocess.run(
            ["fbx2gltf", "-i", str(input_path), "-o", str(output_path)],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"FBX2glTF error: {e}")
        return False
