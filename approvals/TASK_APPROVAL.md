# Task approval register

## FEAT-063 Plan Rev43 — as-built SRS alignment

- Status: `APPROVED` for the exact documentation scope in Plan Rev43.
- Approver: Project owner, direct instruction in this conversation on 2026-11-06: “update lại srs dựa trên hệ thống đang build hiện tại”.
- Recorded timestamp: 2026-11-06 00:48:54 Asia/Saigon.
- Feature: FEAT-063 — whole-repository architecture redesign.
- Approved plan: `features/FEAT-063-system-architecture-rearchitecture/plan/PLAN_REV43_AS_BUILT_SRS_ALIGNMENT_20261106.md`.
- Plan SHA-256 at authorization: `000A4D0C22BB92666C60C4597BB5B8AEB126E0D4C1F654B610909CC7BBDED945`. Current reviewed plan SHA-256: `1F10B3F447F7AFB59FAD847E6BE05F0C898B4CE4F6F51B0536258BBD1806F185`. Later edits record lifecycle completion and clarify AC2 with the AI/database boundary from the owner's adjacent table-use request; implementation scope remains documentation-only.
- Scope: update the canonical SRS and data-model companion with separately labeled implementation status; reconcile current model/role decisions; record local API/database and owner-supplied Modal dashboard observations; update canonical authority pointers and FEAT-063 tracking/evidence records.
- Acceptance criteria: AC1–AC7 in the hash-identified Plan Rev43.
- Exclusions: product/runtime/API/schema/data/migration/test/provider/deployment/secret changes; paid GPU calls; SRS sign-off; edits to preserved historical SRS bodies or unrelated work; staging, commit or push.
- Approval basis: the owner's direct request authorizes this documentation scope. It does not constitute formal product sign-off of the SRS.

## FEAT-063 Plan Rev44 — publish the as-built SRS alignment

- Status: `APPROVED` for the exact documentation publication scope in Plan Rev44.
- Approver: Project owner, direct instruction in this conversation on 2026-11-06: “commit and push”.
- Recorded timestamp: 2026-11-06 05:29:51 Asia/Saigon.
- Feature: FEAT-063 — whole-repository architecture redesign.
- Approved plan: `features/FEAT-063-system-architecture-rearchitecture/plan/PLAN_REV44_PUBLISH_AS_BUILT_SRS_20261106.md`.
- Plan SHA-256: `F54CD43EC4E42BB8B46E698D74688BB161929450793EAB301DC8CDC342EA3E47`.
- Scope: publish only the exact 16 paths listed in Plan Rev44 on a new branch based on the fetched `origin/dev`; preserve unrelated staged/unstaged/untracked work in the original checkout.
- Acceptance criteria: AC1–AC5 in the hash-identified Plan Rev44.
- Exclusions: SRS sign-off; product/runtime/API/schema/database/migration/test/provider/deployment/secret changes; force-push or rewriting `dev`; publication of unrelated work.
- Approval basis: the owner's direct instruction authorizes commit and push of the Rev43 documentation package as scoped in Plan Rev44.

## FEAT-063 ? Qwen3.5-only profile and FLUX.3 component retest

- **Status:** APPROVED / COMPLETE.
- **Approved by:** Project owner, by direct instruction in the active conversation.
- **Approval timestamp:** 2026-11-05 22:58:08 Asia/Saigon.
- **Feature:** FEAT-063 ? system architecture rearchitecture.
- **Plans:**
  - `features/FEAT-063-system-architecture-rearchitecture/plan/PLAN_REV46_QWEN35_ONLY_FLUX_SECRET_RETEST_20261105.md` ? approved SHA-256 `4F796831148D134B2EABB1CBF791AE1D41C341C9D0C736BED4ECCDC11632B51F`; execution closeout SHA-256 `9dc252d80ce46aeddb9eca1c10da6ad60e52c11907441cea2a3c426ecd324f8f`.
  - `features/FEAT-063-system-architecture-rearchitecture/plan/PLAN_REV46A_FLUX_COMPONENT_FILES_AND_FAILED_FLOW_RETEST_20261105.md` ? approved SHA-256 `334ACE80E495EFD453BED980F78F5F9767ADD98C2F32617BCAD8DB87B74C2AE8`; execution closeout SHA-256 `ab24410c6d4b3bcc69cb9acbaf9d58bf7b7ff5bcd6e6785ddb126b8ce375434e`.
