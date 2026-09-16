# FEAT-018 P2-T2 bounded runner implementation-approval package

STATUS: DRAFT  
NOT AN IMPLEMENTATION APPROVAL  
NOT A LIVE EXECUTION AUTHORIZATION

Date: 2026-09-14 (revision 5, self-initiated hardening pass ahead of independent audit)  
Evidence ID: `EV-018-P2-T2-BOUNDED-RUNNER-APPROVAL-PACKAGE-DRAFT-01`  
Related scope: FEAT-018 P2-T2 live Lightning boundary, first-stage implementation review

Revision 2 added four corrections after verdict `NEEDS_REVISION / HOLD` on revision 1: (1) a
source-grounded adapter/retry compatibility contract table; (2) a total-adapter-cap
coordinator/watchdog specification with bounded cleanup and offline hang cases; (3) byte-boundary
limits stated in encoded bytes with receive-side frame validation; and (4) evidence
write/rollback/precedence rules with redaction-sentinel coverage.

Revision 3 closed three findings from the `HOLD` verdict on revision 2 by withdrawing the claim
that the generation-runner instance alone could supervise the whole
`QwenVisionAdapter.understand()` call (adding a separate `Feat018AdapterCallSupervisor`),
requiring real-adapter/fake-runner compatibility tests instead of fake-adapter cardinality tests,
and withdrawing the "two sequential renames are atomic" claim in favor of a three-state evidence
model with one designated commit-record file.

Revision 4 closes four finding groups from the independent review recorded at
`tmp/feat018-p2-t2-revision3-independent-review-20260914/REVIEW.md` (verdict
`PASS_WITH_FINDINGS`, findings G1-1, G2-1/G2-2/G2-3, G3-1/G3-2, G4-1/G5-1): (1) defines exactly
how the supervisor's absolute total-cap deadline crosses the process boundary into the adapter
worker, with clock-origin semantics that do not depend on cross-process monotonic-clock
comparability; (2) replaces PID-message-based generation-child cleanup with race-free OS-level
process-group/job containment, so the supervisor can always reach and terminate the generation
child even if the adapter worker is killed before reporting anything; (3) defines an explicit,
framed supervisor progress state machine (`ADAPTER_STARTED`, `GENERATION_ATTEMPT_STARTED(1|2)`,
terminal outcome) with an atomic post-deadline freeze, so `attempt_count` can never be changed by
a late, duplicate, partial, malformed, out-of-order event, or by an inferred exit code/PID; and
(4) requires the Markdown evidence file to carry `run_id` and `evidence_id` in a fixed
machine-readable field matching the JSON, adds an explicit `commit_state` field to the JSON commit
record, and closes the one previously-untested crash-injection transition (a crash between the
Markdown temp write and the JSON temp write).

Revision 5 is a self-initiated hardening pass, ahead of the next independent audit, closing four
remaining risks in the revision-4 design: (1) it corrects a framing error in the revision-4
deadline-propagation text that could be read as implying the *worker's own* derived deadline
provides safety; this revision states plainly that the supervisor's own externally-enforced
absolute deadline is the sole hard authority regardless of whether the worker ever reads its first
message, uses a skewed clock, or ignores its advisory budget entirely; (2) it replaces the
revision-4 containment description with an explicit, symmetric `CONTAINMENT_READY` gate protocol
for both POSIX and Windows, under which the worker is structurally unable to construct the adapter
or spawn a generation child before the supervisor has established and verified containment, and
adds an explicit fail-closed rule when the containment primitive itself is unavailable; (3) it adds
a formal `FROZEN` state (distinct from a worker-reported `TERMINAL`) to the progress state
machine, defines "event acceptance time" precisely as the supervisor's own monotonic time when a
complete bounded frame has been received and validated (not when it started arriving), and adds a
strict tie-breaking rule at the exact deadline instant; and (4) it adds one consolidated
crash-transition audit table giving the expected reader verdict for every on-disk state the
evidence commit protocol can produce, so no crash outcome is left to prose-only description. No
proposed file scope, marker, or open decision changed. Neither proposed implementation/test file
exists; this revision remains documentation only.

## Purpose and authority

This document packages the proposed first-stage implementation boundary for owner review. It
does not approve implementation, open Lightning, load a model, use a GPU, call a provider, or
authorize a live smoke run. The existing approval in
`features/FEAT-018-live-image-canvas-flow/approvals/TASK_APPROVAL.md` approves the completed
offline P2-T2 contract/mapping slice only. It does not approve this package, the proposed
bounded runner, or live execution.

The authoritative planning input is
`features/FEAT-018-live-image-canvas-flow/plan/P2_T2_LIVE_LIGHTNING_EXECUTION_PLAN_DRAFT_20260913.md`,
which remains `DRAFT`, `NOT AN APPROVAL`, and `NOT AN IMPLEMENTATION AUTHORIZATION`. The local
plan reviews and correction reports were reconciled for this package. Reference material in
`docs/context/SOURCE_REGISTER.md` informs architecture but grants no implementation authority.

The package itself proposes documentation and an approval boundary only. It must remain
unapproved until the project owner records an explicit decision in the canonical approval
record. No approval record is changed by this document.

## Proposed exact implementation scope

The owner-review request is to approve exactly these two additive files, and no other
implementation, fixture, contract, adapter, route, wrapper, CLI, or test file:

1. `backend/src/sketch2life/benchmark/feat018_live_lightning_execution.py`
2. `backend/tests/unit/test_feat018_live_lightning_execution.py`

These paths are proposed only. They must not be created or populated under this draft. An
approval of this scope would authorize offline implementation and offline tests with injected
fakes only. It would not authorize a model, provider, network, GPU, Lightning session, model
weights, or a live adapter call.

The existing FEAT-003 V2 schemas, profile catalog, Qwen adapter, runtime/readiness sources,
FEAT-018 mapper, contracts, fixtures, evidence index, and approval history remain read-only.
The exact two-file scope is the complete proposed implementation surface for this package.

## Why neither existing runner qualifies

The current source was checked at the existing committed boundary in
`backend/src/sketch2life/infrastructure/ai/qwen_vision.py`:

- `KillableSubprocessQwenGenerationRunner` starts a child and waits at the profile's
  120-second deadline, so the child-owned model state has a killable deadline. However, its
  worker sends `(kind, value)` through `Connection.send`, with a successful raw output string
  as `value`. There is no raw-output byte ceiling proven before that send and no bounded IPC
  envelope proven before transport. The deadline therefore does not satisfy the combined
  live boundary: bounded raw output before IPC, bounded IPC, and bounded non-persistent
  stdout/stderr.
- `TransformersQwenGenerationRunner` loads and runs in the current process. It has no hard,
  killable deadline around model/processor loading, generation, and decoding. Exception
  translation is not a killable watchdog and cannot provide the required per-attempt deadline.

Neither existing class is selectable for the future live approval as-is. The adapter's
constructor default is not evidence of an approved live boundary. The future implementation
must be explicitly injected through the existing `generation_runner` seam, and the existing
FEAT-003 adapter source must remain unchanged.

## Adapter and retry compatibility contract

This table is source-grounded against the committed `backend/src/sketch2life/infrastructure/ai/qwen_vision.py`
observed at this revision. No row is inferred from a fake adapter; where the committed source does
not already provide a behavior, the row states that explicitly as a required wrapper
responsibility instead of claiming existing proof.

| Contract element | Exact source identity | Statement |
|---|---|---|
| Existing input/output/error seam | `QwenGenerationRunner.generate(profile: VisionProfileV2, runtime_config: QwenVisionRuntimeConfig, image_path: Path, prompt: str) -> str` (`Protocol`, lines 372-381) | This is the only seam the proposed wrapper may implement. Input is one profile/runtime-config/image-path/prompt tuple per call; output is the raw provider string on success; failure is communicated only by raising one of the exception types below, never by a sentinel return value. |
| Retry ownership | `QwenVisionAdapter.understand()` (lines 709-882), specifically the `while True:` loop at lines 764-882 | The existing, unmodified FEAT-003 adapter owns the entire retry decision and the retry loop. The proposed wrapper's `generate()` implements exactly one attempt per call and must never loop, sleep-and-retry, or call itself recursively; if the adapter calls `generate()` a second time, that is the adapter's decision, not the wrapper's. |
| Sole failure classification allowed to trigger attempt 2 | `QwenTransientRuntimeError` raised on attempt 1 (lines 820-823), or a generic `Exception` for which the adapter's injected `classify_transient` callable returns `True` on attempt 1 (lines 854-859) | The adapter's default `classify_transient=_never_transient` always returns `False` (lines 384-387), so unless the harness explicitly injects a different classifier, `QwenTransientRuntimeError` is the only supported path to attempt 2. The proposed wrapper must raise exactly `QwenTransientRuntimeError` for its own transient case and must not rely on, or silently depend on, an injected non-default `classify_transient` to produce a retry. |
| Terminal on `QwenModelLoadError` | Lines 770-780 | Terminal unconditionally at attempt 1 (`VISION_MODEL_UNAVAILABLE`/`MODEL_LOAD_FAILED`); never advances the loop. Confirmed by source; no wrapper action required beyond raising this type for a real model-load failure. |
| Terminal on `QwenDeviceUnavailableError` | Lines 790-800 | Terminal unconditionally at attempt 1 (`VISION_MODEL_UNAVAILABLE`/`DEVICE_UNAVAILABLE`); never advances the loop. Confirmed by source. |
| Terminal on timeout | `except (QwenTimeoutError, TimeoutError):` at lines 810-819 | Terminal unconditionally regardless of `attempt_number`; the adapter has no timeout-retry path at all. Confirmed by source. |
| Terminal on total-cap expiry | Not present in committed source — the adapter has no concept of `total_adapter_cap_seconds` | **Required wrapper responsibility, not existing behavior.** The wrapper alone must track the total cap across both possible calls to its `generate()` method and, on expiry, raise a terminal exception (never `QwenTransientRuntimeError`) so the unmodified adapter's existing terminal-handling paths apply. See "Outer adapter-call supervisor and total adapter cap" below. |
| Terminal on raw-output/IPC/stdout/stderr overflow | Not present in committed source — `_send_worker_message`/`Connection.send` (lines 558-560) uses unbounded `pickle` transport with no byte ceiling | **Required wrapper responsibility, not existing behavior.** The wrapper must detect overflow itself and raise a terminal exception (e.g. `QwenPermanentRuntimeError`), never `QwenTransientRuntimeError`. See "Byte-boundary and receive-side limits" below. |
| Terminal on `QwenPermanentRuntimeError` | Lines 833-842 | Terminal unconditionally. Confirmed by source. |
| Wrapper uses the existing adapter without modifying FEAT-003 source | `QwenVisionAdapter.__init__(..., generation_runner: QwenGenerationRunner \| None = None, ...)` (lines 674-703) | The proposed `Feat018BoundedKillableQwenGenerationRunner` implements only the `QwenGenerationRunner` protocol and is passed as `generation_runner=` to the unmodified `QwenVisionAdapter`. `qwen_vision.py` is imported only for the frozen `QwenGenerationRunner` protocol and the exception types this table names; it is never edited. |
| Existing subprocess runner disqualification | `KillableSubprocessQwenGenerationRunner` (lines 605-654); `_qwen_worker_entry`/`_send_worker_message` (lines 558-591) | Confirmed by source: the 120-second child deadline exists, but the worker's `Connection.send((kind, value))` has no raw-output byte ceiling and no bounded IPC envelope proof before transport. This class is not reused; the wrapper must implement its own bounded framing over its own child/pipe pair rather than delegating to this class. |
| Existing in-process runner disqualification | `TransformersQwenGenerationRunner` (lines 533-555) | Confirmed by source: no killable deadline around model/processor loading, generation, or decoding. Not reused for the live boundary. |
| Cross-call state requirement | Not present in committed source | **Required wrapper responsibility.** Because retry is invoked transparently by the adapter's own loop, one `Feat018BoundedKillableQwenGenerationRunner` instance must be constructed fresh per `understand()` invocation and must persist its own start time and remaining-cap state across a possible second `generate()` call within that one adapter invocation; it must never be reused across two separate adapter calls. |

## Responsibilities of the proposed source file

