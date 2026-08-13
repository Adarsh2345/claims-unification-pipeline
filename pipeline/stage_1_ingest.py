

import pandas as pd

DATA_DIR = "data"


def ingest():
    """
    Loads the 4 raw files untouched.
    Returns:
        raw: dict of dataframes {'a', 'b', 'c', 'dict'}
        stage_log: list of dicts recording rows in/out for this stage
    """
    files = {
        "a": "source_a_claims.csv.xlsx",
        "b": "source_b_claims.csv.xlsx",
        "c": "source_c_claims.csv.xlsx",
        "dict": "dx_dictionary.csv.xlsx",
    }

    raw = {}
    stage_log = []

    for key, filename in files.items():
        df = pd.read_excel(f"{DATA_DIR}/{filename}")
        raw[key] = df

        # rows_in == rows_out on purpose: this stage doesn't drop anything
        stage_log.append({
            "stage": f"ingest_{key}",
            "rows_in": len(df),
            "rows_out": len(df),
            "dropped": 0,
            "notes": f"Loaded {filename} as-is, no changes applied.",
        })

    return raw, stage_log


if __name__ == "__main__":
    raw, stage_log = ingest()

    print(f"{'stage':<15}{'rows_in':>10}{'rows_out':>10}{'dropped':>10}   notes")
    print("-" * 80)
    for entry in stage_log:
        print(f"{entry['stage']:<15}{entry['rows_in']:>10}{entry['rows_out']:>10}"
              f"{entry['dropped']:>10}   {entry['notes']}")

    print()
    for key, df in raw.items():
        print(f"[{key}] rows={len(df)}, columns={df.shape[1]}")