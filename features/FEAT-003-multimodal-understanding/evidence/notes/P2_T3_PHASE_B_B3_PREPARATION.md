# P2-T3 Phase B B3 preparation — structured-output mapping study

- Evidence ID: `EV-003-T3-07`
- Date: 2026-09-02
- Owner: Person 2
- Scope: **planning only.** No code, test, dependency, `.vision.env`, GPU, model, or provider
  action was taken to produce this note. It does not itself authorize or execute B3; B3 remains
  inside the already-approved bounded B1–B5 scope, and this note's job is to make that scope
  concrete and implementation-ready, the same way `P2_T3_PHASE_B_PREPARATION.md`
  (`EV-003-T3-PLAN-03`) did for the whole of Phase B before B1 was built.
- Approval authority: `approvals/TASK_APPROVAL.md`, bounded P2-T3 Phase B B1–B5 scope. B3 needs
  no new owner approval to begin — it is already inside the approved package — but this note
  flags every point where an implementer would otherwise have to invent an unstated decision,
  consistent with how D-1…D-11 were surfaced before B1.

## Owner decision record (2026-09-03)

**Status: CONFIRMED BY PROJECT OWNER.** The following is the implementation boundary for the
already-approved B3 work package; it neither widens Phase B nor authorizes B4/B5.

1. **Fixtures.** B3 uses exactly eight deterministic, geometric, synthetic image recipes/IDs.
   The runner generates them under ignored scratch and deletes them after the run. They have no
   ground truth or quality score and are disjoint from B4's future held-out set. The owner has
   confirmed the generator recipe and IDs; no per-image review is required for this synthetic,
   non-evaluation B3 study.
2. **Raw-output diagnostics.** The additive hook defaults to `CLASSIFY_ONLY`: it classifies raw
   output in memory and discards it, creating no raw file, log, result field, or evidence. For a
   specific B3 run, the owner or Person 2 may select `EPHEMERAL_CAPTURE` under the already
   approved B0 access rule; it writes only to ignored scratch for manual diagnosis and is deleted
   in `finally`. In either mode, B3 reports/evidence may retain only safe counts and closed typed
   identifiers — never raw text.
3. **Metrics.** The persistent raw-derived B3 breakdown contains only `fenced`, `truncated`,
   `extra_key`, and `invalid_enum` independent flags with denominator = attempted runs; flags may
   overlap. Duplicate-ID/reference integrity comes from typed results. A classifier may recognize
   a missing required field internally, but that category is not persisted in report/evidence.
4. **Execution and repair.** B3 uses the sole approved profile and frozen greedy decoding, makes
   exactly one adapter call per fixture, never retries a mapping failure, records per-run
   latency/VRAM after a `READY` check, and observes the combined B2–B4 one-hour soft cap. The
   repair rule remains lossless complete-fence unwrap only: B3 must not widen repair based on its
   observations.

## Re-verification performed before writing this note

Before drafting, the full governing document set was re-read and the repository state was
re-verified against it (not merely recalled):

- `approvals/TASK_APPROVAL.md` — re-read in full; the bounded B1–B5 scope, contract/runtime
  constraints, data/evidence/compute constraints, and non-goals are unchanged since 2026-09-01.
- `plan/P2_T3_VISION_RESEARCH_PLAN.md` — re-read in full (previously only partially read in this
  session), including the parts not covered by earlier turns: the complete typed error/retry
  matrix, the Phase A fixture/contract-test matrix, the Phase B B1–B5 work-package definitions
  (V1–V5), the safety-metric terminology table, the exit criteria, and the B1/B2 status sections.
- `evidence/notes/P2_T3_PHASE_B_APPROVAL_REQUEST.md` — the full B0 dossier, already read in this
  session; re-checked specifically for the B3 line, the raw-output handling table, and the
  budget rule.
- Repository state: `git status --short` is clean; HEAD is `fa8e089` (`docs(vision): record B2
  GPU preflight evidence`), which already contains the reviewed/hardened B2 preflight runner
  (`f3e5830`) and its evidence. Re-ran, from `backend/`: `pytest` (**427 passed, 5 skipped**),
  `ruff check .` (all checks passed), `mypy --strict src` (no issues in 51 source files), and
  from the repository root: `validate_harness.py` (`HARNESS_VALID`), `validate_repository_security.py`
  (`REPOSITORY_SECURITY_VALID`), `validate_architecture.py` (`ARCHITECTURE_VALID`),
  `validate_skeleton.py` (`SKELETON_VALID`), and `git diff --check` (clean). A grep across the
  whole feature folder for the overclaim phrasings corrected in the last documentation round
  (`full VRAM/device-memory release confirmed`, `not a defect to patch`, `pipeline works/behaved
  as designed end to end`, `did not satisfy`) returns zero matches — those corrections are intact
  in the committed state.

