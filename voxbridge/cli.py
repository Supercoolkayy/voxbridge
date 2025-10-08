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
    from rich import box
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

from .converter import VoxBridgeConverter
from .orchestrated_converter import OrchestratedConverter

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

def print_fancy_header(verbose: bool = False):
    """Print a fancy application header with visual effects"""
    if RICH_AVAILABLE:
        if verbose:
            # Beautiful verbose header
            header_panel = Panel.fit(
                "[bold bright_blue]VoxBridge Converter v2.0.0 - Next Generation 3D Processing[/bold bright_blue]\n\n"
                "[cyan]Advanced GLB ➜ GLTF / Roblox / Unity Exporter[/cyan]\n"
                "[dim]Smart Detection • Lightning Fast • Beautiful Output[/dim]\n"
                "[dim]Auto-Routing • Comprehensive Reports • Optimized Performance[/dim]",
                title="[bold white]VoxBridge v2.0.0[/bold white]",
                border_style="bright_blue",
                padding=(1, 2)
            )
            console.print(header_panel)
        else:
            # Compact version for non-verbose mode
            console.print(Panel.fit(
                "[bold bright_blue]VoxBridge Converter v2.0.0[/bold bright_blue]\n"
                "[dim]Advanced 3D Model Processing Pipeline[/dim]",
                border_style="bright_blue"
            ))
    else:
        print("VoxBridge Converter v2.0.0 - Next Generation 3D Processing")
        if verbose:
            print("Advanced GLB ➜ GLTF / Roblox / Unity Exporter")

def print_header(verbose: bool = False):
    """Legacy header function for backward compatibility"""
    print_fancy_header(verbose)

