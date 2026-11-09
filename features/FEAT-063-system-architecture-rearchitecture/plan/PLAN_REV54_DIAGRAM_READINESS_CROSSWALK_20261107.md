# FEAT-063 Plan Rev54 — v2.6 checklist audit and diagram readiness

- Status: APPROVED
- Plan revision: 1
- Implementation status: NOT_STARTED
- Date: 2026-11-07

## Goal

Audit every M-01–M-16, D-01–D-20, Q-01–Q-13 and R-01–R-05 item in the owner-supplied v2.6 diagram-fix checklist against its cited Rev55 sources and the current canonical v2.7-draft SRS/Data Table Register. Correct stale or overstated statuses, create a traceable diagram-input catalog, and leave owner and technical gates explicit.

## Baseline and source authority

- Current working baseline at task start: commit 98cc34a39af279560b5f8d39f18939a376535834, branch docs/feat063-srs-v26-checklist-20261107.
- Current product authority: FEAT-063 SRS v2.7-draft and its matching Data Table Register v2.7-draft at that commit; both remain unsigned.
- Historical checklist sources to inspect together: v2.6 SRS, v2.6 Data Table Register, ARCHITECTURE_DETAIL_CATALOG_REV55_20261106.md and REPORT_REMEDIATION_CROSSWALK_REV55_20261106.md at source branch docs/feat063-v25-report-remediation-20261106, commit a711e78cf6586dd5b639d811e610a741efd7433d.
- Rev55 source observation references commit 1431ef81972b71303fd4a7909748fd3005769a3c. It is dated static-source evidence and will not be promoted to current runtime/as-built verification.

## Scope

1. Compare the supplied checklist with the four same-commit v2.6/Rev55 sources and current v2.7 SRS/Register; preserve original IDs and distinguish fixed logic, partial/open owner/technical decisions, and as-built evidence.
2. Create a v2.7 diagram-input catalog and a full M/D/Q/R readiness crosswalk. Reconcile status conflicts using current SRS/Register text and name the evidence/approval needed for each remaining gate.
3. Record diagram inputs for Context, Use Case, Workflow, Activity, Conceptual/Logical/Physical ERD, State, Sequence, Screen Flow, Class, System Architecture and Package; label each TO-BE, proposed, blocked, or evidence-dependent.
4. Carry forward only owner clarifications already recorded in the v2.7 SRS/Decision Register: Content Admin is a Platform Admin permission; Platform Admin child-media access defaults to deny; Teacher video uses the occurrence’s school quota only; named Teacher acceptance activates an invitation grant and Parent may revoke; Parent does not select an outdoor activity before video.
5. Keep unresolved parts OPEN-OWNER or OPEN-TECHNICAL. In particular, do not choose any Q-01–Q-13 answer, create a physical schema, infer identity joins, or claim runtime/source verification.
6. Update FEAT-063 context, decision note, source register, evidence index, status and approval records, plus the root source register. Add a local evidence record.
7. Commit the exact reviewed manifest to the named documentation branch and push it normally; verify the remote commit.

## Out of scope

- No production code, API, database, DDL, migration, provider, deployment, credentials, or child-data change.
- No product tests, build, runtime probe, provider call, or new as-built inspection.
- No final diagrams, final physical ERD, OpenAPI contract, UI IA, or package dependency certification. The canonical SRS/Register are unsigned and the task source marks final diagrams as gated. This plan prepares draft inputs only.
- No new owner decision, formal SRS sign-off, PR, merge, push to dev, force-push, or edit outside the manifest.

## Exact path manifest

1. docs/context/SOURCE_REGISTER.md
2. approvals/TASK_APPROVAL.md
3. features/FEAT-063-system-architecture-rearchitecture/CONTEXT.md
4. features/FEAT-063-system-architecture-rearchitecture/DECISIONS.md
5. features/FEAT-063-system-architecture-rearchitecture/SOURCE_REGISTER.md
6. features/FEAT-063-system-architecture-rearchitecture/approvals/TASK_APPROVAL.md
7. features/FEAT-063-system-architecture-rearchitecture/status/STATUS.md
8. features/FEAT-063-system-architecture-rearchitecture/plan/PLAN_REV54_DIAGRAM_READINESS_CROSSWALK_20261107.md
9. features/FEAT-063-system-architecture-rearchitecture/artifacts/DIAGRAM_INPUT_CATALOG_V27_REV54_20261107.md
10. features/FEAT-063-system-architecture-rearchitecture/artifacts/DIAGRAM_READINESS_CROSSWALK_REV54_20261107.md
11. features/FEAT-063-system-architecture-rearchitecture/evidence/EV-063-59_DIAGRAM_CHECKLIST_REVIEW_20261107.md
12. features/FEAT-063-system-architecture-rearchitecture/evidence/README.md

