# Plan Rev59 — SRS alignment to the supplied review note

- **Feature:** FEAT-063 system architecture rearchitecture
- **Date:** 2026-11-09
**Status:** Historical; superseded as current SRS authority by Rev60. (Asia/Saigon)
- **Change type:** SRS-only consistency correction and owner-decision traceability
- **Approval basis:** The project owner directly requested: “fix lại srs dựa trên cái này”. This authorizes the documentation scope below, not product implementation or publication.

## Baseline and authority

- **Canonical working SRS:** `artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md`, v2.5-draft, unsigned; input SHA-256 `9CB2857F12C28779D65A9CE58DB107270F9794932A722CA8822DA7F6C88E8601`.
- **Current companion data register:** `artifacts/DATA_TABLE_REGISTER.md`, v2.5-draft, unsigned; read-only reference SHA-256 `22EF41D77907531754A67C8772A21885F18EB48E4372F87C8E17C4345F880A34`.
- **Owner-supplied review input:** `repository root text.txt`, SHA-256 `1135F27038AFAC5DA51C69572C080EA29702068AA98CF720C49666CFE3FD08EA`.
- The review note and its linked Rev57/v2.7 branch are comparison inputs. The local `docs/context/SRS_AUTHORITY.md` and current project rules keep FEAT-063 v2.5-draft as the canonical working SRS; this plan does not switch branches, fetch, or promote Rev57 as authority.
- Working checkout observed read-only at branch `backup/dev-before-dedup-20261106-575139a5`, HEAD `575139a5bc1b64be2c5a611b295e5ce2bc9aeb29`; unrelated dirty worktree changes must be preserved.

## Scope

1. Correct SRS §1.1 and §§12.1–12.2 to distinguish: the pre-Rev31 86 source mappings, the Rev31 source-derived crosswalk (89 current source mappings), the historical v2.3 design baseline (89 active / 137 projected physical), the current target (38 retained/refactored + 54 new = 92 active, plus 48 legacy = 140 projected physical), and the dated local DB snapshot (41 application tables). Do not call any target count a live database or production count.
2. Reconcile NFR-16 and acceptance criteria AC-09, AC-32 and AC-42 with the current target crosswalk; remove stale `40/78/126` wording from AC-32 and fix stale §31.10 cross-references for Q183/history and Q192/answer 46.
3. Reconcile existing statements that contradict the already-recorded owner clarifications in §31.13: Teacher video usage debits the school organization quota, Parent has a separate account quota, and no Teacher-account quota pool exists; Platform Admin/Content Admin child-media access is denied by default, with any exception requiring a separate future decision. Align the affected scope, business rules, role/quota matrices, FR-PL-24, NFR-36, acceptance criteria AC-61/64 and Q193 trace. Do not introduce a new quota or media-access policy.
4. Expand SRS §31.10 into 17 explicitly numbered owner questions with settled boundaries, the exact unanswered choice, affected requirements/data owners, and `OPEN-OWNER` status. Preserve the decisions already settled in the canonical SRS; do not invent defaults or close any question.
5. Add a Rev59 document-control row and update only the SRS revision date/description as needed. Keep version `2.5-draft`, unsigned status, and all content outside the listed SRS sections or identified contradiction fixes unchanged.
6. Update only the required FEAT-063 plan, approval, evidence, context, source-register, decision-log, and status records to document this review. The only product artifact changed is the canonical SRS.

## Non-goals and data impact

- The only product artifact changed is the canonical SRS. Update the feature-local governance records listed in scope; do not change product/business decisions or modify the Data Table Register, diagram inputs, generated diagrams, code, APIs, migrations, database, secrets, or deployment.
- No product rule or unresolved policy is newly decided; the scope only makes existing recorded Owner clarifications consistent across the SRS. No table, field, FK, API, state, quota value, retention policy, or implementation status is changed. **NO DATA CHANGE:** count reconciliation, cross-reference correction, consistency wording, and open-question tracking do not change persistence design.
- Do not run DB/runtime/product tests or claim physical schema, diagram, API, screen, class/package, or implementation readiness. Do not commit, push, switch branches, or publish.

## Acceptance criteria

- **AC01 — Authority:** The edited file remains the canonical FEAT-063 v2.5-draft and remains unsigned; Rev57 is not copied wholesale or treated as product authority.
- **AC02 — Count consistency:** Historical v2.3, Rev31 source-derived crosswalk, current target crosswalk, and Rev43 local snapshot are separately labeled with the values and limits above.
- **AC03 — SRS consistency:** Current-target counts in §§1.1, 12.1–12.2, NFR-16, AC-09, AC-32 and AC-42 agree with the companion register; explicitly historical values remain clearly historical, and §31.10 references for Q183/Q192 identify the matching questions.
- **AC04 — Owner decisions:** §31.10 lists 17 actionable questions and impacts; all unresolved questions remain open, and the settled scope of the current SRS is preserved.
- **AC05 — Minimal scope:** Only the planned SRS sections, identified contradiction fixes and document-control row change in the product artifact. No companion data, diagram, code, DB or deployment artifact changes; governance updates remain feature-local.
- **AC07 — Settled boundaries:** All current SRS passages consistently state that Teacher usage debits school quota, Parent usage debits Parent quota, no Teacher-account pool exists, and child-media access by Platform Admin/Content Admin is denied by default; future exception policy remains open. Verify AC-61/64 and NFR-36 express those boundaries.
- **AC06 — Evidence:** Record source hashes, exact changed sections, static consistency checks, open blockers and work not performed in FEAT-063 evidence/context/status/decision records.

## Completion status

Documentation correction can complete while the SRS remains a draft. The outcome is not “SRS ready for final diagrams”: owner answers, physical DDL/schema evidence, artifact reviews, diagram gates and any required implementation evidence remain separate.
