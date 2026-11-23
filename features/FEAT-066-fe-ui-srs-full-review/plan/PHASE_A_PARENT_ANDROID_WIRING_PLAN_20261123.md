# Goal v4 Phase A — Parent Android wiring

Date: 2026-11-23 (Asia/Saigon)
Status: APPROVED_FOR_IMPLEMENTATION
Scope: apps/ui-mobile source and tests on feature/fe-mobile-remediation. Required feature plan, approval, context/decision/status records, and evidence remain in FEAT-066. No apps/mobile, backend, credentials, signing configuration, .env, commit, stage, stash, branch switch, or push.

## Authority and inputs

- Product baseline: FEAT-063 SRS v2.7-draft; remains unsigned. Preserve its open questions.
- Implementation contract: tmp/phase-v4/PHASE_A_FINAL_ROUTE_LIST_20261123.md sections 1, 2.3–2.10, 3.1–3.5 and 4, plus the user's final Phase A task prompt. The earlier digest is draft; final route list resolves its recheck items. The two route shapes remain tagged [PROPOSAL] in OpenAPI but are fixed for this phase.
- Source context: existing Parent application layering, API adapter, flow recovery, screen and test patterns; frozen M2 projection stays unchanged.

## Work and acceptance criteria

1. Add strict activity DTOs and optional run fields. Add GET /v1/activities and idempotent POST .../activity-selection in ParentApi, port, module and use case. Map only allow-listed codes to safe Vietnamese copy.
2. Replace the placeholder activity flow with the bounded picker. Empty results permit cancel only. Selection sends current run revision, one visible-ASCII key per user action, and same key on retry. Both race 409 codes reload the run. Last of selection/context confirmation starts story; first story never calls legacy story-revisions.
3. Surface story_confirmation_required, safe re-confirm/rewrite choices and cap behavior. Re-confirm uses a fresh key and reloads run before another video request. Handle new legacy/activity/store errors without exposing codes or server text.
4. Route safety blocks using run state plus video/job state, preserve legacy SAFETY_BLOCKED handling, and show the required exits.
5. Permit replay after Complete, show nullable post-video activities and is_main, and add history watch action through run read, token and playback. Hide unsuitable/complete/generate for completed runs.
6. Add focused Vitest coverage for routes, headers/body, error mappings, list/select/empty/races, run fields, re-confirm, safety block, completed playback and safe copy. Keep frozen projection JSON unchanged.
7. Run the six user-specified gates and report their exact results. Do not claim a pass without captured output. Leave changes unstaged and uncommitted.

## Completion checks

- npm --prefix apps/ui-mobile test (must print UI_COPY_AND_RECOVERY_VALID)
- npm --prefix apps/ui-mobile run typecheck
- python tools/validate_harness.py
- python tools/validate_repository_security.py
- python tools/validate_architecture.py
- git diff --check

No lint script or native Android tests exist in apps/ui-mobile; gradlew assembleDebug is optional and only if offline build works.
