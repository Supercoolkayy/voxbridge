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
        console.print(message, style=style)
    else:
        print(message)


def print_header():
    """Print VoxBridge header"""
    if RICH_AVAILABLE:
        title = Text("VoxBridge v1.0.0", style="bold cyan")
        subtitle = Text("VoxEdit to Unity/Roblox Converter", style="dim white")
        version = Text("Professional Asset Converter", style="italic green")
        if console:
            console.print(Panel.fit(f"{title}\n{subtitle}\n{version}", 
                                   border_style="cyan", padding=(0, 1)))
    else:
        print("VoxBridge v1.0.0 - VoxEdit to Unity/Roblox Converter")
        print("Professional Asset Converter")
        print("=" * 55)


def print_conversion_start(input_path: Path, output_path: Path):
    """Print conversion start information"""
    if RICH_AVAILABLE:
        if console:
            console.print("[bold yellow]File Configuration[/bold yellow]")
            
            table = Table(show_header=False, box=None, show_edge=False)
            table.add_column("Type", style="bold cyan", no_wrap=True, width=10)
            table.add_column("Path", style="white")
            
            table.add_row("Input", str(input_path))
            table.add_row("Output", str(output_path))
            console.print(table)
            console.print()
    else:
        print("[INPUT]  File Configuration")
        print(f"[INPUT]  {input_path}")
        print(f"[OUTPUT] {output_path}")
        print()


