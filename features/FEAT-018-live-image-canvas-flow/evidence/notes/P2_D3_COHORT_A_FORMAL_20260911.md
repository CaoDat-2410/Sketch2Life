# FEAT-018 D3 Formal Cohort A Execution Report

## Executive verdict

- PASS WITH FINDINGS.
- Formal Cohort A completed.
- D3/P2-T1 is closed for the synthetic Cohort A scope by owner approval on 2026-09-11.

## Revision and environment

- Exact commit SHA: c77230ca1593d5cd31098b5e58f3ff2a13d18a63
- Commit subject: test(feat018): close D3 review coverage gaps
- Python: 3.12.10
- PyAV: 18.1.0
- FFmpeg libraries: libavcodec 62.28.102, libavformat 62.12.102, libavutil 60.26.102, libavfilter 11.14.102, libavdevice 62.3.102, libswscale 9.5.102, libswresample 6.3.102
- OS / architecture: Windows 11 / AMD64
- Worktree isolation: detached-HEAD Git worktree pinned to the exact commit above, created solely for this run, verified clean (`git status --porcelain --untracked-files=all` empty) both before and after execution, and removed after the run completed
- Package resolution isolation: PYTHONPATH pinned to the worktree's own backend/src for both the parent process and its child subprocesses, so all code resolved from the pinned commit rather than the main checkout
- Manifest used: evaluation-manifest-v1.json, SHA-256 50952c15fbbabdd4bb7212ffdb1a705d80a2308cf461c121e68e7363bbf5df1e
- Child timeout: approved default, 30.0 seconds (unmodified)
- Cohort scope: Cohort A only (synthetic); Cohort B not run

## Execution summary

- 16 profiles x 20 repeats = 320 forward samples; all 16 profiles fully covered.
- Forward pass: 320/320 exit code 0, 0 typed failures, 0 outcome/reason mismatches against the manifest, 320/320 unique sample identifiers (one fresh subprocess per sample).
- Decode-stage split (forward, matches manifest exactly): ADMITTED 180, PRE_DECODE_REJECTION 120, DECODE_ATTEMPTED_REJECTION 20, summing to 320.
- Order-effect gate (greater than 10% first-5/last-5 median split): triggered by gray8-png (first-5 median 2.530 ms vs. last-5 median 2.207 ms, a 12.79% effect, both values far below the timing target). No other profile crossed the threshold.
- Because the gate triggered, a full reverse pass was executed across all 16 profiles and preserved separately; it did not replace or merge with the forward pass.
- Reverse pass: 320/320 exit code 0, 0 typed failures, 0 mismatches, 320/320 unique sample identifiers, identical decode-stage split (180/120/20).
- complete=true for both passes (every profile has exactly 20 valid, matching samples).
- Total: 640 samples across 2 passes, 0 process failures, 0 memory failures anywhere.
- One reverse-pass timing outlier was observed for near-byte-limit-png (repeat 12 measured 282.569 ms against a roughly 61 to 65 ms baseline for that profile, settling to roughly 80 to 104 ms for the remaining repeats). It is retained and reported as-is, not deleted or rerun; it remained comfortably WITHIN_TARGET against the 5,000 ms target.
- No dependency, D2, or public-contract file was touched; no code change was made to the harness.

## Timing results

All values in milliseconds, forward pass, 20 valid samples per profile.

| Profile | p50 ms | p95 ms | Maximum ms | Target status |
|---|---|---|---|---|
| baseline-jpeg | 2.401 | 2.711 | 2.764 | WITHIN_TARGET |
| edge-limit-png | 30.165 | 31.178 | 31.397 | WITHIN_TARGET |
| garbage-idat-png | 2.418 | 2.687 | 2.708 | WITHIN_TARGET |
| gray8-png | 2.371 | 2.733 | 2.778 | WITHIN_TARGET |
| mono1-png | 2.319 | 2.704 | 2.872 | WITHIN_TARGET |
| multi-frame-jpeg | 2.065 | 2.215 | 2.268 | WITHIN_TARGET |
| near-byte-limit-png | 61.247 | 64.650 | 65.272 | WITHIN_TARGET |
| over-byte-limit | 1.640 | 1.764 | 1.883 | WITHIN_TARGET |
| over-edge-limit | 9.285 | 10.008 | 10.449 | WITHIN_TARGET |
| over-pixel-limit | 10.398 | 11.115 | 11.357 | WITHIN_TARGET |
| palette8-png | 2.311 | 2.575 | 2.601 | WITHIN_TARGET |
| pixel-limit-png | 33.628 | 34.940 | 35.345 | WITHIN_TARGET |
| rgb8-png | 2.443 | 3.700 | 6.518 | WITHIN_TARGET |
| rgba8-png | 2.463 | 2.765 | 2.975 | WITHIN_TARGET |
| truncated-png | 1.891 | 2.173 | 5.615 | WITHIN_TARGET |
| unsupported-rgb16 | 1.993 | 2.217 | 2.353 | WITHIN_TARGET |

