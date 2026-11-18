# M2 S3 task plan — contract freeze and M2 closure, Draft 7

- **Status:** DRAFT / NOT APPROVED / NOT LAUNCHED. Planning successor to Draft 6. It approves nothing: no S3 work, test, validator, OpenAPI generation, database or migration action, provider call, network access, stage, commit or push. Drafts 1 to 6 remain unchanged.
- **Date:** 2026-11-17. **Author:** coordinating Claude session (Fable 5.2). **Owner:** Person 2. Not independently reviewed.
- **Worktree:** `.worktrees/m2-s2`, branch `feature/feat063-m2-s2`, HEAD `7cc5cf74d03c249d17b6c98c877ed3fb1a36b09a`, clean when this draft was written (this file is then the only uncommitted path).
- **Predecessor:** `plan/M2_S3_TASK_APPROVAL_DRAFT6_20261116.md`, 17,317 bytes, SHA-256 `BF7792925F06ED66720850CEE916EFBF2F724100B84D3B2BF3545F11E19108C4`. No review of Draft 6 exists.
- `OWNER_MODAL_CALL_APPROVED=NO`.

## 0. What changed since Draft 6

| Topic | Draft 6 | Now |
|---|---|---|
| Working SRS | Rev68 working copy, 639,948 bytes | The owner-supplied copy adopted by D-209, 701,157 bytes (section 8). It is unsigned and a different branch from the Rev68 working copy |
| S2 state | PARTIAL / NOT COMPLETE, uncommitted, "S3 entry blocked" | CLOSED by the owner with recorded debt and deviations, and committed as `7cc5cf74` |
| Mapper correction | Draft only, owner API choice unresolved | Owner chose lookup by exact public method and path; implemented; task accepted with recorded deviations |
| S2 test evidence | 81 of 82, then an incomplete combined run | Nine-file selection 84 of 84 passed on 2026-11-17 |
| S2 type and lint evidence | 335 Mypy errors, 17 Ruff diagnostics, unclassified | Compared with HEAD `5de30674`: Ruff 0 added; Mypy 19 added (accepted as typing debt), 336 existing |
| Runtime schema and projection | To be generated under S3 | Captured by the mapper task's post export in a pinned environment (section 3); reuse is an owner decision |
| Entry gates of Draft 6 section 7 | Five open | The first three are met; independent review, owner approval and launch remain |
| Source pins | Nine inputs | Five changed, four unchanged (section 8) |

## 1. Authority and current gate state

- The working SRS for this lane is the copy adopted by D-209, as recorded in this worktree's `docs/context/SRS_AUTHORITY.md`. It is unsigned and not final. The root checkout and the mobile worktree still point at Rev60; reconcile that pointer before publishing this lane's requirements or a merge package across worktrees.
- D-208 gave FR-C-08 planning dispositions against the earlier Rev68 working copy. The adopted SRS copy does not contain D-208's lifecycle wording, and D-209 leaves open whether deletion covers FAILED and ABANDONED runs. That question belongs to the FR-C-08 gate. S3 records it as OPEN-OWNER and does not resolve or assume it.
- The following decisions are carried from Draft 6 as it states them. They exist in `DECISIONS.md`; their text was not re-read for this draft, and S3 work must read them at the pinned hash before relying on them: D-171 (S1b deferred; M2-AT-05/06/07 NOT RUN / DEFERRED; NFR-36 and NFR-38 PARTIAL), D-188 (K3 accepted as an unresolved limitation), D-198 (S2 fixed to the integrated Parent StoryRun implementation; K3 carried as NOT VERIFIED), D-199 (job-status evidence through the existing owner-scoped Parent reads; no separate jobs route), D-203 (Rev67 baseline, now superseded as working source by D-209), D-207 (S2 implementation allowlist).
- The planning order of Roadmap Addendum Draft 3 is unchanged: M2 S2/S3, then FR-C-08, then Parent API contract reconciliation, then selective PR #26 integration at M3 entry. This plan advances none of the later items.
- S2 closure and mapper acceptance are in `approvals/TASK_APPROVAL.md` (entries of 2026-11-17). They close S2 only. They do not approve S3.

**S3 entry is no longer blocked by S2.** It still requires an independent review of this plan, an owner-approved S3 allowlist and command card, and a separate launch instruction.

## 2. S3 purpose and scope

