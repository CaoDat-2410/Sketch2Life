# FEAT-018 D3 Formal Cohort A - Independent Verification Report

## Executive verdict

- PASS.
- Independent re-derivation from the raw 640-sample artifact found zero discrepancies against
  the artifact's own aggregates, the `pass_aggregates.forward` / `pass_aggregates.reverse`
  blocks, and every value transcribed into the Markdown execution report
  (`P2_D3_COHORT_A_FORMAL_DRAFT_20260911.md`).
- This verification did not rerun Cohort A or Cohort B and did not modify D2, FEAT-003, code,
  tests, plans, approvals or the evidence index.
- Owner review of the sanitized artifact and report was completed on 2026-09-11. This closes
  D3/P2-T1 for synthetic Cohort A only; Cohort B remains gated.

## Artifact identity

| Item | Expected | Observed | Match |
|---|---|---|---|
| Artifact file | `P2_D3_COHORT_A_c77230c.json` | Located in an approved local scratch/output directory (not in tracked repository content) | yes |
| Byte count | 1818208 | 1818208 | yes |
| SHA-256 | 32e5e2373376eec0b7e30a488b0a7416a8cec4fe5c2b16957794373664606f40 | 32e5e2373376eec0b7e30a488b0a7416a8cec4fe5c2b16957794373664606f40 | yes |
| Manifest SHA-256 | 50952c15fbbabdd4bb7212ffdb1a705d80a2308cf461c121e68e7363bbf5df1e | 50952c15fbbabdd4bb7212ffdb1a705d80a2308cf461c121e68e7363bbf5df1e (recomputed from the committed manifest file) | yes |
| Commit identity (`commit_identity`, top-level and every sample's `environment.commit_identity`) | c77230ca1593d5cd31098b5e58f3ff2a13d18a63 | c77230ca1593d5cd31098b5e58f3ff2a13d18a63 in all 640 samples, single consistent value | yes |
| Commit exists in repository history | required | `c77230c test(feat018): close D3 review coverage gaps` confirmed via `git log` | yes |

The artifact was not reconstructed or invented; it was located, read and hashed as-is.

## Schema and sample integrity

- `schema` = `Feat018ImageAdmissionEvaluationReportV1`, `cohort` = `A`, `complete` = `true`,
  `reverse_pass_required` = `true`, `repeats` = `20`. All as expected.
- Exactly 2 passes present, `pass_id` values `forward` and `reverse`.
- Forward pass: 320 samples; Reverse pass: 320 samples. Total 640.
- Both passes cover the same 16 profiles (`profile_order` sets identical), 20 samples per
  profile per pass, with no missing or extra profile.
- Sample-ID uniqueness: 0 duplicate `sample_id` values within either pass and 0 collisions
  between passes (forward IDs use the `cohort-a:` prefix, reverse IDs use `cohort-a-reverse:`).
- `exit_code` = 0 for all 640 samples; 0 samples with a non-null `measurement_failure` or
  `measurement_error_code`.
- `outcome` == `expected_outcome` and `reason` == `expected_reason` for all 640 samples (0
  mismatches against the manifest-declared expectations).
- `artifact_ref_verified` = `true` for all 640 samples.
- `source_digest_verified` = `true` for every sample that carries a `source_sha256`. Exactly 40
  samples have a null `source_sha256` (20 forward + 20 reverse), and all 40 belong to the
  `over-byte-limit` fixture with `expected_reason` = `FILE_BYTES_EXCEEDED` - the single documented,
  narrow exemption. No other fixture is missing a digest.
- Exactly one consistent `environment` block (architecture, commit, FFmpeg library versions, OS,
  OS release, PyAV, Python) was observed across all 640 samples.
- Per-sample memory recomputation: for every one of the 640 samples,
  `L = max(0, working_set_after_bytes - working_set_before_bytes)` and
  `U = max(0, peak_after_bytes - working_set_before_bytes)` were recomputed independently from the
  raw fields and compared to the stored `memory_lower_bound_bytes` / `memory_upper_bound_bytes`.
  0 mismatches. No sample has `peak_after_bytes < peak_before_bytes` (which would require
  `MEASUREMENT_INVALID`).
- All 640 `source_sha256` values (where present) are well-formed 64-character lowercase hex
  strings; all `source_bytes` values are plain integers, never raw byte content.

## Recomputed forward aggregates

p50/p95 (nearest-rank, nsigma-free rule: `ceil(0.95*n)-1`, zero-based) and maximum were
recomputed directly from the 20 raw `admission_elapsed_ms` values per profile; memory bounds were
recomputed from the raw per-sample `L`/`U` values derived above. Every cell below was compared
byte-for-byte / bit-for-bit against `pass_aggregates.forward` (equivalently the top-level
`aggregates`, which are identical to `pass_aggregates.forward`) and against the Markdown report's
Timing/Memory tables. All values matched exactly.

| Profile | p50 ms | p95 ms | Max ms | Timing status | L bytes | U bytes | U p95 bytes | Memory status |
|---|---|---|---|---|---|---|---|---|
| baseline-jpeg | 2.401 | 2.711 | 2.764 | WITHIN_TARGET | 1,789,952 | 1,794,048 | 1,794,048 | WITHIN_TARGET |
| edge-limit-png | 30.165 | 31.178 | 31.397 | WITHIN_TARGET | 1,773,568 | 12,804,096 | 12,800,000 | WITHIN_TARGET |
| garbage-idat-png | 2.418 | 2.687 | 2.708 | WITHIN_TARGET | 1,613,824 | 1,654,784 | 1,638,400 | WITHIN_TARGET |
| gray8-png | 2.371 | 2.733 | 2.7775 | WITHIN_TARGET | 1,724,416 | 1,728,512 | 1,716,224 | WITHIN_TARGET |
| mono1-png | 2.319 | 2.704 | 2.872 | WITHIN_TARGET | 1,728,512 | 1,732,608 | 1,716,224 | WITHIN_TARGET |
| multi-frame-jpeg | 2.065 | 2.215 | 2.268 | WITHIN_TARGET | 1,429,504 | 1,474,560 | 1,470,464 | WITHIN_TARGET |
| near-byte-limit-png | 61.247 | 64.650 | 65.272 | WITHIN_TARGET | 1,888,256 | 24,432,640 | 24,424,448 | WITHIN_TARGET |
| over-byte-limit | 1.640 | 1.764 | 1.883 | WITHIN_TARGET | 815,104 | 5,029,888 | 5,029,888 | WITHIN_TARGET |
| over-edge-limit | 9.285 | 10.008 | 10.449 | WITHIN_TARGET | 1,495,040 | 12,824,576 | 12,824,576 | WITHIN_TARGET |
| over-pixel-limit | 10.398 | 11.115 | 11.357 | WITHIN_TARGET | 1,445,888 | 13,729,792 | 13,725,696 | WITHIN_TARGET |
| palette8-png | 2.311 | 2.575 | 2.601 | WITHIN_TARGET | 1,724,416 | 1,728,512 | 1,720,320 | WITHIN_TARGET |
| pixel-limit-png | 33.628 | 34.940 | 35.345 | WITHIN_TARGET | 1,724,416 | 13,991,936 | 13,987,840 | WITHIN_TARGET |
| rgb8-png | 2.443 | 3.700 | 6.518 | WITHIN_TARGET | 1,728,512 | 1,732,608 | 1,728,512 | WITHIN_TARGET |
| rgba8-png | 2.463 | 2.765 | 2.974 | WITHIN_TARGET | 1,724,416 | 1,728,512 | 1,728,512 | WITHIN_TARGET |
| truncated-png | 1.891 | 2.173 | 5.615 | WITHIN_TARGET | 1,413,120 | 1,441,792 | 1,396,736 | WITHIN_TARGET |
| unsupported-rgb16 | 1.993 | 2.217 | 2.353 | WITHIN_TARGET | 1,495,040 | 1,527,808 | 1,478,656 | WITHIN_TARGET |

Note: the raw stored maximum for `gray8-png` forward is exactly `2.7775` ms. Standard
round-half-up display rounds this to the Markdown report's `2.778`; this is a display-rounding
convention only, not a numeric discrepancy - the underlying raw value and the JSON aggregate agree
exactly with the recomputation.

All 16 forward-pass profiles are `WITHIN_TARGET` for both timing and memory. 0 `EXCEEDS_TARGET`,
`INCONCLUSIVE`, `NOT_MEASURED` or `MEASUREMENT_INVALID` results in the forward pass.

## Recomputed reverse aggregates

Identical independent method applied to the 320 reverse-pass samples, compared against
`pass_aggregates.reverse` and the Markdown report's reverse-pass table.

| Profile | p50 ms | p95 ms | Max ms | Timing status | L bytes | U bytes | U p95 bytes | Memory status |
|---|---|---|---|---|---|---|---|---|
| baseline-jpeg | 2.711 | 3.245 | 4.129 | WITHIN_TARGET | 1,781,760 | 1,785,856 | 1,781,760 | WITHIN_TARGET |
| edge-limit-png | 32.119 | 34.063 | 34.485 | WITHIN_TARGET | 1,781,760 | 12,808,192 | 12,804,096 | WITHIN_TARGET |
| garbage-idat-png | 2.510 | 2.796 | 2.859 | WITHIN_TARGET | 1,576,960 | 1,617,920 | 1,605,632 | WITHIN_TARGET |
| gray8-png | 2.361 | 2.803 | 2.868 | WITHIN_TARGET | 1,708,032 | 1,712,128 | 1,712,128 | WITHIN_TARGET |
| mono1-png | 2.602 | 3.204 | 3.365 | WITHIN_TARGET | 1,765,376 | 1,769,472 | 1,748,992 | WITHIN_TARGET |
| multi-frame-jpeg | 2.131 | 2.420 | 2.544 | WITHIN_TARGET | 1,429,504 | 1,474,560 | 1,470,464 | WITHIN_TARGET |
| near-byte-limit-png | 64.383 | 103.825 | 282.569 | WITHIN_TARGET | 2,617,344 | 25,141,248 | 24,420,352 | WITHIN_TARGET |
| over-byte-limit | 1.714 | 1.890 | 1.918 | WITHIN_TARGET | 815,104 | 5,029,888 | 5,025,792 | WITHIN_TARGET |
| over-edge-limit | 9.568 | 9.986 | 11.252 | WITHIN_TARGET | 1,437,696 | 12,824,576 | 12,824,576 | WITHIN_TARGET |
| over-pixel-limit | 10.510 | 10.983 | 11.117 | WITHIN_TARGET | 1,495,040 | 13,729,792 | 13,725,696 | WITHIN_TARGET |
| palette8-png | 2.461 | 2.817 | 2.867 | WITHIN_TARGET | 1,753,088 | 1,757,184 | 1,753,088 | WITHIN_TARGET |
| pixel-limit-png | 35.572 | 35.929 | 36.333 | WITHIN_TARGET | 1,753,088 | 14,028,800 | 13,987,840 | WITHIN_TARGET |
| rgb8-png | 2.469 | 2.723 | 3.130 | WITHIN_TARGET | 1,769,472 | 1,773,568 | 1,761,280 | WITHIN_TARGET |
| rgba8-png | 2.410 | 2.817 | 2.928 | WITHIN_TARGET | 1,699,840 | 1,703,936 | 1,703,936 | WITHIN_TARGET |
| truncated-png | 2.004 | 2.249 | 2.561 | WITHIN_TARGET | 1,421,312 | 1,449,984 | 1,400,832 | WITHIN_TARGET |
| unsupported-rgb16 | 2.030 | 2.187 | 2.213 | WITHIN_TARGET | 1,482,752 | 1,515,520 | 1,474,560 | WITHIN_TARGET |

All 16 reverse-pass profiles are `WITHIN_TARGET` for both timing and memory. The
`near-byte-limit-png` maximum of 282.569 ms recomputes exactly from the raw samples and is 0
INCONCLUSIVE / EXCEEDS_TARGET; it remains roughly 18x under the 5,000 ms target, matching the
original report's characterization of this value as a retained, unmodified outlier.

## Order-effect verification

- Forward-pass `gray8-png`, 20 raw samples sorted by `repeat_index`.
- First-5 median (`a`) recomputed: 2.5302 ms.
- Last-5 median (`b`) recomputed: 2.2066 ms.
- `abs(a - b) / max(a, b)` recomputed: 12.79%.
- This exceeds the approved 10% order-effect gate, exactly reproducing the original report's
  trigger condition and matching its stated 12.79% figure.
- No other profile's first-5/last-5 split was checked against the gate by the original report
  (the gate is defined only to decide whether the reverse pass proceeds, not as a per-profile
  report field); the reverse pass covering all 16 profiles is present and independently confirmed
  complete (320/320 samples, above).

## Privacy and cleanup verification

- Regex/content scan of the full JSON artifact and the full Markdown report for: Windows and Unix
  absolute path patterns, Python traceback markers, EXIF references, bearer tokens, authorization
  headers, and generic API-key/secret/password/token key-value patterns. 0 matches in the JSON.
  The only two matches in the Markdown are the words "EXIF" and "prompt" appearing inside the
  report's own sanitation-confirmation sentences (e.g. "no ... EXIF content"), not leaked data.
- Scan for embedded raw byte content (base64-like runs of 200+ characters): 0 found. Every
  `source_bytes` field is a plain integer byte count, never raw bytes.
- Full enumeration of all JSON field names present in the artifact: every field is a bounded
  technical value (codec, container, height, width, pixel_format, timing/memory numbers, typed
  status enums, opaque IDs, environment/version strings) or a null; no field carries a file path,
  prompt text, model/provider identifier, or credential-shaped value.
- Scan for provider/model terms (`qwen`, `runpod`, `lightning`, `whisper`, `asr`): 0 matches in
  either file, consistent with D3's Cohort-A-only, no-provider scope.
- Process/thread cleanup: after running the required test/validator commands below, `tasklist`
  showed no running `python.exe` or `py.exe` processes. This verification pass launched only
  synchronous, already-completed subprocesses (pytest, ruff, mypy, the four validators); none were
  left running.
- Working-tree cleanliness: this verification created two temporary pytest `--basetemp` scratch
  directories under `backend/`; both were deleted immediately after the test runs completed.
  `git status --short` after cleanup shows only the pre-existing untracked
  `P2_D3_COHORT_A_FORMAL_DRAFT_20260911.md` file that was already present before this verification
  began; no other file was added, modified or staged.

## Tests and validators

All commands were run from the current repository checkout (branch
`feature/feat018-p2-image-validation`), not from a re-created isolated worktree, and none of them
re-executed the Cohort A/B benchmark itself.

| Command | Exit status | Result |
|---|---|---|
| `pytest tests/unit/test_image_admission_evaluation.py tests/unit/test_image_admission.py` (D3 + D2 focused) | 0 | 119 passed (61 D3 + 58 D2), matches report |
| `pytest tests/unit/test_media_validation.py` (FEAT-003 serialized-provenance parity test) | 0 | 15 passed, matches report |
| `ruff check --no-cache src tests` | 0 | All checks passed |
| `mypy src/sketch2life/benchmark/image_admission_evaluation.py tests/unit/test_image_admission_evaluation.py` | 0 | Success: no issues found in 2 source files |
| `git diff --check` | 0 | Clean, no output |
| `python tools/validate_harness.py` | 0 | HARNESS_VALID |
| `python tools/validate_repository_security.py` | 0 | REPOSITORY_SECURITY_VALID |
| `python tools/validate_architecture.py` | 0 | ARCHITECTURE_VALID |
| `python tools/validate_skeleton.py` | 0 | SKELETON_VALID |

The full isolated-worktree backend suite and its main-checkout cross-check were not rerun in this
verification pass (not part of the required command list above, and rerunning would duplicate
execution-adjacent work outside this task's scope). Per instruction, their previously observed
results are preserved as-is and are not recharacterized here: 947 passed, 5 skipped, 9
environmental failures in the isolated worktree (both affected files confined to FEAT-003's
gitignored local-image dependency, not a D3/D2/FEAT-018 defect), and 24/24 passed on the
main-checkout cross-check of the same two files.

## Findings

0 new discrepancies were produced by this independent verification. Every recomputed statistic,
every schema/identity check, every sample-level integrity check, and every required test/validator
matched the artifact and the Markdown report exactly.

Two informational, non-blocking findings already disclosed in the original execution report are
carried forward unchanged (not re-litigated, not resolved, not newly discovered here):

1. FEAT-003 gitignored-fixture worktree artifact - the isolated-worktree full backend suite showed
   9 failures confined to two FEAT-003 test files that depend on gitignored local images absent
   from a fresh worktree checkout; the same tests pass 24/24 against the main checkout. No D3, D2
   or FEAT-018 action required.
2. Gray8 order-effect and preserved reverse-pass outlier - the approved >10% order-effect rule
   correctly triggered on `gray8-png` (12.79%, both medians in the low-single-digit-millisecond
   range); the reverse pass was correctly run and preserved separately. One reverse-pass timing
   outlier on `near-byte-limit-png` (282.569 ms on one repeat) was retained and reported, not
   deleted or rerun, and remained comfortably `WITHIN_TARGET`.

## Remaining owner gates

- Owner review of the sanitized artifact and Markdown execution report was completed on 2026-09-11.
- Evidence indexing/publication is authorized by the owner approval recorded in FEAT-018 governance.
- D3/P2-T1 is closed for synthetic Cohort A only; this does not authorize Cohort B or downstream
  integration scopes.
- Cohort B still requires visual review of the 8 actual candidate images and was not run or
  addressed by this verification.