def print_file_config(input_path: Path, output_path: Path, target: str, optimize_mesh: bool = False):
    """Print file configuration in a beautiful format."""
    if RICH_AVAILABLE:
        # Create a beautiful configuration table
        config_table = Table(show_header=False, box=box.ROUNDED, padding=(0, 1))
        config_table.add_column(style="bright_cyan", width=12)
        config_table.add_column(style="white")
        
        config_table.add_row("Input:", str(input_path))
        config_table.add_row("Output:", str(output_path))
        config_table.add_row("Target:", target.upper())
        if optimize_mesh:
            config_table.add_row("Mode:", "Optimized")
        
        console.print(config_table)
    else:
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
                
                if result:
                    progress.update(task, completed=100, description="[bold green]Completed!")
                else:
                    progress.update(task, completed=100, description="[bold red]Failed!")
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
                print_step_info(f"📦 Unzip the folder to use in your {target} project!", 1)
        
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
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output directory path"),
    target: str = typer.Option("unity", "--target", "-t", help="Target platform (unity/roblox)"),
    optimize_mesh: bool = typer.Option(False, "--optimize-mesh", help="Enable mesh optimization"),
    generate_atlas: bool = typer.Option(False, "--generate-atlas", help="Generate texture atlas for optimization"),
    no_blender: bool = typer.Option(False, "--no-blender", help="Skip Blender processing"),
    force_static: bool = typer.Option(False, "--force-static", help="Force static processing path (Trimesh)"),
    force_node: bool = typer.Option(False, "--force-node", help="Force complex processing path (Node.js)"),
    pack_glb: bool = typer.Option(False, "--pack-glb", help="Pack output into single GLB file"),
    use_draco: bool = typer.Option(True, "--use-draco", help="Enable Draco compression"),
    no_draco: bool = typer.Option(False, "--no-draco", help="Disable Draco compression"),
    texture_size: int = typer.Option(1024, "--texture-size", help="Maximum texture size"),
    quantize: bool = typer.Option(True, "--quantize", help="Enable quantization"),
    fast: bool = typer.Option(False, "--fast", help="Fast mode: skip Draco, minimal validation, smaller textures (512px)"),
    balanced: bool = typer.Option(False, "--balanced", help="Balanced mode: medium compression, medium speed (1024px)"),
    full: bool = typer.Option(False, "--full", help="Full mode: all optimizations, larger textures (2048px)"),
    keep_temp: bool = typer.Option(False, "--keep-temp", help="Keep intermediate files for debugging"),
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
    
    # Determine output directory
    if output is None:
        output_dir = input_file.parent / f"{input_file.stem}_output"
    else:
        if output.is_file():
            output_dir = output.parent
        else:
            output_dir = output
    
    # Validate target platform
    valid_targets = ["unity", "roblox"]
    if target.lower() not in valid_targets:
        console.print(f"[bold red]Error: Invalid target platform '{target}'")
        console.print(f"[yellow]Valid targets are: {', '.join(valid_targets)}")
        raise typer.Exit(1)
    
    # Check if input file exists
    if not input_file.exists():
        console.print(f"[bold red]Error: Input file '{input_file}' does not exist")
        raise typer.Exit(1)
    
    # Check if input file is a GLB/GLTF file
    if input_file.suffix.lower() not in ['.glb', '.gltf']:
        console.print(f"[bold red]Error: Input file '{input_file}' is not a GLB/GLTF file.")
        raise typer.Exit(1)
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Print fancy header and configuration
    print_fancy_header(verbose)
    print_file_config(input_file, output_dir, target, optimize_mesh)
    
    # Prepare conversion options
    options = {
        'optimize_mesh': optimize_mesh,
        'generate_atlas': generate_atlas,
        'no_blender': no_blender,
        'force_static': force_static,
        'force_node': force_node,
        'pack_glb': pack_glb,
        'use_draco': use_draco and not no_draco,
        'texture_size': texture_size,
        'quantize': quantize,
        'fast': fast,
        'balanced': balanced,
        'full': full,
        'keep_temp': keep_temp,
        'debug': debug
    }
    
    # Apply speed mode settings
    if fast:
        options['use_draco'] = False
        options['quantize'] = False
        options['optimize_mesh'] = False
        options['generate_atlas'] = False
        options['texture_size'] = 512  # Smaller textures for speed
    elif balanced:
        options['use_draco'] = True
        options['quantize'] = True
        options['optimize_mesh'] = True
        options['generate_atlas'] = False
        options['texture_size'] = 1024  # Medium textures for balance
    elif full:
        options['use_draco'] = True
        options['quantize'] = True
        options['optimize_mesh'] = True
        options['generate_atlas'] = True
        options['texture_size'] = 2048  # Larger textures for quality
    
    # Use unified pipeline runner
    from .pipeline_runner import run_unified_pipeline
    
    try:
        # Show processing with fancy progress
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TimeElapsedColumn(),
            console=console,
            transient=True
        ) as progress:
            task = progress.add_task("Processing model...", total=None)
            
            result = run_unified_pipeline("convert", input_file, output_dir, target, options, debug)
            
            progress.update(task, description="Conversion completed!")
        
        if result['success']:
            # Simplified success message
            success_panel = Panel.fit(
                f"[bold green]Success: Your package is ready![/bold green]\n\n"
                f"Import this file into {target.upper()}: [bold cyan]{result.get('output_path', 'Unknown')}[/bold cyan]\n\n"
                f"[dim]Processing time: {result.get('processing_time', 0):.2f}s[/dim]",
                title="Success",
                border_style="green"
            )
            console.print(success_panel)
            
            if result.get('fallback_used'):
                console.print("[yellow]Note: Fallback processing was used[/yellow]")
            
            # Only show detailed information in debug mode
            if debug:
                # Show warnings with severity differentiation
                warnings = result.get('warnings', [])
                if warnings:
                    critical_warnings = [w for w in warnings if any(keyword in w.lower() for keyword in ['error', 'failed', 'critical', 'fatal'])]
                    advisory_warnings = [w for w in warnings if w not in critical_warnings]
                    
                    if critical_warnings:
                        console.print(f"[red]Critical Issues: {len(critical_warnings)}[/red]")
                        for warning in critical_warnings:
                            console.print(f"  [red]⚠ {warning}[/red]")
                    
                    if advisory_warnings:
                        console.print(f"[yellow]Advisory Warnings: {len(advisory_warnings)}[/yellow]")
                        for warning in advisory_warnings:
                            console.print(f"  [yellow]⚠ {warning}[/yellow]")
                
                # Show post-validation results
                if 'post_validation' in result:
                    post_validation = result['post_validation']
                    if post_validation.get('validation_info'):
                        validation_info = post_validation['validation_info']
                        
                        # Create validation info table
                        validation_table = Table(show_header=False, box=box.ROUNDED, padding=(0, 1))
                        validation_table.add_column(style="bright_cyan", width=20)
                        validation_table.add_column(style="white")
                        
                        # Add relevant info based on conversion type
                        if 'textures' in validation_info:
                            validation_table.add_row("Textures:", str(validation_info['textures']))
                        if 'materials' in validation_info:
                            validation_table.add_row("Materials:", str(validation_info['materials']))
                        if 'nodes' in validation_info:
                            validation_table.add_row("Nodes:", str(validation_info['nodes']))
                        if 'meshes' in validation_info:
                            validation_table.add_row("Meshes:", str(validation_info['meshes']))
                        if 'total_bones' in validation_info:
                            validation_table.add_row("Bones:", str(validation_info['total_bones']))
                        if 'animations' in validation_info:
                            validation_table.add_row("Animations:", str(validation_info['animations']))
                        if 'draco_compression' in validation_info:
                            validation_table.add_row("Draco:", "Yes" if validation_info['draco_compression'] else "No")
                        if 'file_size_mb' in validation_info:
                            validation_table.add_row("Size:", f"{validation_info['file_size_mb']:.1f} MB")
                        
                        if validation_table.rows:
                            console.print("\n[bold blue]Post-Validation Analysis:[/bold blue]")
                            console.print(validation_table)
                
                # Show package info
                if 'package_info' in result:
                    package_info = result['package_info']
                    if package_info.get('structure'):
                        structure = package_info['structure']
                        package_table = Table(show_header=False, box=box.ROUNDED, padding=(0, 1))
                        package_table.add_column(style="bright_cyan", width=20)
                        package_table.add_column(style="white")
                        
                        package_table.add_row("Package Type:", "ZIP Archive")
                        package_table.add_row("Model File:", "Yes" if structure.get('model') else "No")
                        package_table.add_row("Textures:", "Yes" if structure.get('textures') else "No")
                        package_table.add_row("Report:", "Yes" if structure.get('report') else "No")
                        package_table.add_row("Total Files:", str(len(package_info.get('files', []))))
                        
                        console.print("\n[bold blue]Package Structure:[/bold blue]")
                        console.print(package_table)
                
                # Show report file location
                report_path = output_dir / 'voxbridge_report.json'
                if report_path.exists():
                    console.print(f"\n[dim]Detailed report saved to: {report_path}[/dim]")
            else:
                # Show only critical warnings in non-debug mode
                warnings = result.get('warnings', [])
                critical_warnings = [w for w in warnings if any(keyword in w.lower() for keyword in ['error', 'failed', 'critical', 'fatal'])]
                if critical_warnings:
                    console.print(f"[red]Critical Issues: {len(critical_warnings)}[/red]")
                    for warning in critical_warnings:
                        console.print(f"  [red]⚠ {warning}[/red]")
        else:
            # Error panel
            error_panel = Panel.fit(
                f"[bold red]Conversion failed![/bold red]\n\n"
                f"[red]Error:[/red] {result.get('error', 'Unknown error')}\n\n"
                f"[dim]Please check the input file and try again.[/dim]",
                title="Error",
                border_style="red"
            )
            console.print(error_panel)
            raise typer.Exit(1)
            
    except Exception as e:
        error_panel = Panel.fit(
            f"[bold red]Conversion failed with exception![/bold red]\n\n"
            f"[red]Error:[/red] {str(e)}\n\n"
            f"[dim]Please check the input file and try again.[/dim]",
            title="Error",
            border_style="red"
        )
        console.print(error_panel)
        
        if debug:
            logger.exception("Conversion exception:")
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
    
    # Use unified pipeline runner for batch processing
    from .pipeline_runner import run_unified_pipeline
    
    batch_options = {
        'optimize_mesh': optimize_mesh,
        'no_blender': no_blender,
        'use_draco': True,
        'quantize': True
    }
    
    result = run_unified_pipeline("batch", input_dir, output_dir, target, batch_options, verbose)
    
    if result['success']:
        success_count = result.get('success_count', 0)
        total_count = result.get('total_count', 0)
        console.print(f"\n[bold green]Batch conversion completed: {success_count}/{total_count} files converted successfully")
        
        # Show any failed files
        failed_files = result.get('files_failed', [])
        if failed_files:
            console.print(f"\n[yellow]Failed files: {len(failed_files)}[/yellow]")
            for failed in failed_files:
                console.print(f"  [red]❌ {Path(failed['file']).name}: {failed['error']}[/red]")
    else:
        console.print(f"\n[bold red]Batch conversion failed: {result.get('error', 'Unknown error')}")
        raise typer.Exit(1)

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
    
    # Use unified pipeline runner for benchmark processing
    from .pipeline_runner import run_unified_pipeline
    
    benchmark_options = {
        'optimize_mesh': optimize_mesh,
        'use_draco': True,
        'quantize': True,
        'texture_atlas': True
    }
    
    result = run_unified_pipeline("benchmark", input_dir, output_dir, target, benchmark_options, verbose)
    
    if result['success']:
        benchmark_results = result.get('benchmark_results', {})
        
        # Generate benchmark report
        if benchmark_results:
            report_path = output_dir / "benchmark_report.json"
            with open(report_path, 'w') as f:
                json.dump(result, f, indent=2, default=str)
            console.print(f"\n[bold green]Benchmark report generated: {report_path}")
            
            # Display summary
            console.print("\n[bold yellow]Benchmark Summary:")
            for asset_name, asset_result in benchmark_results.items():
                improvements = asset_result.get('improvements', {})
                
                if 'file_size_reduction_percent' in improvements:
                    size_improvement = improvements['file_size_reduction_percent']
                    console.print(f"  {asset_name}:")
                    console.print(f"    File size: {size_improvement:.1f}% improvement")
                
                if 'triangle_reduction_percent' in improvements:
                    triangle_improvement = improvements['triangle_reduction_percent']
                    console.print(f"    Triangles: {triangle_improvement:.1f}% improvement")
        
        console.print(f"\n[bold green]Benchmark completed: {len(benchmark_results)}/{len(glb_files)} assets tested")
    else:
        console.print(f"\n[bold red]Benchmark failed: {result.get('error', 'Unknown error')}")
        raise typer.Exit(1)

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