- **Owner's direct model instruction:** ?x?a b?t qwen 2 ra ?i, d?ng qwen 3.5 th?i?.
- **Approved scope:** retire Qwen2.5 from active FEAT-063 model configuration and use only pinned `Qwen/Qwen3.5-9B` for active Qwen development workloads; preserve historical records. Fix FLUX.3 Diffusers component staging and run one checkpoint download plus one synthetic inference for each Rev46-terminal-failed image workload, using the existing Modal `dev` Secret without reading its value.
- **Acceptance criteria:** active Qwen workloads resolve only to the pinned Qwen3.5 model; FLUX checkpoint verifier requires transformer and VAE files and does not skip incomplete checkpoints because of an existing marker; the two failed image workloads each receive at most one post-fix attempt; output contracts or exact terminal failures are recorded; task-owned Modal app stops with zero tasks; no video, production enablement, real child data, destructive volume action, commit, or push.
- **Execution boundaries:** follow the two approved FEAT-063 plans and keep evidence in that feature's evidence directory. The feature-level plan and approval records remain canonical for detailed per-plan execution history.


## FEAT-063 Plan Rev50 ? local dev duplicate repair, Modal AI integration, and SRS authority

- **Status:** APPROVED / COMPLETE LOCALLY (not pushed) for the exact scope in Plan Rev50.
- **Approver:** Project owner, direct instruction on 2026-11-06 to fix duplicated `dev` commits without changing commit names; selected the full Modal AI branch and pending AI changes. The owner?s prior instruction to keep the newest FEAT-063 SRS canonical is also preserved.
- **Recorded timestamp:** 2026-11-06 06:13:08 Asia/Saigon.
- **Feature:** FEAT-063 ? system architecture rearchitecture.
- **Approved plan:** `features/FEAT-063-system-architecture-rearchitecture/plan/PLAN_REV50_DEV_DUPLICATE_REPAIR_AND_MODAL_AI_INTEGRATION_20261106.md`.
- **Approved plan SHA-256 at authorization:** `404B793E8A00438882A8CC0532013EC5CD7BB188577EF35713A73DC5EF696936`.
- **Current plan SHA-256 after execution closeout:** `783E4EA92CED5BDFC041945653D5DC135CAD7E5D2EDF5830DEF627E31DCA473F`.
- **Scope:** retain a backup of the current dirty checkout; reset only the local `dev` ref to `origin/dev` to remove six patch-equivalent local copies; commit the 269 manifested pending Modal changes (excluding retained pytest scratch directories); integrate the full Modal branch and the published FEAT-063 SRS v2.4 branch while preserving all existing commit objects/messages; record evidence and run the required repository security validator.
- **Acceptance criteria:** AC50.1?AC50.7 in the hash-identified plan.
- **Exclusions:** no push, force push, remote history rewrite, rebase, amend, squash, commit-message change, tests or provider calls, cleanup of the scratch directories, or modification of unrelated dirty checkout content.
- **Approval basis:** direct owner instructions in the current and preceding conversation; this record authorizes only the exact plan scope above.

### Execution closeout ? local dev merge

- Local `dev` merge commit: `370cb26d6e8c99c126f4a5a16df132eaa70c8e70`.
- Full Modal and SRS v2.4 histories are present; zero patch-equivalent duplicates remain relative to `origin/dev`.
- Original dirty checkout is preserved on `backup/dev-before-dedup-20261106-575139a5`; the remote branch was not pushed or rewritten.
- Security validation passed; product tests and AI/provider calls were not run.


## FEAT-063 Plan Rev50 Addendum ? fast-forward publish repaired dev

- **Status:** APPROVED / COMPLETE (fast-forward pushed) for the exact publication scope in the addendum plan.
- **Approver:** Project owner, direct instruction on 2026-11-06: ?commit n?u c?n v? push.?
- **Recorded timestamp:** 2026-11-06 06:43:00 Asia/Saigon.
- **Feature:** FEAT-063 ? system architecture rearchitecture.
- **Approved addendum:** `features/FEAT-063-system-architecture-rearchitecture/plan/PLAN_REV50_ADDENDUM_DEV_FAST_FORWARD_PUSH_20261106.md`.
- **Approved plan SHA-256 at authorization:** `B8D2C5D83BD5766080207F1F2F8283713A915BFB9EABB49645B95143AE6F3C25`.
- **Current plan SHA-256 after execution closeout:** `5959C210013C294178BF574A8645E218421DDB63D024D5022C68597D049E5C7C`.
- **Scope:** security-validate and push only the repaired local `dev` to `origin/dev` using a regular fast-forward push; fetch and verify the exact resulting remote HEAD.
- **Acceptance criteria:** AC50A.1?AC50A.5 in the hash-identified addendum.
- **Exclusions:** force push/history rewrite, other refs, tests or provider calls, and unrelated checkout changes. This addendum supersedes only the earlier no-push boundary; all existing commit subjects/objects remain unchanged.


