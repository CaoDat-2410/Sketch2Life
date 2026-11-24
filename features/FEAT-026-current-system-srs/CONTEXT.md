<!-- SRS-AUTHORITY-REV67 -->
> **Historical SRS context — not current product authority.** Current product requirements and target architecture are defined only by `features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md` (v2.7-draft; Rev57 baseline, local amendments through Rev67; unsigned). Treat older SRS versions and authority claims in this feature context as dated snapshots; use this file for feature-local status/provenance only. See `docs/context/SRS_AUTHORITY.md`.
# Current system SRS document context

## Current English derivative — Rev2 — 2026-10-26

- The approved current-system source remains the original Vietnamese Word form at artifacts/Sketch2Life_SRS_Form.docx; it is preserved byte-for-byte (SHA-256 08f43d867cdb6a30c05440223b9f015a02f5c3f3c2adacd1ede9f29b28b151a6).
- The current English derivative is artifacts/Sketch2Life_SRS_Form_English.docx with a local PDF companion. Both filenames use ASCII English words only. The derivative is not the canonical FEAT-039/FEAT-029 SRS and does not replace either source.
- Rev2 adds all four team members and responsibilities to the introduction, retains the supervisor using ASCII transliteration, centers the two-line cover title with “AI for Children”, standardizes all editable text to Arial 10 pt, and corrects the remaining “Session init” shorthand.
- PDF text, proofing language, font/size distribution, page count, page renders and spelling-review disposition are recorded in evidence/metrics/rev2_english_qa.json and evidence/metrics/rev2_english_spelling_review.json. The refreshed PDF has 13 pages; Appendix A is on the final page and there is no footer-only page.
- Approval and acceptance criteria are in plan/PLAN_REV2_ENGLISH_DELIVERY_20261025.md and approvals/TASK_APPROVAL.md. Source and output hashes are in SOURCE_REGISTER.md.

- Status: APPROVED
- Owner: project owner / Codex reviewer
- Goal: preserve the original editable Vietnamese Word SRS and provide a separate English-only derivative documenting the current Sketch2Life system, its implemented and fixture-only behavior, target boundaries, major contracts, flows, acceptance criteria, and open implementation gaps.
- Scope: documentation artifact only; derive content from the repository snapshot, source register, current architecture, ADRs, and current feature evidence.
- Non-goals: product implementation, contract migration, provider execution, cloud changes, Android release, frontend visual asset application, merge/push, or modification of pre-existing user changes.
- Primary sources: `docs/CURRENT_SYSTEM_STATE.md`, `docs/context/PROJECT_CONTEXT.md`, `docs/context/SOURCE_REGISTER.md`, `docs/architecture/`, `docs/adr/ADR-0003-tech-stack-pending-discovery.md`, `docs/adr/ADR-0004-android-only-private-ai-boundary.md`, `docs/adr/ADR-0005-auth-release-and-ai-provider-strategy.md`, `docs/adr/ADR-0006-parallel-sprint-allocation.md`, and current feature evidence referenced by the snapshot.
- Original source: `artifacts/Sketch2Life_SRS_Form.docx`. Current derived output: `artifacts/Sketch2Life_SRS_Form_English.docx` and its local PDF, with embedded flow diagrams, status chart, requirement tables, contract summary, and sign-off form.
- Sensitive-data boundary: no credentials, provider tokens, raw child media, handbook/workbook originals, or real child data may be copied into the artifact.
