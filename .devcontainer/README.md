# 🐳 Dev Container Guide

## Overview

The project is now configured with a **Dev Container** that provides a complete development environment with Python 3.12, Poetry, and Jupyter Lab pre-configured.

## Prerequisites

### Required
- **Visual Studio Code** - Download from [code.visualstudio.com](https://code.visualstudio.com/)
- **Dev Containers Extension** - Install from VS Code Extensions
- **Docker Desktop** - Download from [docker.com](https://www.docker.com/products/docker-desktop)

### Optional
- **Git** - For version control (included in container)

## Quick Start

### 1. Open Project in Dev Container

1. Open the project folder in VS Code:
   ```powershell
   code c:\source\evefrontier_datasets
   ```

2. Click the **Dev Containers** icon (bottom-left corner) or press `Ctrl+Shift+P`

3. Select **"Reopen in Container"** or **"Dev Containers: Reopen Folder in Container"**

4. Wait for the container to build and start (~2-5 minutes on first run)

### 2. Launch Jupyter Lab

Once the container is ready, open the integrated terminal in VS Code and run:

```bash
poetry run efds lab
```

Jupyter Lab will start and you'll see a URL like: `http://localhost:8888/?token=...`

Click the URL or copy it to your browser to access Jupyter Lab.

### 3. Start Analyzing!

- Create a new notebook: `poetry run efds notebook new analysis`
- Open the sample notebook: `notebooks/sample_analysis.ipynb`
- Start writing Python code!

## Container Features

### ✅ Installed

- **Python 3.12** - Latest Python version
- **Poetry** - Dependency management
- **Jupyter Lab** - Interactive notebooks
- **All Data Science Packages** - pandas, numpy, matplotlib, plotly, seaborn
- **Development Tools** - pytest, black, flake8, mypy, isort
- **VS Code Extensions** - Python, Jupyter, Pylance, Ruff, Black formatter

### ✅ Pre-configured

- **Port Forwarding** - Jupyter Lab on port 8888
- **Volume Mounting** - Workspace synced with container
- **Environment Variables** - Jupyter enabled by default
- **Python Path** - Automatically set to virtual environment

## Available Commands

### Inside the Container

```bash
# Show help
poetry run efds --help

# Start Jupyter Lab
poetry run efds lab

# Start Jupyter Notebook (classic interface)
poetry run efds notebook

# Create new notebook
poetry run efds notebook new <name>

# List all notebooks
poetry run efds notebook list

# Format code
poetry run black evefrontier_datasets/

# Run tests
poetry run pytest

# Show project info
poetry run efds info
```

## VS Code Integration

### Python Extension Features (Auto-configured)

- ✅ **IntelliSense** - Code completion and hints
- ✅ **Linting** - flake8 checks on the fly
- ✅ **Formatting** - Black formatter (Ctrl+Shift+F)
- ✅ **Testing** - Integrated pytest runner
- ✅ **Debugging** - Debug Python scripts

### Jupyter Extension Features

- ✅ **Notebook Editor** - Edit `.ipynb` files directly
- ✅ **Variable Explorer** - Inspect variables
- ✅ **Plot Viewer** - Display visualizations
- ✅ **Export** - Convert notebooks to other formats

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+Shift+F` | Format Python code with Black |
| `Ctrl+Shift+P` > `Python: Lint` | Run linting checks |
| `Ctrl+Shift+P` > `Jupyter: Create` | Create new notebook |
| `Ctrl+Shift+P` > `Reopen in Container` | Reopen in dev container |

## Accessing Jupyter Lab

### From Container Terminal
```bash
poetry run efds lab
```
- Opens on `http://localhost:8888`
- VS Code port forwarding shows the URL

### Direct from Browser
1. Run `poetry run efds lab` in container terminal
2. Copy the URL with token from terminal output
3. Paste into your browser

### VS Code Integrated Browser
1. Open terminal in VS Code
2. Run `poetry run efds lab`
3. VS Code shows a notification "Port 8888 is now open"
4. Click "Open in Browser"

## Port Forwarding

### Configured Ports

| Port | Service | Auto-forward |
|------|---------|--------------|
| 8888 | Jupyter Lab | Yes |
| 8889 | Jupyter Notebook (alt) | Yes |
| 8890 | Alternative/Custom | Yes |

### Using Alternative Ports

If port 8888 is busy, Jupyter will auto-select the next available port:

```bash
# Jupyter Lab on alternate port
poetry run jupyter lab --port 8889
```

## File Synchronization

### Container ↔ Host

- ✅ All files in `/workspace` are synced with your local folder
- ✅ Changes are reflected instantly in both directions
- ✅ Notebooks created in container appear in VS Code
- ✅ Local file edits immediately available in container

### .venv Directory

- ✅ Virtual environment is created in `/workspace/.venv`
- ✅ Synced to host machine
- ✅ Can be cached for faster rebuilds (add to `.devcontainer/.dockerignore`)

## Rebuilding the Container

### When to Rebuild

- After modifying `pyproject.toml` (dependencies changed)
- After modifying `.devcontainer/devcontainer.json`
- If container becomes corrupted
- To pick up base image updates

### How to Rebuild

**Option 1: VS Code Command Palette**
```
Ctrl+Shift+P > "Dev Containers: Rebuild Container"
```

**Option 2: VS Code UI**
- Click the Dev Containers icon (bottom-left)
- Select "Rebuild Container"

**Option 3: Command Line**
```bash
# Close VS Code first
docker system prune -a
code c:\source\evefrontier_datasets
# Then reopen in container
```

## Troubleshooting

### "Dev Container not available"
- Install "Dev Containers" extension in VS Code
- Make sure Docker Desktop is running
- Reload VS Code window

### "Container build failed"
- Check Docker Desktop is running
- Delete container: `Dev Containers: Delete Container`
- Rebuild: `Dev Containers: Rebuild Container`
- Check internet connection (downloading base image)

### "Port 8888 already in use"
- Close other Jupyter instances
- Use alternative port: `poetry run jupyter lab --port 8889`
- Rebuild container: `Dev Containers: Rebuild Container`

### "Can't see changes in container"
- Check file is saved (`Ctrl+S`)
- Wait a moment for sync (usually instant)
- Verify path starts with `/workspace/`

### "Python extension not working"
- Reload window: `Ctrl+Shift+P` > "Reloading Window"
- Check Python path: `poetry run python -c "import sys; print(sys.executable)"`
- Verify virtual environment: `poetry env info`

### "Jupyter Lab won't start"
- Check dependencies: `poetry install`
- Verify Jupyter: `poetry run jupyter --version`
- Check ports: `netstat -ano | findstr :8888`
- Try alternate port: `poetry run jupyter lab --port 8889`

## Advanced Configuration

### Add Additional Extensions

Edit `.devcontainer/devcontainer.json`, in the `extensions` array add:

```json
"customizations": {
	"vscode": {
		"extensions": [
			"ms-python.python",
			// ... other extensions ...
			"ms-vscode.makefile-tools",  // Example: Add Makefile support
			"GitHub.github-vscode-theme"  // Example: Add theme
		]
	}
}
```

Then rebuild: `Dev Containers: Rebuild Container`

### Add System Packages

Create `.devcontainer/Dockerfile` if you need system-level packages:

```dockerfile
FROM mcr.microsoft.com/devcontainers/python:1-3.12-bookworm

# Install additional system packages
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*
```

Update `devcontainer.json`:
```json
"build": {
	"dockerfile": "Dockerfile"
}
```

### Customize Post-Create Commands

Modify `postCreateCommand` in `.devcontainer/devcontainer.json`:

```json
"postCreateCommand": "your-command-here && poetry install"
```

## Performance Tips

### Faster Rebuilds

1. **Cache .venv** - Add to `.devcontainer/.dockerignore`:
   ```
   .venv
   __pycache__
   *.pyc
   .pytest_cache
   ```

2. **Layer Caching** - Docker caches layers; changes to `pyproject.toml` invalidate cache

3. **Use Dev Container CLI** - Faster local development without container rebuild

### Reduce Image Size

- Base image is ~500MB
- Virtual environment adds ~200-300MB
- Total container size: ~1-2GB

## Connecting Other Tools

### Jupyter Notebooks in VS Code

Edit notebooks directly in VS Code with full Jupyter functionality:

1. Open any `.ipynb` file
2. Edit cells with IntelliSense
3. Run cells and see outputs
4. Use integrated debugging

### Terminal Integration

All terminal commands use container Python:

```bash
python --version        # Shows: Python 3.12.x
pip list               # Shows container packages
poetry show            # Shows project dependencies
jupyter --version      # Shows Jupyter Lab version
```

## Exiting the Container

### Return to Local Development

1. Click Dev Containers icon (bottom-left)
2. Select **"Reopen Folder Locally"**
3. Or: `Ctrl+Shift+P` > "Dev Containers: Reopen Folder Locally"

Your local Python environment will be used instead of container.

### Switching Between Environments

Easily switch by reopening in/out of container using the Dev Containers button.

## Benefits of Dev Containers

✅ **Consistent Environment** - Same setup for all developers
✅ **Reproducible** - Exactly Python 3.12 with specified packages
✅ **Isolated** - Doesn't affect your system Python
✅ **Easy Cleanup** - Delete container and everything is gone
✅ **Team Friendly** - Same environment for all team members
✅ **CI/CD Ready** - Can use same Dockerfile for deployment

## Files Modified

- ✅ `.devcontainer/devcontainer.json` - Complete configuration

## Next Steps

1. **Install Prerequisites:**
   - VS Code
   - Dev Containers Extension
   - Docker Desktop

2. **Open in Container:**
   - Open project in VS Code
   - Click Dev Containers icon
   - Select "Reopen in Container"

3. **Launch Jupyter Lab:**
   - Run: `poetry run efds lab`
   - Open the URL in browser

4. **Start Analyzing:**
   - Create notebooks
   - Write Python code
   - Use all VS Code features!

---

## Quick Reference

| Task | Command |
|------|---------|
| Reopen in container | `Ctrl+Shift+P` > "Reopen in Container" |
| Rebuild container | `Ctrl+Shift+P` > "Rebuild Container" |
| Start Jupyter Lab | `poetry run efds lab` |
| Create notebook | `poetry run efds notebook new <name>` |
| Format code | `Ctrl+Shift+F` |
| Run tests | `poetry run pytest` |
| Check linting | `poetry run flake8 evefrontier_datasets/` |

---

**Container Configuration:** `.devcontainer/devcontainer.json`
**Base Image:** `mcr.microsoft.com/devcontainers/python:1-3.12-bookworm`
**Python Version:** 3.12
**Jupyter Lab:** Configured with port forwarding

Happy containerized development! 🐳✨
