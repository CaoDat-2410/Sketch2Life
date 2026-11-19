# ADR-0023: FEAT-081 apps/ui-mobile implementation location

- Date: 2026-11-12
- Status: ACCEPTED FOR FEAT-081 ONLY; implementation NOT LAUNCHED.
- Authority: Direct owner instruction dated 2026-11-12, recorded in FEAT-081 D-009 and its append-only approval addendum.
- Scope: FEAT-081 Wave 1 and any separately approved FEAT-081 Parent UI follow-on waves. This ADR decides the code destination for that feature only.

## Context and conflict

The canonical product source is the unsigned FEAT-063 v2.7-draft Rev60 SRS (SHA-256 70DA43A35106E8C02B4BB8FCCB9628C0376C9E7EA6CFC51909ACB569703B218B). Section 7.2 FR-P-01 names apps/mobile as the current Parent Android foundation and apps/ui-mobile as the behavior/UI reference. Section 9.3 (baseline technology and repository status) likewise names React Native 0.87 in apps/mobile and describes apps/ui-mobile as a reference.

ADR-0020, accepted for FEAT-062 within its stated scope, identifies apps/mobile as the active Parent Android implementation target and apps/ui-mobile as the behavior reference. ADR-0021, still proposed pending review of its technical baseline, also names apps/mobile for Parent Android and apps/ui-mobile as a behavior reference.

The owner has separately directed that FEAT-081 and its separately approved Parent UI follow-on waves remain implemented in apps/ui-mobile, with no move to apps/mobile under this feature. This differs from the broader product target stated in the SRS and ADRs above.

## Decision

For FEAT-081 only, use apps/ui-mobile as the code destination for Wave 1 and for any later Parent UI wave that receives its own feature approval. Do not move or duplicate FEAT-081 wave screens into apps/mobile.

This is a feature-scoped implementation-location exception based on the direct owner instruction. It does not amend, replace, or claim to update the canonical SRS. It does not globally supersede ADR-0020 or ADR-0021. The SRS Rev60 product target and the broader apps/mobile direction in those ADRs remain in force outside FEAT-081. This ADR does not claim that apps/ui-mobile has become the production Parent target or that FEAT-081 alone fulfills the SRS product target.

If the owner intends to change the product-wide or production Parent target from apps/mobile to apps/ui-mobile, that broader change requires a separate owner decision and an explicit SRS/ADR revision. No such change is recorded here.

## Consequences and boundaries

- Wave 1 remains limited to P01 home and P02 lesson gallery in apps/ui-mobile under the approved alternative allowlist.
- Waves 2-5 remain outline-only; each requires a separate approval. The same apps/ui-mobile location applies only if the owner separately approves that FEAT-081 follow-on wave.
- apps/mobile remains unchanged and outside FEAT-081.
- The sibling Vite/React web worktree remains read-only reference material. Do not copy React DOM, CSS, assets, API code, or packages.
- Existing FEAT-081 D-001 through D-008 and Revision 1 records remain unchanged. D-009 records this scoped location exception.
- Implementation, tests, Android work, staging, commit, and push are not authorized by this ADR. Wave 1 still requires an explicit owner launch instruction.