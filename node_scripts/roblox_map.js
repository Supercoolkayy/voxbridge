#!/usr/bin/env node

/**
 * Roblox-specific GLTF mapping and optimization
 * Converts GLTF files to be compatible with Roblox's limitations
 */

const { program } = require("commander");
const fs = require("fs-extra");
const path = require("path");

program
  .name("roblox-map")
  .description("Apply Roblox-specific mappings to GLTF files")
  .version("0.1.0")
  .requiredOption("-i, --input <path>", "Input GLTF file path")
  .requiredOption("-o, --output <path>", "Output GLTF file path")
  .option("--verbose", "Enable verbose output")
  .parse();

const options = program.opts();

async function applyRobloxMapping() {
  try {
    console.log(`Applying Roblox mapping to: ${options.input}`);

    // Load the GLTF file
    const gltfData = await fs.readJson(options.input);

    // Apply Roblox-specific modifications
    const modifiedGltf = await mapToRoblox(gltfData);

    // Save the modified GLTF
    await fs.writeJson(options.output, modifiedGltf, { spaces: 2 });

    console.log(`Roblox mapping completed: ${options.output}`);
  } catch (error) {
    console.error(`Roblox mapping failed: ${error.message}`);
    process.exit(1);
  }
}

async function mapToRoblox(gltfData) {
  const modified = JSON.parse(JSON.stringify(gltfData)); // Deep clone

  // Remove unsupported features for Roblox
  console.log("Removing unsupported Roblox features...");

  // Remove animations (Roblox doesn't support GLTF animations)
  if (modified.animations) {
    console.log(`Removing ${modified.animations.length} animations`);
    delete modified.animations;
  }

  // Remove skins (Roblox handles rigging differently)
  if (modified.skins) {
    console.log(`Removing ${modified.skins.length} skins`);
    delete modified.skins;
  }

  // Remove cameras
  if (modified.cameras) {
    console.log(`Removing ${modified.cameras.length} cameras`);
    delete modified.cameras;
  }

  // Remove lights
  if (modified.extensions && modified.extensions.KHR_lights_punctual) {
    console.log("Removing lights");
    delete modified.extensions.KHR_lights_punctual;
  }

  // Simplify materials for Roblox compatibility
  if (modified.materials) {
    console.log(`Simplifying ${modified.materials.length} materials`);
    for (const material of modified.materials) {
      // Keep only basic PBR properties
      if (material.pbrMetallicRoughness) {
        // Remove complex textures
        delete material.pbrMetallicRoughness.baseColorTexture;
        delete material.pbrMetallicRoughness.metallicRoughnessTexture;

        // Set default values
        if (!material.pbrMetallicRoughness.baseColorFactor) {
          material.pbrMetallicRoughness.baseColorFactor = [1, 1, 1, 1];
        }
        if (material.pbrMetallicRoughness.metallicFactor === undefined) {
          material.pbrMetallicRoughness.metallicFactor = 0;
        }
        if (material.pbrMetallicRoughness.roughnessFactor === undefined) {
          material.pbrMetallicRoughness.roughnessFactor = 0.5;
        }
      }

      // Remove other textures
      delete material.normalTexture;
      delete material.occlusionTexture;
      delete material.emissiveTexture;
      delete material.emissiveFactor;

      // Remove extensions
      delete material.extensions;
    }
  }

  // Remove unsupported extensions
  if (modified.extensionsUsed) {
    const supportedExtensions = [
      "KHR_materials_pbrSpecularGlossiness",
      "KHR_materials_unlit",
    ];

    modified.extensionsUsed = modified.extensionsUsed.filter((ext) =>
      supportedExtensions.includes(ext)
    );

    if (modified.extensionsUsed.length === 0) {
      delete modified.extensionsUsed;
    }
  }

  if (modified.extensionsRequired) {
    const supportedExtensions = [
      "KHR_materials_pbrSpecularGlossiness",
      "KHR_materials_unlit",
    ];

    modified.extensionsRequired = modified.extensionsRequired.filter((ext) =>
      supportedExtensions.includes(ext)
    );

    if (modified.extensionsRequired.length === 0) {
      delete modified.extensionsRequired;
    }
  }

  // Remove extensions object if empty
  if (modified.extensions && Object.keys(modified.extensions).length === 0) {
    delete modified.extensions;
  }

  // Optimize for Roblox's mesh requirements
  if (modified.meshes) {
    console.log(`Optimizing ${modified.meshes.length} meshes for Roblox`);
    for (const mesh of modified.meshes) {
      // Ensure each primitive has required attributes
      if (mesh.primitives) {
        for (const primitive of mesh.primitives) {
          // Ensure POSITION attribute exists
          if (!primitive.attributes.POSITION) {
            console.warn("Mesh primitive missing POSITION attribute");
          }

          // Remove morph targets (not supported in Roblox)
          if (primitive.targets) {
            delete primitive.targets;
          }

          // Ensure material index is valid
          if (primitive.material !== undefined) {
            if (
              primitive.material >=
              (modified.materials ? modified.materials.length : 0)
            ) {
              primitive.material = 0; // Default to first material
            }
          }
        }
      }
    }
  }

  // Ensure scene structure is valid
  if (!modified.scene && modified.scenes && modified.scenes.length > 0) {
    modified.scene = 0; // Use first scene
  }

  // Remove empty scenes
  if (modified.scenes) {
    modified.scenes = modified.scenes.filter(
      (scene) => scene.nodes && scene.nodes.length > 0
    );
  }

  // Ensure nodes reference valid meshes
  if (modified.nodes) {
    console.log(`Validating ${modified.nodes.length} nodes`);
    for (const node of modified.nodes) {
      if (node.mesh !== undefined) {
        if (node.mesh >= (modified.meshes ? modified.meshes.length : 0)) {
          console.warn(`Node references invalid mesh ${node.mesh}`);
          delete node.mesh;
        }
      }
    }
  }

  console.log("Roblox mapping completed successfully");
  return modified;
}

// Run the mapping
if (require.main === module) {
  applyRobloxMapping().catch(console.error);
}

module.exports = { mapToRoblox };