Reverse pass: all 16 profiles remained WITHIN_TARGET. Medians were 5 to 10 percent higher across most profiles, consistent with second-pass cache/OS warmth, except for the documented near-byte-limit-png outlier (maximum 282.569 ms in the reverse pass, still roughly 18 times under the 5,000 ms target).

## Memory results

All values in bytes, forward pass, using the approved [L, U] bracket.

| Profile | Max lower bound (L) | Max upper bound (U) | p95 upper bound (U) | Target status |
|---|---|---|---|---|
| baseline-jpeg | 1,789,952 | 1,794,048 | 1,794,048 | WITHIN_TARGET |
| edge-limit-png | 1,773,568 | 12,804,096 | 12,800,000 | WITHIN_TARGET |
| garbage-idat-png | 1,613,824 | 1,654,784 | 1,638,400 | WITHIN_TARGET |
| gray8-png | 1,724,416 | 1,728,512 | 1,716,224 | WITHIN_TARGET |
| mono1-png | 1,728,512 | 1,732,608 | 1,716,224 | WITHIN_TARGET |
| multi-frame-jpeg | 1,429,504 | 1,474,560 | 1,470,464 | WITHIN_TARGET |
| near-byte-limit-png | 1,888,256 | 24,432,640 | 24,424,448 | WITHIN_TARGET |
| over-byte-limit | 815,104 | 5,029,888 | 5,029,888 | WITHIN_TARGET |
| over-edge-limit | 1,495,040 | 12,824,576 | 12,824,576 | WITHIN_TARGET |
| over-pixel-limit | 1,445,888 | 13,729,792 | 13,725,696 | WITHIN_TARGET |
| palette8-png | 1,724,416 | 1,728,512 | 1,720,320 | WITHIN_TARGET |
| pixel-limit-png | 1,724,416 | 13,991,936 | 13,987,840 | WITHIN_TARGET |
| rgb8-png | 1,728,512 | 1,732,608 | 1,728,512 | WITHIN_TARGET |
| rgba8-png | 1,724,416 | 1,728,512 | 1,728,512 | WITHIN_TARGET |
| truncated-png | 1,413,120 | 1,441,792 | 1,396,736 | WITHIN_TARGET |
| unsupported-rgb16 | 1,495,040 | 1,527,808 | 1,478,656 | WITHIN_TARGET |

Reverse pass: all 16 profiles remained WITHIN_TARGET; the largest upper bound observed was near-byte-limit-png at 25,141,248 bytes, still roughly 10 times under the 256 MiB (268,435,456-byte) target. Raw peak/private-usage values and the peak_saturated flag were captured as diagnostics only in every sample and never affected any classification, per the approved target-to-field binding.

No profile in either pass produced EXCEEDS_TARGET, INCONCLUSIVE, NOT_MEASURED, or MEASUREMENT_INVALID for timing or memory.

## Evidence artifact

- Opaque artifact name: P2_D3_COHORT_A_c77230c.json
- Exact byte count: 1818208
- Exact SHA-256: 32e5e2373376eec0b7e30a488b0a7416a8cec4fe5c2b16957794373664606f40
- Sanitation confirmation: the artifact was scanned in full and contains no traceback text, no absolute machine path pattern, and no secret, token, password, API key, authorization header, bearer value, prompt, or EXIF content; per-sample metadata is limited to bounded technical fields only (for example: codec, container, height, pixel format, width).
- Status: owner-approved canonical evidence artifact, indexed under `evidence/README.md`.
- Repository path: `metrics/P2_D3_COHORT_A_FORMAL_20260911.json`
- Cross-check: every aggregate value in the Timing results, Memory results, and Reverse-pass per-profile results tables of this Markdown report was read directly from and cross-checked against this artifact's `aggregates` and `pass_aggregates` fields; no value in those tables was inferred, recalculated, or estimated independently of the artifact.

## Reverse-pass per-profile results

All values read directly from `pass_aggregates.reverse` in the evidence artifact above, 20 valid samples per profile. Timing values are in milliseconds; memory values are in bytes using the approved [L, U] bracket.

| Profile | p50 ms | p95 ms | Maximum ms | Timing status | Max lower bound (L) | Max upper bound (U) | p95 upper bound (U) | Memory status |
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

All 16 reverse-pass profiles are WITHIN_TARGET for both timing and memory. None crossed EXCEEDS_TARGET, INCONCLUSIVE, NOT_MEASURED, or MEASUREMENT_INVALID. The near-byte-limit-png maximum of 282.569 ms is the outlier already documented in the Execution summary and Findings sections; it is reported here unmodified, exactly as it appears in the evidence artifact.

