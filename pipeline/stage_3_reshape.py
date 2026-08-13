
from pipeline.stage_1_ingest import ingest
from pipeline.stage_2_select_rename import select_rename
from pipeline.save_utils import save_dfs
 
def reshape_a(df_a, stage_log):
    other_cols = [c for c in df_a.columns if not c.startswith("diagnosis_code_")]
    diag_cols = [c for c in df_a.columns if c.startswith("diagnosis_code_")]
 
    melted = df_a.melt(
        id_vars=other_cols,
        value_vars=diag_cols,
        value_name="DIAGNOSIS_CODE",
    )
    melted = melted.drop(columns=["variable"])          # melt() adds this, we don't need it
    melted = melted.dropna(subset=["DIAGNOSIS_CODE"])   # drop empty diagnosis slots
 
    stage_log.append({
        "stage": "reshape_a",
        "rows_in": len(df_a),
        "rows_out": len(melted),
        "dropped": len(df_a) - len(melted),
        "notes": "Unpivoted diagnosis_code_1..8 into one row per diagnosis. "
                 "'dropped' here is negative (rows increased) because one claim row "
                 "becomes multiple diagnosis rows; empty diagnosis slots were removed.",
    })
    return melted
 
 
def reshape_b(df_b, stage_log):
    stage_log.append({
        "stage": "reshape_b",
        "rows_in": len(df_b),
        "rows_out": len(df_b),
        "dropped": 0,
        "notes": "Already one row per diagnosis code. No reshape needed.",
    })
    return df_b
 
 
def reshape_c(df_c, stage_log):
    rows_in = len(df_c)
 
    # Step 1: keep only the latest version of each claim
    latest_idx = df_c.groupby("CLAIM_ID")["VERSION"].idxmax()
    latest = df_c.loc[latest_idx].drop(columns=["VERSION"])
 
    stage_log.append({
        "stage": "reshape_c_latest_version",
        "rows_in": rows_in,
        "rows_out": len(latest),
        "dropped": rows_in - len(latest),
        "notes": "Kept only the highest VERSION per CLAIM_ID (dropped superseded resubmissions).",
    })
 
    # Step 2: split the pipe-delimited diagnosis string into separate rows
    rows_before_split = len(latest)
    latest = latest.copy()
    latest["DIAGNOSIS_CODE"] = latest["DIAGNOSIS_CODE"].str.split("|")
    exploded = latest.explode("DIAGNOSIS_CODE")
    exploded["DIAGNOSIS_CODE"] = exploded["DIAGNOSIS_CODE"].str.strip()
 
    stage_log.append({
        "stage": "reshape_c_split_codes",
        "rows_in": rows_before_split,
        "rows_out": len(exploded),
        "dropped": rows_before_split - len(exploded),
        "notes": "Split the pipe-delimited DIAGNOSIS_CODE string into one row per code. "
                 "'dropped' here is negative (rows increased) since one row can hold several codes.",
    })
    return exploded
 
 
if __name__ == "__main__":
    raw, stage_log = ingest()
    df_a, df_b, df_c = select_rename(raw, stage_log)
 
    df_a = reshape_a(df_a, stage_log)
    df_b = reshape_b(df_b, stage_log)
    df_c = reshape_c(df_c, stage_log)
 
    print(f"{'stage':<28}{'rows_in':>10}{'rows_out':>10}{'dropped':>10}   notes")
    print("-" * 110)
    for entry in stage_log:
        print(f"{entry['stage']:<28}{entry['rows_in']:>10}{entry['rows_out']:>10}"
              f"{entry['dropped']:>10}   {entry['notes']}")
 
    print()
    print("[a] rows:", len(df_a), " columns:", list(df_a.columns))
    print("[b] rows:", len(df_b), " columns:", list(df_b.columns))
    print("[c] rows:", len(df_c), " columns:", list(df_c.columns))

    save_dfs({"stage_3_reshape_a": df_a, "stage_3_reshape_b": df_b, "stage_3_reshape_c": df_c})