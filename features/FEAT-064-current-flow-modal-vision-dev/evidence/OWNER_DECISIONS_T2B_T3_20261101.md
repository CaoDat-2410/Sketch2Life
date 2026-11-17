# FEAT-064 T2B/T3 owner decision record — 2026-11-01

## Scope

This record captures the decisions selected from the owner-provided T2B/T3 ballot and the subsequent instruction to commit and push. It records design direction and creates reviewable task plans; it does not authorize implementation.

Decision plans:

- T2B: `../plan/T2B_BE1_TO_BE2_FACT_ADAPTER_PLAN_20261101.md` (SHA-256 `781A561AEC08BF0990AA18CBDBD27DB7CEB84CB23EA3CDD5ABB483A6A10D83C7`).
- T3: `../plan/T3_STROKE_PROFILE_AND_UI_BLOCKERS_PLAN_20261101.md` (SHA-256 `D948F8DCAB9FDCF0EACBF3B0D4DB5C88914A6A17BC61D7001E1C3B1C28D61DA2`).
- Documentation-only publication plan: `../plan/PLAN_REV2_OWNER_DECISION_RECORD_20261101.md` (SHA-256 `DE455C77CFB687086A01194E628AB00EEC9E851C3E9258915561D4EE186916A2`).

## Outcomes

| Item | Decision | Recorded disposition |
|---|---|---|
| A1 | Sửa | Add `age_revision` and controlled `age_source`; default revision 1, increment only on age change; unknown historical source is `LEGACY_UNKNOWN`; no fabricated provenance. |
| A2 | Đồng ý | Nullable consent references only for `SYNTHETIC_DEV`; keep `consent_effective=false`; legal consent contract stays required and unchanged. |
| A3 | Sửa | Add explicit versioned SHA-256 full-context digest; compare by equality. Preserve BE2's existing integer `context_revision` rather than coercing a string hash into it. |
| A4 | Để sau | CanvasFacts deferred to T3/T4 and later adapter work. |
| A5 | Để sau | GroupRoster revision deferred with roster/canvas/turn adapters. |
| A6 | Đồng ý | T2B limited to `MemberFact` and `ContextDecision`. |
| B1 | Đồng ý | Square 1:1, 1024×1024 white output, logical width 400. |
| B2 | Đồng ý | UI 5/9/14 maps to 5/9/14 logical width and ratios 0.0125/0.0225/0.035. |
| B3 | Đồng ý | Single point draws no dot. |
| B4 | Đồng ý | Server-pinned immutable profile in session; client echoes version; reject mismatch/downgrade; old sessions retain old interpretation. |
| B5 | Đồng ý A | Read-only Child own-canvas reconnect is a separate task after T3. |
| B6 | Đồng ý B | Session-scoped minimal Teacher synthetic-profile lookup is a separate task after T3. |
| B7 | Đồng ý | T3 is limited to stroke profile and canvas. |
| B8 | Sửa | The original T3 §1 allowlist is unavailable in reachable history. Do not infer file paths; authorize no T3 source/test path until the list is restored or explicitly approved. |

## A3 source check and contract adjustment

The source review found `ContextDecision.context_revision` is currently an integer in `application/ports/vision_analysis.py`. Its relevant current consumers compare equality; the typed context path already carries a separate `context_digest`. Therefore A3 is recorded as **Sửa**: BE1/BE2 will use an explicit, versioned digest field for the whole-context freshness token and compare that digest for equality. The existing integer field remains type-compatible and is not ordered or used as the sole cross-owner freshness signal. The digest covers a single coherent snapshot of the age/profile, consent, proof, membership and session facts relevant to the decision.

This change affects a BE2 contract and consumers. A separate implementation approval must identify the exact contract version, changed code paths, migration/test scope if any, and owners before code is edited.

## Operational notes

- T2B/T3 implementation and tests remain **NOT_STARTED** pending separate task approval. Parent FEAT-064 plan revision 6 remains `DRAFT / NOT_STARTED`.
- T12 PostgreSQL awaits a disposable local database and `BE1_TEST_DATABASE_URL` configured outside chat. No database or Alembic operation occurred.
- B4b remains deferred. The requested notice to Hiếu about the 31 MinIO/AWS-dependent test failures is outstanding; no message was sent.
- D-114 is now referenced as D-119 in the Swagger decision history.
- The owner-reported commit `578f3e5e` was unavailable locally and `git fetch origin 578f3e5e` failed because origin has no such advertised ref. The decision documentation is based on remote branch tip `3ca9c1593d4a0e7d449a65ef08ff33d5c0a5b269`; a new forward commit is required.
- The original T3 §1 allowlist referenced in B8 was not found in the current branch, related remote refs, or the accessible temporary worktree search. The T3 plan records the blocker and contains no inferred source/test allowlist.

## Verification boundary

This is documentation-only. No code, tests, migration, database, Docker/MinIO, Modal/GPU/provider, production service or real-child data was used. Repository security validation and `git diff --check` are run before the authorized commit/push and their results are recorded in the final delivery report.
