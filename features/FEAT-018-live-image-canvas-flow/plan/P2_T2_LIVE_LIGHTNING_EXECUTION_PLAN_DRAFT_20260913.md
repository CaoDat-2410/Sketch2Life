# FEAT-018 P2-T2 live Lightning execution plan - draft

STATUS: DRAFT
NOT AN APPROVAL
NOT AN IMPLEMENTATION AUTHORIZATION
NOT A LIVE EXECUTION AUTHORIZATION

Date: 2026-09-16 (reconciliation baseline).
Last updated: 2026-09-22 (D9 offline-implementation-and-correction
reconciliation; D9 package correction; plan-only correction,
binding-findings remediation,
R-001..R-007 remediation, T-001..T-007 plan remediation, T-001 boundary
wording correction, the F-001/F-002 authorized-run-boundary order and D1
wording correction, the B-001 Section 12 preamble correction, the
governance-owner recording of the P2T2-LIVE-D6 sub-decisions, and the owner
binding of the exact committed image-only validator; the update history is in
Sections 11 and 12).

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

Named sub-decision records of the form `P2T2-LIVE-D<n>.<NAME>` (for example
`P2T2-LIVE-D6.MEDIA_VALIDATION_SOURCE`) are required fields of their parent
decision. They add no decision identifier, and a parent decision cannot be
finally approved while any of its sub-decisions is unresolved.

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

`2832455e7cb314cea0fa64a397fbbb84ac914df1` is the
`HISTORICAL_PLANNING_BASELINE_ONLY` documentation commit used by the earlier
reconciliation. The current documentation HEAD for this correction is
`f8533a1ea8b34fd98fa73d1e73139bcfba209bd8`; neither hash is an execution
authorization or a live runtime identity. A future owner approval must receive an externally supplied
`approval_record_commit` after the approval record is committed. The approval
file must never contain its own future commit hash; the execution checkout
must verify that externally supplied commit before any model invocation.

## Canonical reconciliation state (2026-09-21; D9 package correction recorded)

Addendum (2026-09-22): the D9 offline-implementation reconciliation below is
additive to this 2026-09-21 state and does not remove or rewrite it.

- Offline coordinator implementation: COMPLETE
- Offline independent/POSIX verification: COMPLETE WITH FINDINGS CLOSED
- Live coordinator source/test binding: OWNER-BOUND; runtime suitability pending
- P2T2-LIVE-D1: BLOCKED
- P2T2-LIVE-D4: OWNER-APPROVED_PRESTAGED_LOCAL_SNAPSHOT
- D6_BINDING_REVIEW: PASS
- D6_BINDING_PACKAGE: OWNER_APPROVED
- D6_OWNER_DECISION: RECORDED
- P2T2-LIVE-D6 sub-decision `MEDIA_VALIDATION_SOURCE`:
  `RESOLVED: EXACT_COMMITTED_IMAGE_ONLY_VALIDATOR` (Section 2.7.5)
- P2T2-LIVE-D6 sub-decision `MIME_EXTENSION_RULE`: `RESOLVED: REMOVE_REQUIREMENT`
  (Section 2.7.6)
- P2T2-LIVE-D6 overall: NOT FINALLY RESOLVED (fixture identity remains
  `RESOLVED_WITH_PROPOSED_VALUE`)
- P2T2-LIVE-D9: NOT RESOLVED
- D9 numeric ceilings: OWNER_SELECTED_CANDIDATE_ONLY
- D9 stdout/stderr enforcement: SEPARATE_ENFORCEMENT_APPROVAL_REQUIRED
- D9_PACKAGE = DESIGN_RECORD_ONLY
- D9_LIVE_D11_CARRIER_SCOPE = UNKNOWN_UNRESOLVED_PENDING_D11
- D9_PACKAGE_REVIEW = BLOCKED_PENDING_D11_AND_CONTRACT_REVIEW
- D9 = NOT RESOLVED
- D9 numeric ceilings (2026-09-22 note): unchanged; `raw_output_max_bytes=65536`
  and `ipc_envelope_max_bytes=98304` remain `OWNER_SELECTED_CANDIDATE_ONLY`
- D9 stdout/stderr enforcement (2026-09-22 update): OWNER-APPROVED EXACT VALUES
  (`stdout_max_bytes=16384`, `stderr_max_bytes=32768`), approved 2026-09-21 in
  `approvals/TASK_APPROVAL.md`, and implemented offline (authoritative
  checkpoint `86836d2`); this supersedes
  `SEPARATE_ENFORCEMENT_APPROVAL_REQUIRED` for stdout/stderr only
- D9_OFFLINE_ENFORCEMENT_IMPLEMENTATION = IMPLEMENTED_CORRECTED_AND_INDEPENDENTLY_REVIEWED_PASS
  (`tmp/feat018-p2t2-d9-independent-correction-review-20260922/REVIEW.md`)
- D9_OFFLINE_IMPLEMENTATION_COMMIT = `86836d24cfcd83ca14c0bc50e79fff1103cb9ecc`
  (`fix(feat018): close D9 stream enforcement gaps`; sole child of
  `552bc5d939f36b2b87dc7f0cea909110e8750107`)
- D9_OFFLINE_IMPLEMENTATION_SOURCE_BLOB = `e1c89536e612b9f801ff2e429e76f3f0d0c370ee`
- D9_OFFLINE_IMPLEMENTATION_TEST_BLOB = `3a4db7fd56185da82749b95dd42ca1a3bdc13c0d`
- D9 offline no-raw-payload and no-extra-attempt/adapter-call/session
  invariants: independently reproduced and confirmed held
- P2T2-LIVE-D9 (live carrier/session integration): unchanged by the above,
  remains `NOT RESOLVED`
- D9_LIVE_D11_CARRIER_SCOPE = UNKNOWN_UNRESOLVED_PENDING_D11 (unchanged)
- `reviewed_runtime_code_commit` is unchanged by this reconciliation and is
  not rebound to the D9 offline-implementation commit
- P2T2-LIVE-D11: BLOCKED
- P2T2-LIVE-D11 sub-decision `LIVE_SEAM_BINDING`: BLOCKED (Section 2.7.7)
- Stage 4 live-execution approval: NOT READY
- Lightning execution: NOT AUTHORIZED
- FEAT-018 P2-T2 live smoke/model load/model inference/adapter invocation: NONE
- D4 snapshot staging and hardware observation: READINESS-ONLY LIGHTNING
  ACTIVITY; NOT A STAGE-4 RUN

No FEAT-018 P2-T2 live smoke, model load, model inference, adapter invocation,
or Stage-4 runtime execution has occurred.

D4 snapshot staging and hardware observation were readiness-only Lightning
activities. They do not constitute a FEAT-018 live smoke and do not resolve D10
or authorize Stage 4.

The coordinator is implemented and verified offline, and the owner has bound
the reviewed source/test identity. The D4 pre-staged snapshot is now
owner-approved; the D6 MIME/extension sub-decision is resolved by removal and
the D6 media-validation-source binding is owner-approved at the exact commit
`16c52da26c444947ab4388712d9b7310480360b4`. D6 fixture identity remains
proposed. Live-runtime suitability, the approved-caller and concrete live-seam
binding (session controller, preflight, finalizer, and adapter dispatch), and
D1/D11 remain pending. The current HEAD is a planning/documentation identity
only and is not the reviewed runtime source commit. This state does not open
Stage 4 or authorize Lightning.

Historical next sequence, recorded by the 2026-09-17 plan-only correction. Its
first three steps are complete, and its D11 step is superseded by the current
sequence below:

`revised plan -> independent binding review -> owner-bound reviewed runtime commit -> resolve concrete D11 controller -> owner resolution of D1-D12 -> separate Stage 4 approval -> runtime D4 revalidation -> only then Lightning execution`

Current next sequence, after the 2026-09-20 D6 owner binding (Section 11 is
canonical):

`PREPARE_D1_OWNER_RESOLUTION_AND_D6_FIXTURE_BINDING -> approved-caller and concrete live-seam binding under D11 -> D11 resolution -> owner resolution of D1-D12 -> separate Stage 4 approval -> provision session -> SESSION_READY -> D4 runtime/session-local revalidation -> D8 staging and staged digest verification -> exactly one smoke`

Update history, 2026-09-17 through 2026-09-20:

1. The first independent binding review returned `PASS_WITH_FINDINGS`
   (F-001..F-003). The F-001/F-002 plan remediation is recorded in Sections
   2.7.1-2.7.3.
2. The second independent binding review returned `PASS_WITH_FINDINGS`
   (R-001..R-007). The R-001..R-007 plan remediation is recorded in Sections
   2.7-2.7.7, precondition 5, Phases 0-2, Sections 5-8, the P2T2-LIVE-D3, D6,
   and D11 sections, and Sections 9-12.
3. The only current next gate is
   `PREPARE_D1_OWNER_RESOLUTION_AND_D6_FIXTURE_BINDING`. The prior
   `INDEPENDENT_BINDING_REVIEW_RERUN` was satisfied by the independent review
   and is historical. Every earlier `NEXT` value in Sections 11 and 12 is
   historical.
4. The T-001..T-007 plan remediation corrected the preflight evidence boundary,
   cardinality rules, evidence hand-offs, timing/placement wording, approved
   caller binding, import identities, and inventory dependency requirements.
   Its static-validation record is the historical Section 12.2 entry.
5. The 2026-09-18 F-001/F-002 correction aligned the
   `AUTHORIZED_RUN_ATTEMPT_BEGINS` definition with the reviewed source order
   (preflight, lifecycle-boundary construction, counter/state initialization,
   transition, reviewed lifecycle `try`, `finally` cleanup) and corrected the
   D1 planning-disposition wording. Its static-validation record was the
   Section 12.3 entry, now historical.
6. The 2026-09-18 B-001 correction fixed a Section 12 preamble that still
   named an already-superseded section as current; it recorded no plan-level
   decision. Its static-validation record is the historical Section 12.4
   entry.
7. The 2026-09-18 D6 owner-decision recording resolved
   `P2T2-LIVE-D6.MIME_EXTENSION_RULE` to `RESOLVED: REMOVE_REQUIREMENT` and
   set `P2T2-LIVE-D6.MEDIA_VALIDATION_SOURCE` to
   `SELECTED_PENDING_SEPARATE_IMPLEMENTATION_AND_REVIEW` (Sections 2.7.5,
   2.7.6, and 9). D6 overall remains `NOT FINALLY RESOLVED`. At that time, the
   next gate was the separate image-only validator implementation approval and
   independent review, and its static-validation record was the Section 12.5
   entry. Both are now historical: that gate is not the present gate, the
   Section 12.5 entry is not the current validation record, and the later
   item 8 records the subsequent state.

8. The 2026-09-20 D6 owner binding recorded
   `D6_BINDING_REVIEW = PASS`, `D6_BINDING_PACKAGE = OWNER_APPROVED`, and
   `D6.MEDIA_VALIDATION_SOURCE = RESOLVED: EXACT_COMMITTED_IMAGE_ONLY_VALIDATOR`
   at commit `16c52da26c444947ab4388712d9b7310480360b4`. D6 fixture identity
   remains `RESOLVED_WITH_PROPOSED_VALUE`; at that time, the next gate was
   `INDEPENDENT_REVIEW_OF_D6_GOVERNANCE_COMMIT`. The F-002 correction now
   advances the current gate to
   `PREPARE_D1_OWNER_RESOLUTION_AND_D6_FIXTURE_BINDING`. Its static-validation
   record is the historical Section 12.6 entry.

9. The 2026-09-22 D9 offline-implementation reconciliation records that the
   owner-approved exact D9 stdout/stderr ceilings (`stdout_max_bytes=16384`,
   `stderr_max_bytes=32768`, approved 2026-09-21) were implemented at commit
   `552bc5d939f36b2b87dc7f0cea909110e8750107`; that an independent
   post-commit review found four correctness gaps (F1-F4) and returned
   `BLOCKED`; that the correction was applied to the same two authorized
   files only and independently re-reviewed with verdict `PASS`; and that the
   correction was committed as `86836d24cfcd83ca14c0bc50e79fff1103cb9ecc`
   (`fix(feat018): close D9 stream enforcement gaps`), independently
   re-verified by a follow-up commit checkpoint with verdict `PASS`. This is a
   reconciliation of the D9 **offline implementation** only: it does not bind
   a new `reviewed_runtime_code_commit`, does not resolve `P2T2-LIVE-D9` or
   `D9_LIVE_D11_CARRIER_SCOPE` (both remain dependent on the unresolved D11
   live-seam binding), and does not change D1, D6, D11, D4, or Stage 4
   status. Its static-validation record is the current Section 12.7 entry.
   Its first independent review returned `BLOCKED` (F-01..F-06); those
   findings were corrected on 2026-09-22. Its review gate is package-local
   only: `FRESH_INDEPENDENT_D9_GOVERNANCE_RECONCILIATION_REREVIEW`. That gate
   does not replace, supersede, or satisfy the still-open global
   `PREPARE_D1_OWNER_RESOLUTION_AND_D6_FIXTURE_BINDING` gate from item 8,
   which remains the only current next gate (item 3 and Section 11
   `CURRENT`).

These updates do not change the D1, D4, D11, Stage 4, or execution
authorization status. `P2T2-LIVE-D6.MEDIA_VALIDATION_SOURCE` is resolved to
the exact committed image-only validator, and
`P2T2-LIVE-D6.MIME_EXTENSION_RULE` remains resolved to
`RESOLVED: REMOVE_REQUIREMENT`; both are recorded in Section 9. D4
runtime/session-local revalidation remains Stage-4-local after `SESSION_READY`.
The 2026-09-22 D9 offline-implementation reconciliation in item 9 does not
change any of these facts and does not resolve `P2T2-LIVE-D9`.

## 1. Objective and exact scope

The proposed future smoke run is exactly one owner-approved, non-sensitive
JPG/PNG image through the existing backend-only FEAT-003
VisionUnderstandingResultV2 boundary and the existing qwen_vision.py
QwenVisionAdapter, followed by the existing FEAT-018
map_vision_result_to_raw mapper. The run records one typed V2 outcome and one
mapped RawUnderstandingResultV1 outcome, or a typed terminal outcome if a
stop gate fires.

