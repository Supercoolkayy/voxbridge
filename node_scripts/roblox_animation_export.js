#!/usr/bin/env node

/**
 * Roblox Animation Export Script
 * Converts GLTF animations to Roblox .anim format
 */

const fs = require("fs-extra");
const path = require("path");

/**
 * Export animations for Roblox
 */
async function exportRobloxAnimations(gltfPath, outputDir, baseName) {
  console.log("Exporting Roblox animations...");

  try {
    const gltfData = await fs.readJson(gltfPath);

    if (!gltfData.animations || gltfData.animations.length === 0) {
      console.log("No animations found in GLTF file");
      return;
    }

    console.log(`Found ${gltfData.animations.length} animations`);

    // Create animation export directory
    const animDir = path.join(outputDir, "animations");
    await fs.ensureDir(animDir);

    // Export each animation
    for (let i = 0; i < gltfData.animations.length; i++) {
      const animation = gltfData.animations[i];
      const animName = animation.name || `Animation${i + 1}`;

      // Create Roblox .anim file
      const animData = createRobloxAnimData(animation, gltfData);
      const animPath = path.join(animDir, `${baseName}_${animName}.anim`);

      await fs.writeFile(animPath, JSON.stringify(animData, null, 2));
      console.log(`Exported animation: ${animName}`);
    }

    // Create animation linking JSON
    const linkingData = createAnimationLinkingData(
      gltfData.animations,
      baseName
    );
    const linkingPath = path.join(outputDir, `${baseName}_animations.json`);
    await fs.writeFile(linkingPath, JSON.stringify(linkingData, null, 2));

    console.log("Roblox animations exported successfully");
  } catch (error) {
    console.error(`Roblox animation export failed: ${error.message}`);
  }
}

/**
 * Create Roblox .anim file data structure
 */
function createRobloxAnimData(animation, gltfData) {
  const animData = {
    0: {
      Type: "CFrame",
      Value: [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0],
    },
    1: {
      Type: "CFrame",
      Value: [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0],
    },
  };

  // Process animation channels
  if (animation.channels) {
    for (const channel of animation.channels) {
      const sampler = animation.samplers[channel.sampler];
      const target = channel.target;

      if (target && target.node !== undefined) {
        const nodeIndex = target.node;
        const node = gltfData.nodes[nodeIndex];

        if (node && node.name) {
          // Convert GLTF animation data to Roblox format
          const keyframes = convertToRobloxKeyframes(sampler, target.path);
          animData[node.name] = {
            Type: getRobloxPropertyType(target.path),
            Value: keyframes,
          };
        }
      }
    }
  }

  return animData;
}

/**
 * Convert GLTF sampler to Roblox keyframes
 */
function convertToRobloxKeyframes(sampler, path) {
  // This is a simplified conversion - in practice, you'd need more complex logic
  // to handle different animation types and interpolation methods

  const keyframes = [];

  if (sampler.input && sampler.output) {
    const times = gltfData.accessors[sampler.input];
    const values = gltfData.accessors[sampler.output];

    if (times && values) {
      // Convert to Roblox keyframe format
      for (let i = 0; i < Math.min(times.count, 10); i++) {
        // Limit to 10 keyframes for simplicity
        const time = times.array[i];
        const value = values.array.slice(i * 3, (i + 1) * 3); // Assuming 3D vectors

        keyframes.push({
          Time: time,
          Value: value,
        });
      }
    }
  }

  return keyframes;
}

/**
 * Get Roblox property type from GLTF path
 */
function getRobloxPropertyType(path) {
  switch (path) {
    case "translation":
      return "Vector3";
    case "rotation":
      return "CFrame";
    case "scale":
      return "Vector3";
    default:
      return "CFrame";
  }
}

/**
 * Create animation linking data for Roblox
 */
function createAnimationLinkingData(animations, baseName) {
  const linkingData = {
    modelName: baseName,
    animations: [],
  };

  for (let i = 0; i < animations.length; i++) {
    const animation = animations[i];
    const animName = animation.name || `Animation${i + 1}`;

    linkingData.animations.push({
      name: animName,
      fileName: `${baseName}_${animName}.anim`,
      duration: getAnimationDuration(animation),
      loop: true,
      priority: "Action",
    });
  }

  return linkingData;
}

/**
 * Get animation duration
 */
function getAnimationDuration(animation) {
  if (animation.channels && animation.channels.length > 0) {
    const sampler = animation.samplers[animation.channels[0].sampler];
    if (sampler.input) {
      const times = gltfData.accessors[sampler.input];
      if (times && times.array && times.array.length > 0) {
        return times.array[times.array.length - 1];
      }
    }
  }
  return 1.0; // Default duration
}

module.exports = { exportRobloxAnimations };
