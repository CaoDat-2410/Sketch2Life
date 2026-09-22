# Topic quality and T2 activity matching implementation — 2026-09-22

Feature: `FEAT-018-live-image-canvas-flow`

Plan: `plan/TOPIC_AND_T2_ACTIVITY_MATCHING_FIX_PLAN.md`

Approval: owner approval recorded in `approvals/TASK_APPROVAL.md` on 2026-09-22.

## Scope verified

This implementation addresses the owner screenshots showing a shallow topic (`grass`, `flying`,
`nature`) and a T2 screen that displayed hardcoded butterfly art while the backend had no eligible
activity. The demo remains synthetic/non-child, Android Emulator first, in-memory, image-only with
no video. Codex did not call Lightning.

## Implemented behavior

- Vision claims are ranked by reviewed role/specificity rules. Background labels are retained but do
  not outrank a visible subject.
- A closed Vietnamese display lexicon composes a grounded topic from the confirmed subject, action
  and context. Unknown labels remain visible instead of being hallucinated or silently discarded.
- Gate A preserves raw label, display label, claim IDs, confidence, source identity and reviewed
  semantic tags.
- T2 uses the existing reviewed semantic catalog through an application port. Matching order is
  exact/alias/concept-family, then one age-safe baseline fallback if no personalized match exists.
- T2 response metadata is attached at the generic workflow-result payload envelope, so
  `P1ContextOptionsV1` remains unchanged. The mobile UI marks `EXPANDED` fallback suggestions and
  retains the reason.
- The mobile flow clears stale T2 state before a new request and publishes the backend-selected
  activity only after context, filter and ExperienceSpec calls succeed. The previous butterfly-only
  placeholder/detail art is no longer used as a backend result.
- The Lightning prompt now asks the model to prioritize the specific central subject and demote
  scenery/background claims; the deterministic backend ranking remains authoritative.

## Focused evidence

Commands run from the repository root:

```text
backend\\.venv\\Scripts\\python.exe -m pytest backend/tests/contract/test_live_image_demo_api.py -q
9 passed

backend\\.venv\\Scripts\\python.exe -m pytest backend/tests/unit/test_topic_activity_matching.py backend/tests/contract/test_live_image_demo_api.py -q
11 passed before the final contract-test-only rerun

backend\\.venv\\Scripts\\python.exe -m pytest backend/tests/contract/test_live_image_demo_api.py backend/tests/unit/test_semantic_personalization_v2.py backend/tests/unit/test_catalog_expansion.py -q
27 passed

python -m ruff check <changed Python files>
All checks passed

backend\\.venv\\Scripts\\python.exe -m mypy <changed application source files>
Success: no issues found

pnpm --dir apps/ui-mobile exec tsc --noEmit
passed
```

The repository-wide backend collection was attempted with `--tb=short`, but the workstation denied
pytest fixture-temp/cache creation under the user temp directory and `backend\\.pytest_cache`, causing
setup `PermissionError`s. This environment result is recorded as a test-infrastructure limitation,
not a feature assertion failure.

## Owner-run acceptance still pending

The owner must manually start the Lightning server, run the Android Emulator flow with a synthetic
non-child image, confirm Gate A, press the real T2 CTA, and verify that the recommendation metadata,
selected activity and downstream Pixi identity remain consistent. Keep the existing approximately
25-credit ceiling. No token, endpoint, raw image, model output or child data belongs in Git/evidence.
