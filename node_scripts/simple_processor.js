#!/usr/bin/env node

/**
 * Simple GLTF processor without native dependencies
 * This version avoids sharp and other native modules that break pkg bundling
 */

const fs = require('fs');
const path = require('path');
const { program } = require('commander');

program
  .name('voxbridge-simple-processor')
  .description('Simple GLTF processor without native dependencies')
  .version('1.0.0')
  .option('-i, --input <file>', 'Input GLTF/GLB file')
  .option('-o, --output <dir>', 'Output directory')
  .option('-t, --target <platform>', 'Target platform (unity, roblox, gltf)', 'gltf')
  .option('--verbose', 'Verbose output')
  .parse();

const options = program.opts();

if (!options.input || !options.output) {
  console.error('Error: Input and output are required');
  process.exit(1);
}

function processGLTF(inputPath, outputPath, target, verbose = false) {
  try {
    if (verbose) {
      console.log(`Processing ${inputPath} for target ${target}`);
      console.log(`Output: ${outputPath}`);
    }

    // Ensure output directory exists
    if (!fs.existsSync(outputPath)) {
      fs.mkdirSync(outputPath, { recursive: true });
    }

    // Read input file
    const inputBuffer = fs.readFileSync(inputPath);
    const inputExt = path.extname(inputPath).toLowerCase();
    
    if (verbose) {
      console.log(`Input file size: ${inputBuffer.length} bytes`);
      console.log(`Input format: ${inputExt}`);
    }

    // For GLB files, we need to extract GLTF data
    let gltfData;
    if (inputExt === '.glb') {
      // Simple GLB parsing (extract JSON chunk)
      const dataView = new DataView(inputBuffer.buffer, inputBuffer.byteOffset, inputBuffer.byteLength);
      
      // GLB header: magic (4) + version (4) + length (4)
      if (dataView.getUint32(0, true) !== 0x46546C67) { // "glTF"
        throw new Error('Invalid GLB file: missing glTF magic');
      }
      
      const version = dataView.getUint32(4, true);
      const totalLength = dataView.getUint32(8, true);
      
      if (verbose) {
        console.log(`GLB version: ${version}, total length: ${totalLength}`);
      }

      // Find JSON chunk
      let offset = 12;
      let jsonChunk = null;
      let binChunk = null;
      
      while (offset < totalLength) {
        const chunkLength = dataView.getUint32(offset, true);
        const chunkType = dataView.getUint32(offset + 4, true);
        
        if (chunkType === 0x4E4F534A) { // "JSON"
          jsonChunk = inputBuffer.slice(offset + 8, offset + 8 + chunkLength);
        } else if (chunkType === 0x004E4942) { // "BIN\0"
          binChunk = inputBuffer.slice(offset + 8, offset + 8 + chunkLength);
        }
        
        offset += 8 + chunkLength;
      }

      if (!jsonChunk) {
        throw new Error('No JSON chunk found in GLB file');
      }

      gltfData = JSON.parse(jsonChunk.toString('utf8'));
      
      if (verbose) {
        console.log('GLTF data extracted from GLB');
        console.log(`Nodes: ${gltfData.nodes?.length || 0}`);
        console.log(`Meshes: ${gltfData.meshes?.length || 0}`);
        console.log(`Animations: ${gltfData.animations?.length || 0}`);
        console.log(`Skins: ${gltfData.skins?.length || 0}`);
      }
    } else {
      // Direct GLTF file
      gltfData = JSON.parse(inputBuffer.toString('utf8'));
    }

    // Apply platform-specific modifications
    if (target === 'unity') {
      gltfData = modifyForUnity(gltfData, verbose);
    } else if (target === 'roblox') {
      gltfData = modifyForRoblox(gltfData, verbose);
    }

    // Write output
    const outputFileName = path.basename(inputPath, inputExt);
    const gltfOutputPath = path.join(outputPath, `${outputFileName}.gltf`);
    
    fs.writeFileSync(gltfOutputPath, JSON.stringify(gltfData, null, 2));
    
    if (verbose) {
      console.log(`Output written to: ${gltfOutputPath}`);
    }

    console.log(`✅ Simple processing complete for ${target} target`);
    return true;

  } catch (error) {
    console.error(`❌ Processing failed: ${error.message}`);
    if (verbose) {
      console.error(error.stack);
    }
    return false;
  }
}

function modifyForUnity(gltfData, verbose = false) {
  // Unity-specific modifications
  if (verbose) {
    console.log('Applying Unity-specific modifications...');
  }

  // Update materials for Unity's Standard Shader
  if (gltfData.materials) {
    gltfData.materials.forEach((material, index) => {
      if (verbose) {
        console.log(`Modifying material ${index} for Unity`);
      }
      
      // Unity expects metallic-roughness in a specific format
      if (material.pbrMetallicRoughness) {
        // Keep the material structure but ensure Unity compatibility
        material.extensions = material.extensions || {};
        material.extensions.KHR_materials_unlit = {};
      }
    });
  }

  return gltfData;
}

function modifyForRoblox(gltfData, verbose = false) {
  // Roblox-specific modifications
  if (verbose) {
    console.log('Applying Roblox-specific modifications...');
  }

  // Simplify materials for Roblox
  if (gltfData.materials) {
    gltfData.materials.forEach((material, index) => {
      if (verbose) {
        console.log(`Simplifying material ${index} for Roblox`);
      }
      
      // Roblox prefers simple materials
      if (material.pbrMetallicRoughness) {
        material.pbrMetallicRoughness.metallicFactor = 0.0;
        material.pbrMetallicRoughness.roughnessFactor = 1.0;
      }
    });
  }

  return gltfData;
}

// Run the processor
const success = processGLTF(options.input, options.output, options.target, options.verbose);
process.exit(success ? 0 : 1);
