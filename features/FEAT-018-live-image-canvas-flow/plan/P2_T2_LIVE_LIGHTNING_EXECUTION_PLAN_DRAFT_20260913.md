# FEAT-018 P2-T2 live Lightning execution plan - draft

STATUS: DRAFT
NOT AN APPROVAL
NOT AN IMPLEMENTATION AUTHORIZATION
NOT A LIVE EXECUTION AUTHORIZATION

Date: 2026-09-16

This document is a plan correction only. Reading or revising it performs no
Lightning, GPU, model, provider, network, subprocess, or benchmark execution.
It does not change code, contracts, prompts, profiles, approvals, evidence,
fixtures, or runtime configuration. A future live run requires a separate
owner-approved addendum that names the reviewed runtime-code commit, the
externally supplied approval-record checkout commit, fixture, prompt, runner,
hardware, budget, redaction rules, and evidence paths.

The live decision identifiers in this document are owned by this plan and are
exactly P2T2-LIVE-D1 through P2T2-LIVE-D12. They are not P2-T1 decisions and
must not be recorded or described as P2-T1 decisions. The status table in
Section 9 records planning disposition only; no live decision is finally
approved by this draft.

The provenance labels below preserve historical/offline roles. The separate
owner binding below identifies the exact reviewed source/test blobs; it is not
a live-execution approval:

- `c2bd7b5` = `HISTORICAL_PRIMITIVE_PROVENANCE_ONLY` (full commit
  `c2bd7b5ece3f308abb65ab3632add265b3cd586c`); it identifies the original
  bounded-runner primitives and their tests.
- `7f5cbe5` = `VALIDATED_OFFLINE_CORRECTION_PROVENANCE_ONLY` (full commit
  `7f5cbe57fc9756c3e7fa5c248cd655c1dce0ec7b`); it identifies the validated
  offline coordinator/evidence correction.
- `9549a34` = `POSIX TEST CORRECTION PROVENANCE ONLY` (full commit
  `9549a341194f40b1a9be419d6fce0d70f1ca0384`); it identifies the POSIX test
  correction only.

`reviewed_runtime_code_commit` =
`9549a341194f40b1a9be419d6fce0d70f1ca0384`, owner-bound as the exact reviewed
FEAT-018 P2-T2 runner/coordinator source and test blob identity only. This
binding does not resolve D4, all D1-D12, Stage 4, or live execution. The
approval checkout must still verify this exact commit or the exact reviewed
blobs before any future model invocation.

The verification/closure documentation commit is
`8522e2cd830a8fce49759a385dca99c2906ba120`; it records the completed
offline primitive review/finding closure and validation. The independent review
is a separately identified local artifact, not a commit:
`tmp/feat018-p2-t2-launcher-independent-review-20260914/REVIEW.md`, SHA-256
`5b863dbb2fafb33ccec7ecfee82424b80de40d304cf45396f72470f908328d2e`.
The finalization report is likewise a local artifact:
`tmp/feat018-p2-t2-launcher-finalization-20260914/REPORT.md`, SHA-256
`662589c8af7222d9922dfe48d83908952bd5e0dc0381f780dfa81534ce9e266a`.
Neither local artifact hash is a commit identifier.

The POSIX test correction and the offline coordinator implementation are
verified offline. The owner-bound reviewed runtime commit identifies the exact
source/test blobs only; it is not a live authorization and does not resolve D4,
all D1-D12, or Stage 4. References to the provenance commits below describe
offline history only and cannot authorize any other source bytes.

Planning baseline only: repository HEAD observed for this reconciliation was
`2832455e7cb314cea0fa64a397fbbb84ac914df1` (a documentation commit). That hash
is not an execution authorization or a live runtime identity. A future owner
approval must receive an externally supplied
`approval_record_commit` after the approval record is committed. The approval
file must never contain its own future commit hash; the execution checkout
must verify that externally supplied commit before any model invocation.

## Canonical reconciliation state (2026-09-16)

- Offline coordinator implementation: COMPLETE
- Offline independent/POSIX verification: COMPLETE WITH FINDINGS CLOSED
- Live coordinator source/test binding: OWNER-BOUND; runtime suitability pending
- P2T2-LIVE-D1: BLOCKED
- P2T2-LIVE-D4: BLOCKED
- P2T2-LIVE-D11: BLOCKED
- Stage 4 live-execution approval: NOT READY
- Lightning execution: NOT AUTHORIZED
- Live model/GPU/provider/network execution: NONE

The coordinator is implemented and verified offline, and the owner has bound
the reviewed source/test identity. Live-runtime suitability,
session/controller binding, and D1/D4/D11 remain pending. The current HEAD is
a planning/documentation identity only and is not the reviewed runtime source
commit. This state does not open Stage 4 or authorize Lightning.

Next sequence:

`revised plan -> independent binding review -> owner-bound reviewed runtime commit -> D4 snapshot verification -> owner resolution of D1-D12 -> separate Stage 4 approval -> only then Lightning execution`

## 1. Objective and exact scope

The proposed future smoke run is exactly one owner-approved, non-sensitive
JPG/PNG image through the existing backend-only FEAT-003
VisionUnderstandingResultV2 boundary and the existing qwen_vision.py
QwenVisionAdapter, followed by the existing FEAT-018
map_vision_result_to_raw mapper. The run records one typed V2 outcome and one
mapped RawUnderstandingResultV1 outcome, or a typed terminal outcome if a
stop gate fires.

The run records truthful cardinality at the phase boundary; it never fabricates
a call or attempt:

- A stop before invoking the adapter records `adapter_call_count=0` and
  `attempt_count=null`. This includes approval, checkout, fixture, readiness,
  configuration, policy, hardware, manifest, and runner-boundary stops. No V2
  result, Raw mapping, or adapter timing is claimed for this path.
- If the adapter is invoked but rejects the input before model generation, it
  records `adapter_call_count=1` and `attempt_count=0`. This is the existing
  typed input-validation path and is not a model-reaching functional pass.
- A model-reaching adapter call records `adapter_call_count=1` and
  `attempt_count` in `{1, 2}`. Attempt 2 is permitted only after an explicitly
  classified transient runtime failure on attempt 1, inside the one adapter
  call. It never becomes 3 and there is no outer retry.

Every authorized run attempt writes exactly one sanitized JSON/Markdown
evidence pair, including a pre-adapter terminal outcome. If evidence creation
is impossible, the harness writes only a safe local ignored incident record at
`tmp/feat018-live-lightning-incident-<run_id>/INCIDENT.md`; that incident is not
indexed and never substitutes fabricated call or attempt values.

The future run uses exactly the owner-approved runner boundary from
P2T2-LIVE-D1. It does not rely on a constructor default.

In scope:

- The existing FEAT-003 V2 profile
  QWEN3_VL_8B_INSTRUCT_BF16_V1 from vision_profile_catalog_v2().
- The existing local Qwen adapter in
  backend/src/sketch2life/infrastructure/ai/qwen_vision.py, read-only.
- The existing QwenVisionRuntimeConfig, no-model-load environment readiness
  inspection, and typed content-policy boundary, read-only.
- The existing FEAT-018 mapper and RawUnderstandingResultV1 contract, read-only.
- One exact source image, its immutable source identity, its staged
  session-local reference, and the source SHA-256 relationship.
- One Lightning Studio GPU session, subject to the exact TTL and budget
  decision in P2T2-LIVE-D2.
- One sanitized feature-local evidence pair at the exact paths in Section 7,
  created only after a later execution approval.

The V2 profile is consumed exactly as currently defined:

- model identifier: Qwen/Qwen3-VL-8B-Instruct;
- model revision: 0c351dd01ed87e9c1b53cbc748cba10e6187ff3b;
- profile timeout_seconds: 120.0;
- adapter version: qwen3-vl-local-adapter-v2-b1;
- greedy decoding with sampling_enabled=false, beam_count=1,
  repetition_penalty=1.0, seed=0, and max_new_tokens=512;
- image preprocessing identity: qwen3-vl-processor-config-b1;
- exact dependency pins: accelerate==1.10.1, qwen-vl-utils==0.0.14,
  torch==2.8.0, and transformers==4.57.6.

The V2 result is mapped into FEAT-018's already-closed
RawUnderstandingResultV1 contract. The mapper receives the approved synthetic
smoke-session identifier, the staged source digest, the request correlation
ID, and asr_result=None. The mapped envelope therefore retains
gate_a_required=true and narration_status=NOT_SUPPLIED without fabricating
adult confirmation, narration, eligibility, or personality information.

Out of scope and preserved exclusions:

- FEAT-017's remote HTTPS adapter and LightningVisionAdapter; this plan uses
  only the local qwen_vision.py adapter boundary.
- Any FEAT-003 code, contract, prompt, profile, dependency, fixture, runner,
  scoring, benchmark, or historical-evidence change.
- ASR/Whisper execution is excluded from this plan. The image-only smoke run
  assumes ASR_EXCLUDED, subject to the owner's explicit resolution of
  P2T2-LIVE-D3. If the owner wants live narration, this plan remains blocked
  and a separate P2-T3 ASR approval is required.
- Mobile code, mobile builds, mobile transport, mobile credentials, and
  Lightning credentials or endpoints in mobile.
- Gate A UI, adult confirmation/correction, P1ContextV1, eligibility,
  ActivityTemplateV1, P1 filtering, fit computation, or Gate B.
- P2-T4 pilot diagnostics, P2-T5 full evaluation, provider benchmark work,
  p50/p95 benchmark reporting, quality scoring, and production moderation
  claims.
- P3 renderer/assets and P4 provider/media/cache/fallback work.
- Shared session, idempotency, gallery, feedback, handoff, API, queue, or
  production integration.
- Any live execution before a separate approval has resolved
  P2T2-LIVE-D1 through P2T2-LIVE-D12.
- Any new production code, glue code, CLI, wrapper, test, evidence writer,
  approval mutation, commit, or push under this draft.

## 2. Topology, ownership, and explicit construction boundary

The target topology, which remains subject to live suitability checks and future
live approval, is:

```text
Host-side run_live_smoke()
  -> approved LightningSessionController
      -> Lightning session
          -> Feat018AdapterCallSupervisor
              -> adapter worker
                  -> generation child
```

The outer worker is released only after containment is confirmed. The inner
generation child is created only after the worker accepts `CONTAINMENT_READY`.
The runner never retries internally; the unchanged Qwen adapter owns its
explicit transient-only second-attempt decision. `attempt_count` is derived
only from progress events accepted by the supervisor state machine, never from
an uncommitted worker counter or from a planned call.

