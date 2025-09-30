#!/usr/bin/env node

/**
 * GLTF validation script for VoxBridge
 * Validates GLTF/GLB files and generates validation reports
 */

const { program } = require("commander");
const fs = require("fs-extra");
const path = require("path");

program
  .name("validate")
  .description("Validate GLTF/GLB files and generate reports")
  .version("0.1.0")
  .requiredOption("-i, --input <path>", "Input GLTF/GLB file path")
  .option("-o, --output <path>", "Output validation report path")
  .option("--verbose", "Enable verbose output")
  .parse();

const options = program.opts();

async function validateGLTF() {
  try {
    console.log(`Validating GLTF: ${options.input}`);

    // Load the GLTF file
    const gltfData = await fs.readJson(options.input);

    // Perform validation
    const validationResult = await performValidation(gltfData, options.input);

    // Write validation report
    const outputPath =
      options.output ||
      path.join(path.dirname(options.input), "validation_report.json");
    await fs.writeJson(outputPath, validationResult, { spaces: 2 });

    console.log(`Validation completed: ${outputPath}`);
    console.log(`Status: ${validationResult.valid ? "VALID" : "INVALID"}`);
    console.log(
      `Errors: ${validationResult.errors.length}, Warnings: ${validationResult.warnings.length}`
    );

    if (!validationResult.valid) {
      process.exit(1);
    }
  } catch (error) {
    console.error(`Validation failed: ${error.message}`);
    process.exit(1);
  }
}

async function performValidation(gltfData, filePath) {
  const result = {
    file: filePath,
    valid: true,
    errors: [],
    warnings: [],
    stats: {},
    timestamp: new Date().toISOString(),
  };

  // Basic structure validation
  validateBasicStructure(gltfData, result);

  // Asset validation
  validateAsset(gltfData, result);

  // Scene validation
  validateScenes(gltfData, result);

  // Node validation
  validateNodes(gltfData, result);

  // Mesh validation
  validateMeshes(gltfData, result);

  // Material validation
  validateMaterials(gltfData, result);

  // Texture validation
  validateTextures(gltfData, result);

  // Animation validation
  validateAnimations(gltfData, result);

  // Buffer validation
  validateBuffers(gltfData, result);

  // Calculate statistics
  calculateStats(gltfData, result);

  // Determine overall validity
  result.valid = result.errors.length === 0;

  return result;
}

function validateBasicStructure(gltfData, result) {
  // Check required fields
  if (!gltfData.asset) {
    result.errors.push("Missing required asset field");
  }

  if (!gltfData.scene && (!gltfData.scenes || gltfData.scenes.length === 0)) {
    result.errors.push("Missing scenes");
  }

  // Check asset version
  if (gltfData.asset && gltfData.asset.version !== "2.0") {
    result.warnings.push(
      `Unsupported asset version: ${gltfData.asset.version}`
    );
  }
}

function validateAsset(gltfData, result) {
  if (!gltfData.asset) return;

  const asset = gltfData.asset;

  if (!asset.version) {
    result.errors.push("Asset missing version field");
  }

  if (asset.version && asset.version !== "2.0") {
    result.warnings.push(
      `Asset version ${asset.version} may not be fully supported`
    );
  }
}

function validateScenes(gltfData, result) {
  if (!gltfData.scenes) {
    result.errors.push("Missing scenes array");
    return;
  }

  if (gltfData.scenes.length === 0) {
    result.errors.push("Scenes array is empty");
    return;
  }

  // Validate scene references
  if (gltfData.scene !== undefined) {
    if (gltfData.scene >= gltfData.scenes.length) {
      result.errors.push(`Scene index ${gltfData.scene} is out of range`);
    }
  }

  // Validate each scene
  for (let i = 0; i < gltfData.scenes.length; i++) {
    const scene = gltfData.scenes[i];

    if (scene.nodes) {
      for (const nodeIndex of scene.nodes) {
        if (nodeIndex >= (gltfData.nodes ? gltfData.nodes.length : 0)) {
          result.errors.push(`Scene ${i} references invalid node ${nodeIndex}`);
        }
      }
    }
  }
}

