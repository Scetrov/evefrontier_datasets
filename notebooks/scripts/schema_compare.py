from __future__ import annotations
import sqlite3
from pathlib import Path
import pandas as pd

DB_E6C4 = Path("../data/static_data_e6c4.db")
DB_E6C5 = Path("../data/static_data_e6c5.db")


def fetch_schema(db_path: Path) -> dict[str, dict]:
    """Extract a normalized SQLite schema description."""
    if not db_path.exists():
        raise FileNotFoundError(f"Database not found: {db_path}")

    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row

        objects = conn.execute(
            """
            SELECT type, name, tbl_name, sql
            FROM sqlite_master
            WHERE name NOT LIKE 'sqlite_%'
            ORDER BY type, name
            """
        ).fetchall()

        schema: dict[str, dict] = {
            "tables": {},
            "views": {},
            "indexes": {},
            "triggers": {},
        }

        for obj in objects:
            obj_type = obj["type"]
            name = obj["name"]
            sql = obj["sql"]

            if obj_type == "table":
                columns = [
                    dict(row)
                    for row in conn.execute(f"PRAGMA table_info('{name}')").fetchall()
                ]
                foreign_keys = [
                    dict(row)
                    for row in conn.execute(f"PRAGMA foreign_key_list('{name}')").fetchall()
                ]

                index_rows = conn.execute(f"PRAGMA index_list('{name}')").fetchall()
                indexes: list[dict] = []
                for index_row in index_rows:
                    index_name = index_row["name"]
                    index_columns = [
                        dict(row)
                        for row in conn.execute(f"PRAGMA index_info('{index_name}')").fetchall()
                    ]
                    indexes.append(
                        {
                            **dict(index_row),
                            "columns": index_columns,
                        }
                    )

                schema["tables"][name] = {
                    "sql": sql,
                    "columns": columns,
                    "foreign_keys": foreign_keys,
                    "indexes": indexes,
                }

            elif obj_type == "view":
                schema["views"][name] = {"sql": sql}

            elif obj_type == "index":
                index_columns = [
                    dict(row)
                    for row in conn.execute(f"PRAGMA index_info('{name}')").fetchall()
                ]
                schema["indexes"][name] = {
                    "table": obj["tbl_name"],
                    "sql": sql,
                    "columns": index_columns,
                }

            elif obj_type == "trigger":
                schema["triggers"][name] = {
                    "table": obj["tbl_name"],
                    "sql": sql,
                }

        return schema


def compare_named_objects(
    left: dict[str, dict],
    right: dict[str, dict],
    object_type: str,
) -> list[dict[str, str]]:
    """Compare top-level named schema objects."""
    rows: list[dict[str, str]] = []

    left_names = set(left)
    right_names = set(right)

    for name in sorted(left_names - right_names):
        rows.append({"object_type": object_type, "name": name, "difference": "only_in_left"})

    for name in sorted(right_names - left_names):
        rows.append({"object_type": object_type, "name": name, "difference": "only_in_right"})

    for name in sorted(left_names & right_names):
        if left[name] != right[name]:
            rows.append({"object_type": object_type, "name": name, "difference": "definition_differs"})

    return rows


