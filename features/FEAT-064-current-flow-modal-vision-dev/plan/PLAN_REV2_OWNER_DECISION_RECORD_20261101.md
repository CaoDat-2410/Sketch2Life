# Plan Rev2 — Record T2B/T3 owner decisions (2026-11-01)

- Status: **APPROVED / IN_PROGRESS — documentation and publication only**.
- Feature: FEAT-064 — current-flow Modal Vision dev pilot.
- Baseline: `feature/feat063-be-foundation` remote at `3ca9c1593d4a0e7d449a65ef08ff33d5c0a5b269`.
- Owner instruction: after the T2B/T3 decision ballot, “commit and push”.

## Objective

Record the selected T2B and T3 design decisions in FEAT-064, create reviewable task plans with explicit acceptance criteria, preserve the T3 path-list blocker rather than infer paths, then make one documentation-only commit and push it to `feature/feat063-be-foundation`.

## Exact file scope

1. Create `plan/T2B_BE1_TO_BE2_FACT_ADAPTER_PLAN_20261101.md`.
2. Create `plan/T3_STROKE_PROFILE_AND_UI_BLOCKERS_PLAN_20261101.md`.
3. Create this plan.
4. Create `SOURCE_REGISTER.md`.
5. Create `evidence/OWNER_DECISIONS_T2B_T3_20261101.md`.
6. Update `DECISIONS.md`, `CONTEXT.md`, `status/STATUS.md`, `evidence/README.md`, and append a decision-record approval entry to `approvals/TASK_APPROVAL.md`.

No other path is in scope for this documentation commit.

## Decisions to record

### T2B

- A1 **Sửa**: add BE1-managed `age_revision` and `age_source`; initialize revision to 1 and increment only when age changes. Backfill unknown legacy provenance as `LEGACY_UNKNOWN`; use controlled source values and never manufacture provenance from a profile ID, timestamp or session revision. Derive the BE2 age provenance reference from the stored source and age revision.
- A2 **Đồng ý**: consent reference/revision may be `None` only for `eligibility_basis == SYNTHETIC_DEV`; legal consent remains fully required, and synthetic consent remains ineffective.
- A3 **Sửa**: use a versioned, canonical SHA-256 context digest as the full-context freshness token. Repository inspection found that the current BE2 `ContextDecision.context_revision` is an integer and its relevant consumers use equality checks. Keep that integer contract intact; add and compare an explicit digest field rather than putting a string digest into the integer field. The digest covers one coherent read of profile/age provenance, consent, synthetic proof, membership and session facts. It is an equality token, not an ordered counter or a security credential.
- A4 and A5 **Để sau**: CanvasFacts, GroupRoster and `current_turn` belong to T3/T4 and later adapters.
- A6 **Đồng ý**: T2B is limited to `MemberFact` and `ContextDecision`.

### T3

- B1 **Đồng ý**: square 1:1 canvas, 1024×1024 white output, logical width 400.
- B2 **Đồng ý**: UI widths 5/9/14 map to logical widths 5/9/14 on width 400 and normalized ratios 0.0125/0.0225/0.035 (12.8/23.04/35.84 px at 1024).
- B3 **Đồng ý**: a one-point stroke is not rendered as a dot.
- B4 **Đồng ý**: pin an immutable `CanvasOperationProfileV1` into the server-created session configuration; the client echoes the required version and the server rejects mismatch/downgrade. Existing sessions and operations without the profile keep their prior interpretation.
- B5 **Đồng ý A** and B6 **Đồng ý B**: plan separately after T3; neither route is in T3 scope.
- B7 **Đồng ý**: T3 covers stroke profile and canvas only.
- B8 **Sửa**: the owner-referenced T3 §1 path list is absent from reachable history/worktrees. Do not invent or substitute paths; keep T3 code blocked until the exact owner list is restored or explicitly approved.

## Acceptance criteria

- AC1: T2B and T3 plans record every selected/deferred ballot item, conditions, acceptance criteria, future implementation gates and non-goals.
- AC2: T2B A3 respects the current BE2 integer type and adds a separately typed digest freshness field; no digest is coerced into an integer.
- AC3: T3 plan records that its owner-referenced §1 allowlist is unavailable and authorizes no T3 source/test path until restored or explicitly approved. B5/B6 and later canvas export/render tasks are explicitly excluded.
- AC4: FEAT-064 context, decisions, source register, approval and status show that these are design decisions only; the parent FEAT-064 plan remains DRAFT and implementation remains NOT_STARTED pending separate approvals.
- AC5: No source code, tests, migration, database, Docker, MinIO, Modal/GPU, provider or real-child operation is performed.
- AC6: `python tools/validate_repository_security.py` and `git diff --check` pass before commit/push.
- AC7: One docs-only commit is pushed to `feature/feat063-be-foundation`; verify the remote branch points to the pushed commit.

## Explicit exclusions

No T2B/T3 implementation approval, Alembic migration creation/application, PostgreSQL test database setup, running tests, B4b real-data consent lifecycle, outreach to Hiếu, product/runtime change, or force push. The reported local commit `578f3e5e` is not present in this checkout or advertised by origin; use the current remote branch tip and create a new forward commit.

## Verification

Review the staged diff to ensure it contains only the ten paths listed above; run repository security validation and `git diff --check`; commit with a documentation-only message; push the named feature branch normally (no force); fetch/inspect the remote branch tip afterward.
