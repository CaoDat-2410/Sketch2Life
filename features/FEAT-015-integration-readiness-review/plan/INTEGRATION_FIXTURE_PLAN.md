# Integration Fixture v1 — Plan

- Status: REVIEW
- Plan revision: 1
- Implementation status: DONE
- Owner: Integration Sprint allocation pending
- Feature: FEAT-015 integration-readiness-review
- Date: 2026-09-05
- Approval: TASK_APPROVAL.md approved 2026-09-05

## Goal

Define one immutable, synthetic integration fixture package that lets P1, P2, P3 and P4 test the same end-to-end scenario through an offline vertical slice. The fixture proves contract compatibility, provenance, Gate A/B behavior, deterministic Montessori filtering, original-art preservation, learning-media cache/fallback behavior, and activity handoff without live providers, mobile production runtime, database, queue, or real child data.

## Decisions already fixed

- P1 is the canonical authority for activity and learning-objective IDs and versions.
- Gate A is mandatory before Montessori filtering.
- ASR and vision disagreement remains visible as two claims with provenance; it requires adult confirmation or correction.
- If P1 finds no eligible activity, the flow requests additional explicit context and evaluates again.
- The first slice uses fixtures and fake providers through activity handoff.
- P3 supports all planned asset types, but v1 executes `WHOLE_DRAWING` first.
- P3 assets remain fixture/demo-only; no asset is applied to the mobile product in this plan.
- P4 first exercises a reviewed cache hit; cache miss, retry and still+narration fallback are separate cases in the same package.

## Scope

### In scope

1. Versioned package manifest and synthetic-data declaration.
2. Immutable drawing/audio references, hashes and media-validation expectation.
3. Expected P2 ASR, vision and fused raw-understanding artifacts, including an explicit disagreement case.
4. Explicit adult/session context consumed by P1: age, readiness, completed activities, materials, supervision and policy flags.
5. Gate A confirmation/correction fixtures with actor and expected-session-version metadata.
6. P1 candidate filtering expectations using canonical activity/objective references and reason traces.
7. Gate B approval expectation locking both activity and learning-objective ID/version.
8. P3 `WHOLE_DRAWING` asset manifest and animation-plan expectation, including source provenance and SHA-256.
9. P4 cache-hit, cache-miss, validation failure, retry, fallback and block expectations.
10. Activity Bridge handoff and feedback expectation.
11. Contract round-trip, negative, stale-version and failure-path acceptance criteria.
12. Evidence records under this feature's `evidence/` directory.

### Out of scope

- Live Whisper, Qwen3-VL, Lightning, Runpod or Wan2.2 calls.
- Android UI, FastAPI routes, PostgreSQL, S3, Redis/RQ and deployment.
- Real child media or production account data.
- Product visual approval or copying fixture assets into `assets/applied/`.
- Model-quality claims or production eligibility of P1 provisional catalog records.
- P2 fusion implementation, P3 bridge implementation or P4 exception handling; those require their own approved implementation slices.

## Package layout proposal

```text
integration-fixture-v1/
  manifest.json
  media/
    drawing.svg
    narration.wav
  expected/
    media-validation.json
    asr-result.json
    vision-result.json
    raw-understanding.json
    gate-a-confirmation.json
    p1-context.json
    p1-filter-result.json
    gate-b-approval.json
    art-asset-manifest.json
    art-animation-plan.json
    learning-media-cache-hit.json
    learning-media-cache-miss.json
    learning-media-fallback.json
    activity-handoff.json
    feedback.json
  provenance/
    source-register.json
```

The exact repository location must be approved during contract review. The package must be immutable by convention: tests read it, adapters produce derived outputs elsewhere, and no test edits the source fixture in place.

## Required manifest fields

`manifest.json` must contain:

- `fixture_id` and `fixture_version`;
- `synthetic_data: true`;
- source media artifact IDs, versions, relative references and SHA-256 hashes;
- contract names and versions used by every expected artifact;
- P1 activity/objective canonical references and versions;
- expected scenario labels, including agreement/disagreement and cache/fallback case;
- creation timestamp, fixture author and review status;
- provenance references for every derived expected artifact.

