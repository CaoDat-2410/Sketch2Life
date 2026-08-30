# P2-T2 Phase B ASR-only Round-1 report (executed)

- Evidence ID: EV-003-T2-05 (superseded numbers corrected 2026-08-30; see "Correction" below)
- Date: 2026-08-30 (initial run), corrected re-run 2026-08-30
- Scope: the controlled live Round-1 execution already covered by the Phase B approval
  (`approvals/TASK_APPROVAL.md`). This is an ASR profile-selection report only — it is not
  P2-T5's public CLI or end-to-end multimodal report, and it does not freeze a profile or
  select a runtime default.
- Raw report data (references, hashes, and measured numbers only — no transcript/audio
  content), produced by `AsrRound1BenchmarkReportV1`:
  - **Run 1 (corrected run, preserved):** `P2_T2_PHASE_B_ROUND1_REPORT.json` —
    `asr-round1-report-f9095af9…`
  - **Run 2 (repeat run, NEWEST):** `P2_T2_PHASE_B_ROUND1_REPORT_RUN2.json` —
    `asr-round1-report-a7f1b4be…` (evidence ID `EV-003-T2-06`; see "Repeat run 2" below)
- Fixture-source provenance: `P2_T2_PHASE_B_FIXTURE_PROVENANCE.md`.

## Correction (2026-08-30)

An independent review found three defects in the first executed pass and its evidence:

1. **Fabricated warmup provenance.** The runner generated a silent warmup clip and manually
   set `MediaValidationProvenanceV1(decision="PASS")` for it — literal silence legitimately
   receives P2-T1 `RECAPTURE`, so that `PASS` was never earned. Fixed: the runner now
   deterministically selects the first (by `fixture_id`) real manifest fixture that actually
   receives a real P2-T1 `PASS` (`en-clear-01` in this manifest) and warms up with its real
   audio and real, earned provenance. If no fixture passes P2-T1, the runner now raises
   `NoWarmupFixtureAvailableError` before any model load, rather than proceeding with a
   fabricated pass. The warmup call is still excluded from `runs`, WER/CER, language accuracy,
   speech-presence outcomes, and p50/p95 latency — only cold-start timing uses it.
2. **Incorrect per-profile denominator.** The first report's schema-valid-rate prose read
   "1.0 (42/42 runs schema-valid)" for *each* profile, conflating the combined two-profile run
   count (42) with each profile's own count (21). Fixed: `AsrRound1MetricSetV1` now has an
   explicit `total_runs` measurement, and `AsrRound1BenchmarkReportV1` has a Pydantic validator
   that rejects any report where a profile's `total_runs` or `success_count + failure_count`
   does not equal that profile's own run count in `runs` — this is now a structural invariant,
   not prose, and is covered by `test_asr_round1_report_contract.py`.
3. **Metadata not structurally verified/reported.** `duration_band` was manifest-only
   (never checked against the actual audio), and the two `noise`-fixture hallucinations were
   only described in prose. Fixed: the runner now decodes each fixture's actual audio duration
   and fails deterministically (`FixtureIntegrityError`) before any adapter call if it disagrees
   with the manifest's declared `duration_band`. A new structured `speech_presence_outcome`
   (`MATCH`/`MISMATCH`/`NOT_MEASURED`) is computed per succeeded run from
   `expected_speech_present` vs. the model's own `speech_diagnostic`, and a
   `speech_presence_match_rate` aggregate is reported per profile — the two `noise` fixtures now
   appear structurally as `MISMATCH` in the JSON report, not only in prose (see below).

The corrected run reproduced the same quality numbers (WER/CER/language accuracy identical) and
the same two `silence` failures; only the denominator, warmup provenance, and speech-presence
structure changed. The numbers below are from the corrected re-run.

## Run identity and scope

