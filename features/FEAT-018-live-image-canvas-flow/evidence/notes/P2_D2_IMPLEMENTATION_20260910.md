# FEAT-018 P2-T1 D2 — image admission implementation and validation

- Evidence ID: EV-018-P2-D2-IMPL-01
- Date: 2026-09-10
- Type: implementation and offline validation record
- Status: D2 implementation and deterministic tests complete; completed-output review accepted
  2026-09-10 and selected for publication. **D3 performance/memory evaluation is separate and
  NOT started. P2-T1 is not complete after D2 alone.**
- Approval basis: `approvals/TASK_APPROVAL.md` "Approved P2-T1 D2 scope addendum —
  2026-09-10", authorizing U1 (`av==18.1.0` in a new `image-admission` extra) and the
  isolated D2 scope specified in `evidence/P2_IMAGE_ADMISSION_SPEC_20260910.md` (D1,
  revision 2, `EV-018-P2-D1-SPEC-01`) — the sole canonical authority for this scope.
  `evidence/notes/P2_RESEARCH_ROUND2_D2_IMPLEMENTATION_GOAL_20260910.md` was followed as a
  local, Git-ignored, noncanonical execution guide only; it carries no approval authority.
- Environment: local Windows checkout, Python 3.12.10, backend `.venv`. No GPU, provider,
  network call, or dependency install — `av` 18.1.0 was already resolved in the venv
  transitively via `faster-whisper`; this work declares it as its own explicit optional
  dependency but installs nothing new.

## Review fixes — 2026-09-10 (round 2)

A review of the initial D2 implementation found six issues; all six are fixed in this
revision of the record, on the same uncommitted change set (no new commit exists yet for
either round). Test count rose from 46 to 58 (12 new tests); full suite rose from 883 to
895 passed (12 new; 5 skipped unchanged).

1. **Bounded-read contract.** `_read_bounded` requested a full `_READ_CHUNK_BYTES` chunk on
   every read regardless of proximity to the limit, so an oversized file could consume up
   to `max_file_bytes + _READ_CHUNK_BYTES` bytes (measured: 5,242,880 for a file far larger
   than the 5,000,000 limit) before the overflow was detected. Each read now requests
   `min(_READ_CHUNK_BYTES, max_file_bytes + 1 - total)`, so total consumption can never
   exceed `max_file_bytes + 1` regardless of source size. A new spy test
   (`test_bounded_read_never_consumes_more_than_limit_plus_one_byte`) proves this against a
   4x-oversized source and was confirmed to fail against the prior implementation (measured
   5,242,880 bytes consumed there, matching the review's exact number) before passing
   against the fix. No-digest behavior on overflow is unchanged.
2. **Governance records.** `approvals/TASK_APPROVAL.md`'s top status now states P1 and the
   isolated P2-T1 D2 scope are both approved, with D3/P2-T2 through P2-T5/P3/P4/shared
   integration explicitly still pending. The D2 addendum no longer lists the Git-ignored
   execution note as part of the approval basis alongside D1 — D1 (`EV-018-P2-D1-SPEC-01`)
   is now stated as the sole canonical authority, and the execution note is explicitly
   labeled noncanonical. This record's own "Approval basis" line above was corrected the
   same way. `CONTEXT.md` no longer says D2 is `NOT_STARTED`; it now states D2 exists and
   is awaiting completed-output review, D3 is `NOT_STARTED`, and P2-T1 is not complete.
3. **Fixture manifest strengthened.** `expected_outcome`/`expected_reason` are now typed
   directly against the domain's own `AdmissionOutcome`/`AdmissionReason` enums (not free
   strings), with cross-field validation: `ADMITTED` must not carry a reason, every other
   outcome must, and the reason must actually belong to the declared outcome per the
   domain's own `outcome_for_reason` mapping. Duplicate `fixture_id`s are rejected at the
   manifest level. An explicit `FIXTURE_GENERATORS` registry now maps every generator name
   to a real zero-argument function (including new named wrappers for the payloads that
   were previously inline byte-literal expressions); a load-bearing test regenerates every
   manifest entry's payload and asserts its actual SHA-256 equals the checked-in value —
   not merely that the string is 64 characters — and two more tests prove this verification
   genuinely detects an unknown generator and a drifted digest, using synthetic manifests
   built for exactly that purpose. The checked-in `manifest-v1.json` was regenerated with
   the new generator names and fresh digests (necessary regardless, since fix 4 below
   changed what the JPEG generator actually produces).
