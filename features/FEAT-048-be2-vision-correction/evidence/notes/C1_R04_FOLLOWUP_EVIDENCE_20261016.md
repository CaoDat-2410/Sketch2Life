# BE2-02 C1-R04 follow-up evidence (Codex re-review) — 2026-10-16

- Input: `notes/C1_CODEX_REREVIEW_20261016.md` (NEEDS_REVISION, only C1-R04 open, P2) and its
  ignored probes under `evidence/local/codex-rereview-20261016/`.
- Scope: the two remaining reference-guard bypasses in `observation_bounds_violation` only.
  R01/R02/R03/R05/R06 stay CLOSED_C1_COMPONENT_SCOPE by Codex; their tests are unchanged.
- Authority: existing C1 approval and plan snapshot `plan/PLAN_REV1_APPROVED.md`
  (SHA256 `f4733c88…`), both unchanged. Executor disposition for R04:
  **FIXED_PENDING_CODEX_REVIEW** (not CLOSED). BE2-02 remains IN_PROGRESS.
- Earlier implementation/fix reports and both Codex reviews are kept unchanged as history.

## Identity before editing

Branch `feature/be2-02-vision-correction`, HEAD = base `6dcc57ee…`, 0 staged paths. All 19
source/test hashes matched `metrics/C1_CODEX_REREVIEW_20261016.json` (0 mismatches). Imports
pinned to this worktree's `backend/src` (`sketch2life.__file__` verified); Python 3.12.10,
`-B`, `PYTHONDONTWRITEBYTECODE=1`, fresh `--basetemp` under ignored
`evidence/local/claude-r04-followup-20261016/`. No install, network, provider, model, service.

## Change (domain only)

`backend/src/sketch2life/domain/vision_analysis.py`, `observation_bounds_violation`:

1. Optional action refs are collected with `if ref is not None` instead of `if ref`, so an empty
   `actor_ref`/`object_ref` is checked like every other reference (and rejected); `None` stays
   the only "absent" value.
2. The shared reference check uses `_OBSERVATION_REF.fullmatch(ref)` instead of `.match(ref)`,
   so a trailing newline no longer satisfies the `$` anchor. This one loop covers every
   reference kind using the guard: entity/action/relation/theme/ambiguous ids, action
   actor/object refs, relation subject/object refs and theme evidence refs — matching the
   DATA-22 `ObservationRef` pattern and 120 length bound.

Nothing is stripped, normalised or dropped; the DTO, bridge, legacy adapter and foundation
contracts are unchanged. A violation stays `OUTPUT_MALFORMED` before persistence (service guard
for any provider; bridge guard for legacy output).

## Regression (existing file `backend/tests/unit/test_vision_analysis_review_fixes.py`)

Through the supported typed (fake) provider seam:

- `test_r04_final_newline_or_empty_reference_is_malformed_before_storage` — 14 cases: trailing
  newline on each of the 5 id kinds and 5 reference kinds, empty `actor_ref`, `object_ref`,
  `subject_ref`, theme evidence ref. Asserts guard token `OBSERVATION_REF_INVALID`, observation
  `failed/OUTPUT_MALFORMED`, no head/observation/provider result stored, CMD-34 POST is a typed
  404 with no correction/receipt/invalidation (no post-commit 500 path).
- `test_r04_none_and_valid_references_are_accepted_and_project` — 5 cases: all valid, actor None,
  object None, both None, 120-character refs. Accepted; CMD-34 200, replay 200 with
  `Idempotency-Replayed: true`, `AnalysisRecordV1` valid.

Existing 120/256 boundary and bridge→API/replay regressions are unchanged and pass.

| Run (UTC) | Source | Result |
|---|---|---|
| 13:51:50Z before | unfixed (domain sha256 `711a06e6…f45588`) | 19 collected: **12 failed** (all 10 trailing-newline cases, empty actor/object ref), 7 passed (empty required refs were already rejected; positives) — `before/r04-followup-before.xml` + `.log` |
| 13:52:19Z after | fixed | 19 collected: **19 passed** — `after/r04-followup-after.xml` |
| Codex probes after | fixed | `r04_optional_refs_probe.py`: none/valid/120 accepted with valid record; empty/final_newline/121 → `failed/OUTPUT_MALFORMED` for both actor_ref and object_ref. `r04_final_newline_probe.py` now stops at its own `assert result.analysis_id is not None` because no analysis is stored (intended). Outputs in `after/codex_*.after.txt` |

## Final checks (UTC 2026-10-16)

| Check | Result |
|---|---|
| Focused C1 suite 13:52:20Z (8 files) | 233 collected: **232 passed, 1 skipped** (Pillow, NOT_RUN), 0 failed |
| Codex original six service probes 13:52:24Z | 6 passed, 3 deselected |
| Legacy Vision regression 13:52:22Z (bridge uses the guard) | 238: 233 passed, 5 pre-existing skips |
| BE2-01 regression | NOT rerun: no BE2-01-facing code changed (domain guard only); last result 337/338 + 1 Pillow skip |
| ruff / mypy strict (2 changed paths) | PASS / PASS |
| Validators | see `metrics/C1_R04_FOLLOWUP_CHECKS_20261016.json` |

## Unchanged / NOT_RUN

- Pillow-dependent live-app route walk and V2 server test: NOT_RUN (Pillow absent).
- N01 body buffering (P3), legacy F-01 containment, the qualified overlapping
  invalidation/replay concurrency note: unchanged, no new batch.
- Observation (not fixed, outside the R04 reference guard): other domain hash checks such as
  `_require_sha` also use `re.match` with `$`; their inputs come from trusted ports or are
  recomputed, and the review did not raise them.