Unchanged from Draft 6. S3 is a documentation, contract-freeze and M2 evidence-reconciliation phase. It adds no product feature, route, schema, table, migration, provider integration, client integration or M3 opening. It repairs no S2 debt.

Deliverables, after separate approval:

1. A complete inventory of operations in an explicitly pinned runtime composition, distinct from the client-facing OpenAPI projection.
2. An M2-AT-01 to M2-AT-11 evidence ledger reconciled to accepted S1a-T, S1a-P and S2 evidence and to the D-171 dispositions.
3. A frozen contract and compatibility classification for every inventoried operation, with source and evidence level.
4. A limitation and inherited-condition ledger, including the debt S2 was closed with.
5. A separately reviewed closeout recommendation, followed by an owner decision on S3 acceptance and M2 closure.

Evidence levels stay distinct: source-declared; composed or mounted; present in the generated runtime schema; present in the client-facing projection; exercised by an accepted test run; runtime-verified. Unavailable evidence is NOT RUN or NOT VERIFIED.

## 3. Operation inventory and contract boundary

The rules of Draft 6 section 3 stand: every method, path and tag of the selected runtime schema is enumerated exactly once and classified with an explicit requirement, decision or source authority; the runtime inventory and the client-facing projection are separate artifacts; projection membership is an observed fact, not target-contract status; no operation is added, removed, retagged or reclassified without the authority that change needs.

**Available capture (new in Draft 7).** The mapper task's post-fix export produced both schemas in the lock-exact task environment with a cleared child environment:

| Artifact | Bytes | SHA-256 | Content |
|---|---:|---|---|
| `backend/tmp/openapi-mapper-d10-post-367b579d97eb4f0a99cd6a6d329bb1f4/runtime-post.json` | 847,426 | `E9C2D7C8E95225F3D1F8B708C50C9ACC19CF822508ABEFD4F85298AD2E6B3A0C` | Runtime schema, 151 operations |
| `.../published-post.json` | 213,111 | `F23BF908A104667153F88D6438AE8E95BE9895A76DAB7099877EBE9EFC49589D` | Client-facing projection, 34 operations |
| `.../environment.json` | 6,917 | `E974D4926BEEF15DA04A669F1F714DEF6C117E79484BF115F29FEB252E940AAE` | Sanitized environment identity of the export |
| `.../run-manifest.json` | 8,706 | `1286E0F36FA98C9CEE19CB09415CA0BDE05D5606A9289A878850B96F6965548F` | Run manifest |

Facts that bear on reusing it:

- The export ran with the two export flags enabled (`SKETCH2LIFE_STORAGE_EXAMPLE_ENABLED`, `SKETCH2LIFE_SYNTHETIC_PILOT_ENABLED`), so it includes the pilot-only and local example operations. Whether that composition is the one to freeze is the profile decision of owner decision S3-D1.
- It ran without the operating-system egress block; the owner accepted that deviation for the mapper task.
- `app.py` and every other pinned source input of that export are unchanged since. Two test files changed afterwards; test modules are not inputs of the export. This is static reasoning, not a re-export.
- The files are under a git-ignored folder and exist on this machine only. A frozen contract that cites them needs them copied into the feature folder, or regenerated.
- The mapper comparison established that the published file equals the pinned projection of the runtime file, and that every catalogued operation carries the catalog description, tag and response status set.

The accepted-phase contract seeds of Draft 6 section 3 (Parent profiles; `POST /v1/story-runs`; `POST /v1/story-runs/{run_id}/cancel`; the two owner-scoped Parent reads; assistance compatibility operations and other mounted legacy operations; proposal or conditional Parent StoryRun operations) are carried unchanged as reconciliation guides, not as claims.

For every operation the freeze records what Draft 6 lists: contract key and version; method, path and parameter spelling; classification; actor and authorization scope; request and response schemas; required headers; status and error contract; idempotency, revision and invariants; composition and flags; SRS, decision and source citations; evidence levels; artifact and source hashes.

## 4. M2 acceptance-test evidence ledger

Each status is copied only from an accepted phase record. No test is run under this draft.