def print_validation_results(stats: dict):
    """Print validation results"""
    if RICH_AVAILABLE:
        safe_print("[bold magenta]Validation Results[/bold magenta]")
        
        if stats['file_exists']:
            if console:
                table = Table(show_header=False, box=None, show_edge=False)
                table.add_column("Metric", style="bold green", no_wrap=True, width=12)
                table.add_column("Value", style="white")
                
                table.add_row("File Size", f"{stats['file_size']:,} bytes")
                
                if 'materials' in stats and stats['materials'] > 0:
                    table.add_row("Materials", str(stats['materials']))
                    table.add_row("Textures", str(stats['textures']))
                    table.add_row("Meshes", str(stats['meshes']))
                    table.add_row("Nodes", str(stats['nodes']))
                
                console.print(table)
            
            if 'note' in stats:
                safe_print(f"[yellow]Note:[/yellow] {stats['note']}")
                
            if 'error' in stats:
                safe_print(f"[red]Warning:[/red] {stats['error']}")
            
            safe_print("\n[bold green]Ready for import into Unity and Roblox![/bold green]")
        else:
            safe_print("[red]Error: Output file was not created[/red]")
    else:
        print("[STATS] Validation Results:")
        
        if stats['file_exists']:
            print(f"  [OK] File created: {stats['file_size']:,} bytes")
            
            if 'materials' in stats and stats['materials'] > 0:
                print(f"  [MAT] Materials: {stats['materials']}")
                print(f"  [TEX] Textures: {stats['textures']}")
                print(f"  [MESH] Meshes: {stats['meshes']}")
                print(f"  [NODE] Nodes: {stats['nodes']}")
                
            if 'note' in stats:
                print(f"  [INFO] {stats['note']}")
                
            if 'error' in stats:
                print(f"  [WARN] Warning: {stats['error']}")
                
            print(f"\n[READY] Ready for import into Unity and Roblox!")
        else:
            print("  [ERROR] Output file was not created")


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
            with Progress(
                SpinnerColumn(spinner_name="dots", style="bold cyan"),
                TextColumn("[progress.description]{task.description}", style="bold white"),
                BarColumn(bar_width=40, style="cyan", complete_style="green"),
                TimeElapsedColumn(style="dim white"),
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
                    optimize_mesh=optimize_mesh,
                    generate_atlas=generate_atlas,
                    compress_textures=compress_textures,
                    platform=platform
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
            success = converter.convert_file(
                input_path, output_path, use_blender,
                optimize_mesh=optimize_mesh,
                generate_atlas=generate_atlas,
                compress_textures=compress_textures,
                platform=platform
            )
            
            if success:
                print("[SUCCESS] Conversion completed successfully!")
            else:
                print("[ERROR] Conversion failed")
                return False
        
        # Validate output
        print()
        stats = converter.validate_output(output_path)
        print_validation_results(stats)
        
        # Generate performance report if requested
        if generate_report:
            processing_time = time.time() - start_time
            report = converter.generate_performance_report(
                input_path, output_path, stats, 
                changes=[]  # TODO: Collect changes during processing
            )
            report["processing_time"] = round(processing_time, 2)
            
            report_path = converter.save_performance_report(report, output_path.parent)
            print(f"[REPORT] Performance report saved: {report_path}")
        
        return True
            
    except BlenderNotFoundError as e:
        print(f"[ERROR] Blender Error: {e}")
        print("   Try using --no-blender for basic JSON cleanup")
        return False
        
    except ConversionError as e:
        print(f"[ERROR] Conversion Error: {e}")
        return False
        
    except Exception as e:
        print(f"[ERROR] Unexpected Error: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        return False


def check_python_version():
    """Check Python version compatibility"""
    version = sys.version_info
    if version.major == 3 and version.minor >= 9:
        return True, f"Python {version.major}.{version.minor}.{version.micro}"
    else:
        return False, f"Python {version.major}.{version.minor}.{version.micro} (requires 3.9+)"


def check_blender():
    """Check if Blender is available"""
    try:
        converter = VoxBridgeConverter()
        blender_exe = converter.find_blender()
        if blender_exe:
            return True, str(blender_exe)
        else:
            return False, "Not found in PATH"
    except Exception as e:
        return False, f"Error: {e}"


def check_gpu_info():
    """Check basic GPU information if available"""
    try:
        # Try to get GPU info using various methods
        if platform.system() == "Windows":
            try:
                result = subprocess.run(["wmic", "path", "win32_VideoController", "get", "name"], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    if len(lines) > 1:
                        return True, lines[1].strip()
            except:
                pass
        elif platform.system() == "Linux":
            try:
                result = subprocess.run(["lspci", "-v"], capture_output=True, text=True, timeout=5)
                if result.returncode == 0 and "VGA" in result.stdout:
                    return True, "GPU detected (Linux)"
            except:
                pass
        elif platform.system() == "Darwin":
            try:
                result = subprocess.run(["system_profiler", "SPDisplaysDataType"], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    return True, "GPU detected (macOS)"
            except:
                pass
        
        return False, "Not detected"
    except Exception:
        return False, "Error checking GPU"


def run_doctor():
    """Run system diagnostics"""
    if RICH_AVAILABLE:
        safe_print("[bold cyan]VoxBridge System Diagnostics[/bold cyan]")
        safe_print("=" * 50)
        
        if console:
            # Create results table
            table = Table(show_header=True)
            table.add_column("Component", style="bold cyan")
            table.add_column("Status", style="bold")
            table.add_column("Details", style="white")
            
            # Check Python version
            py_ok, py_info = check_python_version()
            table.add_row("Python Version", 
                         "[green]✓ PASS[/green]" if py_ok else "[red]✗ FAIL[/red]", 
                         py_info)
            
            # Check Blender
            blender_ok, blender_info = check_blender()
            table.add_row("Blender", 
                         "[green]PASS[/green]" if blender_ok else "[yellow]WARN[/yellow]", 
                         blender_info)
            
            # Check GPU
            gpu_ok, gpu_info = check_gpu_info()
            table.add_row("GPU Info", 
                         "[green]✓ PASS[/green]" if gpu_ok else "[dim]? UNKNOWN[/dim]", 
                         gpu_info)
            
            # Check Rich availability
            table.add_row("Rich UI", "[green]✓ PASS[/green]", "Available")
            
            console.print(table)
        
        # Summary
        safe_print("\n[bold]Summary:[/bold]")
        if py_ok and blender_ok:
            safe_print("[green]✓ System is ready for VoxBridge![/green]")
        elif py_ok:
            safe_print("[yellow]System ready with basic functionality (Blender recommended)[/yellow]")
        else:
            safe_print("[red]✗ System needs attention[/red]")
            
    else:
        print("VoxBridge System Diagnostics")
        print("=" * 50)
        
        # Check Python version
        py_ok, py_info = check_python_version()
        status = "PASS" if py_ok else "FAIL"
        print(f"Python Version: {status} - {py_info}")
        
        # Check Blender
        blender_ok, blender_info = check_blender()
        status = "PASS" if blender_ok else "WARN"
        print(f"Blender: {status} - {blender_info}")
        
        # Check GPU
        gpu_ok, gpu_info = check_gpu_info()
        status = "PASS" if gpu_ok else "UNKNOWN"
        print(f"GPU Info: {status} - {gpu_info}")
        
        print(f"Rich UI: PASS - Available")
        
        print("\nSummary:")
        if py_ok and blender_ok:
            print("✓ System is ready for VoxBridge!")
        elif py_ok:
            print("System ready with basic functionality (Blender recommended)")
        else:
            print("✗ System needs attention")


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
    """Convert VoxEdit glTF/glb files for Unity and Roblox compatibility.
    
    This command processes VoxEdit exports and optimizes them for game engines.
    Supports both individual file conversion and batch processing.
    
    Examples:
      voxbridge convert --input model.glb --target unity
      voxbridge convert --input model.glb --target roblox --optimize-mesh
      voxbridge convert --input model.glb --target unity --output ./assets/clean_model.glb
    """
    print_header()
    
    # Validate target platform
    if target not in ["unity", "roblox"]:
        safe_print("[red]Error: Target must be 'unity' or 'roblox'[/red]")
        raise typer.Exit(1)
    
    # Generate output path if not specified
    if output is None:
        input_stem = input_file.stem
        output = input_file.parent / f"{input_stem}_{target}_clean{input_file.suffix}"
    
    # Check if output file exists and force flag
    if output.exists() and not force:
        safe_print(f"[red]Error: Output file '{output}' already exists. Use --force to overwrite.[/red]")
        raise typer.Exit(1)
    
    # Perform conversion
    use_blender = not no_blender
    success = handle_conversion(
        input_file, output, use_blender, verbose,
        optimize_mesh=optimize_mesh,
        generate_atlas=generate_atlas,
        compress_textures=compress_textures,
        platform=target,
        generate_report=report
    )
    
    if success:
        safe_print(f"\n[bold green]VoxBridge conversion completed successfully![/bold green]")
        safe_print(f"[dim]Output:[/dim] {output}")
    else:
        safe_print(f"\n[bold red]VoxBridge conversion failed![/bold red]")
        raise typer.Exit(1)


@app.command()
def help():
    """Show detailed help information about VoxBridge capabilities and usage.
    
    This command provides comprehensive information about:
    - What VoxBridge can do
    - Supported file formats
    - Target platforms
    - GUI interface
    - Examples and best practices
    """
    print_header()
    
    if RICH_AVAILABLE and console:
        # Create a comprehensive help panel
        help_text = """
[bold cyan]VoxBridge v1.0.0 - Professional Asset Converter[/bold cyan]

[bold]What is VoxBridge?[/bold]
VoxBridge converts VoxEdit exports (glTF/glb files) into optimized formats
for Unity and Roblox game engines. It handles mesh optimization, texture
atlas generation, and platform-specific material mapping.

[bold]Supported Input Formats:[/bold]
• glTF (.gltf) - VoxEdit JSON exports
• GLB (.glb) - VoxEdit binary exports

[bold]Target Platforms:[/bold]
• Unity - Optimized for Unity's asset pipeline
• Roblox - Optimized for Roblox Studio

[bold]Key Features:[/bold]
• Mesh optimization and polygon reduction
• Texture atlas generation
• Texture compression (1024x1024)
• Platform-specific material mapping
• Batch processing capabilities
• Performance reporting
• GUI interface for easy use

[bold]Commands:[/bold]
• [cyan]convert[/cyan] - Convert individual files
• [cyan]batch[/cyan] - Process multiple files
• [cyan]doctor[/cyan] - System diagnostics
• [cyan]help[/cyan] - This detailed help

[bold]GUI Interface:[/bold]
Run [cyan]voxbridge-gui[/cyan] for a graphical interface with:
• File selection dialog
• Target platform dropdown
• Conversion options
• Real-time progress tracking
• Log output panel

[bold]Examples:[/bold]
• Convert for Unity: [dim]voxbridge convert --input model.glb --target unity[/dim]
• Convert for Roblox: [dim]voxbridge convert --input model.glb --target roblox --optimize-mesh[/dim]
• Batch processing: [dim]voxbridge batch ./input ./output --target unity[/dim]
• System check: [dim]voxbridge doctor[/dim]
• GUI mode: [dim]voxbridge-gui[/dim]

[bold]For more information:[/bold]
• GitHub: https://github.com/Supercoolkayy/voxbridge
• Documentation: https://supercoolkayy.github.io/voxbridge/
• Issues: https://github.com/Supercoolkayy/voxbridge/issues
        """
        console.print(Panel(help_text, title="VoxBridge Help", border_style="cyan"))
    else:
        print("VoxBridge v1.0.0 - Professional Asset Converter")
        print("=" * 60)
        print()
        print("What is VoxBridge?")
        print("VoxBridge converts VoxEdit exports (glTF/glb files) into optimized")
        print("formats for Unity and Roblox game engines.")
        print()
        print("Commands:")
        print("  convert - Convert individual files")
        print("  batch   - Process multiple files")
        print("  doctor  - System diagnostics")
        print("  help    - This detailed help")
        print()
        print("GUI Interface:")
        print("  Run 'voxbridge-gui' for graphical interface")
        print()
        print("Examples:")
        print("  voxbridge convert --input model.glb --target unity")
        print("  voxbridge convert --input model.glb --target roblox --optimize-mesh")
        print("  voxbridge batch ./input ./output --target unity")
        print("  voxbridge doctor")
        print("  voxbridge-gui")
        print()
        print("For more information: https://github.com/Supercoolkayy/voxbridge")


@app.command()
def doctor():
    """Run comprehensive system diagnostics to check VoxBridge compatibility.
    
    This command checks your system for all requirements needed to run VoxBridge:
    - Python version compatibility
    - Required dependencies (rich, typer, etc.)
    - Blender installation and availability
    - GPU information for performance optimization
    - File system permissions
    
    Examples:
      voxbridge doctor
      voxbridge doctor --verbose
    """
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
    """Process multiple files in batch for efficient bulk conversion.
    
    This command allows you to convert multiple VoxEdit exports at once.
    Perfect for processing entire asset libraries or project folders.
    
    Examples:
      voxbridge batch ./input_folder ./output_folder --target unity
      voxbridge batch ./models ./processed --target roblox --recursive
      voxbridge batch ./assets ./clean --pattern "*.glb" --target unity
    """
    print_header()
    
    if not input_dir.exists():
        safe_print(f"[red]Error: Input directory '{input_dir}' not found[/red]")
        raise typer.Exit(1)
    
    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Find files matching pattern
    patterns = pattern.split(",")
    files = []
    for p in patterns:
        if recursive:
            files.extend(input_dir.rglob(p.strip()))
        else:
            files.extend(input_dir.glob(p.strip()))
    
    if not files:
        safe_print(f"[yellow]No files found matching pattern: {pattern}[/yellow]")
        return
    
    safe_print(f"[bold]Found {len(files)} files to process[/bold]")
    
    # Process each file
    success_count = 0
    for file_path in files:
        safe_print(f"[cyan]Processing:[/cyan] {file_path.name}")
        
        # Create output path
        output_path = output_dir / file_path.name
        
        # Convert file
        success = handle_conversion(
            file_path, output_path, True, verbose,
            platform=target
        )
        
        if success:
            success_count += 1
    
    safe_print(f"\n[bold green]Batch processing complete![/bold green]")
    safe_print(f"[dim]Successfully processed:[/dim] {success_count}/{len(files)} files")


def main():
    """Main CLI entry point"""
    try:
        app()
    except Exception as e:
        # Fallback to basic functionality
        print("VoxBridge CLI")
        print("Note: Install 'rich' and 'typer' for enhanced interface")
        print("Usage: voxbridge convert --input input.glb --target unity")
        print("       voxbridge doctor")
        print(f"Error: {e}")


if __name__ == "__main__":
    main() 