# FEAT-018 P2-T1 — D3 image-admission evaluation plan

- Revision: D3-R2, 2026-09-10
- Status: `HARNESS_IMPLEMENTED / PREFLIGHT_VERIFIED / FORMAL_EXECUTION_PENDING`
- Parent task: `FEAT018-P2-T1`
- Prerequisites: D1 specification `EV-018-P2-D1-SPEC-01`; reviewed D2 implementation
  `EV-018-P2-D2-IMPL-01`
- Owner: Person 2
- Scope type: offline performance and native-memory evaluation only

The project owner approved this D3-R2 method and D3-U1 through D3-U6 by direct instruction on
2026-09-10. The approval is recorded in `approvals/TASK_APPROVAL.md`. It authorizes the isolated D3
harness, Cohort A execution and reviewed evidence workflow described here. Cohort B execution still
requires visual review of the actual eight candidate images. Approval does not mark D3 or P2-T1
complete and does not authorize any excluded downstream scope.

## 1. Outcome

Measure the reviewed D2 image-admission implementation against D1's two **evaluation targets**:

- `admission_elapsed_ms` at or below 5 seconds per image;
- native-inclusive admission-phase working-set growth at or below 256 MiB per image, evaluated from
  a conservative lower/upper bracket rather than an unsafe single peak-minus-peak delta.

For memory, `WITHIN_TARGET` requires the measured upper bound to be at or below 256 MiB;
`EXCEEDS_TARGET` requires the measured lower bound to exceed 256 MiB; a bracket crossing the target
is `INCONCLUSIVE`. `parent_wall_ms`, lifetime peak, `PrivateUsage` and saturation are diagnostics
only. No unknown or saturated measurement is silently treated as a pass.

The output is an auditable local evaluation report with distributions, exact environment and
fixture provenance. The targets are observations, not runtime enforcement. An exceeded target
produces an honest `EXCEEDS_TARGET` result; it does not get relabeled as an input failure and does
not silently change D2 limits or policy.

## 2. Non-goals

D3 does not:

- add a timeout, watchdog, worker pool or memory-kill mechanism to production admission;
- change D2 outcomes, limits, allowlists, dependency pins or public contracts;
- connect Qwen, ASR, FEAT-003 producers, mobile transport, Gate A or shared integration;
- evaluate model quality, semantic accuracy, image-quality scoring or recapture UX;
- use child/personal images, network/provider calls, GPU sessions or cloud storage;
- claim production readiness from synthetic fixtures or a small local photo cohort.

Any need for hard time/memory isolation becomes a separate reviewed implementation scope after
D3; it is not smuggled into this evaluation.

## 3. Sources of truth

Before any approved D3 work, read:

1. repository `AGENTS.md` and `docs/context/SOURCE_REGISTER.md`;
2. FEAT-018 `CONTEXT.md`, `DECISIONS.md`, `approvals/TASK_APPROVAL.md`, `plan/PLAN.md` and
   `plan/PERSON_2_AI.md`;
3. D1 sections 3, 5, 7, 8, 9 and 11;
4. D2 implementation/evidence and the exact committed D2 tests;
5. repository benchmark-runner conventions under `backend/src/sketch2life/benchmark/`.

D1 and D2 remain immutable inputs to the measurement. If the runner needs a product-code change,
stop and request a separate scope review.

## 4. Recommended approach

### Alternatives considered

| Approach | Benefit | Main problem | Decision |
|---|---|---|---|
| Measure repeatedly in the pytest process | Smallest effort | Allocator/import/cache retention contaminates memory and cold timing | Reject |
| Fresh subprocess per sample | Isolates lifetime and gives native-inclusive process metrics | More runner work and process-start overhead must be reported separately | **Recommend** |
| Poll current working set | Gives intermediate observations | Scheduling can miss 15–50 ms native spikes; observations are lower bounds only | Diagnostic only; not required |
| Add a killable production worker now | Could enforce deadlines | Expands D2 architecture and confuses measurement with protection | Defer |

Use one fresh local subprocess per sample. The child loads the committed D2 implementation,
admits exactly one file and emits one bounded JSON result to stdout. The parent owns orchestration,
process exit/cleanup, aggregation and evidence writing. No raw bytes or absolute source paths enter
the result.

## 5. Proposed measurement contract

Each child result should contain:

