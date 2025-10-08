"""
Trimesh-based conversion route for static GLTF/GLB files
Optimized for simple models without animations, skins, or morph targets
"""

import json
import time
import zipfile
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class TrimeshRoute:
    """Trimesh-based conversion for static files"""
    
    def __init__(self, debug: bool = False):
        self.debug = debug
        self.conversion_stats = {}
    
    def convert(self, input_path: Path, output_dir: Path, target: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert a static GLTF/GLB file using trimesh
        
        Args:
            input_path: Path to input GLTF/GLB file
            output_dir: Output directory
            target: Target platform (unity/roblox)
            options: Conversion options
            
        Returns:
            Dict containing conversion results and stats
        """
        start_time = time.time()
        
        try:
            # Import trimesh
            try:
                import trimesh
                import numpy as np
            except ImportError as e:
                logger.error(f"Trimesh not available: {e}")
                return {
                    'success': False,
                    'error': 'Trimesh not available',
                    'fallback_used': True
                }
            
            # Load the GLTF file
            if self.debug:
                logger.info(f"Loading GLTF file: {input_path}")
            
            scene = trimesh.load(str(input_path))
            
            # Get initial stats
            initial_stats = self._get_scene_stats(scene)
            
            # Apply optimizations if requested
            if options.get('optimize_mesh', False):
                scene = self._optimize_mesh(scene, options)
            
            # Apply texture optimizations if requested
            if options.get('generate_atlas', False):
                scene = self._optimize_textures(scene, options)
            
            # Get final stats
            final_stats = self._get_scene_stats(scene)
            
            # Export to GLTF
            output_path = output_dir / f"{input_path.stem}_{target}.gltf"
            
            if self.debug:
                logger.info(f"Exporting to: {output_path}")
            
            # Export the scene
            scene.export(str(output_path))
            
            # Apply platform-specific modifications
            self._apply_platform_modifications(output_path, target)
            
            # Package if requested
            if options.get('pack_glb', False):
                package_path = self._package_output(output_path, target)
                if package_path:
                    output_path = package_path
            
            # Calculate conversion time
            conversion_time = time.time() - start_time
            
            # Update stats
            self.conversion_stats = {
                'success': True,
                'input_path': str(input_path),
                'output_path': str(output_path),
                'target': target,
                'conversion_time': conversion_time,
                'initial_stats': initial_stats,
                'final_stats': final_stats,
                'optimizations_applied': {
                    'mesh_optimization': options.get('optimize_mesh', False),
                    'texture_atlas': options.get('generate_atlas', False)
                },
                'fallback_used': False
            }
            
            return self.conversion_stats
            
        except Exception as e:
            logger.error(f"Trimesh conversion failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'fallback_used': True,
                'conversion_time': time.time() - start_time
            }
    
    def _get_scene_stats(self, scene) -> Dict[str, Any]:
        """Get statistics from a trimesh scene"""
        try:
            import numpy as np
            
            stats = {
                'meshes': len(scene.geometry),
                'triangles': sum(getattr(geom, 'faces', np.array([])).shape[0] for geom in scene.geometry.values()),
                'vertices': sum(getattr(geom, 'vertices', np.array([])).shape[0] for geom in scene.geometry.values()),
                'materials': len(scene.materials) if hasattr(scene, 'materials') else 0,
                'textures': len(scene.textures) if hasattr(scene, 'textures') else 0
            }
            
            # Calculate total file size estimate
            total_size = 0
            for geom in scene.geometry.values():
                if hasattr(geom, 'faces'):
                    total_size += geom.faces.nbytes
                if hasattr(geom, 'vertices'):
                    total_size += geom.vertices.nbytes
                if hasattr(geom, 'normals'):
                    total_size += geom.normals.nbytes
                if hasattr(geom, 'texture_coords'):
                    total_size += geom.texture_coords.nbytes
            
            stats['estimated_size_bytes'] = total_size
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting scene stats: {e}")
            return {
                'meshes': 0,
                'triangles': 0,
                'vertices': 0,
                'materials': 0,
                'textures': 0,
                'estimated_size_bytes': 0
            }
    
    def _optimize_mesh(self, scene, options: Dict[str, Any]) -> Any:
        """Apply mesh optimizations"""
        try:
            if self.debug:
                logger.info("Applying mesh optimizations")
            
            # Simplify meshes if requested
            simplify_ratio = options.get('simplify_ratio', 0.3)
            
            for name, geom in scene.geometry.items():
                if hasattr(geom, 'simplify_quadric_decimation'):
                    try:
                        # Simplify the mesh
                        simplified = geom.simplify_quadric_decimation(
                            face_count=int(geom.faces.shape[0] * (1 - simplify_ratio))
                        )
                        scene.geometry[name] = simplified
                        
                        if self.debug:
                            logger.info(f"Simplified {name}: {geom.faces.shape[0]} -> {simplified.faces.shape[0]} faces")
                            
                    except Exception as e:
                        logger.warning(f"Could not simplify {name}: {e}")
            
            return scene
            
        except Exception as e:
            logger.error(f"Mesh optimization failed: {e}")
            return scene
    
    def _optimize_textures(self, scene, options: Dict[str, Any]) -> Any:
        """Apply texture optimizations"""
        try:
            if self.debug:
                logger.info("Applying texture optimizations")
            
            # This is a placeholder - actual texture optimization would require
            # more complex logic for texture atlasing and resizing
            # For now, we'll just return the scene as-is
            
            return scene
            
        except Exception as e:
            logger.error(f"Texture optimization failed: {e}")
            return scene
    
    def _apply_platform_modifications(self, gltf_path: Path, target: str) -> None:
        """Apply platform-specific modifications to the GLTF file"""
        try:
            if self.debug:
                logger.info(f"Applying {target} platform modifications")
            
            # Load the GLTF file
            with open(gltf_path, 'r', encoding='utf-8') as f:
                gltf_data = json.load(f)
            
            # Apply platform-specific modifications
            if target == 'roblox':
                self._apply_roblox_modifications(gltf_data)
            elif target == 'unity':
                self._apply_unity_modifications(gltf_data)
            
            # Save the modified GLTF
            with open(gltf_path, 'w', encoding='utf-8') as f:
                json.dump(gltf_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Platform modifications failed: {e}")
    
    def _apply_roblox_modifications(self, gltf_data: Dict[str, Any]) -> None:
        """Apply Roblox-specific modifications"""
        # Roblox-specific modifications would go here
        # For now, we'll just ensure basic compatibility
        pass
    
    def _apply_unity_modifications(self, gltf_data: Dict[str, Any]) -> None:
        """Apply Unity-specific modifications"""
        # Ensure proper sampler configuration for Unity
        if 'samplers' not in gltf_data:
            gltf_data['samplers'] = []
        
        if 'textures' in gltf_data and gltf_data['textures']:
            # Add default sampler if none exists
            if not gltf_data['samplers']:
                gltf_data['samplers'] = [{
                    "magFilter": 9728,  # NEAREST
                    "minFilter": 9728,  # NEAREST
                    "wrapS": 33071,     # CLAMP_TO_EDGE
                    "wrapT": 33071      # CLAMP_TO_EDGE
                }]
            
            # Ensure all textures have samplers
            for texture in gltf_data['textures']:
                if 'sampler' not in texture:
                    texture['sampler'] = 0
    
    def _package_output(self, gltf_path: Path, target: str) -> Optional[Path]:
        """Package the output into a ZIP file"""
        try:
            package_path = gltf_path.parent / f"{gltf_path.stem}_{target}.zip"
            
            with zipfile.ZipFile(package_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                # Add the GLTF file
                zf.write(gltf_path, gltf_path.name)
                
                # Add any associated BIN files
                bin_files = gltf_path.parent.glob(f"{gltf_path.stem}*.bin")
                for bin_file in bin_files:
                    zf.write(bin_file, bin_file.name)
                
                # Add any texture files
                texture_files = gltf_path.parent.glob("*.png") + gltf_path.parent.glob("*.jpg")
                for tex_file in texture_files:
                    zf.write(tex_file, tex_file.name)
            
            if self.debug:
                logger.info(f"Packaged output: {package_path}")
            
            return package_path
            
        except Exception as e:
            logger.error(f"Packaging failed: {e}")
            return None
    
    def get_conversion_stats(self) -> Dict[str, Any]:
        """Get the last conversion statistics"""
        return self.conversion_stats
