# FEAT-005 standalone learning media plan

- Status: AWAITING_APPROVAL
- Plan revision: 2
- Implementation status: NOT_STARTED
- Owner: Person 4

## Scope

Learning-asset cache contract, cache-first resolver, provider-neutral video-generation adapter, video validation, still+narration fallback, standalone fixture runner, artifact provenance output, and quality/latency/cost benchmark. Backend/session/storage/queue/deployment/E2E integration is excluded.

## Acceptance criteria

- [ ] Reviewed cache is checked before real generation.
- [ ] Video generation/validation failure produces a valid still+narration fallback.
- [ ] Request/result contracts preserve objective/activity/media identity and artifact provenance.
- [ ] Invalid, timeout, unsafe, and corrupt-media fixtures produce typed fallback outcomes.
- [ ] Fixture benchmarks record quality, latency, cost, cache-hit behavior, and failure rate.
- [ ] The runner executes without FastAPI, PostgreSQL, S3, Redis/RQ, mobile, or another Sprint 1 workstream.

## Sprint 1 output contract

- Versioned learning-media request/result and validation schemas.
- Cache-hit, cache-miss, provider-failure, invalid-media, and fallback fixtures.
- Integration compatibility note for later storage/job/orchestration wiring.

Implementation is blocked until this plan is approved.
