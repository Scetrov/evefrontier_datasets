"""Data loading utilities for EVE Frontier static data."""

import sqlite3
from pathlib import Path
from typing import Dict

import pandas as pd
import requests


def download_file(url: str, destination: Path, force: bool = False) -> bool:
    """
    Download a file from URL to destination.

    Args:
        url: The URL to download from.
        destination: The local path to save the file.
        force: If True, overwrite existing file. If False, skip if exists.

    Returns:
        True if download succeeded or file already exists, False otherwise.

    Example:
        >>> from pathlib import Path
        >>> download_file(
        ...     'https://example.com/data.db',
        ...     Path('/workspace/data/data.db')
        ... )
    """
    if destination.exists() and not force:
        print(f"✓ File already exists: {destination.name}")
        return True

    try:
        print(f"⬇️  Downloading {destination.name}...")
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()

        total_size = int(response.headers.get("content-length", 0))
        downloaded = 0

        # Ensure parent directory exists
        destination.parent.mkdir(parents=True, exist_ok=True)

        with open(destination, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size:
                        percent = (downloaded / total_size) * 100
                        mb_downloaded = downloaded / 1024 / 1024
                        print(f"  Progress: {percent:.1f}% ({mb_downloaded:.1f} MB)", end="\r")

        file_size_mb = destination.stat().st_size / 1024 / 1024
        print(f"\n✓ Downloaded: {destination.name} ({file_size_mb:.2f} MB)")
        return True
    except Exception as e:
        print(f"✗ Failed to download {destination.name}: {e}")
        return False


def load_database_tables(db_path: Path) -> Dict[str, pd.DataFrame]:
    """
    Load all tables from SQLite database into DataFrames.

    Args:
        db_path: Path to the SQLite database file.

    Returns:
        Dictionary mapping table names to pandas DataFrames.

    Raises:
        FileNotFoundError: If database file doesn't exist.
        sqlite3.Error: If database cannot be opened.

    Example:
        >>> from pathlib import Path
        >>> db_data = load_database_tables(Path('/workspace/data/static_data.db'))
        >>> print(f"Loaded {len(db_data)} tables")
    """
    if not db_path.exists():
        raise FileNotFoundError(f"Database file not found: {db_path}")

    conn = sqlite3.connect(db_path)

    try:
        # Get all table names
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]

        # Load each table
        data = {}
        for table in tables:
            try:
                data[table] = pd.read_sql_query(f"SELECT * FROM {table}", conn)
            except Exception as e:
                print(f"⚠️  Error loading table {table}: {e}")

        return data
    finally:
        conn.close()


def get_release_info(tag: str = "e6c3") -> dict:
    """
    Get release information for a specific version.

    Args:
        tag: Release tag (default: 'e6c3' for Era 6, Cycle 3).

    Returns:
        Dictionary with release metadata including tag, name, url, and local path.

    Example:
        >>> release = get_release_info('e6c3')
        >>> print(release['name'])
        Era 6, Cycle 3
    """
    release_map = {
        "e6c3": {
            "tag": "e6c3",
            "name": "Era 6, Cycle 3",
            "url": "https://github.com/Scetrov/evefrontier_datasets/releases/download/e6c3/static_data.db",
        },
        # Add more releases here as needed
    }

    if tag not in release_map:
        raise ValueError(f"Unknown release tag: {tag}. Available: {list(release_map.keys())}")

    release_info = release_map[tag].copy()
    # Add local path
    data_dir = Path("/workspace/data")
    data_dir.mkdir(exist_ok=True)
    release_info["path"] = str(data_dir / f"static_data_{tag}.db")

    return release_info


def load_eve_data(
    release_tag: str = "e6c3", force_download: bool = False
) -> Dict[str, pd.DataFrame]:
    """
    Convenience function to download and load EVE Frontier data.

    Args:
        release_tag: Release tag to download (default: 'e6c3').
        force_download: If True, re-download even if file exists.

    Returns:
        Dictionary mapping table names to pandas DataFrames.

    Example:
        >>> db_data = load_eve_data('e6c3')
        >>> print(f"Loaded {len(db_data)} tables")
    """
    release = get_release_info(release_tag)

    print("📊 Loading EVE Frontier Data")
    print(f"   Release: {release['name']} ({release['tag']})")
    print(f"   Local path: {release['path']}")
    print()

    # Download if needed
    if not Path(release["path"]).exists() or force_download:
        success = download_file(release["url"], Path(release["path"]), force=force_download)
        if not success:
            raise RuntimeError(f"Failed to download release {release_tag}")

    # Load database
    print("\n📂 Loading tables from database...")
    db_data = load_database_tables(Path(release["path"]))
    print(f"✓ Loaded {len(db_data)} tables")

    # Display table overview
    print("\n📋 Database Tables:")
    for table_name, df in db_data.items():
        print(f"   {table_name:30} | {len(df):>8,} rows | {len(df.columns):>3} columns")

    return db_data
