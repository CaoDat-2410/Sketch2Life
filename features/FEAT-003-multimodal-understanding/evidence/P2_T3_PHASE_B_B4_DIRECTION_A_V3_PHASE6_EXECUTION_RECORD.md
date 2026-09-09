# P2-T3 Phase B B4 Direction A — prompt-v3 Phase 6 execution record

- Evidence ID: `EV-003-T3-14`
- Related task: P2-T3 Phase B B4 Direction A (prompt-v3 mapping validation)
- Companion report: `metrics/P2_T3_PHASE_B_B4_DIRECTION_A_V3_PHASE6_REPORT.json` (`EV-003-T3-13`)
- Execution date: 2026-09-09
- Record written: 2026-09-09
- Data boundary: synthetic fixtures only; no real child data.
- Combined outcome: technical `MAPPING_READY` / compute governance `CAP_EXCEEDED`.

This record states two separate results that must not be merged. The Phase 6 mapping execution
succeeded on its own technical gate. The same session's official Lightning ledger duration exceeded
the separately authorized 20-minute L4 budget. Neither result cancels the other.

## Sources

| Source | Role |
|---|---|
| `Lightning-AI-activity-2026-08-09-to-2026-09-09.csv` | Operator-provided official Lightning Activity export. Authoritative for billed session duration and cost. Stored locally outside the repository; not committed. |
| `metrics/P2_T3_PHASE_B_B4_DIRECTION_A_V3_PHASE6_REPORT.json` | Immutable safe Phase 6 report (`EV-003-T3-13`). Authoritative for typed outcomes, counts, runner timings, and the readiness verdict. |
| `data/runtime/v3-phase6-safe-report.json` | Local runtime-produced copy of the same report. Git-ignored; retained only for hash/semantic comparison. |
| `../fixtures/vision-v3-map/manifest-v1.json` | Approved eight-fixture mapping manifest. Authoritative for fixture IDs, image hashes, and prompt binding. |
| `../approvals/TASK_APPROVAL.md` | Approved P2-T3 Phase B B1–B5 boundary. |
| `notes/P2_T3_PHASE_B_B4_DIRECTION_A_V3_REAUTHORIZATION.md` | The bounded 20-minute L4 reauthorization this execution ran under (local-only note). |
| `notes/P2_T3_PHASE_B_B4_DIRECTION_A_V3_MAPPING_VALIDATION_PLAN.md` | Phase order and the owner-fixed readiness gate (local-only note). |

Screenshots of the Lightning console were reviewed only as non-authoritative corroboration. They
are not a source for any timestamp, duration, or cost in this record.

## Sanitized execution procedure

The operator ran the reviewed dedicated runner
(`backend/src/sketch2life/benchmark/vision_v3_mapping_validation_study.py`) inside the reauthorized
L4 Studio session, in this order:

1. fresh no-model-load environment readiness check;
2. construct the production adapter factory and a `CLASSIFY_ONLY` raw-output collector;
3. `run_v3_pass(..., run_label="V3_PASS_1")` — eight fixtures, one call each, no retry;
4. `run_v3_pass(..., run_label="V3_REPEAT_1")` — same package, immediately afterwards;
5. `evaluate_v3_readiness(pass_1, repeat_1, same_lightning_session=True)`.

The runner re-verifies the manifest and every on-disk image hash, self-checks the frozen v3 prompt
identity, and requires a real P2-T1 `PASS` on all eight scratch copies before any adapter call. The
literal shell invocation string was `NOT_RECORDED`. No prompt body, raw model output, predicted
text, credential, endpoint, or local path was captured into this record or its companion JSON.

## Readiness and environment identity

| Field | Value |
|---|---|
| Readiness result | `READY` (operator-reported; no model load performed) |
| Readiness artifact | `NOT_RECORDED` — no separate readiness JSON was persisted to evidence |
| Profile | `QWEN3_VL_8B_INSTRUCT_BF16_V1` |
| Model revision | `0c351dd01ed87e9c1b53cbc748cba10e6187ff3b` |
| Device class / precision | `NVIDIA_L4` / BF16 |
| Decoding | greedy; sampling disabled; beam count `1` |
| Output budget / timeout | `max_new_tokens=512`; `120s` |
| Retry / repair | no mapping-failure retry; lossless complete-fence unwrap only |
| Raw-output mode | `CLASSIFY_ONLY` |
| Peak VRAM sample | `17180.0 MB`, identical on every recorded run |

