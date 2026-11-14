# M2 S2 Draft 10 Cold Review — 2026-11-13

## Verdict

**CHANGES REQUIRED.** Draft 10 preserves the owner’s approval boundaries and applies the Rev60/Rev67 authority correctly, but its planned combined-app route set conflicts with the no-dev-route decision, and its migration audit is stale against the `origin/dev` snapshot it names. The listed S2 gates remain proposals; this report grants no approval.

**Review mode:** read-only plan review, not an approval, implementation authorization, allowlist, gate approval, or launch. I did not run backend, database, Docker, Modal, pytest, mypy, Ruff, validators, or install commands. The only file created by this review is this report.

**Independence:** This was a fresh-context cold review of the assigned sources. I did not use or request another session’s review reasoning or summaries, and I did not delegate the review.

Draft 10 reviewed: 53,129 bytes; SHA-256 `A1A680FE6DC94F6AE3A9ED9FAA766B957269A26E33BE69A64FDA58702098BC1D`.

## Findings

### P1-1 — Combined composition can mount the forbidden dev StoryRun route and collide with the target adapter

**Evidence:** Draft 10 §1.3 says to add the target adapters to both the classroom and combined profiles (`M2_S2_TASK_APPROVAL_DRAFT10_20261113.md:69-73`). Its static audit misidentifies `parent_story_runs.py` as `/api/parent/v1/story-runs` (`:204`) and later says only `/api/parent/v1/*` dev routes are excluded (`:262,268`). The owner decision prohibits dev Parent v1 story routes in M2 (`DECISIONS.md:523`). In the reviewed source, `parent_story_runs.py` is actually mounted at `/v1/story-runs` (`backend/src/sketch2life/interfaces/http/routers/parent_story_runs.py:43,116`); the combined composition includes that router by default (`backend/src/sketch2life/interfaces/http/router_composition.py:60-77`), and `create_app()` selects it when `STORYRUN_LITE_MAIN_DEMO_ENABLED=0` (`backend/src/sketch2life/interfaces/http/app.py:260-267,1003-1008`). The OpenAPI projection already lists `POST /v1/story-runs` (`backend/src/sketch2life/interfaces/http/openapi_srs_v22.py:8-20`).

**Impact:** The planned combined profile can retain the dev Parent StoryRun handler at the same method/path as the S2 target. That conflicts with D-196’s no-dev-route direction and leaves route dispatch/schema ownership ambiguous. The test profile in §1.3 is classroom, but §1.3 also commits the combined profile to the target route set.

**Suggested fix:** Correct the router-prefix claim. State explicitly that the combined S2 composition excludes or replaces `parent_story_runs_router` before installing the approved target adapter, and identify which profile owns each route. Keep the dev `/api/parent/v1/ai/*` routes excluded as well. Do not treat the existing projection entry as S2 target approval.

### P1-2 — Migration graph and `story.runs` baseline audit do not match the current dev snapshot

**Evidence:** Draft 10 calls `20261104_story_revisions` the latest Story-chain node (`M2_S2_TASK_APPROVAL_DRAFT10_20261113.md:50,147`) and describes a different `20261110_parent_profile_story_context` / `20261110_parent_lesson_pin` migration in its retained dev audit (`:207-222`). The local `origin/dev` ref is `c87d8008b70910eb0a4d3579b9490312e7e3143f`, the PR 25 merge named by Draft 10 (`git -C .worktrees/m2-s2 branch -avv`, `git -C .worktrees/m2-s2 show -s c87d8008`). That tree contains `backend/alembic/versions/20261112_parent_story_context.py`: it sets `revision = "20261112_parent_story_context"` and `down_revision = "20261104_story_revisions"` (`:10-13`); it refuses to proceed unless `story.runs` is empty (`:30-47`); it adds context/snapshot and lesson-pin columns (`:116-158`). D-196 explicitly defers the snapshot and lesson pin and selects no additive Story DDL (`DECISIONS.md:523`); Draft 10 itself repeats that boundary (`:149,264-265`).