No inconsistency between the approved documents and the implemented/committed code was found.

## Where B2 left off

The one real B2 typed GPU preflight (`EV-003-T3-06`) returned `FAILED` / `VISION_SCHEMA_INVALID`
/ `OUTPUT_MAPPING_FAILED` at `attempt_number=1`, `repair_attempted=false`,
`policy_execution_state=NOT_EXECUTED`. That is exactly one contract-anticipated data point: it
proves the runtime/model-load/invocation/typed-classification/cleanup pathway works, and it shows
the model's output did not map cleanly on that one call, but a single run cannot say *how often*
that happens or *why*. B3 is the work package that turns "it happened once" into a measured
rate with a structural breakdown — it is diagnostic, not a benchmark (that is B4) and not a
recommendation (that is B5).

## B3's exact approved scope

Two governing documents state B3's scope; they agree and this note treats them as one:

- Plan, **V3 — Structured-output mapping behavior** (`plan/P2_T3_VISION_RESEARCH_PLAN.md:857-860`):
  "Measure how the real model's output actually arrives: rates of fenced output, truncation,
  extra keys, invalid enum values, and broken reference integrity; the share rescued by the
  permitted lossless unwrap; and `known_policy_trigger_rate`. Constrained decoding is treated as
  a mitigation, never as a guarantee."
- B0 dossier, **item 3 of the proposed approval scope**
  (`evidence/notes/P2_T3_PHASE_B_APPROVAL_REQUEST.md:659-661`): "Measure schema-valid rate,
  fenced/truncated/extra-key counts, duplicate IDs, broken references, lossless-unwrap recovery,
  and typed-failure counts, under the raw-output handling rules above, within the same combined
  budget."

Read together, B3 must produce, for a sample of real adapter calls against the one approved
candidate (`QWEN3_VL_8B_INSTRUCT_BF16_V1`):

| Measurement | Source |
|---|---|
| Schema-valid rate (`SUCCEEDED` / attempted) | The typed `status` already on every result |
| Typed-failure counts by `error_code`/`error_detail` | Already on every `FAILED` result |
| Lossless-unwrap recovery rate | `repair_attempted=true` share of `SUCCEEDED` results, already on every result |
| `known_policy_trigger_rate` | Reported as `NOT_APPLICABLE`, per D-2 — the fixture lexicon is fictitious, so this is not a real measurement regardless of sample size |
| Rate of fenced output | **Not exposed by the current adapter contract** — see "The measurement gap" below |
| Rate of truncation | **Not exposed by the current adapter contract** |
| Rate of extra keys | **Not exposed by the current adapter contract** |
| Rate of invalid enum values | **Not exposed by the current adapter contract** |
| Duplicate-ID / broken-reference counts | Collapsed into `OUTPUT_MAPPING_FAILED` alongside the four rows above at the public `error_detail` level, **except** `DUPLICATE_OBSERVATION_ID` and `REFERENCE_INTEGRITY_VIOLATION`, which already are their own distinct `error_detail` tokens (`plan/P2_T3_VISION_RESEARCH_PLAN.md:761`) and therefore already countable from the typed result alone |

## The measurement gap (the one real design decision B3 needs)

`VisionNonPolicyErrorDetailV2.OUTPUT_MAPPING_FAILED` is, by design, one token covering several
distinct causes: malformed JSON, truncated JSON, an extra field, a missing field, and an invalid
enum value all map to the same `OUTPUT_MAPPING_FAILED` (`plan/P2_T3_VISION_RESEARCH_PLAN.md:761`,
unchanged by the V2 amendment). That collapsing is deliberate and correct for the **public**
result contract — P2-T4 must never have to branch on raw-output shape — but it means the fenced
/truncated/extra-key/invalid-enum breakdown the approved scope asks for cannot be read off
`VisionUnderstandingResultV2` alone. Getting it requires classifying the *raw* output, which the
frozen adapter never returns to any caller (`qwen_vision.py`'s `_parse_raw_output` is a private
function; raw text never crosses the adapter boundary in any existing return path).