- schema name/version and opaque `sample_id`;
- fixture ID, cohort and repeat index;
- source SHA-256, byte count and declared/decoded metadata allowed by D2;
- D2 outcome/reason and policy/limits identity;
- `admission_elapsed_ms` measured inside the child with `perf_counter_ns()`;
- `parent_wall_ms` covering spawn, import, admission and clean exit;
- `working_set_before_bytes` and `working_set_after_bytes` from the current `WorkingSetSize` field;
- `peak_before_bytes` and `peak_after_bytes` from lifetime `PeakWorkingSetSize`;
- `memory_lower_bound_bytes = max(0, working_set_after_bytes - working_set_before_bytes)`;
- `memory_upper_bound_bytes = max(0, peak_after_bytes - working_set_before_bytes)`;
- `peak_saturated = (peak_after_bytes == peak_before_bytes)` as diagnostic context only;
- `private_usage_before_bytes` and `private_usage_after_bytes` as diagnostic-only commit values;
- process exit status and typed measurement failure, if any;
- Python, PyAV, linked FFmpeg, OS/architecture and commit identity.

Target classification is fixed as follows:

- 5-second target -> `admission_elapsed_ms` only;
- 256-MiB target -> `WITHIN_TARGET` when `memory_upper_bound_bytes <= 256 MiB`,
  `EXCEEDS_TARGET` when `memory_lower_bound_bytes > 256 MiB`, otherwise `INCONCLUSIVE`;
- `parent_wall_ms`, raw current/peak/private values and `peak_saturated` -> diagnostic context only.

The harness always passes an opaque `sample_id`/`fixture_id` as D2's `artifact_ref`. The real
source path is used only to open the local scratch input and must never be supplied as
`artifact_ref` or copied into a result/evidence field.

Never store the absolute file path, raw image, exception traceback, environment dump, command-line
secret, prompt, provider output or token.

### Windows native-memory method

Use `ctypes` with `K32GetProcessMemoryInfo`/`GetProcessMemoryInfo` and
`PROCESS_MEMORY_COUNTERS_EX`. Load the API with `use_last_error=True`, declare every `argtypes` and
`restype` explicitly, represent every Windows `SIZE_T` field as `ctypes.c_size_t` rather than
`c_ulong`, and set `cb = ctypes.sizeof(PROCESS_MEMORY_COUNTERS_EX)` before the call. Check the API's
own `BOOL` return value; a false result records `MEASUREMENT_INVALID` with a bounded typed error
derived from `ctypes.get_last_error()`. Output-value sanity checks are additional protection, not a
substitute for checking the call result. Unit-test all of these requirements against a fake. A zero
raw size or `peak_after_bytes < peak_before_bytes` is `MEASUREMENT_INVALID`. Current
`WorkingSetSize` and `PrivateUsage` may legitimately decrease; their derived growth clamps to zero
and is not rejected merely for decreasing.

Read the same structure twice: immediately before and immediately after
`Feat018ImageAdmission.admit()`. At both points record current `WorkingSetSize`, lifetime
`PeakWorkingSetSize`, and diagnostic `PrivateUsage`. Let `P0` be current working set before the
call, `P1` current working set after it, and `H1` lifetime peak after it. For the true maximum
working-set growth `M` during the call:

```text
L = max(0, P1 - P0)
U = max(0, H1 - P0)
L <= M <= U
```

`L` is conservative because the end reading can miss a released transient spike. `U` is
conservative because the lifetime peak may predate the call. Consequently, `U <= 256 MiB` proves
the target was not exceeded, `L > 256 MiB` proves it was exceeded, and `L <= 256 MiB < U` is
`INCONCLUSIVE`. A saturated lifetime peak never overrides this classification. Never classify
`PeakWorkingSetSize_after - PeakWorkingSetSize_before`; the counterexample where import previously
set a high peak makes that delta capable of a false pass.

If Windows native metrics are unavailable, record `NOT_MEASURED`; if the call fails or returns an
impossible zero/decreasing lifetime reading, record `MEASUREMENT_INVALID`. Do not substitute
`tracemalloc`, Python heap measurements or a polling lower bound. Optional polling may appear only
as separately labeled diagnostic data.

### Timing method

Generate/write the fixture, freeze its digest, and construct the decoder/service before timing.
Set `t0 = perf_counter_ns()` immediately before calling `Feat018ImageAdmission.admit()` and `t1`
immediately after it returns. The interval therefore includes D2's bounded read, complete-source
digest, metadata/frame probe, decode and policy evaluation, but excludes fixture generation,
scratch-file writes, imports, decoder construction and result serialization.

Measure at least these distinct fields:

- in-child admission time;
- parent end-to-end wall time;
- first sample of each profile, reported separately from later samples.

