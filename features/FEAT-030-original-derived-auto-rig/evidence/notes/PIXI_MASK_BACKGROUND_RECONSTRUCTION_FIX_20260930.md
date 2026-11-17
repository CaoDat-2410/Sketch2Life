# Pixi background reconstruction regression — 2026-09-30

- Evidence ID: `E-030-FIX-013`
- Related approved scope: high-pigment mask/cutout quality and FEAT-018 Pixi playback diagnosis.
- Inputs: deterministic synthetic RGBA arrays only; no user artwork, screenshot, child data, or model/provider request.
- Environment: Windows workspace, Node `v24.18.1`, pnpm `11.19.0`.

## Diagnosis

The owner-provided screen displayed `MASK_BACKGROUND_RECONSTRUCTION_FAILED`. In
`packages/art-renderer/src/subjectCutout.ts`, inpainting seeds were accepted only from credible
low-chroma/light paper within five source pixels of the verified mask boundary. A synthetic subject
surrounded by a seven-pixel saturated orange outline reproduced the same typed failure while neutral
paper remained nearby. This isolates the failure to renderer cutout reconstruction, not Pixi startup
or backend/SAM availability.

## Change and regression coverage

The bounded local paper-donor search now reaches at most 12 pixels. High-chroma marks remain
ineligible donors; the algorithm does not use image-wide guesses. If no credible donor exists within
the bound, reconstruction still fails closed. The regression also checks that every source pixel
outside the verified mask is byte-identical and that the source input is immutable. The existing
all-saturated/no-paper fixture continues to require `MASK_BACKGROUND_RECONSTRUCTION_FAILED`.

Before the change, the focused regression failed with that exact error (47 tests passed, 1 failed).
After the change:

- `pnpm --filter @sketch2life/art-renderer test` — 48 tests passed.
- `pnpm --filter @sketch2life/art-renderer typecheck` — passed.
- `pnpm --filter @sketch2life/art-renderer build:demo` — passed; static bundle emitted.
- `pnpm --filter sketch2life-mobile exec tsc --noEmit -p tsconfig.json` — passed.
- `pnpm --filter sketch2life-mobile test` — passed.

## Limitations

`emulator-5554` is connected, but this change was not run through a fresh Android Pixi launch: the
current mobile flow obtains its rig/mask through the live backend path, and no offline mobile launch
fixture is wired to the renderer. No provider request was made. Therefore this is a reproduced and
fixed renderer algorithm class with offline regression coverage, not visual acceptance on the
owner's drawing; masks needing paper beyond 12 pixels still fail closed. The separate bird-topic
recall plan remains awaiting owner approval and was not changed here.
