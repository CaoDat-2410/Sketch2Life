# FEAT-063 Plan Rev52 — reconcile the v2.5 SRS review findings

- **Plan revision:** 52
- **Date:** 2026-11-06
- **Lifecycle:** APPROVED for the exact documentation reconciliation and branch publication scope. The original documentation approval and the later publication authorization are recorded separately in the root and FEAT-063 approval registers.
- **Change type:** Documentation reconciliation plus publication of the reviewed documentation package on the isolated remediation branch.
- **Starting point:** `docs/feat063-rev45-srs-code-alignment-20261106` at `fae180dcf3ea2771b41546aa6925b94636821df1`; work took place in a separate isolated remediation worktree.
- **Review source:** Owner-provided local report `Bao_cao_mau_thuan_thieu_sot_Sketch2Life_v2_5.docx`, SHA-256 `23D1F4129E2FAA0D87E9F82B36D9459065367658E37B5F905596F565677DE2A9`.

## Goal

Review the report against the FEAT-063 v2.5-draft canonical SRS and its matching Data Table Register. Correct only contradictions that are resolved by existing approved/current SRS statements. Preserve product-owner decisions and physical-schema details that remain open; the review report itself is analysis input and does not approve requirements. If the owner answers the outstanding questions in this conversation, incorporate only answers that fit this scope and record them as owner decisions.

## Exact documentation scope

- Update the canonical SRS to v2.6-draft and the matching Data Table Register to the same draft revision. Reconcile role terminology and permission boundaries, Q159/Parent AI lesson suggestion, optional Parent LessonVersion pin, Parent activity timing, the complete eight-value AI Job target set, profile-share invitation transitions, and video admission state ordering.
- Reconcile the additional count mismatch found during the review: the SRS still presents the historical v2.3 89/137 table baseline as current, while its current companion and the review report identify the Rev31 92/140 crosswalk as the current logical target. Keep the historical baseline clearly dated and separate from the current target count.
- Preserve unresolved owner decisions, including content-administration role assignment, Platform Admin child-media access policy, profile-share field/approval/expiry rules, cross-scope Teacher quota precedence, and the platform-admin public-lesson approval record.
- Record all M01–M09, D01–D12, and Q01–Q08 review dispositions in feature-local evidence; update only those open-question lists and data-model statements needed to keep the canonical SRS and companion aligned.
- Update the canonical authority pointers and FEAT-063 context, decisions, source register, approval, status, and evidence index.
- Do not copy the external DOCX or any rendered/extracted report pages into the repository; record its path, hash, and review findings in FEAT-063 evidence.

## Out of scope

- Application source/API behavior, diagrams, runtime, database, physical DDL, schema or migrations, providers/Modal, secrets, deployment, or production configuration.
- Resolving any unanswered product-owner question or importing requirements from older SRS/feature-local records.
- Product tests, builds, provider calls, database access/migration, or new child data/assets.
- SRS sign-off, PR creation, merge, force-push/history rewrite, changes to `dev`, or unrelated worktree changes.
- Any unrelated staged, unstaged, or untracked work outside the approved package.

## Acceptance criteria

- **AC1 — Authority:** v2.6-draft is the single current FEAT-063 working SRS; it remains unsigned. `§32` remains source/as-built evidence, not a substitute for product requirements.
- **AC2 — Requirements reconciliation:** M01, M04, M05, M06, M07, M08, and the additional SRS/Register count mismatch agree across the SRS and Data Table Register, while M02, M03, and M09 are made internally consistent without silently deciding unresolved policy details.
- **AC3 — Open issues:** all report D/Q items that cannot be answered from the current canonical SRS remain explicit, linked to their affected diagrams/schema/workflows, and are not represented as approved decisions.
- **AC4 — Traceability:** FEAT-063 evidence maps every M/D/Q item to `fixed`, `clarified`, or `open`, cites the canonical sections changed, and records report provenance/hash and visual-review limitation.
- **AC5 — Repository records:** root and FEAT-063 authority/context/source/decision/status/approval/evidence records identify the v2.6-draft companion pair and this review without modifying historical SRS bodies.
- **AC6 — Scope and review:** only the 15 package paths listed in the Publication addendum are changed; `git diff --check` and the repository security validator pass. No test/build/runtime operation is performed.
- **AC7 — Publication boundary:** commit the reviewed package on `docs/feat063-srs-conflict-remediation-20261106` and push normally to the same-named `origin` branch. Do not force-push, update `dev`, open a PR, or merge.

## Owner clarifications received

On 2026-11-06, the owner answered the three open questions raised during review:

- “Admin nội dung” is a permission of Platform Admin, not a separate product role.
- Platform Admin child-media access is deny-by-default pending an approved access workflow.
- Teacher video usage draws only from the school organization quota; no separate Teacher-account video pool.

These answers are within AC2 and are recorded in the FEAT-063 decision log and Rev52 evidence. They do not resolve package amounts, exact profile-share fields/expiry, or any other open report item.

## Execution sequence

1. Record the user's direct task request as approval of this exact documentation-only plan; retain the draft status until the approval entry exists.
2. Compare each report finding with FEAT-063 v2.5 and the companion Register; use the report as review evidence, not as requirement authority.
3. Apply the approved document-only changes and update pointers, decisions, evidence, and status.
4. Review the full diff and source/target wording; run `git diff --check`. Do not run product tests or builds.
5. Leave owner-dependent questions open if no answer is received; report the remaining choices to the owner. Run the mandatory repository security validator and `git diff --check`, then commit and push only as specified in the Publication addendum.


## Publication addendum — owner instruction, 2026-11-06

The owner later instructed “commit and push.” This authorizes publishing the completed documentation package in this isolated remediation worktree, superseding only AC7’s previous local-only boundary. It does not approve SRS content sign-off or any product implementation.

- Branch and destination: `docs/feat063-srs-conflict-remediation-20261106` to `origin/docs/feat063-srs-conflict-remediation-20261106`, with a regular non-force push.
- Commit subject: `docs(FEAT-063): reconcile v2.5 SRS review findings`.
- Required checks before commit and before push: `python tools/validate_repository_security.py`; also require `git diff --check` to pass.
- Exact package manifest (15 paths):
  - `AGENTS.md`
  - `approvals/TASK_APPROVAL.md`
  - `docs/context/PROJECT_CONTEXT.md`
  - `docs/context/SOURCE_REGISTER.md`
  - `docs/context/SRS_AUTHORITY.md`
  - `features/FEAT-063-system-architecture-rearchitecture/CONTEXT.md`
  - `features/FEAT-063-system-architecture-rearchitecture/DECISIONS.md`
  - `features/FEAT-063-system-architecture-rearchitecture/SOURCE_REGISTER.md`
  - `features/FEAT-063-system-architecture-rearchitecture/approvals/TASK_APPROVAL.md`
  - `features/FEAT-063-system-architecture-rearchitecture/artifacts/DATA_TABLE_REGISTER.md`
  - `features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md`
  - `features/FEAT-063-system-architecture-rearchitecture/evidence/README.md`
  - `features/FEAT-063-system-architecture-rearchitecture/evidence/EV-063-57_SRS_V25_CONTRADICTION_REVIEW_20261106.md`
  - `features/FEAT-063-system-architecture-rearchitecture/plan/PLAN_REV52_SRS_CONTRADICTION_RECONCILIATION_20261106.md`
  - `features/FEAT-063-system-architecture-rearchitecture/status/STATUS.md`
- Do not include any other path, create a PR, or update `dev`.
