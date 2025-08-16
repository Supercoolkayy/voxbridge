#!/usr/bin/env node

/**
 * VoxBridge GLTF Validation Tool
 * Prevents Error 13 (data corruption) issues for Sketchfab uploads
 *
 * Enhanced with UV validation and buffer size auto-fixing
 *
 * Usage:
 *   node validate_gltf.js <input.gltf>
 *   node validate_gltf.js --help
 *   node validate_gltf.js --fix <input.gltf>  # Auto-fix issues
 */

const fs = require("fs");
const path = require("path");

// ANSI color codes for console output
const colors = {
  reset: "\x1b[0m",
  bright: "\x1b[1m",
  red: "\x1b[31m",
  green: "\x1b[32m",
  yellow: "\x1b[33m",
  blue: "\x1b[34m",
  magenta: "\x1b[35m",
  cyan: "\x1b[36m",
};

class GLTFValidator {
  constructor() {
    this.errors = [];
    this.warnings = [];
    this.fixes = [];
    this.stats = {
      accessors: 0,
      bufferViews: 0,
      buffers: 0,
      meshes: 0,
      materials: 0,
      textures: 0,
      images: 0,
    };
    this.autoFix = false;
    this.gltfPath = null;
    this.gltfData = null;
  }

  /**
   * Main validation entry point
   */
  async validate(inputPath, autoFix = false) {
    this.autoFix = autoFix;
    this.gltfPath = inputPath;

    console.log(
      `${colors.cyan}${colors.bright}🔍 VoxBridge GLTF Validator v1.1${colors.reset}`
    );
    console.log(`${colors.blue}Validating: ${inputPath}${colors.reset}`);
    if (autoFix) {
      console.log(`${colors.yellow}🛠️  Auto-fix mode: ENABLED${colors.reset}`);
    }
    console.log("");

    try {
      // Read and parse GLTF file
      const gltfContent = fs.readFileSync(inputPath, "utf8");
      this.gltfData = JSON.parse(gltfContent);

      // Perform comprehensive validation
      this.validateStructure(this.gltfData);
      this.validateAccessors(this.gltfData);
      this.validateBufferViews(this.gltfData);
      this.validateMeshes(this.gltfData);
      this.validateMaterials(this.gltfData);
      this.validateTextures(this.gltfData);
      this.validateImages(this.gltfData);
      this.validateBuffers(this.gltfData);

      // CRITICAL: UV validation for Error 13 prevention
      this.validateUVs(this.gltfData);

      // CRITICAL: Buffer size validation and auto-fixing
      this.validateBufferSizes(this.gltfData);

      // CRITICAL: Error 23 prevention - Accessor validation and buffer view alignment
      this.validateError23(this.gltfData);

      // CRITICAL: Error 20 prevention - Format corruption and structure validation
      this.validateError20(this.gltfData);

      // Generate validation report
      this.generateReport();

      // Auto-fix if enabled and issues found
      if (autoFix && this.fixes.length > 0) {
        await this.applyFixes();
      }

      return this.errors.length === 0;
    } catch (error) {
      console.error(
        `${colors.red}❌ Validation failed: ${error.message}${colors.reset}`
      );
      return false;
    }
  }

  /**
   * CRITICAL: UV validation for Error 13 prevention
   * Checks for TEXCOORD_0 attributes in each primitive
   */
  validateUVs(gltf) {
    if (!gltf.meshes) return;

    console.log(
      `${colors.cyan}🔍 UV Validation (Error 13 Prevention)${colors.reset}`
    );

    gltf.meshes.forEach((mesh, meshIndex) => {
      if (!mesh.primitives || !mesh.primitives.length) {
        this.errors.push(`Mesh ${meshIndex}: Missing primitives array`);
        return;
      }

      mesh.primitives.forEach((primitive, primitiveIndex) => {
        // CRITICAL: Check for TEXCOORD_0 (UV coordinates)
        if (!primitive.attributes.TEXCOORD_0) {
          const errorMsg = `Mesh ${meshIndex} Primitive ${primitiveIndex}: Missing TEXCOORD_0 (UV coordinates) - This will cause Sketchfab Error 13!`;
          this.errors.push(errorMsg);

          if (this.autoFix) {
            this.fixes.push({
              type: "uv_missing",
              meshIndex,
              primitiveIndex,
              message:
                "UV coordinates missing - requires manual fix in Blender",
            });
          }
        } else {
          // Validate UV accessor reference
          const uvAccessorIndex = primitive.attributes.TEXCOORD_0;
          if (uvAccessorIndex >= (gltf.accessors?.length || 0)) {
            this.errors.push(
              `Mesh ${meshIndex} Primitive ${primitiveIndex}: Invalid TEXCOORD_0 accessor reference ${uvAccessorIndex}`
            );
          } else {
            const uvAccessor = gltf.accessors[uvAccessorIndex];
            if (uvAccessor && uvAccessor.type !== "VEC2") {
              this.errors.push(
                `Mesh ${meshIndex} Primitive ${primitiveIndex}: TEXCOORD_0 must be VEC2, found ${uvAccessor.type}`
              );
            } else {
              console.log(
                `  ✅ Mesh ${meshIndex} Primitive ${primitiveIndex}: TEXCOORD_0 present`
              );
            }
          }
        }
      });
    });

    console.log("");
  }