Absolute machine paths, credentials, provider endpoints and raw model/provider logs are forbidden.

## Scenario set

The package should define at least these scenarios, either as manifest cases or separate case manifests:

1. `happy_cache_hit`: media PASS, ASR/vision agree, Gate A confirms, P1 returns an eligible activity, Gate B approves, P3 validates whole-drawing asset and emits DRAW_REVEAL, P4 returns reviewed cache HIT, then activity handoff and feedback.
2. `modality_conflict_requires_gate_a`: ASR and vision disagree; both claims remain in raw understanding; filtering and media work do not start until Gate A correction.
3. `no_eligible_activity_add_context`: P1 rejects the first context for age/readiness/material/supervision; the flow requests explicit additional context and succeeds or records a typed no-result.
4. `cache_miss_fallback`: P4 cache MISS, fake generation/validation fails in a bounded way, reviewed still+narration fallback retains the same approved objective/activity identity.
5. `asset_integrity_failure`: changed drawing bytes or invalid provenance causes P3 loader rejection and whole-drawing fallback where policy permits; original source remains unchanged.
6. `stale_gate_or_completion`: Gate A, Gate B or worker completion uses an old expected session version and is rejected without mutating newer state.
7. `invalid_media_recap`: corrupt/unsupported image or silent/unreadable audio produces RECAPTURE; P2 adapters are not called.
8. `blocked_learning_media`: P4 reports BLOCK for prohibited or unsafe generated media; the system does not present blocked media and preserves the approved activity handoff decision.

## Contract and identity rules

- Every boundary uses the common envelope where applicable: contract name/version, session ID, expected session version, artifact ID/version, source artifact IDs, created-at and provenance.
- P1 activity and objective references are opaque canonical IDs; adapters may add a display label but must not rewrite the ID.
- Activity and learning-objective versions are separate fields and must be approved together at Gate B.
- Gate A creates a new confirmed-meaning artifact version; downstream artifacts reference that version.
- Raw P2 labels are preserved. Any normalized taxonomy mapping is a separate derived field with mapping version and confidence/status.
- P3 references source art and never replaces it with generated art. `WHOLE_DRAWING` is the v1 execution path; future asset types remain schema-valid but unrequired by v1.
- P4 artifacts reference the approved objective/activity identity and must reject mismatched brief/result identity before playback.
- Unknown, stale, duplicate, missing or mismatched versions fail closed with typed reason codes.

## Implementation steps after approval

1. Review and freeze the manifest schema and common envelope with all four workstream owners.
2. Select or create a synthetic drawing/audio pair; compute hashes; record source provenance.
3. Select a P1 activity/objective record and record its exact canonical IDs/versions without changing production eligibility.
4. Author expected P2 outputs before any live-model output is observed; include one agreement and one conflict case.
5. Author explicit adult context, Gate A confirmation/correction and Gate B approval fixtures.
6. Author P3 asset manifest/plan expectation and verify source hash/provenance fields.
7. Author P4 cache/fallback expected results, including stable identity and reason codes.
8. Build a read-only fixture loader and schema validators in the approved integration workstream.
9. Run producer/consumer round-trip checks for Python contracts, JSON Schema/Pydantic, and TypeScript/PixiJS bridge types.
10. Run the offline vertical slice with in-memory ports and fake providers.
11. Store command output, environment, fixture hashes, result hashes, failures and interpretation in evidence.
12. Review the integration slice, update decisions/status, and request the next approval before adding runtime/API/mobile wiring.

## Acceptance criteria

