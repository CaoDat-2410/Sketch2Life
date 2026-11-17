# P2-T3 Phase B B3 implementation — internal diagnostic hook, runner, no-GPU tests

- Evidence ID: `EV-003-T3-08`
- Date: 2026-09-03
- Owner: Person 2
- Scope: implementation only. No dependency, `.vision.env`, GPU, model, or provider action was
  taken. B3 remains inside the already-approved bounded B1–B5 scope
  (`approvals/TASK_APPROVAL.md`); this is the code slice that follows the fixture-sourcing,
  raw-output-handling, metric-semantics, and execution decisions already recorded in
  `DECISIONS.md` ("P2-T3 Phase B B3 implementation decisions", 2026-09-03) and detailed in
  `evidence/notes/P2_T3_PHASE_B_B3_PREPARATION.md` (`EV-003-T3-07`).

## What changed

- `backend/src/sketch2life/infrastructure/ai/qwen_vision.py`: added an optional
  `on_raw_output: RawOutputHook | None = None` constructor parameter to `QwenVisionAdapter`.
  When supplied, it is invoked once with the raw provider string immediately after a generation
  call succeeds, before any parsing/classification happens inside the adapter. It is never wired
  into any default construction path, adds no field to `VisionUnderstandingResultV2` or any
  other public V1/V2 contract, and a hook exception is swallowed (`contextlib.suppress`) so a
  diagnostic failure can never turn a real understanding call into an uncaught exception. This is
  the one code change to the frozen adapter that the B3 preparation note (`EV-003-T3-07`)
  identified as necessary and called out for review.
- `backend/src/sketch2life/benchmark/vision_b3_mapping_study.py` (new, non-CLI, mirrors
  `vision_b2_preflight.py`'s discipline): `B3RawOutputMode` (`CLASSIFY_ONLY` default,
  `EPHEMERAL_CAPTURE` opt-in per run), `B3RawOutputCollector` (owns the hook; classifies raw text
  in memory and discards it by default; in `EPHEMERAL_CAPTURE` mode additionally writes it to an
  ignored `data/runtime/...` scratch file for the duration of classification and removes it in a
  `finally` that runs even when classification itself raises), `classify_raw_output` (pure,
  deterministic: `fenced`, `truncated`, `extra_key`, `invalid_enum` — independent flags that may
  overlap, e.g. an opened-but-never-closed fence is both `fenced` and `truncated`), a
  classifier-local-only `_detect_missing_required_field` helper (directly unit-tested, never
  returned by `classify_raw_output`, never a field on `B3RawOutputClassification`, so it cannot
  reach a report), eight deterministic geometric synthetic fixture recipes (distinct shading
  patterns over the same proven-safe 160×160 canvas already used by B2's preflight image, never a
  real drawing, regenerated into ignored scratch and deleted after each run, never written under
  `fixtures/vision-b4/**`), and `run_b3_mapping_study` (exactly one `adapter.understand` call per
  fixture, no retry of a mapping failure, per-run latency/VRAM sampling reusing the same
  `_VramSampler` pattern as B2, and a safe `B3MappingStudyReport` aggregate carrying only typed
  outcome counts, the four permitted raw-derived counts with `attempted_runs` as the shared
  denominator, and `known_policy_trigger_rate="NOT_APPLICABLE"` — never raw text, a prompt, or a
  path).
