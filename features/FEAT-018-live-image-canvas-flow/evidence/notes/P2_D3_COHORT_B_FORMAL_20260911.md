# FEAT-018 D3-R2 Cohort B — Source Gate / Execution Attempt

## Executive verdict

- **INCONCLUSIVE**. Source-gate status: **BLOCKED**.
- `execution_occurred: false`; `sample_count: 0`; no timing or memory data was fabricated.
- The source gate stopped because no qualifying owner-approved JPEG/JPG files were located, so the
  required exact 4-JPEG + 4-PNG set could not be formed.
- Precisely: no approved D3 Cohort B manifest exists; no complete owner-approved 4-JPEG + 4-PNG
  set exists; the N01-N08 PNG set is a separate synthetic dataset and does not satisfy the
  photographic Cohort B contract; no image was executed, converted, or substituted.

## Scope and governing gate

The requested target is commit `c77230ca1593d5cd31098b5e58f3ff2a13d18a63` with eight owner-approved
non-sensitive images, three fresh-process repeats per image, and Cohort B min/median/max reporting
without p95. The D3-R2 plan requires exactly four JPEG and four PNG sources and requires visual
owner review plus a local ignored manifest with `owner_reviewed=true` before execution.

The repository approval record still states that Cohort B source approval is pending. This attempt
therefore searched the checkout and designated local input locations, while explicitly excluding the
child-safety S01–S08 files, v3q synthetic shape fixtures, D2 test fixtures, and unrelated local
downloads. No qualifying owner-provided JPEG/JPG source was found.

## Source discovery and composition

| Requirement | Located qualifying source | Result |
|---|---:|---|
| `.jpg`/`.jpeg` with matching JPEG MIME | 0 of 4 | **BLOCKER** |
| `.png` with matching PNG MIME | 0 of 4 in a qualifying owner set | **BLOCKED** |
| Complete owner-approved Cohort B set | 0 of 8 | **BLOCKED** |

The known local child-safety pack (N01-N08) is a separate synthetic PNG dataset: all eight files
are PNG, none is a photograph, and none was owner-reviewed as a Cohort B candidate. It therefore
does not satisfy the photographic Cohort B contract and cannot supply the missing JPEGs. No image
from this or any other set was executed, converted, cropped, regenerated, renamed, substituted, or
silently altered.

## Manifest and source review

- Cohort B manifest: not created (source gate failed).
- `owner_reviewed=true`: not recorded.
- Source hashes: not computed because no qualifying complete set exists.
- Per-image visual/decode/metadata review: not applicable to an owner-approved Cohort B set.
- No raw image bytes, absolute local paths, EXIF/private metadata, prompts, model output, secrets, or
  credentials are present in this report.

## Artifact identity and results

| Item | Value |
|---|---|
| Target commit | `c77230ca1593d5cd31098b5e58f3ff2a13d18a63` |
| Manifest present | `false` |
| Manifest SHA-256 | `n/a` |
| Approved image count | `0` of `8` |
| Expected repeats per image | `3` (not run) |
| Sample count | `0` |
| Aggregates | `{}` |

No per-image min/median/max rows exist because no image was admitted for measurement. Cohort B p95
is intentionally omitted.

## Validation, protocol, privacy, and reproducibility

| Check | Outcome |
|---|---|
| Source extension/MIME composition | **BLOCKED** — 0 qualifying JPEGs found; exact 4+4 set unavailable |
| Source hash verification | Not performed — no qualifying set |
| D3 fresh-process benchmark | Not performed |
| Admission latency / native memory | Not measured |
| Provider, Qwen, Whisper, network, production integration | Not run |
| Protocol/sample validation | Not applicable — zero samples |
| Privacy/redaction | Sanitized artifact contains metadata and numeric results only |
| Reproducibility | Not applicable — no run occurred |

## Environmental failures

None. This is a source-discovery/composition gate stop, not a benchmark, decoder, process, or
measurement failure.

## Verification commands

Results below are recorded after the blocked artifacts were written:

| Command | Exit status | Result |
|---|---:|---|
| JSON parse, Markdown parity, and redaction assertions (PowerShell) | 0 | Valid; zero samples; no absolute paths/raw-payload markers |
| `.\\.venv\\Scripts\\python.exe -m pytest tests/unit/test_image_admission_evaluation.py tests/unit/test_image_admission.py` (from `backend`) | 0 | 119 passed |
| `python tools/validate_repository_security.py` | 0 | `REPOSITORY_SECURITY_VALID` |
| `python tools/validate_architecture.py` | 0 | `ARCHITECTURE_VALID` |
| `python tools/validate_skeleton.py` | 0 | `SKELETON_VALID` |
| `python tools/validate_harness.py` | 0 | `HARNESS_VALID` |
| `git diff --check` | 0 | Clean |

## Limitations and unblock decision

This record is not a Cohort B measurement and carries no performance or memory evidence for real
photographs. D3/P2-T1 remains closed for synthetic Cohort A only; Cohort B remains open.

To unblock, provide exactly four owner-approved `.jpg`/`.jpeg` files with matching JPEG MIME and
four `.png` files with matching PNG MIME, visually review all eight against the exclusion list,
create the ignored manifest with `owner_reviewed=true` and hashes/metadata, and record the explicit
Cohort B approval addendum. Until then, the correct verdict is **INCONCLUSIVE** (source-gate status
**BLOCKED**), with `execution_occurred: false` and `sample_count: 0`.
