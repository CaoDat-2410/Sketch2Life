# FEAT-063 Plan Rev56 — ten-group diagram readiness alignment

- Status: APPROVED for the documentation-only scope and exact-branch publication below, based on the owner's direct requests on 2026-11-08.
- Revision: 2
- Date: 2026-11-08

## Goal

Align the ten remaining diagram-readiness groups across the canonical FEAT-063 SRS, Data Table Register, and a successor Diagram Input Catalog. Correct the Teacher sample-child selection wording so the system selects randomly and the responsible Teacher confirms. Keep every unresolved owner policy and technical evidence gate OPEN.

## Baseline and authority

- Branch/worktree: docs/feat063-diagram-readiness-20261107, clean at 7d35ee3cd75ae7b34a71433daa2231781c9bc60c before this task.
- Canonical working SRS and matching Register: v2.7-draft at baseline 98cc34a39af279560b5f8d39f18939a376535834; both remain unsigned.
- Rev54 Diagram Readiness Crosswalk and Input Catalog are the source checklist records; Rev55 assessment is supporting evidence.
- Use SRS §§1–31 for target requirements and §32 only as dated environment-specific evidence.

## Scope

1. Reconcile the ten groups in the supplied checklist with existing SRS/Register/crosswalk IDs.
2. Align UC-05, FR-T-10, FR-PL-20, and AC-56: system selection is random from the policy-defined eligible set; the responsible Teacher confirms the selection/context. Keep eligibility, consent, reselection, no-eligible behavior details, and selection evidence open under Q-01.
3. Add concise trace matrices in SRS §31.10 and Data Table Register §14.3; publish a v2.7 Rev56 successor to the Rev54 Diagram Input Catalog.
4. Update FEAT-063 context, decision-status note, source registers, evidence index/report, status, and task approval records.
5. Preserve all resolved sub-decisions as settled and all undecided policies/technical facts as OPEN. Do not add product rules, tables, keys, states, permissions, DDL, or final diagrams.
6. Commit and push the exact 13-path manifest to `origin/docs/feat063-diagram-readiness-20261107`, fast-forward only, after repository security validation.

## Out of scope

- Product implementation, APIs, tests/builds, database inspection, DDL, migrations, provider/runtime checks, and as-built claims.
- Closing owner decisions, SRS/Register sign-off, or finalization of any diagram.
- PR, merge, dev update, force-push, or changes outside the exact manifest.
- Any path outside the exact manifest below.

## Exact path manifest

1. approvals/TASK_APPROVAL.md
2. docs/context/SOURCE_REGISTER.md
3. features/FEAT-063-system-architecture-rearchitecture/CONTEXT.md
4. features/FEAT-063-system-architecture-rearchitecture/DECISIONS.md
5. features/FEAT-063-system-architecture-rearchitecture/SOURCE_REGISTER.md
6. features/FEAT-063-system-architecture-rearchitecture/approvals/TASK_APPROVAL.md
7. features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md
8. features/FEAT-063-system-architecture-rearchitecture/artifacts/DATA_TABLE_REGISTER.md
9. features/FEAT-063-system-architecture-rearchitecture/artifacts/DIAGRAM_INPUT_CATALOG_V27_REV56_20261108.md
10. features/FEAT-063-system-architecture-rearchitecture/evidence/EV-063-61_TEN_GROUP_DIAGRAM_READINESS_ALIGNMENT_20261108.md
11. features/FEAT-063-system-architecture-rearchitecture/evidence/README.md
12. features/FEAT-063-system-architecture-rearchitecture/plan/PLAN_REV56_TEN_GROUP_DIAGRAM_READINESS_ALIGNMENT_20261108.md
13. features/FEAT-063-system-architecture-rearchitecture/status/STATUS.md

## Acceptance criteria

- AC1. The sample-child flow consistently says the system selects randomly and Teacher confirms; Q-01 retains eligibility, consent, reselection, no-eligible details, and evidence as OPEN.
- AC2. All ten groups map to existing requirement/decision/readiness IDs in SRS §31.10, Register §14.3, and the Rev56 catalog.
- AC3. Settled scope remains intact, including Content Admin as a Platform Admin permission, child-media default deny, school-only Teacher quota, version/hash pinning, and no-name joins.
- AC4. The unresolved policy and evidence gates are labeled OPEN with only source-recorded owner/status information; no new policy, schema, key, state, permission, or endpoint is invented.
- AC5. Physical ERD remains gated on approved dictionary/DDL/constraints and source-to-target migration mapping; as-built diagrams require current code/schema evidence.
- AC6. SRS and Data Table Register remain v2.7-draft and unsigned; no final diagram or implementation readiness is claimed.
- AC7. FEAT-063 tracking and evidence point to the reviewed source and limits; git diff --check passes for the resulting working-tree diff.
- AC8. Commit and push only the exact 13-path manifest to the current feature branch after repository security validation; do not PR, merge, update dev, or force-push.

## Verification

- Manually compare the ten groups against SRS v2.7, Data Table Register v2.7, Rev54, and Rev55 records.
- Run git diff --check and `python tools/validate_repository_security.py` before commit and again before push.
- Do not run product tests/builds; commit only after the exact path manifest is verified and push only if the remote branch remains a fast-forward target.

## Publication authorization — revision 2

- Owner instruction received 2026-11-08: “commit and push”.
- Target: current branch `docs/feat063-diagram-readiness-20261107` to its configured upstream `origin/docs/feat063-diagram-readiness-20261107`.
- Publication is limited to the exact 13 paths above. No PR, merge, dev update, or force-push is authorized.
- Commit message: `docs(FEAT-063): align ten diagram readiness gates`.
