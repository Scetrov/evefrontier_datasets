# GitHub Copilot Instructions for EVE Frontier Datasets

This file contains instructions to guide GitHub Copilot when generating code for this project.

## Project Overview

This is a Python data analysis project using:

- **Python 3.12+** as the runtime
- **Poetry** for dependency management
- **Jupyter Lab/Notebook** for interactive analysis
- **Data science stack**: pandas, numpy, matplotlib, seaborn, plotly
- **Development tools**: pytest, black, flake8, mypy, isort

## Code Style & Standards

### Python Version

- Target: Python 3.12+
- Use modern Python features (walrus operator, structural pattern matching, etc.)
- Avoid deprecated patterns and older syntax

### Code Formatting

- Use **Black** for formatting with 100 character line length
- Use **isort** for import sorting (Black-compatible profile)
- All code should be auto-formatted with: `poetry run black <file>`

### Linting & Type Checking

- Follow **flake8** linting standards
- Use **mypy** for type hints (not strict, but encouraged)
- Avoid ignoring type checks without justification
- Document type hints for public functions

### Import Organization

- Follow isort conventions
- Group: future → stdlib → third-party → local
- One import per line for clarity
- Keep imports alphabetically sorted within groups

## Project Structure

```
evefrontier_datasets/
├── evefrontier_datasets/       # Main Python package
│   ├── __init__.py            # Package initialization
│   ├── cli.py                 # CLI tool implementation
│   └── [future modules]       # Add new modules here
├── notebooks/                 # Jupyter notebooks
│   ├── sample_analysis.ipynb  # Example (reference, don't modify)
│   └── [user notebooks]       # Add new analysis notebooks here
├── tests/                     # Unit tests (create if needed)
│   └── [test files]          # Add tests here
└── pyproject.toml            # Poetry configuration

```

## Naming Conventions

### Modules & Packages

- Use **snake_case** for module names
- Meaningful, descriptive names
- Example: `data_loader.py`, `analysis_utils.py`

### Functions & Variables

- **snake_case** for functions and variables
- Descriptive names that indicate purpose
- Example: `load_data()`, `calculate_statistics()`

### Classes

- **PascalCase** for class names
- Example: `DataProcessor`, `AnalysisReport`

### Constants

- **UPPER_SNAKE_CASE** for module-level constants
- Example: `MAX_RETRIES = 3`, `DEFAULT_TIMEOUT = 30`

### Jupyter Notebooks

- **snake_case_with_underscores** for notebook names
- Descriptive purpose in name
- Example: `data_exploration.ipynb`, `statistical_analysis.ipynb`

## Documentation Standards

### Docstrings

- Use Google-style docstrings for all public functions/classes
- Include Args, Returns, Raises, Examples sections
- Example:

```python
def calculate_mean(data: list[float]) -> float:
    """Calculate the arithmetic mean of data values.

    Args:
        data: A list of numeric values.

    Returns:
        The arithmetic mean as a float.

    Raises:
        ValueError: If data list is empty.

    Example:
        >>> calculate_mean([1, 2, 3, 4, 5])
        3.0
    """
```

### Comments

- Explain **why**, not **what** (code should be self-explanatory)
- Use `#` for inline comments
- Use `"""` for block documentation
- Keep comments concise and clear

### Type Hints

- Use type hints for function signatures
- Be specific: `list[str]` instead of `list`
- Use `Optional[T]` for nullable values
- Use `|` operator for unions (Python 3.10+)

## CLI Tool (`cli.py`)

When modifying the CLI tool:

### Command Structure

- Use `argparse` for CLI argument parsing
- Follow the existing pattern in `cli.py`
- Add descriptive help text for each command
- Use consistent naming for subcommands

### Return Codes

- Return 0 for success
- Return non-zero for errors
- Document expected return codes

### User Output

- Use emoji for visual clarity (consistent with existing code)
- Print to stdout for normal output
- Print to stderr for errors
- Make output machine-parseable when needed

## Testing

### Test Organization

- Create `tests/` directory if adding tests
- Use **pytest** as the testing framework
- File naming: `test_<module>.py`
- Function naming: `test_<functionality>()`

### Test Coverage

- Write tests for public APIs
- Aim for meaningful coverage, not 100%
- Test edge cases and error conditions
- Use fixtures for common setup

### Running Tests

```bash
poetry run pytest
poetry run pytest -v
poetry run pytest --cov=evefrontier_datasets
```

## Dependencies

### Adding New Packages

- Use `poetry add <package>` for runtime dependencies
- Use `poetry add --group dev <package>` for dev dependencies
- Update version constraints in `pyproject.toml` if needed
- Document why each new dependency is needed

### Preferred Libraries

- **Data Processing**: pandas, polars, numpy
- **Visualization**: matplotlib, seaborn, plotly
- **Scientific**: scipy, scikit-learn (when needed)
- **Testing**: pytest, pytest-cov
- **Quality**: black, flake8, mypy, isort

## Jupyter Notebooks

### Notebook Best Practices

- Use descriptive cell markdown headers
- One major task per cell when possible
- Include outputs and visualizations
- Add markdown explanations between code cells
- Keep notebooks organized and documented

### Cell Structure

1. Markdown header
2. Imports (in first code cell)
3. Configuration/Setup
4. Data Loading
5. Processing/Analysis
6. Visualization/Results
7. Conclusions/Notes

### Clearing Before Commit

- Use nbstripout or manually clear outputs when committing
- Keep notebooks lightweight
- Strip sensitive data before sharing

