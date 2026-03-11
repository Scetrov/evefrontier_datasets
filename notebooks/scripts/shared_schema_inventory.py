from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
DB_E6C4 = PROJECT_ROOT / "data" / "static_data_e6c4.db"
DB_E6C5 = PROJECT_ROOT / "data" / "static_data_e6c5.db"


def fetch_table_columns(db_path: Path) -> dict[str, list[str]]:
    """Return SQLite tables mapped to their ordered column names.

    Args:
        db_path: Path to the SQLite database file.

    Returns:
        A mapping of table name to its column names in schema order.

    Raises:
        FileNotFoundError: If the database file does not exist.
    """
    if not db_path.exists():
        raise FileNotFoundError(f"Database not found: {db_path}")

    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        table_rows = conn.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
            """
        ).fetchall()

        table_columns: dict[str, list[str]] = {}
        for row in table_rows:
            table_name = row["name"]
            column_rows = conn.execute(f"PRAGMA table_info('{table_name}')").fetchall()
            table_columns[table_name] = [column_row["name"] for column_row in column_rows]

    return table_columns


def list_shared_tables_and_columns(
    db_left: Path,
    db_right: Path,
    left_label: str = "left",
    right_label: str = "right",
) -> pd.DataFrame:
    """Build a shared table inventory for two SQLite databases.

    Args:
        db_left: Path to the first database.
        db_right: Path to the second database.
        left_label: Label used for columns describing the first database.
        right_label: Label used for columns describing the second database.

    Returns:
        A DataFrame containing shared tables and their column inventories,
        including shared and database-specific columns.
    """
    left_tables = fetch_table_columns(db_left)
    right_tables = fetch_table_columns(db_right)

    rows: list[dict[str, str | int]] = []
    for table_name in sorted(set(left_tables) & set(right_tables)):
        left_columns = left_tables[table_name]
        right_columns = right_tables[table_name]

        shared_columns = [column for column in left_columns if column in right_columns]
        left_only_columns = [column for column in left_columns if column not in right_columns]
        right_only_columns = [column for column in right_columns if column not in left_columns]

        rows.append(
            {
                "table_name": table_name,
                f"{left_label}_column_count": len(left_columns),
                f"{right_label}_column_count": len(right_columns),
                "shared_column_count": len(shared_columns),
                f"{left_label}_columns": ", ".join(left_columns),
                f"{right_label}_columns": ", ".join(right_columns),
                "shared_columns": ", ".join(shared_columns),
                f"{left_label}_only_columns": ", ".join(left_only_columns),
                f"{right_label}_only_columns": ", ".join(right_only_columns),
            }
        )

    return pd.DataFrame(rows)


if __name__ == "__main__":
    from IPython.display import display

    display(list_shared_tables_and_columns(DB_E6C4, DB_E6C5, left_label="e6c4", right_label="e6c5"))