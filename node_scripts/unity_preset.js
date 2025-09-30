#!/usr/bin/env node

/**
 * Unity-specific GLTF preset and optimization
 * Ensures GLTF files are optimized for Unity's GLTF importer
 */

const { program } = require("commander");
const fs = require("fs-extra");
const path = require("path");

program
  .name("unity-preset")
  .description("Apply Unity-specific presets to GLTF files")
  .version("0.1.0")
  .requiredOption("-i, --input <path>", "Input GLTF file path")
  .requiredOption("-o, --output <path>", "Output GLTF file path")
  .option("--verbose", "Enable verbose output")
  .parse();

const options = program.opts();

async function applyUnityPreset() {
  try {
    console.log(`Applying Unity preset to: ${options.input}`);

    // Load the GLTF file
    const gltfData = await fs.readJson(options.input);

    // Apply Unity-specific modifications
    const modifiedGltf = await mapToUnity(gltfData);

    // Save the modified GLTF
    await fs.writeJson(options.output, modifiedGltf, { spaces: 2 });

    console.log(`Unity preset applied: ${options.output}`);
  } catch (error) {
    console.error(`Unity preset failed: ${error.message}`);
    process.exit(1);
  }
}

async function mapToUnity(gltfData) {
  const modified = JSON.parse(JSON.stringify(gltfData)); // Deep clone

  console.log("Applying Unity-specific optimizations...");

  // Ensure proper sampler configuration for Unity
  if (!modified.samplers || modified.samplers.length === 0) {
    console.log("Adding default samplers for Unity");
    modified.samplers = [
      {
        magFilter: 9728, // NEAREST
        minFilter: 9728, // NEAREST
        wrapS: 33071, // CLAMP_TO_EDGE
        wrapT: 33071, // CLAMP_TO_EDGE
      },
    ];
  }

  // Ensure all textures have samplers
  if (modified.textures) {
    console.log(`Configuring ${modified.textures.length} textures for Unity`);
    for (const texture of modified.textures) {
      if (texture.sampler === undefined) {
        texture.sampler = 0; // Use first sampler
      }
    }
  }

  // Optimize materials for Unity
  if (modified.materials) {
    console.log(`Optimizing ${modified.materials.length} materials for Unity`);
    for (const material of modified.materials) {
      // Ensure PBR material has proper defaults
      if (material.pbrMetallicRoughness) {
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

      // Ensure emissive factor is set if emissive texture exists
      if (material.emissiveTexture && !material.emissiveFactor) {
        material.emissiveFactor = [1, 1, 1];
      }
    }
  }

  // Ensure proper scene structure
  if (!modified.scene && modified.scenes && modified.scenes.length > 0) {
    modified.scene = 0; // Use first scene
  }

  // Validate node hierarchy
  if (modified.nodes) {
    console.log(`Validating ${modified.nodes.length} nodes for Unity`);
    for (let i = 0; i < modified.nodes.length; i++) {
      const node = modified.nodes[i];

      // Ensure mesh references are valid
      if (node.mesh !== undefined) {
        if (node.mesh >= (modified.meshes ? modified.meshes.length : 0)) {
          console.warn(`Node ${i} references invalid mesh ${node.mesh}`);
          delete node.mesh;
        }
      }

      // Ensure children references are valid
      if (node.children) {
        node.children = node.children.filter(
          (childIndex) => childIndex < modified.nodes.length
        );
      }
    }
  }

  // Ensure mesh primitives are valid
  if (modified.meshes) {
    console.log(`Validating ${modified.meshes.length} meshes for Unity`);
    for (const mesh of modified.meshes) {
      if (mesh.primitives) {
        for (const primitive of mesh.primitives) {
          // Ensure required attributes exist
          if (!primitive.attributes.POSITION) {
            console.warn("Mesh primitive missing POSITION attribute");
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

          // Ensure indices reference is valid
          if (primitive.indices !== undefined) {
            if (
              primitive.indices >=
              (modified.accessors ? modified.accessors.length : 0)
            ) {
              console.warn(
                "Mesh primitive references invalid indices accessor"
              );
              delete primitive.indices;
            }
          }
        }
      }
    }
  }

  // Ensure accessors are valid
  if (modified.accessors) {
    console.log(`Validating ${modified.accessors.length} accessors for Unity`);
    for (let i = 0; i < modified.accessors.length; i++) {
      const accessor = modified.accessors[i];

      // Ensure bufferView reference is valid
      if (accessor.bufferView !== undefined) {
        if (
          accessor.bufferView >=
          (modified.bufferViews ? modified.bufferViews.length : 0)
        ) {
          console.warn(
            `Accessor ${i} references invalid bufferView ${accessor.bufferView}`
          );
          delete accessor.bufferView;
        }
      }
    }
  }

  // Ensure bufferViews are valid
  if (modified.bufferViews) {
    console.log(
      `Validating ${modified.bufferViews.length} bufferViews for Unity`
    );
    for (let i = 0; i < modified.bufferViews.length; i++) {
      const bufferView = modified.bufferViews[i];

      // Ensure buffer reference is valid
      if (bufferView.buffer !== undefined) {
        if (
          bufferView.buffer >= (modified.buffers ? modified.buffers.length : 0)
        ) {
          console.warn(
            `BufferView ${i} references invalid buffer ${bufferView.buffer}`
          );
          delete bufferView.buffer;
        }
      }
    }
  }

  // Add Unity-specific metadata
  if (!modified.asset) {
    modified.asset = {
      version: "2.0",
      generator: "VoxBridge Unity Preset",
    };
  } else {
    modified.asset.generator = "VoxBridge Unity Preset";
  }

  // Ensure proper extensions for Unity
  if (!modified.extensionsUsed) {
    modified.extensionsUsed = [];
  }

  // Add Unity-compatible extensions
  const unityExtensions = [
    "KHR_materials_pbrSpecularGlossiness",
    "KHR_materials_unlit",
    "KHR_texture_transform",
  ];

  for (const ext of unityExtensions) {
    if (!modified.extensionsUsed.includes(ext)) {
      modified.extensionsUsed.push(ext);
    }
  }

  console.log("Unity preset applied successfully");
  return modified;
}

// Run the preset application
if (require.main === module) {
  applyUnityPreset().catch(console.error);
}

module.exports = { mapToUnity };