### Execution closeout ? publication

- `origin/dev` was fast-forwarded from `c98701b1e500906f396e773c79ec3bba55db2542` to `0d15b1a0ae6e5373354d7ac35cc163e41b55c42e`.
- Fresh fetch confirmed remote and local `dev` match at `0d15b1a0ae6e5373354d7ac35cc163e41b55c42e`; working tree was clean.
- Security validator passed; existing commit messages/objects were preserved.

## FEAT-063 Plan Rev45 — SRS system and code alignment

- Status: `APPROVED` for the exact documentation-only scope in Plan Rev45; not SRS content sign-off.
- Approver: Project owner, direct SRS review/update request on 2026-11-06.
- Recorded timestamp: 2026-11-06 12:28:16 Asia/Saigon.
- Plan: `features/FEAT-063-system-architecture-rearchitecture/plan/PLAN_REV45_SRS_SYSTEM_CODE_ALIGNMENT_20261106.md`.
- Plan hashes: authorization `AD0554469128DD3DF13484DD7A78BAB42B99CB026C5D433D61D7D48E26950F1A`; approved scope addenda `E9F11167D6BFD1D9D341559B36C1003943460D48B98E0F88D0BDAFA3A2E0A385`, `3BE2B7AB19C69EB229768376B7BD1D041003C175D57B808BBE1BC2706D7BC453`, `1B8A1AD64F80A70D5BDA553311629787936900571B92BBB94433F83191C43175`; final local review `880EC6A2B3DB0B3FBC23A0386589EE2E1E3863E9295F3F1169D9BE7469752F46`.
- Published-port plan SHA-256: `53102EBB02521BC747DA0E79971B1AA636371C4830D501A173D9D7971930C05C`; Plan Rev51 approves its path reindex as EV-063-55 because EV-063-34 is already assigned on `origin/dev`.
- Scope: update the canonical SRS to v2.5-draft, reconcile existing AI directions and local source/runtime boundaries, and update matching authority/tracking records. The v2.5 SRS remains unsigned.

## FEAT-063 Plan Rev51 — publish SRS v2.5 and reconcile latest dev source

- Status: `APPROVED` for the exact publication scope in Plan Rev51.
- Approver: Project owner, direct instruction in this conversation on 2026-11-06: “commit and push”.
- Recorded timestamp: 2026-11-06 17:16:12 Asia/Saigon.
- Approved plan: `features/FEAT-063-system-architecture-rearchitecture/plan/PLAN_REV51_PUBLISH_REV45_SRS_20261106.md`.
- Plan SHA-256 at authorization: `919CD35DC42973A5FE06C9D99D56DC851B4FCDB1313E1AF0612CB525D78116A8`.
- Scope: publish the v2.5-draft SRS/document package on a new branch from fetched `origin/dev` `4749451080f49243464d40a464b8f83a03ae77bb`; add a source-only §32.6 review of that tree; preserve newer remote records and exclude unrelated checkout work.
- Acceptance criteria: AC1–AC8 in the hash-identified Plan Rev51.
- Exclusions: code/API/schema/data/migration/test/build/provider/Modal/deployment/secret changes; SRS sign-off; push to `dev`; force-push/history rewrite; PR creation; and publication outside the manifest.
- Approval basis: the owner's direct request authorizes commit and push of this reviewed SRS package under Plan Rev51, not publication of unrelated work.

### Plan Rev51 execution close-out

- Recorded timestamp: 2026-11-06 17:33:39 Asia/Saigon.
- Final reviewed Plan Rev51 SHA-256: `06DC756E35F621F8232E89ABE8CDBFFD7FFEF493D0EF09050F1D25A2E26EE394`.
- Package commit `620386fb227e2d8b76c48e72ad22892e3b0c1c53` was pushed to `origin/docs/feat063-rev45-srs-code-alignment-20261106`; fresh fetch confirmed the remote SHA matched.
- The security validator passed before the package commit and first push, scanning 6,563 publishable files each time. No force push or `dev` update was performed.

## FEAT-063 Plan Rev51 — bounded Modal AI and legacy API retest

