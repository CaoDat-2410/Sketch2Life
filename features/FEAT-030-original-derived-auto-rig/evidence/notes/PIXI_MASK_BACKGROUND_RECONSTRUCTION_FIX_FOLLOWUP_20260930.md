# Pixi mask-background reconstruction follow-up — 2026-09-30

- Evidence ID: `E-030-FIX-014`
- Approved scope: the integrated SAM-mask/high-pigment cutout workstream and FEAT-018's approved
  Pixi playback diagnosis/fix plan. No new provider/model work was authorized or performed.
- Inputs: deterministic synthetic RGBA arrays and sanitized local renderer/backend logs. No
  screenshot, user artwork, child/profile data, credentials, or provider request was used or stored.

## Runtime evidence and diagnosis

The supplied error was `MASK_BACKGROUND_RECONSTRUCTION_FAILED`. Backend logs for the affected flow
showed HTTP 200 for renderer launch/page, source, rig package, and all four rig-mask reads. The
sanitized renderer diagnostic was the cutout error, so artifact transport succeeded and the failure
was downstream in `subjectCutout.ts`.

The previous fix raised the local credible-paper donor search to 12 pixels. That still failed when a
saturated outline enclosed the subject beyond the local search radius. A synthetic 16-pixel crayon
outline reproduced the failure while the same image still contained credible paper outside the
local neighborhood.

## Fix and regression coverage

The initial pass still prefers nearby low-chroma, light paper. During the existing source/mask scan,
the renderer now also computes a deterministic image-local paper estimate from at least eight
unmasked source pixels meeting the same paper thresholds. It uses that estimate only where the local
donor search has none, then propagates it inward. Writes remain strictly inside the verified mask;
all pixels outside it and the immutable source remain byte-identical. If the unmasked image has no
credible paper samples, the renderer still fails closed with
`MASK_BACKGROUND_RECONSTRUCTION_FAILED`.

The new synthetic 16-pixel-outline regression verifies recovery, source immutability, exact
outside-mask preservation, and retained source RGB on the subject. The all-saturated/no-paper test
continues to verify fail-closed behavior.

## Verification

- `pnpm --filter @sketch2life/art-renderer test` — 49 tests passed.
- `pnpm --filter @sketch2life/art-renderer typecheck` — passed.
- `pnpm --filter @sketch2life/art-renderer build:demo` — passed.
- `pnpm --filter sketch2life-mobile exec tsc --noEmit -p tsconfig.json` — passed.
- `pnpm --filter sketch2life-mobile test` — passed.
- The running backend served `/renderer/mobile.html` and its rebuilt hashed JS bundle with HTTP 200.
  No backend restart was needed: the renderer is served from the built static directory. The
  existing process/session was preserved.

## Remaining acceptance

A fresh emulator visual retest is not claimed. The current Windows shell has no `adb` executable or
configured Android SDK path, so it could not reload the app. The screenshot proves the failure, and
synthetic tests prove the algorithm correction class. Owner-run Android visual acceptance against a
valid rig/mask flow remains pending. The original image always remains safe; no automatic V1
fallback was added.
