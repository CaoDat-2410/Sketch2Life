# FEAT-017 live AI development integration context

- Status: REVIEW
- Owner: integration sprint allocation, after FEAT-016 fixture UI review
- Goal: replace only the deterministic P2 understanding step with a backend-only live Lightning development call while preserving the approved UI flow, versioned contracts, Gate A, P1 identity, P3/P4 fixture adapters and fallback behavior.
- Data policy: synthetic FEAT-015 fixture media only; no real child data, accounts, or production artifacts.
- Dependencies: FEAT-003 provider-shaped ASR/VLM adapters, FEAT-016 runtime/session contracts, mobile fixture UI, and `docs/security/PRIVATE_AI_BOUNDARY.md`.
- Current state: the UI harness is complete and uses deterministic fixture AI. This feature is the separate approval gate for a live development call.

## Explicit exclusions

- Runpod production, production API deployment, cloud provisioning, Android release/signing, and Play distribution.
- Provider credentials or endpoint URLs in source control, mobile code, fixtures, screenshots, logs, or bundles.
- Real child media or identifying metadata.
- Live P3 video/media generation, TTS, or any provider capability beyond the P2 ASR/VLM understanding proposal.
- Bypassing Gate A or changing P1 eligibility rules.

## Approval record

Plan revision 1 is approved in `approvals/TASK_APPROVAL.md` for the bounded Lightning development scope. Production provider, real data, release, and cloud changes remain excluded.

## Implementation update — 2026-09-05

Approval revision 1 is recorded. The backend-only Lightning transport, hash-checked synthetic fixture loader, typed ASR/VLM adapters, local live-understanding route, mobile live-mode client/state and sanitized smoke notebook/guide are implemented. Automated adapter, route, mobile and regression checks pass. A real provider smoke run is intentionally pending the user's configured Lightning HTTPS endpoint and runtime token file; no credential or real data is stored here.


## Live smoke update — 2026-09-06

ASR and Qwen3-VL live inference both returned SUCCEEDED through the Studio provider wrapper. The sanitized result was PROPOSAL with Gate A required and a 5988.8 ms round trip. The fixture SVG is rasterized inside the provider wrapper before VLM inference.
