# Plan Rev57 — substantive diagram-input remediation

- **Feature:** FEAT-063 — system architecture rearchitecture.
- **Baseline:** fetched target branch docs/feat063-diagram-readiness-20261107, Rev56 / ae5707ca188d01d9719ed959b62d768ae927912d.
- **Date:** 2026-11-09 (Asia/Saigon).
- **Status:** APPROVED for the documentation scope below; SRS and Data Table Register remain unsigned v2.7-draft.

## Objective

Turn the owner-provided G01–G10 requirements into usable, internally aligned TO-BE specifications and explicit owner decision questions. Verify AS-BUILT statements against the fetched source snapshot. Preserve all established invariants and leave unresolved rules OPEN-OWNER; do not create final diagrams while gates remain open.

## Work and acceptance criteria

1. Review canonical SRS §§1–32, Data Table Register, Catalog Rev56, Crosswalk Rev54, EV-063-61, authority/source registers, and relevant source/schema/migration/import evidence at the baseline SHA. Record source SHA and limits.
2. Correct actor/package contradictions and align Teacher random-selection behavior across UC-05, FR-T-10, FR-PL-20, AC-56, screens, states, and contract inputs. Add case/guard/action/response/state/evidence detail while leaving owner-dependent eligibility, consent, reselection, empty-set, concurrency and audit-snapshot rules open.
3. Specify identity/share boundaries, role-resolution proposal, plan supersession case matrix, and both Parent no-preset decision branches. Keep unapproved permission, history, retention, publication, age, quota and sharing policy open with concrete options/consequences/owner/status.
4. Add a complete decision register for Q-01–Q-13 and the 17 SRS §31.10 questions; preserve the 4-role boundary, child-media deny-by-default, exact version/hash pin, quota scope/order, 8 AI job targets, target mapping counts and TO-BE/AS-BUILT distinction.
5. Add draft physical dictionary/mapping, transition matrix, API/event contracts, screen navigation map, class/package contracts, requirement trace matrix and 13-output diagram readiness catalog. Mark unknown physical facts or unverified source features blocked/proposed. Do not execute DDL/migrations or change product code/data.
6. Update SRS/DTR at applicable sections and companion artifacts; update feature context, decisions, source register, evidence index, status and evidence report.
7. Check terminology, IDs, actor labels, counts, decision links, document links, git diff --check and repository security validator. Report PASS/PARTIAL/BLOCKED accurately. Commit and fast-forward push only the exact scoped documentation paths if checks pass and the target remote is still based on Rev56.

## Scope manifest

approvals/TASK_APPROVAL.md; docs/context/SOURCE_REGISTER.md; docs/context/SRS_AUTHORITY.md; features/FEAT-063-system-architecture-rearchitecture/CONTEXT.md; DECISIONS.md; SOURCE_REGISTER.md; approvals/TASK_APPROVAL.md; artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md; artifacts/DATA_TABLE_REGISTER.md; artifacts/DIAGRAM_INPUT_CATALOG_V27_REV57_20261109.md; artifacts/DECISION_REGISTER_REV57_20261109.md; artifacts/DIAGRAM_TRACE_MATRIX_REV57_20261109.md; artifacts/PHYSICAL_DATA_DICTIONARY_DRAFT_REV57_20261109.md; artifacts/STATE_TRANSITION_MATRIX_REV57_20261109.md; artifacts/API_EVENT_CONTRACTS_DRAFT_REV57_20261109.md; artifacts/SCREEN_NAVIGATION_MAP_DRAFT_REV57_20261109.md; artifacts/CLASS_PACKAGE_CONTRACTS_DRAFT_REV57_20261109.md; artifacts/REMEDIATION_RESULT_REV57_20261109.md; evidence/EV-063-62_REV57_SUBSTANTIVE_DIAGRAM_INPUT_REMEDIATION_20261109.md; evidence/README.md; status/STATUS.md; this plan file. Paths under features/FEAT-063-system-architecture-rearchitecture/ are relative to that feature directory except where a root path is shown.

## Explicit exclusions

No product/source code, API runtime, schema, database, data, migration, provider, secret, permission implementation, cost action, tests/build/deployment, final diagram publication, formal SRS/DTR approval, PR/merge, or force push. This plan does not decide owner policy questions. Documentation may describe proposals only when labeled TO-BE / PROPOSED.

## Approval basis

The project owner directly requested this exact remediation package, then directly requested commit and push. This approval authorizes only the manifest above and a normal fast-forward push to the named branch; it is not SRS/DTR sign-off and does not resolve OPEN-OWNER decisions.

## Acceptance criteria

- **AC1:** Scope is limited to this manifest; no unrelated dirty work is included.
- **AC2:** All ten groups have substantive specifications or exact, owner-addressed blockers, with cross-document terminology and trace IDs aligned.
- **AC3:** All 13 diagram inputs have source, requirement coverage, status and dependency; no final diagram is labeled approved prematurely.
- **AC4:** Decision register maps Q-01–Q-13 and §31.10 questions without fabricated decisions/owners.
- **AC5:** DTR physical target details are distinguished from as-built evidence; unverified DDL/routes/imports remain draft or blocked.
- **AC6:** Static document/security checks pass, evidence states exactly what was and was not checked, and scoped commit/push is fast-forward only.