- **Status:** APPROVED for the exact scope in Plan Rev51.
- **Approver:** Project owner, direct instruction on 2026-11-06 to continue fixing Modal AI, diagnose and raise only proven execution timeouts, minimize inference usage, test existing APIs, consolidate all results/products in one folder, stop used Modal apps, and commit coherent fixes as they are completed.
- **Recorded timestamp:** 2026-11-06 07:02:29 Asia/Saigon.
- **Feature:** FEAT-063 — system architecture rearchitecture.
- **Approved plan:** `features/FEAT-063-system-architecture-rearchitecture/plan/PLAN_REV51_MODAL_AI_AND_LEGACY_API_RETEST_20261106.md`.
- **Approved plan SHA-256:** `B20103A217D7A9623E02279CE0BD82D5BC61141518D820FA683104057B1A6A2F`.
- **Execution closeout SHA-256:** `1CD7EC57885C20484DD1FBB166C917DABF586C58BEFBE49FF2D2B3FDB1BA953C`.
- **Scope:** reconcile all current non-video Modal AI workload evidence against SRS v2.4-draft; reuse already-passed synthetic artifacts; diagnose the unresolved optional SAM 2.1 capacity timeout and permit at most one bounded synthetic call; raise a timeout only if evidence shows execution was cut off by that timeout; run regression/contract coverage for the current 124-operation API surface and read-only live health/docs/OpenAPI checks; collect outputs and a consolidated API report in the plan's single FEAT-063 evidence folder; stop task-used Modal apps; make only directly related, reproducible AI/contract fixes and commit them separately after security validation.
- **Acceptance criteria:** AC51.1–AC51.8 in the hash-identified plan.
- **Exclusions:** video workloads; broad unrelated legacy refactors; writes/migrations to the shared development database; production enablement; secret/credential access; deleting Modal Volumes/checkpoints; force-push, merge, or push.
- **Approval basis:** the owner's direct request authorizes the bounded test, AI worker and API regression actions, task-app cleanup, and commits exactly as limited by Plan Rev51.

## FEAT-063 Plan Rev52 - non-video Modal AI reliability and observability

- **Status:** APPROVED for the exact scope in Plan Rev52.
- **Approver:** Project owner, direct instruction on 2026-11-06 to continue fixing all non-video Modal AI, add worker logs that reveal failure causes, and keep running verification until the non-video work is complete.
- **Recorded timestamp:** 2026-11-06 12:15:20 Asia/Saigon.
- **Feature:** FEAT-063 - system architecture rearchitecture.
- **Approved plan:** `features/FEAT-063-system-architecture-rearchitecture/plan/PLAN_REV52_NONVIDEO_MODAL_AI_RELIABILITY_20261106.md`.
- **Approved plan SHA-256:** `9703A6CFE3AAF6108A1443B4E7F93805481475A0C60C64C50414106441158938`.
- **Current plan SHA-256 after formatting:** `6B3B1C25CD2A9974860A93551CDAD0FB3363DB38CB00D293ABB4818C9F0782D2`.
- **Scope and exclusions:** exactly as stated in Plan Rev52; all nine registered non-video workloads, safe worker/caller telemetry, current mounted AI API flows, synthetic verification and task-app shutdown; no video, real child data, production enablement, secret-value access, shared database writes or push.
- **Approval basis:** the owner's direct request authorizes the scoped implementation, synthetic Modal tests and local conventional commits after repository security validation.

## FEAT-063 Plan Rev53 — one-shot SAM 2.1 gate retest

- **Status:** APPROVED for the exact scope in Plan Rev53.
- **Approver:** Project owner, direct instruction on 2026-11-06: “test lại sam2 đi, cho mở gate”.
- **Recorded timestamp:** 2026-11-06 18:36:29 Asia/Saigon.
- **Feature:** FEAT-063 — system architecture rearchitecture.
- **Approved plan:** `features/FEAT-063-system-architecture-rearchitecture/plan/PLAN_REV53_SAM2_GATE_RETEST_20261106.md`.
- **Approved plan SHA-256:** `C2695A200FF15253E88E52CC458DC0DA718A51E2B9F8A4EC37BCED198D1EE8B5`.
- **Scope:** add the `drawing.segment` envelope to the narrow L4 worker allowlist, keep the product registry disabled, verify the pinned checkpoint through one CPU preflight, make at most one synthetic SAM2 GPU call in Modal `dev` with the existing 600-second worker timeout and 1,800-second wait bound, record safe stage-level evidence, then stop the task app.
- **Acceptance criteria:** AC53.1–AC53.7 in the hash-identified plan.
- **Exclusions:** production/product API enablement, real child media, repeated GPU calls, timeout increase absent worker-timeout evidence, video, secret-value access, shared database writes, Volume deletion, merge, push, or history rewrite.
- **Approval basis:** this entry records the owner's direct authorization for the exact bounded gate-open test above; it does not approve SAM2 as a required V1 or production workload.
- **Execution closeout:** COMPLETE WITH FINDINGS. The one synthetic worker call passed, while visual quality was partial (central body only); `workloads.json` remains disabled. Dedicated Modal app stopped with 0 tasks. See `features/FEAT-063-system-architecture-rearchitecture/evidence/sam2_gate_retest_20261106/RESULTS.md`.

