#!/usr/bin/env python3
"""
Unit tests for VoxBridge converter module
"""

import json
import unittest
from pathlib import Path
import tempfile
import shutil
from unittest.mock import patch, MagicMock

# Import the converter module
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from voxbridge.converter import (
    VoxBridgeConverter, 
    InputValidationError, 
    ConversionError, 
    BlenderNotFoundError
)

# Try to import PIL for texture tests
try:
    from PIL import Image  # type: ignore
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


class TestVoxBridgeConverter(unittest.TestCase):
    """Test cases for VoxBridgeConverter class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.converter = VoxBridgeConverter()
        self.test_dir = Path(tempfile.mkdtemp())
        
        # Create sample glTF content
        self.sample_gltf = {
            "asset": {"version": "2.0"},
            "scene": 0,
            "scenes": [{"nodes": [0]}],
            "nodes": [{"mesh": 0}],
            "meshes": [{"primitives": [{"attributes": {"POSITION": 0}}]}],
            "accessors": [{"bufferView": 0, "componentType": 5126, "count": 3, "type": "VEC3"}],
            "bufferViews": [{"buffer": 0, "byteLength": 36, "byteOffset": 0}],
            "buffers": [{"byteLength": 36, "uri": "data.bin"}],
            "materials": [
                {"name": "Material #1 (Special!)"},
                {"name": "Another-Bad*Name"},
                {"name": "GoodName"}
            ],
            "images": [
                {"uri": "C:\\absolute\\path\\texture.png"},
                {"uri": "/unix/absolute/path/texture2.jpg"},
                {"uri": "relative_texture.png"}
            ]
        }
        
    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.test_dir)
    
    def create_test_gltf(self, content=None):
        """Create a test glTF file"""
        if content is None:
            content = self.sample_gltf
            
        gltf_path = self.test_dir / "test.gltf"
        with open(gltf_path, 'w') as f:
            json.dump(content, f)
        return gltf_path
    
    def create_test_glb(self):
        """Create a dummy GLB file"""
        glb_path = self.test_dir / "test.glb"
        # GLB files start with "glTF" magic bytes
        with open(glb_path, 'wb') as f:
            f.write(b'glTF')  # Magic
            f.write(b'\x02\x00\x00\x00')  # Version 2
            f.write(b'\x20\x00\x00\x00')  # Total length (32 bytes)
            f.write(b'\x10\x00\x00\x00')  # JSON chunk length (16 bytes)
            f.write(b'JSON')  # JSON chunk type
            f.write(b'{"asset":{"version":"2.0"}}')  # Minimal JSON
        return glb_path
    
    def test_validate_input_valid_gltf(self):
        """Test input validation with valid glTF file"""
        gltf_path = self.create_test_gltf()
        self.assertTrue(self.converter.validate_input(gltf_path))
    
    def test_validate_input_valid_glb(self):
        """Test input validation with valid GLB file"""
        glb_path = self.create_test_glb()
        self.assertTrue(self.converter.validate_input(glb_path))
    
    def test_validate_input_nonexistent_file(self):
        """Test input validation with nonexistent file"""
        fake_path = self.test_dir / "nonexistent.gltf"
        self.assertFalse(self.converter.validate_input(fake_path))
    
    def test_validate_input_wrong_extension(self):
        """Test input validation with wrong file extension"""
        txt_path = self.test_dir / "test.txt"
        txt_path.write_text("not a gltf file")
        self.assertFalse(self.converter.validate_input(txt_path))
    
    def test_clean_gltf_json_material_names(self):
        """Test cleaning of material names"""
        gltf_path = self.create_test_gltf()
        cleaned_data, changes = self.converter.clean_gltf_json(gltf_path)
        
        # Check that material names were cleaned
        materials = cleaned_data['materials']
        self.assertEqual(materials[0]['name'], 'Material_1_Special')
        self.assertEqual(materials[1]['name'], 'Another_Bad_Name')
        self.assertEqual(materials[2]['name'], 'GoodName')  # Should be unchanged
        
        # Check that changes were recorded
        self.assertEqual(len(changes), 2)  # Two materials were changed
        self.assertIn('Material_1_Special', changes[0])
        self.assertIn('Another_Bad_Name', changes[1])
    
    def test_clean_gltf_json_texture_paths(self):
        """Test cleaning of texture paths"""
        gltf_path = self.create_test_gltf()
        cleaned_data, changes = self.converter.clean_gltf_json(gltf_path)
        
        # Check that texture paths were cleaned
        images = cleaned_data['images']
        self.assertEqual(images[0]['uri'], 'texture.png')
        self.assertEqual(images[1]['uri'], 'texture2.jpg')
        self.assertEqual(images[2]['uri'], 'relative_texture.png')  # Should be unchanged
        
        # Check that changes were recorded
        texture_changes = [c for c in changes if 'Fixed image' in c]
        self.assertEqual(len(texture_changes), 2)  # Two images were changed
    
    def test_clean_gltf_json_no_changes_needed(self):
        """Test glTF cleaning when no changes are needed"""
        clean_gltf = {
            "asset": {"version": "2.0"},
            "materials": [{"name": "CleanMaterial"}],
            "images": [{"uri": "clean_texture.png"}]
        }
        
        gltf_path = self.create_test_gltf(clean_gltf)
        cleaned_data, changes = self.converter.clean_gltf_json(gltf_path)
        
        # Should be no changes
        self.assertEqual(len(changes), 0)
        self.assertEqual(cleaned_data['materials'][0]['name'], 'CleanMaterial')
        self.assertEqual(cleaned_data['images'][0]['uri'], 'clean_texture.png')
    
    def test_validate_output_gltf(self):
        """Test output validation for glTF files"""
        # Create output file
        output_path = self.test_dir / "output.gltf"
        with open(output_path, 'w') as f:
            json.dump(self.sample_gltf, f)
        
        stats = self.converter.validate_output(output_path)
        
        self.assertTrue(stats['file_exists'])
        self.assertGreater(stats['file_size'], 0)
        self.assertEqual(stats['materials'], 3)
        self.assertEqual(stats['textures'], 3)
        self.assertEqual(stats['meshes'], 1)
        self.assertEqual(stats['nodes'], 1)
    
    def test_validate_output_glb(self):
        """Test output validation for GLB files"""
        glb_path = self.create_test_glb()
        stats = self.converter.validate_output(glb_path)
        
        self.assertTrue(stats['file_exists'])
        self.assertGreater(stats['file_size'], 0)
        self.assertIn('note', stats)
        self.assertIn('GLB format', stats['note'])
    
    def test_validate_output_nonexistent(self):
        """Test output validation for nonexistent file"""
        fake_path = self.test_dir / "nonexistent.gltf"
        stats = self.converter.validate_output(fake_path)
        
        self.assertFalse(stats['file_exists'])
        self.assertEqual(stats['file_size'], 0)
    
    @patch('shutil.which')
    def test_find_blender_in_path(self, mock_which):
        """Test finding Blender in PATH"""
        mock_which.return_value = "/usr/bin/blender"
        blender_path = self.converter.find_blender()
        self.assertEqual(blender_path, "blender")
    
    @patch('shutil.which')
    @patch('os.path.exists')
    def test_find_blender_standard_location(self, mock_exists, mock_which):
        """Test finding Blender in standard installation location"""
        mock_which.return_value = None
        
        def exists_side_effect(path):
            return path == "/Applications/Blender.app/Contents/MacOS/Blender"
        
        mock_exists.side_effect = exists_side_effect
        blender_path = self.converter.find_blender()
        self.assertEqual(blender_path, "/Applications/Blender.app/Contents/MacOS/Blender")
    
    @patch('shutil.which')
    @patch('os.path.exists')
    def test_find_blender_not_found(self, mock_exists, mock_which):
        """Test when Blender is not found"""
        mock_which.return_value = None
        mock_exists.return_value = False
        blender_path = self.converter.find_blender()
        self.assertIsNone(blender_path)
    
    def test_convert_gltf_json(self):
        """Test glTF JSON conversion"""
        input_path = self.create_test_gltf()
        output_path = self.test_dir / "output.gltf"
        
        success = self.converter.convert_gltf_json(input_path, output_path)
        
        self.assertTrue(success)
        self.assertTrue(output_path.exists())
        
        # Verify the output was cleaned
        with open(output_path, 'r') as f:
            output_data = json.load(f)
        
        # Check material names were cleaned
        self.assertEqual(output_data['materials'][0]['name'], 'Material_1_Special')
        # Check texture paths were cleaned
        self.assertEqual(output_data['images'][0]['uri'], 'texture.png')
    
    def test_copy_associated_files(self):
        """Test copying of associated files (textures, bin files)"""
        # Create input files
        input_gltf = self.test_dir / "input.gltf"
        texture_file = self.test_dir / "texture.png"
        bin_file = self.test_dir / "data.bin"
        
        input_gltf.write_text('{"test": "data"}')
        texture_file.write_bytes(b'fake png data')
        bin_file.write_bytes(b'fake bin data')
        
        # Create output directory
        output_dir = self.test_dir / "output"
        output_dir.mkdir()
        output_gltf = output_dir / "output.gltf"
        
        # Copy associated files
        self.converter.copy_associated_files(input_gltf, output_gltf)
        
        # Check files were copied
        self.assertTrue((output_dir / "texture.png").exists())
        self.assertTrue((output_dir / "data.bin").exists())
    
    @patch.object(VoxBridgeConverter, 'find_blender')
    def test_convert_with_blender_not_found(self, mock_find_blender):
        """Test Blender conversion when Blender is not found"""
        mock_find_blender.return_value = None
        
        input_path = self.create_test_glb()
        output_path = self.test_dir / "output.glb"
        
        with self.assertRaises(RuntimeError) as context:
            self.converter.convert_with_blender(input_path, output_path)
        
        self.assertIn("Blender not found", str(context.exception))
    
    @patch.object(VoxBridgeConverter, 'find_blender')
    @patch('subprocess.run')
    def test_convert_with_blender_success(self, mock_run, mock_find_blender):
        """Test successful Blender conversion"""
        mock_find_blender.return_value = "/usr/bin/blender"
        mock_run.return_value = MagicMock(returncode=0)
        
        input_path = self.create_test_glb()
        output_path = self.test_dir / "output.glb"
        
        success = self.converter.convert_with_blender(input_path, output_path)
        
        self.assertTrue(success)
        mock_run.assert_called_once()
        
        # Check command was constructed correctly
        args, kwargs = mock_run.call_args
        cmd = args[0]
        self.assertEqual(cmd[0], "/usr/bin/blender")
        self.assertIn("--background", cmd)
        self.assertIn("--python", cmd)
    
    @patch.object(VoxBridgeConverter, 'find_blender')
    @patch('subprocess.run')
    def test_convert_with_blender_failure(self, mock_run, mock_find_blender):
        """Test Blender conversion failure"""
        mock_find_blender.return_value = "/usr/bin/blender"
        mock_run.return_value = MagicMock(returncode=1, stderr="Blender error")
        
        input_path = self.create_test_glb()
        output_path = self.test_dir / "output.glb"
        
        with self.assertRaises(RuntimeError) as context:
            self.converter.convert_with_blender(input_path, output_path)
        
        self.assertIn("Blender failed", str(context.exception))
    
    @patch.object(VoxBridgeConverter, 'find_blender')
    @patch('subprocess.run')
    def test_convert_with_blender_timeout(self, mock_run, mock_find_blender):
        """Test Blender conversion timeout"""
        mock_find_blender.return_value = "/usr/bin/blender"
        mock_run.side_effect = subprocess.TimeoutExpired("blender", 120)
        
        input_path = self.create_test_glb()
        output_path = self.test_dir / "output.glb"
        
        with self.assertRaises(RuntimeError) as context:
            self.converter.convert_with_blender(input_path, output_path)
        
        self.assertIn("timed out", str(context.exception))
    
    def test_convert_file_gltf_without_blender(self):
        """Test file conversion for glTF without Blender"""
        input_path = self.create_test_gltf()
        output_path = self.test_dir / "output.gltf"
        
        success = self.converter.convert_file(input_path, output_path, use_blender=False)
        
        self.assertTrue(success)
        self.assertTrue(output_path.exists())
    
    @patch.object(VoxBridgeConverter, 'convert_with_blender')
    def test_convert_file_glb_with_blender(self, mock_convert_blender):
        """Test file conversion for GLB with Blender"""
        mock_convert_blender.return_value = True
        
        input_path = self.create_test_glb()
        output_path = self.test_dir / "output.glb"
        
        success = self.converter.convert_file(input_path, output_path, use_blender=True)
        
        self.assertTrue(success)
        mock_convert_blender.assert_called_once_with(input_path, output_path)
    
    def test_convert_file_creates_output_directory(self):
        """Test that convert_file creates output directory if it doesn't exist"""
        input_path = self.create_test_gltf()
        output_dir = self.test_dir / "nested" / "output" / "dir"
        output_path = output_dir / "output.gltf"
        
        success = self.converter.convert_file(input_path, output_path, use_blender=False)
        
        self.assertTrue(success)
        self.assertTrue(output_dir.exists())
        self.assertTrue(output_path.exists())

    def test_texture_compression(self):
        """Test compressing/resizing textures in glTF conversion"""
        if not PIL_AVAILABLE:
            self.skipTest("PIL/Pillow not installed - skipping texture compression test")
            
        gltf_path = self.create_test_gltf()
        output_path = self.test_dir / "output.gltf"
        # Create a fake large texture
        img_path = self.test_dir / "texture.png"
        img = Image.new('RGBA', (2048, 2048), color=(255, 0, 0, 255))
        img.save(img_path)
        # Patch glTF to reference this texture
        with open(gltf_path, 'r+') as f:
            data = json.load(f)
            data['images'][0]['uri'] = "texture.png"
            f.seek(0)
            json.dump(data, f)
            f.truncate()
        # Run conversion with compression
        self.converter.convert_gltf_json(gltf_path, output_path, compress_textures=True)
        # Check that the texture was resized
        img2 = Image.open(img_path)
        self.assertLessEqual(max(img2.size), 1024)

    def test_texture_atlas_generation(self):
        """Test generating a texture atlas in glTF conversion"""
        if not PIL_AVAILABLE:
            self.skipTest("PIL/Pillow not installed - skipping texture atlas test")
            
        gltf_path = self.create_test_gltf()
        output_path = self.test_dir / "output.gltf"
        # Create two fake textures
        img1 = self.test_dir / "texture1.png"
        img2 = self.test_dir / "texture2.png"
        Image.new('RGBA', (256, 256), color=(255, 0, 0, 255)).save(img1)
        Image.new('RGBA', (256, 256), color=(0, 255, 0, 255)).save(img2)
        # Patch glTF to reference these textures
        with open(gltf_path, 'r+') as f:
            data = json.load(f)
            data['images'][0]['uri'] = "texture1.png"
            data['images'].append({'uri': "texture2.png"})
            f.seek(0)
            json.dump(data, f)
            f.truncate()
        # Run conversion with atlas generation
        self.converter.convert_gltf_json(gltf_path, output_path, generate_atlas=True)
        # Check that the atlas file was created
        atlas_path = self.test_dir / "texture_atlas.png"
        self.assertTrue(atlas_path.exists())


class TestVoxBridgeConverterEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions"""
    
    def setUp(self):
        self.converter = VoxBridgeConverter()
        self.test_dir = Path(tempfile.mkdtemp())
    
    def tearDown(self):
        shutil.rmtree(self.test_dir)
    
    def test_clean_gltf_empty_material_name(self):
        """Test cleaning empty material names"""
        gltf_data = {
            "materials": [
                {"name": ""},
                {"name": "!!!"},  # Only special characters
                {"name": "   "},  # Only whitespace
            ]
        }
        
        gltf_path = self.test_dir / "test.gltf"
        with open(gltf_path, 'w') as f:
            json.dump(gltf_data, f)
        
        cleaned_data, changes = self.converter.clean_gltf_json(gltf_path)
        
        materials = cleaned_data['materials']
        # Empty names should be replaced with 'Material'
        self.assertEqual(materials[0]['name'], 'Material')
        self.assertEqual(materials[1]['name'], 'Material')
        self.assertEqual(materials[2]['name'], 'Material')
    
    def test_clean_gltf_no_materials_or_images(self):
        """Test cleaning glTF with no materials or images"""
        gltf_data = {
            "asset": {"version": "2.0"},
            "scene": 0
        }
        
        gltf_path = self.test_dir / "test.gltf"
        with open(gltf_path, 'w') as f:
            json.dump(gltf_data, f)
        
        cleaned_data, changes = self.converter.clean_gltf_json(gltf_path)
        
        # Should not crash and should return no changes
        self.assertEqual(len(changes), 0)
        self.assertEqual(cleaned_data, gltf_data)
    
    def test_clean_gltf_malformed_json(self):
        """Test handling of malformed JSON"""
        gltf_path = self.test_dir / "malformed.gltf"
        with open(gltf_path, 'w') as f:
            f.write("{ invalid json }")
        
        with self.assertRaises(json.JSONDecodeError):
            self.converter.clean_gltf_json(gltf_path)
    
    def test_validate_output_invalid_json(self):
        """Test output validation with invalid JSON"""
        output_path = self.test_dir / "invalid.gltf"
        with open(output_path, 'w') as f:
            f.write("{ invalid json }")
        
        stats = self.converter.validate_output(output_path)
        
        self.assertTrue(stats['file_exists'])
        self.assertGreater(stats['file_size'], 0)
        self.assertIn('error', stats)
    
    def test_copy_associated_files_no_files(self):
        """Test copying associated files when none exist"""
        input_path = self.test_dir / "input.gltf"
        output_path = self.test_dir / "output" / "output.gltf"
        
        input_path.write_text('{}')
        output_path.parent.mkdir()
        
        # Should not crash when no associated files exist
        self.converter.copy_associated_files(input_path, output_path)
        
        # Only the input file should exist in input dir
        input_files = list(self.test_dir.iterdir())
        self.assertEqual(len(input_files), 2)  # input.gltf and output dir


class TestVoxBridgeConverterIntegration(unittest.TestCase):
    """Integration tests for complete workflows"""
    
    def setUp(self):
        self.converter = VoxBridgeConverter()
        self.test_dir = Path(tempfile.mkdtemp())
        
        # Create a realistic VoxEdit-style glTF with problems
        self.voxedit_gltf = {
            "asset": {"version": "2.0", "generator": "VoxEdit"},
            "scene": 0,
            "scenes": [{"nodes": [0, 1]}],
            "nodes": [
                {"mesh": 0, "name": "Voxel Object #1"},
                {"mesh": 1, "name": "Another-Object*"}
            ],
            "meshes": [
                {"primitives": [{"attributes": {"POSITION": 0}, "material": 0}]},
                {"primitives": [{"attributes": {"POSITION": 1}, "material": 1}]}
            ],
            "materials": [
                {"name": "Material #1 (Red)", "pbrMetallicRoughness": {"baseColorFactor": [1, 0, 0, 1]}},
                {"name": "Blue*Material!", "pbrMetallicRoughness": {"baseColorFactor": [0, 0, 1, 1]}}
            ],
            "images": [
                {"uri": "C:\\VoxEdit\\Exports\\texture_red.png"},
                {"uri": "/home/user/VoxEdit/texture_blue.jpg"}
            ],
            "textures": [
                {"source": 0},
                {"source": 1}
            ],
            "accessors": [
                {"bufferView": 0, "componentType": 5126, "count": 24, "type": "VEC3"},
                {"bufferView": 1, "componentType": 5126, "count": 24, "type": "VEC3"}
            ],
            "bufferViews": [
                {"buffer": 0, "byteLength": 288, "byteOffset": 0},
                {"buffer": 0, "byteLength": 288, "byteOffset": 288}
            ],
            "buffers": [{"byteLength": 576, "uri": "model.bin"}]
        }
    
    def tearDown(self):
        shutil.rmtree(self.test_dir)
    
    def create_voxedit_scene(self):
        """Create a complete VoxEdit-style scene with associated files"""
        # Create main glTF file
        gltf_path = self.test_dir / "voxel_house.gltf"
        with open(gltf_path, 'w') as f:
            json.dump(self.voxedit_gltf, f, indent=2)
        
        # Create associated files
        (self.test_dir / "texture_red.png").write_bytes(b'fake png data')
        (self.test_dir / "texture_blue.jpg").write_bytes(b'fake jpg data')
        (self.test_dir / "model.bin").write_bytes(b'fake binary data' * 36)  # 576 bytes
        
        return gltf_path
    
    def test_complete_voxedit_conversion(self):
        """Test complete conversion of VoxEdit-style file"""
        input_path = self.create_voxedit_scene()
        output_path = self.test_dir / "output" / "clean_house.gltf"
        
        success = self.converter.convert_file(input_path, output_path, use_blender=False)
        
        self.assertTrue(success)
        self.assertTrue(output_path.exists())
        
        # Verify the cleanup was applied
        with open(output_path, 'r') as f:
            cleaned_data = json.load(f)
        
        # Check material names were cleaned
        materials = cleaned_data['materials']
        self.assertEqual(materials[0]['name'], 'Material_1_Red')
        self.assertEqual(materials[1]['name'], 'Blue_Material')
        
        # Check texture paths were cleaned
        images = cleaned_data['images']
        self.assertEqual(images[0]['uri'], 'texture_red.png')
        self.assertEqual(images[1]['uri'], 'texture_blue.jpg')
        
        # Check associated files were copied
        output_dir = output_path.parent
        self.assertTrue((output_dir / "texture_red.png").exists())
        self.assertTrue((output_dir / "texture_blue.jpg").exists())
        self.assertTrue((output_dir / "model.bin").exists())
        
        # Validate the output
        stats = self.converter.validate_output(output_path)
        self.assertTrue(stats['file_exists'])
        self.assertEqual(stats['materials'], 2)
        self.assertEqual(stats['textures'], 2)
        self.assertEqual(stats['meshes'], 2)
        self.assertEqual(stats['nodes'], 2)


if __name__ == '__main__':
    # Import subprocess for the timeout test
    import subprocess
    
    unittest.main(verbosity=2)