# FEAT-064 — Sequential Goal A2 → B1 → B2

- Status: **DRAFT / AWAITING OWNER REVIEW**.
- Goal type: one umbrella goal with three strictly sequential phases and explicit owner/review gates.
- This document is a coordination and execution plan. It is not a blanket implementation approval, a database authorization, or permission for a live Modal call.
- Priority: resume the legacy FEAT-064 canvas / BE1–BE2 pilot chain A2 → B1 → B2. This temporarily takes priority over milestones 2–6 in the separate Parent/Teacher photo-based roadmap. It does not delete or rewrite that roadmap.

## 1. Pinned planning inputs

Planning checkout observed on 2026-11-03:

| Input | Value |
|---|---|
| Branch | `feature/feat063-be-foundation` |
| HEAD | `b6dbfa68e66718f3f40902c093e9ebd634b1ebb9` |
| Index | Clean at planning capture |
| Existing chain baseline manifest | `.claude/handoff/snapshots/FEAT064_CHAIN_BASE_20261103T165013/manifest.json` — SHA-256 `249C34A8E3FA6B1C98076AEC629E02F4158A5F19905378EBEBF6B81F4AEB4D7C` |
| V4 owner decisions | `.claude/handoff/OWNER_DECISIONS_G3G4_V4_20261101.md` — SHA-256 `E11FFBCE0F655C010E679773D231D3E36930A0B960E705450499E2A2A69191F6` |
| A2 continuation plan | `plan/CHAIN_A2_REV3_PLAN_20261103.md` — SHA-256 `0F384549BE15D3BF38AF73287F9C6487D2D5B7AEAA1BFB08D71E18BE7CD2BA91` |
| A2 main-BE database addendum | `plan/CHAIN_A2_MAIN_BE_DB_ADDENDUM_20261103.md` — SHA-256 `4AFA521E50A91FB6B06D4BB33303AEC3A39021BECEB2A26907964B99EDF15BB7` |
| B1 plan | `plan/CHAIN_B1_REV2_PLAN_20261103.md` — SHA-256 `BAA53AC8DB529107C3C9EB340FE2C900251535AB0D183209C157B6F4082A62B4` |
| B2 plan | `plan/CHAIN_B2_REV2_PLAN_20261103.md` — SHA-256 `DBE886D1BCCC1C14A54BA8FE2C499AAA29FA46A742D888E7882D0EE8F776C7DB` |

The captured working tree had 58 entries, including local A2 work and unrelated FEAT-063/FEAT-064 changes. The manifest is a historical planning capture, not an execution baseline. Before each phase launch, recapture branch, HEAD, index, every status path and hashes; make a byte-copy snapshot of dirty allowlisted paths as required by V4. Preserve every unrelated path byte-for-byte. If the observed checkout no longer matches or an unlisted path needs editing, stop and report the difference.

The phase plans remain subject to their own phase gates. Before implementation of each phase, the owner must issue a separate launch that pins the current plan hash(es), current checkout baseline, exact allowlist, and any required database identity. For A2, pin both the Rev3 base plan and the owner-approved main-BE database addendum. Approval of this umbrella goal does not substitute for that launch.

## 2. Goal definition and completion

Complete the remaining accepted scope of A2, then the analysis-only/T8 scope of B1, then the T9/T13-dry-run/T12 scope of B2. Each phase must pass its own acceptance checks, stop at `XONG-CHƯA REVIEW`, and receive an **independent review ACCEPTED** before the owner launches the next phase.

The umbrella goal is complete only when:

1. A2, B1, and B2 each have implementation evidence, exact-path snapshots, and independent review records marked **ACCEPTED**.
2. The owner has recorded the final ledger disposition for each accepted phase.
3. B2 reports the T12 database gate and all non-database checks truthfully; a blocked or `NOT RUN` T12 means the umbrella goal is not complete.

Independent reviews are performed in separate review sessions, not by subagents. This coordination session does not implement the phases.

## 3. Ordered phases and gates