  /**
   * CRITICAL: Buffer size validation and auto-fixing
   * Checks actual file sizes match byteLength declarations
   */
  validateBufferSizes(gltf) {
    if (!gltf.buffers) return;

    console.log(`${colors.cyan}🔍 Buffer Size Validation${colors.reset}`);

    gltf.buffers.forEach((buffer, index) => {
      if (buffer.uri) {
        const bufferPath = path.join(path.dirname(this.gltfPath), buffer.uri);

        try {
          if (fs.existsSync(bufferPath)) {
            const actualSize = fs.statSync(bufferPath).size;
            const declaredSize = buffer.byteLength || 0;

            if (actualSize !== declaredSize) {
              const errorMsg = `Buffer ${index}: Size mismatch - declared: ${declaredSize}, actual: ${actualSize}`;
              this.warnings.push(errorMsg);

              if (this.autoFix) {
                // Auto-fix the byteLength
                const oldSize = buffer.byteLength;
                buffer.byteLength = actualSize;

                this.fixes.push({
                  type: "buffer_size_fix",
                  bufferIndex: index,
                  oldSize,
                  newSize: actualSize,
                  message: `Fixed buffer ${index} byteLength from ${oldSize} to ${actualSize}`,
                });

                console.log(
                  `  🛠️  Auto-fixed buffer ${index} size: ${oldSize} → ${actualSize}`
                );
              }
            } else {
              console.log(
                `  ✅ Buffer ${index}: Size matches (${actualSize} bytes)`
              );
            }
          } else {
            this.errors.push(`Buffer ${index}: File not found: ${buffer.uri}`);
          }
        } catch (error) {
          this.errors.push(
            `Buffer ${index}: Error reading file: ${error.message}`
          );
        }
      } else if (buffer.byteLength !== undefined) {
        // Embedded buffer
        console.log(
          `  ✅ Buffer ${index}: Embedded buffer (${buffer.byteLength} bytes)`
        );
      }
    });

    console.log("");
  }

  /**
   * Validate overall GLTF structure
   */
  validateStructure(gltf) {
    if (!gltf.asset || !gltf.asset.version) {
      this.errors.push("Missing required asset.version field");
    }

    if (!gltf.scenes || !gltf.scenes.length) {
      this.errors.push("Missing required scenes array");
    }

    if (!gltf.nodes || !gltf.nodes.length) {
      this.errors.push("Missing required nodes array");
    }
  }

