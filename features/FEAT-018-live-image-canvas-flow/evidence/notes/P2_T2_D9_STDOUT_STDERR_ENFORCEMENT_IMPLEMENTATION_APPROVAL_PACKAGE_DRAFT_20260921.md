# FEAT-018 P2-T2 D9 stdout/stderr enforcement implementation-approval package

Preparation date: 2026-09-21
Package status: `DRAFT_FOR_OWNER_REVIEW`
Boundary: `IMPLEMENTATION_APPROVAL_PREPARATION_ONLY`

This package is a separate implementation-approval draft prepared after the
owner confirmed the D9 design package only. That confirmation does not bind
`stdout_max_bytes` or `stderr_max_bytes`, authorize implementation, resolve
D9 or D11, or open Stage 4. No source or test implementation is included in
this record.

## Required state

```text
D9_IMPLEMENTATION_APPROVAL_PACKAGE = READY_FOR_OWNER_REVIEW
D9 = BLOCKED_PENDING_EXACT_CEILINGS_AND_D11
D11 = BLOCKED
D1 = BLOCKED_BY_D11
STAGE_4 = NOT_READY
LIVE/MODEL/GPU/PROVIDER/NETWORK/LIGHTNING = NOT_AUTHORIZED
```

`READY_FOR_OWNER_REVIEW` means that the proposed offline implementation scope
and contract are written for an owner decision. It is not an implementation
approval. The implementation gate remains closed until the exact stream
ceilings and the concrete D11/live carrier are separately bound and approved.

## 1. Design and reviewed-source provenance

This draft carries forward the corrected D9 design record and its independent
review without promoting their design-only status:

| Record | Repository-relative path | Identity |
|---|---|---|
| D9 design package | `features/FEAT-018-live-image-canvas-flow/evidence/notes/P2_T2_D9_STDOUT_STDERR_ENFORCEMENT_APPROVAL_PACKAGE_DRAFT_20260921.md` | SHA-256 `61D9B45D384105E8595C185411CA3DFFE5F0526F7B859077A29B0E5260495A76` |
| D9 correction report | `tmp/feat018-p2t2-d9-enforcement-package-correction-20260921/REPORT.md` | SHA-256 `626BA28B03E6C15B2C81649CCF3980FC02D5C8047701DF16B0EE9BE271B88F0C` |
| D9 independent review rerun | `tmp/feat018-p2t2-d9-enforcement-package-independent-review-rerun-20260921/REVIEW.md` | SHA-256 `7B498E908329CD76587E476EEB3F9959A0F296F17ED4E5A573AC2720F8A96D54` |
| Reviewed runtime | `backend/src/sketch2life/benchmark/feat018_live_lightning_execution.py` | owner-bound commit `9549a341194f40b1a9be419d6fce0d70f1ca0384`; blob `94db10bedf95ab105f6c8653adac991bce94fa35` |
| Reviewed unit test | `backend/tests/unit/test_feat018_live_lightning_execution.py` | owner-bound commit `9549a341194f40b1a9be419d6fce0d70f1ca0384`; blob `d7846f22fddf55ae234387e9e43d504a848112ee` |

The reviewed runtime declares `stdout_max_bytes` and `stderr_max_bytes` at
source lines 129-130 and validates them only as non-negative at lines 145-148.
The owner-bound unit test has no references to either field or stream-specific
capture/enforcement tests. The reviewed source has no stdout/stderr capture,
worker hand-off, byte enforcement, overflow carrier, stream finalizer, or
concrete D11/live caller. Existing raw-output and IPC bounds remain separate
mechanisms and do not prove stdout/stderr enforcement.

## 2. Exact proposed writable scope

If and only if this package receives a separate implementation approval, the
future offline D9 implementation may write exactly these two files:

| File | Allowed purpose |
|---|---|
| `backend/src/sketch2life/benchmark/feat018_live_lightning_execution.py` | Add the bounded outer-worker and inner-generation-child capture boundary, raw-byte accounting, typed D9 observations/failures, metadata-only control-frame handoff, supervisor acceptance/finalization, cleanup wiring, cardinality preservation, and sanitized result propagation. |
| `backend/tests/unit/test_feat018_live_lightning_execution.py` | Add injected/fake offline tests for the D9 byte, lifecycle, privacy, cleanup, cardinality, and POSIX/Windows seam matrix. |