| Phase | Frozen scope | Required exit | Next-phase gate | Rough effort |
|---|---|---|---|---:|
| A2 | Only the remaining T2C/T7b evidence and the reproduced test-owned PostgreSQL teardown issue in `CHAIN_A2_REV3_PLAN_20261103.md`, amended only by `CHAIN_A2_MAIN_BE_DB_ADDENDUM_20261103.md`. No speculative cleanup, assertion weakening, AI Jobs source/schema/migration changes, or unrelated route/test changes. | Focused and required PostgreSQL tests pass against the existing full BE database `sketch2life` only under the addendum's identity, no-migration, synthetic-only write, and exact-cleanup gates; offline runner, strict mypy delta, Ruff, validators, diff-check and snapshot are recorded. Stop at `A2 XONG-CHƯA REVIEW` or `BLOCKED`. | Separate reviewer records **ACCEPTED**; owner updates the A2 ledger to its final accepted disposition (normally `COMPLETE`) and sends a separate B1 launch. | 0.5–1 day if the existing BE DB and local credentials are ready; otherwise blocked by environment or safety gates. |
| B1 | Analysis-only/zero-Sketch plus T8 worker/composition pilot, exactly as in `CHAIN_B1_REV2_PLAN_20261103.md` and V4 §3 D6. No T9, T12, T13, migration, Modal, GPU, provider, or UI. | Prove no Sketch/cache/prohibited-event side effects; pilot defaults off; BE1-backed authorization/eligibility; one-attempt guarded worker behavior; no re-dispatch after UNKNOWN/HOLD; tests, static checks and snapshot recorded. Stop at `B1 XONG-CHƯA REVIEW` or `BLOCKED`. | Separate reviewer records **ACCEPTED**; owner updates B1 ledger and sends a separate B2 launch with a fresh post-B1 snapshot and approved T12 DB identity. | 1–2 days. |
| B2 | Four T9 routes, T13 synthetic dry-run through a stub loopback server, and T12 PostgreSQL acceptance, exactly as in `CHAIN_B2_REV2_PLAN_20261103.md`. | T9 contract/auth/projection tests pass; T13 completes synthetic flow and demonstrates bounded UNKNOWN/no external retry; T12 migration/integration checks pass on the approved task-owned disposable DB. Record real counts, migration status, static checks and snapshot. Stop at `B2 XONG-CHƯA REVIEW` or `BLOCKED`. | Separate reviewer records **ACCEPTED**; owner records final ledger disposition. | 2–3 days if the DB gate is ready. |

Estimated implementation effort is **3.5–6 working days**, excluding independent review turnaround and environment/database delays. This is a planning estimate, not a completion promise.

## 4. Phase transition rules

1. Work on one phase at a time. Do not overlap A2, B1, or B2 implementation because they share assistance, vision, runtime, test, and database contracts.
2. A phase ending `XONG-CHƯA REVIEW` is not accepted and does not unlock the next phase. After each phase report, stop and wait for the owner to provide the separate independent review result and launch the next phase.
3. For B1, the A2 gate is: an independent A2 review says **ACCEPTED**, and the latest A2 ledger disposition is **COMPLETE**. The earlier `XONG-CHƯA REVIEW` record remains historical evidence, not the required final state.
4. For B2, the B1 gate is: an independent B1 review says **ACCEPTED**, and the owner has recorded B1's final accepted ledger disposition.
5. If any review returns `NEEDS_REVISION`, return only to that phase under a new owner-approved review-fix plan. Do not move forward until it is accepted.
6. If a phase needs a path, schema, migration, DB operation, runtime behavior, or provider action outside its frozen plan, stop and request a new exact scope. Never infer approval from a green validator or from approval of another phase.

## 5. Database and provider boundaries

- A2 is the owner-approved exception: its PostgreSQL verification may use the existing full BE database `sketch2life` only under `CHAIN_A2_MAIN_BE_DB_ADDENDUM_20261103.md` and a fresh separate A2 launch. Verify exact database/user/owner/loopback/version read-only before test writes; no migration or schema change is allowed.
- B2 T12 still requires a task-owned, disposable, local-loopback database whose exact identity is supplied in the separate B2 launch. Do not infer that the A2 exception applies to B1/B2.
- Do not reset, drop, truncate, recreate, or broadly clean `sketch2life`, `be1_acceptance`, or any shared/unknown database. For A2, the only writes/cleanup are exact synthetic identifiers created by the current test fixture, as specified in the addendum. For B2, cleanup remains limited to exact synthetic rows from its approved run.
- If the expected A2 DB identity, schema, local credentials, exclusive test access, or exact-cleanup safety cannot be verified, mark A2 PostgreSQL `NOT RUN / BLOCKED`; do not fall back to another database. If no safe task-owned DB is supplied for B2, mark T12 `NOT RUN / BLOCKED`.
- No phase in this umbrella goal calls Modal, GPU, or an external provider. B2's T13 is a stub-loopback dry-run only. `OWNER_MODAL_CALL_APPROVED` remains `NO`.
- Do not stage, commit, push, merge, reset, stash, or clean the checkout. Preserve local changes. Commit/push decisions are separate owner tasks after review.

## 6. Required report at each phase boundary

For each phase, report in Vietnamese:

- branch, HEAD, index state, baseline/snapshot identity and exact changed paths;
- the exact plan hash and approval/launch gate used;
- actual test, database, Ruff, mypy and validator outcomes, distinguishing `PASS`, `FAIL`, `SKIPPED`, `NOT RUN`, and `BLOCKED`;
- unresolved findings, DB/provider actions not performed, and whether an independent review is still required;
- no claim of completion or acceptance beyond the recorded evidence.

After A2 and B1, provide the reviewer with the phase report and snapshot, then stop. After B2, stop for final independent review. Never advance automatically.

## 7. Explicitly outside this umbrella goal

- Any real child data or production/legal-consent enablement.
- UI implementation, M2–M6 implementation, and any rework of the photo-based Parent/Teacher product flow.
- Modal live calls, GPU/provider calls, deployment, or credential provisioning.
- Changes to old V4 decisions, old goal files, historical approvals/reports, or the SRS unless a separate plan is reviewed and approved.
- Any work not included in the exact phase allowlist and separately authorized launch.