| Field | Value |
|---|---|
| Report version | `p2-t2-asr-round1-report-v1` (this note); machine contract `AsrRound1BenchmarkReportV1` `1.0` |
| Report ID | `asr-round1-report-f9095af9411ae36ce551e7ea739f1917afb82c6e68b877b8759fcdd4a76de1af` |
| Manifest version | `asr-round1-v1` |
| Manifest SHA-256 | `93f1a745f041f833d0ef24ddfab19c0edf2a361ca2481d2a7795a76796f16b89` |
| Vietnamese normalizer | `vi-asr-normalizer-v1` |
| Data policy | `SYNTHETIC` (TTS) only; no real-child data |
| Split | `HELD_OUT` (all 21 fixtures; no `DEVELOPMENT`-split result exists, so nothing is blended across splits) |
| Fixture count | 21 (5 `vi_clear`, 5 `non_vi_clear`, 3 `vi_en_code_switch`, 2 `silence`, 2 `noise`, 4 `noisy_speech`) |
| Runs (aggregate, both profiles) | 42 (21 fixtures × 2 fixed Round-1 profiles) |
| Runs (per profile) | **21** — each profile's own `total_runs`/`schema_validity_rate` denominator; never 42 |
| Warmup fixture (real, earned P2-T1 PASS; excluded from all metrics below) | `en-clear-01` |
| Measurement status | `MEASURED` (this run); the readiness planner's `NOT_MEASURED` output for an unrun plan is unchanged and still exercised by its own tests |

The report was produced by the internal (non-CLI) `run_round1_benchmark` runner
(`backend/src/sketch2life/benchmark/asr_round1_runner.py`) against the real local GPU
`faster-whisper` adapter, using the locally-configured Turbo snapshot already downloaded to a
user-selected external D: model location (`backend/.asr.env`, never committed).

## Fixed Round-1 profile/config identity

| Profile | Model/revision reference | Compute | Language mode | Beam | VAD | Word timestamps |
|---|---|---|---|---:|---|---|
| `WHISPER_TURBO_INT8_AUTO_V1` | `deepdml/faster-whisper-large-v3-turbo-ct2` @ `4df90f75321148c3a29a9e2351b7ddf8f5b115a8` | `GPU_INT8_FLOAT16` | `AUTO_DETECT` | 5 | false | false |
| `WHISPER_TURBO_FP16_AUTO_V1` | `deepdml/faster-whisper-large-v3-turbo-ct2` @ `4df90f75321148c3a29a9e2351b7ddf8f5b115a8` | `GPU_FLOAT16` | `AUTO_DETECT` | 5 | false | false |