| Acceptance test | S3 closeout rule | Evidence to reconcile |
|---|---|---|
| M2-AT-01 to M2-AT-04B | Reconcile to accepted S1a-T and S1a-P evidence and recorded scope limits. Missing or failed required evidence blocks closure unless an owner-approved partial disposition applies | `evidence/M2_S1A_T_CLOSURE_RECORD_20261109.md`, `M2_S1A_T_IMPLEMENTATION_REPORT_20261107.md`, `M2_S1A_T_K4_SOURCE_RECONCILIATION_20261107.md`, `M2_S1A_P_CLOSURE_RECORD_20261109.md`, `M2_S1A_P_IMPLEMENTATION_REPORT_20261109.md`, `M2_S1A_P2_CLOSURE_RECORD_20261112.md`, `M2_S1A_P2_IMPLEMENTATION_REPORT_20261112.md`, `M2_S1A_P2_REAL_POSTGRES_EVIDENCE_ADDENDUM_20261113.md` |
| M2-AT-05, 06, 07 | May remain NOT RUN / DEFERRED while S1b is DEFERRED under D-171. Never PASS | D-171 |
| M2-AT-08, M2-AT-09 | Reconcile to accepted S2 evidence | `evidence/M2_S2_IMPLEMENTATION_REPORT_20261114.md`, `M2_S2_SHARED_OPENAPI_MAPPER_IMPLEMENTATION_EVIDENCE_20261117.md`, `M2_S2_CLOSURE_VERIFICATION_EVIDENCE_20261117.md` |
| M2-AT-10, M2-AT-11 | Reconcile to accepted S1a-T, S1a-P and S2 evidence and the adopted SRS, with any approved scope limit | As above |

Not established by this draft, to be established by S3 work:

- Which plan document is the controlling definition of M2-AT-01 to M2-AT-11. The adopted SRS copy contains no `M2-AT-` identifier; the rows are defined in the M2 Parent/Teacher foundation plan drafts and the S1a task approvals. S3 must name the approved one and pin it.
- Which of the 84 passed tests, if any, are the evidence for M2-AT-08 and M2-AT-09. A passed selection is not by itself a passed acceptance test.
- Whether the eight S1a evidence files cover every row they are listed for. They were not read for this draft.

The closeout table carries runner or owner, date, exact approved command or owner-run reference, result, exit status, evidence path and digest, accepted scope and limitations. A failed, interrupted, missing, stale or owner-unverified result stays so.

## 5. Fixed M2 dispositions and carried limitations

Carried from Draft 6: S1b DEFERRED and M2-AT-05/06/07 NOT RUN / DEFERRED under D-171; NFR-36 PARTIAL and NFR-38 PARTIAL as M2 dispositions, not completed SRS acceptance; K3 NOT VERIFIED under D-188 and D-198, stopping only if accepted evidence cannot establish the Gate A Story-chain target; the historical A2, B1, B2, N-1 and N-3 labels are evidence pointers needing current reconciliation, never live database facts.

Added by Draft 7 — what S2 was closed with, to be entered in the limitation ledger unchanged:

- Mypy: 19 `arg-type` diagnostics added by the S2 work in `routers/parent_ai.py` and `routers/parent_story_runs.py`, accepted by the owner as typing debt; 336 signatures existing at `5de30674`. Runtime effect not tested.
- Ruff: 17 diagnostics on the six S2 source paths and one `I001` on a contract test, all existing before S2.
- Only the nine-file pytest selection ran. The full backend test suite was not run for S2 or for the mapper task.
- Mapper task deviations: three first runs of one-shot checks failed and stay on record; the post export ran without the egress block; two test files changed after the export and comparison without re-runs; the request-ID inventory remains OPEN beyond the scope decided in the mapper's Amendment 1.
- The stale-version P3 on broader routes (Allowlist R2) is an open follow-up.
- The FEAT-047 description overlay on `be1_artifacts.py` is kept by owner decision.
- Open owner question for FR-C-08: deletion eligibility of FAILED and ABANDONED runs under the adopted SRS.
- Several 2026-11-17 records were not independently reviewed (mapper Amendments 2 and 3, both evidence reports, revision 3 of the closure-verification plan, the Mypy triage).

S3 cannot repair, mask or broaden any of these. `OWNER_MODAL_CALL_APPROVED=NO`: no real-child data, provider or Modal call, external service or production inference.

## 6. Acceptance criteria for a future S3 closeout

