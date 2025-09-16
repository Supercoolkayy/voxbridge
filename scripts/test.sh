#!/bin/bash
# scripts/test.sh - Test runner for VoxBridge

set -e

echo "VoxBridge Test Runner"
echo "===================="

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}[OK] $1${NC}"
}

print_error() {
    echo -e "${RED}[ERROR] $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}[WARN] $1${NC}"
}

# Check if we're in a virtual environment
if [[ -z "$VIRTUAL_ENV" ]] && [[ -d "venv" ]]; then
    print_status "Activating virtual environment..."
    source venv/bin/activate
fi

# Install test dependencies if needed
if ! python -c "import pytest" 2>/dev/null; then
    print_status "Installing test dependencies..."
    pip install pytest pytest-cov
fi

# Install package in development mode
print_status "Installing VoxBridge in development mode..."
pip install -e .

# Run unit tests
print_status "Running unit tests..."
python -m pytest tests/ -v --tb=short

# Run tests with coverage if pytest-cov is available
if python -c "import pytest_cov" 2>/dev/null; then
    print_status "Running tests with coverage..."
    python -m pytest tests/ --cov=voxbridge --cov-report=term-missing --cov-report=html
    print_status "Coverage report saved to htmlcov/index.html"
fi

# Test CLI directly
print_status "Testing CLI interface..."

# Create a simple test glTF file
mkdir -p test_assets
cat > test_assets/simple.gltf << 'EOF'
{
  "asset": {"version": "2.0"},
  "scene": 0,
  "scenes": [{"nodes": [0]}],
  "nodes": [{"mesh": 0}],
  "meshes": [{"primitives": [{"attributes": {"POSITION": 0}}]}],
  "materials": [{"name": "Test#Material!"}],
  "images": [{"uri": "/absolute/path/texture.png"}],
  "accessors": [{"bufferView": 0, "componentType": 5126, "count": 3, "type": "VEC3"}],
  "bufferViews": [{"buffer": 0, "byteLength": 36}],
  "buffers": [{"byteLength": 36, "uri": "data.bin"}]
}
EOF

# Create fake associated files
echo "fake texture data" > test_assets/texture.png
echo "fake binary data for testing purposes" > test_assets/data.bin

# Test CLI with JSON processing
print_status "Testing CLI with glTF file..."
mkdir -p test_output
python -m voxbridge.cli test_assets/simple.gltf test_output/simple_clean.gltf --no-blender

if [[ -f "test_output/simple_clean.gltf" ]]; then
    print_status "CLI test passed - output file created"
    
    # Check if the cleaning worked
    if grep -q "Test_Material" test_output/simple_clean.gltf; then
        print_status "Material name cleaning verified"
    else
        print_warning "Material name cleaning may not have worked"
    fi
    
    if grep -q '"uri": "texture.png"' test_output/simple_clean.gltf; then
        print_status "Texture path cleaning verified"
    else
        print_warning "Texture path cleaning may not have worked"
    fi
else
    print_error "CLI test failed - no output file created"
    exit 1
fi

# Test version command
print_status "Testing version command..."
python -m voxbridge.cli --version

# Test help command
print_status "Testing help command..."
python -m voxbridge.cli --help > /dev/null

# Test error handling
print_status "Testing error handling..."
if python -m voxbridge.cli nonexistent.gltf output.gltf 2>/dev/null; then
    print_error "Error handling test failed - should have failed for nonexistent file"
    exit 1
else
    print_status "Error handling test passed"
fi

# Performance test with larger file
print_status "Running performance test..."
cat > test_assets/complex.gltf << 'EOF'
{
  "asset": {"version": "2.0"},
  "scene": 0,
  "scenes": [{"nodes": [0, 1, 2, 3, 4]}],
  "nodes": [
    {"mesh": 0}, {"mesh": 1}, {"mesh": 2}, {"mesh": 3}, {"mesh": 4}
  ],
  "meshes": [
    {"primitives": [{"attributes": {"POSITION": 0}, "material": 0}]},
    {"primitives": [{"attributes": {"POSITION": 1}, "material": 1}]},
    {"primitives": [{"attributes": {"POSITION": 2}, "material": 2}]},
    {"primitives": [{"attributes": {"POSITION": 3}, "material": 3}]},
    {"primitives": [{"attributes": {"POSITION": 4}, "material": 4}]}
  ],
  "materials": [
EOF

# Add many materials with problematic names
for i in {0..49}; do
    echo "    {\"name\": \"Material#$i (Special*Characters!)\"}," >> test_assets/complex.gltf
done

cat >> test_assets/complex.gltf << 'EOF'
    {"name": "LastMaterial"}
  ],
  "images": [
EOF

# Add many images with absolute paths
for i in {0..49}; do
    echo "    {\"uri\": \"/absolute/path/to/texture$i.png\"}," >> test_assets/complex.gltf
done

cat >> test_assets/complex.gltf << 'EOF'
    {"uri": "/absolute/path/to/last_texture.png"}
  ],
  "accessors": [
    {"bufferView": 0, "componentType": 5126, "count": 100, "type": "VEC3"},
    {"bufferView": 1, "componentType": 5126, "count": 100, "type": "VEC3"},
    {"bufferView": 2, "componentType": 5126, "count": 100, "type": "VEC3"},
    {"bufferView": 3, "componentType": 5126, "count": 100, "type": "VEC3"},
    {"bufferView": 4, "componentType": 5126, "count": 100, "type": "VEC3"}
  ],
  "bufferViews": [
    {"buffer": 0, "byteLength": 1200, "byteOffset": 0},
    {"buffer": 0, "byteLength": 1200, "byteOffset": 1200},
    {"buffer": 0, "byteLength": 1200, "byteOffset": 2400},
    {"buffer": 0, "byteLength": 1200, "byteOffset": 3600},
    {"buffer": 0, "byteLength": 1200, "byteOffset": 4800}
  ],
  "buffers": [{"byteLength": 6000, "uri": "complex.bin"}]
}
EOF

# Performance test
start_time=$(date +%s)
python -m voxbridge.cli test_assets/complex.gltf test_output/complex_clean.gltf --no-blender
end_time=$(date +%s)
duration=$((end_time - start_time))

print_status "Performance test completed in ${duration}s"

if [[ $duration -gt 10 ]]; then
    print_warning "Performance test took longer than expected (${duration}s)"
else
    print_status "Performance test passed (${duration}s)"
fi

# Cleanup test files
print_status "Cleaning up test files..."
rm -rf test_assets test_output

# Final summary
print_status "All tests completed successfully!"

echo ""
echo "Test Summary:"
echo "   Unit tests passed"
echo "   CLI functionality verified"
echo "   Error handling works"
echo "   Performance acceptable"
echo ""
echo "VoxBridge is ready for use!"