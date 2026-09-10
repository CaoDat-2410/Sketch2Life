# FEAT-018 P2 — Image admission and decoding specification (D1)

- Evidence ID: EV-018-P2-D1-SPEC-01
- Date: 2026-09-10; revision: 2 (revision 1 same date; change log in section 10)
- Type: completed implementation-ready specification / owner-selected public record
- Status: specification complete. **Implementation NOT_STARTED.** This record is a
  specification, not an implementation approval, and does not amend
  `approvals/TASK_APPROVAL.md`. A separate D2 task approval is still required before any
  code, test, fixture or dependency change.
- Parent record: [isolated image admission and decoding design](P2_IMAGE_DECODE_DESIGN_20260910.md)
  (`EV-018-P2-DECODE-DESIGN-01`, owner-accepted design).
- Branch: `feature/feat018-p2-image-validation`, HEAD `b33e329`.
- Isolation: additive to FEAT-018 only. This specification changes no FEAT-003 default,
  validator, inspector, contract, policy, prompt, model profile, fixture, scoring rule,
  benchmark runner or historical evidence record. The unrelated, separately approved FEAT-003
  T0 maintenance patch (incremental source hashing) is a different change set and is not part
  of this specification.

## 0. Findings that shape the design

All are offline probe results against the installed environment, not expectations.

**F-A. Pillow is absent; PyAV is present only through an optional extra.** `Pillow`, `torch`,
`torchvision`, `cv2`, `imageio`, `skimage` are all absent. `av` 18.1.0 and `numpy` 2.5.2 are
present, but neither is declared in `backend/pyproject.toml` base dependencies: `av>=11` is a
transitive requirement of `faster-whisper`, in the optional `asr-faster-whisper` extra. A base
install has **no image decoder at all**.

**F-B. The existing validator cannot provide a single controlled snapshot.**
`DeterministicMediaValidator.validate` opens the image twice — once in `_source_reference` for the
hash, once in `inspector.inspect_image` — and the audio a third time. Any inspector injected there
reads different bytes from the ones the service hashed. Fixing that inside the service would change
FEAT-003 behavior, which this slice must not do. Admission is therefore a **separate component that
owns the snapshot**, not a `MediaSignalInspector` drop-in.

**F-C. A successful metadata open is not a valid image.** Measured, three distinct ways:

| Input | `av.open()` | Metadata | Decode |
|---|---|---|---|
| Truncated mid-IDAT | **succeeds** | `0x0`, `format is None` | `InvalidDataError` |
| PNG signature only (8 bytes) | **succeeds, 1 video stream** | — | — |
| Valid header, garbage IDAT | **succeeds** | `64x64 rgb24` (plausible!) | `ExternalError` |

The third case is the dangerous one: metadata looks entirely healthy and only the decode fails.

**F-D. Multi-frame detection can be bounded in-process.** `container.demux(video=0)` yields
compressed **packets** without decoding them. Measured: PNG → 1 packet (250 B), single JPEG → 1
packet (624 B), two-frame MJPEG → 2 packets (624 B each), and the loop can break at the second
packet without ever decoding it. This resolves the open question from revision 1: PyAV **can**
guarantee the required bound in process for frame counting. Packets carry a `size` attribute and
originate inside the snapshot, so the allocation is bounded by the snapshot itself.

**F-E. Container identity distinguishes single from motion JPEG.** Measured
`container.format.name`: PNG → `png_pipe`, single-frame JPEG → `jpeg_pipe`, **two-frame JPEG →
`mjpeg`**. A cheap pre-decode signal, though not sufficient alone (section 4).

**F-F. PyAV does detect malformed compressed streams — via two exception types.** Garbage IDAT
raises `ExternalError`; truncation and non-image bytes raise `InvalidDataError`. Both derive from
`av.error.FFmpegError`, which is the correct thing to catch. Catching only `InvalidDataError` would
let a malformed-stream failure escape as an unhandled exception.

## 1. Architecture

Additive and isolated from FEAT-003. **Seven new files plus one existing file modified.**

Revision 1 described this as "four new files, nothing modified". That was wrong: declaring a
dependency extra edits `backend/pyproject.toml`, and the fixture manifest needs a home. The honest
count is below — six new source/test files plus one new fixture-data file, plus the one modified
file.

