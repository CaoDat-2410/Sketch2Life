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
