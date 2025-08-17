#!/usr/bin/env python3
"""
VoxBridge CLI - Command Line Interface
User interface for VoxBridge converter
"""

import sys
import time
import subprocess
import platform
from pathlib import Path
from typing import Optional, List

try:
    import typer
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
    from rich.panel import Panel
    from rich.text import Text
    from rich.table import Table
    from rich import print as rprint
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

from .converter import VoxBridgeConverter, InputValidationError, ConversionError, BlenderNotFoundError
from . import __version__


# Create Typer app with enhanced help
app = typer.Typer(
    name="voxbridge",
    help="VoxBridge: Professional VoxEdit to Unity/Roblox Asset Converter\n\nConvert VoxEdit glTF/glb exports into optimized formats for Unity and Roblox.\nSupports mesh optimization, texture atlasing, and batch processing.",
    add_completion=False,
    rich_markup_mode="rich",
    no_args_is_help=True,
    epilog="""
Examples:
  voxbridge convert --input model.glb --target unity
  voxbridge convert --input model.glb --target roblox --optimize-mesh
  voxbridge batch ./input_folder ./output_folder --target unity
  voxbridge doctor
  voxbridge-gui

For more information, visit: https://github.com/Supercoolkayy/voxbridge
"""
)

# Global console for rich output
console = Console() if RICH_AVAILABLE else None

def safe_print(message: str, style: str = ""):
    """Safely print with Rich or fallback to regular print"""
    if RICH_AVAILABLE and console:
        try:
            console.print(message, style=style)
        except Exception:
            print(message)
    else:
        print(message)


def print_header():
    """Print VoxBridge header"""
    if RICH_AVAILABLE:
        try:
            title = Text("VoxBridge v1.0.6", style="bold cyan")
            subtitle = Text("VoxEdit to Unity/Roblox Converter", style="dim white")
            version = Text("Professional Asset Converter", style="italic green")
            if console:
                console.print(Panel.fit(f"{title}\n{subtitle}\n{version}", 
                                       border_style="cyan", padding=(0, 1)))
        except Exception:
            print("VoxBridge v1.0.6 - VoxEdit to Unity/Roblox Converter")
            print("Professional Asset Converter")
            print("=" * 55)
    else:
        print("VoxBridge v1.0.6 - VoxEdit to Unity/Roblox Converter")
        print("Professional Asset Converter")
        print("=" * 55)


def print_conversion_start(input_path: Path, output_path: Path):
    """Print conversion start information"""
    if RICH_AVAILABLE:
        try:
            if console:
                console.print("[bold yellow]File Configuration[/bold yellow]")
                
                table = Table(show_header=False, box=None, show_edge=False)
                table.add_column("Type", style="bold cyan", no_wrap=True, width=10)
                table.add_column("Path", style="white")
                
                table.add_row("Input", str(input_path))
                table.add_row("Output", str(output_path))
                console.print(table)
                console.print()
        except Exception:
            print("[INPUT]  File Configuration")
            print(f"[INPUT]  {input_path}")
            print(f"[OUTPUT] {output_path}")
            print()
    else:
        print("[INPUT]  File Configuration")
        print(f"[INPUT]  {input_path}")
        print(f"[OUTPUT] {output_path}")
        print()