| Kind | Path | Responsibility |
|---|---|---|
| **NEW** | `backend/src/sketch2life/domain/understanding/image_admission.py` | Pure policy: limits, outcome/reason enums, decision function over extracted metadata. Stdlib only — the architecture validator bans `pydantic` and frameworks from `domain/` |
| **NEW** | `backend/src/sketch2life/application/ports/image_decoder.py` | `ImageDecoderPort` protocol over **bytes**: `read_metadata`, `probe_frame_count`, `decode_one_frame` |
| **NEW** | `backend/src/sketch2life/application/services/image_admission.py` | `Feat018ImageAdmission`: snapshot acquisition, complete-source digest, port orchestration, policy application, typed internal result. Must not import `infrastructure` or `interfaces` — validator-enforced |
| **NEW** | `backend/src/sketch2life/infrastructure/media_validation/av_image_decoder.py` | `AvImageDecoder`. The only module importing `av`. Explicitly constructed and injected; never registered as a default |
| **NEW** | `backend/tests/unit/test_image_admission.py` | Section 7 tests, with stub decoders and spies |
| **NEW** | `backend/tests/unit/feat018_admission_manifest.py` | FEAT-018-local **internal** typed fixture-manifest schema (section 6). Test-scoped, so `pydantic` is available and it stays out of the shared registry |
| **NEW (data)** | `features/FEAT-018-live-image-canvas-flow/fixtures/image-admission/manifest-v1.json` | Fixture manifest instance. Feature-local, following FEAT-003's `features/<feature>/fixtures/` precedent. Adds a directory, so `python tools/validate_skeleton.py` applies |
| **MODIFIED** | `backend/pyproject.toml` | Adds one optional extra (section 4). The only existing file this slice changes |

No image binaries are committed. Fixtures are generated deterministically in-test with stdlib
`zlib`/`struct` for PNG and PyAV's MJPEG encoder for JPEG — the same approach
`test_media_validation.py` already uses. The manifest records expected outcomes plus the SHA-256 of
each generated payload, so it stays honest without shipping media.

Contract reuse and its boundary:

- **Reused unchanged, success only**: `SourceMediaReferenceV1` from
  `contracts/schemas/media_validation.py` — `artifact_ref`, complete-file `sha256`,
  `source_status="AVAILABLE"`. No parallel source-reference schema is introduced anywhere.
- **Not constructed on any failure**: the type has three statuses and requires a hash exactly when
  `AVAILABLE`. A readable oversized file is none of them, so rejections carry the internal typed
  result and no `SourceMediaReferenceV1` at all.
- **Never emitted by this slice**: `MediaValidationResultV1`. Admission is not media-quality
  validation. Public serialization and any migration are deferred for explicit owner review.

Injection: `Feat018ImageAdmission(decoder=AvImageDecoder(), limits=Feat018AdmissionLimits())`.
No module-level default, no registration, no change to any existing call site.

## 2. Failure semantics

| Outcome | Reason | Meaning | Guidance |
|---|---|---|---|
| `ADMITTED` | — | Bounded bytes, fully hashed, one frame, supported profile, within pixel and edge budgets, decoded output matches admitted metadata | Proceed to validation. **Not** a quality PASS, **not** permission to call a model |
| `REJECTED` | `FILE_BYTES_EXCEEDED` | Actual bytes read exceeded the budget | Choose or export a smaller file |
| `REJECTED` | `PIXEL_BUDGET_EXCEEDED` | Declared pixels over budget, refused **before** decode | Export smaller dimensions |
| `REJECTED` | `LONGEST_EDGE_EXCEEDED` | Declared longest edge over budget, refused before decode | Export smaller dimensions |
| `REJECTED` | `MULTIPLE_FRAMES` | A second packet exists (bounded probe, F-D) | Supply a static image |
| `UNSUPPORTED` | `UNSUPPORTED_CONTAINER` / `UNSUPPORTED_CODEC` / `UNSUPPORTED_PIXEL_FORMAT` | Well-formed but outside the supported set | Name the supported formats; retaking will not help |
| `INVALID_SOURCE` | `NOT_AN_IMAGE` | Open fails, or no video stream. **Includes an empty file** | Choose or export a valid file |
| `INVALID_SOURCE` | `CORRUPT_OR_TRUNCATED` | Dimensions absent/zero, `format is None`, decode raises `FFmpegError`, or decoded output contradicts metadata | Choose or export a valid file |
| `INVALID_SOURCE` | `MISSING_SOURCE` | Path absent or unreadable | Choose a file |
| `PROCESSING_FAILURE` | `DECODER_ERROR` / `INTERNAL_ERROR` | Our side failed | Say the system could not process it. Never imply the photograph was bad |
| `PROCESSING_FAILURE` | `DECODER_TIMEOUT` | **Reserved**, see section 8 | — |

Prohibitions, stated so review can check them mechanically:

1. Never fabricate a digest — no path hash, no placeholder, no digest for an unread file.
2. Never present a prefix digest as a complete-source hash. `FILE_BYTES_EXCEEDED` carries **no
   digest field at all**, rather than a partial one.
