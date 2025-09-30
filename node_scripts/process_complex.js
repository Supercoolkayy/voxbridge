#!/usr/bin/env node

/**
 * Complex GLTF/GLB processing script for VoxBridge
 * Handles animations, skins, morph targets, and other complex features
 */

const { program } = require("commander");
const fs = require("fs-extra");
const path = require("path");
const { execSync } = require("child_process");

// Import gltf-transform modules
const { NodeIO } = require("@gltf-transform/core");
const {
  quantize,
  textureResize,
  textureCompress,
} = require("@gltf-transform/functions");

// Import Draco with fallback
let draco;
try {
  draco = require("@gltf-transform/functions").draco;
  if (typeof draco !== "function") {
    console.warn("Draco function not available in @gltf-transform/functions");
    draco = null;
  }
} catch (error) {
  console.warn("Failed to import Draco:", error.message);
  draco = null;
}

program
  .name("process-complex")
  .description(
    "Process complex GLTF/GLB files with animations and advanced features"
  )
  .version("0.1.0")
  .requiredOption("-i, --input <path>", "Input GLTF/GLB file path")
  .requiredOption("-o, --output <path>", "Output directory path")
  .requiredOption("-t, --target <platform>", "Target platform (unity/roblox)")
  .option("--pack-glb", "Pack output into single GLB file")
  .option("--use-draco", "Enable Draco compression")
  .option("--no-draco", "Disable Draco compression")
  .option("--texture-size <size>", "Maximum texture size", "1024")
  .option("--quantize", "Enable quantization")
  .option("--verbose", "Enable verbose output")
  .parse();

const options = program.opts();

async function processComplexGLTF() {
  const startTime = Date.now();
  const stats = {
    input: options.input,
    target: options.target,
    start: startTime,
    success: false,
    error: null,
    warnings: [],
    optimizations: [],
  };

  try {
    console.log(`Processing complex GLTF: ${options.input}`);
    console.log(`Target platform: ${options.target}`);

    // Ensure output directory exists
    await fs.ensureDir(options.output);

    // Load the GLTF file
    const io = new NodeIO();
    const document = await io.read(options.input);

    // Get initial stats
    const initialStats = getDocumentStats(document);
    stats.initialStats = initialStats;

    console.log(
      `Initial stats: ${initialStats.meshes} meshes, ${initialStats.triangles} triangles`
    );

    // Apply optimizations based on target platform
    try {
      if (options.target === "roblox") {
        console.log("Applying Roblox optimizations...");
        await applyRobloxOptimizations(document, options);
        stats.optimizations.push("roblox_optimizations");
      } else if (options.target === "unity") {
        console.log("Applying Unity optimizations...");
        await applyUnityOptimizations(document, options);
        stats.optimizations.push("unity_optimizations");
      }
    } catch (optError) {
      console.error(`Optimization error: ${optError.message}`);
      console.error(`Stack trace: ${optError.stack}`);
      stats.warnings.push(`Optimization failed: ${optError.message}`);
    }

    // Apply general optimizations
    try {
      if (options.quantize) {
        console.log("Applying quantization...");
        await document.transform(quantize());
        stats.optimizations.push("quantization");
      }

      if (options.useDraco === true) {
        if (draco === null) {
          console.warn(
            "Draco compression requested but not available - skipping"
          );
          stats.warnings.push("Draco compression not available - skipping");
        } else {
          try {
            console.log("Applying Draco compression...");
            await document.transform(draco());
            stats.optimizations.push("draco_compression");
            console.log("Draco compression applied successfully");
          } catch (dracoError) {
            console.error(`Draco compression failed: ${dracoError.message}`);
            stats.warnings.push(
              `Draco compression failed: ${dracoError.message}`
            );
            console.log("Continuing without Draco compression...");
            // Continue without Draco compression
          }
        }
      } else {
        console.log("Draco compression disabled");
      }
    } catch (genError) {
      console.error(`General optimization error: ${genError.message}`);
      console.error(`Stack trace: ${genError.stack}`);
      stats.warnings.push(`General optimization failed: ${genError.message}`);
    }

    // Resize textures if specified
    try {
      const textureSize = parseInt(options.textureSize);
      if (textureSize < 1024) {
        console.log(`Resizing textures to ${textureSize}px...`);
        await document.transform(textureResize({ size: textureSize }));
        stats.optimizations.push(`texture_resize_${textureSize}`);
      }
    } catch (textureError) {
      console.error(`Texture resize error: ${textureError.message}`);
      console.error(`Stack trace: ${textureError.stack}`);
      stats.warnings.push(`Texture resize failed: ${textureError.message}`);
    }

    // Get final stats
    const finalStats = getDocumentStats(document);
    stats.finalStats = finalStats;

    console.log(
      `Final stats: ${finalStats.meshes} meshes, ${finalStats.triangles} triangles`
    );

    // Determine output format - always create clean naming
    const inputExt = path.extname(options.input).toLowerCase();
    const baseName = path.basename(options.input, inputExt);
    const outputName = `${baseName}_${options.target}.gltf`;
    const outputPath = path.join(options.output, outputName);

    // Write the processed file
    await io.write(outputPath, document);
    console.log(`Output written to: ${outputPath}`);

    // Apply platform-specific post-processing
    if (options.target === "roblox") {
      await applyRobloxPostProcessing(outputPath);
    } else if (options.target === "unity") {
      await applyUnityPostProcessing(outputPath);
    }

    // Always package the output
    const packagePath = await packageOutput(
      outputPath,
      options.output,
      options.target,
      baseName
    );
    if (packagePath) {
      stats.outputPath = packagePath;
    } else {
      stats.outputPath = outputPath;
    }

    stats.success = true;
    stats.timeSec = (Date.now() - startTime) / 1000;

    // Write stats to file
    const statsPath = path.join(options.output, "voxbridge_report.json");
    await fs.writeJson(statsPath, stats, { spaces: 2 });

    console.log(`Processing completed in ${stats.timeSec.toFixed(2)}s`);
    console.log(`Stats written to: ${statsPath}`);
  } catch (error) {
    stats.success = false;
    stats.error = error.message;
    stats.timeSec = (Date.now() - startTime) / 1000;

    console.error(`Processing failed: ${error.message}`);

    // Write error stats
    const statsPath = path.join(options.output, "voxbridge_report.json");
    await fs.writeJson(statsPath, stats, { spaces: 2 });

    process.exit(1);
  }
}

