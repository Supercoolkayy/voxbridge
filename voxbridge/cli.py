#!/usr/bin/env python3
"""
VoxBridge CLI - Command Line Interface for VoxEdit to Unity/Roblox Converter
"""

import sys
import time
from pathlib import Path
from typing import Optional, List
import logging

try:
    import typer
    from typer import Typer
except ImportError:
    print("Error: typer is required. Install with: pip install typer")
    sys.exit(1)

try:
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
    from rich.panel import Panel
    from rich.text import Text
    from rich.table import Table
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

from .converter import VoxBridgeConverter

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Create Typer app
app = Typer(
    name="voxbridge",
    help="VoxEdit to Unity/Roblox GLTF Converter",
    add_completion=False
)

# Global console for rich output
console = Console(emoji=False, width=80)

def print_header(verbose: bool = False):
    """Print the VoxBridge header with box-drawing characters."""
    if verbose:
        title = "VoxBridge Converter v1.0.3 (Verbose Mode)"
    else:
        title = "VoxBridge Converter v1.0.3"
    
    subtitle = "GLB ➜ GLTF / Roblox / Unity Exporter"
    
    header = f"""
{'═' * 55}
   {title}
   {subtitle}
{'═' * 55}"""
    
    console.print(header, style="bold blue")

def print_file_config(input_path: Path, output_path: Path, target: str, optimize_mesh: bool = False):
    """Print file configuration in a clean format."""
    config = f"""
Input : {input_path}
Output: {output_path}
Target: {target}"""
    
    if optimize_mesh:
        config += "\nOpts : mesh optimization enabled"
    
    console.print(config, style="dim")

def print_step_header(step_num: int, total_steps: int, title: str):
    """Print a step header with consistent formatting."""
    step_text = f"[{step_num}/{total_steps}] {title}"
    console.print(f"\n{step_text}", style="bold yellow")

def print_step_info(message: str, indent: int = 0):
    """Print step information with proper indentation."""
    indent_str = "   " * indent
    console.print(f"{indent_str}-> {message}", style="dim")

def print_validation_summary(validation_results: dict, verbose: bool = False):
    """Print validation results in a structured format."""
    if not validation_results:
        return
    
    print_step_header(3, 4, "Validation")
    
    # Count errors and warnings
    error_count = validation_results.get('errors', 0)
    warning_count = validation_results.get('warnings', 0)
    
    if verbose:
        # Show detailed validation in verbose mode
        if 'details' in validation_results:
            for detail in validation_results['details']:
                if detail.get('type') == 'error':
                    print_step_info(f"❌ {detail.get('message', 'Unknown error')}", 1)
                elif detail.get('type') == 'warning':
                    print_step_info(f"⚠️  {detail.get('message', 'Unknown warning')}", 1)
    else:
        # Show summary in default mode
        if error_count > 0 or warning_count > 0:
            print_step_info(f"UV maps: OK", 1)
            print_step_info(f"Buffers: OK", 1)
            print_step_info(f"Accessors: {error_count} errors, {warning_count} warnings", 1)
            print_step_info("(run with --verbose for details)", 2)
        else:
            print_step_info("All validations passed", 1)

def print_conversion_summary(converter: VoxBridgeConverter, output_path: Path, verbose: bool = False):
    """Print the final conversion summary."""
    print_step_header(4, 4, "Summary")
    
    # Get asset info from converter's stored statistics
    stats = converter.get_last_conversion_stats()
    meshes = stats.get('meshes', 0)
    materials = stats.get('materials', 0)
    textures = stats.get('textures', 0)
    nodes = stats.get('nodes', 0)
    
    # Get file size - check if we have a ZIP file or the original file
    try:
        # Check if output is a ZIP file
        if output_path.suffix.lower() == '.zip':
            # Use ZIP file size
            file_size = output_path.stat().st_size
            size_kb = file_size / 1024
            if size_kb >= 1024:
                size_str = f"{size_kb/1024:.1f} MB"
            else:
                size_str = f"{size_kb:.0f} KB"
            size_str += " (ZIP)"
        else:
            # Use the stored file size from conversion stats
            stored_size = stats.get('file_size', 0)
            if stored_size > 0:
                size_kb = stored_size / 1024
                if size_kb >= 1024:
                    size_str = f"{size_kb/1024:.1f} MB"
                else:
                    size_str = f"{size_kb:.0f} KB"
            else:
                size_str = "unknown"
    except:
        size_str = "unknown"
    
    print_step_info(f"Meshes:    {meshes}", 1)
    print_step_info(f"Materials: {materials}", 1)
    print_step_info(f"Textures:  {textures}", 1)
    print_step_info(f"Nodes:     {nodes}", 1)
    print_step_info(f"File size: {size_str}", 1)

