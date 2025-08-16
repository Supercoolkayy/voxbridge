#!/usr/bin/env python3
"""
VoxBridge Blender Cleanup Script
Cleans up glTF/glb files exported from VoxEdit for Unity/Roblox compatibility
"""

import bpy
import sys
import os
import re
from pathlib import Path

# Check for required dependencies
try:
    import numpy
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    print("WARNING: numpy not available in Blender's Python environment")
    print("This may cause conversion issues. Install numpy with:")
    print("  /path/to/blender/2.xx/python/bin/python3.7m -m ensurepip")
    print("  /path/to/blender/2.xx/python/bin/python3.7m -m pip install numpy")

def clean_material_name(name):
    """Clean material name to be alphanumeric + underscores only"""
    # Replace non-alphanumeric characters with underscores
    clean_name = re.sub(r'[^a-zA-Z0-9_]', '_', name)
    # Remove multiple consecutive underscores
    clean_name = re.sub(r'_+', '_', clean_name)
    # Remove leading/trailing underscores
    clean_name = clean_name.strip('_')
    # Ensure it's not empty
    if not clean_name:
        clean_name = 'Material'
    return clean_name

def clean_texture_paths():
    """Fix absolute texture paths to relative paths"""
    changes = []
    
    for image in bpy.data.images:
        if image.filepath:
            original_path = image.filepath
            # Convert to just filename (relative path)
            filename = os.path.basename(original_path)
            image.filepath = filename
            
            # If the image was packed, unpack it
            if image.packed_file:
                image.unpack(method='WRITE_LOCAL')
            
            changes.append(f"Fixed texture path: {original_path} -> {filename}")
    
    return changes

def clean_material_names():
    """Clean up material names for Unity/Roblox compatibility"""
    changes = []
    
    for material in bpy.data.materials:
        original_name = material.name
        clean_name = clean_material_name(original_name)
        
        if clean_name != original_name:
            # Check if name already exists, add suffix if needed
            counter = 1
            final_name = clean_name
            while final_name in bpy.data.materials and bpy.data.materials[final_name] != material:
                final_name = f"{clean_name}_{counter:02d}"
                counter += 1
            
            material.name = final_name
            changes.append(f"Renamed material: '{original_name}' -> '{final_name}'")
    
    return changes

def clean_object_names():
    """Clean up object and mesh names"""
    changes = []
    
    for obj in bpy.data.objects:
        if obj.name:
            original_name = obj.name
            clean_name = clean_material_name(original_name)
            
            if clean_name != original_name:
                obj.name = clean_name
                changes.append(f"Renamed object: '{original_name}' -> '{clean_name}'")
        
        # Clean mesh names too
        if obj.type == 'MESH' and obj.data and obj.data.name:
            original_name = obj.data.name
            clean_name = clean_material_name(original_name)
            
            if clean_name != original_name:
                obj.data.name = clean_name
                changes.append(f"Renamed mesh: '{original_name}' -> '{clean_name}'")
    
    return changes

def optimize_for_game_engines():
    """Apply optimizations for Unity/Roblox"""
    changes = []
    
    # Ensure all meshes have proper UVs
    for obj in bpy.data.objects:
        if obj.type == 'MESH':
            mesh = obj.data
            
            # Ensure at least one UV layer exists
            if not mesh.uv_layers:
                mesh.uv_layers.new(name="UVMap")
                changes.append(f"Added UV layer to mesh: {mesh.name}")
            
            # Rename UV layers to standard names
            for i, uv_layer in enumerate(mesh.uv_layers):
                expected_name = f"UVMap" if i == 0 else f"UVMap_{i}"
                if uv_layer.name != expected_name:
                    uv_layer.name = expected_name
                    changes.append(f"Renamed UV layer: {uv_layer.name} -> {expected_name}")
    
    return changes

def optimize_mesh(poly_threshold=5000, reduction_ratio=0.5, split_threshold=20000):
    """
    Reduce polygon count for high-poly meshes and split large meshes into sub-objects.
    Args:
        poly_threshold: Minimum face count to trigger decimation.
        reduction_ratio: Fraction of faces to keep (0.3–0.7 recommended).
        split_threshold: Maximum face count before splitting mesh.
    Returns:
        List of changes made.
    """
    changes = []
    for obj in bpy.data.objects:
        if obj.type == 'MESH':
            mesh = obj.data
            face_count = len(mesh.polygons)
            # Polygon reduction
            if face_count > poly_threshold:
                bpy.context.view_layer.objects.active = obj
                modifier = obj.modifiers.new(name="Decimate", type='DECIMATE')
                modifier.ratio = reduction_ratio
                bpy.ops.object.modifier_apply(modifier=modifier.name)
                new_face_count = len(mesh.polygons)
                changes.append(f"Reduced {obj.name}: {face_count} → {new_face_count} faces")
                face_count = new_face_count
            # Mesh splitting (simple: separate loose parts if above split_threshold)
            if face_count > split_threshold:
                bpy.context.view_layer.objects.active = obj
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.separate(type='LOOSE')
                bpy.ops.object.mode_set(mode='OBJECT')
                changes.append(f"Split {obj.name} into sub-objects due to {face_count} faces")
    return changes