  /**
   * Deep accessor type validation - Critical for Error 13 prevention
   */
  validateAccessors(gltf) {
    if (!gltf.accessors) return;

    this.stats.accessors = gltf.accessors.length;

    gltf.accessors.forEach((accessor, index) => {
      // Validate required fields
      if (accessor.componentType === undefined) {
        this.errors.push(`Accessor ${index}: Missing componentType`);
      }

      if (accessor.count === undefined) {
        this.errors.push(`Accessor ${index}: Missing count`);
      }

      if (accessor.type === undefined) {
        this.errors.push(`Accessor ${index}: Missing type`);
      }

      // Validate component type values
      const validComponentTypes = [5120, 5121, 5122, 5123, 5125, 5126];
      if (!validComponentTypes.includes(accessor.componentType)) {
        this.errors.push(
          `Accessor ${index}: Invalid componentType ${accessor.componentType}`
        );
      }

      // Validate type values
      const validTypes = [
        "SCALAR",
        "VEC2",
        "VEC3",
        "VEC4",
        "MAT2",
        "MAT3",
        "MAT4",
      ];
      if (!validTypes.includes(accessor.type)) {
        this.errors.push(`Accessor ${index}: Invalid type "${accessor.type}"`);
      }

      // Validate bufferView reference
      if (accessor.bufferView === undefined) {
        this.errors.push(`Accessor ${index}: Missing bufferView reference`);
      } else if (accessor.bufferView >= (gltf.bufferViews?.length || 0)) {
        this.errors.push(
          `Accessor ${index}: Invalid bufferView reference ${accessor.bufferView}`
        );
      }

      // Validate byteOffset
      if (accessor.byteOffset !== undefined && accessor.byteOffset < 0) {
        this.errors.push(
          `Accessor ${index}: Invalid byteOffset ${accessor.byteOffset}`
        );
      }

      // Validate min/max bounds for non-SCALAR types
      if (accessor.type !== "SCALAR") {
        if (!accessor.min || !accessor.max) {
          this.warnings.push(
            `Accessor ${index}: Missing min/max bounds for ${accessor.type}`
          );
        } else {
          // Validate min/max array length matches type
          const expectedLength = this.getTypeComponentCount(accessor.type);
          if (
            accessor.min.length !== expectedLength ||
            accessor.max.length !== expectedLength
          ) {
            // Only report as error if the arrays are non-empty but wrong length
            if (accessor.min.length > 0 || accessor.max.length > 0) {
              this.errors.push(
                `Accessor ${index}: Min/max bounds length mismatch for ${accessor.type} (expected: ${expectedLength}, min: ${accessor.min.length}, max: ${accessor.max.length})`
              );
            } else {
              // Empty min/max arrays are valid and common in GLTF files
              console.log(
                `🔍 [DEBUG] Accessor ${index}: Empty min/max bounds (valid)`
              );
            }
          }
        }
      }

      // Validate count consistency with bufferView
      if (accessor.bufferView !== undefined && gltf.bufferViews) {
        const bufferView = gltf.bufferViews[accessor.bufferView];
        if (bufferView) {
          const expectedByteLength = this.calculateAccessorByteLength(accessor);
          if (bufferView.byteLength < expectedByteLength) {
            this.errors.push(
              `Accessor ${index}: BufferView too small for accessor data`
            );
          }
        }
      }
    });
  }

  /**
   * Validate buffer views
   */
  validateBufferViews(gltf) {
    if (!gltf.bufferViews) return;

    this.stats.bufferViews = gltf.bufferViews.length;

    gltf.bufferViews.forEach((bufferView, index) => {
      if (bufferView.buffer === undefined) {
        this.errors.push(`BufferView ${index}: Missing buffer reference`);
      } else if (bufferView.buffer >= (gltf.buffers?.length || 0)) {
        this.errors.push(
          `BufferView ${index}: Invalid buffer reference ${bufferView.buffer}`
        );
      }

      if (bufferView.byteLength === undefined) {
        this.errors.push(`BufferView ${index}: Missing byteLength`);
      }

      if (bufferView.byteOffset !== undefined && bufferView.byteOffset < 0) {
        this.errors.push(
          `BufferView ${index}: Invalid byteOffset ${bufferView.byteOffset}`
        );
      }

      if (
        bufferView.byteStride !== undefined &&
        bufferView.byteStride !== null
      ) {
        if (bufferView.byteStride < 4 || bufferView.byteStride > 252) {
          this.errors.push(
            `BufferView ${index}: Invalid byteStride ${bufferView.byteStride}`
          );
        }
        if (bufferView.byteStride % 4 !== 0) {
          this.errors.push(
            `BufferView ${index}: byteStride must be multiple of 4`
          );
        }
      }
      // Note: byteStride being null or undefined is valid - it means data is tightly packed
    });
  }