**Impact:** The plan’s “latest node” statement is false for the cited dev snapshot, and the plan does not disposition the migration whose effects D-196 defers. The actual task-database row state and Alembic version state were not inspected, so an empty `story.runs` baseline is not established. Applying the child migration would exceed the current owner decision.

**Suggested fix:** Reconcile §§1.1, 5.1, and 7.1–7.3 against `origin/dev` at `c87d8008`. If the planned Gate A target remains `20261104_story_revisions` to exclude the deferred child migration, say so explicitly and stop describing it as the latest node. Record `20261112_parent_story_context` as excluded from current scope; any later proposal to apply it needs a separate reviewed plan and owner decision, plus a freshly verified empty-`story.runs` precondition. No migration or database action is authorized by this review.

### P2-1 — AT-08 route authentication does not disposition the accepted S1a-P2 BE1 role-adapter gap

**Evidence:** Draft 10 requires authenticated Parent target routes and real route/auth wiring (`M2_S2_TASK_APPROVAL_DRAFT10_20261113.md:71,103-107`), while also preserving the production BE1 role adapter as `NOT COVERED` (`:8,13,18,274`). D-190 records that limitation and says it can close only after separate BE1 state alignment (`DECISIONS.md:507`); the S1a-P2 closure record repeats it (`M2_S1A_P2_CLOSURE_RECORD_20261112.md:21-23`).

**Impact:** The planned PostgreSQL acceptance has no stated identity/role path that can satisfy “real” Parent authorization while preserving the known gap. A stubbed role result could make the test pass without verifying the production BE1 adapter; using the current adapter may depend on columns D-190 says are absent from the task database.

**Suggested fix:** Define which authenticated principal and role/ownership boundary AT-08 will exercise. State explicitly whether the accepted gap is outside the S2 assertion or whether acceptance is blocked pending a separate BE1 alignment decision. Do not label a stubbed role result as production adapter coverage.

### P2-2 — AT-09 and AT-10 need explicit observable outcomes for their success and boundary cases

**Evidence:** AT-09 requires success only after a durable `SUCCEEDED` state and authoritative receipt, but does not state the expected public response (`M2_S2_TASK_APPROVAL_DRAFT10_20261113.md:104`). The existing Pilot Assistance status adapter maps an accepted authoritative completion to `processing_state="submitted_to_teacher"` (`backend/src/sketch2life/interfaces/http/routers/pilot_assistance.py:382-432,493-505`); its public `status` field is only `pending`, `cancelled`, or `unavailable` (`:95-103,435-440`). AT-10 says ages 36 and 120 “may proceed” without specifying the expected response or persisted effect (`M2_S2_TASK_APPROVAL_DRAFT10_20261113.md:105`).

**Impact:** A later reviewer cannot determine the exact passing assertion for the success path or the valid age boundaries from the criterion alone.

**Suggested fix:** Specify the AT-09 response field/value for an accepted receipt and the fail-closed response when it is absent. For AT-10, specify the contract-visible result and expected StoryRun-side write for ages 36 and 120, alongside the existing zero-write refusal assertions for 121 and 155. The trusted lookup fixture and prohibition on inserting legacy ages into `parent.*` are otherwise consistent with the Round 4 review (`M2_S2_S3_PLAN_REVIEW_ROUND4_20261110.md:29,46`).

### P3-1 — Dev CI baseline risk is not recorded with the merge context

Draft 10 records PR 25 and local `origin/dev` tip `c87d8008` as context (`M2_S2_TASK_APPROVAL_DRAFT10_20261113.md:292,309`) but does not record the four pre-existing red CI jobs identified in the review request. I could not independently verify those job statuses without network access or a repository CI-result artifact. Before later integration checks, add a dated, pinned source for that baseline or label it as owner-supplied context so those failures are not misattributed to S2.

## Verified OK

