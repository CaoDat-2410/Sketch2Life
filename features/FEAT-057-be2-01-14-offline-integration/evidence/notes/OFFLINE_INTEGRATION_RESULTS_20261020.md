# BE2-01–14 offline integration results — 2026-10-20

## Candidate and merge

- Candidate branch: `feature/be2-01-14-integration`, based on
  `feature/be2-01-07` at `9d1ed184f31ab6b1f18337a1e29bb04fd59aa1b5`.
- Merge commit: `abe3c357e2c40c694317ead6cf9a1b7c479e3f6e` with parents
  `8e569598f9c58bfbcfb2e54bc13e6077d7158d50` and
  `42a6d3122259e6b33133673a2e444deefa45d387`.
- Integrated source: `origin/feature/be2-08-14` at
  `42a6d3122259e6b33133673a2e444deefa45d387`.
- Common base: `6dcc57ee0b3d053f071c8c92e72aaaee2e98d899`.
- The merge preserves both histories. The only conflicts were the two context
  ledgers; both branch-specific blocks were verified present after resolution.
  See `MERGE_CONFLICT_RESOLUTION_20261020.md`.
- Four administrative FEAT number collisions from the split allocations are
  mapped by BE2 card and full directory path in `artifacts/FEATURE_ID_COLLISION_MAP.md`;
  frozen paths and test pins are unchanged.
- Task 7 already equals its requested PR target (`feature/be2-01-07`), so that PR
  has no diff.

## Card-owned offline runners

| Card | Result on merged candidate | Selected test result | SQL in this run |
|---|---|---:|---|
| BE2-08 | PASS | 459 owned + 1,435 regression | 11 collected, not executed |
| BE2-09 | PASS | 458 owned + 1,894 regression | 21 collected, not executed |
| BE2-10 | PASS | 253 owned + 2,352 regression | 14 collected, not executed |
| BE2-11 | PASS | 219 owned + 2,605 regression + 25 legacy catalog | 17 collected, not executed |
| BE2-12 | BLOCKED by environment | 476/477 passed; one app-route test could not initialize | Not reached |
| BE2-13 | PASS | 194 owned + 2,849 regression | 11 collected, not executed |
| BE2-14 | BLOCKED by dependent environment check | 1,061 owned + 114 foundation passed; its 477-case regression delegates to BE2-12 | Not run |

Five of seven card runners pass on the combined source. Exact summary JSON and
JUnit receipts for all seven attempts are in `evidence/raw/component-runs/`; the
SHA-256-bound matrix is `evidence/metrics/offline-test-matrix.json`.

The backend test virtual environment has Python 3.12.10, pytest 8.4.2, Ruff,
Mypy, and Alembic, but lacks `python-multipart`, which is declared by
`backend/pyproject.toml`. The BE2-12 runner's only failing test is
`test_live_app_routes_have_no_candidate_job_route`: importing the existing
FastAPI app raises because the dependency is absent. BE2-14's delegated
regression check returns the same failure. The package was not installed. Pillow
12.1.0, within the declared project range, was already available in the system
Python; a copy of only that package was placed under ignored `.runtime/` so the
decoder/component suites could run without altering either shared virtual
environment.

A full backend suite was attempted but not completed: its collection also needs
`python-multipart` and optional packages used by unrelated legacy tests. It is
not counted as a pass. The selected card runners are the verified combined
regression evidence for this candidate.

## Migration graph and external gates

Alembic reports nine heads: `20261014_0004` (`be1_core`), `20261015_ai_0001`
(`ai_jobs`), `20261017_lc_0001` (`learning_content`), `20261018_ap_0009`
(`ai_policy`), `20261018_kv_0001` (`knowledge_video`), `20261018_vr_0001`
(`video_review`), `20261019_ae_0001` (`activity_execution`), `20261019_pa_0001`
(`preset_automation`), and `20261019_vf_0001` (`video_failure`). Offline SQL
generation for `upgrade heads` succeeded using a placeholder URL and emitted
79,021 bytes. No database connection or migration was run.

The aggregate PostgreSQL, real owner adapters, providers, and Lightning campaign
remain NOT_RUN. Each BE2-08–14 status remains `IN_PROGRESS` or
`IN_PROGRESS_PENDING_EXTERNAL`; this candidate does not accept any card or close
runtime/adoption gates.