3. Never relabel a readable oversized file `UNREADABLE` to fit the V1 status enum.
4. `ADMITTED` grants nothing downstream. The existing adapter ingress checks
   (`MEDIA_VALIDATION_PROVENANCE_MISSING`, `MEDIA_VALIDATION_NOT_PASSED` in `qwen_vision.py` and
   `fake_vision.py`) remain the gate on inference, unweakened and unbypassed.
5. `PROCESSING_FAILURE` is never merged into `INVALID_SOURCE`. Blaming the user for our failure is
   a correctness bug, not a wording preference.

## 3. Bounded data flow

One acquisition, one snapshot, every consumer reads that snapshot.

```
1. OPEN once, binary. No stat-based decision.
2. READ at most (max_file_bytes + 1) bytes in bounded chunks.
     got > max_file_bytes        -> REJECTED / FILE_BYTES_EXCEEDED   (stop; NO digest)
3. SNAPSHOT = the bytes just read. Nothing below re-reads the path.
4. DIGEST = sha256(SNAPSHOT), complete-source, computed from the snapshot.
5. METADATA from SNAPSHOT, header only:
     open raises FFmpegError       -> INVALID_SOURCE / NOT_AN_IMAGE     (covers empty file)
     no video stream               -> INVALID_SOURCE / NOT_AN_IMAGE
     container.format.name not in allowlist -> UNSUPPORTED / UNSUPPORTED_CONTAINER
     codec_context.format is None  -> INVALID_SOURCE / CORRUPT_OR_TRUNCATED
     width < 1 or height < 1       -> INVALID_SOURCE / CORRUPT_OR_TRUNCATED
     codec not in allowlist        -> UNSUPPORTED / UNSUPPORTED_CODEC
     pix_fmt not in allowlist      -> UNSUPPORTED / UNSUPPORTED_PIXEL_FORMAT
     width*height > max_pixels     -> REJECTED / PIXEL_BUDGET_EXCEEDED
     max(width,height) > max_edge  -> REJECTED / LONGEST_EDGE_EXCEEDED
6. FRAME COUNT from SNAPSHOT via demux, no decoding:
     skip packets with size == 0 (flush sentinel)
     second non-empty packet seen  -> REJECTED / MULTIPLE_FRAMES  (break immediately)
7. DECODE exactly one frame from SNAPSHOT:
     FFmpegError                   -> INVALID_SOURCE / CORRUPT_OR_TRUNCATED
     no frame produced             -> INVALID_SOURCE / CORRUPT_OR_TRUNCATED
     any other exception           -> PROCESSING_FAILURE / DECODER_ERROR
8. CROSS-CHECK decoded frame against step 5:
     frame.width/height/format.name != admitted values
                                   -> INVALID_SOURCE / CORRUPT_OR_TRUNCATED
9. ADMITTED with DIGEST, admitted metadata and the frame summary. Release the frame.
```

Why each rule exists:

- **Actual bytes, not `stat`.** Reading `limit + 1` measures what was really read; `stat` can
  disagree with the stream and a growing file defeats it.
- **Snapshot, not path.** This is precisely why the component cannot be a `MediaSignalInspector`
  (F-B). Hashing one read and decoding another leaves a mutation window between them.
- **Metadata gates run before the allocation they protect against.** Measured: a 16,201-byte PNG
  declaring 2000x2000 returns its dimensions from a header-only open in **8.1 ms** with no pixel
  buffer; the full decode allocates a 12.0 MB frame.
- **Steps 5, 7 and 8 exist because open-success is not validity (F-C).** The garbage-IDAT case
  reports a plausible `64x64 rgb24` and fails only at decode, so the decode step is mandatory —
  metadata inspection alone admits corrupt files.
- **Step 8 is not redundant.** Cross-checking decoded width/height/format against the admitted
  metadata is what makes the pixel budget meaningful: a decoder that produced different dimensions
  from those admitted would otherwise slip past the budget entirely. Measured working:
  metadata `(200, 120, 'rgb24')` == decoded `(200, 120, 'rgb24')`.
- **No resize-after-decode.** Resizing cannot undo an allocation that already happened. The pixel
  budget is enforced at step 5 or not at all.
- **Originals are never written.** Read-only: no derivative, no EXIF-rotated file, no normalization.

## 4. Decoder selection and dependency

### Availability, verified

| Candidate | Present | Notes |
|---|---|---|
| `av` (PyAV) 18.1.0 | **yes** | FFmpeg binding. `Requires-Python >=3.11`; **no dependencies of its own**. Currently transitive via `faster-whisper` |
| `numpy` 2.5.2 | yes | Transitive via `ctranslate2`/`onnxruntime` |
| `Pillow` | **no** | Conventional choice; would be a new dependency and every profile claim below would need re-probing |
| `torch`, `torchvision`, `cv2`, `imageio`, `skimage` | no | — |
| stdlib `zlib`/`struct` | yes | Used by the existing PNG inspector. No JPEG support |

