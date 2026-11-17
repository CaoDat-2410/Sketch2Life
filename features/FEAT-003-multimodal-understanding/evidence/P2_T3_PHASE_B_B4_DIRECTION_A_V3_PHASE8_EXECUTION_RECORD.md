# P2-T3 Phase B B4 Direction A — prompt-v3 Phase 8 execution record

- Evidence ID: `EV-003-T3-16`
- Related task: P2-T3 Phase B B4 Direction A (held-out prompt-v3 quality validation)
- Companion report: `metrics/P2_T3_PHASE_B_B4_DIRECTION_A_V3_PHASE8_REPORT.json`
  (`EV-003-T3-15`)
- Execution date: 2026-09-09
- Data boundary: eight owner-approved synthetic held-out fixtures; no real child data.
- Current status: technical execution complete / `QUALITY_NOT_READY` / compute governance
  `CAP_EXCEEDED`.

## Result

The authorized Phase 8 runner completed one `V3_QUALITY_PASS_1` and one immediate
`V3_QUALITY_REPEAT_1` under the fixed D-5/D-6/D-7 rules. Both passes produced exactly eight run
records and eight schema-valid successes. The pair was comparable, but neither pass met D-5, so
the final quality-only verdict is `QUALITY_NOT_READY` with the sole blocking reason
`QUALITY_BELOW_THRESHOLD`.

This is a completed benchmark result, not a runtime failure and not permission to rerun or tune
against the held-out package. It does not override the earlier Phase 6 `MAPPING_READY` result:
mapping validity and held-out semantic quality are separate gates.

## Sources

| Source | Role |
|---|---|
| `metrics/P2_T3_PHASE_B_B4_DIRECTION_A_V3_PHASE8_REPORT.json` | Immutable safe Phase 8 report; authoritative for identities, typed outcomes, scores, runner timings, and verdict. |
| `data/runtime/v3-phase8-safe-report.json` | Git-ignored runtime source imported without byte changes. |
| `../fixtures/vision-v3-quality/manifest-v1.json` | Owner-approved manifest; authoritative for ordered fixture IDs and image hashes. |
| `../approvals/TASK_APPROVAL.md` | Authoritative D-5/D-6/D-7 and bounded D-8 approval. |
| Lightning Activity export `Lightning-AI-activity-2026-08-10-to-2026-09-10.csv` | Authoritative for the finalized billed duration/cost. |

No raw model output, prompt body, predicted text, ground-truth text, credential, endpoint, model
path, or absolute runtime path is present in the safe report or this record.

## Immutable report identity

| Artifact | SHA-256 | Bytes |
|---|---|---:|
| Evidence report | `9bd636fedd470dc519929b6be550a6e72d0ceb03db73a72470e31118212ef916` | `36740` |
| Runtime source | `9bd636fedd470dc519929b6be550a6e72d0ceb03db73a72470e31118212ef916` | `36740` |

The two files are byte-identical JSON, including the repository-standard final newline.

## Experiment identity and D-7 boundary

| Field | Value |
|---|---|
| Manifest | `vision-v3-quality-manifest-v1` |
| Ground-truth SHA-256 | `e836593ec58a63757cee58d64b17800367a814c0f0956e8210458fe2cc6cb099` |
| Matching rule | `vision-v3-quality-matching-rule-v1` |
| Matching-rule SHA-256 | `af4326fb94585a7ed58f6387a8a8bea26f17a6e9ceca6556d6def573f6fea109` |
| Prompt protocol | `vision-v2-structured-output-prompt-v3` |
| Prompt SHA-256 | `bf8b9cab5df6b2551e627cf0bb92fe977e0dc182fdaae5f3c5face5bc34615f3` |
| Profile | `QWEN3_VL_8B_INSTRUCT_BF16_V1` |
| Profile-catalog SHA-256 | `72651b96d2c2259344efcb6fb3349807d42b56079a5422530db09c1590f00947` |
| Raw-output mode | `CLASSIFY_ONLY` |

Both passes carry the same approved identities and the same ordered eight fixture IDs and hashes.
The report records zero fenced, truncated, extra-key, invalid-enum, or lossless-unwrap events.
Raw output was classified only and was not persisted.

## D-6 completeness and comparability