4. **Undeclared NumPy dependency removed.** `_jpeg` used `numpy`, which neither `dev` nor
   `image-admission` declares — it was only ever present transitively via
   `asr-faster-whisper`. Rewritten to use `VideoFrame.from_bytes(..., format="rgba")`
   directly (verified: `rgb24`/`bgr24`/`gray`/`yuv420p` all raise `NotImplementedError` for
   `from_bytes`; only a small set including `rgba` works), supplying a tightly packed,
   unpadded buffer — `from_bytes` handles plane stride/padding internally, verified against
   64x64, 65x33, 63x63 and 100x50 all decoding back to their exact requested dimensions.
   Verified with numpy import-blocked at the interpreter level (`sys.meta_path` poisoning,
   fully in-process, nothing installed or uninstalled): all 58 tests both collect and pass.
5. **Snapshot-mutation test strengthened.** The existing test only proved two *separate*
   `admit()` calls bind to fresh bytes. A new test
   (`test_decoder_mutating_source_mid_admit_does_not_affect_the_result`) adds a decoder
   wrapper that overwrites the source file on disk immediately after receiving the
   snapshot, *during* one `admit()` call, then answers using the snapshot bytes it was
   actually given. Combined with a `Path.open` call-count spy scoped to exactly the
   `admit()` call, it proves the on-disk file genuinely changed, the reported digest and
   metadata still describe only the pre-mutation content, and the path was opened exactly
   once — no stage reopened it.
6. **Provider-versus-decoder conflation corrected.** The prior record wrongly described
   D1's zero-provider-call invariant itself as "not generalizing," using the garbage-IDAT
   decode as its example — but an image decode is not a Qwen/ASR provider call. Corrected
   below and in the relevant test's docstring: the provider invariant holds unconditionally
   and structurally (D2 contains no provider dependency or wiring at all, for any outcome);
   decoder call counts are a separate, narrower, in-scope fact that does legitimately vary
   by which stage detects a rejection. The per-case decoder-call test is kept, now
   explicitly documented as a decoder-call-discipline test and not a restatement of the
   provider invariant.

## Correction to D1

D1's architecture section previously stated "six new files plus one existing file
modified"; its own file table already listed seven new-file rows. Corrected to "seven new
files plus one existing file modified" in `evidence/P2_IMAGE_ADMISSION_SPEC_20260910.md`
sections 1 and 10, per the D2 execution note's explicit instruction.

## Changed files

### Product code — new (7)

| File | Responsibility |
|---|---|
| `backend/src/sketch2life/domain/understanding/image_admission.py` | Pure policy: `AdmissionOutcome`/`AdmissionReason` enums, `Feat018AdmissionLimits` (U4), `ImageMetadataSignals`/`DecodedFrameSignals`/`AdmissionDecision` value objects, and the ordered `evaluate_metadata`/`evaluate_frame_count`/`evaluate_cross_check` decision functions matching D1 section 3 exactly. Stdlib-only. |
| `backend/src/sketch2life/application/ports/image_decoder.py` | `ImageDecoderPort` protocol over bytes (`read_metadata`, `probe_frame_count`, `decode_one_frame`) plus `ImageDecodeSourceError`/`ImageDecodeProcessingError`/`ImageDecodeTimeoutError`. No `av` import. |
| `backend/src/sketch2life/application/services/image_admission.py` | `Feat018ImageAdmission`: single bounded snapshot read, complete-source hashing, port orchestration in the exact D1 step order, and the internal `Feat018AdmissionResult` (reuses `SourceMediaReferenceV1` on `ADMITTED` only). |
| `backend/src/sketch2life/infrastructure/media_validation/av_image_decoder.py` | `AvImageDecoder`, the only module importing `av`. Implements the bounded packet probe and the `FFmpegError`-base-class exception mapping. |
| `backend/tests/unit/test_image_admission.py` | 58 tests: all 6 D1 boundary cases, all 16 behavioral cases, plus domain-level, generator-registry and manifest-schema coverage (12 added in the round-2 review-fix pass). |
| `backend/tests/unit/feat018_admission_manifest.py` | `Feat018AdmissionFixtureManifestV1`/`...EntryV1`, the FEAT-018-local internal fixture schema (D1 section 6), now typed against the domain's own outcome/reason enums with cross-field and duplicate-id validation. Test-scoped; not in `contracts/schemas/`. |
| `features/FEAT-018-live-image-canvas-flow/fixtures/image-admission/manifest-v1.json` | 11-entry fixture manifest instance, referencing the explicit `FIXTURE_GENERATORS` registry by name with digests regenerated from those exact functions. No image binaries committed. |