- Tests: `backend/tests/unit/test_qwen_vision_adapter.py` gained 5 focused tests for the hook
  (invoked on success, invoked on schema-invalid failure, not invoked before generation returns,
  a hook exception is swallowed and the real result is still returned, no hook/raw-output
  artifact ever appears in the serialized V2 result). `backend/tests/unit/test_vision_b3_mapping_study.py`
  (new) covers: the classifier (plain/fenced/unclosed-fence/unbalanced-JSON/extra-key/invalid-enum,
  including overlapping flags), the collector (`CLASSIFY_ONLY` never writes a file;
  `EPHEMERAL_CAPTURE` writes-then-deletes, including when classification raises; stale
  classifications cannot leak between fixtures), fixture generation (eight distinct images, each
  independently verified against the real P2-T1 validator), the runner (exactly one call across
  eight fixtures with no retry even under repeated mapping failure, classification
  overlap/denominator against `attempted_runs`, the report never carrying injected raw-text
  markers, `known_policy_trigger_rate` always `NOT_APPLICABLE`, scratch/capture cleanup on both
  success and an adapter exception, and the same unsafe-scratch-directory/unsafe-fixture-path
  guards B2 already established, mirrored rather than imported).

## Correction — 2026-09-03: two blocking review findings fixed

A review of the above pass found two gaps in `run_b3_mapping_study` before any real execution,
fixed the same day (documentation-only correction to this note; the code fixes are below):

1. **Exact fixture-count invariant.** `build_fixtures` was trusted to return exactly eight image
   paths; a builder bug returning fewer or more would have silently run against the wrong count
   with no rejection. `run_b3_mapping_study` now raises `UnexpectedFixtureCountError` (new,
   module-local — not a public V1/V2 contract token) immediately after `build_fixtures` returns
   and before any P2-T1 validation or adapter call, if `len(image_paths) != _FIXTURE_COUNT`.
2. **Fail closed if the raw-output hook is not wired.** If a caller ever constructed the adapter
   without `on_raw_output=collector.hook`, a `SUCCEEDED`/`PROHIBITED_CLAIM_DETECTED`/schema-invalid
   (`OUTPUT_MAPPING_FAILED`/`DUPLICATE_OBSERVATION_ID`/`REFERENCE_INTEGRITY_VIOLATION`) result —
   every outcome that can only be reached after the adapter's generation call already returned raw
   text — would silently carry no classification, understating every raw-derived bucket rate
   without any signal that this had happened. `run_b3_mapping_study` now raises the new
   `B3RawOutputHookNotWiredError` (module-local, never carries raw text — there is none to
   classify when this fires) the moment such a result has no classification. Runtime/input
   failures that legitimately never reach generation (`INPUT_NOT_VALIDATED`, model/device
   unavailable, timeout, provider failure) remain permitted to have no classification. Both new
   error paths still run inside the function's existing `try`/`finally`, so fixture and
   (`EPHEMERAL_CAPTURE`) capture scratch cleanup still occurs on every raise.

Seven new focused tests were added to `test_vision_b3_mapping_study.py`: fewer-than-eight and
more-than-eight fixture paths are rejected before any adapter call (with scratch cleanup
asserted, including the capture directory in `EPHEMERAL_CAPTURE` mode); a `SUCCEEDED` result and
a schema-invalid mapping-failure result each fail closed when scripted with no observed raw
output (asserting `adapter.calls == 1`, i.e. failing on the very first offending fixture, and
scratch cleanup including the capture directory); a legitimately-raw-output-free failure
(`MODEL_LOAD_FAILED`) is confirmed to remain allowed to have no classification across all eight
fixtures.

## Correction 2 — 2026-09-03: nested `extra_key` detection and error-wording precision

A further review found two remaining gaps, fixed the same day:

1. **`extra_key` only checked the top-level collection keys.** V2's candidate contracts
   (`EntityCandidateV1`/`ActionCandidateV1`/`RelationCandidateV1`/`ThemeCandidateV1`/
   `AmbiguousRegionCandidateV1`) and the shared `ObservedTextV1`/`TextLanguageDeclarationV1`
   nested types are all `extra="forbid"`, so an unknown key at any of those levels also maps to
   `VISION_SCHEMA_INVALID`/`OUTPUT_MAPPING_FAILED` on a real call, but `classify_raw_output` never
   looked past the top level. A new `_detect_nested_extra_key` walks each candidate object's own
   allowed-key set (mirroring the real contract's fields, not merely its required ones — e.g.
   `actor_ref`/`object_ref` are optional but still legal on `ActionCandidateV1`), each candidate's
   single `ObservedTextV1`-typed field (`label`/`predicate`/`note`), and that field's nested
   `language` (`TextLanguageDeclarationV1`). `extra_key` is now `not set(parsed).issubset(top_level)
   or _detect_nested_extra_key(parsed)`. A missing field or a field of the wrong type is never
   treated as an unknown key (only a key that should not exist at all); this remains fully
   independent of the other three flags and can still overlap with them (e.g. fenced + extra_key).
