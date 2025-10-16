"""CLI tool for managing Eve Frontier Datasets project."""

import sys
import subprocess
import argparse
from pathlib import Path
from typing import Optional


def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent


def get_notebooks_dir() -> Path:
    """Get the notebooks directory."""
    notebooks_dir = get_project_root() / "notebooks"
    notebooks_dir.mkdir(exist_ok=True)
    return notebooks_dir


def cmd_jupyter_lab(args: argparse.Namespace) -> int:
    """Start Jupyter Lab."""
    print("🚀 Starting Jupyter Lab...")
    try:
        subprocess.run(["jupyter", "lab"], check=True)
        return 0
    except KeyboardInterrupt:
        print("\n⏹️  Jupyter Lab stopped.")
        return 0
    except FileNotFoundError:
        print("❌ Jupyter Lab not found. Please run: poetry install")
        return 1


def cmd_jupyter_notebook(args: argparse.Namespace) -> int:
    """Start Jupyter Notebook."""
    print("🚀 Starting Jupyter Notebook...")
    try:
        subprocess.run(["jupyter", "notebook"], check=True)
        return 0
    except KeyboardInterrupt:
        print("\n⏹️  Jupyter Notebook stopped.")
        return 0
    except FileNotFoundError:
        print("❌ Jupyter Notebook not found. Please run: poetry install")
        return 1


def cmd_new_notebook(args: argparse.Namespace) -> int:
    """Create a new Jupyter notebook."""
    if not args.name:
        print("❌ Notebook name is required. Use: efds notebook new <name>")
        return 1

    notebooks_dir = get_notebooks_dir()
    notebook_path = notebooks_dir / f"{args.name}.ipynb"

    if notebook_path.exists():
        print(f"❌ Notebook '{args.name}' already exists at {notebook_path}")
        return 1

    # Create a basic notebook structure
    notebook_content = {
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    f"# {args.name.replace('_', ' ').title()}\n",
                    "\n",
                    "Replace this with your notebook description."
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "import pandas as pd\n",
                    "import numpy as np\n",
                    "import matplotlib.pyplot as plt\n",
                    "import seaborn as sns\n",
                    "\n",
                    "# Set up plotting style\n",
                    "sns.set_style('darkgrid')\n",
                    "plt.rcParams['figure.figsize'] = (12, 6)"
                ]
            }
        ],
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3.12",
                "language": "python",
                "name": "python3"
            },
            "language_info": {
                "name": "python",
                "version": "3.12"
            }
        },
        "nbformat": 4,
        "nbformat_minor": 4
    }

    import json
    with open(notebook_path, 'w') as f:
        json.dump(notebook_content, f, indent=1)

    print(f"✅ Created new notebook: {notebook_path}")
    return 0


def cmd_list_notebooks(args: argparse.Namespace) -> int:
    """List all notebooks in the notebooks directory."""
    notebooks_dir = get_notebooks_dir()
    notebooks = list(notebooks_dir.glob("*.ipynb"))

    if not notebooks:
        print("📭 No notebooks found.")
        return 0

    print(f"📓 Found {len(notebooks)} notebook(s):\n")
    for i, notebook in enumerate(sorted(notebooks), 1):
        size = notebook.stat().st_size / 1024  # Size in KB
        print(f"  {i}. {notebook.name} ({size:.1f} KB)")

    return 0


def cmd_install(args: argparse.Namespace) -> int:
    """Install project dependencies."""
    print("📦 Installing dependencies with Poetry...")
    try:
        subprocess.run(["poetry", "install"], check=True)
        print("✅ Dependencies installed successfully!")
        return 0
    except FileNotFoundError:
        print("❌ Poetry not found. Please install Poetry from https://python-poetry.org/")
        return 1
    except subprocess.CalledProcessError as e:
        print(f"❌ Installation failed with error code {e.returncode}")
        return 1


def cmd_update(args: argparse.Namespace) -> int:
    """Update project dependencies."""
    print("📦 Updating dependencies with Poetry...")
    try:
        subprocess.run(["poetry", "update"], check=True)
        print("✅ Dependencies updated successfully!")
        return 0
    except FileNotFoundError:
        print("❌ Poetry not found. Please install Poetry from https://python-poetry.org/")
        return 1
    except subprocess.CalledProcessError as e:
        print(f"❌ Update failed with error code {e.returncode}")
        return 1


def cmd_info(args: argparse.Namespace) -> int:
    """Display project information."""
    print("\n" + "=" * 60)
    print("🎯 Eve Frontier Datasets - Project Information")
    print("=" * 60)
    print(f"\n📍 Project Root: {get_project_root()}")
    print(f"📁 Notebooks Dir: {get_notebooks_dir()}")
    print("🐍 Python Version: 3.12")
    print("\n📚 Quick Commands:")
    print("  • efds lab           - Start Jupyter Lab")
    print("  • efds notebook      - Start Jupyter Notebook")
    print("  • efds notebook new <name> - Create new notebook")
    print("  • efds notebook list - List all notebooks")
    print("  • efds install       - Install dependencies")
    print("  • efds update        - Update dependencies")
    print("\n" + "=" * 60 + "\n")
    return 0


def main(argv: Optional[list[str]] = None) -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Eve Frontier Datasets CLI - Manage Jupyter notebooks and dependencies",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  efds lab                    Start Jupyter Lab
  efds notebook new analysis  Create a new notebook
  efds notebook list          List all notebooks
  efds install                Install dependencies
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Jupyter Lab command
    subparsers.add_parser("lab", help="Start Jupyter Lab")

    # Notebook subcommands
    notebook_parser = subparsers.add_parser(
        "notebook",
        help="Manage notebooks and start Jupyter Notebook"
    )
    notebook_subs = notebook_parser.add_subparsers(dest="notebook_cmd")
    notebook_subs.add_parser("list", help="List all notebooks")
    new_nb = notebook_subs.add_parser("new", help="Create a new notebook")
    new_nb.add_argument("name", help="Name of the notebook to create")

    # Dependency management commands
    subparsers.add_parser("install", help="Install dependencies")
    subparsers.add_parser("update", help="Update dependencies")

    # Info command
    subparsers.add_parser("info", help="Display project information")

    args = parser.parse_args(argv)

    # Route commands
    if not args.command:
        return cmd_info(args)

    if args.command == "lab":
        return cmd_jupyter_lab(args)

    if args.command == "notebook":
        if hasattr(args, 'notebook_cmd'):
            if args.notebook_cmd == "list":
                return cmd_list_notebooks(args)
            elif args.notebook_cmd == "new":
                return cmd_new_notebook(args)
        return cmd_jupyter_notebook(args)

    if args.command == "install":
        return cmd_install(args)

    if args.command == "update":
        return cmd_update(args)

    if args.command == "info":
        return cmd_info(args)

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