1. Every S3 input is pinned at commit `7cc5cf74` or a later named commit. S2's reports, test, type and lint outcomes and limits are reconciled without converting a failure, a waiver or an unavailable result into a pass.
2. The OpenAPI profile and flags are owner-approved. The runtime schema, the full route inventory and the client-facing projection are separately captured and hashed, and are present in the repository or reproducible from pinned inputs.
3. Every runtime operation is inventoried exactly once with an evidenced classification and authority. Every target contract is sourced from accepted S1a-P or S2 records. Compatibility and proposal routes stay distinct.
4. Every M2-AT row has an accepted result or its exact D-171 disposition. Any other missing, failed or unverified required gate blocks closure unless the owner records a specific disposition.
5. K3 is reported as NOT VERIFIED unless newer accepted evidence changes it; the Gate A Story-chain target is established by accepted evidence. NFR-36, NFR-38 and S1b keep their partial or deferred status.
6. The output contains the contract-freeze matrix, the AT ledger, the limitation register including section 5, and hashes and source references. No new route, schema, product rule, migration or SRS change.
7. A fresh independent cold review of the exact pinned S3 package (Sonnet 5.5 high or Opus 5.5 high, model and effort recorded) reports zero P1 and P2 findings. The owner separately records S3 acceptance and M2 closure; a review is not an approval.

Passing these criteria authorizes nothing beyond S3: not FR-C-08, client integration, M3, a database action or PR #26 integration.

## 7. Entry gates, owner decisions and stop conditions

Entry gates:

| Gate | State |
|---|---|
| S2 mapper API choice answered | MET (mapper task accepted 2026-11-17) |
| S2 implementation and verification at accepted closure | MET (owner closure 2026-11-17, with recorded debt) |
| Post-S2 baseline committed | MET (`7cc5cf74`); pushed to origin on 2026-11-17 |
| Independent review of this plan | NOT MET |
| Owner approval of an exact S3 allowlist and command card | NOT MET |
| Owner launch instruction | NOT MET |

Owner decisions this plan needs before an approval text can be exact:

- **S3-D1 — composition to freeze.** (a) Freeze the composition the mapper export captured (151 runtime operations, both export flags enabled), stating which operations exist only because of those flags; or (b) freeze a different, named profile, which requires a new export under its own approval. Recommendation: (a), because it is already captured, hashed and proven consistent with the catalog; the flags must be stated in the freeze.
- **S3-D2 — source of the schema artifacts.** (a) Reuse the mapper export files, copy them byte-for-byte into the feature folder and cite their hashes, carrying the egress deviation; or (b) regenerate with the egress block in effect under a new one-shot approval. Recommendation: (a). If (a) is chosen and S3-D1 is (a), S3 needs no tool run other than hashing and the repository validators.
- **S3-D3 — acceptance-test definitions.** Name the controlling document for M2-AT-01 to M2-AT-11.
- **S3-D4 — what "M2 closure" may carry.** Confirm that M2 can be closed with the section 5 debt recorded as follow-ups, or name the items that must be fixed first.

**Owner answers, 2026-11-17 (planning direction only; not an S3 approval and not a launch).** In the coordinating Claude session the owner was asked whether to accept the four recommendations above and answered "Push và đồng ý review". Recorded reading of that answer:

- S3-D1: (a), freeze the composition the mapper export captured, with the two export flags stated.
- S3-D2: (a), reuse the mapper export files, copied byte-for-byte into the feature folder, carrying the egress deviation.
- S3-D4: M2 may be closed with the section 5 debt recorded as follow-ups.
- S3-D3: NOT ANSWERED. The recommendation for this item was that the owner name the document, and the owner named none. Finding of the coordinating session, offered as a candidate only: D-151 records the owner's acceptance of `plan/M2_PARENT_TEACHER_FOUNDATION_PLAN_DRAFT10_20261106.md` (111,790 bytes, SHA-256 `7539D642FFD95A9A21C99A0C17C5095FF1443E19538017A92789F631D633E2B1`) as the M2 planning baseline; `M2_PARENT_TEACHER_FOUNDATION_PLAN_DRAFT11_20261107.md` (SHA-256 `6F3EFD72D3A70209B06771AC437998AE241842ABD4F20D11019E6B1166B48A68`) describes itself as a draft awaiting review, and no decision accepting it was found by a text search of `DECISIONS.md`. Later S1a and S2 task approvals and D-171 may have narrowed individual rows. The owner must confirm the controlling definition before the ledger is built.