def compare_tables(
    left_tables: dict[str, dict],
    right_tables: dict[str, dict],
) -> tuple[list[dict[str, str]], dict[str, pd.DataFrame]]:
    """Compare SQLite table schemas in detail."""
    summary_rows: list[dict[str, str]] = []
    detail_frames: dict[str, pd.DataFrame] = {}

    left_names = set(left_tables)
    right_names = set(right_tables)

    for table_name in sorted(left_names - right_names):
        summary_rows.append({"object_type": "table", "name": table_name, "difference": "only_in_left"})

    for table_name in sorted(right_names - left_names):
        summary_rows.append({"object_type": "table", "name": table_name, "difference": "only_in_right"})

    for table_name in sorted(left_names & right_names):
        left_table = left_tables[table_name]
        right_table = right_tables[table_name]

        differences: list[dict[str, str]] = []

        if left_table["sql"] != right_table["sql"]:
            differences.append({"section": "table_sql", "status": "different"})

        left_columns = {
            col["name"]: {
                key: col[key]
                for key in ("type", "notnull", "dflt_value", "pk")
            }
            for col in left_table["columns"]
        }
        right_columns = {
            col["name"]: {
                key: col[key]
                for key in ("type", "notnull", "dflt_value", "pk")
            }
            for col in right_table["columns"]
        }

        for column_name in sorted(set(left_columns) - set(right_columns)):
            differences.append(
                {
                    "section": "column",
                    "name": column_name,
                    "status": "only_in_left",
                }
            )

        for column_name in sorted(set(right_columns) - set(left_columns)):
            differences.append(
                {
                    "section": "column",
                    "name": column_name,
                    "status": "only_in_right",
                }
            )

        for column_name in sorted(set(left_columns) & set(right_columns)):
            if left_columns[column_name] != right_columns[column_name]:
                differences.append(
                    {
                        "section": "column",
                        "name": column_name,
                        "status": "definition_differs",
                    }
                )

        if left_table["foreign_keys"] != right_table["foreign_keys"]:
            differences.append({"section": "foreign_keys", "status": "different"})

        left_indexes = {
            idx["name"]: {
                "unique": idx["unique"],
                "origin": idx["origin"],
                "partial": idx["partial"],
                "columns": [col["name"] for col in idx["columns"]],
            }
            for idx in left_table["indexes"]
        }
        right_indexes = {
            idx["name"]: {
                "unique": idx["unique"],
                "origin": idx["origin"],
                "partial": idx["partial"],
                "columns": [col["name"] for col in idx["columns"]],
            }
            for idx in right_table["indexes"]
        }

        if left_indexes != right_indexes:
            differences.append({"section": "indexes", "status": "different"})

        if differences:
            summary_rows.append(
                {
                    "object_type": "table",
                    "name": table_name,
                    "difference": "definition_differs",
                }
            )
            detail_frames[table_name] = pd.DataFrame(differences)

    return summary_rows, detail_frames


def compare_schemas(
    db_left: Path,
    db_right: Path,
    left_label: str = "left",
    right_label: str = "right",
) -> tuple[pd.DataFrame, dict[str, pd.DataFrame]]:
    """Load and compare two SQLite database schemas.

    Args:
        db_left: Path to the first (left/baseline) database.
        db_right: Path to the second (right/new) database.
        left_label: Human-readable label for the left database (used in output).
        right_label: Human-readable label for the right database (used in output).

    Returns:
        A tuple of:
          - schema_diff_summary: DataFrame summarising all object-level differences.
          - table_details: Dict mapping table names to DataFrames with column-level details.
    """
    schema_left = fetch_schema(db_left)
    schema_right = fetch_schema(db_right)

    print(f"Loaded: {db_left}  ({left_label})")
    print(f"Loaded: {db_right}  ({right_label})")
    print()

    print("Object counts:")
    print(
        pd.DataFrame(
            [
                {
                    "database": left_label,
                    "tables": len(schema_left["tables"]),
                    "views": len(schema_left["views"]),
                    "indexes": len(schema_left["indexes"]),
                    "triggers": len(schema_left["triggers"]),
                },
                {
                    "database": right_label,
                    "tables": len(schema_right["tables"]),
                    "views": len(schema_right["views"]),
                    "indexes": len(schema_right["indexes"]),
                    "triggers": len(schema_right["triggers"]),
                },
            ]
        ).to_string(index=False)
    )
    print()

    table_summary, table_details = compare_tables(schema_left["tables"], schema_right["tables"])

    other_summary: list[dict[str, str]] = []
    other_summary.extend(compare_named_objects(schema_left["views"], schema_right["views"], "view"))
    other_summary.extend(compare_named_objects(schema_left["indexes"], schema_right["indexes"], "index"))
    other_summary.extend(compare_named_objects(schema_left["triggers"], schema_right["triggers"], "trigger"))

    schema_diff_summary = (
        pd.DataFrame(table_summary + other_summary)
        .sort_values(by=["object_type", "name", "difference"])
        .reset_index(drop=True)
    )

    return schema_diff_summary, table_details


if __name__ == "__main__":
    from IPython.display import display

    diff_summary, details = compare_schemas(DB_E6C4, DB_E6C5, "e6c4", "e6c5")

    if diff_summary.empty:
        print("Schemas match.")
    else:
        print("Schema differences:")
        display(diff_summary)

        if details:
            print("\nDetailed table differences:")
            for table_name, detail_df in details.items():
                print(f"\n--- {table_name} ---")
                display(detail_df)