# BaoVC UI real-workflow verification — 2026-09-21

## Scope

This note records the correction from the standalone demo screen to BaoVC's original React Native
UI and the image-only backend workflow. It contains no raw image, provider response, token or child
data.

## Implementation decision

`apps/ui-mobile/App.tsx` delegates to the BaoVC shell in `BaoApp.tsx`. The standalone
`DemoWorkflowScreen` remains a reference/debug artifact but is not mounted. BaoVC screens call the
real client through `AppContext` and preserve the approved session/version/idempotency headers.

## Verified path

1. Android emulator showed BaoVC Splash, Onboarding, Dashboard, Child Profile and Capture screens
   with the original artwork and layout.
2. The Child Profile CTA created a backend session and the Capture screen displayed the success
   notice returned by the real client.
3. The local backend accepted the repository's approved synthetic image fixture with
   `ImageAdmissionReceiptV1.decision=ADMITTED`.
4. The client path after that point remains explicitly user-triggered: only tapping the analysis
   action calls the backend understanding endpoint, which is the point at which the owner may send
   one live Lightning request.
5. Gate A, P1/ExperienceSpec, Gate B, Pixi source-only handoff and feedback are represented by
   the corresponding BaoVC screens and client methods; no video or ASR request is wired.

## Validation

- `pnpm --dir apps/ui-mobile exec tsc --noEmit` — passed.
- `backend/.venv/Scripts/python.exe -m pytest backend/tests/contract/test_live_image_demo_api.py -q`
  — 6 passed.
- `http://127.0.0.1:8000/health` — `{"status":"ok","service":"sketch2life-api"}`.
- Manual Lightning execution was not performed by Codex; the owner must initiate it on Lightning
  under the approved aggregate 25-credit ceiling.

## Narration addendum — 2026-09-21

The owner-approved workflow correction is implemented and verified offline:

- Capture now presents `Không thêm`, `Nhập chữ`, and `Ghi âm`; image selection remains required.
- Typed text is sent as `TEXT_TYPED` and reaches Vision context without an ASR call.
- Audio is recorded with `expo-av`, uploaded to `/media/audio`, and only the explicit analysis
  action can call backend `/v1/asr` followed by `/v2/vision`.
- The Lightning server exposes the new ASR route with lazy faster-whisper loading and sanitized
  status logging; no live provider request was made during this implementation.
- `pnpm --dir apps/ui-mobile exec tsc --noEmit` passed. The focused image/narration contract suite
  passed, and the full `backend/tests/contract` plus `backend/tests/unit` collection passed with
  a writable temporary directory (5 tests skipped by existing suite policy).