The same answer authorized the push of the branch; origin `feature/feat063-m2-s2` was at `7cc5cf74d03c249d17b6c98c877ed3fb1a36b09a` after it.

Stop and return to the owner if: an operation cannot be reconciled to current authority; a route, classification or projection change is needed; the pinned composition differs from what the freeze describes; required S1a or S2 evidence is absent or failed; a new requirement or scope expansion is proposed; the Gate A Story-chain target cannot be established; the adopted SRS and an earlier decision conflict on a point S3 must state; or a requested check needs an unapproved database, network, provider or runtime action.

A later approval text must give exact repository paths with hashes, exact output artifacts, environment and flags, any command and its ceiling, writable locations, expected evidence and stop rules. Nothing in Draft 5, Draft 6 or this draft is an authorization.

## 8. Source pins and observation limits

Hashes pin the observations of this draft at commit `7cc5cf74`; they are not launch-time authorization.

| Input | Bytes | SHA-256 | Against Draft 6 |
|---|---:|---|---|
| `docs/context/SRS_AUTHORITY.md` | 5,120 | `CACA7EC03CB570F3276AEA3EAF9214F93DDEC19F3030671A47DB590E19F74726` | changed |
| `features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md` | 701,157 | `B9B1F42D0BB118C19C81607D3913B7E4F1D8B6F673F0C3FBB6402888FEB675F5` | changed (D-209) |
| `.../DECISIONS.md` | 219,748 | `00776DF5428F15F83633FB7205D8AC8F526A60710AC1204FA493B9FF4C303572` | changed (through D-209) |
| `.../approvals/TASK_APPROVAL.md` | 478,001 | `249E096717A2D38465D20E26F542A2C4934933EC37532D9D6E1AB49FC0FEAE37` | changed (through S2 closure) |
| `.../status/STATUS.md` | 121,560 | `6826345E901AFDADB5918835E203C71005C9B769D22A0D75AFC69A458EE77555` | changed |
| `.../CONTEXT.md` | 121,752 | `4DC5C4E07917FEE1B117A52A14948D870796D463F9B379661FDCA355F8E00638` | not pinned by Draft 6 |
| `.../evidence/M2_S2_IMPLEMENTATION_REPORT_20261114.md` | 25,879 | `F49D1FDB2B3C26387FFABC51C316F226C5D1FC5FC12B4856B0A6172A81941F55` | unchanged |
| `.../evidence/M2_S2_SHARED_OPENAPI_MAPPER_IMPLEMENTATION_EVIDENCE_20261117.md` | 12,424 | `CCB014AFB23D7A156FC4E229C7B4A717B758982D425023E075AAED632F5C60C6` | new |
| `.../evidence/M2_S2_CLOSURE_VERIFICATION_EVIDENCE_20261117.md` | 10,487 | `CF644A09FF0802F7A2E4444CCBCC9E01B67528A3DC8B3F718686E441ED454525` | new |
| `.../evidence/M2_REV67_CROSSWALK_FOR_S2_S3_20261113.md` | 9,184 | `98C3E656B2CDA391C103C21D10E780DF3BB102286E2053360C1690D03FC11891` | not pinned by Draft 6; written against Rev67, not re-read |
| `.../plan/M3_M6_SRS_ALIGNED_ROADMAP_ADDENDUM_DRAFT3_20261116.md` | 14,223 | `38A155C257F066780DEB9BEF21BC46AC4D94A9A4585DF9EC4043C38B81E65E95` | unchanged; it pins the earlier SRS copy |
| `.../plan/M2_S2_TASK_APPROVAL_DRAFT18_20261114.md` | 101,153 | `5CA09CC6F9D936C1BA74772251F4D3A9C0480F3E6F82818FE11114205FD3E331` | unchanged; historical |

Observation limits of this draft:

- Read for this draft: Draft 6 in full; the S2 implementation report; the two 2026-11-17 evidence reports (written by the same session); the D-209 row heading; file listings and hashes. Not read: the decision texts D-171 to D-208, the eight S1a evidence files, the Rev67 crosswalk, the M2 foundation plan drafts, and the adopted SRS beyond identifier counts (`NFR-36`, `NFR-38` and `FR-C-08` occur in it; `M2-AT-` does not).
- The operation counts 151 and 34 come from the mapper task's records, not from a new count.
- This draft was not independently reviewed. S3 remains closed pending review, owner approval and launch.
