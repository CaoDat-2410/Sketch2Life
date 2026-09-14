# FEAT-018 D3 Formal Cohort B - Independent Verification Report

## Executive verdict

**PASS WITH FINDINGS.**

Independent re-derivation from the raw 24-sample artifact, the local approved inputs, and the
committed runner source found **zero discrepancies** in any data value: every hash, byte count,
per-image and aggregate minimum/median/maximum, target classification, and Markdown/JSON
cross-reference recomputes exactly as published. The Formal Cohort B result itself (24/24
`ADMITTED`, `WITHIN_TARGET` for timing and memory throughout, `complete: true`) is confirmed
accurate.

Two findings were produced by this verification's code review of the runner (not previously
disclosed in the original execution report), plus one informational design note. None of the three
change, weaken, or contradict any published number; they concern the completeness of a
reproducibility safeguard and test-coverage depth, not correctness of the executed measurement.
See **Findings** below.

This verification did not rerun Cohort B or Cohort A, and did not modify code, tests, existing
reports, metrics, approval records, indexes, context, decisions, plans, local images, or the local
manifest.

## Commit identities and verification scope

| Role | Commit | Subject | Verified |
|---|---|---|---|
| Measured D2 implementation commit (`commit_identity` in the report) | `9191565a8961aab1bd10b2a0aa3efff7aefdf998` | `docs(feat018): record blocked Cohort B execution` | Confirmed a real commit object (`git cat-file -t` = `commit`); confirmed ancestor of both commits below |
| Cohort B runner commit | `73a88bed00c126859ba85971d49065febd2d1d65` | `feat(feat018): add Cohort B evaluation runner and tests` | Confirmed a real commit object; confirmed `9191565` is its ancestor |
| Evidence commit (verification target) | `5c22a92a1ab58b6a5a1e9fce7535b1a1a7220b73` | `docs(feat018): publish Formal Cohort B execution evidence` | Confirmed a real commit object; confirmed `73a88be` is its ancestor; confirmed equal to current `HEAD` |

These three commits are correctly distinct and correctly ordered: the D2 implementation actually
measured (`9191565`) predates the harness code that measured it (`73a88be`), which predates the
commit that published the resulting evidence (`5c22a92`). This is consistent with the report's own
statement that the Cohort B harness extension was implemented in the same working session as
execution and was not required to be pre-committed, unlike the D2 code it measures, which was
required to (and did) already exactly match a clean, prior commit.

`git status` at the time of this verification: working tree clean, `HEAD` at `5c22a92`, branch
`feature/feat018-p2-image-validation` up to date with `origin/feature/feat018-p2-image-validation`.

## 1. Local approved-input recomputation (independent of manifest and JSON)

All eight files under `tmp/feat018-cohort-b-input-20260912/` were re-hashed directly with a
freshly written script that does not import or call any function from
`image_admission_evaluation.py` for this step.

| Image | Format | Bytes (actual) | SHA-256 (actual, recomputed) | Manifest match | JSON match | Magic bytes | Extension |
|---|---|---:|---|---|---|---|---|
| B01 | JPEG | 337,481 | `c60faed3...68ab9cc3` | yes | yes | `FF D8 FF` | `.jpg` |
| B02 | JPEG | 389,288 | `65852906...cdeed478278a` | yes | yes | `FF D8 FF` | `.jpg` |
| B03 | JPEG | 328,336 | `77fcd37d...d37d95930522` | yes | yes | `FF D8 FF` | `.jpg` |
| B04 | JPEG | 303,048 | `60ba1d6f...762a81d31452404f` | yes | yes | `FF D8 FF` | `.jpg` |
| B05 | PNG | 2,562,614 | `54341d96...0603bb3dec7` | yes | yes | `89 50 4E 47 0D 0A 1A 0A` | `.png` |
| B06 | PNG | 2,006,855 | `2acc86ac...2fb8f8f7d8` | yes | yes | `89 50 4E 47 0D 0A 1A 0A` | `.png` |
| B07 | PNG | 1,726,857 | `a5d074a6...647a6c6b337aca` | yes | yes | `89 50 4E 47 0D 0A 1A 0A` | `.png` |
| B08 | PNG | 1,721,040 | `6f1986d7...4e762cdd0066dabc8` | yes | yes | `89 50 4E 47 0D 0A 1A 0A` | `.png` |

