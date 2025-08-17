#!/usr/bin/env python3
"""
VoxBridge Repository Cleanup Script
Audits and removes redundant/unnecessary files
"""

import os
import shutil
from pathlib import Path
import json

def audit_files():
    """Audit all files in the repository"""
    print("VoxBridge Repository Audit")
    print("=" * 40)
    
    # Files to check for removal
    files_to_remove = [
        "test_tool.py",  # Already removed
        "RELEASE_NOTES_v0.2.md",  # Already removed
        "PROJECT_STRUCTURE.md",  # Already removed
        "CLEANUP_SUMMARY.md",  # Already removed
        ".pre-commit-config.yaml",  # Already removed
        "setup.py",  # Should be replaced by pyproject.toml
    ]
    
    # Directories to check
    dirs_to_check = [
        "voxbridge.egg-info",
        "__pycache__",
        ".pytest_cache",
        "build",
        "dist",
        "*.egg-info",
    ]
    
    # Check for files that should be removed
    print("Checking for files that should be removed:")
    for file_path in files_to_remove:
        path = Path(file_path)
        if path.exists():
            print(f"  ❌ {file_path} - Should be removed")
        else:
            print(f"   {file_path} - Already removed or doesn't exist")
    
    # Check for directories that should be cleaned
    print("\nChecking for directories that should be cleaned:")
    for dir_pattern in dirs_to_check:
        if "*" in dir_pattern:
            # Handle glob patterns
            matches = list(Path(".").glob(dir_pattern))
            for match in matches:
                if match.exists():
                    print(f"  ❌ {match} - Should be removed")
                else:
                    print(f"   {match} - Already removed")
        else:
            path = Path(dir_pattern)
            if path.exists():
                print(f"  ❌ {dir_pattern} - Should be removed")
            else:
                print(f"   {dir_pattern} - Already removed or doesn't exist")
    
    # Check for redundant documentation
    print("\nChecking for redundant documentation:")
    doc_files = [
        "docs/installation.md",
        "docs/usage.md",
        "docs/performance.md",
        "docs/milestone3-plan.md",
    ]
    
    for doc_file in doc_files:
        path = Path(doc_file)
        if path.exists():
            print(f"  📄 {doc_file} - Exists")
        else:
            print(f"  ❌ {doc_file} - Missing")
    
    # Check for test files
    print("\nChecking test structure:")
    test_files = [
        "tests/test_converter.py",
        "tests/fixtures/",
    ]
    
    for test_file in test_files:
        path = Path(test_file)
        if path.exists():
            print(f"   {test_file} - Exists")
        else:
            print(f"  ❌ {test_file} - Missing")
    
    # Check for essential files
    print("\nChecking essential files:")
    essential_files = [
        "pyproject.toml",
        "voxbridge/__init__.py",
        "voxbridge/cli.py",
        "voxbridge/converter.py",
        "voxbridge/gui/app.py",
        "README.md",
        "LICENSE",
        ".gitignore",
        "requirements.txt",
    ]
    
    for essential_file in essential_files:
        path = Path(essential_file)
        if path.exists():
            print(f"   {essential_file} - Exists")
        else:
            print(f"  ❌ {essential_file} - Missing")

def cleanup_build_artifacts():
    """Remove build artifacts"""
    print("\nCleaning build artifacts...")
    
    artifacts = [
        "build/",
        "dist/",
        "*.egg-info/",
        "__pycache__/",
        ".pytest_cache/",
        "*.pyc",
        "*.pyo",
        "*.pyd",
    ]
    
    for artifact in artifacts:
        if "*" in artifact:
            # Handle glob patterns
            matches = list(Path(".").glob(artifact))
            for match in matches:
                if match.exists():
                    if match.is_dir():
                        shutil.rmtree(match)
                        print(f"  🗑️  Removed directory: {match}")
                    else:
                        match.unlink()
                        print(f"  🗑️  Removed file: {match}")
        else:
            path = Path(artifact)
            if path.exists():
                if path.is_dir():
                    shutil.rmtree(path)
                    print(f"  🗑️  Removed directory: {path}")
                else:
                    path.unlink()
                    print(f"  🗑️  Removed file: {path}")

def verify_structure():
    """Verify the repository structure is correct"""
    print("\nVerifying repository structure...")
    
    expected_structure = {
        "voxbridge/": {
            "__init__.py": "Main package init",
            "cli.py": "CLI interface",
            "converter.py": "Core converter",
            "gui/": {
                "__init__.py": "GUI package init",
                "app.py": "GUI application",
            }
        },
        "examples/": {
            "input/": "Input examples",
            "output/": "Output examples",
        },
        "tests/": {
            "test_converter.py": "Converter tests",
            "fixtures/": "Test fixtures",
        },
        "scripts/": {
            "build_cli.sh": "CLI build script",
            "build_gui.sh": "GUI build script",
        },
        ".github/workflows/": {
            "release.yml": "Release workflow",
        },
        "pyproject.toml": "Package configuration",
        "README.md": "Documentation",
        "LICENSE": "License",
        ".gitignore": "Git ignore",
        "requirements.txt": "Dependencies",
    }
    
    def check_structure(structure, base_path=""):
        for item, details in structure.items():
            path = Path(base_path) / item
            if isinstance(details, dict):
                # Directory
                if path.exists():
                    print(f"   {path}/ - Exists")
                    check_structure(details, str(path))
                else:
                    print(f"  ❌ {path}/ - Missing")
            else:
                # File
                if path.exists():
                    print(f"   {path} - {details}")
                else:
                    print(f"  ❌ {path} - Missing ({details})")
    
    check_structure(expected_structure)

def main():
    """Main cleanup function"""
    print("VoxBridge Repository Cleanup")
    print("=" * 40)
    
    # Audit files
    audit_files()
    
    # Clean build artifacts
    cleanup_build_artifacts()
    
    # Verify structure
    verify_structure()
    
    print("\nCleanup completed!")
    print("\nNext steps:")
    print("1. Test the CLI: python test_cli.py")
    print("2. Build the package: bash scripts/build_cli.sh")
    print("3. Test installation: pipx install --force ./dist/voxbridge-1.0.0-py3-none-any.whl")

if __name__ == "__main__":
    main() 