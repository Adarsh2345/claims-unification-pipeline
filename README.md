# Claims Pipeline

Unifies three differently-shaped claims source files (A, B, C) plus a
diagnosis dictionary into one combined table, exposes it through a small
API, and shows the results on a simple page.

## Project structure

```
claims_pipeline_adarsh/
├── data/                       raw input files (xlsx)
├── output/                     intermediate output saved by each stage, for inspection
├── screenshots/                screenshots for the README (run page, checks)
├── static/
│   └── index.html              the simple run page
├── pipeline/
│   ├── stage_1_ingest.py
│   ├── stage_2_select_rename.py
│   ├── stage_3_reshape.py
│   ├── stage_4_normalize.py
│   ├── stage_5_filter.py
│   ├── stage_6_combine.py
│   ├── stage_7_deduplicate.py
│   ├── stage_8_join_dict.py
│   ├── stage_9_validate.py     ties all stages together, runs the pipeline end to end
│   ├── print_utils.py          shared helper to print the stage log
│   └── save_utils.py           shared helper to save a dataframe to output/
├── main.py                     FastAPI app: the 4 endpoints + serves the page
├── requirements.txt
├── README.md
└── DESIGN_NOTES.md
```

## 1. Setup

From the project root:

```
pip install -r requirements.txt
```

Make sure the 4 source files are present in `data/`:
```
source_a_claims.csv.xlsx
source_b_claims.csv.xlsx
source_c_claims.csv.xlsx
dx_dictionary.csv.xlsx
```

## 2. Run the pipeline on its own (no API/page)

Useful for checking the pipeline works and inspecting numbers directly in
the terminal, without going through the API.

```
python -m pipeline.stage_9_validate
```

This runs all 9 stages end to end, prints the full stage log (rows in /
out / dropped / notes per stage), then prints all 10 acceptance checks as
pass/fail.

Each individual stage file can also be run on its own the same way, e.g.:
```
python -m pipeline.stage_1_ingest
python -m pipeline.stage_6_combine
```

## 3. Run the API + page

```
uvicorn main:app --reload
```

Then open:
```
http://127.0.0.1:8000/
```

Click **"Run pipeline"** on the page. This will:
1. Call `POST /run` to run the pipeline and get a `run_id`.
2. Call `GET /run/{run_id}/stages` and render the stage-by-stage row counts and drop reasons.
3. Call `GET /run/{run_id}/validate` and render the 10 acceptance checks as pass/fail.

The interactive API docs (useful for testing each endpoint individually)
are available at:
```
http://127.0.0.1:8000/docs
```

## API endpoints

| Endpoint | Description |
|---|---|
| `POST /run` | Runs the pipeline, returns `{"run_id": "..."}` |
| `GET /run/{run_id}/stages` | Per-stage rows in / out / dropped, with notes |
| `GET /run/{run_id}/validate` | The 10 acceptance checks, each pass/fail |
| `GET /summary` | Final row and claim counts per source, for the most recent run |

## Output

Every stage file, when run directly, also saves its output to `output/`
as an `.xlsx` file, so intermediate results can be opened and inspected
directly (e.g. `output/stage_6_combined.xlsx`, `output/stage_8_final.xlsx`).

## Screenshots

See `screenshots/` and `DESIGN_NOTES.md` for the run page and acceptance
checks output.
