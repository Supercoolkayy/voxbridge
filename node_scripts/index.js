#!/usr/bin/env node
/**
 * VoxBridge Node.js Binary Entry Point
 * Standalone binary for complex GLTF processing
 */

const { program } = require("commander");
const fs = require("fs-extra");
const path = require("path");

// Import our processing modules
const processComplex = require("./process_complex");
const validate = require("./validate");
const robloxMap = require("./roblox_map");
const unityPreset = require("./unity_preset");

program
  .name("voxbridge-node")
  .description("VoxBridge Node.js GLTF Processor")
  .version("2.0.0");

program
  .command("process")
  .description("Process complex GLTF/GLB files")
  .requiredOption("-i, --input <file>", "Input GLTF/GLB file")
  .requiredOption("-o, --output <dir>", "Output directory")
  .requiredOption("-t, --target <platform>", "Target platform (unity|roblox)")
  .option("--fast", "Fast mode (512px textures)")
  .option("--balanced", "Balanced mode (1024px textures)")
  .option("--full", "Full mode (2048px textures)")
  .option("--no-draco", "Disable Draco compression")
  .option("--texture-size <size>", "Custom texture size", "1024")
  .action(async (options) => {
    try {
      console.log("VoxBridge Node.js Processor v2.0.0");
      console.log(`Processing: ${options.input}`);
      console.log(`Target: ${options.target}`);
      console.log(`Output: ${options.output}`);

      const result = await processComplex.processFile(options);

      if (result.success) {
        console.log("✅ Processing completed successfully");
        console.log(`📦 Output: ${result.outputPath}`);
        process.exit(0);
      } else {
        console.error("❌ Processing failed:", result.error);
        process.exit(1);
      }
    } catch (error) {
      console.error("❌ Fatal error:", error.message);
      process.exit(1);
    }
  });

program
  .command("validate")
  .description("Validate GLTF/GLB files")
  .requiredOption("-i, --input <file>", "Input GLTF/GLB file")
  .action(async (options) => {
    try {
      console.log("Validating GLTF file...");
      const result = await validate.validateFile(options.input);

      if (result.valid) {
        console.log("✅ File is valid");
        console.log(`📊 Stats: ${JSON.stringify(result.stats, null, 2)}`);
        process.exit(0);
      } else {
        console.error("❌ File is invalid:", result.errors);
        process.exit(1);
      }
    } catch (error) {
      console.error("❌ Validation error:", error.message);
      process.exit(1);
    }
  });

program
  .command("roblox-map")
  .description("Generate Roblox-specific mappings")
  .requiredOption("-i, --input <file>", "Input GLTF/GLB file")
  .action(async (options) => {
    try {
      console.log("Generating Roblox mappings...");
      const result = await robloxMap.generateMappings(options.input);
      console.log("✅ Roblox mappings generated");
      console.log(`📄 Output: ${result.outputPath}`);
      process.exit(0);
    } catch (error) {
      console.error("❌ Mapping error:", error.message);
      process.exit(1);
    }
  });

program
  .command("unity-preset")
  .description("Generate Unity-specific presets")
  .requiredOption("-i, --input <file>", "Input GLTF/GLB file")
  .action(async (options) => {
    try {
      console.log("Generating Unity presets...");
      const result = await unityPreset.generatePresets(options.input);
      console.log("✅ Unity presets generated");
      console.log(`📄 Output: ${result.outputPath}`);
      process.exit(0);
    } catch (error) {
      console.error("❌ Preset error:", error.message);
      process.exit(1);
    }
  });

// Handle unknown commands
program.on("command:*", () => {
  console.error("Unknown command:", program.args.join(" "));
  program.help();
  process.exit(1);
});

// Parse command line arguments
program.parse(process.argv);

// Show help if no command provided
if (!process.argv.slice(2).length) {
  program.help();
}