FEAT-003 remains the owner of the V2 schemas, profile catalog, model runtime,
prompts, and qwen_vision.py implementation. FEAT-018 consumes those inputs
without editing them. The mapper is an already-approved offline boundary; it
does not execute a model, provider, network, or storage operation.

### 2.1 Runtime configuration

The approved future harness must construct
QwenVisionRuntimeConfig explicitly from one owner-approved, session-local
configuration file. The construction boundary is exactly
`QwenVisionRuntimeConfig.from_env_file(approved_session_relative_env_file,
environ={})`; ambient process environment values must not be merged. The exact
file identity, the selected model_dir/model_cache_dir choice, device,
device_index, and allow_model_download fields are recorded under
P2T2-LIVE-D11 and P2T2-LIVE-D4/D10 before approval. In pseudocode:

    QwenVisionRuntimeConfig.from_env_file(
        approved_session_relative_env_file,
        environ={},
    )

The selected file must provide the exact
SKETCH2LIFE_VISION_MODEL_DIR or SKETCH2LIFE_VISION_MODEL_CACHE_DIR,
SKETCH2LIFE_VISION_DEVICE, SKETCH2LIFE_VISION_DEVICE_INDEX, and
SKETCH2LIFE_VISION_ALLOW_MODEL_DOWNLOAD values approved in
P2T2-LIVE-D4 and P2T2-LIVE-D10. The file is ignored runtime configuration,
never committed, and never copied into evidence. Its paths are interpreted
inside the Lightning session; a host-local Windows path is never presumed to
exist remotely.

The current no-model-load readiness checker can report READY only when its
own requirements are met, including a configured local model directory,
download disabled, a verifiable pinned snapshot revision, exact dependencies,
CUDA, BF16, and its expected NVIDIA L4 device class. If the selected
configuration cannot satisfy that checker, the future run must stop unless a
separate approval names an equivalent already-approved readiness boundary.
This plan does not authorize modifying the checker.

### 2.2 Content-policy construction

The policy must be explicitly constructed and injected at the existing port.
The exact implementation identity is
`sketch2life.infrastructure.ai.vision_lexical_policy.LexicalRegressionContentPolicy`
and the exact synthetic lexicon factory is
`sketch2life.infrastructure.ai.vision_lexical_policy.synthetic_prohibited_lexicon`:

    content_policy: ObservableContentPolicyV1 =
        LexicalRegressionContentPolicy(synthetic_prohibited_lexicon())

The resulting exact values are
`content_policy_version=vision-prohibited-lexicon-fixture-v1` and
`policy_match_view_version=vision-policy-match-view-v2`. The approved harness
passes this object as `content_policy` while constructing QwenVisionAdapter;
there is no default, alternate, unreviewed, semantic, or production policy
configuration. The exact import/factory identity, values, and synthetic
fixture/regression purpose are recorded in P2T2-LIVE-D12 and the evidence
pair. The scope limitation and owner decision are P2T2-LIVE-D12.

### 2.3 Prompt construction

The reviewed live boundary has an explicit string path, not an implicit
adapter default: `run_bounded_adapter_call` accepts `prompt`,
`adapter_worker_entry` constructs `QwenVisionAdapter(..., prompt=prompt,
generation_runner=runner)`, and `QwenVisionAdapter` installs that explicit
prompt rather than `_default_prompt_builder`. The reviewed implementation
therefore makes the empty default unreachable on this path, but it does not
itself bind the string to a protocol identity. The future approved caller must
resolve the proposed committed C1-v2 protocol below, verify the exact UTF-8
hash, reject an empty string, and pass that string through this explicit
`prompt=` path.

The future approval must name the exact owner-approved prompt protocol/source,
its prompt identity, and its SHA-256. Prompt text is kept in memory only and
is never logged or written to either evidence file. The approved harness must
inject it through the explicit `prompt=` argument; a prompt-builder default is
not acceptable.
The harness must hash the exact UTF-8 text selected for injection immediately
before the adapter invocation:

    sha256(prompt_text.encode("utf-8")).hexdigest() == approved_prompt_sha256

The comparison is an in-memory self-check; the prompt text is not persisted or
logged. A mismatch is a pre-adapter terminal with
`adapter_call_count=0` and `attempt_count=null`.
Changing or adding a FEAT-003 prompt is outside this plan and requires a
separate approval. The decision is P2T2-LIVE-D7.

### 2.4 Runner construction and timeout boundary

The reviewed implementation replaces the previously unsuitable choices for
this plan. `Feat018AdapterCallSupervisor` launches the outer adapter worker;
after the containment gate, that worker constructs the real
`QwenVisionAdapter` with `Feat018BoundedKillableQwenGenerationRunner`. Each
runner `generate()` call launches one inner generation child using the real
spawn context by default, with `daemon=False`, and bounds model/processor
loading, generation, decoding, and the result envelope. The runner performs no
retry; the unchanged adapter owns the one permitted transient retry.

The offline implementation uses the historical primitive provenance
`c2bd7b5` only. The validated offline correction provenance is `7f5cbe5`, and
the POSIX test correction provenance is `9549a34`. The owner-bound
`reviewed_runtime_code_commit` is `9549a341194f40b1a9be419d6fce0d70f1ca0384`
for source/test identity only. The coordinator is implemented and verified
offline, but live-runtime suitability and session/controller binding still
require the remaining owner gates. A later live approval must verify the exact
reviewed source commit and prove the real nested spawn, descendant containment,
and two-level cleanup assertions listed in Section 5. A model factory, the old in-process runner, the old unbounded
subprocess IPC, and persistent raw-output diagnostic sinks are not live
alternatives.

The per-attempt child deadline is exactly 120 seconds and covers loading,
generation, and decoding. A separate positive `total_adapter_cap_seconds`
covers the entire single adapter call, including a possible second attempt,
without resetting on retry. Readiness may inspect versions, hardware, and a
local snapshot without loading weights; it must not preload weights. Any model
download/load choice remains inside the future D4 approval and the child
deadline.

### 2.5 Reviewed primitives and remaining orchestration boundary

Repository conventions use feature-local, directly imported executors under
`backend/src/sketch2life/benchmark/` with focused unit tests under
`backend/tests/unit/`. The smallest proposed source/test scope is exactly:

- `backend/src/sketch2life/benchmark/feat018_live_lightning_execution.py`:
  the reviewed bounded supervisor, adapter worker, generation runner, progress
  protocol, containment cleanup, and evidence-pair writer/reader primitives.
  `run_bounded_adapter_call` accepts an already constructed request, runtime
  config, policy and prompt. It returns supervisor status. The current repair
  adds optional worker-local Raw mapping when a synthetic session ID is
  supplied, with a bounded raw_status terminal claim; V2/Raw observations
  never cross the progress channel. The coordinator is implemented and
  verified offline in this source/test boundary; live-runtime suitability and
  session/controller binding remain pending. FEAT-003
  source remains unchanged.
- `backend/tests/unit/test_feat018_live_lightning_execution.py`: offline tests
  with injected seams plus synthetic local process-boundary tests only; no
  Lightning/provider/model execution occurs. It covers raw and IPC overflow, stdout/stderr
  ceilings, per-attempt timeout and total-cap termination, child/IPC cleanup
  on success and failure, pre-adapter `0/null`, adapter input rejection
  `1/0`, model-reaching `1/1`, explicitly transient retry `1/2`, no third or
  outer retry, and evidence-pair hash/rename integrity. Prompt-hash selection,
  device placement, full evidence redaction and incident handling are covered
  by offline injected coordinator seams; live-runtime suitability and
  session/controller binding remain pending. The verification evidence is
  provenance-bound to
  the offline correction records and the separate review artifacts identified
  at the top of this plan.

No other source, wrapper, CLI, fixture, adapter edit, or test file is in the
reviewed boundary. This plan does not authorize adding a live caller or
changing either reviewed path. Any new orchestration file requires a new
exact-file-scope approval.

#### Four-finding correction scope and acceptance (2026-09-15)

The direct owner request to fix B1/B2/M1/N1 authorizes the correction recorded
in TASK_APPROVAL.md. Code changes remain within the two paths above. The
offline correction implements `Feat018EvidenceFinalizer`: mandatory cleanup,
provisional pair creation, mandatory precommit postflight/integrity validation,
then the JSON rename. A failed or exceptional gate cannot publish success.
If finalization cannot safely commit, report a typed non-committed result with
truthful residual artifacts; the future coordinator remains responsible for
supplying the approved ignored destination/preflight and invoking the sanitized
incident writer. The low-level writer remains a storage primitive, not a live
entry point or an authorization bypass.

Offline acceptance: success ordering is observed at filesystem operations;
cleanup false/exception and postflight false/exception cannot leave a valid
success pair; mutation of provisional bytes is rejected; the artifact inventory
is reverified after Markdown rename immediately before JSON rename; JSON-rename
and rollback failures remain non-authoritative and disclose residuals; failed
runtime outcome cannot be promoted; both files share the finalized outcome; no
raw exception text crosses this finalizer boundary. Postcommit reader checks are
read-only and do not change the recorded runtime outcome.

The owner-approved cleanup invariant is a quiescent single-writer boundary:
after cleanup succeeds, every supervised process and descendant is absent, no
runtime writer remains, and evidence finalization is the sole authorized writer.
The two inventory scans close the ordinary mutation window under that invariant.
They do not claim filesystem-wide atomicity or protection from an unrelated
hostile external writer, and metadata checks do not defeat timestamp restoration.

The complete coordinator is `run_live_smoke` in this same source file, with
tests in the same test file. Its offline implementation and verification are
  complete. The following responsibilities are implemented behind injected
  offline seams; live-runtime suitability, session/controller binding, and the
  D1/D4/D11 gates remain pending:

1. verify approval/checkout and complete ignored-artifact baseline;
2. construct explicit runtime config and the existing lexical policy; verify
   D4 snapshot, readiness, D6 admission/staged digest and D7 prompt hash;
3. enforce session TTL/budget and hardware placement with real observable
   dependencies, with no success-valued placeholder probes;
4. invoke the bounded adapter exactly once with the synthetic session ID;
   require accepted worker-local Raw mapping before considering success,
   using only the terminal raw_status claim and never V2 observations;
5. terminate/verify session and descendants, inspect runtime artifacts, call
   the evidence finalizer, and handle non-commit through a sanitized incident.

No manual notebook, new CLI or unreviewed caller may fill these gaps. B1 is
corrected as a planning discrepancy; live-runtime suitability and binding
remain an explicit independent-review gate. D1/D11 stay BLOCKED until that
gate closes.