Generate each Cohort A source once before its run and reuse byte-identical, hash-verified scratch
content for its repeats. "First sample" can reflect uncontrolled OS source/interpreter/DLL cache
state; D3 does not flush OS caches and must not label observations as controlled cold-cache data.
Do not subtract an assumed process-start cost. Report raw observations and sample counts.

## 6. Proposed fixture cohorts

### Cohort A — deterministic synthetic boundary set

Generate ephemeral files once per run from versioned generator identities, verify their hashes,
and reuse the exact bytes for all repeats; commit no image binaries. Include:

- supported PNG: RGB, RGBA, grayscale, palette and 1-bit;
- supported baseline JPEG `yuvj420p`;
- near byte limit, 4 MP pixel limit and 4096 longest-edge cases;
- over-byte, over-pixel, over-edge, corrupt/truncated and unsupported cases;
- one multi-frame/container rejection diagnostic.

Measure rejected cases too because early rejection cost is part of admission behavior, but report
them separately from fully decoded `ADMITTED` samples. Further split rejections into those that
never reached `decode_one_frame` and those, such as the garbage-IDAT case, that attempted decode;
trivial early rejections must not dilute the memory-relevant decode-attempted subgroup.

### Cohort B — local non-sensitive photographic diagnostic set

Recommended only after explicit fixture-source approval:

- 8 owner-reviewed images: 4 JPEG and 4 PNG;
- no people, children, documents, screens, location clues or personal metadata;
- before hashing or execution, the owner visually reviews every candidate against that exclusion
  list and records a bounded `owner_reviewed=true` decision in the ignored local manifest;
- varied dimensions/bytes spanning small, typical and near-policy limits;
- raw files and local path manifest remain ignored and never enter Git;
- canonical evidence retains only opaque IDs, hashes, bounded metadata and results.

This cohort is needed because D1's uniform synthetic images are highly compressible and cannot
support camera-realistic performance claims. Eight images are still diagnostic, not statistically
representative; the report must say so.

### Repetition proposal

- Cohort A: 20 fresh-process repeats per synthetic source/profile;
- Cohort B: 3 fresh-process repeats per owner-reviewed photograph;
- deterministic fixed seed/order recorded, with a second reversed-order pass only if cache/order
  effects exceed 10%;
- Cohort A reports p50, p95, maximum and sample count only for a homogeneous source/profile with at
  least 20 valid observations;
- p95 uses the dependency-free nearest-rank rule: sort ascending and select
  `ceil(0.95 * n) - 1` using a zero-based index;
- Cohort B reports minimum, median, maximum and sample count; it must not report p95 from three
  repeats;
- never combine unlike profiles merely to obtain a larger percentile sample.

For the order-effect gate, compute `a` as the median `admission_elapsed_ms` of the first five valid
repeats and `b` as the median of the last five for each Cohort A profile. An effect is
`abs(a - b) / max(a, b) > 0.10`. If any profile crosses it, run one full second pass with the
profile order reversed and report both passes separately; never replace the original pass.

## 7. Proposed file impact

The approved implementation may create or change only these proposed files:

1. `backend/src/sketch2life/benchmark/image_admission_evaluation.py` — parent runner, child mode,
   native-memory adapter, typed result and aggregation;
2. `backend/tests/unit/test_image_admission_evaluation.py` — result validation, command/cleanup,
   aggregation, invalid-memory and redaction tests;
3. `features/FEAT-018-live-image-canvas-flow/fixtures/image-admission/evaluation-manifest-v1.json`
   — synthetic evaluation identities/expected D2 outcomes only, no image bytes or machine paths;
4. ignored operator-local input manifest for Cohort B — exact location chosen only at execution;
5. after execution, one sanitized metrics JSON and one Markdown execution record under this
   feature's `evidence/` tree.

No dependency change is proposed. If native metrics require a new package, stop; the preferred
implementation is stdlib `ctypes`.

The new benchmark module belongs to FEAT-018 and may import only the reviewed FEAT-018 D2 service,
its contracts/ports and stdlib/PyAV implementation boundary. It must not import, edit, register
with, or be imported by any FEAT-003 benchmark module; sharing the directory creates no behavioral
dependency.

## 8. Delivery phases and gates

### D3-0 — approval and fixture gate

- Owner selects Cohort A only or A+B.
- Record D3 scope approval in `approvals/TASK_APPROVAL.md`.
- For Cohort B, visually review each candidate against the exclusion list before hashing, then
  review the source policy and ignored local manifest before execution.
- Freeze result schema, repetition/reporting rules and the exact target-to-field bindings:
  5 seconds to `admission_elapsed_ms`, and 256 MiB to the approved memory bracket. Freeze
  `INCONCLUSIVE` as a valid measurement outcome that can never be counted as a pass.