def remove_unused_materials():
    """Remove materials that aren't used by any objects"""
    changes = []
    
    # Find materials that are actually used
    used_materials = set()
    for obj in bpy.data.objects:
        if obj.type == 'MESH' and obj.data.materials:
            for material in obj.data.materials:
                if material:
                    used_materials.add(material.name)
    
    # Remove unused materials
    materials_to_remove = []
    for material in bpy.data.materials:
        if material.name not in used_materials:
            materials_to_remove.append(material)
    
    for material in materials_to_remove:
        bpy.data.materials.remove(material)
        changes.append(f"Removed unused material: {material.name}")
    
    return changes

def main():
    if len(sys.argv) < 7:  # Blender adds 4 default args, plus our 2
        print("Usage: blender --background --python blender_cleanup.py -- input.glb output.glb")
        sys.exit(1)
    
    # Parse command line arguments (after the --)
    try:
        script_args = sys.argv[sys.argv.index("--") + 1:]
        input_path = script_args[0]
        output_path = script_args[1]
    except (ValueError, IndexError):
        print("Error: Could not parse input and output paths")
        sys.exit(1)
    
    input_file = Path(input_path)
    output_file = Path(output_path)
    
    print(f"VoxBridge Blender Cleanup")
    print(f"Input:  {input_file}")
    print(f"Output: {output_file}")
    
    # Clear existing mesh objects
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    
    # Clear existing materials and textures
    for material in bpy.data.materials:
        bpy.data.materials.remove(material)
    for image in bpy.data.images:
        bpy.data.images.remove(image)
    
    try:
        # Import the glTF/glb file
        print("Importing file...")
        if input_file.suffix.lower() == '.glb':
            bpy.ops.import_scene.gltf(filepath=str(input_file))
        elif input_file.suffix.lower() == '.gltf':
            bpy.ops.import_scene.gltf(filepath=str(input_file))
        else:
            print(f"Unsupported format: {input_file.suffix}")
            sys.exit(1)
        
        print("File imported successfully")
        
        # Apply cleanup operations
        all_changes = []
        
        print("Cleaning texture paths...")
        all_changes.extend(clean_texture_paths())
        
        print("Cleaning material names...")
        all_changes.extend(clean_material_names())
        
        print("Cleaning object names...")
        all_changes.extend(clean_object_names())
        
        print("Optimizing for game engines...")
        all_changes.extend(optimize_for_game_engines())

        # Polygon reduction & mesh splitting (if enabled)
        if '--optimize-mesh' in sys.argv:
            print("Applying mesh optimization (polygon reduction & splitting)...")
            all_changes.extend(optimize_mesh())
        
        print("Removing unused materials...")
        all_changes.extend(remove_unused_materials())
        
        # Print summary of changes
        if all_changes:
            print(f"\nApplied {len(all_changes)} fixes:")
            for change in all_changes:
                print(f"  - {change}")
        else:
            print("\nNo changes needed - file was already clean")
        
        # Export the cleaned file
        print(f"\nExporting to {output_file}...")
        
        # Create output directory if needed
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Export based on output format
        if output_file.suffix.lower() == '.glb':
            bpy.ops.export_scene.gltf(
                filepath=str(output_file),
                export_format='GLB',
                export_image_format='AUTO',
                export_texcoords=True,
                export_normals=True,
                export_materials='EXPORT',
                use_selection=False,
                export_extras=False,
                export_yup=True  # Unity uses Y-up
            )
        elif output_file.suffix.lower() == '.gltf':
            bpy.ops.export_scene.gltf(
                filepath=str(output_file),
                export_format='GLTF_SEPARATE',
                export_image_format='AUTO',
                export_texcoords=True,
                export_normals=True,
                export_materials='EXPORT',
                use_selection=False,
                export_extras=False,
                export_yup=True  # Unity uses Y-up
            )
        else:
            print(f"Unsupported output format: {output_file.suffix}")
            sys.exit(1)
        
        print("Export completed successfully!")
        
        # Print final statistics
        print(f"\nFinal Statistics:")
        print(f"  - Objects: {len([obj for obj in bpy.data.objects if obj.type == 'MESH'])}")
        print(f"  - Materials: {len(bpy.data.materials)}")
        print(f"  - Textures: {len(bpy.data.images)}")
        print(f"  - Meshes: {len(bpy.data.meshes)}")
        
    except Exception as e:
        print(f"Error during processing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 