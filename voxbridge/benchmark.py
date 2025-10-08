"""
VoxBridge Benchmark Module
Tracks optimization metrics and performance improvements for 3D models
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import hashlib

class ModelBenchmark:
    """Benchmarks 3D model optimization and conversion performance"""
    
    def __init__(self, debug: bool = False):
        self.debug = debug
        self.benchmark_results = {}
        self.test_assets = []
        
    def add_test_asset(self, name: str, file_path: Path, category: str):
        """Add a test asset for benchmarking"""
        self.test_assets.append({
            'name': name,
            'path': file_path,
            'category': category,
            'original_stats': None,
            'optimized_stats': None
        })
        
    def measure_model_stats(self, gltf_path: Path) -> Dict:
        """Measure model statistics from GLTF file"""
        try:
            import json
            
            with open(gltf_path, 'r', encoding='utf-8') as f:
                gltf_data = json.load(f)
            
            # Calculate file size
            file_size = gltf_path.stat().st_size
            
            # Count meshes, materials, textures, nodes
            mesh_count = len(gltf_data.get('meshes', []))
            material_count = len(gltf_data.get('materials', []))
            texture_count = len(gltf_data.get('textures', []))
            node_count = len(gltf_data.get('nodes', []))
            
            # Calculate total triangle count
            total_triangles = 0
            for mesh in gltf_data.get('meshes', []):
                for primitive in mesh.get('primitives', []):
                    if 'indices' in primitive and primitive['indices'] is not None:
                        # Each triangle has 3 indices
                        triangle_count = len(primitive['indices']) // 3
                        total_triangles += triangle_count
            
            # Calculate texture memory usage
            texture_memory = 0
            for image in gltf_data.get('images', []):
                if 'uri' in image and image['uri']:
                    img_path = gltf_path.parent / image['uri']
                    if img_path.exists():
                        try:
                            from PIL import Image
                            with Image.open(img_path) as img:
                                # Estimate memory usage (RGBA = 4 bytes per pixel)
                                texture_memory += img.width * img.height * 4
                        except:
                            pass
            
            return {
                'file_size': file_size,
                'mesh_count': mesh_count,
                'material_count': material_count,
                'texture_count': texture_count,
                'node_count': node_count,
                'total_triangles': total_triangles,
                'texture_memory': texture_memory,
                'timestamp': time.time()
            }
            
        except Exception as e:
            if self.debug:
                print(f"Warning: Could not measure model stats: {e}")
            return {}
    
    def run_optimization_benchmark(self, asset_name: str, original_path: Path, 
                                 optimized_path: Path) -> Dict:
        """Run benchmark comparison between original and optimized models"""
        try:
            # Measure original model
            original_stats = self.measure_model_stats(original_path)
            
            # Measure optimized model
            optimized_stats = self.measure_model_stats(optimized_path)
            
            # Calculate improvements
            improvements = {}
            for key in ['file_size', 'total_triangles', 'texture_memory']:
                if key in original_stats and key in optimized_stats:
                    if original_stats[key] > 0:
                        improvement_pct = ((original_stats[key] - optimized_stats[key]) / original_stats[key]) * 100
                        improvements[f'{key}_improvement_pct'] = improvement_pct
                        improvements[f'{key}_reduction'] = original_stats[key] - optimized_stats[key]
            
            benchmark_result = {
                'asset_name': asset_name,
                'original_stats': original_stats,
                'optimized_stats': optimized_stats,
                'improvements': improvements,
                'benchmark_timestamp': time.time()
            }
            
            self.benchmark_results[asset_name] = benchmark_result
            
            if self.debug:
                print(f"Benchmark completed for {asset_name}")
                print(f"File size: {original_stats.get('file_size', 0)} -> {optimized_stats.get('file_size', 0)} bytes")
                print(f"Triangles: {original_stats.get('total_triangles', 0)} -> {optimized_stats.get('total_triangles', 0)}")
                print(f"Improvements: {improvements}")
            
            return benchmark_result
            
        except Exception as e:
            if self.debug:
                print(f"Warning: Benchmark failed for {asset_name}: {e}")
            return {}
    
    def generate_benchmark_report(self, output_path: Path) -> bool:
        """Generate comprehensive benchmark report"""
        try:
            if not self.benchmark_results:
                if self.debug:
                    print("No benchmark results to report")
                return False
            
            report = {
                'benchmark_summary': {
                    'total_assets_tested': len(self.benchmark_results),
                    'benchmark_timestamp': time.time(),
                    'overall_improvements': {}
                },
                'asset_results': self.benchmark_results,
                'category_summary': {}
            }
            
            # Calculate overall improvements
            total_improvements = {}
            for asset_name, result in self.benchmark_results.items():
                for key, value in result.get('improvements', {}).items():
                    if key not in total_improvements:
                        total_improvements[key] = []
                    total_improvements[key].append(value)
            
            # Calculate averages
            for key, values in total_improvements.items():
                if values:
                    report['benchmark_summary']['overall_improvements'][key] = {
                        'average': sum(values) / len(values),
                        'min': min(values),
                        'max': max(values)
                    }
            
            # Generate category summary
            categories = {}
            for asset in self.test_assets:
                category = asset['category']
                if category not in categories:
                    categories[category] = []
                categories[category].append(asset['name'])
            
            report['category_summary'] = categories
            
            # Save report
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2)
            
            if self.debug:
                print(f"Benchmark report saved to: {output_path}")
            
            return True
            
        except Exception as e:
            if self.debug:
                print(f"Warning: Could not generate benchmark report: {e}")
            return False
    
    def get_benchmark_summary(self) -> str:
        """Get a human-readable summary of benchmark results"""
        if not self.benchmark_results:
            return "No benchmark results available"
        
        summary_lines = []
        summary_lines.append("=== VoxBridge Optimization Benchmark Summary ===")
        summary_lines.append(f"Total assets tested: {len(self.benchmark_results)}")
        
        # Overall improvements
        if 'benchmark_summary' in self.benchmark_results.get(list(self.benchmark_results.keys())[0], {}):
            overall = self.benchmark_results[list(self.benchmark_results.keys())[0]]['benchmark_summary'].get('overall_improvements', {})
            for metric, stats in overall.items():
                if isinstance(stats, dict) and 'average' in stats:
                    summary_lines.append(f"{metric}: {stats['average']:.1f}% average improvement")
        
        # Asset-specific results
        summary_lines.append("\nAsset Results:")
        for asset_name, result in self.benchmark_results.items():
            summary_lines.append(f"\n{asset_name}:")
            improvements = result.get('improvements', {})
            for metric, value in improvements.items():
                if 'improvement_pct' in metric:
                    summary_lines.append(f"  {metric}: {value:.1f}%")
        
        return "\n".join(summary_lines)
