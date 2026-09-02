# Phase 7 - Retry and still+narration fallback

## Responsibility

This phase keeps a failed video generation from breaking the learning explanation. `RetryPolicy` limits re-generation attempts, while `StillNarrationFallback` resolves a reviewed still+narration asset using the same objective identity.

## Flow

```text
ValidationResult
  -> RETRY and retry_count < 1: generate once more
  -> FALLBACK or retry exhausted: find reviewed still+narration
      -> found: FALLBACK
      -> missing: BLOCK
```

## Invariants

- Retry is allowed at most once by default.
- A `BLOCK` or `FALLBACK` result is never retried.
- Fallback must match objective ID, version, locale, and age band.
- Fallback never changes the approved learning objective.
- No reviewed fallback asset means `BLOCK` with an explicit reason code.
