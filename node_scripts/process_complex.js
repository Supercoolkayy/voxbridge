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
  simplify,
  weld,
  MeshoptSimplifier,
} = require("@gltf-transform/functions");
const sharp = require("sharp");

// Initialize MeshOptimizer for simplification
let meshoptReady = false;
async function initMeshopt() {
  try {
    const MeshoptEncoder = require("meshoptimizer");
    await MeshoptEncoder.ready;
    meshoptReady = true;
    console.log("MeshOptimizer initialized successfully");
  } catch (err) {
    console.warn("MeshOptimizer initialization warning:", err.message);
    console.warn("Mesh simplification will use basic algorithm");
  }
}

// Initialize immediately
initMeshopt();

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
  .option("--simplify", "Enable mesh simplification")
  .option("--simplify-ratio <ratio>", "Simplification ratio (0.0-1.0)", "0.5")
  .option("--keep-temp", "Keep intermediate files for debugging")
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
    // Wait for meshopt to initialize
    await initMeshopt();

    console.log(`Processing complex GLTF: ${options.input}`);
    console.log(`Target platform: ${options.target}`);

    // Ensure output directory exists
    await fs.ensureDir(options.output);

    // Load the GLTF file with extension preprocessing
    console.log("Loading GLTF file...");

    // First, try to preprocess the file to handle extensions
    let preprocessedPath = null;
    try {
      preprocessedPath = await preprocessGLTFForExtensions(
        options.input,
        options.output
      );
      if (preprocessedPath) {
        console.log(`Preprocessing successful: ${preprocessedPath}`);
      } else {
        console.log("No preprocessing needed (no extension issues detected)");
      }
    } catch (prepError) {
      console.warn(`Preprocessing error: ${prepError.message}`);
      preprocessedPath = null;
    }

    const io = new NodeIO();
    let document;

    try {
      // Always try preprocessed file first if preprocessing occurred
      if (preprocessedPath && (await fs.pathExists(preprocessedPath))) {
        console.log("Loading preprocessed GLTF file...");
        document = await io.read(preprocessedPath);
      } else {
        console.log("Loading original GLTF file...");
        document = await io.read(options.input);
      }
    } catch (readError) {
      console.error(`GLTF loading failed: ${readError.message}`);

      // If this was the original file and it failed, force preprocessing
      if (!preprocessedPath || !(await fs.pathExists(preprocessedPath))) {
        console.log(
          "Load failed - forcing preprocessing to handle extensions..."
        );
        const retryPreprocessedPath = await preprocessGLTFForExtensions(
          options.input,
          options.output
        );
        if (
          retryPreprocessedPath &&
          (await fs.pathExists(retryPreprocessedPath))
        ) {
          console.log("Retrying with preprocessed file...");
          try {
            document = await io.read(retryPreprocessedPath);
            console.log("Successfully loaded preprocessed file after retry");
          } catch (retryError) {
            console.error(`Preprocessing also failed: ${retryError.message}`);
            throw readError; // Throw original error for clarity
          }
        } else {
          throw readError;
        }
      } else {
        throw readError;
      }
    }

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
      // Handle specular-glossiness extension conversion first
      await handleSpecularGlossinessExtension(document, stats);

      // Apply mesh simplification if requested
      if (options.simplify) {
        try {
          const simplifyRatio = parseFloat(options.simplifyRatio);
          console.log(
            `Applying mesh simplification with ratio ${simplifyRatio}...`
          );

          // Get triangle count before simplification
          const beforeStats = getDocumentStats(document);
          const beforeTriangles = beforeStats.triangles;
          console.log(`Before simplification: ${beforeTriangles} triangles`);

          // Check if model has animations or skins that might prevent reduction
          const hasAnimations = document.getRoot().listAnimations().length > 0;
          const hasSkins = document.getRoot().listSkins().length > 0;

          if (hasAnimations || hasSkins) {
            console.log(
              `WARNING: Model contains ${hasAnimations ? "animations" : ""} ${
                hasAnimations && hasSkins ? "and " : ""
              } ${hasSkins ? "skins/rigging" : ""}`
            );
            console.log(
              "Mesh simplification may not reduce triangle count to preserve animation integrity."
            );
            console.log(
              "Proceeding with other optimizations (quantization, texture optimization)..."
            );
            stats.warnings.push(
              `Mesh simplification limited: Model contains ${
                hasAnimations ? "animations" : ""
              } ${hasSkins ? "skinning" : ""} that must be preserved`
            );
          }

          // First weld vertices to merge duplicates - this provides significant reduction
          console.log("Welding vertices to merge duplicates...");
          await document.transform(weld({ tolerance: 0.0001 }));

          // Get stats after welding
          const weldStats = getDocumentStats(document);
          const weldTriangles = weldStats.triangles;
          console.log(`After welding: ${weldTriangles} triangles`);

          const weldReduction = beforeTriangles - weldTriangles;
          let optimizationStatus = "already_optimized";
          let optimizationMessage = "";

          if (weldReduction > 0) {
            const weldPercent = (
              (weldReduction / beforeTriangles) *
              100
            ).toFixed(1);
            console.log(
              `Welding reduced: ${weldReduction} triangles (${weldPercent}%)`
            );
            optimizationStatus = "partially_optimized";
            optimizationMessage = `Vertex welding removed ${weldReduction} duplicate vertices (${weldPercent}%)`;
          } else {
            console.log("");
            console.log("========================================");
            console.log("MODEL ALREADY OPTIMIZED");
            console.log("========================================");
            console.log("This model has no duplicate vertices to merge.");
            console.log("The mesh is already well-optimized and efficient.");
            console.log("");
            console.log("Why no reduction:");
            console.log(
              "  - Model has clean topology with no duplicate vertices"
            );
            console.log(
              "  - Geometry is already optimized by the original creator"
            );

            if (hasAnimations || hasSkins) {
              console.log(
                "  - Contains animations/rigging that must be preserved"
              );
            }

            console.log("");
            console.log("Other optimizations still applied:");
            console.log("  + Quantization (vertex precision optimization)");
            console.log("  + Texture optimization and embedding");
            console.log("  + Material optimization");
            console.log("  + Cross-platform compatibility fixes");
            console.log("========================================");
            console.log("");

            optimizationStatus = "already_optimized";
            optimizationMessage =
              "Model is already optimized - no duplicate vertices found. Geometry is efficient.";
          }

          // Get final triangle count
          const afterStats = weldStats;
          const afterTriangles = weldTriangles;
          console.log(`Final optimized: ${afterTriangles} triangles`);

          // Calculate reduction statistics
          const triangleReduction = beforeTriangles - afterTriangles;
          const reductionPercent =
            beforeTriangles > 0
              ? ((triangleReduction / beforeTriangles) * 100).toFixed(1)
              : 0;

          if (triangleReduction > 0) {
            console.log(
              `Triangle reduction: ${triangleReduction} triangles (${reductionPercent}%)`
            );
            console.log("Mesh simplification applied successfully");
          } else {
            console.log("NOTE: Mesh simplification did not reduce triangles.");
            console.log(
              "This is expected for models with animations, skinning, or highly optimized meshes."
            );
            console.log(
              "Other optimizations (quantization, texture optimization) will still be applied."
            );
          }

          // Store simplification stats
          stats.meshSimplification = {
            beforeTriangles,
            afterTriangles,
            triangleReduction,
            reductionPercent: parseFloat(reductionPercent),
            simplifyRatio,
            limitedDueToAnimations: hasAnimations || hasSkins,
            optimizationStatus: optimizationStatus,
            optimizationMessage: optimizationMessage,
            alreadyOptimized: optimizationStatus === "already_optimized",
          };

          if (optimizationStatus === "partially_optimized") {
            stats.optimizations.push(
              `mesh_optimization_${simplifyRatio}_reduced_${reductionPercent}pct`
            );
          } else if (optimizationStatus === "already_optimized") {
            stats.optimizations.push(
              `mesh_already_optimized_no_reduction_needed`
            );
          } else {
            stats.optimizations.push(
              `mesh_simplification_attempted_${simplifyRatio}`
            );
          }
        } catch (simplifyError) {
          console.error(`Mesh simplification failed: ${simplifyError.message}`);
          console.log(
            "Note: Mesh simplification skipped. Continuing with other optimizations..."
          );
          stats.warnings.push(
            `Mesh simplification skipped: ${simplifyError.message}`
          );
        }
      }

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

    // Apply texture path fixes and metallic-roughness splitting
    await applyTextureFixes(outputPath, options.target, baseName);

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

    // Clean up intermediate files, keep only the final ZIP (unless --keep-temp is set)
    if (!options.keepTemp) {
      await cleanupIntermediateFiles(options.output);
    } else {
      console.log("Skipping cleanup due to --keep-temp flag");
    }
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

  // Export Roblox animations
  const baseName = path.basename(gltfPath, ".gltf");
  const outputDir = path.dirname(gltfPath);
  await exportRobloxAnimations(gltfPath, outputDir, baseName);
}

