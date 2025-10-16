# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

EVE Frontier Datasets is a Python 3.12 data analysis project using Poetry for dependency management and Jupyter Lab/Notebook for interactive analysis. The project includes a custom CLI tool (`efds`) for managing notebooks and dependencies.

## Essential Commands

### Development Environment Setup
```powershell
# Install dependencies
poetry install

# Activate virtual environment  
poetry shell
```

### Custom CLI Tool (`efds`)
```powershell
# Start Jupyter Lab (recommended)
poetry run efds lab

# Start Jupyter Notebook  
poetry run efds notebook

# Create new notebook with starter template
poetry run efds notebook new <name>

# List all notebooks
poetry run efds notebook list

# Install/update dependencies
poetry run efds install
poetry run efds update

# Project information
poetry run efds info
```

### Code Quality & Testing
```powershell
# Format code
poetry run black evefrontier_datasets/
poetry run isort evefrontier_datasets/

# Lint code  
poetry run flake8 evefrontier_datasets/
poetry run mypy evefrontier_datasets/

# Run tests
poetry run pytest
poetry run pytest -v
poetry run pytest --cov=evefrontier_datasets
```

## Architecture & Structure

### Package Layout
- `evefrontier_datasets/` - Main Python package containing CLI and utilities
- `notebooks/` - Jupyter notebooks (created on demand via CLI)
- `pyproject.toml` - Poetry configuration with dependencies and tools
- `.github/copilot-instructions.md` - Comprehensive development guidelines

### CLI Architecture  
The CLI (`evefrontier_datasets/cli.py`) uses argparse with subcommands:
- `lab` - Launches Jupyter Lab
- `notebook` - Manages notebooks (list, new, start)
- `install/update` - Dependency management 
- `info` - Project information

Each command is implemented as a separate function (`cmd_*`) returning exit codes.

### Data Science Stack
Pre-configured with:
- **Analysis**: pandas, numpy, polars
- **Visualization**: matplotlib, seaborn, plotly  
- **Environment**: Jupyter Lab/Notebook, IPython
- **Development**: pytest, black, flake8, mypy, isort, pylint

## Code Standards

### Formatting & Style
- **Black**: 100 character line length, Python 3.12 target
- **isort**: Black-compatible profile with line_length=100
- **Type hints**: Encouraged but not strictly enforced (mypy configured)
- **Docstrings**: Google-style for public functions

### Python Patterns
- Use modern Python 3.12+ features (walrus operator, pattern matching, `|` unions)
- Snake_case for modules/functions, PascalCase for classes, UPPER_SNAKE_CASE for constants
- Pathlib over os.path, f-strings over format(), type hints for signatures

### Jupyter Guidelines
- First cell: imports and configuration
- Use descriptive markdown headers between code sections
- Include starter template: pandas, numpy, matplotlib, seaborn setup
- Create notebooks via `poetry run efds notebook new <name>`

## Dependencies Management

### Adding Packages
```powershell
# Runtime dependencies
poetry add <package>

# Development dependencies  
poetry add --group dev <package>
```

### Preferred Libraries
- **Data**: Use pandas as primary, polars for performance-critical tasks
- **Visualization**: matplotlib + seaborn for statistical plots, plotly for interactive
- **Testing**: pytest with coverage extensions
- **Quality**: Stick to pre-configured black, flake8, mypy, isort

## Development Workflow

1. Create virtual environment: `poetry install`
2. Start development: `poetry run efds lab`  
3. Create notebooks: `poetry run efds notebook new <analysis_name>`
4. Format code: `poetry run black evefrontier_datasets/`
5. Run quality checks: `poetry run flake8 evefrontier_datasets/`
6. Test: `poetry run pytest`

## Important Notes

- **Windows Environment**: Project configured for PowerShell on Windows
- **Python Version**: Strict requirement for Python 3.12+
- **CLI Entry Point**: All tasks should use `poetry run efds <command>` pattern
- **Notebook Management**: Always use CLI for notebook creation (includes proper templates)
- **Poetry Lock**: Commit both `pyproject.toml` and `poetry.lock` for dependency changes