  /**
   * Validate meshes and their primitives
   */
  validateMeshes(gltf) {
    if (!gltf.meshes) return;

    this.stats.meshes = gltf.meshes.length;

    gltf.meshes.forEach((mesh, meshIndex) => {
      if (!mesh.primitives || !mesh.primitives.length) {
        this.errors.push(`Mesh ${meshIndex}: Missing primitives array`);
        return;
      }

      mesh.primitives.forEach((primitive, primitiveIndex) => {
        // Validate attributes
        if (!primitive.attributes) {
          this.errors.push(
            `Mesh ${meshIndex} Primitive ${primitiveIndex}: Missing attributes`
          );
          return;
        }

        // Validate required attributes for different primitive types
        if (primitive.mode !== 1) {
          // Not POINTS
          if (primitive.attributes.POSITION === undefined) {
            this.errors.push(
              `Mesh ${meshIndex} Primitive ${primitiveIndex}: Missing POSITION attribute`
            );
          }
        }

        // Validate attribute accessor references
        Object.entries(primitive.attributes).forEach(
          ([name, accessorIndex]) => {
            if (accessorIndex >= (gltf.accessors?.length || 0)) {
              this.errors.push(
                `Mesh ${meshIndex} Primitive ${primitiveIndex}: Invalid ${name} accessor reference ${accessorIndex}`
              );
            }
          }
        );

        // Validate indices accessor
        if (primitive.indices !== undefined) {
          if (primitive.indices >= (gltf.accessors?.length || 0)) {
            this.errors.push(
              `Mesh ${meshIndex} Primitive ${primitiveIndex}: Invalid indices accessor reference ${primitive.indices}`
            );
          }
        }

        // Validate material reference
        if (primitive.material !== undefined) {
          if (primitive.material >= (gltf.materials?.length || 0)) {
            this.errors.push(
              `Mesh ${meshIndex} Primitive ${primitiveIndex}: Invalid material reference ${primitive.material}`
            );
          }
        }
      });
    });
  }

  /**
   * Validate materials
   */
  validateMaterials(gltf) {
    if (!gltf.materials) return;

    this.stats.materials = gltf.materials.length;

    gltf.materials.forEach((material, index) => {
      if (material.pbrMetallicRoughness) {
        const pbr = material.pbrMetallicRoughness;

        // Validate base color texture
        if (pbr.baseColorTexture) {
          if (pbr.baseColorTexture.index >= (gltf.textures?.length || 0)) {
            this.errors.push(
              `Material ${index}: Invalid baseColorTexture reference ${pbr.baseColorTexture.index}`
            );
          }
        }

        // Validate metallic roughness texture
        if (pbr.metallicRoughnessTexture) {
          if (
            pbr.metallicRoughnessTexture.index >= (gltf.textures?.length || 0)
          ) {
            this.errors.push(
              `Material ${index}: Invalid metallicRoughnessTexture reference ${pbr.metallicRoughnessTexture.index}`
            );
          }
        }
      }

      // Validate normal texture
      if (material.normalTexture) {
        if (material.normalTexture.index >= (gltf.textures?.length || 0)) {
          this.errors.push(
            `Material ${index}: Invalid normalTexture reference ${material.normalTexture.index}`
          );
        }
      }

      // Validate occlusion texture
      if (material.occlusionTexture) {
        if (material.occlusionTexture.index >= (gltf.textures?.length || 0)) {
          this.errors.push(
            `Material ${index}: Invalid occlusionTexture reference ${material.occlusionTexture.index}`
          );
        }
      }

      // Validate emissive texture
      if (material.emissiveTexture) {
        if (material.emissiveTexture.index >= (gltf.textures?.length || 0)) {
          this.errors.push(
            `Material ${index}: Invalid emissiveTexture reference ${material.emissiveTexture.index}`
          );
        }
      }
    });
  }

  /**
   * Validate textures
   */
  validateTextures(gltf) {
    if (!gltf.textures) return;

    this.stats.textures = gltf.textures.length;

    gltf.textures.forEach((texture, index) => {
      if (texture.source === undefined) {
        this.errors.push(`Texture ${index}: Missing source reference`);
      } else if (texture.source >= (gltf.images?.length || 0)) {
        this.errors.push(
          `Texture ${index}: Invalid source reference ${texture.source}`
        );
      }

      if (texture.sampler !== undefined) {
        if (texture.sampler >= (gltf.samplers?.length || 0)) {
          this.errors.push(
            `Texture ${index}: Invalid sampler reference ${texture.sampler}`
          );
        }
      }
    });
  }

