#!/usr/bin/env python3
"""
Debug script for Roblox profile
"""

import sys
from pathlib import Path
import json

# Add the voxbridge package to the path
sys.path.insert(0, str(Path(__file__).parent))

from voxbridge.platform_profiles import RobloxProfile

# Sample glTF data
sample_gltf = {
    "asset": {"version": "2.0"},
    "scene": 0,
    "materials": [
        {
            "name": "TestMaterial",
            "pbrMetallicRoughness": {
                "baseColorFactor": [1.0, 0.0, 0.0, 1.0],
                "metallicFactor": 0.5,
                "roughnessFactor": 0.3
            },
            "extensions": {"some_extension": {}}
        }
    ],
    "images": [
        {"uri": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="}
    ],
    "nodes": [
        {"name": "VeryLongNodeNameThatExceedsRobloxLimitsAndShouldBeTruncated"}
    ]
}

print("Original glTF:")
print(json.dumps(sample_gltf, indent=2))

profile = RobloxProfile(debug=True)
optimized = profile.optimize_gltf(sample_gltf, Path("test_output"))

print("\nOptimized glTF:")
print(json.dumps(optimized, indent=2))

# Check specific assertions
material = optimized['materials'][0]
print(f"\nMaterial checks:")
print(f"Has pbrMetallicRoughness: {'pbrMetallicRoughness' in material}")
print(f"Has metallicFactor: {'metallicFactor' in material['pbrMetallicRoughness']}")
print(f"Has extensions: {'extensions' in material}")
print(f"Extensions used length: {len(optimized.get('extensionsUsed', []))}")
print(f"Node name length: {len(optimized['nodes'][0]['name'])}")

# Check what should be removed
print(f"\nWhat should be removed:")
print(f"metallicFactor should be removed: {'metallicFactor' not in material['pbrMetallicRoughness']}")
print(f"extensions should be removed: {'extensions' not in material}")
print(f"extensionsUsed should be empty: {len(optimized.get('extensionsUsed', [])) == 0}")
print(f"Node name should be <= 32: {len(optimized['nodes'][0]['name']) <= 32}")