The continuing owner-requested repair implements the worker mapper handoff
in the same two files. An optional synthetic session ID activates mapping
inside the gated adapter worker and inside the supervisor deadline. The
unchanged mapper checks source hash and correlation; only a closed
`raw_status` value (SUCCEEDED/FAILED) can accompany the terminal event.
The session ID is supplied in adapter-worker bootstrap arguments and may be
serialized by spawn multiprocessing, but it is bounded, opaque and non-secret;
it is excluded from progress/event IPC and evidence payload bodies. No V2/Raw
observation or free text crosses progress IPC. Legacy primitive calls without a
session ID emit no mapper claim. The future coordinator must require an accepted
raw_status matching its terminal outcome. Tests cover the real adapter/fake
generation path through the real mapper, mapper rejection, absent mapping,
malformed summary, and late-event rejection.

The same correction adds `Feat018ArtifactInventory` and
`Feat018IncidentWriter` inside the same source/test boundary. Inventory takes
explicit non-overlapping roots, uses an entry budget and metadata-only
fingerprints, rejects symlinks/reparse points/special files, and never traverses
`.worktrees`. All roots must be supplied from the future approved inventory;
an omitted root cannot be claimed audited. The writer permits only the exact
relative incident destination
`tmp/feat018-live-lightning-incident-<run_id>/INCIDENT.md`; it validates the
bounded run ID, expected filename, repository containment, traversal absence,
and link/reparse safety, and requires the future coordinator/preflight to pass
an explicit Git-ignored confirmation. Tracked, publishable, arbitrary absolute,
traversal and mismatched-run destinations are rejected. The precommit comparison
allows only the exact two provisional evidence files beyond the captured
baseline, then repeats the inventory comparison after Markdown rename. Metadata
checks detect ordinary change, not adversarial timestamp restoration;
source/fixture/prompt exact-hash checks remain distinct requirements. Incident
writing accepts only a non-committed finalization result and emits fixed status,
opaque run/evidence identities and a residual count, never raw exceptions or
paths. Failure to write the incident remains explicitly reported. Offline tests
cover additions/deletions/changes, mutation after the initial scan, the
commit-adjacent mutation check, failed quiescence, absent roots, traversal
budget, symbolic-link/reparse rejection, exact provisional-file exclusions,
incident destination rejection, and secret-bearing failure details that must not
appear in incident bytes.

`finalize_smoke_run` connects the accepted supervisor result, captured
inventory, mandatory session cleanup, finalizer and incident writer. Success
requires a matching accepted Raw success and successful process cleanup;
worker terminal diagnostics alone cannot supply it. The inventory's exact
precommit verification is wired directly, not replaced by a constant callback,
and is repeated at the JSON commit boundary. Rejected publication triggers the
sanitized incident writer; its success or failure is a separate typed result.
Integration tests inject filesystem changes after the initial scan and at the
commit-adjacent audit, exercise failed quiescence, and prove no false committed
PASS.

### 2.6 Mapper and synthetic session identity

RawResultEnvelopeV1 requires a non-empty session_id. The isolated smoke run
does not invoke shared session or idempotency orchestration, so the approved
harness must create a synthetic, opaque smoke-session identifier and pass it
to map_vision_result_to_raw. The identifier is not sourced from V2, mobile,
or a production session. It must be non-empty, at most 64 characters, use only
lowercase letters, digits, `_` or `-`, contain no path, URL, credential, or
token, and be recorded as safe metadata only. It is supplied in the
adapter-worker bootstrap arguments and may be serialized under spawn; it is
excluded from progress/event IPC and evidence payload bodies. The exact source,
format, and value-handling rule are resolved in P2T2-LIVE-D11.

The mapper call must be equivalent to:

    map_vision_result_to_raw(
        result,
        session_id=approved_synthetic_session_id,
        expected_source_sha256=staged_source_sha256,
        expected_correlation_id=request.correlation_id,
        asr_result=None,
    )

No session bridge or mapper modification is implied by this plan.

## 3. Preconditions

All of the following must be true before the Lightning GPU session starts.
The future execution approval must record each value; a statement that a
condition is "reasonable", "available", or "unchanged" is not sufficient.

1. Approval gate. A future addendum to
   features/FEAT-018-live-image-canvas-flow/approvals/TASK_APPROVAL.md says
   APPROVED for this exact live smoke scope, names all resolved
   P2T2-LIVE-D1 through P2T2-LIVE-D12 decisions, records
   `reviewed_runtime_code_commit`, and enumerates the exact two evidence paths.
   The existing offline P2-T2 approval is not live-execution approval. The
   post-approval `approval_record_commit` is supplied to the operator
   externally after the approval record is committed; the approval record
   does not contain its own future commit hash.

2. Exact reviewed code and approval checkout. The owner-bound value for
   `reviewed_runtime_code_commit` is
   `9549a341194f40b1a9be419d6fce0d70f1ca0384`, identifying only the reviewed
   source/test blobs. The offline correction coordinator/correction provenance
   is `7f5cbe57fc9756c3e7fa5c248cd655c1dce0ec7b`, and the POSIX test correction
   provenance is the same owner-bound commit; the binding is not live
   authorization. The historical primitive commit
   `c2bd7b5ece3f308abb65ab3632add265b3cd586c` is provenance only.
   After the live approval is
   committed, an external execution record supplies one exact 40-hex
   `approval_record_commit`; the execution checkout must verify
   `git rev-parse HEAD == approval_record_commit` before any model invocation.
   It must also prove zero diff for both reviewed implementation paths between
   `reviewed_runtime_code_commit` and that checkout, or prove the exact blob
   identities for both paths. A floating branch, tag, latest revision, or
   host-only assertion is invalid. The evidence records both commit identities
   without treating the approval record as self-referential.
   The two paths are exactly
   `backend/src/sketch2life/benchmark/feat018_live_lightning_execution.py` and
   `backend/tests/unit/test_feat018_live_lightning_execution.py`.

3. Clean source checkout. Before session startup, git status --porcelain is
   completely empty with no path filter, and git status --ignored --short
   matches the recorded approved ignored baseline. Any modified tracked file,
   untracked file, staged change, generated file, or unexpected/changed ignored
   runtime artifact stops the run. The Lightning checkout repeats the
   approval-record commit, reviewed-path zero-diff/blob, and clean-checkout
   verification before the adapter call. The planning checkout is never used
   as the execution checkout merely because it has the right branch name.

4. Exact fixture identity. P2T2-LIVE-D6 names exactly one owner-reviewed,
   non-sensitive JPG or PNG fixture_id, source identity, format, dimensions,
   and source_sha256. The owner review reference and whether the image is
   reused or newly reviewed are recorded. The proposed value is Cohort B
   `B01.jpg`, relative identity only, with `image/jpeg`, `1254x1254`,
   `337481` bytes, and source SHA-256
   `c60faed33034b5911e611a512dde03cc94fb21146f85dfba4ef7236268ab9cc3`.
   These facts match the local owner-review reference
   `tmp/feat018-cohort-b-input-20260912/SOURCE_REVIEW.md` dated 2026-09-12
   and `candidate-manifest.json`; the live approval must recheck the bytes
   and magic before use. No child, personal, production, or unreviewed image
   is permitted.

5. Admission and staging integrity. The exact fixture passes the existing
   P2-T1 D2 image-admission policy before a vision call. It satisfies the bounded limits of
   max_file_bytes=5000000, max_pixels=4000000, max_longest_edge=4096,
   max_frames=1, decodability, and MIME/extension agreement. The approved
   P2T2-LIVE-D8 method mounts, copies, or uploads only a derived
   session-local working reference. The original remains immutable. The
   staged bytes are hashed inside Lightning before inference and must equal
   source_sha256. The request's VisionImageReferenceV1 and the adapter's own
   _verify_image_reference check use that same digest.

6. Exact model/profile. The request uses only
   QWEN3_VL_8B_INSTRUCT_BF16_V1. The exact model identifier and revision are
   Qwen/Qwen3-VL-8B-Instruct and
   0c351dd01ed87e9c1b53cbc748cba10e6187ff3b. The pre-run record includes
   vision_profile_config_hash_v2(profile) and the catalog hash. No other
   model, revision, profile, or decoding value may be substituted.

7. Exact dependencies. The installed versions inside Lightning equal the
   profile's four exact pins: accelerate 1.10.1, qwen-vl-utils 0.0.14,
   torch 2.8.0, and transformers 4.57.6. A mismatch, missing package, or
   unrecorded extra runtime is a stop condition. If a pre-staged local
   snapshot is used, its required files and revision metadata must be
   verifiable. The profile's repository-level weight SHA-256 remains absent
   with reason SOURCE_DOES_NOT_PUBLISH_A_DIGEST; the run must not invent one.

8. Prompt and policy. P2T2-LIVE-D7 records the prompt protocol/source,
   prompt_sha256, and explicit builder injection. The proposed source is the
   committed FEAT-003 C1-v2 protocol in
   `backend/src/sketch2life/benchmark/vision_c1_prompt_mapping_study.py`,
   resolved by `C1_PROMPT_V2`/`c1_prompt_text_v2()` and injected as the
   explicit `prompt=` argument through `adapter_worker_entry`; its protocol
   identity and hash are recorded in Section 9 without copying prompt text.
   Immediately before the adapter call, the harness hashes the exact injected
   text as
   `sha256(prompt_text.encode("utf-8")).hexdigest()` and requires equality
   with the approved hash without logging or persisting the text. P2T2-LIVE-D12
   records the exact import/factory identity (`LexicalRegressionContentPolicy`
   plus `synthetic_prohibited_lexicon()`),
   `content_policy_version=vision-prohibited-lexicon-fixture-v1`, and
   `policy_match_view_version=vision-policy-match-view-v2`. An empty prompt,
   hash mismatch, missing policy, or alternate policy is a pre-adapter stop.

9. Hardware. P2T2-LIVE-D10 records the exact Lightning accelerator/SKU,
   device_count, device_index, minimum_vram_mib, cuda requirement, driver
   facts, and BF16 requirement. The observed GPU SKU, VRAM, CUDA availability,
   device count, and BF16 support are checked inside Lightning. A different,
   unavailable, or unverifiable device is a stop condition. The current
   readiness contract expects the NVIDIA_L4 device class; no prior L4
   choice is silently inherited. The boundary must also require single-device
   visibility or a post-load assertion that the model and inference inputs
   occupy the approved device index; inventory alone is insufficient.

