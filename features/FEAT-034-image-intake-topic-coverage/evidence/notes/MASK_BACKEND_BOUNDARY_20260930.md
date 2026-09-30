# Backend mask admission follow-up

Owner instruction: “continue”. Approved plan: `../../plan/MASK_BACKEND_BOUNDARY_FOLLOWUP_20260930.md`.

Implemented source/mask identity and decoded-pixel validation before part processing and caching. Reject PNG encoding errors, animated/mismatched/oversized dimensions, and foreground outside 0.001–0.75 using the renderer's RGB-average × alpha threshold >8. Opaque grayscale uses a histogram; color/alpha uses bounded byte iteration. No source or mask pixels are modified, and no new provider request/retry is introduced.

Invalid masks lose renderer eligibility, receive a specific job failure code and safe log reason, and never get a read capability or usable rig parts. Packaging rechecks provenance/admission. Original artifacts and the supervised session remain available. This is early rejection, not evidence that the provider now cuts the intended subject correctly.

Verification: 65 focused tests passed across auto-rig service, subject-mask pixel admission, SAM runtime and live-image API contracts; Ruff passed. New cases cover exact 75% acceptance, over-limit/empty/transparent/color-average/corrupt/mismatched masks and no invalid-mask capability. Prior 1×1 capability fixtures were replaced with valid 8×8 matching synthetic masks/sources. Repository security and diff checks passed.

Runtime: stopped only verified local Uvicorn PID 47388; restarted backend PID 44216, listening on 8000; /health returned 200. Local logs remain in ignored runtime-output. Existing emulator is connected and ADB reverse maps both 8081 and 8000; Metro status was running. Backend in-memory sessions were reset. Attempted app restart was blocked by the tool policy, so app reload was not claimed; start a new app session before testing.

Pending: external Lightning worker source update/restart and fresh user-flow validation. No live GPU/provider calls were made by this verification and no private image, profile, capability or credential was retained as evidence. No commit/push performed in this follow-up.