- Composition recomputed directly from the 8 actual files: **exactly 4 JPEG + 4 PNG**, matching
  both the manifest and the tracked JSON's `composition` field.
- **B08 digest check (explicit)**: the local manifest and `SOURCE_REVIEW.md` both now record
  `6f1986d771013357fd5d5bdc595131cbe4c96e3cef577ba4e762cdd0066dabc8` -- confirmed **64 hexadecimal
  characters**, and confirmed byte-for-byte equal to `hashlib.sha256` of the actual on-disk file.
  The tracked JSON's `manifest_correction` block (`fixture_id: B08`, `before_hex_length: 63`,
  `after_hex_length: 64`) accurately describes this fix; no other manifest entry required
  correction (all other 7 recomputed hashes matched their manifest entries with no edit needed).
- Manifest-level integrity: `manifest.owner_reviewed == true`, `manifest.execution_authorized ==
  true`, and the tracked JSON's `manifest_sha256` (`18d760e3...bcf6cd0ea`) matches
  `hashlib.sha256` of the current local `candidate-manifest.json` file exactly.
- `TASK_APPROVAL.md`'s "Owner approval and Cohort B source admission - 2026-09-12" addendum names
  the exact B01-B08 set and the exact input directory
  (`tmp/feat018-cohort-b-input-20260912/`); it does not itself embed per-file hashes (by design --
  it defers to the manifest), so the addendum's authorization is necessarily scoped to whatever
  set the manifest identifies. Since the manifest identifies these exact 8 files by their true,
  now-corrected hashes, the addendum's approval applies to the exact B01-B08 hashes actually
  executed.

## 2. JSON re-parse and top-level execution facts

Parsed independently with the stdlib `json` module (not via any harness helper).

| Field | Expected | Observed | Match |
|---|---|---|---|
| `execution_occurred` | `true` | `true` | yes |
| `complete` | `true` | `true` | yes |
| `sample_count` | `24` | `24` | yes |
| `repeats_per_image` | `3` | `3` | yes |
| `expected_image_count` | `8` | `8` | yes |
| `len(samples)` | `24` | `24` | yes |
| Unique `sample_id` count | `24` | `24` (0 collisions) | yes |
| Samples per fixture (B01-B08) | `3` each | `3` each, `repeat_index` values `{0,1,2}` for every image | yes |
| Distinct `outcome` values | `{"ADMITTED"}` | `{"ADMITTED"}` | yes |
| Distinct `reason` values | `{None}` | `{None}` | yes |
| Distinct `exit_code` values | `{0}` | `{0}` | yes |
| Distinct `measurement_failure` values | `{None}` | `{None}` | yes |
| `source_digest_verified` | `true` x24 | `true` x24 | yes |
| `artifact_ref_verified` | `true` x24 | `true` x24 | yes |
| Distinct environment blocks | `1` | `1` (Python 3.12.10, PyAV 18.1.0, identical FFmpeg library set, Windows 11 / AMD64) | yes |
| `environment.commit_identity` (all samples) | `9191565a89...` | `9191565a89...` (single value, all 24) | yes |
| Any `ChildFailure` value present anywhere (`INVALID_REQUEST`, `MEMORY_API_FAILURE`, `CHILD_PROTOCOL_FAILURE`, `ABNORMAL_EXIT`, `HARNESS_TIMEOUT`, `OUTPUT_LIMIT_EXCEEDED`, `PROCESS_CLEANUP_FAILED`) | none | none found in any of the 24 `failure` fields | yes |

Zero process, timeout, protocol, cleanup, or measurement failures confirmed across all 24 samples.

## 3. Independent per-image and aggregate recomputation

For every image, `admission_elapsed_ms` across its 3 raw samples was sorted and reduced with plain
`min()`/`statistics.median()`/`max()`; native-memory bounds were recomputed per sample as
`L = max(0, working_set_after_bytes - working_set_before_bytes)` and
`U = max(0, peak_after_bytes - working_set_before_bytes)`, then reduced to per-image and aggregate
maxima. None of this reused `summarize_cohort_b` or `aggregate_cohort_b_group` from the module
under audit.

