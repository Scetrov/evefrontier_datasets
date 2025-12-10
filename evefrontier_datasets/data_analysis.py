"""Data analysis utilities for EVE Frontier static data."""

from typing import Dict, Optional

import numpy as np
import pandas as pd


def get_database_overview(db_data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """
    Create an overview of all tables in the database.

    Args:
        db_data: Dictionary mapping table names to DataFrames.

    Returns:
        DataFrame with table statistics (rows, columns, memory usage).

    Example:
        >>> overview = get_database_overview(db_data)
        >>> print(overview)
    """
    overview_data = []
    for table_name, df in db_data.items():
        overview_data.append(
            {
                "Table": table_name,
                "Rows": len(df),
                "Columns": len(df.columns),
                "Memory (MB)": df.memory_usage(deep=True).sum() / 1024 / 1024,
            }
        )

    overview_df = pd.DataFrame(overview_data).sort_values("Rows", ascending=False)
    return overview_df


def detect_coordinate_columns(df: pd.DataFrame) -> Optional[dict]:
    """
    Detect coordinate columns in a DataFrame.

    Looks for patterns like:
    - centerX, centerY, centerZ
    - fromCenterX, fromCenterY, fromCenterZ
    - toCenterX, toCenterY, toCenterZ

    Args:
        df: DataFrame to inspect.

    Returns:
        Dictionary with keys 'x_col', 'y_col', 'z_col' (None if not found),
        or None if no coordinate columns found.

    Example:
        >>> coords = detect_coordinate_columns(df)
        >>> if coords:
        ...     print(f"X: {coords['x_col']}, Y: {coords['y_col']}")
    """
    cols = set(df.columns)

    # Check for different coordinate patterns
    patterns = [
        ("centerX", "centerY", "centerZ"),
        ("fromCenterX", "fromCenterY", "fromCenterZ"),
        ("toCenterX", "toCenterY", "toCenterZ"),
    ]

    for x_col, y_col, z_col in patterns:
        if x_col in cols and y_col in cols:
            return {
                "x_col": x_col,
                "y_col": y_col,
                "z_col": z_col if z_col in cols else None,
                "has_z": bool(z_col in cols),
            }

    return None


def scan_coordinate_tables(db_data: Dict[str, pd.DataFrame]) -> Dict[str, dict]:
    """
    Scan all tables in database for coordinate columns.

    Args:
        db_data: Dictionary mapping table names to DataFrames.

    Returns:
        Dictionary mapping table names to their coordinate column info.
        Only includes tables that have coordinate columns.

    Example:
        >>> coord_tables = scan_coordinate_tables(db_data)
        >>> for table, coords in coord_tables.items():
        ...     print(f"{table}: X={coords['x_col']}, Y={coords['y_col']}")
    """
    coordinate_tables = {}

    for table_name, df in db_data.items():
        coords = detect_coordinate_columns(df)
        if coords:
            coordinate_tables[table_name] = coords

    return coordinate_tables


def get_coordinate_statistics(
    df: pd.DataFrame, x_col: str, y_col: str, z_col: Optional[str] = None
) -> dict:
    """
    Calculate statistics for coordinate columns.

    Args:
        df: DataFrame containing coordinate data.
        x_col: Name of X coordinate column.
        y_col: Name of Y coordinate column.
        z_col: Name of Z coordinate column (optional).

    Returns:
        Dictionary with coordinate statistics including ranges and valid point count.

    Example:
        >>> stats = get_coordinate_statistics(df, 'centerX', 'centerY', 'centerZ')
        >>> print(f"Valid points: {stats['valid_points']}")
    """
    df_clean = df.dropna(subset=[x_col, y_col])

    stats = {
        "valid_points": len(df_clean),
        "x_range": (df_clean[x_col].min(), df_clean[x_col].max()),
        "y_range": (df_clean[y_col].min(), df_clean[y_col].max()),
    }

    if z_col and z_col in df.columns:
        df_clean_z = df_clean.dropna(subset=[z_col])
        stats["z_range"] = (df_clean_z[z_col].min(), df_clean_z[z_col].max())
        stats["has_z"] = True
    else:
        stats["has_z"] = False

    return stats


def find_numeric_columns(df: pd.DataFrame, max_columns: int = 10) -> list:
    """
    Find numeric columns in a DataFrame for potential coloring.

    Args:
        df: DataFrame to inspect.
        max_columns: Maximum number of columns to return.

    Returns:
        List of numeric column names.

    Example:
        >>> numeric_cols = find_numeric_columns(df)
        >>> print(f"Found {len(numeric_cols)} numeric columns")
    """
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    return numeric_cols[:max_columns]


def get_solar_system_info(db_data: Dict[str, pd.DataFrame], system_id: int) -> Optional[dict]:
    """
    Get information about a specific solar system.

    Args:
        db_data: Dictionary of database tables.
        system_id: Solar system ID to query.

    Returns:
        Dictionary with system information, or None if not found.

    Example:
        >>> system_info = get_solar_system_info(db_data, 30000142)
        >>> if system_info:
        ...     print(system_info['name'])
    """
    if "SolarSystems" not in db_data:
        return None

    systems_df = db_data["SolarSystems"]
    system = systems_df[systems_df["solarSystemId"] == system_id]

    if len(system) == 0:
        return None

    system_row = system.iloc[0]

    info = {
        "system_id": system_id,
        "name": system_row["name"],
        "center": (system_row["centerX"], system_row["centerY"], system_row["centerZ"]),
    }

    # Count celestial objects
    if "Planets" in db_data:
        info["planet_count"] = len(
            db_data["Planets"][db_data["Planets"]["solarSystemId"] == system_id]
        )
    else:
        info["planet_count"] = 0

    if "Moons" in db_data:
        info["moon_count"] = len(db_data["Moons"][db_data["Moons"]["solarSystemId"] == system_id])
    else:
        info["moon_count"] = 0

    if "NpcStations" in db_data:
        info["station_count"] = len(
            db_data["NpcStations"][db_data["NpcStations"]["solarSystemId"] == system_id]
        )
    else:
        info["station_count"] = 0

    return info


def search_solar_systems(db_data: Dict[str, pd.DataFrame], query: str) -> pd.DataFrame:
    """
    Search for solar systems by name.

    Args:
        db_data: Dictionary of database tables.
        query: Search query (case-insensitive substring match).

    Returns:
        DataFrame with matching solar systems.

    Example:
        >>> results = search_solar_systems(db_data, 'Brana')
        >>> print(f"Found {len(results)} systems")
    """
    if "SolarSystems" not in db_data:
        return pd.DataFrame()

    systems_df = db_data["SolarSystems"]
    results = systems_df[systems_df["name"].str.contains(query, case=False, na=False)]

    return results


def find_system_with_most_planets(db_data: Dict[str, pd.DataFrame]) -> Optional[dict]:
    """
    Find the solar system with the most planets.

    Args:
        db_data: Dictionary of database tables.

    Returns:
        Dictionary with system information, or None if no systems found.

    Example:
        >>> best_system = find_system_with_most_planets(db_data)
        >>> if best_system:
        ...     print(f"{best_system['name']} has {best_system['planet_count']} planets")
    """
    if "Planets" not in db_data or "SolarSystems" not in db_data:
        return None

    planets_df = db_data["Planets"]
    planet_counts = planets_df["solarSystemId"].value_counts()

    if len(planet_counts) == 0:
        return None

    best_system_id = int(planet_counts.idxmax())
    return get_solar_system_info(db_data, best_system_id)


def print_database_summary(db_data: Dict[str, pd.DataFrame]) -> None:
    """
    Print a comprehensive summary of the database.

    Args:
        db_data: Dictionary of database tables.

    Example:
        >>> print_database_summary(db_data)
    """
    overview = get_database_overview(db_data)

    print("\n📊 Database Overview")
    print("=" * 80)
    print(overview.to_string(index=False))
    print(f"\nTotal Rows: {overview['Rows'].sum():,}")
    print(f"Total Memory: {overview['Memory (MB)'].sum():.2f} MB")

    # Coordinate tables
    coord_tables = scan_coordinate_tables(db_data)
    if coord_tables:
        print(f"\n\n🔍 Found {len(coord_tables)} tables with coordinate data:")
        print("=" * 80)
        for table_name, coords in coord_tables.items():
            z_info = f"+ Z ({coords['z_col']})" if coords["z_col"] else "2D only"
            print(f"   {table_name:30} | X: {coords['x_col']:15} Y: {coords['y_col']:15} {z_info}")

    # Solar systems summary
    if "SolarSystems" in db_data:
        systems_df = db_data["SolarSystems"]
        print(f"\n\n🌍 Solar Systems: {len(systems_df):,} total")
        print("=" * 80)

        if "Planets" in db_data:
            planets_df = db_data["Planets"]
            total_planets = len(planets_df)
            print(f"   Total Planets: {total_planets:,}")

            best_system = find_system_with_most_planets(db_data)
            if best_system:
                print(
                    f"   Most Planets: {best_system['planet_count']} in {best_system['name']} (ID: {best_system['system_id']})"
                )

        if "Moons" in db_data:
            total_moons = len(db_data["Moons"])
            print(f"   Total Moons: {total_moons:,}")

        if "NpcStations" in db_data:
            total_stations = len(db_data["NpcStations"])
            print(f"   Total NPC Stations: {total_stations:,}")

    print("\n" + "=" * 80)
