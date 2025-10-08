#!/usr/bin/env python3
"""
VoxBridge CLI - Command Line Interface for VoxEdit to Unity/Roblox Converter
Standalone version for PyInstaller
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

# Add the voxbridge package to the path
sys.path.insert(0, str(Path(__file__).parent))

from voxbridge.converter import VoxBridgeConverter

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Create Typer app
app = Typer(
    name="voxbridge",
    help="VoxEdit to Unity/Roblox GLTF Converter",
    add_completion=False
)

# Initialize console for rich output
console = Console() if RICH_AVAILABLE else None

def print_rich(text: str, style: str = None):
    """Print with rich formatting if available, otherwise plain text"""
    if console:
        console.print(text, style=style)
    else:
        print(text)

def print_panel(title: str, content: str, style: str = "blue"):
    """Print a rich panel if available, otherwise plain text"""
    if console:
        console.print(Panel(content, title=title, style=style))
    else:
        print(f"\n{title}")
        print("=" * len(title))
        print(content)
        print("=" * len(title))

def print_table(headers: List[str], rows: List[List[str]]):
    """Print a rich table if available, otherwise plain text"""
    if console:
        table = Table()
        for header in headers:
            table.add_column(header)
        for row in rows:
            table.add_row(*row)
        console.print(table)
    else:
        # Plain text table
        col_widths = [max(len(str(row[i])) for row in [headers] + rows) for i in range(len(headers))]
        print(" | ".join(f"{headers[i]:<{col_widths[i]}}" for i in range(len(headers))))
        print("-" * (sum(col_widths) + 3 * (len(headers) - 1)))
        for row in rows:
            print(" | ".join(f"{str(row[i]):<{col_widths[i]}}" for i in range(len(row))))

@app.command()
def convert(
    input_path: str = typer.Argument(..., help="Path to input VOX file or directory"),
    output_path: str = typer.Argument(..., help="Path to output GLTF file or directory"),
    platform: str = typer.Option("unity", help="Target platform (unity, roblox)"),
    quality: str = typer.Option("medium", help="Quality setting (low, medium, high)"),
    optimize_textures: bool = typer.Option(True, help="Optimize textures"),
    verbose: bool = typer.Option(False, help="Enable verbose output")
):
    """Convert VOX files to GLTF format for Unity or Roblox"""
    
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    input_path = Path(input_path)
    output_path = Path(output_path)
    
    if not input_path.exists():
        print_rich(f"❌ Error: Input path '{input_path}' does not exist", "red")
        raise typer.Exit(1)
    
    print_panel("VoxBridge Converter", f"Converting VOX files to {platform.upper()} GLTF format")
    
    try:
        converter = VoxBridgeConverter()
        
        # Set platform-specific settings
        if platform.lower() == "roblox":
            converter.set_platform_profile("roblox")
        else:
            converter.set_platform_profile("unity")
        
        # Set quality settings
        quality_settings = {
            "low": {"texture_size": 256, "lod_levels": 1},
            "medium": {"texture_size": 512, "lod_levels": 2},
            "high": {"texture_size": 1024, "lod_levels": 3}
        }
        
        settings = quality_settings.get(quality.lower(), quality_settings["medium"])
        converter.set_quality_settings(settings)
        
        if input_path.is_file():
            # Single file conversion
            print_rich(f"🔄 Converting: {input_path.name}", "yellow")
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TimeElapsedColumn(),
                console=console
            ) if console else None as progress:
                
                task = progress.add_task("Converting...", total=100) if progress else None
                
                result = converter.convert_file(
                    str(input_path),
                    str(output_path),
                    optimize_textures=optimize_textures
                )
                
                if progress and task:
                    progress.update(task, completed=100)
            
            if result:
                print_rich(f" Successfully converted: {output_path}", "green")
            else:
                print_rich(f"❌ Failed to convert: {input_path}", "red")
                raise typer.Exit(1)
                
        else:
            # Directory conversion
            vox_files = list(input_path.glob("**/*.vox"))
            if not vox_files:
                print_rich(f"❌ No VOX files found in: {input_path}", "red")
                raise typer.Exit(1)
            
            print_rich(f"📁 Found {len(vox_files)} VOX files", "blue")
            
            # Create output directory if it doesn't exist
            output_path.mkdir(parents=True, exist_ok=True)
            
            successful = 0
            failed = 0
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TimeElapsedColumn(),
                console=console
            ) if console else None as progress:
                
                task = progress.add_task("Converting files...", total=len(vox_files)) if progress else None
                
                for vox_file in vox_files:
                    relative_path = vox_file.relative_to(input_path)
                    output_file = output_path / relative_path.with_suffix('.gltf')
                    
                    # Create output subdirectory if needed
                    output_file.parent.mkdir(parents=True, exist_ok=True)
                    
                    if progress and task:
                        progress.update(task, description=f"Converting {vox_file.name}")
                    
                    result = converter.convert_file(
                        str(vox_file),
                        str(output_file),
                        optimize_textures=optimize_textures
                    )
                    
                    if result:
                        successful += 1
                    else:
                        failed += 1
                        print_rich(f"❌ Failed: {vox_file.name}", "red")
                    
                    if progress and task:
                        progress.advance(task)
            
            # Summary
            print_panel("Conversion Summary", f" Successful: {successful}\n❌ Failed: {failed}")
            
            if failed > 0:
                raise typer.Exit(1)
    
    except Exception as e:
        print_rich(f"❌ Error during conversion: {str(e)}", "red")
        if verbose:
            import traceback
            traceback.print_exc()
        raise typer.Exit(1)

@app.command()
def info(
    input_path: str = typer.Argument(..., help="Path to VOX file to analyze")
):
    """Display information about a VOX file"""
    
    input_path = Path(input_path)
    
    if not input_path.exists():
        print_rich(f"❌ Error: File '{input_path}' does not exist", "red")
        raise typer.Exit(1)
    
    if not input_path.suffix.lower() == '.vox':
        print_rich(f"❌ Error: File '{input_path}' is not a VOX file", "red")
        raise typer.Exit(1)
    
    try:
        converter = VoxBridgeConverter()
        info_data = converter.get_file_info(str(input_path))
        
        print_panel("VOX File Information", f"File: {input_path.name}")
        
        # Display file information
        rows = [
            ["Property", "Value"],
            ["File Size", f"{input_path.stat().st_size:,} bytes"],
            ["Dimensions", f"{info_data.get('width', 'N/A')} x {info_data.get('height', 'N/A')} x {info_data.get('depth', 'N/A')}"],
            ["Voxel Count", f"{info_data.get('voxel_count', 'N/A'):,}"],
            ["Color Count", f"{info_data.get('color_count', 'N/A')}"],
            ["Material Count", f"{info_data.get('material_count', 'N/A')}"],
        ]
        
        print_table(["Property", "Value"], rows[1:])
        
    except Exception as e:
        print_rich(f"❌ Error analyzing file: {str(e)}", "red")
        raise typer.Exit(1)

@app.command()
def platforms():
    """List available platform profiles"""
    
    try:
        converter = VoxBridgeConverter()
        profiles = converter.get_available_platforms()
        
        print_panel("Available Platform Profiles", "Platform-specific optimization settings")
        
        rows = [["Platform", "Description", "Optimizations"]]
        for platform, info in profiles.items():
            rows.append([
                platform.title(),
                info.get('description', 'N/A'),
                ', '.join(info.get('features', []))
            ])
        
        print_table(["Platform", "Description", "Optimizations"], rows[1:])
        
    except Exception as e:
        print_rich(f"❌ Error getting platform info: {str(e)}", "red")
        raise typer.Exit(1)

@app.command()
def version():
    """Show version information"""
    
    try:
        import voxbridge
        version_info = f"VoxBridge {voxbridge.__version__}"
        
        print_panel("Version Information", version_info)
        
        # Additional system info
        rows = [
            ["Component", "Version"],
            ["VoxBridge", voxbridge.__version__],
            ["Python", f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"],
            ["Platform", f"{sys.platform}"],
        ]
        
        print_table(["Component", "Version"], rows[1:])
        
    except Exception as e:
        print_rich(f"❌ Error getting version info: {str(e)}", "red")
        raise typer.Exit(1)

def main():
    """Main entry point"""
    try:
        app()
    except KeyboardInterrupt:
        print_rich("\n⚠️  Operation cancelled by user", "yellow")
        raise typer.Exit(1)
    except Exception as e:
        print_rich(f"❌ Unexpected error: {str(e)}", "red")
        raise typer.Exit(1)

if __name__ == "__main__":
    main()
