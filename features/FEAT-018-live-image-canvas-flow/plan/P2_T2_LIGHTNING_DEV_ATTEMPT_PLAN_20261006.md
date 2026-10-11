# FEAT-018 P2-T2 owner-managed Lightning development attempt

Revision: A-OFFLINE-R1. Implementation approval is recorded separately before coding.
Scope: OWNER_MANAGED_STUDIO_DEVELOPMENT; offline implementation and synthetic tests only.
Owner: Person 2. Owner decision timestamp: NOT SUPPLIED (accepted by owner).

## Authority and preserved state

The owner submitted the implementation goal and approved proposal A. Review is
advisory; no independent PASS is claimed. Only the eight code/test paths and
five record paths below may be changed. No actual SSH, credentials/account,
installation, provider/model/GPU/service-network, Git, validators, commit/push,
D6, Runpod, or abandoned-runner work is authorized. Public documentation reads
are permitted. Live-plan CURRENT and its canonical sequence stay unchanged.
D1/D11 remain unresolved; live entry NOT_AUTHORIZED; runtime binding unchanged;
POSIX UNVERIFIED; security PENDING; Security S3 separate.

The five accepted snapshot pins were verified without drift before editing.
Their bounded offline acceptance, disclosed Medium malformed-JSON residual and
historical NEEDS_REMEDIATION remain historical. The prior 1104 passed / 4 POSIX
skips are not new results. New bytes require separate independent review.

## Exact writable scope (repository-relative)

Code and tests:

- backend/src/sketch2life/contracts/schemas/feat018_live_binding.py
- backend/src/sketch2life/benchmark/feat018_live_lightning_execution.py
- backend/src/sketch2life/infrastructure/ai/feat018_lightning_ssh.py
- backend/src/sketch2life/interfaces/cli/feat018_lightning_dev_attempt.py
- backend/tests/unit/test_feat018_live_lightning_binding.py
- backend/tests/unit/test_feat018_live_lightning_execution.py
- backend/tests/unit/test_feat018_lightning_ssh.py
- backend/tests/unit/test_feat018_lightning_dev_attempt.py

Records:

- features/FEAT-018-live-image-canvas-flow/plan/P2_T2_LIGHTNING_DEV_ATTEMPT_PLAN_20261006.md
- features/FEAT-018-live-image-canvas-flow/approvals/TASK_APPROVAL.md
- features/FEAT-018-live-image-canvas-flow/CONTEXT.md
- features/FEAT-018-live-image-canvas-flow/DECISIONS.md
- features/FEAT-018-live-image-canvas-flow/evidence/notes/P2_T2_LIGHTNING_DEV_ATTEMPT_OFFLINE_20261006.md

## Architecture and change from the live plan

Owner manages Studio allocation, lifetime and billing. Code owns one invocation
and its supervised resources only. Studio identity/ownership, invocation identity,
and actual Python/module/process birth/containment identity remain separate.
This development contract does not substitute task cleanup for provider release,
sealing, complete allocation observation or a GPU/currency meter.

New public host/session entries deny authorization before real effects. START
and its nonce identify a task; they are not authority. Offline paths accept
explicit synthetic I/O, clocks and adapter doubles; no default real launcher.

Native OpenSSH uses an explicitly bound binary, strict trusted host identity,
no PTY/sharing, a fixed remote command, and bounded protected JSON frames.
Arguments and private tokens never become shell syntax or published metadata.
The current SDK source reference is lightning-sdk 2026.10.1 at publishing commit
d52819aa991124c9ca0e2e4ecb38de623cc7dece; no SDK dependency is added.

The session gate serializes START and CANCEL under one lock. It claims one
invocation privately before launch, binds a private control socket, and services
bounded control polling while work proceeds. EOF, malformed/late frames,
cancellation and work expiry freeze new work and begin the same cleanup window.
Remote deadlines use only the remote monotonic clock. Reconnect/repeated cancel
cannot extend them. The host clock is a separate transport watchdog.

Existing containment, supervisor, bounded generation runner, 120-second attempt
profile, D9 capture/discard and adapter-owned transient retry rules are reused.
Progress callbacks occur only after state-machine acceptance. Worker validates
the actual concrete V2/Raw variants, correlation/source/model/profile provenance,
Gate A and narration invariants; only closed verification metadata leaves it.
Whole results, labels/text, raw output and private tokens do not cross the wire.

Cleanup proof requires independently supplied trusted birth/containment coverage
and observations. PID/PGID absence is insufficient. Reuse, escaped/omitted
descendants, stale observations, supervisor loss and missing proof retain
ownership and report UNKNOWN/FAILED. Successful proof covers invocation only.

