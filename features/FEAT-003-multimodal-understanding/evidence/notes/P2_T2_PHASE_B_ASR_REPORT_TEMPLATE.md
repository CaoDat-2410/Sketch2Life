# P2-T2 Phase B ASR-only Round-1 report template

Status: `NOT_MEASURED` until a concrete fixture source is selected and compliant local
payload/reference-transcript refs and hashes are supplied. The Phase B approval already
covers the controlled live Round-1 execution. This is an ASR profile-selection report only;
it is not P2-T5's public CLI or end-to-end multimodal report.

The Round-1 execution has since been run against 21 synthetic `HELD_OUT` fixtures; see the
filled report at `P2_T2_PHASE_B_ROUND1_ASR_REPORT.md`. This file remains the reusable template
for any later round.

## Run identity and scope

| Field | Value |
|---|---|
| Report version | `p2-t2-asr-round1-report-v1` |
| Run ID | `{{RUN_ID}}` |
| Manifest version | `{{MANIFEST_VERSION}}` |
| Manifest SHA-256 | `{{MANIFEST_SHA256}}` |
| Vietnamese normalizer | `vi-asr-normalizer-v1` |
| Data policy | `SYNTHETIC` or `LICENSED` only; no real-child data |
| Measurement status | `NOT_MEASURED` |

The report must contain references and hashes only. Do not copy audio, transcript content,
credentials, provider payloads, endpoint URLs, or absolute local paths into this report.

## Fixed Round-1 profile/config identity

| Profile | Model/revision reference | Profile config SHA-256 | Compute | Language mode | Beam | VAD | Word timestamps |
|---|---|---|---|---|---:|---|---|
| `WHISPER_TURBO_INT8_AUTO_V1` | `{{MODEL_REVISION}}` | `{{CONFIG_HASH_INT8}}` | `GPU_INT8_FLOAT16` | `AUTO_DETECT` | 5 | false | false |
| `WHISPER_TURBO_FP16_AUTO_V1` | `{{MODEL_REVISION}}` | `{{CONFIG_HASH_FP16}}` | `GPU_FLOAT16` | `AUTO_DETECT` | 5 | false | false |

No `HONOR_HINT` profile, large-v3 run, profile freeze, or runtime-default selection is part of
this Round-1 report.

## Quality and language measurements

Use `NOT_MEASURED` when the required fixture/reference or run result is unavailable. Never use
zero to mean missing data.

### WER

| Profile | Eligible fixture count | WER | Status/notes |
|---|---:|---:|---|
| `WHISPER_TURBO_INT8_AUTO_V1` | `NOT_MEASURED` | `NOT_MEASURED` | `{{WER_INT8_NOTES}}` |
| `WHISPER_TURBO_FP16_AUTO_V1` | `NOT_MEASURED` | `NOT_MEASURED` | `{{WER_FP16_NOTES}}` |

Scoring view: `vi-asr-normalizer-v1` normalized WER tokens. Raw ASR transcripts are not
rewritten by this benchmark view.

### CER

| Profile | Eligible fixture count | CER | Status/notes |
|---|---:|---:|---|
| `WHISPER_TURBO_INT8_AUTO_V1` | `NOT_MEASURED` | `NOT_MEASURED` | `{{CER_INT8_NOTES}}` |
| `WHISPER_TURBO_FP16_AUTO_V1` | `NOT_MEASURED` | `NOT_MEASURED` | `{{CER_FP16_NOTES}}` |

Scoring view: `vi-asr-normalizer-v1` normalized character sequence with whitespace removed.

### Language accuracy

| Profile | Auto-detect evaluated count | Detected-language accuracy | Calibration/notes |
|---|---:|---:|---|
| `WHISPER_TURBO_INT8_AUTO_V1` | `NOT_MEASURED` | `NOT_MEASURED` | `{{LANGUAGE_INT8_NOTES}}` |
| `WHISPER_TURBO_FP16_AUTO_V1` | `NOT_MEASURED` | `NOT_MEASURED` | `{{LANGUAGE_FP16_NOTES}}` |

Round 1 is `AUTO_DETECT` only. A later forced-language round, if authorized as a distinct
round, must keep hint-applied results out of auto-detection accuracy/calibration metrics.

## Latency and runtime measurements

| Profile | Cold start | Inference p50 | Inference p95 | Peak VRAM | Status/notes |
|---|---:|---:|---:|---:|---|
| `WHISPER_TURBO_INT8_AUTO_V1` | `NOT_MEASURED` | `NOT_MEASURED` | `NOT_MEASURED` | `NOT_MEASURED` | `{{RUNTIME_INT8_NOTES}}` |
| `WHISPER_TURBO_FP16_AUTO_V1` | `NOT_MEASURED` | `NOT_MEASURED` | `NOT_MEASURED` | `NOT_MEASURED` | `{{RUNTIME_FP16_NOTES}}` |

## Schema and success/failure coverage

| Profile | Schema-valid result rate | Success count | Typed failure count | Failure codes/details | Status |
|---|---:|---:|---:|---|---|
| `WHISPER_TURBO_INT8_AUTO_V1` | `NOT_MEASURED` | `NOT_MEASURED` | `NOT_MEASURED` | `NOT_MEASURED` | `NOT_MEASURED` |
| `WHISPER_TURBO_FP16_AUTO_V1` | `NOT_MEASURED` | `NOT_MEASURED` | `NOT_MEASURED` | `NOT_MEASURED` | `NOT_MEASURED` |

For every measured success or typed failure, record `attempt_number` and
`repair_attempted` without recording raw provider output or exception text.

## Controlled-variable coverage

| Variable | Round-1 setting | Alternative coverage |
|---|---|---|
| Language mode | `AUTO_DETECT` | `HONOR_HINT`: `NOT_MEASURED` |
| VAD | disabled | enabled/parameter alternatives: `NOT_MEASURED` |
| Beam size | 5 | alternative beam sizes: `NOT_MEASURED` |
| Word timestamps | disabled | enabled: `NOT_MEASURED` |

## Synthetic-only limitation and reviewer decision

Synthetic-only limitation: evidence from synthetic voices is directional and is not evidence
of real child-speech performance. A licensed non-child voice source has the same limitation
with respect to real child speech. Real child audio is prohibited in this workstream without
a separate data-governance approval. If any required result remains unavailable, retain
`NOT_MEASURED` and do not propose a profile freeze or runtime default.

Reviewer decision: `{{REVIEWER_DECISION}}`