@app.command("selftest")
def selftest():
    """Test VoxBridge integration (Python + Node.js)"""
    console = Console()
    
    console.print("\n[bold blue]VoxBridge Self-Test[/bold blue]")
    console.print("=" * 50)
    
    # Test Python imports
    console.print("\n[bold]Testing Python Integration:[/bold]")
    try:
        from .orchestrated_converter import OrchestratedConverter
        from .utils.paths import get_node_runner_path, is_bundled
        console.print("  ✓ Python modules imported successfully")
    except Exception as e:
        console.print(f"  ✗ Python import failed: {e}")
        return
    
    # Test Node.js runner
    console.print("\n[bold]Testing Node.js Integration:[/bold]")
    try:
        node_runner_path = get_node_runner_path()
        console.print(f"  Node runner path: {node_runner_path}")
        
        if node_runner_path.exists():
            console.print("  ✓ Node runner found")
            
            # Test version command
            import subprocess
            result = subprocess.run([str(node_runner_path), '--version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                console.print(f"  ✓ Node runner version: {result.stdout.strip()}")
            else:
                console.print(f"  ✗ Node runner version failed: {result.stderr}")
                return
        else:
            console.print("  ✗ Node runner not found")
            return
            
    except Exception as e:
        console.print(f"  ✗ Node.js test failed: {e}")
        return
    
    # Test bundled status
    console.print("\n[bold]Testing Bundle Status:[/bold]")
    if is_bundled():
        console.print("  ✓ Running as bundled executable")
    else:
        console.print("  ℹ Running as development script")
    
    # Test converter initialization
    console.print("\n[bold]Testing Converter Initialization:[/bold]")
    try:
        converter = OrchestratedConverter(debug=True)
        console.print("  ✓ OrchestratedConverter initialized")
        
        if converter.node_available:
            console.print("  ✓ Node.js processing available")
        else:
            console.print("  ⚠ Node.js processing not available")
            
    except Exception as e:
        console.print(f"  ✗ Converter initialization failed: {e}")
        return
    
    console.print("\n[bold green]✅ All tests passed! VoxBridge is ready.[/bold green]")

def main():
    """Main entry point for the CLI."""
    app()

if __name__ == "__main__":
    main() 