# G6 review fixes plan — 2026-11-01

## Scope

Apply the four bounded findings from the independent G2–G6 review. This is a separate TREO KHÔNG COMMIT task; it does not resume the G2–G6 goal or change its blocked status.

### F1 — BE1 route and operation counts

- Update the two assertions in `backend/tests/integration/test_be1_postgres_api.py` from 50/55 to the observed `/api/be1/v1/` counts, expected 51 paths and 56 operations.
- Before editing, run the focused PostgreSQL OpenAPI test and independently count routes/operations from the composed application. Stop if counts differ from 51/56.

### F2 — isolate the consent monkeypatch in the durable start test

- Confirm the failing request and denial path in the PostgreSQL test before editing.
- In `test_room_code_start_revocation_stage_and_early_outcome_are_durable`, patch `consent_is_effective` in both `be1_sessions` and `be1_canvas`; the former serves session/admission gates, while the latter owns the canvas guard exercised by the accepted drawing request.
- Add a negative PostgreSQL case in the same file proving a pending-consent profile remains denied by the canvas guard when neither module is patched. Do not alter product guards or consent records.
- Stop if reproducing the failure shows a different cause or requires any additional bypass/patch.

### F3 — preserve the committed T12 report and document the discrepancy

- Copy the exact committed bytes of `evidence/notes/T12_LITE_POSTGRES_REPORT_20261101.md` from HEAD into `evidence/notes/T12_LITE_POSTGRES_REPORT_20261101_RUN1_AS_COMMITTED.md`; preserve LF and record SHA-256.
- Append an “Đối chiếu hai lượt chạy” section to the current report. Compare the committed run with the current report on cleanup of B5 replay rows. Resolve only if existing logs/count evidence proves one version; otherwise mark `MÂU THUẪN CHƯA PHÂN XỬ` and recommend a separately approved isolated check.

### F4 — run the repository-compatible Ruff checks

- Record the Ruff requirement and version sources in `backend/pyproject.toml`, CI and the installed environment.
- Run Ruff check and format-check on the Python files changed/new in G1–G6 plus F1–F2. Edit only the two paths named in the review (`backend/tests/unit/test_canvas_source_render.py` import order and `backend/tests/contract/test_openapi_contract_catalog.py` formatting) if the installed project-compatible Ruff reports the findings. Do not reformat any other file.

## Allowlist

- `backend/tests/integration/test_be1_postgres_api.py`
- `backend/tests/unit/test_canvas_source_render.py` — import ordering only, if required by the project-compatible Ruff
- `backend/tests/contract/test_openapi_contract_catalog.py` — formatting only, if required by the project-compatible Ruff
- `features/FEAT-064-current-flow-modal-vision-dev/evidence/notes/T12_LITE_POSTGRES_REPORT_20261101.md` — append-only
- `features/FEAT-064-current-flow-modal-vision-dev/evidence/notes/T12_LITE_POSTGRES_REPORT_20261101_RUN1_AS_COMMITTED.md` — new exact byte copy
- `features/FEAT-064-current-flow-modal-vision-dev/evidence/G6_REVIEW_FIXES_REPORT_20261101.md` — new
- `features/FEAT-064-current-flow-modal-vision-dev/plan/G6_REVIEW_FIXES_PLAN_20261101.md` — this plan
- `features/FEAT-064-current-flow-modal-vision-dev/status/PILOT_GOAL_LEDGER_20261101.md` — append-only task record
- `features/FEAT-064-current-flow-modal-vision-dev/approvals/TASK_APPROVAL.md` — append-only approval
- `.claude/handoff/snapshots/G6R_<timestamp>/**` — local ignored snapshot

## Exclusions

- No files under `backend/src`, schemas, migrations, OpenAPI catalog, application/product guards, or consent behavior.
- No changes for M1 (operation/time ceilings) or M3 (checkpoint blocks export); both remain owner decisions.
- No ClamAV/Lesson Library work, Modal/GPU/provider, network access, real child data, UI, B4b/B6/B7/T13, stage, commit, or push.
- PostgreSQL checks use only the owner-created disposable loopback `*_be1_acceptance` database under the pinned T12 procedure. If its safety gates fail, PostgreSQL work is NOT RUN and no replacement database is created.

## Test matrix and expected result

| Check | Before edit | After edit |
| --- | --- | --- |
| F1 OpenAPI path/operation PostgreSQL case | Run first; record actual red | Pass with exact 51/56 inventory |
| F2 durable room-code/session/canvas PostgreSQL case | Run first; record actual red and failing request | Pass after only the canvas-module test monkeypatch |
| F2 pending-consent canvas negative case | New test; expected denied response | Pass without any consent monkeypatch |
| Ruff check and format-check | Run using installed project-compatible Ruff | Pass, or record version-specific finding without changing unrelated files |
| Full backend contract and unit suites | Not a red→green comparison; run after scoped edits and compare with reviewer baseline | Report real totals and explain each difference |
| Repository validators and `git diff --check` | Not applicable | Run all four required final checks |