## Acceptance criteria

AC1: Public denial is zero-effect and no identity/START flag opens live access.
AC2: Protected model_validate_json ingress; closed bounded frames, strict trust,
fixed command, private exclusive claim/socket and no duplicate invocation.
AC3: START/CANCEL race is authoritative; bounded multiplexing services EOF/cancel;
one work deadline and one cleanup window never reset or cross clock domains.
AC4: Exact trusted registration/inspection coverage; every ambiguity retains
ownership, no PID-only or producer-flag proof, no Studio/provider release claim.
AC5: Actual worker V2/Raw validation and metadata-only summary; accepted counts
only, existing retry/D9/privacy and cleanup precedence preserved.
AC6: Full permitted binding/execution/SSH/dev-attempt/Qwen/Raw offline suites
run in the existing venv with fake I/O/clocks, finite fixtures, no model processes,
bytecode/cache disabled and private temporary fixtures. POSIX skips UNVERIFIED.
AC7: Record actual results, failures corrected, limitations and final identities;
preserve unrelated bytes/record prefixes and hand off for independent review.

## Verification and handoff

Tests are authorized by the submitted goal, not by implicit workflow inference.
Use python -B -m pytest -p no:cacheprovider with PYTHONDONTWRITEBYTECODE=1.
Exact suite paths and actual results belong in the listed evidence note. Do not
run linters, validators, Git or actual SSH/model/provider processes. Advisory
review may guide corrections but cannot become independent PASS.
Fresh Studio/account/SSH trust/runtime/containment/disconnect/cancellation and
billing proof remain UNBOUND. No installation or runtime calibration is included.

## A-OFFLINE-R2 — Batch A independent-review correction

Status: narrow offline remediation addendum to A-OFFLINE-R1; implementation is
authorized only after the matching Person 2 approval is appended to
`approvals/TASK_APPROVAL.md`. Owner decision timestamp: NOT SUPPLIED, explicitly
accepted. The recorder timestamp is recorded separately in the approval and
evidence records.

The correction is limited to findings F1-F4 in the scoped independent review.
Only these code/test paths may change in this addendum:

- `backend/src/sketch2life/infrastructure/ai/feat018_lightning_ssh.py`;
- `backend/src/sketch2life/interfaces/cli/feat018_lightning_dev_attempt.py`;
- `backend/tests/unit/test_feat018_lightning_ssh.py`; and
- `backend/tests/unit/test_feat018_lightning_dev_attempt.py`.

No other code/test path may change. Only this plan, `approvals/TASK_APPROVAL.md`,
`CONTEXT.md`, `DECISIONS.md`, and
`evidence/notes/P2_T2_LIGHTNING_DEV_ATTEMPT_OFFLINE_20261006.md` may be updated
as records. Preserve the A-OFFLINE-R1 text and record prefixes.

### F1 — idle polling does not consume the received-control cap

Count received controls against `MAX_CONTROL_POLLS`, not timed idle polls. Keep
all wire/frame/stdio caps, the absolute work and cleanup deadlines, and finite
anti-spin behavior when an empty poll returns immediately while the monotonic
clock is frozen. Through `OfflineDevAttemptCoordinator` and the actual
`run_bounded_adapter_call` supervisor, a blocking-idle fake must demonstrate
more than 1024 timed idle polls without truncating a 120-second generation
attempt or a valid adapter-owned transient retry. Work expiry and received
control-frame overflow must still freeze. Immediate empty polls under a frozen
clock must terminate finitely. Existing assertions remain intact.

### F2 — invalid secondary control cannot redirect primary lifecycle frames

On every invalid secondary identity or rejected control/gate path, clear stale
reply ownership before freezing. READY, PROGRESS, VERIFICATION, and TERMINAL
remain on the primary invocation channel and retain its accepted sequence.
Valid secondary STATUS and CANCEL responses remain directed to their requesting
secondary peer. A wrong-identity secondary received during work must freeze
admission; TERMINAL must reach the primary with the correct sequence and must
not be delivered to the secondary.

### F3 — invalid post-START OPEN and INSPECT freeze work

After START has been accepted, OPEN and INSPECT are invalid controls and must
freeze admission with `CONTROL_INVALID`. They must not be ignored, start another
adapter invocation, or yield success. Accepted progress/attempt counts remain
unchanged and ownership stays retained until cleanup proof. Preserve
`START_REUSED` for repeated START and the existing STATUS, CANCEL, and EOF
semantics. Test OPEN and INSPECT separately through the bounded coordinator.

### F4 — OpenSSH binding paths reject expansion syntax