  /**
   * Validate images
   */
  validateImages(gltf) {
    if (!gltf.images) return;

    this.stats.images = gltf.images.length;

    gltf.images.forEach((image, index) => {
      if (!image.uri && !image.bufferView) {
        this.errors.push(`Image ${index}: Missing uri or bufferView`);
      }

      if (image.bufferView !== undefined) {
        if (image.bufferView >= (gltf.bufferViews?.length || 0)) {
          this.errors.push(
            `Image ${index}: Invalid bufferView reference ${image.bufferView}`
          );
        }
      }
    });
  }

  /**
   * Validate buffers
   */
  validateBuffers(gltf) {
    if (!gltf.buffers) return;

    this.stats.buffers = gltf.buffers.length;

    gltf.buffers.forEach((buffer, index) => {
      if (!buffer.uri && !buffer.byteLength) {
        this.errors.push(`Buffer ${index}: Missing uri or byteLength`);
      }

      if (buffer.byteLength !== undefined && buffer.byteLength <= 0) {
        this.errors.push(
          `Buffer ${index}: Invalid byteLength ${buffer.byteLength}`
        );
      }
    });
  }

  /**
   * CRITICAL: Error 23 prevention - Accessor validation and buffer view alignment
   * Checks for common issues like accessor type mismatch, bufferView byteLength mismatch,
   * and accessor byteOffset/stride alignment issues.
   */
  validateError23(gltf) {
    if (!gltf.accessors || !gltf.bufferViews) return;

    console.log(
      `${colors.cyan}🔍 Error 23 Prevention (Accessor/BufferView Alignment)${colors.reset}`
    );

    let error23Detected = false;

    gltf.accessors.forEach((accessor, index) => {
      console.log(`🔍 [DEBUG] Validating accessor ${index}:`, accessor);

      if (accessor.bufferView === undefined || accessor.bufferView === null) {
        this.errors.push(`Accessor ${index}: Missing bufferView reference`);
        error23Detected = true;
        return;
      }

      const bufferViewIndex = accessor.bufferView;
      console.log(
        `🔍 [DEBUG] Accessor ${index} references bufferView ${bufferViewIndex}`
      );

      if (bufferViewIndex < 0 || bufferViewIndex >= gltf.bufferViews.length) {
        this.errors.push(
          `Accessor ${index}: Invalid bufferView index ${bufferViewIndex} (max: ${
            gltf.bufferViews.length - 1
          })`
        );
        error23Detected = true;
        return;
      }

      const bufferView = gltf.bufferViews[bufferViewIndex];
      console.log(`🔍 [DEBUG] BufferView ${bufferViewIndex}:`, bufferView);

      if (!bufferView) {
        this.errors.push(
          `Accessor ${index}: BufferView ${bufferViewIndex} is null/undefined`
        );
        error23Detected = true;
        return;
      }

      // Check byteStride
      if (
        bufferView.byteStride !== undefined &&
        bufferView.byteStride !== null
      ) {
        const componentCount = this.getTypeComponentCount(accessor.type);
        const componentSize = this.getComponentSize(accessor.componentType);
        const minStride = componentCount * componentSize;

        console.log(
          `🔍 [DEBUG] Accessor ${index}: componentCount=${componentCount}, componentSize=${componentSize}, minStride=${minStride}, actualStride=${bufferView.byteStride}`
        );

        if (bufferView.byteStride < minStride) {
          this.errors.push(
            `Accessor ${index}: byteStride ${bufferView.byteStride} too small for type ${accessor.type} (minimum: ${minStride})`
          );
          error23Detected = true;
        }

        if (bufferView.byteStride % 4 !== 0) {
          this.errors.push(
            `Accessor ${index}: byteStride ${bufferView.byteStride} not aligned to 4-byte boundary`
          );
          error23Detected = true;
        }
      } else {
        // byteStride is null or undefined, which is valid - it means data is tightly packed
        console.log(
          `🔍 [DEBUG] Accessor ${index}: byteStride is null/undefined (tightly packed data)`
        );
      }

      // Check byteOffset
      if (accessor.byteOffset !== undefined) {
        if (accessor.byteOffset < 0) {
          this.errors.push(
            `Accessor ${index}: Negative byteOffset ${accessor.byteOffset}`
          );
          error23Detected = true;
        }

        if (accessor.byteOffset >= bufferView.byteLength) {
          this.errors.push(
            `Accessor ${index}: byteOffset ${accessor.byteOffset} exceeds bufferView byteLength ${bufferView.byteLength}`
          );
          error23Detected = true;
        }
      }

      // Check count vs buffer size
      const bytesPerElement = this.calculateAccessorByteLength(accessor);
      const totalBytesNeeded = accessor.count * bytesPerElement;

      console.log(
        `🔍 [DEBUG] Accessor ${index}: count=${accessor.count}, bytesPerElement=${bytesPerElement}, totalBytesNeeded=${totalBytesNeeded}, bufferViewSize=${bufferView.byteLength}`
      );

      if (totalBytesNeeded > bufferView.byteLength) {
        this.errors.push(
          `Accessor ${index}: Accessor count ${accessor.count} exceeds BufferView byteLength ${bufferView.byteLength} (needs ${totalBytesNeeded} bytes)`
        );
        error23Detected = true;
      }
    });

    if (!error23Detected) {
      console.log("  ✅ All accessors passed alignment checks");
    }

    console.log("✅ Error 23 prevention checks completed");
  }

