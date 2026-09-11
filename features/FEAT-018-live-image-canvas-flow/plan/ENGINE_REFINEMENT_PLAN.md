# FEAT-018 revision 2 — ExperienceSpec engine and coherent off-screen journey

- Status: `APPROVED` for the P1 implementation slice only; P2/P3/P4/shared tasks remain pending approval
- Implementation status: `P1 COMPLETE (fixture-only); P2/P3/P4/shared pending`
- Scope boundary: fixture-first contracts and offline integration planning. No live provider, production API, Android release, cloud deployment, or real child data is authorized by this document.

## Problem and goal

Video and off-screen activity must be generated from one shared learning concept. A drawing about a butterfly must not lead to a video about insect anatomy and an unrelated activity about colour sorting merely because both are broadly related to butterflies.

The engine creates one versioned `ExperienceSpecV1` after Gate A:

```text
P2 observation
  -> confirmed semantic anchors
  -> one learning objective
  -> one approved activity template
  -> ExperienceSpecV1
  -> video/animation plan + off-screen activity plan
  -> fit validation
  -> Gate B
  -> handoff, gallery journey and feedback
```

The original drawing remains immutable. AI observations remain proposals until adult confirmation. P1 owns domain eligibility and curated activity templates; P3 and P4 consume the approved spec and must not select a different concept.

## Product invariants

1. Each session has one primary child anchor, one learning objective and one activity template after selection.
2. Video, original-art animation, off-screen activity and bridge sentence reference the same `ExperienceSpecV1` identity and version.
3. An activity keeps at least one confirmed semantic anchor from the drawing or narration, unless an adult explicitly corrects the anchor.
4. P1 hard age, readiness, material, supervision, safety and prerequisite rules run before ranking or media generation.
5. Media failure changes delivery mode only; it cannot change the approved objective, activity, template or off-screen handoff.
6. No provider, renderer or media adapter may invent Montessori pedagogy or replace an approved objective.
7. Original artwork and all derived artifacts retain source references, hashes and provenance.

## Proposed contracts — not frozen until approval

These names are proposals for the revision-2 contract freeze. They must be added to the shared registry only after review.

### `SemanticAnchorSetV1`

Provider-neutral, Gate-A-confirmed observations containing an anchor set ID/version, primary and optional secondary anchors, subject/action/visual-feature/story references, source claim IDs, confidence/uncertainty, adult confirmation/correction metadata, source artifact IDs and provenance. Original and normalized labels remain separate. It contains no age, readiness, eligibility or psychological claims.

### `LearningFocusV1`

The single selected learning direction: objective ID/version, selected anchor reference, child-facing goal, selection policy/version, adult/context provenance, and rejected alternatives/reason codes where audit requires them.

### `ActivityTemplateV1`

Curated, versioned activity template with supported objectives and anchors, age/readiness/material/supervision/safety rules, physical steps, interaction mode, personalization slots, fallback/accessibility guidance, production eligibility and provenance. LLM output cannot create or mutate a template at runtime.

### `ExperienceSpecV1`

The immutable source of truth for downstream planners. It links session/source-artifact identity, `SemanticAnchorSetV1`, `LearningFocusV1`, `ActivityTemplateV1`, video plan, animation plan, physical activity plan, `BridgeSentenceV1`, `ActivityFitEvaluationV1`, policy versions and a spec hash. A correction creates a new version and invalidates dependent plans.

### `ActivityFitEvaluationV1`

Deterministic validation with proposed weights: drawing relevance 30%, objective alignment 35%, video continuity 20%, Montessori/safety suitability 15%. It returns total score, threshold, ordered failures/warnings, evaluated spec/template/catalog versions. The proposed approval threshold is `80/100`; a different policy needs a decision record.

### `BridgeSentenceV1`

Child-facing transition from the video/animation to the off-screen activity. It references the selected anchor and objective and cannot introduce a new concept.

## Existing contract changes

- `RawUnderstandingResultV1` supplies claims to `SemanticAnchorSetV1`.
- `P1ContextV1` and `P1FilterResultV1` supply eligibility inputs and candidate identity.
- `IntegrationGateDecisionV1` locks objective, activity, template and spec versions.
- `LearningMediaRequestV1/ResultV1` carries spec/template identity through cache and fallback.
- `ArtAnimationPlanV1` references the spec and immutable source artwork.
- `ActivityHandoffV1` carries the approved spec and exact activity/objective identity.
- `FeedbackV1` records the same identity and spec version.

No existing contract may be widened silently. A breaking change requires a new version and migration fixture.

## Workstream tasks

### P1 — domain, templates and selection

| ID | Task | Deliverable / acceptance evidence |
|---|---|---|
| `FEAT018-P1-E1` | Build Activity Template Library | Versioned templates for supported objective families, with age/material/safety/supervision rules and provenance. |
| `FEAT018-P1-E2` | Select anchor and learning focus | Deterministically select one confirmed anchor and one objective after Gate A; unknown, conflicting and missing-context cases are typed. |
| `FEAT018-P1-E3` | Compile `ExperienceSpecV1` | One immutable spec links anchor, objective, template, activity plan, video plan and bridge sentence. |
| `FEAT018-P1-E4` | Implement fit validator | Deterministic score and reason codes; unrelated activity is rejected or blocked below threshold. |
| `FEAT018-P1-E5` | Extend Gate B and pilot pack | Gate B locks objective/activity/template/spec versions; pilot covers butterfly symmetry, mismatch, correction, stale and no-context cases. |

