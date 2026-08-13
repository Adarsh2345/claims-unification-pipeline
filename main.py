from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
import uuid
from datetime import datetime,timezone
from pipeline.stage_9_validate import run_pipeline, validate

app = FastAPI()


runs = {}
def build_summary(final):

    summary = []
    for src, group in final.groupby("SRC"):
        summary.append(
            {
                "SRC":src,
                "Count":len(group),
                "distinct claims":group["CLAIM_ID"].nunique()
            }
        )
    return summary

def check_reproducibility(final_run1):

    final_run2,_ = run_pipeline()

    cols = list(final_run1.columns)

    final_run1 = final_run1.sort_values(cols).reset_index(drop = True)
    final_run2=  final_run2.sort_values(cols).reset_index(drop = True)

    matches = final_run1.equals(final_run2)

    return {
        "check":"Two consecutive runs produce same output",
        "expected":True,
        "actual":matches,
        "result":"PASS" if matches else "FAIL"
    }

@app.post('/run')
def run():
    final,stage_log = run_pipeline()

    checks = validate(final)
    checks.append(check_reproducibility(final))

    run_id = str(uuid.uuid4())

    runs[run_id] = {
        "stage_log":stage_log,
        "checks":checks,
        "summary":build_summary(final),
         "created_at": datetime.now(timezone.utc).isoformat(),
    }

    return {"run_id":run_id}


@app.get("/run/{id}/stages")
def get_stages(id : str):
    if id not in runs:
        raise HTTPException(status_code = 404,detail = "Run id not found")

    return runs[id]["stage_log"]

@app.get("/run/{id}/validate")
def get_checks(id : str):
    if id not in runs:
        raise HTTPException(status_code = 404, detail = "Run id not found")

    return runs[id]["checks"]

@app.get("/summary")
def get_summary():
    if not runs:
        raise HTTPException(status_code = 404,detail ="No runs yet. Call POST /run first")
    latest_id = list(runs.keys())[-1]

    return runs[latest_id]["summary"]

app.mount("/", StaticFiles(directory="static", html=True), name="static")