- [ ] Package is versioned, synthetic, immutable and contains no secret, absolute path or real child data.
- [ ] All source and derived artifacts have traceable IDs, versions, hashes and provenance.
- [ ] P1 canonical activity/objective IDs and versions survive every boundary unchanged.
- [ ] Gate A is required; unconfirmed or stale meaning cannot reach P1.
- [ ] ASR/vision conflict preserves both claims and blocks downstream work until adult resolution.
- [ ] Missing eligibility context causes an explicit context-needed result and a controlled re-evaluation.
- [ ] P1 hard rules run before any selector or learning-media generation.
- [ ] Gate B locks both activity and objective references and rejects stale/mismatched approval.
- [ ] P3 validates the WHOLE_DRAWING asset manifest/hash and preserves the original through DRAW_REVEAL or fallback.
- [ ] P4 cache HIT never calls generation; cache MISS and bounded fallback retain objective/activity identity.
- [ ] Invalid media, stale completion, duplicate completion, blocked media and asset-integrity failures fail safely.
- [ ] A successful fixture run ends in an Activity Bridge handoff and feedback record.
- [ ] All existing standalone workstream checks remain passing; skips and limitations are recorded.
- [ ] Evidence is reproducible and stored under FEAT-015.

## Verification plan

- P1: run domain, Golden and console validators; use the 74 Golden cases as regression oracle.
- P2: run offline pytest, schema round-trip and deterministic fusion/conflict fixtures; no live provider claim.
- P3: run typecheck, Vitest, asset-manifest/hash tests, demo build and bridge schema-negative tests.
- P4: run pytest/unittest, cache spy, generation exception/timeout, identity mismatch, FFmpeg and fallback tests; keep mock and real-provider evidence separate.
- Integration: run all eight scenario cases in an in-memory application harness, assert transition history and artifact provenance, then run merged-tree CI after the approved integration branch is created.
- Security/harness: run `python tools/validate_harness.py --feature features/FEAT-015-integration-readiness-review`, `python tools/validate_repository_security.py`, and architecture/team-allocation validators before any commit/push.

## Risks and mitigations

- Contract drift: freeze schema versions and require round-trip fixtures.
- False semantic mapping: preserve raw labels and require adult Gate A.
- P1/P4 identity mismatch: use P1 canonical references and reject mismatches.
- Original-art loss: hash source bytes and require whole-drawing fallback.
- Provider failure: typed errors, bounded retries and reviewed fallback.
- Fixture coupling: keep P1-P4 fixtures standalone and add a separate immutable integration package.
- Visual gate bypass: keep fixture assets in test/demo paths and require approval before app application.

Revision-2 implementation is approved and complete for the offline scope. Any broader runtime/API/mobile/provider scope remains blocked until a separate plan and approval under ADR-0006.

## Implementation evidence

- Fixture package: `fixtures/integration-fixture-v1/`.
- Loader/harness: `src/integration_fixture/loader.py`, `src/run_fixture.py`.
- Tests: `tests/test_integration_fixture.py`.
- Result: 6 tests passed; happy, conflict and cache-fallback smoke scenarios completed.
- Scope limitation: fixture validation and transition simulation only. P2 fusion, P3 bridge, P4 provider exception handling, API, Android, database, queue and live providers remain out of scope.

## Revision 2 approved scope

Plan revision 2 adds offline integration adapters and orchestration around the existing immutable fixture: P2 deterministic ASR/vision fusion with conflict preservation and Gate A requirement; Gate A confirmation/correction and Gate B activity/objective approval with expected-session-version checks; P1 adapter consuming only confirmed meaning plus explicit context; P3 whole-drawing asset bridge validating source bytes/provenance before DRAW_REVEAL; P4 cache-first resolver with identity checks and bounded fallback/block outcomes; and an in-memory offline flow with traceable transitions.

This revision does not authorize live providers, production API/mobile work, Android release, database/storage/queue wiring, product asset application, or real child data.

## Revision 2 implementation evidence

- `src/integration_fixture/flow.py` implements the approved offline adapters and in-memory flow.
- `tests/test_integration_flow.py` covers fusion/conflict, Gate A/B, P1 filtering, asset bridge and P4 media outcomes.
- Revision 2 result: 15 tests passed.
- Revision 2 remains limited to synthetic fixtures and fake/in-memory behavior; runtime provider/API/mobile work is not implemented.


## Eight-scenario execution evidence

- `run_named_scenario` now executes all eight approved scenario cases through the offline adapters, including tamper and stale-version branches.
- Latest result: 23 tests passed.
- All eight outcomes are typed and preserve the approved P1 identity where a handoff is retained.
