# FEAT-018 P2-T2 D9 stdout/stderr enforcement approval package

Preparation date: 2026-09-21
Package status: `DESIGN_RECORD_ONLY`
Verdict: `D9_PACKAGE_BLOCKED_PENDING_D11_AND_CONTRACT_REVIEW`

This is a governance/design package only. It does not modify source or tests,
resolve D9 or D11, make a live authorization, or run a runtime workload. It
records a proposed stdout/stderr enforcement contract and a proposed offline
design boundary. It does not establish an exact implementation-approval scope
while the concrete D11/live carrier remains unknown. Implementation requires a
separate explicit approval after D11 and contract review.

## Protected state

```text
D9 numeric ceilings = OWNER_SELECTED_CANDIDATE_ONLY
D9 stdout/stderr = SEPARATE_ENFORCEMENT_APPROVAL_REQUIRED
D9_PACKAGE = DESIGN_RECORD_ONLY
D9_LIVE_D11_CARRIER_SCOPE = UNKNOWN_UNRESOLVED_PENDING_D11
D9 = BLOCKED_PENDING_D11_AND_CONTRACT_REVIEW
D11 = BLOCKED
D1 = BLOCKED_BY_D11
STAGE_4 = NOT READY
LIVE/MODEL/GPU/PROVIDER/NETWORK/LIGHTNING = NOT AUTHORIZED
```

The package does not interpret the existing `0` constructor defaults as a
stream-disable rule and does not claim that an observed byte currently fails
closed. Those semantics are absent from the reviewed runtime and remain a
separate enforcement approval.

## 1. Source-grounded baseline

The reviewed implementation identity is owner-bound to commit
`9549a341194f40b1a9be419d6fce0d70f1ca0384`:

| Role | Repository-relative path | Git blob |
|---|---|---|
| Reviewed runtime | `backend/src/sketch2life/benchmark/feat018_live_lightning_execution.py` | `94db10bedf95ab105f6c8653adac991bce94fa35` |
| Reviewed unit tests | `backend/tests/unit/test_feat018_live_lightning_execution.py` | `d7846f22fddf55ae234387e9e43d504a848112ee` |

The checked-out source and test blobs were re-verified against the live Git
object store and have no local diff. Direct inspection establishes:

| Reviewed fact | Evidence | Conclusion |
|---|---|---|
| Configuration fields exist | `Feat018BoundedRunnerConfig` declares `stdout_max_bytes` and `stderr_max_bytes` at source lines 129-130 | Declaration only |
| Configuration validation exists | `__post_init__` checks both fields only for non-negative values at lines 145-148 | Validation only; no enforcement meaning |
| Raw output is bounded | `_generation_child_entry` accepts `raw_output_max_bytes`, measures `len(raw_output.encode("utf-8"))`, and emits `raw_output_overflow` before the success frame at lines 1067-1104 | Existing raw-output seam, independent of streams |
| IPC is bounded | `MultiprocessingBoundedConnection` receives/sends under `ipc_envelope_max_bytes`; overflow maps to `ipc_envelope_overflow` | Existing IPC seam, independent of streams |
| Stream capture/handoff is absent | The reviewed source has no stdout/stderr capture, redirect, pipe, reader, stream argument, or stream handoff beyond lines 129-148 | No current stream boundary |
| Stream byte enforcement is absent | A full-file search finds no other `stdout_max_bytes` or `stderr_max_bytes` reference | No current stream byte check or overflow action |
| Stream overflow carrier is absent | No stream-specific failure code, frame, result field, or finalizer fact exists in the reviewed boundary | No typed stream failure fact |
| Stream tests are absent | The reviewed unit test file has no `stdout_max_bytes` or `stderr_max_bytes` reference and no stream-capture fixture/test | No stream enforcement test coverage |
| Current worker handoff | `adapter_worker_entry` constructs the adapter and runner after the containment gate; it does not pass stream ceilings or install a stream boundary | Worker handoff is unresolved |
| Current live dispatch | `run_live_smoke` receives an injected `adapter_call`; the reviewed source has no concrete live caller or bounded-dispatch wrapper | D11 remains a dependency |

The plan and earlier bounded-runner package contain a proposed zero-stream
interpretation, but the direct source/test baseline above controls this package:
the reviewed runtime currently declares and validates the fields only.

## 2. Candidate values and approval status

The separate D1 candidate-ratification report records the following as
`OWNER_SELECTED_CANDIDATE` values only. This package preserves that status and
does not promote any value to an exact runtime binding:

