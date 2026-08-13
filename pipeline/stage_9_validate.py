"""
Stage 9: Validate

Runs the 10 acceptance checks from the spec against the final table and
reports each as pass/fail, alongside the actual value found and the
expected value.

This does not change the data at all - it only inspects the final table
and reports what it finds. This is exactly what GET /run/{id}/validate
will call later.

Check 10 (two consecutive runs produce identical output) is handled
differently from the rest - it re-runs the entire pipeline a second time
from scratch and compares the two results, rather than inspecting a
single result. This is the only check that needs two runs to even make
sense.
"""

import pandas as pd
from pipeline.stage_1_ingest import ingest
from pipeline.stage_2_select_rename import select_rename
from pipeline.stage_3_reshape import reshape_a, reshape_b, reshape_c
from pipeline.print_utils import print_stage_log
from pipeline.save_utils import save_df
from pipeline.stage_4_normalize import normalize
from pipeline.stage_5_filter import filter_all,DATE_MIN, DATE_MAX
from pipeline.stage_6_combine import combine
from pipeline.stage_7_deduplicate import dedupe
from pipeline.stage_8_join_dict import join_dictionary



def run_pipeline():
    """Runs the full pipeline start to finish, returns (final_df, stage_log)."""
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
    return final, stage_log


def validate(final):
    """Runs checks 1-9 against a single final table. Returns a list of check results."""
    checks = []

    def add_check(number, name, expected, actual):
        checks.append({
            "check": f"#{number} {name}",
            "expected": expected,
            "actual": actual,
            "result": "PASS" if expected == actual else "FAIL",
        })

    add_check(1, "Total rows in final output", 159704, len(final))
    add_check(2, "Distinct claims across all sources", 68205, final["CLAIM_ID"].nunique())
    add_check(3, "Distinct patients", 11963, final["PATIENT_ID"].nunique())
    add_check(4, "Distinct diagnosis codes", 44, final["DIAGNOSIS_CODE"].nunique())

    p00042 = final[final["PATIENT_ID"] == "P00042"]
    add_check(5, "Patient P00042 - distinct diagnosis codes", 7, p00042["DIAGNOSIS_CODE"].nunique())
    add_check(6, "Patient P00042 - total rows", 7, len(p00042))

    no_dots_all_upper = (
        (~final["DIAGNOSIS_CODE"].str.contains(".", regex=False)) &
        (final["DIAGNOSIS_CODE"] == final["DIAGNOSIS_CODE"].str.upper())
    ).all()
    add_check(7, "No DIAGNOSIS_CODE contains a dot; all uppercase", True, bool(no_dots_all_upper))

    dates_in_range = ((final["SERVICE_DATE"] >= DATE_MIN) & (final["SERVICE_DATE"] <= DATE_MAX)).all()
    add_check(8, "All SERVICE_DATE between 2018-01-01 and 2025-02-28", True, bool(dates_in_range))

    no_empty_patient = final["PATIENT_ID"].notna().all()
    add_check(9, "No row has an empty PATIENT_ID", True, bool(no_empty_patient))

    return checks


def validate_reproducibility():
    """Check #10: run the pipeline twice, confirm identical output."""
    run1, _ = run_pipeline()
    run2, _ = run_pipeline()

    run1_sorted = run1.sort_values(list(run1.columns)).reset_index(drop=True)
    run2_sorted = run2.sort_values(list(run2.columns)).reset_index(drop=True)

    identical = run1_sorted.equals(run2_sorted)

    return {
        "check": "#10 Two consecutive runs produce identical output",
        "expected": True,
        "actual": identical,
        "result": "PASS" if identical else "FAIL",
    }


if __name__ == "__main__":
    final, stage_log = run_pipeline()

    checks = validate(final)
    checks.append(validate_reproducibility())

    print_stage_log(stage_log)

    print()
    print(f"{'check':<55}{'expected':>12}{'actual':>12}{'result':>8}")
    print("-" * 90)
    for c in checks:
        print(f"{c['check']:<55}{str(c['expected']):>12}{str(c['actual']):>12}{c['result']:>8}")

    passed = sum(1 for c in checks if c["result"] == "PASS")
    print()
    print(f"{passed}/{len(checks)} checks passed")