## FEAT-063 Plan Rev54 - integrate SRS v2.5 and Modal AI into dev

- **Status:** APPROVED for the exact integration scope in Plan Rev54.
- **Approver:** Project owner, direct instruction on 2026-11-06: “merge 2 cái nhánh nãy vào nhánh dev, gồm cái sửa srs và AI”.
- **Recorded timestamp:** 2026-11-06 19:06:22 Asia/Saigon.
- **Approved plan:** `features/FEAT-063-system-architecture-rearchitecture/plan/PLAN_REV54_MERGE_SRS_V25_AND_MODAL_AI_TO_DEV_20261106.md`.
- **Approved plan SHA-256:** `C6882123DF3F1671AF7014784651E9F6A37AD799BA3763223BFC10C9E2A9F937`.
- **Scope:** integrate SRS branch `fae180dcf3ea2771b41546aa6925b94636821df1` and AI branch `c6818490d0d889ab17dc9f8de3830987eb2a230d` into `dev`; preserve all source commits; resolve the two approval-register conflicts by retaining both histories; run security validation and push normally to `origin/dev`.
- **Acceptance criteria:** AC54.1-AC54.8 in the hash-identified plan.
- **Boundaries:** SRS v2.5 remains an unsigned draft; SAM2 product workload remains disabled. No force push, history rewrite, video inference, new AI calls, or unrelated branch changes.
- **Approval basis:** this direct owner instruction authorizes the integration and dev publication; it does not sign off the SRS as final.

### Plan Rev54 local execution checkpoint

- Status: COMPLETE. Fast-forwarded local `dev` and pushed normally to `origin/dev`; the fetched remote matched integration commit `47e5308a5c547df8dab5f3c560f949ee925f441e`. A later closeout documentation commit was pushed normally as well.
- AI merge: `634e0e20f56cbfa6101ece6e67f3e4267a30ae92`; SRS merge: `6bbb375a359fb78f06585963b8ee9f7bfc2246ff`.
- Conflict handling retained both histories. SRS decision IDs D-144/D-145 were reassigned to D-148/D-149 to preserve all four records without duplicate IDs.
- Evidence: `features/FEAT-063-system-architecture-rearchitecture/evidence/EV-063-57_SRS_V25_AND_MODAL_AI_DEV_INTEGRATION_20261106.md`.
- Validation: `git diff --check` passed; `python tools/validate_repository_security.py` reported `REPOSITORY_SECURITY_VALID` with 6,731 publishable files scanned before commit and push. No force push or history rewrite.

## Revision 13 authorization — Restore Parent registration UI and auth link

- Approved plan: features/FEAT-036-ui-current-direction-alignment/plan/PLAN_REV13_PARENT_REGISTRATION_UI_AND_AUTH_LINK.md
- Plan revision: 13
- Plan SHA-256: 0832F08952DA8B48342EE61FA257EAB2BD46DBC4EDBF101D8C593D77DDC951D5
- Approval status: APPROVED
- Prepared / approved: 2026-11-10
- Reviewer / approver: Project owner (explicit instruction in this conversation)

### Authorization recorded

The owner requested: “Thiếu đăng ký lấy lại UI và đường dẫn đăng ký ở UI auth cho tôi đi”. This authorizes a visual-only Parent registration page and a registration entry on the Parent sign-in screen.

### Approval boundaries

- Add the registration screen and sign-in link in the existing Parent auth visual system.
- Preserve email navigation state; do not pass passwords through route state.
- Do not create accounts, call auth/backend services, send email or verification codes, or display a false success state. Parent registration flow remains open in the canonical SRS.
- Reuse existing assets and dependencies. No SRS or other portal changes.
- Automated tests/builds, deployment, publishing, commit, and push are outside this approval.
## Revision 14 authorization — Optimize Parent auth layout for tablets

- Approved plan: features/FEAT-036-ui-current-direction-alignment/plan/PLAN_REV14_TABLET_AUTH_LAYOUT.md
- Plan revision: 14
- Plan SHA-256: 75ABC318C5869E545B3796328C594F9617F7D7DF3D18AED5ABC810DDE24F42DC
- Approval status: APPROVED
- Prepared / approved: 2026-11-10
- Reviewer / approver: Project owner (explicit instruction in this conversation)

### Authorization recorded

The owner requested: “Sau đó tối ưu cho các thiết bị tablet ipad đồ lun cho tôi”. This authorizes responsive presentation changes for the Parent sign-in, password-recovery, and registration screens.

### Approval boundaries

