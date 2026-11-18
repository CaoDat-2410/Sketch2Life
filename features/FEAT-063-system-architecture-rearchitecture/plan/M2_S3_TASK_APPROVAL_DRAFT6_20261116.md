# M2 S3 task plan — contract freeze and M2 closure, Draft 6

**Status: DRAFT / NOT APPROVED / NOT LAUNCHED / S3 ENTRY BLOCKED.** This is a planning successor to historical Draft 5. It does not approve S3, implementation, tests, validators, database or migration work, provider calls, network access, stage, commit, or push. Drafts 1–5 remain unchanged. No S3 Task Approval or launch instruction is present in this draft.

**Date:** 2026-11-16  
**Worktree:** `.worktrees/m2-s2`, branch `feature/feat063-m2-s2`, HEAD `5de30674bc826591ad4b3cc00fca53c7597ead51`.  
**OWNER_MODAL_CALL_APPROVED:** NO.

## 1. Authority and current gate state

- The active FEAT-063 working SRS is unsigned v2.7-draft Rev68, as recorded in this worktree's `docs/context/SRS_AUTHORITY.md`. It is the current requirements source for this lane; it is not signed or final. The root checkout still points at Rev60. Reconcile that authority pointer before publishing this lane's requirements or merge package across worktrees.
- D-203 adopted Rev67 as the working baseline. D-208 directed a documentation-only Rev68 reconciliation, scoped its dispositions to FR-C-08 planning, and grants no S3 implementation, test, or launch authority. Do not interpret Rev68's FR-C-08 additions as S3 work.
- D-171 keeps S1b deferred, M2-AT-05/06/07 NOT RUN / DEFERRED, and NFR-36 and NFR-38 PARTIAL. Those dispositions remain the M2 closeout boundary. S3 must not turn PARTIAL into PASS.
- D-188 accepts K3 as an unresolved limitation. D-198 carries K3 as NOT VERIFIED and says to stop only if accepted evidence cannot establish the Gate A Story-chain target. The historical Draft 5 rule that unresolved K3 alone blocks S2/S3 closeout is superseded and must not be used.
- D-198 fixes S2 to the integrated Parent StoryRun implementation. D-199 uses the existing owner-scoped Parent reads `GET /v1/story-runs/active/current` and `GET /v1/story-runs/{run_id}` for job-status evidence; it does not mount a separate `/v1/jobs/{job_id}` target. The standalone Jobs route in Draft 5 is stale.
- D-207 approves only its pinned S2 implementation allowlist and ceilings. It does not approve the mapper correction in S2 Mapper Draft 3 or any S3 action. The one-time FEAT-047 description overlay and combined S2 verification invocation are recorded as consumed.
- Roadmap Addendum Draft 3 preserves the sequence M2 S2/S3 → FR-C-08 → Parent API contract reconciliation → selective PR #26 integration at M3 entry. This plan does not advance FR-C-08, the API audit, or PR integration.

**S3 entry is currently blocked.** The S2 report is PARTIAL / NOT COMPLETE. Its recorded evidence includes 81/82 tests in an earlier owner-provided run, an incomplete/failed later combined invocation, 335 mypy errors, and 17 Ruff diagnostics; the approved verification ceilings are consumed. S2 Mapper Fix Draft 3 remains DRAFT and identifies an unresolved owner choice about the public route-metadata API available in locked FastAPI 0.162.0. The worktree is dirty and the S2 changes are not an accepted, committed S2 baseline. No checks were rerun for this plan.

S3 cannot start until S2 has an accepted and committed closure, exact current source pins, a recorded S2 inventory/baseline, and a separate S3 Task Approval plus launch instruction. The S3 plan itself does not satisfy those entry gates.

## 2. S3 purpose and scope

S3 is a documentation, contract-freeze, and M2 evidence-reconciliation phase after S2. It adds no product feature, route, schema, database table, migration, PostgreSQL operation, provider integration, UI/client integration, or M3 opening.

The proposed S3 deliverables, after separate approval, are:

1. A complete inventory of operations in an explicitly pinned runtime composition, distinct from the client-facing OpenAPI projection.
2. An AT-01 through AT-11 evidence ledger reconciled to accepted S1a-P and S2 evidence and to D-171's allowed partial/deferred dispositions.
3. A frozen contract and compatibility classification for every inventoried operation, with source and evidence level recorded.
4. A limitation/inherited-condition ledger that preserves accepted evidence boundaries and unresolved items.
5. A separately reviewed closeout recommendation, followed by an owner decision on S3 acceptance and M2 closure.

S3 does not use or publish a runtime result merely because a plan, decorator, router, OpenAPI entry, or test file exists. Distinguish at least: source-declared, composed/mounted, present in generated runtime schema, present in the client-facing projection, exercised by an accepted test run, and runtime-verified. Mark unavailable evidence NOT RUN or NOT VERIFIED.

## 3. Operation inventory and contract boundary

The S3 approval must pin the exact application composition, environment flags, dependency versions, dotenv behavior, and offline test node before any OpenAPI generation or test. Do not reuse Draft 5's proposed profile without rechecking it against the current application, composition root, route catalog, and accepted S2 contract. Do not launch a database, call a provider, or access the network to create this evidence.

The inventory must enumerate every method/path/tag in the selected runtime schema exactly once and classify it with an explicit requirement/decision/source authority. Produce and hash separate artifacts for:

- the complete runtime OpenAPI schema;
- the complete method/path/tag route inventory, including composition profile and classification; and
- the client-facing OpenAPI projection.

The runtime inventory and client-facing projection have different purposes and need not contain the same paths. Preserve pre-existing projection membership as an observed source fact; membership alone does not establish target-contract status. Do not add, remove, retag, or reclassify a projected operation under this plan without the authority required for that change.

Use these accepted-phase contract seeds only to guide reconciliation; they are not a claim that current routes are mounted or verified:

| Seed | Current authority and classification direction |
|---|---|
| `POST /v1/parent/profiles`, `GET /v1/parent/profiles/{profile_id}`, `PATCH /v1/parent/profiles/{profile_id}` | S1a-P target contracts; freeze only from accepted S1a-P evidence and the current SRS/decisions. |
| `POST /v1/story-runs` | S2 Parent StoryRun target under D-198; freeze only from accepted S2 evidence. |
| `POST /v1/story-runs/{run_id}/cancel` | S2 Parent cancel contract under D-199 and its subsequent controlling decisions; preserve pending-delete semantics. A 202/PENDING response is not proof of completed purge. |
| `GET /v1/story-runs/active/current`, `GET /v1/story-runs/{run_id}` | Existing Parent owner-scoped reads used for S2 job-status evidence under D-199. Do not invent a separate `/v1/jobs/{job_id}` target. |
| The three assistance compatibility-test operations and other mounted legacy BE1/classroom/demo operations | Inventory from current source and the pinned runtime composition; classify under the controlling compatibility decision. Do not promote them to new target contracts because they are mounted or present in a projection. |
| Any additional proposal or conditional Parent StoryRun operation | Record actual source/composition/OpenAPI evidence and its `[PROPOSAL]` or conditional status. It is not an accepted M2 target absent explicit authority. |

The exact target set and schema names must come from the accepted S1a-P/S2 contracts and current owner decisions. Draft 5's six-operation seed, standalone Jobs route, historical tag assumptions, and runtime profile are not controlling. If the current source, accepted phase evidence, and decision record cannot be reconciled, stop and request an owner decision; do not infer a new contract.

For every operation, the contract freeze records: stable contract key/version; method/path and parameter spelling; target/compatibility/other classification; actor and authorization scope; request/response schemas; required headers; status and error contract; idempotency/revision/invariants; exact composition and flags; SRS/decision/source citations; declared/mounted/schema/test/runtime evidence levels; and relevant artifact/source hashes.

## 4. M2 acceptance-test evidence ledger

At S3 entry, copy each status only from an accepted phase record. Do not copy planning statuses as results and do not run tests under this draft.

| Acceptance test | S3 closeout rule |
|---|---|
| M2-AT-01 through M2-AT-04B | Reconcile each row to its accepted S1a-T/S1a-P evidence and recorded scope limitations. Missing or failed required evidence blocks closure unless an owner-approved partial disposition explicitly applies. |
| M2-AT-05, M2-AT-06, M2-AT-07 | May remain NOT RUN / DEFERRED while S1b remains DEFERRED under D-171. Preserve that status; do not call it PASS. |
| M2-AT-08, M2-AT-09 | Reconcile to accepted S2 evidence. Current S2 implementation report records these checks as incomplete/failed; no new result is inferred. |
| M2-AT-10, M2-AT-11 | Reconcile to accepted S1a-T/S1a-P/S2 evidence and adopted Rev68 requirements, recording any approved scope limitation. |