No `HONOR_HINT` profile, large-v3 run, profile freeze, or runtime-default selection is part of
this Round-1 report. Per-profile `config_hash` values are in the raw JSON report
(`metrics_by_profile` keys plus each run's `profile_config_hash`).

## Quality and language measurements

### WER / CER

| Profile | Eligible fixture count | WER | CER |
|---|---:|---:|---:|
| `WHISPER_TURBO_INT8_AUTO_V1` | 17 (mean over succeeded WER/CER-eligible fixtures) | 0.0049 (0.49%) | 0.0027 (0.27%) |
| `WHISPER_TURBO_FP16_AUTO_V1` | 17 | 0.0049 (0.49%) | 0.0027 (0.27%) |

Scoring view: `vi-asr-normalizer-v1` normalized WER tokens / CER characters. 16 of 17 eligible
fixtures scored exact WER/CER `0.0` for both profiles; the one non-zero case
(`vi-en-code-switch-01`, WER `0.083`, CER `0.045`) was identical for both profiles — a single
token/character-level normalization mismatch on a Vietnamese sentence containing an English
loanword, not a profile-specific quality difference. Raw ASR transcripts are not rewritten by
this benchmark view and are not stored in this evidence.

### Language accuracy (`AUTO_DETECT` only)

| Profile | Eligible count | Detected-language accuracy |
|---|---:|---:|
| `WHISPER_TURBO_INT8_AUTO_V1` | 10 (5 `vi_clear` + 5 `non_vi_clear`) | 1.0 (10/10) |
| `WHISPER_TURBO_FP16_AUTO_V1` | 10 | 1.0 (10/10) |

`vi_en_code_switch` and `noisy_speech` fixtures are excluded from this metric by contract
(code-switch is never language-accuracy eligible; this package did not mark `noisy_speech`
language-accuracy eligible, only WER/CER eligible, so noise-shifted detection cannot inflate or
deflate this number). Round 1 is `AUTO_DETECT` only; no `HONOR_HINT` variant exists to blend
with this metric.

## Latency and runtime measurements

| Profile | Cold start (warmup: `en-clear-01`, excluded below) | Inference p50 | Inference p95 | Peak VRAM |
|---|---:|---:|---:|---:|
| `WHISPER_TURBO_INT8_AUTO_V1` | 3771 ms | 465 ms | 489 ms | 3117 MB |
| `WHISPER_TURBO_FP16_AUTO_V1` | 1865 ms | 524 ms | 556 ms | 5173 MB |

Cold start is a dedicated warmup transcription per profile, using the real audio and real,
earned P2-T1 `PASS` provenance of `en-clear-01` (the first, by `fixture_id`, manifest fixture
that actually passes P2-T1 — never a fabricated pass on synthetic silence). It is timed
separately from the 19 per-fixture inference calls that feed p50/p95 for that profile, and the
warmup call is not one of those 19 — the two are never blended. Peak VRAM is the maximum
`nvidia-smi --query-gpu=memory.used` sample taken by a background poller (≈100 ms interval)
while that profile's fixtures ran; GPU: NVIDIA GeForce RTX 4060 Laptop GPU (8 GB), local Windows
development machine. Repeat runs (across three executions total, used to verify runner fixes)
reproduced quality metrics exactly and latency/VRAM within normal run-to-run variance (cold
start ranged 1865-10743 ms across runs — attributable to OS/driver caching state before the
first CUDA context of the process, not a profile property; inference p50/p95 and VRAM were
stable within roughly 10%).

## Schema and success/failure coverage

**Denominators are per-profile, never the combined 42.** Each profile ran all 21 fixtures
exactly once; `total_runs`, `schema_validity_rate`, and `success_count + failure_count` are all
computed from — and structurally validated against — that profile's own 21 runs only
(`AsrRound1BenchmarkReportV1`'s Pydantic validator rejects a report where any profile's counts
disagree with its own run list). The combined 42 exists only as `len(report.runs)` across both
profiles and is never presented as a per-profile rate.

| Profile | Total runs (own) | Schema-valid result rate | Success count | Typed failure count | Failure codes/details |
|---|---:|---:|---:|---:|---|
| `WHISPER_TURBO_INT8_AUTO_V1` | 21 | 1.0 (21/21 runs schema-valid) | 19 | 2 | `INPUT_NOT_VALIDATED` / `MEDIA_VALIDATION_NOT_PASSED` ×2 |
| `WHISPER_TURBO_FP16_AUTO_V1` | 21 | 1.0 (21/21 runs schema-valid) | 19 | 2 | `INPUT_NOT_VALIDATED` / `MEDIA_VALIDATION_NOT_PASSED` ×2 |

Both typed failures are the two `silence` fixtures (`silence-01`, `silence-02`), for both
profiles, at `attempt_number=0` (rejected before any adapter/model call), `repair_attempted`
`false`. This is a **real, not fabricated**, outcome: the runner requires a real per-fixture
P2-T1 `PASS` (via `DeterministicMediaValidator`, the same validator P2-T1 ships) before ever
calling the ASR adapter. Literal digital silence has `AUDIO_SILENT`-range RMS under P2-T1's
existing `MediaQualityPolicy`, so P2-T1 legitimately returns `RECAPTURE` for those two fixtures,
and the runner correctly reports `INPUT_NOT_VALIDATED` rather than skipping them or calling the
model anyway. This is expected, correct behavior of the P2-T1/P2-T2 boundary, not an ASR defect.

### Structured speech-presence outcome (per profile)

Every succeeded run now carries a structured `speech_presence_outcome` — `MATCH`, `MISMATCH`, or
`NOT_MEASURED` (an `INDETERMINATE` model diagnostic) — comparing the manifest's declared
`expected_speech_present` against the model's own `speech_diagnostic`. Failed runs (the two
`silence` fixtures) carry no `speech_presence_outcome` at all — "not evaluated by ASR" is a
distinct state from a model producing an inconclusive diagnostic.

