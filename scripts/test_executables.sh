#!/usr/bin/env bash
set -euo pipefail

# VoxBridge Executable Test Script
# Tests executables on all platforms to ensure they work out of the box

echo "VoxBridge Executable Test Script"
echo "================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[OK] $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}[WARN] $1${NC}"
}

print_error() {
    echo -e "${RED}[ERROR] $1${NC}"
}

print_info() {
    echo -e "${BLUE}[INFO] $1${NC}"
}

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

test_command() {
    local test_name="$1"
    local command="$2"
    local expected_exit_code="${3:-0}"
    
    print_info "Testing: $test_name"
    
    if eval "$command" > /dev/null 2>&1; then
        local exit_code=$?
        if [[ $exit_code -eq $expected_exit_code ]]; then
            print_status "$test_name passed"
            ((TESTS_PASSED++))
            return 0
        else
            print_error "$test_name failed (exit code: $exit_code, expected: $expected_exit_code)"
            ((TESTS_FAILED++))
            return 1
        fi
    else
        local exit_code=$?
        if [[ $exit_code -eq $expected_exit_code ]]; then
            print_status "$test_name passed"
            ((TESTS_PASSED++))
            return 0
        else
            print_error "$test_name failed (exit code: $exit_code, expected: $expected_exit_code)"
            ((TESTS_FAILED++))
            return 1
        fi
    fi
}

# Detect platform
PLATFORM=$(uname -s)
print_info "Testing on platform: $PLATFORM"

# Check if executables exist
if [[ ! -f "dist/voxbridge" ]] && [[ ! -f "dist/voxbridge.exe" ]]; then
    print_error "CLI executable not found. Please build first."
    exit 1
fi

if [[ ! -f "dist/voxbridge-gui" ]] && [[ ! -f "dist/voxbridge-gui.exe" ]]; then
    print_error "GUI executable not found. Please build first."
    exit 1
fi

# Set executable permissions on Linux/macOS
if [[ "$PLATFORM" == "Linux" ]] || [[ "$PLATFORM" == "Darwin" ]]; then
    chmod +x dist/voxbridge dist/voxbridge-gui
fi

# Test CLI executable
print_info "Testing CLI executable..."

# Test --help
if [[ "$PLATFORM" == "MINGW"* ]] || [[ "$PLATFORM" == "CYGWIN"* ]] || [[ "$PLATFORM" == "MSYS"* ]]; then
    test_command "CLI --help" "dist\\voxbridge.exe --help"
    test_command "CLI convert --help" "dist\\voxbridge.exe convert --help"
    test_command "CLI doctor" "dist\\voxbridge.exe doctor"
else
    test_command "CLI --help" "./dist/voxbridge --help"
    test_command "CLI convert --help" "./dist/voxbridge convert --help"
    test_command "CLI doctor" "./dist/voxbridge doctor"
fi

# Test with invalid input (should fail gracefully)
if [[ "$PLATFORM" == "MINGW"* ]] || [[ "$PLATFORM" == "CYGWIN"* ]] || [[ "$PLATFORM" == "MSYS"* ]]; then
    test_command "CLI invalid input" "dist\\voxbridge.exe convert --input nonexistent.glb --target unity" 1
else
    test_command "CLI invalid input" "./dist/voxbridge convert --input nonexistent.glb --target unity" 1
fi

# Test GUI executable
print_info "Testing GUI executable..."

# Test GUI startup (should not crash)
if [[ "$PLATFORM" == "MINGW"* ]] || [[ "$PLATFORM" == "CYGWIN"* ]] || [[ "$PLATFORM" == "MSYS"* ]]; then
    test_command "GUI startup" "timeout 5s dist\\voxbridge-gui.exe --help" 0
else
    test_command "GUI startup" "timeout 5s ./dist/voxbridge-gui --help" 0
fi

# Test file types and architecture
print_info "Verifying file types and architecture..."

if [[ "$PLATFORM" == "Linux" ]]; then
    if file dist/voxbridge | grep -q "ELF 64-bit"; then
        print_status "CLI is a valid 64-bit ELF binary"
        ((TESTS_PASSED++))
    else
        print_error "CLI is not a valid 64-bit ELF binary"
        ((TESTS_FAILED++))
    fi
    
    if file dist/voxbridge-gui | grep -q "ELF 64-bit"; then
        print_status "GUI is a valid 64-bit ELF binary"
        ((TESTS_PASSED++))
    else
        print_error "GUI is not a valid 64-bit ELF binary"
        ((TESTS_FAILED++))
    fi
    
elif [[ "$PLATFORM" == "Darwin" ]]; then
    if file dist/voxbridge | grep -q "Mach-O 64-bit"; then
        print_status "CLI is a valid 64-bit Mach-O binary"
        ((TESTS_PASSED++))
    else
        print_error "CLI is not a valid 64-bit Mach-O binary"
        ((TESTS_FAILED++))
    fi
    
    if file dist/voxbridge-gui | grep -q "Mach-O 64-bit"; then
        print_status "GUI is a valid 64-bit Mach-O binary"
        ((TESTS_PASSED++))
    else
        print_error "GUI is not a valid 64-bit Mach-O binary"
        ((TESTS_FAILED++))
    fi
    