- **Authority:** `docs/context/SRS_AUTHORITY.md:5-14` selects the unsigned FEAT-063 v2.7-draft Rev60 artifact as the current working SRS. Draft 10 correctly keeps Rev67 comparison-only (`:11,253,288`) and does not change the authority.
- **D-194 / S1a-P2:** `DECISIONS.md:521`, `approvals/TASK_APPROVAL.md:2848-2859`, the closure record (`:3-10,21-23`), and the real-PostgreSQL addendum (`:10-22,59-71`) support ACCEPTED WITH KNOWN GAP, consumed failed Gate P2, no retry, three remaining synthetic rows, and production BE1 role adapter NOT COVERED. Draft 10 preserves those limits (`:8,13,18,274`).
- **D-196:** basis B, no dev Parent StoryRun routes, no additive Story DDL, deferred snapshot and lesson pin, and K3 carried NOT VERIFIED with the Story-chain target as the stop condition match `DECISIONS.md:523` and Draft 10 `:147-149,261-268`.
- **D-197:** S1b remains DEFERRED; Q-04/Q-13 remain unanswered; no sharing; OI-05 through OI-08 stay OPEN/deferred; real-child-data/provider use remains blocked; `OWNER_MODAL_CALL_APPROVED=NO`. These match `DECISIONS.md:524` and Draft 10 `:249,305`.
- **BQ-1/BQ-2:** the legal post-context transitions/resume behavior and Parent cancel/abandon route remain open in the handoff (`BE_AI_HANDOFF_FOR_AI_AGENT_20261113.md:44-52`) and are carried as dependencies in Draft 10 (`:21,300-301`).
- **S2 target contract:** the three Story routes and their principal scope align with D-171 (`DECISIONS.md:475`) and Rev60 §21.2 (`SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md:1616-1649`), with Parent-only scope narrowed by D-171. The three assistance compatibility operations and separate Teacher-pending inventory are present in the current source (`assistance_requests.py:45,54-63,98-117`; `pilot_assistance.py:447-455,458-510`) and correctly distinguished in Draft 10 (`:30-41,104`).
- **Rev67 crosswalk:** the dated crosswalk’s rows are Rev61 CONDITIONAL, Rev62 CONDITIONAL, Rev63 CONDITIONAL, Rev64 NOT AFFECTED, Rev65 CONDITIONAL, Rev66 CONDITIONAL, and Rev67 CONDITIONAL (`M2_REV67_CROSSWALK_FOR_S2_S3_20261113.md:14-22`). Draft 10’s claim that effects remain conditional and do not expand the route set matches its disposition (`:11,253,268`) and the crosswalk current-state section (`:24-30`).
- **S3 and prior reviews:** Draft 10 correctly leaves S3 Draft 5 unchanged pending accepted S2 and a separate review (`:294`). Round 4 was a static review of S2 Draft 5/S3 Draft 5, not Draft 10 approval (`M2_REV67_CROSSWALK_FOR_S2_S3_20261113.md:29`; `M2_S2_S3_PLAN_REVIEW_ROUND4_20261110.md:27-31,58-60`).
- **Approval boundary:** the document says DRAFT / NOT APPROVED / NOT LAUNCHED, with no exact allowlist, and describes its inherited command ceilings only as unapproved proposals (`M2_S2_TASK_APPROVAL_DRAFT10_20261113.md:3,158-183,270-276`). D-194/D-196 do not grant S2 approval or launch (`DECISIONS.md:521,523`). I found no invented gate, command, allowlist, or launch authorization.
- **Dev ref:** the local `origin/dev` ref points to `c87d8008b70910eb0a4d3579b9490312e7e3143f`, whose subject is PR 25’s merge. This verifies Draft 10’s stated local snapshot, not the live remote’s present state.

## AT-08–AT-10 and route-set assessment

The acceptance scenarios are materially more testable than the earlier drafts: AT-08 requires a real OS-process exit and a new composition; AT-09 names the three exact assistance operations and forbids substituting the Teacher-pending route; AT-10 avoids writing an out-of-range age into the Parent schema. The route list agrees with D-171 and Rev60. The remaining testability issues are P2-1 and P2-2 above: resolve the BE1 role-adapter boundary, state public success assertions for AT-09, and state explicit positive outcomes for AT-10. No runtime exposure or PostgreSQL behavior was tested.

## Rehashed input pins

Every row in Draft 10 §13 was independently rehashed for byte count and SHA-256. All 20 rows match the recorded values. The two owner-record paths and the crosswalk resolve to the M2 worktree; the remaining paths resolve to the root checkout or the cited mobile worktree.