This is not a blocker invented by this note — the B0 dossier's raw-output handling table already
anticipates it: "Who may read it: The project owner, and Person 2 while diagnosing mapping
failures" (`evidence/notes/P2_T3_PHASE_B_APPROVAL_REQUEST.md:533`) only makes sense if *some*
mechanism exposes raw output ephemerally for that diagnosis. B3 is where that mechanism has to
actually exist. The proposed shape, consistent with every constraint already approved:

1. Add an **optional, injectable diagnostic hook** to the generation path (e.g. an
   `on_raw_output: Callable[[str], None] | None` passed at adapter-construction or call time),
   never wired into any default/production path and never added to `VisionUnderstandingResultV2`
   or any other public contract. This is additive to the adapter's internals only.
2. In the default `CLASSIFY_ONLY` mode, the B3 runner supplies a local B3-only classifier that
   examines raw output in memory — fenced vs. plain, complete vs. truncated JSON,
   extra/missing/invalid-enum-shaped — then discards the text. It writes no raw text anywhere.
   For a specific diagnostic run only, the owner or Person 2 may select `EPHEMERAL_CAPTURE`:
   ignored scratch may then hold the text for manual diagnosis, with deletion in `finally`.
3. Only the resulting approved **counts** (never text) are folded into the B3 report. The
   persistent raw-derived breakdown is fenced/truncated/extra-key/invalid-enum only;
   missing-required-field is classifier-local and never reported or evidenced.
4. Person 2 and the owner may read an `EPHEMERAL_CAPTURE` file during that specific run under the
   existing B0 raw-output table. This is an operational mode of an already-approved access rule,
   not a new approval; the evidence boundary remains counts and closed identifiers only.

