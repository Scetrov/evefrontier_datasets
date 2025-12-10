"""Eve Frontier Datasets - A project for managing Eve Frontier datasets with Jupyter Notebooks."""

__version__ = "0.1.0"
__author__ = "Scetrov"

# Import key functions for easy access
from evefrontier_datasets.data_analysis import (
    find_system_with_most_planets,
    get_database_overview,
    get_solar_system_info,
    print_database_summary,
    scan_coordinate_tables,
    search_solar_systems,
)
from evefrontier_datasets.data_loader import (
    download_file,
    get_release_info,
    load_database_tables,
    load_eve_data,
)
from evefrontier_datasets.visualization import (
    explore_coordinates,
    plot_2d_scatter,
    plot_3d_scatter,
    visualize_solar_system,
)

__all__ = [
    # Data loading
    "download_file",
    "get_release_info",
    "load_database_tables",
    "load_eve_data",
    # Data analysis
    "find_system_with_most_planets",
    "get_database_overview",
    "get_solar_system_info",
    "print_database_summary",
    "scan_coordinate_tables",
    "search_solar_systems",
    # Visualization
    "explore_coordinates",
    "plot_2d_scatter",
    "plot_3d_scatter",
    "visualize_solar_system",
]