10. Timeout and attempt policy. The profile timeout is exactly 120.0 seconds
     per generation attempt in the proposed killable runner. Its child
     deadline starts after process start and includes model loading, generation,
     and decoding in that attempt. A separate positive
     `total_adapter_cap_seconds`, recorded under P2T2-LIVE-D2, covers the
     entire one adapter call and any permitted retry without resetting. A
     timeout or total-cap terminal is never retried. Before adapter invocation
     record `adapter_call_count=0`, `attempt_count=null`; an adapter input
     rejection before model generation records `1/0`; a model-reaching call
     records `1/1` or `1/2`. Only QwenTransientRuntimeError or a generic
     exception explicitly classified transient on the first generation attempt
     may advance the latter to attempt 2. QwenModelLoadError and
     QwenDeviceUnavailableError are terminal on the first attempt and never
     trigger the internal retry. Model-load failure, device-unavailable
     failure, timeout, total-cap expiry, malformed output, policy rejection,
     mapper failure, cleanup failure, permanent runtime failure, and every
     second-attempt failure are terminal. There is no outer retry.
     The live assertion must observe the real nested spawn: the outer
     `MultiprocessingProcessLauncher` is non-daemon, the inner generation
     launcher is reached only after `CONTAINMENT_READY`, and the accepted
     progress stream contains at most one attempt-1 and one attempt-2 start.

11. Bounded output and IPC. P2T2-LIVE-D9 records the exact proposed integer
    values `raw_output_max_bytes=65536`, `ipc_envelope_max_bytes=98304`,
    `stdout_max_bytes=0`, and `stderr_max_bytes=0`, plus their enforcement
    component. The ceiling is enforced before an unbounded raw value can cross
    the child-parent boundary. A zero stream ceiling means the stream is
    disabled and any byte is a failure. stdout and stderr are either disabled or
    captured by a bounded, non-persistent sink; they may not contain prompts,
    raw model output, credentials, URLs, paths, or provider payloads. If the
    selected runner or harness cannot prove these bounds, the run stops before
   model invocation. The exact profile setting max_new_tokens=512 must remain
   recorded and unchanged, but it does not by itself prove a byte bound.

12. Runtime manifest. A sanitized runtime manifest is created inside
    Lightning after source, dependency, CUDA, driver, and GPU checks and
    before inference. The exact allowlist and canonical hash are in
    Section 3A. Any secret, absolute path, prompt, raw output, URL, credential,
    hostname, or non-allowlisted key causes a stop before evidence writing.

13. Budget and TTL. P2T2-LIVE-D2 records positive
     `session_ttl_seconds` and `total_adapter_cap_seconds`, plus at least one
     exact numeric cap: gpu_minute_cap or currency_cap. The total adapter cap
     covers both possible generation attempts; the session TTL and GPU/currency
     cap cover the broader session. If multiple caps are supplied, the first
     reached cap wins. The action at any cap is terminate the session and mark
     the run failed, including when the adapter is in flight. The caps are
     never folded into adapter timing.

14. Evidence destination and file scope. The exact date-qualified JSON and
    Markdown paths in Section 7 are absent before the run and are named in
    the future approval's exact file list. Only that pair may be created by
    the run. A tmp report, shared evidence dump, runtime config, cache,
    generated model output, prompt file, or third evidence artifact is not an
    approved destination.

### 3A. Sanitized runtime manifest

The runtime manifest is a small JSON object with only the following allowlisted
facts. It is collected inside the Lightning session; it is not a full
environment dump or pip-freeze output:

    {
      "manifest_version": "P2T2-LIVE-RUNTIME-MANIFEST-V1",
      "python": {
        "implementation": "<allowlisted interpreter name>",
        "version": "<allowlisted interpreter version>"
      },
      "dependencies": [
        {"package": "accelerate", "version": "<installed exact version>"},
        {"package": "qwen-vl-utils", "version": "<installed exact version>"},
        {"package": "torch", "version": "<installed exact version>"},
        {"package": "transformers", "version": "<installed exact version>"}
      ],
      "cuda": {
        "available": "<boolean>",
        "device_count": "<integer>",
        "runtime_version": "<allowlisted CUDA runtime fact>"
      },
      "driver": {
        "version": "<allowlisted NVIDIA driver fact>"
      },
      "gpu": {
        "device_index": "<integer>",
        "sku": "<allowlisted GPU SKU>",
        "vram_mib": "<integer>",
        "bf16_supported": "<boolean>"
      }
    }

The implementation must reject keys outside this allowlist, sort dependency
records by package, and canonicalize with UTF-8 JSON, sorted keys, compact
separators, and no hash field. runtime_manifest_sha256 is SHA-256 of that
canonical byte sequence. The evidence pair may contain the allowlisted
manifest object and its hash. It must not contain model/cache/runtime-config
paths, environment values, URLs, credentials, tokens, prompts, raw provider
output, hostnames, process command lines, or arbitrary package inventory.

The `reviewed_runtime_code_commit`, externally supplied
`approval_record_commit`, model identifier/revision, profile/config hashes,
fixture hash, and prompt hash are recorded as separate sanitized metadata;
they are not a reason to widen the runtime-manifest allowlist. The approval
record never hashes or names its own future commit as if it were already
known.

## 4. Execution phases

### Phase 0 - approval and local preflight

This phase occurs before any Lightning session and does not run a model,
provider, network call, benchmark, or live subprocess.

- Verify the future approval is APPROVED for this exact scope, resolves
  P2T2-LIVE-D1 through P2T2-LIVE-D12, and lists the exact evidence pair.
- Verify the externally supplied `approval_record_commit`, the reviewed-path
  zero-diff/blob relationship to `reviewed_runtime_code_commit`, and an empty
  unfiltered `git status --porcelain` in the execution checkout.
- Verify the fixture_id, owner-review reference, source_sha256, and P2-T1 D2
  image-admission result=PASS. A RECAPTURE or source-digest mismatch stops before
  Lightning starts.
- Verify the profile, catalog/config hashes, dependency pins, prompt identity,
  policy identity, hardware decision, per-attempt timeout,
  `total_adapter_cap_seconds`, TTL, budget, and output ceilings are completely
  recorded.
- Verify the date-qualified evidence paths do not already exist. Never
  overwrite an existing evidence artifact.
- Initialize `adapter_call_count=0` and `attempt_count=null` before any
  pre-adapter check. If a check stops the run, preserve those values and enter
  the terminal evidence path; no adapter, mapper, or model-reaching attempt is
  claimed. If evidence creation is impossible, write only the safe ignored
  incident record described in Section 1 and do not index it.

### Phase 1 - Lightning provisioning and session startup

Start exactly one Lightning Studio GPU session under the approved TTL, total
adapter cap, and budget. Measure provisioning and session startup separately:

- provisioning interval: request/allocate start through session allocation;
- session-startup interval: allocation through approved session readiness;
- session total: session start through confirmed termination.

None of these intervals is part of adapter_wall_clock_ms.

Inside the session, before any model invocation:

- verify git rev-parse HEAD equals the externally supplied
  `approval_record_commit`, verify the two reviewed paths against
  `reviewed_runtime_code_commit`, and verify the checkout is clean; a branch
  name alone is not evidence;
- construct the supervisor containment boundary before releasing the outer
  adapter worker, verify the outer worker was created through the real spawn
  context with `daemon=False`, and require containment to cover descendants;
- require the worker to accept `CONTAINMENT_READY` before it constructs the
  Qwen adapter or the inner generation launcher; the live run must observe a
  real nested spawn rather than infer it from a fake seam;
- load the explicitly selected runtime config without copying its values to
  evidence;
- verify installed dependency versions, CUDA, driver, GPU SKU, device count,
  VRAM, and BF16 facts;
- require single approved-device visibility or, after model load, assert that
  the model and inference inputs occupy the approved device index;
- run only the no-model-load readiness inspection applicable to the approved
  configuration; require READY or stop;
- stage the approved image using the exact P2T2-LIVE-D8 method, keep its
  reference session-local and relative, and recompute the staged SHA-256;
- create and hash the sanitized runtime manifest;
- do not preload model weights. If P2T2-LIVE-D4 approves a model download,
  the download/load occurs inside the selected runner's child model-loading
  phase and is covered by the same 120-second subprocess boundary. A separate
  pre-invocation download requires separate approval.

If provisioning, session startup, readiness, staging, or manifest creation
fails, the resource cleanup finally block in Phase 4 still runs and Phase 5
records the terminal outcome.

### Phase 2 - one bounded adapter call

Construct one VisionUnderstandingRequestV2 with:

- the owner-approved fresh correlation_id;
- the session-local relative source_image_ref and staged source_sha256;
- no processing image unless a separately approved derivation is named;
- media_validation.decision=PASS with its approved provenance;
- requested_profile_id=QWEN3_VL_8B_INSTRUCT_BF16_V1.

Immediately before the single call, set `adapter_call_count=0`,
`attempt_count=null`, and compute the SHA-256 of the exact in-memory UTF-8
prompt text selected for injection. Require that hash to equal the approved
`prompt_sha256` before setting adapter_start. Then increment
`adapter_call_count` to 1 and invoke `QwenVisionAdapter.understand(request)`
exactly once; there is no outer retry counter. Immediately after it returns or
raises, set adapter_end. A prompt-hash mismatch stops before the invocation
with `adapter_call_count=0` and `attempt_count=null` and has no fabricated
adapter duration.
adapter_wall_clock_ms is adapter_end minus adapter_start and includes all work
inside understand(), including adapter-side validation, prompt construction,
model loading, generation, decoding, and any internal transient retry.

For the proposed killable runner, each generation attempt has its own
120-second child deadline after process start. It includes the child
model/processor load, generation, and decoding; it is not a model-load
deadline followed by a separate generation deadline. The separate
`total_adapter_cap_seconds` begins at adapter_start, covers all generation
attempts inside this one adapter call, and is not reset for attempt 2. Either
timeout is terminal and cannot authorize another attempt. The raw provider
string remains in memory only and never reaches stdout, stderr, a hook sink, or
evidence.

If the adapter returns its typed input-validation rejection before model
generation, record `adapter_call_count=1` and `attempt_count=0`, and never
retry or relabel it as a model-reaching smoke run. If the runner is entered,
record `adapter_call_count=1` and `attempt_count=1` or `2`, cross-checking the
value against the adapter's `attempt_number`; attempt 2 requires an explicit
transient runtime classification from attempt 1. No other call/attempt
combination is accepted, and no missing value is invented. The worker's
`ADAPTER_STARTED`, `GENERATION_ATTEMPT_STARTED`, and `TERMINAL` frames are
committed only when the supervisor accepts their sequence/deadline transition;
duplicate, gapped, invalid, late, or post-terminal events are rejected and
cannot alter `attempt_count`.

### Phase 3 - typed result and mapper

Independently assert that the in-memory adapter return is exactly one
schema-valid VisionUnderstandingSuccessV2 or VisionUnderstandingFailureV2.
Check profile_id, profile_catalog_hash, config_hash, adapter_version, model
identifier, model revision, dependency pins, source digest, correlation ID,
attempt state, and policy state against the pre-run records.

