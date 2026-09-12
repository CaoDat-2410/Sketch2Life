# FEAT-018 D3 Formal Cohort B Execution Report

- Date: 2026-09-12
- Target commit: `9191565a8961aab1bd10b2a0aa3efff7aefdf998`
- Scope: FEAT-018 P2-T1 D3-R2 offline image-admission evaluation, Cohort B only. Measures the
  committed D2 `Feat018ImageAdmission.admit()` implementation against 8 owner-approved local
  non-sensitive photographs (4 JPEG + 4 PNG), 3 fresh-process repeats each, 24 total samples.
  No Qwen, Whisper, provider, network, mobile, FEAT-003, or shared-integration work is included.

## Executive verdict

**PASS.** All 24 samples executed, all `ADMITTED`, all `WITHIN_TARGET` for both the 5-second
timing target and the 256 MiB native-memory bracket, at both the per-image and aggregate level.
`execution_occurred: true`, `complete: true`, `sample_count: 24`.

## Source gate and owner approval

- Source gate status: **APPROVED**. The project owner approved the exact local B01-B08
  candidate set for Cohort B (four JPEG + four PNG files), recorded in
  `approvals/TASK_APPROVAL.md` under "Owner approval and Cohort B source admission -
  2026-09-12", authorizing only this offline evaluation.
- The local candidate manifest sets `owner_reviewed=true` and `execution_authorized=true`, and
  the accompanying local source-review note records an explicit per-file visual disposition
  (no people, children, documents, screens, location clues, brands, or other excluded content)
  for all 8 files, approved by the owner on 2026-09-12.
- Manifest SHA-256 (of the local, git-ignored `candidate-manifest.json`):
  `18d760e37211048996e073d61cf03a2155c26e022ef7dd2c48720a5bcf6cd0ea`.

### Manifest correction disclosed before execution

Before hashing/execution, the local candidate manifest's `B08` entry recorded a SHA-256 value
of 63 hexadecimal characters -- one character short of a valid digest -- identical to a matching
truncation independently present in the local source-review note. The other seven entries
matched their files exactly, and B08's recorded byte count (1,721,040) and dimensions
(1254x1254) already matched its file. Recomputed directly from the on-disk file, the true
64-character digest is the recorded value plus a trailing `8`. This was surfaced to the project
owner before any execution; the owner explicitly confirmed correcting the local manifest and
proceeding. Both local files (`candidate-manifest.json` and `SOURCE_REVIEW.md`) were corrected to
the true digest before execution; no image content changed. This correction is local-only (both
files are git-ignored) and is disclosed here, in the sanitized JSON artifact's
`manifest_correction` field, and in the session record for auditability.

## Composition

Exactly 4 JPEG + 4 PNG, matching the approved Cohort B format contract:

| Image | Format | MIME | Declared dimensions | Bytes |
|---|---|---|---:|---:|
| B01 | JPEG | image/jpeg | 1254x1254 | 337,481 |
| B02 | JPEG | image/jpeg | 1254x1254 | 389,288 |
| B03 | JPEG | image/jpeg | 1254x1254 | 328,336 |
| B04 | JPEG | image/jpeg | 1254x1254 | 303,048 |
| B05 | PNG | image/png | 1254x1254 | 2,562,614 |
| B06 | PNG | image/png | 1254x1254 | 2,006,855 |
| B07 | PNG | image/png | 1254x1254 | 1,726,857 |
| B08 | PNG | image/png | 1254x1254 | 1,721,040 |

Dimensions were independently probed header-only (no full decode, no policy) directly from each
file and cross-checked against the D2 admission service's own decoded metadata for every sample;
both agreed on 1254x1254 for all 8 images across all 24 samples. Format was independently
confirmed from file signature (JPEG SOI marker / PNG signature), not merely from filename
extension or the manifest's declared value.

## Environment and revision

- Python: 3.12.10
- PyAV: 18.1.0
- FFmpeg libraries: libavcodec 62.28.102, libavformat 62.12.102, libavutil 60.26.102,
  libavfilter 11.14.102, libavdevice 62.3.102, libswscale 9.5.102, libswresample 6.3.102