def print_validation_results(stats: dict):
    """Print validation results"""
    if RICH_AVAILABLE:
        try:
            safe_print("[bold magenta]Validation Results[/bold magenta]")
            
            if stats.get('file_exists'):
                safe_print("[bold green]✅ File created successfully![/bold green]")
                safe_print(f"[dim]File size:[/dim] {stats.get('file_size', 0):,} bytes")
                
                if stats.get('materials') is not None:
                    safe_print(f"[dim]Materials:[/dim] {stats.get('materials', 0)}")
                if stats.get('textures') is not None:
                    safe_print(f"[dim]Textures:[/dim] {stats.get('textures', 0)}")
                if stats.get('meshes') is not None:
                    safe_print(f"[dim]Meshes:[/dim] {stats.get('meshes', 0)}")
                if stats.get('nodes') is not None:
                    safe_print(f"[dim]Nodes:[/dim] {stats.get('nodes', 0)}")
                
                if stats.get('note'):
                    safe_print(f"[dim]Note:[/dim] {stats.get('note')}")
            else:
                safe_print("[bold red]❌ File creation failed![/bold red]")
        except Exception:
            # Fallback to regular print
            if stats.get('file_exists'):
                print("✅ File created successfully!")
                print(f"File size: {stats.get('file_size', 0):,} bytes")
            else:
                print("❌ File creation failed!")
    else:
        # Regular print fallback
        if stats.get('file_exists'):
            print("✅ File created successfully!")
            print(f"File size: {stats.get('file_size', 0):,} bytes")
        else:
            print("❌ File creation failed!")


def handle_conversion(
    input_path: Path, 
    output_path: Path, 
    use_blender: bool, 
    verbose: bool,
    optimize_mesh: bool = False, 
    generate_atlas: bool = False, 
    compress_textures: bool = False, 
    platform: str = "unity", 
    generate_report: bool = False
):
    """Handle the conversion process with proper error handling"""
    converter = VoxBridgeConverter()
    
    # Track processing time if report is requested
    start_time = time.time()
    
    # Validate input
    if not converter.validate_input(input_path):
        if not input_path.exists():
            safe_print(f"[red]Error: Input file '{input_path}' not found[/red]")
        else:
            safe_print(f"[red]Error: Unsupported format '{input_path.suffix}'. Supported: {', '.join(converter.supported_formats)}[/red]")
        return False
    
    print_conversion_start(input_path, output_path)
    
    try:
        # Show progress with Rich if available
        if RICH_AVAILABLE and not verbose:
            try:
                with Progress(
                    SpinnerColumn(spinner_name="dots"),
                    TextColumn("[progress.description]{task.description}"),
                    BarColumn(bar_width=40),
                    TimeElapsedColumn(),
                    console=console
                ) as progress:
                    task = progress.add_task("[bold cyan]Initializing...", total=None)
                
                # Determine processing method
                if use_blender and input_path.suffix.lower() == '.glb':
                    progress.update(task, description="[bold yellow]Using Blender for GLB cleanup...")
                    
                    # Check if Blender is available
                    blender_exe = converter.find_blender()
                    if not blender_exe:
                        progress.update(task, description="[bold red]Blender not found")
                        progress.stop()
                        safe_print("[bold red]Blender not found. Please install Blender or add it to your PATH[/bold red]")
                        safe_print("[dim]Download from: https://www.blender.org/download/[/dim]")
                        safe_print("[dim]Alternatively, use --no-blender for basic JSON cleanup[/dim]")
                        return False
                    
                    if verbose:
                        console.print(f"[cyan]Using Blender:[/cyan] {blender_exe}")
                        console.print(f"[cyan]Script:[/cyan] {converter.blender_script_path}")
                    
                elif input_path.suffix.lower() == '.gltf':
                    progress.update(task, description="[bold green]Processing glTF JSON...")
                else:
                    progress.update(task, description="[bold blue]Processing with basic cleanup...")
                
                # Perform conversion
                progress.update(task, description="[bold magenta]Converting file...")
                success = converter.convert_file(
                    input_path, output_path, use_blender,
                    optimize_mesh,
                    generate_atlas,
                    compress_textures,
                    platform
                )
                
                if success:
                    progress.update(task, description="[bold green]Conversion completed successfully!")
                    progress.stop()
                    safe_print("[bold green]Conversion completed successfully![/bold green]")
                else:
                    progress.update(task, description="[bold red]Conversion failed")
                    progress.stop()
                    safe_print("[bold red]Conversion failed![/bold red]")
                    return False
            except Exception as e:
                # Fallback if Rich progress fails
                print(f"Progress display failed: {e}")
                # Continue with conversion
                success = converter.convert_file(
                    input_path, output_path, use_blender,
                    optimize_mesh,
                    generate_atlas,
                    compress_textures,
                    platform
                )
                
                if success:
                    safe_print("[bold green]Conversion completed successfully![/bold green]")
                else:
                    safe_print("[bold red]Conversion failed![/bold red]")
                    return False
        else:
            # Fallback to regular output
            if use_blender and input_path.suffix.lower() == '.glb':
                print("[PROCESS] Using Blender for GLB cleanup...")
                
                # Check if Blender is available
                blender_exe = converter.find_blender()
                if not blender_exe:
                    print("[ERROR] Blender not found. Please install Blender or add it to your PATH")
                    print("   Download from: https://www.blender.org/download/")
                    print("   Alternatively, use --no-blender for basic JSON cleanup")
                    return False
                
                if verbose:
                    print(f"   Using Blender: {blender_exe}")
                    print(f"   Script: {converter.blender_script_path}")
                
            elif input_path.suffix.lower() == '.gltf':
                print("[PROCESS] Processing glTF JSON...")
            else:
                print("[PROCESS] Processing with basic cleanup...")
            
            # Perform conversion
            print("[PROCESS] Converting file...")
            success = converter.convert_file(
                input_path, output_path, use_blender,
                optimize_mesh,
                generate_atlas,
                compress_textures,
                platform
            )
            
            if success:
                print("[SUCCESS] Conversion completed successfully!")
            else:
                print("[ERROR] Conversion failed!")
                return False
        
        # Validate output
        if output_path.exists():
            stats = converter.validate_output(output_path)
            print_validation_results(stats)
            
            # Generate performance report if requested
            if generate_report:
                processing_time = time.time() - start_time
                report = converter.generate_performance_report(
                    input_path, output_path, stats, 
                    changes=getattr(converter, 'last_changes', [])
                )
                report['processing_time'] = processing_time
                
                report_path = converter.save_performance_report(report, output_path.parent)
                safe_print(f"[bold green]Performance report saved:[/bold green] {report_path}")
        
        safe_print("[bold green]Ready for import into Unity and Roblox![/bold green]")
        safe_print("[bold cyan]VoxBridge conversion complete![/bold cyan]")
        return True
        
    except Exception as e:
        safe_print(f"[bold red]Unexpected Error:[/bold red] {str(e)}")
        if verbose:
            import traceback
            safe_print("[dim]Traceback:[/dim]")
            safe_print(traceback.format_exc())
        return False


