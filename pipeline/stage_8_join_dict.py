"""
Stage 8: Join the diagnosis dictionary

Adds DIAGNOSIS_DESC by matching each row's (already normalized) DIAGNOSIS_CODE
against dx_dictionary's dx_code.

DECISION - codes with no match in the dictionary:
Our data has 44 distinct diagnosis codes, but the dictionary only has 40.
That means some codes genuinely have no matching description. We choose to
KEEP these rows and set DIAGNOSIS_DESC to "UNKNOWN DIAGNOSIS", rather than
dropping the row.

Why: dropping rows here would change our final row count, which we already
verified matches the target (159,704) before this stage runs. A code that
isn't in a 40-row reference dictionary doesn't mean the underlying claim or
diagnosis is invalid - it just means our dictionary is incomplete. Silently
dropping real claims because of a small reference-data gap would be a worse
outcome than showing a clear "UNKNOWN DIAGNOSIS" placeholder. This also makes
the gap visible and inspectable, instead of hiding it as a blank/null cell
that could be mistaken for a data-loading bug.

We verified the dictionary has no duplicate dx_code values, so this merge
cannot multiply rows - each row matches at most one dictionary entry.
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
from pipeline.stage_7_deduplicate import dedupe
from pipeline.print_utils import print_stage_log
from pipeline.save_utils import save_df
UNKNOWN_LABEL = "UNKNOWN DIAGNOSIS"


def join_dictionary(deduped, dx_dict, stage_log):
    rows_before = len(deduped)

    merged = deduped.merge(
        dx_dict[["dx_code", "dx_description"]],
        left_on="DIAGNOSIS_CODE",
        right_on="dx_code",
        how="left",
    )
    merged = merged.rename(columns={"dx_description": "DIAGNOSIS_DESC"})
    merged = merged.drop(columns=["dx_code"])
    merged["DIAGNOSIS_DESC"] = merged["DIAGNOSIS_DESC"].fillna(UNKNOWN_LABEL)

    unmatched_codes = sorted(
        merged.loc[merged["DIAGNOSIS_DESC"] == UNKNOWN_LABEL, "DIAGNOSIS_CODE"].unique()
    )

    stage_log.append({
        "stage": "join_dictionary",
        "rows_in": rows_before,
        "rows_out": len(merged),
        "dropped": rows_before - len(merged),
        "notes": f"Joined DIAGNOSIS_DESC from dx_dictionary. "
                 f"{len(unmatched_codes)} code(s) had no match and were labeled '{UNKNOWN_LABEL}': "
                 f"{unmatched_codes}. No rows dropped.",
    })

    return merged


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

    final = join_dictionary(deduped, raw["dict"], stage_log)

    print_stage_log(stage_log)

    print()
    print("Final row count:", len(final))
    print("Rows labeled UNKNOWN DIAGNOSIS:", (final["DIAGNOSIS_DESC"] == UNKNOWN_LABEL).sum())
    print(final[["DIAGNOSIS_CODE", "DIAGNOSIS_DESC"]].head(10))
    save_df(final, "stage_8_final")