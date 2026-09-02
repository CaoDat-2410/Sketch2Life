# FEAT-005 Implementation Phases

## Purpose

This document defines the implementation order for Person 4's standalone learning-media POC. It is a planning artifact; it does not authorize implementation before the feature approval record is `APPROVED`.

## Scope

The POC owns:

- reviewed learning-asset metadata and fixture-local library lookup;
- cache-first resolution;
- provider-neutral generation brief and generator adapter;
- FFmpeg media inspection and frame sampling;
- Qwen3-VL content validation over sampled frames;
- retry, still+narration fallback, and typed outcomes;
- provenance, standalone demo, tests, and benchmark evidence.

The POC excludes FastAPI, PostgreSQL, S3, Redis/RQ, mobile playback, deployment, and E2E integration.

## Phase order

### Phase 1 - Project and documentation foundation

Create the feature-local implementation folders, configuration placeholders, fixture locations, README sections, and phase documentation. No model inference is performed.

### Phase 2 - Contracts and fixtures

Define versioned request/result schemas and synthetic fixtures for cache hit, cache miss, provider failure, invalid media, and still+narration fallback.

### Phase 3 - Library and cache-first resolver

Index reviewed assets by objective ID/version/locale/age band. Return `HIT` only for a valid reviewed asset; otherwise return `MISS`. A valid `HIT` must not invoke a generator.

### Phase 4 - Generation brief and provider adapter

Compile one approved learning objective into a bounded generation brief. Implement a mock provider first, then the Wan2.2 adapter behind the same interface.

### Phase 5 - Media validation

Use FFmpeg for media integrity checks and frame sampling at 0%, 25%, 50%, 75%, and 100%. Send sampled frames plus the objective/brief to the Qwen3-VL content validator.

### Phase 6 - Outcomes and fallback

Return `PASS`, `RETRY`, `FALLBACK`, or `BLOCK` with reason codes. Retry at most once. On video failure, return a reviewed still+narration asset without changing the objective identity/version.

### Phase 7 - Standalone runner and evidence

Provide cache-hit, cache-miss/pass, and generation-failure/fallback demos. Add unit/fixture tests, provenance output, and benchmark records.

### Phase 8 - Lightning AI validation

Run the mock and tests on CPU first. Then run Wan2.2 on a GPU Studio, validate generated MP4s, and record duration, profile, peak VRAM, generation time, retry rate, fallback rate, and OOM results.

## Runtime flow

```text
LearningObjective
  -> AssetLibrary
  -> CacheFirstResolver
      -> HIT: return reviewed asset
      -> MISS: compile GenerationBrief
          -> Generator (mock or Wan2.2)
          -> FFmpeg media check + frame sampling
          -> Qwen3-VL content validation
              -> PASS
              -> RETRY (maximum one retry)
              -> FALLBACK (reviewed still+narration)
              -> BLOCK
```

## Definition of done for the foundation phase

- The phase order and boundaries are documented.
- No provider credential or real child data is committed.
- The feature remains standalone and fixture-driven.
- Implementation remains blocked until `approvals/TASK_APPROVAL.md` is explicitly `APPROVED`.
