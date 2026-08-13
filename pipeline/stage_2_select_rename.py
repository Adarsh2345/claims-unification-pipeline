
from pipeline.stage_1_ingest import ingest
from pipeline.save_utils import save_dfs
 
def select_rename(raw, stage_log):
    df_a = raw["a"].rename(columns={
        "patient_id": "PATIENT_ID",
        "claim_id": "CLAIM_ID",
        "service_from_date": "SERVICE_DATE",
        "patient_birth_year": "BIRTH_YEAR",
        "patient_gender": "GENDER",
        "patient_zip3": "ZIP3",
        "place_of_svc_cd": "PLACE_OF_SERVICE",
        "provider_rendering_id": "RENDERING_NPI",
        "provider_referring_id": "REFERRING_NPI",
        "provider_billing_id": "BILLING_NPI",
        "primary_plan_id": "PRIMARY_PLAN_ID",
        "bill_amt": "BILLED_AMOUNT",
        "data_source": "SRC",
    })
    keep_a = ["SRC", "PATIENT_ID", "BIRTH_YEAR", "GENDER", "ZIP3", "CLAIM_ID",
              "SERVICE_DATE", "PLACE_OF_SERVICE", "RENDERING_NPI", "REFERRING_NPI",
              "BILLING_NPI", "PRIMARY_PLAN_ID", "BILLED_AMOUNT",
              "diagnosis_code_1", "diagnosis_code_2", "diagnosis_code_3",
              "diagnosis_code_4", "diagnosis_code_5", "diagnosis_code_6",
              "diagnosis_code_7", "diagnosis_code_8"]
    df_a = df_a[keep_a]
 
    df_b = raw["b"].rename(columns={
        "member_id": "PATIENT_ID",
        "encounter_id": "CLAIM_ID",
        "svc_date": "SERVICE_DATE",
        "dx_code": "DIAGNOSIS_CODE",
        "birth_yr": "BIRTH_YEAR",
        "gender": "GENDER",
        "zip3": "ZIP3",
        "pos_code": "PLACE_OF_SERVICE",
        "rendering_npi": "RENDERING_NPI",
        "referring_npi": "REFERRING_NPI",
        "billing_npi": "BILLING_NPI",
        "payer_primary": "PRIMARY_PLAN_ID",
        "billed_amount": "BILLED_AMOUNT",
        "src": "SRC",
    })
    keep_b = ["SRC", "PATIENT_ID", "BIRTH_YEAR", "GENDER", "ZIP3", "CLAIM_ID",
              "SERVICE_DATE", "PLACE_OF_SERVICE", "RENDERING_NPI", "REFERRING_NPI",
              "BILLING_NPI", "PRIMARY_PLAN_ID", "BILLED_AMOUNT", "DIAGNOSIS_CODE"]
    df_b = df_b[keep_b]
 
    df_c = raw["c"].rename(columns={
        "pt_ref": "PATIENT_ID",
        "claim_ref": "CLAIM_ID",
        "date_of_service": "SERVICE_DATE",
        "diagnosis_codes": "DIAGNOSIS_CODE",
        "yob": "BIRTH_YEAR",
        "sex": "GENDER",
        "zip_3": "ZIP3",
        "service_place": "PLACE_OF_SERVICE",
        "npi_rendering": "RENDERING_NPI",
        "npi_referring": "REFERRING_NPI",
        "npi_billing": "BILLING_NPI",
        "plan_1": "PRIMARY_PLAN_ID",
        "amount_billed": "BILLED_AMOUNT",
        "source_system": "SRC",
        "version": "VERSION",  # kept temporarily, needed by the next stage
    })
    keep_c = ["SRC", "PATIENT_ID", "BIRTH_YEAR", "GENDER", "ZIP3", "CLAIM_ID",
              "SERVICE_DATE", "PLACE_OF_SERVICE", "RENDERING_NPI", "REFERRING_NPI",
              "BILLING_NPI", "PRIMARY_PLAN_ID", "BILLED_AMOUNT", "DIAGNOSIS_CODE",
              "VERSION"]
    df_c = df_c[keep_c]
 
    # this stage only selects/renames columns - it must never change row counts
    for key, df_before, df_after in [("a", raw["a"], df_a), ("b", raw["b"], df_b), ("c", raw["c"], df_c)]:
        stage_log.append({
            "stage": f"select_rename_{key}",
            "rows_in": len(df_before),
            "rows_out": len(df_after),
            "dropped": len(df_before) - len(df_after),
            "notes": "Selected and renamed columns to common schema. No rows should change.",
        })
 
    return df_a, df_b, df_c
 
 
if __name__ == "__main__":
    raw, stage_log = ingest()
    df_a, df_b, df_c = select_rename(raw, stage_log)
 
    print(f"{'stage':<20}{'rows_in':>10}{'rows_out':>10}{'dropped':>10}   notes")
    print("-" * 90)
    for entry in stage_log:
        print(f"{entry['stage']:<20}{entry['rows_in']:>10}{entry['rows_out']:>10}"
              f"{entry['dropped']:>10}   {entry['notes']}")
 
    print()
    print("[a] columns:", list(df_a.columns))
    print("[b] columns:", list(df_b.columns))
    print("[c] columns:", list(df_c.columns))


    save_dfs({"stage_2_rename_a": df_a, "stage_2_rename_b": df_b, "stage_2_rename_c": df_c})


    