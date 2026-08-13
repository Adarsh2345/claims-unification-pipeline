"""
Stage 7: Deduplicate

The target grain is: one row per (SRC, CLAIM_ID, DIAGNOSIS_CODE).
There must be no duplicates at that grain.

We already normalized DIAGNOSIS_CODE (Stage 4) before combining (Stage 6),
so any two rows that are "the same diagnosis on the same claim" - even if
they were originally formatted differently in the source file - now look
identical and will be caught here. Doing dedupe in this order (normalize
first, dedupe after) is deliberate - see stage_4_normalize.py for why.

We saw a real example of this earlier: claim A0018349 in Source A listed
diagnosis R97.20 twice across its 8 diagnosis columns. After unpivoting,
that became two identical rows - exactly what this stage removes.
"""

import pandas as pd
from pipeline.stage_1_ingest import ingest
from pipeline.stage_2_select_rename import select_rename
from pipeline.stage_3_reshape import reshape_a, reshape_b, reshape_c
from pipeline.print_utils import print_stage_log
from pipeline.save_utils import save_df
from pipeline.stage_4_normalize import normalize
from pipeline.stage_5_filter import filter_all
from pipeline.stage_6_combine import combine

GRAIN = ["SRC", "CLAIM_ID", "DIAGNOSIS_CODE"]


def dedupe(combined, stage_log):
    rows_before = len(combined)

    deduped = combined.drop_duplicates(subset=GRAIN, keep="first")

    stage_log.append({
        "stage": "dedupe",
        "rows_in": rows_before,
        "rows_out": len(deduped),
        "dropped": rows_before - len(deduped),
        "notes": f"Dropped duplicate rows at the grain {GRAIN}. "
                 "Kept the first occurrence of each duplicate.",
    })

    return deduped


if __name__ == "__main__":
    raw, stage_log = ingest()
    df_a, df_b, df_c = select_rename(raw, stage_log)
    df_a = reshape_a(df_a, stage_log)
    df_b = reshape_b(df_b, stage_log)
    df_c = reshape_c(df_c, stage_log)
    df_a, df_b, df_c = normalize(df_a, df_b, df_c, stage_log)
    df_a, df_b, df_c = filter_all(df_a, df_b, df_c, stage_log)
    combined = combine(df_a, df_b, df_c, stage_log)

    deduped = dedupe(combined, stage_log)

    print_stage_log(stage_log)

    print()
    print("Final row count after dedupe:", len(deduped))
    print("Distinct claims:", deduped["CLAIM_ID"].nunique())
    print("Distinct diagnosis codes:", deduped["DIAGNOSIS_CODE"].nunique())

    from save_utils import save_df
    save_df(deduped, "stage_7_deduped")