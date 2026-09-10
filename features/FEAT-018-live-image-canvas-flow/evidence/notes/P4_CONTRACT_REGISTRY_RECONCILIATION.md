# FEAT-018 Person 4 contract registry reconciliation

Status: `P4 RECONCILIATION RECORDED`  
Scope: `FEAT018-P4-01`  
Date: 2026-09-10

## Authority

The FEAT-018 contract freeze is the semantic boundary for this work. The
authoritative implementation location is:

```text
backend/src/sketch2life/contracts/schemas/
```

Person 4 must not create a second schema package with different names or
versions. Any new media contract must be added to the canonical backend schema
location and accompanied by positive/negative fixtures and a compatibility
review.

## P4 registry

| Contract | Version | Producer | Consumer | Current source-of-truth | P4 decision |
|---|---:|---|---|---|---|
| `SourceMediaReferenceV1` | 1.0 | P2 | backend/mobile/P1/P3/P4 | FEAT-018 contract freeze; backend implementation to be verified during shared contract work | Consume unchanged; preserve `artifact_ref`, availability status, and SHA-256 rules |
| `MediaValidationResultV1` | 1.0 | P2 | backend/mobile | `backend/src/sketch2life/contracts/schemas/media_validation.py` | Consume unchanged; `RECAPTURE` stops inference |
| `PixiArtAssetManifestV1` | 1.0 | P3 | renderer/mobile/P4 boundary | FEAT-018 contract freeze; P3 runtime/schema work is separate | Reference only; P4 does not redefine renderer fields |
| `ArtAnimationPlanV1` | 1.0 | P3 | renderer/mobile/P4 boundary | FEAT-018 contract freeze; P3 runtime/schema work is separate | Reference only; preserve plan/source identity |
| `LearningMediaRequestV1` | 1.0 | shared/P1-Gate B boundary | P4 | Named by FEAT-018 freeze; no canonical backend schema currently present | Do not implement until canonical schema fields are frozen |
| `LearningMediaResultV1` | 1.0 | P4 | P3/mobile | Named by FEAT-018 freeze; no canonical backend schema currently present | Do not implement until canonical schema fields are frozen |
| `ActivityHandoffV1` | 1.0 | P1/shared | mobile/offscreen activity | FEAT-018 contract freeze; shared integration ownership | P4 preserves identity; does not own handoff orchestration |
| `FeedbackV1` | 1.0 | shared | mobile/evidence | FEAT-018 contract freeze; shared integration ownership | P4 emits only compatible evidence references |

## Required request invariants

When the canonical P4 request is frozen, it must carry the transport-boundary
fields required by the shared freeze:

```text
session_id
expected_session_version
request_id
idempotency_key
```

The media identity must bind the exact activity/objective/renderer IDs and
versions. A cache key must never contain raw image bytes, provider output,
credentials, signed URLs, or personal metadata.

## Required result invariants

`LearningMediaResultV1` must preserve the exact identity/version tuple across
cache hit, cache miss, timeout, invalid media, and fallback. It must expose the
cache status, `generation_called`, provenance, and a typed failure or fallback
reason. It must not silently substitute another activity or objective.

## Finding and next action

The existing backend contains `MediaValidationResultV1`, but it does not yet
contain canonical `LearningMediaRequestV1` or `LearningMediaResultV1` schemas.
Therefore this card records the registry and boundary without inventing a
parallel P4 contract. The next approval/reconciliation action is to add the
canonical P4 schemas under the backend contract authority, or record an
explicit versioned decision identifying where they will live.

No provider, GPU, database, cloud storage, mobile credential, or real child
data is required for this reconciliation.