function validateNodes(gltfData, result) {
  if (!gltfData.nodes) return;

  for (let i = 0; i < gltfData.nodes.length; i++) {
    const node = gltfData.nodes[i];

    // Validate mesh reference
    if (node.mesh !== undefined) {
      if (node.mesh >= (gltfData.meshes ? gltfData.meshes.length : 0)) {
        result.errors.push(`Node ${i} references invalid mesh ${node.mesh}`);
      }
    }

    // Validate children references
    if (node.children) {
      for (const childIndex of node.children) {
        if (childIndex >= gltfData.nodes.length) {
          result.errors.push(
            `Node ${i} references invalid child node ${childIndex}`
          );
        }
      }
    }

    // Validate skin reference
    if (node.skin !== undefined) {
      if (node.skin >= (gltfData.skins ? gltfData.skins.length : 0)) {
        result.errors.push(`Node ${i} references invalid skin ${node.skin}`);
      }
    }
  }
}

function validateMeshes(gltfData, result) {
  if (!gltfData.meshes) return;

  for (let i = 0; i < gltfData.meshes.length; i++) {
    const mesh = gltfData.meshes[i];

    if (!mesh.primitives || mesh.primitives.length === 0) {
      result.errors.push(`Mesh ${i} has no primitives`);
      continue;
    }

    for (let j = 0; j < mesh.primitives.length; j++) {
      const primitive = mesh.primitives[j];

      // Validate attributes
      if (!primitive.attributes || !primitive.attributes.POSITION) {
        result.errors.push(
          `Mesh ${i} primitive ${j} missing POSITION attribute`
        );
      }

      // Validate material reference
      if (primitive.material !== undefined) {
        if (
          primitive.material >=
          (gltfData.materials ? gltfData.materials.length : 0)
        ) {
          result.errors.push(
            `Mesh ${i} primitive ${j} references invalid material ${primitive.material}`
          );
        }
      }

      // Validate indices reference
      if (primitive.indices !== undefined) {
        if (
          primitive.indices >=
          (gltfData.accessors ? gltfData.accessors.length : 0)
        ) {
          result.errors.push(
            `Mesh ${i} primitive ${j} references invalid indices accessor ${primitive.indices}`
          );
        }
      }
    }
  }
}

function validateMaterials(gltfData, result) {
  if (!gltfData.materials) return;

  for (let i = 0; i < gltfData.materials.length; i++) {
    const material = gltfData.materials[i];

    // Validate texture references
    const textureFields = [
      "normalTexture",
      "occlusionTexture",
      "emissiveTexture",
    ];

    if (material.pbrMetallicRoughness) {
      textureFields.push("baseColorTexture", "metallicRoughnessTexture");
    }

    for (const field of textureFields) {
      const texture = material[field];
      if (texture && texture.index !== undefined) {
        if (
          texture.index >= (gltfData.textures ? gltfData.textures.length : 0)
        ) {
          result.errors.push(
            `Material ${i} ${field} references invalid texture ${texture.index}`
          );
        }
      }
    }
  }
}

function validateTextures(gltfData, result) {
  if (!gltfData.textures) return;

  for (let i = 0; i < gltfData.textures.length; i++) {
    const texture = gltfData.textures[i];

    // Validate source reference
    if (texture.source !== undefined) {
      if (texture.source >= (gltfData.images ? gltfData.images.length : 0)) {
        result.errors.push(
          `Texture ${i} references invalid image ${texture.source}`
        );
      }
    }

    // Validate sampler reference
    if (texture.sampler !== undefined) {
      if (
        texture.sampler >= (gltfData.samplers ? gltfData.samplers.length : 0)
      ) {
        result.errors.push(
          `Texture ${i} references invalid sampler ${texture.sampler}`
        );
      }
    }
  }
}

