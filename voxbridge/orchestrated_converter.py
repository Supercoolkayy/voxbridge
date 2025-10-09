"""
Orchestrated VoxBridge Converter
Routes files through appropriate conversion paths based on complexity detection
"""

import json
import subprocess
import time
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging

# Import detection and routing modules
from .utils.detect import is_complex_gltf, get_file_stats
from .utils.paths import get_node_runner_path, ensure_executable, is_bundled
from .converter import VoxBridgeConverter

logger = logging.getLogger(__name__)

class OrchestratedConverter:
    """Orchestrates conversion between static and complex file processing"""
    
    def __init__(self, debug: bool = False):
        self.debug = debug
        self.static_converter = VoxBridgeConverter(debug=debug)
        self.conversion_stats = {}
        
        # Check if Node.js is available
        self.node_available = self._check_node_availability()
        
        if not self.node_available:
            logger.warning("Node.js not available - complex files will use fallback processing")
    
    def convert_file(self, input_path: Path, output_dir: Path, target: str, 
                    options: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Main conversion entry point with automatic routing
        
        Args:
            input_path: Path to input GLTF/GLB file
            output_dir: Output directory
            target: Target platform (unity/roblox)
            options: Conversion options
            
        Returns:
            Dict containing conversion results and stats
        """
        if options is None:
            options = {}
        
        start_time = time.time()
        
        # Initialize result structure
        result = {
            'input': str(input_path),
            'target': target,
            'start': start_time,
            'success': False,
            'error': None,
            'warnings': [],
            'fallback_used': False,
            'complex_mode': False,
            'conversion_path': None
        }
        
        try:
            # Step 1: Detect file complexity
            logger.info(f"Analyzing file complexity: {input_path}")
            input_path_obj = Path(input_path)
            complexity_analysis = is_complex_gltf(input_path_obj)
            
            if self.debug:
                logger.info(f"Complexity analysis: {complexity_analysis}")
            
            # Step 2: Determine conversion path
            force_static = options.get('force_static', False)
            force_node = options.get('force_node', False)
            
            if force_static:
                use_complex_path = False
                result['conversion_path'] = 'static_forced'
            elif force_node:
                use_complex_path = True
                result['conversion_path'] = 'complex_forced'
            else:
                use_complex_path = complexity_analysis['is_complex']
                result['conversion_path'] = 'complex' if use_complex_path else 'static'
            
            result['complex_mode'] = use_complex_path
            
            # Step 3: Route to appropriate converter
            if use_complex_path:
                if self.node_available:
                    logger.info("Using Node.js complex processing path")
                    result = self._process_complex_file(input_path_obj, Path(output_dir), target, options, result, input_path_obj)
                else:
                    logger.warning("Node.js not available, falling back to static processing")
                    result['fallback_used'] = True
                    result = self._process_static_file(input_path_obj, Path(output_dir), target, options, result, input_path_obj)
            else:
                logger.info("Using Trimesh static processing path")
                result = self._process_static_file(input_path_obj, Path(output_dir), target, options, result, input_path_obj)
            
            # Step 4: Post-validation pass
            if result['success']:
                # Fast validation first
                validation_result = self._validate_output_fast(result.get('output_path'))
                result['validation'] = validation_result
                
                if not validation_result['valid']:
                    logger.warning(f"Output validation failed: {validation_result['errors']}")
                    result['warnings'].extend(validation_result['errors'])
                else:
                    # Comprehensive post-validation based on conversion type
                    post_validation = self._post_validate_output(
                        result.get('output_path'), 
                        target, 
                        result.get('conversion_path', 'unknown'),
                        result.get('initial_stats', {}),
                        result.get('final_stats', {})
                    )
                    result['post_validation'] = post_validation
                    
                    # Add warnings from post-validation
                    if post_validation.get('warnings'):
                        result['warnings'].extend(post_validation['warnings'])
            
            # Step 5: Unified packaging and cleanup
            if result['success']:
                output_path = result.get('output_path')
                if output_path and not output_path.endswith('.zip'):
                    # Create unified package from loose files
                    packaged_result = self._create_unified_package(
                        output_path, 
                        output_dir, 
                        target, 
                        input_path.stem
                    )
                    if packaged_result['success']:
                        result['output_path'] = packaged_result['package_path']
                        result['package_info'] = packaged_result['package_info']
                        
                        # Clean up loose intermediate files
                        self._cleanup_intermediate_files(output_dir, packaged_result['package_path'], options.get('keep_temp', False))
                else:
                    # If already a ZIP, clean it up and ensure proper structure
                    if output_path and Path(output_path).exists():
                        logger.debug(f"Found existing ZIP package: {output_path}")
                        logger.debug(f"Cleaning existing ZIP package: {output_path}")
                        # Clean up the existing ZIP to remove duplicates and ensure clean structure
                        cleaned_result = self._clean_existing_package(output_path, input_path.stem, target)
                        if cleaned_result['success']:
                            result['output_path'] = cleaned_result['package_path']
                            result['package_info'] = cleaned_result['package_info']
                            logger.debug(f"Successfully cleaned package: {cleaned_result['package_info']['files']}")
                        else:
                            logger.warning(f"Package cleaning failed: {cleaned_result.get('error', 'Unknown error')}")
                            result['package_info'] = self._analyze_existing_package(output_path)
                        
                        # Clean up any loose files in the directory
                        self._cleanup_intermediate_files(output_dir, output_path, options.get('keep_temp', False))
            
            # Step 6: Generate final report and embed in package
            processing_time = time.time() - start_time
            result['time_sec'] = processing_time
            result['processing_time'] = processing_time
            result['timestamp'] = time.time()
            
            # Embed report in the final package only if it doesn't already exist
            if result['success'] and result.get('output_path'):
                package_info = result.get('package_info', {})
                if not package_info.get('structure', {}).get('report', False):
                    self._embed_report_in_package(result, output_dir, options.get('debug', False))
            
            logger.info(f"Conversion completed in {result['time_sec']:.2f}s")
            if result['success']:
                logger.info(f"Package ready: {result['output_path']}")
            
            return result
            
        except Exception as e:
            logger.error(f"Conversion failed: {e}")
            result['success'] = False
            result['error'] = str(e)
            result['time_sec'] = time.time() - start_time
            
            # Write error report
            report_path = output_dir / 'voxbridge_report.json'
            with open(report_path, 'w') as f:
                json.dump(result, f, indent=2, default=str)
            
            return result
    
    def _process_static_file(self, input_path: Path, output_dir: Path, target: str, 
                           options: Dict[str, Any], result: Dict[str, Any], input_path_obj: Path = None) -> Dict[str, Any]:
        """Process static files using existing VoxBridgeConverter (Blender → Assimp → Trimesh)"""
        try:
            # Get initial file stats
            if input_path_obj is None:
                input_path_obj = input_path
            initial_stats = get_file_stats(input_path_obj)
            result['initial_stats'] = initial_stats
            
            # Determine output file path
            output_file = output_dir / f"{input_path.stem}_{target}.gltf"
            
            # Use existing VoxBridgeConverter with its proven fallback system
            success = self.static_converter.convert_file(
                input_path=input_path,
                output_path=output_file,
                use_blender=not options.get('no_blender', False),
                optimize_mesh=options.get('optimize_mesh', False),
                generate_atlas=options.get('generate_atlas', False),
                platform=target
            )
            
            if success:
                result['success'] = True
                
                # Check if a ZIP file was created (existing converter behavior)
                zip_file = output_dir / f"{input_path.stem}_{target}.zip"
                if zip_file.exists():
                    result['output_path'] = str(zip_file)
                else:
                    result['output_path'] = str(output_file)
                
                # Get final stats from the converter
                final_stats = self.static_converter.get_last_conversion_stats()
                result['final_stats'] = final_stats
                
                # Calculate improvements
                if 'initial_stats' in result and 'final_stats' in result:
                    result['improvements'] = self._calculate_improvements(
                        result['initial_stats'], result['final_stats']
                    )
            else:
                result['success'] = False
                result['error'] = 'Static conversion failed'
                result['fallback_used'] = True
            
            return result
            
        except Exception as e:
            logger.error(f"Static processing failed: {e}")
            result['success'] = False
            result['error'] = str(e)
            result['fallback_used'] = True
            return result
    
    def _process_complex_file(self, input_path: Path, output_dir: Path, target: str, 
                            options: Dict[str, Any], result: Dict[str, Any], input_path_obj: Path = None) -> Dict[str, Any]:
        """Process complex files using Node.js tools"""
        try:
            # Get initial file stats
            if input_path_obj is None:
                input_path_obj = input_path
            initial_stats = get_file_stats(input_path_obj)
            result['initial_stats'] = initial_stats
            
            # Prepare Node.js command using bundled runner
            node_runner_path = get_node_runner_path()
            
            if not node_runner_path.exists():
                raise FileNotFoundError(f"Node.js runner not found: {node_runner_path}")
            
            # Build command arguments
            cmd = [
                str(node_runner_path), 'process',
                '--input', str(input_path.absolute()),
                '--output', str(output_dir.absolute()),
                '--target', target
            ]
            
            if options.get('pack_glb', False):
                cmd.append('--pack-glb')
            
            if options.get('use_draco', True):
                cmd.append('--use-draco')
            else:
                cmd.append('--no-draco')
            
            if options.get('texture_size'):
                cmd.extend(['--texture-size', str(options['texture_size'])])
            
            if options.get('quantize', True):
                cmd.append('--quantize')
            
            if self.debug:
                cmd.append('--verbose')
                logger.info(f"Running Node.js command: {' '.join(cmd)}")
            
            # Run Node.js processing
            process_result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=node_script.parent
            )
            
            if process_result.returncode != 0:
                error_msg = f"Node.js processing failed: {process_result.stderr}"
                logger.error(error_msg)
                result['success'] = False
                result['error'] = error_msg
                result['fallback_used'] = True
                return result
            
            # Parse Node.js output for stats
            try:
                # Try to parse stdout as JSON first
                if process_result.stdout.strip():
                    # Check if stdout looks like JSON (starts with { or [)
                    stdout_clean = process_result.stdout.strip()
                    if stdout_clean.startswith('{') or stdout_clean.startswith('['):
                        node_stats = json.loads(stdout_clean)
                        result['node_stats'] = node_stats
            except json.JSONDecodeError:
                # If stdout is not JSON, it might be a GLB file or other output
                pass
            
            # Always try to find the report file
            report_path = output_dir / 'voxbridge_report.json'
            if report_path.exists():
                try:
                    with open(report_path, 'r') as f:
                        node_stats = json.load(f)
                        result['node_stats'] = node_stats
                except json.JSONDecodeError:
                    pass
            
            # Find output file - look for ZIP files first (Node.js creates ZIP), then GLTF/GLB files
            # First try to find ZIP files with the target platform in the name
            zip_files = list(output_dir.glob(f"*{target}*.zip"))
            
            if zip_files:
                result['output_path'] = str(zip_files[0])
                result['success'] = True
                logger.debug(f"Found ZIP output: {zip_files[0]}")
            else:
                # Fallback to GLTF/GLB files
                output_files = list(output_dir.glob(f"*{target}*"))
                glb_files = [f for f in output_files if f.suffix.lower() == '.glb']
                gltf_files = [f for f in output_files if f.suffix.lower() == '.gltf']
                
                # If no files with target platform, look for any GLTF/GLB files
                if not gltf_files and not glb_files:
                    all_gltf_files = list(output_dir.glob("*.gltf"))
                    all_glb_files = list(output_dir.glob("*.glb"))
                    gltf_files = all_gltf_files
                    glb_files = all_glb_files
                
                if glb_files:
                    result['output_path'] = str(glb_files[0])
                    result['success'] = True
                elif gltf_files:
                    result['output_path'] = str(gltf_files[0])
                    result['success'] = True
                elif output_files:
                    result['output_path'] = str(output_files[0])
                    result['success'] = True
                else:
                    result['success'] = False
                    result['error'] = "No output file generated"
                result['fallback_used'] = True
            
            return result
            
        except Exception as e:
            logger.error(f"Complex processing failed: {e}")
            result['success'] = False
            result['error'] = str(e)
            result['fallback_used'] = True
            return result
    
    def _validate_output_fast(self, output_path: Optional[str]) -> Dict[str, Any]:
        """Fast validation - just check file exists and has content"""
        if not output_path or not Path(output_path).exists():
            return {
                'valid': False,
                'errors': ['Output file not found'],
                'warnings': []
            }
        
        try:
            path_obj = Path(output_path)
            if path_obj.stat().st_size == 0:
                return {
                    'valid': False,
                    'errors': ['Output file is empty'],
                    'warnings': []
                }
            
            return {
                'valid': True,
                'errors': [],
                'warnings': []
            }
                
        except Exception as e:
            logger.error(f"Fast validation failed: {e}")
            return {
                'valid': False,
                'errors': [f"Validation error: {e}"],
                'warnings': []
            }
    
    def _post_validate_output(self, output_path: str, target: str, conversion_path: str, 
                            initial_stats: Dict[str, Any], final_stats: Dict[str, Any]) -> Dict[str, Any]:
        """Comprehensive post-validation based on conversion type"""
        try:
            path_obj = Path(output_path)
            if not path_obj.exists():
                return {
                    'valid': False,
                    'warnings': ['Output file not found for post-validation'],
                    'errors': []
                }
            
            warnings = []
            validation_info = {}
            
            if conversion_path == 'static':
                # Static file validation
                static_validation = self._validate_static_output(path_obj, target, initial_stats, final_stats)
                warnings.extend(static_validation.get('warnings', []))
                validation_info.update(static_validation.get('info', {}))
                
            elif conversion_path in ['complex', 'complex_forced']:
                # Animated file validation
                animated_validation = self._validate_animated_output(path_obj, target, initial_stats, final_stats)
                warnings.extend(animated_validation.get('warnings', []))
                validation_info.update(animated_validation.get('info', {}))
            
            # Common validation for both types
            common_validation = self._validate_common_output(path_obj, target)
            warnings.extend(common_validation.get('warnings', []))
            validation_info.update(common_validation.get('info', {}))
            
            return {
                'valid': True,
                'warnings': warnings,
                'errors': [],
                'validation_info': validation_info
            }
            
        except Exception as e:
            logger.error(f"Post-validation failed: {e}")
            return {
                'valid': False,
                'warnings': [],
                'errors': [f"Post-validation error: {e}"]
            }
    
    def _validate_static_output(self, output_path: Path, target: str, 
                              initial_stats: Dict[str, Any], final_stats: Dict[str, Any]) -> Dict[str, Any]:
        """Validate static file output"""
        warnings = []
        info = {}
        
        try:
            # Check if it's a ZIP file for detailed analysis
            if output_path.suffix.lower() == '.zip':
                import zipfile
                with zipfile.ZipFile(output_path, 'r') as zip_file:
                    file_list = zip_file.namelist()
                    info['zip_files'] = len(file_list)
                    
                    # Check for standard structure
                    has_gltf = any(f.endswith('.gltf') for f in file_list)
                    has_glb = any(f.endswith('.glb') for f in file_list)
                    has_textures = any('texture' in f.lower() or f.endswith(('.png', '.jpg', '.jpeg')) for f in file_list)
                    
                    if not (has_gltf or has_glb):
                        warnings.append("ZIP file missing main GLTF/GLB file")
                    
                    # Count textures from ZIP contents
                    texture_files = [f for f in file_list if f.endswith(('.png', '.jpg', '.jpeg'))]
                    info['textures'] = len(texture_files)
                    
                    # Try to analyze GLTF file inside ZIP for detailed stats
                    gltf_file = None
                    for f in file_list:
                        if f.endswith('.gltf'):
                            gltf_file = f
                            break
                    
                    if gltf_file:
                        try:
                            with zip_file.open(gltf_file) as gltf_data:
                                gltf_content = json.load(gltf_data)
                                
                                materials = gltf_content.get('materials', [])
                                nodes = gltf_content.get('nodes', [])
                                meshes = gltf_content.get('meshes', [])
                                
                                info['materials'] = len(materials)
                                info['nodes'] = len(nodes)
                                info['meshes'] = len(meshes)
                                
                                # Warn if more than 80% nodes collapsed
                                if initial_stats.get('nodes', 0) > 0:
                                    node_reduction = (initial_stats['nodes'] - len(nodes)) / initial_stats['nodes']
                                    if node_reduction > 0.8:
                                        warnings.append(f"High node collapse: {node_reduction:.1%} of nodes were collapsed during optimization")
                                
                                # Check texture optimization
                                if initial_stats.get('textures', 0) > 0:
                                    texture_reduction = (initial_stats['textures'] - len(texture_files)) / initial_stats['textures']
                                    if texture_reduction > 0.5:
                                        warnings.append(f"Significant texture reduction: {texture_reduction:.1%} of textures were optimized")
                                
                                # Check material count
                                if len(materials) > 50:
                                    warnings.append(f"High material count: {len(materials)} materials may impact performance")
                                
                                # Check mesh complexity
                                total_triangles = sum(len(mesh.get('primitives', [])) for mesh in meshes)
                                if total_triangles > 100000:
                                    warnings.append(f"High triangle count: {total_triangles:,} triangles may impact performance")
                        except Exception as e:
                            logger.warning(f"Could not analyze GLTF inside ZIP: {e}")
            
            elif output_path.suffix.lower() == '.gltf':
                # Direct GLTF file analysis
                with open(output_path, 'r') as f:
                    gltf_data = json.load(f)
                
                # Check textures
                textures = gltf_data.get('textures', [])
                materials = gltf_data.get('materials', [])
                nodes = gltf_data.get('nodes', [])
                meshes = gltf_data.get('meshes', [])
                
                info['textures'] = len(textures)
                info['materials'] = len(materials)
                info['nodes'] = len(nodes)
                info['meshes'] = len(meshes)
                
                # Warn if more than 80% nodes collapsed
                if initial_stats.get('nodes', 0) > 0:
                    node_reduction = (initial_stats['nodes'] - len(nodes)) / initial_stats['nodes']
                    if node_reduction > 0.8:
                        warnings.append(f"High node collapse: {node_reduction:.1%} of nodes were collapsed during optimization")
                
                # Check texture optimization
                if initial_stats.get('textures', 0) > 0:
                    texture_reduction = (initial_stats['textures'] - len(textures)) / initial_stats['textures']
                    if texture_reduction > 0.5:
                        warnings.append(f"Significant texture reduction: {texture_reduction:.1%} of textures were optimized")
                
                # Check material count
                if len(materials) > 50:
                    warnings.append(f"High material count: {len(materials)} materials may impact performance")
                
                # Check mesh complexity
                total_triangles = sum(len(mesh.get('primitives', [])) for mesh in meshes)
                if total_triangles > 100000:
                    warnings.append(f"High triangle count: {total_triangles:,} triangles may impact performance")
            
            return {'warnings': warnings, 'info': info}
            
        except Exception as e:
            logger.error(f"Static validation failed: {e}")
            return {'warnings': [f"Static validation error: {e}"], 'info': {}}
    
    def _validate_animated_output(self, output_path: Path, target: str, 
                                initial_stats: Dict[str, Any], final_stats: Dict[str, Any]) -> Dict[str, Any]:
        """Validate animated file output"""
        warnings = []
        info = {}
        
        try:
            if output_path.suffix.lower() == '.gltf':
                with open(output_path, 'r') as f:
                    gltf_data = json.load(f)
                
                # Check rig compatibility
                skins = gltf_data.get('skins', [])
                animations = gltf_data.get('animations', [])
                nodes = gltf_data.get('nodes', [])
                
                info['skins'] = len(skins)
                info['animations'] = len(animations)
                info['nodes'] = len(nodes)
                
                # Check bone count
                total_bones = 0
                for skin in skins:
                    joints = skin.get('joints', [])
                    total_bones += len(joints)
                
                info['total_bones'] = total_bones
                
                if total_bones > 100:
                    warnings.append(f"High bone count: {total_bones} bones may impact performance")
                
                # Check weight normalization
                for skin in skins:
                    if 'inverseBindMatrices' not in skin:
                        warnings.append("Missing inverse bind matrices in skin")
                
                # Check animation count and calculate durations
                if len(animations) > 10:
                    warnings.append(f"High animation count: {len(animations)} animations may impact performance")
                
                # Calculate animation durations
                animation_durations = []
                total_duration = 0
                for i, animation in enumerate(animations):
                    duration = 0
                    channels = animation.get('channels', [])
                    for channel in channels:
                        sampler_idx = channel.get('sampler', 0)
                        if sampler_idx < len(animation.get('samplers', [])):
                            sampler = animation['samplers'][sampler_idx]
                            input_idx = sampler.get('input', 0)
                            if input_idx < len(gltf_data.get('accessors', [])):
                                accessor = gltf_data['accessors'][input_idx]
                                if 'max' in accessor and len(accessor['max']) > 0:
                                    duration = max(duration, accessor['max'][0])
                    
                    animation_durations.append({
                        'name': animation.get('name', f'Animation_{i}'),
                        'duration': duration
                    })
                    total_duration += duration
                
                info['animation_durations'] = animation_durations
                info['total_animation_duration'] = total_duration
                
                # Check for Draco compression
                extensions_used = gltf_data.get('extensionsUsed', [])
                if 'KHR_draco_mesh_compression' in extensions_used:
                    if target == 'unity':
                        warnings.append("Draco compression detected: Unity requires KHR_draco_mesh_compression plugin")
                    info['draco_compression'] = True
                else:
                    info['draco_compression'] = False
                
                # Check rig complexity
                if total_bones > 0 and len(animations) > 0:
                    bones_per_animation = total_bones / len(animations)
                    if bones_per_animation > 50:
                        warnings.append(f"Complex rig: {bones_per_animation:.1f} bones per animation on average")
            
            return {'warnings': warnings, 'info': info}
            
        except Exception as e:
            logger.error(f"Animated validation failed: {e}")
            return {'warnings': [f"Animated validation error: {e}"], 'info': {}}
    
    def _validate_common_output(self, output_path: Path, target: str) -> Dict[str, Any]:
        """Common validation for both static and animated outputs"""
        warnings = []
        info = {}
        
        try:
            # Check file size
            file_size = output_path.stat().st_size
            info['file_size_bytes'] = file_size
            info['file_size_mb'] = round(file_size / (1024 * 1024), 2)
            
            if file_size > 100 * 1024 * 1024:  # 100MB
                warnings.append(f"Large file size: {file_size / (1024 * 1024):.1f}MB may impact loading performance")
            
            # Check for proper file extension
            if target == 'unity' and output_path.suffix.lower() not in ['.gltf', '.glb', '.zip']:
                warnings.append(f"Unexpected file extension for Unity: {output_path.suffix}")
            
            if target == 'roblox' and output_path.suffix.lower() not in ['.gltf', '.glb', '.zip']:
                warnings.append(f"Unexpected file extension for Roblox: {output_path.suffix}")
            
            return {'warnings': warnings, 'info': info}
            
        except Exception as e:
            logger.error(f"Common validation failed: {e}")
            return {'warnings': [f"Common validation error: {e}"], 'info': {}}
    
    def _create_unified_package(self, output_path: str, output_dir: Path, target: str, model_name: str) -> Dict[str, Any]:
        """Create unified ZIP package with standard structure"""
        try:
            import zipfile
            import shutil
            
            # Create package name
            package_name = f"{model_name}_{target}.zip"
            package_path = output_dir / package_name
            
            # Remove existing package if it exists
            if package_path.exists():
                package_path.unlink()
            
            with zipfile.ZipFile(package_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                package_info = {
                    'files': [],
                    'structure': {},
                    'total_size': 0
                }
                
                # Add main model file
                if Path(output_path).exists():
                    try:
                        if Path(output_path).suffix.lower() == '.zip':
                            # If output is already a ZIP, extract and repackage
                            with zipfile.ZipFile(output_path, 'r') as existing_zip:
                                for file_info in existing_zip.filelist:
                                    if not file_info.is_dir():
                                        # Extract to memory and add to new package
                                        file_data = existing_zip.read(file_info.filename)
                                        
                                        # Clean naming for main files
                                        if file_info.filename.endswith('.gltf'):
                                            zip_path = f'{model_name}_{target}.gltf'
                                        elif file_info.filename.endswith('.glb'):
                                            zip_path = f'{model_name}_{target}.glb'
                                        elif file_info.filename.endswith('.bin'):
                                            # Only rename .bin files that contain the model name
                                            if model_name in file_info.filename:
                                                zip_path = f'{model_name}_{target}.bin'
                                            else:
                                                zip_path = file_info.filename
                                        elif file_info.filename.endswith(('.png', '.jpg', '.jpeg')):
                                            zip_path = f'textures/{Path(file_info.filename).name}'
                                        else:
                                            zip_path = file_info.filename
                                        
                                        zip_file.writestr(zip_path, file_data)
                                        package_info['files'].append(zip_path)
                                        package_info['total_size'] += len(file_data)
                        else:
                            # Single file output with clean naming
                            if Path(output_path).suffix.lower() == '.gltf':
                                zip_path = f'{model_name}_{target}.gltf'
                            elif Path(output_path).suffix.lower() == '.glb':
                                zip_path = f'{model_name}_{target}.glb'
                            else:
                                zip_path = Path(output_path).name
                            
                            zip_file.write(output_path, zip_path)
                            package_info['files'].append(zip_path)
                            package_info['total_size'] += Path(output_path).stat().st_size
                    except zipfile.BadZipFile:
                        # If it's not a valid ZIP, treat as regular file
                        if Path(output_path).suffix.lower() == '.gltf':
                            zip_path = f'{model_name}_{target}.gltf'
                        elif Path(output_path).suffix.lower() == '.glb':
                            zip_path = f'{model_name}_{target}.glb'
                        else:
                            zip_path = Path(output_path).name
                        
                        zip_file.write(output_path, zip_path)
                        package_info['files'].append(zip_path)
                        package_info['total_size'] += Path(output_path).stat().st_size
                
                # Add any additional files in output directory with clean structure
                for file_path in output_dir.iterdir():
                    if file_path.is_file() and file_path != package_path:
                        if file_path.suffix.lower() in ['.png', '.jpg', '.jpeg']:
                            zip_path = f'textures/{file_path.name}'
                        elif file_path.suffix.lower() == '.bin' and model_name in file_path.name:
                            zip_path = f'{model_name}_{target}.bin'
                        elif file_path.name == 'voxbridge_report.json':
                            zip_path = 'report.json'
                        else:
                            zip_path = file_path.name
                        
                        zip_file.write(file_path, zip_path)
                        package_info['files'].append(zip_path)
                        package_info['total_size'] += file_path.stat().st_size
                
                # Create standard structure info
                package_info['structure'] = {
                    'model': any(f.endswith(('.gltf', '.glb')) for f in package_info['files']),
                    'textures': any(f.startswith('textures/') for f in package_info['files']),
                    'report': 'report.json' in package_info['files']
                }
            
            return {
                'success': True,
                'package_path': str(package_path),
                'package_info': package_info
            }
            
        except Exception as e:
            logger.error(f"Unified packaging failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'package_info': {}
            }
    
    def _analyze_existing_package(self, package_path: str) -> Dict[str, Any]:
        """Analyze an existing ZIP package"""
        try:
            import zipfile
            
            package_info = {
                'files': [],
                'structure': {},
                'total_size': 0
            }
            
            with zipfile.ZipFile(package_path, 'r') as zip_file:
                for file_info in zip_file.filelist:
                    if not file_info.is_dir():
                        package_info['files'].append(file_info.filename)
                        package_info['total_size'] += file_info.file_size
                
                # Create standard structure info
                package_info['structure'] = {
                    'model': any(f.endswith(('.gltf', '.glb')) for f in package_info['files']),
                    'textures': any(f.startswith('textures/') or f.endswith(('.png', '.jpg', '.jpeg')) for f in package_info['files']),
                    'report': any(f.endswith('report.json') for f in package_info['files'])
                }
            
            return package_info
            
        except Exception as e:
            logger.error(f"Package analysis failed: {e}")
            return {
                'files': [],
                'structure': {},
                'total_size': 0
            }
    
    def _clean_existing_package(self, package_path: str, model_name: str, target: str) -> Dict[str, Any]:
        """Clean an existing ZIP package to remove duplicates and ensure clean structure"""
        try:
            import zipfile
            import tempfile
            import shutil
            
            # Create a temporary clean ZIP
            temp_zip_path = Path(package_path).parent / f"{model_name}_{target}_clean.zip"
            
            with zipfile.ZipFile(package_path, 'r') as source_zip:
                with zipfile.ZipFile(temp_zip_path, 'w', zipfile.ZIP_DEFLATED) as clean_zip:
                    seen_files = set()
                    package_info = {
                        'files': [],
                        'structure': {},
                        'total_size': 0
                    }
                    
                    for file_info in source_zip.filelist:
                        if file_info.is_dir():
                            continue
                            
                        # Skip duplicates
                        if file_info.filename in seen_files:
                            logger.debug(f"Skipping duplicate file: {file_info.filename}")
                            continue
                        seen_files.add(file_info.filename)
                        
                        # Read file data
                        file_data = source_zip.read(file_info.filename)
                        
                        # Determine clean path
                        if file_info.filename.endswith('.gltf'):
                            clean_path = f'{model_name}_{target}.gltf'
                        elif file_info.filename.endswith('.glb'):
                            clean_path = f'{model_name}_{target}.glb'
                        elif file_info.filename.endswith('.bin') and model_name in file_info.filename:
                            clean_path = f'{model_name}_{target}.bin'
                        elif file_info.filename.endswith(('.png', '.jpg', '.jpeg')):
                            clean_path = f'textures/{Path(file_info.filename).name}'
                        elif file_info.filename == 'report.json':
                            clean_path = 'report.json'
                        else:
                            clean_path = file_info.filename
                        
                        # Add to clean ZIP
                        clean_zip.writestr(clean_path, file_data)
                        package_info['files'].append(clean_path)
                        package_info['total_size'] += len(file_data)
                    
                    # Create structure info
                    package_info['structure'] = {
                        'model': any(f.endswith(('.gltf', '.glb')) for f in package_info['files']),
                        'textures': any(f.startswith('textures/') for f in package_info['files']),
                        'report': 'report.json' in package_info['files']
                    }
            
            # Replace original with clean version
            shutil.move(str(temp_zip_path), package_path)
            
            return {
                'success': True,
                'package_path': package_path,
                'package_info': package_info
            }
            
        except Exception as e:
            logger.error(f"Package cleaning failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'package_info': {}
            }

    def _cleanup_intermediate_files(self, output_dir: Path, package_path: str, keep_temp: bool = False):
        """Clean up loose intermediate files, keeping only the package and optional log"""
        if keep_temp:
            logger.debug("Skipping cleanup due to --keep-temp flag")
            return
            
        try:
            package_file = Path(package_path)
            
            for file_path in output_dir.iterdir():
                if file_path.is_file() and file_path != package_file:
                    # Keep only .log files, delete everything else
                    if file_path.suffix.lower() != '.log':
                        file_path.unlink()
                        logger.debug(f"Cleaned up intermediate file: {file_path.name}")
                
        except Exception as e:
            logger.warning(f"Cleanup failed: {e}")
    
    def _embed_report_in_package(self, result: Dict[str, Any], output_dir: Path, debug: bool):
        """Embed the report in the final package"""
        try:
            import zipfile
            import tempfile
            
            package_path = Path(result['output_path'])
            if not package_path.exists() or package_path.suffix.lower() != '.zip':
                return
            
            # Create temporary report file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_report:
                json.dump(result, temp_report, indent=2, default=str)
                temp_report_path = temp_report.name
            
            # Add report to the package
            with zipfile.ZipFile(package_path, 'a', zipfile.ZIP_DEFLATED) as zip_file:
                zip_file.write(temp_report_path, 'report.json')
            
            # Clean up temporary file
            Path(temp_report_path).unlink()
            
            # Only keep loose report if debug mode is enabled
            if not debug:
                loose_report = output_dir / 'voxbridge_report.json'
                if loose_report.exists():
                    loose_report.unlink()
                    logger.debug("Removed loose report file (debug mode disabled)")
            
        except Exception as e:
            logger.warning(f"Failed to embed report in package: {e}")
    
    def _validate_output_comprehensive(self, output_path: Optional[str], target: str) -> Dict[str, Any]:
        """Comprehensive validation with JSON checking"""
        if not output_path or not Path(output_path).exists():
            return {
                'valid': False,
                'errors': ['Output file not found'],
                'warnings': []
            }
        
        try:
            path_obj = Path(output_path)
            if path_obj.stat().st_size == 0:
                return {
                    'valid': False,
                    'errors': ['Output file is empty'],
                    'warnings': []
                }
            
            # Check if it's a valid GLTF/GLB file
            if path_obj.suffix.lower() == '.gltf':
                try:
                    with open(path_obj, 'r') as f:
                        gltf_data = json.load(f)
                    
                    # Basic GLTF structure validation
                    if 'asset' not in gltf_data:
                        return {
                            'valid': False,
                            'errors': ['Invalid GLTF: missing asset information'],
                            'warnings': []
                        }
                    
                    return {
                        'valid': True,
                        'errors': [],
                        'warnings': [],
                        'gltf_info': {
                            'version': gltf_data.get('asset', {}).get('version', 'unknown'),
                            'generator': gltf_data.get('asset', {}).get('generator', 'unknown'),
                            'meshes': len(gltf_data.get('meshes', [])),
                            'materials': len(gltf_data.get('materials', [])),
                            'textures': len(gltf_data.get('textures', [])),
                            'animations': len(gltf_data.get('animations', []))
                        }
                    }
                except json.JSONDecodeError as e:
                    return {
                        'valid': False,
                        'errors': [f'Invalid JSON in GLTF file: {e}'],
                        'warnings': []
                    }
            elif path_obj.suffix.lower() == '.glb':
                # GLB files are binary, just check they exist and have content
                return {
                    'valid': True,
                    'errors': [],
                    'warnings': [],
                    'glb_info': {
                        'size_bytes': path_obj.stat().st_size,
                        'type': 'binary_gltf'
                    }
                }
            else:
                return {
                    'valid': True,
                    'errors': [],
                    'warnings': ['Unknown file type, assuming valid']
                }
                
        except Exception as e:
            logger.error(f"Comprehensive validation failed: {e}")
            return {
                'valid': False,
                'errors': [f"Validation error: {e}"],
                'warnings': []
            }
    
    def _validate_with_node(self, output_path: str) -> Dict[str, Any]:
        """Validate using Node.js validation script"""
        try:
            node_runner_path = get_node_runner_path()
            
            cmd = [str(node_runner_path), 'validate', '--input', output_path]
            
            process_result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=node_script.parent
            )
            
            if process_result.returncode == 0:
                # Try to parse validation report
                report_path = Path(output_path).parent / 'validation_report.json'
                if report_path.exists():
                    with open(report_path, 'r') as f:
                        return json.load(f)
                else:
                    return {'valid': True, 'errors': [], 'warnings': []}
            else:
                return {
                    'valid': False,
                    'errors': [process_result.stderr],
                    'warnings': []
                }
                
        except Exception as e:
            logger.error(f"Node.js validation failed: {e}")
            return self._validate_basic(output_path)
    
    def _validate_basic(self, output_path: str) -> Dict[str, Any]:
        """Basic validation without Node.js"""
        try:
            # Check if file exists and is readable
            path_obj = Path(output_path)
            if not path_obj.exists():
                return {'valid': False, 'errors': ['File does not exist'], 'warnings': []}
            
            # Check file size
            if path_obj.stat().st_size == 0:
                return {'valid': False, 'errors': ['File is empty'], 'warnings': []}
            
            # For GLTF files, try to parse as JSON
            if path_obj.suffix.lower() == '.gltf':
                with open(path_obj, 'r') as f:
                    json.load(f)
            # For GLB files, just check that they exist and have content
            elif path_obj.suffix.lower() == '.glb':
                # GLB files are binary, so we just check they exist and have content
                pass
            
            return {'valid': True, 'errors': [], 'warnings': []}
            
        except json.JSONDecodeError:
            return {'valid': False, 'errors': ['Invalid JSON format'], 'warnings': []}
        except Exception as e:
            return {'valid': False, 'errors': [f'Validation error: {e}'], 'warnings': []}
    
    def _calculate_improvements(self, initial_stats: Dict[str, Any], 
                              final_stats: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate improvement metrics"""
        improvements = {}
        
        # File size improvement
        if 'estimated_size_bytes' in initial_stats and 'estimated_size_bytes' in final_stats:
            initial_size = initial_stats['estimated_size_bytes']
            final_size = final_stats['estimated_size_bytes']
            if initial_size > 0:
                improvements['size_reduction_percent'] = ((initial_size - final_size) / initial_size) * 100
        
        # Triangle count improvement
        if 'triangles' in initial_stats and 'triangles' in final_stats:
            initial_triangles = initial_stats['triangles']
            final_triangles = final_stats['triangles']
            if initial_triangles > 0:
                improvements['triangle_reduction_percent'] = ((initial_triangles - final_triangles) / initial_triangles) * 100
        
        # Mesh count change
        if 'meshes' in initial_stats and 'meshes' in final_stats:
            improvements['mesh_count_change'] = final_stats['meshes'] - initial_stats['meshes']
        
        return improvements
    
    def _check_node_availability(self) -> bool:
        """Check if Node.js is available (either system node or bundled node_runner)"""
        try:
            # First try bundled node_runner
            node_runner_path = get_node_runner_path()
            if node_runner_path.exists():
                # Ensure it's executable
                if ensure_executable(node_runner_path):
                    # Test if it works
                    result = subprocess.run([str(node_runner_path), '--version'], 
                                          capture_output=True, text=True, timeout=10)
                    if result.returncode == 0:
                        logger.info(f"Using bundled Node.js runner: {node_runner_path}")
                        return True
            
            # Fallback to system node
            result = subprocess.run(['node', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                logger.info("Using system Node.js")
                return True
                
            return False
        except (FileNotFoundError, subprocess.TimeoutExpired, Exception) as e:
            logger.warning(f"Node.js not available: {e}")
            return False
    
    def get_conversion_stats(self) -> Dict[str, Any]:
        """Get the last conversion statistics"""
        return self.conversion_stats