The canonical SRS and Data Table Register are read-only in this task because the v2.7 text already contains the supported R-01–R-05 reconciliation and explicitly records the unresolved questions. If the cross-check identifies a material unsupported requirement, record it as a blocker for a separately scoped SRS amendment rather than changing product intent under this readiness audit.

## Acceptance criteria

- AC1. All 54 original M/D/Q/R codes appear exactly once in the new crosswalk, retain their meaning, and have a current disposition with the source section, affected diagram, evidence and next gate.
- AC2. The crosswalk explicitly reconciles checklist progress counts against the current baseline, identifies every status reclassification, and never equates FIXED/COVERED-LOGICAL with APPROVED or AS-BUILT VERIFIED.
- AC3. The catalog provides diagram-ready TO-BE input boundaries and identifies each blocker. Parent activity source, exact LessonVersion pin, quota ownership/admission, invitations, role/media boundaries and plan supersession are represented without making open choices.
- AC4. Q-01–Q-13 remain OPEN-OWNER as complete decision items. Previously answered subparts are attributed and scoped; the remaining question is visible.
- AC5. No requirements, source code, schema, migration, test, runtime, provider or external-system state is changed; no final diagram or as-built verification is claimed.
- AC6. FEAT-063 tracking records point to the new evidence and catalog, while the SRS remains v2.7-draft and unsigned.
- AC7. Exact manifest review and git diff --check pass; repository security validation passes before commit and before push; a fresh remote lookup confirms the pushed commit SHA.
- AC8. The branch contains only the approved manifest, has no unrelated changes, and is clean after publication.

## Steps

1. Read the authority record, current v2.7 SRS/Register, four same-commit v2.6/Rev55 sources, existing Rev53 plan and EV-063-58.
2. Create draft artifacts and run a complete ID/status/section/diagram/evidence cross-check.
3. Record the project owner's direct instruction to check/fix all listed points and commit/push as approval for this bounded documentation scope; leave the product SRS unsigned.
4. Complete the catalog, crosswalk, evidence and tracking records; review links, counts, status labels and manifest.
5. Run git diff --check and the required repository security validator; inspect the full diff and exact path list.
6. Commit on docs/feat063-diagram-readiness-20261107 and perform a normal push; verify origin points to the resulting commit and the worktree is clean.

## Risks and mitigations

- Historical Rev55 status labels may conflict with the v2.7 open registers. Resolve against current source and describe the discrepancy instead of silently preserving a stale classification.
- A detailed logical catalog could be mistaken for final design. Label every section DRAFT/TO-BE and list unresolved gates.
- Owner answers cover only portions of some Q items. Keep the whole Q OPEN-OWNER while naming settled subparts and remaining decisions.
- Static source observations can be mistaken for as-built proof. Attribute them to their source commit and state that no fresh verification is performed.

## Verification plan

- Manual trace: every checklist ID M-01–M-16, D-01–D-20, Q-01–Q-13, R-01–R-05 maps to current source, disposition and diagram/gate.
- Manual consistency check across catalog, crosswalk, evidence, context, decisions and source registers.
- Run git diff --check.
- Run python tools/validate_repository_security.py before commit and again before push.
- Do not run product tests/builds or source/runtime/database/provider checks; they are outside this documentation task.

## Evidence plan

- Record source branch/commit, working baseline SHA, exact paths, current status classifications, manual review steps and limitations in EV-063-59 inside this feature's evidence directory.
- Link the artifacts from the evidence README, FEAT-063 status/context/source register, root source register and both approval registers.

Both root and feature approval registers record approval for this exact plan revision and the authorization hash stated there. This approval covers documentation readiness and publication only; it does not approve product requirements or final diagrams.