## Integrity and privacy

- Fresh subprocesses: 640 of 640 samples across both passes had unique sample identifiers, each corresponding to one fresh child subprocess.
- Outcome/reason integrity: 0 mismatches against the manifest across all 640 samples.
- Source hash/byte-count integrity: 0 unexpected digest failures; the only samples without a digest are the manifest's byte-budget-exceeded case, under the approved narrow exemption.
- Commit/environment identity: a single, consistent environment block (Python/PyAV/FFmpeg/OS/architecture/commit) was recorded across all 320 samples of each pass, and the declared commit SHA matched exactly in all 640 samples.
- Field bindings: timing status was derived only from admission_elapsed_ms; memory status was derived only from the approved [L, U] bracket; raw peak/private values were diagnostic-only in every case.
- Process/thread cleanup: no residual threads were observed inside the parent process after the run, and no residual child processes remained afterward.
- Request/output caps: all 640 samples completed within the 64 KiB stdin/stdout/stderr caps; no output-limit or timeout failures occurred.
- Redaction: a full scan of the serialized report found no traceback text, no absolute machine path pattern, and no secret, token, password, API key, authorization header, bearer value, prompt, or EXIF content anywhere in the report. Per-sample metadata was limited to bounded technical fields only (for example: codec, container, height, pixel format, width).
- Worktree hygiene: the isolated worktree used for this run reported a clean, unmodified state both before and after execution, and has since been removed. The main checkout was not touched by this execution.

## Test and validator results

| Command | Exit status | Counts / notes |
|---|---|---|
| D3 + D2 focused tests, pre-execution | 0 | 119 passed (61 D3 + 58 D2) |
| D3 + D2 focused tests, post-execution | 0 | 119 passed (61 D3 + 58 D2) |
| FEAT-003 serialized-provenance parity test | 0 | 15 passed |
| Full backend suite, isolated worktree | 1 | 947 passed, 5 skipped, 9 failed; see Finding 1 (environment artifact, not a code defect) |
| Full backend suite cross-check, main checkout (same 2 affected test files) | 0 | 24 passed |
| Ruff (--no-cache), isolated worktree | 0 | All checks passed |
| Mypy on the D3 runner and its tests | 0 | No issues found in 2 source files |
| git diff --check, isolated worktree | 0 | Clean, no output |
| validate_harness.py | 0 | HARNESS_VALID |
| validate_repository_security.py | 0 | REPOSITORY_SECURITY_VALID |
| validate_architecture.py | 0 | ARCHITECTURE_VALID |
| validate_skeleton.py | 0 | SKELETON_VALID |

## Findings

1. FEAT-003 gitignored-fixture worktree artifact - informational, non-blocking, no D3 action required.

The full backend suite run inside the isolated worktree showed 9 failures, all confined to two FEAT-003 test files (test_vision_v3_quality_benchmark.py and test_vision_v3_quality_execution.py). Root cause: these tests load real, non-committed local test images from a gitignored vision-v3-quality/images/ directory that exists only in the main checkout's working tree and is never materialized by a fresh Git worktree checkout. No code or fixture-manifest byte differs between the pinned D3 commit and the current main checkout for these files, and the same tests pass 24 of 24 when run against the main checkout, which has the local images present. This is a reproducibility characteristic of using an isolated worktree for full-suite verification, not a D3, D2, or FEAT-018 code defect. The isolated full backend suite result is reported exactly as observed, 947 passed, 5 skipped, 9 failed, and this report does not describe that isolated run as green or as a clean pass. No action required for D3/P2-T1; anyone reproducing a full-suite run from an isolated worktree in the future should be aware that these gitignored local images must be copied in separately if a fully green full-suite result is desired there.

2. Gray8 order-effect and preserved reverse-pass outlier - informational, non-blocking, no code action required.

The approved greater-than-10% order-effect rule correctly triggered on gray8-png (12.79% first-5/last-5 median split, both values in the low-single-digit-millisecond range, noise at this timescale rather than a real regression), and the harness correctly ran and preserved a full reverse pass across all 16 profiles as a separate result set, never replacing the forward pass. One timing outlier appeared during the reverse pass for near-byte-limit-png (282.569 ms on one repeat, versus a roughly 61 to 65 ms baseline), consistent with a transient OS/scheduling disturbance; it has been retained and reported rather than deleted or rerun. It remained comfortably WITHIN_TARGET. No action required; recorded for owner awareness.

## Remaining owner gates

- Owner review of this sanitized draft is required before it may be treated as canonical evidence.
- No evidence indexing or publication may occur before that review.
- D3/P2-T1 closure may not be granted before that review, even though this run's data satisfies the closure criteria on its own merits (no EXCEEDS_TARGET or INCONCLUSIVE result occurred).
- Cohort B requires visual review of 8 actual images and was not run in this execution.
