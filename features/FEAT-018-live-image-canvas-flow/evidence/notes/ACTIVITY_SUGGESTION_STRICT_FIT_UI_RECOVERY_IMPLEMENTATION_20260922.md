# Activity suggestion strict-fit and UI recovery implementation evidence

Date: 2026-09-22

Feature: `FEAT-018-live-image-canvas-flow`

Plan: `plan/ACTIVITY_SUGGESTION_STRICT_FIT_UI_RECOVERY_PLAN.md`

## Implemented behavior

- `P1ExperienceCompiler.context_options` now rejects token-overlap candidates unless the same
  authoritative continuity and fit evaluation used by ExperienceSpec returns `PASS`.
- The reviewed semantic resolver ranks exact, alias, then age-baseline candidates; it evaluates each
  with compiler fit policy and continues after a rejection until the first reviewed `PASS`.
- Semantic matches still require compatible anchor kind. Direct label continuity is bypassed only by
  reviewed semantic evidence, not by loose token overlap.
- Existing hard adult-context rules and exact activity/template/objective identity checks remain in
  `select`, `compile`, and Gate B.
- BaoVC guards the complete P1 request chain with a synchronous ref lock, does not clear a previous
  valid result before success, and reopens prepared results without issuing another request.
- Expected P1/fit/version/session failures are mapped from closed reason codes to bounded Vietnamese
  guidance; internal exceptions, prompts, paths, credentials, and media are not exposed.

## Regression evidence

- A butterfly anchor with reviewed tags `động vật` and `chuyển động` does not expose `ACT-0029`.
- The same butterfly HTTP workflow resolves reviewed fallback `ACT-0026`, passes P1 filtering,
  prepares ExperienceSpec, reaches `GATE_B_PENDING`, and preserves exact option/spec identity.
- A deterministic unit test forces the highest-ranked candidate to `REJECT` and confirms the next
  reviewed age fallback is selected.
- Existing exact `cây` behavior remains available after strict discovery was introduced.

## Verification commands and results

```text
python -m pytest -q backend/tests/unit/test_topic_activity_matching.py \
  backend/tests/unit/test_p1_experience.py \
  backend/tests/contract/test_live_image_demo_api.py
PASS

python -m pytest -q backend/tests
PASS to 100%; 6 configured skips

ruff check <changed backend modules and tests>
All checks passed

mypy <changed backend service modules>
Success: no issues found in 3 source files

pnpm --dir apps/ui-mobile exec tsc --noEmit
PASS

python tools/validate_architecture.py
ARCHITECTURE_VALID

python tools/validate_repository_security.py
REPOSITORY_SECURITY_VALID; publishable_files_scanned=1530

git diff --check
PASS
```

`tools/validate_harness.py` also ran. It reported only that the unrelated, user-owned
`features/FEAT-026-current-system-srs` worktree content is missing `evidence/raw` and
`evidence/metrics`. FEAT-026 was not modified or staged for this task.

No Lightning, Qwen, ASR, video, external network, or credit-consuming request was made during this
implementation or verification.