- OS / architecture: Windows 11 / AMD64
- A single, consistent environment block was recorded across all 24 samples.
- D2 implementation cleanliness: the reviewed D2 admission implementation, its ports, its
  decoder adapter, `backend/pyproject.toml`, D2's own tests, and D2's fixture manifest were all
  verified to exactly match commit `9191565a8961aab1bd10b2a0aa3efff7aefdf998` (no uncommitted
  change) immediately before execution. This D3-R2 Cohort B harness extension itself
  (`backend/src/sketch2life/benchmark/image_admission_evaluation.py` and its test file) was
  implemented in this same working session and is not required to be committed before a Cohort B
  run, unlike Cohort A's later, fully committed formal run; only the D2 code actually being timed
  is required to match the declared commit exactly.
- Child protocol: one fresh subprocess per sample, current interpreter, bounded 64 KiB
  stdin/stdout/stderr, default 30-second parent-owned harness timeout (unmodified, unused --
  no sample approached it).

## Execution summary

- 8 images x 3 repeats = 24 samples; all 8 images fully covered.
- 24/24 exit code 0, 0 typed failures, 0 process failures, 0 memory-measurement failures.
- 24/24 unique sample identifiers (one fresh subprocess per sample).
- 24/24 `source_digest_verified: true`, 24/24 `artifact_ref_verified: true` (D2's `artifact_ref`
  carried only the opaque per-image ID; the real source path never appeared in any child result).
- 24/24 outcome `ADMITTED`, 0 rejections, 0 unsupported, 0 invalid-source, 0 processing failures.
- `complete: true` -- every image has exactly 3 valid, matching samples.

## Per-image results (sample_count = 3 each)

All timing values in milliseconds, minimum/median/maximum only -- Cohort B never reports p95 from
3 repeats (D3-U2). Memory values are the per-image maximum lower bound (L) and upper bound (U) of
the approved `[L, U]` native-working-set bracket in bytes.

| Image | Format | Min ms | Median ms | Max ms | Timing | Max L (bytes) | Max U (bytes) | Memory |
|---|---|---:|---:|---:|---|---:|---:|---|
| B01 | JPEG | 8.3074 | 8.6636 | 8.7248 | WITHIN_TARGET | 1,794,048 | 5,242,880 | WITHIN_TARGET |
| B02 | JPEG | 9.0432 | 9.0484 | 9.7009 | WITHIN_TARGET | 1,789,952 | 5,394,432 | WITHIN_TARGET |
| B03 | JPEG | 8.0992 | 8.4732 | 8.5336 | WITHIN_TARGET | 1,785,856 | 5,214,208 | WITHIN_TARGET |
| B04 | JPEG | 7.6721 | 8.1253 | 8.1496 | WITHIN_TARGET | 1,798,144 | 5,144,576 | WITHIN_TARGET |
| B05 | PNG | 107.6164 | 107.7520 | 108.2184 | WITHIN_TARGET | 1,757,184 | 14,204,928 | WITHIN_TARGET |
| B06 | PNG | 98.0326 | 100.6828 | 101.3834 | WITHIN_TARGET | 1,736,704 | 12,496,896 | WITHIN_TARGET |
| B07 | PNG | 92.3419 | 92.9876 | 93.0883 | WITHIN_TARGET | 1,744,896 | 11,673,600 | WITHIN_TARGET |
| B08 | PNG | 86.2650 | 86.8930 | 87.8845 | WITHIN_TARGET | 1,736,704 | 11,653,120 | WITHIN_TARGET |

JPEG images decode markedly faster (~8-10 ms) than the PNG images (~86-108 ms) at this
resolution; this is consistent with D1's documented limitation that photographic PNG content
compresses and decodes far less favorably than synthetic uniform test images, and is reported
here as an observation, not a target breach -- every value remains far inside the 5,000 ms target.

## Aggregate results (24 samples)

| Metric | Value |
|---|---|
| Sample count | 24 |
| Minimum elapsed | 7.6721 ms |
| Median elapsed | 47.98295 ms |
| Maximum elapsed | 108.2184 ms |
| Timing target status | WITHIN_TARGET |
| Max lower bound (L) | 1,798,144 bytes |
| Max upper bound (U) | 14,204,928 bytes |
| Memory target status | WITHIN_TARGET |
| Process failure count | 0 |
| Memory failure count | 0 |

The aggregate maximum upper bound (14,204,928 bytes, ~13.5 MiB) is approximately 19x under the
256 MiB (268,435,456-byte) target. The aggregate maximum elapsed time (108.2184 ms) is
approximately 46x under the 5,000 ms target. No sample or image produced `EXCEEDS_TARGET`,
`INCONCLUSIVE`, `NOT_MEASURED`, or `MEASUREMENT_INVALID` for either timing or memory.