`backend/src/sketch2life/benchmark/feat018_live_lightning_execution.py` would own the
feature-local smoke coordinator, a proposed `Feat018BoundedKillableQwenGenerationRunner`
implementing the `QwenGenerationRunner` seam for one generation attempt, and a proposed
`Feat018AdapterCallSupervisor` that independently supervises the complete
`QwenVisionAdapter.understand()` invocation (see "Outer adapter-call supervisor and total adapter
cap" below). All three responsibilities remain inside the one proposed source file; no additional
file is introduced. The implementation approval must make these responsibilities testable and
fail closed:

### Construction and pre-adapter controls

- Construct `QwenVisionRuntimeConfig` from one explicitly selected session-relative env file
  using the equivalent of `from_env_file(..., environ={})`; do not merge ambient environment
  values. Never copy runtime-config contents into evidence.
- Construct and inject the exact existing synthetic policy boundary:
  `sketch2life.infrastructure.ai.vision_lexical_policy.LexicalRegressionContentPolicy` with
  `sketch2life.infrastructure.ai.vision_lexical_policy.synthetic_prohibited_lexicon()`.
  Record only the safe versions
  `vision-prohibited-lexicon-fixture-v1` and `vision-policy-match-view-v2`. This is a
  functional synthetic regression check, not semantic-safety or production moderation
  evidence.
- Inject an owner-approved prompt explicitly. Immediately before the adapter call, hash the
  exact in-memory text as `sha256(prompt_text.encode("utf-8")).hexdigest()` and compare it with
  the approved prompt hash. A mismatch is a pre-adapter terminal. Never log, persist, or place
  prompt text in evidence; the adapter's empty default must be unreachable.
- Validate the one approved non-sensitive JPG/PNG through the existing P2-T1 admission
  boundary before a vision call, preserve the immutable original, stage only a derived
  session-relative reference, and verify the staged SHA-256 against the approved source hash.
- Verify the approved hardware facts and require either single-device visibility or a
  post-load assertion that the model and inference inputs occupy the approved device index.
  Inventory alone is insufficient. A wrong or unverifiable GPU/SKU, device count/index,
  VRAM, CUDA, BF16, driver, or placement fact is terminal.

### Normative Lightning provisioning and readiness contract

The complete coordinator is host-side and uses mandatory injected preflight and
finalization seams plus one injected `LightningSessionController` for the
provider-owned session lifecycle. There is no default adapter callable: a run
without an explicit bounded adapter seam is rejected before provisioning. The
finalizer must return typed evidence-pair and incident-handling proof before a
successful result is exposed.

The controller is an independently cancellable seam. `provision()`,
`wait_ready()`, and `terminate()` return operation handles promptly; each handle
has separately bounded `wait(timeout_seconds=...)` and `cancel(timeout_seconds=...)`
methods. The host coordinator owns sequencing and its own monotonic watchdog
checks; it never accepts an unbounded provider operation or a bare boolean as
termination proof.

The coordinator configuration contains the explicit positive finite integer
`session_provision_timeout_seconds`. It also contains positive
`session_ttl_seconds`, `gpu_minute_cap`, and the separate explicit positive
`session_termination_deadline_seconds`; the existing
`Feat018BoundedRunnerConfig` remains unchanged and continues to own the frozen
bounded adapter-runner protocol.

The controller contract returns provider-owned typed facts, not coordinator
placeholders:

```text
provision() -> LightningOperationHandle[LightningProvisionFacts]
wait_ready() -> LightningOperationHandle[LightningReadyFacts]
terminate() -> LightningOperationHandle[LightningTerminationFacts]

LightningOperationHandle[T]:
  wait(*, timeout_seconds: float) -> T
  cancel(*, timeout_seconds: float) -> LightningCancellationFacts

LightningProvisionFacts:
  allocation_confirmed: bool
  session_identity: bounded opaque provider identity
  placement: LightningPlacementFacts
  gpu_minute_budget_start_monotonic: finite non-negative host-monotonic timestamp

LightningPlacementFacts:
  gpu_sku, device_index, device_count, vram_mib
  cuda_available, bf16_supported, single_device_visible
  model_device_index, input_device_index

LightningReadyFacts:
  readiness: NOT_READY | SESSION_READY
  lifecycle: LightningSessionLifecycleFacts | null

LightningSessionLifecycleFacts:
  session_identity: bounded opaque provider identity
  session_ready_at_monotonic: finite non-negative timestamp
  session_ttl_start_monotonic: same timestamp as session_ready_at_monotonic
  session_ttl_deadline_monotonic: finite timestamp after TTL start

LightningTerminationFacts:
  termination_verified: bool
  cleanup_status: SUCCEEDED | CLEANUP_FAILED
  session_identity: bounded opaque provider identity
  session_cleanup_verified: bool
```

`provision_start` is the host monotonic reading captured immediately before
the non-blocking `LightningSessionController.provision()` operation and
`ready_deadline = provision_start + session_provision_timeout_seconds`.
The wait budget is passed to the returned operation handle, and a timeout
attempts typed cancellation before forced session termination.
`SESSION_READY` must be returned and observed strictly before `ready_deadline`;
an exact-deadline or late readiness is a timeout. The session TTL starts only
at provider-confirmed readiness represented by its lifecycle facts. The
controller-owned TTL start/deadline must agree with the configured TTL; the
coordinator never derives it from a host placeholder. A controller
allocation/billing fact supplies the GPU-minute budget start, and the typed
placement facts must match the explicit approval. Missing, malformed,
contradictory, identity-mismatched, or unverified controller facts fail closed.

Before provisioning, the typed preflight facts must match the synthetic session
ID and verify approval identity, checkout identity, D4 readiness, fixture
digest, prompt hash, hardware placement, policy identity, and runtime
inventory. After cleanup, the typed finalizer must verify evidence-pair
finalization and sanitized incident handling. Either gate failing produces a
non-success result; neither gate is inferred from an adapter or controller
return value.

After readiness, the coordinator performs one final host-clock TTL/GPU-cap check
immediately before capturing `adapter_start` and making the single injected
`run_bounded_adapter_call()`-shaped invocation. That call receives the unchanged
`Feat018BoundedRunnerConfig` and synthetic session ID exactly once; its own
total adapter cap starts at that invocation boundary and is not reset by any
retry owned by the unchanged adapter/runner protocol.

Every path after provisioning begins attempts controller termination exactly
once. The separate `session_termination_deadline_seconds` starts when final
cleanup begins and includes the controller/session termination operation and
its verification. A termination timeout, exception, false typed verification,
identity mismatch, or missing termination proof produces `CLEANUP_FAILED`,
overriding any prior adapter success. If provisioning raises, times out,
cancellation fails, or
`SESSION_READY` is not accepted before its deadline, the final outcome is
`FAILED` unless termination cannot be verified, in which case it is
`CLEANUP_FAILED`; `adapter_call_count=0`, `attempt_count=null`, no mapper or
model invocation occurs, and no success-valued session fact is emitted.

### Bounded execution and cardinality

- Put model/processor loading, generation, and decoding for each generation attempt inside a
  killable child boundary. Enforce exactly a 120-second hard deadline per generation attempt,
  beginning after child start and including loading, generation, and decoding.
- Keep the adapter call count and generation attempt count truthful:

  | Boundary reached | `adapter_call_count` | `attempt_count` | Result rule |
  |---|---:|---:|---|
  | Stop before invoking `QwenVisionAdapter.understand()` | `0` | `null` | No V2 result, Raw result, or adapter duration is claimed. |
  | Adapter invoked but rejects input before model generation | `1` | `0` | Preserve the typed V2 input-validation failure and map it once if mapping is reached; never retry. |
  | Runner/model generation is reached | `1` | `1` or `2` | Attempt 2 is allowed only after an explicitly classified transient first-attempt failure. |

  There is exactly one adapter call, no outer retry, no third generation attempt, and no
  backfilled call or attempt value. Model-load, device, timeout, total-cap, malformed-output,
  policy, mapper, permanent-runtime, and cleanup failures are terminal. Only a transient
  first-attempt classification can advance the model-reaching state from `1` to `2`.

### Outer adapter-call supervisor and total adapter cap

Revision 2 claimed the proposed generation-runner instance alone was "the coordinator/watchdog
for `total_adapter_cap_seconds` ... the only object present for the entire span of the one-call
adapter boundary." **That claim is withdrawn as incorrect.** The generation runner's `generate()`
method is only active while the adapter is actually inside a call to it. It has no presence, and
therefore no kill authority, during (a) the adapter's own code inside `understand()` before the
first `generate()` call — profile/catalog resolution, media-validation checks,
`_resolve_verified_input_image`'s file read and SHA-256 computation, and the `prompt_builder(request)`
call (qwen_vision.py lines 709-763) — or (b) the adapter's own code after `generate()` returns, in
`_map_raw_output` — JSON parsing, schema validation, and `self._policy.evaluate(...)` (lines
884-984). Both regions run as ordinary synchronous Python inside whichever process executes
`understand()`; a hang there is invisible to, and cannot be terminated by, a watchdog that exists
only during a `generate()` call.

This revision names a separate `Feat018AdapterCallSupervisor`, defined in the same proposed
source file alongside `Feat018BoundedKillableQwenGenerationRunner`, as the exact object
responsible for the complete `QwenVisionAdapter.understand()` invocation.

- **Adapter-worker boundary.** The supervisor spawns one child process (the "adapter worker")
  that constructs the already-approved `Feat018BoundedKillableQwenGenerationRunner`, constructs
  the unmodified `QwenVisionAdapter` with that runner injected as `generation_runner=`, and calls
  `.understand(request)` exactly once, entirely inside that child. This is a second, outer
  process boundary, distinct from and enclosing the per-attempt generation child that
  `Feat018BoundedKillableQwenGenerationRunner.generate()` spawns for each attempt. Pre-adapter
  checks that must complete before `understand()` is ever invoked (env config load, prompt-hash
  check, image admission, hardware checks) may still run in the parent coordinator process before
  the adapter worker is spawned; a stop there already correctly records `adapter_call_count=0`/
  `attempt_count=null` without supervisor involvement. From the moment `understand()` is invoked
  onward, the supervisor's absolute deadline and kill authority apply to everything inside the
  adapter worker: the pre-generate() code, both possible generation attempts, and the
  post-generate() parsing/policy/mapping code.
- **One absolute deadline, and it is the sole hard authority (revision-5 correction).** The
  supervisor computes `cap_deadline_monotonic = time.monotonic() + total_adapter_cap_seconds`
  once, in its own process, before spawning the adapter worker, and never resets or recomputes
  it. This is the **only** value that ever determines when the run is terminated for exceeding
  its total budget. The supervisor enforces it with a wait loop entirely of its own: each
  iteration computes `remaining = cap_deadline_monotonic - time.monotonic()` on the supervisor's
  own clock and polls its IPC channel for at most `min(remaining, small_poll_interval_seconds)`;
  the loop condition that ends the wait and triggers termination is `time.monotonic() >=
  cap_deadline_monotonic`, checked independently of whatever the poll returned. This wait
  **does not require the worker to have sent, or ever send, anything at all.** If the worker
  never reads its first message, if it uses an incorrectly skewed local clock, or if it computes
  and then deliberately or accidentally ignores its own advisory budget and keeps running past
  it internally, none of that changes when the supervisor's loop condition becomes true, because
  that condition depends only on the supervisor's own clock and the passage of wall time — never
  on any signal, cooperation, or correctness from the worker. Revision 4's framing risked reading
  as though the worker's own derived deadline were part of what kept the run bounded; this
  revision states plainly that it is not: the worker's derived value, defined next, is advisory
  only, and the supervisor's independent wait above is what actually terminates the run.
- **Cross-process deadline propagation is advisory only (closes independent-review finding
  G1-1; revised for revision 5).** A raw `time.monotonic()` value must never be transmitted to,
  or interpreted by, a different process: its reference point is implementation-defined and this
  design must not depend on it happening to be numerically comparable across two separate OS
  processes. The supervisor therefore also transmits a plain **duration**, not a timestamp, using
  the same length-prefixed, ceiling-checked framing as every other supervisor IPC message (see
  "Byte-boundary and receive-side limits") — but this transmission exists purely so the generation
  runner *inside* the worker has a reasonable, self-imposed, cooperative bound for its own
  per-attempt work; it grants the worker no authority over how long the run actually lasts.
  1. Immediately before sending the `CONTAINMENT_READY` signal (see "Race-free ownership via a
     `CONTAINMENT_READY` gate protocol" below — containment is established *before* any deadline
     information is ever shared, so the worker is contained regardless of what it does with the
     duration), the supervisor computes
     `remaining_seconds_at_spawn = cap_deadline_monotonic - time.monotonic()`.
  2. This value is carried as a payload field on that same `CONTAINMENT_READY` message — the one
     bounded message that both releases the worker from its start gate and advises it of its
     remaining budget — rather than as a separate handshake requiring its own round trip. If the
     worker never reads this message, sends nothing back, or reads it very late, that has no
     effect on the supervisor's own wait above, which continues regardless; a worker that never
     receives `CONTAINMENT_READY` at all also never proceeds past its start gate (see the
     containment section), so it can only ever be terminated pre-execution in that case.
  3. If the worker does receive it, it may compute its own local
     `worker_cap_deadline_monotonic = worker_local_monotonic_origin + remaining_seconds_at_spawn`
     and use it as a cooperative internal bound. This local value can be wrong — subject to the
     worker's own clock skew, scheduling delay before it captured
     `worker_local_monotonic_origin`, or a bug that causes the worker to ignore it outright — and
     the design tolerates all of these, because none of them is load-bearing: the worker's local
     value is never consulted by the supervisor and never substitutes for the supervisor's own
     `cap_deadline_monotonic` check. **IPC transport latency, worker clock skew, and a
     non-cooperative worker never extend the run past the supervisor's own deadline; the previous
     claim that latency "conservatively shortens" the worker's derived deadline is withdrawn as an
     implied safety argument — the worker's derived deadline provides no safety guarantee of any
     kind, only a best-effort internal optimization.**
  4. Once released, the worker sends its own `ADAPTER_STARTED` progress event (the first event of
     its own sequenced progress stream, defined in "Supervisor progress state machine and deadline
     freeze" below) as it begins constructing the adapter. This is a separate, worker-authored
     event, distinct from the supervisor-authored `CONTAINMENT_READY` release signal that preceded
     it.
- **The 120-second per-attempt bound is advisory inside the worker; the supervisor's absolute
  deadline is what actually bounds the run.** If the worker computed a local
  `worker_cap_deadline_monotonic`, its generation runner may bound each attempt's own child at
  `min(120.0, worker_cap_deadline_monotonic - time.monotonic())` as a cooperative optimization.
  Whether or not the worker does this correctly, at all, or in a timely fashion, the supervisor's
  own external wait (above) still terminates the adapter worker — and, via containment below,
  every process it spawned — the instant its own `cap_deadline_monotonic` passes.
- **Required offline tests for supervisor-only authority (revision 5):**
  1. *Delayed first message*: a fake worker double never reads the `CONTAINMENT_READY` release
     signal (carrying the advisory duration) at all, and therefore never proceeds past its start
     gate. Assert the supervisor still terminates at exactly its own `cap_deadline_monotonic`,
     using only its own clock, with no dependency on the handshake having been read.
  2. *Worker clock skew*: a fake worker double is given a deliberately skewed fake clock so its
     own locally-computed `worker_cap_deadline_monotonic` would fire either much earlier or much
     later than the supervisor's true deadline. Assert the supervisor's own termination time is
     unaffected by the worker's skewed clock in either direction.
  3. *Worker ignoring the budget*: a fake worker double receives the advisory duration and
     explicitly discards it, running its fake generation loop with no internal bound at all.
     Assert the supervisor still terminates the double at its own `cap_deadline_monotonic`.
  4. *Late success*: retained from revision 4 — a fake completed result arrives after the
     supervisor's deadline has passed. Assert it is discarded and never accepted.
  5. *Retry near deadline*: a fake worker double begins a second generation attempt very close to
     the supervisor's deadline (with or without correctly computing that little time remains).
     Assert the supervisor's deadline still fires and terminates the run regardless of whether an
     attempt was already mid-flight, and that no third attempt or extension is ever granted.
  In every one of these cases, the supervisor's own, independently-computed
  `cap_deadline_monotonic` is the value that wins.
- **Reject late success.** If the adapter worker sends its completed result back to the
  supervisor after `cap_deadline_monotonic` has already passed, the supervisor discards that
  result and raises a terminal exception. A result is never accepted once the deadline has
  passed, at either the generation-runner level (revision 2) or the supervisor level (this
  revision). This rule is now subsumed by, and stated formally in, the atomic post-deadline
  freeze in "Supervisor progress state machine and deadline freeze" below.
- **No outer retry; no fabricated result or attempt count.** The supervisor invokes the adapter
  worker's `understand()` call exactly once and never restarts it. `attempt_count` is governed
  entirely by the explicit progress state machine defined in "Supervisor progress state machine
  and deadline freeze" below, not by silence, timing, or any inferred signal.
- **Race-free ownership via a `CONTAINMENT_READY` gate protocol (closes independent-review
  findings G2-1, G2-2, G2-3; hardened for revision 5).** Revision 3 relied on the adapter worker
  reporting the generation child's PID to the supervisor over IPC after spawning it. Revision 4
  replaced this with OS-level containment but described the containment-assignment step loosely.
  Revision 5 defines one explicit, symmetric gate protocol for both platforms, so the worker is
  structurally unable to construct the adapter or spawn a generation child before containment is
  established and verified:
  1. **Fail closed if containment is unavailable.** Before doing anything else, the supervisor
     attempts to create the platform containment primitive (a POSIX process group/session, or a
     Windows job object). If this creation itself fails — the primitive is unsupported or
     unavailable in the current runtime — the supervisor does not spawn the adapter worker at
     all; the run stops as a pre-adapter terminal failure (`adapter_call_count=0`,
     `attempt_count=null`). There is no permitted mode in which the worker runs uncontained.
  2. **The worker starts behind a start gate and does no other work first.** The supervisor spawns
     the adapter worker. The worker's process-entry function's first and only action, before
     constructing anything, is to block on a bounded receive for a `CONTAINMENT_READY` signal from
     the supervisor over the bounded IPC channel. **The worker must not construct the
     `QwenVisionAdapter`, the generation runner, or spawn any generation child before this signal
     is received.** This applies identically on both platforms; the platform difference is only
     in what the supervisor does *before* sending the signal:
     - **POSIX.** Before spawning the worker, the worker's own designated entry point is written
       so that, immediately upon starting and before waiting at the gate, it places itself into
       its own new session/process group (for example via `os.setpgrp()`), which the supervisor
       already knows the identity of (a POSIX process's group ID is deterministic relative to its
       own PID at the moment it calls `setpgrp()`). The supervisor then independently confirms
       this from outside (for example by reading the process's own group ID from the OS) before
       proceeding. This gives POSIX a real containment gate, not merely an inference that
       "the first line of code is fast": the supervisor's independent confirmation is what makes
       it a gate rather than an assumption.
     - **Windows.** The supervisor already created the job object in step 1. Once the worker
       process exists (already blocked at the start gate, having done nothing else), the
       supervisor calls the job-assignment primitive to assign the worker's process handle into
       that job object, then independently verifies the assignment succeeded by querying the job
       for its current process membership and confirming the worker's identity is present.
  3. **`CONTAINMENT_READY` is sent only after verified assignment, and is itself bounded.** The
     supervisor sends the `CONTAINMENT_READY` signal to the worker only after the platform-specific
     verification in step 2 has positively confirmed containment. The entire gate — spawn, assign
     (Windows) or confirm (POSIX), verify, and signal — is itself bounded by a small, fixed
     `containment_setup_timeout_seconds`, distinct from `total_adapter_cap_seconds`.
  4. **Any failure or timeout in the gate kills the worker before execution.** If assignment
     fails, if verification does not confirm membership, or if the gate's own bounded timeout
     elapses before `CONTAINMENT_READY` can be sent, the supervisor terminates the worker
     immediately (it is still blocked at the gate, having done nothing else) and records a
     pre-adapter terminal failure. The worker never proceeds to construct the adapter or spawn a
     generation child in this case.
  5. **After release, containment covers every further spawned process automatically.** Once the
     worker receives `CONTAINMENT_READY` and proceeds, every further process it spawns — in
     particular each attempt's generation child — automatically inherits containment membership: a
     POSIX child inherits its parent's process group unless it explicitly changes it, and a
     Windows process created by a job-contained parent stays in that job by default. From this
     point on, no further IPC message is required for containment to hold.
  6. **Cleanup targets the stable containment handle established in steps 1–2, never a reported
     PID.** Whenever the supervisor terminates the adapter worker for any reason — the absolute
     deadline (which, per the previous section, is enforced by the supervisor regardless of
     anything the worker does), a detected failure, or ordinary completion — it terminates the
     **whole container** using the same handle/identity it created and verified before ever
     releasing the gate (POSIX: signal the whole process group; Windows: terminate the job by its
     handle), not a PID value learned later from the worker. This kills the generation child even
     if the worker was killed before it could run its own cleanup, before it ever spawned a
     generation child, or after it had already exited on its own.
  7. **Containment-empty verification never depends on a specific PID.** Confirming cleanup
     succeeded means confirming the container itself has no remaining live members (POSIX: no
     process remains in the group; Windows: the job reports zero active processes) — a property
     the OS tracks independently of any individual PID and therefore immune to PID reuse. A PID
     may still be reported by the worker, over the same bounded channel, purely as a **diagnostic
     identity for evidence/logging**; it is never the supervisor's load-bearing termination or
     verification mechanism.
- **Bounded verification and no indefinite wait, at every level.** Confirming the container is
  empty requires a bounded poll (termination signals are asynchronous; a process can take a small
  amount of time to actually exit after being signalled), using the same `cleanup_deadline_seconds`
  budget and the same "no indefinite wait" rule as elsewhere in this package. If the container
  still reports a live member after that bounded deadline is exhausted, cleanup has failed exactly
  as already specified for `CLEANUP_FAILED`.
- **No reliance solely on `finally` inside a worker being killed.** A process terminated from
  outside cannot be trusted to run its own Python `finally` blocks to completion — a hard kill can
  interrupt execution at any point, including inside the `finally` body itself. Cleanup of
  anything the adapter worker owns is therefore never assumed to have happened merely because the
  worker's own source contains a `try/finally`; it is always independently confirmed by the
  container-emptiness check above.
- **Offline fake cases for the gate protocol and orphan/race conditions (revision 5)**, required
  in the offline test matrix below:
  1. *Assignment failure*: a fake Windows-style job-assignment call reports failure. Assert the
     supervisor never sends `CONTAINMENT_READY`, terminates the fake worker while it is still at
     the gate, and records a pre-adapter terminal failure without the fake worker ever
     constructing a fake adapter or spawning a fake child.
  2. *Start-gate timeout*: the fake assignment/verification sequence never completes within
     `containment_setup_timeout_seconds`. Assert the same pre-adapter-terminal outcome as above,
     with no `CONTAINMENT_READY` ever sent.
  3. *Worker attempting early child creation*: a deliberately non-conformant fake worker double
     attempts to spawn a fake generation child before receiving `CONTAINMENT_READY`. Assert the
     test double's own gate-blocking construction prevents this from having any observable effect
     reachable by the supervisor (the fake spawn call, if made, is not one the supervisor's
     containment or cleanup accounting depends on) — this test documents and enforces the ordering
     invariant the design relies on, rather than trusting worker good behavior alone.
  4. *Deadline during assignment*: the supervisor's fake absolute deadline elapses while the fake
     assignment/verification sequence is still in progress, before `CONTAINMENT_READY` has been
     sent. Assert the worker is terminated at the gate, never released, and the run records a
     truthful terminal outcome for a stop that occurred before any generation attempt could begin.
  5. *Worker death before release*: the fake worker double dies (crashes) while blocked at the
     gate, before `CONTAINMENT_READY` was ever sent. Assert the supervisor detects this (its own
     bounded wait on the gate does not hang) and proceeds directly to termination/cleanup without
     waiting indefinitely for a signal that will never come.
  6. *Descendant cleanup after worker death*: as defense-in-depth against the ordering invariant in
     case 3 ever being violated by an implementation bug, a fake scenario places a fake descendant
     into the container despite the gate, then the fake worker dies. Assert the supervisor's
     containment-wide termination and containment-emptiness verification still finds and removes
     that descendant, because cleanup acts on the whole container, not on any specific expected
     process list.
- **Bounded terminate/grace/kill/join, at both levels.** The supervisor applies the same
  terminate -> bounded grace period -> kill -> bounded `join` pattern used elsewhere in this
  package (mirroring the existing `_terminate_worker` shape in qwen_vision.py lines 594-602) to
  the adapter-worker process, and the adapter worker applies the same pattern to its own
  generation child. Every `join` at both levels carries an explicit timeout; no indefinite `join`
  exists anywhere in the supervisor or the runner.
- **Same bounded framing for all supervisor IPC.** The channel between the supervisor and the
  adapter worker uses the identical length-prefixed, ceiling-checked framing rules defined in
  "Byte-boundary and receive-side limits" below — a declared frame length is checked against its
  own ceiling before any payload is read or decoded. This channel carries only the
  `CONTAINMENT_READY` release signal (including the propagated advisory deadline duration), the
  worker-authored framed progress/terminal events defined below (starting with `ADAPTER_STARTED`),
  and an optional diagnostic PID for evidence/logging; it never carries raw output, prompt text,
  unbounded diagnostic text, or a live process handle (which cannot be meaningfully serialized
  across the process boundary and is never required, since cleanup uses container
  containment rather than PID/handle-based targeting).
- **`CLEANUP_FAILED` overrides prior success.** If the supervisor cannot confirm both the
  adapter worker and any generation child it spawned are terminated within the bounded cleanup
  deadline (`cleanup_deadline_seconds`, as introduced below), the overall run is forced to
  `FAILED`/`CLEANUP_FAILED` regardless of any result already produced, with no retry and no
  second session, exactly as already stated for the generation-runner level.
- **Bounded cleanup deadline** (unchanged from revision 2, now shared by both levels): one
  explicit, positive `cleanup_deadline_seconds`, separate from `total_adapter_cap_seconds` and
  from D9's byte ceilings, bounds the sum of all terminate/kill/join attempts at both the
  supervisor and generation-runner levels for one run.
- **Offline fake cases for actual adapter hangs**, required in the offline test matrix below,
  replacing the revision-2 "hang before/after runner" cases (which modeled only
  generation-runner/child-wait hangs and did not model a hang in the adapter's own synchronous
  code):
  1. *Hang before first `generate()`*: a fake adapter-worker double hangs before ever calling a
     fake `generate()`, modeling a stuck `_resolve_verified_input_image` or `prompt_builder`
     inside `understand()`, so only `ADAPTER_STARTED` was ever accepted. Assert the supervisor
     terminates the adapter-worker double at the absolute deadline, that no fake `generate()` call
     was ever made, and that `attempt_count` is recorded as `null` because no
     `GENERATION_ATTEMPT_STARTED` event was accepted.
  2. *Hang after `generate()` returns*: a fake adapter-worker double's fake `generate()` returns
     promptly (its `GENERATION_ATTEMPT_STARTED` event was accepted) but the double then hangs
     inside fake post-generate processing (modeling a stuck `_map_raw_output`/policy-evaluation
     path) before it can send its terminal event. Assert the supervisor terminates the double at
     the absolute deadline using the last **accepted** event's `attempt_number` (per "Supervisor
     progress state machine and deadline freeze" below), and that no fabricated V2/Raw result
     crosses the supervisor boundary.
  3. *Cleanup hang at either level*: retained from revision 2 — the fake process's `is_alive()`
     remains `True` after every bounded fake `join` in the cleanup budget is exhausted. Assert
     `CLEANUP_FAILED` is reported and overrides any success already recorded, and that no second
     child, worker, or session is started.
- These offline fake-clock/fake-process cases prove only the supervisor's and generation
  runner's own control-flow and state-machine correctness against injected doubles. **They do
  not, and cannot, prove real GPU memory release or real OS-process termination**; that remains
  unverified until the later live smoke run under a separate execution approval.

### Supervisor progress state machine and deadline freeze

Revision 3 tracked `attempt_count` informally, from "the last progress message actually
received." The independent review found this had no explicit rule preventing a late-arriving
message from being accepted after the supervisor's deadline had already passed (finding G3-1),
and no explicit validation rule for the progress messages themselves (finding G3-2). Revision 4
replaces the informal description with an explicit, closed state machine.

**Events.** Exactly three kinds of framed, **worker-authored** event exist, each using the same
length-prefixed, ceiling-checked framing as every other supervisor IPC message. These are distinct
from the supervisor-authored `CONTAINMENT_READY` release signal (which precedes all of them, is
not part of this sequenced stream, and carries the advisory deadline duration — see "Race-free
ownership via a `CONTAINMENT_READY` gate protocol" above):

- `ADAPTER_STARTED` — sent exactly once by the adapter worker, as `seq=1` of its own progress
  stream, immediately after the worker has received `CONTAINMENT_READY` and begun constructing the
  adapter. It carries no payload of its own; the advisory deadline duration was already delivered
  via `CONTAINMENT_READY`.
- `GENERATION_ATTEMPT_STARTED(attempt_number)` — sent exactly once per generation attempt,
  immediately before the adapter worker's injected generation runner is entered for that attempt,
  with `attempt_number` equal to `1` or `2`.
- one terminal outcome event — sent exactly once, immediately after `understand()` returns or
  raises, carrying the harness's own classification of the outcome (success, or one of the
  existing typed/terminal failure categories); it never carries raw output, a V2/Raw object, or
  prompt text.

**Sequencing.** Every event carries a plain integer `seq`, assigned by the adapter worker,
starting at `1` and incrementing by exactly `1` for each event it sends on this channel. The
supervisor tracks `last_accepted_seq` (initialized to `0`) and `state` (initialized to
`NOT_STARTED`; the full state set is `NOT_STARTED`, `ADAPTER_STARTED`,
`GENERATION_ATTEMPT_STARTED(1)`, `GENERATION_ATTEMPT_STARTED(2)`, `TERMINAL`, and `FROZEN` —
`FROZEN` is defined below and is reachable from any of the other states).

**Event acceptance time (revision 5, precise definition).** Every incoming frame has exactly one
`acceptance_time`: the supervisor's own `time.monotonic()` reading captured at the instant a
**complete** bounded frame — its full declared length received, and validated under the shared
bounded-framing rules in "Byte-boundary and receive-side limits" — first becomes available for
processing. `acceptance_time` is captured once, at that instant, and is never recomputed or
substituted later. A frame that *begins* arriving before the deadline but whose length-declared
bytes do not finish arriving (and validating) until after the deadline has an `acceptance_time`
after the deadline — its arrival start time is irrelevant; only completion matters.

**Acceptance rule.** On receiving a frame, the supervisor accepts it as the new committed state
only if **all** of the following hold, checked in this order, with no other code running between
the deadline comparison and the accept/reject decision — this is the supervisor's single,
serialized event loop (or an equivalent explicitly locked design if ever made concurrent, such
that no two acceptance decisions can interleave):

1. **Deadline comparison, using the supervisor's own authoritative deadline.** The frame is
   rejected if `acceptance_time >= cap_deadline_monotonic` (the supervisor's own value from "One
   absolute deadline, and it is the sole hard authority" above — **never** the worker's advisory
   `worker_cap_deadline_monotonic`, which this design does not trust for any purpose). The
   comparison is `>=`, not `>`: an event whose `acceptance_time` exactly equals the deadline is
   rejected, not accepted — ties go to the freeze, never to acceptance. If this check fails, the
   supervisor transitions `state` to `FROZEN` (if not already `FROZEN` or `TERMINAL`) and proceeds
   directly to termination, regardless of the event's content.
2. The frame parses under the shared bounded-framing rules (a malformed or truncated frame is
   never decoded, let alone accepted).
3. `seq` equals exactly `last_accepted_seq + 1`. A duplicate (`seq <= last_accepted_seq`) or an
   out-of-order/gapped value (`seq > last_accepted_seq + 1`) is rejected; a gap specifically is
   treated as a broken stream and forces an immediate terminal harness failure, since sequencing
   integrity can no longer be trusted for anything received afterward.
4. The event's kind and (for `GENERATION_ATTEMPT_STARTED`) its `attempt_number` are a valid
   transition from the current `state` under the closed transition table:
   `NOT_STARTED -> ADAPTER_STARTED -> GENERATION_ATTEMPT_STARTED(1) -> [GENERATION_ATTEMPT_STARTED(2)] -> TERMINAL`.
   Any other requested transition (a second `ADAPTER_STARTED`, `GENERATION_ATTEMPT_STARTED(1)`
   received twice, `GENERATION_ATTEMPT_STARTED(2)` received before `GENERATION_ATTEMPT_STARTED(1)`,
   a third attempt, or any event after `TERMINAL` or `FROZEN`) is rejected and forces an immediate
   terminal harness failure.

Only when all four checks pass does the supervisor update `state`, set `last_accepted_seq = seq`,
and — for a `GENERATION_ATTEMPT_STARTED` event — set `attempt_count` to that event's
`attempt_number`. **`attempt_count` changes at no other point and by no other mechanism.**

**`FROZEN` is a distinct, formal state, entered exactly once (atomic post-deadline freeze).**
`FROZEN` is reached only via acceptance-rule check 1 failing; it is never reached by a
worker-reported event. It is distinct from `TERMINAL`, which is reached only by a validly-accepted
terminal event received strictly before the deadline. The supervisor's event-processing loop is
single-threaded and synchronous: the deadline comparison (check 1) and the resulting transition to
`FROZEN` happen back to back with no yield point between them, so there is exactly one place where
"has the deadline passed" is decided, decided fresh against every frame's own `acceptance_time`,
and never cached from an earlier check. The instant `state` becomes `FROZEN`, the supervisor stops
reading any further frames from the channel — including any additional frames already buffered
and waiting to be read — and immediately begins adapter-worker/container termination using only
the `state`/`attempt_count` already committed strictly before that moment. A progress or terminal
event that was merely in flight, or already queued, at the moment of the freeze is never
processed, regardless of what it contains. This closes the "late event" race (G3-1): there is no
path by which an event can be evaluated against a stale notion of "before the deadline," because
every event's own `acceptance_time` is fixed at the moment it is first fully validated, not at
whatever later moment the loop happens to get around to comparing it.

**Duplicate, partial, malformed, gapped, out-of-order, and late events cannot change
`attempt_count` or manufacture success.** Each is rejected by one of the four acceptance-rule
checks above before any state mutation occurs; none of them can reach the point where
`attempt_count` or `state` is written. In particular, a terminal event reporting success can never
be accepted once `state` is already `TERMINAL` or `FROZEN`, so a duplicate or replayed success
message can never retroactively convert an already-recorded failure into a success, and no failure
outcome (whether reached via `TERMINAL` or `FROZEN`) can ever be "overwritten" by a later,
differently-timed success event.

**Exit code, PID, and uncommitted worker state are never evidence of an attempt.** Even after
container-based cleanup (above) confirms the generation child and adapter worker have exited, even
if a diagnostic PID or exit code was observed, and even if the worker's own internal memory
believed it had reached a further attempt or a different outcome than what was actually accepted,
none of that is ever used to infer, backfill, or corroborate `attempt_count` or the outcome. The
only source of truth for `attempt_count` and outcome is the sequence of events actually **accepted**
under the rule above — never a value the worker merely computed, held, or intended to send but
that was never accepted before `FROZEN`/`TERMINAL`. An OS-level signal about whether or how a
process exited, or any state that existed only inside the worker's own memory, is disjoint from,
and never a substitute for, that accepted event stream.

**If the supervisor must kill the adapter worker/container before any event was ever accepted**
(`state` is still `NOT_STARTED`), it records `attempt_count=null` and `adapter_call_count` as
whatever value the harness had already set before invoking `understand()` (see the existing
cardinality table above); it never infers `0`, `1`, or `2` from the absence of events.

**Required deterministic offline test cases**, in addition to the hang cases already listed
above:

- one case per rejected-event condition: a duplicate `seq`, a gapped `seq`, a malformed/truncated
  frame, an invalid state transition (each of the specific invalid transitions named in
  acceptance-rule check 4), and a terminal event received after `state` is already `TERMINAL` —
  each asserting the event is rejected and `attempt_count`/`state` are unchanged;
- **event/deadline tie (revision 5)**: a fake event's `acceptance_time` is constructed to equal
  `cap_deadline_monotonic` exactly. Assert the event is rejected (the `>=` comparison, not `>`)
  and `state` transitions to `FROZEN`, never accepting an exactly-tied event;
- **frame completes after deadline (revision 5)**: a fake frame begins arriving (partial bytes
  received) before the fake deadline, but its length-declared bytes do not finish arriving and
  validating until after the deadline. Assert `acceptance_time` is computed at completion, not at
  first-byte-arrival, and the event is therefore rejected;
- a deadline/event race case: a fake event is constructed to arrive at, or a fixed small interval
  after, the exact fake-clock instant the deadline passes, in both possible orderings (event
  processed just before vs. just after the deadline check); assert the outcome is deterministic
  and matches the acceptance rule exactly, with no dependence on incidental scheduling order in
  the test harness itself;
- a case where a fake success terminal event is queued behind, but not yet processed at, the
  moment a fake deadline check fails: assert the success is never accepted and the run's outcome
  is the same terminal failure the deadline itself produces, never a success;
- **terminal followed by progress (revision 5)**: a fake `GENERATION_ATTEMPT_STARTED` or a second
  terminal event arrives with a valid `seq` immediately after a terminal event was already
  accepted. Assert it is rejected under the closed transition table and `state`/`attempt_count`
  remain exactly as they were at `TERMINAL`;
- a case where a fake exit code of `0` (or any other value), or a fake worker-internal
  "uncommitted" attempt count, is available for the generation child or adapter worker but no
  corresponding typed event was ever accepted: assert `attempt_count` and outcome are unaffected
  by either.

### Byte-boundary and receive-side limits

All four ceilings below are defined on **encoded bytes**, never on character counts:

- `raw_output_max_bytes` bounds `len(raw_output_str.encode("utf-8"))` — the exact UTF-8 byte
  length of the decoded provider string. The child must compute this encoded length before
  constructing any IPC envelope and must refuse to send if it is exceeded. This is a required
  wrapper responsibility: the existing `_send_worker_message`/`Connection.send` path has no
  such check (see the adapter/retry compatibility contract above).
- `ipc_envelope_max_bytes` bounds the length of the **complete serialized frame** that crosses
  the child-parent boundary, including any envelope wrapper, `kind` discriminator, and error
  metadata — not just the payload's own bytes. Because the existing worker protocol uses
  Python's unbounded `pickle` transport with no length-prefixed frame, the wrapper must
  implement its own length-prefixed framing (a fixed-size byte length header followed by
  exactly that many bytes of a JSON- or msgpack-encoded envelope) so the child can "prove the
  envelope fits its exact byte ceiling before sending" and the parent can validate the declared
  frame length **before** accepting or decoding the payload: read only the length header first,
  reject immediately if the declared length exceeds `ipc_envelope_max_bytes`, and never read or
  decode the remaining payload bytes when that check fails.
- `stdout_max_bytes` and `stderr_max_bytes` are independent ceilings, each measured on the raw
  encoded bytes written to that specific stream by the child — not a combined ceiling and not a
  decoded-character count. Because a `multiprocessing.Process` inherits the parent's stdout/
  stderr file descriptors by default, the wrapper must either redirect each stream to a
  bounded, non-persistent sink that the parent reads with its own byte-count cap, or disable
  the stream entirely.
- **Ceiling `0` is defined separately per stream.** `stdout_max_bytes=0` (or
  `stderr_max_bytes=0`) means that stream is fully disabled: any single byte observed on it is
  an overflow and triggers `TERMINATE_AND_MARK_FAILED`. Per the live plan's D9,
  `raw_output_max_bytes` and `ipc_envelope_max_bytes` must each be an exact **positive**
  integer; `0` is not a valid setting for either of those two, and an implementation or
  approval attempting `0` there must be rejected before any run.
- Any overflow above raises a terminal exception from the wrapper (for example
  `QwenPermanentRuntimeError`), never `QwenTransientRuntimeError`, so the existing adapter's
  terminal-handling paths apply without modification.

Required additional offline test cases, beyond the matrix already in revision 1, for each of the
four ceilings:

- **`N-1`, `N`, `N+1`** encoded-byte-length cases per ceiling, where `N` is the configured
  value: `N-1` and `N` must be accepted, `N+1` must be rejected before crossing the boundary.
- **Multibyte UTF-8 boundary**: a case where the configured ceiling lands in the middle of a
  multibyte UTF-8 code point. Assert the boundary is enforced on raw encoded bytes (not on a
  truncated-then-redecoded string), and that the wrapper never attempts to decode a byte
  sequence it has already rejected as oversized.
- **Raw-pass/envelope-fail**: raw output is under `raw_output_max_bytes`, but the constructed
  envelope (with metadata/errors added) exceeds `ipc_envelope_max_bytes`. Assert this is
  classified as an IPC-envelope overflow, never misreported as a raw-output overflow.
- **Malformed/truncated frame**: the parent reads a length header claiming more bytes than
  actually arrive, or a header it cannot parse. Assert the parent rejects before attempting to
  decode any partial payload.
- **Child death during transfer**: the fake child process dies mid-write of a frame (fake
  `is_alive()` becomes `False`, or the fake pipe raises `EOFError`/`BrokenPipeError`). Assert
  the parent treats the partial/absent frame as a terminal runtime failure — never a false
  success and never a hang — consistent with the existing adapter's own
  `except (EOFError, OSError): raise QwenPermanentRuntimeError` handling shape (qwen_vision.py
  lines 636-637).

### Typed handoff, cleanup, and evidence

- Accept exactly one schema-valid typed V2 success/failure union from the existing adapter,
  then call `map_vision_result_to_raw` exactly once when a V2 result exists. Pass the approved
  opaque synthetic session ID, staged source digest, request correlation ID, and
  `asr_result=None`. Do not alter the mapper or infer eligibility, personality, readiness,
  activity, objective, Gate A confirmation, Gate B, or semantic safety.
- Wrap the complete authorized run body in `try/finally`. Cleanup must close IPC, terminate and
  join any child within `cleanup_deadline_seconds` (see "Outer adapter-call supervisor and total
  adapter cap" above; no indefinite `join`), discard raw output and decoded tensors,
  terminate the Lightning session, and confirm no residual runner process or GPU execution
  remains. Cleanup is required on every stop path, including pre-adapter stops. Any cleanup
  failure forces overall `FAILED`/`CLEANUP_FAILED`, overriding any prior success, and permits
  no retry and no second session.
- Produce a sanitized runtime manifest using only the plan's allowlist: interpreter identity
  and version; the four exact dependency names/versions; CUDA availability, device count,
  and an allowlisted runtime fact; driver version; and approved GPU index, SKU, VRAM, and BF16
  facts. Canonicalize the allowlist deterministically and record its SHA-256. Reject extra
  keys and never include paths, environment values, hostnames, URLs, credentials, tokens,
  prompts, raw output, tensors, or arbitrary package/cache inventory.
- Build the future run's exact feature-local JSON/Markdown evidence pair from selected safe
  metadata rather than serializing V2 or Raw objects wholesale:
  `features/FEAT-018-live-image-canvas-flow/evidence/metrics/P2_LIVE_SMOKE_<YYYYMMDD>.json`
  and
  `features/FEAT-018-live-image-canvas-flow/evidence/notes/P2_LIVE_SMOKE_<YYYYMMDD>.md`.
  Those paths are not created by this package. Writing them follows the three-state commit
  protocol in "Evidence commit protocol" below. If the pair cannot reach the authoritative
  committed state under that protocol, write only an ignored local incident fallback at
  `tmp/feat018-live-lightning-incident-<run_id>/INCIDENT.md`; it is not indexed and must not
  contain a prompt, raw output, secret, credential, URL, path, or raw media value.

### Evidence commit protocol

Revision 2 described two sequential renames (JSON, then Markdown) as forming "one atomic unit."
**That claim is withdrawn.** A filesystem rename is atomic only for the single file it renames;
two separate renames are two separate events, and a crash or interruption between them is a real,
observable state that revision 2's rollback bullets already had to special-case. This revision
replaces "atomic pair" with an explicit three-state model and one designated commit-record file.

**Three states:**

1. **Provisional result** — the in-memory outcome the harness has computed (a mapped Raw result,
   a terminal V2/harness failure, cleanup status, and postflight status). Nothing is on disk yet.
2. **Provisional artifacts** — evidence content written to temporary paths in the same
   directories as the final files (for example `<final_path>.tmp-<run_id>`), fully assembled and
   allowlist-validated, but not yet visible at their final paths. A provisional artifact is never
   evidence and is never reported as a result.
3. **Authoritative committed pair** — both final-path files exist, share one `run_id` and one
   `evidence_id`, their hashes/commit metadata agree, the JSON commit record's own
   `commit_state` field reads exactly `FINAL`, and the designated commit record (below) is
   present at its final path. Only this state may be reported as the run's evidence.

**Identity fields (closes independent-review finding G4-1).** Both `run_id` (identifying this
harness execution) and `evidence_id` (identifying this specific evidence pair) are minted once, in
memory, as part of the provisional result in step 1 below, before either file is drafted. Both
identifiers are required, in a fixed, machine-readable location, in **both** files:

- In the JSON commit record, `run_id` and `evidence_id` are ordinary top-level fields.
- In the Markdown companion, `run_id` and `evidence_id` appear as fixed `key: value` lines in a
  dedicated metadata block immediately following the document title — for example:

      # P2 live smoke evidence
      run_id: <value>
      evidence_id: <value>

  This is a fixed, line-based convention specifically so a postflight/validity check can extract
  both values from the Markdown with a plain line-scan, without needing a full Markdown parser.
  A pair is never valid if the Markdown's `run_id`/`evidence_id` lines are absent, malformed, or
  do not match the JSON's values exactly.

**One-directional hash DAG.** The JSON file is the sole designated commit record and the sole
holder of a cross-file hash:

- the JSON contains `companion_markdown_sha256`, the SHA-256 of the Markdown file's finished
  bytes;
- the Markdown contains its own `run_id` and `evidence_id` as plain identity fields, exactly as
  above, but **never** a hash of the JSON file, in any form. This is restated explicitly, in
  addition to the one-directional ordering already implied by the write sequence below, so a
  future revision cannot silently reintroduce a circular hash by having the Markdown reference
  "the JSON it expects" before the JSON exists.

**Ordering and the commit point.** The sequence is:

1. Compute the provisional result, including `run_id`, `evidence_id`, `cleanup_status` from
   cleanup (see the supervisor section above), and the first postflight check (run after cleanup,
   before any file is written). **Cleanup and this first postflight check must both complete
   before any outcome is written into either provisional artifact** — an outcome is never written
   as `SUCCEEDED` and then corrected afterward; if either check has already failed, the
   provisional result already reflects `FAILED`/`CLEANUP_FAILED`/postflight-failure before any
   artifact is drafted.
2. Write the Markdown provisional artifact (temp path) from that final provisional result,
   including its `run_id`/`evidence_id` metadata block, then compute `markdown_sha256` over its
   finished bytes.
3. Write the JSON provisional artifact (temp path), embedding the same `run_id`, the same
   `evidence_id`, the same finalized outcome, `companion_markdown_sha256 = markdown_sha256`, and
   `commit_state = "FINAL"`. `commit_state` is written once, as part of this same temp-file
   content — it is never appended or flipped after the fact — so that the JSON's own bytes, from
   the moment they exist at all, already declare the exact state they will have once committed.
   No third manifest, index, or artifact is introduced; the JSON file's own fields are the commit
   metadata.
4. Rename the Markdown provisional artifact to its final path. This makes the companion file
   visible, but by itself does **not** make the pair authoritative — a reader who observes only
   the Markdown file at its final path (with no JSON at its final path yet) must treat that as an
   incomplete, non-authoritative state, never as a published result.
5. Rename the JSON provisional artifact to its final path. **This single rename is the exact
   commit point.** The instant it succeeds, the pair is authoritative: both files exist, they
   share `run_id` and `evidence_id`, the JSON's `commit_state` reads `FINAL`, and the JSON's
   `companion_markdown_sha256` matches the already-present Markdown's content. Before this rename
   succeeds, the pair is never authoritative, regardless of what exists at the Markdown path.
6. A second postflight check runs after this commit point, per the existing plan's Section 8
   item 8. Because the commit record's on-disk bytes are not rewritten in place once committed
   (rewriting a committed record would recreate exactly the ambiguity this correction removes),
   a failure at this stage is handled as **quarantine, not correction**: the already-committed
   pair is left in place, and the incident-fallback writer records an explicit quarantine
   note — naming both files' safe identities and the postflight discrepancy — without altering
   either file's bytes. The run's reported outcome for indexing purposes is `FAILED` with the
   postflight-failure code; the committed pair alone, unaltered, remains the truthful record of
   what was actually produced before the discrepancy was detected.

**Validity rule ("all predicates pass").** A pair is valid only when **all** of the following
hold simultaneously — a partial match is never sufficient:

- both files exist at their final paths;
- they share one `run_id` and one `evidence_id`, read from the JSON's own fields and from the
  Markdown's fixed metadata-block lines;
- the JSON's `commit_state` field reads exactly `FINAL` (a `PROVISIONAL` value, or the field's
  absence, is never treated as valid even if the file happens to exist at its final path);
- the JSON's `companion_markdown_sha256` equals the SHA-256 actually computed over the
  Markdown file's current bytes;
- the JSON commit record's rename (step 5) is known to have completed.

A missing file, a `run_id`/`evidence_id` mismatch, a `commit_state` other than `FINAL`, a hash
mismatch, a provisional-only artifact, or a pair interrupted before step 5 is never accepted as
success under any circumstance.

**Rollback and quarantine.** If step 4 or step 5 cannot complete (for example, a filesystem error
on rename), no partial pair is left claiming success: any file already at a final path from this
run is removed or moved to a quarantine location, and the incident fallback records the residual
artifact truthfully. **Rollback/quarantine is remediation, not proof of crash consistency** — it
recovers a known-bad state after the fact; it does not retroactively make an interrupted write
safe. If the rollback/quarantine step itself fails (for example, the removal or move errors), the
writer records that failure explicitly: overall status is `FAILED`, and the incident record names
the exact residual artifact(s) rather than claiming a clean state.

**Required fake-filesystem interruption tests**, at every transition, including the transition
the independent review found untested (finding G5-1):

- **Before either temp write** (cleanup/first-postflight failure, before any artifact is
  drafted): assert the provisional result already reflects the failure and that the
  eventually-committed pair never shows a `SUCCEEDED` outcome that was later silently corrected.
- **After the Markdown temp write but before the JSON temp write** (closes finding G5-1): a
  simulated crash leaves exactly one provisional artifact — the Markdown temp file — with no
  corresponding JSON temp file at all, not even a partial one. Assert a recovery/postflight pass
  recognizes the lone Markdown temp file as provisional garbage (never evidence), and specifically
  that it is never incorrectly paired with an unrelated leftover temp file from a different
  `run_id` during recovery.
- **After each validation, before its rename** (both the Markdown and the JSON provisional
  artifacts, considered separately): a simulated crash after a provisional artifact has been fully
  written and allowlist/schema-validated (including, for the JSON, after `commit_state="FINAL"`
  has been written into its content) but before that specific file's rename. Assert the
  not-yet-renamed file is still only a provisional artifact and is never treated as evidence.
- **Before either rename** (both provisional artifacts fully written and validated, neither
  renamed): a simulated crash here leaves only temp files. Assert no final-path file is ever
  treated as evidence and that a recovery/postflight pass recognizes the temp files as
  provisional garbage, not as a result.
- **After the first (Markdown) rename only** (Markdown at its final path, JSON still at its temp
  path or absent): assert this state is detected as non-authoritative — no commit record exists
  yet — and is never reported as `SUCCEEDED` or as a valid pair, even though the Markdown's
  `run_id`/`evidence_id` fields are already readable at that point.
- **Immediately before the final JSON commit rename** (step 5): identical in effect to the
  previous case; assert the pair is still non-authoritative.
- **Immediately after the final JSON commit rename** (step 5 has completed): assert the pair is
  now authoritative under the full validity rule above, and that a simulated subsequent crash does
  not change that — the commit point is the single event that matters, not anything that follows
  it.
- **Cleanup or second-postflight failure, after commit**: retained from the quarantine behavior
  in step 6 above; assert the committed pair's bytes are never rewritten and the run is reported
  `FAILED` via quarantine, not via mutating the committed files.
- **Rollback/quarantine failure**: assert overall status becomes `FAILED` and the incident record
  truthfully names the residual artifact(s) rather than claiming a clean fallback-only state.

**Redaction sentinel tests**, required in the offline test matrix, seed fakes with sentinel
prompt/raw-output/path/URL/token/credential/transcript/exception-text/cache values in four
independent places and assert each is stripped or rejected rather than passed through:
(a) inside a value under an allowlisted key (for example a fake dependency-version string, a
fake GPU SKU, or a fake prompt-source identity carrying a sentinel substring) — an allowlisted
*key* never excuses an unsafe *value*; (b) inside an extra/unlisted key injected by a fake
result or fake manifest — asserted dropped, not merged; (c) independently in both the JSON and
the Markdown evidence files, since free-text Markdown interpolation can leak a sentinel even
when the JSON allowlist check is correct; and (d) inside the incident fallback content itself,
since that writer must enforce redaction on its own rather than being assumed safe merely
because it is a smaller code path.

Run postflight inventory after cleanup (before any artifact is drafted, per step 1 above) and
again after the commit point (step 6). Inspect tracked, untracked, ignored, temporary child/IPC,
cache, runtime-config, generated-output, and evidence artifacts. Only the exact future-approved
pair is allowed; the ignored incident path is the sole exception when the pair cannot reach the
authoritative committed state. Record safe identities and hashes without exposing local paths or
contents.

**Revision 5 crash-transition audit table.** The table below restates the one-way hash DAG and
every crash transition already described above as a single reference for an auditor: given an
observed on-disk state, what verdict a reader must reach. No row below may ever be read as
`AUTHORITATIVE_SUCCESS` unless every one of `run_id` match, `evidence_id` match,
`commit_state=="FINAL"`, and `companion_markdown_sha256` match holds simultaneously at the exact
final-path JSON.

| # | Observed on-disk state | Required reader verdict |
|---|---|---|
| 1 | Neither temp file exists yet (pre-draft, cleanup/first-postflight already failed) | `NOT_EVIDENCE` — no artifact exists; outcome already reflects the pre-draft failure |
| 2 | Markdown temp file exists and is complete; JSON temp file does not exist (or is itself incomplete) | `NOT_EVIDENCE` (provisional garbage) — never paired with an unrelated `run_id`'s leftover temp file |
| 3 | Both Markdown and JSON temp files exist, fully written and validated (JSON content already declares `commit_state="FINAL"`); neither renamed | `NOT_EVIDENCE` (provisional garbage) — content correctness does not matter until the rename in row 6 |
| 4 | Markdown at its final path; JSON absent from its final path (still temp, or never written) | `NON_AUTHORITATIVE` — no commit record exists, even though Markdown's `run_id`/`evidence_id` are already readable |
| 5 | Markdown at its final path; JSON temp file fully written and validated but not yet renamed | `NON_AUTHORITATIVE` — identical in effect to row 4; the rename has not occurred |
| 6 | Markdown at its final path; JSON at its final path; `commit_state=="FINAL"`; `run_id`/`evidence_id` match on both files; `companion_markdown_sha256` matches the Markdown's actual bytes | `AUTHORITATIVE` — the pair is valid; the recorded outcome field (which may itself be `SUCCEEDED` or `FAILED`) is the truthful result |
| 7 | Both files at their final paths, but `commit_state` is `PROVISIONAL` or absent from the JSON despite the JSON existing at its final path | `NON_AUTHORITATIVE` / integrity failure — path existence alone is never sufficient |
| 8 | Both files at their final paths, `commit_state=="FINAL"`, but `run_id` or `evidence_id` differs between the two files | `NON_AUTHORITATIVE` / integrity failure — identity mismatch |
| 9 | Both files at their final paths, `commit_state=="FINAL"`, IDs match, but `companion_markdown_sha256` does not match the Markdown's actual current bytes | `NON_AUTHORITATIVE` / integrity failure — hash mismatch, regardless of cause (corruption, external modification, or a writer bug) |
| 10 | A previously-authoritative pair (row 6) is later flagged by the second postflight check (step 6) as having an unexpected artifact or hash discrepancy, and is quarantined | `QUARANTINED` — the run's indexed outcome is `FAILED` with the postflight-failure code; the original committed bytes are left unaltered as a historical record of what was produced *before* the discrepancy, but are never re-read as current authoritative success |
| 11 | A rollback/quarantine action itself fails, leaving a residual file at (or partway to) a final path in an inconsistent state | `RESIDUAL` — never authoritative under any circumstance; the incident record must name the exact residual artifact truthfully rather than asserting a clean state |
| 12 | Only the ignored incident-fallback record exists at `tmp/feat018-live-lightning-incident-<run_id>/INCIDENT.md`; no JSON/Markdown pair exists at any final path | `NOT_EVIDENCE` — the incident record is not itself evidence, is not indexed, and is not read as any form of success |

Provisional (rows 1–3, 5), incomplete (row 4), mismatched (rows 7–9), quarantined (row 10), and
residual (row 11) artifacts are never read as authoritative success under this table. Only row 6
is `AUTHORITATIVE`, and even then the recorded outcome field — not the mere fact of being
authoritative — determines whether the truthful result was success or failure.

## Responsibilities of the proposed offline test file

`backend/tests/unit/test_feat018_live_lightning_execution.py` would use injected typed fakes,
fake clocks, fake child/process handles, fake bounded transports, fake hardware/readiness
probes, and fake evidence sinks. It must not load a provider or model, touch a GPU, open
Lightning, use a network, or launch a real subprocess. The test file must not modify the existing
FEAT-003 adapter or any other source file. Fake *adapters* are restricted as described in the
real-adapter compatibility contract immediately below; they are not a general substitute for the
real `QwenVisionAdapter`.

### Real-adapter compatibility test contract

Revision 2's offline test matrix allowed retry/cardinality assertions to be made against a fake
adapter. This revision requires the retry and terminal-classification assertions to instead
exercise the **real, unmodified** `QwenVisionAdapter.understand()` control flow imported directly
from `backend/src/sketch2life/infrastructure/ai/qwen_vision.py`, with only its dependencies
faked:

- Construct the real `QwenVisionAdapter` with a fake `QwenGenerationRunner` (implementing the
  real `generate(profile, runtime_config, image_path, prompt) -> str` seam, or raising one of the
  real typed exceptions `QwenModelLoadError`, `QwenDeviceUnavailableError`, `QwenTimeoutError`,
  `QwenTransientRuntimeError`, or `QwenPermanentRuntimeError`), a fake `content_policy`, a fake
  `runtime_config`, and a fake `clock`. The fake runner must never return a prebuilt V2 result;
  it returns only a raw string or raises, exactly like the real seam.
- Do not monkeypatch `QwenVisionAdapter.understand`, its internal `while True:` retry loop, or
  any other adapter method. The adapter's own source and control flow run unmodified; only the
  constructor-injected dependencies are fakes.
- Pin `classify_transient` to the adapter's approved default, `_never_transient` (always
  `False`), unless a specific test is deliberately verifying a separately owner-approved
  non-default classifier. A test must never leave an ad hoc permissive classifier in place that
  would let an arbitrary generic exception look transient; that would mask the real adapter's
  actual retry boundary rather than test it.

Required assertions, all against the real adapter's observable behavior (its returned
`VisionUnderstandingResultV2`, and the fake runner's own call count):

- a fake runner raising `QwenTransientRuntimeError` on the first `generate()` call causes the
  real adapter to call `generate()` a second time (attempt 2 is permitted);
- a fake runner raising `QwenTransientRuntimeError` again on the second call causes the real
  adapter to stop at attempt 2 with a terminal `VISION_PROVIDER_FAILURE`/
  `TRANSIENT_RUNTIME_FAILURE` result; the fake runner's `generate()` is never called a third
  time;
- `QwenTimeoutError`/`TimeoutError`, `QwenModelLoadError`, `QwenDeviceUnavailableError`, and
  `QwenPermanentRuntimeError` from the fake runner each cause the real adapter to stop
  immediately with the corresponding terminal `VisionUnderstandingFailureV2`, with no second
  `generate()` call in any of these cases;
- the wrapper-detected overflow case (raw-output/IPC/stdout/stderr overflow) is exercised at this
  level by having the fake runner raise the same terminal exception type the wrapper contract
  above designates for overflow (`QwenPermanentRuntimeError`); this confirms the real adapter
  treats a wrapper-signalled overflow identically to any other permanent failure — it does not
  re-simulate actual byte counting, which remains covered by the wrapper-level fakes in
  "Byte-boundary and receive-side limits";
- the fake runner's own `generate()` implementation is a single-attempt function with no
  internal loop; the wrapper itself never retries — any second call the fake observes originates
  only from the real adapter's own retry decision, never from the wrapper calling `generate()` a
  second time on its own;
- the coordinator/supervisor invokes `QwenVisionAdapter.understand()` exactly once per run; it
  never re-invokes `understand()` itself after a supervisor-forced kill or any other stop
  condition;
- across the full real-adapter test suite, the fake runner's `generate()` call counter never
  exceeds 2;
- the test suite imports `qwen_vision.py` without modification and does not patch, subclass with
  overridden retry behavior, or otherwise alter `QwenVisionAdapter.understand`,
  `KillableSubprocessQwenGenerationRunner`, or `TransformersQwenGenerationRunner`; the existing
  FEAT-003 adapter source remains exactly as committed.

Fake *adapters* (rather than a fake runner injected into the real adapter) remain acceptable only
for the outer-supervisor edge cases in "Outer adapter-call supervisor and total adapter cap"
above, where the object under test is the supervisor's own process-management logic and not the
adapter's retry decision. All of these tests remain fully offline: no real subprocess, model,
GPU, network, or Lightning execution occurs in either category.

## Offline test matrix

| Area | Required injected-fake cases | Required assertions |
|---|---|---|
| One-attempt success | A bounded fake runner returns one valid typed success path. | Exactly `1/1`; V2-to-Raw handoff is typed; provenance, `gate_a_required=true`, and `NOT_SUPPLIED` narration are preserved; cleanup and postflight run. |
| Real-adapter transient retry | Real `QwenVisionAdapter.understand()` with a fake `QwenGenerationRunner` that raises `QwenTransientRuntimeError` on the first call, then returns success; a second case where it raises the same error again on the second call. | First case: real adapter calls the fake `generate()` a second time and returns exactly `1/2` success; second case: terminal at `2` with `TRANSIENT_RUNTIME_FAILURE`; fake `generate()` is never called a third time; `classify_transient` remains the adapter's default `_never_transient`. |
| Real-adapter terminal classifications | Real `QwenVisionAdapter.understand()` with a fake runner raising, in separate cases, `QwenTimeoutError`/`TimeoutError`, `QwenModelLoadError`, `QwenDeviceUnavailableError`, and `QwenPermanentRuntimeError` (the latter also standing in for a wrapper-signalled overflow). | Each case stops at the real adapter's corresponding terminal `VisionUnderstandingFailureV2` with no second `generate()` call; `qwen_vision.py` is imported unmodified and never monkeypatched. |
| Real-adapter no-outer-retry | Real adapter and fake runner as above; coordinator/supervisor test double invokes `.understand()` from the harness side. | `.understand()` is called exactly once per run; the fake runner's own `generate()` has no internal loop; across the full real-adapter suite the fake `generate()` call counter never exceeds `2`. |
| Pre-adapter stop | Approval, checkout, fixture, readiness, prompt, policy, hardware, manifest, runner-boundary, or budget fake stops before the adapter. | Exactly `0/null`; no V2/Raw claim, mapper call, or fabricated adapter timing; `finally` cleanup and terminal evidence path still run. |
| Adapter input rejection | Real adapter returns the existing typed input-validation result with `attempt_number=0` (profile/media-validation stop, no fake runner call needed). | Exactly `1/0`; typed failure is mapped once if applicable; no model-reaching label and no retry. |
| Timeout and total cap | Fake child exceeds the per-attempt deadline; supervisor/runner consume the total cap across a possible retry. | Child is killably terminated at 120 seconds per attempt; total cap covers the whole one-call boundary without reset; terminal is failed and never retried. |
| Supervisor hang before first `generate()` | Fake adapter-worker double hangs before ever calling a fake `generate()` (models a stuck `_resolve_verified_input_image` or `prompt_builder` inside `understand()`), so only `ADAPTER_STARTED` was ever accepted. | Supervisor terminates the double at the absolute deadline; no fake `generate()` call was made; `attempt_count` is `null` (no `GENERATION_ATTEMPT_STARTED` event was accepted); no `QwenTransientRuntimeError` is raised. |
| Supervisor hang after `generate()` returns | Fake adapter-worker double's fake `generate()` returns promptly (its `GENERATION_ATTEMPT_STARTED` event was accepted), then the double hangs in fake post-generate processing (models a stuck `_map_raw_output`/policy path) before sending its terminal event. | Supervisor terminates the double at the absolute deadline using the last **accepted** event's `attempt_number`; no fabricated V2/Raw result crosses the supervisor boundary; a late fake terminal event delivered after the deadline is discarded, never accepted. |
| Supervisor cleanup hang | Fake process's `is_alive()` (or fake container membership) remains non-empty after every bounded fake `join`/poll in the cleanup budget is exhausted, at either the supervisor or generation-runner level. | `CLEANUP_FAILED` is reported and overrides any success already recorded in the same run; no second child, worker, or session starts. |
| Delayed first message | Fake worker double never reads the `CONTAINMENT_READY` release signal at all. | Supervisor terminates at exactly its own `cap_deadline_monotonic`, with no dependence on the worker having read anything. |
| Worker clock skew | Fake worker double is given a deliberately skewed fake clock so its own locally-derived deadline would fire earlier or later than the supervisor's true deadline. | Supervisor's own termination time is unaffected by the worker's skewed clock in either direction. |
| Worker ignoring the budget | Fake worker double receives the advisory duration and explicitly runs its fake generation loop with no internal bound at all. | Supervisor still terminates the double at its own `cap_deadline_monotonic`, independent of the worker's cooperation. |
| Retry near deadline | Fake worker double begins a second fake generation attempt very close to the supervisor's deadline. | Supervisor's deadline fires and terminates the run regardless of an attempt already mid-flight; no third attempt or extension is ever granted. |
| Containment assignment failure | Fake Windows-style job-assignment call reports failure. | Supervisor never sends `CONTAINMENT_READY`; fake worker is terminated at the gate; run records a pre-adapter terminal failure; no fake adapter/child construction occurs. |
| Containment start-gate timeout | Fake assignment/verification sequence never completes within `containment_setup_timeout_seconds`. | Same pre-adapter-terminal outcome as assignment failure; `CONTAINMENT_READY` is never sent. |
| Worker attempting early child creation | A non-conformant fake worker double attempts to spawn a fake generation child before receiving `CONTAINMENT_READY`. | The gate-blocking test-double construction prevents this from having any effect the supervisor's containment/cleanup accounting depends on, documenting and enforcing the ordering invariant. |
| Deadline during containment assignment | Fake absolute deadline elapses while fake assignment/verification is still in progress, before `CONTAINMENT_READY` is sent. | Worker is terminated at the gate, never released; run records a truthful pre-generation-attempt terminal outcome. |
| Worker death before gate release | Fake worker double dies while blocked at the start gate, before `CONTAINMENT_READY` was ever sent. | Supervisor's bounded wait on the gate does not hang; supervisor proceeds directly to termination/cleanup. |
| Descendant cleanup after worker death | Defense-in-depth case: a fake descendant is placed into the container despite the gate, then the fake worker dies. | Containment-wide termination and containment-emptiness verification still find and remove the descendant, since cleanup acts on the whole container. |
| Kill before child registration | Fake container double is instructed to terminate before any generation-child diagnostic-PID message was ever sent. | Fake container-wide termination call occurs and the fake generation child is reported terminated; no test setup requires a PID message to have been sent. |
| Child start concurrent with deadline | A fake child-spawn call and a fake deadline expiry are interleaved in both possible orders. | The fake container-wide kill is issued and the fake child ends up terminated in both orderings, independent of which event the fake scheduler delivers first. |
| Stale/reused PID | A diagnostic PID recorded for a prior, already-exited fake child numerically matches a currently-live, unrelated fake process outside this run's container. | Cleanup verification (container-emptiness) correctly ignores the unrelated process and does not report it as a live residual child. |
| Worker death before cleanup | Fake adapter-worker double dies unexpectedly (not via a supervisor-issued kill) before running any of its own cleanup code. | Supervisor's container-level termination/verification still determines the true state correctly (already empty, or terminates and confirms removal of any still-live descendant) without depending on the worker's own `finally`. |
| Progress event: duplicate/gapped `seq` | A fake worker double sends a `GENERATION_ATTEMPT_STARTED(1)` event twice (duplicate `seq`), and separately a case where `seq` jumps from `1` to `3` (gap). | Both are rejected; the duplicate leaves `state`/`attempt_count` unchanged; the gap forces an immediate terminal harness failure; neither is silently accepted. |
| Progress event: invalid transition | Fake events attempt each invalid transition named in the state-machine table: a second `ADAPTER_STARTED`, `GENERATION_ATTEMPT_STARTED(2)` before `GENERATION_ATTEMPT_STARTED(1)`, a third attempt-start, and a second terminal event after `TERMINAL`. | Each is rejected and forces an immediate terminal harness failure; `attempt_count`/`state` never reflect a rejected transition. |
| Progress event: terminal followed by progress | A fake `GENERATION_ATTEMPT_STARTED` or second terminal event, with a valid `seq`, arrives immediately after a terminal event was already accepted. | Rejected under the closed transition table; `state`/`attempt_count` remain exactly as recorded at `TERMINAL`. |
| Progress event: malformed/partial frame | A fake progress or terminal event frame is truncated or fails the shared bounded-framing checks. | Rejected before decode, exactly as any other malformed frame; `attempt_count`/`state` are unchanged. |
| Event/deadline tie | A fake event's `acceptance_time` is constructed to equal `cap_deadline_monotonic` exactly. | Rejected under the `>=` comparison; `state` transitions to `FROZEN`, never accepting an exactly-tied event. |
| Frame completes after deadline | A fake frame begins arriving before the fake deadline but its declared bytes finish arriving/validating only after it. | `acceptance_time` is computed at completion, not first-byte-arrival; the event is rejected. |
| Deadline/event race | A fake event is constructed to arrive at, or immediately after, the exact fake-clock instant the deadline passes, tested in both possible processing orders. | The outcome is deterministic per the acceptance rule in both orderings; an event that arrives at or after the deadline check is never accepted, regardless of incidental test-harness scheduling. |
| Queued success behind a failed deadline check | A fake terminal success event is already queued on the channel at the moment a fake deadline check fails. | The queued success is never processed or accepted; the run's outcome is the same terminal failure the deadline itself produces, never a success. |
| Exit code/uncommitted state is not evidence | A fake exit code of `0` (or any other value), or a fake worker-internal uncommitted attempt count, is available for the generation child or adapter worker, but no corresponding typed event was ever accepted. | `attempt_count` and outcome are completely unaffected by either; only accepted typed events are consulted. |
| Raw-output overflow | Fake child produces raw bytes over the configured raw ceiling, measured as encoded UTF-8 bytes. | Rejected before IPC send; no raw value reaches parent, stream, hook, log, or evidence; session termination and cleanup occur. |
| Raw-output byte boundary | Fake raw output at exactly `N-1`, `N`, and `N+1` encoded bytes, plus a case where the ceiling lands mid multibyte-UTF-8 code point. | `N-1`/`N` accepted, `N+1` rejected; the mid-codepoint case is enforced on raw bytes, never on a truncated-then-redecoded string. |
| IPC-envelope overflow | Fake serialized envelope is over the configured IPC ceiling or cannot be proven bounded. | Rejected before send/acceptance; terminal bounded-output failure; no unbounded `Connection.send` path is accepted. |
| IPC-envelope byte boundary and raw-pass/envelope-fail | Fake envelope at exactly `N-1`, `N`, `N+1` encoded frame bytes; a case where raw output is under its own ceiling but the assembled envelope exceeds `ipc_envelope_max_bytes`. | `N-1`/`N` accepted, `N+1` rejected; the raw-pass/envelope-fail case is classified as an IPC-envelope overflow, never a raw-output overflow. |
| Malformed or truncated frame | Fake parent receives a length header claiming more bytes than arrive, or an unparsable header. | Parent rejects before decoding any partial payload; terminal bounded-output failure; no hang. |
| Child death during transfer | Fake child dies mid-write of a frame (`is_alive()` becomes `False`, or the fake pipe raises `EOFError`/`BrokenPipeError`). | Parent treats the partial/absent frame as a terminal runtime failure, never a false success and never a hang. |
| Stdout/stderr overflow | Each bounded non-persistent stream exceeds its configured ceiling, including a `0`-ceiling case forbidding any byte on that stream. | Each independently terminates and fails the run; stream content is not persisted or exposed; `0` ceiling rejects the first byte. |
| Malformed output | Invalid JSON, duplicate keys/IDs, extra fields, broken references, missing confidence, or schema-invalid fake output. | Existing typed schema/mapping failure is retained; no repair or retry outside the existing adapter behavior; no raw error text leaks. |
| Mapper failure | Fake mapper raises source/hash, correlation/session, unsupported-variant, or other mapping failure. | Terminal harness failure; no fabricated Raw result; cardinality remains the pre-mapping value; cleanup still runs. |
| Policy failure | Fake typed output triggers the injected synthetic lexical policy. | Typed policy rejection is terminal; matched text is absent from logs/evidence; no semantic-safety or production-moderation claim is made. |
| Cleanup failure | Each cleanup operation fails after success and after representative stop/failure paths. | `finally` still attempts all required cleanup; overall result is `FAILED` with `CLEANUP_FAILED`, overriding any prior success; no retry or second session. |
| Prompt-hash mismatch | Builder returns text whose exact UTF-8 hash differs from the approved hash. | Stop before adapter invocation with exactly `0/null`; prompt text is not logged, persisted, or included in evidence. |
| Wrong GPU placement | Hardware inventory, device count/index, or post-load model/input placement fake disagrees with approval. | Fail closed before model generation where possible; otherwise record the entered-attempt cardinality truthfully; never report a functional success on the wrong device. |
| Evidence interruption: cleanup/first-postflight failure before drafting | Fake cleanup or fake first-postflight (run before any artifact is drafted) reports failure. | The provisional result already reflects `FAILED`/`CLEANUP_FAILED`/postflight-failure; the eventually-committed pair never shows a `SUCCEEDED` outcome that was later silently corrected. |
| Evidence interruption: Markdown temp written, JSON temp not yet started | Fake filesystem crashes after the Markdown temp write completes but before the JSON temp write begins (closes independent-review finding G5-1). | A recovery/postflight pass recognizes the lone Markdown temp file as provisional garbage, never evidence, and never pairs it with an unrelated leftover temp file from a different `run_id`. |
| Evidence interruption: validated but not yet renamed | Fake filesystem crashes after a provisional artifact (Markdown, or JSON including its `commit_state="FINAL"` content) is fully written and validated, but before that file's own rename. | The not-yet-renamed file remains only a provisional artifact and is never treated as evidence. |
| Evidence interruption: before either rename | Fake filesystem crashes after both provisional artifacts are fully written and validated but before either rename. | No final-path file is ever treated as evidence; a recovery/postflight pass recognizes the temp files as provisional garbage, not a result. |
| Evidence interruption: after Markdown rename only | Fake filesystem completes the Markdown rename (step 4) but crashes before the JSON rename (step 5). | The state is detected as non-authoritative (no commit record exists, `commit_state` cannot be read as `FINAL` from any final-path JSON); it is never reported as `SUCCEEDED` or as a valid pair, even though the Markdown's `run_id`/`evidence_id` are already readable. |
| Evidence interruption: before/after commit point | One case crashes immediately before the JSON rename in step 5; a second case crashes immediately after it completes. | Before: pair remains non-authoritative, identical to the prior case. After: pair is authoritative under the full validity rule and a simulated subsequent crash does not change that; the commit point alone determines authority. |
| Evidence interruption: second-postflight failure after commit | Fake pair is committed (JSON rename in step 5 succeeds, `commit_state="FINAL"`) as `SUCCEEDED`, then a fake second-postflight check (after commit) reports an unexpected artifact or hash mismatch. | The committed pair's bytes are never rewritten; the run is quarantined (incident record notes both files' safe identities and the discrepancy) and reported `FAILED` with the postflight-failure code, without altering the committed files. |
| Evidence rollback/quarantine failure | Fake filesystem fails the removal/move step itself during rollback or quarantine (for example after an interruption above). | Overall run status is `FAILED`; incident fallback truthfully records the exact residual artifact(s) rather than claiming a clean fallback-only state. |
| Evidence identity mismatch | Fake Markdown and JSON are constructed with mismatched `run_id` or `evidence_id` values, or a JSON whose `commit_state` is `PROVISIONAL` (or absent) despite existing at its final path. | The pair fails the validity rule and is never reported as authoritative, even though both files exist at their final paths. |
| Redaction: allowlisted-key values | Fake dependency version, GPU SKU, or prompt-source identity carries a sentinel prompt/raw-output/path/URL/token/credential/transcript/exception-text/cache value inside an otherwise-allowlisted key. | Sentinel is stripped or rejected; an allowlisted key does not excuse an unsafe value. |
| Redaction: extra keys | Fake result or fake manifest injects an extra/unlisted key carrying a sentinel value. | Extra key is dropped, not merged, in both evidence files. |
| Redaction: both evidence files | Sentinel values are present in fakes feeding both the JSON and the Markdown writer. | Neither file contains the sentinel; the Markdown writer is checked independently of the JSON allowlist check. |
| Redaction: incident fallback | Sentinel values are present in fakes feeding the incident-fallback writer specifically. | Incident content contains no sentinel; the incident writer enforces redaction independently rather than being assumed safe by construction. |
| Evidence cardinality | Evidence writer is exercised for pre-adapter, adapter-input, one-attempt, and two-attempt outcomes. | JSON/Markdown agree on `0/null`, `1/0`, `1/1`, or `1/2` once committed (step 5); no V2/Raw claim exists for `0/null`; the committed pair's `run_id`, `evidence_id`, `commit_state="FINAL"`, and content-hash linkage are all exact. |
| Evidence-write incident | Fake writer cannot reach the authoritative committed state (step 5 never succeeds), with no prior partial commit. | Only the ignored incident fallback is attempted; it is unindexed, sanitized, and does not fabricate call/attempt values. |
| No live execution | All tests use injected fakes and guarded imports/call seams. | No provider, model, model-weight, GPU, Lightning, network, or real generation-subprocess execution occurs. |

The tests must also assert that timeout, cap, overflow, malformed output, policy rejection,
mapper failure, permanent runtime failure, model-load failure, and device failure cannot cause
an additional adapter call or an unauthorized retry.

## Required staged governance sequence

The package is complete for owner review only. The following sequence is mandatory and
sequential:

1. The project owner approves the exact two-file implementation scope above, including each
   file's responsibilities and the prohibition on changing the FEAT-003 adapter.
2. The approved implementation is created and tested offline with injected fakes only. This
   stage does not use a model, provider, network, GPU, Lightning, or real subprocess.
3. An independent code review examines bounded raw output and IPC, stdout/stderr sinks,
   killable per-attempt timeout, total adapter cap, cardinality, cleanup, placement, prompt
   hash, redaction, evidence writing, incident fallback, and postflight.
4. A separate owner approval resolves `P2T2-LIVE-D1` through `P2T2-LIVE-D12` against the
   reviewed implementation, and names the exact runtime source commit, fixture, prompt,
   hardware, budget, redaction rules, and future evidence pair.
5. Only after stages 1–4 pass may an operator open Lightning and run the single approved
   smoke test. The smoke test is not a benchmark, production approval, semantic-safety
   result, quality evaluation, or P2-T2 closure.

## Unresolved owner decisions for the later live approval

All twelve identifiers below belong to the live plan. None is resolved by the existing
offline approval or by this draft. The later live approval must record concrete values and
observable acceptance evidence; “reasonable”, “available”, “unchanged”, or an implicit
default is not a resolution.

| Decision | Owner decision still required |
|---|---|
| `P2T2-LIVE-D1` — runner/deadline | Approve the implemented bounded runner identity and source commit, prove a killable 120-second deadline per generation attempt covering load/generation/decode, and prove bounded IPC/streams. The two existing runners remain disqualified as described above. |
| `P2T2-LIVE-D2` — TTL/budget | Set positive `session_ttl_seconds` and `total_adapter_cap_seconds`, plus an exact numeric GPU-minute and/or currency cap. Define the first-cap action as terminate session and mark failed; no cap resets or retry. |
| `P2T2-LIVE-D3` — ASR | Select `ASR_EXCLUDED` with `asr_execution=false`, `asr_result=null`, and `narration_status=NOT_SUPPLIED`, or obtain a separate P2-T3 approval. This package does not combine ASR with the smoke. |
| `P2T2-LIVE-D4` — model-weight staging | Select exactly one pre-staged local snapshot or separately approved one-time download. Record revision verification and download policy; any approved load/download remains inside the runner's 120-second attempt boundary. |
| `P2T2-LIVE-D5` — evidence indexing | Select indexing only after independent review, or hold for a named P2 batch. No evidence index update is authorized by this package. |
| `P2T2-LIVE-D6` — fixture | Name exactly one owner-reviewed, non-sensitive JPG/PNG, its fixture/source identity, review reference/date, MIME, dimensions, source SHA-256, and reused-Cohort-B versus newly reviewed status. |
| `P2T2-LIVE-D7` — prompt | Name the exact prompt protocol/source identity, approved SHA-256, and explicit builder/injection. Require the in-memory UTF-8 hash check immediately before the one adapter call; never record prompt text. |
| `P2T2-LIVE-D8` — staging | Select one approved session-relative mount, copy, or upload method, with logical derived reference and pre/post digest checks. The original remains immutable. |
| `P2T2-LIVE-D9` — output/IPC/streams | Set exact positive raw-output and IPC-envelope byte ceilings, exact non-negative stdout/stderr ceilings, the enforcement phase/component, and `TERMINATE_AND_MARK_FAILED` on overflow. |
| `P2T2-LIVE-D10` — hardware/placement | Set exact accelerator tier, GPU SKU, device count/index, minimum and observed VRAM, CUDA, driver and BF16 requirements, plus single-device visibility or post-load model/input placement proof. |
| `P2T2-LIVE-D11` — harness/session identity | Approve the exact two-file boundary and later reviewed source commit; record the safe opaque synthetic session-ID rule. It is not a production session, path, URL, token, or credential. |
| `P2T2-LIVE-D12` — content policy | Select `USE_LEXICAL_REGRESSION_FUNCTIONAL_ONLY` with the exact existing class/factory and versions, and record only the policy result without matched text. It is not semantic-safety, model-quality, or production-moderation evidence. |

The implementation-stage approval and the later live-execution approval are separate gates. In
particular, approving the two files cannot resolve fixture, prompt, hardware, TTL/budget,
model-weight, evidence-indexing, or policy decisions, and cannot authorize Lightning.

## Preserved exclusions

This package preserves every exclusion in the live plan:

- No FEAT-017 remote HTTPS adapter or `LightningVisionAdapter`.
- No FEAT-003 code, schema, prompt, profile, dependency, fixture, runner, scoring,
  benchmark, historical evidence, or adapter modification. `qwen_vision.py` remains read-only.
- No ASR/Whisper or P2-T3 narration execution; narration requires its own approval.
- No mobile code, mobile build/transport, mobile credentials, or Lightning credentials or
  endpoints in mobile.
- No Gate A UI, adult confirmation/correction, `P1ContextV1`, eligibility,
  `ActivityTemplateV1`, P1 filtering, fit computation, or Gate B.
- No P2-T4 pilot diagnostics, P2-T5 full evaluation, provider benchmark, p50/p95 benchmark,
  quality, semantic-safety, or production-moderation claim.
- No P3 renderer/assets or P4 provider/media/cache/fallback work.
- No shared session, idempotency, gallery, feedback, handoff, API, queue, production,
  cloud, Runpod, or public-contract integration.
- No model-weight download, provider/network call, GPU use, Lightning session, live adapter
  invocation, or live execution under this documentation task.
- No file outside the exact two proposed implementation/test paths may be added as part of
  the future implementation approval. This draft itself does not authorize either path.
- No change to `TASK_APPROVAL.md`, `CONTEXT.md`, `DECISIONS.md`, the plan, the evidence index,
  fixtures, registry, route, or any other worktree. No commit, push, branch switch, reset,
  rebase, merge, or delete.

One future smoke run is functional boundary evidence only. It is not a benchmark, production
approval, model-quality result, semantic-safety result, or closure of P2-T2. Live execution
and any downstream closure remain separately gated.

## Package acceptance and handoff

This package is acceptable for owner review when:

- the exact two proposed paths are clearly listed and neither exists or is populated;
- the source-grounded adapter/retry compatibility contract table names the exact existing
  seam, confirms which component owns retry, states the sole failure classification allowed
  to trigger attempt 2, and marks every claim the committed source cannot support as a wrapper
  responsibility rather than proven existing behavior;
- a separate `Feat018AdapterCallSupervisor` independently supervises the complete
  `QwenVisionAdapter.understand()` invocation — including hangs before the first `generate()`
  call and after the last one returns, not only the per-attempt generation child — enforces its
  own absolute deadline as the sole hard authority via its own externally-enforced wait loop, so
  the run is bounded even if the worker never reads its first message, uses a skewed clock, or
  ignores its advisory duration outright (the propagated duration is explicitly advisory only and
  never load-bearing), contains the adapter worker and every process it spawns behind an explicit,
  symmetric `CONTAINMENT_READY` gate on both POSIX (process group/session) and Windows (job
  object, assigned and verified before the gate is released) so the worker cannot construct the
  adapter or spawn a generation child before containment is confirmed, fails closed if the
  containment primitive itself is unavailable, targets cleanup at the stable containment
  handle rather than a reported PID so the generation child cannot become an unmanaged orphan and
  PID reuse cannot corrupt cleanup verification, bounds cleanup with no indefinite `join`/poll,
  and makes `CLEANUP_FAILED` override prior success at both levels, with offline fake cases for
  hangs before/after `generate()`, cleanup hangs, assignment failure, gate timeout, early child
  creation, a deadline-during-assignment race, worker death before release, descendant cleanup
  after worker death, a delayed first message, worker clock skew, an ignored budget, and a retry
  attempted near the deadline;
- an explicit, closed supervisor progress state machine (`ADAPTER_STARTED`,
  `GENERATION_ATTEMPT_STARTED(1|2)`, one terminal outcome, plus a formal `FROZEN` state distinct
  from `TERMINAL`) governs `attempt_count` by exactly one mechanism — a sequenced, framed event
  whose `acceptance_time` (the supervisor's own monotonic time when a complete bounded frame has
  been received and validated, not when it started arriving) is compared against the supervisor's
  own authoritative deadline with a strict tie-goes-to-freeze rule, under a closed transition
  table — with an atomic post-deadline freeze so no event queued or in flight at the deadline can
  be processed afterward, so duplicate/gapped/malformed/partial/out-of-order/late events, a
  terminal event followed by a further progress event, or an event exactly tied with the deadline
  can never change `attempt_count` or convert a failure into a success, and so an exit code, PID,
  or the worker's own uncommitted internal state is never used to infer an attempt, with
  deterministic offline tests for every rejected-event condition, the deadline tie, a frame that
  completes after the deadline, and the deadline/event race;
- retry and terminal-classification assertions exercise the real, unmodified
  `QwenVisionAdapter.understand()` with a fake `QwenGenerationRunner` and fake
  policy/config/clock — never a fake adapter or a monkeypatched retry loop — with
  `classify_transient` pinned to the adapter's approved default, confirming first-transient
  retry, second-transient termination at 2, no retry on timeout/model-load/device/
  permanent/overflow, no wrapper-internal retry, exactly one `.understand()` call per run, no
  third generation call, and an unmodified `qwen_vision.py`; fake adapters remain limited to the
  outer-supervisor edge cases;
- the byte-boundary limits are stated in encoded bytes for raw output, the full IPC frame
  (including the supervisor's own adapter-worker channel), and independent stdout/stderr, with
  parent-side framed-length validation before decoding, an explicit per-stream meaning for
  ceiling `0`, and `N-1`/`N`/`N+1`, multibyte-UTF-8, raw-pass/envelope-fail,
  malformed/truncated-frame, and child-death-during-transfer cases;
- the evidence writer follows the three-state commit protocol (provisional result, provisional
  artifacts, authoritative committed pair) rather than claiming two sequential renames are
  atomic, requires the Markdown to carry `run_id` and `evidence_id` in a fixed machine-readable
  metadata block matching the JSON exactly, publishes the Markdown companion before the JSON
  commit record, treats the JSON rename alone (with its content-level `commit_state="FINAL"`
  field) as the exact commit point, keeps a strictly one-directional hash reference (JSON holds
  the Markdown's hash; the Markdown never holds a JSON hash), quarantines rather than rewrites a
  committed pair on a later postflight failure, never publishes authoritative `SUCCEEDED` before
  cleanup and the first postflight check complete, has a crash-injection test for every transition
  including the one previously missing (Markdown temp written, JSON temp not yet started), and is
  cross-checked against the revision-5 crash-transition audit table so provisional, incomplete,
  mismatched, quarantined, and residual artifacts are each mapped to an explicit, unambiguous
  non-`AUTHORITATIVE_SUCCESS` reader verdict;
- the existing runner gap, truthful cardinality, bounded output/IPC/streams, 120-second
  per-attempt deadline, separate total cap, prompt hash, placement, redaction, and postflight
  obligations remain explicit;
- the offline test matrix uses injected fakes only and covers all required positive, real-adapter
  retry/terminal, stop, overflow, byte-boundary, malformed/truncated-frame, child-death,
  supervisor-hang/cleanup, orphan/race (kill-before-registration, concurrent child-start/deadline,
  stale PID, worker-death-before-cleanup), progress-event rejection and deadline/event-race,
  policy, mapper, cleanup, placement, redaction, evidence-interruption (including the
  Markdown-then-JSON temp-write gap), evidence-identity-mismatch, cardinality, and
  no-live-execution cases;
- the five-stage governance sequence is preserved;
- `P2T2-LIVE-D1` through `P2T2-LIVE-D12` remain open for a later live approval; and
- all live-plan exclusions and the smoke-not-benchmark/not-closure boundary remain intact.

This document is a draft owner-review package, not evidence that implementation approval was
granted. No implementation may begin until the canonical approval record explicitly authorizes
the exact two-file scope.
