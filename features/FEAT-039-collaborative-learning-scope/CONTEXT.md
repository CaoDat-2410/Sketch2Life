# Feature context

## Current SRS — revision 5 / v3.3, 2026-10-24

The current SRS v3.3 is `artifacts/Collaborative_Learning_SRS_v3.3.md` and canonical `features/FEAT-029-master-srs/artifacts/Sketch2Life_Master_SRS.md`. Exact v3.2 bytes are preserved at `artifacts/Collaborative_Learning_SRS_v3.2.md` (SHA-256 `9d7a71cc3fd0ab45b3175823c09780af0eb2e129d21a991d5470693dae25a21d`); exact v3.1 remains at `artifacts/Sketch2Life_Master_SRS_v3.1_preserved_20261023.md` (SHA-256 `A95C89589843E3555E967C5E486F3BCAF4BBDF9446CB3BC9C49ED16F672964D9`). Revision 5/B28 records six owner decisions: revoke pending admissions atomically on Start; approve a shared lobby code with pre-start rotation and persistent 10-invalid/IP/15-minute throttling; require next-stage progression with interleaved/`not_needed` Assistance; prohibit stage rewind until OD07 is resolved; save unfinished group work as a draft before advance; and require an early-stop reason category with optional note. These are product policies, not implementation sign-off. Exact BE1 contract, security/migration review and routes remain gated; FEAT-057/Modal remain separately gated.

- Goal: assess reuse and prepare SRS for Montessori-inspired collaborative creative learning.
- Owner: Sketch2Life project owner.
- Date: 2026-10-10.
- Historical foundation completion: canonical system-foundation SRS v3.2 (revision 4); its exact copy remains preserved. Current revision 5/v3.3 is maintained above.
- Input: user-supplied Final Product Scope v1.0, Discovery Complete, Implementation Refinement Pending.
- Sources: attachment, PROJECT_CONTEXT.md, SOURCE_REGISTER.md, Master SRS v2.0, ADRs and inspected checkout.
- Constraints: preserve confirmed source behaviors, separate proposed/TBD, preserve original media/provenance, Firebase Authentication only, backend-only providers and storage.
- Dependencies reviewed: actual backend/AI/frontend audit, source coverage, owner answers on replacement/device/retained frameworks and product/foundation choices. Remaining refinement/other-stack/consent-verification/other data-class decisions remain in SRS B17.
- Owner answers: new scope replaces current scope; Android tablets/phones; retain FastAPI and React Native. Preserve old SRS exactly before updating canonical file.
- Refinement answers: per-suggestion Teacher review; shared tablet active-child turn selection; exhausted video failure has explicit Teacher retry/skip/end choices. No automatic video skip while generating.
- Foundation answers: one-school pilot prepared for expansion; teacher-managed child profiles + QR/session code, no child login; school collects guardian consent and authorized Teacher/Admin record evidence/purposes.
- Foundation boundary answers: 36–155 completed months inclusive; pilot one simultaneous class with at most 40 children; session/artwork default retention 90 days after session end. Target capacity is unverified; portfolio/profile/audit/copies have separate policies.
- Conflicts: 3–12 vs current under-9; Child/Teacher/Super Admin vs PARENT/GUIDE/ADMIN; classroom/group concurrency vs one-child flow; video wait vs fallback; parent portal/billing not confirmed in new scope.
- Non-goals: application code, provider calls, stack/version upgrades, contract adoption or approved visual assets.
- Risks: stale documentation, fixture claims mistaken for integration, unresolved shared-device attribution and consent.
- Next gate: source/traceability review, unresolved product refinements and proposed architecture review; runtime changes require separately approved features.

## Completion — 2026-10-10

Canonical SRS v3.0 replaces the old target; preserved v2.0 hash verified unchanged. Report, proposed technical ADR and source/evidence/status records are complete. Independent QA found no remaining actionable issues after corrections and owner answers. Own static/harness/security-content checks and architecture pass; global harness/security findings from earlier features/local outputs remain recorded in evidence/notes/VALIDATION.md. No runtime edit, provider call, upgrade, publication or commit/push.

## Foundation completion — revision 3, 2026-10-10

Canonical and consolidated SRS v3.1 are identical; exact v2.0/v3.0 hashes are preserved. B19–B26 provide detailed policies/states/use cases/DTO/API/UI/privacy/NFR/verification with all 66 FRs traced. Six foundation answers and prior product choices are integrated into canonical/ADR/context/source/approval. Independent cross-section review and final document checks pass; global pre-existing repository limitations remain in FOUNDATION_VALIDATION.md. Documentation baseline is ready for feature/contract/QA planning; runtime contracts, full stack and future implementation/release still need the relevant decision/approval/evidence.