| Image | Format | Min ms | Median ms | Max ms | Recomputed match | Max L (bytes) | Max U (bytes) | Recomputed match |
|---|---|---:|---:|---:|---|---:|---:|---|
| B01 | JPEG | 8.3074 | 8.6636 | 8.7248 | exact | 1,794,048 | 5,242,880 | exact |
| B02 | JPEG | 9.0432 | 9.0484 | 9.7009 | exact | 1,789,952 | 5,394,432 | exact |
| B03 | JPEG | 8.0992 | 8.4732 | 8.5336 | exact | 1,785,856 | 5,214,208 | exact |
| B04 | JPEG | 7.6721 | 8.1253 | 8.1496 | exact | 1,798,144 | 5,144,576 | exact |
| B05 | PNG | 107.6164 | 107.7520 | 108.2184 | exact | 1,757,184 | 14,204,928 | exact |
| B06 | PNG | 98.0326 | 100.6828 | 101.3834 | exact | 1,736,704 | 12,496,896 | exact |
| B07 | PNG | 92.3419 | 92.9876 | 93.0883 | exact | 1,744,896 | 11,673,600 | exact |
| B08 | PNG | 86.2650 | 86.8930 | 87.8845 | exact | 1,736,704 | 11,653,120 | exact |
| **Aggregate (24)** | - | 7.6721 | 47.98295 | 108.2184 | exact | 1,798,144 | 14,204,928 | exact |

No `p50`/`p95` key is present anywhere in `per_image[*].aggregate` or the top-level `aggregate`,
confirmed by direct key inspection -- Cohort B correctly never reports a percentile from 3 repeats.

Every one of the 24 individual samples was also independently re-checked (not just the per-image
maxima): its own `memory_lower_bound_bytes`/`memory_upper_bound_bytes` against its own raw
before/after fields, its own `peak_before/after >= working_set_before/after` and
`peak_after >= peak_before` monotonicity invariants, and that every raw memory field is a positive
integer. Zero mismatches and zero invariant violations across all 24 samples.

## 4. Independent target classification (D3-R2)

Applied directly from raw fields, without calling `classify_timing`/`classify_memory` from the
module under audit:

- **Timing**: `WITHIN_TARGET` iff every valid sample's `admission_elapsed_ms <= 5000`;
  `EXCEEDS_TARGET` if any exceeds it. All 24 raw values are between 7.6721 ms and 108.2184 ms,
  so every image and the aggregate independently classify as `WITHIN_TARGET` -- exactly matching
  the published `timing_status` in every case (8 per-image + 1 aggregate = 9/9 match).
- **Memory**: `U <= 268,435,456` (256 MiB) proves `WITHIN_TARGET`; `L > 268,435,456` proves
  `EXCEEDS_TARGET`; otherwise `INCONCLUSIVE`. Every image's recomputed `U` (maximum 14,204,928
  bytes, for B05) is far under the 256 MiB target, so every image and the aggregate independently
  classify as `WITHIN_TARGET` -- exactly matching the published `memory_status` in every case (9/9
  match). No sample or group fell into the `INCONCLUSIVE` band, and none was misreported as such.
- Raw `peak_saturated`, current/peak/private-usage values were confirmed present only as
  diagnostics and never referenced by the classification recomputation above, consistent with the
  approved target-to-field binding.
- Every sample's own decoded `metadata.width`/`metadata.height` (produced by D2 inside the timed
  `admit()` call) was cross-checked against the report's independently-probed
  `per_image[*].declared_width`/`declared_height` (produced by the parent harness before spawning
  any child). All 24 samples agree: `1254 x 1254`, both format families.

## 5. Markdown / JSON parity

Every row of the Markdown "Per-image results" table was parsed with a regular expression and
compared field-by-field (format, min, median, max, timing status, max L, max U, memory status)
against `per_image[*].aggregate` in the JSON: **8/8 rows match exactly**, including the comma
formatting collapsing to identical numeric values. The "Aggregate results" table's six data points
(sample count, minimum/median/maximum elapsed, timing status, memory status) all appear verbatim
in the JSON's `aggregate` block. `commit_identity` and `manifest_sha256` both appear verbatim in
the Markdown text. The Markdown's stated evidence byte count (65,492) and SHA-256
(`9c1eadc1...4b04a1c`) were independently recomputed from the JSON file as committed and match
exactly. The Markdown's `manifest_correction` narrative (63 -> 64 characters, B08, trailing `8`)
matches the JSON's `manifest_correction` object field-for-field. The Markdown's stated limitations
(diagnostic cohort, observational targets, no p95, no downstream-scope claim) all correspond to
literal strings present in the JSON's `limitations` array.