| Profile | `speech_presence_match_rate` | Eligible (succeeded, conclusive) | `MISMATCH` fixtures |
|---|---:|---:|---|
| `WHISPER_TURBO_INT8_AUTO_V1` | 0.895 (17/19) | 19 | `noise-white-noise-v1`, `noise-room-tone-v1` |
| `WHISPER_TURBO_FP16_AUTO_V1` | 0.895 (17/19) | 19 | `noise-white-noise-v1`, `noise-room-tone-v1` |

**The two `noise`-only fixtures (`expected_speech_present: false`) both structurally report
`speech_diagnostic=DETECTED` / `speech_presence_outcome=MISMATCH`** for both profiles, in the
JSON report itself — not only in prose. This is a known category of Whisper-family
hallucination-on-noise behavior, not a runner or contract defect: P2-T1 passed both `noise`
fixtures (its speech-activity heuristic is amplitude-based, not a real speech detector, so noise
with sufficient energy passes), and the ASR model then produced a schema-valid `SUCCEEDED`
result with fabricated-sounding text. No WER/CER is computed for `noise` fixtures (not eligible,
no reference transcript), so this does not distort the WER/CER numbers above, but it is worth
carrying into any later VAD-focused round.

## Controlled-variable coverage

| Variable | Round-1 setting | Alternative coverage |
|---|---|---|
| Language mode | `AUTO_DETECT` | `HONOR_HINT`: `NOT_MEASURED` (out of Round-1 scope) |
| VAD | disabled | enabled/parameter alternatives: `NOT_MEASURED` |
| Beam size | 5 | alternative beam sizes: `NOT_MEASURED` |
| Word timestamps | disabled | enabled: `NOT_MEASURED` |

## INT8 vs. FP16 observational comparison (not a freeze decision)

| Dimension | `WHISPER_TURBO_INT8_AUTO_V1` | `WHISPER_TURBO_FP16_AUTO_V1` | Observation |
|---|---|---|---|
| WER / CER | 0.49% / 0.27% | 0.49% / 0.27% | Identical on this 21-fixture synthetic set — INT8 quantization showed no measurable quality loss here. |
| Language accuracy | 100% (10/10) | 100% (10/10) | Identical. |
| Speech-presence match rate | 89.5% (17/19) | 89.5% (17/19) | Identical — both profiles hallucinate speech on both `noise` fixtures. |
| Inference p50 / p95 | 465 ms / 489 ms | 524 ms / 556 ms | INT8 is ~11% faster at p50 on this GPU/fixture set. |
| Peak VRAM | 3117 MB | 5173 MB | INT8 uses ~40% less VRAM — material on an 8 GB laptop GPU. |
| Cold start | 3771 ms (range across 3 runs: 1865-10743 ms) | 1865 ms (range: 1872-1925 ms) | Noisy across repeats; not treated as a reliable differentiator without more runs. |
| Failure behavior | Identical typed-failure set (2× `INPUT_NOT_VALIDATED` on `silence`), per-profile denominator 21/21 | Identical | No profile-specific failure difference observed. |

**Observation, not a decision:** on this synthetic, 21-fixture, single-GPU sample, INT8 matched
FP16 on every quality metric measured while using materially less VRAM and slightly less
latency. This package does not propose a profile freeze or runtime default — per the approved
Phase B scope, that remains a separate R5/Integration-Sprint/ADR decision requiring more
evidence (larger sample, additional hardware, and non-synthetic considerations) than this single
Round-1 pass provides.

## Repeat run 2 — independent re-execution (2026-08-30, NEWEST)