This hook is a small, additive, non-breaking adapter change (a new optional parameter, not a new
result field) and is squarely inside the approved B3 scope ("under the raw-output handling rules
above"), but it **is** a code change to `qwen_vision.py`, so it should go through the same
review discipline as B1/B2's code did — it is called out here explicitly rather than silently
assumed.

## Fixture sourcing — owner-confirmed

B3 does not score accuracy, so it needs no ground truth and no owner-reviewed held-out manifest
the way B4 does (D-10 governs B4's held-out set specifically). But B3 does need **varied**
synthetic images: decoding is frozen greedy (`VisionDecodingV1.sampling_enabled=False`), so
running the *same* image repeatedly — as B2's single scratch image does — would reproduce the
identical output every time and add no information about how mapping behavior varies with input.

The owner has confirmed the following B3-only fixture boundary:

- Generate exactly **eight distinct deterministic synthetic images** (varied shape
  count/complexity, still
  purely synthetic — no real child data, matching the same style already proven to pass P2-T1 in
  `_write_synthetic_preflight_image`/`_write_p2t1_companion_image`), regenerated as ephemeral
  scratch on each run rather than versioned in the repository — this needs no new `.gitignore`
  entry or fixture directory, unlike B4's `fixtures/vision-b4/images/**`, which is reserved for
  the held-out set and must stay reserved for it.
- **B3's images must be disjoint from B4's held-out set.** Running the model against an image
  before B4 sees it — even just to observe mapping behavior, with no ground truth involved — is a
  form of peeking that could bias how the pipeline (or a future prompt/decoding tweak) is tuned
  before the held-out evaluation. This note flags it explicitly because no existing document
  states it, and B4's integrity depends on it.
- The eight stable recipe IDs and generator are recorded in B3 code/tests, not as image payloads
  in the repository. The owner has confirmed that this is not an accuracy/ground-truth study and
  therefore needs no per-image review. B4's held-out images remain separately authored and
  reviewed under D-10.

## Constraints carried forward unchanged

- **Budget.** B2's one call measured `wall_latency_ms=25729.17` (~25.7 s) against the shared
  one-hour B2–B4 Lightning L4 soft cap — a small fraction of it, but this note does not claim a
  cumulative session total; tracking remaining budget stays the operator's responsibility, and
  the stop-and-reauthorize rule applies exactly as it did for B2.
- **Raw-output handling.** `CLASSIFY_ONLY` is default: raw text is classified in memory and
  discarded. A specific run may use owner/Person-2-selected `EPHEMERAL_CAPTURE` in gitignored
  `data/runtime/...`, deleted in `finally`, for diagnosis only. Only safe counts and closed typed
  identifiers may persist into the B3 report; model-produced free text, prompts, provider
  payloads, and stack traces containing output may never persist.
- **D-1 (semantic-safety control).** Synthetic-fixtures-only, with owner review before any
  real-model output enters feature evidence — this governs the B3 *report*, which must contain
  counts only, never text, so nothing in it requires per-item owner review; it does not relax the
  general reminder that a human is reading unfiltered model text during diagnosis, which is B3's
  real safety exposure, controlled by process rather than the lexical layer.
- **D-2 (lexicon).** `known_policy_trigger_rate` stays `NOT_APPLICABLE` against the synthetic
  fixture lexicon; the lexical-policy tests remain wiring evidence only, never a model-safety
  claim.
- **No widening.** V1 stays frozen. The repair rule stays lossless-fence-unwrap-only — B3 measures
  the schema-valid rate as a finding, it does not become a reason to widen repair. `timeout_retry_policy`
  stays `NEVER_RETRY`. No new `error_code`/`error_detail` token is added to the public contract by
  the diagnostic hook above.

## Explicit non-goals for B3

No B4 held-out benchmark or repeat run. No B5 recommendation, ADR profile freeze, or runtime
default. No CLI, API, UI, mobile, database, or queue work. No real child data. No production or
Integration Sprint decision. No ground-truth authoring (that is D-10's B4-specific requirement).

## Proposed B3 report shape

Mirroring `VisionB2PreflightResult`'s discipline (typed fields, `NOT_MEASURED`/`NOT_APPLICABLE`
stated explicitly, never a bare `0` standing in for "no data"), a B3 report per run should carry:
the typed outcome fields already on `VisionUnderstandingResultV2` (or a summary of them across
the sample), independent `fenced`, `truncated`, `extra_key`, and `invalid_enum` flags/counts,
the lossless-unwrap recovery rate, `known_policy_trigger_rate=NOT_APPLICABLE`, and per-run
latency/VRAM exactly as B2 already measures them (reusing `_VramSampler`-style sampling).
`missing_required_field` is classifier-local and absent from report/evidence. Aggregation across
the sample must state its denominator explicitly (attempted-run count); raw-derived flags may
overlap and are therefore not a partition of attempted runs.

## Acceptance checklist before B3 executes for real

- [x] Owner confirmed the eight deterministic geometric B3 fixture recipes/IDs, ephemeral
      scratch generation, no ground truth/per-image review, and disjointness from B4's held-out
      set.
- [ ] The raw-output diagnostic hook is implemented as an additive, optional adapter parameter,
      reviewed the way B1/B2's code changes were. It defaults to in-memory `CLASSIFY_ONLY`; an
      owner/Person-2-selected per-run `EPHEMERAL_CAPTURE` must clean scratch in `finally`; neither
      mode may persist raw text. No public contract or repair rule may widen, and no-GPU tests
      must prove this using an injected fake — the same anti-fabrication discipline finding #14
      already established for B2.
- [ ] The B3 runner (multi-fixture, single-profile) is implemented, unit-tested against an
      injected fake `VisionUnderstandingPortV2` (success, each relevant typed-failure path,
      cleanup-on-raise), and passes the full local validation set: focused tests, full backend
      suite, Ruff, `mypy --strict`, all four repository validators, `git diff --check`.
- [ ] A pre-run readiness check (`QwenVisionEnvironmentReadinessV1`) returns `READY` on the
      Lightning session that will run it.
- [ ] Remaining Lightning L4 budget under the shared one-hour B2–B4 soft cap is confirmed
      sufficient before starting; the operator stops and requests reauthorization if it is
      reached mid-run rather than continuing silently.
- [ ] The evidence note recording the real B3 execution states measured values only, with
      `NOT_MEASURED`/`NOT_APPLICABLE` for anything not actually captured, and contains no raw
      model output, prompt, path, credential, or traceback — matching every prior B2 evidence
      note in this feature.

## What this note is not

Not a B3 implementation. Not a code change. Not a GPU/model/dependency/`.vision.env` action. Not
a new owner approval (none is needed; B3 is already inside the approved B1–B5 package). It records
the owner's B3 implementation decisions but does not execute them. Not B4 or B5.
