"""
Stage 4: Normalize values

Three separate things get standardized here, one per rule from the spec:

1. DIAGNOSIS_CODE -> uppercase, no dots, no stray whitespace.
   Source A: "E03.9"  -> "E039"
   Source B: "K5900"  -> "K5900" (already clean, unaffected)
   Source C: "h25.13" -> "H2513"
   This must happen BEFORE deduplication (a later stage) - otherwise two
   codes that are really the same thing but formatted differently would
   look like different values and slip past a duplicate check.

2. SERVICE_DATE -> a real date type for all three sources.
   Source A stores it as an integer like 20231002 (YYYYMMDD) - this gets
   parsed into an actual date. B and C are already proper dates, so they
   pass through unchanged.

3. GENDER -> normalized to "M" or "F" for all three sources.
   Source A: already "M"/"F", left as-is.
   Source C: "Male"/"Female" -> "M"/"F", a direct, unambiguous mapping.
   Source B: uses "1"/"2" with no key provided anywhere in the data.
   ASSUMPTION (documented, not verified): we map 1 -> M and 2 -> F,
   following the common ISO 5218 convention (1=male, 2=female) used in
   many claims/EHR systems. This is a judgment call since Source B gives
   us no dictionary to confirm it - flagged here and in DESIGN_NOTES.md
   as something we assumed rather than proved.
"""

import pandas as pd
from pipeline.stage_1_ingest import ingest
from pipeline.stage_2_select_rename import select_rename
from pipeline.stage_3_reshape import reshape_a, reshape_b, reshape_c
from pipeline.print_utils import print_stage_log
from pipeline.save_utils import save_dfs


def normalize_diagnosis_code(df):
    df = df.copy()
    df["DIAGNOSIS_CODE"] = (
        df["DIAGNOSIS_CODE"]
        .str.upper()
        .str.replace(".", "", regex=False)
        .str.strip()
    )
    return df


def normalize_service_date_a(df):
    df = df.copy()
    # 20231002 -> "20231002" -> parsed as YYYYMMDD into a real date
    df["SERVICE_DATE"] = pd.to_datetime(df["SERVICE_DATE"].astype(str), format="%Y%m%d")
    return df


def normalize_gender(df, mapping):
    df = df.copy()
    df["GENDER"] = df["GENDER"].astype(str).map(mapping)
    return df


def normalize(df_a, df_b, df_c, stage_log):
    rows_a_before, rows_b_before, rows_c_before = len(df_a), len(df_b), len(df_c)

    df_a = normalize_diagnosis_code(df_a)
    df_b = normalize_diagnosis_code(df_b)
    df_c = normalize_diagnosis_code(df_c)

    df_a = normalize_service_date_a(df_a)
    # df_b and df_c SERVICE_DATE are already real dates - nothing to do

    df_a = normalize_gender(df_a, {"M": "M", "F": "F"})
    df_b = normalize_gender(df_b, {"1": "M", "2": "F"})   # ASSUMPTION, see notes above
    df_c = normalize_gender(df_c, {"Male": "M", "Female": "F"})

    # normalization never adds/removes rows - just cleans values in place
    for key, before, after in [("a", rows_a_before, len(df_a)),
                                ("b", rows_b_before, len(df_b)),
                                ("c", rows_c_before, len(df_c))]:
        stage_log.append({
            "stage": f"normalize_{key}",
            "rows_in": before,
            "rows_out": after,
            "dropped": before - after,
            "notes": "Normalized DIAGNOSIS_CODE (upper, no dots), SERVICE_DATE (real date), "
                     "GENDER (M/F). No rows added or removed.",
        })

    return df_a, df_b, df_c


if __name__ == "__main__":
    raw, stage_log = ingest()
    df_a, df_b, df_c = select_rename(raw, stage_log)
    df_a = reshape_a(df_a, stage_log)
    df_b = reshape_b(df_b, stage_log)
    df_c = reshape_c(df_c, stage_log)

    df_a, df_b, df_c = normalize(df_a, df_b, df_c, stage_log)

    print_stage_log(stage_log)

    print()
    print("A sample:")
    print(df_a[["DIAGNOSIS_CODE", "SERVICE_DATE", "GENDER"]].head(5))
    print("\nB sample:")
    print(df_b[["DIAGNOSIS_CODE", "SERVICE_DATE", "GENDER"]].head(5))
    print("\nC sample:")
    print(df_c[["DIAGNOSIS_CODE", "SERVICE_DATE", "GENDER"]].head(5))

    save_dfs({"stage_4_normalized_a":df_a,"stage_4_normalized_b":df_b,"stage_4_normalized_c":df_c})

