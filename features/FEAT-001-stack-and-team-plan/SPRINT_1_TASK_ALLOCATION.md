# Detailed Sprint 1 task allocation

- Status: PROPOSED - requires approval with FEAT-001 plan revision 3 and each owning feature plan
- Planning date: 2026-08-26
- Basis: ADR-0006, current system baseline, source register, and the user-provided P2 task list
- Target workload: five bounded task cards per person; a provisional 10 points per person / 40 points total. Point estimates for Persons 1, 3, and 4 are planning estimates, not measured delivery commitments.

## Rules applying to every person

Each workstream must publish a versioned synthetic fixture manifest, a versioned output contract, a local standalone runner/harness, positive and negative/failure evidence, and a short Integration Sprint compatibility note. A workstream cannot wait for or call another person's live server.

No person may use real child data, provider/mobile credentials, Firebase Storage/Firestore/Realtime Database, direct mobile-to-provider/S3 calls, or unapproved product visuals. Original/derived artifact provenance is mandatory.

## Shared first checkpoint: contract review

Before the task cards begin, all four people review naming/version conventions, synthetic-data declaration, artifact/source references, provenance envelope, typed failures, and fixture locations. This is a shared review, not a fifth person's workstream. Once the examples are accepted, each stream develops independently.

## Person 1 - BA / Montessori domain (10 proposed points)

| Card | Work | Deliverable and acceptance evidence |
|---|---|---|
| P1-T1 | Define `ActivityCatalogV1` and `LearningObjectiveV1` | Versioned schemas plus 20-30 synthetic/reviewable activity records; every record has ID/version, age/readiness, materials, steps, safety information, and objective. |
| P1-T2 | Define prerequisite and safety/material rule vocabulary | Versioned rule fixture set covering hard/soft prerequisite, safety, supervision, material availability, and no-valid-activity outcomes. |
| P1-T3 | Create positive/negative decision fixtures | Expected candidate validity/reason for age, readiness, prerequisite, safety, material, inactive/review status, and empty-result cases. |
| P1-T4 | Build deterministic rule harness | Local runner evaluates the fixtures without AI/database/mobile and proves hard constraints execute before any selector. |
| P1-T5 | Publish acceptance/traceability pack | Traceability matrix from catalog/rules to future recommendation and Gate B contract; locks activity and learning-objective IDs/versions together conceptually, without a UI/runtime. |

**Not owned:** recommendation ranking runtime, Gate B UI, FastAPI/backend wiring, data persistence.

## Person 2 - AI understanding (10 points)

| Card | Work | Deliverable and acceptance evidence |
|---|---|---|
| P2-T1 | Validate drawing and narration input quality | Deterministic `PASS | RECAPTURE` result with stable reasons for corrupt/unsupported/too-dark/blurred/cropped images and unreadable/silent/invalid audio; original hashes unchanged. |
| P2-T2 | Whisper large-v3-turbo adapter | Provider-neutral `AsrResultV1`: transcript, language, segments, quality, source-audio reference, provenance, and typed errors; fixture fake first. |
| P2-T3 | Qwen3-VL structured drawing adapter | Strict `VisionUnderstandingResultV1`: entities, actions, relations, themes, ambiguity/uncertainty, image reference, provenance; never a free-text output contract. |
| P2-T4 | Deterministic fusion and conflict detection | `RawUnderstandingResultV1` preserves both modalities, support map, conflicts, uncertainty, and provenance; it is never canonical meaning. |
| P2-T5 | CLI and evaluation harness | Around 20 synthetic fixture pairs; schema validity, recapture counts, ASR WER/CER, entity/action F1, labeled-conflict metrics, and p50/p95 latency. |

**Order:** `P2-T1 -> (P2-T2, P2-T3) -> P2-T4 -> P2-T5`. With one owner, execute T2 then T3; they can be parallel only after contract review and only with fixtures.

**Not owned:** Gate A UI/confirmation, session/job orchestration, FastAPI API integration, real child-data model evaluation.

## Person 3 - original-art animation (10 proposed points)

| Card | Work | Deliverable and acceptance evidence |
|---|---|---|
| P3-T1 | Define drawing/scene/motion/playback contracts | Versioned synthetic drawing manifest, `ArtAnimationPlan`/motion/event/error schemas, source/crop/mask provenance and bounds rules. |
| P3-T2 | Build standalone PixiJS/GSAP fixture player | Local player loads valid fixture plans without React Native capture or a backend, emitting validated playback events. |
| P3-T3 | Implement Motion DSL and `DRAW_REVEAL` | Deterministic `DRAW_REVEAL`, transform, camera/highlight primitives; invalid target, duration, or bounds is rejected before playback. |
| P3-T4 | Preservation validator and fallback | Pixel/source/provenance checks; segmentation/rig failure falls back to whole-drawing reveal, transform-only motion, or still rather than regenerated art. |
| P3-T5 | Performance and visual evidence harness | Startup, FPS, memory, playback error, and fallback measurements on a synthetic fixture/device matrix, plus Integration Sprint bridge note. |

**Not owned:** the complete Android application, capture, authentication, Gate A/B screens, backend calls. Product visual assets cannot be applied without the separate asset-review gate.

## Person 4 - learning media (10 proposed points)

| Card | Work | Deliverable and acceptance evidence |
|---|---|---|
| P4-T1 | Define cache/request/result/validation contracts | Versioned synthetic `LearningMediaRequestV1`, reviewed-cache asset record, result, provenance, validation, and fallback schemas. |
| P4-T2 | Implement cache-first resolver | Fixture-local cache double proves an approved matching asset is selected before any generation request. |
| P4-T3 | Implement provider-neutral generation adapter | Fixture fake and typed request/result/error mapping for a video generator; no session state, provider credentials, or mobile dependency. |
| P4-T4 | Validate media and build still+narration fallback | Invalid, timeout, unsafe, corrupt, or validation-failed clip produces a reviewed still+narration fallback without altering activity/objective identity. |
| P4-T5 | Standalone benchmark/report | Quality/validation coverage, latency, estimated cost, cache hit/miss, retry/fallback/failure rate, provenance, and Integration Sprint compatibility note. |

**Not owned:** backend/session orchestration, PostgreSQL/S3/Redis/RQ implementations, deployment, E2E, or ownership of the physical activity UI.

## Sprint 1 exit and cross-review

At the end of Sprint 1, review the four published contracts against synthetic fixtures, run every standalone harness, and inspect failure/fallback evidence. Do not wire the components together yet. The outcome is a contract-freeze candidate and an evidence-backed estimate for the Integration Sprint.

## Deferred Integration Sprint - deliberately unassigned now

The following are a separate backlog and must receive a fresh, balanced allocation after Sprint 1 evidence is reviewed:

- Android capture, waiting, Gate A, Gate B, experience, Activity Bridge, and feedback flows;
- backend HTTP commands, session state machine, jobs, auth/authorization, PostgreSQL, S3-compatible artifacts, Redis/RQ, and provider adapters;
- cross-component contract generation/round-trip, stale-version behavior, telemetry/redaction, deployment, device verification, and fixture-only E2E.

This is intentionally not assigned to Person 3 or Person 4 by default. The workload must be sized from actual Sprint 1 contract complexity, benchmark data, and team capacity.