```text
raw_output_max_bytes = 65536
ipc_envelope_max_bytes = 98304
stdout/stderr = SEPARATE_ENFORCEMENT_APPROVAL_REQUIRED
```

`raw_output_max_bytes` and `ipc_envelope_max_bytes` remain exact-value
unresolved until the owner approves their binding in the appropriate D1/D9
record. No numeric `stdout_max_bytes` or `stderr_max_bytes` is selected here.
Any stdout/stderr limit remains unresolved until this implementation contract,
the exact enforcement seam, and the corresponding separate approval are
accepted. A missing or implicit stream value is not a disable signal.

## 3. Proposed D9 contract for owner approval

The following is the exact contract proposed for review. It is not current
runtime behavior and is not implementation authorization.

### 3.1 Boundary and mode

`stdout` and `stderr` are proposed to be **captured at every supervised child
boundary into bounded, non-persistent byte sinks**, rather than inherited by
the host or written to a log. The boundaries are:

1. the outer adapter worker, before self-containment, release handling,
   adapter construction, or imports that may write output; and
2. the inner generation child, before model loading, generation, decoding, or
   provider-adapter imports.

The capture is measure-and-discard: the implementation may buffer only the
bounded control state needed to account for bytes and report a typed result; it
must not retain the stream payload. A text-only `sys.stdout` replacement is
not sufficient by itself because native/binary writes must be covered at the
same child boundary.

The owner may reject this proposed capture mode and choose an explicit
reject-at-boundary mode, but that would require recording the alternative
contract, its exact seam, and its exact tests before implementation. This
draft does not silently substitute rejection or treat a zero value as that
choice.

### 3.2 Bounded byte accounting

- stdout and stderr have independent ceilings and independent counters.
- Accounting is on raw bytes at the OS stream boundary, before decoding,
  newline conversion, Unicode normalization, or logging.
- Each received chunk is counted in full. A chunk that crosses the ceiling is
  an overflow; the implementation must not accept a prefix as a successful
  stream.
- The counter is bounded: normal accounting retains `bytes_seen` only up to
  the configured ceiling, and an overflow fact reports a saturated
  `ceiling + 1` observation rather than retaining or exposing an unbounded
  count.
- A stream that closes normally after the child has exited and its writes have
  been drained produces a zero-byte or under-limit observation. Zero observed
  bytes is a test case, not a zero-ceiling semantic.
- Missing, implicit, or unapproved stream ceilings are a configuration failure
  before model/provider work; they are not treated as disabled streams.

### 3.3 UTF-8 and binary behavior

The capture contract is byte-oriented. Valid UTF-8, partial UTF-8, malformed
UTF-8, NUL bytes, and arbitrary binary bytes are all counted identically. The
capture path must not decode the stream to decide whether it fits. Therefore
there is no UTF-8 decode failure for stream accounting; malformed/binary data
is accepted only when its raw byte count is within the approved ceiling, then
discarded. No stream bytes are copied into a diagnostic exception, IPC error
message, log, or evidence artifact.

### 3.4 Overflow action and typed failure codes

The exact action for any accepted stream overflow is:

```text
TERMINATE_AND_MARK_FAILED
```

The first bounded control fact must use one of these proposed closed codes:

| Code | Meaning |
|---|---|
| `STDOUT_LIMIT_EXCEEDED` | stdout exceeded its approved ceiling |
| `STDERR_LIMIT_EXCEEDED` | stderr exceeded its approved ceiling |
| `BOTH_STREAM_LIMITS_EXCEEDED` | both stream ceilings were observed exceeded before terminal acceptance |
| `STDOUT_CAPTURE_READ_FAILED` | stdout could not be read/finalized truthfully |
| `STDERR_CAPTURE_READ_FAILED` | stderr could not be read/finalized truthfully |
| `STDOUT_LATE_OUTPUT` | stdout bytes arrived after the hard acceptance boundary or stream closure boundary |
| `STDERR_LATE_OUTPUT` | stderr bytes arrived after the hard acceptance boundary or stream closure boundary |
| `WORKER_DIED_BEFORE_STREAM_FINALIZATION` | a supervised worker died before its stream facts were final |
| `STREAM_FINALIZATION_FAILED` | bounded stream cleanup/finalization could not be verified |

Overflow, read failure, late output, worker death before stream finalization,
and stream-finalization failure are terminal failures. They do not trigger a
second adapter call or a third generation attempt. If both streams overflow
before the supervisor accepts a terminal fact, the carrier reports the single
aggregate code `BOTH_STREAM_LIMITS_EXCEEDED` plus one bounded observation per
stream.