### Product configuration — modified (1)

| File | Change |
|---|---|
| `backend/pyproject.toml` | Added the `image-admission` optional extra: `av==18.1.0`, exact-pinned, with a recorded reason, following the `asr-faster-whisper`/`vision-qwen` precedent. No other line changed. |

### Governance/evidence (4)

| File | Change |
|---|---|
| `features/FEAT-018-live-image-canvas-flow/approvals/TASK_APPROVAL.md` | Added the "Approved P2-T1 D2 scope addendum — 2026-09-10" recording the owner's explicit-in-conversation approval of U1 and the D2 scope; top status updated; execution note demoted to noncanonical (round 2). |
| `features/FEAT-018-live-image-canvas-flow/evidence/P2_IMAGE_ADMISSION_SPEC_20260910.md` | File-count correction (see above); two occurrences. |
| `features/FEAT-018-live-image-canvas-flow/CONTEXT.md` | D2-exists/awaiting-review, D3-`NOT_STARTED`, P2-T1-not-complete status added (round 2). |
| `features/FEAT-018-live-image-canvas-flow/evidence/notes/P2_D2_IMPLEMENTATION_20260910.md` | This record. |

**FEAT-003: zero files touched.** Verified by `git diff --stat` scoped to the change set above, which shows only the files listed and no `FEAT-003` path.

## Decisions applied (U1–U7, all as locked in D1/the execution note)

- **U1**: `av==18.1.0` declared in a new, dedicated `image-admission` extra; never relied on transitively through `asr-faster-whisper`.
- **U2**: closed pixel-format allowlist — `{rgb24, rgba, gray, pal8, monob, yuvj420p}` only; 16-bit PNG rejected as `UNSUPPORTED_PIXEL_FORMAT`.
- **U3**: container validation precedes the frame-count probe; a two-frame JPEG (container `mjpeg`) resolves to `UNSUPPORTED_CONTAINER`, never reaching the packet probe.
- **U4**: `max_file_bytes=5_000_000`, `max_pixels=4_000_000`, `max_longest_edge=4096`, `max_frames=1`, all enforced exactly.
- **U5**: no EXIF reporting implemented — optional/"if free" per D1, not required by any D1 section 7 test, so deliberately deferred rather than adding unrequested scope. No derivative or source file is written anywhere in this component.
- **U6**: `Feat018AdmissionResult`/`AdmissionDecision` are internal only; no public schema, no `MediaValidationResultV1`, no serialization migration.
- **U7**: FEAT-018-local fixture directory and test-scoped manifest schema used; `data/fixtures/manifests/media-validation-v1.json` untouched.

## Findings during implementation (verified, not merely asserted)