This two-file list is a proposed implementation scope only. The package file,
the companion ignored report, and existing governance records are preparation
artifacts, not future runtime scope. No implementation may begin from this
draft alone.

## 3. Exact exclusions

The future implementation must not create or modify any other file, scope, or
system. Explicit exclusions are:

- no committed fixtures;
- no versioned contracts or schemas;
- no `pyproject.toml`, lockfile, workflow, environment, provider, or dependency
  changes;
- no `qwen_vision.py`;
- no FEAT-003 changes;
- no D6 validator or fixture changes;
- no D10 hardware or placement changes;
- no D11 concrete seam creation;
- no plan, `CONTEXT.md`, `DECISIONS.md`, approval, or validator changes;
- no routes, registries, ports, mobile code, provider configuration, or
  evidence-destination changes;
- no worktree, stash, branch, commit, or remote changes.

No D11/live carrier, host caller, preflight, session controller, smoke
finalizer, adapter-dispatch wrapper, or environment closure may be invented
inside this two-file boundary. If the D11 carrier requires another file or
cross-feature contract, implementation must stop for a new explicit scope
approval.

## 4. Proposed implementation responsibilities

These are owner-review requirements, not current runtime behavior.

### 4.1 Capture boundary and discard mode

- Capture `stdout` and `stderr` independently at both supervised child
  boundaries: the outer adapter worker and the inner generation child.
- Install each capture boundary before self-containment, release handling,
  adapter construction, model/provider imports, generation, decoding, or any
  first possible write at that boundary.
- Use bounded, non-persistent capture-and-discard sinks. A text-only
  `sys.stdout` replacement is insufficient; native and binary writes must be
  covered by the same child boundary.
- Retain only bounded control state needed to report the observation. Never
  retain, spool, log, or publish stream payload bytes.

### 4.2 Raw-byte accounting and independent ceilings

- Account at the OS stream boundary before UTF-8 decoding, newline conversion,
  Unicode normalization, or logging.
- Maintain independent stdout and stderr ceilings and counters.
- Count every received chunk in full. A chunk crossing a ceiling is an
  overflow; accepting a successful prefix is prohibited.
- Keep counters bounded: retain `bytes_seen` only through the approved
  ceiling, and report an overflow as a saturated `ceiling + 1` observation.
- Treat valid UTF-8, partial UTF-8, malformed UTF-8, NUL bytes, and arbitrary
  binary bytes as raw bytes. Do not decode to decide whether a stream fits.
- Missing, implicit, or unapproved stream ceilings are a configuration
  failure before model/provider work. They are not a disabled-stream signal.

### 4.3 Typed observations and metadata-only handoff

- Define typed D9 stream observations and failures in the reviewed runtime
  file only after owner approval of their exact fields.
- Transfer only bounded metadata through the existing bounded IPC seam:
  stream name, process role, already-accepted attempt number, bounded byte
  count, approved ceiling, disposition, terminal observation category, and
  typed failure code.
- Do not transfer raw stream bytes, payload-derived exception text, paths,
  handles, process identifiers, prompts, model/provider details, or secrets.
- Preserve the existing adapter/attempt cardinality and finalizer contract;
  D9 facts may reach evidence only as sanitized typed metadata after cleanup.

### 4.4 Finalization, cleanup, and retry behavior

- Apply the deterministic event order in Section 6 for every supervised
  child stream.
- Make overflow, read failure, worker death before finalization, late output,
  and finalization failure terminal and fail closed.
- Run the existing bounded cleanup sequence exactly once for the affected
  containment. If cleanup cannot prove quiescence, `CLEANUP_FAILED` overrides
  the effective result while preserving the D9 fact only as sanitized
  diagnostic metadata.
- Preserve truthful cardinality: before dispatch `adapter_call_count=0` and
  `attempt_count=null`; after entering the bounded adapter wrapper the host
  adapter count is exactly one; accepted attempts remain one or two according
  to accepted attempt events.