## Target classification rules applied (D3-R2)

- Timing: `WITHIN_TARGET` only when every valid sample's `admission_elapsed_ms` is at or below
  5,000 ms; `EXCEEDS_TARGET` if any valid sample exceeds it. All 24 samples were within target.
- Memory: computed only from the conservative `[L, U]` bracket around
  `Feat018ImageAdmission.admit()` -- `U <= 256 MiB` proves `WITHIN_TARGET`, `L > 256 MiB` proves
  `EXCEEDS_TARGET`, otherwise `INCONCLUSIVE`. No peak-to-peak delta and no polling observation was
  used. Raw current/peak/private-usage values and `peak_saturated` were captured as diagnostics
  only in every sample and never affected classification.
- No per-sample or per-image status was spoofed or trusted from the child directly: the harness
  recomputes both classifications from the raw recorded fields during aggregation.

## Limitations

- Eight images is a diagnostic cohort, not a production-representative or statistically
  representative sample (D3-R2 section 6, D3-U2). No claim of camera-realism generality, and no
  claim about any other image, resolution, or device is made from this result.
- The 5,000 ms and 256 MiB figures remain observational evaluation targets, not enforced limits;
  this report makes no runtime-enforcement claim.
- Cohort B reports minimum/median/maximum only; p95 is intentionally never computed from 3
  repeats.
- This result says nothing about Qwen3-VL understanding quality, Gate A/B, mobile transport, or
  any other downstream FEAT-018 scope.

## Privacy and provenance

- The 8 raw Cohort B image files and the local `candidate-manifest.json` (and its companion
  `SOURCE_REVIEW.md`) remain under `tmp/feat018-cohort-b-input-20260912/`, which is Git-ignored.
  **They are not tracked in Git and are not part of this evidence.** Only this Markdown report and
  its sanitized JSON counterpart are tracked.
- No raw image bytes, absolute local machine paths, EXIF/private metadata, prompts, provider
  output, or secrets appear in either tracked artifact. Per-sample metadata is limited to the D2
  `ImageMetadataSignals` bounded technical fields only (container, codec, pixel format, width,
  height), the same fields already published in the owner-approved Cohort A evidence.
- D2's `artifact_ref` carried only the opaque per-image ID (for example `B01`) in every sample;
  `artifact_ref_verified: true` in all 24 samples proves the real source path was never used as
  the artifact reference.

## Validation results

| Command | Result |
|---|---|
| `pytest tests/unit/test_image_admission_evaluation.py tests/unit/test_image_admission.py` | 148 passed (119 pre-existing + 29 new Cohort B tests) |
| `ruff check` (harness + test file) | All checks passed |
| `mypy` (harness + test file, run together per this repo's `packages` config) | No issues found in 2 source files |
| `python tools/validate_harness.py` | `HARNESS_VALID` |
| `python tools/validate_repository_security.py` | `REPOSITORY_SECURITY_VALID` |
| `python tools/validate_architecture.py` | `ARCHITECTURE_VALID` |
| `python tools/validate_skeleton.py` | `SKELETON_VALID` |
| `git diff --check` | Clean, no output |

No dependency was changed. No D2 admission policy, outcome, limit, or public contract was
changed. No FEAT-003, provider, mobile, Gate A, or shared-integration file was touched.

## Evidence artifact

- Repository path: `metrics/P2_D3_COHORT_B_FORMAL_20260912.json`
- Exact byte count: 65,492
- Exact SHA-256: `9c1eadc1315757e2eaf0a26c2e50cd1ac027591ed6849e611a6bb9c474b04a1c`
- Cross-check: every aggregate and per-image value in this report was read directly from and
  matches this artifact's `aggregate` and `per_image` fields; no value here was inferred,
  recalculated, or estimated independently of the artifact.

## Final verdict

**PASS.** Formal Cohort B execution completed: 24/24 samples, all `ADMITTED`, `complete: true`,
`WITHIN_TARGET` for both timing and memory at every image and in aggregate, zero process or
measurement failures, zero redaction findings. This is a diagnostic result over 8 real
photographs, not a statistically representative or production benchmark. This report requires
owner review before it may be treated as canonical evidence, indexed, or used to recommend
D3/P2-T1 closure for Cohort B.