P1 also completes catalog promotion, ACT-0004 migration, 100-MVP validation and 20-golden evidence from `PERSON_1_DOMAIN.md`.

### P2 — structured observation and anchor evidence

| ID | Task | Deliverable / acceptance evidence |
|---|---|---|
| `FEAT018-P2-E1` | Enrich observation output | Subject, action, visual feature, story, uncertainty and source-claim references are available without changing provider identity. |
| `FEAT018-P2-E2` | Publish anchor candidates | Candidate anchors preserve original/normalized labels and provenance; P2 does not select objectives or activities. |
| `FEAT018-P2-E3` | Cover ambiguity and conflict | Fixtures cover unknown, ambiguous, contradictory and adult-corrected observations; unsupported claims cannot become anchors. |
| `FEAT018-P2-E4` | Add handoff compatibility | A versioned adapter maps `RawUnderstandingResultV1` to `SemanticAnchorSetV1` and rejects missing provenance. |

P2 model, provider and safety boundaries remain unchanged. P2-T4/T5 still require their own approval if implemented beyond the approved P2 scope.

### P3 — original-art renderer and visual continuity

| ID | Task | Deliverable / acceptance evidence |
|---|---|---|
| `FEAT018-P3-E1` | Consume `ExperienceSpecV1` | Renderer resolves only approved spec/template/objective versions and rejects stale or missing identity. |
| `FEAT018-P3-E2` | Map anchor to renderer profile | Visual hook highlights the confirmed source region/feature; original artwork remains the source layer. |
| `FEAT018-P3-E3` | Validate continuity and fallback | Invalid bounds, absent anchor, hash mismatch or protocol drift produces typed fallback without replacement art. |

P3 does not choose the learning objective or off-screen activity.

### P4 — coherent learning media and fallback

| ID | Task | Deliverable / acceptance evidence |
|---|---|---|
| `FEAT018-P4-E1` | Consume the approved spec | Video plan uses the same anchor/objective/template and cannot select an independent concept. |
| `FEAT018-P4-E2` | Update cache identity | Cache keys/results include objective/template/spec versions and source provenance. |
| `FEAT018-P4-E3` | Validate video continuity | A video teaching a different objective or dropping the anchor is rejected. |
| `FEAT018-P4-E4` | Preserve concept in fallback | Still+narration fallback keeps objective, activity identity, template and bridge sentence. |

P4 remains responsible for cache, media validation, generator adapter and fallback; pedagogical template ownership remains with P1.

### Shared integration, mobile and gallery

| ID | Task | Deliverable / acceptance evidence |
|---|---|---|
| `FEAT018-S-E1` | Freeze contract registry | JSON Schemas, positive/negative fixtures, compatibility report and producer/consumer table. |
| `FEAT018-S-E2` | Add engine state transitions | `EXPERIENCE_SPEC_COMPILED` and `EXPERIENCE_SPEC_VALIDATED`; stale/idempotent transitions are tested. |
| `FEAT018-S-E3` | Extend Gate B and handoff | Gate B and `ActivityHandoffV1` preserve exact spec identity. |
| `FEAT018-S-E4` | Refine gallery/session journey | Gallery shows original art, anchor, objective, video/animation, off-screen status and feedback from one session read model. |
| `FEAT018-S-E5` | Add continuity E2E | Butterfly symmetry, unrelated activity rejection, video/activity mismatch, missing anchor/context, fallback and stale spec cases. |

Shared work requires a separately approved integration allocation; it is not silently assigned to P3 or P4.

## Acceptance criteria for revision 2

- Butterfly → wings → symmetry → fold-and-print passes fit validation and Gate B.
- Butterfly → unrelated sorting activity is rejected or blocked below the approved threshold.
- Video and off-screen activity with different objectives are rejected before delivery.
- Missing anchor, missing adult context, stale template or mismatched objective blocks the spec.
- Cache hit, cache miss, provider failure and media fallback preserve objective/activity/template/spec identity.
- P3 animation uses original artwork and the confirmed anchor; no generated replacement is accepted.
- Gallery shows one continuous session journey from source drawing to off-screen activity and feedback.
- All handoffs carry contract name/version, exact identity/version, provenance and typed failure semantics.
- Existing standalone Sprint 1 tests remain green.
- No real child data, credentials, provider endpoint, production API or Android release work is included.

## Execution order and stop gates

1. Review and approve this plan revision and proposed contracts. **Completed for the P1 slice on 2026-09-09.**
2. Freeze JSON Schemas and migration fixtures.
3. P1 publishes catalog/template/provenance fixtures.
4. P2 publishes anchor candidate fixtures and adapter compatibility.
5. P1 compiles specs and fit-evaluation fixtures.
6. P3/P4 consume only approved specs.
7. Shared integration adds state, Gate B, gallery and fixture-only E2E.
8. Stop on identity mismatch, missing provenance, missing adult context, fit score below threshold, stale spec, unsafe media or source-hash mismatch.

P1 implementation may begin within the approved slice. P2/P3/P4/shared implementation remains blocked until its own scope and downstream contract handoffs are approved.

## Approval checklist

- [x] Contract names and versions accepted for the P1 slice.
- [x] One-anchor/one-objective/one-template session rule accepted for P1 spec compilation.
- [x] Activity Template Library ownership assigned to P1.
- [x] Fit weights and threshold approved for P1 fixture validation.
- [x] Gate B lock scope includes template/spec version for the P1 slice.
- [ ] Gallery read-model scope approved.
- [ ] Shared integration allocation approved separately.
- [ ] Existing exclusions remain unchanged.
