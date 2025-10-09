"""
Unified Pipeline Runner for VoxBridge
Handles convert, batch, and benchmark commands with consistent Node.js/Python fallback logic
"""

import json
import logging
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn

from .orchestrated_converter import OrchestratedConverter
from .utils.detect import is_complex_gltf

logger = logging.getLogger(__name__)
console = Console(emoji=False, width=80)

class UnifiedPipelineRunner:
    """Unified pipeline runner for all VoxBridge commands"""
    
    def __init__(self, debug: bool = False):
        self.debug = debug
        self.converter = OrchestratedConverter(debug=debug)
    
    def run_pipeline(self, mode: str, input_path: Path, output_path: Path, 
                    target: str = "unity", options: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Run the unified pipeline for any mode (convert, batch, benchmark)
        
        Args:
            mode: Pipeline mode ('convert', 'batch', 'benchmark')
            input_path: Input file or directory path
            output_path: Output file or directory path
            target: Target platform ('unity', 'roblox')
            options: Additional options
            
        Returns:
            Dict with pipeline results
        """
        if options is None:
            options = {}
        
        start_time = time.time()
        
        # Initialize result structure
        result = {
            'mode': mode,
            'input': str(input_path),
            'output': str(output_path),
            'target': target,
            'start_time': start_time,
            'success': False,
            'error': None,
            'warnings': [],
            'fallback_used': False,
            'node_js_attempted': False,
            'processing_time': 0
        }
        
        try:
            if mode == 'convert':
                result = self._run_convert_pipeline(input_path, output_path, target, options, result)
            elif mode == 'batch':
                result = self._run_batch_pipeline(input_path, output_path, target, options, result)
            elif mode == 'benchmark':
                result = self._run_benchmark_pipeline(input_path, output_path, target, options, result)
            else:
                result['error'] = f"Unknown pipeline mode: {mode}"
                return result
            
            result['processing_time'] = time.time() - start_time
            return result
            
        except Exception as e:
            result['success'] = False
            result['error'] = str(e)
            result['processing_time'] = time.time() - start_time
            logger.error(f"Pipeline failed: {e}")
            return result
    
    def _run_convert_pipeline(self, input_path: Path, output_path: Path, 
                             target: str, options: Dict[str, Any], result: Dict[str, Any]) -> Dict[str, Any]:
        """Run convert pipeline with unified Node.js/Python handling"""
        
        # Ensure output directory exists
        if output_path.is_file():
            output_dir = output_path.parent
        else:
            output_dir = output_path
            output_dir.mkdir(parents=True, exist_ok=True)
        
        # Use orchestrated converter with unified pipeline
        conversion_result = self.converter.convert_file(input_path, output_dir, target, options)
        
        # Map orchestrated converter result to unified result
        result.update({
            'success': conversion_result.get('success', False),
            'error': conversion_result.get('error'),
            'warnings': conversion_result.get('warnings', []),
            'fallback_used': conversion_result.get('fallback_used', False),
            'node_js_attempted': self.converter.node_available,
            'conversion_path': conversion_result.get('conversion_path'),
            'complex_mode': conversion_result.get('complex_mode', False),
            'output_path': conversion_result.get('output_path'),
            'package_info': conversion_result.get('package_info', {}),
            'post_validation': conversion_result.get('post_validation', {}),
            'texture_fixes': conversion_result.get('texture_fixes'),
            'extension_fallbacks': conversion_result.get('extension_fallbacks', [])
        })
        
        return result
    
    def _run_batch_pipeline(self, input_dir: Path, output_dir: Path, 
                           target: str, options: Dict[str, Any], result: Dict[str, Any]) -> Dict[str, Any]:
        """Run batch pipeline with unified handling"""
        
        # Find all GLB files
        glb_files = list(input_dir.glob("*.glb"))
        if not glb_files:
            result['error'] = f"No GLB files found in '{input_dir}'"
            return result
        
        result['files_found'] = len(glb_files)
        result['files_processed'] = []
        result['files_failed'] = []
        
        success_count = 0
        
        for glb_file in glb_files:
            file_output_dir = output_dir / glb_file.stem
            
            # Process each file using unified pipeline
            file_result = self._run_convert_pipeline(
                glb_file, file_output_dir, target, options, 
                {'mode': 'convert', 'start_time': time.time()}
            )
            
            if file_result['success']:
                success_count += 1
                result['files_processed'].append({
                    'file': str(glb_file),
                    'output': file_result.get('output_path'),
                    'processing_time': file_result.get('processing_time', 0)
                })
            else:
                result['files_failed'].append({
                    'file': str(glb_file),
                    'error': file_result.get('error', 'Unknown error')
                })
        
        result['success'] = success_count > 0
        result['success_count'] = success_count
        result['total_count'] = len(glb_files)
        
        return result
    
    def _run_benchmark_pipeline(self, input_dir: Path, output_dir: Path, 
                               target: str, options: Dict[str, Any], result: Dict[str, Any]) -> Dict[str, Any]:
        """Run benchmark pipeline with unified handling"""
        
        # Find all GLB files
        glb_files = list(input_dir.glob("*.glb"))
        if not glb_files:
            result['error'] = f"No GLB files found in '{input_dir}'"
            return result
        
        result['files_found'] = len(glb_files)
        result['benchmark_results'] = {}
        
        # Enable optimizations for benchmarking
        benchmark_options = options.copy()
        benchmark_options.update({
            'optimize_mesh': True,
            'use_draco': True,
            'quantize': True
        })
        
        for glb_file in glb_files:
            file_output_dir = output_dir / f"{glb_file.stem}_benchmark"
            
            # Get initial stats
            initial_stats = self._get_file_stats(glb_file)
            
            # Process file with optimizations
            file_result = self._run_convert_pipeline(
                glb_file, file_output_dir, target, benchmark_options,
                {'mode': 'benchmark', 'start_time': time.time()}
            )
            
            if file_result['success']:
                # Get final stats
                final_stats = self._get_file_stats(Path(file_result.get('output_path', '')))
                
                # Calculate improvements
                improvements = self._calculate_improvements(initial_stats, final_stats)
                
                result['benchmark_results'][glb_file.stem] = {
                    'initial_stats': initial_stats,
                    'final_stats': final_stats,
                    'improvements': improvements,
                    'processing_time': file_result.get('processing_time', 0),
                    'optimizations_applied': file_result.get('extension_fallbacks', [])
                }
        
        result['success'] = len(result['benchmark_results']) > 0
        
        return result
    
    def _get_file_stats(self, file_path: Path) -> Dict[str, Any]:
        """Get file statistics"""
        try:
            if not file_path.exists():
                return {}
            
            stats = {
                'file_size': file_path.stat().st_size,
                'file_type': file_path.suffix.upper()
            }
            
            # Try to get GLTF stats if it's a GLTF/GLB file
            if file_path.suffix.lower() in ['.gltf', '.glb']:
                try:
                    from .utils.detect import get_file_stats
                    gltf_stats = get_file_stats(file_path)
                    stats.update(gltf_stats)
                except Exception:
                    pass
            
            return stats
            
        except Exception as e:
            logger.warning(f"Could not get file stats for {file_path}: {e}")
            return {}
    
    def _calculate_improvements(self, initial_stats: Dict[str, Any], 
                              final_stats: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate improvement metrics"""
        improvements = {}
        
        # File size improvement
        if 'file_size' in initial_stats and 'file_size' in final_stats:
            initial_size = initial_stats['file_size']
            final_size = final_stats['file_size']
            if initial_size > 0:
                size_reduction = ((initial_size - final_size) / initial_size) * 100
                improvements['file_size_reduction_percent'] = size_reduction
        
        # Triangle count improvement
        if 'triangles_estimated' in initial_stats and 'triangles_estimated' in final_stats:
            initial_triangles = initial_stats['triangles_estimated']
            final_triangles = final_stats['triangles_estimated']
            if initial_triangles > 0:
                triangle_reduction = ((initial_triangles - final_triangles) / initial_triangles) * 100
                improvements['triangle_reduction_percent'] = triangle_reduction
        
        return improvements

def run_unified_pipeline(mode: str, input_path: Path, output_path: Path, 
                        target: str = "unity", options: Dict[str, Any] = None,
                        debug: bool = False) -> Dict[str, Any]:
    """
    Unified pipeline entry point for all VoxBridge commands
    
    Args:
        mode: Pipeline mode ('convert', 'batch', 'benchmark')
        input_path: Input file or directory path
        output_path: Output file or directory path
        target: Target platform ('unity', 'roblox')
        options: Additional options
        debug: Enable debug logging
        
    Returns:
        Dict with pipeline results
    """
    runner = UnifiedPipelineRunner(debug=debug)
    return runner.run_pipeline(mode, input_path, output_path, target, options)
