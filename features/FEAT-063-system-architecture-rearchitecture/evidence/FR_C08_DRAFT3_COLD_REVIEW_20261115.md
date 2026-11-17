# FR-C-08 Draft 3 Independent Cold Review — 2026-11-15

## Verdict

**READY WITH NOTES** — 0 P1, 0 P2, 1 P3 finding.

The Draft 3 lifecycle plan and implementation specification reconcile the reviewed FR-C-08 policy to D-208 and unsigned Rev68. The P3 note concerns proposed sequencing language that is stricter than D-208's stated deadlines; it does not change lifecycle behavior or authorize work.

## Review identity and boundary

- Worktree: `.worktrees/m2-s2`; branch `feature/feat063-m2-s2`; HEAD `5de30674bc826591ad4b3cc00fca53c7597ead51`.
- All 18 supplied input pins matched their expected byte counts and SHA-256 values before content review and again before this report was written.
- Root and worktree `AGENTS.md` and the repository-root `.codex/sketch2life-harness.md` were read. There is no worktree-local `.codex/sketch2life-harness.md` at the requested path.
- This was a read-only documentation review. No tests, validators, builds, backend/runtime, database, migration, Docker, install, network, provider, Modal, or Android command was run. No runtime or database behavior was inferred from documentation.
- The worktree was already dirty before this review. Those pre-existing changes were preserved. The designated report path was absent at review start; it is the only file created by this review.

## Finding

### P3-01 — Label the earlier sequencing gates as Draft 3 proposals

`FR_C08_PARENT_TEACHER_CANCEL_PURGE_IMPLEMENTATION_SPEC_DRAFT3_20261115.md` §3 (line 27) places M2 reconciliation before FR-C-08 implementation planning, and §5.1 (line 60) requires named module owners before an implementation allowlist can be proposed. D-208 in `DECISIONS.md` line 535 requires M2 reconciliation before FR-C-08 implementation and named owners before launch. The lifecycle plan §4 (lines 36–43) sequences M2 reconciliation, owner assignment and contract work before the separate allowlist package.

These are reasonable proposed planning sequences, but they advance the stated D-208 deadlines. Label the earlier sequencing as a Draft 3 proposal for later owner review, or align the binding wording with D-208's before-implementation and before-launch boundaries. The named owners remain unassigned; no owner is invented here.

## Verified requirements

1. **Cancel eligibility:** Rev68 UC-11 gives exactly the 13 requested cancel states and excludes `COMPLETED`, `FAILED`, `ABANDONED`, `DELETE_PENDING` and `DELETED` (SRS line 1518). Spec Draft 3 §4 reproduces the same matrix and exact 13-state list (line 54).

2. **Explicit DELETE eligibility:** UC-07 allows a user-requested DELETE for `COMPLETED`, `FAILED` or `ABANDONED`, and states that `FAILED`/`ABANDONED` are not automatically purged (SRS lines 1470 and 1472). Section 21.2 carries the same three-state eligibility (line 1674). Draft 3 preserves it (Spec §4 lines 48–50 and §5.2 line 65; Lifecycle Plan §3 lines 22–23).

3. **Pending and terminal lifecycle read:** Rev68 keeps `DELETE_PENDING` public until required purge is verified and exposes `DELETED` only afterward (SRS UC-11 line 1520; §21.2 line 1674). Draft 3 uses the owner-scoped `GET /v1/story-runs/{id}` as the default, requires verification that its approved response is sufficient, and adds no route, state, version field, percentage or count by inference (Spec §5.2 lines 66–67; Lifecycle Plan §3 line 28). The SRS separately describes this GET as the default lifecycle read at §21.6 line 1736 and the composed run read at line 1811.

4. **Current authority:** UC-07 and UC-11 name the Parent owner or currently assigned Teacher, validated against current BE1 assignment/version; former Teacher status and creator provenance alone do not authorize (SRS lines 1469–1470 and 1517–1518). Draft 3 carries that rule and does not treat a caller-supplied organization ID or assignment as authority (Spec §5.1 line 60).

5. **Revocation, cancellation, fencing and purge:** Rev68 requires immediate fencing of API, download, playback-token, cache, upload and job-dispatch access; job/provider cancellation is best-effort; late results are fenced, non-playable and purged; Story releases its lock in its own transaction (SRS UC-07 line 1472; UC-11 lines 1520–1521; BR-26 line 270). Draft 3 retains owning-module purge, private derivatives, incomplete uploads, idempotent retry, independent-reference verification for shared assets, quota usage and successful Teacher sample-claim retention, and the provider/backup evidence limit (Spec §§5.3–6, especially lines 71 and 75–83; Lifecycle Plan §5 lines 47–49).

6. **Open scope and ownership:** D-208 keeps Parent scope typed `PARENT_ACCOUNT` with no fabricated organization ID; the physical representation, versioned cross-module contract and durable receipt ownership/schema remain open (DECISIONS.md line 535). The DTR's scope rules agree (lines 73–75). Draft 3 leaves those items, named owners, audit-reader permissions, physical audit mapping and the 180/365-day record-type map OPEN-TECHNICAL (Spec §§6 and 8, lines 79, 83, 106 and 112; Lifecycle Plan §4 C1 and §6 items 3 and 9). It does not claim DTR or physical-schema changes.

