# EVE Frontier Datasets

Supplying EVE Frontier Datasets for analysis and visualization using Jupyter Notebooks.

## Features

- 🐍 **Python 3.12** - Modern Python version with latest features
- 📓 **Jupyter Lab & Notebook** - Interactive analysis and visualization
- 📦 **Poetry** - Dependency management and virtual environments
- 🎯 **CLI Tool** - Convenient command-line interface for common tasks
- 📊 **Data Science Stack** - Pre-configured with pandas, numpy, matplotlib, seaborn, and plotly
- 🔧 **Development Tools** - pytest, black, flake8, mypy, and isort included

## Prerequisites

- **Python 3.12+** - Download from [python.org](https://www.python.org/)
- **Poetry** - Install from [python-poetry.org](https://python-poetry.org/docs/#installing-with-pipx) (recommended via pipx)

### Create a Virtual Environment

```sh
python -m venv .venv
```

### Installing Poetry

```sh
# Using pipx (recommended)
pipx install poetry

# Or using pip
pip install poetry
```

## Quick Start

### 1. Install Dependencies

```sh
poetry install
```

This will:

- Create a virtual environment
- Install all dependencies (Jupyter, pandas, numpy, matplotlib, etc.)
- Install development dependencies

### 2. Start Jupyter Lab

```powershell
poetry run efds lab
```

### 3. Create a New Notebook

```powershell
poetry run efds notebook new my_analysis
```

This creates a new notebook at `notebooks/my_analysis.ipynb` with starter code.

## CLI Commands

The project includes a custom CLI tool (`efds`) for common tasks:

```powershell
# Start Jupyter Lab
poetry run efds lab

# Start Jupyter Notebook
poetry run efds notebook

# Create a new notebook
poetry run efds notebook new <name>

# List all notebooks
poetry run efds notebook list

# Install dependencies
poetry run efds install

# Update dependencies
poetry run efds update

# Display project information
poetry run efds info
```

### Examples

```powershell
# Create and work on a new analysis
poetry run efds notebook new datasets_analysis
poetry run efds lab

# List all your notebooks
poetry run efds notebook list

# Update all dependencies to latest versions
poetry run efds update
```

## Project Structure

```
evefrontier_datasets/
├── README.md                    # This file
├── LICENSE                      # MIT License
├── pyproject.toml              # Poetry configuration
├── notebooks/                  # Jupyter notebooks
│   └── .gitkeep
└── evefrontier_datasets/       # Python package
    ├── __init__.py
    └── cli.py                  # CLI implementation
```

## Available Packages

### Data Science & Analysis

- **pandas** - Data manipulation and analysis
- **numpy** - Numerical computing
- **polars** - Fast dataframe library
- **plotly** - Interactive visualizations

### Visualization

- **matplotlib** - Static, animated, and interactive plotting
- **seaborn** - Statistical data visualization

### Development

- **pytest** - Testing framework
- **black** - Code formatter
- **flake8** - Linting
- **mypy** - Static type checker
- **isort** - Import sorting

## Development

### Code Formatting

```powershell
poetry run black evefrontier_datasets/
poetry run isort evefrontier_datasets/
```

### Linting

```powershell
poetry run flake8 evefrontier_datasets/
poetry run mypy evefrontier_datasets/
```

### Running Tests

```powershell
poetry run pytest
```

## Adding New Dependencies

To add a new package:

```powershell
poetry add <package-name>
```

For development dependencies only:

```powershell
poetry add --group dev <package-name>
```

## Updating Dependencies

```powershell
poetry update
```

Or use the CLI:

```powershell
poetry run efds update
```

## Tips for Working with Notebooks

1. **Keep notebooks organized** - Use the `notebooks/` directory
2. **Use the CLI** - Create notebooks with `poetry run efds notebook new <name>`
3. **Version control** - Notebooks are tracked in git by default
4. **Restart kernels** - If you modify code, restart the kernel for changes to take effect

## Troubleshooting

### "Poetry not found"

Make sure Poetry is installed and in your PATH:

```powershell
poetry --version
```

### "Jupyter not found"

Run `poetry install` to ensure all dependencies are installed:

```powershell
poetry install
```

### Virtual environment issues

To activate the Poetry virtual environment directly:

```powershell
poetry shell
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Author

Scetrov
