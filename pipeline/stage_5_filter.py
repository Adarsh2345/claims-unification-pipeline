import pandas as pd

from pipeline.stage_1_ingest import ingest
from pipeline.stage_2_select_rename import select_rename
from pipeline.stage_3_reshape import reshape_a, reshape_b, reshape_c
from pipeline.print_utils import print_stage_log
from pipeline.save_utils import save_dfs
from pipeline.stage_4_normalize import normalize

DATE_MIN = pd.Timestamp("2018-01-01")
DATE_MAX = pd.Timestamp("2025-02-28")
 
 
def filter_source(df, key, stage_log):
    # Step 1: drop rows with missing PATIENT_ID
    rows_before = len(df)
    df = df[df["PATIENT_ID"].notna()]
    stage_log.append({
        "stage": f"filter_{key}_missing_patient",
        "rows_in": rows_before,
        "rows_out": len(df),
        "dropped": rows_before - len(df),
        "notes": "Dropped rows with no PATIENT_ID.",
    })
 
    # Step 2: drop rows outside the allowed date range
    rows_before = len(df)
    df = df[(df["SERVICE_DATE"] >= DATE_MIN) & (df["SERVICE_DATE"] <= DATE_MAX)]
    stage_log.append({
        "stage": f"filter_{key}_date_range",
        "rows_in": rows_before,
        "rows_out": len(df),
        "dropped": rows_before - len(df),
        "notes": f"Dropped rows with SERVICE_DATE outside {DATE_MIN.date()} to {DATE_MAX.date()}.",
    })
 
    return df
 
 
def filter_all(df_a, df_b, df_c, stage_log):
    df_a = filter_source(df_a, "a", stage_log)
    df_b = filter_source(df_b, "b", stage_log)
    df_c = filter_source(df_c, "c", stage_log)
    return df_a, df_b, df_c
 
 
if __name__ == "__main__":
    raw, stage_log = ingest()
    df_a, df_b, df_c = select_rename(raw, stage_log)
    df_a = reshape_a(df_a, stage_log)
    df_b = reshape_b(df_b, stage_log)
    df_c = reshape_c(df_c, stage_log)
    df_a, df_b, df_c = normalize(df_a, df_b, df_c, stage_log)
 
    df_a, df_b, df_c = filter_all(df_a, df_b, df_c, stage_log)
 
    print_stage_log(stage_log)
 
    print()
    print(f"Rows remaining -> A: {len(df_a)}  B: {len(df_b)}  C: {len(df_c)}")


    save_dfs({"stage_5_filtered_a":df_a,"stage_5_filtered_b":df_b,"stage_5_filtered_c":df_c})