# ADR-0014: Collaborative creative learning scope replacement

- Date: 2026-10-10 (Asia/Saigon).
- Status: SCOPE_REPLACEMENT_ACCEPTED; TECHNICAL_DESIGN_PROPOSED.
- Owner: Sketch2Life project owner.
- Approval: FEAT-039 task approval revision 3, documentation only.

## Context

Owner supplied Product Scope v1.0 for Montessori-inspired collaborative creative learning, then explicitly answered that it replaces the current scope, targets Android tablets/phones and retains FastAPI and React Native. The prior Master SRS v2.0 contains incompatible under-9, Parent/Guide, individual-session, parent-portal/payment and media policies. Source runtime has not been migrated.

## Accepted product decisions

1. The new product target is ages 3–12 with Child, Teacher and Super Admin functional actors, classroom/group sessions, collaborative canvas, adaptive sketch, gallery, teacher-approved knowledge video, off-screen, reflection/portfolio and administration/privacy/recovery.
2. Retain FastAPI and React Native; Android is the confirmed child device target.
3. Canonical Master SRS is v3.1 at features/FEAT-029-master-srs/artifacts/Sketch2Life_Master_SRS.md. Exact pre-edit v2.0 and v3.0 are preserved with hashes under FEAT-039. Source PROPOSED/TBD details remain unconfirmed; B19–B26 are detailed logical refinements for review, not adopted runtime contracts.
4. Old product assumptions are not automatically requirements of the replacement: under-9 guards, Parent/Guide roles/ownership/shares, Parent portal/payment/credit, mandatory animation/narration, 40–60-second video, Wan baseline and numeric retention. Original/provenance and repository security rules continue.
5. No automatic video fallback or skip while generating: the source explicitly requires waiting. Owner subsequently resolved OD01: after permitted retries fail, Teacher explicitly selects retry, skip or end; retry budget is open. No successful-video claim for a skipped stage.
6. Owner resolved OD02: per-suggestion Teacher review before child access for pilot. Owner resolved OD03: shared tablet selects the active child by turn; security identity and selected contributor are separate, no retrospective reassignment of strokes.
7. Owner chose a one-school pilot with preparation for expansion (OD06). Organization/class resource scoping is proposed logical design; this does not select a multi-tenant deployment topology or authorize a multi-school launch.
8. Owner chose teacher-managed profiles and QR/session code admission without independent child login (part of OD14). Pending device admission, possession and scoped capability/revocation contracts are proposed, not authenticated proof of who physically draws.
9. Owner chose school collection of legal-representative consent, with authorized Teacher/Admin recording evidence and purposes (part of OD04). Enrollment and role are not consent. Exact representative/recorder/verifier authority, policy purposes, jurisdiction, retention and request processes remain refinement gates.
10. Owner resolved OD13 endpoint: at least 36 and at most 155 completed months, from age 3 to before 13. Exact age/reference-date calculations, UI-band month mapping and mixed-age curriculum contracts remain refinement.
11. Owner resolved OD12 capacity target: one simultaneous class, at most 40 children. This is a verification target, not achieved runtime performance; devices, groups, network and AI budget/profile remain proposed.
12. Owner resolved the session/artwork default in OD05: retain for 90 days after session end. Profile/portfolio/audit and other data-class durations, shared deletion and copy/provider/backup enforcement remain separate policy/evidence gates.

## Technical proposal, not an accepted full stack

- Keep inward domain/application/adapter boundaries and versioned contracts. Start with a modular monolith plus separate worker processes; split deployment only with evidence.
- Add ClassroomSession/GroupProgress/Participant and CanvasDocument domains; retain existing artwork-understanding pipelines under them. Do not change meaning of existing V1 contracts without versioned migration.
- Consolidate apps/ui-mobile and apps/mobile into one approved React Native runtime after compatibility/device verification. Current Expo52/RN0.76.9 demo and RN0.87 fixture skeleton are different baselines.
- Compare native React Native Skia and a newly built Pixi/WebView editor. Existing Pixi/GSAP player is reusable playback, not a drawing editor.
- REST/HTTP polling stays a candidate for commands/jobs. WebSocket canvas/presence/live projections is a proposed amendment to the old polling default; implementation requires accepted transport/authorization/recovery ADR evidence.
- Compare server-ordered, durable stroke operations/checkpoints with Yjs/CRDT. Merge convergence does not provide authorization, region lock, identity attribution or durable recovery by itself.
- PostgreSQL/SQLAlchemy/Alembic, Redis/RQ, S3-compatible/MinIO and adult Firebase Authentication are reuse candidates/current constraints, not completed production adapters. Teacher/Admin web technology, local persistence, AI models/providers, deployment and capacity remain open.

## Decisions required before full stack freeze

SRS B17 owns the current register. OD01/02/03 behavior, school/profile/consent choices, exact age endpoint, pilot cardinality and default session/artwork duration are resolved. Retry parameters, turn/review binding, consent verification/other data-class retention, measured capacity/device/network/model budgets, stage rewind, tools/imports/rubric/screen time, age calculation, admission grant/teacher-offline lifecycle, mobile runtime/canvas/sync, AI/media, grouping criteria and jurisdiction remain refinement gates. Only Android/FastAPI/React Native are newly confirmed technical choices; no full stack freeze follows from the detailed logical contracts.

## Consequences and authority

- This ADR records target scope replacement; it does not authorize runtime, schema/contract migration, provider calls or deployment.
- ADR-0003/0004/0005/0008–0013 retain implementation/history significance, but conflicting product targets are superseded by SRS v3.1. Security invariants remain. Model/provider/library/deployment assumptions must be reconfirmed for the new product rather than silently extended.
- ADR-0006 still governs four independent fixture/contract Sprint 1 workstreams. Dependency roadmap and team allocation stay separate; integration/reallocation needs an approved plan.
- Existing runtime still accepts old demo actor/age/state patterns. Do not release it as the new target until separately approved features prove authorization, durable recovery and classroom behavior.

## Evidence

- features/FEAT-039-collaborative-learning-scope/approvals/TASK_APPROVAL.md.
- features/FEAT-039-collaborative-learning-scope/evidence/notes/SOURCE_REVIEW.md.
- features/FEAT-039-collaborative-learning-scope/artifacts/REUSE_AND_ARCHITECTURE.md.
- features/FEAT-039-collaborative-learning-scope/artifacts/Collaborative_Learning_SRS_v3.1.md.
- features/FEAT-039-collaborative-learning-scope/evidence/notes/FOUNDATION_EXPANSION_SOURCE_AND_DECISIONS.md.