## Immutable report hashes

| Artifact | SHA-256 |
|---|---|
| `metrics/P2_T3_PHASE_B_B4_DIRECTION_A_V3_PHASE6_REPORT.json` | `ea891f1cd540909337c1e9e194981d1c159800c8911cea641696a6b50b5bca20` |
| `data/runtime/v3-phase6-safe-report.json` | `236288e3814e0bd06de4f8c32d3a5634f869587b1a76828ec7c6e3fd5848b52b` |

Both files parse as JSON and compare semantically equal. Their only byte difference is the single
repository-standard final newline present in the evidence copy (`11573` versus `11572` bytes).
Neither file was modified while writing this record.

## Manifest, prompt, and profile identity

| Field | Value | Verification |
|---|---|---|
| Fixture manifest version | `vision-v3-map-manifest-v1` | Matches both passes' stamped version |
| Fixture IDs | `v3-map-fixture-01` … `v3-map-fixture-08` | Match the manifest's approved order in both passes |
| Fixture image hashes | eight distinct SHA-256 values | Every recorded run hash matches the manifest's declared hash |
| Prompt protocol | `vision-v2-structured-output-prompt-v3` | Matches manifest and both passes |
| Prompt SHA-256 | `bf8b9cab5df6b2551e627cf0bb92fe977e0dc182fdaae5f3c5face5bc34615f3` | Matches manifest, both passes, and the frozen constant recomputed from current source |
| Schema target | `VisionUnderstandingResultV2` | Matches manifest |
| Profile catalog hash | `72651b96d2c2259344efcb6fb3349807d42b56079a5422530db09c1590f00947` | Recomputed from current source; matches both passes |

## Per-pass aggregates and typed failure

| Field | `V3_PASS_1` | `V3_REPEAT_1` |
|---|---|---|
| Started at (runner clock, UTC) | `07:08:44.525952` | `07:11:41.833227` |
| Completed at (runner clock, UTC) | `07:11:41.097190` | `07:14:35.240516` |
| Attempted runs | `8` | `8` |
| Run records | `8` | `8` |
| Schema/mapping-valid | `7 / 8` | `7 / 8` |
| Typed failures | `OUTPUT_MAPPING_FAILED` × 1 | `OUTPUT_MAPPING_FAILED` × 1 |
| Truncated / fenced / extra-key / invalid-enum | `0 / 0 / 0 / 0` | `0 / 0 / 0 / 0` |
| Lossless unwrap recoveries | `0` | `0` |
| `known_policy_trigger_rate` | `NOT_APPLICABLE` | `NOT_APPLICABLE` |

The single failure in each pass is the same fixture, `v3-map-fixture-07`
(`straight_nondirectional_relation`), returning `VISION_SCHEMA_INVALID` / `OUTPUT_MAPPING_FAILED`
at `attempt_number=1` with `repair_attempted=false`. The other seven fixtures returned `SUCCEEDED`
in both passes. The passes are evaluated independently and are never pooled into a combined
denominator.

## Repeat comparability

| Field | Value |
|---|---|
| Rule | `V3_REPEAT_1.started_at - V3_PASS_1.completed_at <= 15 minutes` |
| Measured repeat gap | `00:00:00.736037` |
| Same Lightning session | `true` (operator attestation; the runner cannot detect a Studio reset) |
| Configuration drift | none |
| Fixture-manifest mismatch | none |
| Comparability outcome | comparable pair |

## Technical verdict

`MAPPING_READY`, with an empty `blocking_reasons` list. Each pass independently met the owner-fixed
gate of exactly eight attempts and eight records with at least `7/8` mapping-valid, and no
truncation (`>=2/8`), configuration drift, manifest mismatch, input-integrity failure, or
runtime/device failure occurred in either pass.

## Compute governance — official Lightning ledger

