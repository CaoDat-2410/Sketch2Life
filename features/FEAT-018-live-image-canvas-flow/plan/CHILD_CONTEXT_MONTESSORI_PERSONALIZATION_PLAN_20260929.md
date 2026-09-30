# Child-context personalization for Montessori recommendations

- Feature ownership: FEAT-018 supervised mobile flow; FEAT-020 semantic activity catalog/backend producer
- Revision: 1
- Status: IMPLEMENTATION_IN_PROGRESS_UNDER_APPROVED_INTEGRATED_PLAN
- Plan type: approved implementation workstream; coordinated release gates remain open
- Coordination: profile-editor UI and combined release are governed by FEAT-018 `INTEGRATED_CHILD_PROFILE_AND_RIG_QUALITY_PLAN_20260929.md`; this detail plan is not a separate approval request.
- Owner-confirmed UI: Parent/Guide profile area plus an edit control at child selection at the very beginning of the main flow; no mid-flow profile editor.
- Owner-confirmed current data boundary: session-only changes now; durable backend/storage is the long-term target and requires its own later approval/ADR before writes.

## Question and current-state diagnosis

The current recommender is not yet using a persisted child's interests, dislikes, accomplishments,
or observed learning history as a personal profile. The existing V2 resolver receives the confirmed
visual/narrated anchor set, age, catalog, compiler, and narration text. It ranks catalog matches and
uses an anchor-order `child_interest_alignment` value (1.0 for primary and 0.65 for secondary)
created from visual salience. That is a picture/topic relevance proxy, not evidence of a child's
long-term preference.

The mobile demo's selected child is mock data and currently provides age/name rather than a verified
preference/history profile. P1 context generation calls the resolver with age and the confirmed
anchor/narration context. Feedback can record completion status and optional interest/independence
scores, but the recommender does not consume a child's longitudinal history; completion is not proof
of mastery. Readiness, prerequisites and materials exist in activity/catalog and Gate-B rules, but
the current workflow does not have a reliable persisted per-child profile that supplies all of the
child-specific context.

The app currently loads the MVP plus the curated expansion catalog (100 base profiles plus 200
curated variants in the current source). The primary gap is therefore not simply the number of
activities: it is the absence of explicit, trustworthy child context and measured coverage of
interests, developmental goals, readiness, materials, accessibility/support preferences and
progression. Do not expand catalog rows blindly before a coverage audit.

## Goal

Recommend activities that remain Montessori-appropriate and safe while considering adult-confirmed
child interests and avoidances, observed accomplishments/progression, readiness, available materials,
and optional non-clinical support preferences—without inferring a child's psychology from a drawing,
voice, or model output.

## Proposed work, gated by approval

1. **Audit catalog and current decision path.** Produce a field/coverage matrix for all 300 current
   profiles/variants: age band, concept/objective, prerequisite, readiness criteria, materials and
   substitutes, supervision/safety, support variants, explicit interest tags, accessibility, and
   source/review status. Identify actual uncovered combinations before proposing additions.
2. **Define the child-context boundary.** Design a versioned, minimal context contract that separates
   (a) session-confirmed drawing/narration topic, (b) guardian/Guide-confirmed interests and
   avoidances, (c) observed learning history/progression, (d) current available materials and
   readiness, and (e) optional user-selected non-clinical support accommodations. Keep proposed
   fields `PROPOSED_UNADOPTED` until reconciled through FEAT-003's contract registry and an ADR.
3. **Separate hard eligibility from personalization ranking.** First exclude candidates that fail
   age, safety/supervision, explicit avoidances, readiness/prerequisite, material availability, or
   policy requirements. Then rank the eligible set by the adult-confirmed current interest, stated
   learning goal, recent explicit preference/feedback, observed prerequisite/progression and catalog
   match. Explain recommendations with evidence/reason codes and retain the adult's choice at the
   existing approval gate; no recommender bypasses Gate B.
4. **Represent accomplishments carefully.** Distinguish “activity attempted/completed,” reported
   interest/independence, and an adult/Guide-observed milestone from demonstrated mastery. Use only
   explicitly recorded observations with source, date/recency and reviewer; do not infer mastery
   from completion, time-on-task, facial/audio signals, or artwork. Regressing/changing interests
   should not permanently lock a child into a skill level.
5. **Provide transparent preference controls.** Let a parent/Guide review, edit, clear and expire
   explicit interest/dislike and support entries; record who supplied them and when. A dislike should
   suppress or down-rank only according to the explicitly chosen policy, and the UI should explain
   when it leaves no eligible choice. Children can express a preference in the supervised flow, but
   an adult retains safety and activity approval authority.