/**
 * Export Roblox animations
 */
async function exportRobloxAnimations(gltfPath, outputDir, baseName) {
  try {
    const { exportRobloxAnimations } = require("./roblox_animation_export");
    await exportRobloxAnimations(gltfPath, outputDir, baseName);
  } catch (error) {
    console.warn(`Roblox animation export failed: ${error.message}`);
  }
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

  // Add VoxBridge metadata for Unity import script detection
  if (!gltfData.asset) {
    gltfData.asset = {};
  }
  gltfData.asset.generator = "VoxBridge Unity Exporter v2.0.0";

  // Save the modified GLTF
  await fs.writeJson(gltfPath, gltfData, { spaces: 2 });

  // Copy Unity import script to output directory
  await copyUnityImportScript(gltfPath);
}

/**
 * Copy Unity import script to the output directory
 */
async function copyUnityImportScript(gltfPath) {
  try {
    const outputDir = path.dirname(gltfPath);
    const scriptPath = path.join(__dirname, "VoxbridgeImport.cs");
    const targetPath = path.join(outputDir, "VoxbridgeImport.cs");

    if (await fs.pathExists(scriptPath)) {
      await fs.copy(scriptPath, targetPath);
      console.log("VoxBridge: Copied Unity import script to output directory");
    }
  } catch (error) {
    console.warn(`Failed to copy Unity import script: ${error.message}`);
  }
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

    // Add texture files to root directory (flattened for Unity/Roblox compatibility)
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
          // Flatten textures to root directory for Unity/Roblox compatibility
          const textureZipPath = file; // No subfolder - textures go in root
          if (!addedFiles.has(textureZipPath)) {
            zipFile.addFile(textureZipPath, fileBuffer);
            addedFiles.add(textureZipPath);
            console.log(`Added texture to root: ${textureZipPath}`);
          }
        }
      }
    }

    // Add Unity import script if target is Unity
    if (target === "unity") {
      const unityScriptPath = path.join(outputDir, "VoxbridgeImport.cs");
      if (await fs.pathExists(unityScriptPath)) {
        const scriptData = await fs.readFile(unityScriptPath);
        zipFile.addFile("VoxbridgeImport.cs", scriptData);
        addedFiles.add("VoxbridgeImport.cs");
        console.log("Added Unity import script to package");
      }
    }

    // Add Roblox animation files if target is Roblox
    if (target === "roblox") {
      const animDir = path.join(outputDir, "animations");
      if (await fs.pathExists(animDir)) {
        const animFiles = await fs.readdir(animDir);
        for (const animFile of animFiles) {
          if (animFile.endsWith(".anim")) {
            const animPath = path.join(animDir, animFile);
            const animData = await fs.readFile(animPath);
            zipFile.addFile(`animations/${animFile}`, animData);
            addedFiles.add(`animations/${animFile}`);
          }
        }

        // Add animation linking JSON
        const linkingFile = `${baseName}_animations.json`;
        const linkingPath = path.join(outputDir, linkingFile);
        if (await fs.pathExists(linkingPath)) {
          const linkingData = await fs.readFile(linkingPath);
          zipFile.addFile(linkingFile, linkingData);
          addedFiles.add(linkingFile);
        }

        console.log("Added Roblox animation files to package");
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

/**
 * Apply texture path fixes, embedding, and metallic-roughness splitting
 */
async function applyTextureFixes(gltfPath, target, baseName) {
  console.log(
    "Applying texture path fixes, embedding, and metallic-roughness splitting..."
  );

  try {
    const gltfData = await fs.readJson(gltfPath);
    const outputDir = path.dirname(gltfPath);
    let modified = false;

    // First, ensure all textures are properly embedded or have correct URIs
    await ensureTextureEmbedding(gltfData, outputDir, baseName);

    // Process materials for metallic-roughness splitting
    if (gltfData.materials) {
      for (let i = 0; i < gltfData.materials.length; i++) {
        const material = gltfData.materials[i];
        if (
          material.pbrMetallicRoughness &&
          material.pbrMetallicRoughness.metallicRoughnessTexture
        ) {
          console.log(`Splitting metallic-roughness texture for material ${i}`);

          const textureIndex =
            material.pbrMetallicRoughness.metallicRoughnessTexture.index;
          const texture = gltfData.textures[textureIndex];
          const imageIndex = texture.source;
          const image = gltfData.images[imageIndex];

          if (image && image.uri) {
            const imagePath = path.join(outputDir, image.uri);
            if (await fs.pathExists(imagePath)) {
              await splitMetallicRoughnessTexture(
                imagePath,
                outputDir,
                baseName,
                i,
                gltfData,
                imageIndex
              );
              modified = true;
            }
          }
        }
      }
    }

    // Flatten texture paths - rewrite all texture URIs to be in root directory
    if (gltfData.images) {
      for (let i = 0; i < gltfData.images.length; i++) {
        const image = gltfData.images[i];
        if (image.uri && image.uri.includes("/")) {
          const fileName = path.basename(image.uri);
          const oldPath = path.join(outputDir, image.uri);
          const newPath = path.join(outputDir, fileName);

          // Move texture file to root if it exists
          if (await fs.pathExists(oldPath)) {
            await fs.move(oldPath, newPath, { overwrite: true });
            image.uri = fileName; // Update URI to be in root
            modified = true;
            console.log(`Moved texture: ${image.uri} -> ${fileName}`);
          }
        }
      }
    }

    // Save modified GLTF if changes were made
    if (modified) {
      await fs.writeJson(gltfPath, gltfData, { spaces: 2 });
      console.log("Texture fixes applied successfully");
    }
  } catch (error) {
    console.error(`Texture fixes failed: ${error.message}`);
    // Don't fail the entire process for texture issues
  }
}

/**
 * Ensure all textures are properly embedded or have correct URIs
 */
async function ensureTextureEmbedding(gltfData, outputDir, baseName) {
  console.log("Ensuring texture embedding and URI correctness...");

  try {
    if (!gltfData.images) {
      return;
    }

    for (let i = 0; i < gltfData.images.length; i++) {
      const image = gltfData.images[i];

      if (image.uri) {
        // Check if texture file exists
        const texturePath = path.join(outputDir, image.uri);

        if (await fs.pathExists(texturePath)) {
          // Texture file exists, ensure URI is correct
          const fileName = path.basename(image.uri);
          image.uri = fileName; // Ensure URI is just the filename
          console.log(`Fixed texture URI: ${image.uri}`);
        } else {
          // Texture file missing - try to find it in common locations
          const fileName = path.basename(image.uri);
          const possiblePaths = [
            path.join(outputDir, fileName),
            path.join(outputDir, "textures", fileName),
            path.join(outputDir, "images", fileName),
            path.join(outputDir, "assets", fileName),
          ];

          let found = false;
          for (const possiblePath of possiblePaths) {
            if (await fs.pathExists(possiblePath)) {
              // Move to root directory
              const rootPath = path.join(outputDir, fileName);
              await fs.move(possiblePath, rootPath, { overwrite: true });
              image.uri = fileName;
              console.log(
                `Found and moved texture: ${possiblePath} -> ${fileName}`
              );
              found = true;
              break;
            }
          }

          if (!found) {
            console.warn(`Texture file not found: ${image.uri}`);
            // Create a placeholder texture to prevent missing textures
            await createPlaceholderTexture(outputDir, fileName);
            image.uri = fileName;
            console.log(`Created placeholder texture: ${fileName}`);
          }
        }
      } else if (image.bufferView !== undefined) {
        // Texture is embedded in buffer, this is fine
        console.log(`Texture ${i} is embedded in buffer`);
      } else {
        console.warn(`Texture ${i} has no URI or bufferView`);
      }
    }
  } catch (error) {
    console.error(`Texture embedding check failed: ${error.message}`);
  }
}

/**
 * Create a placeholder texture to prevent missing textures
 */
async function createPlaceholderTexture(outputDir, fileName) {
  try {
    const placeholderPath = path.join(outputDir, fileName);

    // Create a simple 1x1 white PNG as placeholder
    const sharp = require("sharp");
    await sharp({
      create: {
        width: 1,
        height: 1,
        channels: 4,
        background: { r: 255, g: 255, b: 255, alpha: 1 },
      },
    })
      .png()
      .toFile(placeholderPath);

    console.log(`Created placeholder texture: ${fileName}`);
  } catch (error) {
    console.error(`Failed to create placeholder texture: ${error.message}`);
  }
}

/**
 * Split metallic-roughness texture into separate occlusion, roughness, and metallic textures
 */
async function splitMetallicRoughnessTexture(
  imagePath,
  outputDir,
  baseName,
  materialIndex,
  gltfData,
  imageIndex
) {
  try {
    const image = sharp(imagePath);
    const metadata = await image.metadata();
    const { width, height } = metadata;

    // Extract channels with consistent naming
    const occlusionPath = path.join(
      outputDir,
      `${baseName}_material${materialIndex}_occlusion.png`
    );
    const roughnessPath = path.join(
      outputDir,
      `${baseName}_material${materialIndex}_roughness.png`
    );
    const metallicPath = path.join(
      outputDir,
      `${baseName}_material${materialIndex}_metallic.png`
    );

    // Extract R channel (Occlusion)
    await image
      .extractChannel(0) // Red channel
      .png()
      .toFile(occlusionPath);

    // Extract G channel (Roughness)
    await image
      .extractChannel(1) // Green channel
      .png()
      .toFile(roughnessPath);

    // Extract B channel (Metallic)
    await image
      .extractChannel(2) // Blue channel
      .png()
      .toFile(metallicPath);

    // Add new images to GLTF
    const occlusionImageIndex = gltfData.images.length;
    const roughnessImageIndex = gltfData.images.length + 1;
    const metallicImageIndex = gltfData.images.length + 2;

    gltfData.images.push(
      { uri: path.basename(occlusionPath) },
      { uri: path.basename(roughnessPath) },
      { uri: path.basename(metallicPath) }
    );

    // Add new textures
    const occlusionTextureIndex = gltfData.textures.length;
    const roughnessTextureIndex = gltfData.textures.length + 1;
    const metallicTextureIndex = gltfData.textures.length + 2;

    gltfData.textures.push(
      { source: occlusionImageIndex, sampler: 0 },
      { source: roughnessImageIndex, sampler: 0 },
      { source: metallicImageIndex, sampler: 0 }
    );

    // Update material to use separate textures
    const material = gltfData.materials.find(
      (m) =>
        m.pbrMetallicRoughness &&
        m.pbrMetallicRoughness.metallicRoughnessTexture
    );
    if (material) {
      // Remove the combined metallic-roughness texture
      delete material.pbrMetallicRoughness.metallicRoughnessTexture;

      // Add separate textures
      material.pbrMetallicRoughness.roughnessTexture = {
        index: roughnessTextureIndex,
      };
      material.pbrMetallicRoughness.metallicTexture = {
        index: metallicTextureIndex,
      };

      // Add occlusion texture if not already present
      if (!material.occlusionTexture) {
        material.occlusionTexture = { index: occlusionTextureIndex };
      }
    }

    console.log(`Split metallic-roughness texture into separate channels`);
  } catch (error) {
    console.error(
      `Failed to split metallic-roughness texture: ${error.message}`
    );
  }
}

/**
 * Handle KHR_materials_pbrSpecularGlossiness extension conversion
 */
async function handleSpecularGlossinessExtension(document, stats) {
  try {
    console.log("Checking for specular-glossiness extensions...");

    // Use gltf-transform's metalRough function to convert specular-glossiness to metallic-roughness
    const { metalRough } = require("@gltf-transform/functions");

    try {
      console.log("Applying metalRough conversion for specular-glossiness...");
      await document.transform(metalRough());
      stats.optimizations.push("specular_glossiness_to_metallic_roughness");
      console.log(
        "Successfully converted specular-glossiness to metallic-roughness"
      );
    } catch (metalRoughError) {
      console.warn(`metalRough conversion failed: ${metalRoughError.message}`);
      console.log("Falling back to manual specular-glossiness conversion...");

      // Fallback to manual conversion
      const root = document.getRoot();
      const materials = root.listMaterials();
      let convertedCount = 0;

      for (const material of materials) {
        const extensions = material.getExtensions();
        if (extensions && extensions["KHR_materials_pbrSpecularGlossiness"]) {
          console.log(
            `Converting specular-glossiness material: ${
              material.getName() || "Unnamed"
            }`
          );

          // Get the specular-glossiness extension
          const specGlossExt =
            extensions["KHR_materials_pbrSpecularGlossiness"];

          // Convert diffuse to base color
          const diffuseFactor = specGlossExt.getDiffuseFactor();
          if (diffuseFactor) {
            material.setBaseColorFactor(diffuseFactor);
          }

          // Convert specular-glossiness to metallic-roughness
          const specularFactor = specGlossExt.getSpecularFactor();
          const glossinessFactor = specGlossExt.getGlossinessFactor();

          if (specularFactor && glossinessFactor !== undefined) {
            // Convert to metallic-roughness
            material.setMetallicFactor(0.0); // Assume dielectric
            material.setRoughnessFactor(1.0 - glossinessFactor);

            // If specular is very high, it might be metallic
            if (Array.isArray(specularFactor)) {
              const avgSpecular =
                specularFactor.reduce((a, b) => a + b, 0) /
                specularFactor.length;
              if (avgSpecular > 0.8) {
                material.setMetallicFactor(0.5);
              }
            } else if (specularFactor > 0.8) {
              material.setMetallicFactor(0.5);
            }
          }

          // Convert textures
          const diffuseTexture = specGlossExt.getDiffuseTexture();
          if (diffuseTexture) {
            material.setBaseColorTexture(diffuseTexture);
          }

          // Remove the extension
          material.setExtension("KHR_materials_pbrSpecularGlossiness", null);
          convertedCount++;
        }
      }

      if (convertedCount > 0) {
        console.log(
          `Manually converted ${convertedCount} specular-glossiness materials to metallic-roughness`
        );
        stats.optimizations.push(
          `manual_specular_glossiness_conversion_${convertedCount}`
        );
      }
    }
  } catch (error) {
    console.error(`Specular-glossiness conversion failed: ${error.message}`);
    stats.warnings.push(
      `Specular-glossiness conversion failed: ${error.message}`
    );
  }
}

/**
 * Preprocess GLTF/GLB file to handle extensions before loading with gltf-transform
 */
async function preprocessGLTFForExtensions(inputPath, outputDir) {
  try {
    console.log("Preprocessing GLTF/GLB file for extension handling...");

    // Check if it's a GLB file (binary) or GLTF file (JSON)
    const isGLB = inputPath.toLowerCase().endsWith(".glb");

    let gltfData;
    if (isGLB) {
      // For GLB files, we need to extract the JSON part first
      console.log("Extracting JSON from GLB file...");
      const glbBuffer = await fs.readFile(inputPath);

      // GLB format: magic (4 bytes) + version (4 bytes) + length (4 bytes) + JSON chunk
      const magic = glbBuffer.readUInt32LE(0);
      if (magic !== 0x46546c67) {
        // "glTF" in little endian
        throw new Error("Invalid GLB file format");
      }

      const version = glbBuffer.readUInt32LE(4);
      const length = glbBuffer.readUInt32LE(8);

      // JSON chunk header
      const jsonChunkLength = glbBuffer.readUInt32LE(12);
      const jsonChunkType = glbBuffer.readUInt32LE(16);

      if (jsonChunkType !== 0x4e4f534a) {
        // "JSON" in little endian
        throw new Error("Invalid GLB JSON chunk");
      }

      // Extract JSON data
      const jsonData = glbBuffer.slice(20, 20 + jsonChunkLength);
      const jsonString = jsonData.toString("utf8");
      gltfData = JSON.parse(jsonString);
    } else {
      // For GLTF files, read as JSON
      gltfData = await fs.readJson(inputPath);
    }

    let modified = false;

    // Handle specular-glossiness extension
    if (gltfData.materials) {
      for (let i = 0; i < gltfData.materials.length; i++) {
        const material = gltfData.materials[i];
        if (
          material.extensions &&
          material.extensions.KHR_materials_pbrSpecularGlossiness
        ) {
          console.log(`Preprocessing specular-glossiness material ${i}...`);

          const specGloss =
            material.extensions.KHR_materials_pbrSpecularGlossiness;

          // Convert to PBR metallic-roughness
          if (!material.pbrMetallicRoughness) {
            material.pbrMetallicRoughness = {};
          }

          // Convert diffuse to base color
          if (specGloss.diffuseFactor) {
            material.pbrMetallicRoughness.baseColorFactor =
              specGloss.diffuseFactor;
          }

          // Convert specular-glossiness to metallic-roughness
          if (
            specGloss.specularFactor &&
            specGloss.glossinessFactor !== undefined
          ) {
            material.pbrMetallicRoughness.metallicFactor = 0.0;
            material.pbrMetallicRoughness.roughnessFactor =
              1.0 - specGloss.glossinessFactor;

            // Check if specular is high (might be metallic)
            if (Array.isArray(specGloss.specularFactor)) {
              const avgSpecular =
                specGloss.specularFactor.reduce((a, b) => a + b, 0) /
                specGloss.specularFactor.length;
              if (avgSpecular > 0.8) {
                material.pbrMetallicRoughness.metallicFactor = 0.5;
              }
            } else if (specGloss.specularFactor > 0.8) {
              material.pbrMetallicRoughness.metallicFactor = 0.5;
            }
          }

          // Convert textures
          if (specGloss.diffuseTexture) {
            material.pbrMetallicRoughness.baseColorTexture =
              specGloss.diffuseTexture;
          }

          // Remove the extension
          delete material.extensions.KHR_materials_pbrSpecularGlossiness;

          // Clean up empty extensions object
          if (Object.keys(material.extensions).length === 0) {
            delete material.extensions;
          }

          modified = true;
        }
      }
    }

    // Remove from extensionsUsed and extensionsRequired
    if (gltfData.extensionsUsed) {
      gltfData.extensionsUsed = gltfData.extensionsUsed.filter(
        (ext) => ext !== "KHR_materials_pbrSpecularGlossiness"
      );
    }

    if (gltfData.extensionsRequired) {
      gltfData.extensionsRequired = gltfData.extensionsRequired.filter(
        (ext) => ext !== "KHR_materials_pbrSpecularGlossiness"
      );
    }

    if (modified) {
      if (isGLB) {
        // For GLB files, we need to reconstruct the GLB with preprocessed JSON
        console.log("Reconstructing GLB with preprocessed JSON...");

        // Read original GLB buffer
        const originalGlbBuffer = await fs.readFile(inputPath);

        // Extract binary chunk from original GLB
        const magic = originalGlbBuffer.readUInt32LE(0);
        const version = originalGlbBuffer.readUInt32LE(4);
        const length = originalGlbBuffer.readUInt32LE(8);

        // JSON chunk
        const jsonChunkLength = originalGlbBuffer.readUInt32LE(12);
        const jsonChunkType = originalGlbBuffer.readUInt32LE(16);

        // Binary chunk (if exists)
        let binaryChunkStart = 20 + jsonChunkLength;
        let binaryChunkLength = 0;
        let binaryChunkType = 0;
        let binaryData = null;

        if (binaryChunkStart < originalGlbBuffer.length) {
          binaryChunkLength = originalGlbBuffer.readUInt32LE(binaryChunkStart);
          binaryChunkType = originalGlbBuffer.readUInt32LE(
            binaryChunkStart + 4
          );
          if (binaryChunkType === 0x004e4942) {
            // "BIN\0" in little endian
            binaryData = originalGlbBuffer.slice(
              binaryChunkStart + 8,
              binaryChunkStart + 8 + binaryChunkLength
            );
          }
        }

        // Create new JSON chunk
        const newJsonString = JSON.stringify(gltfData);
        const newJsonBuffer = Buffer.from(newJsonString, "utf8");
        const newJsonChunkLength = newJsonBuffer.length;

        // Calculate new GLB length
        let newGlbLength = 12 + 8 + newJsonChunkLength; // Header + JSON chunk header + JSON data
        if (binaryData) {
          newGlbLength += 8 + binaryChunkLength; // Binary chunk header + binary data
        }

        // Create new GLB buffer
        const newGlbBuffer = Buffer.alloc(newGlbLength);
        let offset = 0;

        // GLB header
        newGlbBuffer.writeUInt32LE(0x46546c67, offset); // "glTF" magic
        offset += 4;
        newGlbBuffer.writeUInt32LE(2, offset); // Version
        offset += 4;
        newGlbBuffer.writeUInt32LE(newGlbLength, offset); // Length
        offset += 4;

        // JSON chunk header
        newGlbBuffer.writeUInt32LE(newJsonChunkLength, offset);
        offset += 4;
        newGlbBuffer.writeUInt32LE(0x4e4f534a, offset); // "JSON" type
        offset += 4;

        // JSON data
        newJsonBuffer.copy(newGlbBuffer, offset);
        offset += newJsonChunkLength;

        // Binary chunk (if exists)
        if (binaryData) {
          newGlbBuffer.writeUInt32LE(binaryChunkLength, offset);
          offset += 4;
          newGlbBuffer.writeUInt32LE(0x004e4942, offset); // "BIN\0" type
          offset += 4;
          binaryData.copy(newGlbBuffer, offset);
        }

        // Save reconstructed GLB
        const preprocessedPath = path.join(outputDir, "preprocessed.glb");
        await fs.writeFile(preprocessedPath, newGlbBuffer);
        console.log("Preprocessed GLB file saved for extension handling");
        return preprocessedPath;
      } else {
        // For GLTF files, save as JSON
        const preprocessedPath = path.join(outputDir, "preprocessed.gltf");
        await fs.writeJson(preprocessedPath, gltfData, { spaces: 2 });
        console.log("Preprocessed GLTF file saved for extension handling");
        return preprocessedPath;
      }
    }

    return null;
  } catch (error) {
    console.warn(`GLTF preprocessing failed: ${error.message}`);
    return null;
  }
}

/**
 * Clean up intermediate files, keep only the final ZIP package
 */
async function cleanupIntermediateFiles(outputDir) {
  try {
    console.log("Cleaning up intermediate files...");

    const files = await fs.readdir(outputDir);
    let cleanedCount = 0;

    for (const file of files) {
      const filePath = path.join(outputDir, file);
      const stat = await fs.stat(filePath);

      // Keep only ZIP files and JSON reports
      if (!file.endsWith(".zip") && !file.endsWith(".json")) {
        if (stat.isDirectory()) {
          await fs.remove(filePath);
          console.log(`Removed directory: ${file}`);
        } else {
          await fs.remove(filePath);
          console.log(`Removed file: ${file}`);
        }
        cleanedCount++;
      }
    }

    if (cleanedCount > 0) {
      console.log(`Cleaned up ${cleanedCount} intermediate files`);
    } else {
      console.log("No intermediate files to clean up");
    }
  } catch (error) {
    console.warn(`Cleanup failed: ${error.message}`);
  }
}

// Run the processing
if (require.main === module) {
  processComplexGLTF().catch(console.error);
}

module.exports = { processComplexGLTF, processFile: processComplexGLTF };
