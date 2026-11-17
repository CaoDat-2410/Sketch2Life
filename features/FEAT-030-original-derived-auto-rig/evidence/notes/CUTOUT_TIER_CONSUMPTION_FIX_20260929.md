# CUTOUT_MICRO_MOTION consumer fix — 2026-09-29

- Evidence ID: `E-030-FIX-009`
- Approved scope: `plan/PIXIJ_PART_MOTION_RESTORATION_20260928.md`, follow-up section “consume the subject-only cutout tier”; approval recorded in `approvals/TASK_APPROVAL.md`.
- Runtime trigger: Android WebView console at 11:27 reported `[art-renderer] Renderer V2 package could not start. PART_MASKS_REQUIRED` for the renderer loaded from `http://10.0.2.2:8000`.

## Diagnosis and change

The mobile renderer loaded and validated the package and its subject mask, but then unconditionally
required `FULL_AUTO_RIG` and at least two independent part masks. That made the supported
`CUTOUT_MICRO_MOTION` tier impossible to play and forced the V1 fallback, even though the Pixi auto-
rig player already supports rendering an intact subject cutout on a validated paper background.

The WebView now branches by package tier. `CUTOUT_MICRO_MOTION` passes the validated source and
subject mask to the player without fetching part-mask capabilities. `FULL_AUTO_RIG` retains all
existing part count, capability, digest, provenance and renderer-quality checks. Unsupported tiers
still use the safe original-art fallback.

## Verification

- `pnpm --filter @sketch2life/art-renderer test`: 43 passed.
- `pnpm --filter @sketch2life/art-renderer typecheck`: passed.
- `pnpm --filter @sketch2life/art-renderer build:demo`: passed; bundle `mobile-vRRuVPez.js` built.
- Local backend restarted from the current checkout. `GET /health`, `/renderer/mobile.html`, and the
  rebuilt hashed mobile bundle returned HTTP 200; Uvicorn access log confirmed those responses.
- Sanitized local configuration check confirmed the Lightning development adapter and SAM2.1
  adapter remain enabled/configured from the ignored `backend/.env`; no values or credentials were
  read into evidence, changed, or printed.

## Remaining acceptance

Backend restart cleared process-local session state. A fresh owner-run image flow is required to
verify actual SAM/image-processing tier selection and Android visual playback. Codex did not submit
an image to Qwen, SAM2.1, Lightning, or another model/provider. No code commit or push was made.
