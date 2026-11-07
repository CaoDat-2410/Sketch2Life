# FEAT-063 Plan Rev53 — reconcile the v2.6 SRS checklist

- **Plan revision:** 53
- **Date:** 2026-11-07
- **Lifecycle:** APPROVED for this exact documentation scope; owner approval is recorded in the root and FEAT-063 task approval registers.
- **Change type:** Documentation-only correction of the canonical SRS and its Data Table Register companion.
- **Starting point:** branch `docs/feat063-srs-conflict-remediation-20261106`, commit `51d739f1caddcfb5bc8c61354f6c2366bc0fa362`; this work uses a separate remediation worktree.
- **Review source:** owner-provided `Sketch2Life_Checklist_Cuoi_Fix_1_Luot_v2_6.docx`, SHA-256 `5D23504F26C97977B07F40704BA1E020D69F80CDDD57562E9B3E179F69E37486`. The source file stays outside the repository.

## Goal

Compare the checklist’s M/D/Q/R findings with the canonical FEAT-063 v2.6-draft SRS and matching Data Table Register. Apply only statements already supported by current owner decisions, make contradictory or stale wording internally consistent, and leave unresolved product policy and physical-schema details explicitly open. Advance both documents to v2.7-draft only for this reviewed documentation package; do not sign off product requirements.

The checklist and Rev55 review artifacts are analysis inputs. The canonical SRS and existing owner decisions remain the authority. A recommendation in the checklist does not itself approve a requirement, role, state, endpoint, table, column, or migration.

## Exact documentation scope

- Update the canonical SRS and matching Data Table Register to v2.7-draft, unsigned.
- Reconcile R-01 by showing the optional, typed, versioned LessonVersion pin across a lesson occurrence, its derived plan revision, and a Teacher StoryRun. Preserve the exact version/hash fence and never resolve “latest”. Keep field persistence, SQL types, constraints, indexes, and migration behind the approved DDL gate; do not create cross-owner SQL foreign keys.
- Rephrase the video admission summary so the same business request/idempotency key coordinates separate AI Policy, Billing, and Story owner transactions. Preserve reservation, receipt, rejection, uncertain-outcome reconciliation, and accepted-usage rules.
- Align “Organization Admin” wording with the current School Manager product role where current SRS decisions establish that alias. Keep permission assignment, identity persistence, effective scope, revoke/audit mapping, and any role-model details that lack an owner decision open.
- Clarify the known global, approved/versioned Parent activity catalog and the post-video ordering. For a Parent run without a lesson preset, keep the selection/filtering, response cardinality, stored snapshot, revoke/unpublish effects, and empty-result behavior open until the owner approves that contract. Do not require Parent activity selection before video.
- Fix the Data Table Register table-of-contents and section heading so “40 baseline tables” is historical v2.2 wording, while the current logical target remains 92 active + 48 legacy/read-only = 140 projected mappings. Preserve explicitly dated historical counts.
- Regression-check all other M/D/Q/R findings against v2.6. Record each as fixed, clarified, partial, or open in feature-local evidence. In particular preserve the open accepted-run behavior when an approved plan is superseded; profile-share fields/expiry/offboarding and school-wide acceptor; teacher-sample eligibility/consent; quota commercial allocation; public-lesson review; legacy age handling; DDL/index/migration; API/state/screen/class/package detail.
- Update authority pointers, project/feature context, feature source register, approval, status, evidence index and review evidence. Record no new owner decision unless one is actually supplied.

## Out of scope

- Product code/API/runtime/provider/database changes, SQL DDL, schema or migrations, tests, builds, deployments, or diagrams.
- Changes to the separate Rev55 architecture catalog/crosswalk or historical SRS bodies.
- Resolving unanswered product-owner choices, inferring physical schema, or formal SRS sign-off.
- Copying the external DOCX or extracted/rendered source pages into the repository.

## Acceptance criteria

