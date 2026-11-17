# E08 — C4 local verification, synthetic full-frame fixture and acceptance audit

2026-10-18 Asia/Saigon; parent d55e9ca; approved revision1 P4/P5 preparation.
No production source/shared contract/migration changed in this checkpoint.

## Final one-batch observation

- Existing backend venv Python invoked own src/run_component_checks.py from root.
  Final status PASS/exit0, local component only.459 own +1435 existing=1894 cases,
  zero failures/errors/skips. Own2.592s, regression8.612s.23 existing regression
  warnings (native-negative Pydantic cases/legacy Alembic), not new failures.
- Own459 = prior422 +24 runner checks +13 actual synthetic full-frame GIF fixture
  checks. Source/node count growth is test scaffolding, not new product features.
- SQL11 exact node collection only, COLLECTED_NOT_RUN. No SQL fixture/migration/
  provider/selected-runtime decoder execution or service provisioning. Runner
  strips inherited KV08 opt-in/URL from children and has no SQL execution flag.
- Ruff all19 owned sources, own suites/prepared integration/fixture helper/runner/
  own migration/Alembic env PASS. Mypy19 PASS; architecture/feature harness/security/
  whitespace PASS. Frozen plan hash unchanged, approval checked by runner.
- 702 source/config/approval/inventory/tool files re-enumerated before/after, exact
  path+SHA256 map unchanged=True. Map retained in private summary. Includes all
  backend Python and feature source scripts; excludes mutable report prose.
  This is broader than earlier backend-only643 inventory, not a comparable count.
- Ignored private receipt directory:
  `.runtime/knowledge-video-component/20261018-071229-160151/`.
  summary.json SHA256858ff22b1f43358242498a304995b2f1379335ee78adf096948eb1cab122aa5d;
  owned.xml SHA25688da130db4cbf88f8e936156415774b97c18e17e69bb9030678b19e8134b4a6f;
  regression.xml SHA256bce9e9bbe16ba47f40a29b4aaf83406d6544eb9027d0c6dcac00e5c30de4ab70.
- Exact collection counts/node digests pinned in src/TEST_INVENTORY.json. No
  automatic rebaseline or skip-as-PASS behavior. Collection/execution failures,
  missing/extra/duplicate cases, wrong pin or changed source cannot pass.

## Initial runner findings retained

First full runner at `.runtime/knowledge-video-component/20261018-071039-811475/`
returned FAIL although own458/regression1435 test processes passed. The reused
inventory helper normalized backslashes in parameter bytes as path separators,
causing identity mismatch; Ruff root cwd also misclassified backend first-party
imports. Own inventory now normalizes only path before `::`, regression test added;
Ruff runs with backend cwd/config, no existing source import rewrites. Existing14
helper untouched. Final runner rerun all packs/checks and passed. Initial failed
receipt not overwritten; final own count459 includes that new regression test.

## Scope of actual decoder fixture evidence

Already-installed declared Pillow fully loads2 authored8x8 RGB GIF frames and
checks pixels, total500ms/frame count/profile/hash; corrupt/truncated/header-only,
wrong container/codec/hash/duration/dimensions/encoding/byte limit rejected.
Rights metadata embedded in tests/knowledge_video_decoder_fixtures.py: authored
synthetic colors, no external/personal/child media. No assets/model/packages added.
Actual FULL FRAME decoding of this fixture PASS; production selected video/audio
decoder, resource sandbox/deadline/profile and actual generation remain NOT_RUN.
GIF fixture is NOT a new product encoding/duration/decoder choice.

## Handoff / remaining work

artifacts/LOCAL_VERIFICATION_HANDOFF.md gives one local command, safe SQL
preconditions and candidate CMD-40/error example. ACCEPTANCE_AUDIT.md maps A1–A8
with actual adoption/evidence gaps. RUNTIME_DECISION_SHEET.md prepares undecided
provider/license/profile/environment/budget/copy decisions; activation NOT_APPROVED.
P4 local runner/fixture/audit component delivered; actual own SQL11 and production
decoder/integration/runtime evidence still open. Whole08 IN_PROGRESS, not full DONE.
No push/merge/deploy. Update context/decisions/status/evidence together at checkpoint.