| Input | Bytes | SHA-256 |
|---|---:|---|
| Draft 9 | 49,154 | `6B6821710E3A5716DFA5AB6FB827A980F96717109BA8F0640BB93CBAEBF58C9C` |
| S3 Draft 5 | 23,308 | `BC2518817202C6275CED9543200CC17DAAADA36759FF4B53C4FF3D16928A2B9D` |
| S2/S3 Round 4 review | 9,553 | `D2A4BB19B513F9B69A2D0AE51FFDB30D2631F96CAC82C3A6C84A38B00495CE26` |
| S1b decision brief | 2,368 | `CBD93FA70F45B82C22F42E6D956AE0E5E956A2BB067E1D0EF7B5ADE70E8E637D` |
| M2 Parent/Teacher Draft 11 | 133,204 | `6F3EFD72D3A70209B06771AC437998AE241842ABD4F20D11019E6B1166B48A68` |
| BE/AI handoff | 9,206 | `F746A7B3D425A2C6EF0541C28A8584CC8CEF0D6D0F140CD09A68F14F9FA091EA` |
| S2/S3 open questions | 8,274 | `2E74E680B6074BDFCA2DD91EA7C18BB85587B2F94F1674F6EB01B31C36952A9D` |
| S2/S3 status report | 19,418 | `5E926225AE94ECC703B572735A325A8FFA5D4438B1E03F4803BF2F86141932D1` |
| SRS authority | 4,054 | `032223EDDD46D251DE052C54BFF16AB1D4D794F865A457272507D893E3C1521F` |
| Root source register | 113,526 | `D09F5849F4A3829EC4241FF1A840319225909E0EECA93A9BF6964625C4E987A0` |
| FEAT-063 source register | 66,896 | `08A0AE379D87CD237A923F921E2FC7F1385BAAE63C74F264FEBD24721FC1EED1` |
| FEAT-063 context | 113,670 | `7137B59263B7B886F3EB5A18D741DB08F976E3E08947C7BE80679ED3FE50EDEF` |
| Canonical Rev60 SRS | 553,948 | `70DA43A35106E8C02B4BB8FCCB9628C0376C9E7EA6CFC51909ACB569703B218B` |
| Owner-supplied Rev67 | 634,291 | `B704163C9AAF7BB198D8578699F75DB8766C2226A52CD48B0ED1314AF5E21996` |
| S1a-P2 closure record | 3,503 | `0C1801119F17D98FBD4ADA2C7D884530DFAB4A068AF88DE7C74525ADA61F40E4` |
| S1a-P2 real-PostgreSQL addendum | 5,547 | `6BB4A6EA6F477B44486A4E518766099CC2DA9A97246DE7ADAD08E4C00C891485` |
| DECISIONS.md after D-194–D-197 | 190,063 | `BDC6FB0A5F5B350F1C3DDD21175277FB169B618BFFE8075567FBF485B02F813C` |
| TASK_APPROVAL.md with S1a-P2 addendum | 404,042 | `0D4E434C2D932C5FBF09D7BAE75DBA46CD29835AA41884FBFEBFC2A36C5DA73A` |
| Parent API Contract Rev67 | 9,573 | `0BB99DAFDC6592118B367EBEB60BC0D15FBE80DCD697499EB68EC135C302C47D` |
| Rev67 S2/S3 crosswalk | 9,184 | `98C3E656B2CDA391C103C21D10E780DF3BB102286E2053360C1690D03FC11891` |

## Could not be verified

- Whether `story.runs` is empty in the task database, the task database’s current Alembic version rows, or any live migration applicability/rollback behavior. No database command or connection was used.
- Runtime route exposure, actual OpenAPI output, real authentication/authorization, process-restart recovery, AT-08–AT-10, or any PostgreSQL acceptance result. No backend or test command was run.
- The four pre-existing red CI jobs on `dev`; no network or pinned CI result was available in the listed inputs.
- The live remote `dev` tip after the local `origin/dev` tracking ref at `c87d8008`; no network fetch was performed.