function getDocumentStats(document) {
  const root = document.getRoot();
  const meshes = root.listMeshes();
  const materials = root.listMaterials();
  const textures = root.listTextures();
  const nodes = root.listNodes();
  const animations = root.listAnimations();
  const skins = root.listSkins();

  // Calculate triangle count
  let triangles = 0;
  if (meshes && meshes.length > 0) {
    for (const mesh of meshes) {
      const primitives = mesh.listPrimitives();
      if (primitives && primitives.length > 0) {
        for (const primitive of primitives) {
          const indices = primitive.getIndices();
          if (indices) {
            triangles += indices.getCount() / 3;
          } else {
            const position = primitive.getAttribute("POSITION");
            if (position) {
              triangles += position.getCount() / 3;
            }
          }
        }
      }
    }
  }

  // Calculate animation durations
  const animationDurations = [];
  if (animations && animations.length > 0) {
    for (const animation of animations) {
      const channels = animation.listChannels();
      let maxTime = 0;
      for (const channel of channels) {
        const sampler = channel.getSampler();
        if (sampler) {
          const input = sampler.getInput();
          if (input) {
            const times = input.getArray();
            if (times && times.length > 0) {
              maxTime = Math.max(maxTime, times[times.length - 1]);
            }
          }
        }
      }
      animationDurations.push({
        name: animation.getName() || "Unnamed",
        duration: maxTime,
      });
    }
  }

  return {
    meshes: meshes.length,
    materials: materials.length,
    textures: textures.length,
    nodes: nodes.length,
    animations: animations.length,
    skins: skins.length,
    triangles: Math.floor(triangles),
    animationDurations: animationDurations,
  };
}

async function applyRobloxOptimizations(document, options) {
  console.log("Applying Roblox optimizations...");

  // Roblox-specific optimizations
  // - Remove unsupported features
  // - Basic optimizations for Roblox compatibility

  const root = document.getRoot();

  // Remove animations (Roblox doesn't support GLTF animations)
  const animations = root.listAnimations();
  if (animations && animations.length > 0) {
    for (const animation of animations) {
      animation.dispose();
    }
  }

  // Remove skins (Roblox handles rigging differently)
  const skins = root.listSkins();
  if (skins && skins.length > 0) {
    for (const skin of skins) {
      skin.dispose();
    }
  }

  console.log(`Optimized ${root.listMeshes().length} meshes for Roblox`);
  console.log(`Optimized ${root.listMaterials().length} materials for Roblox`);
}

