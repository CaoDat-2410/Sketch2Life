# EV-063-18 — Platform lesson library and sharing reconciliation

- Date: 2026-10-28
- Feature: FEAT-063
- Type: documentation-only change and static cross-document reconciliation
- Status: SRS and Data Table Register remain drafts; no content sign-off or product implementation approval is implied.

## Authority and scope

Plan Rev25 is approved for this documentation amendment only. Its SHA-256 is `90EDB84AE60864740A64863423F7F9C72052AFE757ED7427360FC6A29D8AB621`. The owner answers 1–49 are represented in SRS §31.11 as Q147–Q195. The amendment is additive and preserves prior Parent/Teacher behavior, the planned child-specific image-to-video pipeline and decision history except where an explicit new answer updates it.

## Updated records

- Canonical SRS: `artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md`, v2.3-draft.
- Canonical data model: `artifacts/DATA_TABLE_REGISTER.md`, v2.3-draft.
- Proposed architecture record: `docs/adr/ADR-0022-platform-lesson-library-and-sharing.md`.
- Feature context, decision log, status, source register and evidence index.
- Global pointer: `docs/context/SOURCE_REGISTER.md`.
- Current post-amendment SHA-256: SRS `8646E6A5ABA4CCFB2A05D425316DFD2A373C5DA104108AFA65CF135875DA0E94`; Data Table Register `7B2A775A54B1B5C28688CA20C55DD10C1DF27BE24CD635CFEBB226885DA1C904`.
- Preserved pre-amendment v2.2 snapshots:
  - SRS SHA-256: `3317CAEE771ADEA9A7A3C1F9FA29C20FD61B10462BDDE0EA9FEA6FE5AD70E426`.
  - Data Table Register SHA-256: `EDCC8EE831B307BBB2E86B7FBE7292875B1A8ECC793E1491DD3E7F13189B594B`.

## Reconciled product direction

- Platform Admin, School Manager, Teacher and Parent roles; one school per organization; scoped, audited and revocable authorization.
- Parent and Teacher profiles remain separately owned. Parent–Teacher sharing is invitation-based, consented, field-scoped and revocable.
- Reusable lesson versions are separate from occurrences. Parent/Teacher may request AI edits to a reused lesson as a draft/personal copy with lineage; the source remains unchanged. Visibility includes private, school, selected audience and public. Manager approval is required before Teacher content becomes public. Platform Admin can moderate/hide.
- Uploads use a structured template, parser and allowlist filter. The raw original/full plan is not sent to AI; Teacher reviews/corrects the extracted structured draft first. AI results remain drafts.
- Parent flow is drawing → optional in-session sketch guidance → capture → existing video pipeline → configured activity list. Teacher flow and the one-child representative sample remain. Teacher sketch generation is opt-in when enabled in-session.
- Each child video is generated anew from that child’s drawing and approved profile context. Lesson script direction is optional. Subject mismatch requires adult confirmation/correction.
- Parent can access delivered/public/shared lessons, download permitted lesson content and send lesson-scoped feedback; replies remain in the responsible school scope. No direct chat, completion mark or drawing-photo feedback upload.
- Platform cost is handled by the platform. Billing models school, Teacher and Parent quota scopes; AI Policy retains compute reservation. Exact package values and charge precedence remain open.
- Age scope is 36–120 months (3–10 years), Vietnamese-first. Exact Montessori age bands remain open.

## Static reconciliation

- SRS v2.3 declares 107 functional requirements, 60 business rules, 38 non-functional requirements, 65 Given/When/Then acceptance criteria and 19 edge scenarios.
- New platform IDs: FR-PL-01–25, BR-47–60, NFR-34–38 and AC-46–65.
- Data Table Register arithmetic: 38 retained/refactored + 51 new = 89 active; plus 48 legacy/read-only = 137 projected physical. The 11 new platform entities are listed in §14.1; counts are repository-derived and no live database was inspected.
- Requirement trace Q147–Q195 covers all 49 owner answers; open or ambiguous points remain in SRS §31.10 and Data Table Register §14.3.
- Plan SHA and preserved snapshot SHA values were checked with SHA-256. Cross-document text checks confirmed the active Q167 session opt-in, updated Parent draw/capture/video/activity order, the unpublish rule, target counts and new AI Job target kinds.
- Static ID counting confirmed 107 FR, 60 BR, 38 NFR, 65 acceptance criteria and all 49 trace rows Q147-Q195. Per-ID FR/NFR and BR trace matrices include FR-PL-01 to FR-PL-25 and BR-47 to BR-60. The 11 added logical table names were present in the current Data Table Register.
- `git diff --check -- docs/context/SOURCE_REGISTER.md` returned no whitespace errors; a trailing-whitespace scan of the new plan, ADR and evidence note found none; the conflict-marker search returned no matches. These are document hygiene checks, not product tests. No product tests or builds were run.

## Limits and remaining gates

No product code, UI, API, physical schema, migration, database access, provider/model call, generated visual, product test/build, deployment or real-child processing was performed. Final stack/provider selection remains open. Open items include exact age bands, AI lesson-suggestion initiator roles, share field/expiry policy, 30/60-day history, sample eligibility, script defaults, public review for Admin-authored lessons, generated visual approval, quota package/charge precedence and answer 46.

The previously generated diagram/PDF package predates this SRS revision and was not refreshed. It is not evidence of v2.3 content.