- Add tablet-specific layout, spacing, typography, touch target, and safe-area treatment for the three Parent auth screens.
- Preserve the existing phone presentation and all current route/state behavior.
- Do not add authentication/account behavior, backend calls, assets, dependencies, or SRS changes. Parent registration/recovery requirements and Parent Web target scope remain open.
- Automated tests/builds, deployment, publishing, commit, and push are outside this approval.
## Revision 15 authorization — Parent auth guard on hard refresh

- Approved plan: features/FEAT-036-ui-current-direction-alignment/plan/PLAN_REV15_PARENT_REFRESH_AUTH_GUARD.md
- Plan revision: 15
- Plan SHA-256: B5852BC76683922E1BC578AC06DD9B8FFDFB0003A4D645B69B5B1C0A15058A34
- Approval status: APPROVED by explicit owner request on 2026-11-10.
- Authorized behavior: if Parent has no session on direct load or F5, replace the route with /p11-authentication. Preserve an existing real auth session when the current bridge confirms its token. Local demo preview requires explicit user action and does not persist across reload.
- Boundaries: keep Firebase configuration and backend token/role guards; do not create fake sessions or change API/backend behavior. No tests/builds, deployment, publishing, commit, or push.
## Revision 16 authorization — Optimize Parent UI for iPad

- Approved plan: features/FEAT-036-ui-current-direction-alignment/plan/PLAN_REV16_PARENT_TABLET_LAYOUT.md
- Plan revision: 16
- Plan SHA-256: A48D81C858DB9B5E6AEC754AE466DDD2C6460875D11F73DBB70A6DF939AD5932
- Approval status: APPROVED by explicit owner request on 2026-11-10.
- Authorized scope: improve Parent app shell and selected screens for iPad portrait/landscape; keep phone and auth layouts, route behavior, Firebase configuration, backend/API behavior, and product requirements unchanged.
- Verification boundary: manual local visual review only; no automated tests/builds, deployment, publishing, commit, or push.

## FEAT-070 Plan Rev2 — Parent Web P06-to-P07 quota admission on active preview

- Status: APPROVED for the exact scope in the hash-identified plan.
- Approver: Project owner, direct chat instruction on 2026-11-10, including the follow-up that the bug persists and asks for a deep end-to-end review.
- Approved plan: features/FEAT-070-parent-web-video-admission-demo-fix/plan/PLAN.md.
- Plan SHA-256: F37487038B338BAE850AD33ABC622E4023E637861134B8B1F798EEC4B5FC2BAA.
- Runtime diagnosis: port 5171 serves apps/parent-ui from fe-ui-full-remediation; the initial web-remediation patch was not loaded there. A one-unit physical click on the active preview consumes quota and closes P06 confirmation but leaves the route at P06.
- Scope: return admission result from ParentContext; navigate to P07 only on acceptance; show post-use quota copy; physically re-run the synthetic route on port 5171 and record evidence.
- Exclusions: changes to FEAT-036/067/068/069 or their in-progress files, SRS changes/sign-off, API/backend/auth/billing/provider integration, automated tests/builds, commit/push, deployment, and publishing.
- Approval basis: user's direct request to fix P06, run the complete FE-only SRS demo, and follow-up authorization to investigate the persisting failure in detail.

## FEAT-071 Plan Rev1 — Parent profile one-tap switching

- Status: APPROVED for the exact scope in the hash-identified plan.
- Approver: Project owner, direct instruction on 2026-11-10 after review of the plan: “lên plan xong sửa cho tôi đi”.
- Approved plan: `features/FEAT-071-parent-profile-one-tap-switch/plan/PLAN.md`.
- Plan SHA-256: `08DFAD14941DA13838860069C63A8821776E108418087508DB704AE7F3BDA511`.
- Scope: one-tap active child selection from P13 and P10; keep profile details/editing as a separate action; reflect the selected child in existing Parent UI state; session-only local FE preview.
- Boundaries: no auth/account switching, API/backend, persistence, SRS changes, or payment changes. Preserve existing in-flight FEAT-036/067/068/069 changes, including the auth diff in `ParentScreens.tsx`.
- Verification: manual local-preview review only. Automated tests/builds, commit, push, deployment, and publishing are excluded.

## FEAT-072 Plan Rev1 — Refresh Parent video quota screen