### 3.4.1 Capture and finalization event order

The authoritative order for each supervised child stream is exactly:

```text
capture raw bytes
-> stop/close child stream
-> bounded drain
-> finalize stream observation
-> publish typed observation or failure
-> reject later bytes
```

The first step counts bytes at the OS stream boundary without decoding them.
Overflow, deadline, or child-terminal handling stops/closes the child stream
before the bounded drain. The observation is not publishable until the drain
and finalization checks complete. Bytes or facts arriving after finalization or
terminal publication are rejected as late and cannot revive success.

If bounded drain or stream-finalization verification fails, the result is
fail-closed: no success is published; the typed failure is
`STREAM_FINALIZATION_FAILED`; the existing bounded cleanup still runs; and a
cleanup failure may override the effective outcome with `CLEANUP_FAILED`.
Only sanitized typed metadata may reach IPC, logs, or evidence; no raw stream
content or failure detail is carried forward.

### 3.5 Read failure and normal close

A reader/handle/pipe exception, an unverified reader exit while its child is
still alive, or an inability to complete the bounded drain is a typed
`*_CAPTURE_READ_FAILED` or `STREAM_FINALIZATION_FAILED` result and fails the
run. EOF is normal only after the owning child has exited or has reached its
defined terminal point and the bounded reader has drained all available bytes.
No exception text, handle value, path, or payload is carried forward.

### 3.6 Worker death and late output

- If the outer worker or inner generation child dies before its stream facts
  and required protocol terminal state are final, the supervisor records
  `WORKER_DIED_BEFORE_STREAM_FINALIZATION`, marks the run failed, and performs
  the existing bounded termination/cleanup sequence.
- Bytes becoming readable after the supervisor's hard deadline, after stream
  finalization or terminal publication are late. They cannot revive a success
  or change a closed result to a success. The owning stream receives a
  `*_LATE_OUTPUT` fact and the effective outcome is failure.
- A late frame or late stream fact is never treated as a new attempt, never
  increments adapter cardinality, and never creates a second evidence pair.

### 3.7 Privacy and leakage boundary

The stream sink, control frames, logs, and evidence may carry only bounded
metadata: stream name, process role, attempt number when already accepted,
bounded byte count, approved ceiling, disposition, and the closed failure
code. The explicit prohibited leakage classes are:

- raw stream bytes;
- secrets, tokens, or credentials;
- URLs;
- absolute paths;
- prompt text;
- model or provider details;
- traceback text;
- raw exception text; and
- process handles or identifiers.

The sink must not persist a spool file or append to a shared log. These
prohibitions remain future implementation and test requirements.

### 3.8 Cleanup and cardinality

- The generation runner owns inner-child stream finalization; the adapter-call
  supervisor owns outer-worker acceptance, deadline handling, and the overall
  cleanup result. `Feat018EvidenceFinalizer` may receive only the sanitized
  typed facts after cleanup succeeds.
- An overflow/read/late/death fact requests exactly one bounded cleanup
  sequence for the affected containment. If cleanup cannot prove quiescence,
  `CLEANUP_FAILED` overrides the prior D9 failure for the effective outcome;
  the D9 fact remains a diagnostic sub-fact.
- Before bounded adapter dispatch, cardinality is `adapter_call_count=0` and
  `attempt_count=null`. Once the bounded adapter wrapper is entered, the host
  adapter cardinality is exactly one. An outer-worker stream failure before an
  accepted generation-start event therefore remains `1/null`; an inner-child
  stream failure after an accepted start is `1/1` or `1/2`, according to the
  already accepted attempt events.
- D9 never adds a retry. The unchanged adapter may retain its one explicitly
  permitted transient retry, but stream failure never authorizes that retry,
  an outer retry, a third attempt, or a second session.
- Each stream/process invocation produces exactly one terminal observation:
  `ZERO_OR_UNDER_LIMIT`, `LIMIT_EXCEEDED`, `READ_FAILED`, `LATE_OUTPUT`,
  `WORKER_DIED_BEFORE_STREAM_FINALIZATION`, or
  `STREAM_FINALIZATION_FAILED`. Duplicate observations are a protocol failure,
  not a second valid result.

## 4. Ownership and seam boundaries