function validateAnimations(gltfData, result) {
  if (!gltfData.animations) return;

  for (let i = 0; i < gltfData.animations.length; i++) {
    const animation = gltfData.animations[i];

    if (!animation.channels || animation.channels.length === 0) {
      result.warnings.push(`Animation ${i} has no channels`);
      continue;
    }

    for (const channel of animation.channels) {
      // Validate sampler reference
      if (channel.sampler !== undefined) {
        if (
          channel.sampler >=
          (animation.samplers ? animation.samplers.length : 0)
        ) {
          result.errors.push(
            `Animation ${i} channel references invalid sampler ${channel.sampler}`
          );
        }
      }

      // Validate target node
      if (channel.target && channel.target.node !== undefined) {
        if (
          channel.target.node >= (gltfData.nodes ? gltfData.nodes.length : 0)
        ) {
          result.errors.push(
            `Animation ${i} channel targets invalid node ${channel.target.node}`
          );
        }
      }
    }
  }
}

function validateBuffers(gltfData, result) {
  if (!gltfData.buffers) return;

  for (let i = 0; i < gltfData.buffers.length; i++) {
    const buffer = gltfData.buffers[i];

    if (buffer.byteLength === undefined) {
      result.errors.push(`Buffer ${i} missing byteLength`);
    }

    if (
      buffer.uri &&
      !buffer.uri.startsWith("data:") &&
      !buffer.uri.startsWith("http")
    ) {
      // Check if buffer file exists
      const bufferPath = path.join(path.dirname(result.file), buffer.uri);
      if (!fs.existsSync(bufferPath)) {
        result.warnings.push(`Buffer ${i} file not found: ${buffer.uri}`);
      }
    }
  }
}

function calculateStats(gltfData, result) {
  result.stats = {
    scenes: gltfData.scenes ? gltfData.scenes.length : 0,
    nodes: gltfData.nodes ? gltfData.nodes.length : 0,
    meshes: gltfData.meshes ? gltfData.meshes.length : 0,
    materials: gltfData.materials ? gltfData.materials.length : 0,
    textures: gltfData.textures ? gltfData.textures.length : 0,
    images: gltfData.images ? gltfData.images.length : 0,
    animations: gltfData.animations ? gltfData.animations.length : 0,
    skins: gltfData.skins ? gltfData.skins.length : 0,
    cameras: gltfData.cameras ? gltfData.cameras.length : 0,
    lights:
      gltfData.extensions && gltfData.extensions.KHR_lights_punctual
        ? gltfData.extensions.KHR_lights_punctual.lights.length
        : 0,
    accessors: gltfData.accessors ? gltfData.accessors.length : 0,
    bufferViews: gltfData.bufferViews ? gltfData.bufferViews.length : 0,
    buffers: gltfData.buffers ? gltfData.buffers.length : 0,
  };

  // Calculate triangle count
  let triangles = 0;
  if (gltfData.meshes) {
    for (const mesh of gltfData.meshes) {
      if (mesh.primitives) {
        for (const primitive of mesh.primitives) {
          if (primitive.indices !== undefined && gltfData.accessors) {
            const accessor = gltfData.accessors[primitive.indices];
            if (accessor && accessor.count) {
              triangles += accessor.count / 3;
            }
          } else if (
            primitive.attributes &&
            primitive.attributes.POSITION !== undefined
          ) {
            const posAccessor =
              gltfData.accessors[primitive.attributes.POSITION];
            if (posAccessor && posAccessor.count) {
              triangles += posAccessor.count / 3;
            }
          }
        }
      }
    }
  }

  result.stats.triangles = Math.floor(triangles);
}

// Run validation
if (require.main === module) {
  validateGLTF().catch(console.error);
}

module.exports = { validateGLTF, performValidation };
