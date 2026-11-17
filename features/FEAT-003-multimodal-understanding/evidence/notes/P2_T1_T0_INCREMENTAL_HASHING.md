# P2-T1 maintenance — T0 incremental source hashing

- Evidence ID: EV-003-T1-T0-01
- Date: 2026-09-10
- Task: FEAT-003 P2-T1 maintenance, approved 2026-09-10
- Type: implementation and offline validation
- Environment: local Windows checkout, Python 3.12.10, backend `.venv`; no GPU, provider,
  network call or dependency install

## Change

`_source_reference` in `backend/src/sketch2life/application/services/media_validation.py`
previously computed `sha256(path.read_bytes())`, loading the entire source into memory before
hashing. It now hashes through a new module-private `_file_digest` helper that reads the file in
fixed-size chunks of `_HASH_CHUNK_BYTES` (1 MiB), matching the existing in-repository idiom in
`backend/src/sketch2life/infrastructure/ai/qwen_vision.py`.

The `try`/`except OSError` structure and the `MISSING`/`UNREADABLE` mapping are unchanged;
`path.open("rb")` raises the same `OSError` subclasses that `path.read_bytes()` raised.

Scope: this is the whole change. No contract, schema, enum, policy threshold, limit, decoder,
inspector default, adapter, prompt, profile, dependency, fixture or benchmark was modified.

## Compatibility verification

An independent baseline of the serialized `MediaValidationResultV1` was captured **before** the
change, from the previous whole-file implementation, over seven deterministic cases. The
post-change implementation was then run against the identical fixtures and compared to that
stored baseline — not to itself.

| Case | Serialized result | Provenance SHA-256 |
|---|---|---|
| `pass-both-modalities` | identical | identical |
| `small-dark-silent` | identical | identical |
| `corrupt-both` | identical | identical |
| `missing-both` | identical | identical |
| `empty-image` | identical | identical |
| `multichunk-image` (3,072,000 bytes) | identical | identical |
| `directory-as-image` (`UNREADABLE`) | identical | identical |

Image digests also matched independently computed `sha256(file_bytes)` for all eight fixture
files, including the empty file and the multi-chunk file.

**Digest and serialized-provenance compatibility: PASSED.** The provenance hash is the value the
benchmark helpers record as `validation_artifact_sha256` via
`_sha256_text(result.model_dump_json())`, so this result is what keeps existing validation
provenance stable. The canonical PASS fixture hashes to
`cded7b49413310fe54232ca793693db7d31db999b381908fff4c6521f9dbf5e5`, and that value is asserted
directly in the test suite.

## Tests added

All in `backend/tests/unit/test_media_validation.py`, exercising the application service rather
than the inspector alone. The read spy is scoped with a stub inspector, because the unchanged
`FileMediaSignalInspector` independently calls `read_bytes()`.

1. `test_source_hashing_reads_the_file_in_bounded_chunks` — bans `Path.read_bytes`, records every
   size requested from `Path.open`, and asserts each is positive and at most 1 MiB, that at least
   three reads occurred, and that the digest still matches an independently computed one.
2. `test_source_digests_match_independent_hashes_across_chunk_boundaries` — empty, sub-chunk,
   exactly-one-chunk and multi-chunk inputs against independent SHA-256 values.
3. `test_unreadable_source_keeps_its_status_without_a_hash` — directory input stays `UNREADABLE`
   with no hash. Missing-file parity remains covered by the existing
   `test_missing_source_has_no_fake_path_hash`.
4. `test_serialized_result_and_provenance_hash_stay_byte_identical` — asserts the pre-change
   baseline provenance hash.

The bounded-read test was confirmed to discriminate: run against the previous whole-file
implementation it fails with `AssertionError: source hashing must not read the whole file into
memory`; against the new implementation it passes with five bounded reads, maximum 1,048,576 bytes.

## Commands and results

Executed 2026-09-10 from the repository root unless noted. `--basetemp` is required because the
default pytest temporary root is not writable in this environment; that is unrelated to this change.

| Command | Result |
|---|---|
| `pytest tests/unit/test_media_validation.py` (in `backend/`) | 15 passed |
| `pytest` on the affected callers: `test_media_validation`, `test_vision_b3_mapping_study`, `test_vision_b4_quality_benchmark`, `test_vision_v3_quality_benchmark`, `test_vision_v3_quality_fixtures`, `test_vision_v3_quality_execution`, `test_vision_v3_mapping_fixtures`, `test_vision_v3_mapping_validation_study`, `test_asr_round1_runner`, `test_vision_b2_preflight` | 275 passed |
| `pytest tests` (full backend suite) | 837 passed, 5 skipped |
| `ruff check src tests` | All checks passed |
| `mypy src/sketch2life/application/services/media_validation.py` | Success: no issues found |
| `python tools/validate_harness.py` | `HARNESS_VALID` |
| `python tools/validate_repository_security.py` | `REPOSITORY_SECURITY_VALID`, 863 files scanned |
| `python tools/validate_architecture.py` | `ARCHITECTURE_VALID` |
| `git diff --check` | exit 0 |

No live benchmark, GPU session or provider call was executed. No commit or push was made.

## Pre-existing conditions, not caused by this change

- `mypy` in its configured package mode (`packages = ["sketch2life"]`) fails with
  `Package 'sketch2life' cannot be type checked due to missing py.typed marker`. Per-file
  invocation works, and the changed source file is clean.
- `backend/tests/unit/test_media_validation.py` reports seven `mypy` errors: four
  `import-untyped` (the same missing `py.typed` marker) and three `no-untyped-def` on the
  pre-existing `_validate`, `_write_png` and `_png_payload` helpers. The identical seven errors
  are present on the unmodified `HEAD` version of the file; this change adds none.
- `ruff format --check` reports pre-existing formatting differences in both files, in regions
  this change does not touch. Repository linting uses `ruff check`, which passes. No
  reformatting was applied, to avoid touching code outside the approved scope.
- The default pytest temporary root is not writable in this environment, so every `tmp_path`
  test errors without an explicit `--basetemp`. This affects pre-existing tests equally.

## Limitations

T0 bounds hashing memory only. It does **not**:

- bound total bytes read from disk — the whole file is still read;
- bound elapsed time;
- bound decoding memory. The inspector's per-pixel cost is the dominant resource exposure and is
  unchanged: `_MAX_IMAGE_PIXELS` (25,000,000) is independent of `_MAX_MEDIA_BYTES`, so a small,
  highly compressible PNG can declare a very large pixel count. A locally measured example: a
  9,960-byte synthetic PNG declaring 1500x1500 decoded in 26.9 s using 81.9 MB peak, and was
  accepted. That measurement is a synthetic diagnostic probe, not a production validation result,
  and it motivates a separate proposal rather than any change here;
- close the window between validation and inference in which a source file could change.

No model-quality, readiness or promotion claim follows from this change. Historical benchmark
outcomes are untouched.