7. **M2 and the FR-C-08 allowlist:** The pinned M2 implementation report says `PARTIAL / NOT COMPLETE` and records no DDL, new route, provider call, job cancellation or purge worker (lines 3 and 20). D-208 line 535 makes M2 a separate coordination gate and explicitly bars transfer of its approvals, allowlists and command ceilings. Draft 3 keeps that separation (Spec §§3 and 9; Lifecycle Plan §§2 and 4 C0/C7). The current FR-C-08 Allowlist Draft 1 remains `PROPOSED / NOT APPROVED / NOT LAUNCHED` (line 3); its scope points to the earlier Spec Draft 1 (line 7). Draft 3 flags the inherited completed-run-only wording as a conflict for a later allowlist revision (Spec §9 line 116; Lifecycle Plan §7 line 67), and neither edits nor approves the allowlist. D-207's approval remains scoped to the separate M2 allowlist and its launch boundary (`approvals/TASK_APPROVAL.md` lines 2880–2890).

8. **SRS and DTR status:** The Rev68 history entry says the update follows D-208, preserves Rev67 and the D-203 pin as history, leaves the DTR, routes and StoryRun state inventory unchanged, and remains unsigned (SRS lines 4 and 39). `SRS_AUTHORITY.md` lines 9–14 and 40, and `SOURCE_REGISTER.md` lines 6, 13 and 720, identify Rev68 as the unsigned canonical working SRS and retain Rev67 provenance. D-203 is recorded at `DECISIONS.md` line 530. The DTR matches its supplied unchanged pin; no physical-schema state was inferred.

9. **Approval boundary:** Both Draft 3 documents remain DRAFT / NOT APPROVED / NOT LAUNCHED and explicitly authorize no implementation, DDL, route, approval, test, provider action or launch (Spec §§1 and 11; Lifecycle Plan §§1 and 9). D-208 is a documentation-only SRS direction, not implementation, allowlist, command, database/migration, test, launch or provider approval (`DECISIONS.md` line 535).

## Exact input pins verified

All entries below matched the supplied byte count and SHA-256 exactly.

| Input | Bytes | SHA-256 |
|---|---:|---|
| FEAT-063 `DECISIONS.md` through D-208 | 216212 | `52F2E141244829281FF762BA100D1A991D5CADFF042A237C8C125F324300725F` |
| Canonical SRS Rev68 | 639948 | `69C83FE49CD4689D5D2540656D3319721838CF7343BAD00E24CDE558B8F5E944` |
| `docs/context/SRS_AUTHORITY.md` | 4313 | `D6153D38000C95E43A4091C5DF2E856FAD872A33177E3A8542E30EF2BEDCAB60` |
| `docs/context/PROJECT_CONTEXT.md` | 83919 | `B53D00641590E5B0DB7D6D19603AB796F19658F9F3F6AD8BC31076FDF51D631D` |
| `docs/context/SOURCE_REGISTER.md` | 116802 | `AA85FBB167AB065322258C5C90F05AF40B331BA30F9009020E40147B9DEACC6B` |
| `DATA_TABLE_REGISTER.md` (unchanged) | 171609 | `7CDFDBECDC24E28BB08E62C98A33B338165350204447EBC59B86F5BE69899BC2` |
| FR-C-08 implementation specification Draft 3 | 19897 | `1D680D04D1B06ED827F0FFD71A30D5E2C2AFC09828158997276D1F8424F37313` |
| FR-C-08 lifecycle plan Draft 3 | 13246 | `832D3653A38BAF8E3D82D75C319D7BA275B7628510074932DF726F459EB8A95E` |
| FR-C-08 implementation specification Draft 2 | 44378 | `4C4C905B19883C94C8E60109E9731B9289B5F4C31A780020DAD9420211EB7318` |
| FR-C-08 lifecycle plan Draft 2 | 24996 | `300BEC5A0716B8CFC09896E52B9752F5D6EBF499C4BB86822A71AF9D29A41310` |
| Current FR-C-08 Allowlist Draft 1 | 44643 | `82978E82A2A07A94007E7574BC43FA45663CA3B03D72FAEFDD24C15964D01800` |
| FEAT-063 `approvals/TASK_APPROVAL.md` including D-207 | 410676 | `C6A506404AF68A6180E150B83DE120113CE5EA54FCD7DEDFF9EAB01E4D375088` |
| M2 implementation report | 25879 | `F49D1FDB2B3C26387FFABC51C316F226C5D1FC5FC12B4856B0A6172A81941F55` |
| M2 Draft 18 | 101153 | `5CA09CC6F9D936C1BA74772251F4D3A9C0480F3E6F82818FE11114205FD3E331` |
| M2 Draft 18 independent review | 5169 | `4CE583BA092D140C62E7F1600E4B58778569885D7F7E3B62FB812839DD09835B` |
| M2 implementation allowlist Draft 1 | 14768 | `7DCEEB785C2121D250B7C016EDC2030E2CD7912F87BE537F07CC8B359A2A0CE8` |
| M2 allowlist independent review R2 | 2715 | `6872DA02B2CD88644AED71BA039D9ABBD38F243639DD44EDCCBAF2000C57645D` |
| M5/M6 roadmap | 20115 | `A0A485EE421FBB1DA9DEC99DD8EC08279D14EAF27EC548AD6A0A4CE8F234F8FA` |

The allowlist's cited FR-C-08 Spec Draft 1 was outside the supplied strict pin set. It was consulted only to locate the inherited completed-run wording that Draft 3 flags; it was not used as current product authority. The current SRS and D-208 remain controlling.

## Limits and conclusion

This is an independent read-only documentation review, not approval, implementation authorization or launch. The review verifies document consistency only; it does not establish runtime behavior, database contents, effective permissions, token/cache/upload invalidation, provider cancellation, object deletion or physical schema. The OPEN-TECHNICAL items remain open as recorded.

**Result:** READY WITH NOTES. Before a later approval, clarify P3-01 as proposed planning sequencing or align its deadlines to D-208. No other P1/P2/P3 finding was identified.