- D9 never adds a retry, outer retry, third attempt, second adapter call, or
  second session. The unchanged adapter may retain its one already-approved
  transient retry, but stream failure never authorizes it.

## 5. Exact unresolved owner decisions

The following values and identities must remain unresolved in this draft:

```text
stdout_max_bytes = UNRESOLVED_PENDING_OWNER_BINDING
stderr_max_bytes = UNRESOLVED_PENDING_OWNER_BINDING
raw_output_max_bytes = 65536  # OWNER_SELECTED_CANDIDATE_ONLY; not exact
ipc_envelope_max_bytes = 98304  # OWNER_SELECTED_CANDIDATE_ONLY; not exact
concrete D11/live carrier = UNRESOLVED_PENDING_D11
approved host caller = UNRESOLVED_PENDING_D11
```

The existing constructor values `stdout_max_bytes=0` and
`stderr_max_bytes=0` are not a stream-disable decision and must not be
promoted into one. No default, constructor value, observed byte count,
historical proposal, design candidate, or package wording may be promoted
automatically to an exact owner binding.

The owner must separately decide and record:

1. the exact positive stream ceiling for stdout;
2. the exact positive stream ceiling for stderr;
3. the final handoff of those values into the approved enforcement seam;
4. the concrete D11/live carrier, host caller, cleanup/evidence handoff, and
   environment closure; and
5. whether the two-file offline scope remains sufficient after D11 is bound.

Until those decisions are separately recorded and reviewed, the effective
state is `D9 = BLOCKED_PENDING_EXACT_CEILINGS_AND_D11`.

## 6. Required event order and fail-closed behavior

The authoritative order for each supervised child stream is exactly:

```text
capture raw bytes
-> stop/close stream
-> bounded drain
-> finalize observation
-> publish typed observation/failure
-> reject later bytes
```

Overflow, deadline, or child-terminal handling stops/closes the stream before
the bounded drain. No observation is publishable until drain and finalization
checks complete. Bytes or facts arriving after finalization or terminal
publication are rejected as late and cannot revive success.

If bounded drain or finalization verification fails, no success is published;
the typed failure is `STREAM_FINALIZATION_FAILED`; cleanup still runs; and a
cleanup failure may override the effective outcome with `CLEANUP_FAILED`.
Read/handle/pipe failure, worker death before stream finalization, and late
output are likewise terminal failures. Normal EOF is accepted only after the
owning child reaches its defined terminal point and the bounded reader drains
available bytes.

## 7. Required typed failure vocabulary

The first bounded control fact must use the following proposed typed failure
vocabulary:

```text
STDOUT_LIMIT_EXCEEDED
STDERR_LIMIT_EXCEEDED
BOTH_STREAM_LIMITS_EXCEEDED
STDOUT_CAPTURE_READ_FAILED
STDERR_CAPTURE_READ_FAILED
STDOUT_LATE_OUTPUT
STDERR_LATE_OUTPUT
WORKER_DIED_BEFORE_STREAM_FINALIZATION
STREAM_FINALIZATION_FAILED
```

`CLEANUP_FAILED` is not a stream payload or a replacement for the D9 fact; it
may override the effective outcome when cleanup cannot prove quiescence. If
both streams overflow before terminal acceptance, the bounded carrier uses
`BOTH_STREAM_LIMITS_EXCEEDED` with one bounded observation per stream. No
failure code carries raw exception text, stream bytes, paths, handles, or
process identifiers.

For terminal-observation closure, each stream/process invocation produces one
and only one category:

```text
ZERO_OR_UNDER_LIMIT
LIMIT_EXCEEDED
READ_FAILED
LATE_OUTPUT
WORKER_DIED_BEFORE_STREAM_FINALIZATION
STREAM_FINALIZATION_FAILED
```

The stream-specific codes above provide the bounded detail for failure
categories; duplicate observations are a protocol failure, not a second valid
result.

## 8. Required offline test matrix

The implementation approval must require offline tests using injected fakes,
synthetic bytes, and synthetic local process/reader boundaries. No committed
fixture is needed or allowed. The matrix must cover:

| Case | Required assertion |
|---|---|
| Zero-byte stdout/stderr | Both streams finalize at zero observed bytes under positive approved test ceilings; no failure and no payload retention. |
| Under-limit output | Independent raw-byte counts below each ceiling succeed without decode or newline transformation. |
| Exact-limit output | Exactly the approved byte count succeeds with no off-by-one rejection. |
| Overflow | The first byte beyond the relevant ceiling produces the correct stdout, stderr, or aggregate typed failure, terminates containment, and cannot publish success. |
| Binary/malformed UTF-8 | Invalid UTF-8, partial multibyte sequences, NUL bytes, and arbitrary binary are counted as bytes without a text decode path. |
| Read failure | Injected reader/handle failure produces the correct typed read/finalization failure and fails closed. |
| Worker death | Outer/inner death before stream finalization produces `WORKER_DIED_BEFORE_STREAM_FINALIZATION` and bounded cleanup. |
| Late output | Bytes/facts after deadline, terminal acceptance, or finalization are rejected as late and cannot revive success. |
| Finalization failure | Drain/finalization failure publishes no success, emits `STREAM_FINALIZATION_FAILED`, and still invokes cleanup. |
| Cleanup failure | Cleanup failure overrides the effective result with `CLEANUP_FAILED`; no successful evidence pair is published. |
| No raw leakage | None of the prohibited classes in Section 9 appears in IPC facts, exceptions, logs, result metadata, evidence, or spool files. |
| Cardinality | Pre-dispatch is `0/null`; post-wrapper failure is `1/null`; accepted attempts remain `1` or `2`; D9 never increments or retries. |
| POSIX seams | Synthetic process-group, pipe, reader, close, drain, and late/overflow cleanup behavior is covered where the existing harness permits. |
| Windows seams | Synthetic handle inheritance/closure, reader finalization, job containment, and equivalent typed outcomes are covered where applicable. |
| Capture-before-first-write | Capture is installed before the first possible write at both supervised boundaries. |
| Normal child exit | A normal child exit and fully drained EOF are not misclassified as a read/finalization failure. |

## 9. Privacy restrictions

The implementation, IPC carrier, logs, results, incidents, and evidence must
never contain or expose:

- raw stream bytes;
- secrets, tokens, or credentials;
- URLs;
- absolute paths;
- prompt text;
- model or provider details;
- traceback text;
- raw exception text; or
- process handles or identifiers.

Only bounded allowlisted metadata may cross the D9 carrier: stream name,
process role, already-accepted attempt number, bounded byte count, approved
ceiling, disposition, terminal observation category, and typed failure code.
No stream sink may persist a spool file or append to a shared log.

## 10. Approval boundary and stop condition

This package is an implementation-approval draft only. It does not:

- authorize implementation or modify source/tests;
- resolve D9 or D11;
- bind stdout/stderr ceilings or promote raw/IPC candidates to exact values;
- create a concrete D11 seam, host caller, carrier, or environment closure;
- authorize Stage 4, Lightning, model, GPU, provider, network, or live work;
- authorize a commit, push, or approval-record update.

Owner approval must explicitly accept or reject the proposed capture-and-
discard mode, raw-byte/binary rule, typed vocabulary and event order, cleanup
and cardinality behavior, exact ceiling handoff, and the proposed two-file
scope. A D11 scope expansion requires a new explicit approval. If any exact
scope or contract point is rejected or remains materially ambiguous, the
implementation gate remains blocked and no source/test change may begin.

The authoritative stop state remains:

```text
D9_IMPLEMENTATION_APPROVAL_PACKAGE = READY_FOR_OWNER_REVIEW
D9 = BLOCKED_PENDING_EXACT_CEILINGS_AND_D11
D11 = BLOCKED
D1 = BLOCKED_BY_D11
STAGE_4 = NOT_READY
LIVE/MODEL/GPU/PROVIDER/NETWORK/LIGHTNING = NOT_AUTHORIZED
```

No model, GPU, provider, network, Lightning, Stage 4, runtime, subprocess
workload, or live execution was performed to prepare this draft.