Stop if approval or compliant inputs are missing.

### D3-1 — deterministic harness implementation

- Implement typed parent/child protocol and redacted result schema.
- Enforce one sample per fresh subprocess, a hard 64 KiB input-request limit, and a hard 64 KiB cap
  for each of stdout and stderr. Reject oversized input before child processing. Terminate/clean up
  a child that exceeds either output cap and record `OUTPUT_LIMIT_EXCEEDED`; do not capture
  unbounded output first and truncate it afterward.
- Launch the child with the current environment's interpreter using
  `sys.executable -m sketch2life.benchmark.image_admission_evaluation --child`. Pass the bounded
  single-sample request through stdin so the source path is not exposed in the child command line.
- Apply a parent-owned hard timeout solely to prevent a stuck evaluation subprocess. This is
  benchmark-harness failure handling, not production admission enforcement.
- Pass only an opaque ID as D2 `artifact_ref`; the scratch path remains input plumbing and is never
  serialized into D2 results or evidence.
- Wrap the child entry point in a top-level exception boundary. Stdout is either one valid bounded
  JSON result or empty; a raw traceback is never written to stdout or published from stderr. Map
  malformed/partial output and abnormal exits to bounded typed parent-side failures.
- Add cleanup/abnormal-exit handling without claiming production timeout enforcement.
- Add unit tests using fakes for `c_size_t` layout, `cb`, false API returns/last-error handling,
  invalid values, timeout/cleanup and redaction, plus a minimal real-process smoke.

No performance conclusion is produced in this phase.

### D3-2 — preflight

- Verify exact commit, Python, PyAV and FFmpeg identity.
- Verify every source hash before running.
- Confirm no raw bytes/path/EXIF/private metadata can enter evidence.
- Run D2 focused tests and repository security/architecture validators.
- Execute one non-reporting sample and inspect the complete output schema.
- Run a real-process adapter calibration using a known-size, page-touched allocation and a stated
  tolerance. This validates Win32 wiring only; it does not prove exact PyAV allocation accounting.

Stop on version drift, hash drift, invalid native-memory readings or residual child processes.

### D3-3 — controlled local execution

- Run the approved cohort/repetitions with no other intentional workload.
- Prepare and hash scratch inputs before child launch; reuse exact bytes within the approved run.
- Preserve every typed sample result locally until aggregation succeeds.
- On crash or interruption, keep the run incomplete; never merge partial runs into a completed
  distribution without labeling them.
- Confirm every child exited and no process remains.

### D3-4 — analysis and evidence

- Aggregate by admitted/rejected outcome, format/profile, size band and cohort.
- Apply the approved cohort-specific statistics: Cohort A p50/p95/max only for homogeneous groups
  with at least 20 valid observations; Cohort B min/median/max with no p95.
- Classify each sample's 5-second target from `admission_elapsed_ms`. Classify memory from `[L, U]`
  as `WITHIN_TARGET`, `EXCEEDS_TARGET`, `INCONCLUSIVE`, `NOT_MEASURED` or
  `MEASUREMENT_INVALID`.
- A homogeneous profile is `WITHIN_TARGET` only when every valid sample has `U <= 256 MiB`; it is
  `EXCEEDS_TARGET` when any valid sample has `L > 256 MiB`; otherwise it is `INCONCLUSIVE`.
- A homogeneous timing profile is `WITHIN_TARGET` only when every valid sample is at or below 5
  seconds and is `EXCEEDS_TARGET` when any valid sample exceeds 5 seconds; typed failures remain
  separate and cannot be counted as passing samples.
- Report `parent_wall_ms` and raw current/peak/private values separately as diagnostics; never
  classify those raw fields against a D1 target.
- Explain outliers without deleting them; reruns are separately identified, never substituted.
- Publish sanitized JSON plus a human-readable execution record only after owner review.

### D3-5 — P2-T1 close recommendation

D3 execution/evidence can complete while honestly reporting `INCONCLUSIVE`. D3 can recommend
P2-T1 completion only if the approved run is complete, evidence is reviewed, all D2 regressions
remain green, and every `EXCEEDS_TARGET` or `INCONCLUSIVE` profile has an explicit owner resolution.
Neither a breach nor uncertainty automatically fails D2 correctness; each creates a separately
reviewed decision to accept the trial result, gather stronger evidence, revise the target with new
authority, or design hard isolation.

## 9. Acceptance criteria

