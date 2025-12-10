"""Visualization functions for EVE Frontier static data."""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import seaborn as sns


def visualize_solar_system(
    db_data: dict,
    system_id: int,
    system_name: str = None,
    size_scale: float = 1.0
) -> pd.DataFrame:
    """
    Visualize a specific solar system with all its celestial objects.
    
    Objects are color-coded:
    - Red: Primary Star (sun at center)
    - Blue: Planets
    - Green: Moons
    - Orange: NPC Stations
    
    Uses logarithmic scaling to handle the huge coordinate ranges.
    
    Args:
        db_data: Dictionary of DataFrames containing the database tables
        system_id: The solarSystemId to visualize
        system_name: Optional name to display (will look up if not provided)
        size_scale: Scale factor for object sizes (default 1.0)
    
    Returns:
        DataFrame with plot data including scaled coordinates
    """
    
    # Get system info
    if 'SolarSystems' not in db_data:
        print("✗ SolarSystems table not found")
        return None
    
    systems_df = db_data['SolarSystems']
    system_info = systems_df[systems_df['solarSystemId'] == system_id]
    
    if len(system_info) == 0:
        print(f"✗ Solar system {system_id} not found")
        return None
    
    if system_name is None:
        system_name = system_info.iloc[0]['name']
    
    # Get sun position (center of system)
    sun_x = system_info.iloc[0]['centerX']
    sun_y = system_info.iloc[0]['centerY']
    sun_z = system_info.iloc[0]['centerZ']
    
    print(f"\n⭐ Visualizing Solar System: {system_name} (ID: {system_id})")
    print(f"   Sun position: ({sun_x:.2e}, {sun_y:.2e}, {sun_z:.2e})")
    
    # Prepare data for plotting
    plot_data = {
        'x': [],
        'y': [],
        'z': [],
        'type': [],
        'name': [],
        'size': [],
        'color': []
    }
    
    # Add sun at center
    plot_data['x'].append(sun_x)
    plot_data['y'].append(sun_y)
    plot_data['z'].append(sun_z)
    plot_data['type'].append('Star')
    plot_data['name'].append(f'{system_name} Star')
    plot_data['size'].append(20)
    plot_data['color'].append('Red')
    
    # Add planets
    if 'Planets' in db_data:
        planets_df = db_data['Planets']
        planets = planets_df[planets_df['solarSystemId'] == system_id]
        
        for idx, planet in planets.iterrows():
            plot_data['x'].append(planet['centerX'])
            plot_data['y'].append(planet['centerY'])
            plot_data['z'].append(planet['centerZ'])
            plot_data['type'].append('Planet')
            plot_data['name'].append(planet.get('name', f"Planet {idx}"))
            plot_data['size'].append(12)
            plot_data['color'].append('Blue')
        
        print(f"   ✓ Found {len(planets)} planets")
    
    # Add moons
    if 'Moons' in db_data:
        moons_df = db_data['Moons']
        moons = moons_df[moons_df['solarSystemId'] == system_id]
        
        for idx, moon in moons.iterrows():
            plot_data['x'].append(moon['centerX'])
            plot_data['y'].append(moon['centerY'])
            plot_data['z'].append(moon['centerZ'])
            plot_data['type'].append('Moon')
            plot_data['name'].append(moon.get('name', f"Moon {idx}"))
            plot_data['size'].append(8)
            plot_data['color'].append('Green')
        
        print(f"   ✓ Found {len(moons)} moons")
    
    # Add NPC stations
    if 'NpcStations' in db_data:
        stations_df = db_data['NpcStations']
        stations = stations_df[stations_df['solarSystemId'] == system_id]
        
        for idx, station in stations.iterrows():
            plot_data['x'].append(station['centerX'])
            plot_data['y'].append(station['centerY'])
            plot_data['z'].append(station['centerZ'])
            plot_data['type'].append('NPC Station')
            plot_data['name'].append(station.get('name', f"Station {idx}"))
            plot_data['size'].append(10)
            plot_data['color'].append('Orange')
        
        print(f"   ✓ Found {len(stations)} NPC stations")
    
    # Create interactive 3D scatter plot with plotly
    plot_df = pd.DataFrame(plot_data)
    
    # Center coordinates around the sun (first object, which is the star)
    sun_coords = plot_df.iloc[0][['x', 'y', 'z']]
    plot_df['x_centered'] = plot_df['x'] - sun_coords['x']
    plot_df['y_centered'] = plot_df['y'] - sun_coords['y']
    plot_df['z_centered'] = plot_df['z'] - sun_coords['z']
    
    # Calculate ranges to understand the scale
    x_range = plot_df['x_centered'].max() - plot_df['x_centered'].min()
    y_range = plot_df['y_centered'].max() - plot_df['y_centered'].min()
    z_range = plot_df['z_centered'].max() - plot_df['z_centered'].min()
    
    # Find the minimum non-zero distance to use as appropriate offset
    non_zero_distances = []
    for coord in ['x_centered', 'y_centered', 'z_centered']:
        non_zero = plot_df[coord][plot_df[coord] != 0].abs()
        if len(non_zero) > 0:
            non_zero_distances.extend(non_zero.tolist())
    
    # Use 1% of minimum non-zero distance as offset, or 1.0 as fallback
    offset = min(non_zero_distances) * 0.01 if non_zero_distances else 1.0
    
    print(f"   Coordinate ranges:")
    print(f"     X: {plot_df['x_centered'].min():.2e} to {plot_df['x_centered'].max():.2e} (range: {x_range:.2e})")
    print(f"     Y: {plot_df['y_centered'].min():.2e} to {plot_df['y_centered'].max():.2e} (range: {y_range:.2e})")
    print(f"     Z: {plot_df['z_centered'].min():.2e} to {plot_df['z_centered'].max():.2e} (range: {z_range:.2e})")
    print(f"     Log offset: {offset:.2e}")
    
    # Use logarithmic scaling to handle huge coordinate ranges
    # This prevents precision loss and ensures visibility of all objects
    plot_df['x_scaled'] = np.sign(plot_df['x_centered']) * np.log10(np.abs(plot_df['x_centered']) + offset)
    plot_df['y_scaled'] = np.sign(plot_df['y_centered']) * np.log10(np.abs(plot_df['y_centered']) + offset)
    plot_df['z_scaled'] = np.sign(plot_df['z_centered']) * np.log10(np.abs(plot_df['z_centered']) + offset)
    
    # Color mapping
    color_map = {
        'Red': '#FF0000',
        'Blue': '#0000FF',
        'Green': '#00FF00',
        'Orange': '#FFA500'
    }
    
    fig = go.Figure()
    
    # Add traces for each object type
    for obj_type in plot_df['type'].unique():
        type_data = plot_df[plot_df['type'] == obj_type]
        color = type_data['color'].iloc[0]
        
        fig.add_trace(go.Scatter3d(
            x=type_data['x_scaled'],
            y=type_data['y_scaled'],
            z=type_data['z_scaled'],
            mode='markers',
            name=obj_type,
            marker=dict(
                size=type_data['size'] * size_scale,
                color=color_map[color],
                opacity=0.8,
                line=dict(width=1, color='white')
            ),
            text=[f"<b>{name}</b><br>Type: {t}<br>Relative X: {x:.2e}<br>Relative Y: {y:.2e}<br>Relative Z: {z:.2e}" 
                  for name, t, x, y, z in zip(type_data['name'], type_data['type'], 
                                               type_data['x_centered'], type_data['y_centered'], type_data['z_centered'])],
            hovertemplate='%{text}<extra></extra>'
        ))
    
    # Calculate bounding box for scaling (using log-scaled coordinates)
    x_min, x_max = plot_df['x_scaled'].min(), plot_df['x_scaled'].max()
    y_min, y_max = plot_df['y_scaled'].min(), plot_df['y_scaled'].max()
    z_min, z_max = plot_df['z_scaled'].min(), plot_df['z_scaled'].max()
    
    # Add padding (15% of range)
    x_range_scaled = x_max - x_min
    y_range_scaled = y_max - y_min
    z_range_scaled = z_max - z_min
    
    x_pad = x_range_scaled * 0.15 if x_range_scaled > 0 else 1
    y_pad = y_range_scaled * 0.15 if y_range_scaled > 0 else 1
    z_pad = z_range_scaled * 0.15 if z_range_scaled > 0 else 1
    
    fig.update_layout(
        title=f'<b>{system_name}</b><br>Solar System Overview (Log-Scaled)',
        scene=dict(
            xaxis=dict(
                range=[x_min - x_pad, x_max + x_pad],
                title='Log10(|Relative X|) Coordinate'
            ),
            yaxis=dict(
                range=[y_min - y_pad, y_max + y_pad],
                title='Log10(|Relative Y|) Coordinate'
            ),
            zaxis=dict(
                range=[z_min - z_pad, z_max + z_pad],
                title='Log10(|Relative Z|) Coordinate'
            ),
            aspectmode='auto',
            camera=dict(
                eye=dict(x=1.5, y=1.5, z=1.5)
            )
        ),
        width=1200,
        height=800,
        showlegend=True,
        hovermode='closest'
    )
    
    fig.show()
    
    print(f"   📊 Total objects: {len(plot_df)}")
    print(f"   ✅ Visualization complete")
    
    return plot_df


