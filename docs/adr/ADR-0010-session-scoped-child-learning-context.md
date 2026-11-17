# ADR-0010: Session-scoped child learning context for Montessori recommendations

- Status: Accepted for the FEAT-018/020/030 integrated increment
- Date: 2026-09-29
- Decision owners: project owner and implementation team
- Scope: recommendation request semantics only; no durable child-profile storage

## Context

The P1/V2 Montessori recommender previously received age and the adult-confirmed scene, but no
explicit child interests, dislikes, adult-confirmed progress, readiness, available materials,
supervision availability, or explicit non-clinical learning supports. Current-scene salience is not
a trustworthy substitute for child preference. The integrated plan was approved in
`features/FEAT-018-live-image-canvas-flow/approvals/TASK_APPROVAL.md`.

## Decision

1. The current mobile test profile is volatile application-session state, keyed by the selected
   mock child only for routing within that running app process. It is not written to AsyncStorage,
   local databases, backend session storage, analytics, or logs.
2. A versioned `ChildLearningProfileContextV1` may be sent in the actor/session-checked
   recommendation request (the current demo uses its demo actor; production authentication remains
   a separate, unimplemented decision). The server validates it and uses it only for that request;
   the read does not mutate the workflow session or create a child-history record.
3. Safety/supervision, adult-confirmed prerequisites, explicit dislikes, readiness, and required
   material groups are hard eligibility gates. Explicit interests, confirmed objective progression,
   and selected non-clinical supports may affect deterministic ranking only after hard gates pass.
4. Missing catalog readiness/material metadata fails closed only when an adult profile filter is
   enabled; requests without a child profile retain the previous no-profile behavior. Missing
   profile fields are not silently inferred or filled from scene/age.
5. The response may include a bounded, deterministic baseline-versus-personalized comparison and
   exclusion reasons. It must not call Qwen again, update model weights, claim mastery from
   completion, or infer psychological traits from artwork, speech, or behavior.
6. Durable profile/history storage is a future decision. It requires separate approval and an ADR
   covering backend-owned storage, identity/consent, caregiver/Guide authorization, audit, retention,
   correction, export/deletion, and the existing Firebase-data-service prohibition. This ADR does
   not select a database or storage provider.

## Consequences

- A session restart discards all profile edits; the adult must re-enter the test profile.
- The mobile editor is available in Parent/Guide profile settings and at initial child selection,
  never in the middle of an active child flow.
- The test profile is useful for checking recommendation behavior but is not a production child
  record and must not contain identifying free text.
- Catalog omissions can remove all eligible options when profile hard constraints are active. The
  app must report the no-match condition instead of silently dropping those constraints.
- This is an additive request contract; the existing profile-free GET path remains available.

## Verification boundary

Unit/contract tests and synthetic mask tests can verify determinism, hard gates, compatibility, and
metric calculations. They do not prove pedagogical validity, real-child suitability, SAM accuracy
on real drawings, L4 latency, or Android visual quality. Those remain explicit review/acceptance
gates under the owning feature evidence indexes.
