# Feature decisions

## Owner-confirmed proposal choices — 2026-09-29

- Interests/dislikes: free text, AI classification.
- The declared interests/dislikes represent relatively stable preferences stated by the adult, not only momentary curiosity.
- AI-generated topic tags must be shown to the adult and confirmed/edited before they affect recommendations.
- The adult-confirmed drawing topic remains primary; profile interests/dislikes only adjust ranking among related eligible activities and must not cause topic drift.
- Current-form progress: remove; do not present fabricated example history.
- Supervision/readiness: remove the profile-level availability selector; confirm adult participation at profile setup, then explicitly confirm the exact supervision requirement per candidate and ask readiness in activity context.
- Persistence: session-only remains in force for this increment; no durable writes.

These decisions are captured in the owner-approved FEAT-033 revision 3 plan. They do not alter SRS/ADR authority. Implementation reuses the existing backend-owned Qwen model/runtime and a versioned allowlisted taxonomy-only classifier contract. Readiness is needed only to determine whether a concrete candidate's authored prerequisite has been observed; an unknown response excludes only candidates requiring that prerequisite, not the entire candidate set. Adult support counts only when that activity's authored criterion permits support.

## Implementation follow-up — 2026-09-30

- The catalog audit is extended using FEAT-022 Decision 2 as an audit-only demand-family mapping; runtime matching remains unchanged.
- Coverage gaps are not filled with AI-generated or unreviewed activity/readiness content. New records require an authoritative source and qualified review; current report shows 200/300 templates have `UNSPECIFIED` readiness metadata and missing house/home concept coverage.
- The Lightning classifier is not treated as available merely because local code and mocked contract tests pass. The local API's typed `CLASSIFIER_UNAVAILABLE` response and a successful remote inference are separate verification states.
- Adult tag confirmation is now explicit in the V2 child-profile request. The backend rejects unconfirmed non-empty tag lists, while the mobile serializer sends no tags until confirmation.
- Phase-one condition-check candidates are returned in stable activity-ID order; only final eligible recommendations are ranked after adult answers.
- SRS BR-013 is enforced across legacy and V2 paths: under-three candidate displays elevate supervision to direct caregiver supervision; legacy `P1ContextV1` cannot submit under-three context; `P1ContextV2` carries caregiver participation through P1 filtering. See `docs/adr/ADR-0011-contextual-readiness-candidate-contract.md`.
- Mobile age entry uses exact completed years plus months, bounded to 0–155 months; it does not request or store date of birth. This is an implementation choice using the exact age value already consumed by the approved catalog filter, not a new owner-confirmed retention or birth-date decision. Ages 0–35 expose a caregiver-specific direct-supervision confirmation and use the additive P1 context contract. SRS OPEN-014's unresolved DOB/time-zone/snapshot semantics remain unresolved.
- Verification boundary: the 35/36-month UI transition is visually verified on a dedicated API 37 AVD, but the 59.73 ms JS callback-to-next-frame proxy is not equivalent to native input-to-presented-pixel latency. Keep AC-09 open until an event-correlated trace and comparable baseline exist; do not treat a local classifier contract as proof that the deployed Lightning route is available. See `FEAT033-EV-20260930-17`.
- Activity-specific readiness/material answers and adult/caregiver participation are scoped to one completed workflow. Clear them only after successful feedback persistence; failed saves retain them for retry. Stable adult-declared preferences/tags remain session-local and available for later activities in the same app session. See `FEAT033-EV-20260930-18`.
- P1 phase-two filtering must validate the chosen activity against the server-recomputed, unranked phase-one shortlist, not a newly ranked default top-three. Canonical readiness identifiers are normalized at the catalog adapter; caregiver presence remains an adult safety/supervision condition, never evidence of child readiness. Existing hard gates remain authoritative. See `FEAT033-EV-20260930-19`.

## Owner-directed scope amendment — revision 6 — 2026-09-30

- After Gate A, activity discovery returns the complete reviewed set matching the confirmed drawing topic and exact child age; there is no fixed top-three limit. Pagination is acceptable only as transport/UI mechanics that preserve access to the whole set.
- Child-profile interests/dislikes are stable adult-declared preferences. AI can propose only reviewed taxonomy tags; an adult confirms/edits them. Confirmed preferences rank and explain matches within the topic+age set; they cannot change topic or eliminate otherwise matching activities.
- Remove child readiness, completed-activity history, and current material availability as activity-discovery questions or eligibility filters. Materials can be displayed as preparation information after activity selection.
- Preserve reviewed/active catalog status, exact age, confirmed topic, authored safety/policy, explicit adult participation, and age-under-three caregiver/direct-supervision gates. Keep adult review before starting.
- This decision supersedes earlier decisions in this file that require readiness/material confirmation before final recommendations. SRS v1.8 B33 records the same owner change; runtime contracts must be additive/versioned and captured in an ADR.