**Result: full parity, zero discrepancies found between the two tracked artifacts.**

## 6. Security / sanitization scan

A regex scan of both tracked artifacts (JSON + Markdown, full text) for Windows/Unix absolute-path
patterns, the operating account name, `Traceback`, private-key headers, and generic
API-key/secret/token key-value shapes returned **zero matches**. The only repository-relative path
string present (`tmp/feat018-cohort-b-input-20260912/`, appearing twice, once in the JSON's
`raw_inputs.description` and once in the Markdown's "Privacy and provenance" section) is the
disclosed, expected location of the git-ignored local inputs -- not an absolute machine path and
not a leak. Every per-sample `metadata` object contains only the five bounded
`ImageMetadataSignals` fields (`container`, `codec`, `pixel_format`, `width`, `height`), the same
shape already published and owner-approved in the Cohort A evidence; no EXIF, orientation, or
free-form metadata field is present anywhere. No base64-shaped run of 200+ characters (a proxy for
embedded raw image bytes) was found in either file. `python tools/validate_repository_security.py`
independently confirms `absolute_machine_paths=absent` across all 886 scanned publishable files.

## Findings

Zero findings from data verification (Sections 1-6 above): every hash, count, statistic,
classification, and cross-reference reproduces exactly. The two findings below come from this
verification's code review of the runner (`image_admission_evaluation.py`) and its test file,
per requirement 10. Neither one is a defect in the published Cohort B numbers -- both were checked
against what actually happened during this specific run and confirmed not to have affected it.

1. **MAJOR (process-integrity / reproducibility-guarantee completeness, not a data-correctness
   defect in this evidence).** `_resolve_backend_clean_head`'s default `_D2_IMPLEMENTATION_PATHS`
   (`backend/src/sketch2life/benchmark/image_admission_evaluation.py:1545-1554`) lists 8 paths
   intended to cover "the reviewed D2 admission implementation actually being timed." It omits two
   files that are part of that same import graph and execute inside the timed `admit()` call:
   - `backend/src/sketch2life/contracts/schemas/media_validation.py` -- imported at
     `application/services/image_admission.py:24` (`from sketch2life.contracts.schemas.media_validation
     import SourceMediaReferenceV1`), and `SourceMediaReferenceV1(...)` is constructed at
     `application/services/image_admission.py:179`, inside the `admit()` method (defined at line 65)
     that the D3 harness times.
   - `backend/src/sketch2life/domain/understanding/media_quality.py` -- imported by the file above
     (`contracts/schemas/media_validation.py:9`) and therefore equally part of the same closure.

   **Failure scenario**: if either file had an uncommitted change at execution time, this run's
   preflight "D2 implementation matches commit `9191565` exactly, no uncommitted change" claim
   would have passed anyway, because the check never inspects these two paths -- silently
   weakening the reproducibility guarantee the check exists to provide.

   **Verified harmless for this specific run**: `git diff 9191565a8961aab1bd10b2a0aa3efff7aefdf998
   -- backend/src/sketch2life/contracts/schemas/media_validation.py` and the same command for
   `media_quality.py` both return empty output -- neither file differs between the measured commit
   and the current `HEAD`. The Cohort B numbers published in this evidence are therefore not
   affected. This finding concerns the check's completeness for any *future* run that might rely
   on it, not the correctness of the data already published here.

2. **MINOR (test-coverage gap, not a functional defect).** No automated test exercises the exact
   historical scenario that occurred during this Cohort B run: a manifest entry's `sha256` field
   holding a 63-character (one-short) string. `load_cohort_b_manifest`'s `len(digest) != 64` guard
   (present at two call sites, including
   `backend/src/sketch2life/benchmark/image_admission_evaluation.py` around line 1393) was
   confirmed by direct inspection to reject such a value at manifest-load time, before any file I/O
   or execution -- so the safeguard demonstrably works. However,
   `test_cohort_b_source_validation_rejects_hash_drift` in
   `backend/tests/unit/test_image_admission_evaluation.py` exercises a *different* function
   (`validate_cohort_b_source`) with a full-length-but-wrong hash (`"a" * 64`), not
   `load_cohort_b_manifest`'s own length check, and no other test constructs a short-digest
   manifest entry. The specific defense that actually would have caught (and structurally could
   catch again) this exact class of input error has no dedicated regression test.

3. **LOW / informational (shared, pre-existing design characteristic, not introduced by the Cohort
   B extension).** `_resolve_backend_clean_head` (like Cohort A's `_resolve_clean_git_head`) checks
   D2-implementation cleanliness once, before the 24-sample loop begins; it is not re-verified
   between samples. A hypothetical mid-run edit to one of the checked files would not be caught
   for later samples in the same run. This mirrors Cohort A's own equivalent design exactly and is
   not a new gap; noted for completeness since requirement 10 asked for a full review, not because
   it is practically exploitable in a controlled, single-operator local run such as this one.

## Carried limitations

The following limitations, already stated in the original execution report, are confirmed accurate
by this verification and are not re-litigated or resolved here:

- Eight images is a diagnostic cohort, not a production-representative or statistically
  representative sample (D3-R2 section 6, D3-U2).
- The 5,000 ms and 256 MiB figures are observational evaluation targets, not enforced limits; this
  verification makes no runtime-enforcement claim either.
- Cohort B correctly reports minimum/median/maximum only; this verification independently confirms
  no p95 value exists anywhere in the tracked artifacts.
- This result says nothing about Qwen3-VL understanding quality, Gate A/B, mobile transport, or any
  other downstream FEAT-018 scope, and this verification did not touch any of those areas.

## Tests and validators

All commands were run from the current repository checkout (branch
`feature/feat018-p2-image-validation`, `HEAD` = `5c22a92`), using a scratch `--basetemp` directory
to avoid an unrelated local pytest-temp-directory permission issue; no repository file was written
by these commands.

| Command | Exit status | Result |
|---|---:|---|
| `pytest tests/unit/test_image_admission_evaluation.py tests/unit/test_image_admission.py` | 0 | `148 passed` (matches the original report's stated 148 = 119 pre-existing + 29 new) |
| `python tools/validate_harness.py` | 0 | `HARNESS_VALID` |
| `python tools/validate_repository_security.py` | 0 | `REPOSITORY_SECURITY_VALID` (886 files scanned, `absolute_machine_paths=absent`) |
| `python tools/validate_architecture.py` | 0 | `ARCHITECTURE_VALID` |
| `python tools/validate_skeleton.py` | 0 | `SKELETON_VALID` |
| `git diff --check` | 0 | Clean, no output |

`git status --short` after all commands: no output (working tree clean; this verification added no
untracked or modified files to the tracked tree other than this report itself).

## Readiness for owner approval and indexing

**Ready for owner approval and indexing as a Cohort B measurement.** The executed data, its
aggregation, its target classifications, and its cross-artifact consistency are all independently
confirmed correct with zero discrepancies. The manifest correction disclosed in the original report
is itself independently confirmed accurate and complete (true 64-character digest, matching file,
explicit disclosure in both tracked artifacts).

Recommend the owner also note Finding 1 (the incomplete `_D2_IMPLEMENTATION_PATHS` list) as
follow-up work before the next formal D3 run of any cohort relies on `_resolve_backend_clean_head`
for its reproducibility guarantee; it did not affect this run's already-published numbers, so it is
not a reason to withhold approval of this evidence, but it should be closed before being trusted
again. Finding 2 (missing regression test for the truncated-digest case) is a reasonable
follow-up test addition whenever the harness is next touched. Neither finding requires re-running
Cohort B.

This verification does not itself grant D3/P2-T1 closure, index this or any evidence, modify
`CONTEXT.md`/`DECISIONS.md`/`TASK_APPROVAL.md`/`evidence/README.md`, or authorize any provider,
mobile, Gate A, or shared-integration scope. Those steps remain separately gated on explicit owner
review, per D3-U6.