When a typed V2 result exists, call map_vision_result_to_raw exactly once with
the approved synthetic session_id, staged digest, request correlation, and
asr_result=None. This includes the adapter's typed input-validation result,
which maps to a typed Raw validation failure. A pre-adapter terminal has no V2
result and therefore makes no mapper call; its evidence records
`adapter_call_count=0` and `attempt_count=null`. No ASR or Whisper process is
started. Verify that the mapped result:

- is RawUnderstandingSuccessV1 or RawUnderstandingFailureV1;
- preserves source hash and correlation;
- carries the approved synthetic session ID;
- retains complete provenance on success;
- has gate_a_required=true;
- has narration_status=NOT_SUPPLIED when successful;
- contains no eligibility, personality, readiness, activity, objective,
  Gate B, or semantic-safety decision.

A source/hash mismatch, stale correlation, missing confidence, unsupported
variant, or any other mapper exception is terminal and is never repaired or
retried live.

### Phase 4 - in-memory disposal and resource cleanup

Cleanup is structurally required in a finally block around the entire
authorized run body, including local preflight, session provisioning, success,
timeout, malformed output, policy rejection, mapper failure, and subprocess
failure. For a pre-adapter stop before a session exists, the cleanup operations
are safe no-ops but the same terminal-recording path still runs. The approved
harness must not use early returns that bypass it. The required shape is:

    try:
        run_preflight_session_adapter_call_and_map()
    finally:
        cleanup_runner_ipc_and_child()
        discard_raw_output_and_decoded_tensors()
        terminate_lightning_session()
        confirm_no_residual_gpu_or_runner_process()

The live approval must identify the reviewed boundary. Cleanup closes the
inner generation-child IPC, terminates and joins the inner child, then
terminates and joins the outer adapter worker, terminates the containment
group/job, and verifies that both process levels and all descendants are
absent. It discards raw model output and tensors and terminates the single
Lightning session. Cleanup is required for success, timeout, malformed output,
policy rejection, mapper failure, model-load failure, device failure, and
every subprocess failure. If cleanup itself fails, the run status is FAILED with
`run_failure_code=CLEANUP_FAILED`, regardless of the V2 or Raw result, and no
retry or second session is permitted.

### Phase 5 - sanitized evidence and postflight

The evidence lifecycle is ordered and has one authoritative commit point:

1. record the runtime outcome;
2. complete cleanup and verify both process levels/descendants are gone;
3. build and write a provisional JSON/Markdown pair in temporary names,
   validating the allowlist and bounded identities;
4. run final postflight and integrity checks against the provisional pair and
   the complete artifact inventory, then repeat the inventory comparison after
   Markdown rename immediately before the authoritative JSON rename;
5. derive the final outcome, including any postflight or cleanup failure;
6. rename the authoritative JSON into its final path as the sole commit point.

`Feat018EvidenceFinalizer` owns cleanup and the mandatory precommit gate;
`Feat018EvidenceCommitWriter` supplies storage operations only. The finalizer
requires the future coordinator's complete postflight inventory check and the
writer verifies the provisional pair's exact bytes before either final rename.
The writer performs a second inventory/audit check after Markdown rename and
immediately before JSON commit. This is a commit-adjacent check under the
quiescent single-writer invariant, not filesystem-wide atomicity or protection
from an unrelated hostile writer. A failed gate aborts publication and returns
non-committed evidence, never a false success. Failure reporting or incident
fallback must retain that result.
The one-way hash protocol is:
the JSON may contain `companion_markdown_sha256`, the JSON omits its own hash,
and the Markdown never contains a JSON hash. A final JSON/Markdown pair is
authoritative only when the final JSON has `commit_state=FINAL`, matching
identities, and the Markdown hash. Hashes of both final files are collected
later in independent-review evidence, not put into either file during its own
commit protocol.

This writer is required for every authorized run attempt, including a
pre-adapter terminal. If the pair cannot be created or atomically completed,
write only the safe ignored incident record at the exact relative destination
`tmp/feat018-live-lightning-incident-<run_id>/INCIDENT.md`; do not index an
incomplete pair or the incident. The future coordinator/preflight must confirm
that exact destination is Git-ignored, and the writer rejects tracked,
publishable, arbitrary absolute, traversal, mismatched-run and link/reparse
destinations. The writer must not serialize the V2 or Raw object wholesale
because their provenance may contain fields, URLs, or details that are not
allowed in sanitized evidence. It selects only the allowlisted metadata
described below. If an unexpected tracked, untracked, ignored, temporary,
cache, runtime-config, or generated artifact is found, the run fails and the
artifact is not published or indexed. Do not delete or overwrite an unexpected
user artifact under this plan; stop and report its logical category and safe
identity.

## 5. Assertions and terminal outcome rules

All assertions below are required for a functional PASS:

The live checklist is explicit: real nested spawn succeeds; the outer worker
is non-daemon; containment covers all descendants; no orphan remains after a
kill; cleanup confirms both levels are absent; late events are rejected; and
`attempt_count` comes only from committed progress.

- a model-reaching run has exactly one adapter call:
  `adapter_call_count=1`;
- a pre-adapter terminal is recorded as `adapter_call_count=0` and
  `attempt_count=null`; an adapter input rejection before model generation is
  recorded as `adapter_call_count=1` and `attempt_count=0`;
- a model-reaching run records `attempt_count=1` or `2`, and attempt 2 occurs
  only after an explicitly classified transient runtime failure on attempt 1;
- no call or attempt value is inferred, backfilled, or fabricated; the only
  source of `attempt_count` is a supervisor-accepted committed progress event;
- the source fixture was admitted before any vision call;
- the original and staged source SHA-256 values match, and the adapter's
  independent image-reference verification passed;
- the externally supplied `approval_record_commit` was verified inside
  Lightning before the adapter call, and both reviewed implementation paths
  have the approved zero-diff/blob relationship to
  `reviewed_runtime_code_commit`;
- the sanitized runtime manifest is allowlist-valid and its hash matches;
- the exact profile, model identifier/revision, config/catalog hashes,
  dependencies, prompt identity/hash, policy identity, and hardware facts
  match the approval;
- the configured raw-output, IPC, stdout, and stderr ceilings were enforced;
- the live nested-spawn assertion succeeded: the outer worker was really
  non-daemon, its inner generation child was really spawned only after the
  containment release gate, and the containment mechanism covered all
  descendants;
- a kill/timeout leaves no orphan at either process level, cleanup confirms
  both levels and the containment group/job are absent, and any late progress
  event is rejected rather than changing the terminal result;
- each generation attempt was bounded at 120 seconds and the separate
  `total_adapter_cap_seconds` covered the complete adapter call, including any
  permitted retry, without resetting;
- the V2 result is schema-valid, or the typed terminal failure is recorded;
- the mapper result is schema-valid when mapping was reached;
- correlation, source, synthetic session identity, and provenance checks pass;
- gate_a_required=true and no P1/Gate A/Gate B decision was fabricated;
- ASR/Whisper was not run and narration is not represented as supplied;
- the adapter timing includes model load, generation, decoding, and internal
  retry, while provisioning/session startup/cleanup are separately measured;
- cleanup ran in finally and cleanup_status=SUCCEEDED; any cleanup failure
  makes the overall run FAILED;
- the exact sanitized evidence pair was attempted for every authorized run
  attempt, including pre-adapter terminals; an impossible pair has only the
  safe ignored incident record and is not indexed;
- postflight inventory satisfies the exact two-file evidence scope.

One smoke run is functional evidence only. It is not a benchmark, does not
establish p50/p95 latency, throughput, quality, accuracy, semantic safety, or
production moderation readiness, and cannot close P2-T2 by itself. Full P2
closure needs separately approved live/evaluation work and its own evidence.

### 5.1 Retry and failure matrix

| Condition | V2 or harness outcome | Retry rule | adapter_call_count | attempt_count |
|---|---|---|---|---|
| Approval, checkout, fixture, readiness, configuration, policy, hardware, manifest, runner-boundary, or session/budget stop before adapter invocation | Harness terminal; no V2 or Raw result | Terminal; no adapter call | 0 | `null` |
| Adapter input validation rejects before model generation | V2 INPUT_NOT_VALIDATED; mapper may produce typed Raw validation failure | Terminal; no retry | 1 | 0 |
| Model-load failure after the runner is entered | V2 VISION_MODEL_UNAVAILABLE / MODEL_LOAD_FAILED | Terminal; no second generation call | 1 | 1 |
| Device unavailable or wrong device after the runner is entered | V2 VISION_MODEL_UNAVAILABLE / DEVICE_UNAVAILABLE | Terminal; no retry | 1 | 1 |
| Timeout on either generation attempt | V2 VISION_TIMEOUT / TIMEOUT_BUDGET_EXCEEDED | Terminal; no retry after timeout | 1 | 1 or 2 |
| Total adapter cap reached | Harness or V2 timeout terminal | Terminal; no retry and no cap reset | 1 | 1 or 2 |
| Explicit or classified transient runtime failure on attempt 1 | Internal adapter retry | One retry only; proceed to attempt 2 | 1 | 2 after retry |
| Transient failure again on attempt 2 | V2 VISION_PROVIDER_FAILURE / TRANSIENT_RUNTIME_FAILURE | Terminal; no third attempt | 1 | 2 |
| Permanent runtime failure after the runner is entered | V2 VISION_PROVIDER_FAILURE / PERMANENT_RUNTIME_FAILURE | Terminal; no retry | 1 | 1 or 2 |
| Malformed JSON, schema-invalid output, duplicate ID, or reference failure | V2 VISION_SCHEMA_INVALID with the existing typed detail | Terminal; no repair/retry outside current adapter behavior | 1 | 1 or 2 |
| Content-policy rejection | V2 PROHIBITED_CLAIM_DETECTED with typed category | Terminal; no retry or semantic reinterpretation | 1 | 1 or 2 |
| Mapper failure or source/correlation mismatch at mapper | RawUnderstandingMappingError; no fabricated Raw result | Terminal; no retry | 1 | 0, 1, or 2 as recorded before mapping |
| IPC, raw-output, stdout, or stderr ceiling exceeded | Harness-level bounded-output failure | Terminal; stop session; no retry | 1 | 1 or 2 |
| Cleanup failure | Harness FAILED / CLEANUP_FAILED | Terminal; no second session | 0, 1 | `null`, 0, 1, or 2 as recorded |

The current subprocess worker maps generic worker exceptions to a permanent
runtime failure; it does not infer transient status from arbitrary provider
text. Only an explicit approved transient seam may produce attempt 2.

### 5.2 Existing source/hash failure mapping

