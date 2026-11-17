# EV-063-61 — Ten-group diagram-readiness alignment

- Date: 2026-11-08
- Branch: docs/feat063-diagram-readiness-20261107
- Source tip before edits: 7d35ee3cd75ae7b34a71433daa2231781c9bc60c
- Canonical pair: FEAT-063 SRS and Data Table Register v2.7-draft at 98cc34a39af279560b5f8d39f18939a376535834; both remain unsigned.
- Plan/approval: Plan Rev56 and its SHA-256 are recorded in root and feature approvals/TASK_APPROVAL.md.

## Review outcome

The source checklist was reconciled with the existing Rev54 readiness crosswalk/catalog and Rev55 assessment. The Teacher sample language now consistently says the system selects randomly under an owner-approved eligibility/consent policy and the responsible Teacher reviews/confirms the child/context, including UC-05, the Teacher responsibility row, the FR-T-10 verification trace, Teacher screen inventory, error guidance and §5.2. FR-PL-20 and AC-56 are aligned. Historical Q185 source wording is preserved and annotated with the current requirement interpretation. Occurrence-level selection evidence/snapshot handling remains open and distinct from the required run-input context snapshot.

Eligibility, consent/guardian notice, exclusion, reselection, no-eligible response, and selection evidence remain OPEN under Q-01. The other nine groups are mapped to existing M/D/Q/R/OI references. Settled sub-decisions remain intact, including Content Admin as a Platform Admin permission, child-media default deny, school-only Teacher quota, exact version/hash pins, and no-name identity matching. UC/screen actor labels use Platform Admin (Content Admin permission), not a separate role.

## Files updated

- SRS §31.10 and Teacher sample use case/requirement/acceptance, actor, screen/error and verification wording.
- Data Table Register §14.3 and a ten-group data-readiness trace.
- Diagram Input Catalog v2.7 Rev56 successor; Rev54 is preserved.
- FEAT-063 plan, approvals, context, decision-status note, source registers, evidence index, and status.

## Limits and verification

- No owner decision was closed. No new rule, schema/table, key, state, permission, DDL, endpoint, or final diagram was created.
- Physical ERD remains blocked on approved DDL/constraints and approved source-to-target migration mapping. As-built diagrams still require current code/schema evidence. All 13 diagram handoff artifacts must later cite requirement/decision IDs and the same approved SRS/Register baseline; that baseline is not approved yet.
- No product tests/builds, source/runtime/API/database/provider inspection, or migration was run.
- `git diff --check`: PASS. Repository security validation passed before commit and push (`publishable_files_scanned=6576`).
- Publication: commit `09cfc5ca396016cbb7b238a5c744e004f7c7025a` was pushed to `origin/docs/feat063-diagram-readiness-20261107`; fresh `git ls-remote` confirmed the same SHA.
