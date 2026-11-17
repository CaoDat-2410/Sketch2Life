# Priority verification notes

- Evidence ID: FEAT-035-EV-001
- Related: C-01, H-01..H-06, M-01..M-12, M-07 harness baseline
- Type: Static source review + offline pure probes + repository harness
- Date/environment: 2026-10-03, Windows PowerShell, repository root, branch `codex/pixi-ai-show-20261001`, baseline commit `7a65890`
- Provider/model calls: None. No image/audio data was sent anywhere.
- Working tree before planning artifacts: clean and tracking `origin/codex/pixi-ai-show-20261001`.

## Independently reproduced

1. **C-01 — no runtime-eligible topic assets.** Loaded `features/FEAT-028-pixi-topic-asset-library/assets/generated/asset-catalog.v2.json` with `load_topic_asset_catalog`, then counted records matching the exact candidate filter in `build_topic_asset_candidate_context`: runtime-eligible, `APPROVED`/`APPLIED`, and license `CLEARED`. Output: `catalog_count=144 runtime_eligible=0`. The candidate builder returns a miss when that eligible set is empty; `supervised_flow.py` makes a non-ready context a planner failure. The finding that this blocks every planner-required renderer request is supported by source; a live request was deliberately not sent.
2. **H-04 — common 12 MP image boundary.** `Feat018AdmissionLimits()` reports `max_pixels=4000000`, `max_longest_edge=4096`. `apps/ui-mobile/src/context/workflowSafety.ts` reports `MAX_SOURCE_IMAGE_PIXELS=12000000` and checks the source dimensions before the separate normalize path. 4032×3024 is 12,192,768 pixels, so it exceeds the mobile source decode budget. No image was opened or uploaded.
3. **H-06 — Vietnamese token collision.** Offline call to `_confirmed_subject_hint(label, ())` returned:

   | Label | Current class |
   |---|---|
   | `cà rốt` | `FISH` |
   | `hóa thạch` | `PLANT` |
   | `con gà` | `UNKNOWN` |
   | `ô tô` | `UNKNOWN` |
   | `chim` | `BIRD` |
   | `bướm` | `INSECT` |

   This confirms the substring/short-alias collision and missing-common-label cases. The output was printed with ASCII escaping to avoid the Windows console code page issue encountered in the first probe.
4. **H-01/H-02 — lock/event-loop design.** Source inspection confirms `async def` image/audio routes invoke synchronous service methods; `LiveImageDemoService` and `SupervisedFlowService` each use a shared `RLock`, with source showing the understanding/renderer workflows inside critical sections. This establishes a blocking risk. The report's measured health latency increase (0.12s to 3.15s) was not re-measured in this verification turn.
5. **H-03 — ASR transport exception path.** Source inspection confirms the ASR adapter maps selected exception types but the service call is not wrapped in the same broad typed recovery path used for Vision. Connection-reset behavior and `500 text/plain` were not re-probed here.
6. **H-05 — Android microphone permission.** `apps/ui-mobile/app.json` sets the ImagePicker `microphonePermission` false and has no Expo AV plugin; the checked-in `apps/ui-mobile/android/app/src/main/AndroidManifest.xml` does not declare `RECORD_AUDIO`. The reported merged/prebuild behavior was not rebuilt in this turn.
7. **M-05 — container resources.** `backend/Dockerfile` copies only `pyproject.toml`, `README.md`, and `src`; `app.py` locates repository data using `Path(__file__).resolve().parents[5]` and accesses `data/`, `features/`, and renderer paths. This source-layout mismatch is confirmed; Docker was not built here.
8. **M-07 — harness.** After FEAT-035's required directories and plan records were created, `python tools/validate_harness.py` still failed exactly on: FEAT-026 missing `evidence/raw` and `evidence/metrics`; FEAT-033 missing `evidence/raw` and `evidence/screenshots`; FEAT-034 missing `evidence/raw`, `evidence/screenshots`, and `evidence/metrics`. FEAT-035 itself passes harness path checks. The older missing paths are outside this feature's ownership until the approved plan authorizes their remediation.
9. **M-08/M-10 — mobile script and Android target.** `apps/ui-mobile/package.json` maps `test` only to `validate-ui-copy.mjs`, with no `vitest` dev dependency. `apps/ui-mobile/android/build.gradle` defaults to min/compile/target 24/35/34; `app/build.gradle` assigns debug signing to release. `tools/validate_skeleton.py` references `apps/mobile`, not the active `apps/ui-mobile`. The reported orphan test failure was not rerun.

## Source-confirmed, dynamic claim not reproduced

- **M-01:** `_expire` deletes the session and artifacts; report/source indicate idempotency scopes are not enumerated/deleted and replay occurs before session validation. TTL replay/memory behavior was not re-executed with a fake clock here.
- **M-02/M-03/M-04:** implementation structure and request boundaries were only partially reviewed; reported runtime/timeout/parser outcomes remain to be reproduced with fakes before fixing.
- **M-09:** project decision in ADR-0005 already requires Firebase ID-token verification at the backend boundary. Current routers were not exhaustively probed for unauthorized access in this turn; the report's unauthenticated reachability requires an explicit HTTP test.
- **M-11/M-12 and L-01..L-17:** retain report status pending focused reproduction/code review. Do not treat them as independently validated solely because the report lists them.

## Reproduction commands / inspected inputs

- Catalog/alias probe: `PYTHONPATH=backend/src backend/.venv/Scripts/python.exe` with `load_topic_asset_catalog`, `build_topic_asset_candidate_context` domain models, and `_confirmed_subject_hint` from `sketch2life.application.services.pixi_show_compiler`; see exact source files linked above.
- Image limits: same Python environment, inspect `sketch2life.domain.understanding.image_admission.Feat018AdmissionLimits`; source check in `apps/ui-mobile/src/context/workflowSafety.ts`.
- Harness: `python tools/validate_harness.py`.
- Security: `python tools/validate_repository_security.py` returned `REPOSITORY_SECURITY_VALID` (`publishable_files_scanned=1906`; no absolute machine paths).
- Read-only source review: `backend/src/sketch2life/application/services/live_image_demo.py`, `backend/src/sketch2life/application/services/supervised_flow.py`, `backend/src/sketch2life/infrastructure/ai/lightning_client.py`, `backend/src/sketch2life/interfaces/http/routers/images.py`, `backend/src/sketch2life/interfaces/http/app.py`, Android app configuration and validators listed above.

## Interpretation and limitation

The highest-impact Pixi, image-budget, Vietnamese classifier, harness, Android permission/configuration, and package-layout concerns have direct evidence. Locking, ASR reset, mobile test failures, auth exposure, Docker startup, and remaining medium/low findings still need focused reproduction after approval. The security validator passes on the current tree. No reported issue is considered fixed by this plan. The review report's quantitative suite counts and latency measurements are not independently certified here.