| Condition | Existing adapter outcome | Existing mapper outcome |
|---|---|---|
| Adapter verifies a staged digest mismatch | error_code=INPUT_NOT_VALIDATED, error_detail=SOURCE_IMAGE_HASH_MISMATCH, attempt_number=0, retryable=false; record `adapter_call_count=1`, `attempt_count=0` | RawFailureCode.VALIDATION_REJECTED with upstream detail SOURCE_IMAGE_HASH_MISMATCH |
| Adapter cannot read the staged source | error_code=INPUT_NOT_VALIDATED, error_detail=SOURCE_IMAGE_UNREADABLE, attempt_number=0, retryable=false; record `adapter_call_count=1`, `attempt_count=0` | RawFailureCode.VALIDATION_REJECTED with upstream detail SOURCE_IMAGE_UNREADABLE |
| Mapper sees result.source_image_ref.sha256 different from expected_source_sha256 | No new V2 result | Raises RawUnderstandingMappingError before Raw construction |

The direct mapper mismatch is not RawFailureCode.SOURCE_MISMATCH. That enum
member is not the current V2 mapper path. No mapping change is authorized. A
stop before the adapter has no row in the existing-adapter column and records
`adapter_call_count=0`, `attempt_count=null` in the sanitized harness evidence.

## 6. Negative and stop gates

The following stop the run immediately. They are terminal, are recorded
without raw content, and still pass through the cleanup finally block:

- any missing or unresolved approval decision;
- `approval_record_commit` mismatch, reviewed-path zero-diff/blob mismatch,
  dirty checkout, untracked file, or unexpected source artifact;
- fixture admission RECAPTURE, fixture identity/hash mismatch, or staged
  digest mismatch;
- unverified model revision, profile/config/catalog drift, or dependency
  mismatch;
- missing or wrong prompt-builder identity, policy identity, or output bound;
- CUDA unavailable, wrong SKU/device count/index, insufficient or
  unverifiable VRAM, BF16 unavailable, or failed model/input placement on the
  approved device;
- a selected runner that cannot bound IPC, stdout, stderr, and raw output;
- model-load failure, device-unavailable failure, timeout, malformed output,
  policy rejection, permanent runtime failure, mapper failure, or cleanup
  failure;
- a cardinality combination other than pre-adapter `0/null`, adapter input
  rejection `1/0`, or model-reaching `1/1` or `1/2`; an outer retry, a third
  generation attempt, or a retry for any non-transient failure;
- `total_adapter_cap_seconds`, session TTL, or GPU/currency cap reached;
- any secret, token, credential, URL, absolute path, prompt, raw provider
  output, transcript, or raw media value entering evidence or logs;
- any artifact outside the exact future-approved evidence pair modified or
  created.

If the adapter returns an input failure with `attempt_number=0`, record
`adapter_call_count=1`, `attempt_count=0`, map that typed result once, and
retain it as a terminal non-functional outcome. It is never retried to force
attempt_count into a model-reaching value. If a stop occurs before the adapter,
record `adapter_call_count=0`, `attempt_count=null`; neither value may be
backfilled from a planned call. Every such authorized terminal still requires
the exact sanitized evidence pair, or only the ignored incident fallback when
pair creation is impossible.

## 7. Evidence policy

After a separately approved run, write exactly this feature-local pair, with
the date replaced by the actual run date:

- features/FEAT-018-live-image-canvas-flow/evidence/metrics/P2_LIVE_SMOKE_<YYYYMMDD>.json
- features/FEAT-018-live-image-canvas-flow/evidence/notes/P2_LIVE_SMOKE_<YYYYMMDD>.md

The future approval must name the exact date-qualified paths, and the paths
must be absent before execution. Do not write a third run artifact, use tmp as
evidence, index before the required review, or overwrite an existing pair.

The JSON/Markdown pair follows the evidence lifecycle in Phase 5. The JSON is
the authoritative commit record and is the last rename. JSON may reference
the exact SHA-256 of its Markdown companion, but JSON cannot hash itself and
Markdown must not reference the JSON hash. The hashes of both final files are
captured only by the later independent-review evidence; they are not inserted
into the pair while either file is being authored.

Every authorized run attempt, including a terminal before adapter invocation,
must produce exactly this JSON/Markdown pair. A pre-adapter terminal records
`adapter_call_count=0` and `attempt_count=null` and omits V2/Raw result claims;
an adapter input rejection records `adapter_call_count=1` and
`attempt_count=0`; a model-reaching call records `adapter_call_count=1` and
`attempt_count=1` or `2`. If the pair cannot be created or atomically
completed, the only fallback is the safe local ignored incident record at
`tmp/feat018-live-lightning-incident-<run_id>/INCIDENT.md`; it is not feature
evidence, is not indexed, and must contain no prompt, raw output, secret,
credential, URL, path, or raw media.

The sanitized JSON and Markdown companion contain the same bounded run
metadata, with the Markdown providing human-readable interpretation:

- exact `reviewed_runtime_code_commit`, externally supplied
  `approval_record_commit`, and verified=true;
- run_id, correlation_id, and synthetic session_id only when they are opaque
  safe identifiers with no path, URL, token, or credential;
- exact fixture_id, source_sha256, staged reference class, MIME, width, height,
  and the approved staging method; never image bytes;
- model identifier, model revision, profile ID, adapter version,
  profile_config_hash, and profile_catalog_hash; never a weight-source URL;
- prompt_protocol_id, prompt_source_identity, and prompt_sha256; never prompt
  text;
- content_policy_version, policy_match_view_version, policy_scope, and
  P2T2-LIVE-D12 result; no lexicon text or semantic-safety claim;
- the allowlisted runtime_manifest object and runtime_manifest_sha256;
- GPU SKU, device index/count, vram_mib, BF16 result, CUDA runtime fact, and
  driver version only through the allowlisted manifest, plus the approved
  single-device visibility or post-load model/input placement assertion;
- max_new_tokens=512, raw_output_max_bytes, ipc_envelope_max_bytes,
  stdout_max_bytes, stderr_max_bytes, and an enforcement=CONFIRMED result;
- adapter_call_count and attempt_count using the conditional cardinality
  rules above, together with the adapter's typed attempt/result status when a
  V2 result exists; no raw model output;
- outcome status SUCCEEDED or FAILED; typed V2/Raw failure code when a valid
  typed result exists; harness-level run_failure_code when mapping, bounds,
  or cleanup fails;
- timing fields: provisioning_wall_clock_ms,
  session_startup_wall_clock_ms, session_total_wall_clock_ms,
  adapter_wall_clock_ms, mapper_wall_clock_ms, and explicit boundary labels;
  adapter timing is not combined with provisioning or session startup; a
  pre-adapter terminal uses no fabricated adapter duration;
- per_attempt_timeout_seconds=120.0, total_adapter_cap_seconds,
  session_ttl_seconds, gpu_minute_cap and/or currency_cap, cap outcome, and
  safe budget-consumed value;
- ASR/Whisper execution=false and narration_status=NOT_SUPPLIED when a Raw
  success exists;
- cleanup_status, postflight_status, and a safe artifact-inventory summary.

Safe hashes may be recorded for the fixture, staged fixture, prompt identity,
runtime manifest, reviewed and approval commit metadata, and
profile/config/catalog metadata. The SHA-256 values of both final evidence
files belong to later independent-review evidence, not to the pair's own
contents. Never hash-and-publish secrets, credentials, raw output, prompts as
a replacement for the required prompt identity rule, raw media, or arbitrary
cache contents. Do not serialize V2 or Raw objects wholesale.

Never store in either evidence file, normal logs, or tracked Git history:

- raw image/audio bytes or derivative renderings;
- prompt text or raw provider/model output;
- HTTP/session headers, URLs, tokens, credentials, or Lightning secrets;
- transcripts or ASR content;
- absolute local paths, hostnames, command lines, cache paths, or runtime-env
  values;
- child-process exceptions, Pydantic messages, or provider payloads that may
  contain unbounded or user-derived text.

## 8. Postflight inspection and audit

Failure-producing postflight is required after cleanup, with the provisional
pair present and before either final rename. It inspects the following
inventory. After JSON commit, only read-only pair/publication verification is
permitted; this is not a second runtime-outcome gate. A failed later integrity
check prevents indexing and labels the pair non-authoritative without rewriting
the recorded outcome. Independent verification records that disposition.

1. Tracked files: unfiltered git status --porcelain, git diff --name-status,
   the exact `approval_record_commit`, and the reviewed-path zero-diff/blob
   relationship to `reviewed_runtime_code_commit`.
2. Untracked files: all newly untracked paths in the source checkout and any
   execution workspace.
3. Ignored files: git status --ignored --short, with before/after comparison
   for approved ignored runtime config, caches, and local fixture locations.
4. Temporary artifacts: child-worker files, IPC/pipe remnants, temporary
   directories, scratch logs, and session teardown artifacts. Confirm the
   outer adapter worker, every inner generation child, and the containment
   group/job are absent after cleanup; a surviving or unverifiable descendant
   is a failed postflight.
5. Cache artifacts: model cache, framework cache, compiler cache, and
   generated weight/index files; verify that no new raw output or credentials
   are present.
6. Runtime-config artifacts: the selected env file and any derived config;
   inspect existence and safe logical identity only, never publish its
   contents or secret hash.
7. Generated artifacts: model output, decoded tensors, prompt dumps,
   provider responses, reports, notebooks, and other generated files; none
   may remain as an unapproved run artifact.
8. Evidence artifacts: precommit inventory permits only the exact provisional
   pair; final paths must be absent. The finalizer verifies its bytes. After
   commit, read-only publication verification validates `commit_state=FINAL`, identity
   agreement, and the JSON-to-Markdown companion hash. The later independent
   review, not the live pair, records the SHA-256 of both final files. If pair
   creation is impossible, the only permitted exception is the safe ignored
   incident path from Section 7, which is recorded as an unindexed failure
   artifact rather than evidence.

The postflight result must record safe identities/hashes where applicable:
reviewed_runtime_code_commit, approval_record_commit, fixture/source and staged
digests, prompt_sha256,
runtime_manifest_sha256, profile/config/catalog hashes, and evidence-file
hashes only in the later independent-review artifact. It must record category
and disposition for every inspected ignored
or temporary artifact without exposing its path or contents in the published
evidence. A new or changed artifact outside the exact approved pair fails the
run and prevents indexing, except for the explicitly permitted ignored
incident path created only when pair creation is impossible.

## 9. Explicit owner decisions required before live approval

Each decision below is owner-decidable and auditable. The owner must select
one stated resolution and record every required field in the future approval.
Blank values, an implicit default, or a prose-only statement does not resolve
the decision.

These labels are live P2-T2 plan identifiers only; they do not alter, rename,
or close any P2-T1 decision.