### Measured profile surface

| Input | `container.format.name` | `codec` | `pix_fmt` | Proposed |
|---|---|---|---|---|
| PNG 8-bit RGB | `png_pipe` | `png` | `rgb24` | **accept** |
| PNG 8-bit RGBA | `png_pipe` | `png` | `rgba` | **accept** |
| PNG 8-bit grayscale | `png_pipe` | `png` | `gray` | **accept** |
| PNG 8-bit palette | `png_pipe` | `png` | `pal8` | **accept** |
| PNG 1-bit grayscale | `png_pipe` | `png` | `monob` | **accept** |
| JPEG baseline, one frame | `jpeg_pipe` | `mjpeg` | `yuvj420p` | **accept** |
| JPEG, two frames | `mjpeg` | `mjpeg` | `yuvj420p` | **reject** (container + packet probe) |
| PNG 16-bit RGB | `png_pipe` | `png` | `rgb48be` | **reject**, `UNSUPPORTED_PIXEL_FORMAT` |
| PNG 16-bit grayscale | `png_pipe` | `png` | `gray16be` | **reject**, `UNSUPPORTED_PIXEL_FORMAT` |
| Non-image bytes / empty | — | — | — | `InvalidDataError` → `NOT_AN_IMAGE` |

Three closed allowlists, all checked from header metadata before decoding:

- container: `{png_pipe, jpeg_pipe}` — `mjpeg` is excluded, which rejects motion-JPEG at the
  container level in addition to the packet probe;
- codec: `{png, mjpeg}`;
- pixel format: `{rgb24, rgba, gray, pal8, monob, yuvj420p}` as **measured**, with
  `{yuvj422p, yuvj444p, yuv420p, yuv422p, yuv444p}` as **candidates pending probe** (U2).

Closed allowlists mean anything unnamed is rejected rather than attempted. 16-bit PNG, CMYK JPEG
and animated images are rejected, as the parent design note requires. Progressive and grayscale
JPEG are **not yet measured** and must not be claimed as supported until probed.

### Exception mapping

`av.error.InvalidDataError` and `av.error.ExternalError` both derive from `av.error.FFmpegError`
(verified). The adapter catches **`av.error.FFmpegError`** and maps it to `INVALID_SOURCE`; any
other exception maps to `PROCESSING_FAILURE / DECODER_ERROR`. Catching only `InvalidDataError`
would let the malformed-compressed-stream case (F-F) escape unhandled.

### Dependency decision — recommended

Declare PyAV explicitly, exact-pinned, in a **new optional extra named `image-admission`**.
Relying on `av` arriving transitively through `asr-faster-whisper` is ruled out: image admission
would fail to import on a base install, and its version would be whatever `av>=11` happened to
resolve to.

Proposed addition to `backend/pyproject.toml` under `[project.optional-dependencies]`, matching the
exact-pin-with-recorded-reason pattern already used by `asr-faster-whisper` and `vision-qwen`:

```toml
# FEAT-018 P2 image admission (D1): exact-pinned, optional. PyAV is the only decoder whose
# JPEG/PNG profile behaviour is measured in this environment. Declared explicitly so image
# admission never depends on `av` arriving transitively through `asr-faster-whisper`.
image-admission = [
  "av==18.1.0",
]
```

**Compatibility, checked statically — no install performed:**

| Constraint | Value | Result |
|---|---|---|
| `faster-whisper` 1.2.1 requires | `av>=11` | `av==18.1.0` **satisfies** it; both extras co-install and resolve to 18.1.0 |
| `av` 18.1.0 `Requires-Python` | `>=3.11` | Compatible with the project's `>=3.12,<3.14` |
| `av` own dependencies | **none** | Adds exactly one distribution |
| Environment | `av` 18.1.0 already resolved under Python 3.12.10 | The pin matches what is installed; no resolution change expected |

Residual risk: if `faster-whisper` later requires `av>=19`, the exact pin conflicts and must be
revisited together. This is the ordinary cost of exact pinning and the same exposure the two
existing extras already carry.

### EXIF

Read-only in this slice, and only if free: orientation may be **reported** as a metadata field. No
rotation, no derivative file, no change to stored bytes. Writing a normalized derivative belongs to
inference preparation, where `processing_image_ref` and `ImageDerivationProvenanceV1` already exist
in `contracts/schemas/vision.py`. `working_copy_ref` in `SourceMediaReferenceV1` remains typed
`None` and is not used.