def check_python_version():
    """Check Python version compatibility"""
    version = sys.version_info
    if version < (3, 9):
        return False, f"Python {version.major}.{version.minor} detected. Python 3.9+ required."
    return True, f"Python {version.major}.{version.minor} ✓"


def check_blender():
    """Check if Blender is available"""
    try:
        converter = VoxBridgeConverter()
        blender_path = converter.find_blender()
        if blender_path:
            return True, f"Blender found: {blender_path}"
        else:
            return False, "Blender not found in PATH"
    except Exception as e:
        return False, f"Blender check failed: {str(e)}"


def check_gpu_info():
    """Check GPU information"""
    try:
        import subprocess
        result = subprocess.run(['nvidia-smi', '--query-gpu=name,memory.total', '--format=csv,noheader,nounits'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            gpu_info = result.stdout.strip().split(',')
            if len(gpu_info) >= 2:
                return True, f"GPU: {gpu_info[0].strip()} ({gpu_info[1].strip()}MB)"
        return False, "GPU information not available"
    except Exception:
        return False, "GPU check failed"


def run_doctor():
    """Run system diagnostics"""
    print_header()
    safe_print("[bold yellow]System Diagnostics[/bold yellow]")
    safe_print("=" * 40)
    
    # Check Python version
    py_ok, py_msg = check_python_version()
    if py_ok:
        safe_print(f"[OK] {py_msg}")
    else:
        safe_print(f"[FAILED] {py_msg}")
    
    # Check Blender
    blender_ok, blender_msg = check_blender()
    if blender_ok:
        safe_print(f"[OK] {blender_msg}")
    else:
        safe_print(f"[WARNING] {blender_msg}")
        safe_print("[dim]Blender is optional but recommended for GLB processing[/dim]")
    
    # Check GPU
    gpu_ok, gpu_msg = check_gpu_info()
    if gpu_ok:
        safe_print(f"[OK] {gpu_msg}")
    else:
        safe_print(f"[INFO] {gpu_msg}")
    
    # Check dependencies
    safe_print("\n[bold yellow]Dependencies:[/bold yellow]")
    dependencies = [
        ("typer", "CLI framework"),
        ("rich", "Rich text formatting"),
        ("pygltflib", "glTF processing"),
        ("Pillow", "Image processing"),
        ("numpy", "Numerical operations"),
        ("scipy", "Scientific computing")
    ]
    
    for dep, desc in dependencies:
        try:
            __import__(dep)
            safe_print(f"[OK] {dep} ({desc})")
        except ImportError:
            safe_print(f"[FAILED] {dep} ({desc}) - Missing")
    
    safe_print("\n[bold green]Diagnostics complete![/bold green]")


@app.command()
def convert(
    input_file: Path = typer.Option(..., "--input", "-i", help="Input glTF or glb file exported from VoxEdit"),
    target: str = typer.Option("unity", "--target", "-t", help="Target platform: unity or roblox"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file path (auto-generated if not specified)"),
    optimize_mesh: bool = typer.Option(False, "--optimize-mesh", help="Enable polygon reduction and mesh splitting for better performance"),
    generate_atlas: bool = typer.Option(False, "--generate-atlas", help="Generate texture atlas to reduce draw calls"),
    compress_textures: bool = typer.Option(False, "--compress-textures", help="Compress textures to 1024x1024 for better memory usage"),
    no_blender: bool = typer.Option(False, "--no-blender", help="Skip Blender processing (basic JSON cleanup only)"),
    report: bool = typer.Option(False, "--report", help="Generate detailed performance report"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output for debugging"),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing output file without confirmation"),
):
    """Convert VoxEdit glTF/glb files to Unity/Roblox compatible formats"""
    print_header()
    
    # Auto-generate output path if not specified
    if output is None:
        input_stem = input_file.stem
        # Always use .gltf extension since we no longer generate GLB files
        output = input_file.parent / f"{input_stem}_{target}_clean.gltf"
    else:
        # Ensure output has proper extension - always use .gltf
        if not output.suffix:
            output = output.with_suffix('.gltf')
        elif output.suffix.lower() == '.glb':
            # Convert .glb to .gltf since we don't generate GLB files
            output = output.with_suffix('.gltf')
    
    # Check if output file exists and handle force flag
    if output.exists() and not force:
        safe_print(f"[yellow]Warning: Output file '{output}' already exists.[/yellow]")
        if not typer.confirm("Overwrite existing file?"):
            safe_print("[red]Conversion cancelled.[/red]")
            raise typer.Exit(1)
    
    # Validate target platform
    if target.lower() not in ["unity", "roblox"]:
        safe_print(f"[red]Error: Invalid target '{target}'. Supported: unity, roblox[/red]")
        raise typer.Exit(1)
    
    # Perform conversion
    success = handle_conversion(
        input_path=input_file,
        output_path=output,
        use_blender=not no_blender,
        verbose=verbose,
        optimize_mesh=optimize_mesh,
        generate_atlas=generate_atlas,
        compress_textures=compress_textures,
        platform=target.lower(),
        generate_report=report
    )
    
    if not success:
        safe_print("[bold red]VoxBridge conversion failed![/bold red]")
        raise typer.Exit(1)


@app.command()
def sketchfab(
    input_file: Path = typer.Option(..., "--input", "-i", help="Input GLB/GLTF file to create Sketchfab-ready package"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output directory for Sketchfab package"),
    create_zip: bool = typer.Option(True, "--create-zip", help="Create ZIP file with GLTF and binary files for Sketchfab"),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing output file without confirmation"),
):
    """Create Sketchfab-ready package that fixes Error 33 issues"""
    
    print_header()
    
    # Set output directory
    if output is None:
        output = Path(f"sketchfab_ready_{input_file.stem}")
    
    # Ensure output directory exists
    output.mkdir(parents=True, exist_ok=True)
    
    print(f"🎯 Creating Sketchfab-ready package for: {input_file}")
    print(f"📁 Output Directory: {output}")
    print()
    
    try:
        # Import converter
        from .converter import VoxBridgeConverter
        
        converter = VoxBridgeConverter()
        
        # First convert to GLTF if needed
        if input_file.suffix.lower() == '.glb':
            print("📦 Converting GLB to GLTF...")
            gltf_output = output / f"{input_file.stem}.gltf"
            
            if not converter.convert_file(input_file, gltf_output, use_blender=False, platform="unity"):
                raise RuntimeError("Failed to convert GLB to GLTF")
            
            print(f"✅ GLTF created: {gltf_output}")
        else:
            gltf_output = input_file
        
        # Create Sketchfab-ready package
        print("\n🎯 Creating Sketchfab-ready package...")
        if converter.create_sketchfab_ready_package(gltf_output):
            print("\n🎉 SUCCESS: Sketchfab-ready package created!")
            print("📁 This package should upload without Error 33!")
            
            # Show package contents
            sketchfab_dir = output / "sketchfab_ready"
            if sketchfab_dir.exists():
                print("\n📁 Package contents (flat structure, no folders):")
                for file_path in sketchfab_dir.iterdir():
                    if file_path.is_file():
                        print(f"  - {file_path.name}")
                
                # Show ZIP file
                zip_files = list(output.glob("*_sketchfab.zip"))
                if zip_files:
                    print(f"\n📦 Upload this ZIP file to Sketchfab: {zip_files[0].name}")
                    print("💡 This ZIP has the correct flat structure to avoid Error 33")
            
        else:
            print("\n❌ FAILED: Could not create Sketchfab-ready package")
            raise RuntimeError("Package creation failed")
        
    except Exception as e:
        print(f"❌ Sketchfab package creation failed: {e}")
        raise typer.Exit(1)


@app.command()
def help():
    """Show detailed help information"""
    print_header()
    safe_print("[bold yellow]VoxBridge Help[/bold yellow]")
    safe_print("=" * 40)
    
    safe_print("[bold cyan]Commands:[/bold cyan]")
    safe_print("  convert   - Convert single file")
    safe_print("  sketchfab - Create Sketchfab-compatible files")
    safe_print("  batch     - Process multiple files")
    safe_print("  doctor    - System diagnostics")
    safe_print("  help      - Show this help")
    
    safe_print("\n[bold cyan]Examples:[/bold cyan]")
    safe_print("  # Basic Unity conversion")
    safe_print("  voxbridge convert --input model.glb --target unity")
    
    safe_print("  # Sketchfab-ready conversion")
    safe_print("  voxbridge sketchfab --input model.glb")
    
    safe_print("  # Optimized Roblox conversion")
    safe_print("  voxbridge convert --input model.glb --target roblox --optimize-mesh --generate-atlas")
    
    safe_print("  # Batch processing")
    safe_print("  voxbridge batch ./input_folder ./output_folder --target unity --recursive")
    
    safe_print("  # System check")
    safe_print("  voxbridge doctor")
    
    safe_print("\n[bold cyan]Options:[/bold cyan]")
    safe_print("  --optimize-mesh      - Enable mesh optimization")
    safe_print("  --generate-atlas     - Create texture atlas")
    safe_print("  --compress-textures  - Compress textures to 1024x1024")
    safe_print("  --no-blender        - Skip Blender processing")
    safe_print("  --report            - Generate performance report")
    safe_print("  --verbose           - Show detailed output")
    safe_print("  --force             - Overwrite existing files")
    
    safe_print("\n[bold cyan]Platforms:[/bold cyan]")
    safe_print("  unity   - Unity 3D engine")
    safe_print("  roblox  - Roblox Studio")
    
    safe_print("\n[bold cyan]File Formats:[/bold cyan]")
    safe_print("  Input:  .gltf, .glb (VoxEdit exports)")
    safe_print("  Output: .gltf, .glb (engine-ready)")
    
    safe_print("\n[bold cyan]Support:[/bold cyan]")
    safe_print("  GitHub: https://github.com/Supercoolkayy/voxbridge")
    safe_print("  Issues: https://github.com/Supercoolkayy/voxbridge/issues")


@app.command()
def doctor():
    """Run system diagnostics and health check"""
    run_doctor()


@app.command()
def batch(
    input_dir: Path = typer.Argument(..., help="Input directory containing glTF/glb files to process"),
    output_dir: Path = typer.Argument(..., help="Output directory where processed files will be saved"),
    pattern: str = typer.Option("*.glb,*.gltf", "--pattern", help="File pattern to match (comma-separated)"),
    recursive: bool = typer.Option(False, "--recursive", "-r", help="Process subdirectories recursively"),
    target: str = typer.Option("unity", "--target", "-t", help="Target platform: unity or roblox"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output for debugging"),
):
    """Batch process multiple glTF/glb files"""
    print_header()
    
    # Validate input directory
    if not input_dir.exists():
        safe_print(f"[red]Error: Input directory '{input_dir}' not found[/red]")
        raise typer.Exit(1)
    
    if not input_dir.is_dir():
        safe_print(f"[red]Error: '{input_dir}' is not a directory[/red]")
        raise typer.Exit(1)
    
    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Parse file patterns
    patterns = [p.strip() for p in pattern.split(",")]
    
    # Find matching files
    files_to_process = []
    for pattern in patterns:
        if recursive:
            files_to_process.extend(input_dir.rglob(pattern))
        else:
            files_to_process.extend(input_dir.glob(pattern))
    
    if not files_to_process:
        safe_print(f"[yellow]No files found matching patterns: {patterns}[/yellow]")
        raise typer.Exit(1)
    
    safe_print(f"[bold cyan]Found {len(files_to_process)} files to process[/bold cyan]")
    
    # Process files
    converter = VoxBridgeConverter()
    successful = 0
    failed = 0
    
    for i, file_path in enumerate(files_to_process, 1):
        if verbose:
            safe_print(f"\n[bold cyan]Processing {i}/{len(files_to_process)}:[/bold cyan] {file_path.name}")
        
        # Generate output path
        relative_path = file_path.relative_to(input_dir)
        # Always use .gltf extension since we no longer generate GLB files
        output_path = output_dir / relative_path.with_suffix(f"_{target}_clean.gltf")
        
        # Create output subdirectory if needed
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            success = converter.convert_file(
                file_path, output_path, use_blender=True,
                optimize_mesh=False,  # Disable for batch processing
                generate_atlas=False,  # Disable for batch processing
                compress_textures=False,  # Disable for batch processing
                platform=target.lower()
            )
            
            if success:
                successful += 1
                if verbose:
                    safe_print(f"[OK] {file_path.name} -> {output_path.name}")
            else:
                failed += 1
                safe_print(f"[FAILED] Failed to convert {file_path.name}")
                
        except Exception as e:
            failed += 1
            safe_print(f"[ERROR] Error processing {file_path.name}: {str(e)}")
    
    # Summary
    safe_print(f"\n[bold green]Batch processing complete![/bold green]")
    safe_print(f"  [green]Successful:[/green] {successful}")
    safe_print(f"  [red]Failed:[/red] {failed}")
    safe_print(f"  [cyan]Total:[/cyan] {len(files_to_process)}")


def main():
    """Main entry point"""
    try:
        app()
    except KeyboardInterrupt:
        safe_print("\n[bold red]Operation cancelled by user[/bold red]")
        raise typer.Exit(1)
    except Exception as e:
        safe_print(f"[bold red]Unexpected error:[/bold red] {str(e)}")
        raise typer.Exit(1)


if __name__ == "__main__":
    main() 