### Current decision status

Each status is one of the permitted planning dispositions. `RESOLVED_WITH_PROPOSED_VALUE`
means that the reviewed source or local owner-reviewed input supports a
concrete value, not that the future live approval has been granted.

| Decision | Status | Current basis or blocker |
|---|---|---|
| P2T2-LIVE-D1 | `BLOCKED` | Offline coordinator implementation and source/test binding are complete; remaining D1 owner resolution and Stage 4 approval are pending. |
| P2T2-LIVE-D2 | `READY_TO_RESOLVE` | Positive TTL, total adapter cap, and numeric GPU-minute/currency cap still require owner selection. |
| P2T2-LIVE-D3 | `RESOLVED_WITH_PROPOSED_VALUE` | `ASR_EXCLUDED`, `asr_execution=false`, and `narration_status=NOT_SUPPLIED` are the proposed image-only value. |
| P2T2-LIVE-D4 | `BLOCKED` | No locally proven pre-staged snapshot identity/completeness/revision record; see the exact unblock requirement in D4. |
| P2T2-LIVE-D5 | `READY_TO_RESOLVE` | Owner must choose independent-review indexing or P2 batch hold. |
| P2T2-LIVE-D6 | `RESOLVED_WITH_PROPOSED_VALUE` | Owner-reviewed Cohort B `B01.jpg` metadata and digest match the manifest and source review. |
| P2T2-LIVE-D7 | `RESOLVED_WITH_PROPOSED_VALUE` | Committed C1-v2 source, builder, explicit `prompt=` path, and exact UTF-8 hash are traced; Stage 4 must bind them. |
| P2T2-LIVE-D8 | `READY_TO_RESOLVE` | Mount/copy/upload session-relative staging method remains an owner choice. |
| P2T2-LIVE-D9 | `RESOLVED_WITH_PROPOSED_VALUE` | Proposed integers are 65536, 98304, 0, and 0 with the reviewed bounded enforcement path. |
| P2T2-LIVE-D10 | `READY_TO_RESOLVE` | Approval values and observed GPU evidence must be supplied separately; no live hardware was observed here. |
| P2T2-LIVE-D11 | `BLOCKED` | Exact two-file scope and source/test binding are complete; live-runtime/session-controller suitability and Stage 4 approval remain pending. |
| P2T2-LIVE-D12 | `RESOLVED_WITH_PROPOSED_VALUE` | Synthetic lexical regression policy identity and scope are committed and proposed. |

D4 is explicitly blocked, and D6/D7 are not marked resolved without their
local metadata/source proof. No table row authorizes live execution.

### Required staged governance sequence

The authorization sequence is mandatory and sequential. Its current
disposition is explicit:

| Stage | Required gate | Status | Bound evidence or next action |
|---|---|---|---|
| 1 | Exact two-file scope approval, with the FEAT-003 exclusion | COMPLETE | `6c1d607eb379a3b5b5b8f5cf120a904460da9ff1` and the feature-local approval package |
| 2 | Offline coordinator implementation and verification with injected seams and synthetic local process tests only | COMPLETE FOR OFFLINE IMPLEMENTATION/VERIFICATION | `7f5cbe57fc9756c3e7fa5c248cd655c1dce0ec7b` and `9549a341194f40b1a9be419d6fce0d70f1ca0384`; offline coordinator/POSIX findings are closed; no live execution is claimed |
| 3 | Offline independent review/finalization and source/plan binding review | COMPLETE FOR OFFLINE IMPLEMENTATION/VERIFICATION; SOURCE/TEST BINDING RECORDED | Offline review/finalization records close the offline findings; owner binding records `9549a341194f40b1a9be419d6fce0d70f1ca0384` for source/test identity only; live session/controller suitability remains pending |
| 4 | Separate owner live-execution approval resolving D1-D12 and supplying the post-approval checkout commit | PENDING | owner approval must name exact fixture, prompt, hardware, budget, redaction, evidence pair, and external `approval_record_commit` |
| 5 | Open Lightning and run the approved smoke | BLOCKED UNTIL STAGE 4 | no live process, model, GPU, provider, network, or Lightning execution is authorized by this draft |

Historic primitive approval/review does not resolve the live D1-D12 approval. The
Reviewed offline validation includes synthetic local process-boundary tests for
host preemption and POSIX containment, but it does not start a real
Lightning/provider/model session. Stage 4 must still carry the real
nested-spawn, descendant-containment, no-orphan, and two-level-cleanup
assertions against the approved live environment.

The current focused offline suite for this verification lineage is `268
passed, 1 skipped`; the related sweep is `955 passed, 6 skipped, 420
deselected`. The earlier `196 passed`, `170 passed`, and historic
`154 focused`/`839 related` figures are historical checkpoints, not current
totals.

### P2T2-LIVE-D1 - Runner and deadline enforcement

Planning disposition: `BLOCKED` pending remaining D1 owner resolution and
Stage 4 approval; source/test identity is already owner-bound.

The proposed future value remains `NEW_GLUE_EXPLICITLY_APPROVED`. The offline
coordinator uses the bounded primitives identified by historical provenance
`c2bd7b5ece3f308abb65ab3632add265b3cd586c` only; the validated offline
coordinator/correction provenance is
`7f5cbe57fc9756c3e7fa5c248cd655c1dce0ec7b`, and the POSIX test correction
   provenance is `9549a341194f40b1a9be419d6fce0d70f1ca0384`. The owner-bound
   reviewed runtime commit identifies these exact source/test blobs only. The offline coordinator's supervisor launches the
non-daemon adapter worker, the worker constructs the real adapter after
containment release, and `Feat018BoundedKillableQwenGenerationRunner` launches
one bounded generation child per adapter attempt. The runner's 120-second
deadline covers model/processor loading, generation, and decoding; its bounded
IPC and cleanup are covered by Stage 3 review. The later live approval must
still record the external `approval_record_commit`, prove the real nested
spawn and descendant containment, set `total_adapter_cap_seconds`, and verify
the conditional call/attempt cardinality. This proposed value is not live
   authorization. D1 remains blocked pending the remaining owner resolution
   and Stage 4 approval; the current documentation HEAD is not the runtime
   source identity.

### P2T2-LIVE-D2 - TTL and budget cap

Planning disposition: `READY_TO_RESOLVE`.

Record positive `session_ttl_seconds` and
`total_adapter_cap_seconds`, plus at least one exact numeric `gpu_minute_cap`
or `currency_cap`. The total adapter cap begins at adapter_start and covers
the complete one-call adapter boundary, including any permitted second
generation attempt; it does not reset on retry. The session TTL and
GPU/currency cap cover the broader session. If multiple caps are supplied,
record the cap clock, the currency if applicable, and the exact action
`TERMINATE_SESSION_AND_MARK_FAILED` at the first cap. A total-cap, timeout,
TTL, or GPU/currency terminal cannot trigger another attempt. The owner may
not approve an unbounded session or a cap described only as "small" or
"within budget".

### P2T2-LIVE-D3 - ASR/Whisper exclusion

Planning disposition: `RESOLVED_WITH_PROPOSED_VALUE`.

Select ASR_EXCLUDED for this image-only smoke run and record
asr_execution=false, asr_result=null, and narration_status=NOT_SUPPLIED. If
the owner does not select ASR_EXCLUDED, this plan is blocked and a separate
P2-T3 live ASR/Whisper approval must enumerate its own model, fixture,
budget, redaction, retries, cleanup, and evidence. This plan never combines
the modalities.

### P2T2-LIVE-D4 - Model-weight staging

Planning disposition: `BLOCKED`.

The repository profile and readiness checker define the required pinned model
revision and completeness rule, but discovery found no local, owner-reviewed
snapshot manifest proving a session-local Qwen snapshot identity, complete
required files/shards, and matching revision metadata. No cache path, arbitrary
weight hash, or host-local model location is published here. D4 therefore has
no proven selected value yet.

Exact unblock requirement: the owner must provide a safe logical/session-local
snapshot identity, the pinned revision
`0c351dd01ed87e9c1b53cbc748cba10e6187ff3b`, the readiness completeness proof
(all loader-required files plus every shard named by the safetensors index and
per-file revision metadata), and `allow_model_download=false`, or must
separately approve `APPROVED_ONE_TIME_DOWNLOAD` with its source identity,
`allow_model_download=true`, no repository weight digest, and acceptance that
download/load stays inside the generation child deadline. Until one of those
two owner records exists and is verifiable inside Lightning, the live run is
blocked.

Select exactly one:

- PRESTAGED_LOCAL_SNAPSHOT: record the session-local model directory
  identity, allow_model_download=false, snapshot completeness, and verified
  revision metadata; or
- APPROVED_ONE_TIME_DOWNLOAD: record the approved source identity, the
  allow_model_download=true setting, the absence of a repository-published
  weight SHA-256, and the acceptance that download/load occurs inside the
  runner's model-loading interval and 120-second deadline.

A download is never a separate unapproved pre-invocation phase. The runtime
manifest and evidence contain no URL, credential, absolute path, or raw
weight data. If the chosen option cannot be verified with the current
readiness boundary, the run stops.

### P2T2-LIVE-D5 - Evidence indexing timing

Planning disposition: `READY_TO_RESOLVE`.

Select exactly one:

- INDEX_AFTER_INDEPENDENT_REVIEW: record the reviewer, review timestamp,
  review artifact, and the rule that no index update occurs before the
  review; or
- HOLD_FOR_P2_BATCH: record the holding owner/location and the later review
  gate.

This decision authorizes no edit to evidence/README.md in this draft.

### P2T2-LIVE-D6 - Exact fixture identity

Planning disposition: `RESOLVED_WITH_PROPOSED_VALUE`.

The proposed fixture is the owner-reviewed reused Cohort B candidate
`B01.jpg`, recorded only as the opaque relative identity `Cohort B/B01.jpg`.
The local manifest and source review agree on JPEG / `image/jpeg`, dimensions
`1254x1254`, byte count `337481`, and SHA-256
`c60faed33034b5911e611a512dde03cc94fb21146f85dfba4ef7236268ab9cc3`.
Independent read-only recomputation of B01 found JPEG SOI magic `ffd8ff` and
the same byte count, dimensions, and digest. The owner-review reference is
the local `SOURCE_REVIEW.md`, dated 2026-09-12, with visual disposition PASS.
The final approval must repeat these checks on the immutable original before
staging; the review artifact must not contain image bytes or an absolute path.

Record exactly one owner-approved fixture_id, source/derivation identity,
owner visual-review reference and date, MIME/extension, width, height,
source_sha256, and whether it is a reused Cohort B image or a newly reviewed
image. The original is immutable and never committed. A new image cannot be
used merely because it passes the P2-T1 D2 image-admission policy.