## 5. Trial configuration

| Setting | Value | Status |
|---|---|---|
| `max_file_bytes` | 5,000,000 | **Enforced.** Matches `lightning_client.py:174,231` and `tools/lightning_provider_server.py:25` |
| `max_pixels` | 4,000,000 | **Enforced**, pre-decode |
| `max_longest_edge` | 4096 | **Enforced**, pre-decode |
| `max_frames` | 1 | **Enforced**, bounded packet probe (F-D) |
| Concurrency | one decode at a time per worker | Enforced by construction |
| Decode wall time | 5 seconds | **Unmeasured evaluation target, not a cap** |
| Incremental process memory | 256 MiB | **Unmeasured evaluation target, not a cap** |

`max_longest_edge` is an **independent dimension guard**, not an aspect-ratio rule. It bounds the
single largest dimension regardless of the other, and regardless of total pixels. It is deliberately
redundant with `max_pixels` for typical shapes and binds independently on elongated ones — for
example 4200 x 900 is 3,780,000 pixels (inside the pixel budget) and is still rejected for a
4200-pixel edge. Both limits are applied; neither substitutes for the other.

The two performance figures are not enforcement. Enforcing them requires a worker with a kill
mechanism and cleanup tests; none exists in this slice. A target that is only measured protects
nothing, and any report must say so rather than implying a guarantee.

### Measured cost at the budget, native-inclusive

| Declared pixels | File bytes | Metadata open | Full decode | RSS delta | Decoded array |
|---|---|---|---|---|---|
| 1,000,000 | 5,210 | 3.6 ms | 0.047 s | 14.3 MB | 3.0 MB |
| 4,000,000 | 16,201 | 8.1 ms | 0.015 s | 12.3 MB | 12.0 MB |

Both sit far inside the targets — on uniform synthetic images that compress unrealistically well.
These are not photographic workloads and must not be reported as evidence that the targets hold for
real inputs.

### Limitation for camera photographs

A 12 MP phone photo is about 4032 x 3024 = **12,192,768 pixels**, roughly **3x over** the 4,000,000
budget, and is rejected with `PIXEL_BUDGET_EXCEEDED`. That is intended trial behavior and a real
product constraint, not an oversight. Note its longest edge (4032) passes the edge guard, so the
pixel budget is what binds for ordinary photos.

The limits also bind unevenly by format: a 4 MP JPEG is typically 1-2 MB and clears the byte limit
comfortably, while a 4 MP photographic PNG routinely exceeds 5,000,000 bytes and is rejected on
bytes before its pixels are examined.

## 6. Fixture manifest — FEAT-018-local, not `MediaFixtureManifestV1`

Revision 1 proposed reusing `MediaFixtureManifestV1`. That was wrong, for two reasons verified in
`contracts/schemas/media_validation.py`:

1. `expected_decision: MediaDecision` admits only `PASS` and `RECAPTURE`. It **cannot** express
   `ADMITTED`, `REJECTED`, `UNSUPPORTED`, `INVALID_SOURCE` or `PROCESSING_FAILURE`, and
   `expected_reasons: tuple[MediaRecaptureReason, ...]` cannot express any admission reason.
2. `audio_ref: str = Field(min_length=1)` is **mandatory** with no `audio_status` field. An
   image-only admission fixture would need a placeholder audio reference for a modality it does not
   have — dishonest by construction.

Reusing it would therefore mean either misreporting outcomes or inventing audio. Neither is
acceptable, and widening it is a shared-contract change that this slice must not make.

**Specified instead:** a FEAT-018-local internal typed schema
`Feat018AdmissionFixtureManifestV1` in `backend/tests/unit/feat018_admission_manifest.py`,
deliberately test-scoped so it stays out of the shared `contracts/schemas/` registry and is never
mistaken for a published contract. Entry fields:

| Field | Purpose |
|---|---|
| `fixture_id` | Stable identifier |
| `generator` | Exact function that produces the bytes, so fixtures are reproducible |
| `payload_sha256` | Digest of the generated bytes |
| `declared_width`, `declared_height` | What the header claims |
| `expected_outcome` | `ADMITTED` / `REJECTED` / `UNSUPPORTED` / `INVALID_SOURCE` / `PROCESSING_FAILURE` |
| `expected_reason` | Nullable; required for every non-`ADMITTED` outcome |
| `expected_container`, `expected_codec`, `expected_pixel_format` | Nullable; populated only where the fixture is expected to reach metadata inspection |
| `synthetic_data` | Pinned true |

No audio field exists, because admission has no audio modality. `SourceMediaReferenceV1` continues
to be reused on successful admission only, and is **not** duplicated by this schema.

