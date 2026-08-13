import pandas as pd
from pipeline.stage_1_ingest import ingest
from pipeline.stage_2_select_rename import select_rename
from pipeline.stage_3_reshape import reshape_a, reshape_b, reshape_c
from pipeline.print_utils import print_stage_log
from pipeline.save_utils import save_df
from pipeline.stage_4_normalize import normalize
from pipeline.stage_5_filter import filter_all

 
 
def combine(df_a, df_b, df_c, stage_log):
    rows_before = len(df_a) + len(df_b) + len(df_c)
 
    combined = pd.concat([df_a, df_b, df_c], ignore_index=True)
 
    stage_log.append({
        "stage": "combine",
        "rows_in": rows_before,
        "rows_out": len(combined),
        "dropped": rows_before - len(combined),
        "notes": "Stacked the three sources into one table. Same columns, "
                 "same grain already - nothing dropped here.",
    })
 
    return combined
 
 
if __name__ == "__main__":
    raw, stage_log = ingest()
    df_a, df_b, df_c = select_rename(raw, stage_log)
    df_a = reshape_a(df_a, stage_log)
    df_b = reshape_b(df_b, stage_log)
    df_c = reshape_c(df_c, stage_log)
    df_a, df_b, df_c = normalize(df_a, df_b, df_c, stage_log)
    df_a, df_b, df_c = filter_all(df_a, df_b, df_c, stage_log)
 
    combined = combine(df_a, df_b, df_c, stage_log)
 
    print_stage_log(stage_log)
 
    print()
    print("Combined table:", combined.shape)
    print(combined["SRC"].value_counts())
    print()
    print(combined.head(5))

    save_df(combined,"stage_6_combined")
    