| Responsibility | Proposed owner/seam | Current status |
|---|---|---|
| Child/worker capture | New bounded capture bootstrap/helper in `feat018_live_lightning_execution.py`, installed before outer-worker self-containment/imports and at the first instruction of the inner generation child | Proposed; absent from reviewed source |
| Bounded IPC handoff | Existing `MultiprocessingBoundedConnection` with a dedicated control frame carrying only the typed D9 code, stream/process role, bounded count, and disposition | Existing transport; D9 frame is absent and needs approval/implementation |
| Supervisor acceptance | `Feat018AdapterCallSupervisor` owns the deadline, acceptance order, late-fact rejection, effective outcome, and adapter/attempt cardinality | Existing supervisor; D9 acceptance is absent |
| Inner-child finalization | `Feat018BoundedKillableQwenGenerationRunner` joins the generation child and finalizes its two stream observations before returning a result | Existing cleanup seam; stream finalization is absent |
| Outer-worker finalization | Existing adapter-worker/supervisor cleanup coordinator; no success until the outer stream facts and protocol terminal are finalized | Existing cleanup seam; stream finalization is absent |
| Evidence/finalization handoff | Existing `SupervisorRunResult`/`finalize_smoke_run` path, extended only with allowlisted D9 facts after cleanup | Existing finalizer; D9 carrier is absent |
| Typed carrier | Proposed `D9StreamObservation` plus `D9StreamFailure`/closed failure code in the reviewed runtime source; generation-child-to-worker and worker-to-supervisor transfers use bounded control frames | Not present; exact field names require owner approval |
| D11 dependency | Concrete approved adapter-dispatch wrapper must bind the bounded supervisor result and D9 typed facts into the live `run_live_smoke` path. The current injected `adapter_call` is not a concrete wrapper and does not prove host preemption of an arbitrary blocking call | `UNRESOLVED`; D11 remains `BLOCKED` |

The ownership map deliberately does not invent a `LightningPreflight`,
`LightningSessionController`, `LightningSmokeFinalizer`, approved host caller,
or adapter-dispatch implementation. If live D9 handoff requires any file or
carrier outside the exact scope below, implementation must stop and obtain a
separate scope decision; no new wrapper is authorized by this package.

## 5. Proposed offline design boundary (not implementation approval)

The following two-file boundary is proposed for a future offline D9
implementation review. It is not an implementation approval scope while the
concrete D11/live carrier remains unknown:

| File class | Exact allowed path | Allowed purpose |
|---|---|---|
| Source | `backend/src/sketch2life/benchmark/feat018_live_lightning_execution.py` | Add the bounded child capture bootstrap/sinks, raw-byte accounting, typed D9 codes/carriers, bounded control frames, worker/supervisor acceptance, cleanup/finalization wiring, and safe result propagation |
| Tests | `backend/tests/unit/test_feat018_live_lightning_execution.py` | Add synthetic/injected tests for the D9 matrix, leakage, cleanup, OS-specific seams, and cardinality |
| Fixtures | `NONE` | No committed fixture is needed or allowed; use in-memory synthetic bytes and injected child/reader doubles |
| Versioned contracts/schemas | `NONE` | The proposed carrier remains local to the reviewed FEAT-018 runtime until a separately approved cross-feature contract is required |
| Configuration/dependency files | `NONE` | No `pyproject.toml`, environment file, lockfile, CLI, workflow, or provider configuration may change |

No other source, test, fixture, contract, configuration, plan, context,
decision, approval, validator, worktree, or evidence file is part of this
design record. In particular, `qwen_vision.py`, FEAT-003, D6
fixtures/validator, D10 hardware records, and any concrete D11 seam remain
read-only.

`D9_OFFLINE_FILE_SCOPE = PROPOSED_TWO_FILES_ONLY_PENDING_SEPARATE_APPROVAL`
`D9_LIVE_D11_CARRIER_SCOPE = UNKNOWN_UNRESOLVED_PENDING_D11`
`D9_PACKAGE_BLOCKED_IF_SCOPE_EXPANDS = TRUE`

The boundary is sufficient for design review only. It cannot be used to
resolve the live D11 carrier, authorize implementation, or open the Stage 4
boundary.

## 6. Focused test matrix required after separate approval

Tests must remain offline and use injected fakes or synthetic local process
boundaries. The expected matrix is:

| Case | Required assertion |
|---|---|
| Zero-byte stdout/stderr | Both streams finalize as zero observed bytes under positive test ceilings; no failure, no payload retention |
| Under-limit output | Raw byte count below each independent ceiling succeeds; no decode or newline transformation affects the count |
| Exact-limit output | Exactly the approved number of raw bytes succeeds; no off-by-one rejection |
| Over-limit output | The first byte beyond the approved ceiling produces the correct typed stdout/stderr/both code, terminates the containment, and cannot publish success |
| Malformed/binary output | Invalid UTF-8, NUL, partial multibyte sequences, and arbitrary binary are counted as bytes; no text decode path or raw leakage |
| Stream read failure | Injected reader/handle failure produces the correct typed read/finalization code and fail-closed outcome |
| Worker death | Outer/inner worker death before stream finalization produces typed worker-death failure and bounded cleanup |
| Late output | Bytes/facts after the supervisor deadline, terminal acceptance, or stream finalization are rejected as late and cannot revive success |
| Cleanup failure | A cleanup failure overrides any apparent D9 success/failure with `CLEANUP_FAILED`; no successful evidence pair is published |
| No raw stream leakage | Raw bytes, secrets/tokens/credentials, URLs, absolute paths, prompt text, model/provider details, traceback text, raw exception text, and process handles/identifiers never appear in IPC facts, exceptions, logs, result metadata, or evidence bytes |
| Truthful adapter/attempt cardinality | Pre-dispatch is `0/null`; post-wrapper failures are `1/null`; accepted attempts remain `1` or `2`; D9 never increments or retries |
| POSIX behavior | Pipe/process-group/reader cleanup and late/overflow behavior are covered by synthetic POSIX seams where the existing harness permits |
| Windows behavior | Handle inheritance/closure, reader finalization, job containment, and the same typed outcomes are covered through injected Windows seams where applicable |

The tests must also prove capture is installed before the first possible write
at both supervised process boundaries, and that a normal child exit is not
mistaken for a stream read failure.

## 7. Rollback and exclusions

If a separately approved implementation cannot satisfy the contract, rollback
is limited to the D9 changes in the two approved source/test files. No prior
FEAT-018 changes may be reset or overwritten. A failure to establish the exact
live carrier or D11 wrapper stops the work and returns to owner review; it does
not justify adding a new adapter, route, workflow, contract, or configuration
file.

Explicit exclusions:

- no Qwen, model, provider, GPU, Lightning, network, or credential changes;
- no FEAT-003 changes;
- no D6 fixture, validator, or media-contract changes;
- no D10 hardware or placement changes;
- no D11 concrete seam creation or resolution;
- no Stage 4 artifact, session, model load, or live execution;
- no runtime workload, pytest, Ruff, mypy, dependency installation, or
  subprocess workload as part of this package;
- no raw stdout/stderr content in logs, evidence, reports, or incidents;
- no edit to `TASK_APPROVAL.md`, the plan, `CONTEXT.md`, `DECISIONS.md`,
  source, or tests by this package.

## 8. Required owner decision and stop condition

Owner review must explicitly accept or reject:

1. capture-and-discard at both supervised child boundaries;
2. the independent raw-byte accounting and UTF-8/binary rule;
3. the typed code set, overflow action, read/death/late-output behavior, and
   cleanup/cardinality rule;
4. the exact stream ceiling values and their explicit handoff; and
5. the proposed two-file offline design boundary, including the rule that any
   D11/live carrier expansion requires a new scope approval.

Until all five are approved and the concrete D11 dependency is separately
bound, the authoritative state remains:

```text
D9_PACKAGE = DESIGN_RECORD_ONLY
D9_LIVE_D11_CARRIER_SCOPE = UNKNOWN_UNRESOLVED_PENDING_D11
D9 = BLOCKED_PENDING_D11_AND_CONTRACT_REVIEW
D9 stdout/stderr = SEPARATE_ENFORCEMENT_APPROVAL_REQUIRED
D11 = BLOCKED
D1 = BLOCKED_BY_D11
STAGE_4 = NOT READY
LIVE/MODEL/GPU/PROVIDER/NETWORK/LIGHTNING = NOT AUTHORIZED
```

## 9. Validation and repository observations

Validation is limited to the read-only/static checks required by the task. The
results are recorded in the companion ignored report after execution. No
pytest, Ruff, mypy, dependency installation, subprocess workload, model load,
GPU, provider, network, Lightning, or live execution is permitted.

The source register is `docs/context/SOURCE_REGISTER.md`; the project context,
FEAT-018 plan, `CONTEXT.md`, `DECISIONS.md`, `TASK_APPROVAL.md`, D1 package,
candidate-ratification report, reviewed runtime, and reviewed tests were read
before this draft. Existing user-owned changes, untracked files, worktrees,
and stashes were preserved.

Prior preparation report (historical, pre-correction; not the current package
verdict):
`tmp/feat018-p2t2-d9-enforcement-package-20260921/REPORT.md`

Current correction report:
`tmp/feat018-p2t2-d9-enforcement-package-correction-20260921/REPORT.md`