The S3 closeout table must include runner/owner, date, exact approved command or owner-run reference, result, exit status, evidence path and digest, accepted scope, and limitations. A failed, interrupted, missing, stale, or owner-unverified result remains so. New verification requires its own exact allowlist, command ceiling, approval, and launch instruction.

## 5. Fixed M2 dispositions and carried limitations

Under D-171, record S1b as DEFERRED and M2-AT-05/06/07 as NOT RUN / DEFERRED. Record NFR-36 as PARTIAL: child-media access is deferred to M5, cross-organisation feedback to M6, and Platform Admin child-media access remains deny by default. Record NFR-38 as PARTIAL: M2 claims age and language metadata only; AC-65 story work is assigned to M4 and video work to M5. These are explicit M2 dispositions, not completed SRS acceptance.

Reconcile inherited conditions using their newest accepted records. In particular:

- Carry K3 as NOT VERIFIED under D-188/D-198. Do not require resolution of the historical discrepancy as a universal S3 stop. Stop only if accepted evidence cannot establish the Gate A Story-chain target.
- Treat historical A2, B1, B2, N-1, and N-3 labels as evidence pointers requiring current source/owner reconciliation, not as current database or runtime facts. Preserve each known limitation and provenance; never claim a live database state from static files.
- Keep the D-188 accepted S1a-P limitations and all current S2 failures/unknowns visible. S3 cannot repair, mask, or broaden them.
- Keep OWNER_MODAL_CALL_APPROVED=NO. No real-child data, provider/Modal call, external service, or production inference is authorized.

## 6. Acceptance criteria for a future S3 closeout

S3 can be recommended for owner closure only when all applicable criteria below have accepted evidence:

1. S2 is accepted and committed, and the exact commit and all input files are re-pinned. Its implementation report, test/type/lint outcomes, and limits are reconciled without converting any failure or unavailable result into a pass.
2. The selected OpenAPI profile and flags are approved and reproducible within the authorized offline environment. The generated runtime schema, full route inventory, and client-facing projection are separately captured and hashed.
3. Every runtime operation is inventoried exactly once and has an evidenced classification and authority. Every target contract is sourced from accepted S1a-P/S2 records. Compatibility and proposal routes remain explicitly distinct.
4. Every M2-AT row has an accepted result or the exact D-171 deferred/partial disposition. Any other missing, failed, or unverified required gate remains blocking unless the owner records a specific accepted disposition.
5. K3 is reported as NOT VERIFIED unless newer accepted evidence changes it; the Gate A Story-chain target is established by accepted evidence. NFR-36/38 and S1b remain at their fixed partial/deferred status.
6. The output includes the contract-freeze matrix, AT ledger, inherited-condition/limitations register, and hashes/source references. No new route, schema, product rule, migration, or SRS change is introduced.
7. A fresh independent cold review of the exact pinned S3 package reports READY or READY WITH NOTES with zero P1/P2 findings. The owner separately records S3 acceptance and M2 closure; review is not owner approval.

Passing these criteria does not authorize FR-C-08, client integration, M3, a database action, or PR #26 integration. Those remain on the separate roadmap with their own approvals.

## 7. Entry gates, stop conditions, and future approval package

S3 execution remains stopped until all of these are true:

- S2's unresolved mapper API choice is answered by the owner and any required plan/approval is separately reviewed;
- S2 implementation and required verification reach accepted closure without exceeding consumed command ceilings;
- the post-S2 baseline is committed and every S3 input is rechecked against that baseline;
- this S3 plan has received an independent review and the owner approves an exact S3 allowlist and command card; and
- the owner provides a separate launch instruction for those exact pins and commands.

Stop and return to the owner if an operation cannot be reconciled to current authority; a route/classification/projection change is needed; the pinned profile differs; required S2 evidence is absent or failed; a new requirement or scope expansion is proposed; the Gate A Story-chain target cannot be established; or a requested check requires an unapproved database, network, provider, or runtime action.