### P2T2-LIVE-D7 - Prompt identity and explicit builder

Planning disposition: `RESOLVED_WITH_PROPOSED_VALUE`.

The committed authoritative candidate is C1-v2:

- `prompt_protocol_id=vision-v2-structured-output-prompt-v2`;
- source identity/version:
  `backend/src/sketch2life/benchmark/vision_c1_prompt_mapping_study.py`,
  `C1_PROMPT_V2` / `c1_prompt_text_v2()`;
- exact UTF-8 prompt SHA-256:
  `1e880e946dc1f1dcf11731c299702b33ab58e3c098cdda3d6607c080dc8f9fd6`;
- injection: resolve `c1_prompt_text_v2()` once, verify its UTF-8 digest, then
  pass the resulting string as `prompt=` to `run_bounded_adapter_call`,
  through `adapter_worker_entry` to
  `QwenVisionAdapter(..., prompt=prompt, generation_runner=runner)`.

This traces the actual reviewed Qwen adapter seam without copying prompt text.
The explicit `prompt=` argument means `QwenVisionAdapter` does not reach its
empty `_default_prompt_builder`; the live caller must additionally reject an
empty string and a hash mismatch before incrementing `adapter_call_count`.
The reviewed bounded runner accepts a prompt string but does not choose its
protocol, so the proposed binding remains subject to Stage 4 owner approval.
If the owner selects any other prompt, the approval must name its committed
source/version and recomputed exact UTF-8 hash; an uncommitted or unverifiable
prompt leaves D7 `BLOCKED`.

Record the exact prompt_protocol_id, prompt source identity/version,
prompt_sha256, and the explicit PromptBuilder or prompt injection used by
the approved harness. Immediately before invoking the adapter, hash the exact
in-memory UTF-8 injected text with
`sha256(prompt_text.encode("utf-8")).hexdigest()` and require equality with
the approved `prompt_sha256`; record only the approved hash and safe identity.
Confirm the empty adapter default is unreachable and do not log or persist the
prompt text.
The prompt text is never recorded. Any new or changed FEAT-003 prompt
requires another approval and is not authorized by this plan.

### P2T2-LIVE-D8 - Fixture staging and mount method

Planning disposition: `READY_TO_RESOLVE`.

Select exactly one owner-approved mechanism:

- MOUNT_SESSION_RELATIVE;
- COPY_SESSION_RELATIVE; or
- UPLOAD_THEN_SESSION_RELATIVE.

Record the method, a logical session-relative artifact_ref, source-to-derived
provenance, pre/post staging digest checks, and immutable-original rule. A
host-local Windows path, signed URL, credential, or unbounded base64/log
transport is not a valid staging reference.

### P2T2-LIVE-D9 - Raw output, IPC, stdout, and stderr ceilings

Planning disposition: `RESOLVED_WITH_PROPOSED_VALUE`.

The proposed exact integers are
`raw_output_max_bytes=65536`, `ipc_envelope_max_bytes=98304`,
`stdout_max_bytes=0`, and `stderr_max_bytes=0`. The zero stream values mean
the streams are disabled; any observed byte fails the run. These values are
approval values, not implicit source defaults, and must be passed explicitly
to `Feat018BoundedRunnerConfig`.

Record exact positive integer values for raw_output_max_bytes and
ipc_envelope_max_bytes, exact non-negative integer values for
stdout_max_bytes and stderr_max_bytes, the enforcement component and phase,
UTF-8/protocol behavior, and the exact overflow action
TERMINATE_AND_MARK_FAILED. The fixed model bound max_new_tokens=512 remains
in force but does not replace these ceilings. The proposed
`NEW_GLUE_EXPLICITLY_APPROVED` boundary must enforce the raw-output ceiling
before any raw value crosses IPC, send only an envelope already proven to fit
the IPC ceiling, and make stdout/stderr bounded and non-persistent. The
reviewed bounded implementation, not the old subprocess `Connection.send` or
the old in-process runner, is the selected boundary. These are required
implementation/test acceptance conditions for the exact scope in Section 2.5;
if the selected approval values cannot be proven at runtime, the owner must
leave the live run unapproved.

### P2T2-LIVE-D10 - Exact GPU/SKU/VRAM/BF16 decision

Planning disposition: `READY_TO_RESOLVE`.

Approval requirements and observed runtime evidence are separate records.
The approval must state the permitted accelerator provider/tier, exact GPU
SKU, `device_count`, `device_index`, numeric `minimum_vram_mib`, required
`cuda=true`, required `bf16_supported=true`, driver-fact allowlist, and the
mismatch action `TERMINATE_SESSION_AND_MARK_FAILED`. The proposed readiness
class is the existing `NVIDIA_L4` boundary, but no live GPU was observed in
this plan-only reconciliation and no observed VRAM/SKU/BF16 result is being
claimed.

At runtime, the allowlisted manifest must separately record the actual SKU,
device index/count, `vram_mib`, CUDA runtime fact, driver fact, and BF16 result;
the run must also record either single-device visibility or a post-load
assertion that the model and inference inputs occupy the approved device index.
Those observed facts can satisfy the approval only when they match it; they
cannot silently supply missing approval values, and an inventory-only check
does not satisfy D10.

Record approved accelerator provider/tier, exact GPU SKU, device_count, device_index,
minimum_vram_mib, required cuda=true, required
bf16_supported=true, and the readiness mismatch action
TERMINATE_SESSION_AND_MARK_FAILED. The current readiness contract's expected
device class is NVIDIA_L4; selecting another SKU requires an already-approved
readiness boundary and cannot be made true by editing code during the run.
Require either single approved-device visibility or a post-load assertion that
the model and inference inputs are placed on the approved device index;
inventory facts alone do not satisfy D10.

### P2T2-LIVE-D11 - Approved harness, glue boundary, and session ID

Planning disposition: `BLOCKED` pending remaining live suitability,
session/controller binding, and Stage 4 approval in Section 2.5.

The historic bounded primitives have `NEW_GLUE_EXPLICITLY_APPROVED` scope under
historical provenance `c2bd7b5ece3f308abb65ab3632add265b3cd586c`; the
validated offline coordinator/correction provenance is
`7f5cbe57fc9756c3e7fa5c248cd655c1dce0ec7b`, and the POSIX test correction
provenance is `9549a341194f40b1a9be419d6fce0d70f1ca0384`. The owner-bound
`reviewed_runtime_code_commit` identifies the exact reviewed source/test blobs
only; no old runner or existing harness satisfies
the combined deadline and bounded-IPC requirements. The exact two-file scope
is:

- `backend/src/sketch2life/benchmark/feat018_live_lightning_execution.py` for
  the bounded killable runner, supervisor, progress and containment primitives,
  and pair writer/reader; the current coordinator responsibilities in Section
  2.5 are implemented in the offline source boundary but still require live
  suitability and session/controller binding;
- `backend/tests/unit/test_feat018_live_lightning_execution.py` for all
  existing offline overflow, timeout, cleanup, cardinality and pair tests,
  plus the correction tests; live coordinator acceptance remains pending.

The offline coordinator implementation and independent/POSIX verification are
complete with findings closed. The owner-bound
`reviewed_runtime_code_commit` identifies the exact reviewed source/test blobs,
but does not resolve the remaining live suitability, controller/session, D4,
or Stage 4 gates. The provenance commits and current documentation HEAD cannot
substitute for that exact source identity. The
separate Stage 4 approval must
identify `approval_record_commit`, prove zero diff/blob identity for both
paths, identify the exact evidence-writer paths, and authorize the real nested
spawn only after D1-D12 are resolved. Record the safe synthetic `session_id`
handling rule and confirm it is not a production session, credential, URL, or
path.

### P2T2-LIVE-D12 - Functional synthetic content-policy boundary

Planning disposition: `RESOLVED_WITH_PROPOSED_VALUE`.

Select USE_LEXICAL_REGRESSION_FUNCTIONAL_ONLY and record:

- `sketch2life.infrastructure.ai.vision_lexical_policy.LexicalRegressionContentPolicy`;
- `sketch2life.infrastructure.ai.vision_lexical_policy.synthetic_prohibited_lexicon()`;
- `content_policy_version=vision-prohibited-lexicon-fixture-v1`;
- `policy_match_view_version=vision-policy-match-view-v2`;
- synthetic fixture/regression purpose; and
- the policy result in the evidence pair without matched text.

This policy is functional-only/synthetic-regression checking. It is not
semantic safety evidence, model quality evidence, or production content
moderation evidence. No owner may treat a policy PASS as any of those
claims. A semantic or production moderation policy needs a separate plan and
approval; no alternate policy is silently substituted here.

## 10. Final acceptance boundary

The future live smoke is accepted only after the staged governance sequence
passes and the separate live approval covers the exact
`reviewed_runtime_code_commit`, externally supplied `approval_record_commit`,
fixture, prompt, runner, hardware, budgets, redaction rules, and evidence
paths. The run must then pass exact fixture/staged-digest,
profile/dependency, prompt and policy, hardware/placement, TTL/budget,
per-attempt 120-second,
`total_adapter_cap_seconds`, bounded IPC/logging, timing, typed V2-to-Raw
mapping, finally cleanup, sanitized-manifest, postflight, and evidence-pair
checks. Its cardinality must be truthful: pre-adapter `0/null`, adapter input
rejection `1/0`, or model-reaching `1/1` or `1/2` only, with attempt 2 allowed
solely after an explicitly classified transient failure.

Every authorized run attempt must have the exact sanitized JSON/Markdown pair,
including pre-adapter terminals. If evidence creation is impossible, the safe
ignored incident record is the only permitted fallback and the run is not
indexed. No missing call or attempt is backfilled.

A typed failure is useful evidence of a stop gate but is not a functional
PASS. Cleanup failure is always overall FAILED. A smoke result does not
authorize indexing until P2T2-LIVE-D5 is resolved and the required
independent review occurs.

This draft records planning dispositions for P2T2-LIVE-D1 through D12 but
does not grant their separate live approval. D1/D4/D11 remain BLOCKED, D2/D5/D8/D10
remain READY_TO_RESOLVE, and the proposed values in the other rows still
require the Stage 4 owner approval. Offline coordinator implementation and
independent/POSIX verification are complete with findings closed; live runtime
suitability and session/controller binding remain pending. The draft does not authorize live
execution, provider benchmark work, or closure of P2-T2. It also does not
authorize any FEAT-017 remote HTTPS adapter,
FEAT-003 modification, mobile, Gate A UI, P1 eligibility, P3/P4, shared
integration, P2-T3 narration, P2-T4/P2-T5 evaluation, commit, or push.