The run records truthful cardinality at the phase boundary; it never fabricates
a call or attempt. The plan-only T-001 resolution is
`PREFLIGHT_PREAUTHORIZATION_NO_EVIDENCE_PAIR`: the reviewed preflight call
occurs before the coordinator constructs its lifecycle boundary, initializes
its counters and lifecycle state, and enters the reviewed lifecycle `try`
whose `finally` owns cleanup. `AUTHORIZED_RUN_ATTEMPT_BEGINS` is the
plan-level transition immediately before entry into that reviewed lifecycle
`try`, after successful preflight, successful lifecycle-boundary construction,
and successful counter/state initialization (Section 4, "Authorized-run
transition"). A preflight return or exception, or any other failure before
that transition, is not an authorized run attempt. It returns
`adapter_call_count=0`, `attempt_count=null`, and produces no live evidence pair,
incident record, or finalizer call. The owner must ratify this boundary in the
D11/Stage-4 approval; D11 remains blocked until then.

- A stop after that authorized-run transition but before invoking the adapter
  records `adapter_call_count=0` and `attempt_count=null` and must use the
  bound cleanup/finalization path. This includes in-session checkout
  revalidation, D4 snapshot runtime revalidation, staged-fixture digest,
  observed readiness/hardware, runtime-manifest, and TTL/budget/session-gate
  stops. No V2 or Raw result is claimed.
- Once the adapter-dispatch wrapper is invoked, the coordinator records
  `adapter_call_count=1`. Input validation, containment/launch failure,
  dispatch exception, invalid result, or a pre-attempt hang records
  `attempt_count=null` because no accepted generation-start event exists. The
  adapter's typed input result may carry `attempt_number=0`; that adapter-local
  field is not the coordinator's `attempt_count`.
- A model-reaching adapter call records `adapter_call_count=1` and
  `attempt_count` in `{1, 2}`. Attempt 2 is permitted only after an explicitly
  classified transient runtime failure on attempt 1, inside the one adapter
  call. It never becomes 3 and there is no outer retry.

Every authorized run attempt that passes `AUTHORIZED_RUN_ATTEMPT_BEGINS` writes
exactly one sanitized JSON/Markdown evidence pair, including a post-transition
pre-adapter terminal outcome. A preflight rejection, or any other failure
before that transition, is pre-authorization and has no live evidence pair,
incident fallback, or finalizer call. If evidence creation is impossible after
the authorized transition, the harness writes only a safe local ignored incident
record at `tmp/feat018-live-lightning-incident-<run_id>/INCIDENT.md`; that
incident is not indexed and never substitutes fabricated call or attempt values.

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

The reviewed `run_live_smoke` signature receives an already constructed
`runtime_config` before it calls preflight (`feat018_live_lightning_execution.py`
L3223-3226). The approved caller must therefore construct
QwenVisionRuntimeConfig explicitly from one owner-approved configuration file
in the environment where that caller actually runs. The construction boundary
is exactly `QwenVisionRuntimeConfig.from_env_file(
approved_environment_relative_env_file, environ={})`; ambient process environment
values must not be merged. The exact file identity, the selected
model_dir/model_cache_dir choice, device, device_index, and
allow_model_download fields are recorded under P2T2-LIVE-D11 and
P2T2-LIVE-D4/D10 before approval. In pseudocode:

    QwenVisionRuntimeConfig.from_env_file(
        approved_environment_relative_env_file,
        environ={},
    )

The selected file must provide the exact
SKETCH2LIFE_VISION_MODEL_DIR or SKETCH2LIFE_VISION_MODEL_CACHE_DIR,
SKETCH2LIFE_VISION_DEVICE, SKETCH2LIFE_VISION_DEVICE_INDEX, and
SKETCH2LIFE_VISION_ALLOW_MODEL_DOWNLOAD values approved in
P2T2-LIVE-D4 and P2T2-LIVE-D10. The file is ignored runtime configuration,
never committed, and never copied into evidence. `from_env_file` interprets
the path in the environment where that call executes; a host-local Windows
path is never presumed to exist in the Lightning session. Because
`run_live_smoke` receives its already-built `runtime_config` before preflight,
the approved caller must either run in the environment that owns the file or
use a separately reviewed typed hand-off whose identity is revalidated by the
session controller. The reviewed source provides neither hand-off. Until
caller placement, file placement, and the configuration-loading/revalidation
boundary are bound and reviewed, the preflight must fail closed before
`AUTHORIZED_RUN_ATTEMPT_BEGINS`.

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
is never logged or written to either evidence file. The approved caller must
resolve and hash the exact prompt text immediately before invoking the reviewed
`run_live_smoke` boundary, then pass that same immutable string through the
explicit `prompt=` argument; a prompt-builder default is not acceptable. The
reviewed call order does not expose a separate prompt seam between the
`run_live_smoke` call and the adapter-count increment. If a future approval
requires a later last-mile rehash, it must bind a separately reviewed pre-count
seam under D11; hashing inside the current `BoundedAdapterCall` would occur
after the coordinator records the adapter call and would produce the
`1/null` in-dispatch terminal defined below.

The selected caller-side check is:

    sha256(prompt_text.encode("utf-8")).hexdigest() == approved_prompt_sha256

The comparison is an in-memory self-check; the prompt text is not persisted or
logged. A mismatch, missing caller-side typed fact, or change in the string
between this check and the reviewed boundary is a pre-authorization terminal
with `adapter_call_count=0` and `attempt_count=null`; it produces no live
evidence pair under the selected T-001 rule. The adapter-dispatch binding must
prove that it passes the exact checked string unchanged. Changing or adding a
FEAT-003 prompt is outside this plan and requires a separate approval. The
decision is P2T2-LIVE-D7.

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
offline, but live-runtime suitability and the concrete live-seam binding
(Section 2.7.7) still require the remaining owner gates. A later live approval must verify the exact
reviewed source commit and prove the real nested spawn, descendant containment,
and two-level cleanup assertions listed in Section 5. A model factory, the old in-process runner, the old unbounded
subprocess IPC, and persistent raw-output diagnostic sinks are not live
alternatives.

The per-attempt child deadline is exactly 120 seconds and covers loading,
generation, and decoding. A separate positive `total_adapter_cap_seconds`
covers the entire single adapter call, including a possible second attempt,
without resetting on retry. Readiness may inspect versions, hardware, and the
approved pre-staged local snapshot without loading weights; it must not preload
weights. The selected snapshot is approved under D4, but model loading remains
prohibited until the separate Stage 4 approval and its child deadline.

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
  the concrete live-seam binding (Section 2.7.7) remain pending. FEAT-003
  source remains unchanged.
- `backend/tests/unit/test_feat018_live_lightning_execution.py`: offline tests
  with injected seams plus synthetic local process-boundary tests only; no
  Lightning/provider/model execution occurs. It covers the existing raw and
  IPC overflow, per-attempt timeout and total-cap termination, child/IPC
  cleanup on success and failure, pre-adapter `0/null`, bounded-dispatch
  failures with `1/null`, model-reaching `1/1`, explicitly transient retry
  `1/2`, no third or outer retry, and evidence-pair hash/rename integrity.
  The D9 stdout/stderr capture, byte-accounting, finalization, leakage, and
  platform cases remain future implementation/test requirements because the
  reviewed runtime currently only declares/validates those fields and has no
  stream capture or enforcement. It does not claim a dedicated
  adapter-input-rejection case; that path is represented by the adapter's
  typed `attempt_number=0` while the host cardinality remains `1/null`.
  Prompt-hash selection,
  device placement, full evidence redaction and incident handling are covered
  by offline injected coordinator seams; live-runtime suitability and the
  concrete live-seam binding (Section 2.7.7) remain pending. The verification
  evidence is
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
  offline seams; live-runtime suitability, the concrete live-seam binding
  (Section 2.7.7), and the D1/D11 gates remain pending; D4 snapshot readiness
  is owner-approved:

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

## 2.7 Stage-4 approval identity and binding sets

The Stage-4 approval record binds:

- `reviewed_runtime_code_commit`;
- the fully resolved P2T2-LIVE-D1 through P2T2-LIVE-D12 values; and
- the exact approval inputs, evidence paths, redaction, cleanup, and rollback
  rules.

The approval record does not contain its own future Git commit hash.
`approval_record_commit=EXTERNALLY_SUPPLIED_AFTER_APPROVAL_COMMIT`. After the
owner signs and the approval is committed, an external execution record supplies
the exact 40-hex `approval_record_commit`. Before any authorized run:

`git rev-parse HEAD == approval_record_commit`

The reviewed implementation evidence set is exactly:

- `backend/src/sketch2life/benchmark/feat018_live_lightning_execution.py`
- `backend/tests/unit/test_feat018_live_lightning_execution.py`

These two blobs establish the reviewed FEAT-018 implementation/test identity.
They are not the complete runtime semantic dependency set. Before Stage 4, an
independent binding review must enumerate and freeze every runtime-semantic
dependency actually consumed by the live path, including at minimum:

- `backend/src/sketch2life/benchmark/feat018_live_lightning_execution.py`;
- the concrete approved host caller that constructs the runtime config,
  content policy, request, and preflight input and invokes `run_live_smoke`;
  its exact repository-relative module path and immutable identity are a
  required D11 binding input because no caller implementation is present in
  the reviewed two-file source boundary;
- `backend/src/sketch2life/infrastructure/ai/qwen_vision.py`;
- `backend/src/sketch2life/application/services/raw_understanding_mapper.py`;
- `backend/src/sketch2life/infrastructure/ai/qwen_vision_runtime_config.py`;
- `backend/src/sketch2life/infrastructure/ai/qwen_vision_environment_readiness.py`
  (Section 2.7.2);
- `backend/src/sketch2life/benchmark/vision_c1_prompt_mapping_study.py`;
- `backend/src/sketch2life/infrastructure/ai/vision_lexical_policy.py`;
- the complete P2-T1 D2 image-admission dependency closure in Section 2.7.1;
- the runtime schema dependencies `vision_v2.py` (including the V2
  profile/catalog definitions), `vision.py`, `raw_understanding.py`, and
  `media_validation.py`, enumerated in Section 2.7.2;
- the import-time closure classified in Section 2.7.4;
- the owner-bound image-only media-quality validator closure recorded under
  `P2T2-LIVE-D6.MEDIA_VALIDATION_SOURCE` at commit
  `16c52da26c444947ab4388712d9b7310480360b4` (Section 2.7.5);
- `P2T2-LIVE-D6.MIME_EXTENSION_RULE` is `RESOLVED: REMOVE_REQUIREMENT`; no
  MIME/extension enforcer is bound or required (Section 2.7.6);
- the concrete live seams bound under `P2T2-LIVE-D11.LIVE_SEAM_BINDING`:
  `LightningPreflight`, `LightningSessionController`,
  `LightningSmokeFinalizer`, and the adapter-dispatch wrapper (Section 2.7.7);
- the exact per-environment interpreter and installed-distribution inventories
  required by Section 2.7.2; and
- any other imported module whose semantics can change the approved live path.

The binding review must prove that the approved execution checkout preserves
the frozen dependency list and reviewed blobs. A test file remains part of
implementation-review evidence; it is not itself a runtime semantic
dependency.

### 2.7.1 P2-T1 D2 image-admission runtime dependency closure

This subsection was added by the 2026-09-17 binding-findings remediation,
responding to independent binding review finding F-001. The R-001..R-004
remediation corrected it.

Precondition 5 and Phase 0 require the fixture's P2-T1 D2 image-admission
outcome to be exactly `AdmissionOutcome.ADMITTED` before any vision call. D2
records exactly five outcomes: `ADMITTED`, `REJECTED`, `UNSUPPORTED`,
`INVALID_SOURCE`, and `PROCESSING_FAILURE`
(`domain/understanding/image_admission.py` L15-22). Every non-`ADMITTED`
outcome carries exactly one `AdmissionReason` (L25-26).

`ADMITTED` grants only eligibility for further validation (L16).

- The approved D1 specification states that `ADMITTED` is not a quality PASS
  and not permission to call a model. It also states that the adapter's
  media-validation ingress checks remain the gate on inference, unweakened
  (`evidence/P2_IMAGE_ADMISSION_SPEC_20260910.md` L105 and L123-125).
- D2 emits no `MediaValidationResultV1` (specification L95-96; service
  docstring `application/services/image_admission.py` L48-50).

This plan therefore never records `ADMITTED` as `PASS` and never derives
`media_validation` provenance from an admission result. Media-quality
validation is a separate gate (Section 2.7.5).

The admission implementation, its decoder, and its schema and manifest inputs
are runtime semantic dependencies of the live path.

The reviewed runner/coordinator source does not import this closure or the
readiness module in Section 2.7.2. Pre-adapter results reach the reviewed
coordinator only through its injected Protocols, and the reviewed source
contains no concrete implementation of them. Under the ownership map in
Section 2.7.7:

- D2 admission is owned by the future concrete `LightningPreflight` (host,
  Phase 0).
- The no-model-load readiness check is owned by the future concrete
  `LightningSessionController` (inside the session, Phase 1).

Both identities must be bound under `P2T2-LIVE-D11.LIVE_SEAM_BINDING` before
D11 can be resolved. The current boolean `LightningPreflightFacts`
(`feat018_live_lightning_execution.py` L2004-2032) do not carry the admission
outcome or reason.

The complete D2 closure is:

| Role | Repository-relative path | Semantic role in the live path | Git blob at `f8533a1` | SHA-256 of Git blob content |
|---|---|---|---|---|
| Admission service | `backend/src/sketch2life/application/services/image_admission.py` | `Feat018ImageAdmission` (L56) and `admit` (L65): one bounded source-byte snapshot, snapshot SHA-256, policy evaluation, and `SourceMediaReferenceV1` construction | `3ff03149e19650a7bbc34d7999678019030ce137` | `aab3b39c864ff0a7646645a5541fd56c0606997a80f7b23f745eb96e2cdf32cf` |
| Admission domain policy | `backend/src/sketch2life/domain/understanding/image_admission.py` | `Feat018AdmissionLimits` (L67) plus the outcome/reason mapping and the metadata, frame-count, and decode cross-check rules | `cfe3253655faea33a7cff02249f163d0b8b332ab` | `34480da59fd2436db6a4fc92380fc0ad9284e8f4eb4c46b61cd2578aab349df5` |
| Decoder adapter | `backend/src/sketch2life/infrastructure/media_validation/av_image_decoder.py` | `AvImageDecoder` (L29); the only module that imports `av` (L12-13) | `a070b44ca4323605e2bbbe206812c1ab8b102928` | `08beafb474e9cc0c7a4a00878129894ded3335e4bfbceaae8caf572b79378769` |
| Decoder port | `backend/src/sketch2life/application/ports/image_decoder.py` | `ImageDecoderPort` (L36) and the typed decode errors that the service maps to admission reasons | `48dd8e4da64f5f95c0f35c89dc9dd985447adcae` | `6ff48559c1a98953ec0e844d10323940106559282921d7ba60a64727997f30dc` |
| Media-validation schema | `backend/src/sketch2life/contracts/schemas/media_validation.py` | Pydantic contracts (import L7): `SourceMediaReferenceV1` (L18), constructed by the admission service; `MediaValidationResultV1` (L58); and `media_validation_contract` (L128) | `951c44f5269ea3cc17024dd37aaeb9765727a00e` | `2e247d60c729e900979fa5a0b5f44efe641701481b1129d2bced2fb8c66394f9` |
| Transitive domain import | `backend/src/sketch2life/domain/understanding/media_quality.py` | Imported when `media_validation.py` loads (L9-15): `MediaDecision`, `MediaRecaptureReason`, and the signal/assessment types. It imports only the standard library. F-001 did not list it; this remediation's import check identified it | `cfc83496e084734d08de95ac945e02f8402469cc` | `b6e61211c9baacca1e10927fb3e16461edc8b04938d0014d1781f501edc4a44c` |
| Dependency manifest | `backend/pyproject.toml` | Optional extra `image-admission` with the exact pin `av==18.1.0` (L54-56), plus the base-runtime ranges recorded in Section 2.7.2 | `8f8a344f505be839b9bd0bd0d640fa0d18cf6b33` | `9ca3a54905d11fdb7f30a84356d23741f256b2115b254bcc9fba4efacdf17df6` |

The Stage-4 approval must bind these identities together with the admission
inputs actually used for the run:

- the constructed `Feat018AdmissionLimits` values, including the byte, pixel,
  edge, and frame limits and the container, codec, and pixel-format allowlists;
- the injected decoder implementation;
- the required admission outcome, exactly `ADMITTED`, and the requirement that
  the admission snapshot digest equal the D6 `source_sha256`; and
- the recording and verification rules for the observed admission outcome in
  Section 2.7.7.

The `media_validation` provenance is bound separately under Section 2.7.5. It
is never supplied for, or derived from, an admission result.

The D2 closure above contains no MIME-type or filename-extension comparison. It
classifies the byte snapshot by container, codec, and pixel format only
(`domain/understanding/image_admission.py` L80-82 and L136-145). D2 is
therefore not a MIME/extension enforcer. The owner decision on that
requirement, `P2T2-LIVE-D6.MIME_EXTENSION_RULE` (Section 2.7.6), is
`RESOLVED: REMOVE_REQUIREMENT`; D2's admission responsibilities above are
unchanged by that resolution.

### 2.7.2 Readiness, schema, and base-runtime closure

This subsection was added by the 2026-09-17 binding-findings remediation,
responding to independent binding review finding F-002.

The following are runtime semantic dependencies:

- the no-model-load readiness check and its configuration input. The check is
  owned in-session by the concrete session controller (Section 2.7.7); and
- the runtime schemas consumed by readiness, by the V2 adapter boundary, by the
  mapper, and by D2 admission.

| Role | Repository-relative path | Semantic role in the live path | Git blob at `f8533a1` | SHA-256 of Git blob content |
|---|---|---|---|---|
| No-model-load readiness | `backend/src/sketch2life/infrastructure/ai/qwen_vision_environment_readiness.py` | `inspect_qwen_vision_environment` (L244) and `inspect_qwen_vision_environment_from_env_file` (L346). It defines Pydantic readiness models (import L14), consumes the V2 catalog and hash functions (L16-21) and `QwenVisionRuntimeConfig` (L22-24), and compares only the four profile dependency pins | `0bafefdbaa4394e680ac19145118a5af01f7d564` | `8652d72be48d6671011e78e08bd73053943ac3eacf408abfcbbd99432f57c26a` |
| Readiness configuration input (already listed in Section 2.7) | `backend/src/sketch2life/infrastructure/ai/qwen_vision_runtime_config.py` | `QwenVisionRuntimeConfig`, loaded by the readiness `from_env_file` path | `a7c7ec8b848f6b3166561071c4022693d8fe5d1c` | `6c790946bd27b079b1441b02b9e5bc13b419acf1652add350bbcbf1891445870` |
| Runtime schema | `backend/src/sketch2life/contracts/schemas/vision_v2.py` | V2 request/result contracts; the `QWEN3_VL_8B_INSTRUCT_BF16_V1` profile and its exact dependency pins (L193-198); the V2 catalog (L217); and the config/catalog hash functions (L223, L232). Pydantic import at L18; imports `vision.py` (L20-32) | `15dc773cbfb1d903756abbe3cdf3485ec15e0357` | `ee7d35c7dbdc2d8661aa6da1b4b43ae82f21d4092519b36614193d55e905470e` |
| Runtime schema | `backend/src/sketch2life/contracts/schemas/vision.py` | Version-neutral value objects reused by V2 and Raw (`VisionImageReferenceV1`, `ObservedTextV1`, the candidate types, the error enums) and `VISION_POLICY_MATCH_VIEW_VERSION` (L16). Pydantic import at L13 | `6a3f326174f1ad11258700a1d0f95685d571465f` | `c3f2719c593d443404b90e22013dcaec4cd8befed9dc6a985c0214766c3a90f4` |
| Runtime schema | `backend/src/sketch2life/contracts/schemas/raw_understanding.py` | FEAT-018 `RawUnderstandingResultV1`, the mapper's output contract. Pydantic import at L12; imports `vision.py` (L14-17) and `vision_v2.py` (L18-21) | `81f952171a8d9dca344eac65d4b43c43d86530e0` | `09a6ce19946656690940e7a3c23a05ed23ef51ad65bf661028219e393aaf196c` |
| Runtime schema | `backend/src/sketch2life/contracts/schemas/media_validation.py` | `SourceMediaReferenceV1`, produced by D2 admission; the same identity as in Section 2.7.1 | `951c44f5269ea3cc17024dd37aaeb9765727a00e` | `2e247d60c729e900979fa5a0b5f44efe641701481b1129d2bced2fb8c66394f9` |

`backend/pyproject.toml` declares the base runtime only as ranges, which are
not exact identities:

- Python: `requires-python = ">=3.12,<3.14"` (L10);
- `pydantic>=2.11,<3` (L16), imported by the runtime schemas and by the
  readiness and Qwen adapter modules;
- `pydantic-settings>=2.10,<3` (L17), a declared base dependency of the
  backend project. It is record-only for this plan. Its only importer,
  `backend/src/sketch2life/infrastructure/config/settings.py` L10, is imported
  by no module in the frozen closure, so it is not a runtime-semantic
  dependency of the live path; and
- the exact optional pins already declared: `av==18.1.0` (L55) and the four
  `vision-qwen` pins `accelerate==1.10.1`, `qwen-vl-utils==0.0.14`,
  `torch==2.8.0`, and `transformers==4.57.6` (L45-48).

No Python dependency lockfile exists in the repository. There is no `uv.lock`,
`poetry.lock`, `Pipfile.lock`, `pdm.lock`, `pylock*.toml`, or pinned
requirements or constraints file. The only tracked lockfile, `pnpm-lock.yaml`,
belongs to the JavaScript workspace and pins no backend Python package. The
ranges above therefore do not identify the interpreter or the packages that a
future run would actually use.

Before Stage 4, the owner-bound runtime binding must include one immutable
runtime-environment inventory for each execution environment. The R-006
remediation replaced the earlier single-environment wording. The environments
follow the placement in Section 2.7.7, which
`P2T2-LIVE-D11.LIVE_SEAM_BINDING` must confirm:

- **Host environment.** It runs the approved caller and the concrete
  `LightningPreflight`:
  - the approved caller's exact bound module and its caller-side prompt/config/
    request construction dependencies;
  - D2 admission, which imports `av`;
  - the media-quality validation to be selected under Section 2.7.5, once
    separately implemented and reviewed;
  - no MIME/extension enforcer (Section 2.7.6 is
    `RESOLVED: REMOVE_REQUIREMENT`);
  - prompt resolution and policy construction;
  - the host-side `run_live_smoke` coordination, lifecycle boundary, and
    finalizer.
- **Lightning session environment.** It runs:
  - the in-session checks of the concrete `LightningSessionController`:
    checkout, dependency and hardware facts, readiness, staging, and the
    runtime manifest;
  - the adapter-dispatch target: the supervisor, adapter worker, generation
    child (which imports `torch` and `transformers`), adapter, and worker-local
    mapper.

Each inventory must record:

- the exact interpreter identity: implementation, full version including the
  release level, and build/ABI identity, recorded without absolute paths;
- the complete installed-distribution inventory visible to that interpreter:
  the normalized name and exact version of every installed distribution,
  including transitive dependencies, not only the packages that repository
  code imports directly; and
- the repository-relative path and Git blob identity of every internal module
  in that environment's frozen closure, including the approved caller and
  every concrete D11 seam; a caller or seam with no immutable identity is a
  binding failure.

The runtime-semantic packages that must also match their declared pins or
ranges are:

- **Host:** `pydantic`, `av==18.1.0`, the dependencies of the validator and
  enforcer selected under Sections 2.7.5 and 2.7.6, and the dependencies of
  every concrete D11 seam and the approved caller placed on the host,
  including any provider SDK.
- **Session:** `pydantic`, `accelerate==1.10.1`, `qwen-vl-utils==0.0.14`,
  `torch==2.8.0`, and `transformers==4.57.6`, plus the dependencies of every
  concrete D11 seam and the approved caller placed in the session, including
  any provider SDK.

Notes on those packages:

- No module in `backend/src` imports `accelerate`. It is used through the
  `transformers` loading path with `device_map="auto"` (`qwen_vision.py` L431).
- No module in `backend/src` imports `qwen-vl-utils`; it is version-checked
  only.
- `pydantic-settings` is record-only in both environments.

If the owner binds a single environment for both roles, the binding must say
so explicitly and still record the complete inventory. Each inventory must
have an immutable identity recorded by the Stage-4 approval. This remediation
does not modify `backend/pyproject.toml`, add a lockfile, install anything, or
choose the inventory format.

These pre-Stage-4 inventories are distinct from the in-session sanitized
evidence manifest `P2T2-LIVE-RUNTIME-MANIFEST-V1` in Section 3A. Neither
remediation changes the Section 3A allowlist or the four exact Qwen pins in
precondition 7. The Stage-4 approval must define how each frozen inventory is
verified at runtime and whether any additional fact is recorded in evidence.

### 2.7.3 Identity basis, non-coverage, and future verification

**Identity basis.** The Git blob IDs in Sections 2.7.1, 2.7.2, and 2.7.4 are
`git rev-parse <commit>:<path>` values observed at the current documentation
HEAD `f8533a1ea8b34fd98fa73d1e73139bcfba209bd8`. The SHA-256 values hash the
Git blob content (`git cat-file blob <commit>:<path>`), not the checked-out
bytes, whose line endings can vary by platform.

The approved caller is also part of the required identity set, but its
identity is intentionally not fabricated here: the reviewed source contains
no concrete caller module. D11 must bind the exact repository-relative module
or approved external entry, its immutable source/blob and content identity,
its environment placement, and its review record before that caller can
participate in an authorized run. A missing caller identity is fail-closed.

**Non-coverage.** These values are read-only reference observations, not frozen
bindings or owner approvals. They are not covered by
`reviewed_runtime_code_commit` = `9549a341194f40b1a9be419d6fce0d70f1ca0384`.
That owner binding identifies only the two reviewed FEAT-018 implementation
source/test blobs listed at the start of Section 2.7. Both blob IDs were
verified identical at `9549a34` and `f8533a1`:

- `backend/src/sketch2life/benchmark/feat018_live_lightning_execution.py`,
  blob `94db10bedf95ab105f6c8653adac991bce94fa35`; and
- `backend/tests/unit/test_feat018_live_lightning_execution.py`, blob
  `d7846f22fddf55ae234387e9e43d504a848112ee`.

**Future verification.** The complete runtime dependency set must be frozen
before Stage 4 and verified in the future approved execution checkout before
any model invocation. That set comprises:

- the two reviewed blobs;
- every module in the transitive runtime import closure, including static and
  dynamic imports (the lists in Section 2.7 and its subsections are a minimum,
  not the complete closure);
- the concrete approved host caller, including its exact repository-relative
  entry module, immutable source/blob and content identity, environment
  placement, and dependencies;
- the concrete live seams bound under `P2T2-LIVE-D11.LIVE_SEAM_BINDING`
  (`LightningPreflight`, `LightningSessionController`,
  `LightningSmokeFinalizer`, and the adapter-dispatch wrapper), once bound;
- the owner-bound image-only validator selected under the D6 sub-decisions;
  no MIME/extension enforcer is selected; and
- the per-environment interpreter and installed-distribution inventories.

Any mismatch with a frozen identity is a dependency-mismatch stop under
Section 6. The planning checkout's observations above cannot substitute for
that verification.

### 2.7.4 Import-time closure classification

This subsection was added by the 2026-09-17 R-001..R-007 remediation (R-007)
and completed by the T-006 plan remediation. It classifies modules that the
live path or the approved caller loads at import time but that Sections 2.7.1
and 2.7.2 did not list.

- **Identity basis.** It is the same as in Section 2.7.3.
- **Status of the values.** The values are read-only reference observations,
  not owner bindings. They are not covered by `reviewed_runtime_code_commit`.

The table below contains 21 rows: ten runtime modules and eleven package
initializers. The four core modules named in Section 2.7 are included here as
`REQUIRED`; their identities remain reference observations until the future
Stage-4 approval binds the complete closure.

Classes:

- `REQUIRED`: loaded on the live path or by the approved caller; must be frozen.
- `EXCLUDED`: not loaded on the live path; must not be added silently.
- `FUTURE-BOUND`: outside the path until a named owner decision binds it.

Paths are relative to `backend/src/sketch2life/`. The expected environment
follows Section 2.7.2 and is subject to the placement confirmed under
`P2T2-LIVE-D11.LIVE_SEAM_BINDING`.

| Module | Loaded by | Expected environment | Class | Semantic role | Git blob at `f8533a1` | SHA-256 of Git blob content |
|---|---|---|---|---|---|---|
| `infrastructure/ai/qwen_vision.py` | coordinator L42-48; worker adapter construction L1639-1644 | host and session | `REQUIRED` | `QwenVisionAdapter`, explicit prompt/config boundary, and Qwen runtime adapter | `7f4aecb4d189d1fbd494992fd38a09d80d6ba27f` | `549a87b4ba5149bb0dcb8f729608a2dfeb5a2a147b3de227183e5fe33c5e194e` |
| `application/services/raw_understanding_mapper.py` | coordinator L39; worker-local mapping L1655-1660 | host and session | `REQUIRED` | `map_vision_result_to_raw` and the typed V2-to-Raw boundary | `8af2a6c2f53e9094575115e0186d54a60a9eff14` | `0a0e5356b042856dcd788e3abf1ff30c7044c6d0bb95e3dc8aebb07903bf7aea` |
| `benchmark/vision_c1_prompt_mapping_study.py` | approved caller's C1-v2 prompt-resolution path; imports L97-116 | host | `REQUIRED` | C1 prompt protocol/source identity and exact UTF-8 verification | `12e1411c319c56ba9847c7aaefead7acc9ce0edf` | `b1c32404ae9da9c6fb930154b43c844a5b28994eee0e69bc0790e306b21338a6` |
| `infrastructure/ai/vision_lexical_policy.py` | approved caller's explicit policy construction; imports L11-20 | host | `REQUIRED` | synthetic lexical regression policy implementation and lexicon factory | `eef0484affadcb863b84e829790c10ed9b12d1b0` | `3d05a370042573b23aeb43b5db1bdc69c11c206c55d6a896df57ecdff0647382` |
| `application/ports/vision_content_policy.py` | coordinator L37; `infrastructure/ai/qwen_vision.py` L29; `infrastructure/ai/vision_lexical_policy.py` L11; `benchmark/vision_c1_prompt_mapping_study.py` L97 | host and session | `REQUIRED` | `ObservableContentPolicyV1` Protocol for the injected policy | `00e93c43d2567768a80cb941292af790d5ebb57c` | `d927f56b91a758fabb9734dc34c7a1cd69f8b5213bf6e96ea79213677a102ff8` |
| `application/ports/vision_understanding_v2.py` | `qwen_vision.py` L30; C1 study L98; B3 study L61 | host and session | `REQUIRED` | `VisionUnderstandingPortV2` Protocol implemented by the adapter; import-time only | `9e7506c4c7223ceaf0cfe9c25c5c747a99b15512` | `0d21de16c869c1777cf0ca0924dffb6081f4addf9fce221c2d7952a177221bd4` |
| `contracts/schemas/asr.py` | `application/services/raw_understanding_mapper.py` L7-12 | host and session | `REQUIRED` | Import-time schema and the `asr_result` type. The live branch is `_map_asr(None)`, which yields `NOT_SUPPLIED` (mapper L185-189). ASR execution stays excluded by P2T2-LIVE-D3 | `4035daf703de9f8bdab4b5536943434709610b29` | `1dcf8db144ebfd080266f05b8e75ae404ec230edc7983937a0e598e48c0b9b22` |
| `benchmark/vision_b3_mapping_study.py` | C1 study L99-103 | host | `REQUIRED` | Import-time only, in the process that resolves the C1-v2 prompt. `c1_prompt_text_v2` (C1 L269) does not use it | `6890f974dc6ec11fabc09f23f210817db485a8b5` | `53fc38b3a65d0400add71648db07f0f86b825163afc0b89f0e38988d92b4e40c` |
| `application/services/media_validation.py` | B3 study L62-65, through the C1 import | host | `REQUIRED` | Import-time only today. The audio-bearing `DeterministicMediaValidator` remains excluded from the image-only path; the owner-bound image-only validator is `feat018-image-only-structural-validator-v1` at commit `16c52da26c444947ab4388712d9b7310480360b4` (Section 2.7.5) | `c592be22cf0c1f3fe46f1e3c787039f9e70038c1` | `baa00b4d72f05ffcd1aafdf934726ea967d49ac16a6801c37bcf8aece7e94264` |
| `infrastructure/media_validation/file_inspector.py` | B3 study L81, through the C1 import | host | `REQUIRED` | Import-time only today. It imports only the standard library and `media_quality` (L6-18). Its semantic use is `FUTURE-BOUND` under the same D6 sub-decision | `6b309c804af56704686e90e73276284af67920d3` | `3f8ef6d85a272b64c5770721fe9cc3e3741f073feea89042db44e0a781602238` |
| `__init__.py` | every import below `sketch2life` | host and session | `REQUIRED` | Package initializer; no import statements | `949578614ac9d0a6a57dc1dfba6898bc99d5ed44` | `0c34d1364aac564dff44a914a7071e5958e6b901b374ea9cfe97c28796da62f0` |
| `benchmark/__init__.py` | coordinator and C1 study imports | host and session | `REQUIRED` | Package initializer; no import statements | `e87e12948b7ffe86b74321957963bc0d8e418507` | `87205633ee3166d596a7460617a17a26cf0f70eef0e32f2f3757cfc2fb18d45d` |
| `application/__init__.py` | port, service, and mapper imports | host and session | `REQUIRED` | Package initializer; no import statements | `a096c50d5d4bcd879f053737be3bee8bfac16335` | `963cdb872a3f9a65383213656d375c28d13cb105aeec35bd40bbb1c328b3ff72` |
| `application/services/__init__.py` | mapper, D2 service, and media-validation service imports | host and session | `REQUIRED` | Package initializer; no import statements | `eb0e684621e2bf4d0276a295933755cdabf81bf3` | `5781d7d2ff602ff93af7ec8d3c362835c5ed867b71656bfecdf3649d73ae9877` |
| `application/ports/__init__.py` | port imports | host and session | `REQUIRED` | Package initializer; no import statements | `65393d139afa1f9e49ae7d2b2eb732d08156ae8c` | `d2d8ca6d469947c81dcc49339b428fa2590297aeb586bebab65861c6a92f4693` |
| `contracts/__init__.py` | schema imports | host and session | `REQUIRED` | Package initializer; no import statements. `contracts/schemas/` has no `__init__.py` (namespace package) | `f10e250e521404bdaaf865ad9f9ceecdadc8caac` | `7cf1b25017c51d873ec0df29df3fefe985f59a86440270f0b43c087d048ee181` |
| `domain/__init__.py` | domain imports (D2 policy and the `media_quality` import of `contracts/schemas/media_validation.py`) | host | `REQUIRED` | Package initializer; no import statements | `1e928d8910dade6848c22b9eae2a01a8c2560228` | `0e3e8b018753cf959c3f07f510c21ae15ecff64e1f56a9656bc21f0d80dab02f` |
| `domain/understanding/__init__.py` | admission and media-quality imports | host | `REQUIRED` | Package initializer; no import statements | `33bfb05a0b5a2be6ef457cee88227bc9ac938593` | `a44c6d274ad18bd24bfcc520bf290edb9d09f3c8e0b65cbc4f03f2b98927235e` |
| `infrastructure/__init__.py` | infrastructure imports | host and session | `REQUIRED` | Package initializer; no import statements | `bbd299b150359c694491ab5bd4d1f51ddf8a3ec4` | `4f73be91577bd895239ef8942261a85284598ab599f5627af86b999522f01ee4` |
| `infrastructure/ai/__init__.py` | adapter, runtime-config, readiness, and policy imports | host and session | `REQUIRED` | Package initializer; no import statements | `7bfbbed020215a05e0e94d4fd6d7674a3f9b5ef9` | `f1f31ad1e044ad248bad04f3fe2b73edeca97bf739fbac63877db09b2780b4d7` |
| `infrastructure/media_validation/__init__.py` | decoder and inspector imports | host | `REQUIRED` | Package initializer; no import statements | `f53ae2239387c9c3e259e6b55f694732ed6c4420` | `e01846c407bb29fd127649dc9c54639dc7e7c23b25b6842f0419268f2a49fc11` |

The following modules remain outside the live path. Adding any of them
requires a named owner decision and a new binding review.

- `benchmark/image_admission_evaluation.py` (blob
  `84e95d63363152f6f9692d396fa03d363e77db4f`): `EXCLUDED`.
  `P2T2-LIVE-D6.MIME_EXTENSION_RULE` = `RESOLVED: REMOVE_REQUIREMENT`
  (Section 2.7.6): `validate_cohort_b_source` is not bound, and this module
  does not become `FUTURE-BOUND` under that decision. Adding it would require
  a new owner decision superseding this resolution and a new binding review.
- These modules are `EXCLUDED`:
  - `application/services/backend_ai_workflow.py`
  - `interfaces/cli/workflow_demo.py`
  - `infrastructure/ai/lightning_client.py` (FEAT-017)
  - `infrastructure/config/settings.py`
  - `benchmark/vision_b2_preflight.py`
  - `benchmark/vision_b4_quality_benchmark.py`
  - `benchmark/vision_v3_quality_benchmark.py`

This classification does not broaden the live path. It makes explicit the
modules that the live path and the approved caller already load. It does not
create a caller implementation: the approved caller's module identity remains
a separate required D11 binding field under Section 2.7.3.

### 2.7.5 Admission outcome versus media-quality validation

This subsection was added by the 2026-09-17 R-001..R-007 remediation (R-001).

Two distinct gates must both pass before adapter invocation.

The D2 and media-quality checks below are owned by the Phase-0 preflight in
the proposed binding. Their failures are pre-authorization `0/null` returns
with no live evidence pair or incident record; they are not post-transition
pre-adapter terminals.

1. **D2 image admission.** The outcome must be exactly `ADMITTED`.
   - `REJECTED`, `UNSUPPORTED`, `INVALID_SOURCE`, and `PROCESSING_FAILURE` each
     stop the Phase-0 preflight before adapter invocation, with the reviewed
     return `adapter_call_count=0` and `attempt_count=null`; no live evidence
     pair or incident record is produced.
   - `ADMITTED` grants only eligibility for further validation (Section 2.7.1).
     It is never recorded as `PASS`.
2. **Media-quality validation.** `VisionMediaValidationProvenanceV1`
   (`contracts/schemas/vision.py` L62-70) may carry `decision="PASS"` only
   when it is built from a real result of the validator selected under
   `P2T2-LIVE-D6.MEDIA_VALIDATION_SOURCE`. Each of the following stops the run
   before adapter invocation with `0/null`:
   - a `RECAPTURE` decision;
  - a missing or unbound validator result;
  - any provenance mismatch. These are the same pre-authorization `0/null`
    returns and have no live evidence pair or incident record.

The adapter's ingress gate checks only two things: that `media_validation` is
present, and that its `decision` is `"PASS"` (`infrastructure/ai/qwen_vision.py`
L721-734). It does not verify the artifact reference, the artifact hash, or the
policy version. The harness must verify them before it constructs the request.

**Existing validator facts.**

- The only repository validator that produces a `PASS`/`RECAPTURE` result is
  `DeterministicMediaValidator` (`application/services/media_validation.py`
  L41-56), with `FileMediaSignalInspector`. Its policy version is
  `media-quality-policy-v1` (`MediaQualityPolicy`,
  `domain/understanding/media_quality.py` L49-63).
- It requires audio:
  - `MediaValidationRequest` requires `image_path` and `audio_path` (L25-30).
  - `MediaValidationResultV1` requires `audio` and `audio_signals`
    (`contracts/schemas/media_validation.py` L58-73).
  - `assess_media` returns `PASS` only when both the image and the audio
    assessments return no reason. A missing audio duration yields
    `AUDIO_UNREADABLE` (`media_quality.py` L104-108 and L136-148).
- This smoke is image-only (P2T2-LIVE-D3). The approved D1 specification
  records two positions (specification L320-325):
  - a placeholder audio reference for an image-only admission fixture is
    "dishonest by construction";
  - "inventing audio" is not acceptable.
- The exact committed image-only validator now produces
  `ImageOnlyValidationResultV1@1.0`; the audio-bearing
  `DeterministicMediaValidator` remains excluded from this image-only path.

**Owner decision `P2T2-LIVE-D6.MEDIA_VALIDATION_SOURCE` = `RESOLVED: EXACT_COMMITTED_IMAGE_ONLY_VALIDATOR`
(2026-09-20).** The owner approved the exact committed implementation after
the D6 binding package independent review returned `PASS`.

The immutable binding is:

- Commit: `16c52da26c444947ab4388712d9b7310480360b4`;
- contract: `ImageOnlyValidationResultV1@1.0`;
- validator: `feat018-image-only-structural-validator-v1`; and
- policy: `feat018-image-only-structural-policy-v1`.

The exact committed four-file validator identity is:

| Path | Role | Commit blob |
|---|---|---|
| `backend/src/sketch2life/contracts/schemas/media_validation.py` | image-only result, verification, provenance, and serialization contract | `e5681c2f260329513788d117d0425c043fe215a2` |
| `backend/src/sketch2life/application/services/media_validation.py` | offline image-only validator service | `6b0e8de7b34500cc4bbfd7c01ed9235388c021b9` |
| `backend/src/sketch2life/domain/understanding/media_quality.py` | image-only structural policy bridge | `b8d89efebc6ae8a82b3821e3d833627ef4fd2439` |
| `backend/tests/unit/test_media_validation.py` | deterministic contract and validator tests | `cd4a170105b59ba40c1416135e13f4adaa97b886` |

The accepted artifact-reference grammar is exactly:

- `fixture-b[0-9]{2}`;
- `fixture:drawing:v[0-9]+`;
- `fixture:small-dark-drawing:v[0-9]+`;
- `fixture:corrupt-drawing:v[0-9]+`; and
- `fixture:rejected-reference:v1`.

The `fixture-b[0-9]{2}` pattern syntactically permits `fixture-b00` through
`fixture-b99`. It does not assert that every such fixture exists, that every
such fixture was owner-reviewed, or that every such fixture is independently
authorized for a live run. Fixture existence, identity, and authorization
remain separate run-specific gates.

The canonical artifact hash is the lowercase SHA-256 of UTF-8 bytes from
`result.model_dump_json(by_alias=False, exclude_none=False, indent=None)`.
Verification reparses the result and requires byte-identical canonical
reserialization. The image-only result has no audio field and no staged digest
field; D8 owns later staged-digest verification.

**Required binding fields** for this owner-bound validator:

| Field | Requirement |
|---|---|
| Validator identity | Exact commit, module path, class/function identity, and commit blob listed above |
| Policy | `feat018-image-only-structural-policy-v1` and the committed structural policy fields |
| Validator result | `ImageOnlyValidationResultV1@1.0` with the closed image-only failure vocabulary |
| `validation_artifact_ref` | One accepted grammar value above; bounded and free of a path, URL, token, or credential |
| `validation_artifact_sha256` | Lowercase SHA-256 of the exact canonical serialization rule above |
| `decision` | Exactly `PASS` from the bound image-only validator result; any typed failure stops |
| Provenance rule | Source and validator facts are copied from the bound result only |

Provenance rules:

- **Source.** The validator result is produced by the Phase-0 preflight
  before `AUTHORIZED_RUN_ATTEMPT_BEGINS`, from the immutable original. A
  validation failure is therefore pre-authorization and has no live evidence
  pair or incident record.
- **Image digest.** The result source digest equals the D6 `source_sha256` and
  the D2 admission snapshot digest.
- **Later digests.** The same source digest is compared with the D8 staged
  digest and the request's `source_image_ref.sha256` after `SESSION_READY`.
- **Copying.** Every provenance field is copied only from the bound result;
  provenance is never derived from `ADMITTED`, a test fixture value, or a
  constant.

This resolves only the D6 media-validation-source binding. D6 overall remains
`NOT FINALLY RESOLVED` because fixture identity remains
`RESOLVED_WITH_PROPOSED_VALUE`. The binding does not resolve D11, authorize
Stage 4, or authorize live execution. The preflight remains fail-closed when
the committed validator identity, result, or provenance is missing or
mismatched, with `0/null` and no live evidence pair or incident record.

### 2.7.6 MIME/extension agreement

This subsection was added by the 2026-09-17 R-001..R-007 remediation (R-002).

**Facts.**

- **Origin.** Precondition 5 inherited "MIME/extension agreement" from the
  P2-T1 task card (`plan/PERSON_2_AI.md` L45) and the pre-specification decode
  proposal (`evidence/notes/P2_IMAGE_DECODE_PROPOSAL_20260910.md` L74-75).
- **Not in D1/D2.** Neither the approved D1 specification nor the D2 closure
  contains a MIME/extension check (Section 2.7.1).
- **Only existing enforcer.** It is `validate_cohort_b_source` in
  `backend/src/sketch2life/benchmark/image_admission_evaluation.py`
  L1434-1469 (Git blob `84e95d63363152f6f9692d396fa03d363e77db4f`). It belongs
  to the offline D3-R2 Cohort B harness:
  - it compares the filename extension with the declared format
    (L1447-1449);
  - it compares the magic-signature sniff with the declared format
    (L1450-1454);
  - it derives MIME from the sniffed format and does not compare it with a
    declared MIME (L1464);
  - its input must come from `load_cohort_b_manifest` (L1340-1416), which
    accepts only the complete owner-approved B01-B08 manifest;
  - only its unit test imports it, and it is not on the live path.

**Owner decision `P2T2-LIVE-D6.MIME_EXTENSION_RULE` = `RESOLVED: REMOVE_REQUIREMENT`
(2026-09-18).** The owner selected option (b): MIME/extension agreement is
removed from precondition 5 and from this live path.

- **(a) `BIND_ENFORCER`.** Not selected. `validate_cohort_b_source` and the
  rest of `image_admission_evaluation.py` are not added to the live path, and
  no other MIME/extension enforcer is bound.
- **(b) `REMOVE_REQUIREMENT`.** Selected. Precondition 5's MIME/extension
  clause is satisfied by removal, not by a runtime check. No component may be
  described as enforcing MIME/extension agreement.

This resolution means:

- the live path makes no MIME/extension-agreement claim, and none may be
  added without a new owner decision;
- `image_admission_evaluation.py` (including `validate_cohort_b_source` and
  `load_cohort_b_manifest`) and the offline Cohort B tooling remain outside
  the live path and are not imported, called, or relied on by it;
- D2 admission's responsibilities are unchanged by this resolution: bounded
  decode, the container/codec/pixel-format checks in
  `domain/understanding/image_admission.py`, and source/staged digest
  equality (Section 2.7.1) remain the only D2-owned checks;
- the B01.jpg MIME/extension facts recorded under D6 fixture identity
  (Section 9) remain owner-reviewed metadata only; they are not promoted to a
  runtime agreement check by this resolution;
- no MIME/extension enforcer is added by this plan or this decision.

**Fail-closed condition — resolved.** The precondition-5 MIME/extension
clause is satisfied by this removal and no longer independently blocks
Phase 0. This resolution does not by itself unblock D11 or Stage 4, which
remain `BLOCKED`/`NOT READY` pending the concrete
`P2T2-LIVE-D11.LIVE_SEAM_BINDING` (Section 2.7.7), the remaining D1-D12
resolution, and the independent review of this D6 governance commit.

No component may be described as enforcing MIME/extension agreement unless
option (a) names and freezes it.

### 2.7.7 Live seams, check ownership, recording, and verification

This subsection was added by the 2026-09-17 R-001..R-007 remediation (R-003
and R-004). It preserves the Protocol-only boundary of the reviewed source and
authorizes no source change. Line references are to
`backend/src/sketch2life/benchmark/feat018_live_lightning_execution.py` unless
another file is named.

**Seam ownership.** `P2T2-LIVE-D11.LIVE_SEAM_BINDING` (Section 9) owns every
concrete live seam and the approved caller boundary:

| Seam | Reviewed Protocol and use | Placement to be confirmed by the binding | Concrete implementation today |
|---|---|---|---|
| Approved host caller | The reviewed `run_live_smoke` entry accepts the prebuilt request, runtime config, policy, prompt, and injected seams (L3223-3237); no caller implementation is in the reviewed two-file boundary | Host or session, explicitly bound | None; the D11 binding must supply its immutable identity |
| `LightningPreflight` | L2064-2067, documented as host-side; `verify` is invoked before provisioning (L3297-3314) | Host | None |
| `LightningSessionController` | L2076-2090; `provision`, `wait_ready`, and `terminate` are invoked through the host lifecycle process boundary (L2673, L3316) at L3378-3382, L3435-3439, and L3609-3614 | Invoked from the host. The binding must name how its in-session checks execute inside the Lightning session | None |
| `LightningSmokeFinalizer` | L2070-2073; must delegate to `finalize_smoke_run` (L4228-4279) and incident handling | Host | None |
| Adapter-dispatch wrapper | `BoundedAdapterCall` L2093-2105; invoked once at L3511 | Invoked from the host. The binding must name how the unchanged `run_bounded_adapter_call` (L1673-1681) executes inside the Lightning session | None |

**Cardinality constraint.**

1. The reviewed source order is: injected-seam presence checks (L3247-3295,
   typed `0/null` returns); preflight (L3297-3314, typed `0/null` returns with
   no evidence or finalizer call); lifecycle-boundary construction
   (L3316-3328); counter and lifecycle-state initialization, including
   `adapter_call_count=0` and `attempt_count=None` (L3330-3349); the reviewed
   lifecycle `try` (L3360) whose `finally` (L3595) owns cleanup; and the only
   finalizer call after that block (L3668). Under the selected plan-only T-001
   rule, a preflight exception or false fact is pre-authorization, returns
   `0/null`, and produces no live evidence pair, incident record, or finalizer
   call.
2. `AUTHORIZED_RUN_ATTEMPT_BEGINS` is the plan-level transition immediately
   before entry into the reviewed lifecycle `try` (L3360), after successful
   preflight, successful lifecycle-boundary construction, and successful
   counter/state initialization. It is a plan-level marker only; the reviewed
   source has no runtime token or field for it, and this plan defines none.
   Any failure before the transition is pre-authorization (`0/null`, no
   evidence pair, no finalizer). Any failure after it uses the bound
   cleanup/finalization path. The concrete D11 binding must record this
   transition without moving pre-transition failures into evidence.
3. The reviewed coordinator sets `adapter_call_count=1` immediately before
   invoking the adapter-dispatch wrapper (L3509-3511). Any check performed
   inside that wrapper, including containment/launch, dispatch, input
   validation, or pre-attempt failure, is therefore recorded with count `1`.
   Because no generation-start event is accepted in those cases, the host
   `attempt_count` is `null`; an adapter-local `attempt_number=0` is not copied
   into that host field.
4. Post-transition pre-adapter checks must be owned by the session controller
   and fail closed with `0/null` through the authorized finalization path. A
   `NOT_READY` readiness returns `SESSION_NOT_READY` (L3446-3454).

**Check-to-owner map.**

| Check (plan location) | Future owner | Reviewed gate or carrier today |
|---|---|---|
| Approval `APPROVED`, D1-D12 resolved, evidence pair listed (Phase 0) | Preflight | `approval_identity_verified` (boolean) |
| External `approval_record_commit`, reviewed-path zero-diff/blob, clean host checkout (Phase 0) | Preflight | `checkout_identity_verified` (boolean) |
| Fixture identity, owner-review reference, and `source_sha256` (Phase 0) | Preflight | `fixture_digest_verified` (boolean) |
| D2 admission outcome exactly `ADMITTED`; snapshot digest equals `source_sha256` (Phase 0; Section 2.7.5) | Preflight | None; no admission field exists |
| Media-quality validation `PASS` and provenance (Phase 0; Section 2.7.5) | Preflight against the owner-bound `P2T2-LIVE-D6.MEDIA_VALIDATION_SOURCE` | None |
| MIME/extension rule (precondition 5; Section 2.7.6) | N/A — `RESOLVED: REMOVE_REQUIREMENT`; no enforcer, no preflight check | None; requirement removed |
| Profile, catalog/config hashes, pins, prompt and policy identity, hardware decision, timeouts, caps, TTL, budget, and output ceilings recorded (Phase 0) | Preflight | `prompt_hash_verified`, `policy_identity_verified`, and `hardware_placement_verified` (booleans); the explicit `Feat018LiveSmokeConfig` (L2115-2138) |
| D4 snapshot/readiness/identity (pre-Stage 4) | Preflight | `d4_readiness_verified` (boolean). This is `RESOLVED_FOR_RUNTIME_REVALIDATION`; it is not in-session readiness |
| Host environment matches its frozen inventory (Section 2.7.2) | Preflight | `runtime_inventory_verified` (boolean) |
| Evidence destinations absent (Phase 0; Section 2.5) | Preflight. The reviewed finalizer re-checks the evidence destinations at commit (L4002-4010) | No dedicated preflight fact; D11 must bind the baseline hand-off |
| Artifact-inventory baseline captured before finalization (Phase 0; Section 2.5) | Preflight captures the baseline; `finalize_smoke_run` requires it (L4233-4240) and the inventory implementation captures it (L4115) | No reviewed carrier from preflight into the finalizer; D11 must bind one or fail closed |
| Git-ignored incident-destination confirmation (Phase 0; Section 2.5) | Preflight confirms the exact incident destination; `Feat018IncidentWriter` requires `git_ignored=True` (L4141-4160) | No dedicated preflight fact or reviewed writer hand-off; D11 must bind one or fail closed |
| `AUTHORIZED_RUN_ATTEMPT_BEGINS` transition (after preflight, lifecycle-boundary construction at L3316-3328, and counter/state initialization at L3330-3349; immediately before the reviewed lifecycle `try` at L3360) | Future D11 caller/coordinator binding; the reviewed coordinator constructs the boundary and initializes `adapter_call_count=0` and `attempt_count=null` only after preflight returns, and all three steps precede the transition | No reviewed boundary token or source field; D11 must record the transition without treating pre-transition failures as authorized |
| In-session `approval_record_commit`, reviewed paths, and clean checkout (Phase 1) | Session controller | None; a failure must be reported as `NOT_READY` |
| Explicitly selected runtime config loaded without copying values to evidence (Phase 1; Section 2.1) | The approved caller constructs `QwenVisionRuntimeConfig` before `run_live_smoke`/preflight (L3223-3226 receives it); an in-session `from_env_file` call is a separate revalidation in the environment where it executes and must prove the same approved identity | No reviewed config hand-off/equality carrier; caller placement, file placement, and revalidation remain D11 fail-closed |
| Installed dependency versions, CUDA, driver, GPU SKU, device count, VRAM, and BF16 (Phase 1) | Session controller | `LightningPlacementFacts` (L1808-1819), matched by `_placement_matches_approval` (L2225; call at L3396-3399). No dependency or driver field |
| Provision-time single-device visibility/placement (Phase 1) | Session controller | `LightningPlacementFacts` fields `single_device_visible`, `model_device_index`, and `input_device_index` (L1817-1819), checked before model load |
| Post-load model/input placement (Phase 1; D10) | Concrete session controller/dispatch binding | No reviewed post-load carrier; current placement facts are pre-load, so a selected post-load branch fails closed pending D10/D11 binding |
| No-model-load readiness `READY` (Phase 1) | Session controller, before `SESSION_READY` | `LightningSessionReadiness` only (L1755-1759) |
| D4 runtime/session-local revalidation of snapshot presence and revision (Phase 1) | Session controller, after `SESSION_READY` and before D8 staging | `LightningSessionReadiness` only (L1755-1759) |
| D8 staging and staged SHA-256 recomputation (Phase 1) | Session controller, after D4 runtime/session-local revalidation and before adapter dispatch | No reviewed staging/reference carrier. The adapter's `_verify_image_reference` (`qwen_vision.py` L1088-1101) is an independent in-call check and a mismatch is `1/null` after dispatch |
| Sanitized runtime manifest creation and hash (Phase 1; Section 3A) | Session controller | None |
| No weight preload (Phase 1) | Session controller | None (negative assertion) |
| Containment boundary, non-daemon spawn, and `CONTAINMENT_READY` before adapter construction (Phase 1) | Adapter-dispatch wrapper running the reviewed supervisor and worker | `SupervisorRunResult` (L1223-1238); recorded inside the one adapter call |
| Request construction with the D6-bound provenance and D8 reference (before `run_live_smoke`) | Approved caller (host), with the D8 reference delivered through a reviewed post-`SESSION_READY` staging hand-off before dispatch | No reviewed request/staging hand-off; D11 must bind the caller and reference identity or fail closed |
| Prompt hash equality before the `run_live_smoke` call (Phase 2) | Approved caller, then preflight verifies the received immutable string/fact | `prompt_hash_verified` (boolean); no reviewed last-mile rehash seam after preflight |
| Provisioning, readiness deadline, TTL, GPU budget, adapter cap, and termination (Phases 1-4) | Session controller facts plus the reviewed coordinator | `LightningProvisionFacts` (L1882-1893), `LightningReadyFacts` (L1916-1920), `LightningTerminationFacts` (L1934); reviewed deadline logic |
| Evidence finalization and incident handling (Phase 5) | Finalizer delegating to `finalize_smoke_run` | `LightningFinalizationFacts` (L2036; booleans); the finalizer/writer must not publish values they do not receive |
| Post-transition pre-adapter terminal input to finalization (Phase 4-5) | Session controller/coordinator hand-off into the finalizer | `LightningSmokeFinalizer.finalize` receives `Feat018LiveSmokeResult`, while `finalize_smoke_run` takes `SupervisorRunResult` (L2070-2073, L4228-4237); no reviewed non-fabricating carrier is present, so D11 must bind one or re-scope this terminal path |

**Recording and verification contract.**

| Value | Expected value bound at Stage 4 | Verified by | Carried by reviewed types today | Required record |
|---|---|---|---|---|
| Admission outcome and reason | Exactly `ADMITTED`, with no reason; snapshot digest equal to the D6 `source_sha256` | Preflight (host) | None. `LightningPreflightFacts` (L2004-2032) has eight booleans only | Typed fact plus evidence fields `admission_outcome` and `admission_reason`; preflight rejection remains pre-authorization and has no live pair |
| Validation artifact reference and SHA-256 | The Section 2.7.5 binding | Preflight (host). It recomputes the SHA-256 by the bound rule and compares it with the request provenance | None | Typed fact plus evidence fields `validation_artifact_ref` and `validation_artifact_sha256` |
| Validator identity, policy version, and decision | The Section 2.7.5 binding; decision exactly `PASS` | Preflight (host) | None | Typed fact plus evidence fields `validator_identity`, `validator_policy_version`, and `media_validation_decision` |
| Readiness result | `status=READY` with no issues (`QwenVisionEnvironmentReadinessV1`, `qwen_vision_environment_readiness.py` L75-100) | Session controller, before `SESSION_READY` | `LightningSessionReadiness` only | Typed fact plus evidence fields `readiness_status` and `readiness_issue_codes` |
| D4 runtime/session-local revalidation | Approved snapshot presence and revision, after `SESSION_READY` | Session controller | `LightningSessionReadiness` only | Typed fact plus D4 runtime identity fields |
| Staged digest | Equal to `source_sha256` under the D8 method, after D4 runtime/session-local revalidation | Session controller | None | Typed fact plus evidence field `staged_source_sha256` |
| Runtime manifest identity | The Section 3A allowlist and the frozen session inventory (Section 2.7.2) | Session controller, after `SESSION_READY` | None | Typed fact plus the existing evidence fields `runtime_manifest` and `runtime_manifest_sha256` |

**Typed-carrier gap and fail-closed rule.**

The reviewed types can gate these checks but cannot record or prove their
values:

- `LightningPreflightFacts` carries eight booleans (L2004-2032).
- `LightningProvisionFacts` and `LightningReadyFacts` carry allocation,
  placement, readiness-enum, and lifecycle facts (L1882-1893 and L1916-1920).
- `SupervisorRunResult` carries supervisor state (L1223-1238).
- `Feat018LiveSmokeResult` carries lifecycle and cardinality fields
  (L2141-2165).
- `Feat018EvidenceFinalizer.finalize` publishes only `status`,
  `cleanup_status`, and `postflight_status` (L4011-4024).
  `Feat018EvidenceCommitWriter.commit` adds `run_id`, `evidence_id`,
  `companion_markdown_sha256`, and `commit_state` (L3800-3806).

For a post-transition pre-adapter terminal, the reviewed
`LightningSmokeFinalizer.finalize` Protocol receives `Feat018LiveSmokeResult`,
but the delegated `finalize_smoke_run` function accepts `SupervisorRunResult`
instead. The plan must not fabricate a supervisor result to bridge that type
gap. D11 must bind a reviewed non-fabricating carrier or explicitly re-scope
that terminal's evidence requirement before Stage 4.

A boolean or a readiness enum may fail closed, but it is not a record of the
admission outcome, validation provenance, readiness result, staged digest, or
runtime-manifest identity.

Before D11 can be resolved, `P2T2-LIVE-D11.LIVE_SEAM_BINDING` must identify an
independently reviewed typed carrier and evidence path for these values.

- If none exists, creating one requires a separate implementation authorization
  and an independent review before D11 can be resolved.
- This plan authorizes no such implementation.
- Until a reviewed carrier and evidence path exist, D11 cannot be resolved and
  Stage 4 cannot be approved.

**Broader metadata and live-assertion gate (T-003).** The same fail-closed
rule applies to every Section 7 metadata field beyond the six rows above and
to the Section 5 assertions, including commit/fixture/model/prompt/policy
identities, ceilings and cap outcomes, inventory summaries, nested-spawn and
non-daemon observations, descendant containment/no-orphan results, and
late-event rejection. Before D11 can resolve, the binding must identify for
each retained field or assertion its reviewed producer, typed carrier or
writer hand-off into finalization, safe serialization/allowlist rule, and
verification point. The reviewed finalizer/writer may publish only values it
actually receives; it does not receive or publish these missing values merely
because the plan lists them. If no such reviewed hand-off exists, the owner
must explicitly re-scope the affected Section 5/7 requirement in D11/Stage 4;
otherwise the requirement remains fail-closed. This plan authorizes no carrier
implementation or re-scope.

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

5. Admission, validation, and staging integrity.
   - **Admission.** Before a vision call, the exact fixture's P2-T1 D2
     image-admission outcome is exactly `ADMITTED` under the bounded limits
     max_file_bytes=5000000, max_pixels=4000000, max_longest_edge=4096, and
     max_frames=1, with decodability established by D2's bounded full decode.
   - **Stops.** Any other D2 outcome (`REJECTED`, `UNSUPPORTED`,
     `INVALID_SOURCE`, or `PROCESSING_FAILURE`) is a pre-authorization
     preflight rejection. It returns `adapter_call_count=0` and
     `attempt_count=null` from the reviewed entry, creates no live evidence
     pair or incident record, and never reaches the authorized-run boundary.
   - **Validation.** `ADMITTED` grants only eligibility for further
     validation. The separate media-quality validation gate and its
     provenance are defined in Section 2.7.5 under
     `P2T2-LIVE-D6.MEDIA_VALIDATION_SOURCE`.
   - **MIME/extension.** D2 does not enforce MIME/extension agreement.
     `P2T2-LIVE-D6.MIME_EXTENSION_RULE` (Section 2.7.6) is
     `RESOLVED: REMOVE_REQUIREMENT`: this precondition's MIME/extension
     clause is satisfied by removal, and no MIME/extension enforcer is
     bound or required on the live path.
  - **Staging.** The approved P2T2-LIVE-D8 method mounts, copies, or uploads
     only a derived session-local working reference after `SESSION_READY` and
     successful D4 runtime/session-local revalidation. The original remains
     immutable. If staging occurs inside the session, the concrete controller
     must provide a separately reviewed typed hand-off that establishes the
     exact session-relative `source_image_ref` before adapter dispatch; the
     reviewed source has no such carrier. The staged bytes are hashed inside
     Lightning before inference and must equal `source_sha256`. The request's
     `VisionImageReferenceV1` and the adapter's `_verify_image_reference`
     check use that same digest. Until the D8 placement/handoff is bound under
     D11, this precondition is fail-closed.

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
   The approved caller hashes the exact injected text before invoking
   `run_live_smoke` and requires equality with the approved hash without
   logging or persisting the text. The reviewed coordinator has no separate
   last-mile prompt seam after preflight; a later rehash requires a separately
   reviewed D11 seam. P2T2-LIVE-D12
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
   visibility from the provision-time facts, or bind a separate reviewed
   post-load assertion whose typed result proves that the model and inference
   inputs occupy the approved device index. `LightningPlacementFacts`
   currently reports provision-time placement and is not a post-load carrier;
   if D10 selects the post-load alternative and D11 has not bound that carrier,
   the run is fail-closed. Inventory alone is insufficient.

10. Timeout and attempt policy. The profile timeout is exactly 120.0 seconds
     per generation attempt in the proposed killable runner. Its child
     deadline starts after process start and includes model loading, generation,
     and decoding in that attempt. A separate positive
     `total_adapter_cap_seconds`, recorded under P2T2-LIVE-D2, covers the
     entire one adapter call and any permitted retry without resetting. A
     timeout or total-cap terminal is never retried. A post-transition stop
     before adapter dispatch records `adapter_call_count=0`,
     `attempt_count=null`; once the adapter-dispatch wrapper is invoked, an
     adapter input rejection before model generation records `1/null`; a
     model-reaching call records `1/1` or `1/2`. Only QwenTransientRuntimeError or a generic
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

11. Bounded output and IPC. P2T2-LIVE-D9 remains `NOT RESOLVED`. The
    owner-selected candidates are `raw_output_max_bytes=65536` and
    `ipc_envelope_max_bytes=98304`; they are not exact runtime bindings.
    `stdout/stderr=SEPARATE_ENFORCEMENT_APPROVAL_REQUIRED`: no numeric stream
    ceilings or disable semantics are selected. The reviewed runtime currently
    only declares and validates `stdout_max_bytes`/`stderr_max_bytes`; it has
    no stream capture, worker hand-off, byte enforcement, overflow action, or
    stream tests. The D9 design record proposes bounded, non-persistent
    capture-and-discard with raw-byte accounting, no UTF-8 decoding, typed
    overflow/read/death/late/finalization outcomes, and the event order
    `capture -> stop/close -> bounded drain -> finalize -> publish -> reject
    later bytes`. A future approved runner may not carry prompts, raw model
    output, secrets, tokens, credentials, URLs, absolute paths, provider
    details, traceback/exception text, process handles, or identifiers.
    If the future approved contract cannot prove these bounds, the run stops
    before model/provider work. The exact profile setting max_new_tokens=512
    must remain recorded and unchanged, but it does not by itself prove a byte
    bound.

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
provider, network call, benchmark, or live subprocess. Section 2.7.7 maps the
owner of each check below.

- Verify the future approval is APPROVED for this exact scope, resolves
  P2T2-LIVE-D1 through P2T2-LIVE-D12, and lists the exact evidence pair.
- Verify the externally supplied `approval_record_commit`, the reviewed-path
  zero-diff/blob relationship to `reviewed_runtime_code_commit`, and an empty
  unfiltered `git status --porcelain` in the execution checkout.
- Verify the fixture_id, owner-review reference, and source_sha256.
- Verify that the P2-T1 D2 image-admission outcome is exactly `ADMITTED` and
  that its snapshot digest equals source_sha256. `REJECTED`, `UNSUPPORTED`,
  `INVALID_SOURCE`, `PROCESSING_FAILURE`, or a digest mismatch stops before
  Lightning starts.
- Verify the media-quality validation result and provenance bound under
  Section 2.7.5: `decision=PASS`, validator identity, policy version, artifact
  reference, and recomputed artifact SHA-256. Any of these stops before
  Lightning starts:
  - `RECAPTURE`;
  - a missing or mismatched owner-bound D6 validator identity, result, or
    provenance;
  - any provenance mismatch.
- `P2T2-LIVE-D6.MIME_EXTENSION_RULE` is `RESOLVED: REMOVE_REQUIREMENT`. No
  MIME/extension check is applied before Lightning starts, and none may be
  added without a new owner decision.
- Verify the profile, catalog/config hashes, dependency pins, prompt identity,
  policy identity, hardware decision, per-attempt timeout,
  `total_adapter_cap_seconds`, TTL, budget, and output ceilings are completely
  recorded.
- Verify the date-qualified evidence paths do not already exist and capture
  the approved artifact-inventory baseline, including the exact Git-ignored
  incident-destination confirmation. Never overwrite an existing evidence
  artifact. These are pre-authorization checks; the baseline and confirmation
  must be handed to the later finalizer/writer through a reviewed typed path or
  the run remains fail-closed.
- Every check in this phase is pre-transition. The reviewed preflight runs
  before the coordinator constructs its lifecycle boundary, initializes
  `adapter_call_count=0` and `attempt_count=null`, enters the reviewed
  lifecycle `try`, and makes its only finalizer call. A preflight exception,
  false fact, missing typed hand-off, or failed Phase-0 check returns `0/null`
  as a pre-authorization result, creates no live evidence pair or incident
  record, calls no finalizer, and does not claim an authorized run. Only
  after all preflight checks pass, the lifecycle boundary is constructed
  successfully, and the counters and lifecycle state are initialized
  successfully does the plan record `AUTHORIZED_RUN_ATTEMPT_BEGINS`; the
  coordinator then enters the reviewed lifecycle `try`, whose `finally` owns
  cleanup and which leads to the bound finalization path.

### Authorized-run transition and pre-adapter failure classes

Definition:

`AUTHORIZED_RUN_ATTEMPT_BEGINS` = the plan-level transition immediately before
entry into the reviewed lifecycle `try`, after successful preflight,
successful lifecycle-boundary construction, and successful counter/state
initialization.

The reviewed source order (`feat018_live_lightning_execution.py` at
`reviewed_runtime_code_commit`) is:

1. preflight runs (L3297-3314);
2. a preflight exception or false fact returns `0/null` with no evidence pair
   and no finalizer call (L3300-3314);
3. the lifecycle boundary is constructed successfully (L3316-3328);
4. the counters and lifecycle state are initialized successfully
   (L3330-3349);
5. `AUTHORIZED_RUN_ATTEMPT_BEGINS` (plan-level marker; no runtime token or
   source field exists or is defined by this plan);
6. the reviewed lifecycle `try` starts (L3360);
7. cleanup is owned by `finally` (L3595), followed by the only finalizer call
   (L3668).

`AUTHORIZED_RUN_ATTEMPT_BEGINS` therefore occurs only after all of the
following are true:

- a valid Stage-4 approval has been established;
- `approval_record_commit` has been externally supplied and verified;
- execution-checkout identity and scope validation has passed;
- the exact approved evidence destinations have been established;
- every Phase-0 preflight check has passed;
- the lifecycle boundary has been constructed successfully; and
- the counters and lifecycle state have been initialized successfully.

Any failure before this transition is pre-authorization: it returns `0/null`,
produces no Lightning session, model load, inference, adapter call, live
evidence pair, or incident record, and calls no finalizer. The reviewed
source returns typed `0/null` results for seam-missing and preflight failures;
it has no reviewed handler for an exception raised during lifecycle-boundary
construction or state initialization, so such an exception leaves
`run_live_smoke` before the lifecycle `try` without an evidence pair or
finalizer call, and the D11 caller binding must classify it as
pre-authorization `0/null` rather than as an authorized attempt.

After this transition, a pre-adapter gate may still fail. Post-transition
examples are limited to in-session checkout revalidation, D4 snapshot runtime
revalidation, staged-fixture digest verification, observed session
hardware/readiness, runtime-manifest creation and hash, and TTL/budget/session
gates. Caller-side prompt, request, and fixture checks remain pre-transition
under Phase 0 and Section 2.7.7; they are not reclassified as post-transition
without a separately reviewed D11 seam. Such a post-transition terminal
outcome must preserve `adapter_call_count=0` and `attempt_count=null`, avoid
model load when the failed gate precedes it, run the bound cleanup/`finally`
and finalization path, and write the exact sanitized FAILED JSON/Markdown
evidence pair. If evidence creation is itself impossible, write only the
sanitized ignored incident record and do not index an evidence pair.

Every authorized run attempt retains a terminal evidence path; failures before
the transition do not.

### Phase 1 - Lightning provisioning and session startup

Start exactly one Lightning Studio GPU session under the approved TTL, total
adapter cap, and budget. The coordinator may maintain internal monotonic
lifecycle facts for provisioning, readiness, TTL, GPU-budget, adapter-cap, and
termination enforcement. Those monotonic control facts are not published
timing evidence merely because they exist in memory.

The current reviewed FEAT-018 runtime publishes no `*_wall_clock_ms` evidence
fields. No wall-clock telemetry field is imported from another lineage.

Inside the session, before any model invocation. Section 2.7.7 maps each check
to its owner. After Stage-4 approval, the mandatory order is:

```text
Stage-4 approval
-> provision session
-> SESSION_READY
-> D4 runtime/session-local revalidation
-> D8 staging and staged digest verification
-> exactly one smoke
```

The pre-Stage-4 D4 state is
`D4 snapshot/readiness/identity = RESOLVED_FOR_RUNTIME_REVALIDATION`.

The D4 runtime/session-local check is not required before Stage 4 approval.

- The session controller performs the checkout, dependency, hardware, and
  no-model-load readiness checks before it reports `SESSION_READY`.
- After `SESSION_READY`, the session controller performs D4 runtime/session-
  local revalidation, D8 staging and staged digest verification, and manifest
  checks before adapter dispatch.
- The adapter-dispatch wrapper runs the reviewed containment and spawn checks
  inside the one adapter call.

The checks are:

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
- revalidate the explicitly selected runtime-config identity in the
  environment that owns the session without copying its values to evidence.
  The `runtime_config` passed to `run_live_smoke` was already constructed by
  the approved caller before preflight; an in-session `from_env_file` call is
  not a retroactive construction of that object. The concrete caller/session
  hand-off and any equality check must be bound under D11, or the run stops;
- verify installed dependency versions, CUDA, driver, GPU SKU, device count,
  VRAM, and BF16 facts;
- require single approved-device visibility from provision-time facts. If D10
  selects the alternative post-load assertion, the concrete dispatch/session
  binding must return a separately reviewed typed post-load placement fact
  proving the model and inference inputs occupy the approved device index.
  The reviewed `LightningPlacementFacts` is collected before readiness/model
  load and cannot satisfy that post-load branch; without the bound carrier the
  run stops fail-closed;
- run only the no-model-load readiness inspection applicable to the approved
  configuration; require READY or stop before `SESSION_READY`;
- after `SESSION_READY`, revalidate the approved D4 snapshot presence and
  exact revision in the session; a failure stops before adapter dispatch;
- after successful D4 runtime/session-local revalidation, stage the approved
  image using the exact P2T2-LIVE-D8 method, keep its reference session-local
  and relative, and recompute the staged SHA-256;
- create and hash the sanitized runtime manifest;
- do not preload model weights. If P2T2-LIVE-D4 approves a model download,
  the download/load occurs inside the selected runner's child model-loading
  phase and is covered by the same 120-second subprocess boundary. A separate
  pre-invocation download requires separate approval.

If provisioning, session startup, readiness, staging, or manifest creation
fails, the resource cleanup finally block in Phase 4 still runs and Phase 5
records the terminal outcome.

### Phase 2 - one bounded adapter call

The approved caller constructs one `VisionUnderstandingRequestV2` before
invoking `run_live_smoke` and supplies that already-built object to the
reviewed entry. When D8 staging is session-local, a separately reviewed typed
staging hand-off must establish and verify the exact session-relative
`source_image_ref` after `SESSION_READY` and D4 runtime/session-local
revalidation but before adapter dispatch; the reviewed source currently has no
such carrier and therefore remains fail-closed.

The request contains:

- the owner-approved fresh correlation_id;
- the request's D8-bound session-relative `source_image_ref` and expected
  staged `source_sha256`;
- no processing image unless a separately approved derivation is named;
- media_validation built only from the media-quality validator result bound
  under Section 2.7.5 (`decision=PASS`, `validator_policy_version`,
  `validation_artifact_ref`, and `validation_artifact_sha256`), never from the
  D2 admission outcome;
- requested_profile_id=QWEN3_VL_8B_INSTRUCT_BF16_V1.

The approved caller has already computed the SHA-256 of the exact in-memory
UTF-8 prompt and checked it against the approved `prompt_sha256` before calling
`run_live_smoke`; the reviewed preflight receives the same prompt and can
verify the caller-side fact, but no reviewed seam re-hashes it after
`wait_ready` and before dispatch. A missing, changed, or mismatched prompt
fact is therefore a pre-authorization `0/null` stop with no live evidence
pair under T-001. A future last-mile rehash requires a separately reviewed
D11 seam and must not be implied by this plan.

Immediately before invoking the one adapter boundary, start the authoritative
monotonic `total_adapter_cap_seconds` enforcement window. Then increment
`adapter_call_count` to 1 and invoke the approved bounded adapter boundary
exactly once; there is no outer retry counter. The cap covers all work inside
that one adapter call, including adapter-side validation, prompt construction,
model loading, generation, decoding, and any permitted internal transient
second attempt. No adapter wall-clock evidence field is created or required.

For the proposed killable runner, each generation attempt has its own
120-second child deadline after process start. It includes the child
model/processor load, generation, and decoding; it is not a model-load
deadline followed by a separate generation deadline. The separate
`total_adapter_cap_seconds` begins at adapter_start, covers all generation
attempts inside this one adapter call, and is not reset for attempt 2. Either
timeout is terminal and cannot authorize another attempt. The raw provider
string remains in memory only and never reaches stdout, stderr, a hook sink, or
evidence.

If the adapter-dispatch wrapper is invoked and the adapter returns its typed
input-validation rejection before model generation, record
`adapter_call_count=1` and `attempt_count=null`; the adapter-local
`attempt_number=0` is not a host progress event and is not copied into the
coordinator result. Never retry or relabel that outcome as a model-reaching
smoke run. If the runner is entered, record `adapter_call_count=1` and
`attempt_count=1` or `2`; attempt 2 requires an explicit transient runtime
classification from attempt 1. No other call/attempt combination is accepted,
and no missing value is invented. The worker's
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

Cleanup is structurally required in the `finally` of the reviewed lifecycle
`try` around the authorized run body only. The local preflight,
lifecycle-boundary construction, and counter/state initialization are outside
that body: they execute before `AUTHORIZED_RUN_ATTEMPT_BEGINS`, and a failure
in any of them returns the selected pre-authorization `0/null` result with no
evidence pair or finalizer call. Once the transition has occurred, the
`finally` covers session provisioning, success, timeout, malformed output,
policy rejection, mapper failure, and subprocess failure. For a
post-transition pre-adapter stop before a session exists, cleanup operations
are safe no-ops but the bound terminal finalization path still runs. The
approved harness must not use early returns inside the authorized body that
bypass cleanup. The required shape, matching the reviewed source order, is:

    preflight = run_preflight_before_authorized_transition()
    if not preflight.authorized:
        return preauthorization_result_0_null_without_evidence_or_finalizer()
    boundary = construct_lifecycle_boundary()          # failure: pre-authorization
    initialize_counters_and_lifecycle_state()           # adapter_call_count=0, attempt_count=null
    # AUTHORIZED_RUN_ATTEMPT_BEGINS (plan-level marker; no runtime token)
    try:
        run_authorized_session_adapter_call_and_map()
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
   the complete artifact inventory;
5. rename the Markdown companion into its final path;
6. repeat the inventory comparison immediately before the authoritative JSON
   rename and treat that as the commit-adjacent check;
7. derive the final outcome, including any postflight or cleanup failure;
8. rename the authoritative JSON into its final path as the sole commit point.

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
post-transition pre-adapter terminal. A preflight rejection is not an
authorized attempt and does not invoke this writer. If the pair cannot be
created or atomically completed after authorization, write only the safe
ignored incident record at the exact relative destination
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

`CONTEXT.md`, `DECISIONS.md`, approval records, evidence indexes, and other
tracked governance/documentation updates occur only after the execution
evidence lifecycle is closed and the audited execution checkout has completed
its final inventory checks.

A later operator action that sleeps or stops the persistent Lightning Studio
after the approved session has already been terminated is post-run Studio
lifecycle management, not the runtime cleanup step.

## 5. Assertions and terminal outcome rules

All assertions below are required for a functional PASS:

The assertions are not evidence claims merely because the runtime can observe
them. Each retained assertion must have the reviewed producer, typed
carrier/writer hand-off, safe serialization rule, and verification point
required by the T-003 gate in Section 2.7.7; otherwise D11 and Stage 4 remain
blocked or the owner must explicitly re-scope that assertion.

The live checklist is explicit: real nested spawn succeeds; the outer worker
is non-daemon; containment covers all descendants; no orphan remains after a
kill; cleanup confirms both levels are absent; late events are rejected; and
`attempt_count` comes only from committed progress.

- a model-reaching run has exactly one adapter call:
  `adapter_call_count=1`;
- a preflight rejection, or any other failure before
  `AUTHORIZED_RUN_ATTEMPT_BEGINS`, is pre-authorization, returns
  `adapter_call_count=0` and `attempt_count=null`, and produces no live
  evidence pair, incident record, or finalizer call; a post-transition
  pre-adapter terminal is
  recorded as `adapter_call_count=0` and `attempt_count=null`; once the
  adapter-dispatch wrapper is invoked, an adapter input rejection before model
  generation is recorded as `adapter_call_count=1` and `attempt_count=null`;
- a model-reaching run records `attempt_count=1` or `2`, and attempt 2 occurs
  only after an explicitly classified transient runtime failure on attempt 1;
- no call or attempt value is inferred, backfilled, or fabricated; the only
  source of `attempt_count` is a supervisor-accepted committed progress event;
- before any vision call, all of the following held:
  - the source fixture's D2 admission outcome was exactly `ADMITTED`;
  - the media-quality validator bound under Section 2.7.5 returned `PASS`
    with verified provenance;
  - the rule selected under `P2T2-LIVE-D6.MIME_EXTENSION_RULE` was satisfied;
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
- the separately approved D9 contract is bound and future runtime evidence
  confirms the approved raw-output, IPC, stdout, and stderr rules; this is a
  future gate because the reviewed source currently only declares/validates
  the stdout/stderr fields;
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
- provisioning, readiness, TTL, GPU-budget, adapter-cap, and cleanup boundaries
  use the approved authoritative monotonic control facts; the current runtime
  publishes no `*_wall_clock_ms` evidence fields;
- cleanup ran in finally and cleanup_status=SUCCEEDED; any cleanup failure
  makes the overall run FAILED;
- the exact sanitized evidence pair was attempted for every authorized run
  attempt, including post-transition pre-adapter terminals; a preflight
  rejection or other pre-transition failure is not an authorized attempt and
  has no pair, incident record, or finalizer call;
  an impossible pair after authorization has only the safe ignored incident
  record and is not indexed;
- postflight inventory satisfies the exact two-file evidence scope.

One smoke run is functional evidence only. It is not a benchmark, does not
establish p50/p95 latency, throughput, quality, accuracy, semantic safety, or
production moderation readiness, and cannot close P2-T2 by itself. Full P2
closure needs separately approved live/evaluation work and its own evidence.

### 5.1 Retry and failure matrix

| Condition | V2 or harness outcome | Retry rule | adapter_call_count | attempt_count |
|---|---|---|---|---|
| Preflight rejection before `AUTHORIZED_RUN_ATTEMPT_BEGINS` (approval, checkout, fixture, D2 admission, media-quality provenance, MIME/extension rule, prompt/policy identity, or host inventory) | Pre-authorization terminal; no V2 or Raw result, live evidence pair, incident record, or finalizer call | No authorized run; stop | 0 | `null` |
| Lifecycle-boundary construction or counter/state initialization failure before `AUTHORIZED_RUN_ATTEMPT_BEGINS` | Pre-authorization terminal; no V2 or Raw result, live evidence pair, incident record, or finalizer call | No authorized run; stop | 0 | `null` |
| Post-transition pre-adapter stop (in-session checkout revalidation, D4 snapshot runtime revalidation, staged-fixture digest, observed readiness/hardware, runtime manifest, or TTL/budget/session gate) | Harness terminal; no V2 or Raw result | Terminal; no adapter call; bound cleanup/`finally`, then finalize through the bound non-fabricating carrier | 0 | `null` |
| Adapter input validation rejects before model generation | V2 INPUT_NOT_VALIDATED; mapper may produce typed Raw validation failure | Terminal; no retry | 1 | `null` |
| Model-load failure after the runner is entered | V2 VISION_MODEL_UNAVAILABLE / MODEL_LOAD_FAILED | Terminal; no second generation call | 1 | 1 |
| Device unavailable or wrong device after the runner is entered | V2 VISION_MODEL_UNAVAILABLE / DEVICE_UNAVAILABLE | Terminal; no retry | 1 | 1 |
| Timeout on either generation attempt | V2 VISION_TIMEOUT / TIMEOUT_BUDGET_EXCEEDED | Terminal; no retry after timeout | 1 | 1 or 2 |
| Total adapter cap reached | Harness or V2 timeout terminal | Terminal; no retry and no cap reset | 1 | 1 or 2 |
| Explicit or classified transient runtime failure on attempt 1 | Internal adapter retry | One retry only; proceed to attempt 2 | 1 | 2 after retry |
| Transient failure again on attempt 2 | V2 VISION_PROVIDER_FAILURE / TRANSIENT_RUNTIME_FAILURE | Terminal; no third attempt | 1 | 2 |
| Permanent runtime failure after the runner is entered | V2 VISION_PROVIDER_FAILURE / PERMANENT_RUNTIME_FAILURE | Terminal; no retry | 1 | 1 or 2 |
| Malformed JSON, schema-invalid output, duplicate ID, or reference failure | V2 VISION_SCHEMA_INVALID with the existing typed detail | Terminal; no repair/retry outside current adapter behavior | 1 | 1 or 2 |
| Content-policy rejection | V2 PROHIBITED_CLAIM_DETECTED with typed category | Terminal; no retry or semantic reinterpretation | 1 | 1 or 2 |
| Mapper failure or source/correlation mismatch at mapper | RawUnderstandingMappingError; no fabricated Raw result | Terminal; no retry | 1 | `null`, 1, or 2 as recorded before mapping |
| IPC, raw-output, stdout, or stderr ceiling exceeded | Harness-level bounded-output failure | Terminal; stop session; no retry | 1 | 1 or 2 |
| Cleanup failure after authorization | Harness FAILED / CLEANUP_FAILED | Terminal; no second session | 0 or 1 | `null`, 1, or 2 as recorded |

The current subprocess worker maps generic worker exceptions to a permanent
runtime failure; it does not infer transient status from arbitrary provider
text. Only an explicit approved transient seam may produce attempt 2.

### 5.2 Existing source/hash failure mapping

| Condition | Existing adapter outcome | Existing mapper outcome |
|---|---|---|
| Adapter verifies a staged digest mismatch | error_code=INPUT_NOT_VALIDATED, error_detail=SOURCE_IMAGE_HASH_MISMATCH, adapter-local `attempt_number=0`, retryable=false; record `adapter_call_count=1`, `attempt_count=null` | RawFailureCode.VALIDATION_REJECTED with upstream detail SOURCE_IMAGE_HASH_MISMATCH |
| Adapter cannot read the staged source | error_code=INPUT_NOT_VALIDATED, error_detail=SOURCE_IMAGE_UNREADABLE, adapter-local `attempt_number=0`, retryable=false; record `adapter_call_count=1`, `attempt_count=null` | RawFailureCode.VALIDATION_REJECTED with upstream detail SOURCE_IMAGE_UNREADABLE |
| Mapper sees result.source_image_ref.sha256 different from expected_source_sha256 | No new V2 result | Raises RawUnderstandingMappingError before Raw construction |

The direct mapper mismatch is not RawFailureCode.SOURCE_MISMATCH. That enum
member is not the current V2 mapper path. No mapping change is authorized. A
A post-transition stop before the adapter has no row in the existing-adapter
column and records `adapter_call_count=0`, `attempt_count=null` in the
sanitized harness evidence. A preflight stop, or any other stop before
`AUTHORIZED_RUN_ATTEMPT_BEGINS`, is pre-authorization and has no live
evidence pair or finalizer call.

## 6. Negative and stop gates

The following stop the run immediately. A failure before
`AUTHORIZED_RUN_ATTEMPT_BEGINS` (Phase-0 preflight, lifecycle-boundary
construction, or counter/state initialization) is pre-authorization: it
returns `0/null`, creates no live evidence pair or incident record, and does
not enter cleanup/finalization. A failure after
`AUTHORIZED_RUN_ATTEMPT_BEGINS` is terminal, is recorded without raw content,
and passes through the reviewed lifecycle `finally` cleanup block and the
bound evidence path.

- any missing or unresolved approval decision;
- `approval_record_commit` mismatch, reviewed-path zero-diff/blob mismatch,
  dirty checkout, untracked file, or unexpected source artifact;
- a D2 admission outcome other than `ADMITTED` (`REJECTED`, `UNSUPPORTED`,
  `INVALID_SOURCE`, or `PROCESSING_FAILURE`), fixture identity/hash mismatch,
  or staged digest mismatch;
- any of these media-validation failures:
  - a media-quality validation `RECAPTURE`;
  - a missing, unbound, or mismatched validation provenance;
  - a missing or mismatched
    `RESOLVED: EXACT_COMMITTED_IMAGE_ONLY_VALIDATOR` binding (see Section
    2.7.5);
  (`P2T2-LIVE-D6.MIME_EXTENSION_RULE` is `RESOLVED: REMOVE_REQUIREMENT` and is
  no longer a stop condition; see Section 2.7.6);
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
- a cardinality combination other than preflight `0/null` with no authorized
  evidence, post-transition pre-adapter `0/null`, in-dispatch
  pre-generation `1/null`, or model-reaching `1/1` or `1/2`; an outer retry, a
  third generation attempt, or a retry for any non-transient failure;
- `total_adapter_cap_seconds`, session TTL, or GPU/currency cap reached;
- any secret, token, credential, URL, absolute path, prompt, raw provider
  output, transcript, or raw media value entering evidence or logs;
- any artifact outside the exact future-approved evidence pair modified or
  created.

If the adapter returns an input failure with adapter-local `attempt_number=0`,
record `adapter_call_count=1`, `attempt_count=null`, map that typed result once,
and retain it as a terminal non-functional outcome. It is never retried and its
local zero is never copied into host progress. If a stop occurs before the
adapter after authorization, record `adapter_call_count=0`,
`attempt_count=null`; neither value may be backfilled from a planned call. A
preflight stop before authorization has no live evidence pair or incident
record. Every authorized terminal still requires the exact sanitized evidence
pair, or only the ignored incident fallback when pair creation is impossible.

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

Every authorized run attempt, including a post-transition terminal before
adapter invocation, must produce exactly this JSON/Markdown pair. A preflight
rejection before authorization is not an authorized attempt and produces no
live pair or incident record. A post-transition pre-adapter terminal records
`adapter_call_count=0` and `attempt_count=null` and omits V2/Raw result claims;
an adapter input rejection records `adapter_call_count=1` and
`attempt_count=null`; a model-reaching call records `adapter_call_count=1` and
`attempt_count=1` or `2`. If the pair cannot be created or atomically
completed after authorization, the only fallback is the safe local ignored incident record at
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
- admission, validation, and readiness fields; Section 2.7.7 defines their
  verification:
  - `admission_outcome` and `admission_reason`;
  - `media_validation_decision`, `validator_identity`,
    `validator_policy_version`, `validation_artifact_ref`, and
    `validation_artifact_sha256`;
  - `readiness_status` and `readiness_issue_codes`;
  - `staged_source_sha256`.

Publishing these fields requires the typed carrier and evidence path that
`P2T2-LIVE-D11.LIVE_SEAM_BINDING` must resolve. The finalizer and writer may
publish only values they actually receive through that reviewed hand-off;
they must not infer or synthesize missing metadata.
- model identifier, model revision, profile ID, adapter version,
  profile_config_hash, and profile_catalog_hash; never a weight-source URL;
- prompt_protocol_id, prompt_source_identity, and prompt_sha256; never prompt
  text;
- content_policy_version, policy_match_view_version, policy_scope, and
  P2T2-LIVE-D12 result; no lexicon text or semantic-safety claim;
- the allowlisted runtime_manifest object and runtime_manifest_sha256;
- GPU SKU, device index/count, vram_mib, BF16 result, CUDA runtime fact, and
  driver version only through the allowlisted manifest, plus approved
  provision-time single-device visibility. A post-load model/input placement
  assertion is publishable only when its separate reviewed typed carrier is
  bound under D10/D11; current placement facts do not prove it;
- the D9 candidate-state marker; after separate D9/D11 approval, the exact
  approved raw-output, IPC, stdout, and stderr ceilings plus an
  `enforcement=CONFIRMED` result;
- adapter_call_count and attempt_count using the conditional cardinality
  rules above, together with the adapter's typed attempt/result status when a
  V2 result exists; no raw model output;
- outcome status SUCCEEDED or FAILED; typed V2/Raw failure code when a valid
  typed result exists; harness-level run_failure_code when mapping, bounds,
  or cleanup fails;
- no `*_wall_clock_ms` evidence fields are required or published by the
  current reviewed runtime. Internal monotonic provisioning, readiness, TTL,
  GPU-budget, adapter-cap, and cleanup facts are control/enforcement facts,
  not evidence timing fields. A later telemetry field requires separate
  implementation authorization and review;
- per_attempt_timeout_seconds=120.0, total_adapter_cap_seconds,
  session_ttl_seconds, gpu_minute_cap and/or currency_cap, cap outcome, and
  safe budget-consumed value;
- ASR/Whisper execution=false and narration_status=NOT_SUPPLIED when a Raw
  success exists;
- cleanup_status, postflight_status, and a safe artifact-inventory summary.

Safe hashes may be recorded for the fixture, staged fixture, media-quality
validation artifact, prompt identity, runtime manifest, reviewed and approval
commit metadata, and
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
digests, validation_artifact_sha256, prompt_sha256,
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
| P2T2-LIVE-D1 | `BLOCKED` | Offline coordinator implementation and source/test binding are complete; `BLOCKED` pending remaining D1 owner resolution; source/test identity is already owner-bound. Stage 4 remains blocked until D1 is resolved. |
| P2T2-LIVE-D2 | `READY_TO_RESOLVE` | Positive TTL, total adapter cap, and numeric GPU-minute/currency cap still require owner selection. |
| P2T2-LIVE-D3 | `RESOLVED_WITH_PROPOSED_VALUE` | `ASR_EXCLUDED`, `asr_execution=false`, and `narration_status=NOT_SUPPLIED` are the proposed image-only value. |
| P2T2-LIVE-D4 | `OWNER-APPROVED_PRESTAGED_LOCAL_SNAPSHOT` | Owner-approved Lightning snapshot: Qwen/Qwen3-VL-8B-Instruct at revision `0c351dd01ed87e9c1b53cbc748cba10e6187ff3b`, 16-file manifest, four indexed shards, manifest SHA-256 `8a1d50d6aef809130acd7b05b71369cccbb2360192b157f7871de2bd40c43eaf`, and `allow_model_download=false`. |
| P2T2-LIVE-D5 | `READY_TO_RESOLVE` | Owner must choose independent-review indexing or P2 batch hold. |
| P2T2-LIVE-D6 | `RESOLVED_WITH_PROPOSED_VALUE` (fixture identity only) | Owner-reviewed Cohort B `B01.jpg` metadata and digest match the manifest and source review. The media-validation-source binding is recorded, but the fixture identity remains proposed. |
| P2T2-LIVE-D6.MEDIA_VALIDATION_SOURCE | `RESOLVED: EXACT_COMMITTED_IMAGE_ONLY_VALIDATOR` | Owner-approved on 2026-09-20 after `D6_BINDING_REVIEW = PASS`: exact commit `16c52da26c444947ab4388712d9b7310480360b4`, contract `ImageOnlyValidationResultV1@1.0`, validator `feat018-image-only-structural-validator-v1`, and policy `feat018-image-only-structural-policy-v1` (Section 2.7.5). |
| P2T2-LIVE-D6.MIME_EXTENSION_RULE | `RESOLVED: REMOVE_REQUIREMENT` | Owner-resolved (2026-09-18): MIME/extension agreement removed from precondition 5; no enforcer added; `image_admission_evaluation.py`/Cohort B tooling stay off the live path; D2 responsibilities and B01.jpg's owner-reviewed MIME/extension metadata are unchanged (Section 2.7.6). |
| P2T2-LIVE-D7 | `RESOLVED_WITH_PROPOSED_VALUE` | Committed C1-v2 source, builder, explicit `prompt=` path, and exact UTF-8 hash are traced; Stage 4 must bind them. |
| P2T2-LIVE-D8 | `READY_TO_RESOLVE` | Mount/copy/upload session-relative staging method remains an owner choice. |
| P2T2-LIVE-D9 | `NOT RESOLVED` | Numeric ceilings are owner-selected candidates only: `raw_output_max_bytes=65536` and `ipc_envelope_max_bytes=98304`. `stdout/stderr=SEPARATE_ENFORCEMENT_APPROVAL_REQUIRED`; the reviewed runtime only declares/validates those fields, and the D9 design record is blocked pending D11 and contract review. 2026-09-22 update: `stdout_max_bytes=16384`/`stderr_max_bytes=32768` are now owner-approved exact values, and the offline enforcement is implemented, corrected, independently reviewed `PASS`, and committed at `86836d24cfcd83ca14c0bc50e79fff1103cb9ecc` (see the "P2T2-LIVE-D9" section below, 2026-09-22 addendum). This is the offline-implementation state only; the live decision `P2T2-LIVE-D9` remains `NOT RESOLVED` because `D9_LIVE_D11_CARRIER_SCOPE` is still `UNKNOWN_UNRESOLVED_PENDING_D11`. |
| P2T2-LIVE-D10 | `READY_TO_RESOLVE` | Approval values and observed GPU evidence must be supplied separately; no live hardware was observed here. |
| P2T2-LIVE-D11 | `BLOCKED` | Exact two-file scope and source/test binding are complete; live-runtime suitability, the concrete live-seam binding, and Stage 4 approval remain pending. |
| P2T2-LIVE-D11.LIVE_SEAM_BINDING | `BLOCKED` | No concrete approved host caller, `LightningPreflight`, `LightningSessionController`, `LightningSmokeFinalizer`, or adapter-dispatch wrapper is bound. The caller/seam identities, check-owner map, recording contract, and typed-carrier resolution in Section 2.7.7 must be bound before D11 can be resolved. |
| P2T2-LIVE-D12 | `RESOLVED_WITH_PROPOSED_VALUE` | Synthetic lexical regression policy identity and scope are committed and proposed. |

D4 is owner-approved for the pre-staged snapshot identity and has
`D4 snapshot/readiness/identity = RESOLVED_FOR_RUNTIME_REVALIDATION`; D4
runtime/session-local revalidation remains Stage-4-local only after
`SESSION_READY`. `D6_BINDING_REVIEW = PASS`,
`D6_BINDING_PACKAGE = OWNER_APPROVED`, and `D6_OWNER_DECISION = RECORDED`.
`P2T2-LIVE-D6.MIME_EXTENSION_RULE` is resolved and
`P2T2-LIVE-D6.MEDIA_VALIDATION_SOURCE` is resolved to the exact committed
image-only validator; `P2T2-LIVE-D6` overall remains
`NOT FINALLY RESOLVED` because fixture identity remains
`RESOLVED_WITH_PROPOSED_VALUE`. The D11 sub-decision row remains `BLOCKED`
until the owner binds it. No table row authorizes live execution.

### Required staged governance sequence

The authorization sequence is mandatory and sequential. Its current
disposition is explicit:

| Stage | Required gate | Status | Bound evidence or next action |
|---|---|---|---|
| 1 | Exact two-file scope approval, with the FEAT-003 exclusion | COMPLETE | `6c1d607eb379a3b5b5b8f5cf120a904460da9ff1` and the feature-local approval package |
| 2 | Offline coordinator implementation and verification with injected seams and synthetic local process tests only | COMPLETE FOR OFFLINE IMPLEMENTATION/VERIFICATION | `7f5cbe57fc9756c3e7fa5c248cd655c1dce0ec7b` and `9549a341194f40b1a9be419d6fce0d70f1ca0384`; offline coordinator/POSIX findings are closed; no live execution is claimed |
| 3 | Offline independent review/finalization and source/plan binding review | COMPLETE FOR OFFLINE IMPLEMENTATION/VERIFICATION; SOURCE/TEST BINDING RECORDED | Offline review/finalization records close the offline findings; owner binding records `9549a341194f40b1a9be419d6fce0d70f1ca0384` for source/test identity only; live suitability and the concrete live-seam binding remain pending; the 2026-09-17 first independent plan binding review returned `PASS_WITH_FINDINGS` and its F-001/F-002 plan remediation is recorded in Sections 2.7.1-2.7.3; the second binding review returned `PASS_WITH_FINDINGS` (R-001..R-007), and its plan remediation is recorded in Sections 2.7-2.7.7 and the D6/D11 sections; the current next gate is `PREPARE_D1_OWNER_RESOLUTION_AND_D6_FIXTURE_BINDING` |
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

Planning disposition: `BLOCKED` pending remaining D1 owner resolution;
source/test identity is already owner-bound.

Stage 4 remains blocked until D1 is resolved. Stage 4 approval is not a
precondition of D1 resolution.

P2T2-LIVE-D1 is resolved before Stage 4 by owner approval of the exact reviewed
coordinator/supervisor implementation, authoritative deadline and containment
semantics, conditional cardinality rules, cleanup/preemption rules, exact
budget boundaries, and exact source/runtime dependency binding.

D1 resolution does not require a Lightning smoke to occur first. The separate
Stage-4 approval authorizes exactly one smoke in which the mandatory real
nested-spawn, containment, descendant-cleanup, no-orphan, and late-event
assertions are acceptance assertions. Failure of any such assertion makes the
authorized smoke FAILED; it does not retroactively mean Stage 4 had to run
before D1 could be resolved.

The offline coordinator uses the bounded primitives identified by historical
provenance `c2bd7b5ece3f308abb65ab3632add265b3cd586c`; the validated offline
coordinator/correction provenance is
`7f5cbe57fc9756c3e7fa5c248cd655c1dce0ec7b`, and the POSIX test correction
provenance is `9549a341194f40b1a9be419d6fce0d70f1ca0384`. These provenance
records identify offline history only. D1 remains `BLOCKED` until the owner
records its resolution.

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

Because this smoke is image-only, the existing media-quality validator, which
requires an audio input, cannot be applied silently. The owner decision is
`P2T2-LIVE-D6.MEDIA_VALIDATION_SOURCE` (Section 2.7.5). This paragraph does not
change the D3 planning disposition.

### P2T2-LIVE-D4 - Model-weight staging

Planning disposition: `OWNER-APPROVED_PRESTAGED_LOCAL_SNAPSHOT`.

The owner-approved Lightning snapshot manifest proves the session-local Qwen
snapshot identity, complete required files/shards, matching revision metadata,
and disabled runtime download. No cache path, arbitrary weight hash, or
host-local model location is published here.

The completed D4 record provides the safe logical/session-local snapshot
identity, the pinned revision
`0c351dd01ed87e9c1b53cbc748cba10e6187ff3b`, the readiness completeness proof
(all loader-required files plus every shard named by the safetensors index and
per-file revision metadata), and `allow_model_download=false`. The selected
manifest SHA-256 is
`8a1d50d6aef809130acd7b05b71369cccbb2360192b157f7871de2bd40c43eaf`.
`APPROVED_ONE_TIME_DOWNLOAD` was not selected.

The selected D4 option is `PRESTAGED_LOCAL_SNAPSHOT`; its record contains the
logical snapshot identity, `allow_model_download=false`, snapshot completeness,
verified revision metadata, and the sanitized manifest digest. The alternative
`APPROVED_ONE_TIME_DOWNLOAD` is not selected.

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

Planning disposition: `NOT FINALLY RESOLVED`. The fixture identity below is
`RESOLVED_WITH_PROPOSED_VALUE`. `P2T2-LIVE-D6.MIME_EXTENSION_RULE` is
`RESOLVED: REMOVE_REQUIREMENT`, and
`P2T2-LIVE-D6.MEDIA_VALIDATION_SOURCE` is
`RESOLVED: EXACT_COMMITTED_IMAGE_ONLY_VALIDATOR`. D6 overall remains not
finally resolved because fixture identity remains proposed.

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
used merely because its P2-T1 D2 image-admission outcome is `ADMITTED`.

The 2026-09-17 R-001..R-007 remediation added two required sub-decisions. The
owner resolved the MIME/extension rule on 2026-09-18 and the
media-validation-source binding on 2026-09-20. D6 overall remains
`NOT FINALLY RESOLVED` because fixture identity remains proposed.

- `P2T2-LIVE-D6.MEDIA_VALIDATION_SOURCE` =
  `RESOLVED: EXACT_COMMITTED_IMAGE_ONLY_VALIDATOR` (2026-09-20). The owner
  bound the exact image-only validator at commit
  `16c52da26c444947ab4388712d9b7310480360b4` after the independent D6 binding
  review returned `PASS`. The contract is
  `ImageOnlyValidationResultV1@1.0`, the validator is
  `feat018-image-only-structural-validator-v1`, and the policy is
  `feat018-image-only-structural-policy-v1`. The accepted artifact-reference
  grammar is the committed `fixture-b[0-9]{2}` plus the four named drawing,
  corrupt-drawing, and rejected-reference patterns in Section 2.7.5. The
  pattern permits B00-B99 syntactically without asserting fixture existence,
  owner review, or live authorization. The existing audio-bearing
  `DeterministicMediaValidator` remains excluded and no audio is fabricated.
- `P2T2-LIVE-D6.MIME_EXTENSION_RULE` = `RESOLVED: REMOVE_REQUIREMENT`
  (2026-09-18). MIME/extension agreement is removed from precondition 5 and
  from the live path; no enforcer is bound; `image_admission_evaluation.py`
  and the offline Cohort B tooling are not added; D2's admission
  responsibilities are unchanged; B01.jpg's MIME/extension remains
  owner-reviewed metadata only. Full detail is in Section 2.7.6.

### P2T2-LIVE-D7 - Prompt identity and explicit builder

Planning disposition: `RESOLVED_WITH_PROPOSED_VALUE`.

The committed authoritative candidate is C1-v2:

- `prompt_protocol_id=vision-v2-structured-output-prompt-v2`;
- source identity/version:
  `backend/src/sketch2life/benchmark/vision_c1_prompt_mapping_study.py`,
  `C1_PROMPT_V2` / `c1_prompt_text_v2()`;
- exact UTF-8 prompt SHA-256:
  `1e880e946dc1f1dcf11731c299702b33ab58e3c098cdda3d6607c080dc8f9fd6`;
- injection: resolve `c1_prompt_text_v2()` once in the approved caller, verify
  its UTF-8 digest before invoking `run_live_smoke`, then pass the resulting
  immutable string through preflight and as `prompt=` to
  `run_bounded_adapter_call`, through `adapter_worker_entry` to
  `QwenVisionAdapter(..., prompt=prompt, generation_runner=runner)`.

This traces the actual reviewed Qwen adapter seam without copying prompt text.
The explicit `prompt=` argument means `QwenVisionAdapter` does not reach its
empty `_default_prompt_builder`; the approved caller must additionally reject
an empty string and a hash mismatch before invoking `run_live_smoke`. The
reviewed coordinator has no separate prompt check between preflight and the
adapter-count increment.
The reviewed bounded runner accepts a prompt string but does not choose its
protocol, so the proposed binding remains subject to Stage 4 owner approval.
If the owner selects any other prompt, the approval must name its committed
source/version and recomputed exact UTF-8 hash; an uncommitted or unverifiable
prompt leaves D7 `BLOCKED`.

Record the exact prompt_protocol_id, prompt source identity/version,
prompt_sha256, and the explicit PromptBuilder or prompt injection used by
the approved caller. Before invoking `run_live_smoke`, hash the exact
in-memory UTF-8 injected text with
`sha256(prompt_text.encode("utf-8")).hexdigest()` and require equality with
the approved `prompt_sha256`; record only the approved hash and safe identity.
The preflight must receive and verify the same string/fact, and the D11
binding must prove that no later seam changes it. Confirm the empty adapter
default is unreachable and do not log or persist the prompt text.
The prompt text is never recorded. Any new or changed FEAT-003 prompt
requires another approval and is not authorized by this plan.

### P2T2-LIVE-D8 - Fixture staging and mount method

Planning disposition: `READY_TO_RESOLVE`.

Select exactly one owner-approved mechanism:

- MOUNT_SESSION_RELATIVE;
- COPY_SESSION_RELATIVE; or
- UPLOAD_THEN_SESSION_RELATIVE.

Record the method, a logical session-relative `artifact_ref`, source-to-derived
provenance, pre/post staging digest checks, and immutable-original rule. The
approved caller must construct the request with the D8-bound reference before
invoking `run_live_smoke`; if the selected method stages later inside the
session, D11 must bind a typed hand-off that establishes the same reference
before adapter dispatch. A host-local Windows path, signed URL, credential, or
unbounded base64/log transport is not a valid staging reference. Without that
placement or hand-off proof, D8 remains unfulfilled and the run is
fail-closed.

### P2T2-LIVE-D9 - Raw output, IPC, stdout, and stderr ceilings

Planning disposition: `NOT RESOLVED`.

The owner-selected candidate values are
`raw_output_max_bytes=65536` and `ipc_envelope_max_bytes=98304`. They remain
candidate-only and are not `EXACT_VALUE_BOUND`. The stream decision is
`stdout/stderr=SEPARATE_ENFORCEMENT_APPROVAL_REQUIRED`; no numeric
`stdout_max_bytes` or `stderr_max_bytes` value, zero-disable behavior, or
automatic byte-failure behavior is selected.

The reviewed runtime currently only declares and validates
`stdout_max_bytes`/`stderr_max_bytes`. It has no stream capture, worker
  hand-off, byte enforcement, overflow handling, typed stream failure carrier,
  or stream tests. The D9 package is `D9_PACKAGE=DESIGN_RECORD_ONLY` with
  `D9_LIVE_D11_CARRIER_SCOPE=UNKNOWN_UNRESOLVED_PENDING_D11` and
  `D9_PACKAGE_REVIEW=BLOCKED_PENDING_D11_AND_CONTRACT_REVIEW`; D9 remains
  `NOT RESOLVED`.

The future D9 decision must record the exact approved raw/IPC values, any
approved stream ceilings, the enforcement component and phase, UTF-8/binary
behavior, the event order `capture -> stop/close -> bounded drain ->
finalize -> publish -> reject later bytes`, the typed outcome set including
`STREAM_FINALIZATION_FAILED`, and the exact overflow action
`TERMINATE_AND_MARK_FAILED`. Drain/finalization failure must publish no
success, must still run cleanup, and must not carry raw stream content into
evidence or logs; cleanup failure may override the effective outcome. The
fixed model bound `max_new_tokens=512` remains in force but does not replace
these ceilings. The reviewed bounded implementation, not the old subprocess
`Connection.send` or the old in-process runner, is the historical offline
boundary; it does not provide current stdout/stderr enforcement. If a future
approved contract cannot prove these bounds, the owner must leave the live
run unapproved.

**2026-09-22 offline-implementation addendum (additive; does not change the
`NOT RESOLVED` planning disposition above).** The stdout/stderr half of this
decision has since been separately owner-approved with exact values
(`approvals/TASK_APPROVAL.md`, 2026-09-21: `stdout_max_bytes=16384`,
`stderr_max_bytes=32768`) and implemented, corrected, and independently
reviewed at HEAD. This addendum distinguishes three states that must not be
conflated:

- **Historical pre-implementation D9 package state (2026-09-21 and earlier,
  unchanged above):** `raw_output_max_bytes`/`ipc_envelope_max_bytes` remain
  owner-selected candidates only, and `D9_PACKAGE=DESIGN_RECORD_ONLY`.
- **Completed offline D9 stdout/stderr implementation/correction state
  (new, this addendum):** implemented at
  `552bc5d939f36b2b87dc7f0cea909110e8750107`; an independent post-commit
  review found four correctness gaps (F1-F4) and returned `BLOCKED`
  (`tmp/feat018-p2t2-d9-two-commit-post-commit-review-20260922/REVIEW.md`);
  the correction, confined to the same two authorized files, was
  independently reviewed with verdict `PASS`
  (`tmp/feat018-p2t2-d9-independent-correction-review-20260922/REVIEW.md`)
  and committed as `86836d24cfcd83ca14c0bc50e79fff1103cb9ecc`
  (`fix(feat018): close D9 stream enforcement gaps`; source blob
  `e1c89536e612b9f801ff2e429e76f3f0d0c370ee`, test blob
  `3a4db7fd56185da82749b95dd42ca1a3bdc13c0d`), independently re-verified by a
  follow-up commit checkpoint with verdict `PASS`
  (`tmp/feat018-p2t2-d9-followup-commit-checkpoint-20260922/REPORT.md`). No
  raw stream payload is retained or published, and no D9-created retry,
  additional attempt, adapter call, or session was introduced. The
  architecture validator's pre-existing `backend_ai_workflow.py` finding is
  unchanged.
- **Still-unresolved live D9/D11 carrier state (unchanged):** commit
  `86836d2` is not bound as `reviewed_runtime_code_commit`;
  `raw_output_max_bytes`/`ipc_envelope_max_bytes` remain unresolved;
  `D9_LIVE_D11_CARRIER_SCOPE=UNKNOWN_UNRESOLVED_PENDING_D11` and
  `P2T2-LIVE-D9` remain `NOT RESOLVED`; D11 and `D11.LIVE_SEAM_BINDING`
  remain `BLOCKED`, D1 remains `BLOCKED_BY_D11`, and Stage 4 remains
  `NOT READY`; and Lightning/model/GPU/provider/network execution remains
  `NOT AUTHORIZED`.

Full reconciliation detail, including before/after hashes and validation
results, is in
`evidence/notes/P2_T2_D9_GOVERNANCE_RECONCILIATION_20260922.md`. The
static-validation record for this addendum is Section 12.7.

### P2T2-LIVE-D10 - Exact GPU/SKU/VRAM/BF16 decision

Planning disposition: `READY_TO_RESOLVE`.

Approval requirements and observed runtime evidence are separate records.
The approval must state the permitted accelerator provider/tier, exact GPU
SKU, `device_count`, `device_index`, numeric `minimum_vram_mib`, required
`cuda=true`, required `bf16_supported=true`, driver-fact allowlist, and the
mismatch action `TERMINATE_SESSION_AND_MARK_FAILED`. The proposed readiness
class is the existing `NVIDIA_L4` boundary.

The D4 readiness activity observed an NVIDIA L4 and 23034 MiB VRAM. Those are
readiness-only runtime observations, not D10 approval inputs and not a Stage-4
execution result. D10 still requires independently stated approval
requirements and runtime matching.

At runtime, the allowlisted manifest must separately record the actual SKU,
device index/count, `vram_mib`, CUDA runtime fact, driver fact, and BF16 result;
the run must record single-device visibility from the provision-time facts or
bind a separate reviewed post-load assertion that the model and inference
inputs occupy the approved device index. The current `LightningPlacementFacts`
are produced before readiness and model load, so they cannot satisfy the
post-load alternative. If D10 selects that alternative, the missing typed
post-load carrier is a D11 fail-closed condition. Observed facts can satisfy
the approval only when they match it; they cannot silently supply missing
approval values, and an inventory-only check does not satisfy D10.

Record approved accelerator provider/tier, exact GPU SKU, device_count, device_index,
minimum_vram_mib, required cuda=true, required
bf16_supported=true, and the readiness mismatch action
TERMINATE_SESSION_AND_MARK_FAILED. The current readiness contract's expected
device class is NVIDIA_L4; selecting another SKU requires an already-approved
readiness boundary and cannot be made true by editing code during the run.
Require single approved-device visibility from the provision-time facts, or a
separately reviewed post-load carrier proving that the model and inference
inputs are placed on the approved device index. The reviewed source currently
provides only the provision-time `LightningPlacementFacts`; if the post-load
branch is selected, D10/D11 remain fail-closed until its carrier and placement
are bound. Inventory facts alone do not satisfy D10.

### P2T2-LIVE-D11 - Approved harness, glue boundary, and session ID

Planning disposition: `BLOCKED` pending three items:

- the concrete live-seam binding `P2T2-LIVE-D11.LIVE_SEAM_BINDING`
  (Section 2.7.7);
- the remaining live suitability (Section 2.5); and
- Stage 4 approval.

`LightningSessionController`, `LightningPreflight`, `LightningSmokeFinalizer`,
and `BoundedAdapterCall` in the reviewed FEAT-018 source are Protocol
boundaries, not concrete implementations.

Protocol != concrete Lightning controller, preflight, finalizer, or adapter
dispatch.

D11 cannot be resolved by `reviewed_runtime_code_commit=9549a34` alone. D11 owns
every concrete live seam. D11 cannot be considered resolved until
`P2T2-LIVE-D11.LIVE_SEAM_BINDING` binds all of the following:

- the approved host caller that constructs the runtime config, content policy,
  prompt, D6-bound request, and preflight input, verifies the caller-side
  prompt/config/request identities, and invokes `run_live_smoke`:
  - exact repository-relative module path or approved external entry;
  - immutable source/blob/content identity and review record;
  - host/session placement and any typed hand-off into the session;
  - dependency closure, including provider SDKs; and
  - sequence relationship to preflight, `AUTHORIZED_RUN_ATTEMPT_BEGINS`,
    staging, and adapter dispatch. No unbound caller may supply these values;
- the concrete `LightningSessionController`:
  - module/version or immutable source identity;
  - authentication boundary;
  - provision, wait-ready, and terminate semantics;
  - placement-fact source and GPU-budget meter source;
  - session-ID generation and handling rules;
  - the in-session checks it owns under Section 2.7.7;
  - the concrete `LightningPreflight`: its immutable source identity and the host
  checks it owns under Section 2.7.7. These include D2 admission and the
  owner-bound validation under
  `P2T2-LIVE-D6.MEDIA_VALIDATION_SOURCE`; no MIME/extension enforcer check is
  included, since `P2T2-LIVE-D6.MIME_EXTENSION_RULE` is
  `RESOLVED: REMOVE_REQUIREMENT`;
- the concrete `LightningSmokeFinalizer`: its immutable source identity and its
  delegation to `finalize_smoke_run` and incident handling;
- the concrete adapter-dispatch wrapper: its immutable source identity and the
  mechanism by which the unchanged `run_bounded_adapter_call` executes inside
  the Lightning session; and
- the typed-carrier and evidence-path resolution for the values in the
  Section 2.7.7 recording contract.

`P2T2-LIVE-D6.MIME_EXTENSION_RULE` is resolved (`REMOVE_REQUIREMENT`), and
`P2T2-LIVE-D6.MEDIA_VALIDATION_SOURCE` is resolved to the exact committed
image-only validator after its separate implementation approval and
independent binding review. The concrete preflight still cannot be bound until
D11 supplies its immutable seam identity and typed carriers. If a concrete
seam does not already exist in an independently reviewed approved boundary,
creating it requires a separate implementation authorization. This
plan-only correction does not authorize that implementation.

The synthetic session ID remains bounded and opaque, may be used in approved
bootstrap arguments, is excluded from progress IPC and published evidence
bodies, and is not resolved through a hidden session-store or database lookup.

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
  suitability and the concrete live-seam binding;
- `backend/tests/unit/test_feat018_live_lightning_execution.py` for all
  existing offline overflow, timeout, cleanup, cardinality and pair tests,
  plus the correction tests; live coordinator acceptance remains pending.

The offline coordinator implementation and independent/POSIX verification are
complete with findings closed. The owner-bound
`reviewed_runtime_code_commit` identifies the exact reviewed source/test blobs,
but does not resolve the remaining live suitability, the concrete live-seam
binding, the D4 snapshot's runtime revalidation, or Stage 4. The provenance
commits and current documentation HEAD cannot
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
`total_adapter_cap_seconds`, bounded IPC/logging, approved monotonic
budget/deadline enforcement, typed V2-to-Raw
mapping, finally cleanup, sanitized-manifest, postflight, and evidence-pair
checks. Its cardinality must be truthful: preflight or post-transition
pre-adapter `0/null`, in-dispatch pre-generation `1/null`, or model-reaching
`1/1` or `1/2` only, with attempt 2 allowed solely after an explicitly
classified transient failure. Adapter-local `attempt_number=0` is not a host
`attempt_count`.

Every authorized run attempt must have the exact sanitized JSON/Markdown pair,
including post-transition pre-adapter terminals. A preflight rejection is not
an authorized attempt and has no live pair or incident record. If evidence
creation is impossible after authorization, the safe ignored incident record
is the only permitted fallback and the run is not indexed. No missing call or
attempt is backfilled.

A typed failure is useful evidence of a stop gate but is not a functional
PASS. Cleanup failure is always overall FAILED. A smoke result does not
authorize indexing until P2T2-LIVE-D5 is resolved and the required
independent review occurs.

This draft records planning dispositions for P2T2-LIVE-D1 through D12 but
does not grant their separate live approval. The current dispositions are:

- D1/D11 remain BLOCKED.
- `P2T2-LIVE-D6.MIME_EXTENSION_RULE` is `RESOLVED: REMOVE_REQUIREMENT`;
  `P2T2-LIVE-D6.MEDIA_VALIDATION_SOURCE` is
  `RESOLVED: EXACT_COMMITTED_IMAGE_ONLY_VALIDATOR`; D6 overall remains
  `NOT FINALLY RESOLVED` because fixture identity remains
  `RESOLVED_WITH_PROPOSED_VALUE`. The D11 sub-decision remains `BLOCKED`.
- D4 is owner-approved for the pre-staged snapshot, with
  `D4 snapshot/readiness/identity = RESOLVED_FOR_RUNTIME_REVALIDATION` and
  runtime/session-local revalidation remaining after `SESSION_READY`.
- D2/D5/D8/D10 remain READY_TO_RESOLVE.
- The proposed values in the other rows still require the Stage 4 owner
  approval.

Offline coordinator implementation and independent/POSIX verification are
complete with findings closed. Live runtime suitability and the concrete
live-seam binding remain pending. The draft does not authorize live
execution, provider benchmark work, or closure of P2-T2. It also does not
authorize any FEAT-017 remote HTTPS adapter,
FEAT-003 modification, mobile, Gate A UI, P1 eligibility, P3/P4, shared
integration, P2-T3 narration, P2-T4/P2-T5 evaluation, commit, or push.

## 11. Canonical status and sequence (updated 2026-09-20 after the D6 owner binding)

Section 11 is the canonical status record.

- Blocks labeled `HISTORICAL` preserve earlier states for provenance only.
- The block labeled `CURRENT` is the only current state.
- Its `NEXT` value is the only current next gate.

The earlier conditional step `AFTER INDEPENDENT BINDING REVIEW RERUN PASS: NEXT =
RESOLVE_CONCRETE_D11_CONTROLLER` is superseded. The fifth independent binding
review returned `PASS`, and the owner then recorded the D6 source binding:
`P2T2-LIVE-D6.MIME_EXTENSION_RULE` remains `RESOLVED: REMOVE_REQUIREMENT`,
and `P2T2-LIVE-D6.MEDIA_VALIDATION_SOURCE` is now
`RESOLVED: EXACT_COMMITTED_IMAGE_ONLY_VALIDATOR` at commit
`16c52da26c444947ab4388712d9b7310480360b4`. The next gate recorded at that time was the independent
review of this D6 governance commit; that review/correction sequence is
historical and satisfied by the 2026-09-20 governance-review rerun `PASS`.
Section 11 `CURRENT` is the sole canonical current gate. Concrete live-seam
binding under D11 and D11 resolution remain downstream unresolved work.

```text
HISTORICAL - BEFORE THE 2026-09-17 PLAN-ONLY CORRECTION:
PLAN SEQUENCE = PASS WITH CORRECTIONS
NEXT = PLAN-ONLY CORRECTION
STAGE 4 = NOT READY
LIGHTNING = NOT AUTHORIZED
TIMING CODE = NOT AUTHORIZED

HISTORICAL - AFTER PLAN CORRECTION + STATIC VALIDATION (SATISFIED):
READY_FOR_INDEPENDENT_BINDING_REVIEW

HISTORICAL - FIRST INDEPENDENT BINDING REVIEW (2026-09-17):
INDEPENDENT_BINDING_REVIEW = PASS_WITH_FINDINGS
F-001 = D2 IMAGE-ADMISSION CLOSURE -> PLAN REMEDIATION IN SECTION 2.7.1
F-002 = READINESS/SCHEMA/BASE-RUNTIME CLOSURE -> PLAN REMEDIATION IN SECTION 2.7.2
F-003 = PRE-EXISTING backend_ai_workflow.py ARCHITECTURE FAILURE -> UNCHANGED; OUTSIDE THIS PLAN

HISTORICAL - AFTER BINDING-FINDINGS REMEDIATION + STATIC VALIDATION (SATISFIED):
PLAN_BINDING_FINDINGS_REMEDIATED
NEXT = INDEPENDENT_BINDING_REVIEW_RERUN (SATISFIED BY THE SECOND REVIEW)

HISTORICAL - SECOND INDEPENDENT BINDING REVIEW (2026-09-17):
INDEPENDENT_BINDING_REVIEW_RERUN = PASS_WITH_FINDINGS
R-001 = ADMISSION VERSUS MEDIA-QUALITY VALIDATION -> SECTIONS 2.7.1, 2.7.5; PRECONDITION 5; PHASES 0, 2; SECTIONS 5-7; D3, D6
R-002 = MIME/EXTENSION AGREEMENT -> SECTIONS 2.7.1, 2.7.6; PRECONDITION 5; D6
R-003 = CHECK OWNERSHIP, RECORDING, VERIFICATION -> SECTION 2.7.7; PHASES 0-1; SECTIONS 7-8
R-004 = CONCRETE LIVE-SEAM OWNERSHIP -> SECTIONS 2.7, 2.7.7, 9; D11; THIS SEQUENCE
R-005 = STALE PLAN STATE -> HEADER; UPDATE HISTORY; SECTIONS 11-12
R-006 = RUNTIME INVENTORY SCOPE -> SECTION 2.7.2
R-007 = IMPORT-TIME CLOSURE -> SECTION 2.7.4

HISTORICAL - AFTER T-001 BOUNDARY WORDING CORRECTION (2026-09-18):
T001_PREAUTHORIZATION_BOUNDARY_WORDING_CORRECTED
The plan now separates preflight from the authorized run body: preflight
failure returns `0/null` with no evidence/finalizer, while `finally` cleanup
starts only after the authorized boundary. Post-transition pre-adapter
terminals retain the bound cleanup/finalization path.
NEXT = INDEPENDENT_BINDING_REVIEW_RERUN

HISTORICAL - THIRD INDEPENDENT BINDING REVIEW (2026-09-18):
INDEPENDENT_BINDING_REVIEW_RERUN = PASS_WITH_FINDINGS
T-002..T-007 = REMEDIATED (UNCHANGED BY THIS CORRECTION)
F-001 = AUTHORIZED-RUN BOUNDARY ORDER -> SECTIONS 1, 2.7.7; PHASE 0; TRANSITION SUBSECTION; PHASE 4; SECTIONS 5, 5.1, 5.2, 6
F-002 = D1 WORDING -> SECTION 9 STATUS TABLE AND P2T2-LIVE-D1

HISTORICAL - AFTER F-001/F-002 CORRECTION (2026-09-18):
F001_AUTHORIZED_RUN_BOUNDARY_ORDER_ALIGNED
AUTHORIZED_RUN_ATTEMPT_BEGINS = plan-level transition immediately before the
reviewed lifecycle `try`, after successful preflight, successful
lifecycle-boundary construction, and successful counter/state initialization;
pre-transition failures return `0/null` with no evidence pair or finalizer;
post-transition failures use the bound cleanup/finalization path.
F002_D1_WORDING_CORRECTED
D1 = BLOCKED pending remaining D1 owner resolution; source/test identity is
already owner-bound; Stage 4 remains blocked until D1 is resolved.
NEXT = INDEPENDENT_BINDING_REVIEW_RERUN

HISTORICAL - FOURTH INDEPENDENT BINDING REVIEW (2026-09-18):
INDEPENDENT_BINDING_REVIEW_RERUN = BLOCKED
F-001 = CLOSED IN PLAN CONTENT (boundary order verified against 9549a34)
F-002 = CLOSED (D1 wording verified)
B-001 = SECTION 12 PREAMBLE NAMED SUPERSEDED 12.2 AS CURRENT -> CORRECTED BELOW

HISTORICAL - AFTER B-001 CORRECTION (2026-09-18):
B001_SECTION_12_PREAMBLE_CORRECTED
Section 12 preamble now names 12.0-12.3 as HISTORICAL/SUPERSEDED and 12.4 as
the current validation record, matching the section headings. Section 12.3
is relabeled HISTORICAL (SUPERSEDED) and a new Section 12.4 CURRENT record
is added.
NEXT = INDEPENDENT_BINDING_REVIEW_RERUN

HISTORICAL - FIFTH INDEPENDENT BINDING REVIEW (2026-09-18):
INDEPENDENT_BINDING_REVIEW = PASS
F-001 = CLOSED (unaffected by the B-001 correction; re-confirmed against 9549a34)
F-002 = CLOSED (unaffected by the B-001 correction; re-confirmed)
B-001 = CORRECTED AND VERIFIED
NEXT (AT THAT TIME) = OWNER_SELECT_D6_SUBDECISIONS

HISTORICAL - AFTER D6 OWNER-DECISION RECORDING (2026-09-18):
D6_MIME_EXTENSION_RULE_RESOLVED_REMOVE_REQUIREMENT
The owner resolved `P2T2-LIVE-D6.MIME_EXTENSION_RULE` to
`RESOLVED: REMOVE_REQUIREMENT` (Section 2.7.6): no MIME/extension claim, no
enforcer, `image_admission_evaluation.py`/Cohort B tooling excluded, D2
responsibilities and B01.jpg's owner-reviewed metadata unchanged.
D6_MEDIA_VALIDATION_SOURCE_SELECTED_PENDING_IMPLEMENTATION
The owner selected `P2T2-LIVE-D6.MEDIA_VALIDATION_SOURCE` =
`SELECTED_PENDING_SEPARATE_IMPLEMENTATION_AND_REVIEW` (Section 2.7.5):
image-only input, no fabricated audio, `DeterministicMediaValidator` not
selected; a separate implementation approval, validator/result contract,
provenance hash rule, exact identity, focused tests, and independent review
are required before `RESOLVED`.
D6 = NOT FINALLY RESOLVED
NEXT = SEPARATE_IMAGE_ONLY_VALIDATOR_IMPLEMENTATION_APPROVAL

CURRENT (AFTER T-001..T-007 REMEDIATION, T-001 WORDING CORRECTION, F-001/F-002 CORRECTION, B-001 CORRECTION, D6 OWNER BINDING + STATIC VALIDATION):
PLAN_T001_T007_REMEDIATION_COMPLETE
T001_PREAUTHORIZATION_BOUNDARY_WORDING_CORRECTED
F001_AUTHORIZED_RUN_BOUNDARY_ORDER_ALIGNED
F002_D1_WORDING_CORRECTED
B001_SECTION_12_PREAMBLE_CORRECTED
D6_BINDING_REVIEW = PASS
D6_BINDING_PACKAGE = OWNER_APPROVED
D6_OWNER_DECISION = RECORDED
NEXT=PREPARE_D1_OWNER_RESOLUTION_AND_D6_FIXTURE_BINDING
D1 = BLOCKED
D4 = OWNER-APPROVED_PRESTAGED_LOCAL_SNAPSHOT
D4 snapshot/readiness/identity = RESOLVED_FOR_RUNTIME_REVALIDATION
D4 runtime/session-local revalidation = STAGE_4_LOCAL_ONLY_AFTER_SESSION_READY
D6 = NOT FINALLY RESOLVED; FIXTURE IDENTITY = RESOLVED_WITH_PROPOSED_VALUE
D6.MEDIA_VALIDATION_SOURCE = RESOLVED: EXACT_COMMITTED_IMAGE_ONLY_VALIDATOR
D6.MIME_EXTENSION_RULE = RESOLVED: REMOVE_REQUIREMENT
D9_PACKAGE = DESIGN_RECORD_ONLY
D9 numeric ceilings = OWNER_SELECTED_CANDIDATE_ONLY
D9 stdout/stderr enforcement = SEPARATE_ENFORCEMENT_APPROVAL_REQUIRED
D9_LIVE_D11_CARRIER_SCOPE = UNKNOWN_UNRESOLVED_PENDING_D11
D9_PACKAGE_REVIEW = BLOCKED_PENDING_D11_AND_CONTRACT_REVIEW
D9 = NOT RESOLVED
D11 = BLOCKED
D11.LIVE_SEAM_BINDING = BLOCKED PENDING APPROVED HOST CALLER, CONCRETE LightningPreflight, LightningSessionController, LightningSmokeFinalizer, ADAPTER-DISPATCH, AND TYPED-CARRIER BINDING
STAGE 4 = NOT READY
LIGHTNING/MODEL/GPU/PROVIDER/NETWORK EXECUTION = NOT AUTHORIZED
reviewed_runtime_code_commit = 9549a341194f40b1a9be419d6fce0d70f1ca0384

THEN:
PREPARE_D1_OWNER_RESOLUTION_AND_D6_FIXTURE_BINDING
(owner-resolution preparation and exact D6 fixture-identity binding; this does
not resolve D1, D6 overall, D11, Stage 4, or the proposed fixture identity)

THEN:
BIND_CONCRETE_LIVE_SEAMS_UNDER_D11
(APPROVED HOST CALLER, LightningPreflight, LightningSessionController,
LightningSmokeFinalizer, ADAPTER DISPATCH, AND TYPED CARRIERS; bind each
immutable identity, environment placement, dependency closure, and sequence;
A SEPARATE IMPLEMENTATION AUTHORIZATION IS REQUIRED WHERE NO REVIEWED SEAM
EXISTS)

THEN:
RESOLVE_D11

THEN:
OWNER_D1_D12_RESOLUTION

THEN:
STAGE_4_APPROVAL_DRAFT
-> INDEPENDENT_STAGE_4_REVIEW
-> OWNER_STAGE_4_APPROVAL
-> COMMIT_APPROVAL
-> EXTERNALLY_BIND_APPROVAL_RECORD_COMMIT
-> LIGHTNING_PREFLIGHT
-> EXACTLY_ONE_SMOKE
-> CLEANUP
-> PROVISIONAL_EVIDENCE
-> POSTFLIGHT
-> FINAL_JSON
-> SEPARATE_GOVERNANCE_DOCS_UPDATE
```

**2026-09-22 addendum (status-neutral; does not change the `CURRENT` block,
its `NEXT`, the THEN sequence above, or any D1/D4/D6/D11/Stage-4 status, and
does not resolve `P2T2-LIVE-D9`).** The D9 offline stdout/stderr enforcement
implementation described in the "P2T2-LIVE-D9" section's 2026-09-22 addendum
(Section 9, above) and in the Canonical reconciliation state block at the top
of this document is reconciled here. It is a documentation-only
reconciliation of already-committed, already-independently-reviewed work
(commit `86836d24cfcd83ca14c0bc50e79fff1103cb9ecc`); it performs no
Lightning, GPU, model, provider, network, subprocess, or benchmark execution,
and it does not advance the THEN sequence above, which still begins with
`PREPARE_D1_OWNER_RESOLUTION_AND_D6_FIXTURE_BINDING`. This addendum is not a
canonical current-state source: the `CURRENT` block above remains the sole
canonical current-state block, and its
`NEXT=PREPARE_D1_OWNER_RESOLUTION_AND_D6_FIXTURE_BINDING` remains the only
global next gate. The separate approval called for by the `CURRENT` line
`D9 stdout/stderr enforcement = SEPARATE_ENFORCEMENT_APPROVAL_REQUIRED` was
granted by the owner on 2026-09-21 (`approvals/TASK_APPROVAL.md`); this
addendum records that fact without amending the `CURRENT` block. The review
gate for this D9 reconciliation package is package-local only:
`FRESH_INDEPENDENT_D9_GOVERNANCE_RECONCILIATION_REREVIEW`. It does not
replace, supersede, or satisfy the global `NEXT`. Its static-validation
record is Section 12.7.

## 12. Static validation records

Section 12 keeps each correction's validation record for provenance.

- Sections 12.0, 12.1, 12.2, 12.3, 12.4, and 12.5 are `HISTORICAL` and
  `SUPERSEDED`. Their `NEXT` values were satisfied and are not current.
- Section 12.6 is `HISTORICAL` (`SUPERSEDED`) as a validation record only.
  Its `NEXT` value, `PREPARE_D1_OWNER_RESOLUTION_AND_D6_FIXTURE_BINDING`, is
  not satisfied; it remains the current global gate in Section 11 `CURRENT`.
- Section 12.7 is the current validation record.
- Section 11 `CURRENT` is canonical.

### 12.0 HISTORICAL (SUPERSEDED): plan-only correction validation (2026-09-17)

The corrected tracked diff must contain exactly one file:

`features/FEAT-018-live-image-canvas-flow/plan/P2_T2_LIVE_LIGHTNING_EXECUTION_PLAN_DRAFT_20260913.md`

Validation must establish:

- no mandatory `*_wall_clock_ms` remains;
- no source/test file changed;
- no P2-T4 file changed;
- D4 remains `OWNER-APPROVED_PRESTAGED_LOCAL_SNAPSHOT`;
- D1 remains `BLOCKED` pending owner resolution;
- D11 remains `BLOCKED` pending concrete-controller binding;
- Stage 4 remains `NOT READY`;
- Lightning remains `NOT AUTHORIZED`;
- `reviewed_runtime_code_commit` remains
  `9549a341194f40b1a9be419d6fce0d70f1ca0384`;
- `approval_record_commit` is described as externally supplied only after the
  approval commit exists;
- authorized pre-adapter terminals retain `0/null` cardinality and sanitized
  FAILED evidence semantics;
- failure before an authorized run begins does not create a live evidence pair;
- cleanup precedes provisional evidence and postflight;
- governance/docs updates occur after the run evidence lifecycle closes; and
- `git diff --check` passes.

Historical successful disposition (satisfied by the first independent binding
review; not current):

```text
PLAN_ONLY_CORRECTION = COMPLETE
STATIC_VALIDATION = PASS
NEXT = READY_FOR_INDEPENDENT_BINDING_REVIEW
```

### 12.1 HISTORICAL (SUPERSEDED): binding-findings remediation validation (2026-09-17)

Section 12.2 and Sections 2.7.1-2.7.7 supersede this record. In particular,
the R-003 map in Section 2.7.7 supersedes the description below of admission
and readiness reaching the reviewed source only through `LightningPreflight`.
Section 2.7.6 supersedes the open MIME/extension note.

The binding-findings remediation for independent binding review findings
F-001 and F-002 changes only this same plan file. The tracked diff still
contains exactly one file. Validation must additionally establish:

- Section 2.7.1 enumerates the complete P2-T1 D2 image-admission closure with
  a read-only identity reference for each path. The source paths below are
  abbreviated relative to `backend/src/sketch2life/`; Section 2.7.1 gives the
  full repository-relative paths:
  - `application/services/image_admission.py`;
  - `domain/understanding/image_admission.py`;
  - `infrastructure/media_validation/av_image_decoder.py`;
  - `application/ports/image_decoder.py`;
  - `contracts/schemas/media_validation.py`;
  - the transitive `domain/understanding/media_quality.py`; and
  - `backend/pyproject.toml`, including `av==18.1.0`.
- Section 2.7.1 states that the reviewed runner/coordinator source consumes
  admission and readiness only through the injected `LightningPreflight`
  Protocol, whose concrete implementation must be bound before Stage 4. It also
  records the open MIME/extension reconciliation without resolving it.
- Section 2.7.2 enumerates `qwen_vision_environment_readiness.py` and the
  runtime schema dependencies `vision_v2.py`, `vision.py`,
  `raw_understanding.py`, and `media_validation.py` with identity references.
- Section 2.7.2 records Python `>=3.12,<3.14`, `pydantic>=2.11,<3`,
  `pydantic-settings>=2.10,<3`, and the absence of any Python dependency
  lockfile. It requires an immutable runtime manifest or an exact package and
  source inventory before Stage 4.
- No dependency identity is described as covered by
  `reviewed_runtime_code_commit`, which remains
  `9549a341194f40b1a9be419d6fce0d70f1ca0384` for the two reviewed FEAT-018
  source/test blobs only.
- The complete dependency set must be frozen before Stage 4 and verified in
  the future approved execution checkout.
- `backend/pyproject.toml` is unchanged, and nothing is installed.
- The gates are unchanged:
  - D1 remains `BLOCKED`;
  - D4 remains `OWNER-APPROVED_PRESTAGED_LOCAL_SNAPSHOT`, subject to runtime
    revalidation;
  - D11 remains `BLOCKED` pending a concrete `LightningSessionController`;
  - Stage 4 remains `NOT READY`; and
  - Lightning, model, GPU, provider, and network execution remain
    `NOT AUTHORIZED`.
- No source, test, approval, evidence, or P2-T4 file changed.
- `git diff --check` passes.
- The known `backend_ai_workflow.py` architecture-validator failure is
  classified separately as pre-existing and unchanged.

Historical successful disposition (satisfied by the second independent binding
review, verdict `PASS_WITH_FINDINGS`; not current):

```text
PLAN_BINDING_FINDINGS_REMEDIATED
NEXT = INDEPENDENT_BINDING_REVIEW_RERUN
```

### 12.2 HISTORICAL (SUPERSEDED): T-001..T-007 plan-remediation validation (2026-09-17)

This plan-only remediation changes exactly the same one tracked plan file. It
does not implement a caller, typed carrier, finalizer path, staging hand-off,
post-load placement assertion, source/test behavior, or owner decision.
Validation must establish:

- **T-001 — preflight evidence boundary.** The selected rule is
  `PREFLIGHT_PREAUTHORIZATION_NO_EVIDENCE_PAIR`: preflight failures return
  `0/null` before the reviewed counters/finalizer, create no live evidence
  pair or incident record, and are not authorized attempts. Post-transition
  pre-adapter terminals remain `0/null` through a separately bound,
  non-fabricating finalization path. The plan explicitly forbids fabricating a
  `SupervisorRunResult`; D11 remains blocked if that carrier/path is absent.
  The Phase 4 `finally` wording applies only after
  `AUTHORIZED_RUN_ATTEMPT_BEGINS`; it does not wrap or finalize the
  pre-authorization preflight.
- **T-002 — cardinality.** Every in-dispatch pre-generation path, including
  adapter input rejection, containment/launch failure, dispatch exception,
  invalid result, and pre-attempt hang, is `adapter_call_count=1` with
  `attempt_count=null`. Adapter-local `attempt_number=0` is not host progress.
  No unsupported host `1/0` or runner-boundary `0/null` claim remains, and the
  test-coverage statement does not claim a dedicated adapter-input-rejection
  case.
- **T-003 — evidence hand-offs.** Inventory baseline and Git-ignored incident
  confirmation have dedicated map rows. All Section 5 assertions and Section 7
  metadata beyond the six core values are explicitly fail-closed unless D11
  binds a reviewed producer, typed carrier/writer hand-off, serialization
  rule, and verification point, or the owner re-scopes them. The finalizer and
  writer may publish only values they receive.
- **T-004 — call order and placement.** Prompt hashing and request construction
  occur in the approved caller before `run_live_smoke`; runtime-config loading
  is tied to the environment where `from_env_file` executes; D8 staging must
  establish the prebuilt request's reference or provide a reviewed hand-off;
  provision-time placement is not presented as post-load placement. An
  unbound post-load carrier fails closed under D10/D11.
- **T-005 — approved caller identity.** The caller is listed in the D11 seam
  set, dependency identity set, Section 2.7.7 map, and Section 11 sequence;
  its immutable identity, placement, dependency closure, and call sequence
  remain required before D11.
- **T-006 — core import identities.** `qwen_vision.py`,
  `raw_understanding_mapper.py`, `vision_c1_prompt_mapping_study.py`, and
  `vision_lexical_policy.py` each have a `REQUIRED` import-closure row with
  loader, environment, Git blob, and blob-content SHA-256 identities.
- **T-007 — inventory dependency scope.** Host and session must-match lists
  include dependencies of every concrete D11 seam and the approved caller,
  including provider SDKs, while preserving complete transitive distribution
  inventory requirements.
- **Scope and gates.** No source, test, approval, evidence, context, decision,
  `pyproject.toml`, P2-T4, or governance file changed; nothing is installed.
  D1 remains `BLOCKED`; D4 remains
  `OWNER-APPROVED_PRESTAGED_LOCAL_SNAPSHOT` with runtime revalidation; both D6
  sub-decisions remain `BLOCKED`/unselected; D11 remains `BLOCKED`; Stage 4 is
  `NOT READY`; Lightning/model/GPU/provider/network execution remains
  `NOT AUTHORIZED`; and `reviewed_runtime_code_commit` remains
  `9549a341194f40b1a9be419d6fce0d70f1ca0384`.
- **Validation commands.** Results are recorded below only after the one-file
  diff and permitted static validators run. No pytest, model, GPU, provider,
  network, subprocess, or Lightning execution is performed.

STATIC_VALIDATION = PASS_WITH_PRE_EXISTING_ARCHITECTURE_FAILURE
git diff --check = PASS
python -B tools/validate_harness.py = PASS
python -B tools/validate_repository_security.py = PASS
python -B tools/validate_skeleton.py = PASS
python -B tools/validate_architecture.py = FAIL; pre-existing unchanged
  finding: application/services/backend_ai_workflow.py imports an outer layer
ARCHITECTURE_FAILURE_CLASSIFICATION = PRE_EXISTING_UNCHANGED_OUTSIDE_THIS_PLAN

Historical disposition (superseded by Section 12.3):

```text
PLAN_T001_T007_REMEDIATION_COMPLETE
NEXT=INDEPENDENT_BINDING_REVIEW_RERUN
```

### 12.3 HISTORICAL (SUPERSEDED): F-001/F-002 boundary-order and D1 wording correction validation (2026-09-18)

Section 12.4 supersedes this record. The fourth independent binding review
(2026-09-18) returned `BLOCKED` on finding B-001: the Section 12 preamble
above still named the earlier, already-superseded Section 12.2 as the
current validation record instead of this section. The F-001 and F-002
dispositions recorded below were independently re-verified against the
`9549a34` source and the plan text by that review and found unchanged and
closed; only the preamble's stale pointer was defective.

This plan-only correction changes exactly the same one tracked plan file. It
implements no code, binds no seam, selects no D6 sub-decision, resolves no
D11 item, creates no Stage 4 approval, and claims no PASS. Validation must
establish:

- **F-001 — authorized-run boundary order.** The plan's transition definition
  matches the reviewed source order at `reviewed_runtime_code_commit`
  `9549a341194f40b1a9be419d6fce0d70f1ca0384`: preflight (L3297-3314) ->
  successful lifecycle-boundary construction (L3316-3328) -> successful
  counter/state initialization (L3330-3349) -> `AUTHORIZED_RUN_ATTEMPT_BEGINS`
  -> reviewed lifecycle `try` (L3360) -> `finally` cleanup (L3595) -> the only
  finalizer call (L3668). Any failure before the transition is
  pre-authorization (`0/null`, no evidence pair, no finalizer). Any failure
  after it uses the bound cleanup/finalization path. No runtime token or
  source field is invented. All Phase-0 checks remain pre-transition;
  post-transition examples are limited to in-session checkout revalidation,
  D4 snapshot runtime revalidation, staged-fixture digest verification,
  observed session hardware/readiness, runtime manifest, and
  TTL/budget/session gates. Sections 1, 2.7.7, Phase 0, the transition
  subsection, Phase 4, 5, 5.1, 5.2, and 6 are consistent with that order.
- **F-002 — D1 wording.** The Section 9 status table and the P2T2-LIVE-D1
  section state `BLOCKED` pending remaining D1 owner resolution, with
  source/test identity already owner-bound, and that Stage 4 remains blocked
  until D1 is resolved. No wording implies that Stage 4 approval is required
  to resolve D1. The canonical sequence is unchanged.
- **T-002..T-007.** Unchanged and closed.
- **Scope and gates.** No source, test, approval, evidence, context, decision,
  P2-T4, P2-T5, timing-remediation, manifest, or generated file changed.
  The plan remains DRAFT, NOT AN APPROVAL, NOT AN IMPLEMENTATION
  AUTHORIZATION, and NOT A LIVE EXECUTION AUTHORIZATION. D1 remains
  `BLOCKED`; D4 remains `OWNER-APPROVED_PRESTAGED_LOCAL_SNAPSHOT` with runtime
  revalidation; both D6 sub-decisions remain `BLOCKED`/unselected; D11 remains
  `BLOCKED`; Stage 4 is `NOT READY`; Lightning/model/GPU/provider/network
  execution remains `NOT AUTHORIZED`; no mandatory `*_wall_clock_ms`
  requirement is reintroduced; and `reviewed_runtime_code_commit` remains
  `9549a341194f40b1a9be419d6fce0d70f1ca0384`.
- **Validation commands.** Results are recorded below only after the one-file
  diff and permitted static validators run. No pytest, model, GPU, provider,
  network, subprocess, or Lightning execution is performed.

STATIC_VALIDATION = PASS_WITH_PRE_EXISTING_ARCHITECTURE_FAILURE
git diff --check = PASS
python -B tools/validate_harness.py = PASS (HARNESS_VALID)
python -B tools/validate_repository_security.py = PASS (REPOSITORY_SECURITY_VALID)
python -B tools/validate_skeleton.py = PASS (SKELETON_VALID)
python -B tools/validate_architecture.py = FAIL; pre-existing unchanged
  finding: application/services/backend_ai_workflow.py imports an outer layer
ARCHITECTURE_FAILURE_CLASSIFICATION = PRE_EXISTING_UNCHANGED_OUTSIDE_THIS_PLAN
MARKER_STATUS_WHITESPACE_ASSERTIONS = PASS (no CRLF, no trailing whitespace,
  no stale "D1 owner resolution and Stage 4 approval" wording, no mandatory
  `*_wall_clock_ms` requirement, all gate markers present)

Historical disposition (superseded by Section 12.4):

```text
PLAN_T001_T007_REMEDIATION_COMPLETE
F001_AUTHORIZED_RUN_BOUNDARY_ORDER_ALIGNED
F002_D1_WORDING_CORRECTED
NEXT=INDEPENDENT_BINDING_REVIEW_RERUN
```

### 12.4 HISTORICAL (SUPERSEDED): B-001 Section 12 preamble correction validation (2026-09-18)

Section 12.5 supersedes this record. The fifth independent binding review
(2026-09-18) returned `PASS` after this correction; the owner then recorded
the `P2T2-LIVE-D6` sub-decisions described in Section 12.5. B-001, F-001, and
F-002 were not re-litigated by that later step and remain as recorded below.

This plan-only correction changes exactly the same one tracked plan file. It
implements no code, binds no seam, selects no D6 sub-decision, resolves no
D11 item, creates no Stage 4 approval, and claims no PASS. It corrects only
finding B-001 from the fourth independent binding review: the Section 12
preamble (this section's own introductory bullets) named the earlier,
already-superseded Section 12.2 as the current validation record instead of
the section that was actually current at that time. Validation must
establish:

- **B-001 — Section 12 preamble.** The preamble bullets now read "Sections
  12.0, 12.1, 12.2, and 12.3 are `HISTORICAL` and `SUPERSEDED`" and "Section
  12.4 is the current validation record," matching the section headings:
  12.0, 12.1, 12.2, and 12.3 are each labeled `HISTORICAL (SUPERSEDED)`, and
  this section, 12.4, is labeled `CURRENT`.
- **F-001, F-002.** Unchanged from Section 12.3; re-confirmed closed by the
  fourth independent binding review against the `9549a34` source and the
  plan text. Not re-litigated by this correction.
- **T-002..T-007.** Unchanged and closed.
- **Scope and gates.** No source, test, approval, evidence, context, decision,
  P2-T4, P2-T5, timing-remediation, manifest, or generated file changed.
  The plan remains DRAFT, NOT AN APPROVAL, NOT AN IMPLEMENTATION
  AUTHORIZATION, and NOT A LIVE EXECUTION AUTHORIZATION. D1 remains
  `BLOCKED`; D4 remains `OWNER-APPROVED_PRESTAGED_LOCAL_SNAPSHOT` with runtime
  revalidation; both D6 sub-decisions remain `BLOCKED`/unselected; D11 remains
  `BLOCKED`; Stage 4 is `NOT READY`; Lightning/model/GPU/provider/network
  execution remains `NOT AUTHORIZED`; no mandatory `*_wall_clock_ms`
  requirement is reintroduced; and `reviewed_runtime_code_commit` remains
  `9549a341194f40b1a9be419d6fce0d70f1ca0384`.
- **Validation commands.** Results are recorded below only after the one-file
  diff and permitted static validators run. No pytest, model, GPU, provider,
  network, subprocess, or Lightning execution is performed.

STATIC_VALIDATION = PASS_WITH_PRE_EXISTING_ARCHITECTURE_FAILURE
git diff --check = PASS
python -B tools/validate_harness.py = PASS (HARNESS_VALID)
python -B tools/validate_repository_security.py = PASS (REPOSITORY_SECURITY_VALID)
python -B tools/validate_skeleton.py = PASS (SKELETON_VALID)
python -B tools/validate_architecture.py = FAIL; pre-existing unchanged
  finding: application/services/backend_ai_workflow.py imports an outer layer
ARCHITECTURE_FAILURE_CLASSIFICATION = PRE_EXISTING_UNCHANGED_OUTSIDE_THIS_PLAN
MARKER_STATUS_WHITESPACE_ASSERTIONS = PASS (no CRLF, no trailing whitespace,
  no stale "D1 owner resolution and Stage 4 approval" wording, no mandatory
  `*_wall_clock_ms` requirement, all gate markers present, Section 12 preamble
  now points to 12.4)

Historical disposition (superseded by Section 12.5):

```text
PLAN_T001_T007_REMEDIATION_COMPLETE
F001_AUTHORIZED_RUN_BOUNDARY_ORDER_ALIGNED
F002_D1_WORDING_CORRECTED
B001_SECTION_12_PREAMBLE_CORRECTED
NEXT=INDEPENDENT_BINDING_REVIEW_RERUN
```

### 12.5 HISTORICAL (SUPERSEDED): P2T2-LIVE-D6 owner-decision recording validation (2026-09-18)

This is a governance/documentation change only. It implements no code, binds
no D11 seam, resolves no D11 item, creates no Stage 4 approval, and does not
implement or test the image-only media validator. It records two owner
decisions on the `P2T2-LIVE-D6` sub-decisions, made after the fifth
independent binding review returned `PASS`. Validation must establish:

- **`P2T2-LIVE-D6.MEDIA_VALIDATION_SOURCE` = `SELECTED_PENDING_SEPARATE_IMPLEMENTATION_AND_REVIEW`.**
  Recorded in Sections 2.7.5, 9 (status table and P2T2-LIVE-D6 section), and
  11. The recorded decision requires image-only input, forbids fabricated
  audio, does not select the existing `DeterministicMediaValidator`, and
  requires a separate implementation approval plus a validator/result
  contract, provenance serialization/hash rule, exact identity, focused
  tests, and independent review before this sub-decision becomes `RESOLVED`.
  `P2T2-LIVE-D6` overall remains `NOT FINALLY RESOLVED` until then.
- **`P2T2-LIVE-D6.MIME_EXTENSION_RULE` = `RESOLVED: REMOVE_REQUIREMENT`.**
  Recorded in Sections 2.7.1, 2.7.6, 9, and 11, and in precondition 5, the
  Phase 0 preflight bullet, the check-to-owner map, the dependency-closure
  lists in Section 2.7 and 2.7.2, the Section 2.7.4 import-classification
  rows, and Section 6. The live path makes no MIME/extension-agreement
  claim; `image_admission_evaluation.py` and the offline Cohort B tooling
  are not added to the live path; D2's admission responsibilities (bounded
  decode, container/codec/pixel-format checks, source/staged digest
  equality) are unchanged; B01.jpg's MIME/extension remains owner-reviewed
  metadata only; no MIME/extension enforcer is added.
- **Preserved states.** D6 fixture identity remains
  `RESOLVED_WITH_PROPOSED_VALUE`; D1 remains `BLOCKED`; D11 and
  `D11.LIVE_SEAM_BINDING` remain `BLOCKED`; Stage 4 remains `NOT READY`;
  Lightning/model/GPU/provider/network execution remains `NOT AUTHORIZED`;
  `reviewed_runtime_code_commit` remains
  `9549a341194f40b1a9be419d6fce0d70f1ca0384`; T-002..T-007 remain closed; no
  mandatory `*_wall_clock_ms` requirement is reintroduced.
- **Scope.** Only this plan file, `CONTEXT.md`, and `DECISIONS.md` under this
  feature changed. No source, test, evidence, P2-T4, P2-T5, or
  timing-remediation file changed. No D1/D2/D3/D4/D5/D7-D12 decision was
  selected or changed. TASK_APPROVAL.md gained one dated addendum recording
  the same two decisions, consistent with the existing addendum-per-owner-
  decision format used for D4 and the reviewed-source binding.
- **Validation commands.** Results are recorded below only after the
  three-file diff and permitted static validators run. No pytest, model,
  GPU, provider, network, subprocess, or Lightning execution is performed.

STATIC_VALIDATION = PASS_WITH_PRE_EXISTING_ARCHITECTURE_FAILURE
git diff --check = PASS
python -B tools/validate_harness.py = PASS (HARNESS_VALID)
python -B tools/validate_repository_security.py = PASS (REPOSITORY_SECURITY_VALID)
python -B tools/validate_skeleton.py = PASS (SKELETON_VALID)
python -B tools/validate_architecture.py = FAIL; pre-existing unchanged
  finding: application/services/backend_ai_workflow.py imports an outer layer
ARCHITECTURE_FAILURE_CLASSIFICATION = PRE_EXISTING_UNCHANGED_OUTSIDE_THIS_PLAN
MARKER_STATUS_WHITESPACE_ASSERTIONS = PASS (no CRLF, no trailing whitespace,
  all gate markers present, Section 12 preamble points to 12.5, no
  BIND_ENFORCER wording left implying an enforcer was added, no
  DeterministicMediaValidator selection claimed)

Current disposition:

```text
D6_OWNER_DECISIONS_RECORDED = PASS
D6_MEDIA_VALIDATION = PENDING_SEPARATE_IMPLEMENTATION_AND_REVIEW
D6_MIME_EXTENSION = RESOLVED_REMOVE_REQUIREMENT
D6_OVERALL = NOT_FINALLY_RESOLVED
NEXT = SEPARATE_IMAGE_ONLY_VALIDATOR_IMPLEMENTATION_APPROVAL
```

### 12.6 HISTORICAL (SUPERSEDED): P2T2-LIVE-D6 owner binding validation (2026-09-20)

This is a governance/documentation synchronization only. It records the
owner-approved D6 media-validation-source binding after the independent D6
binding review returned `PASS`. It changes no implementation, test, D2
dependency, security validator, runtime seam, worktree, or stash, and it does
not create a Stage 4 approval.

Validation establishes:

- `D6_BINDING_REVIEW = PASS`;
- `D6_BINDING_PACKAGE = OWNER_APPROVED`;
- `D6_OWNER_DECISION = RECORDED`;
- `D6.MEDIA_VALIDATION_SOURCE = RESOLVED: EXACT_COMMITTED_IMAGE_ONLY_VALIDATOR`;
- `D6.MIME_EXTENSION_RULE = RESOLVED: REMOVE_REQUIREMENT`;
- the exact validator commit is
  `16c52da26c444947ab4388712d9b7310480360b4`, with contract
  `ImageOnlyValidationResultV1@1.0`, validator
  `feat018-image-only-structural-validator-v1`, and policy
  `feat018-image-only-structural-policy-v1`;
- the accepted grammar is the exact five-pattern grammar in Section 2.7.5;
  `fixture-b[0-9]{2}` syntactically permits B00-B99 without asserting fixture
  existence, owner review, or live authorization; and
- D4 pre-Stage-4 state is
  `D4 snapshot/readiness/identity = RESOLVED_FOR_RUNTIME_REVALIDATION`, with
  runtime/session-local revalidation only after Stage 4 approval and
  `SESSION_READY`, followed by D8 staging and staged digest verification and
  exactly one smoke.

The CI scope remains narrow: run `35500484772` proves only that the
`feat018-posix` process-group cleanup workflow passed for commit `16c52da`; it
is not full validator CI or full repository validation. D6 overall remains
`NOT FINALLY RESOLVED` because fixture identity remains
`RESOLVED_WITH_PROPOSED_VALUE`. D11 remains `BLOCKED`, Stage 4 remains
`NOT READY`, and live/model/GPU/provider/network/Lightning execution remains
`NOT AUTHORIZED`.

Only the requested governance files changed: this plan, `CONTEXT.md`,
`DECISIONS.md`, and the dated owner addendum in
`approvals/TASK_APPROVAL.md`. The original four-file implementation approval
marker remains unchanged and appears exactly once. No pytest, model, GPU,
provider, network, Lightning, live smoke, commit, or push action is performed
by this documentation task.

```text
STATIC_VALIDATION = PASS
git diff --check = PASS
D6_BINDING_REVIEW = PASS
D6_OWNER_DECISION = RECORDED
D6.MEDIA_VALIDATION_SOURCE = RESOLVED: EXACT_COMMITTED_IMAGE_ONLY_VALIDATOR
D6.MIME_EXTENSION_RULE = RESOLVED: REMOVE_REQUIREMENT
D11 = BLOCKED
STAGE_4 = NOT READY
LIVE/MODEL/GPU/PROVIDER/NETWORK/LIGHTNING = NOT AUTHORIZED
NEXT = PREPARE_D1_OWNER_RESOLUTION_AND_D6_FIXTURE_BINDING
```

### 12.7 CURRENT: D9 offline-implementation-and-correction reconciliation validation (2026-09-22)

This is a governance/documentation synchronization only. It reconciles
`CONTEXT.md`, `DECISIONS.md`, and this plan with the already-committed,
already-independently-reviewed D9 stdout/stderr enforcement correction at
commit `86836d24cfcd83ca14c0bc50e79fff1103cb9ecc`. It changes no
implementation, test, D2 dependency, security validator, runtime seam,
worktree, or stash, does not modify `approvals/TASK_APPROVAL.md`, and does
not create a Stage 4 approval.

Validation establishes:

- HEAD `86836d24cfcd83ca14c0bc50e79fff1103cb9ecc`, parent
  `552bc5d939f36b2b87dc7f0cea909110e8750107`, commit message exactly
  `fix(feat018): close D9 stream enforcement gaps`, containing exactly the
  two authorized files at blobs `e1c89536e612b9f801ff2e429e76f3f0d0c370ee`
  and `3a4db7fd56185da82749b95dd42ca1a3bdc13c0d` (independently re-verified
  by `git rev-parse` and `git diff-tree` in this reconciliation);
- the independent correction review
  (`tmp/feat018-p2t2-d9-independent-correction-review-20260922/REVIEW.md`)
  and the follow-up commit checkpoint
  (`tmp/feat018-p2t2-d9-followup-commit-checkpoint-20260922/REPORT.md`) both
  record verdict `PASS`;
- the diff is limited to `CONTEXT.md`, `DECISIONS.md`, this plan, and one new
  evidence note
  (`evidence/notes/P2_T2_D9_GOVERNANCE_RECONCILIATION_20260922.md`); the
  pre-existing D6 draft and the untracked D1 draft are byte-identical to
  their hashes before this reconciliation
  (`b80e4d4d5e565f575155c7e31787a4f6b4c0ddf2` and
  `9b42d46c9326f35e952816569d59df5274335993`);
- `P2T2-LIVE-D9` remains `NOT RESOLVED` and `D9_LIVE_D11_CARRIER_SCOPE`
  remains `UNKNOWN_UNRESOLVED_PENDING_D11`; `reviewed_runtime_code_commit`
  remains `9549a341194f40b1a9be419d6fce0d70f1ca0384`, unchanged and not
  rebound to `86836d2`;
- the first independent review of this reconciliation
  (`tmp/feat018-p2t2-d9-governance-reconciliation-independent-review-20260922/REVIEW.md`)
  returned `BLOCKED` with findings F-01..F-06, and the correction
  (`tmp/feat018-p2t2-d9-governance-reconciliation-correction-20260922/REPORT.md`)
  restored the pre-existing global `NEXT` in `CONTEXT.md`, kept Section
  12.6's still-open `NEXT` out of the satisfied list, separated the
  candidate-only raw-output/IPC ceilings from the owner-approved stdout/stderr
  ceilings, restored "Section 11 `CURRENT` is canonical.", restored "D9
  package correction" in the header, and corrected the Section 9
  cross-reference; and
- compared with the pre-reconciliation blobs, every pre-existing uncommitted
  addition in `CONTEXT.md`, `DECISIONS.md`, and this plan is preserved except
  three disclosed edits in this plan: the header's first line (date and new
  lead item; its prior items are retained), pointer correction #2 in
  update-history item 8, and a pure append to the Section 9 `P2T2-LIVE-D9`
  row.

