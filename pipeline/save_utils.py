"""
Shared helper to dump dataframes to Excel after any stage, so you can
open them up in Excel/VS Code and eyeball what a stage actually produced.

Files get written to an "output/" folder in the project root.
"""

import os

OUTPUT_DIR = "output"


def save_df(df, name):
    """Save a single dataframe to output/<name>.xlsx"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    path = os.path.join(OUTPUT_DIR, f"{name}.xlsx")
    df.to_excel(path, index=False)
    print(f"Saved {path}  ({len(df)} rows, {df.shape[1]} columns)")


def save_dfs(named_dfs: dict):
    """Save multiple dataframes at once. named_dfs = {"a": df_a, "b": df_b, ...}"""
    for name, df in named_dfs.items():
        save_df(df, name)