def plot_2d_scatter(
    db_data: dict,
    table_name: str,
    x_col: str,
    y_col: str,
    color_col: str = None,
    size: int = 50
):
    """Create a 2D scatter plot from coordinate data."""
    if table_name not in db_data:
        print(f"✗ Table '{table_name}' not found")
        return
    
    df = db_data[table_name]
    
    # Remove rows with NaN coordinates
    plot_df = df.dropna(subset=[x_col, y_col])
    
    if len(plot_df) == 0:
        print(f"✗ No valid coordinate data in {table_name}")
        return
    
    fig, ax = plt.subplots(figsize=(12, 10))
    
    if color_col and color_col in df.columns:
        scatter = ax.scatter(
            plot_df[x_col], plot_df[y_col],
            c=pd.to_numeric(plot_df[color_col], errors='coerce'),
            s=size, alpha=0.6, cmap='viridis', edgecolors='black', linewidth=0.5
        )
        cbar = plt.colorbar(scatter, ax=ax)
        cbar.set_label(color_col, rotation=270, labelpad=20)
    else:
        ax.scatter(plot_df[x_col], plot_df[y_col], s=size, alpha=0.6, edgecolors='black', linewidth=0.5)
    
    ax.set_xlabel(x_col, fontsize=12)
    ax.set_ylabel(y_col, fontsize=12)
    ax.set_title(f'{table_name} - 2D Spatial Distribution\n({len(plot_df):,} points)', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.show()
    
    print(f"✓ Plotted {len(plot_df):,} points from {table_name}")


def plot_3d_scatter(
    db_data: dict,
    table_name: str,
    x_col: str,
    y_col: str,
    z_col: str,
    color_col: str = None,
    size: int = 30
):
    """Create a 3D scatter plot from coordinate data."""
    if table_name not in db_data:
        print(f"✗ Table '{table_name}' not found")
        return
    
    df = db_data[table_name]
    
    # Remove rows with NaN coordinates
    plot_df = df.dropna(subset=[x_col, y_col, z_col])
    
    if len(plot_df) == 0:
        print(f"✗ No valid 3D coordinate data in {table_name}")
        return
    
    # Use plotly for interactive 3D visualization
    if color_col and color_col in df.columns:
        color_data = pd.to_numeric(plot_df[color_col], errors='coerce')
        fig = px.scatter_3d(
            plot_df,
            x=x_col, y=y_col, z=z_col,
            color=color_col,
            title=f'{table_name} - 3D Spatial Distribution ({len(plot_df):,} points)',
            labels={x_col: x_col, y_col: y_col, z_col: z_col},
            hover_data=list(plot_df.columns[:min(5, len(plot_df.columns))])
        )
    else:
        fig = px.scatter_3d(
            plot_df,
            x=x_col, y=y_col, z=z_col,
            title=f'{table_name} - 3D Spatial Distribution ({len(plot_df):,} points)',
            labels={x_col: x_col, y_col: y_col, z_col: z_col},
            hover_data=list(plot_df.columns[:min(5, len(plot_df.columns))])
        )
    
    fig.update_traces(marker=dict(size=size, opacity=0.7))
    fig.show()
    
    print(f"✓ Plotted {len(plot_df):,} points in 3D space")


def explore_coordinates(
    db_data: dict,
    table_name: str,
    x_col: str = None,
    y_col: str = None,
    z_col: str = None
) -> dict:
    """Interactively explore coordinate data from any table."""
    if table_name not in db_data:
        print(f"✗ Table '{table_name}' not found")
        return None
    
    df = db_data[table_name]
    
    # Auto-detect columns if not provided
    if not x_col or not y_col:
        cols = set(df.columns)
        if 'centerX' in cols:
            x_col = x_col or 'centerX'
            y_col = y_col or 'centerY'
            z_col = z_col or ('centerZ' if 'centerZ' in cols else None)
        elif 'fromCenterX' in cols:
            x_col = x_col or 'fromCenterX'
            y_col = y_col or 'fromCenterY'
            z_col = z_col or ('fromCenterZ' if 'fromCenterZ' in cols else None)
        elif 'toCenterX' in cols:
            x_col = x_col or 'toCenterX'
            y_col = y_col or 'toCenterY'
            z_col = z_col or ('toCenterZ' if 'toCenterZ' in cols else None)
    
    if not x_col or not y_col:
        print(f"✗ Could not find X and Y columns in {table_name}")
        print(f"Available columns: {list(df.columns)}")
        return None
    
    print(f"\n📍 Exploring {table_name}")
    print(f"   X: {x_col}")
    print(f"   Y: {y_col}")
    if z_col:
        print(f"   Z: {z_col}")
    
    # Statistics
    df_clean = df.dropna(subset=[x_col, y_col])
    print(f"\n📊 Statistics:")
    print(f"   Valid points: {len(df_clean):,}")
    print(f"   X range: [{df_clean[x_col].min():.2e}, {df_clean[x_col].max():.2e}]")
    print(f"   Y range: [{df_clean[y_col].min():.2e}, {df_clean[y_col].max():.2e}]")
    if z_col and z_col in df.columns:
        df_clean_z = df_clean.dropna(subset=[z_col])
        print(f"   Z range: [{df_clean_z[z_col].min():.2e}, {df_clean_z[z_col].max():.2e}]")
    
    # Find numeric columns for coloring
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    print(f"\n🎨 Available numeric columns for coloring:")
    for i, col in enumerate(numeric_cols[:10], 1):
        print(f"   {i}. {col}")
    
    return {
        'table': table_name,
        'x_col': x_col,
        'y_col': y_col,
        'z_col': z_col,
        'numeric_cols': numeric_cols
    }
