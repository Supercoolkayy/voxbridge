# GitHub Release & PyPI Publishing Checklist

## Pre-Release Checklist

### **Code Quality**

- [x] All linter errors resolved
- [x] No TODO comments in main files
- [x] No placeholder modules
- [x] Professional documentation (no emojis)
- [x] Consistent code formatting

### **Package Configuration**

- [x] `pyproject.toml` properly configured
- [x] Entry points for `voxbridge` and `voxbridge-gui`
- [x] Dependencies correctly specified
- [x] Version set to 1.0.0
- [x] Metadata complete (author, email, URLs)

### **Documentation**

- [x] `README.md` updated with installation instructions
- [x] Usage examples provided
- [x] Professional tone throughout
- [x] Correct GitHub links
- [x] License file present

### **Testing**

- [x] CLI commands work: `voxbridge --help`
- [x] Subcommands functional: `convert`, `doctor`, `batch`, `help`
- [x] GUI command available: `voxbridge-gui`
- [x] Package installs via `pip install -e .`

## Release Process

### 1. **Final Testing (WSL Ubuntu)**

```bash
# Switch to WSL
wsl
cd /home/emmzycode/voxbridge

# Test CLI
voxbridge --help
voxbridge help
voxbridge doctor
voxbridge convert --help
voxbridge batch --help

# Test GUI (if tkinter installed)
voxbridge-gui
```

### 2. **Build Package**

```bash
# Build distribution
bash scripts/build_cli.sh

# Verify build artifacts
ls -la dist/
# Should show: voxbridge-1.0.0-py3-none-any.whl and voxbridge-1.0.0.tar.gz
```

### 3. **Local Installation Test**

```bash
# Test local installation
pip install -e .
voxbridge --help
voxbridge doctor
```

### 4. **GitHub Repository Preparation**

```bash
# Check git status
git status

# Add all files
git add .

# Commit with descriptive message
git commit -m "v1.0.0: Universal CLI with enhanced help and GUI

- Enhanced CLI with subcommands: convert, doctor, batch, help
- Rich colored output and comprehensive help
- Tkinter GUI interface
- Automated PyPI publishing
- Professional documentation"

# Push to main branch
git push origin main
```

### 5. **Create GitHub Release**

```bash
# Create and push tag
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0
```

### 6. **GitHub Actions Automation**

- [x] `.github/workflows/release.yml` configured
- [x] PyPI API token set in repository secrets
- [x] Workflow triggers on tag push
- [x] Automatic PyPI publishing

### 7. **PyPI Publishing**

The GitHub Actions workflow will automatically:

- Build the package
- Run tests
- Publish to PyPI
- Create GitHub Release with artifacts

### 8. **Post-Release Verification**

#### Test PyPI Installation

```bash
# Create fresh environment
python -m venv test_env
source test_env/bin/activate

# Install from PyPI
pip install voxbridge

# Test commands
voxbridge --help
voxbridge doctor
voxbridge convert --help
```

#### Test GUI Installation

```bash
# Install tkinter if needed
sudo apt install python3-tk

# Test GUI
voxbridge-gui
```

## Public Installation Instructions

### Quick Install

```bash
pip install voxbridge
```

### With GUI Support

```bash
# Install package
pip install voxbridge

# Install GUI dependencies (Ubuntu/Debian)
sudo apt install python3-tk

# Run GUI
voxbridge-gui
```

### CLI Usage

```bash
# Get help
voxbridge --help
voxbridge help

# Convert files
voxbridge convert --input model.glb --target unity
voxbridge convert --input model.glb --target roblox --optimize-mesh

# Batch processing
voxbridge batch ./input_folder ./output_folder --target unity

# System diagnostics
voxbridge doctor
```

## Marketing & Documentation

### GitHub Repository

- [x] Professional README with installation instructions
- [x] Usage examples and screenshots
- [x] Feature list and capabilities
- [x] Links to documentation

### PyPI Page

- [x] Package description
- [x] Installation instructions
- [x] Usage examples
- [x] Project URLs (GitHub, documentation)

### Documentation

- [x] README.md with comprehensive guide
- [x] Installation instructions
- [x] Usage examples
- [x] Troubleshooting section

## Success Criteria

### **Release Complete When:**

- [ ] Package published to PyPI
- [ ] GitHub Release created with v1.0.0 tag
- [ ] Installation works: `pip install voxbridge`
- [ ] CLI commands work: `voxbridge --help`
- [ ] GUI launches: `voxbridge-gui`
- [ ] Documentation accessible
- [ ] Issues/PRs enabled on GitHub

### **Metrics to Track**

- PyPI download statistics
- GitHub repository stars/forks
- User feedback and issues
- Documentation page visits

## Troubleshooting

### Common Issues

1. **PyPI API Token**: Ensure `PYPI_API_TOKEN` is set in GitHub repository secrets
2. **Build Failures**: Check GitHub Actions logs for build errors
3. **Import Errors**: Verify all dependencies are correctly specified
4. **GUI Issues**: Ensure tkinter is installed on target systems

### Support

- GitHub Issues: https://github.com/Supercoolkayy/voxbridge/issues
- Documentation: https://supercoolkayy.github.io/voxbridge/
- Email: team@dappsoverapps.com