- Every reported sample ran in a fresh subprocess against the recorded D2 commit.
- Source hashes, configuration, environment and decoder identities are complete.
- Native-inclusive memory is measured through the approved Windows API or explicitly unavailable.
- Timing and memory fields cannot silently default to zero.
- Every valid memory classification satisfies the bracket rules; no peak-to-peak delta or polling
  observation can classify the 256-MiB target.
- The Windows adapter uses `c_size_t` for `SIZE_T`, initializes `cb`, checks the API `BOOL` result
  and records bounded last-error information on failure.
- Parent confirms clean child exit; interruption/partial runs cannot be marked complete.
- Synthetic and photographic cohorts are never combined into one unlabeled statistic.
- Targets remain observational; no hard-enforcement claim appears.
- Evidence contains no raw bytes, absolute paths, EXIF/private metadata or secrets.
- D2 `artifact_ref` contains only the opaque sample ID and is proven not to contain the source path.
- Child output obeys the 64 KiB per-stream caps, and unexpected harness exceptions cannot publish
  tracebacks or partial/untyped output.
- Focused D2 tests, full backend regressions, lint/type checks and repository validators pass.
- Report states sample counts, limitations and whether each target was met.
- Target status uses only the approved target-to-field bindings; diagnostic fields cannot affect it.
- No D2 product behavior, FEAT-003 file or downstream integration is modified.

## 10. Validation required after approved implementation

- focused unit tests for the D3 runner and result schema;
- native-memory adapter tests covering structure layout, `cb`, false API return, invalid values and
  bounded last-error handling;
- real-process known-allocation calibration with a documented tolerance and an explicit statement
  that it validates adapter wiring rather than exact decoder accounting;
- bracket truth-table and aggregate-profile tests covering `WITHIN_TARGET`, `EXCEEDS_TARGET` and
  `INCONCLUSIVE`, including the 500/100/400 MiB false-pass counterexample;
- child invocation, 64 KiB stdin/stdout/stderr enforcement, output-overflow, harness-timeout,
  opaque-`artifact_ref`, traceback redaction and cleanup tests;
- existing 58-test D2 suite;
- FEAT-003 regression list and serialized-provenance parity;
- full backend suite;
- Ruff and mypy on new files;
- `validate_harness.py`, `validate_repository_security.py`, `validate_architecture.py`,
  `validate_skeleton.py` and `git diff --check`;
- explicit process-leak check after success, child failure and interrupted-run tests.

## 11. Risks and stop conditions

- **Measurement validity:** stop if native metrics are zero, unavailable without labeling,
  impossible, or polluted by reuse of the same process. Never convert an inconclusive bracket into
  a pass.
- **Fixture realism:** do not generalize Cohort A to real photographs or Cohort B to production.
- **Privacy:** stop and remove a local input from the run if it contains a person or identifying
  information; never add the raw file to Git/evidence.
- **Scope:** stop if evaluation needs a production worker or production timeout, dependency, D2
  policy change, public contract or FEAT-003 edit. A parent-owned benchmark subprocess timeout is
  allowed only as evaluation cleanup/failure handling.
- **Reproducibility:** stop publication if generator/hash/environment identity is incomplete.
- **Interruption:** an interrupted run is `INCOMPLETE`, not a smaller successful sample set.

## 12. Approved owner decisions

| ID | Decision | Recommendation |
|---|---|---|
| D3-U1 | Fixture scope | Approve Cohort A+B; allow A-only harness development first; require owner visual review of every Cohort B image before hashing/execution |
| D3-U2 | Sample and reporting policy | Cohort A: 20 repeats per homogeneous source/profile with p50/p95/max; Cohort B: 8 non-sensitive files (4 JPEG + 4 PNG), 3 repeats each with min/median/max and no p95 |
| D3-U3 | Target semantics | Keep targets observational; bind 5 s to `admission_elapsed_ms`; classify 256 MiB only from `[L,U]`: `U <= target` within, `L > target` exceeds, otherwise inconclusive |
| D3-U4 | Memory platform | Approve two Win32 current/peak reads around `admit()` with explicit `ctypes` checks; raw peak/private values are diagnostic and other platforms report `NOT_MEASURED` |
| D3-U5 | Order-effect rule | Reverse profile order only if first-five versus last-five timing medians differ by more than 10%; preserve and report both passes |
| D3-U6 | Evidence publication | Review sanitized JSON/Markdown before indexing or marking D3/P2-T1 complete |

D3-U1 through D3-U6 and the exact file scope are approved and recorded. D3 implementation may
begin within this boundary. Cohort B may not execute until the owner visually reviews the actual
eight candidate images, and sanitized evidence may not be indexed or used to close D3/P2-T1 until
the completed output receives owner review.
