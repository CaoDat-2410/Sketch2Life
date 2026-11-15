# Rev87.17 — Parent SVG guide runtime through Modal

**Date:** 2026-11-15<br>
**Status:** APPROVED by the owner's direct instructions to fix the Parent SVG guide flow and test it, with the dataset stored on Modal Volume rather than Docker.<br>
**Baseline:** FEAT-063 SRS v2.7-draft; target requirements §§1–31 remain unchanged.

## Problem and evidence

- Rev87.16 verified one real Qwen3.5 catalog worker result, but explicitly did not verify Parent HTTP/API/UI.
- The live `rev87-parent-authfix` API container is healthy but its `parent_ai.py` SHA-256 differs from the current worktree; its SVG infrastructure package lacks the Openclipart/ OpenMoji guide adapters. It is an older image than the code under test.
- The current backend route attempts local Openclipart/OpenMoji/Arcadia source derivation before dispatching to Modal. The current Dockerfile copies those source datasets into the API image, contrary to the owner's Modal-Volume-only direction.
- The root `.env` has Modal/Firebase credentials but no Parent SVG-guide feature flag, and Compose does not pass `SKETCH2LIFE_SVG_TOPIC_STROKE_GUIDE_GENERATION_ENABLED` to the API. A rebuild from the worktree therefore starts with this capability disabled unless the mapping is fixed.

## Goal

Run the current Parent SVG guide API against the deployed Modal catalog without copying the source corpus into Docker. Keep optional curated local packs usable when deliberately present; if a pack is absent from the runtime image, continue to the Modal catalog worker instead of failing before inference.

## Approved work

1. Remove the Openclipart, OpenMoji and Arcadia dataset directories from Docker build context and API image. Keep the Modal health app files needed by Compose.
2. Make each optional local source adapter distinguish an absent pack from an invalid present pack. An absent pack is skipped; a present but corrupt or unsafe pack remains fail-closed.
3. Map the SVG-guide flag through Compose and `.env.example` (default off); enable it in the ignored root `.env` for this approved dev test only. Never print or record credential values.
4. Rebuild and recreate only the existing API service in Compose, explicitly using the single root `<repo-root>\.env`. Do not restart unrelated services or deploy/alter Modal apps or secrets.
5. Verify API health, that the dataset directories are absent in the API image, that Firebase Auth points to the local emulator, and that the SVG-guide capability is enabled.
6. Register one short-lived synthetic Parent identity through the backend against Firebase Auth Emulator, obtain an emulator token, and call `POST /api/parent/v1/ai/sketch-guides` once for a generic topic that has no local pinned guide. Send no child profile, child image, voice, consent, or real personal data.
7. Validate HTTP status and response contract, Modal call ID/model revision, source dataset/license/hash, path count and exact path coverage, 4–8 ordered stages, quality gates, and worker timing/logs. Preserve only redacted evidence. Delete the ephemeral emulator identity and its backend identity row if created.
8. If the single real inference fails, preserve diagnostics and stop without retry. Do not run video, teacher presentation, Android UI, workload-wide generation, or any additional GPU inference in this amendment.
9. Update feature status/context/evidence index and append dated as-built evidence to SRS §32 only. Do not change §§1–31.

## Acceptance criteria

- [x] Docker build context/image excludes the three SVG dataset directories; Modal Volume remains the sole full-corpus source.
- [x] Missing local packs fall through to the Modal worker; invalid present packs remain rejected.
- [x] Compose passes the SVG-guide flag and the test runtime uses the root `.env` with the capability enabled.
- [x] Only the Parent API container was rebuilt/recreated and reported healthy.
- [x] One synthetic Parent API request reached Modal, which succeeded; the API safely rejected the valid worker result because it compared the worker content schema to the separate API response schema. This terminal 502 was recorded without retry; Rev87.18 fixes and retests the contract.
- [x] No child data/profile/consent, video, additional inference, secret change, unrelated service restart, commit, push, or merge was used.
- [x] The ephemeral test identity was removed; evidence contains no credentials or auth tokens.
- [x] SRS §§1–31 were not changed by this amendment; implementation evidence is recorded in §32.

## File scope

- `.dockerignore`
- `backend/Dockerfile`
- `compose.yaml`
- `.env.example`
- ignored root `<repo-root>\.env` for this dev test only; never commit or record its values
- `backend/src/sketch2life/interfaces/http/routers/parent_ai.py`
- `backend/src/sketch2life/infrastructure/svg/openclipart_guide.py`
- `backend/src/sketch2life/infrastructure/svg/openmoji_guide.py`
- `backend/src/sketch2life/infrastructure/svg/arcadia_gallus_guide.py`
- focused Parent SVG route contract tests
- this plan, FEAT-063 approval/context/source/status/evidence records and SRS §32
- one new evidence directory under `features/FEAT-063-system-architecture-rearchitecture/evidence/`

## Runtime result

**Completed; terminal result fixed by Rev87.18.** Docker context/image no longer contains the full Openclipart/OpenMoji/Arcadia packs; the API image was rebuilt from the current source and the Parent SVG flag was explicitly enabled from the ignored root `.env` for this dev run. The only fresh Parent request used a temporary Firebase Auth Emulator Parent and no child data. Modal call `fc-01M7E09QD3E3MWW107GSA56Q2E` completed successfully (worker 86.670 s; API wait 95.394 s), but the API returned HTTP 502 `MODAL_SVG_SOURCE_GUIDE_OUTPUT_REJECTED` because it expected the API entity schema instead of Modal's `SvgTopicStrokeGuideContentV1`. This was a contract mismatch, not a worker timeout or invalid SVG. No retry was made in Rev87.17; the synthetic identity and one backend identity row were deleted. See `evidence/EV-063-112_PARENT_MODAL_API_GUIDE_RUNTIME_20261115/REPORT.md`. Rev87.18 records the fix and one successful fresh request.