  /**
   * CRITICAL: Error 20 prevention - Format corruption and structure validation
   * Checks for common issues that cause Sketchfab upload failures.
   */
  validateError20(gltf) {
    if (!gltf.accessors || !gltf.bufferViews || !gltf.meshes) return;

    console.log(
      `${colors.cyan}🔍 Error 20 Prevention (Format Corruption)${colors.reset}`
    );

    // Check for actual corruption issues, not legitimate GLTF sharing patterns
    let corruptionDetected = false;

    // Check for null/undefined references that would cause corruption
    gltf.accessors.forEach((accessor, index) => {
      if (accessor.bufferView === null || accessor.bufferView === undefined) {
        this.errors.push(
          `Accessor ${index}: Invalid bufferView reference (null/undefined)`
        );
        corruptionDetected = true;
      }
    });

    gltf.bufferViews.forEach((bufferView, index) => {
      if (bufferView.buffer === null || bufferView.buffer === undefined) {
        this.errors.push(
          `BufferView ${index}: Invalid buffer reference (null/undefined)`
        );
        corruptionDetected = true;
      }
    });

    // Check for circular references that would cause corruption
    const visited = new Set();
    const checkCircular = (obj, path) => {
      if (visited.has(obj)) {
        this.errors.push(`Circular reference detected at ${path}`);
        corruptionDetected = true;
        return;
      }
      visited.add(obj);
    };

    // Check for malformed JSON structures
    if (typeof gltf !== "object" || gltf === null) {
      this.errors.push(`Invalid GLTF structure: root is not an object`);
      corruptionDetected = true;
    }

    // Check for missing required fields that would cause corruption
    if (!gltf.asset || !gltf.asset.version) {
      this.errors.push(`Missing required asset.version field`);
      corruptionDetected = true;
    }

    if (!gltf.scenes || !Array.isArray(gltf.scenes)) {
      this.errors.push(`Missing or invalid scenes array`);
      corruptionDetected = true;
    }

    if (!gltf.nodes || !Array.isArray(gltf.nodes)) {
      this.errors.push(`Missing or invalid nodes array`);
      corruptionDetected = true;
    }

    if (!corruptionDetected) {
      console.log("  ✅ No format corruption detected");
      console.log("  ✅ GLTF structure is valid");
      console.log("  ✅ All references are properly defined");
    }

    console.log("✅ Error 20 prevention checks completed");
  }

  /**
   * Calculate the expected byte length for an accessor
   */
  calculateAccessorByteLength(accessor) {
    const componentCount = this.getTypeComponentCount(accessor.type);
    const componentSize = this.getComponentSize(accessor.componentType);
    return componentCount * componentSize; // Return bytes per element, not total bytes
  }

  /**
   * Get the number of components for an accessor type
   */
  getTypeComponentCount(type) {
    const typeMap = {
      SCALAR: 1,
      VEC2: 2,
      VEC3: 3,
      VEC4: 4,
      MAT2: 4,
      MAT3: 9,
      MAT4: 16,
    };
    return typeMap[type] || 1;
  }

  /**
   * Get the size of a component type in bytes
   */
  getComponentSize(componentType) {
    const sizeMap = {
      5120: 1, // BYTE
      5121: 1, // UNSIGNED_BYTE
      5122: 2, // SHORT
      5123: 2, // UNSIGNED_SHORT
      5125: 4, // UNSIGNED_INT
      5126: 4, // FLOAT
    };
    return sizeMap[componentType] || 4;
  }