- **AC1 — Authority:** the FEAT-063 SRS and companion Register are both v2.7-draft and unsigned; the SRS remains the only current product requirements source; implementation snapshots remain separate.
- **AC2 — Direct reconciliation:** R-01/R-02/R-05 are fixed logically; R-03 is confirmed already resolved in the canonical v2.6 text; M-04 and M-12 retain the already-decided role/quota semantics without opening new roles or pools; no contradictory cross-owner transaction wording remains.
- **AC3 — Open policy:** R-04 and unresolved M/D/Q items remain explicit open gates, including plan supersession, school-wide invitation acceptance, profile-share expiry/scope, sample selection/consent, quota terms, and physical schema/migration details. The report’s suggestions are not presented as approved.
- **AC4 — Traceability:** feature-local evidence records source filename/hash, visual review limits, dispositions for all M-01–16, D-01–20, Q-01–13 and R-01–05, and citations to changed SRS/Register sections.
- **AC5 — Repository records:** root and FEAT-063 authority/context/source/status/evidence records identify the v2.7-draft pair and this review without rewriting history.
- **AC6 — Scope/checks:** only the 15 package paths listed below change; `git diff --check` and `python tools/validate_repository_security.py` pass. No product test/build/runtime/provider operation is performed.
- **AC7 — Publication:** commit on `docs/feat063-srs-v26-checklist-20261107` and push normally to the same-named `origin` branch. No force-push, PR, merge, or change to `dev`.

## Owner clarifications already recorded

D-146 and the preceding owner decisions remain in force: content administration is a Platform Admin permission; Platform Admin child-media access is deny-by-default until a separate workflow is approved; Teacher video usage consumes only the school organization quota for its occurrence; Parent activity is not selected before video; named Teacher invitation acceptance activates that grant; Parent may optionally pin a typed LessonVersion when a lesson is used. These decisions do not settle the remaining field, expiry, commercial, lifecycle, or physical-schema questions.

## Exact package manifest (15 paths)

1. `AGENTS.md`
2. `approvals/TASK_APPROVAL.md`
3. `docs/context/PROJECT_CONTEXT.md`
4. `docs/context/SOURCE_REGISTER.md`
5. `docs/context/SRS_AUTHORITY.md`
6. `features/FEAT-063-system-architecture-rearchitecture/CONTEXT.md`
7. `features/FEAT-063-system-architecture-rearchitecture/DECISIONS.md`
8. `features/FEAT-063-system-architecture-rearchitecture/SOURCE_REGISTER.md`
9. `features/FEAT-063-system-architecture-rearchitecture/approvals/TASK_APPROVAL.md`
10. `features/FEAT-063-system-architecture-rearchitecture/artifacts/DATA_TABLE_REGISTER.md`
11. `features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md`
12. `features/FEAT-063-system-architecture-rearchitecture/evidence/README.md`
13. `features/FEAT-063-system-architecture-rearchitecture/evidence/EV-063-58_SRS_V26_CHECKLIST_REMEDIATION_20261107.md`
14. `features/FEAT-063-system-architecture-rearchitecture/plan/PLAN_REV53_SRS_V26_CHECKLIST_RECONCILIATION_20261107.md`
15. `features/FEAT-063-system-architecture-rearchitecture/status/STATUS.md`

## Execution sequence

1. Record the user’s direct request as approval for this exact documentation scope; retain DRAFT until the approval entries exist.
2. Map each checklist statement to the canonical SRS/Register and previously recorded owner decisions. Treat the checklist as review input, not requirement authority.
3. Apply only the scoped SRS, Register, authority and tracking changes. Preserve unresolved choices as OPEN.
4. Review the complete path-scoped diff, verify the M/D/Q/R disposition matrix, and run `git diff --check`.
5. Run the repository security validator immediately before commit and again before push. Commit only the 15 manifest paths with subject `docs(FEAT-063): reconcile v2.6 SRS checklist`, then make a normal push to the branch in AC7.
