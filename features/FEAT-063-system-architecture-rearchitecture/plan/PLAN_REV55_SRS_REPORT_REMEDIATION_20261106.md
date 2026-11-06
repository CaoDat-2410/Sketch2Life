# FEAT-063 Plan Rev55 — remediate SRS review report

**Date:** 2026-11-06 (Asia/Saigon)
**Lifecycle:** COMPLETE for this documentation-only scope; canonical drafts remain unsigned.
**Feature:** FEAT-063 — system architecture rearchitecture.

## Source and authority

- Owner-provided review: `Sketch2Life_Bao_cao_hop_nhat_Fix_1_luot_v2_5.docx` (read-only copy supplied from Downloads; baseline SRS/Data Register v2.5-draft).
- Current product authority at plan creation: `artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md` v2.5-draft and matching `artifacts/DATA_TABLE_REGISTER.md` v2.5-draft; both unsigned.
- Supporting review context: FEAT-063 `CONTEXT.md`, `SOURCE_REGISTER.md`, `DECISIONS.md`, status and prior evidence. Older SRS versions are historical only.
- Scope authorization: the owner's direct request, “ĐỌC NÀY VÀ FIX CÁC ĐIỂM NHIUWTREEN,” authorizes a documentation remediation based on the report, within the boundaries below.

## Goal

Resolve every report finding that is supported by the current canonical SRS, source register, or repository evidence; make the SRS and Data Table Register internally consistent; and record every remaining product, data, legal, or implementation question without silently choosing a value.

## Scope

1. Evaluate all report items M-01–M-16, D-01–D-20, and Q-01–Q-13 against the current v2.5-draft SRS, Data Table Register, and attributable repository evidence. Record each as fixed, already covered, partially specified, implementation gap, not applicable, or OPEN, with the controlling source and reason.
2. Correct verifiable contradictions in the canonical SRS, especially Parent post-video activity order, video admission transitions, Q159 AI-suggestion roles, role/permission wording, AI-job target kinds, state/lifecycle descriptions, and trace links. Preserve established requirements and distinguish product decisions from technical proposals.
3. Reconcile the SRS and Data Table Register count narrative, table section headings, and historical decisions. Keep the source-derived target count separate from the dated local database snapshot and from historical baselines.
4. Add a structured remediation crosswalk and supporting logical specifications where repository evidence is sufficient: state/transition rules, API target-versus-as-built boundary, role/scope mapping, data relationship/lineage, screen/workflow coverage, and domain/package responsibility. Mark details without authoritative evidence as OPEN or NOT SPECIFIED.
5. Update the SRS/Data Register draft version and their authority pointers, plus FEAT-063 context, source register, decisions/status, and task evidence so the next reviewer can trace each change.

## Explicit exclusions and constraints

- No product-code, API implementation, database DDL/migration, Modal/provider, runtime configuration, deployment, or real-data changes.
- No invented quota precedence/pricing, media-access grant model beyond existing authority, role merges, random-sample eligibility, invitation acceptance actor, consent/legal policy, migration disposition, physical SQL types/defaults/index predicates, or other Q answers.
- Do not add database tables/columns or imply the target schema has migrated. Do not create a cross-owner foreign key where the architecture requires an opaque typed reference.
- Keep Q159 and the current parent activity ordering, 36–120 month age range, and decisions already resolved in §31 as controlling. Preserve unresolved questions as OPEN and retain their IDs/traces.
- No architecture diagrams/PDF publication while formal SRS/Data Register sign-off is pending.
- No commit or push is included in this plan.

## Work sequence

1. Build an item-by-item M/D/Q crosswalk against the current SRS, Data Register, and evidence; flag report claims that are stale, already resolved, or unsupported.
2. Edit the canonical SRS and Data Register in place as a new unsigned draft revision. Harmonize requirements, actor/permission language, state transitions, table counts, target-vs-as-built labels, and traceability without deleting historical decisions.
3. Add the report crosswalk/supporting catalogs under FEAT-063 artifacts and record unresolved items as OPEN or NOT SPECIFIED with their dependency/owner decision needed.
4. Update `AGENTS.md`, `docs/context/SRS_AUTHORITY.md`, FEAT-063 context/source/status/decision records and evidence to point only to the latest canonical working SRS.
5. Review every report ID for disposition; run `git diff --check`, targeted link/ID/count consistency checks and repository security validation only if a later commit is requested. Do not run product tests because this is a documentation-only task and no code is changing.

## Acceptance criteria

- **AC55.1 — Report coverage:** all 49 findings (16 M, 20 D, 13 Q) have explicit dispositions in the crosswalk; none disappear silently.
- **AC55.2 — Contradiction repair:** each supported contradiction is fixed at its authoritative SRS/Data Register location and its related FR/BR/AC/UC/permission/state/API/data traces are reconciled or explicitly marked OPEN.
- **AC55.3 — Open decisions preserved:** unresolved Q items and evidence-limited D items remain visibly OPEN/NOT SPECIFIED; no new product or schema decision is inferred from the report alone.
- **AC55.4 — Count and lifecycle integrity:** target mapping counts, source mapping counts, local snapshot counts, and legacy/historical counts are separately labeled and arithmetically consistent; no migration is implied.
- **AC55.5 — Authority and records:** canonical SRS/Data Register are version-aligned unsigned drafts, and repository authority/context/source/status/evidence pointers identify the new revision.
- **AC55.6 — No implementation side effects:** no code, database, provider, deployment, test-suite, commit, or push changes occur.
- **AC55.7 — Reviewability:** `git diff --check` passes; changed-file list is scoped to FEAT-063 documentation and required authority pointers; all new internal links and IDs resolve.

## Risks

- Report findings may reflect stale or mistaken assumptions. The current SRS and evidence take precedence; unsupported findings will be dispositioned, not blindly copied.
- Some architecture diagrams and physical schema details cannot be finalized until the owner resolves dependent questions and formally signs the SRS/Data Register.
- Version/count edits may expose older decisions that were never marked superseded; historical entries must remain traceable while current authority is made explicit.

## Review and approval

- Reviewer/approver: project owner, via direct task request.
- Approval state: record the exact plan SHA-256 and scope in `approvals/TASK_APPROVAL.md` before implementation.
