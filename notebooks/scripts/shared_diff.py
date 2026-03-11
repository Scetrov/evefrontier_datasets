from __future__ import annotations

import sqlite3

import pandas as pd

from shared_schema_inventory import DB_E6C4, DB_E6C5


def diff_table_rows(
    db_left,
    db_right,
    table_name,
    key_columns,
    left_label="e5c4",
    right_label="e5c5",
):
    with sqlite3.connect(db_left) as conn_left, sqlite3.connect(db_right) as conn_right:
        left_df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn_left)
        right_df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn_right)

    merged = left_df.merge(
        right_df,
        on=key_columns,
        how="outer",
        suffixes=(f"_{left_label}", f"_{right_label}"),
        indicator=True,
    )

    compare_columns = [c for c in left_df.columns if c not in key_columns]
    
    # 0. Identify Changes
    both_rows = merged[merged["_merge"] == "both"].copy()
    changed_mask = pd.Series(False, index=both_rows.index)
    for col in compare_columns:
        l, r = f"{col}_{left_label}", f"{col}_{right_label}"
        diff = ~(both_rows[l].eq(both_rows[r]) | (both_rows[l].isna() & both_rows[r].isna()))
        changed_mask = changed_mask | diff

    # 1. Combine all differences
    diff_rows = pd.concat([
        merged[merged["_merge"] == "left_only"].assign(row_status=f"only_in_{left_label}"),
        merged[merged["_merge"] == "right_only"].assign(row_status=f"only_in_{right_label}"),
        both_rows[changed_mask].assign(row_status="changed")
    ], ignore_index=True)

    if diff_rows.empty:
        print("No differences found.")
        return None

    # 2. Organize Columns
    ordered = list(key_columns)
    for col in compare_columns:
        ordered.extend([f"{col}_{left_label}", f"{col}_{right_label}"])
    ordered.append("row_status")
    
    final_df = diff_rows[ordered].sort_values(by=key_columns).reset_index(drop=True)

    # 3. The Styler Function
    def apply_color(df):
        style_df = pd.DataFrame('', index=df.index, columns=df.columns)
        # Only highlight if the status is 'changed' (ignores orphans)
        changed_idx = df.index[df['row_status'] == 'changed']
        
        for col in compare_columns:
            l, r = f"{col}_{left_label}", f"{col}_{right_label}"
            # Find mismatches within 'changed' rows
            mismatch = ~(df.loc[changed_idx, l].eq(df.loc[changed_idx, r]) | 
                         (df.loc[changed_idx, l].isna() & df.loc[changed_idx, r].isna()))
            
            # Apply color to the specific indices that mismatched
            style_df.loc[mismatch[mismatch].index, [l, r]] = 'background-color: #7B0000; color: white;'
        return style_df

    return final_df.style.apply(apply_color, axis=None)