## Version Control

### Commit Messages

- Use imperative mood: "Add feature" not "Added feature"
- First line: 50 characters max, describe what changed
- Body: Explain why, not what (if needed)
- Example: `Add data validation module for CSV imports`

### Git Workflow

- Keep commits focused and atomic
- Update `poetry.lock` when changing dependencies
- Use descriptive branch names: `feature/xyz`, `fix/issue-123`
- Write clear pull request descriptions

## Environment Variables

### Configuration

- Use `.env` file for local secrets (never commit)
- Copy from `.env.example` template
- Document all env vars in `.env.example`
- Use `python-dotenv` to load environment

## Error Handling

### Best Practices

- Use specific exception types
- Provide helpful error messages
- Log errors appropriately
- Handle edge cases gracefully

### Exception Structure

```python
try:
    # operation
except SpecificError as e:
    logger.error(f"Failed to process: {e}")
    raise ValueError("Descriptive error message") from e
```

## CLI Application Guidelines

When working with the CLI in `evefrontier_datasets/cli.py`:

### New Commands

- Keep commands focused and single-purpose
- Use subparsers for command groups
- Provide clear help text
- Return appropriate exit codes

### User Experience

- Provide progress feedback for long operations
- Use colors/emoji for status messages
- Make output human-readable
- Include usage examples in help

## Jupyter Integration

When working with Jupyter:

### IPython Compatibility

- Code should work in Jupyter cells
- Avoid hard dependencies on Jupyter features
- Use standard Python patterns

### Display Output

- Use `print()` for standard output
- Use `display()` from IPython for rich output
- Matplotlib integrates automatically

## Performance Considerations

### Optimization

- Profile code before optimizing
- Use vectorized operations with numpy/pandas
- Prefer list comprehensions over loops
- Cache expensive computations

### Memory Management

- Be aware of memory when loading large datasets
- Use generators for large data streams
- Clean up temporary objects in notebooks

## Security

### Best Practices

- Never commit secrets or API keys
- Use environment variables for sensitive config
- Validate and sanitize user inputs
- Use HTTPS for external data sources

### Dependencies

- Keep dependencies up to date
- Monitor for security vulnerabilities
- Review new dependency licenses

## Code Examples

### Good Python Pattern

```python
"""Module for data processing utilities."""

from pathlib import Path
import logging

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

class DataProcessor:
    """Process and validate datasets."""

    def __init__(self, data_path: str | Path):
        """Initialize with data path."""
        self.data_path = Path(data_path)

    def load_data(self) -> pd.DataFrame:
        """Load data from CSV file."""
        try:
            return pd.read_csv(self.data_path)
        except FileNotFoundError as e:
            logger.error(f"Data file not found: {self.data_path}")
            raise ValueError(f"Cannot find data at {self.data_path}") from e
```

### Good Jupyter Pattern

```python
# In first cell
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Configuration
plt.style.use('seaborn-v0_8-darkgrid')
pd.set_option('display.max_columns', None)

# Load data
df = pd.read_csv('data.csv')
print(f"Loaded {len(df)} rows")

# Analysis
results = df.groupby('category')['value'].mean()
results.plot(kind='bar')
```

## Specific Guidance

### For CLI Tool (`cli.py`)

- Maintain existing command structure
- Add new commands as new functions
- Update argument parser with new commands
- Test with `poetry run efds <command>`
- Keep help text updated and clear

### For Data Analysis Code

- Use pandas DataFrames as primary data structure
- Document data assumptions
- Include data validation
- Provide summary statistics

### For Notebooks

- Make them reproducible (include all imports)
- Add markdown explanations
- Use consistent styling for plots
- Version control outputs sparingly

## Deployment & Distribution

### Package Distribution

- Update version in `pyproject.toml`
- Update `poetry.lock` file
- Create git tags for releases
- Document breaking changes in CHANGELOG

### Testing Before Release

```bash
poetry run black evefrontier_datasets/
poetry run isort evefrontier_datasets/
poetry run flake8 evefrontier_datasets/
poetry run mypy evefrontier_datasets/
poetry run pytest
```

## Common Tasks

### Add New Feature

1. Create new file in `evefrontier_datasets/`
2. Follow naming conventions
3. Add docstrings and type hints
4. Write tests if applicable
5. Format with black/isort
6. Update imports in `__init__.py`

### Fix a Bug

1. Write test that demonstrates bug
2. Fix the bug
3. Verify test passes
4. Run full test suite
5. Commit with clear message

### Update Dependencies

1. Run `poetry add/remove <package>`
2. Test changes thoroughly
3. Commit both `pyproject.toml` and `poetry.lock`
4. Update documentation if needed

## Useful Commands

```bash
# Format and lint
poetry run black evefrontier_datasets/
poetry run isort evefrontier_datasets/
poetry run flake8 evefrontier_datasets/
poetry run mypy evefrontier_datasets/

# Testing
poetry run pytest
poetry run pytest -v
poetry run pytest --cov

# Jupyter
poetry run efds lab
poetry run efds notebook

# Package management
poetry install
poetry update
poetry add <package>
```

## Questions & Clarifications

When in doubt:

- Check existing code for patterns
- Refer to `pyproject.toml` for project configuration
- Look at examples in `notebooks/sample_analysis.ipynb`
- Check docstrings in existing functions
- Review project documentation in root directory

---

**Last Updated**: October 16, 2025
**Project**: evefrontier_datasets
**Python Version**: 3.12+
**Package Manager**: Poetry
