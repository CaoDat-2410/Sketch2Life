# T3 — Stroke profile and canvas UI blockers (2026-11-01)

- Status: **DESIGN DECISIONS RECORDED; implementation requires a separate task approval**.
- Feature: FEAT-064, synthetic-only current-flow pilot.
- Parent plan: `plan/PLAN.md` revision 6. This plan does not change the parent status (`DRAFT / NOT_STARTED`).

## 1. Implementation path allowlist (B8 — BLOCKED)

The owner ballot directs use of the exact file list in the original T3 plan §1 and prohibits adding paths. That source plan is not present in the reachable `feature/feat063-be-foundation` history at `3ca9c159`, the related remote refs, or the searched local worktree area. The reported `578f3e5e` commit is also unavailable locally and from origin.

**No T3 source, test, or implementation-evidence path is authorized by this plan.** Do not reconstruct the missing allowlist from source inspection. Restore the owner-provided T3 plan/§1 or obtain explicit approval for a revised list, then pin the exact file paths and plan hash in a new task approval before implementation.

This B8 block does not prevent the separately approved documentation-only decision record, whose exact paths are listed in `PLAN_REV2_OWNER_DECISION_RECORD_20261101.md`.

## Goal and scope

Define a versioned server-pinned `CanvasOperationProfileV1` for the pilot canvas, enforce it on accepted strokes, and make the Child canvas use the same geometry. T3 covers stroke profile and canvas only; it does not implement image export/render/admission (later tasks), AI/provider work, or the two routes in B5/B6.

## Approved design decisions

- **B1 — frame:** square 1:1 aspect; 1024×1024 px white output; logical width 400; normalized coordinates remain finite within `[0,1]`.
- **B2 — thickness:** UI brush choices 5, 9, 14 map to logical widths 5, 9, 14 at logical width 400; normalized fractions are 0.0125, 0.0225, 0.035, yielding 12.8, 23.04, 35.84 px at 1024.
- **B3 — one-point stroke:** accept/replay rules match the current UI; a stroke containing one point paints no dot.
- **B4 — profile binding:** the server attaches an immutable `CanvasOperationProfileV1` to the operator-created pilot session configuration. The profile includes the T0 palette (`#FFD21F`, `#FF596C`, `#1685F8`, `#31C978`, `#9250E8`), geometry, widths, append-only/revision semantics and one-point behavior. The client echoes the profile version for each write; the server rejects missing, mismatched or downgraded versions on profile-enabled sessions. The client cannot define or mutate the profile.
- Existing sessions/operations without the profile keep their existing interpretation; T3 does not silently reinterpret stored operations.

## Deferred blockers and boundaries

- **B5 — Child canvas reconnect:** select A as a separate task after T3. A future read-only route may return only the requesting Child's own canvas for `active` or `paused` sessions. It must use session/Child ownership checks, must not reuse a write guard, and must not enable writes or imply legal consent.
- **B6 — Teacher synthetic profile:** select B as a separate task. A future session-scoped route may return only the synthetic profile matching that session's `pilot_run_ref`, with minimal fields (`synthetic-…` id and display label; no age). Keep existing legal-profile routes and consent semantics unchanged.
- **B7 — Đồng ý:** T3 is limited to stroke profile and canvas. Reconnect and Teacher profile lookup are separate tasks with their own plans/approvals.
- **B8 — Sửa:** do not add or infer an allowlist; the owner-referenced source list is unavailable, so implementation stays blocked until it is restored or explicitly approved.
- No render/export, Pillow call, image upload, provider/Modal/GPU, roster/current-turn adapter, consent change or DB migration is included.

## Future implementation sequence

1. After B8 is resolved and implementation is approved, define the immutable profile and strict request contract in the newly approved paths.
2. Pin the server-owned profile only for the explicitly configured pilot session; do not trust client profile values.
3. Validate width, color, coordinates, operation type and version server-side; retain append-only ordering and legacy behavior for sessions without the profile.
4. Update the Child UI to a white strokes-only 1:1 canvas, use the same logical-width mapping, echo the pinned version, and preserve existing retry/idempotency semantics.
5. Verify only the tests in the restored/approved allowlist; any PostgreSQL integration test belongs to an approved T12 plan/database scope.

## Acceptance criteria for the future implementation

- AC1: server session response pins exactly one immutable versioned profile for eligible pilot sessions.
- AC2: writes with a missing/unknown/downgraded profile version, unsupported width/color/operation or invalid geometry are rejected before persistence; old unprofiled sessions remain unchanged.
- AC3: client geometry and server acceptance use the same square logical canvas and exact width mapping.
- AC4: one-point strokes do not render a dot; accepted operations remain append-only and revision ordered.
- AC5: B5/B6 routes are absent from T3 changes and are not implied to be implemented.
- AC6: B8 is resolved by restoring/approving an exact allowlist and pinning it in task approval before any T3 path is touched.

## Approval gate

This plan records owner decisions only. It does not approve any implementation step or test. B8 must be resolved first. A later approval must pin this file's exact hash and the restored/approved allowlist, name reviewers, define checks and clarify whether the local environment/DB is available. Visual changes must follow the repository's generated/provenance/visual-approval gate if they introduce new assets.