- Status: APPROVED for the exact scope in the hash-identified plan.
- Approver: Project owner, direct instruction on 2026-11-10.
- Approved plan: features/FEAT-072-parent-video-quota-visual-refresh/plan/PLAN.md.
- Plan SHA-256: A45145F858A5DB6DB2000D5BD3649FB8907681E5EEB080DC802C24EF6732067D.
- Authorization recorded: “Dùng skill sửa lại toàn bộ giao diện lượt tạo này sao cho mới mẻ hợp với phong cách trẻ em mà SRS đề ra”.
- Scope: visual and interaction-presentation redesign of Parent P12 quota and top-up screen; retain existing local demo data, simulated purchase behavior, route, and ledger behavior; responsive phone/tablet presentation and manual review on the active port-5171 preview.
- Product authority: FEAT-063 SRS v2.7-draft from the main checkout per its SRS_AUTHORITY.md, SHA-256 BE0D656966FDE91BA7CD5C914C319EF301D137985EF5CC91B94F36FEBCF61FB5; awaiting formal owner sign-off. The target worktree still contains stale v2.5 authority copies and these will not be used or edited.
- Boundaries: no API/auth/persistence/billing/quota policy/price/package/SRS changes; no generated external assets; preserve all other worktree changes. No automated tests/builds, commit, push, deployment, or publication.

## FEAT-073 Plan Rev1 — Child profile gender and matching avatar

- Status: APPROVED for the exact scope in the hash-identified plan.
- Approver: Project owner, direct instruction on 2026-11-10.
- Approved plan: features/FEAT-073-parent-profile-gender-avatar/plan/PLAN.md.
- Plan SHA-256: 76623107BBEBFFC10BFD92EC3A158685816998928CAA1CD1D9C85047D0FFD36B.
- Authorization recorded: “phần tạo hồ sơ thiếu giới tính nữa ví dụ như là giới tính nam thì avatar là đứa bé trai nếu là con gái thì là avatar đứa bé gái á”.
- Scope: add a local FE demo gender choice on child-profile creation and editing, drive the avatar from the saved choice, and update all Parent profile avatar views.
- Product authority: FEAT-063 SRS v2.7-draft from the main checkout per its SRS_AUTHORITY.md, SHA-256 BE0D656966FDE91BA7CD5C914C319EF301D137985EF5CC91B94F36FEBCF61FB5; awaiting formal owner sign-off. The target worktree has stale v2.5 authority copies, which remain unchanged.
- Product question: the canonical SRS defines age range and profile context but does not specify gender. Keep the field local to the requested demo UI; do not add an API/schema/SRS requirement or use it in AI context.
- Boundaries: no API/backend/persistence/analytics/consent/auth changes; preserve existing profile workflows and in-flight worktree changes. No automated tests/builds, commit, push, deployment, or publication.

## FEAT-074 Plan Rev1 — Parent settings grouped into two categories

- Status: APPROVED for the exact scope in the hash-identified plan.
- Approver: Project owner, direct request in this conversation on 2026-11-10.
- Approved plan: features/FEAT-074-parent-settings-two-groups/plan/PLAN.md.
- Plan SHA-256: E2E9A9BA756C205D9EECB5BACE12B4E1A4698E950EF61DE0DD57681694124098.
- Authorization recorded: “Cái này gom hết vào 2 cái là đầu tiên là tài khoản cài đặt và cuối cùng là bảo mật đc k ? phân đều ra á”.
- Scope: replace the three P13 account/security navigation rows with two categories. “Tài khoản & cài đặt” contains existing parent details and preferences; “Bảo mật” contains existing privacy/AI-data information, profile-access information, and password change. Preserve all existing behavior.
- Product authority: FEAT-063 SRS v2.7-draft from the main checkout per its SRS_AUTHORITY.md, SHA-256 BE0D656966FDE91BA7CD5C914C319EF301D137985EF5CC91B94F36FEBCF61FB5; awaiting formal owner sign-off.
- Boundaries: presentation/navigation only; no API, backend, authentication, persistence, SRS, or product-policy changes. No automated tests/builds, commit, push, deployment, or publication.

## FEAT-075 Plan Rev1 — Final Parent FE demo-flow SRS UI/UX review

- Status: APPROVED for the exact scope in the hash-identified plan.
- Approver: Project owner, direct request in this conversation on 2026-11-10.
- Approved plan: features/FEAT-075-parent-srs-flow-final-review/plan/PLAN.md.
- Plan SHA-256: EB66C2DBDBE39112BE6385A2B2DD8EC76D747D8D4441B5DB4B7B6DFA9BB1F504.
- Authorization: “Sau đó check UI/UX theo luồng của SRS lần cuối cho tôi có lỗi thì sửa ko thì trả báo cáo đã check gì chạy luồng như nào cho tôi và đợi yêu cầu tiếp theo”.
- Worktree: F:/Github/Sketch2Life-worktrees/fe-ui-full-remediation, as explicitly directed by the user; do not transfer changes to the main checkout.
- Scope: manually run the complete synthetic Parent FE story-to-video flow; audit SRS-required navigation, confirmations, rewrite/retry/quota/status gates, playback, post-video activities, feedback/history and responsive interaction; fix only reproduced Parent FE defects and record evidence.
- Product authority: FEAT-063 SRS v2.7-draft Rev57, SHA-256 BE0D656966FDE91BA7CD5C914C319EF301D137985EF5CC91B94F36FEBCF61FB5; unsigned.
- Boundaries: no API/backend/provider/auth/persistence/payment/SRS/policy change; preserve open questions and all existing worktree changes. No automated tests/builds, commit, push, deploy or publication.