elif [[ "$PLATFORM" == "MINGW"* ]] || [[ "$PLATFORM" == "CYGWIN"* ]] || [[ "$PLATFORM" == "MSYS"* ]]; then
    if file dist/voxbridge.exe | grep -q "PE32+"; then
        print_status "CLI is a valid 64-bit PE executable"
        ((TESTS_PASSED++))
    else
        print_error "CLI is not a valid 64-bit PE executable"
        ((TESTS_FAILED++))
    fi
    
    if file dist/voxbridge-gui.exe | grep -q "PE32+"; then
        print_status "GUI is a valid 64-bit PE executable"
        ((TESTS_PASSED++))
    else
        print_error "GUI is not a valid 64-bit PE executable"
        ((TESTS_FAILED++))
    fi
fi

# Test with sample file if available
if [[ -f "examples/input/4_cubes.glb" ]]; then
    print_info "Testing with sample file..."
    
    # Create test output directory
    mkdir -p test_output
    
    if [[ "$PLATFORM" == "MINGW"* ]] || [[ "$PLATFORM" == "CYGWIN"* ]] || [[ "$PLATFORM" == "MSYS"* ]]; then
        test_command "CLI sample conversion" "dist\\voxbridge.exe convert --input examples/input/4_cubes.glb --target unity --output test_output/sample"
    else
        test_command "CLI sample conversion" "./dist/voxbridge convert --input examples/input/4_cubes.glb --target unity --output test_output/sample"
    fi
    
    # Check if output was created
    if [[ -f "test_output/sample.zip" ]] || [[ -f "test_output/sample.gltf" ]]; then
        print_status "Sample conversion created output file"
        ((TESTS_PASSED++))
    else
        print_error "Sample conversion did not create output file"
        ((TESTS_FAILED++))
    fi
    
    # Clean up test output
    rm -rf test_output
fi

# Test package extraction and execution
print_info "Testing package extraction and execution..."

if [[ -f "release_builds/voxbridge-linux.tar.gz" ]] || [[ -f "release_builds/voxbridge-macos.tar.gz" ]] || [[ -f "release_builds/voxbridge-windows.zip" ]]; then
    # Create test directory
    mkdir -p test_package
    cd test_package
    
    if [[ "$PLATFORM" == "Linux" ]] && [[ -f "../release_builds/voxbridge-linux.tar.gz" ]]; then
        print_info "Testing Linux package..."
        tar -xzf ../release_builds/voxbridge-linux.tar.gz
        
        if [[ -f "voxbridge" ]] && [[ -f "voxbridge-gui" ]]; then
            chmod +x voxbridge voxbridge-gui
            test_command "Package CLI --help" "./voxbridge --help"
            test_command "Package GUI startup" "timeout 5s ./voxbridge-gui --help"
            print_status "Linux package test passed"
            ((TESTS_PASSED++))
        else
            print_error "Linux package missing executables"
            ((TESTS_FAILED++))
        fi
        
    elif [[ "$PLATFORM" == "Darwin" ]] && [[ -f "../release_builds/voxbridge-macos.tar.gz" ]]; then
        print_info "Testing macOS package..."
        tar -xzf ../release_builds/voxbridge-macos.tar.gz
        
        if [[ -f "voxbridge" ]] && [[ -f "voxbridge-gui" ]]; then
            chmod +x voxbridge voxbridge-gui
            test_command "Package CLI --help" "./voxbridge --help"
            test_command "Package GUI startup" "timeout 5s ./voxbridge-gui --help"
            print_status "macOS package test passed"
            ((TESTS_PASSED++))
        else
            print_error "macOS package missing executables"
            ((TESTS_FAILED++))
        fi
        
    elif [[ "$PLATFORM" == "MINGW"* ]] || [[ "$PLATFORM" == "CYGWIN"* ]] || [[ "$PLATFORM" == "MSYS"* ]]; then
        if [[ -f "../release_builds/voxbridge-windows.zip" ]]; then
            print_info "Testing Windows package..."
            unzip -q ../release_builds/voxbridge-windows.zip
            
            if [[ -f "voxbridge.exe" ]] && [[ -f "voxbridge-gui.exe" ]]; then
                test_command "Package CLI --help" ".\\voxbridge.exe --help"
                test_command "Package GUI startup" "timeout 5s .\\voxbridge-gui.exe --help"
                print_status "Windows package test passed"
                ((TESTS_PASSED++))
            else
                print_error "Windows package missing executables"
                ((TESTS_FAILED++))
            fi
        fi
    fi
    
    cd ..
    rm -rf test_package
else
    print_warning "No release packages found. Skipping package tests."
fi

# Display final results
echo ""
echo "=========================================="
echo "Test Results Summary"
echo "=========================================="
echo "Tests Passed: $TESTS_PASSED"
echo "Tests Failed: $TESTS_FAILED"
echo ""

if [[ $TESTS_FAILED -eq 0 ]]; then
    print_status "All tests passed! Executables are working correctly."
    exit 0
else
    print_error "Some tests failed. Please check the issues above."
    exit 1
fi