- **The D1 test-plan's stated mechanism for the "PNG signature only" case does not match measured PyAV behavior**, though the required *outcome* is unaffected. D1 section 7 test 3 says this case resolves "via the dimension check"; measured, `codec_context.format` is `None` for this exact input (not merely `width=0`/`height=0` with a resolved format) — so it actually resolves via the earlier `pixel_format is None` branch in `evaluate_metadata`. Both branches produce the identical `INVALID_SOURCE/CORRUPT_OR_TRUNCATED` outcome, which is what the acceptance checklist actually requires; the test asserts the outcome, not the internal branch.
- **Provider calls versus decoder calls are two different things and must not be conflated (corrected in the round-2 review-fix pass — see item 6 above).** A malformed-IDAT input correctly requiring one *image decode* is not a Qwen/ASR *provider* call, and the two claims are independent:
  - **The provider invariant holds unconditionally.** Zero Qwen/ASR calls occur for every non-`ADMITTED` outcome — in fact for every outcome including `ADMITTED` — because D2 contains no provider dependency, adapter, or wiring of any kind. This is not proven by any one test; it is structurally guaranteed by what this slice does not contain, and it cannot be violated by anything in this change set.
  - **Decoder call counts are a separate, narrower, in-scope fact, and they do legitimately vary by which stage detects the rejection.** For the garbage-IDAT case, D1's own finding F-C establishes that metadata inspection reports a plausible, fully-valid-looking header and *only the decode step* reveals the corruption — so exactly one `decode_one_frame` call is correct and necessary for that specific case, not zero. `test_decode_is_attempted_only_when_it_is_the_detection_mechanism` asserts the correct per-case expectation (0 for every metadata/byte-budget-decidable rejection, 1 for the one case where decode is the only detection mechanism) and its docstring now says explicitly that it is a decoder-call-discipline test, not a restatement of the provider invariant.
- **A genuine multi-frame PNG or single-container-compliant multi-frame JPEG could not be constructed** to exercise the `MULTIPLE_FRAMES` rejection end-to-end through the real decoder, because every multi-frame JPEG this session could produce reports container `mjpeg` (not `jpeg_pipe`), which U3's container gate intercepts first. The bounded packet-probe mechanism itself is tested directly against the real decoder (`test_multiframe_probe_examines_at_most_two_packets_and_decodes_none`); the end-to-end `MULTIPLE_FRAMES` rejection path is tested via a stub decoder that reports a supported container/codec/pixel-format with a frame count of 2 (`test_multiframe_rejection_end_to_end_via_stub`).

## Commands and results

Run 2026-09-10 from the repository/backend roots, both the initial pass and the round-2
review-fix pass. `--basetemp` supplied throughout for the same pre-existing environment
reason recorded in `EV-003-T1-T0-01`. Figures below are the final, post-fix results.

| Command | Result |
|---|---|
| `pytest tests/unit/test_image_admission.py` | 58 passed |
| Same, with `numpy` import-blocked (`sys.meta_path` poisoning, in-process) | 58 passed — proves the NumPy removal (fix 4) is real, not merely untested |
| FEAT-003 regression list (`test_media_validation`, `test_vision_b3_mapping_study`, `test_vision_b4_quality_benchmark`, `test_vision_v3_quality_benchmark`, `test_vision_v3_quality_fixtures`, `test_vision_v3_quality_execution`, `test_vision_v3_mapping_fixtures`, `test_vision_v3_mapping_validation_study`, `test_asr_round1_runner`, `test_vision_b2_preflight`) | 275 passed |
| Serialized-provenance parity (canonical PASS fixture, independent script) | `cded7b49413310fe54232ca793693db7d31db999b381908fff4c6521f9dbf5e5` — identical to the value recorded in `EV-003-T1-T0-01` |
| `pytest tests` (full backend suite) | 895 passed, 5 skipped (888 prior + 12 new = 900 collected) |
| `ruff check src tests` | All checks passed |
| `mypy` on all 5 new source files (4 `src/` + the manifest schema) | Success: no issues found |
| `mypy` on `test_image_admission.py` | 6 pre-existing-class findings only (see below); zero new-code findings after fixing 8 genuine issues introduced across both passes |
| `python tools/validate_harness.py` | `HARNESS_VALID` |
| `python tools/validate_repository_security.py` | `REPOSITORY_SECURITY_VALID`, 874 files scanned |
| `python tools/validate_architecture.py` | `ARCHITECTURE_VALID` (after one fix, below) |
| `python tools/validate_skeleton.py` | `SKELETON_VALID` |
| `git diff --check` | exit 0 |