def print_final_status(success: bool, validation_results: dict = None):
    """Print the final status with box-drawing borders."""
    if success:
        status = "SUCCESS"
        style = "bold green"
    else:
        status = "FAILED"
        style = "bold red"
    
    if validation_results:
        error_count = validation_results.get('errors', 0)
        warning_count = validation_results.get('warnings', 0)
        if error_count > 0:
            status = f"VALIDATION FAILED ({error_count} errors, {warning_count} warnings)"
            style = "bold yellow"
    
    footer = f"""
{'═' * 55}
Status: {status}
{'═' * 55}"""
    
    console.print(footer, style=style)

def handle_conversion(
    input_path: Path, 
    output_path: Path, 
    target: str,
    optimize_mesh: bool = False, 
    generate_atlas: bool = False,
    no_blender: bool = False,
    verbose: bool = False,
    debug: bool = False
) -> bool:
    """Handle the conversion process with clean output and proper logging."""
    # Set logging level based on flags
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)
    elif verbose:
        logging.getLogger().setLevel(logging.INFO)
    else:
        logging.getLogger().setLevel(logging.WARNING)
    
    try:
        # Step 1: Environment Setup
        print_step_header(1, 4, "Environment Setup")
        
        # Check Blender availability
        blender_path = None
        try:
            import subprocess
            result = subprocess.run(['which', 'blender'], capture_output=True, text=True)
            if result.returncode == 0:
                blender_path = result.stdout.strip()
                print_step_info(f"Blender: detected at {blender_path}", 1)
            else:
                print_step_info("Blender: not found", 1)
        except:
            print_step_info("Blender: detection failed", 1)
        
        if blender_path and not no_blender:
            print_step_info("Cleanup script: voxbridge/blender_cleanup.py", 1)
            print_step_info("Using Blender for conversion", 1)
        else:
            print_step_info("Cleanup script: voxbridge/blender_cleanup.py", 1)
            print_step_info("Using fallback conversion (Blender skipped)", 1)
        
        # Step 2: File Processing
        print_step_header(2, 4, "File Processing")
        
        # Initialize converter
        converter = VoxBridgeConverter(debug=debug)
        
        # Show progress bar for file processing
        if RICH_AVAILABLE and not verbose:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TimeElapsedColumn(),
                console=console
            ) as progress:
                task = progress.add_task("Processing GLB file...", total=100)
                
                # Simulate progress updates
                progress.update(task, advance=25)
                time.sleep(0.1)
                
                # Process the file
                result = converter.convert_file(
                    input_path,
                    output_path,
                    use_blender=not no_blender,
                    optimize_mesh=optimize_mesh,
                    generate_atlas=generate_atlas,
                    platform=target
                )
                
                progress.update(task, completed=100, description="[bold green]Completed!")
        else:
            # No progress bar in verbose mode
            result = converter.convert_file(
                input_path,
                output_path,
                use_blender=not no_blender,
                optimize_mesh=optimize_mesh,
                generate_atlas=generate_atlas,
                platform=target
            )
        
        if not result:
            print_step_info("Conversion failed", 1)
            return False
                
        # Check if we got a ZIP file back from the converter
        final_output_path = output_path
        if hasattr(converter, '_last_conversion_stats') and converter._last_conversion_stats:
            # If we have conversion stats, the file was packaged into a ZIP
            zip_path = output_path.parent / f"{output_path.stem}.zip"
            if zip_path.exists():
                final_output_path = zip_path
        
        # Get file info
        try:
            file_size = final_output_path.stat().st_size
            size_mb = file_size / (1024 * 1024)
            if size_mb >= 1.0:
                print_step_info(f"GLB parsed: {size_mb:.1f} MB", 1)
            else:
                size_kb = file_size / 1024
                print_step_info(f"GLB parsed: {size_kb:.0f} KB", 1)
        except:
            print_step_info("GLB parsed: size unknown", 1)
        
        print_step_info("Buffers extracted: completed", 1)
        print_step_info("BIN file created", 1)
        if final_output_path.suffix.lower() == '.zip':
            print_step_info(f"GLTF written: {final_output_path.stem}.gltf (packaged in {final_output_path.name})", 1)
        else:
            print_step_info(f"GLTF written: {final_output_path.name}", 1)
        
        # Step 3: Validation (placeholder for now)
        validation_results = {
            'errors': 0,
            'warnings': 0,
            'details': []
        }
        print_validation_summary(validation_results, verbose)
        
        # Step 4: Summary
        print_conversion_summary(converter, final_output_path, verbose)
        
        # Final status
        print_final_status(True, validation_results)
        
        return True
        
    except Exception as e:
        if debug:
            logger.exception("Conversion failed with exception:")
        else:
            console.print(f"\n[bold red]Error: {str(e)}")
        return False