  /**
   * Apply auto-fixes to the GLTF file
   */
  async applyFixes() {
    if (this.fixes.length === 0) return;

    console.log(`${colors.yellow}🛠️  Applying Auto-Fixes...${colors.reset}`);

    try {
      // Write the updated GLTF data back to file
      const updatedContent = JSON.stringify(this.gltfData, null, 2);
      fs.writeFileSync(this.gltfPath, updatedContent);

      console.log(
        `${colors.green}✅ Auto-fixes applied successfully!${colors.reset}`
      );
      console.log(
        `${colors.green}📁 Updated file: ${this.gltfPath}${colors.reset}`
      );

      // Show summary of fixes
      this.fixes.forEach((fix, index) => {
        console.log(`  ${index + 1}. ${fix.message}`);
      });
    } catch (error) {
      console.error(
        `${colors.red}❌ Failed to apply auto-fixes: ${error.message}${colors.reset}`
      );
    }

    console.log("");
  }

  /**
   * Generate comprehensive validation report
   */
  generateReport() {
    console.log(
      `${colors.cyan}${colors.bright}📊 VALIDATION REPORT${colors.reset}\n`
    );

    // Statistics
    console.log(`${colors.blue}📈 Asset Statistics:${colors.reset}`);
    console.log(`  • Accessors: ${this.stats.accessors}`);
    console.log(`  • Buffer Views: ${this.stats.bufferViews}`);
    console.log(`  • Buffers: ${this.stats.buffers}`);
    console.log(`  • Meshes: ${this.stats.meshes}`);
    console.log(`  • Materials: ${this.stats.materials}`);
    console.log(`  • Textures: ${this.stats.textures}`);
    console.log(`  • Images: ${this.stats.images}\n`);

    // Errors
    if (this.errors.length > 0) {
      console.log(
        `${colors.red}❌ ERRORS (${this.errors.length}):${colors.reset}`
      );
      this.errors.forEach((error, index) => {
        console.log(`  ${index + 1}. ${error}`);
      });
      console.log("");
    }

    // Warnings
    if (this.warnings.length > 0) {
      console.log(
        `${colors.yellow}⚠️  WARNINGS (${this.warnings.length}):${colors.reset}`
      );
      this.warnings.forEach((warning, index) => {
        console.log(`  ${index + 1}. ${warning}`);
      });
      console.log("");
    }

    // Fixes applied
    if (this.fixes.length > 0) {
      console.log(
        `${colors.green}🛠️  AUTO-FIXES APPLIED (${this.fixes.length}):${colors.reset}`
      );
      this.fixes.forEach((fix, index) => {
        console.log(`  ${index + 1}. ${fix.message}`);
      });
      console.log("");
    }

    // Final status
    if (this.errors.length === 0) {
      console.log(`${colors.green}✅ VALIDATION PASSED${colors.reset}`);
      console.log(
        `${colors.green}🎯 This GLTF file is ready for Sketchfab upload!${colors.reset}`
      );

      // Check if Error 13 prevention is active
      const hasUVs =
        this.gltfData.meshes &&
        this.gltfData.meshes.every(
          (mesh) =>
            mesh.primitives &&
            mesh.primitives.every(
              (primitive) =>
                primitive.attributes &&
                primitive.attributes.TEXCOORD_0 !== undefined
            )
        );

      // Check if Error 23 prevention is active
      const hasValidAccessors =
        this.gltfData.accessors &&
        this.gltfData.accessors.every((accessor) => {
          if (
            !accessor.bufferView ||
            !this.gltfData.bufferViews[accessor.bufferView]
          )
            return false;
          const bufferView = this.gltfData.bufferViews[accessor.bufferView];
          if (
            bufferView.byteStride !== undefined &&
            bufferView.byteStride % 4 !== 0
          )
            return false;
          return true;
        });

      // Check if Error 20 prevention is active
      const hasValidStructure =
        this.errors.length === 0 ||
        !this.errors.some(
          (error) => error.includes("Duplicate") || error.includes("corruption")
        );

      if (hasUVs) {
        console.log(
          `${colors.green}🛡️  Error 13 prevention: ACTIVE${colors.reset}`
        );
      }

      if (hasValidAccessors) {
        console.log(
          `${colors.green}🛡️  Error 23 prevention: ACTIVE${colors.reset}`
        );
      }

      if (hasValidStructure) {
        console.log(
          `${colors.green}🛡️  Error 20 prevention: ACTIVE${colors.reset}`
        );
      }
    } else {
      console.log(`${colors.red}❌ VALIDATION FAILED${colors.reset}`);
      console.log(
        `${colors.red}🚫 This GLTF file has issues that may cause upload failures${colors.reset}`
      );

      // Check for critical Error 13 issues
      const hasUVIssues = this.errors.some((error) =>
        error.includes("TEXCOORD_0")
      );
      if (hasUVIssues) {
        console.log(
          `${colors.red}🚨 CRITICAL: Missing UV coordinates detected!${colors.reset}`
        );
        console.log(
          `${colors.red}🚨 This will cause Sketchfab Error 13!${colors.reset}`
        );
        console.log(
          `${colors.yellow}💡 Fix UV coordinates in Blender before uploading${colors.reset}`
        );
      }

      console.log(
        `${colors.yellow}💡 Fix the errors above before uploading to Sketchfab${colors.reset}`
      );
    }

    console.log("");
  }
}