Fixture data lives at
`features/FEAT-018-live-image-canvas-flow/fixtures/image-admission/manifest-v1.json`, following
FEAT-003's `features/<feature>/fixtures/` precedent. No image binaries are committed: payloads are
generated deterministically in-test and the manifest records the generator plus each digest. Adding
this directory is a repository structure change, so `python tools/validate_skeleton.py` applies.

FEAT-003's `data/fixtures/manifests/media-validation-v1.json` is not touched, and no entry is added
to it.

## 7. Tests and measurement

All tests are new and FEAT-018-owned. No existing test is modified.

### Boundary tests — exact limit and limit+1

| Case | Input | Expected |
|---|---|---|
| Bytes at limit | exactly 5,000,000 | passes step 2 |
| Bytes over | exactly 5,000,001 | `REJECTED/FILE_BYTES_EXCEEDED`, **no digest field present** |
| Pixels at limit | 2000 x 2000 = 4,000,000 | passes step 5 |
| Pixels over | 2000 x 2001 = 4,002,000 | `REJECTED/PIXEL_BUDGET_EXCEEDED`, no decode |
| Edge at limit | 4096 x 900 (3,686,400 px) | passes both dimension rules |
| Edge over, pixels inside | 4200 x 900 (3,780,000 px) | `REJECTED/LONGEST_EDGE_EXCEEDED` — proves the edge guard is independent |

### Behavioral tests

1. **Compressed-small, pixel-large.** A ~16 KB PNG declaring 3000x3000 rejected **before** decode.
   Assert via spy that `decode_one_frame` was never called.
2. **Truncated input** → `INVALID_SOURCE/CORRUPT_OR_TRUNCATED`. Must cover the measured trap: the
   metadata open succeeds and reports `0x0` with `format is None`, so the test fails if the
   implementation infers validity from a successful open, or crashes on `format.name` when
   `format` is `None`.
3. **PNG signature only** (8 bytes) → opens with a video stream; must still be
   `INVALID_SOURCE/CORRUPT_OR_TRUNCATED` via the dimension check.
4. **Malformed compressed stream** (valid header, garbage IDAT) → metadata reports a plausible
   `64x64 rgb24`, decode raises `ExternalError`; expect `INVALID_SOURCE/CORRUPT_OR_TRUNCATED`.
   This test specifically guards the `FFmpegError` base-class catch.
5. **Empty file** → `INVALID_SOURCE/NOT_AN_IMAGE` at admission level.
6. **Empty bytes at the helper level** → the snapshot/hash helper must return
   `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`. These two are different
   assertions at different layers and must not be conflated.
7. **Not an image** (arbitrary bytes) → `INVALID_SOURCE/NOT_AN_IMAGE`.
8. **Unsupported profiles.** 16-bit RGB (`rgb48be`) and 16-bit grayscale (`gray16be`) →
   `UNSUPPORTED/UNSUPPORTED_PIXEL_FORMAT`, distinct from corrupt.
9. **Unsupported container.** Two-frame JPEG probes as container `mjpeg` →
   `UNSUPPORTED/UNSUPPORTED_CONTAINER` or `REJECTED/MULTIPLE_FRAMES` depending on which gate runs
   first; the test pins the expected one so the ordering is deliberate rather than incidental.
10. **Supported profiles.** One admitted case per measured allowlist row.
11. **Multiple frames, bounded.** Two-frame MJPEG → `REJECTED/MULTIPLE_FRAMES`, and assert the
    probe examined at most two packets and decoded none.
12. **Decoded/metadata cross-check.** A stub decoder returning dimensions that disagree with the
    admitted metadata → `INVALID_SOURCE/CORRUPT_OR_TRUNCATED`.
13. **Source mutation.** Overwrite the file after the snapshot is taken; digest and decoded result
    must both still describe the snapshot, and a re-run must produce a different digest. This is
    what proves single-snapshot binding.
14. **Complete-source digest across chunk boundaries.** For **valid admitted images** only, sized
    just under, exactly at, and just over the read-chunk size, the digest must equal an
    independently computed `sha256` of the whole file. A prefix digest fails this.
15. **Zero provider calls after rejection.** Spy decoder plus spy vision/ASR adapters; call counts
    exactly zero for every non-`ADMITTED` outcome.
16. **Processing-failure separation.** A stub decoder raising a non-`FFmpegError` exception →
    `PROCESSING_FAILURE/DECODER_ERROR`, never `INVALID_SOURCE`.

### Measurement method

- **Native-inclusive memory is mandatory.** Measured: `tracemalloc` reported a **0.03 MB** Python
  peak for a decode whose process RSS delta was **12-14 MB**. Python allocation tracing is blind to
  FFmpeg and must not be used for this budget.