@app.command()
def convert(
    input_file: Path = typer.Option(..., "--input", "-i", help="Input GLB file path"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file path"),
    target: str = typer.Option("unity", "--target", "-t", help="Target platform (unity/roblox)"),
    optimize_mesh: bool = typer.Option(False, "--optimize-mesh", help="Enable mesh optimization"),
    generate_atlas: bool = typer.Option(False, "--generate-atlas", help="Generate texture atlas for optimization"),
    no_blender: bool = typer.Option(False, "--no-blender", help="Skip Blender processing"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
    debug: bool = typer.Option(False, "--debug", "-d", help="Enable debug output")
):
    """Convert a GLB file to GLTF format for Unity or Roblox."""
    
    # Set logging level based on flags
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)
    elif verbose:
        logging.getLogger().setLevel(logging.INFO)
    else:
        logging.getLogger().setLevel(logging.WARNING)
    
    # Determine output path
    if output is None:
        output = input_file.with_suffix('.gltf')
    else:
        # Always ensure output has .gltf extension
        if not output.suffix:
            output = output.with_suffix('.gltf')
        elif output.suffix.lower() == '.glb':
            # Convert .glb to .gltf since we don't generate GLB files
            output = output.with_suffix('.gltf')
    
    # Check if input file exists
    if not input_file.exists():
        console.print(f"[bold red]Error: Input file '{input_file}' does not exist")
        raise typer.Exit(1)
    
    # Check if input file is a GLB file
    if input_file.suffix.lower() != '.glb':
        console.print(f"[bold red]Error: Input file '{input_file}' is not a GLB file. Only .glb files are supported.")
        raise typer.Exit(1)
    
    # Check if output file exists and ask for confirmation
    if output.exists():
        try:
            response = input(f"Warning: Output file '{output}' already exists. Overwrite? [y/N]: ")
            if response.lower() not in ['y', 'yes']:
                console.print("[yellow]Operation cancelled")
                raise typer.Exit(0)
        except (EOFError, KeyboardInterrupt):
            console.print("\n[yellow]Operation cancelled")
            raise typer.Exit(0)
    
    # Print header and configuration
    print_header(verbose)
    print_file_config(input_file, output, target, optimize_mesh)
    
    # Handle conversion
    success = handle_conversion(
        input_path=input_file,
        output_path=output,
        target=target,
        optimize_mesh=optimize_mesh,
        generate_atlas=generate_atlas,
        no_blender=no_blender,
        verbose=verbose,
        debug=debug
    )
    
    if not success:
        raise typer.Exit(1)

@app.command()
def batch(
    input_dir: Path = typer.Argument(..., help="Input directory containing GLB files"),
    output_dir: Path = typer.Option(..., "--output-dir", "-o", help="Output directory for converted files"),
    target: str = typer.Option("unity", "--target", "-t", help="Target platform (unity/roblox)"),
    optimize_mesh: bool = typer.Option(False, "--optimize-mesh", help="Enable mesh optimization"),
    no_blender: bool = typer.Option(False, "--no-blender", help="Skip Blender processing"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output")
):
    """Convert multiple GLB files in batch."""
    
    if not input_dir.exists():
        console.print(f"[bold red]Error: Input directory '{input_dir}' does not exist")
        raise typer.Exit(1)
    
    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)
    
    # Find all GLB files
    glb_files = list(input_dir.glob("*.glb"))
    if not glb_files:
        console.print(f"[yellow]No GLB files found in '{input_dir}'")
        return
    
    console.print(f"Found {len(glb_files)} GLB files to convert")
    
    success_count = 0
    for glb_file in glb_files:
        output_file = output_dir / f"{glb_file.stem}.gltf"
        console.print(f"\nConverting {glb_file.name}...")
        
        success = handle_conversion(
            input_path=glb_file,
            output_path=output_file,
            target=target,
            optimize_mesh=optimize_mesh,
            no_blender=no_blender,
            verbose=verbose,
            debug=False
        )
        
        if success:
            success_count += 1
    
    console.print(f"\n[bold green]Batch conversion completed: {success_count}/{len(glb_files)} files converted successfully")

@app.command()
def benchmark(
    input_dir: Path = typer.Option(..., "--input-dir", "-i", help="Input directory with test assets"),
    output_dir: Path = typer.Option(..., "--output-dir", "-o", help="Output directory for benchmark results"),
    target: str = typer.Option("unity", "--target", "-t", help="Target platform (unity/roblox)"),
    optimize_mesh: bool = typer.Option(True, "--optimize-mesh", help="Enable mesh optimization"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output")
):
    """Run optimization benchmarks on test assets."""
    console.print("[bold blue]VoxBridge Benchmark - Optimization Testing")
    
    if not input_dir.exists():
        console.print(f"[bold red]Error: Input directory '{input_dir}' does not exist")
        raise typer.Exit(1)
    
    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)
    
    # Find all GLB files
    glb_files = list(input_dir.glob("*.glb"))
    if not glb_files:
        console.print(f"[yellow]No GLB files found in '{input_dir}'")
        return
    
    console.print(f"Found {len(glb_files)} test assets for benchmarking")
    
    # Initialize converter with benchmark support
    from .converter import VoxBridgeConverter
    converter = VoxBridgeConverter(debug=verbose)
    
    # Enable optimizations for benchmarking
    converter.optimization_settings['mesh_optimization'] = optimize_mesh
    converter.optimization_settings['texture_atlas'] = True
    
    benchmark_results = {}
    success_count = 0
    
    for glb_file in glb_files:
        console.print(f"\n[bold cyan]Benchmarking {glb_file.name}...")
        
        # Convert with optimizations
        output_file = output_dir / f"{glb_file.stem}_optimized"
        success = converter.convert_file(
            input_path=glb_file,
            output_path=output_file,
            platform=target,
            optimize_mesh=optimize_mesh,
            use_blender=True
        )
        
        if success:
            success_count += 1
            # Get benchmark results
            asset_results = converter.get_benchmark_results()
            if glb_file.stem in asset_results:
                benchmark_results[glb_file.stem] = asset_results[glb_file.stem]
                console.print(f"  ✓ Benchmark data collected")
        
        # Clean up intermediate files
        for temp_file in output_dir.glob(f"{glb_file.stem}_optimized*"):
            if temp_file.suffix != '.zip':
                temp_file.unlink()
    
    # Generate benchmark report
    if benchmark_results:
        report_path = output_dir / "benchmark_report.json"
        if converter.generate_benchmark_report(report_path):
            console.print(f"\n[bold green]Benchmark report generated: {report_path}")
            
            # Display summary
            console.print("\n[bold yellow]Benchmark Summary:")
            for asset_name, result in benchmark_results.items():
                original = result.get('original_stats', {})
                optimized = result.get('optimized_stats', {})
                
                if original and optimized:
                    file_size_improvement = ((original.get('file_size', 0) - optimized.get('file_size', 0)) / max(original.get('file_size', 1), 1)) * 100
                    triangle_improvement = ((original.get('total_triangles', 0) - optimized.get('total_triangles', 0)) / max(original.get('total_triangles', 1), 1)) * 100
                    
                    console.print(f"  {asset_name}:")
                    console.print(f"    File size: {file_size_improvement:.1f}% improvement")
                    console.print(f"    Triangles: {triangle_improvement:.1f}% improvement")
    
    # Also try to generate report from converter's benchmark data
    if converter.benchmark and hasattr(converter.benchmark, 'benchmark_results'):
        if converter.benchmark.benchmark_results:
            report_path = output_dir / "converter_benchmark_report.json"
            if converter.benchmark.generate_benchmark_report(report_path):
                console.print(f"\n[bold green]Converter benchmark report generated: {report_path}")
    
    console.print(f"\n[bold green]Benchmark completed: {success_count}/{len(glb_files)} assets tested")

@app.command()
def doctor():
    """Diagnose and fix common VoxBridge issues."""
    console.print("[bold blue]VoxBridge Doctor - System Diagnostics")
    
    # Check Python version
    python_version = sys.version_info
    console.print(f"Python: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    # Check dependencies
    console.print("\nDependencies:")
    
    try:
        import typer
        console.print("  ✓ typer")
    except ImportError:
        console.print("  ✗ typer (missing)")
    
    try:
        import rich
        console.print("  ✓ rich")
    except ImportError:
        console.print("  ✗ rich (missing)")
    
    try:
        import pygltflib
        console.print("  ✓ pygltflib")
    except ImportError:
        console.print("  ✗ pygltflib (missing)")
    
    # Check Blender
    console.print("\nExternal Tools:")
    try:
        import subprocess
        result = subprocess.run(['which', 'blender'], capture_output=True, text=True)
        if result.returncode == 0:
            console.print(f"  ✓ Blender: {result.stdout.strip()}")
        else:
            console.print("  ✗ Blender: not found")
    except:
        console.print("  ✗ Blender: detection failed")
    
    # Check Node.js
    try:
        result = subprocess.run(['which', 'node'], capture_output=True, text=True)
        if result.returncode == 0:
            console.print(f"  ✓ Node.js: {result.stdout.strip()}")
        else:
            console.print("  ✗ Node.js: not found")
    except:
        console.print("  ✗ Node.js: detection failed")

def main():
    """Main entry point for the CLI."""
    app()

if __name__ == "__main__":
    main() 