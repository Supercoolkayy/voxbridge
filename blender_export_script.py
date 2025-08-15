
import bpy
import sys

# Get command line arguments
input_file = sys.argv[-2]
output_file = sys.argv[-1]

# Clear scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Import GLB
bpy.ops.import_scene.gltf(filepath=input_file)

# Apply transforms
for obj in bpy.data.objects:
    if obj.type == 'MESH':
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        
        # Reset transforms
        obj.location = (0, 0, 0)
        obj.rotation_euler = (0, 0, 0)
        obj.scale = (1, 1, 1)
        
        # Apply transforms
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

# Export FBX with correct settings
bpy.ops.export_scene.fbx(
    filepath=output_file,
    use_selection=False,
    global_scale=1.0,
    apply_unit_scale=True,
    apply_scale_options='FBX_SCALE_ALL',
    bake_space_transform=True,
    object_types=('MESH', 'ARMATURE'),
    use_mesh_modifiers=True,
    mesh_smooth_type='FACE',
    use_tspace=True,
    use_custom_props=True,
    add_leaf_bones=False,
    primary_bone_axis='Y',
    secondary_bone_axis='X',
    use_armature_deform_only=False,
    bake_anim=True,
    bake_anim_use_all_bones=True,
    bake_anim_use_nla_strips=True,
    bake_anim_use_all_actions=True,
    bake_anim_force_startend_keying=True,
    bake_anim_step=1,
    bake_anim_bake_to_obj=True,
    path_mode='RELATIVE',
    embed_textures=True
)