```text
STATIC_VALIDATION = PASS
git diff --check = PASS
HARNESS_VALID
REPOSITORY_SECURITY_VALID (1031 publishable files scanned)
SKELETON_VALID
ARCHITECTURE_INVALID (sole finding: backend_ai_workflow.py, PRE_EXISTING_UNCHANGED, blob 2f339ab982d65ea490c20475baeeb122a57ba5ef at HEAD and worktree, empty diff)
Git index = empty
D9_OFFLINE_ENFORCEMENT_IMPLEMENTATION = IMPLEMENTED_CORRECTED_AND_INDEPENDENTLY_REVIEWED_PASS
D9_OFFLINE_IMPLEMENTATION_COMMIT = 86836d24cfcd83ca14c0bc50e79fff1103cb9ecc
D9 numeric ceilings (raw_output_max_bytes=65536, ipc_envelope_max_bytes=98304) = OWNER_SELECTED_CANDIDATE_ONLY
D9 stdout/stderr = OWNER-APPROVED EXACT VALUES (16384/32768), IMPLEMENTED OFFLINE; supersedes SEPARATE_ENFORCEMENT_APPROVAL_REQUIRED for stdout/stderr only
P2T2-LIVE-D9 = NOT RESOLVED
D9_LIVE_D11_CARRIER_SCOPE = UNKNOWN_UNRESOLVED_PENDING_D11
D11 = BLOCKED
D1 = BLOCKED_BY_D11
D6 = NOT FINALLY RESOLVED
STAGE_4 = NOT READY
LIVE/MODEL/GPU/PROVIDER/NETWORK/LIGHTNING = NOT AUTHORIZED
NEXT = PREPARE_D1_OWNER_RESOLUTION_AND_D6_FIXTURE_BINDING (global; Section 11 CURRENT; unchanged)
D9_RECONCILIATION_PACKAGE_GATE = FRESH_INDEPENDENT_D9_GOVERNANCE_RECONCILIATION_REREVIEW (package-local; does not replace, supersede, or satisfy NEXT)
```