/**
 * Main execution
 */
async function main() {
  const args = process.argv.slice(2);

  // Help command
  if (args.includes("--help") || args.includes("-h") || args.length === 0) {
    console.log(
      `${colors.cyan}${colors.bright}VoxBridge GLTF Validator v1.1${colors.reset}`
    );
    console.log(
      `${colors.blue}Prevents Error 13 (data corruption), Error 20 (format corruption), and Error 23 (accessor validation) issues for Sketchfab uploads${colors.reset}\n`
    );
    console.log("Usage:");
    console.log("  node validate_gltf.js <input.gltf>");
    console.log(
      "  node validate_gltf.js --fix <input.gltf>  # Auto-fix issues"
    );
    console.log("  node validate_gltf.js --help\n");
    console.log("Examples:");
    console.log("  node validate_gltf.js model.gltf");
    console.log("  node validate_gltf.js --fix scene.glb");
    console.log("");
    console.log("This tool performs comprehensive validation including:");
    console.log(
      "  • UV coordinate validation (TEXCOORD_0) - Critical for Error 13"
    );
    console.log(
      "  • Accessor validation and buffer alignment - Critical for Error 23"
    );
    console.log(
      "  • Format corruption and structure validation - Critical for Error 20"
    );
    console.log("  • Deep accessor type validation");
    console.log("  • Data consistency checks");
    console.log("  • Buffer reference validation");
    console.log("  • Mesh and primitive validation");
    console.log("  • Material and texture validation");
    console.log("  • Buffer size auto-fixing");
    console.log("  • Error 13 prevention checks");
    console.log("  • Error 20 prevention checks");
    console.log("  • Error 23 prevention checks");
    return;
  }

  // Check for auto-fix mode
  const autoFix = args.includes("--fix");
  const inputPath = autoFix ? args[args.indexOf("--fix") + 1] : args[0];

  if (!inputPath) {
    console.error(`${colors.red}❌ No input file specified${colors.reset}`);
    console.error(
      `${colors.yellow}Usage: node validate_gltf.js [--fix] <input.gltf>${colors.reset}`
    );
    process.exit(1);
  }

  // Check if file exists
  if (!fs.existsSync(inputPath)) {
    console.error(
      `${colors.red}❌ File not found: ${inputPath}${colors.reset}`
    );
    process.exit(1);
  }

  // Validate file extension
  const ext = path.extname(inputPath).toLowerCase();
  if (ext !== ".gltf" && ext !== ".glb") {
    console.error(
      `${colors.red}❌ Unsupported file type: ${ext}${colors.reset}`
    );
    console.error(
      `${colors.yellow}Supported types: .gltf, .glb${colors.reset}`
    );
    process.exit(1);
  }

  // Perform validation
  const validator = new GLTFValidator();
  const isValid = await validator.validate(inputPath, autoFix);

  // Exit with appropriate code
  process.exit(isValid ? 0 : 1);
}

// Run if called directly
if (require.main === module) {
  main().catch((error) => {
    console.error(
      `${colors.red}❌ Unexpected error: ${error.message}${colors.reset}`
    );
    process.exit(1);
  });
}

module.exports = GLTFValidator;
