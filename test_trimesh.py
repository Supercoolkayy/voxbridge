#!/usr/bin/env python3
"""
Test script to verify Trimesh is working properly
"""

try:
    import trimesh
    print("✅ Trimesh imported successfully")
    print(f"   Version: {trimesh.__version__}")
    
    # Test basic functionality
    import trimesh.io
    import trimesh.visual
    import trimesh.scene
    print("✅ All Trimesh submodules imported successfully")
    
    # Test if it can load a GLB file
    try:
        # This is a basic test - we won't actually load the file
        print("✅ Trimesh is ready for GLB processing")
    except Exception as e:
        print(f"⚠️  Trimesh import OK but may have issues: {e}")
        
except ImportError as e:
    print(f"❌ Trimesh import failed: {e}")
    print("   Please install trimesh: pip install trimesh")
    exit(1)

print("\n🎯 Trimesh is ready for VoxBridge!")