6. **Keep current edits session-scoped.** Prove the algorithm with synthetic profiles/fixtures and
   adult-entered values held only in the active supervised session, then send those values through
   the approved backend request to the deterministic recommender. Define a replaceable backend
   persistence seam for the long-term direction, but do not write the profile to durable storage in
   this increment. Durable child profiles/history need a later storage ADR and explicit consent,
   access control, retention/deletion and authentication approval; Firebase Storage/Firestore/
   Realtime Database remain prohibited.
7. **Expand the catalog only from evidence.** If the coverage matrix identifies gaps, add reviewed
   activities/variants for those exact age × concept/goal × readiness/material/support intersections.
   Validate child-safety, Montessori fit, source/reviewer provenance, duplicates and strict Gate-B
   compiler fit. Preserve a no-match outcome with an actionable explanation rather than suggesting
   an unrelated age-only fallback.
8. **Evaluate personalization.** Use synthetic child-context fixtures and adult-reviewed expected
   rankings to test hard safety/eligibility, explicit preference effects, recency, tie-breaking,
   explanation quality, no-profile behavior, no eligible candidate, profile clearing, and regression
   against current age/topic-only results. Report coverage and disparities by age band without using
   real child records in repository evidence.

## Acceptance criteria

- AC-CTX-01: A source-backed audit documents exactly which child attributes are currently consumed,
  which are catalog-only, which are mock/unavailable, and which fields are absent. It clearly labels
  visual-anchor salience as a topic relevance proxy rather than personal preference.
- AC-CTX-02: The versioned design distinguishes confirmed interest, explicit avoidances, observed
  accomplishments/progression, readiness/material constraints, and optional non-clinical support
  preferences with provenance, recency and adult control. It introduces no psychological diagnosis
  or inferred personality/emotion feature.
- AC-CTX-03: Candidate safety/age/readiness/prerequisite/material/supervision constraints are hard
  eligibility gates applied before ranking; explicit preferences only personalize eligible choices.
  Gate A/Gate B identity and adult approval are unchanged.
- AC-CTX-04: Completion feedback is not treated as mastery. Any progression influence must be based
  on an explicitly defined adult/Guide observation or approved evidence source, and the explanation
  identifies its provenance and recency.
- AC-CTX-05: Catalog additions, if justified by the coverage audit, close named measured gaps and
  pass provenance/review, duplicate, safety, age-fit and compiler tests. No blanket expansion target
  is assumed.
- AC-CTX-06: Synthetic tests cover profile/no-profile, preferences and avoidances, stale/cleared
  profile fields, achievement evidence, all hard constraints, no eligible activity, explanation
  stability, and current ranking compatibility. No real child profile or personal data enters Git.
- AC-CTX-07: Contract/ADR/privacy/persistence gates are explicitly satisfied before any durable
  child-level profile or history is implemented; otherwise the delivery remains session-scoped.

## Boundaries and risks

- No inference of a child's mental state, diagnosis, personality, ability, or preference from the
  drawing, narration, voice, or behavior. Only explicitly supplied, reviewable context is eligible.
- No changes to source image/AI understanding, catalog expansion by count alone, Gate A/B authority,
  provider calls, Firebase/S3/storage policy, authentication, or durable child-data writes under this
  plan's current session-scoped approval.
- No weakening of age, Montessori safety, readiness, prerequisites, material, supervision, or
  session-state requirements to force a recommendation.
- Risks include stale adult-entered context, biased/incomplete catalog labels, over-personalization,
  sensitive child profiling, and treating a proxy score as a fact. The plan favors transparent
  evidence and editable context over opaque model personalization.

## Verification and evidence plan

Keep the catalog coverage matrix, synthetic profile fixtures, expected rankings, reason-code review,
test results, and data-minimization decisions in FEAT-018/FEAT-020 feature-local evidence. Record the
catalog revision, source inputs, command/environment, timestamp, reviewer and limitations. Do not
store raw child records or sensitive profile values in Git.

## Approval record and remaining gates

This is a detailed workstream under FEAT-018
`INTEGRATED_CHILD_PROFILE_AND_RIG_QUALITY_PLAN_20260929.md`, which is the single owner-approval
artifact for the coordinated FEAT-018/020/030 increment. The integrated plan is approved; the exact
current SHA-256 and reconciliation are recorded in `../approvals/TASK_APPROVAL.md`. Session-only
contracts/resolver/UI work is authorized under that scope. Durable profile/history writes, auth,
consent and retention implementation remain excluded and require separate privacy/authorization
decisions. See `../../../../docs/adr/ADR-0010-session-scoped-child-learning-context.md` for the
accepted volatile-state/request boundary; existing contract ownership rules remain in force.