Reject `%`, `$`, and `~` in each of `binary_path`, `identity_file`, and
`known_hosts_file`; never expand, normalize, or resolve such input into an
accepted binding. Add token, environment-variable, and tilde negative cases for
each field plus valid absolute-path controls. Keep the fixed SSH options,
private diagnostics, and public zero-launch denial unchanged.

### Verification and preserved boundaries

Run the focused F1-F4 regressions and all ten complete suites listed in the
pinned R1 evidence note, from the existing backend virtual environment, with
`PYTHONDONTWRITEBYTECODE=1`, `-B`, pytest cache disabled, and private synthetic
fixtures. Record actual commands, results, skips, and final file identities.
POSIX process-group and AF_UNIX behavior remains UNVERIFIED when skipped.

Do not change schemas, the bounded execution source/tests, the binding wrapper,
the canonical live plan, or the historical five-file acceptance snapshot.
Preserve its disclosed malformed-TypeAdapter-JSON Medium and historical
`NEEDS_REMEDIATION`; do not expand scope for Info I1-I6. This correction and its
offline tests do not establish provider, Studio, account, runtime, remote
cancellation, remote cleanup, billing, or POSIX capability; they provide no
independent PASS or new-byte owner acceptance. D1/D11 remain unresolved,
runtime binding unchanged, live entry NOT_AUTHORIZED, security PENDING, S3
separate, and the old runner ABANDONED.

## A-OFFLINE-R2 implementation and verification record - 2026-10-07

The approved four-path offline correction batch is implemented. F1 now counts
received controls against the frame cap while timed idle polls are bounded by
the existing absolute work/cleanup deadlines; only repeated empty polls with no
clock progress consume the finite anti-spin allowance. F2 clears secondary
reply ownership on invalid control paths, so lifecycle terminal frames return
to the primary peer; valid secondary STATUS/CANCEL responses remain supported.
F3 freezes post-START OPEN/INSPECT with CONTROL_INVALID. F4 rejects %, $ and ~
in each bound OpenSSH file path without expansion or normalization.

The targeted regression selection passed 16 tests. The ten complete approved
suites collected 1506 tests and finished with 1502 passed, 4 POSIX-only skips,
0 failures. The real bounded supervisor regression passed a 120-second second
attempt after the first accepted attempt, with more than 1024 timed idle polls.
Work expiry, received-frame overflow, frozen-clock anti-spin, invalid secondary
identity routing, both invalid post-START controls, and all nine path-expansion
field/character combinations were exercised offline.

This is author-side implementation/test evidence for fresh independent
re-review. It is not independent PASS, technical/reviewer closure, or owner
acceptance of current bytes. The historical five-file acceptance and its
disclosed Medium malformed-JSON residual are unchanged. Exact commands, skips
and final four code/test identities are recorded in
`evidence/notes/P2_T2_LIGHTNING_DEV_ATTEMPT_OFFLINE_20261006.md`. POSIX remains
UNVERIFIED; D1/D11 unresolved; live entry NOT_AUTHORIZED; runtime binding
unchanged; security PENDING; S3 separate; old runner ABANDONED.

## A-OFFLINE-R3 - Remaining F2 lifecycle routing correction

Status: scoped offline correction; code changes begin only after the matching
Person 2 approval below is recorded in approvals/TASK_APPROVAL.md against the
measured revised plan identity. Owner decision timestamp: NOT SUPPLIED.
Recorder time is separate. Preserve every preceding record byte as a prefix.

The supplied R2 independent review retains F2 as Low and NEEDS_REMEDIATION;
F1/F3/F4 are closed only for that offline review. Its overflow and concurrent
primary-EOF reproductions supersede the earlier R2 author claim of complete
F2 coverage. This correction supplies no independent PASS or new-byte acceptance.

Only these code/test paths may change:

- backend/src/sketch2life/interfaces/cli/feat018_lightning_dev_attempt.py
- backend/tests/unit/test_feat018_lightning_dev_attempt.py

Only this plan, approvals/TASK_APPROVAL.md, CONTEXT.md, DECISIONS.md, and
evidence/notes/P2_T2_LIGHTNING_DEV_ATTEMPT_OFFLINE_20261006.md may change as
records. No new report or other implementation/test artifact is authorized.
Before edits, verify the full combined R2 eight-file snapshot, the supplied
source/test/plan/evidence pins and historical record prefixes. Preserve and
report any unknown or mismatched source changes before editing.

### R3 acceptance criteria