2. **`B3RawOutputHookNotWiredError`'s wording overclaimed the cause.** It previously stated the
   *only* explanation for a missing classification was the adapter being constructed without
   `on_raw_output=collector.hook`. A swallowed hook exception, a capture-write failure, or a
   classifier failure inside the hook would look identical from the runner's perspective. Both the
   exception's docstring and the runner's raise message (and `run_b3_mapping_study`'s own
   docstring) now say the diagnostic hook was "unavailable or failed for this call," naming
   omitted wiring as the most likely but not the only cause, without ever exposing raw text.

Eight new focused tests were added to `test_vision_b3_mapping_study.py`: an unknown
candidate-level key is flagged; an unknown key nested inside `label.language` is flagged; an
unknown key directly on the `label`/`ObservedTextV1` dict itself is flagged; a fully valid,
populated payload across all five collections (entities/actions/relations/themes/
ambiguous_regions) with correct nested text/language shapes is *not* flagged; a missing field or
a wrong-type field is confirmed never treated as an extra key; and three new fail-closed tests
cover `PROHIBITED_CLAIM_DETECTED`, `DUPLICATE_OBSERVATION_ID`, and
`REFERENCE_INTEGRITY_VIOLATION` each raising `B3RawOutputHookNotWiredError` with exactly one
adapter call and full scratch cleanup (including the capture directory for the
`REFERENCE_INTEGRITY_VIOLATION` case, run under `EPHEMERAL_CAPTURE`).

## Local validation (all run from `backend/`, no GPU)

- Focused: `pytest tests/unit/test_vision_b3_mapping_study.py tests/unit/test_qwen_vision_adapter.py -q` — all passed.
- Full backend suite: **475 passed, 5 skipped** (480 total; up from the 467 passed/5 skipped
  recorded after Correction 1 — the 8-test delta is exactly this round's P1/P2 coverage; baseline
  before the original B3 implementation pass was 427 passed, 5 skipped per `EV-003-T3-07`). Zero
  failures, zero errors.
- `ruff check .` — all checks passed.
- `mypy --strict src` — success, no issues found in 52 source files.
- From the repository root: `validate_harness.py` → `HARNESS_VALID`; `validate_repository_security.py`
  → `REPOSITORY_SECURITY_VALID`; `validate_architecture.py` → `ARCHITECTURE_VALID`;
  `validate_skeleton.py` → `SKELETON_VALID`; `git diff --check` → clean (no output).

## Confirmations

- No GPU, model, dependency, `.vision.env`, provider, or cloud action occurred; no B4/B5 work;
  no API/UI/CLI work.
- No raw model output was ever written, logged, or persisted by this change or its tests — the
  new tests assert this structurally (no capture file in `CLASSIFY_ONLY`, the capture file is
  removed even when classification raises, and the report/serialized result never contain
  injected raw-text markers).
- No public V1/V2 contract field, error token, or enum value was added, renamed, or removed; the
  hook is a private adapter-construction parameter only. `VisionProfileIdV2`, the frozen greedy
  `VisionDecodingV1`, and the lossless-fence-unwrap-only repair rule are all unchanged.
- No commit, push, pull request, or approval-record edit was made. `CONTEXT.md`, `DECISIONS.md`,
  and `evidence/README.md` were left exactly as found (not staged, not edited by this task); this
  note is itself local-only under the already-gitignored `evidence/notes/` directory.