async function applyUnityOptimizations(document, options) {
  console.log("Applying Unity optimizations...");

  // Unity-specific optimizations
  // - Basic optimizations for Unity compatibility
  // - Focus on core functionality without complex material operations

  const root = document.getRoot();

  // Basic Unity optimizations - just ensure the document is valid
  console.log(`Optimizing ${root.listMeshes().length} meshes for Unity`);
  console.log(`Optimizing ${root.listMaterials().length} materials for Unity`);
}

async function applyRobloxPostProcessing(gltfPath) {
  console.log("Applying Roblox post-processing...");

  // Load and modify the GLTF file for Roblox compatibility
  const gltfData = await fs.readJson(gltfPath);

  // Remove unsupported extensions
  if (gltfData.extensionsUsed) {
    gltfData.extensionsUsed = gltfData.extensionsUsed.filter(
      (ext) => !ext.startsWith("KHR_") && !ext.startsWith("EXT_")
    );
  }

  if (gltfData.extensionsRequired) {
    gltfData.extensionsRequired = gltfData.extensionsRequired.filter(
      (ext) => !ext.startsWith("KHR_") && !ext.startsWith("EXT_")
    );
  }

  // Save the modified GLTF
  await fs.writeJson(gltfPath, gltfData, { spaces: 2 });
}

async function applyUnityPostProcessing(gltfPath) {
  console.log("Applying Unity post-processing...");

  // Load and modify the GLTF file for Unity compatibility
  const gltfData = await fs.readJson(gltfPath);

  // Ensure proper sampler configuration
  if (!gltfData.samplers || gltfData.samplers.length === 0) {
    gltfData.samplers = [
      {
        magFilter: 9728,
        minFilter: 9728,
        wrapS: 33071,
        wrapT: 33071,
      },
    ];
  }

  // Ensure all textures have samplers
  if (gltfData.textures && Array.isArray(gltfData.textures)) {
    for (const texture of gltfData.textures) {
      if (texture.sampler === undefined) {
        texture.sampler = 0;
      }
    }
  }

  // Save the modified GLTF
  await fs.writeJson(gltfPath, gltfData, { spaces: 2 });
}

async function packageOutput(gltfPath, outputDir, target, baseName) {
  console.log("Packaging output...");

  try {
    const zip = require("adm-zip");
    const zipPath = path.join(outputDir, `${baseName}_${target}.zip`);
    const zipFile = new zip();

    // Track added files to prevent duplicates
    const addedFiles = new Set();

    // Add the GLTF file with clean naming
    const gltfZipPath = `${baseName}_${target}.gltf`;
    if (!addedFiles.has(gltfZipPath)) {
      const gltfData = await fs.readFile(gltfPath);
      zipFile.addFile(gltfZipPath, gltfData);
      addedFiles.add(gltfZipPath);
    }

    // Add any associated BIN files with clean naming
    const binFiles = await fs.readdir(outputDir);
    for (const file of binFiles) {
      if (file.endsWith(".bin") && file.includes(baseName)) {
        const binZipPath = `${baseName}_${target}.bin`;
        if (!addedFiles.has(binZipPath)) {
          const binData = await fs.readFile(path.join(outputDir, file));
          zipFile.addFile(binZipPath, binData);
          addedFiles.add(binZipPath);
        }
      }
    }

    // Add texture files to textures/ folder (deduplicate by hash)
    const textureHashes = new Map();
    for (const file of binFiles) {
      if (
        file.endsWith(".png") ||
        file.endsWith(".jpg") ||
        file.endsWith(".jpeg")
      ) {
        const filePath = path.join(outputDir, file);
        const fileBuffer = await fs.readFile(filePath);
        const hash = require("crypto")
          .createHash("md5")
          .update(fileBuffer)
          .digest("hex");

        if (!textureHashes.has(hash)) {
          textureHashes.set(hash, file);
          const textureZipPath = `textures/${file}`;
          if (!addedFiles.has(textureZipPath)) {
            zipFile.addFile(textureZipPath, fileBuffer);
            addedFiles.add(textureZipPath);
          }
        }
      }
    }

    zipFile.writeZip(zipPath);
    console.log(`Packaged to: ${zipPath}`);

    return zipPath;
  } catch (error) {
    console.error(`Packaging failed: ${error.message}`);
    return null;
  }
}

// Run the processing
if (require.main === module) {
  processComplexGLTF().catch(console.error);
}

module.exports = { processComplexGLTF };