R3-AC1: Every lifecycle send targets the primary invocation peer even when
secondary reply ownership remains after a rejection, no-reply exit or exception.
Only valid STATUS/CANCEL_ACK replies may use the secondary requester. Preserve
primary and per-secondary sequence domains; do not clear the valid CANCEL peer
in _freeze, which runs before CANCEL_ACK. Preserve failure precedence, counts,
wire/frame caps, work/cleanup deadlines and retained ownership semantics.

R3-AC2: A deterministic socket-double regression drives OPEN/START, 1022 valid
secondary STATUS controls, then wrong-identity STATUS. Received count 1025
must freeze with FRAME_LIMIT before identity handling; primary receives
READY(0)/TERMINAL(1), secondary receives only STATUS replies, never TERMINAL.

R3-AC3: Primary EOF and a secondary wrong-identity control in the same poll
must not redirect TERMINAL. Cover primary delivery and BrokenPipe failure.
When primary delivery fails, report transport uncertainty, retain original
supervisor result/ownership and never fabricate delivery or choose another peer.

R3-AC4: Valid secondary CANCEL receives CANCEL_ACK(0), followed by primary
TERMINAL(1). Exercise surrounding stale-reply rejection/exception paths and
lifecycle frame kinds without leaking frames or losing primary sequence.

R3-AC5: Preserve closed F1/F3/F4 tests and I1-I6 limitations. Run focused R3
regressions and all ten complete offline suites already listed in the existing
evidence note, using the existing venv, python -B -m pytest (never pytest from
stdin), PYTHONDONTWRITEBYTECODE=1, pytest cache disabled, and private finite
synthetic fixtures. Record actual commands/results/skips and final identities.
POSIX skips remain UNVERIFIED. Routine in-scope test helper errors may be fixed
without weakening tests or changing production caps.

R3-AC6: Record the supplied review's independence/procedure disclosures,
including its preliminary out-of-scope read-only Git status. R3 does not
retroactively authorize that action. Implementation assistance in this batch
is not independent re-review. Preserve exact historical offline acceptance,
1104 passed / 4 POSIX skips, disclosed unfixed malformed-TypeAdapter-JSON
Medium, protected model_validate_json ingress and historical NEEDS_REMEDIATION.

No Git/validators, actual SSH, credentials/account, SDK install/import,
provider/model/GPU/service-network, D6, commit/push, live action, Runpod or
abandoned-runner action. D1/D11 unresolved; live NOT_AUTHORIZED; runtime binding
and canonical live-plan CURRENT unchanged; security PENDING; S3 separate;
old runner ABANDONED. Finish the authorized fix/tests/records and hand off for
fresh independent re-review of the exact final bytes.

## A-OFFLINE-R3 author implementation and verification - 2026-10-07

The approved F2 correction adds exactly two lines at coordinator _send: every
kind except STATUS/CANCEL_ACK discards pending reply ownership before sequence
selection. All coordinator output uses this single send boundary. Valid
secondary replies and _freeze remain unchanged; no counters, caps, failure
precedence, deadlines or ownership calculation changed.

Twenty-one appended synthetic regression cases passed (85 deselected, 0 failed,
1.33 seconds). They cover exact count-1025 overflow, simultaneous EOF with
successful/failed primary delivery, valid secondary CANCEL, nine surrounding
stale-reply fault paths, all six lifecycle kinds and two-secondary sequence
domains. All ten complete approved suites passed: 1523 passed, 4 POSIX-only
skips, 0 failed, 105.27 seconds. No pytest-from-stdin invocation was used.

The source is 60778 bytes, SHA-256
bee746126b5e3d8bfd0bac3bd019b01ad8ebf999c98687fdc4ebdad4ab4b2c09.
The test is 67582 bytes, SHA-256
245f8d9199a929ca13f2a06f98936218f189d704551a7077cad596c861c99c65.
The entire 54827-byte R2 test prefix is unchanged. Removing the two new source
lines in memory reproduces the exact R2 source pin. Six other combined R2
source/test pins remain unchanged; no backend/src or backend/tests path was
added or removed. Exact commands, skips and disclosures are in the existing
evidence note. R3 approval binds the 16453-byte pre-code plan prefix, not this
later author execution append.

This completes author-side R3 work for fresh independent re-review only.
The supplied R2 review remains NEEDS_REMEDIATION with F2 Low; no independent
PASS, reviewer closure or acceptance of these new bytes is claimed. Its
out-of-scope preliminary Git read remains disclosed and is not retroactively
authorized. I1-I6, the unfixed malformed-TypeAdapter-JSON Medium and historical
five-file acceptance remain unchanged. POSIX UNVERIFIED; D1/D11 unresolved;
live NOT_AUTHORIZED; runtime binding/CURRENT unchanged; security PENDING;
S3 separate; old runner ABANDONED. No prohibited live or external action.