- On Windows use `K32GetProcessMemoryInfo` (kernel32) or `GetProcessMemoryInfo` (psapi) via
  `ctypes`, reading `WorkingSetSize` / `PeakWorkingSetSize`. **Declare `argtypes` and `restype`
  explicitly** — without them the call silently returns zeros, which is exactly what happened on
  the first probe attempt and would have been read as "no memory used". `psutil` is not installed.
- Measure each image in a **fresh subprocess** and report peak working set. In-process deltas are
  contaminated by allocator retention: above, the 1 MP case reported a *larger* delta than the 4 MP
  case.
- Report sample counts, decoder identity and version (`av.__version__` plus the FFmpeg build), and
  a distribution rather than a single number. One sample is not a benchmark.

### FEAT-003 regression and provenance parity — in acceptance

Run and report, modifying none of them:

- `backend/tests/unit/test_media_validation.py`.
- The benchmark validation and provenance helpers that call the validator:
  `test_vision_b3_mapping_study.py`, `test_vision_b4_quality_benchmark.py`,
  `test_vision_v3_quality_benchmark.py`, `test_vision_v3_quality_fixtures.py`,
  `test_vision_v3_quality_execution.py`, `test_vision_v3_mapping_fixtures.py`,
  `test_vision_v3_mapping_validation_study.py`, `test_asr_round1_runner.py`,
  `test_vision_b2_preflight.py`.
- **Serialized-provenance parity**: `MediaValidationResultV1.model_dump_json()` and its SHA-256
  unchanged on the deterministic fixtures, because the benchmark helpers record that hash as
  `validation_artifact_sha256` via `_sha256_text(result.model_dump_json())`.
- Diff inspection proving no FEAT-003 source file, contract, policy, inspector, fixture, manifest,
  prompt, profile, scoring rule, runner or evidence record is touched.

## 8. Timeout and frame-probe honesty

**Timeout.** `DECODER_TIMEOUT` exists in the internal failure model so a later killable worker has
a reason code to return. **The initial in-process PyAV implementation cannot enforce it.** A decode
inside `libavcodec` does not yield to Python, so no in-process mechanism — signal, thread, or
watchdog — can reliably interrupt it. Consequently:

- No acceptance criterion may claim timeout protection.
- Stub-based tests for `DECODER_TIMEOUT` prove **mapping behavior only**: that if something reports
  a timeout, the result is `PROCESSING_FAILURE/DECODER_TIMEOUT`. They prove nothing about runtime
  interruption.
- The 5-second figure stays an evaluation target. Real enforcement requires process isolation with
  a kill mechanism and cleanup tests, deferred to a later worker scope.

**Frame probe.** Revision 1 left open whether multi-frame detection could be bounded in process.
F-D settles it: `container.demux(video=0)` yields compressed packets **without decoding**, and the
loop breaks at the second non-empty packet. Bounded probe strategy:

- Iterate `demux(video=0)`, skipping packets where `size == 0` (the flush sentinel — counting these
  would produce a wrong frame count).
- Stop at the second non-empty packet and return `MULTIPLE_FRAMES` immediately. The second packet
  is never decoded, and its allocation is bounded by its own compressed size, which is bounded by
  the snapshot.
- Close the container in a `finally` block; release the decoded frame reference after the
  cross-check so the pixel buffer is not retained past step 9.

Honest limitation: this bounds **allocation attributable to frame counting**, not total decoder
memory. A single frame within the pixel budget can still allocate on the order of tens of MB
(measured: 12.0 MB for 4 MP), and there is no in-process cap on that. Hard isolation remains a
later worker scope.

## 9. Decision table and acceptance checklist

### Owner decisions

| # | Decision | Recommendation | Blocker? |
|---|---|---|---|
| U1 | Dependency strategy | **Declare `av==18.1.0` in a new optional `image-admission` extra.** Explicitly rule out relying on the ASR extra's transitive `av` | **Yes — blocks implementation.** Modifies `backend/pyproject.toml` |
| U2 | JPEG pixel-format allowlist | Ship with measured `yuvj420p` only; probe progressive, grayscale, 4:2:2 and 4:4:4 before widening | No — a narrower allowlist is safe |
| U3 | Gate ordering for two-frame JPEG | Pin container check before packet probe, or the reverse, deliberately | No |
| U4 | 12 MP camera photos rejected in trial | Accept as a stated constraint | No |
| U5 | EXIF orientation reported at all | Read-only reporting only; no derivative regardless | No |
| U6 | Public serialization of admission results | Keep internal until separately reviewed | No |
| U7 | Fixture directory `features/FEAT-018.../fixtures/image-admission/` | Approve the new directory; run `validate_skeleton.py` | No |

### Implementation acceptance checklist

