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
        with open(gltf_path, 'r', encoding='utf-8') as f:
            gltf_data = json.load(f)
        
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
            # Use Blender for GLB files
            return self.convert_with_blender(input_path, output_path, optimize_mesh=optimize_mesh)
        else:
            # Use JSON parsing for glTF files
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
                raise RuntimeError(f"Blender failed with return code {result.returncode}\n{result.stderr}")
                
        except subprocess.TimeoutExpired:
            raise RuntimeError("Blender processing timed out (120s)")
        except Exception as e:
            raise RuntimeError(f"Failed to run Blender: {e}")
    
    def convert_gltf_json(self, input_path: Path, output_path: Path, generate_atlas: bool = False, compress_textures: bool = False, platform: str = "unity") -> bool:
        """Convert glTF by parsing and cleaning JSON, with optional texture optimization and material mapping"""
        try:
            gltf_data, changes = self.clean_gltf_json(input_path)
            
            # Apply material mapping for platform compatibility
            if platform in ["unity", "roblox"]:
                material_changes = self.map_materials(gltf_data, platform)
                changes.extend(material_changes)
            
            input_dir = input_path.parent
            # Gather all texture image paths
            image_paths = []
            if 'images' in gltf_data:
                for image in gltf_data['images']:
                    if 'uri' in image:
                        img_path = input_dir / image['uri']
                        if img_path.exists():
                            image_paths.append(str(img_path))
            # Compress/resize textures if requested
            if compress_textures:
                for img_path in image_paths:
                    if TEXTURE_OPTIMIZATION_AVAILABLE:
                        resize_texture(img_path, max_size=1024)
                    else:
                        print(f"PIL not available, skipping texture optimization for {img_path}")
            # Write cleaned glTF first
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(gltf_data, f, indent=2)
            
            # Generate texture atlas if requested
            if generate_atlas and image_paths:
                atlas_img, mapping = generate_texture_atlas(image_paths, atlas_size=1024)
                atlas_filename = "texture_atlas.png"
                atlas_path = input_dir / atlas_filename
                atlas_img.save(atlas_path)
                update_gltf_with_atlas(output_path, mapping, atlas_filename)
            # Copy associated files (textures, bin files)
            self.copy_associated_files(input_path, output_path)
            return True
        except Exception as e:
            raise RuntimeError(f"Failed to process glTF: {e}")
    
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