# EV-063-57 — Reconcile v2.5 SRS and Data Table Register review findings

- Date: 2026-11-06
- Work item: Plan Rev52, documentation reconciliation and owner-authorized branch publication; approvals are recorded in root and FEAT-063 TASK_APPROVAL registers.
- Review source: Owner-provided local report `Bao_cao_mau_thuan_thieu_sot_Sketch2Life_v2_5.docx`
- Source SHA-256: 23D1F4129E2FAA0D87E9F82B36D9459065367658E37B5F905596F565677DE2A9; 45,112 bytes.
- The report is review evidence, not an approved requirement source. Canonical authority remains FEAT-063 SRS v2.6-draft; it remains unsigned.
- Review method: extracted paragraphs from the DOCX OOXML package and cross-checked them against the v2.5 SRS/Register. Word visual preview was interrupted by a physical Escape input; this evidence makes no visual-layout claim. The external DOCX and extracts are not copied into the repository.

## Owner clarifications

1. “Admin nội dung” is a permission of Platform Admin, not a separate product role.
2. Platform Admin child-media access is deny-by-default until a separately approved workflow exists. All requests remain denied until then.
3. Teacher video generation consumes only the school organization quota of the occurrence. No Teacher-account pool or fallback exists; Parent retains a Parent-account quota.

## M findings

| ID | Disposition | Reconciliation |
|---|---|---|
| M01 | Fixed | Parent may edit only an authorized existing draft/personal copy; Parent cannot initiate lesson/activity/plan suggestion generation. Platform Admin and Teacher remain eligible initiators. Updated SRS §§31.2, 31.4, FR-PL-03, AC-59 and role-specific flow. Parent line-sketch guide remains a separate feature. |
| M02 | Clarified | Four product roles remain Platform Admin, School Manager, Teacher and Parent. Content Admin is a Platform Admin permission; System Operator is technical-only. Role/permission storage and effective-policy resolution remain open under D04. |
| M03 | Clarified; workflow open | Platform Admin access to child media is explicitly denied by default until a separate owner-approved workflow. Approval actor, purpose/scope, expiry, audit detail and break-glass remain open. |
| M04 | Fixed; personal-copy details open | Parent StoryRun can pin an optional typed LessonVersion ref/version when a lesson is used; Teacher still pins occurrence/approved plan/activity. Data Table Register §5.6 now matches SRS §31.2. Personal-copy owner, fields and retention remain open. |
| M05 | Fixed | Parent does not submit or select an activity before video. Parent activity list appears after playable video; Teacher still pins one approved activity before sample-video generation. Updated UC-02, §6.1.1, API/acceptance wording and Register §5.6. |
| M06 | Fixed; implementation mapping open | SRS §9.9 and §11.1 identify all eight targets: STORY_RUN, VIDEO_GENERATION, VIDEO_GENERATION_SCENE, LESSON_SOURCE_DOCUMENT, LESSON_LIBRARY_VERSION, LESSON_VERSION_VISUAL_ASSET, LESSON_SKETCH_DECK_REVISION, PARENT_SKETCH_GUIDE. Exact API/DDL mapping and migration remain open implementation details. |
| M07 | Fixed; school-wide acceptor open | Parent consent and invitation put a named Teacher grant in INVITED; the named Teacher accepts, then the grant becomes ACTIVE; Parent may revoke. The actor who accepts an invitation sent to an entire school/class remains open. |
| M08 | Fixed | SCRIPT_REVIEW enters VIDEO_ADMISSION_PENDING; only accepted compute-budget and quota receipts allow VIDEO_QUEUED. Rejection returns to SCRIPT_REVIEW; uncertain receipts remain pending until reconciliation. |
| M09 | Clarified | Teacher video uses only the school organization quota resolved through the occurrence; no Teacher-account pool or cross-scope fallback. Parent account quota remains separate. Included units, prices and school/Parent purchase allocation remain open. |
| M10 | Additional SRS/Register mismatch found during this review; fixed | Current target is 92 active + 48 legacy = 140 projected mappings. 89 active + 48 legacy = 137 is explicitly historical v2.3 baseline. Updated SRS §§1.1–1.2, AC-09/42, §12.2, NFR-16 and companion references; neither count is production DDL/inventory. |

## D findings retained as open

| ID | Open design detail |
|---|---|
| D01 | SQL data types, nullability/defaults, enums/checks, keys, constraints and partial indexes for the physical model. |
| D02 | Final columns and backward-compatible migration/backfill for 38 retained/refactored mappings. |
| D03 | Exact Parent–Teacher–Lesson Delivery recipient/share-grant linkage, eligibility, version and revoke validation. |
| D04 | Canonical storage and lifecycle for roles/permissions, tenant scope and policy resolution; the three role/media/quota semantics above are clarified. |
| D05 | Full aggregate transition matrices for guards, actions, failures, timeouts, concurrency and idempotency; only the video-admission contradiction was reconciled here. |
| D06 | Safety-block and technical-failure retry/recovery behavior, quota, timeout and stale callback handling. |
| D07 | Effects of a newer approved plan revision on occurrence, Deck, active StoryRun, jobs and pinned hashes. |
| D08 | Random sample eligibility, consent, policy version, selection snapshot, Parent notification and re-selection/exclusion. |
| D09 | Storage of publication/moderation decisions, revoke, reason/evidence audit and any future admin media-view workflow. Current child-media access is deny-by-default. |
| D10 | Complete main/alternate/error use-case flows across lessons, sharing, feedback and quota; only directly implicated flows were corrected. |
| D11 | Role-to-screen/route/action/state/navigation inventory for Parent Android and web portals. |
| D12 | Repository-mapped class/interface behavior, ports/adapters and package dependencies. |

## Q decisions

| ID | Status | Remaining question |
|---|---|---|
| Q01 | Scope clarified; commercial details open | Teacher uses school quota only; how many included units, prices and purchase/allocation rules apply to Parent and school scopes? |
| Q02 | Open | Exact shared fields, support-needs/observations access, expiry, revoke and retention. |
| Q03 | Default deny clarified; workflow open | Who approves a future request, purpose/scope, expiry, audit detail and break-glass? |
| Q04 | Open | Random sample eligibility, consent, Parent notification and re-selection/exclusion. |
| Q05 | Open | Approval and review record for Platform Admin-authored public lessons and generated visuals/slides. |
| Q06 | Partial | Parent personal-copy ownership/editable fields and script-following default/override remain open. Q159 AI suggestion role boundaries are resolved. |
| Q07 | Open | Parent history period (30/60 days) and age-band boundaries within 36–120 months. |
| Q08 | Open | Migration for legacy 121–155 month profiles and the source question behind Q192/answer 46. |

## Review boundary

- No code, API, DDL, migration, database, provider, runtime, test or build operation was performed for this remediation.
- Final documentation diff was reviewed; `git diff --check` passed with no whitespace errors.
- The SRS and companion Register are v2.6-draft and unsigned; diagrams requiring the still-open details remain gated by the owner-review sequence.
- Review plan SHA-256: 9B6100D907B27302A90F194ADB20B0D67AE2811987F9A5C82DAC23B03B432D55.
- Repository security validator passed before commit and push (`publishable_files_scanned=6565`; no absolute machine paths). No force push, `dev` update, PR, or merge was performed.
- Worktree/branch: isolated worktree / branch `docs/feat063-srs-conflict-remediation-20261106`. Publication is complete: package commit `ca3c5dda695dc8d325442921ace684364d0215b1` was pushed to `origin/docs/feat063-srs-conflict-remediation-20261106`; fresh `git ls-remote` confirmed the remote SHA matches.
