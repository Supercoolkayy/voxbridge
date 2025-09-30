#!/usr/bin/env python3
"""
Unity/Roblox Import Validation Script
Validates that exported models can be properly imported into target platforms
"""

import json
import zipfile
from pathlib import Path
import subprocess
import tempfile
import shutil

class ImportValidator:
    def __init__(self):
        self.results = {
            "unity_validation": {},
            "roblox_validation": {},
            "errors": []
        }
    
    def validate_gltf_structure(self, zip_path, target_platform):
        """Validate GLTF structure for target platform"""
        print(f"\n🔍 Validating GLTF structure for {target_platform}")
        
        try:
            with zipfile.ZipFile(zip_path, 'r') as zf:
                # Find GLTF file
                gltf_files = [f for f in zf.namelist() if f.endswith('.gltf')]
                if not gltf_files:
                    return {"valid": False, "error": "No GLTF file found"}
                
                gltf_file = gltf_files[0]
                gltf_data = zf.read(gltf_file)
                
                # Parse GLTF JSON
                gltf_json = json.loads(gltf_data.decode('utf-8'))
                
                validation_result = {
                    "valid": True,
                    "gltf_file": gltf_file,
                    "structure": {},
                    "warnings": []
                }
                
                # Check basic structure
                required_sections = ['asset', 'scene', 'scenes', 'nodes']
                for section in required_sections:
                    if section in gltf_json:
                        validation_result["structure"][section] = True
                    else:
                        validation_result["structure"][section] = False
                        validation_result["warnings"].append(f"Missing required section: {section}")
                
                # Check for meshes
                if 'meshes' in gltf_json:
                    mesh_count = len(gltf_json['meshes'])
                    validation_result["structure"]["meshes"] = mesh_count
                    if mesh_count == 0:
                        validation_result["warnings"].append("No meshes found")
                
                # Check for materials
                if 'materials' in gltf_json:
                    material_count = len(gltf_json['materials'])
                    validation_result["structure"]["materials"] = material_count
                
                # Check for textures
                if 'textures' in gltf_json:
                    texture_count = len(gltf_json['textures'])
                    validation_result["structure"]["textures"] = texture_count
                
                # Check for animations
                if 'animations' in gltf_json:
                    animation_count = len(gltf_json['animations'])
                    validation_result["structure"]["animations"] = animation_count
                
                # Platform-specific validation
                if target_platform == "unity":
                    validation_result.update(self._validate_unity_specific(gltf_json))
                elif target_platform == "roblox":
                    validation_result.update(self._validate_roblox_specific(gltf_json))
                
                return validation_result
                
        except Exception as e:
            return {"valid": False, "error": str(e)}
    
    def _validate_unity_specific(self, gltf_json):
        """Validate Unity-specific requirements"""
        unity_validation = {
            "unity_compatible": True,
            "unity_warnings": []
        }
        
        # Check for samplers (Unity requires them)
        if 'samplers' not in gltf_json or len(gltf_json['samplers']) == 0:
            unity_validation["unity_warnings"].append("No samplers found - Unity may have issues")
        
        # Check for PBR materials
        if 'materials' in gltf_json:
            pbr_materials = 0
            for material in gltf_json['materials']:
                if 'pbrMetallicRoughness' in material:
                    pbr_materials += 1
            
            if pbr_materials == 0:
                unity_validation["unity_warnings"].append("No PBR materials found")
            else:
                unity_validation["pbr_materials"] = pbr_materials
        
        # Check for proper texture references
        if 'textures' in gltf_json and 'images' in gltf_json:
            texture_image_refs = 0
            for texture in gltf_json['textures']:
                if 'source' in texture:
                    texture_image_refs += 1
            
            if texture_image_refs == 0:
                unity_validation["unity_warnings"].append("No texture-image references found")
        
        return unity_validation
    
    def _validate_roblox_specific(self, gltf_json):
        """Validate Roblox-specific requirements"""
        roblox_validation = {
            "roblox_compatible": True,
            "roblox_warnings": []
        }
        
        # Check for bone hierarchy (Roblox needs proper rigging)
        if 'skins' in gltf_json and 'nodes' in gltf_json:
            skin_count = len(gltf_json['skins'])
            if skin_count > 0:
                roblox_validation["skins"] = skin_count
            else:
                roblox_validation["roblox_warnings"].append("No skins found - animations may not work")
        
        # Check for proper node hierarchy
        if 'nodes' in gltf_json:
            node_count = len(gltf_json['nodes'])
            roblox_validation["nodes"] = node_count
            
            # Check for parent-child relationships
            parent_child_relationships = 0
            for node in gltf_json['nodes']:
                if 'children' in node and len(node['children']) > 0:
                    parent_child_relationships += 1
            
            if parent_child_relationships == 0:
                roblox_validation["roblox_warnings"].append("No parent-child relationships found")
        
        return roblox_validation
    
    def validate_texture_quality(self, zip_path):
        """Validate texture quality and format"""
        print("\n🖼️ Validating texture quality")
        
        try:
            with zipfile.ZipFile(zip_path, 'r') as zf:
                texture_files = [f for f in zf.namelist() if f.startswith('textures/') and f.endswith(('.png', '.jpg', '.jpeg'))]
                
                texture_validation = {
                    "texture_count": len(texture_files),
                    "texture_formats": {},
                    "warnings": []
                }
                
                for texture_file in texture_files:
                    # Extract texture info
                    texture_data = zf.read(texture_file)
                    file_size = len(texture_data)
                    
                    # Determine format
                    if texture_file.endswith('.png'):
                        format_type = 'PNG'
                    elif texture_file.endswith('.jpg') or texture_file.endswith('.jpeg'):
                        format_type = 'JPEG'
                    else:
                        format_type = 'Unknown'
                    
                    if format_type not in texture_validation["texture_formats"]:
                        texture_validation["texture_formats"][format_type] = 0
                    texture_validation["texture_formats"][format_type] += 1
                    
                    # Check file size (warn if too large)
                    if file_size > 5 * 1024 * 1024:  # 5MB
                        texture_validation["warnings"].append(f"Large texture: {texture_file} ({file_size/1024/1024:.1f}MB)")
                
                return texture_validation
                
        except Exception as e:
            return {"error": str(e)}
    
    def validate_animation_quality(self, zip_path):
        """Validate animation quality and structure"""
        print("\n🎬 Validating animation quality")
        
        try:
            with zipfile.ZipFile(zip_path, 'r') as zf:
                # Find report.json
                report_files = [f for f in zf.namelist() if f == 'report.json']
                if not report_files:
                    return {"error": "No report.json found"}
                
                report_data = zf.read(report_files[0])
                report_json = json.loads(report_data.decode('utf-8'))
                
                animation_validation = {
                    "valid": True,
                    "animation_info": {},
                    "warnings": []
                }
                
                # Extract animation info from report
                if 'post_validation' in report_json:
                    post_validation = report_json['post_validation']
                    if 'validation_info' in post_validation:
                        validation_info = post_validation['validation_info']
                        
                        # Check animation count
                        if 'animations' in validation_info:
                            animation_count = validation_info['animations']
                            animation_validation["animation_info"]["count"] = animation_count
                            
                            if animation_count == 0:
                                animation_validation["warnings"].append("No animations found")
                        
                        # Check animation durations
                        if 'animation_durations' in validation_info:
                            durations = validation_info['animation_durations']
                            animation_validation["animation_info"]["durations"] = durations
                            
                            # Check for very short animations
                            for anim in durations:
                                if anim['duration'] < 0.1:
                                    animation_validation["warnings"].append(f"Very short animation: {anim['name']} ({anim['duration']:.3f}s)")
                        
                        # Check bone count
                        if 'total_bones' in validation_info:
                            bone_count = validation_info['total_bones']
                            animation_validation["animation_info"]["bones"] = bone_count
                            
                            if bone_count > 100:
                                animation_validation["warnings"].append(f"High bone count: {bone_count} (may impact performance)")
                
                return animation_validation
                
        except Exception as e:
            return {"error": str(e)}
    
    def validate_zip_package(self, zip_path):
        """Validate the complete ZIP package structure"""
        print(f"\n📦 Validating ZIP package: {zip_path}")
        
        try:
            with zipfile.ZipFile(zip_path, 'r') as zf:
                files = zf.namelist()
                
                package_validation = {
                    "valid": True,
                    "files": files,
                    "structure": {},
                    "warnings": []
                }
                
                # Check for required files
                required_files = {
                    "gltf": [f for f in files if f.endswith('.gltf')],
                    "bin": [f for f in files if f.endswith('.bin')],
                    "report": [f for f in files if f == 'report.json'],
                    "textures": [f for f in files if f.startswith('textures/')]
                }
                
                for file_type, file_list in required_files.items():
                    if file_list:
                        package_validation["structure"][file_type] = len(file_list)
                    else:
                        if file_type in ['gltf', 'bin', 'report']:
                            package_validation["warnings"].append(f"Missing required {file_type} file")
                        else:
                            package_validation["structure"][file_type] = 0
                
                # Check for duplicate files
                seen_files = set()
                duplicates = []
                for file in files:
                    if file in seen_files:
                        duplicates.append(file)
                    seen_files.add(file)
                
                if duplicates:
                    package_validation["warnings"].append(f"Duplicate files found: {duplicates}")
                
                return package_validation
                
        except Exception as e:
            return {"valid": False, "error": str(e)}
    
    def validate_all(self, zip_path, target_platform):
        """Run all validation checks"""
        print(f"🔍 Starting import validation for {target_platform}")
        print("=" * 60)
        
        # Validate ZIP package
        package_validation = self.validate_zip_package(zip_path)
        if not package_validation["valid"]:
            print(f"❌ Package validation failed: {package_validation['error']}")
            return False
        
        # Validate GLTF structure
        gltf_validation = self.validate_gltf_structure(zip_path, target_platform)
        if not gltf_validation["valid"]:
            print(f"❌ GLTF validation failed: {gltf_validation['error']}")
            return False
        
        # Validate textures
        texture_validation = self.validate_texture_quality(zip_path)
        
        # Validate animations
        animation_validation = self.validate_animation_quality(zip_path)
        
        # Print results
        print("\n📊 VALIDATION RESULTS")
        print("=" * 60)
        
        # Package structure
        print(f"📦 Package Structure:")
        for file_type, count in package_validation["structure"].items():
            print(f"  - {file_type}: {count}")
        
        # GLTF structure
        print(f"\n🔧 GLTF Structure:")
        for section, exists in gltf_validation["structure"].items():
            status = "✅" if exists else "❌"
            print(f"  - {section}: {status}")
        
        # Platform-specific validation
        if target_platform == "unity":
            print(f"\n🎮 Unity Compatibility:")
            if "unity_warnings" in gltf_validation:
                for warning in gltf_validation["unity_warnings"]:
                    print(f"  ⚠️ {warning}")
            else:
                print("  ✅ No Unity-specific issues found")
        
        elif target_platform == "roblox":
            print(f"\n🎮 Roblox Compatibility:")
            if "roblox_warnings" in gltf_validation:
                for warning in gltf_validation["roblox_warnings"]:
                    print(f"  ⚠️ {warning}")
            else:
                print("  ✅ No Roblox-specific issues found")
        
        # Texture validation
        if "texture_count" in texture_validation:
            print(f"\n🖼️ Textures: {texture_validation['texture_count']}")
            for format_type, count in texture_validation["texture_formats"].items():
                print(f"  - {format_type}: {count}")
        
        # Animation validation
        if "animation_info" in animation_validation:
            anim_info = animation_validation["animation_info"]
            print(f"\n🎬 Animations: {anim_info.get('count', 0)}")
            if "durations" in anim_info:
                for anim in anim_info["durations"]:
                    print(f"  - {anim['name']}: {anim['duration']:.2f}s")
            if "bones" in anim_info:
                print(f"  - Bones: {anim_info['bones']}")
        
        # Warnings
        all_warnings = []
        all_warnings.extend(package_validation.get("warnings", []))
        all_warnings.extend(gltf_validation.get("warnings", []))
        all_warnings.extend(texture_validation.get("warnings", []))
        all_warnings.extend(animation_validation.get("warnings", []))
        
        if all_warnings:
            print(f"\n⚠️ Warnings ({len(all_warnings)}):")
            for warning in all_warnings:
                print(f"  - {warning}")
        else:
            print(f"\n✅ No warnings found")
        
        return True

def main():
    import sys
    
    if len(sys.argv) != 3:
        print("Usage: python validate_imports.py <zip_path> <target_platform>")
        print("Example: python validate_imports.py test_output/model_unity.zip unity")
        sys.exit(1)
    
    zip_path = sys.argv[1]
    target_platform = sys.argv[2]
    
    if not Path(zip_path).exists():
        print(f"Error: ZIP file not found: {zip_path}")
        sys.exit(1)
    
    if target_platform not in ["unity", "roblox"]:
        print(f"Error: Invalid target platform: {target_platform}")
        print("Valid platforms: unity, roblox")
        sys.exit(1)
    
    validator = ImportValidator()
    success = validator.validate_all(zip_path, target_platform)
    
    if success:
        print(f"\n✅ Import validation completed successfully!")
    else:
        print(f"\n❌ Import validation failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