| Field | Value |
|---|---|
| Official session rows for 2026-09-09 | exactly one `Qwen 3 VL` Studio row on `1 × L4` |
| Official billed session duration | `00:44:41` |
| Official session cost | `0.35` credits |
| Authorized budget | `00:20:00` |
| Exceedance | `00:24:41` |
| Governance status | **`CAP_EXCEEDED`** |
| Official session start clock time | `NOT_AVAILABLE_FROM_EXPORT` — the export carries a start *date* only |
| Official session stop clock time | `NOT_AVAILABLE_FROM_EXPORT` — not derivable, and deliberately not derived |
| Operator-recorded prospective session start | `2026-09-09T07:03:09Z` — captured before the run and carried in the Phase 6 report as `studio_session_started_at`; not independently verified as the official Lightning billed start clock |
| Operator-recorded prospective session stop | `NOT_RECORDED` — the reauthorization required a stop time and it was not captured |

Aggregate ledger position through 2026-09-09, from the same export:

| Field | Value |
|---|---|
| L4 Studio rows | `12` |
| Aggregate L4 duration | `07:43:24` |
| Aggregate L4 cost | `3.93` credits |
| Storage cost | `0.14` credits |
| Non-L4 CPU Studio cost | `0.00` credits |
| Total export cost | `4.07` credits |

The previous reconciliation, taken from the earlier export, recorded `11` L4 sessions totalling
`06:58:43` and `3.58` credits. The delta to this export is exactly one session: `+00:44:41` and
`+0.35` credits — the 2026-09-09 Phase 6 session. The original one-hour B2–B4 soft cap remains
exceeded and no remaining capacity is claimed under it.

## Runner timing versus billed session timing

These are different measurements and must never be substituted for one another.

| Measurement | Value | What it is |
|---|---|---|
| Operator-recorded prospective start | `2026-09-09T07:03:09Z` | Operator-recorded prospective Studio-session start; not independently verified as the official Lightning billed start clock |
| Runner finish | `2026-09-09T07:14:35.240860Z` | The wrapper's own clock read after the repeat returned |
| Recorded-start-to-runner-finish interval | `00:11:26.240860` | An application-side observation window only |
| Official billed session duration | `00:44:41` | The authoritative Lightning ledger value |

The `00:11:26.240860` interval is **not** the billed duration and is never reported as compliance
with the 20-minute budget. The `00:44:41` official duration is the figure the cap is measured
against. How much of the `00:44:41` was post-repeat idle Studio time cannot be established from the
export (`NOT_AVAILABLE_FROM_EXPORT`), and that limitation is not used to reduce the recorded
exceedance.

## Reviewer and review verdict

| Field | Value |
|---|---|
| Independent verification | Read-only verification session run in this repository on 2026-09-09 |
| Verification scope | JSON parse/semantic equality, both SHA-256 values, per-pass counts, fixture-07 failure identity, repeat-gap arithmetic, verdict recomputation, prompt/profile/catalog identity recomputed from source, secret/path scan, and the four repository validators |
| Verification verdict at that time | `APPROVE_WITH_NOTES` — no Critical/High/Medium finding; the missing official Lightning Activity duration was recorded as the principal residual risk |
| Status of that residual risk | Closed by this record, as `CAP_EXCEEDED` |
| Project owner sign-off | `NOT_RECORDED` |

## Interpretation

`MAPPING_READY` states one thing only: under the v3 prompt, the model's raw output mapped onto the
strict `VisionUnderstandingResultV2` contract for seven of eight synthetic fixtures, repeatably,
across two independent passes in one comparable session. It is mapping evidence, not semantic
quality evidence, and the fixture set deliberately carries no ground truth.

Specifically, this result does **not**:

- change, rescore, pool with, or reinterpret the immutable B4 held-out quality `NO_GO`;
- measure semantic quality, coverage, or accuracy of any observation;
- resolve Direction B, the canonical-vocabulary mismatch hypothesis, which remains open;
- select a runtime default, freeze a profile, or choose a production provider;
- authorize Phase 8, any further Lightning/GPU time, deployment, or integration.

## Remaining authorization boundary

The reauthorized 20-minute L4 budget is spent and, per the official ledger, overspent by
`00:24:41`. Any further Lightning or GPU use requires a new explicit owner decision that accounts
for this exceedance. The previous reauthorization required both a prospective Studio start and stop
time; the start was recorded (`2026-09-09T07:03:09Z`) but the stop was not, so a future session must
record both. `approvals/TASK_APPROVAL.md` is unchanged by this
record, and this record creates no authorization of any kind.