- Evidence ID: `EV-003-T2-06`
- Raw data: `P2_T2_PHASE_B_ROUND1_REPORT_RUN2.json`
- Report ID: `asr-round1-report-a7f1b4beab20b16fae3c8ee1a8e497b4f473c69a147230a123929626d9b33a93`
- Manifest SHA-256: `93f1a745f041f833d0ef24ddfab19c0edf2a361ca2481d2a7795a76796f16b89` (identical to run 1 — same fixture set, byte-for-byte)
- Prior run 1 evidence (`P2_T2_PHASE_B_ROUND1_REPORT.json`, `asr-round1-report-f9095af9…`) is **preserved unmodified**; run 2 is an additional artifact, not a replacement.

Re-executed under identical fixed settings (`AUTO_DETECT`, beam 5, VAD disabled, word timestamps
disabled, `language_hint_policy=NOT_USED`) through the same internal `run_round1_benchmark` flow,
with real P2-T1 gating and a real earned-`PASS` warmup. 42 aggregate runs; **21 per profile**.

| Metric | INT8 (run 2) | FP16 (run 2) | vs. run 1 |
|---|---:|---:|---|
| Total runs (own) | 21 | 21 | identical |
| Schema-valid rate | 1.0 (21/21) | 1.0 (21/21) | identical |
| Success / typed failure | 19 / 2 | 19 / 2 | identical |
| WER | 0.004902 (0.49%) | 0.004902 (0.49%) | **bit-identical** |
| CER | 0.002674 (0.27%) | 0.002674 (0.27%) | **bit-identical** |
| Language accuracy | 1.0 (10/10) | 1.0 (10/10) | identical |
| Speech-presence match rate | 0.8947 (17/19) | 0.8947 (17/19) | identical |
| Cold start | 3242 ms | 1851 ms | within run-to-run variance |
| Inference p50 | 466 ms | 524 ms | within ~1% |
| Inference p95 | 487 ms | 580 ms | within ~4% |
| Peak VRAM | 3212 MB | 5275 MB | +3% / +2% (sampling jitter) |
| VAD / beam / word-timestamp alternatives | `NOT_MEASURED` | `NOT_MEASURED` | unchanged by design |

**Reproducibility finding:** every quality metric (WER, CER, language accuracy, speech-presence
match rate) reproduced **exactly**, and the typed-failure and mismatch sets were identical
fixture-for-fixture. Only latency/VRAM moved, and only within normal single-machine measurement
jitter. This materially strengthens the run-1 numbers as reproducible rather than incidental.

Typed failures (both profiles, unchanged from run 1): `silence-01`, `silence-02` →
`INPUT_NOT_VALIDATED` / `MEDIA_VALIDATION_NOT_PASSED` at `attempt_number=0`,
`repair_attempted=false` — real P2-T1 gating before inference, never counted as ASR successes.

Speech-presence `MISMATCH` (both profiles, unchanged from run 1): `noise-white-noise-v1`,
`noise-room-tone-v1` → `speech_diagnostic=DETECTED` on `expected_speech_present=false`, i.e. the
hallucination-on-noise behavior reproduced deterministically across both runs and both profiles.

## Synthetic-only limitation and reviewer decision

Synthetic-only limitation: all evidence above comes from `edge-tts` (Microsoft Edge neural TTS)
synthesized voices, mixed with synthetic noise. It is directional evidence about this specific
Whisper Turbo build's behavior on clear synthetic narration, code-switched synthetic narration,
noise-mixed synthetic narration, literal silence, and pure noise — and is **not** evidence of
performance on real child speech, whose pitch, articulation, and disfluency differ materially.
Real child audio remains prohibited in this workstream without a separate data-governance
approval; none was used. A 21-fixture, single-GPU, single-noise-mix-ratio sample is directional,
not statistically robust, evidence. Both executed runs used **one machine and one GPU** (RTX 4060
Laptop, 8 GB); repeat run 2 establishes *reproducibility on that machine*, not cross-hardware
generalization, and does not increase the effective sample size beyond the same 21 fixtures.

Reviewer decision: `PENDING` — no profile freeze or runtime-default selection is made by this
report. Recorded strictly as Round-1 profile-selection evidence per the approved Phase B scope.
