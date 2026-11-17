# P2-T3 Optional Narration — Status Reconciliation

- Date: 2026-10-20.
- Branch: `feature/feat018-p2t3-optional-narration`.
- Inspected commit: `f220781876472950093856e97bbdaaec5170a7c1` (same as `origin/dev` at inspection).
- Status: `IMPLEMENTED — OFFLINE VERIFIED; OWNER LIVE SMOKE PENDING`.
- This is a coordinator status/evidence note, not a new approval or independent review.

## Basis and scope

The owner-approved full-workflow/narration addendum and implementation closure are recorded in
`approvals/TASK_APPROVAL.md` under “Approved full workflow debug and narration-input addendum” and
“Implementation closure for the approved addendum” (2026-09-21). The approved implementation plan
is `plan/UI_BACKEND_FULL_WORKFLOW_ASR_DEBUG_PLAN.md`, especially its implementation result section.
These later records supersede the older 2026-09-12 progress statement that P2-T3 was still gated.

The implemented scope covers an image-required workflow with optional narration:

| Requirement | Current implementation/evidence |
|---|---|
| Narration absent is explicit; no transcript is invented | `NarrationInputV1` supports `NONE`; the approved addendum defines absent narration as an explicit choice. |
| Typed text keeps its source and bypasses ASR | `NarrationInputV1` / `MobileWorkflowCommandV1` use `TEXT_TYPED`; `test_typed_narration_is_forwarded_as_text_without_an_asr_call` covers the path. |
| Audio is admitted and processed through the backend | Session-scoped `/media/audio` ingress and backend-only faster-whisper path are documented in the approved implementation result; Capture UI exposes the explicit record and analyze actions. |
| ASR uses the approved large-v3-turbo family and preserves source provenance | `faster_whisper_asr.py` binds `deepdml/faster-whisper-large-v3-turbo-ct2`; adapter tests cover source/hash validation and provenance. |
| ASR and Vision evidence remain distinct; failure does not become missing narration | `raw_understanding.py` validates correlation before mapping; `test_asr_failure_is_not_collapsed_into_missing_narration` and the correlation tests cover this boundary. |
| Silence is represented explicitly | `test_silence_maps_to_success_not_recapture` asserts `NO_SPEECH_SUSPECTED`; it is not silently converted into a fabricated transcript or forced recapture. |
| No live provider call by Codex | No live Lightning or ASR provider request was made during this inspection or verification. Owner-run smoke remains pending under the existing approval boundary. |

Relevant implementation paths include:

- `backend/src/sketch2life/contracts/schemas/narration.py`
- `backend/src/sketch2life/application/services/live_image_demo.py`
- `backend/src/sketch2life/infrastructure/ai/faster_whisper_asr.py`
- `backend/src/sketch2life/interfaces/http/routers/images.py`
- `apps/ui-mobile/src/screens/modules/CaptureScreen.tsx`
- `apps/ui-mobile/src/demo/api.ts`
- `apps/ui-mobile/src/context/AppContext.tsx`
- `backend/tests/contract/test_live_image_demo_api.py`
- `backend/tests/unit/test_faster_whisper_asr_adapter.py`
- `backend/tests/unit/test_raw_understanding.py`
- `backend/tests/unit/test_lightning_v2_asr_adapter.py`

## Verification on the inspected branch

Passed in this session:

```text
cd backend
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/unit/test_faster_whisper_asr_adapter.py tests/unit/test_raw_understanding.py tests/unit/test_lightning_v2_asr_adapter.py -ra
36 passed in 0.37s
```

Blocked, not passed:

- `backend/tests/contract/test_live_image_demo_api.py` did not collect because the environment
  lacks `PIL` (`ModuleNotFoundError` from the `auto_rig` import). The route-level suite therefore
  has no fresh result from this session.
- `pnpm --dir apps/ui-mobile exec tsc --noEmit` did not reach TypeScript compilation: pnpm failed
  while opening its SQLite cache with `[ERR_SQLITE_ERROR] unable to open database file`. No
  dependencies were installed and no alternate cache/tool path was tried.

The 2026-09-21 approval record contains historical offline verification results for the full
contract/unit suite and mobile TypeScript. Those historical results are not represented here as
fresh passes on the inspected commit.

## Disposition

P2-T3 offline implementation is complete based on the owner-approved scope, recorded implementation
closure, current code/tests, and the fresh focused unit result above. The API contract suite and
mobile TypeScript check remain unverified in this environment; this is a verification limitation,
not a claim that either check passed. Owner-only live Lightning/ASR smoke remains pending. No code,
approval record, provider setting, or live service was changed or invoked for this reconciliation.