No live benchmark, GPU session, provider call, dependency install, staging, commit, or push
occurred at any point across either pass.

### One validator finding, fixed

`validate_architecture.py`'s application-layer check is a **literal substring scan** for
`"sketch2life.infrastructure"`/`"sketch2life.interfaces"` anywhere in a file's text — not an
AST-based import check. The first draft of `application/services/image_admission.py`'s
module docstring explained, in prose, that the module *does not* import those packages,
and that explanation itself contained the banned substrings, so it was rejected by name-
matching rather than by an actual import. Reworded the docstring to describe the same
constraint without using those literal strings; re-ran the validator, which then passed.
This is a documented pre-existing quirk of the validator's approach, not a defect
introduced by this change, and no import was ever actually present.

## Pre-existing conditions, not caused by this change

- Same `py.typed`-marker-driven `mypy` `import-untyped` class of finding recorded in
  `EV-003-T1-T0-01` reproduces identically — now 5 occurrences on `test_image_admission.py`
  (one more than the initial pass's 4, because the round-2 bounded-read spy test adds one
  more intra-package import) plus 1 on `feat018_admission_manifest.py`. Every occurrence is
  the identical root cause (no `py.typed` marker anywhere in this package), not a new class
  of problem. No `no-untyped-def` or other new-code finding remains after fixing, across
  both passes: a `probe_frame_count` return type flowing through `Any` (twice — the
  original `_SpyDecoder` and the round-2 `_MutateOnFirstCallDecoder`), a bare `tuple`
  return-type annotation missing its type arguments, an `Any`-returning `_oversized_bytes`,
  an untyped `Path.open` wrapper signature mypy could not resolve against its overloads
  (twice), a same-scope variable-name reuse across incompatible `open()` modes, and a
  `_load_manifest` helper whose `-> object` return type was stricter than the rest of this
  file's already-`Any` typing under the missing-py.typed condition — all fixed.
- The default pytest temporary root remains unwritable in this environment; `--basetemp` was
  supplied to every invocation, as before.

## Limitations

- **D3 performance/memory evaluation is not performed here.** No timing or native-inclusive
  memory measurement was collected in this implementation pass; D1's measurement methodology
  (fresh-subprocess `K32GetProcessMemoryInfo`) remains a specification for a separately scoped
  D3 task, not code shipped in this change.
- **`DECODER_TIMEOUT` is proven only as a mapping.** `test_decoder_timeout_stub_proves_mapping_only`
  demonstrates the application service correctly classifies a hypothetical future timeout
  signal; it proves nothing about runtime interruption, and no in-process timeout mechanism
  exists anywhere in this change, consistent with D1 section 8.
- **The JPEG allowlist remains partly unverified**, exactly as D1 recorded: only baseline
  `yuvj420p` is measured and accepted; progressive and grayscale JPEG are unmeasured and
  therefore rejected by the closed allowlist, not merely untested.
- **EXIF reporting is not implemented** (U5). Optional per D1 ("if free"); not required by any
  D1 section 7 test; deliberately left out to avoid unrequested scope.
- **The `MULTIPLE_FRAMES` outcome is not exercised end-to-end through the real decoder**, for
  the structural reason recorded above (every constructible multi-frame JPEG fails the
  container gate first, per U3). The bounded-probe mechanism and the end-to-end policy
  application are each tested separately instead.
- This is a specification implementation and its deterministic tests, not a completion claim
  for FEAT018-P2-T1. D3 evaluation, any FEAT-003 producer connection, Qwen/ASR wiring, mobile
  transport, Gate A, and public-schema migration all remain entirely separate, unauthorized,
  and untouched by this change.

## Publication note

The completed D2 output passed technical review and was owner-selected for publication on
2026-09-10. This record is indexed by `evidence/README.md`. Publication records only the accepted
isolated D2 slice; it does not approve D3, mark P2-T1 complete, or authorize any provider,
FEAT-003, mobile, Gate A, public-contract or shared-integration work.