1. Every outcome and reason in section 2 is reachable and covered by a test.
2. A digest is emitted only for a completely read file and equals an independently computed
   `sha256` of the whole file, verified across chunk boundaries on **valid admitted images**.
3. No `SourceMediaReferenceV1` is constructed for any non-`ADMITTED` outcome; no
   `MediaValidationResultV1` is produced anywhere in this slice.
4. Pixel and edge rejections occur with `decode_one_frame` never called, spy-proven.
5. Metadata, digest, frame probe and decode all read the same snapshot; the mutation test passes.
6. Truncated, signature-only, empty and malformed-stream inputs are all `INVALID_SOURCE`, never
   admitted, despite metadata opening successfully for three of the four.
7. Decoded width, height and pixel format are cross-checked against admitted metadata.
8. Multi-frame detection examines at most two packets and decodes none.
9. No timeout-enforcement claim appears anywhere in code, tests or evidence.
10. All FEAT-003 regressions in section 7 pass unchanged, and serialized provenance is
    byte-identical.
11. `ruff check`, `mypy` on new source files, and `validate_harness` / `validate_repository_security`
    / `validate_architecture` pass; `validate_skeleton` passes given the new fixture directory.
12. The evidence report states the measured time and memory distribution and says plainly that
    5 s and 256 MiB were targets, not enforced.

## 10. Change log from revision 1

| # | Revision 1 said | Revision 2 |
|---|---|---|
| 1 | "Four new files, nothing modified" | **Corrected.** Seven new files plus `backend/pyproject.toml` modified. Declaring an extra edits an existing file |
| 2 | Recommended `av` "exact-pinned in a new optional extra", unnamed | **Named `image-admission`, pinned `av==18.1.0`**, with a static compatibility check against `faster-whisper`'s `av>=11`, `Requires-Python >=3.11` and the project's `>=3.12,<3.14` |
| 3 | Called `max_longest_edge` "near-redundant… an aspect-ratio guard" and suggested lowering it | **Corrected.** It is an independent dimension guard. Kept at 4096, with a test (4200 x 900) proving it binds while pixels are inside budget |
| 4 | Validated codec and pixel format | **Extended**: container/signature added; decoded frame cross-checked against admitted metadata; `format is None` handled; `FFmpegError` base class specified after finding `ExternalError` |
| 5 | Fixtures in a `MediaFixtureManifestV1` instance | **Corrected.** That schema cannot express admission outcomes and mandates `audio_ref`. Replaced with a FEAT-018-local internal typed manifest; `SourceMediaReferenceV1` still reused on success only |
| 6 | "empty… sizes" listed under full-hash parity | **Split.** Empty bytes test the hash helper; an empty *file* must be `INVALID_SOURCE/NOT_AN_IMAGE`. Chunk-boundary digest parity applies to valid admitted images |
| 7 | `DECODER_TIMEOUT` listed with no caveat | **Corrected.** Reserved for a future killable worker; in-process PyAV cannot enforce it; stub tests prove mapping only |
| 8 | Multi-frame bound left open | **Resolved by probe.** `demux()` counts packets without decoding; bounded probe and cleanup specified; residual single-frame allocation limitation stated |
| 9 | FEAT-003 preservation asserted | **Unchanged in intent**, now with explicit regression and serialized-provenance parity in the acceptance checklist |
| 10 | File table listed four files | **Replaced** with a table distinguishing new files from the one modified file, including manifest schema and data paths |

## 11. Limitations

1. All measurements come from synthetic, highly compressible images generated in-probe. They are
   not photographic workloads and establish neither camera-realistic cost nor threshold correctness.
2. The 5 s and 256 MiB figures remain unmeasured targets. Nothing here enforces them, and no worker
   isolation or cleanup mechanism is proposed in this slice.
3. The JPEG allowlist is partly unverified (U2). Only baseline `yuvj420p` was probed; progressive
   and grayscale JPEG are unmeasured.
4. Malformed-stream detection is demonstrated for one constructed case (garbage IDAT). That is a
   counterexample-level result: it shows PyAV detects that class of corruption, not that it detects
   all malformed streams. No general robustness claim is made.
5. `Pillow` was not evaluated because it is absent; adopting it would require re-probing every
   profile claim in section 4.
6. Snapshot binding protects this component only. It does not close the separate window in
   `qwen_vision.py`, where the model runtime re-opens the image path in a subprocess after
   verification.
7. Frame-probe bounding limits allocation attributable to frame counting, not total decoder memory
   for a single admitted frame.
8. No D2 implementation, dependency change, benchmark run, provider call, staging, commit or push
   was performed. Repository validators were re-run for publication and passed; this does not
   constitute D2 runtime validation.
