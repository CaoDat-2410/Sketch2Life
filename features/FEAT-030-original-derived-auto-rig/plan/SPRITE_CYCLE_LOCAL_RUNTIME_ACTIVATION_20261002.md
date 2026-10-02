# Sprite-cycle local runtime activation — task plan

- Feature: FEAT-030 with FEAT-028 asset lifecycle
- Revision: 1
- Status: APPROVED BY OWNER'S DIRECT IMPLEMENTATION REQUEST
- Date: 2026-10-02
- Parent: `SPRITE_CYCLE_RENDERER_INTEGRATION_20261002.md`, revision 1
- Approval: recorded in `approvals/TASK_APPROVAL.md`; pre-approval plan SHA-256
  `9808D1690A44A08D924A607E0745055EBD3CE8FCE2E2376C6E8819FF38FB810A`.

## Goal and scope

Make the newly approved sprite cycles visibly playable in the local Android development runtime,
without making unverified sheets available to production. Audit all 37 manifest cycles, recover the
ImageGen-returned full `revisedPrompt` for each generation output ID from the local Codex session
record, complete cycle-specific technical QA, and activate only the mapped cycles that pass.

The local preview is server-controlled, defaults off, and is allowed only when
`SKETCH2LIFE_ENV` is `local` or `test`. The existing production `runtimeEligible` gate remains false
and the production rights status remains `REVIEW_REQUIRED`. No legal non-infringement opinion,
commercial/publication approval, external asset source, or prompt that is not in the session record
will be claimed. The owner’s direct request authorizes internal development preview only.

Do not regenerate, retouch, or overwrite generated/approved source sheets. Promote only exact
hash-matched approved PNGs to FEAT-028 `assets/applied/`. Keep every candidate that fails QA blocked
and unavailable to the renderer; no fallback or substitution is introduced.

## Acceptance criteria

- AC-01: All 37 manifest output IDs have a feature-local provenance record containing the exact
  ImageGen-returned `revisedPrompt`, output ID, source filename/hash, generation date, and any
  project-owned style-reference lineage; no local machine paths or child data are recorded.
- AC-02: The rights record is scoped to owner-authorized local development preview. It records the
  applicable ImageGen terms boundary and explicitly does not certify non-infringement or distribution
  rights. Production rights remain pending.
- AC-03: All 37 cycles receive deterministic atlas/crop checks: source hash and RGBA dimensions,
  cell geometry, transparent bounds, nonempty-frame count, edge clearance, frame-to-frame change,
  loop seam, and placement/pivot stability. Results are recorded per cycle. Edge-clipped, unstable,
  non-looping, or otherwise ambiguous cycles remain blocked.
- AC-04: A dedicated applied-cycle catalog contains only cycles that passed AC-03, are covered by
  owner visual approval, and are reachable by the current closed subject/behavior selector. The
  applied files are byte-identical to their approved source sheets. No catalog-only/unmapped cycle
  is made selectable by model text.
- AC-05: The backend verifies per-cycle registration/eligibility and reads applied assets. A default-
  off, server-only local/test preview setting is required to issue development capabilities; setting
  it in staging/production cannot open the preview path. Production gate behavior remains unchanged.
- AC-06: Tests prove default-off, local/test-only, per-cycle allowlisting, failed QA/catalog rejection,
  integrity checks, and production fail-closed behavior. Existing FEAT-018 renderer contracts stay
  compatible.
- AC-07: On the running Android emulator, exercise at least one approved, QA-passed cycle through
  the backend-issued frame capabilities and Pixi show clock. Capture feature-local evidence for
  `[pixi-cycle]` load/decode/play logs, visible motion, and teardown; verify no red screen or unsafe
  fallback. Keep backend/Metro/emulator logs free of tokens and image data.

## Implementation and verification

1. Record this plan and the owner’s direct implementation approval before changing runtime code or
   applying assets.
2. Recover and archive the 37 returned prompt transcripts; reconcile each with the manifest output
   ID and PNG SHA-256.
3. Run the repeatable 37-cycle image QA; visually inspect candidates that the current selector can
   reach; select only cycles with clear margins and stable, readable loop behavior.
4. Record cycle-level gates and create the applied catalog; copy only exact approved PNGs to
   `assets/applied/`.
5. Add cycle-level enforcement and the default-off local/test preview flag; preserve strict production
   gates and add backend/TypeScript tests.
6. Run focused and relevant full tests, repository harness/security validation, start/restart the
   local backend with the preview flag, and validate Pixi playback on the connected emulator.
7. Update FEAT-028/FEAT-030 status, decisions, and evidence with exact results. Do not commit or push
   unless separately requested.

## Risks and controls

- A generated sheet can have alpha corners yet still clip a pose at an individual cell edge. Measure
  each cell, not just the whole atlas; reject any cycle with insufficient margin.
- Visual approval does not grant blanket production/publication rights. Preview is local-only, and the
  ordinary production gate remains closed.
- The current AI planner/selector supports only a subset of the 29-class behavior registry. Do not
  expose unused cycles or silently map a new subject/action; leave them cataloged as blocked until
  separately wired and verified.
- Never log full prompts, reference images, frame payloads, capability tokens, or local user paths at
  runtime. Provenance prompts stay only in feature-local review evidence.