| Field | Pass 1 | Repeat 1 |
|---|---:|---:|
| Attempted runs | 8 | 8 |
| Run records | 8 | 8 |
| Schema-valid results | 8 | 8 |
| Typed failures | 0 | 0 |
| Thresholds met | `false` | `false` |
| Started (UTC) | `16:24:33.523572` | `16:28:56.536997` |
| Completed (UTC) | `16:28:55.210908` | `16:32:21.426954` |
| Pass duration | `261.687336s` | `204.889957s` |
| Sum of per-fixture wall latency | `261.684469s` | `204.887371s` |

Repeat began `1.326089s` after Pass 1 completed, well inside the approved 15-minute window, and
the report declares the same Lightning session. There was no configuration, package, input,
runtime, device, schema-validity, completeness, truncation, or repeat-window blocker.

The operator-recorded interval from `studio_started_at=2026-09-09T16:24:08Z` to
`runner_finished_at=2026-09-09T16:32:21.428533Z` is `493.428533s` (`00:08:13.428533`). This is an
application-side interval only and must not be represented as the official billed duration.

## D-5 quality result

Both passes produced identical aggregate quality scores:

| Collection | Ground truth | Predicted | Matched | Coverage | Accuracy / count-rate | D-5 |
|---|---:|---:|---:|---:|---:|---|
| `entities` | 18 | 18 | 2 | `0.111111` | accuracy `0.111111` | Fail; both must be `>=0.80` |
| `actions` | 3 | 1 | 0 | `0.0` | accuracy `0.0` | Fail; both must be `>=0.80` |
| `relations` | 6 | 0 | 0 | `0.0` | accuracy `null` | Fail; coverage/accuracy must be `>=0.80` |
| `themes` | 5 | 0 | 0 | `0.0` | accuracy `null` | Fail; coverage/accuracy must be `>=0.80` |
| `ambiguous_regions` | 1 | 0 | 0 | `0.0` | count-rate `0.0` | Fail; count-rate must equal `1.0` |

The safe diagnostic counts were also identical: 16 entity exact-canonical-label mismatches, 13
expected-collection omissions, and one action full-label/endpoint mismatch per pass. The model
predicted the same total number of entities as ground truth but matched only two under the approved
strict rule; it omitted every expected relation, theme, and ambiguous region. Because raw and
predicted text are intentionally unavailable, this record does not infer the unseen vocabulary or
silently weaken the matching rule.

## Compute ledger — `CAP_EXCEEDED`

The finalized Activity export contains two 2026-09-09 `Qwen 3 VL` Studio rows on `1 × L4`.
The already-reconciled `00:44:41` / `0.35`-credit row is the Phase 6 session. The new
`00:37:22` / `0.24`-credit row is the Phase 8 session and supersedes the earlier partial
`00:06:32` / `0.07` snapshot; it is not an additional session. The CSV supplies only a start
date, not an official start or stop clock, so no clock or post-run idle allocation is inferred.

| Field | Value |
|---|---|
| D-8 hard cap | `00:30:00` |
| Operator-recorded runner interval | `00:08:13.428533` |
| Official billed duration | `00:37:22` |
| Official session cost | `0.24` credits |
| Cap exceedance | `00:07:22` |
| Compute-governance result | `CAP_EXCEEDED` |
| Official Lightning start clock | `NOT_AVAILABLE_FROM_EXPORT` (start date only) |
| Official Lightning stop clock | `NOT_AVAILABLE_FROM_EXPORT` |

The billed duration exceeds the D-8 hard cap even though the application-side benchmark interval
is shorter. The export does not identify how much billed time occurred before or after the runner,
so the excess is recorded without attribution. This governance result does not change the
technical report or quality verdict. No additional GPU run is required or authorized.

## Conclusion and next gate

- Phase 8 execution: complete.
- Structural/schema/repeat gate: passed.
- Held-out semantic quality gate: failed repeatably.
- Technical verdict: `QUALITY_NOT_READY`.
- Evidence closure: complete, including the official Activity duration/cost reconciliation.
- P2-T3 remains `IN_PROGRESS`; B5 and any production profile/default recommendation remain open.

Any prompt, scoring, taxonomy, matching-rule, or model remediation is a new planned and approved
work item. The Phase 8 package and this result must not be tuned against, rescored under a changed
rule, pooled with another run, or silently replaced.