## FEAT-076 Plan Rev1 — Native React Native Parent demo flow

- Status: APPROVED for the exact scope in the hash-identified plan.
- Approver: Project owner, direct instruction in the active conversation on 2026-11-10: “V thì build 1 bản qua react native bỏ vào đó cho tôi đi”.
- Worktree: F:/Github/Sketch2Life-worktrees/fe-ui-full-remediation, previously specified by the owner.
- Approved plan: features/FEAT-076-parent-react-native-parent-flow/plan/PLAN.md, Rev1.
- Plan SHA-256: AA96EF0084537C37F3E2017DBF8FDE03D3B96E0100F509B1675C12DD07962360.
- Scope: deliver a native React Native synthetic Parent story-to-video demo flow; fix P06 preflight to P07 status/READY navigation; add profile gender/avatar and one-tap selection; align quota/settings screens with the recently reviewed Parent UI; build a local Android debug APK if prerequisites are available.
- Product authority: FEAT-063 SRS v2.7-draft Rev57, SHA-256 BE0D656966FDE91BA7CD5C914C319EF301D137985EF5CC91B94F36FEBCF61FB5; unsigned working baseline.
- Boundaries: no API/backend/auth provider/persistence/payment/device/media/provider integration; no SRS/schema/policy decisions; keep no-preset activity policy open. No release signing, commit, push, deploy, or publication. Preserve unrelated files and do not modify the web app or Fixture lab.

## FEAT-077 Plan Rev1 — Parent account edit entry point

- Status: APPROVED for the exact scope in the hash-identified plan.
- Approver: Project owner, direct instruction in the active conversation on 2026-11-10.
- Worktree: F:/Github/Sketch2Life-worktrees/fe-ui-full-remediation, previously specified by the owner.
- Approved plan: features/FEAT-077-parent-account-edit-entry-point/plan/PLAN.md, Rev1.
- Plan SHA-256: D55D1E729A4DA220C2714843CCE0F6D2A70130CE512FD80E40B517A69ED09546.
- Scope: preserve the two outer settings groups and add an accessible edit action beside the Parent account summary in web and React Native; web opens its existing account form, native edits only local demo snapshot values.
- Product authority: FEAT-063 SRS v2.7-draft Rev57, SHA-256 BE0D656966FDE91BA7CD5C914C319EF301D137985EF5CC91B94F36FEBCF61FB5; unsigned working baseline.
- Boundaries: no API/backend/authentication/persistence/SRS/security-policy changes, generated/external assets, commit, push, deployment, or publication. Preserve unrelated worktree changes.
## FEAT-078 Plan Rev1 — Parent account and security page UX

- Status: APPROVED for the exact scope in the hash-identified plan.
- Approver: Project owner, direct instruction in the active conversation on 2026-11-10 to reorganize the two supplied UX pages using the skill.
- Worktree: F:/Github/Sketch2Life-worktrees/fe-ui-full-remediation.
- Approved plan: features/FEAT-078-parent-settings-pages-ux/plan/PLAN.md, Rev1.
- Plan SHA-256: FC1E54AF4E2CA7BA7605E1EF3EBFD745439D2DB5072E023922FEEAFBE3CCC284.
- Scope: reorganize the Parent web account and security subviews; preserve content, settings actions, privacy wording, form validation, feedback, and navigation.
- Product authority: FEAT-063 SRS v2.7-draft Rev57, SHA-256 BE0D656966FDE91BA7CD5C914C319EF301D137985EF5CC91B94F36FEBCF61FB5, per active AGENTS.md; unsigned working baseline.
- Boundaries: no API/backend/authentication/persistence/SRS/security-policy changes, generated/external assets, commit, push, deployment, or publication. Preserve unrelated worktree changes.

## Owner authorization — one local commit for current worktree (2026-11-11)

- Status: APPROVED by direct project owner instruction in the active conversation: stop emulator work, gather the worktree changes into one commit, use an English message, and commit everything.
- Scope: one local commit covering all current tracked and untracked worktree changes that pass repository security checks, including the Parent UI work and mobile Expo base.
- Commit message: `fix(mobile): rebuild Expo base for emulator compatibility`.
- Boundary: local commit only; no push, merge, rebase, or deployment was requested. Existing feature implementation scopes and product requirements remain unchanged.