Before launch, a separate approval must specify exact R/E/N/H repository paths with hashes, exact output artifacts, environment and flags, test node and invocation, credential/database isolation, per-command ceilings, writable cache/basetemp locations, expected evidence, and stop rules. No command name or ceiling from historical S3 Draft 5 is authorization. No tests, validators, builds, OpenAPI generation, typecheck, lint, database inspection, or network work are authorized by Draft 6.

## 8. Current source pins and observation limits

These hashes pin the planning observations only; they are not launch-time authorization. Recompute them after S2 closure and before any review/approval. The pre-draft worktree observation was 70 status entries (24 modified, 46 untracked, 0 staged); the dirty S2 baseline is not a merge or S3 execution baseline.

| Input | Bytes | SHA-256 | Use / limit |
|---|---:|---|---|
| `docs/context/SRS_AUTHORITY.md` | 4,313 | `D6153D38000C95E43A4091C5DF2E856FAD872A33177E3A8542E30EF2BEDCAB60` | Rev68 authority; worktree only; root authority remains Rev60. |
| `features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md` | 639,948 | `69C83FE49CD4689D5D2540656D3319721838CF7343BAD00E24CDE558B8F5E944` | Canonical unsigned working SRS Rev68 for this lane. |
| `features/FEAT-063-system-architecture-rearchitecture/DECISIONS.md` | 216,212 | `52F2E141244829281FF762BA100D1A991D5CADFF042A237C8C125F324300725F` | Current decision record through D-208. |
| `features/FEAT-063-system-architecture-rearchitecture/approvals/TASK_APPROVAL.md` | 410,676 | `C6A506404AF68A6180E150B83DE120113CE5EA54FCD7DEDFF9EAB01E4D375088` | Historical approvals; D-207 is limited to S2. No S3 approval inferred. |
| `features/FEAT-063-system-architecture-rearchitecture/status/STATUS.md` | 115,680 | `69AB9F119C2182E189230D5C96BD4E0C769059C71D39D64A5DAE3050DB749359` | Status history, not a current live-system observation. |
| `features/FEAT-063-system-architecture-rearchitecture/evidence/M2_S2_IMPLEMENTATION_REPORT_20261114.md` | 25,879 | `F49D1FDB2B3C26387FFABC51C316F226C5D1FC5FC12B4856B0A6172A81941F55` | Current S2 report; PARTIAL / NOT COMPLETE. |
| `features/FEAT-063-system-architecture-rearchitecture/plan/M2_S2_TASK_APPROVAL_DRAFT18_20261114.md` | 101,153 | `5CA09CC6F9D936C1BA74772251F4D3A9C0480F3E6F82818FE11114205FD3E331` | Historical S2 approved-scope plan; cites S3 Draft 5 stale K3 clause. |
| `features/FEAT-063-system-architecture-rearchitecture/plan/M2_S2_SHARED_OPENAPI_MAPPER_FIX_DRAFT3_20261116.md` | 17,569 | `47FBBDA1B3C21FFA6CCD4DFE4322BD1C6B9C8D4851A1B584699EA694E4019525` | DRAFT only; unresolved owner API choice. |
| `features/FEAT-063-system-architecture-rearchitecture/plan/M3_M6_SRS_ALIGNED_ROADMAP_ADDENDUM_DRAFT3_20261116.md` | 14,223 | `38A155C257F066780DEB9BEF21BC46AC4D94A9A4585DF9EC4043C38B81E65E95` | Owner-accepted planning order only. |
| Root-checkout `features/FEAT-063-system-architecture-rearchitecture/plan/M2_S3_TASK_APPROVAL_DRAFT5_20261110.md` (historical) | 23,308 | `BC2518817202C6275CED9543200CC17DAAADA36759FF4B53C4FF3D16928A2B9D` | Read-only historical plan. Its route seed and K3 stop rule are superseded; its proposed OpenAPI profile is unverified. Do not copy these as current requirements. |

**Boundary:** Draft 6 supersedes historical S3 Draft 5 only as a current planning proposal. It edits no approval, decision, SRS, status, implementation, test, or historical evidence. S3 remains closed pending owner approval and launch.
