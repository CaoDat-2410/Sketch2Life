# FEAT-003 P2-T5 Evaluation Harness Plan

> **P2-T5 DRAFT — READY_FOR_PRE_G1_PLAN_CHECKPOINT_REVIEW**
> **OWNER DECISION BUNDLE V3: APPROVED** (2026-09-19; `approvals/TASK_APPROVAL.md` and
> `DECISIONS.md`, confirmed by `tmp/p2-t5-v3-owner-confirmation-20260919-r2/REPORT.md`)
> **P2-T5 IMPLEMENTATION: NOT APPROVED**
> **LIVE/RUNTIME/PROVIDER/MODEL/GPU/LIGHTNING/NETWORK: NOT APPROVED**

This is a preliminary planning document for the feature-qualified task **FEAT-003 P2-T5**.
It is not an implementation approval, a fixture-authoring approval, a model-selection decision,
or an evidence authorization.

## Document control and authority

| Field | Value |
|---|---|
| Feature/task | `FEAT-003 Multimodal understanding / P2-T5` |
| Current remediation revision | `0.15` |
| Document | `P2_T5_EVALUATION_HARNESS_PLAN.md` |
| Status | `P2-T5 DRAFT — READY_FOR_PRE_G1_PLAN_CHECKPOINT_REVIEW` |
| Preliminary revision | `0.15` — documentation-only V3 owner-bundle synchronization; content identity is not frozen until the future plan candidate checkpoint is created and G1 binds its exact tuple |
| Task owner | Person 2, as recorded in the proposed Sprint 1 allocation; that allocation does not authorize implementation |
| Expected planning base | `f11a6f4fee81032a677b492303cdecd9b09663d4` |
| Current P2-T4 state | `COMPLETE — GOVERNANCE-CLOSED`; G6 `PASS_WITH_FINDINGS`, G7 `PASS`, G8 `PASS`, G9 `COMPLETE` |
| Current P2-T5 state | `NOT APPROVED` |
| Current live/runtime state | `NOT APPROVED` |
| Tracked P2-T5 artifact state | `TRACKED P2-T5 FIXTURE/MEDIA/EVIDENCE ARTIFACTS: NOT CREATED` (ignored local review reports may exist under `tmp/`; they are not tracked P2-T5 artifacts) |

Authority for this plan is ordered as follows: the direct task instruction; the current
`features/FEAT-003-multimodal-understanding/approvals/TASK_APPROVAL.md`; accepted ADRs and
repository governance; the corrected, immutable P2-T4 freeze/package identities; the T1–T4
contracts and evidence; then planning proposals and implementation facts. A plan statement marked
**proposal**, **owner decision**, or **future** is not a decision and cannot authorize work.

The current P2-T4 G9 closeout is the sole current P2-T4 gate state. Earlier `PAUSED`, `HOLD`, or
pre-G9 wording in historical plan and approval sections remains history. It does not make P2-T5
approved. `HARNESS_VALID` is a structural validator result, not task approval.

The current P2-T5 position is `PRE-G1`; the owner approved the exact `OWNER DECISION BUNDLE V3`
on 2026-09-19 (`approvals/TASK_APPROVAL.md` and `DECISIONS.md`, "P2-T5 fixture-only v1 owner
decision bundle", confirmed by `tmp/p2-t5-v3-owner-confirmation-20260919-r2/REPORT.md`). The next
action is this documentation-only plan synchronization, followed by independent post-sync
technical and governance/privacy review and the immutable pre-G1 plan candidate checkpoint.
Any value outside the approved V3 bundle's scope that still requires owner selection remains
explicitly `OWNER DECISION REQUIRED`. `READY_FOR_PRE_G1_PLAN_CHECKPOINT_REVIEW` does not mean G1 is
granted, does not itself create the future plan candidate checkpoint, and grants no owner plan
approval, implementation approval, fixture/media/evidence authority, or runtime/live authority.

This document does not implement or edit any code, schema, test, fixture, runtime, adapter,
provider, model, GPU, Lightning, network, migration, approval, freeze artifact, or closeout
record.

## 1. Purpose and status

P2-T5 is proposed as a standalone, local, fixture-provider-only CLI and evaluation harness for
the FEAT-003 multimodal understanding workstream. It evaluates deterministic synthetic fixtures
or locally available, non-child licensed fixtures through the already-defined P2-T1, P2-T2,
P2-T3, and P2-T4 boundaries. Its primary deliverable is a versioned machine-readable report plus
a bounded human-readable summary.

The v1 evidentiary claim is deliberately narrow:

- the fixture loader, contract adapters, T1–T4 handoff, scorer, oracle comparison, report
  serializer, and privacy boundary behave as specified;
- typed success, invalid-input, recapture, rejection, and simulated-failure cases are accounted
  for without changing their upstream identities; and
- repeated offline runs are reproducible under an identical approved input/configuration identity.

P2-T5 v1 is not evidence of Whisper, Qwen, provider, model, semantic-safety, or real-child
drawing quality. It does not select a model, freeze a runtime default, produce a Gate A decision,
or establish a production capability.

P2-T5 is downstream of T1–T4. It consumes their versioned contracts and deterministic fixture
paths; it does not redefine their fields, statuses, retry behavior, policy, matching semantics,
canonicalization, or rejection identities. A P2-T5 report-layer contract is additive and must
never be substituted for an upstream contract.

## 2. Explicit scope and non-goals

### 2.1 In scope after separate approval

The future approved v1 scope is limited to:

1. A local CLI with the proposed `validate`, `understand --provider fixture`, and `evaluate`
   commands.
2. A new feature-local P2-T5 fixture package with an owner-approved manifest, split, hashes,
   hand-authored expected values, and synthetic/non-child provenance.
3. Deterministic use of the existing P2-T1 validator, P2-T2 fake ASR adapter, P2-T3 fake Vision
   adapter, and P2-T4 offline fusion boundary through their existing ports/contracts.
4. P2-T5 report, run, case-summary, measurement, and typed-harness-failure schemas, each with a
   versioned identity approved before implementation.
5. Independent oracle comparison and metric computation over new P2-T5 fixtures only.
6. Offline contract, privacy, import-boundary, deterministic-serialization, and command-behavior
   validation.

Fixture mode is the local deterministic baseline, run locally with the exact commands and exact
CPython 3.13.5 interpreter. Any other interpreter is NON_CANONICAL_ENVIRONMENT and cannot produce
canonical G6-G8 evidence. No P2-T5 CI job exists or is implied; CI enablement is out of scope.

### 2.2 Explicit non-goals and forbidden authority

P2-T5 v1 must not authorize or perform:

- live Whisper, Qwen, Lightning, Runpod, or any other provider/model execution;
- model loading, weight downloads, dependency installation, cache population, or provider SDK
  imports;
- GPU, CUDA, Lightning, cloud, network, public TTS, external service, or egress activity;
- mobile, UI, HTTP, session, job, queue, database, storage, backend-route, or Integration Sprint
  wiring;
- any change to FEAT-018, FEAT-020, B0 mapping/adoption, or another feature's contract or code;
- any mutation of P2-T1, P2-T2, P2-T3, or P2-T4 schemas, runtime mapping, fixtures, freeze
  artifacts, or evidence;
- any Vision V2-to-V1 projection or claim that a V2/Qwen result reached the P2-T4 V1 boundary;
- P2-T1 threshold/policy calibration, automatic recapture, modality fallback, or vision-only
  continuation after a required-input recapture/failure;
- semantic-paraphrase judging, embedding/fuzzy scoring, psychological inference, diagnostic,
  personality, developmental, trauma, or mental-state claims;
- re-execution, re-scoring, pooling, tuning against, or changed-rule comparison of existing ASR
  Round-1, Vision B4/v3, P2-T4, or live benchmark evidence;
- publication of raw provider/model output, raw exceptions, full prompts, credentials, secrets,
  endpoints, absolute paths, or unapproved child data.

An invalid-input, timeout, provider-failure, or fallback-shaped fixture may simulate an already
defined typed branch in memory. It must not wait, call a provider, load a model, or perform a live
timeout. For P2-T5, “fallback case” means an attempted continuation after a terminal T1/T2/T3/T4
condition is correctly blocked and recorded; it does not introduce a new fallback contract.

Any future live benchmark is a separate feature-qualified plan and separate approval sequence. It
must define its own capture/scoring boundary and new fixtures; it cannot be added as a provider
enum member or optional flag to this v1 plan. This plan does not implement, authorize, or satisfy
`FEAT018-P2-T5`.

## 3. Dependency and contract binding

### 3.1 Upstream contract table

| Boundary | Existing contract/fact | P2-T5 treatment |
|---|---|---|
| P2-T1 media admission | `MediaValidationResultV1@1.0`, with `decision=PASS` or `RECAPTURE`, ordered `recapture_reasons`, source references, hashes, signals, and validator provenance | Validate the manifest media through the existing deterministic validator. Only `PASS` may enter an ASR/Vision request. A `RECAPTURE` case is recorded by reason and downstream stages are `NOT_EXECUTED`; P2-T5 does not recalibrate or override T1. |
| P2-T2 ASR | `P2.AsrResultV1@1.0`, discriminated by `SUCCEEDED`/`FAILED`, with existing profile, attempt, repair, source, diagnostic, segment, and typed-error semantics | Use only the deterministic fake profile/path. Preserve `INPUT_NOT_VALIDATED`, `ASR_TIMEOUT`, `ASR_MODEL_UNAVAILABLE`, `ASR_PROVIDER_FAILURE`, and `ASR_SCHEMA_INVALID` exactly. A simulated branch is not live ASR. |
| P2-T3 Vision | `P2.VisionUnderstandingResultV1@1.0`, fake profile `FAKE_DETERMINISTIC_V1`, strict collections and policy provenance | Use only the existing deterministic fake. Preserve `VISION_MODEL_UNAVAILABLE`, `VISION_TIMEOUT`, `VISION_PROVIDER_FAILURE`, `VISION_SCHEMA_INVALID`, `PROHIBITED_CLAIM_DETECTED`, and `INPUT_NOT_VALIDATED` semantics. No Vision V2 or model provenance enters a V1 result. |
| P2-T4 input | Only `P2.AsrResultV1@1.0` and `P2.VisionUnderstandingResultV1@1.0` are accepted | Construct or obtain exact typed P2 V1 results in memory. Wrong-family, wrong-version, malformed, inadmissible, and correlation cases are sent through the existing T4 classification boundary and are not normalized by P2-T5. |
| P2-T4 output | `P2T4.P2T4FusedResultV1@1.0`, serialized as `P2T4FusedResultV1 / 1.0`, statuses `FUSED` or `UPSTREAM_FAILURE` | Record the exact result identity/status and canonical digest. Do not add fields, change status semantics, or convert rejection into `UPSTREAM_FAILURE`. |
| P2-T4 outer rejection | `P2T4.P2T4FusionInputRejectionV2@2.0`, `status=REJECTED`, with closed slot/phase/code/identity/status/field-code values | Record the exact V2 rejection identity and closed fields. It remains a separate terminal result and never enters the fused-result union. The superseded V1 rejection is not accepted. |
| P2-T5 report layer | No approved P2-T5 schema exists yet | The report/run/case/measurement/failure identities below are proposals. They must be approved before implementation and cannot replace any upstream model. |

### 3.2 T4 freeze, package, and G9 binding

The future implementation/evidence approval must bind the exact five-field artifact identities below;
the plan does not recompute or replace them:

| Artifact | Source commit | Corrected normalized SHA-256 | Raw-file SHA-256 | Git blob |
|---|---|---|---|---|
| Freeze revision 12: `plan/P2_T4_CONTRACT_FREEZE_REVISION_12.md` | `5b6501b2d8b809f9dd4caf77b5c5d51d2e1e9cf2` | `103695e5e1c49d9f9b1cc85fd5286f42980580f338578db799febdeedb310ee5` | `b9606292e00b1b956ec38e141eb27f868bad2835f8ea5e8d20693a18acd2fa20` | `1e7e487362efec02b3b5f3bbf9dd4c64eabaa0d9` |
| Package revision 16: `evidence/notes/P2_T4_IMPLEMENTATION_APPROVAL_PACKAGE_REVISION_16.md` | `5b6501b2d8b809f9dd4caf77b5c5d51d2e1e9cf2` | `75cd5d69e6896d7fae10d3771a90019003e0644fff1138161b7ac330e840b270` | `8ce46b5f762b27b556030d85666ccb6827a1fdbaeb56312dc8490d6e214a75ce` | `8784e84a537260668e81c6c889aadc8688086857` |

Current G9 topology is `implementation candidate 21249dc696c8ea3d958e78394ed69b8ac9f9505a`;
the evidence checkpoint is `c80c58fbd2b76d28af52156301caca87e7a794f5`. These are provenance facts,
not P2-T5 authority.

The exact frozen service/schema paths already exist and are read-only dependencies of this plan:

- `backend/src/sketch2life/application/services/p2_t4_fusion.py`
- `backend/src/sketch2life/contracts/schemas/p2_t4_fusion.py`
- `backend/tests/contract/test_p2_t4_contract.py`
- `backend/tests/unit/test_p2_t4_fusion.py`
- `features/FEAT-003-multimodal-understanding/fixtures/p2-t4-fusion-v1/manifest-v1.json`
- `features/FEAT-003-multimodal-understanding/fixtures/p2-t4-fusion-v1/cases-v1.json`
- `features/FEAT-003-multimodal-understanding/fixtures/p2-t4-fusion-v1/expected-v1.json`

P2-T5 must not modify or copy these files into a new authority. New P2-T5 fixtures are separate
and must bind to the T4 service through its public typed boundary.

### 3.3 Fixture-to-T4 data flow

The proposed offline flow is:

1. Load a P2-T5 manifest from a repository-relative path and verify its manifest hash, entry hash,
   split, synthetic/licensed provenance, and no-parent-traversal path rules.
2. Load the case's local media references and verify each byte hash before any adapter call. Build
   the existing `MediaFixtureManifestV1`/request shape without changing T1's contract.
3. Call the existing `DeterministicMediaValidator`. For `RECAPTURE`, emit the case summary with
   ordered reasons and `downstream_status=NOT_EXECUTED`; do not call ASR, Vision, or T4.
4. For `PASS`, construct `AsrRequestV1` and `VisionUnderstandingRequestV1` with the same stable
   correlation ID, source references, T1 validation provenance, and the approved fake profile IDs.
   The requests are validated before either port is invoked.
5. Invoke only the existing `AsrPort` and `VisionUnderstandingPort` implementations backed by
   deterministic fixture adapters. Their full typed results remain in memory for validation and
   hashing; persisted case summaries use closed identities/statuses/codes and digests only.
6. Pass the exact P2 V1 result objects to `validate_and_fuse(asr, vision, policy, executed_at)`.
   The injected `executed_at` is timezone-aware and supplied by the CLI; no wall clock is read by
   the harness. T4's existing terminal precedence remains identity/version, strict validation,
   admissibility, correlation, typed status, then fusion; ASR is checked before Vision.
7. Persist only the P2-T5 report-layer summary and canonical hashes. Never serialize a second T4
   shape, a V2 result, raw provider/model text, exception text, or a rejected input object.

#### Fixture-only adversarial T4 composition seam

The fixture descriptor does not attempt to make a raw fake-adapter payload invalid. After the
existing deterministic fake adapter has returned a complete typed P2 V1 result, a fixture-only
composition seam may construct one in-memory adversarial input before the call to
validate_and_fuse. This seam is infrastructure/test composition, not a provider adapter and not a
new T4 contract. The typed result is revalidated before it crosses the T4 public boundary.
The existing fake Vision adapter overwrites policy_match_view_version with its policy token before
validating a success, so a raw fixture payload alone cannot produce this success-only
noncanonical case; only this post-adapter in-memory seam can do so.

The only proposed P2-T5 mutation categories are:

| Mutation category | In-memory operation and exact typed field | T4/oracle boundary |
|---|---|---|
| NONE | Pass the fake-adapter AsrResultV1 and VisionUnderstandingResultV1 objects unchanged. | Normal T4 result oracle. |
| WRONG_FAMILY_ASR | Replace only the ASR slot with an in-memory typed FEAT018.LiveAsrResultV1@1.0 object whose status is SUCCEEDED; do not serialize it. | T4 must emit P2T4FusionInputRejectionV2@2.0, ASR / IDENTITY_VERSION / WRONG_FAMILY, field UPSTREAM_TYPE. |
| DUPLICATE_ASR_SEGMENT_INDEX | Rebuild a typed P2.AsrResultV1@1.0 success with two segments[*].index values equal, while leaving Vision unchanged. | T4 must emit ASR / ADMISSIBILITY / INVALID_STRUCTURE, field DUPLICATE_SEGMENT_INDEX. |
| NONCANONICAL_VISION_MATCH_VIEW | Rebuild a typed P2.VisionUnderstandingResultV1@1.0 success with only policy_match_view_version resolved from the private test-only SYNTHETIC_NONCANONICAL_SENTINEL category; the value must differ byte-for-byte from the upstream VISION_POLICY_MATCH_VIEW_VERSION constant. | T4 must emit VISION / ADMISSIBILITY / INVALID_STRUCTURE, field POLICY_MATCH_VIEW_VERSION, with observed status SUCCEEDED. |
| CORRELATION_MISMATCH | Rebuild one otherwise valid typed result with a distinct non-empty correlation_id; keep the other result's correlation ID unchanged. | T4 must emit the existing BOTH / CORRELATION / CORRELATION_MISMATCH oracle form, field CORRELATION_ID. |

The case JSON stores only the closed mutation category. The actual wrong-family object, duplicate
index, correlation value, and noncanonical match-view value exist only in memory at this seam.
The noncanonical value is never stored in a fixture, expected oracle, case summary, canonical
digest, exception, log, evidence artifact, or report. The oracle stores only the closed T4
identity/status/slot/phase/code/field values and the resulting T4 canonical digest. A mutation
does not invoke a provider, load a model, wait for a timeout, or alter the fake-adapter output
contract.

The exact serialized T4 policy projection for P2-T5 is the following indivisible candidate. The
owner approved this exact projection as part of `P2T5.OwnerDecisionBundleV3@1.0` (`DECISIONS.md`,
2026-09-19); the approval does not permit silently selecting a different policy value. These
exact bytes and this exact hash are the only policy binding used for every P2-T5 T4 call:

| Field | Approved value (`OWNER_APPROVED_V3_20260919`) |
|---|---|
| `contract_name` | `P2T4FusionPolicyConfigV1` |
| `contract_version` | `1.0` |
| `config_version` | `p2-t4-fusion-policy-fixture-v1` |
| `entity_match_mode` | `WHOLE_TOKEN_SEQUENCE` |
| `narration_weight_mode` | `SUPPORT_ONLY` |
| `confidence_floor` | `0.5` (finite; compare the original base confidence only) |
| `uncertainty_formula_id` | `AGREEMENT_WEIGHTED_V1` |
| `match_view_version` | `vision_policy_match_view-v2` (recipe identity, not the upstream admissibility token) |
| `negation_cues` | `[["not"], ["no"], ["never"], ["isn", "t"], ["doesn", "t"], ["didn", "t"]]` |
| `negation_window_tokens` | `3` |
| `corroboration_increment` | `"0.10"` (decimal string retained exactly) |

The policy identity is `P2T4FusionPolicyConfigV1@1.0`; its serialized identity fields are the
P2T4FusionPolicyConfigV1 contract name and version 1.0. The canonicalization identity is
`P2T4-CANONICAL-JSON-V1`: UTF-8 bytes, `ensure_ascii=false`, `sort_keys=true`, compact
comma-colon separators, `allow_nan=false`, no trailing newline, and the hash field excluded from
the projection. The projection source is
`backend/src/sketch2life/contracts/schemas/p2_t4_fusion.py`, `P2T4FusionPolicyConfigV1`; the
immutable freeze/package bindings in section 3.2 remain the governing upstream provenance. The
exact no-newline canonical UTF-8 bytes are:

```json
{"confidence_floor":0.5,"config_version":"p2-t4-fusion-policy-fixture-v1","contract_name":"P2T4FusionPolicyConfigV1","contract_version":"1.0","corroboration_increment":"0.10","entity_match_mode":"WHOLE_TOKEN_SEQUENCE","match_view_version":"vision_policy_match_view-v2","narration_weight_mode":"SUPPORT_ONLY","negation_cues":[["not"],["no"],["never"],["isn","t"],["doesn","t"],["didn","t"]],"negation_window_tokens":3,"uncertainty_formula_id":"AGREEMENT_WEIGHTED_V1"}
```

That exact canonical payload is exactly 466 UTF-8 bytes and has proposed
`fusion_policy_config_hash`
`4b378f69a33b86aeefc7443a23ac819e46b986132525cdd8a55d112dfb96415c`. This is a recorded
candidate binding, not P2-T5 approval. The token-array negation cues and decimal-string
corroboration increment shown above are byte-significant; numeric coercion or a flattened cue list
is a mismatch. Before T4 is called, the harness must canonicalize the selected policy projection
and compare the resulting identity, version, exact canonical bytes, byte count, and SHA-256 with
this bound value. A missing policy, missing hash, canonicalization error, byte-domain mismatch, or
hash mismatch is the terminal P2-T5 failure `T4_POLICY_INTEGRITY_FAILURE` at the T4 precondition
boundary, with exactly one of the closed reasons
`MISSING_POLICY_HASH | MISMATCHED_POLICY_HASH | POLICY_CANONICALIZATION_ERROR |
POLICY_BYTE_DOMAIN_MISMATCH`; it
terminates the case before T4 and produces no T4 output. No fallback, default policy, T4 result,
rejection, metric, or report case may be emitted under a missing, mismatched, or unbound policy.
If the owner rejects or changes this instance, the entire projection, identity/version, byte count,
and hash must be replaced as one explicitly approved proposal before implementation; the table
above cannot be partially inherited.

### 3.4 Existing implementation facts used for placement

The current repository layout was inspected before this proposal:

- T1 service/schema: `backend/src/sketch2life/application/services/media_validation.py` and
  `backend/src/sketch2life/contracts/schemas/media_validation.py`.
- T2 port/fake: `backend/src/sketch2life/application/ports/asr.py` and
  `backend/src/sketch2life/infrastructure/ai/fake_asr.py`.
- T3 port/fake: `backend/src/sketch2life/application/ports/vision_understanding.py` and
  `backend/src/sketch2life/infrastructure/ai/fake_vision.py`.
- A separate generic fixture adapter exists at
  `backend/src/sketch2life/infrastructure/understanding/fixture_adapters.py`; it serves the
  generic `understanding`/FEAT-018-shaped contracts and is not silently substituted for P2 V1.
- The existing `backend/src/sketch2life/interfaces/cli/workflow_demo.py` is a FEAT-020 live
  workflow entrypoint that imports real ASR/Vision/runtime configuration. P2-T5 must not edit,
  call, or use it as its CLI composition root.
- There is currently no P2-T5 CLI module, report schema, P2-T5 fixture directory, or Python lock
  file in the repository.

### 3.5 Correlation and terminal-stage semantics (`OWNER_APPROVED_V3_20260919`)

The owner did not design correlation in this plan; the owner approved the exact correlation
semantics below as part of `P2T5.OwnerDecisionBundleV3@1.0` (`DECISIONS.md`, 2026-09-19). The
identity, metadata fields, canonicalization, SHA-derived ID, and T2/T3/T4 propagation are the
recorded decision below.

The proposed correlation identity is `P2T5.CorrelationIdV1@1.0`. For every manifest
entry, the harness constructs exactly this metadata object before T2 or T3 execution:

```json
{
  "feature_task": "FEAT003-P2T5",
  "manifest_id": "<owner-approved-manifest-id>",
  "manifest_version": "<owner-approved-manifest-version>",
  "fixture_id": "<lowercase-fixture-id>",
  "split": "DEVELOPMENT|HELD_OUT"
}
```

The proposed value is
`p2t5-corr-<sha256-of-canonical-utf8-metadata>`, where the metadata object is serialized with
`ensure_ascii=false`, `sort_keys=true`, `separators=(",", ":")`, and `allow_nan=false`. This
source is manifest identity/version, fixture ID, split, and the fixed feature/task token only. It
never uses an absolute path, media bytes or media digest, timestamp, hostname, username, process
ID, random value, filesystem order, or runtime completion order. The exact resulting string is
passed unchanged to the T2 ASR request, T3 Vision request, and T4 input/result; the case summary
must assert equality across all three values. T1 records the same proposed value in the P2-T5
case envelope but the existing T1 contract is not changed to consume a new field.

The proposed run, case, recapture, and retry semantics are described below. The owner must approve
or reject these exact proposed semantics; this plan does not silently record an owner decision.
`run_id` is a required caller-supplied lowercase token matching `[a-z0-9][a-z0-9-]{0,63}`. It
identifies the logical selected-split evaluation, must remain stable for a deterministic rerun, and
is never generated from random state, a UUID, wall clock, timestamp, hostname, username, process
ID, filesystem order, or completion order. For the same manifest, case, selected split, and
configuration, a deterministic rerun may reuse the same `run_id`; a separately retained duplicate
execution must use a new explicit caller-supplied `run_id`. `run_id` is part of the deterministic
core and participates in `deterministic_core_sha256`. A deterministic rerun also reuses the same
manifest/case bytes, policy/profile identities, and exact `executed_at` input. `fixture_id` is the case identity: exactly one case row is emitted per selected
manifest entry per run, with no case retry row, duplicate, or completion-order meaning. The selected
split is one of `DEVELOPMENT` or `HELD_OUT`; a run with an empty selection is a preflight failure.

The proposed harness performs no outer retry. A retry of the same manifest/case/split reuses the
same deterministic `correlation_id`; it does not create a second case row. A duplicate execution
uses a distinct explicit `run_id` while retaining the same deterministic `correlation_id` when
manifest, case, and split are unchanged. `attempt_number`, `repair_attempted`, and `retryable` are copied
from the exact fake-adapter typed result and describe that adapter's bounded internal behavior; they
are not instructions for the harness. Under the selected `FAKE_DETERMINISTIC_V1` ASR profile,
`TIMEOUT` is attempt 1 and non-retryable; `PROVIDER_TRANSIENT_FAILURE` is the adapter's exact
attempt-2 retryable result; and all selected model/permanent failures are attempt 1 and
non-retryable. Vision uses its selected fake profile's exact attempt/retry fields and never gets an
outer retry. A typed failure therefore completes the invoked stage with its typed result and proceeds
to the existing T4 typed-failure boundary; an exception or missing result is `PARTIAL` or `FAILED`
according to the stage table and never produces a successful deterministic report.

For T1 `RECAPTURE`, T1 executes once, its existing `PASS | RECAPTURE` decision and ordered reasons
are preserved, ASR/Vision/T4 are not invoked, and the harness does not retry media or reinterpret
recapture as a typed downstream failure. For a T4 rejection, both upstream results and their shared
correlation value are already complete; the rejection is one expected terminal case outcome, not a
retry request. The proposed repeat command is a new observation governed by the run-id rule above,
never an additional attempt inside the original case. A recapture is terminal for the current run;
a later rerun uses a new `run_id` and retains the same `correlation_id` when manifest, case, and
split are unchanged. A typed upstream modality failure preserves its typed completed-with-failures
status; unavailable quality metrics are `NOT_MEASURED`. This proposal requires owner approval before
implementation.

The proposed closed stage and case accounting is:

StageExecutionState is exactly NOT_EXECUTED | EXECUTED | PARTIAL | FAILED. NOT_EXECUTED means the
stage was not entered, including a downstream stage blocked by an earlier terminal result.
EXECUTED means the stage boundary was entered and emitted its complete typed result or decision;
a typed ASR/Vision failure and a T4 rejection are still EXECUTED. PARTIAL means a stage was
entered but interruption, unexpected exception, or missing output prevented a complete typed
result. FAILED means a deterministic stage or harness precondition failed without its normal
typed result; it is not used for an ordinary typed ASR/Vision failure.

CaseRunStatus is exactly COMPLETED | COMPLETED_WITH_TYPED_FAILURES | EXPECTED_TERMINAL | SKIPPED |
PARTIAL | FAILED. case_status and run_status use this same closed vocabulary. The T1 contract
decision remains its existing independent two-value enum PASS | RECAPTURE; it is never encoded as
a stage state and EXPECTED_TERMINAL_FAILURE is not a permitted token.

| Condition | T1 stage state | T2 ASR stage state | T3 Vision stage state | T4 stage state | Case status and exact accounting |
|---|---|---|---|---|---|
| Manifest/path/media-reference/case/oracle preflight failure before T1 | NOT_EXECUTED | NOT_EXECUTED | NOT_EXECUTED | NOT_EXECUTED | FAILED; emit only the closed harness failure identity; no publishable case result |
| T1 validator or media-precondition failure after case entry, without a T1 decision | FAILED | NOT_EXECUTED | NOT_EXECUTED | NOT_EXECUTED | FAILED; no downstream call or partial report |
| T1 RECAPTURE with ordered existing reasons | EXECUTED | NOT_EXECUTED | NOT_EXECUTED | NOT_EXECUTED | EXPECTED_TERMINAL; preserve the T1 decision/reasons and record downstream states explicitly |
| T1 PASS, both invoked adapters return complete typed results, and T4 fuses | EXECUTED | EXECUTED | EXECUTED | EXECUTED | COMPLETED; T4 result status is FUSED |
| T1 PASS, one or both invoked adapters return typed failures, and T4 returns a typed result | EXECUTED | EXECUTED with success or exact typed failure | EXECUTED with success or exact typed failure | EXECUTED | COMPLETED_WITH_TYPED_FAILURES; T4 result status is UPSTREAM_FAILURE, counted by modality and code |
| T4 outer rejection after complete T1/T2/T3 results | EXECUTED | EXECUTED | EXECUTED | EXECUTED with P2T4FusionInputRejectionV2@2.0 | EXPECTED_TERMINAL; count exact identity/slot/phase/code/field values and never coerce to FUSED |
| Deterministic T4 policy-integrity failure before the T4 call | EXECUTED | EXECUTED | EXECUTED | NOT_EXECUTED | FAILED; emit the closed policy-integrity failure only and no T4 output |
| Unexpected exception, interruption, or missing result after a stage is entered | completed earlier stages | PARTIAL if ASR was entered without a result, otherwise NOT_EXECUTED | PARTIAL if Vision was entered without a result, otherwise NOT_EXECUTED | PARTIAL if T4 was entered without a result, otherwise NOT_EXECUTED | PARTIAL; no successful report and no fabricated stage result |
| Declared split exclusion before execution | NOT_EXECUTED | NOT_EXECUTED | NOT_EXECUTED | NOT_EXECUTED | SKIPPED; allowed only for an explicitly excluded split, never for a T1 recapture |

For a run summary, FAILED has precedence over PARTIAL, which has precedence over
COMPLETED_WITH_TYPED_FAILURES. SKIPPED is used only when every selected case is a declared
split exclusion; EXPECTED_TERMINAL is used when every non-skipped case is terminal for an
expected T1/T4 reason; otherwise a fully resolved mix of COMPLETED and expected terminals is
COMPLETED. A run with at least one typed UPSTREAM_FAILURE and no failed or partial case is
COMPLETED_WITH_TYPED_FAILURES. This makes every stage state and every case/run status
deterministic and prevents partial or failed execution from publishing a completed evaluation.

The shorthand unexpected row above expands to these exact stage tuples; no other partial mapping is
permitted:

| Unexpected point | T1 | ASR | Vision | T4 | Case status |
|---|---|---|---|---|---|
| Exception or missing decision while T1 is entered | `FAILED` | `NOT_EXECUTED` | `NOT_EXECUTED` | `NOT_EXECUTED` | `FAILED` |
| ASR entered without a complete typed result | `EXECUTED` | `PARTIAL` | `NOT_EXECUTED` | `NOT_EXECUTED` | `PARTIAL` |
| Vision entered without a complete typed result after ASR completed | `EXECUTED` | `EXECUTED` | `PARTIAL` | `NOT_EXECUTED` | `PARTIAL` |
| T4 entered without a complete fused/rejection result after both upstream stages completed | `EXECUTED` | `EXECUTED` | `EXECUTED` | `PARTIAL` | `PARTIAL` |

If a stage is never entered in one of the last three rows, its state is `NOT_EXECUTED`; if an
earlier stage has already emitted a typed failure, that earlier stage remains `EXECUTED`. No
unexpected exception is serialized beyond the closed P2T5 failure identity and stage tuple.

## 4. CLI contract — proposed values pending owner approval

The command names below are proposals. The logical commands are fixed for planning purposes, while
the packaging/installation name remains an owner decision.

### 4.1 Invocation grammar

The canonical local verification form is proposed as a module invocation so it does not require a
new package installer entrypoint:

```text
python -m sketch2life.interfaces.cli.p2_t5_evaluation validate \
  --manifest <repo-relative-json> --fixture-root <repo-relative-dir> \
  --output <repo-relative-json>

python -m sketch2life.interfaces.cli.p2_t5_evaluation understand \
  --provider fixture --manifest <repo-relative-json> --fixture-root <repo-relative-dir> \
  --fixture-id <lowercase-feature-qualified-id> --output <repo-relative-json>

python -m sketch2life.interfaces.cli.p2_t5_evaluation evaluate \
  --provider fixture --manifest <repo-relative-json> --fixture-root <repo-relative-dir> \
  --split DEVELOPMENT|HELD_OUT --run-id <lowercase-run-id> \
  --executed-at <RFC3339-UTC> --run-dir <repo-relative-dir> \
  --output <repo-relative-json>
```

The `p2t5 validate`, `p2t5 understand --provider fixture`, and `p2t5 evaluate` forms are
illustrative aliases only. They may be packaged only after a separate owner approval of the
packaging path; the alias must invoke the canonical module and cannot introduce a second behavior.

### 4.2 Common input rules

- `--manifest`, `--fixture-root`, `--run-dir`, and `--output` are repository-relative POSIX paths.
  Drive-letter, rooted, UNC, home-directory, `..`, NUL, unresolved environment-variable, and
  symlink-escape forms are rejected before fixture loading.
- The manifest must validate as the owner-approved `P2T5.P2T5FixtureManifestV1@1.0`; its raw bytes,
  referenced case bytes, expected/oracle bytes, and all media bytes must match declared SHA-256
  values.
- `--provider` is a required closed value with the only member `fixture`. Any other value, an
  omitted value, a model name, an endpoint, a URL, or an environment-based provider selection is
  rejected before importing an adapter or model/provider module.
- `--run-id` is a caller-supplied lowercase token matching `[a-z0-9][a-z0-9-]{0,63}`. It is never a
  random UUID, an uppercase identifier, or a timestamp-derived default. `--executed-at` is required for `evaluate`, is
  timezone-aware RFC3339 UTC, and is passed to T4; it is never read from the wall clock.
- The output path is written atomically only after the complete output validates. A failed command
  does not leave a plausible partial report at the requested path.

### 4.3 `validate`

`validate` checks manifest shape, split/ID uniqueness, path safety, byte hashes, data-policy
declarations, expected/oracle references, and the P2-T1 input contract. It does not call ASR,
Vision, T4, a provider, a model, or a network. Its output is a `P2T5.P2T5CommandEnvelopeV1@1.0`
  containing a `P2T5.P2T5ValidationSummaryV1@1.0` payload with counts and per-case T1 decision/reason
summaries; it never embeds media bytes or raw labels in the command output.

An empty manifest, an empty requested split, duplicate IDs, a hash mismatch, invalid path, or
invalid expected identity is a command/input error. A valid `PASS` or `RECAPTURE` is a successful
validation result, including a recapture case.

### 4.4 `understand --provider fixture`

`understand` executes one named local fixture through the deterministic T1→fake ASR/fake Vision→T4
path described in section 3.3. It returns a `P2T5.P2T5CommandEnvelopeV1@1.0` whose payload is a
`P2T5.P2T5FixtureCaseResultV1@1.0` summary. The summary contains upstream identities, status, typed
failure/rejection fields, source/result/policy hashes, stage-execution flags, and metric eligibility
flags. It does not persist `transcript_raw`, raw Vision text, raw adapter payloads, exception
messages, prompts, or media.

An expected fixture `RECAPTURE`, typed ASR/Vision failure, T4 `UPSTREAM_FAILURE`, or exact T4
rejection is a valid case result and returns process success when the case is declared for that
outcome. An undeclared outcome, wrong oracle hash, unsupported fixture scenario, or contract
identity mismatch is a harness failure and uses the exit-code table below.

### 4.5 `evaluate`

`evaluate` selects exactly one approved split, runs every entry in stable manifest order, compares
each redacted case summary to the independent expected oracle, and writes one
`P2T5.P2T5EvaluationReportV1@1.0`. Expected invalid/recapture/failure/rejection cases do not abort the
split; they are counted with their exact typed outcome. An unexpected harness exception aborts the
run and produces only a sanitized failure envelope, not a partial publishable report.

The output file is canonical machine-readable JSON. Standard output contains one bounded line of
the form `P2T5_STATUS <status> <exit_code>`; standard error may contain the same closed failure
code. Neither stream contains absolute paths, raw media, full transcripts, raw Vision/model text,
prompts, credentials, endpoints, stack traces, or arbitrary exception strings.

### 4.6 Proposed deterministic exit codes and typed failures

| Exit | Closed category | Meaning |
|---:|---|---|
| `0` | `SUCCESS` | Valid command/report produced, including declared expected case failures, recaptures, T4 rejections, and metric mismatches recorded in the report. |
| `2` | `INVALID_ARGUMENT` | CLI syntax, missing argument, invalid relative path, empty split, manifest schema, or manifest-selection error. |
| `3` | `UNSUPPORTED_PROVIDER` | Any provider/mode other than the literal `fixture`, or any attempted live/model/runtime selection. Rejection occurs before live imports. |
| `4` | `CONTRACT_OR_ORACLE_REJECTED` | An unlisted identity/version/status, hash mismatch, oracle mismatch, unsupported case, or privacy/path sentinel prevents a valid evaluation. |
| `5` | `REPORT_WRITE_FAILED` | Canonical serialization or atomic output write failed. |
| `6` | `UNEXPECTED_HARNESS_ERROR` | Unexpected internal error; no raw exception detail is emitted. |

The proposed `P2T5.P2T5FailureV1@1.0` has only `code`, `phase`, `case_id` (nullable), and a closed
`reason_code`; it has no free-form exception, input object, local path, raw payload, or stack trace.
Its closed reason catalog includes `MISSING_POLICY_HASH`, `MISMATCHED_POLICY_HASH`,
`ORACLE_HASH_MISMATCH`, `MANIFEST_HASH_MISMATCH`, `PRIVACY_SENTINEL`,
`UNEXPECTED_HARNESS_ERROR`, and the approved stage-specific typed-failure tokens. A policy
integrity failure uses `code=T4_POLICY_INTEGRITY_FAILURE` and is terminal before T4.
Upstream error codes remain inside the redacted case summary as their existing T1/T2/T3/T4 typed
values. A P2-T5 failure code must never replace `P2T4FusionInputRejectionV2@2.0`.

## 5. Report contract — proposal, not frozen

### 5.1 Proposed report-layer identities

The following identities are a minimum proposal and require owner approval before implementation:

- `P2T5.P2T5FixtureManifestV1@1.0`
- `P2T5.P2T5RunRecordV1@1.0`
- `P2T5.P2T5ValidationSummaryV1@1.0`
- `P2T5.P2T5FixtureCaseResultV1@1.0`
- `P2T5.P2T5MeasurementV1@1.0`
- `P2T5.P2T5FailureV1@1.0`
- `P2T5.P2T5CommandEnvelopeV1@1.0`
- `P2T5.CorrelationIdV1@1.0`
- `P2T5.ASRMetricRuleV1@1.0`
- `P2T5.ConflictMatchingRuleV1@1.0`
- `P2T5.P2T5EvaluationReportV1@1.0`
- proposed report canonicalization identity `P2T5-REPORT-CANONICAL-JSON-V1`

These are report-layer objects. For every P2-T5 contract, the fully qualified identity is exactly
`P2T5.<ContractName>@1.0`; the serialized envelope is exactly
`contract_name=<ContractName>` and `contract_version="1.0"`. The namespace and `@1.0` suffix are
binding metadata, not part of the serialized `contract_name`. For example,
`P2T5.P2T5EvaluationReportV1@1.0` serializes as
`contract_name="P2T5EvaluationReportV1"` and `contract_version="1.0"`. A producer or consumer
must reject a namespace in `contract_name`, a mismatched version, or a fully qualified identity
that does not match these two serialized fields. T1–T4 contract names and versions remain the
upstream values in section 3; no P2-T5 schema may alias them.

The owner decision bundle must enumerate this complete eleven-identity P2-T5 contract set before
G1. The eleven contract identities are `P2T5.P2T5FixtureManifestV1@1.0`,
`P2T5.P2T5RunRecordV1@1.0`, `P2T5.P2T5ValidationSummaryV1@1.0`,
`P2T5.P2T5FixtureCaseResultV1@1.0`, `P2T5.P2T5MeasurementV1@1.0`,
`P2T5.P2T5FailureV1@1.0`, `P2T5.P2T5CommandEnvelopeV1@1.0`,
`P2T5.CorrelationIdV1@1.0`, `P2T5.ASRMetricRuleV1@1.0`,
`P2T5.ConflictMatchingRuleV1@1.0`, and `P2T5.P2T5EvaluationReportV1@1.0`.
`P2T5-REPORT-CANONICAL-JSON-V1` is an algorithm identity, not a twelfth contract identity.

### 5.2 Manifest and run fields

The proposed `P2T5.P2T5FixtureManifestV1@1.0` contains:

| Field | Proposed semantics |
|---|---|
| `contract_name`, `contract_version` | Exact P2-T5 manifest identity/version. |
| `manifest_id`, `manifest_version` | Stable feature-qualified package identity; a changed byte creates a new version. |
| `data_policy` | `SYNTHETIC_ONLY` for the initial recommendation; a future `LICENSED_NON_CHILD_ONLY` value requires owner decision and local license provenance. |
| `matching_rule_id`, `matching_rule_sha256` | Exact content identity of the approved entity/action/relation/theme matching rule. |
| `oracle_ref`, `oracle_sha256` | Repository-relative reference and raw SHA-256 of the hand-authored expected artifact. |
| `entries` | Stable IDs, split, relative media refs/hashes, expected T1/T2/T3/T4 outcome classes, ground-truth ref, case hash, and coverage tags. |
| `authoring` | Role owner, independent reviewer role, authoring method, source/license declaration, and review state; no personal data. |

`oracle_sha256` is a required future manifest field, not a PRE-G1 owner-bundle value. The owner
freezes the identity/version and immutability policy now; the raw hash and Git blob are populated
only after the approved `expected-v1.json` bytes exist and are independently reviewed.

Canonical machine IDs use lowercase because current upstream fixture contracts require lowercase
identifier patterns. The proposed 20 IDs are:

- development: `feat003-p2t5-dev-001` through `feat003-p2t5-dev-012`;
- held-out: `feat003-p2t5-heldout-001` through `feat003-p2t5-heldout-008`.

All fixture IDs in this plan and the parent summary use the exact lowercase forms above. An
uppercase `FEAT003-P2T5` label, when used for a feature/task reference, is not a fixture ID and
must not be serialized as one. This plan does not create the manifest.

The composition count invariant is auditable without running the harness:
`|entries| = 20`, `|DEVELOPMENT| = 12`, `|HELD_OUT| = 8`, `12 + 8 = 20`, and each entry has
exactly one image and one audio reference, so `|media paths| = 2 * 20 = 40`. The manifest ID set,
case ID set, expected-oracle ID set, and ID-matched media stem set must each be equal to the exact
20-ID set above; each set must be unique, and the four package files must contain no unreferenced
entry or media. These are validation invariants, not estimates and not permission to create files.

The proposed `P2T5.P2T5RunRecordV1@1.0` contains only stable run identity and sanitized provenance:
`run_id`, `manifest_id/version/hash`, `oracle_sha256`, `matching_rule_id/hash`, selected split,
selected upstream contract identities, fake profile IDs/config hashes, the owner-approved T4
policy identity/hash, `executed_at`, implementation-plan identity, implementation commit, and
environment/dependency identity fields. It contains no host root, username, hostname, environment
values, provider endpoint, secret, raw payload, or model output.

### 5.3 Case summary and report fields

The proposed `P2T5.P2T5FixtureCaseResultV1@1.0` contains:

- `contract_name`, `contract_version`, `fixture_id`, `split`, and `case_status`;
- stage_state objects for `t1`, `asr`, `vision`, and `fusion`, each using exactly
  `NOT_EXECUTED`, `EXECUTED`, `PARTIAL`, or `FAILED`; T1 `PASS | RECAPTURE` remains a separate
  decision field and no `EXPECTED_TERMINAL_FAILURE` value is valid;
- exact upstream identity/version and status for each produced result;
- typed T1 reason codes, T2/T3 failure codes/details, or exact T4 rejection fields where present;
- source/result/policy/canonical hashes and metric eligibility flags;
- no nested raw T1 media, ASR transcript, Vision text, provider response, exception, or input
  object.

The proposed `P2T5.P2T5EvaluationReportV1@1.0` contains these required top-level fields:

```text
contract_name
contract_version
deterministic_core
deterministic_core_sha256
volatile_run_metadata
```

`deterministic_core` contains `mode`, `run`, `manifest`, `fixture_split`, `upstream_contracts`,
`profile_and_policy_identities`, `case_results`, `measurements`, `typed_failure_summary`,
`interpretation_id`, and `limitations_id`. `manifest` contains IDs/version/raw hashes only;
`run.environment_identity` contains the sanitized interpreter, dependency, plan, and
implementation identities; `case_results` are sorted by stable `fixture_id`;
`typed_failure_summary` is a closed count map; and the interpretation/limitation identifiers
select bounded, predefined text rather than arbitrary model/provider content.

The report must separate stable content from volatile observations. The exact projection,
serialization, digest fields, and exclusion rules are defined in section 5.5 below and are owner-
approved (`OWNER_APPROVED_V3_20260919`); recording the decision is not implementation authority.

### 5.4 Measurement state

The proposed `P2T5.P2T5MeasurementV1@1.0` is:

```text
metric_id
status = MEASURED | NOT_MEASURED | NOT_APPLICABLE
value = decimal-string-at-six-places | null
numerator = integer | null
denominator = integer | null
unit
reason_code = closed token | null
eligibility_rule_id
```

Rules:

- `MEASURED` requires a non-null value and a valid denominator; zero is a valid measured value
  when the metric's formula produces zero.
- `NOT_MEASURED` requires `value=null` and a closed reason such as `NO_ELIGIBLE_CASES`,
  `OWNER_FORMULA_PENDING`, `INPUT_FAILURES_EXCLUDED`, or `POLICY_INSTANCE_UNFROZEN`.
- `NOT_APPLICABLE` is reserved for a deliberately out-of-population metric. For fixture-only v1,
  the proposed latency disposition is the closed token `NOT_APPLICABLE` with reason
  `FIXTURE_ONLY_LATENCY_DISABLED`; it is not a synonym for missing data.
- A missing measurement, free-form reason, status/value mismatch, or fabricated zero for an
  unavailable metric is invalid.

The v1 vocabulary is `MEASURED | NOT_MEASURED | NOT_APPLICABLE`; the owner approved this exact
vocabulary as part of `P2T5.OwnerDecisionBundleV3@1.0` (`DECISIONS.md`, 2026-09-19). The shape does
not silently reuse `AsrBenchmarkMeasurementV1`, and the closed reason catalog is the one named in
this plan. A future change requires a new owner decision and plan revision.

### 5.5 Canonical report and hash contract (`OWNER_APPROVED_V3_20260919`)

This section is the complete P2-T5 report identity and canonicalization rule. It is the owner-
approved decision recorded in `DECISIONS.md` (2026-09-19); recording it here is not implementation
authority or a frozen plan-checkpoint identity.

The report identity is `P2T5.P2T5EvaluationReportV1@1.0`. The serialized envelope must
carry `contract_name = "P2T5EvaluationReportV1"` and
`contract_version = "1.0"`; the `@1.0` form is the fully qualified identity used in bindings.
The envelope has exactly two conceptual regions:

1. `deterministic_core`, which is the only region hashed for
   `deterministic_core_sha256`; and
2. `volatile_run_metadata`, which is excluded from that hash and from all rerun-parity claims.

The complete report envelope contains exactly the five fields shown in section 5.3. The
`contract_name` and `contract_version` envelope values must equal the corresponding values inside
the core; they are duplicated so a consumer can reject the envelope before reading the core. The
deterministic-core projection contains only these stable paths, with no undeclared extras:

```text
deterministic_core.contract_name
deterministic_core.contract_version
deterministic_core.mode
deterministic_core.run.run_id
deterministic_core.run.executed_at
deterministic_core.run.manifest_id
deterministic_core.run.manifest_version
deterministic_core.run.manifest_sha256
deterministic_core.run.oracle_sha256
deterministic_core.run.fixture_split
deterministic_core.run.implementation_plan_identity
deterministic_core.run.implementation_commit
deterministic_core.run.environment_identity
deterministic_core.run.dependency_identity
deterministic_core.manifest.manifest_id
deterministic_core.manifest.manifest_version
deterministic_core.manifest.manifest_sha256
deterministic_core.manifest.oracle_sha256
deterministic_core.manifest.fixture_split
deterministic_core.manifest.fixture_ids
deterministic_core.manifest.data_policy
deterministic_core.manifest.matching_rules
deterministic_core.manifest.normalizers
deterministic_core.upstream_contracts
deterministic_core.profile_and_policy_identities
deterministic_core.case_results
deterministic_core.measurements
deterministic_core.typed_failure_summary
deterministic_core.interpretation_id
deterministic_core.limitations_id
```

`run_id` is a required caller-supplied lowercase token matching `[a-z0-9][a-z0-9-]{0,63}`. It
must remain stable for a deterministic rerun and is never generated from random state, a UUID, wall
clock, timestamp, hostname, username, process ID, filesystem order, or completion order. For the
same manifest, case, selected split, and configuration, a deterministic rerun may reuse the same
`run_id`; a separately retained duplicate execution must use a new explicit caller-supplied
`run_id`. `run_id` is part of `deterministic_core` and participates in
`deterministic_core_sha256`.

`profile_and_policy_identities` contains the complete proposed T4 policy projection from section
3.3 plus its bound `fusion_policy_config_hash`, the two `FAKE_DETERMINISTIC_V1` profile IDs,
and their approved catalog/config identities. `case_results` contain only stable IDs, stage
states, closed statuses/codes, correlation ID, source/result/policy/canonical digests, and metric
eligibility/count fields. They never contain media, reference or hypothesis transcript text,
Vision labels, prompts, provider payloads, raw exceptions, or paths. `interpretation_id` and
`limitations_id` select bounded, predeclared fixture-only text; free-form interpretation is not
part of the core.

The exact proposed serialization algorithm identity is `P2T5-REPORT-CANONICAL-JSON-V1`; it is
not a P2-T5 contract binding identity and is never serialized as `contract_name`:

```python
json.dumps(
    deterministic_core,
    ensure_ascii=False,
    sort_keys=True,
    separators=(",", ":"),
    allow_nan=False,
)
```

The returned string is encoded as UTF-8. `sort_keys=True` orders object keys by code point. Arrays
are sorted before serialization by these required keys: `case_results` by lowercase
`fixture_id`; `measurements` by `metric_id`; `manifest.matching_rules` by `(scope, rule_id)`;
`manifest.normalizers` by `(scope, normalizer_id)`; and all closed failure/count maps by lexical
key. No source traversal order, filesystem order, hash-map order, process order, hostname, or
runtime completion order may affect the core.

The scalar rules are exact: JSON `null` is retained for declared nullable stable fields and is
never replaced with omission; every datetime is normalized to UTC and serialized as
`YYYY-MM-DDTHH:mm:ss.ffffffZ`; non-finite numbers (`NaN`, `Infinity`, and `-Infinity`) are
rejected before projection and again by `allow_nan=false`; decimal measurements are parsed from
decimal strings, never from binary floats, quantized to exactly six fractional places using
`ROUND_HALF_EVEN`, and serialized as strings such as `"0.000000"` or `"1.250000"`. Counts remain
integers. A status/value/denominator mismatch is a typed report failure, not a coercion.

`deterministic_core_sha256` is the lowercase SHA-256 of the exact UTF-8 bytes of the serialized
core above. The hash field is an envelope value excluded from the core projection. The raw-file
SHA-256 is computed separately over the complete final report file bytes and is recorded only in
the separately authorized evidence/approval binding; it is not embedded in the report that it
hashes. Git blob IDs and plan/artifact binding hashes are likewise external metadata. Thus no
artifact contains or hashes its own core hash, raw-file hash, or Git blob ID.

`volatile_run_metadata` is the only non-core region and has exactly these five keys, each with a
nullable value:
`started_at`, `finished_at`, `stage_durations_ms`, `harness_overhead_ms`, and
`timing_sample_counts`. The two times use the same UTC six-fraction format; duration and sample
values are finite non-negative integers; maps are sorted by their closed stage/metric keys; a
missing optional observation is `null` rather than an invented zero. No process ID, temporary
location, host identity, environment value, exception text, or raw payload is a report field, even
in this volatile region. `volatile_run_metadata` is serialized in the complete report but is never
included in the deterministic core or any rerun-parity claim.

`run.executed_at` is not a volatile field. It is required exactly once in the stable core as a
caller-injected UTC instant formatted `YYYY-MM-DDTHH:mm:ss.ffffffZ`; the identical string is passed
to every invoked T4 call in the run and therefore participates in every fused T4 canonical digest.
It is never read from the wall clock, regenerated per case, rounded, or replaced by
`started_at`/`finished_at`. A missing, non-UTC, differently formatted, or per-case value is a typed
report/precondition failure. The full report itself uses the same UTF-8 compact JSON rules for its
five envelope fields, but only the `deterministic_core` bytes feed `deterministic_core_sha256`.

The `P2T5-CASE-OUTCOME-CANONICAL-JSON-V1` projection is also closed: it contains the case
contract identity/version, fixture ID/split, T1 decision/reasons, four stage states, correlation ID,
upstream identities/versions/statuses, closed failure/rejection fields, source/result/policy
digests, and measurement status/count/value/eligibility fields. It excludes `run_id`,
`executed_at`, all volatile fields, raw media, transcript/label text, paths, rejected inputs,
report-envelope fields, and `case_outcome_sha256` itself. Its arrays and maps use the section 5.5 order
and scalar rules; omission, reordering, or an undeclared field is a domain mismatch.

### 5.6 Digest domains and external identity bindings (OWNER_APPROVED_V3_20260919)

Every digest field below is lowercase hexadecimal SHA-256. The input bytes are exact and UTF-8 is
used only where the row says so. No digest field includes itself, a parent envelope hash, a Git
blob ID, a raw-file hash, or volatile metadata. A field named sha256 must use one of these
domains; it may not use an implementation-specific object representation.

| Field or binding | Domain identity and exact bytes |
|---|---|
| manifest_sha256, cases_sha256, oracle_sha256, matching_rule_sha256 | P2T5-RAW-BYTES-SHA256-V1: complete raw bytes of the named JSON file as read from the repository, including its current newline bytes; no JSON parsing, whitespace normalization, Unicode normalization, or reserialization |
| source_media_sha256 | P2T5-RAW-BYTES-SHA256-V1: complete raw bytes of the referenced PNG or WAV file; this is the same value placed in the T1 source reference and no decoded media representation is hashed |
| t1_result_sha256 | P2T5-T1-RESULT-CANONICAL-JSON-V1: MediaValidationResultV1.model_dump(mode='json'), serialized with UTF-8, ensure_ascii=false, sort_keys=true, compact separators, and allow_nan=false; object keys are sorted, arrays retain contract order, and no report/envelope/hash field is added |
| asr_result_sha256 and vision_result_sha256 | Existing P2T4-CANONICAL-JSON-V1 over the exact validated P2.AsrResultV1@1.0 or P2.VisionUnderstandingResultV1@1.0 object, using the frozen canonical_projection / canonical_bytes / canonical_sha256 helper; no report fields or raw transcript/provider text are appended |
| t4_result_sha256 | Existing P2T4-CANONICAL-JSON-V1 over the exact typed P2T4.P2T4FusedResultV1@1.0, including its status and typed upstream-failure data; no P2-T5 wrapper is substituted |
| t4_rejection_sha256 | Existing P2T4-CANONICAL-JSON-V1 over the exact typed P2T4.P2T4FusionInputRejectionV2@2.0; the rejected input and any observed noncanonical value are excluded from the rejection model and are never hashed into it |
| fusion_policy_config_hash | Existing T4 fusion_policy_config_hash: P2T4-CANONICAL-JSON-V1 over the complete validated P2T4FusionPolicyConfigV1 projection; the external hash field is not included in its own projection |
| deterministic_core_sha256 | P2T5-REPORT-CANONICAL-JSON-V1: exact UTF-8 bytes of the serialized deterministic_core defined in section 5.5; deterministic_core_sha256, volatile metadata, complete-report raw bytes, and Git identity are excluded |
| case_outcome_sha256 | P2T5-CASE-OUTCOME-CANONICAL-JSON-V1: exact stable redacted case-result projection after excluding case_outcome_sha256, volatile metadata, raw media, transcript/label text, rejected inputs, and report-envelope fields; apply the section 5.5 UTF-8 JSON rules and required semantic array ordering |
| Plan, implementation, dependency, environment, and Git identities | External approval/provenance bindings or the explicitly named raw bytes; they are not silently treated as T4 canonical digests and are never embedded in a value they hash |

The T4 source-result helper is authoritative for T2/T3/T4 typed model digests; the P2-T5
report/core and case-outcome domains are distinct. A future schema must name the domain beside
every generic digest field and must reject an omitted or mismatched domain rather than guessing.

## 6. Fixture and oracle design

### 6.1 Count, split, IDs, ownership, and provenance

The recommended initial target is exactly 20 entries: 12 development and 8 held-out. This is a
proposal requiring owner confirmation; “approximately 20” is not an acceptance criterion. The
development/held-out purpose, coverage allocation, and final named ground-truth owner are owner
decisions. The proposed ground-truth owner role is the P2-T5 task owner, with a reviewer distinct
from the author and not involved in scorer implementation.

The initial data policy is `SYNTHETIC_ONLY` and local. A licensed fixture is permitted only if it
is non-child, locally present before the run, has a recorded license/source identity, and requires
no network retrieval. No real child, personal, identifying, or external handbook/workbook data may
enter the package.

The proposed tracked fixture package is:

Each of the four exact paths below is `PROPOSED_PATH_ALLOWLIST` — not authorized. The package
does not exist and this documentation task does not create it.

```text
features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/manifest-v1.json
features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/cases-v1.json
features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/expected-v1.json
features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/matching-rule-v1.json
```

These four JSON files do not exist yet. `matching-rule-v1.json` is a hand-authored serialization of
the owner-approved rule identities, scopes, canonical bytes, and hashes; it is not generated from
the scorer and is not an independent permission to change a rule. The approval must enumerate each
file; `fixtures/**`, directory wildcards, generated artifacts, README files, and unlisted media are
not an approval scope.

Each entry must carry raw SHA-256 values for the manifest/case/oracle bytes and every referenced
media byte. A changed byte creates a new fixture package version and invalidates prior evidence.
No fixture may reuse an ASR Round-1, Vision B4/v3, P2-T4, FEAT-018, or live benchmark case,
ground-truth file, output, or generated payload. The new oracle is authored from the new fixture
specification before the evaluator is run.

The owner decision bundle freezes the oracle identity/version scheme, author role, independent
review requirement, immutability/revision rule, no-implementation-derived-oracle rule, and
held-out anti-tuning rule only. Because the fixture package does not yet exist, no truthful
`expected-v1.json` raw SHA-256 or Git blob may be recorded at PRE-G1. The exact oracle raw hash,
blob identity, and package hashes are bound later at the approved fixture/G2-G5 checkpoint after
the bytes actually exist; inventing a future hash is prohibited.

Each future cases-v1 entry has exactly one fixture_id, split, image_ref, audio_ref,
source_media_sha256 values, expected_t1 decision/reasons, asr_scenario, vision_scenario,
t4_input_mutation, expected_t4 outcome/projection, expected case_status, and coverage tags.
The image_ref and audio_ref are the ID-matched PNG/WAV pair in section 9.3. The scenario fields
select one exact existing fake-adapter enum member or NOT_INVOKED for a T1 recapture; they never
contain raw provider text. expected-v1.json has exactly one hand-authored oracle row for each
fixture_id and repeats the exact T1, typed T2/T3, T4, stage-state, case-status, and metric
eligibility expectations. The manifest, cases, expected oracle, and matching-rule ID sets must
be equal where applicable; no raw private sentinel or rejected input value is stored.

### 6.2 Proposed coverage matrix

The following allocation is a coverage proposal, not an approved fixture manifest:

The common exact success tuples used below are not alternatives:

Every T4 identity named in the matrix is fully qualified: the display spelling P2T4FusedResultV1@1.0
means P2T4.P2T4FusedResultV1@1.0, and P2T4FusionInputRejectionV2@2.0 means
P2T4.P2T4FusionInputRejectionV2@2.0. The serialized contract_name/version fields remain the
upstream wire values defined by the T4 contract.

- A-VIETNAMESE means FakeAsrScenario.VIETNAMESE -> P2.AsrResultV1@1.0, status SUCCEEDED,
  profile FAKE_DETERMINISTIC_V1, attempt 1, repair_attempted false, and speech diagnostic
  DETECTED.
- A-SILENCE means FakeAsrScenario.SILENCE -> the same P2 ASR identity/profile, status SUCCEEDED,
  attempt 1, repair_attempted false, speech diagnostic NO_SPEECH_SUSPECTED, and zero segments.
- V-RAW means FakeVisionScenario.RAW_OUTPUT -> P2.VisionUnderstandingResultV1@1.0, status
  SUCCEEDED, profile FAKE_DETERMINISTIC_V1, attempt 1, repair_attempted false,
  policy_execution_state PASSED, and the upstream constant policy_match_view_version
  vision-policy-match-view-v2. The output profile named after V-RAW selects only the
  hand-authored collection shape: ORDINARY_SUCCESS, EMPTY_SUCCESS, ALL_COLLECTIONS,
  ALL_SCORED_COLLECTIONS, ENTITIES_ONLY, or VISION_ONLY_OBSERVATIONS.
- A typed-failure cell names the exact FakeAsrScenario/FakeVisionScenario, P2 identity, status,
  profile, error code, error detail, attempt_number, repair_attempted, retryable, and Vision
  policy_execution_state. T4 UPSTREAM_FAILURE keeps the exact typed failure reference and sets
  failed_modality to ASR, VISION, or BOTH.

These expansions bind to the read-only sources
`backend/src/sketch2life/infrastructure/ai/fake_asr.py`,
`backend/src/sketch2life/infrastructure/ai/fake_vision.py`,
`backend/src/sketch2life/contracts/schemas/asr.py`,
`backend/src/sketch2life/contracts/schemas/vision.py`, and
`backend/src/sketch2life/contracts/schemas/media_validation.py`. Each matrix row selects exactly
one existing enum member and one exact typed tuple from those sources; `NOT_INVOKED` is the only
value for a T1 recapture. The matrix does not use an unlisted scenario, a slash-separated
alternative, a caller retry, or an inferred error detail.

| ID | Split and exact media | T1 oracle | ASR fake scenario and exact result | Vision fake scenario and exact result | T4 mutation and exact oracle | Case/run status |
|---|---|---|---|---|---|---|
| feat003-p2t5-dev-001 | DEVELOPMENT; media/feat003-p2t5-dev-001.png + media/feat003-p2t5-dev-001.wav | PASS; no recapture reasons | A-VIETNAMESE; ordinary non-empty transcript; WER/CER reference absent; exact success tuple | V-RAW; ORDINARY_SUCCESS; exact success tuple | NONE; P2T4FusedResultV1@1.0 status FUSED; oracle carries source/result/policy/case digests | COMPLETED; run contribution COMPLETED |
| feat003-p2t5-dev-002 | DEVELOPMENT; media/feat003-p2t5-dev-002.png + media/feat003-p2t5-dev-002.wav | PASS; no recapture reasons | A-VIETNAMESE; exact success tuple | V-RAW; EMPTY_SUCCESS; SUCCEEDED with empty entities/actions/relations/themes, policy PASSED | NONE; P2T4FusedResultV1@1.0 status FUSED; no fabricated semantic claim | COMPLETED |
| feat003-p2t5-dev-003 | DEVELOPMENT; media/feat003-p2t5-dev-003.png + media/feat003-p2t5-dev-003.wav | RECAPTURE; IMAGE_DIMENSIONS_TOO_SMALL | NOT_INVOKED; no ASR request/result | NOT_INVOKED; no Vision request/result | NONE; T4 NOT_EXECUTED; oracle asserts all downstream states NOT_EXECUTED | EXPECTED_TERMINAL |
| feat003-p2t5-dev-004 | DEVELOPMENT; media/feat003-p2t5-dev-004.png + media/feat003-p2t5-dev-004.wav | RECAPTURE; AUDIO_NO_SPEECH_SIGNAL | NOT_INVOKED; no ASR request/result | NOT_INVOKED; no Vision request/result | NONE; T4 NOT_EXECUTED; oracle asserts no vision-only continuation | EXPECTED_TERMINAL |
| feat003-p2t5-dev-005 | DEVELOPMENT; media/feat003-p2t5-dev-005.png + media/feat003-p2t5-dev-005.wav | PASS; no recapture reasons | A-VIETNAMESE; hand-authored reference present; exact success tuple; WER/CER eligible true | V-RAW; ORDINARY_SUCCESS; exact success tuple | NONE; P2T4FusedResultV1@1.0 status FUSED; metric oracle has eligible denominator 1 | COMPLETED |
| feat003-p2t5-dev-006 | DEVELOPMENT; media/feat003-p2t5-dev-006.png + media/feat003-p2t5-dev-006.wav | PASS; no recapture reasons | A-SILENCE; exact success tuple; no WER/CER eligibility and NO_SPEECH_SUSPECTED | V-RAW; ORDINARY_SUCCESS; exact success tuple | NONE; P2T4FusedResultV1@1.0 status FUSED; no automatic T1 recapture | COMPLETED |
| feat003-p2t5-dev-007 | DEVELOPMENT; media/feat003-p2t5-dev-007.png + media/feat003-p2t5-dev-007.wav | PASS; no recapture reasons | FakeAsrScenario.TIMEOUT -> P2.AsrResultV1@1.0 FAILED, profile FAKE_DETERMINISTIC_V1, ASR_TIMEOUT / TIMEOUT_BUDGET_EXCEEDED, attempt 1, repair false, retryable false | V-RAW; ORDINARY_SUCCESS; exact success tuple | NONE; P2T4FusedResultV1@1.0 status UPSTREAM_FAILURE, failed_modality ASR, exact ASR failure ref | COMPLETED_WITH_TYPED_FAILURES |
| feat003-p2t5-dev-008 | DEVELOPMENT; media/feat003-p2t5-dev-008.png + media/feat003-p2t5-dev-008.wav | PASS; no recapture reasons | FakeAsrScenario.PROVIDER_TRANSIENT_FAILURE -> P2.AsrResultV1@1.0 FAILED, profile FAKE_DETERMINISTIC_V1, ASR_PROVIDER_FAILURE / TRANSIENT_RUNTIME_FAILURE, attempt 2, repair false, retryable true | V-RAW; ORDINARY_SUCCESS; exact success tuple | NONE; P2T4FusedResultV1@1.0 status UPSTREAM_FAILURE, failed_modality ASR, exact ASR failure ref | COMPLETED_WITH_TYPED_FAILURES |
| feat003-p2t5-dev-009 | DEVELOPMENT; media/feat003-p2t5-dev-009.png + media/feat003-p2t5-dev-009.wav | PASS; no recapture reasons | A-VIETNAMESE; exact success tuple | V-RAW; ALL_COLLECTIONS; exact success tuple with entity/action/relation/theme collections | NONE; P2T4FusedResultV1@1.0 status FUSED; oracle has all scored collection counts | COMPLETED |
| feat003-p2t5-dev-010 | DEVELOPMENT; media/feat003-p2t5-dev-010.png + media/feat003-p2t5-dev-010.wav | PASS; no recapture reasons | A-VIETNAMESE; exact success tuple | FakeVisionScenario.RAW_OUTPUT -> P2.VisionUnderstandingResultV1@1.0 FAILED, profile FAKE_DETERMINISTIC_V1, PROHIBITED_CLAIM_DETECTED / MENTAL_STATE_CLAIM, attempt 1, repair false, retryable false, policy_execution_state BLOCKED | NONE; P2T4FusedResultV1@1.0 status UPSTREAM_FAILURE, failed_modality VISION, exact Vision failure ref | COMPLETED_WITH_TYPED_FAILURES |
| feat003-p2t5-dev-011 | DEVELOPMENT; media/feat003-p2t5-dev-011.png + media/feat003-p2t5-dev-011.wav | PASS; no recapture reasons | A-VIETNAMESE; exact success tuple | FakeVisionScenario.TIMEOUT -> P2.VisionUnderstandingResultV1@1.0 FAILED, profile FAKE_DETERMINISTIC_V1, VISION_TIMEOUT / TIMEOUT_BUDGET_EXCEEDED, attempt 1, repair false, retryable false, policy_execution_state NOT_EXECUTED | NONE; P2T4FusedResultV1@1.0 status UPSTREAM_FAILURE, failed_modality VISION, exact Vision failure ref | COMPLETED_WITH_TYPED_FAILURES |
| feat003-p2t5-dev-012 | DEVELOPMENT; media/feat003-p2t5-dev-012.png + media/feat003-p2t5-dev-012.wav | PASS; no recapture reasons | FakeAsrScenario.MODEL_UNAVAILABLE -> P2.AsrResultV1@1.0 FAILED, profile FAKE_DETERMINISTIC_V1, ASR_MODEL_UNAVAILABLE / MODEL_LOAD_FAILED, attempt 1, repair false, retryable false | V-RAW; ORDINARY_SUCCESS; exact success tuple; no fallback adapter/request | NONE; P2T4FusedResultV1@1.0 status UPSTREAM_FAILURE, failed_modality ASR, exact terminal result recorded and no continuation | COMPLETED_WITH_TYPED_FAILURES |
| feat003-p2t5-heldout-001 | HELD_OUT; media/feat003-p2t5-heldout-001.png + media/feat003-p2t5-heldout-001.wav | PASS; no recapture reasons | A-VIETNAMESE; exact success tuple | V-RAW; ALL_SCORED_COLLECTIONS; exact success tuple | NONE; P2T4FusedResultV1@1.0 status FUSED; held-out oracle row is read-only to scorer/tuning | COMPLETED |
| feat003-p2t5-heldout-002 | HELD_OUT; media/feat003-p2t5-heldout-002.png + media/feat003-p2t5-heldout-002.wav | PASS; no recapture reasons | A-VIETNAMESE; support-only hand-authored narration reference; exact success tuple | V-RAW; ENTITIES_ONLY; exact success tuple | NONE; P2T4FusedResultV1@1.0 status FUSED; narration support cannot create unsupported candidates | COMPLETED |
| feat003-p2t5-heldout-003 | HELD_OUT; media/feat003-p2t5-heldout-003.png + media/feat003-p2t5-heldout-003.wav | PASS; no recapture reasons | A-SILENCE; exact success tuple; empty transcript/no WER/CER eligibility | V-RAW; VISION_ONLY_OBSERVATIONS; exact success tuple | NONE; P2T4FusedResultV1@1.0 status FUSED; vision-only output remains eligible | COMPLETED |
| feat003-p2t5-heldout-004 | HELD_OUT; media/feat003-p2t5-heldout-004.png + media/feat003-p2t5-heldout-004.wav | PASS; no recapture reasons | FakeAsrScenario.PROVIDER_PERMANENT_FAILURE -> P2.AsrResultV1@1.0 FAILED, profile FAKE_DETERMINISTIC_V1, ASR_PROVIDER_FAILURE / PERMANENT_RUNTIME_FAILURE, attempt 1, repair false, retryable false | FakeVisionScenario.PROVIDER_PERMANENT_FAILURE -> P2.VisionUnderstandingResultV1@1.0 FAILED, profile FAKE_DETERMINISTIC_V1, VISION_PROVIDER_FAILURE / PERMANENT_RUNTIME_FAILURE, attempt 1, repair false, retryable false, policy_execution_state NOT_EXECUTED | NONE; P2T4FusedResultV1@1.0 status UPSTREAM_FAILURE, failed_modality BOTH, both exact failure refs | COMPLETED_WITH_TYPED_FAILURES |
| feat003-p2t5-heldout-005 | HELD_OUT; media/feat003-p2t5-heldout-005.png + media/feat003-p2t5-heldout-005.wav | PASS; no recapture reasons | A-VIETNAMESE; exact success tuple, then T4 seam replaces slot | V-RAW; ORDINARY_SUCCESS; exact success tuple | WRONG_FAMILY_ASR; P2T4FusionInputRejectionV2@2.0 REJECTED, ASR / IDENTITY_VERSION / WRONG_FAMILY, expected P2.AsrResultV1@1.0, observed FEAT018.LiveAsrResultV1@1.0, observed_status SUCCEEDED, field UPSTREAM_TYPE | EXPECTED_TERMINAL |
| feat003-p2t5-heldout-006 | HELD_OUT; media/feat003-p2t5-heldout-006.png + media/feat003-p2t5-heldout-006.wav | PASS; no recapture reasons | A-VIETNAMESE; exact success tuple, then duplicate segments[*].index at T4 seam | V-RAW; ORDINARY_SUCCESS; exact success tuple | DUPLICATE_ASR_SEGMENT_INDEX; P2T4FusionInputRejectionV2@2.0 REJECTED, ASR / ADMISSIBILITY / INVALID_STRUCTURE, expected and observed P2.AsrResultV1@1.0, observed_status SUCCEEDED, field DUPLICATE_SEGMENT_INDEX | EXPECTED_TERMINAL |
| feat003-p2t5-heldout-007 | HELD_OUT; media/feat003-p2t5-heldout-007.png + media/feat003-p2t5-heldout-007.wav | PASS; no recapture reasons | A-VIETNAMESE; exact success tuple | V-RAW; ORDINARY_SUCCESS; exact success tuple, then policy_match_view_version mutation at T4 seam | NONCANONICAL_VISION_MATCH_VIEW; P2T4FusionInputRejectionV2@2.0 REJECTED, VISION / ADMISSIBILITY / INVALID_STRUCTURE, expected and observed P2.VisionUnderstandingResultV1@1.0, observed_status SUCCEEDED, field POLICY_MATCH_VIEW_VERSION | EXPECTED_TERMINAL |
| feat003-p2t5-heldout-008 | HELD_OUT; media/feat003-p2t5-heldout-008.png + media/feat003-p2t5-heldout-008.wav | PASS; no recapture reasons | A-VIETNAMESE; exact success tuple, correlation retained until T4 seam | V-RAW; ORDINARY_SUCCESS; exact success tuple | CORRELATION_MISMATCH; P2T4FusionInputRejectionV2@2.0 REJECTED, BOTH / CORRELATION / CORRELATION_MISMATCH, expected_identity NONE, observed_identity UNKNOWN, observed_status null, field CORRELATION_ID | EXPECTED_TERMINAL |

This is a complete 20-row split: 12 DEVELOPMENT and 8 HELD_OUT. Each row names one
FakeAsrScenario or FakeVisionScenario, one exact output shape, one mutation category, and one
oracle outcome; slash alternatives are not unresolved cases. The matrix is
`OWNER_APPROVED_V3_20260919` under OD-2 and OD-4 (`DECISIONS.md`, 2026-09-19). The future manifest, cases, and expected
oracle must have the same 20 IDs, exactly 40 ID-matched media paths, exactly one oracle row per
ID, no unreferenced media, no duplicate IDs, no raw private sentinel, and no held-out case
available to rule/scorer tuning.

### 6.3 Independent oracle and anti-circularity rules

`expected-v1.json` is the hand-authored oracle. It is created by the ground-truth owner and
independently reviewed before any evaluator run. It contains expected T1 decisions/reasons,
expected T2/T3 typed branches, expected T4 outcome/closed rejection fields, eligible metric
denominators, and hand-computed expected aggregate checks. It does not contain raw provider/model
output.

The evaluator must never generate, mutate, or rewrite the oracle. The fixture generator, if one is
approved later, cannot import the evaluator, scorer, implementation-under-test, or output report.
The scorer cannot derive expected values from an adapter output, T4 implementation snapshot, or
previous report. Tests must load the oracle as an independent input and verify its raw hash before
comparison. A mismatch is a reported oracle/harness failure, not a reason to update expected data.

Ownership is intentionally separated: the fixture/ground-truth author authors the media references,
case descriptors, and hand-computed oracle; the scorer implementer cannot author or edit the oracle;
the independent reviewer is distinct from both and reviews the frozen raw hash before evaluation.
The held-out eight IDs and their oracle rows are frozen before any scorer, normalizer, threshold,
policy, or interpretation tuning. Development-only tuning may read only the 12 development rows;
the evaluator reads held-out rows only during the explicitly selected `HELD_OUT` evaluation, and
the scorer has no write path to either split. Any held-out change creates a new manifest/oracle
version and invalidates prior comparison; it is never an in-place correction after seeing a score.

HELD_OUT cases may have independently authored and frozen ground truth/oracles for scoring. After
HELD_OUT evaluation starts, held-out observations and results must never tune scorer logic,
matching rules, generators, thresholds, or the oracle. Any post-start change requires a new
manifest/oracle version and a separately reviewed comparison; it cannot alter the in-progress or
prior evaluation.

The proposed canonical semantic matching rule is the existing `vision-b4-matching-rule-v1` text
unchanged, by exact content identity (`SHA-256 4e405275257f1428f8f73b5339dac1941ce6f008ff00d39cc19c391c035b96bb`).
Its scope is exactly entity, action, relation, and theme matching only. Reusing a rule by hash is
not reusing B4 fixtures or rescoring B4 evidence. If the owner chooses a new P2-T5 rule, it must
receive a new identity, hand-authored text, hash, and owner decision; no silent wording change is
allowed.

Under the proposed rule:

1. Score only schema-mapped, eligible results. Schema-invalid, input-invalid, typed failure, and
   T4 rejection cases receive no semantic-quality score; their typed counts remain first-class.
2. Normalize candidate and oracle labels/predicates only under the semantic
   `vision-b4-matching-rule-v1` domain: Unicode NFC, case-folding, trimming, hyphen-to-space
   conversion, and Unicode whitespace collapse. This is not the `vi-asr-normalizer-v1` domain,
   which is reserved for Vietnamese WER/CER views. No synonym,
   stemming, translation, embedding, substring, model judge, or post-authoring alias is allowed.
3. Build same-collection bipartite edges for exact normalized labels/predicates and select a
   maximum-cardinality matching. Ties are resolved by ascending ground-truth ID, then predicted
   observation ID.
4. Credit actions only when every non-null actor/object endpoint resolves to the corresponding
   matched ground-truth entity; null endpoints match only null endpoints. Credit relations only
   when both endpoints resolve to the corresponding matched entity/action. Credit themes only
   when every evidence reference resolves to a matched authored entity/action/relation.
5. Confidence is not scored. Ambiguous regions report count/rate only; accuracy remains
   `NOT_MEASURED` because the current V1 contract has no geometry/evidence-target ground truth.
6. The oracle's case and aggregate expected values are computed independently by hand or by a
   separately reviewed non-production calculation; the implementation scorer never writes them.

Ground-truth labels may exist in the tracked synthetic oracle because they are explicitly authored
test data. They are not copied into final evidence summaries, logs, CLI output, or report fields
unless a future evidence authorization explicitly permits a bounded synthetic field.

### 6.4 Four separate rule identities, hashes, and scopes (`OWNER_APPROVED_V3_20260919`)

The following four identities and domains are separate owner-approved bindings, not aliases: (1) the semantic
matching rule, (2) the ASR normalizer plus its source-file provenance and raw source hash, (3) the
`P2T5.ASRMetricRuleV1@1.0` canonical rule payload and canonical payload hash, and (4) the
`P2T5.ConflictMatchingRuleV1@1.0` canonical rule payload and canonical payload hash. The first
two hashes identify complete source files; the latter two hashes identify exact canonical JSON
rule payload bytes. A source-file hash is never substituted for a canonical rule-payload hash, and
no implementation may reuse any identity or hash outside the scope shown in its row.

| Scope | Approved rule/normalizer identity | Approved hash or hash domain | Allowed use | Explicitly not allowed |
|---|---|---|---|---|
| Entity, action, relation, theme matching | `vision-b4-matching-rule-v1` | `4e405275257f1428f8f73b5339dac1941ce6f008ff00d39cc19c391c035b96bb` (raw SHA-256 of the exact B4 rule text) | Same-collection label/predicate/endpoint/evidence-reference matching and the collection coverage/accuracy views described in section 6.3 | WER, CER, conflict sets, T1 validity, or any reuse of B4 fixtures/evidence |
| WER and CER normalization | `vi-asr-normalizer-v1` | Source implementation provenance only: `backend/src/sketch2life/benchmark/asr_scoring.py`, raw SHA-256 `955be57f55ea917f4ed1e6ed58bc2744d8b4a5218183e2bcd186900aea8e470c`; no B4 matching-rule hash is a substitute | Vietnamese ASR WER token view and CER character view | Entity/action/relation/theme matching or conflict matching |
| WER/CER scoring rule | `P2T5.ASRMetricRuleV1@1.0` | SHA-256 `8be5f74a13d7515a7995dbffcff2db8aca6876cd7fe3898c4da26ecf86823711` of the exact canonical payload below; `OWNER_APPROVED_V3_20260919` | WER/CER formula, eligibility, denominator, normalization, six-place representation, and unavailable-state handling only | Entity/action/relation/theme or conflict matching |
| Conflict matching | `P2T5.ConflictMatchingRuleV1@1.0` | SHA-256 `dfe093c10d82b36cc34bfd3d4fe7572d8de1fb3d5f1b0598e0adb85f9d7e5fd8` of the exact canonical payload below; `OWNER_APPROVED_V3_20260919` | Exact-set conflict TP/FP/FN and conflict precision/recall only | Entity/action/relation/theme matching, WER, or CER |

The source, scope, byte-count, and hash audit for these bindings is:

| Binding | Exact source path(s) and byte scope | Scope | Exact UTF-8 bytes | SHA-256 |
|---|---|---|---:|---|
| `vision-b4-matching-rule-v1` | `features/FEAT-003-multimodal-understanding/fixtures/vision-b4/matching-rule-v1.md`; complete raw file bytes, including its current newline bytes | Entity, action, relation, and theme matching only | 2,526 raw | `4e405275257f1428f8f73b5339dac1941ce6f008ff00d39cc19c391c035b96bb` |
| `vi-asr-normalizer-v1` | `backend/src/sketch2life/benchmark/asr_scoring.py`; complete raw source file bytes, including its current newline bytes | Vietnamese WER token view and CER character view only | 4,156 raw | `955be57f55ea917f4ed1e6ed58bc2744d8b4a5218183e2bcd186900aea8e470c` |
| `P2T5.ASRMetricRuleV1@1.0` | This plan, section 6.4 canonical payload; the payload's `normalizer.source_path` above is the scorer source provenance | WER and CER formulas, eligibility, denominators, exclusions, and decimal representation only | 1,563 canonical; no newline | `8be5f74a13d7515a7995dbffcff2db8aca6876cd7fe3898c4da26ecf86823711` |
| `P2T5.ConflictMatchingRuleV1@1.0` | This plan, section 6.4 canonical payload; field semantics are constrained by `backend/src/sketch2life/contracts/schemas/p2_t4_fusion.py` and `backend/src/sketch2life/application/services/p2_t4_fusion.py` | Exact P2T4 conflict-key TP/FP/FN and precision/recall only | 1,521 canonical; no newline | `dfe093c10d82b36cc34bfd3d4fe7572d8de1fb3d5f1b0598e0adb85f9d7e5fd8` |
| `P2T4FusionPolicyConfigV1` candidate | This plan, section 3.3 canonical payload; projection source `backend/src/sketch2life/contracts/schemas/p2_t4_fusion.py`; freeze/package provenance is section 3.2 | T4 entity/action/narration/negation policy instance only | 466 canonical; no newline | `4b378f69a33b86aeefc7443a23ac819e46b986132525cdd8a55d112dfb96415c` |

The two new rule payloads are complete JSON objects. The code blocks are the exact compact UTF-8
JSON bytes used for hashing; object keys are lexicographically sorted, arrays remain in the shown
order, insignificant whitespace is absent, and `allow_nan=false` is required. An independent
reproduction is:

The owner decision bundle must bind these exact payload bytes, canonical byte counts, payload
SHA-256 values, source paths/provenance, and scope rows; it must not approve only an abstract hash
domain. The payloads remain proposals until owner approve/reject, but no replacement payload or
hash may be selected implicitly during implementation.

```python
canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True,
                       separators=(",", ":"), allow_nan=False).encode("utf-8")
sha256(canonical).hexdigest()
```

`P2T5.ASRMetricRuleV1@1.0` canonical payload:

```json
{"eligibility":{"asr_status":["SUCCEEDED"],"manifest_wer_cer_flags":["wer_eligible=true","cer_eligible=true"],"provider":"fixture","reference_view":"non_empty_after_normalization","t1_decision":["PASS"]},"empty_set_behavior":{"empty_eligible_population":"NOT_MEASURED: NO_ELIGIBLE_CASES","empty_normalized_reference":"excluded_before_scoring"},"exclusion_rules":["T1 decision is not PASS","ASR result is not SUCCEEDED","manifest WER/CER eligibility is false","normalized reference sequence is empty"],"metrics":{"CER":{"denominator":"reference_character_count","formula":"levenshtein_distance(reference_characters,hypothesis_characters) / reference_character_count","numerator":"levenshtein_distance(reference_characters,hypothesis_characters)"},"WER":{"denominator":"reference_token_count","formula":"levenshtein_distance(reference_tokens,hypothesis_tokens) / reference_token_count","numerator":"levenshtein_distance(reference_tokens,hypothesis_tokens)"}},"normalizer":{"cer_view":"remove_all_normalized_whitespace","id":"vi-asr-normalizer-v1","operations":["NFC","casefold","punctuation_to_space","unicode_whitespace_collapse"],"preserve":["diacritics","U+0111_LATIN_SMALL_LETTER_D_WITH_STROKE"],"source_path":"backend/src/sketch2life/benchmark/asr_scoring.py","source_sha256":"955be57f55ea917f4ed1e6ed58bc2744d8b4a5218183e2bcd186900aea8e470c","wer_view":"split_normalized_text_on_whitespace"},"rounding":{"decimal_places":6,"mode":"ROUND_HALF_EVEN","representation":"decimal_string"},"rule_id":"P2T5.ASRMetricRuleV1","rule_version":"1.0","scope":["WER","CER"]}
```

Its independently reproduced SHA-256 is
`8be5f74a13d7515a7995dbffcff2db8aca6876cd7fe3898c4da26ecf86823711`.

`P2T5.ConflictMatchingRuleV1@1.0` canonical payload:

```json
{"eligibility":{"case_result_status":["FUSED"],"labeled_conflict_keys":true,"provider":"fixture","t1_decision":["PASS"]},"empty_set_behavior":{"eligible_case_with_both_empty_sets":{"fn":0,"fp":0,"precision":"NOT_MEASURED: ZERO_DENOMINATOR","recall":"NOT_MEASURED: ZERO_DENOMINATOR","tp":0},"no_labeled_conflict_keys_population":"NOT_MEASURED: NO_ELIGIBLE_CASES"},"exclusion_rules":["T1 decision is not PASS","fused result status is not FUSED","typed upstream failure, recapture, T4 rejection, or input failure","case has no labeled conflict keys"],"matching":{"allowed_reason_codes":["ENTITY_ATTRIBUTE_CONTRADICTION","ACTION_CONTRADICTION","RELATION_CONTRADICTION","LOW_CONFIDENCE_EVIDENCE"],"fn":"reference_keys - predicted_keys","fp":"predicted_keys - reference_keys","identity_invariant":"P2T4ConflictV1.vision_claim_ref equals fused_observation_id","include_low_confidence_evidence":true,"key_fields":["reason_code","fused_observation_id"],"non_key_fields":["conflict_id","narration_claim_ref","recommended_reviewer_attention"],"precision":"tp / (tp + fp)","recall":"tp / (tp + fn)","set_operation":"exact","source_contract_field_map":{"fused_observation_id":"P2T4ConflictV1.vision_claim_ref","reason_code":"P2T4ConflictV1.reason_code"},"tp":"intersection(reference_keys,predicted_keys)"},"normalizer":{"id":"NONE","text_normalization":"none"},"rounding":{"decimal_places":6,"mode":"ROUND_HALF_EVEN","representation":"decimal_string"},"rule_id":"P2T5.ConflictMatchingRuleV1","rule_version":"1.0","scope":["CONFLICT"]}
```

Its independently reproduced SHA-256 is
`dfe093c10d82b36cc34bfd3d4fe7572d8de1fb3d5f1b0598e0adb85f9d7e5fd8`.

The B4 hash is therefore used only for the four semantic collections. The ASR normalizer and the
two P2-T5 scoring rules have distinct identities and hash domains. A changed rule, changed
normalizer, changed scope, or changed hash creates a new proposal/version and invalidates the
affected oracle; it is never silently folded into an existing identity. Until the owner approves
the two new rule payloads and their hashes, their measurements are `NOT_MEASURED` with
`OWNER_FORMULA_PENDING` rather than scored under the B4 hash.

`matching-rule-v1.json` is the only proposed tracked rule artifact. Once separately approved, it
must serialize exactly four separate rule entries: the unchanged semantic
`vision-b4-matching-rule-v1` binding; the `vi-asr-normalizer-v1` source provenance/raw-hash
binding; and the two complete canonical payload/hash pairs above. The artifact is not created by
this task. Validation must recompute the semantic and normalizer entries from their complete raw
source files and each metric/conflict entry from its exact canonical UTF-8 payload; it must reject
a missing, duplicate, extra, malformed, stale, or scope-mismatched entry, and reject any
scope-broadened alias. No entry may be merged across the four domains, and no rule may be reused
for T1 validity, a different metric, or historical fixtures/evidence. All four entries are
`OWNER_APPROVED_V3_20260919` (`DECISIONS.md`, 2026-09-19); the artifact bytes themselves are not
created by this task.

## 7. Metrics

### 7.1 Deterministic metric definitions

| Metric family | Proposed semantics | Eligibility and unavailable behavior |
|---|---|---|
| Schema validity | `schema_valid_count / attempted_result_count`, with T1 validation validity reported separately | T1 `RECAPTURE` is not a malformed adapter result. No attempted result yields `NOT_MEASURED`. |
| Recapture/invalid input | Counts by T1 decision and each ordered reason; invalid manifest/hash/input failures are separate typed counts | Fixture cases are the counting unit for recapture/typed-failure/terminal outcomes; adapter-attempt denominators remain separate. |
| ASR WER | Existing `word_error_rate` over `vi-asr-normalizer-v1` normalized token sequences | Only manifest-eligible successful transcript cases with non-empty reference; typed failures/recaptures excluded with reason. |
| ASR CER | Existing `character_error_rate` over the same versioned normalizer's character view | Same eligibility and exclusion rules as WER; no raw transcript persists in report/evidence. |
| Entity/action/relation/theme coverage | Matched ground-truth items divided by ground-truth item count, per the approved matching rule | A zero-ground-truth fixture is `NOT_MEASURED` and excluded from the aggregate coverage denominator. |
| Entity/action/relation/theme accuracy | Matched predicted items divided by predicted item count, per the approved matching rule | A zero-prediction fixture is `NOT_MEASURED`; nonzero predictions with zero matches produce measured `0`. |
| Conflict detection | Exact-set true-positive/false-positive/false-negative counts over the closed `(reason_code, fused_observation_id)` keys, with precision and recall | Only `FUSED`, labeled-conflict cases. The pending rule payload defines no labeled keys as `NOT_MEASURED: NO_ELIGIBLE_CASES`; an eligible both-empty case has zero counts and ratio state `NOT_MEASURED: ZERO_DENOMINATOR`. |
| Ambiguous-region coverage | Matched/count-rate only where an explicit oracle count exists | Accuracy is always `NOT_MEASURED` under the current V1 contract; no geometry is invented. |
| Per-stage/end-to-end timing | Disabled in fixture-only v1 | `NOT_APPLICABLE` with reason `FIXTURE_ONLY_LATENCY_DISABLED`; no wall-clock timing is persisted or included in `deterministic_core`. It is never model/provider latency. |

The proposed v1 collection vocabulary is `coverage`/`accuracy`, while the original P2-T5 card's
precision/recall/F1 wording is not used for collection metrics. Conflict metrics alone use exact-set
precision and recall. WER/CER remain separate ASR metrics. F1 is not emitted in v1. The owner must
approve or reject this exact vocabulary; implementation must not choose a different one silently.

### 7.2 Aggregation, empty sets, normalization, and rounding decisions

The exact v1 proposal is: collection vocabulary `coverage`/`accuracy`; conflict vocabulary
`TP/FP/FN/precision/recall`; WER/CER as separate ASR metrics; micro aggregation as the only
primary aggregate; no macro output; six fractional decimal places with `ROUND_HALF_EVEN` and
decimal-string serialization; zero denominators as `NOT_MEASURED`; and `NOT_APPLICABLE` only for
deliberately out-of-population metrics. The owner approved this complete proposal on 2026-09-19
as part of `P2T5.OwnerDecisionBundleV3@1.0` (`DECISIONS.md`, resolving OD-6/OD-7); the
implementation must not choose a different value silently.

The following implementation behaviors are required and owner-approved (`OWNER_APPROVED_V3_20260919`):

- Per-case measurements are computed first; aggregate denominators sum only eligible per-case
  numerators/denominators. A missing/empty denominator never becomes zero by coercion.
- Micro aggregation is the only primary aggregate in v1. Macro aggregation is not emitted in v1;
  adding it requires a new owner decision and plan revision.
- The matching normalizer is either the exact B4 rule hash above or a new owner-approved identity;
  no implementation may use the T3 stored-value normalizer as an implicit replacement for the
  approved scoring view.
- Metric outputs use six fractional decimal places with `ROUND_HALF_EVEN` and are serialized as
  decimal strings. Raw binary float repr is forbidden.
- Fixture latency is disabled: it is `NOT_APPLICABLE` with reason
  `FIXTURE_ONLY_LATENCY_DISABLED`; no warm-up, percentile, p95, or wall-clock semantics exist in
  v1.
- The final report contains formulas/eligibility identities, not raw candidate labels or text.

For the proposed v1 metric vocabulary, collection metrics use `coverage` and `accuracy`; they do
not emit precision/recall/F1. Conflict metrics alone use exact-set precision and recall over the
closed key `(reason_code, fused_observation_id)`, include `LOW_CONFIDENCE_EVIDENCE`, and treat
`narration_claim_ref` as descriptive T4 provenance rather than a second key. A split with no
labeled conflict keys is `NOT_MEASURED` with `NO_ELIGIBLE_CASES`; an eligible both-empty case
records zero TP/FP/FN and its undefined ratio as `NOT_MEASURED` with `ZERO_DENOMINATOR`, never as
fabricated zero. Recapture and typed-failure counts use fixture cases as the counting unit, with
one count for each case and each ordered T1 reason/code; adapter-attempt denominators are kept
separate. Schema validity uses one denominator per attempted T2/T3 result and does not count a
T1 `RECAPTURE` as a malformed adapter result. The owner approved these exact values on 2026-09-19
as part of `P2T5.OwnerDecisionBundleV3@1.0` (`DECISIONS.md`, resolving OD-6/OD-7), and they must be
represented by the separate rule identities in section 6.4.

Recording this owner approval is not implementation authority; implementation must not select an
alternative terminology, aggregation, empty-set, rounding, or latency behavior. The remaining
owner decision is approve/reject, not an open-ended design task; the exact proposal is listed in
section 12.

## 8. Reproducibility

### 8.1 Interpreter, dependencies, and lock identity

The current `backend/pyproject.toml` declares `requires-python = ">=3.12,<3.14"` and range-pins
ordinary backend dependencies. No Python lockfile currently exists in the repository.
Historical T4 evidence was produced under the historical CPython 3.13.x range, but the P2-T5
canonical evidence interpreter is pinned to
CPython **3.13.5**.

The planning-base dependency/lock identity is explicit and read-only:

| Artifact | Current byte count | Current raw SHA-256 | Meaning |
|---|---:|---|---|
| `backend/pyproject.toml` | 2,395 | `9ca3a54905d11fdb7f30a84356d23741f256b2115b254bcc9fba4efacdf17df6` | Python project metadata and declared dependency ranges |
| `pnpm-lock.yaml` | 323,917 | `b406b4c36c1e5304cf0c43b175c426d50aa3b43dc9a2bb81be357ea2b80b1665` | Repository frontend/tooling lock identity; not a Python dependency lock |
| Python lockfile (`backend/uv.lock`, `backend/poetry.lock`, or `backend/requirements*.txt`) | absent | no hash | Absence is part of the current binding; it is not silently replaced by the pnpm lock |

The current Python lock identity is exactly `NO_PYTHON_LOCKFILE`. This task does not create a
Python lockfile. The read-only selected direct distribution/version set observed in the existing
CPython 3.13.5 environment is:

- base: `alembic==1.20.0`, `boto3==1.43.95`, `fastapi==0.141.1`, `httpx2==2.13.0`,
  `pydantic==2.13.5`, `pydantic-settings==2.15.0`, `psycopg==3.3.5`, `redis==6.4.0`,
  `rq==2.12.0`, `sqlalchemy==2.0.54`, `structlog==25.5.0`, `uvicorn==0.53.0`;
- development: `mypy==1.20.2`, `pytest==8.4.2`, `pytest-asyncio==1.4.0`, `ruff==0.16.7`;
- selected optional image admission extra: `av==18.1.0`;
- unselected protected ASR/Vision extras: no `faster-whisper`, `ctranslate2`, `accelerate`,
  `qwen-vl-utils`, `torch`, or `transformers` distribution is selected in this environment.

This selected set is a planning-base observation, not a lockfile and not an installation
authorization. Its use as the canonical P2-T5 dependency/version set remains
`OWNER DECISION REQUIRED`; no resolved transitive set is inferred from the range declarations.

The owner decision bundle freezes only the PRE-G1 policy: CPython `3.13.5`, no new dependencies,
dependency installation `NOT AUTHORIZED`, the raw `backend/pyproject.toml` identity, and
`lock_identity=NO_PYTHON_LOCKFILE`. It does not freeze the planning-base observed package/version
set, and no exact installed package/version set is inferred from range declarations at PRE-G1.

At G2, the implementation approval record must materialize the exact installed interpreter and
package/version set actually used, capture the exact sanitized configuration identity, and bind the
resulting dependency/environment identity in the G2 approval record. That identity must not be
inferred from range declarations.

At G6, the parent and candidate runs must use exactly the G2-bound interpreter, package/version
set, sanitized configuration identity, lock identity, and permitted fixture state. G6 must reuse the
exact G2-bound dependency/environment identity; it may not re-resolve, upgrade, install, substitute,
or silently replace a dependency. Any mismatch is an environment/baseline failure, not a valid
comparison.

Once G2 materializes and binds it, the canonical P2-T5 Python execution identity is exactly
`backend/pyproject.toml` raw SHA-256 + CPython implementation/version + exact selected package/version
set + `NO_PYTHON_LOCKFILE` (plus any owner-approved wheel/source hashes if a future lock later
supplies them). `pnpm-lock.yaml` is excluded from Python execution identity unless frontend tooling
is proven to participate in the harness and a new owner-approved identity explicitly adds it. A run
cannot claim a dependency lock hash for an absent Python lockfile, and creating or changing one is a
new owner decision rather than an implied implementation step.

The proposal is to require CPython **3.13.5** for a canonical P2-T5 run. Any other interpreter,
including another 3.13 patch release, must be labelled `NON_CANONICAL_ENVIRONMENT` and cannot
produce G6/G7/G8 closeout evidence without a separately approved environment exception. The exact
interpreter identity (`implementation`, `version`, and executable-independent provenance) must be
captured without leaking host paths. This pin is a P2-T5 evidence rule, not a change to
`pyproject.toml` or a dependency-install authorization.
P2-T5 v1 adds no dependency and performs no installation. The report must bind the raw SHA-256 of
`backend/pyproject.toml`, the exact G2-bound dependency-version set, and
`lock_identity=NO_PYTHON_LOCKFILE`. The `pnpm-lock.yaml` SHA may be recorded as a separate
repository-tooling observation, but it is excluded from Python execution identity unless frontend
tooling is proven to participate in the harness and separately approved. Creating a lockfile or
changing dependency pins is outside this plan unless separately approved.

### 8.2 Stable identity and serialization

The proposed `P2T5-REPORT-CANONICAL-JSON-V1` rules are fully specified in section 5.5:
UTF-8 JSON; `ensure_ascii=false`; `sort_keys=true`; compact `separators=(",", ":")`;
`allow_nan=false`; explicit semantic array ordering; six-place decimal strings with half-even
rounding; retained nullable values; UTC datetimes with six fractional digits; and separate stable
and volatile regions. `run.executed_at` is a caller-injected stable input because it is passed to
T4 and affects the T4 canonical digest. The exact volatile fields are the two run times, stage
durations, harness overhead, and timing sample counts; temporary locations, process identities,
host observations, and execution diagnostics are not report fields at all. The resulting UTF-8 core bytes produce
`deterministic_core_sha256`; the complete report's raw-file SHA-256 and Git blob ID remain
separate external bindings. No wall-clock timestamp may create a run ID or fixture/oracle hash.
The complete field-by-field digest domains are the table in section 5.6. T4 typed source/result
digests use existing P2T4-CANONICAL-JSON-V1 only where that table names it; report/core and
case-outcome digests use their distinct P2-T5 domains, and no generic digest field may be emitted
without an exact domain row.

### 8.3 Deterministic fixture adapter and rerun parity

The existing P2 fake adapters are deterministic, dependency-free, and use fixed fixture behavior;
their fixed adapter timestamps and profile/config identities are part of the input implementation
identity. P2-T5 must not alter them to make a live path available. The future harness must:

1. load identical case bytes and media hashes;
2. use identical fake profile/catalog/policy identities;
3. inject the same `run_id` and `executed_at`;
4. run with no network, model/cache variables, provider credentials, or ignored model files; and
5. compare canonical report bytes, case outcome hashes, typed counts, and stable measurements.

Any difference is a parity failure requiring diagnosis; it is not repaired by changing the oracle.
Fixture output is evidence of harness behavior only and must remain separate from any future live
evidence.

### 8.4 Clean-run and environment capture

A clean run means a fresh checkout at the approved implementation commit, with only the explicitly
approved synthetic/licensed fixture package available, no `backend/.asr.env`, no `backend/.vision.env`,
no model/cache environment values, no downloaded weights, no provider credentials, no network, and
**CPython 3.13.5** plus the owner-approved dependency identity. Environment capture is a sanitized
object with Python implementation/version, allowlisted package versions, `backend/pyproject.toml`
hash, lockfile state, runner version, and platform-independent policy values. It must not include
`os.environ`, usernames, hostnames, current working directory, drive paths, or validator `root=`
lines. If CPython 3.13.5 is unavailable, the run is `NON_CANONICAL_ENVIRONMENT` and cannot satisfy
G6 evidence.

### 8.5 T5 baseline disposition (`OWNER_APPROVED_V3_20260919`)

The only inherited architecture baseline in the P2-T5 comparison is exactly
ARCHITECTURE-POLICY-B-BASELINE-001 at backend/src/sketch2life/application/services/backend_ai_workflow.py
with finding application imports an outer layer and validator SHA-256
fa236c8d389b608251153d601fc370efe3f3e2479446ca4a56a3d395f892e0b5.

```text
ARCHITECTURE-POLICY-B-BASELINE-001
file: backend/src/sketch2life/application/services/backend_ai_workflow.py
finding: application imports an outer layer
validator SHA-256: fa236c8d389b608251153d601fc370efe3f3e2479446ca4a56a3d395f892e0b5
```

P2-T5 inherits the current G9 baseline; it does not repair, suppress, or reinterpret unrelated
findings. The comparison topology is ordered and role-specific: **G2 binds the immutable
implementation-parent baseline; G3 implements only the G2-approved paths in the working tree; G4
independently reviews that exact uncommitted working tree/diff; G5 commits exactly the G4-reviewed
bytes and paths after proving zero drift; and G6 compares that exact G5 candidate against the
G2-bound parent**. G2 does not bind a future candidate, and G5 does not replace the parent baseline.
The G6 comparison must use the **same CPython 3.13.5 interpreter,
dependency and lockfile state, configuration, and available ignored fixture state** on both sides.
A finding is `INHERITED_BASELINE` only when its exact fingerprint (test node/file/line/exception,
mypy file/line/code/message, Ruff path/line/code/message, or architecture rule/file/count) appears
on both sides. Counts alone, matching prose, or a different environment do not prove inheritance.
Any candidate-only fingerprint is `P2T5_NEW_FINDING` and blocks the checkpoint. The exact inherited
finding identities proposed for the T5 comparison are:

| Finding fingerprint | Exact inherited location/details | T5 disposition |
|---|---|---|
| `ARCHITECTURE-POLICY-B-BASELINE-001` | `backend/src/sketch2life/application/services/backend_ai_workflow.py`; one `application imports an outer layer` finding; validator SHA-256 `fa236c8d389b608251153d601fc370efe3f3e2479446ca4a56a3d395f892e0b5` | Preserve exactly one finding and report the architecture result truthfully as `ARCHITECTURE_INVALID`. |
| `MYPY-BASELINE-001` | `backend/src/sketch2life/application/services/learning_media_resolver.py:101` (`arg-type`): Argument "reason_code" to "LearningMediaResultV1" has incompatible type "str"; expected "Literal['CACHE_MISS', 'STALE_MEDIA', 'CORRUPT_MEDIA', 'UNSAFE_MEDIA', 'RENDERER_FAILURE', 'MEDIA_UNAVAILABLE', 'PROVIDER_TIMEOUT'] | None"__; `backend/src/sketch2life/application/services/learning_media_fallback.py:82` (`arg-type`): Argument "fallback_type" to "LearningMediaResultV1" has incompatible type "str"; expected "Literal['STILL_NARRATION', 'WHOLE_IMAGE_REVEAL', 'SUPERVISED_HANDOFF'] | None"__; `backend/src/sketch2life/application/services/learning_media_fallback.py:85` (`arg-type`): Argument "reason_code" to "LearningMediaResultV1" has incompatible type "str"; expected "Literal['CACHE_MISS', 'STALE_MEDIA', 'CORRUPT_MEDIA', 'UNSAFE_MEDIA', 'RENDERER_FAILURE', 'MEDIA_UNAVAILABLE', 'PROVIDER_TIMEOUT'] | None"__ | Inherited and unchanged; outside the P2-T5 allowlist; no fix or suppression. |
| `RUFF-BASELINE-001` | `backend/src/sketch2life/contracts/schemas/learning_media.py:79` (`E501`): Line too long (103 > 100); `backend/tests/unit/test_learning_media_scenario_matrix.py:1` (`I001`): Import block is un-sorted or un-formatted; `backend/tests/unit/test_learning_media_scenario_matrix.py:14` (`E501`): Line too long (121 > 100) | Inherited and unchanged; outside the P2-T5 allowlist; no fix or suppression. |
| `FEAT-018-TIMING-001` | `backend/tests/unit/test_feat018_live_lightning_execution.py::test_repeated_fake_execution_is_deterministic_and_does_not_add_an_outer_attempt`; observed non-stable field `adapter_wall_clock_ms`; the other 20 fields match | Pre-existing/out-of-scope for P2-T5; no fix, rerun, or reclassification here. |

The exact G6 fingerprint tuple is typed by diagnostic family. For Mypy and Ruff it is
`(repository-relative-path, line, diagnostic_code, exact_message_text)`. For architecture it is
`(validator_identity, rule, repository-relative-path, exact_finding_text)`. The FEAT-018 tuple is
`(test_node, nonstable_field, disposition)`. Message text is therefore part of the Mypy/Ruff
identity in this V3 decision bundle, while the architecture finding text is always exact.

```text
ARCHITECTURE-POLICY-B-BASELINE-001
  (validator_identity=python tools/validate_architecture.py,
   rule=ARCHITECTURE-POLICY-B-BASELINE-001,
   path=backend/src/sketch2life/application/services/backend_ai_workflow.py,
   exact_finding_text=application imports an outer layer,
   validator_sha256=fa236c8d389b608251153d601fc370efe3f3e2479446ca4a56a3d395f892e0b5)
MYPY-BASELINE-001
  (path=backend/src/sketch2life/application/services/learning_media_resolver.py, line=101,
   code=arg-type,
   message=Argument "reason_code" to "LearningMediaResultV1" has incompatible type "str"; expected "Literal['CACHE_MISS', 'STALE_MEDIA', 'CORRUPT_MEDIA', 'UNSAFE_MEDIA', 'RENDERER_FAILURE', 'MEDIA_UNAVAILABLE', 'PROVIDER_TIMEOUT'] | None")
  (path=backend/src/sketch2life/application/services/learning_media_fallback.py, line=82,
   code=arg-type,
   message=Argument "fallback_type" to "LearningMediaResultV1" has incompatible type "str"; expected "Literal['STILL_NARRATION', 'WHOLE_IMAGE_REVEAL', 'SUPERVISED_HANDOFF'] | None")
  (path=backend/src/sketch2life/application/services/learning_media_fallback.py, line=85,
   code=arg-type,
   message=Argument "reason_code" to "LearningMediaResultV1" has incompatible type "str"; expected "Literal['CACHE_MISS', 'STALE_MEDIA', 'CORRUPT_MEDIA', 'UNSAFE_MEDIA', 'RENDERER_FAILURE', 'MEDIA_UNAVAILABLE', 'PROVIDER_TIMEOUT'] | None")
RUFF-BASELINE-001
  (path=backend/src/sketch2life/contracts/schemas/learning_media.py, line=79,
   code=E501, message=Line too long (103 > 100))
  (path=backend/tests/unit/test_learning_media_scenario_matrix.py, line=1,
   code=I001, message=Import block is un-sorted or un-formatted)
  (path=backend/tests/unit/test_learning_media_scenario_matrix.py, line=14,
   code=E501, message=Line too long (121 > 100))
FEAT-018-TIMING-001
  (pytest, backend/tests/unit/test_feat018_live_lightning_execution.py::test_repeated_fake_execution_is_deterministic_and_does_not_add_an_outer_attempt,
   observed_non_stable_field=adapter_wall_clock_ms,
   disposition=PRE_EXISTING_OUT_OF_SCOPE_FOR_P2_T5)
```

The architecture tuple is exact only when all four architecture lines above match. The mypy,
Ruff, and FEAT-018 tuples are exact node/code/field identities, not finding counts.

The proposed T5 zero-new-finding rule is set equality: after the approved P2-T5 change, the
architecture finding set must contain exactly `ARCHITECTURE-POLICY-B-BASELINE-001` above and no new
finding. A validator result of `ARCHITECTURE_INVALID` is expected with
ARCHITECTURE-POLICY-B-BASELINE-001 at backend/src/sketch2life/application/services/backend_ai_workflow.py
for finding application imports an outer layer with validator SHA-256
fa236c8d389b608251153d601fc370efe3f3e2479446ca4a56a3d395f892e0b5;
it must not be relabelled `ARCHITECTURE_VALID`, `PASS`, or "no findings". Any additional
architecture, mypy, Ruff, timing, privacy, or import finding is a new finding and fails the T5
checkpoint. The P2-T5 implementation allowlist must not include any inherited-baseline file, and
no unrelated baseline file may be fixed merely to make the validation output green.

The G6 gate verdict vocabulary is closed and separate from individual validator outputs:

| G6 verdict | Exact meaning |
|---|---|
| `PASS` | Parent and candidate are fully clean across every approved test, type, lint, architecture, hash, privacy, scope, and parity check. |
| `PASS_WITH_ACCEPTED_BASELINE_FINDINGS` | There are zero candidate-only findings, and the only remaining findings are the exact owner-accepted inherited fingerprints bound by G2 and reproduced unchanged on both parent and candidate. |
| `FAIL` | Any candidate-only test, type, lint, architecture, hash, privacy, scope, or G4/G5 parity finding exists; an unbound or changed baseline fingerprint also fails. |

While `ARCHITECTURE-POLICY-B-BASELINE-001` exists for
`backend/src/sketch2life/application/services/backend_ai_workflow.py` with finding
`application imports an outer layer` and validator SHA-256
`fa236c8d389b608251153d601fc370efe3f3e2479446ca4a56a3d395f892e0b5`, the architecture command
must still report `ARCHITECTURE_INVALID`. A successful G6 may therefore be
`PASS_WITH_ACCEPTED_BASELINE_FINDINGS`; the architecture output itself is never rewritten as
`PASS`.

## 9. Architecture and implementation boundary

### 9.1 Responsibilities and data flow

```mermaid
flowchart LR
    CLI[interfaces/cli/p2_t5_evaluation.py] --> APP[application/services/p2_t5_evaluation.py]
    APP --> T1[existing T1 validator]
    APP --> ASR[AsrPort]
    APP --> VISION[VisionUnderstandingPort]
    APP --> T4[existing p2_t4_fusion boundary]
    COMP[fixture composition/loader] --> ASR
    COMP --> VISION
    APP --> SCORE[application/services/p2_t5_scoring.py]
    ORACLE[(hand-authored expected-v1.json)] --> SCORE
    SCORE --> REPORT[P2T5.P2T5EvaluationReportV1@1.0]
```

The CLI is an interface/composition root: parse safe relative paths, select the literal fixture
mode, compose the existing fake adapters, and call the application service. The application
service owns the use-case ordering and depends on `AsrPort`/`VisionUnderstandingPort`, T1/T4
contract types, and a deterministic clock/value supplied by the caller. It must not import provider
SDKs, model runtimes, HTTP routers, settings, storage, or read files. The scorer is pure over
validated case summaries and a read-only oracle; it must not call adapters or rewrite fixtures.
Infrastructure owns file/hash loading and fake-adapter composition. Contracts own Pydantic/schema
validation only. No domain module is changed or made provider-aware.

### 9.2 Proposed exact future implementation allowlist

The following paths are proposals for a future, separately approved implementation. Their parent
directories were verified to exist; the files themselves do not currently exist unless noted.
Approval must name each path individually; no wildcard or directory approval is valid.
The proposed implementation/test/fixture/media inventory has exactly 54 concrete paths: 10
source/test paths, 4 fixture/oracle JSON paths, and 40 media paths. This 54-path count is a
proposed planning invariant only; it remains unapproved until G2 separately names the exact
implementation, test, fixture, and media paths. It is not evidence authority.

| Future path | Role | Current state |
|---|---|---|
| `backend/src/sketch2life/contracts/schemas/p2_t5_evaluation.py` | P2-T5 manifest/run/case/report/measurement/failure schemas | Absent; `contracts/schemas/` exists |
| `backend/src/sketch2life/application/services/p2_t5_evaluation.py` | T1→fake T2/T3→T4 orchestration and redacted case summaries | Absent; `application/services/` exists |
| `backend/src/sketch2life/application/services/p2_t5_scoring.py` | Pure matching, aggregate metrics, and oracle comparison | Absent; `application/services/` exists |
| `backend/src/sketch2life/infrastructure/ai/p2_t5_fixture_loader.py` | Relative-path/hash loader plus the fixture-only in-memory T4 composition seam; it resolves only the closed mutation categories in section 3.3 after fake-adapter output and before validate_and_fuse | Absent; `infrastructure/ai/` exists |
| `backend/src/sketch2life/interfaces/cli/p2_t5_evaluation.py` | Argument parsing, safe output, and CLI composition root | Absent; `interfaces/cli/` exists |
| `backend/tests/contract/test_p2_t5_evaluation_contract.py` | Hand-authored schema/parity oracle for P2-T5 wrappers | Absent; `tests/contract/` exists |
| `backend/tests/unit/test_p2_t5_evaluation.py` | Stage ordering, typed outcomes, split and report behavior | Absent; `tests/unit/` exists |
| `backend/tests/unit/test_p2_t5_scoring.py` | Independent metric/matching tests and oracle cases | Absent; `tests/unit/` exists |
| `backend/tests/unit/test_p2_t5_cli.py` | CLI input/output/exit-code and no-live-import tests | Absent; `tests/unit/` exists |
| `backend/tests/unit/test_p2_t5_privacy.py` | Path/environment/raw-output privacy sentinel | Absent; `tests/unit/` exists |

Every source and test row in this table is labelled `PROPOSED_PATH_ALLOWLIST` for planning only;
no row is authorized, and no unlisted source, test, helper, generated file, or package path may be
created without a later exact-path approval.

The proposal does not authorize changing `backend/pyproject.toml`, adding a package entrypoint,
editing `__init__.py`, or modifying existing fake adapters. If packaging requires one of those
paths, it is a new owner decision and a new exact allowlist item.

### 9.3 Proposed exact fixture allowlist

The future tracked fixture allowlist is limited to the four package files in section 6.1 plus the
following 40 explicitly named media files if media bytes are selected by the owner:

Each of the 40 following path literals is individually labelled `PROPOSED_PATH_ALLOWLIST` — not
authorized. The fixture package, media directory, and every media file are absent; no media or
fixture is created by this task.

```text
features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-dev-001.png
features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-dev-001.wav
features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-dev-002.png
features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-dev-002.wav
features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-dev-003.png
features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-dev-003.wav
features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-dev-004.png
features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-dev-004.wav
features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-dev-005.png
features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-dev-005.wav
features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-dev-006.png
features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-dev-006.wav
features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-dev-007.png
features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-dev-007.wav
features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-dev-008.png
features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-dev-008.wav
features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-dev-009.png
features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-dev-009.wav
features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-dev-010.png
features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-dev-010.wav
features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-dev-011.png
features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-dev-011.wav
features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-dev-012.png
features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-dev-012.wav
features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-heldout-001.png
features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-heldout-001.wav
features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-heldout-002.png
features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-heldout-002.wav
features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-heldout-003.png
features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-heldout-003.wav
features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-heldout-004.png
features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-heldout-004.wav
features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-heldout-005.png
features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-heldout-005.wav
features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-heldout-006.png
features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-heldout-006.wav
features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-heldout-007.png
features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-heldout-007.wav
features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-heldout-008.png
features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-heldout-008.wav
```

The path audit is the literal-set equation `10 source/test + 4 fixture/oracle JSON + 40 media =
54 proposed paths`. The ten source/test rows are exactly the five `p2_t5_*.py` source paths and
five `test_p2_t5_*.py` paths in section 9.2; the four JSON rows are exactly the four package paths
in section 6.1; and the media set is exactly the 40 literals above. No directory wildcard,
unlisted helper, generated artifact, README, evidence file, or `<run-id>` template is included in
the 54-path count or authorized by it.

The owner decision bundle may approve this 54-path inventory only as a planning invariant. It
does not authorize any path. The later immutable plan checkpoint records the exact 54 literals,
and G2 must repeat each approved implementation/test/fixture/media path individually. A count-only
statement can never substitute for the exact path allowlist.

The paths above are future placeholders, not files created by this planning task. If the approved
fixture design uses scripted byte references without media files, the approval must explicitly
remove the media entries and define why T1 validation remains covered. It may not silently substitute
existing fixtures.

### 9.4 Protected paths and import boundary

The future P2-T5 modules must not import or transitively select these live/runtime paths:

```text
backend/src/sketch2life/infrastructure/ai/faster_whisper_asr.py
backend/src/sketch2life/infrastructure/ai/faster_whisper_runtime_config.py
backend/src/sketch2life/infrastructure/ai/qwen_vision.py
backend/src/sketch2life/infrastructure/ai/qwen_vision_environment_readiness.py
backend/src/sketch2life/infrastructure/ai/qwen_vision_runtime_config.py
backend/src/sketch2life/infrastructure/ai/lightning_client.py
backend/src/sketch2life/infrastructure/understanding/whisper_adapter.py
backend/src/sketch2life/infrastructure/understanding/qwen3_vl_adapter.py
backend/src/sketch2life/interfaces/cli/workflow_demo.py
backend/src/sketch2life/interfaces/http/routers/live_understanding.py
```

The import-boundary test must inspect the exact future module allowlist and fail on provider SDK
names, model/runtime modules, HTTP clients, environment-secret access, or any protected path. It
must also prove that a non-`fixture` provider is rejected before protected modules are imported.
The architecture validator's existing single ARCHITECTURE-POLICY-B-BASELINE-001 baseline at
backend/src/sketch2life/application/services/backend_ai_workflow.py for finding application imports
an outer layer with validator SHA-256 fa236c8d389b608251153d601fc370efe3f3e2479446ca4a56a3d395f892e0b5
is not sufficient proof of this P2-T5-specific boundary. Every path in the protected list above is labelled
`PROTECTED_OUT_OF_SCOPE` — not a P2-T5 allowlist item and not authorized.

### 9.5 Exact path classes and privacy separation (`PROPOSED_PATH_ALLOWLIST`)

The path classes are disjoint and remain proposals, never authorization:

| Path class | Exact scope | Status and permitted material |
|---|---|---|
| Source | The five `backend/src/.../p2_t5_*` paths in section 9.2 | `PROPOSED_PATH_ALLOWLIST` — future code only; not authorized |
| Tests | The five `backend/tests/.../test_p2_t5_*` paths in section 9.2 | `PROPOSED_PATH_ALLOWLIST` — future tests only; not authorized |
| Fixture/oracle package | The four exact `fixtures/p2-t5-evaluation-v1/{manifest-v1.json,cases-v1.json,expected-v1.json,matching-rule-v1.json}` paths in section 6.1 | `PROPOSED_PATH_ALLOWLIST` — future metadata, oracle, and rule JSON only; not authorized |
| Media | The 40 individually enumerated `.png`/`.wav` paths in section 9.3 | `PROPOSED_PATH_ALLOWLIST` — synthetic media only if separately approved; not authorized |
| Evidence | The `<run-id>` filename templates in section 10.1 | `PROPOSED_NAME_TEMPLATE` — naming proposals only; never G2 authority, not authorized, and not concrete paths |

The privacy boundary is invariant across the future flow: only the exact synthetic fixture package
may contain media bytes and bounded hand-authored reference/label fields; report JSON may contain
only redacted identities, hashes, closed statuses, measurements, and limitations; evidence may
contain only authorized redacted summaries plus external provenance bindings. No report, evidence,
review, log, CLI stream, or ignored run file becomes a second fixture/oracle store. The evidence
templates remain names only, and a later exact-path G7 authorization must repeat this boundary.

Synthetic media may exist only at the 40 exact media paths in section 9.3. Synthetic reference
transcripts may exist only as explicitly bounded fixture/oracle fields in the exact
`cases-v1.json` and `expected-v1.json` paths in the fixture package; they may not be added to a
new transcript file, report, run directory, evidence record, log, exception, or CLI stream. The
manifest and matching-rule JSON are metadata/rule paths and are not a transcript sink.

The CLI and future runtime output must never copy or persist media bytes, reference transcripts,
`transcript_raw`, segment or word text, Vision labels/text, prompts, provider/model payloads,
credentials, secrets, endpoints, raw exception messages, stack traces, usernames, hostnames,
environment-variable values, child data, or absolute paths. This prohibition applies equally to
`tmp/p2-t5-runs/<run-id>/` files, `tmp/p2-t5-notes/`, report JSON, case summaries, evidence
summaries, logs, exception text, stdout, and stderr. Paths must be repository-relative POSIX
references only; drive-letter, rooted, UNC, home, traversal, symlink-escape, and validator
`root=` output are rejected or redacted. Standard output/error remains the closed status/failure
token contract from section 4.5. The existing repository security validator is not sufficient by
itself; a P2-T5 privacy sentinel must scan every generated artifact. A report, evidence record, or
review record must not contain its own final raw-file SHA-256 or Git blob ID; those identities are
computed and reported by an external paired review/checkpoint. Self-hash and self-blob fields are
rejected even when the value is otherwise correct.

## 10. Evidence and approval sequence

### 10.1 Persistence rules

Before evidence authorization, runtime material is ignored local output only:

```text
tmp/p2-t5-runs/<run-id>/report.json
tmp/p2-t5-runs/<run-id>/case-summaries.json
tmp/p2-t5-runs/<run-id>/environment.json
tmp/p2-t5-runs/<run-id>/stdout.txt
tmp/p2-t5-runs/<run-id>/stderr.txt
tmp/p2-t5-notes/<note>.md
```

These local paths may contain only hash/status summaries and sanitized structured diagnostics. They
are never final evidence by default and must not copy raw fixture/oracle data. They must not contain
credentials, secrets, endpoints, raw
provider/model output, prompts, raw exceptions, full transcripts, unapproved labels, real child
data, host paths, usernames, hostnames, or environment-variable values.

The future evidence names below are `<run-id>` naming templates only. Every concrete evidence path
requires a separate exact-path authorization naming the literal run ID, file, commit, Git blob,
and raw SHA-256; none is authorized or created by this task:

```text
features/FEAT-003-multimodal-understanding/evidence/P2_T5_G4_INDEPENDENT_CANDIDATE_REVIEW_<run-id>.md
features/FEAT-003-multimodal-understanding/evidence/P2_T5_G5_IMPLEMENTATION_CHECKPOINT_<run-id>.md
features/FEAT-003-multimodal-understanding/evidence/P2_T5_G6_CHECKPOINT_FIXTURE_VERIFICATION_<run-id>.json
features/FEAT-003-multimodal-understanding/evidence/P2_T5_G6_CHECKPOINT_FIXTURE_VERIFICATION_<run-id>.md
features/FEAT-003-multimodal-understanding/evidence/P2_T5_G7_EVIDENCE_CREATION_<run-id>.json
features/FEAT-003-multimodal-understanding/evidence/P2_T5_G7_EVIDENCE_CREATION_<run-id>.md
features/FEAT-003-multimodal-understanding/evidence/P2_T5_G8_INDEPENDENT_EVIDENCE_REVIEW_<run-id>.md
features/FEAT-003-multimodal-understanding/evidence/P2_T5_G9_GOVERNANCE_CLOSEOUT_<run-id>.md
```

Every template line above is a `PROPOSED_NAME_TEMPLATE` only; it is a naming proposal, never G2
authority and not a concrete evidence authorization. The evidence class is separate from source,
test, fixture, and media classes. G7 must separately name each exact evidence path, and the literal
`<run-id>` token must never be committed as if it were a real run.

The owner decision bundle and G1 may freeze only these naming templates and the evidence-path
authorization policy. They must not substitute a run ID, enumerate a future concrete G7 path, or
pre-authorize any `<run-id>` expansion. G4/G5/G6 work remains in sanitized ignored local records
until a later G7 exact-path authorization permits publication; the templates above do not create a
tracked record before G7.

The JSON report may be published only if its evidence authorization explicitly permits machine
output. A Markdown summary may contain scope, exact contract identities, fixture/split counts,
raw hashes, typed-status counts, measurement states, command references made repository-relative,
reviewer, interpretation, and limitations. It must not contain raw media, raw ASR transcript, raw
Vision/model/provider output, prompts, labels unless a bounded synthetic field is explicitly
approved, credentials, endpoints, absolute paths, or child-related content.

Every future evidence record must bind the exact plan revision, implementation commit, Git blob
ID, raw-file SHA-256, fixture manifest/cases/expected hashes, matching-rule hash, T4 freeze/package
tuple, environment/dependency identity, command, timestamp, reviewer, interpretation, and
limitations. A normalized digest may be used only with the full-line-match method accepted by the
P2-T4 digest-binding erratum; raw-byte hash and Git object identity remain mandatory.

### 10.2 Required pre-G1 checkpoint and G1-G9 topology

The current position is `PRE-G1`. The topology below is a proposal for the owner decision bundle;
this task does not create the plan checkpoint, an approval record, an implementation checkpoint,
an evidence checkpoint, or any G1-G9 gate:

```text
owner reviews and selects exact values
-> decisions are recorded
-> both plans are synchronized
-> independent technical post-sync review: PASS
-> independent governance/privacy post-sync review: PASS
-> PLAN CANDIDATE CHECKPOINT
-> READY_FOR_OWNER_PLAN_APPROVAL
-> G1 plan-approval record commit
-> G2 exact implementation-approval record commit
-> [no intermediate tracked commits]
-> G3 fixture-only implementation in the working tree
-> G4 independent review of that same uncommitted working tree/diff
-> G5 implementation checkpoint commit
-> G6 parent/candidate verification
-> G7 exact evidence authorization record commit
-> G7 evidence creation
-> G7 evidence checkpoint commit
-> G8 independent review of the exact G7 checkpoint
-> G8 review checkpoint commit
-> G9 governance-only closeout
```

The parent `PLAN.md` repeats this topology non-normatively. Neither occurrence grants an approval,
creates a checkpoint, or authorizes implementation/evidence work.

#### Pre-G1 plan candidate checkpoint

The plan candidate checkpoint may be created only after both post-sync reviews report `PASS`. It
must commit exactly these two synchronized plan files and no other path:

```text
features/FEAT-003-multimodal-understanding/plan/PLAN.md
features/FEAT-003-multimodal-understanding/plan/P2_T5_EVALUATION_HARNESS_PLAN.md
```

The checkpoint commit must contain no approval/governance record, code, test, fixture, media, or
evidence file. After it is created, the executor records the checkpoint commit SHA and, for each
plan, its repository path, revision, raw SHA-256, and Git blob ID. Because a commit cannot embed its
own final SHA, that immutable tuple is reported after checkpoint creation and copied into the later
G1 approval record without amending either plan. The checkpoint is not an approval. This
documentation task describes it but must not create it.

#### Gate definitions and immutable commit topology

1. **G1 — Owner plan approval record commit.** G1 must bind the complete owner decision bundle to
   the exact plan-checkpoint tuple: checkpoint commit SHA plus each plan path, revision, raw
   SHA-256, and Git blob ID. G1 freezes evidence naming templates and the evidence authorization
   policy only; it must not substitute `<run-id>`, name a concrete future evidence path, or
   pre-authorize any G7 artifact. `parent(G1 approval record commit)` must equal the plan candidate
   checkpoint. G1 does not authorize G2, G3, implementation, fixtures/media, or evidence.
2. **G2 — Exact implementation approval record commit.** G2 must be a separate commit whose direct
   parent is the G1 approval-record commit. It names only exact implementation/test/fixture/media
   paths and binds all of the following:
   - `implementation_parent_commit`, defined as the resulting G2 approval-record commit and reported
     after commit creation without self-referential tracked-file editing;
   - CPython `3.13.5`;
   - raw SHA-256 of `backend/pyproject.toml`;
   - the exact dependency/version identity selected by the owner;
   - lock identity `NO_PYTHON_LOCKFILE`;
   - validator identities, including exact path, source commit, Git blob ID, and raw SHA-256 for
     every approved repository validator plus the approved test/type/lint command identities;
   - the exact owner-accepted inherited baseline fingerprints from section 8.5; and
   - relevant configuration identities: upstream contract/profile catalogs, fake-adapter profiles,
     T4 policy/hash, matching/normalization/scoring rules, manifest/oracle identities, report
     canonicalization, and privacy/import-boundary configuration selected by the owner.
   G2 authorizes no evidence path. Every concrete G7 evidence path requires later exact-path
   approval. P2-T5 remains fixture-only; live/runtime/provider/model/GPU/Lightning/network work is
   not authorized.
3. **No intermediate tracked commits.** From the G2 approval-record commit through G4, HEAD remains
   the G2 commit. No tracked commit may occur before G5. This makes the required identity exact:
   `parent(G5) = G2 exact implementation-approval record commit`.
4. **G3 — Fixture-only implementation in the working tree.** Create or edit only G2-named paths,
   with no dependency installation, model/cache files, network, provider import, production wiring,
   evidence creation, or commit.
5. **G4 — Independent uncommitted-candidate review.** A reviewer/session distinct from the
   implementation author reviews the exact uncommitted G3 working tree and its diff from the G2
   commit. G4 is not a commit review. Its sanitized ignored local record binds the complete path
   set, raw SHA-256 and prospective Git blob ID for every candidate file, diff identity, fixture/
   oracle hashes, and scope/import/privacy/contract findings. Any edit after G4 invalidates the G4
   result and requires a fresh independent G4 review.
6. **G5 — One implementation checkpoint commit.** Only after G4 reports `PASS`, commit exactly the
   bytes and paths reviewed at G4 in one checkpoint. Before treating G5 as bound, compare every G4
   path/raw-hash/blob tuple with the committed G5 tree and prove zero byte drift, zero path drift,
   and no unreviewed file. `parent(G5)` must equal the G2 approval-record commit. Any mismatch is a
   G5 failure and requires returning to G4; it cannot be waived as formatting or checkpoint work.
7. **G6 — Parent/candidate verification.** Compare the exact G5 checkpoint with its G2 parent under
   the identical G2-bound interpreter, dependency/lock, validator, configuration, baseline, and
   fixture state. Run the approved tests, type/lint checks, privacy/import checks, deterministic
   parity checks, hash/scope checks, and repository validators. Emit exactly one gate verdict from
   section 8.5: `PASS`, `PASS_WITH_ACCEPTED_BASELINE_FINDINGS`, or `FAIL`. The architecture command
   remains `ARCHITECTURE_INVALID` while ARCHITECTURE-POLICY-B-BASELINE-001 at
   backend/src/sketch2life/application/services/backend_ai_workflow.py for finding application imports
   an outer layer with validator SHA-256 fa236c8d389b608251153d601fc370efe3f3e2479446ca4a56a3d395f892e0b5 exists.
8. **G7 — Exact authorization, creation, and evidence checkpoint.** After a successful G6 verdict,
   the owner creates a separately committed exact-path authorization record naming every concrete
   evidence path, literal run ID, permitted content/redactions, evidence author/assembler, and the
   G5/G6 identities. G6 creates no tracked commit, so `parent(G7 authorization record commit)` must
   equal G5 unless a later owner decision explicitly changes that rule. Evidence is then created
   only at the authorized paths and committed once as the G7 evidence checkpoint, direct-parented
   to the G7 authorization-record commit. G7 is a creation/checkpoint gate, not a review verdict.
   Its state is `COMPLETE — EVIDENCE CHECKPOINT BOUND` (or the transient creation state
   `EVIDENCE_CREATED`), never `G7: PASS`.
9. **G8 — Independent evidence review and review checkpoint.** G8 reviews the exact committed G7
   evidence checkpoint, not floating working-tree evidence. The G8 reviewer must be distinct from
   the implementation author, the G4 candidate reviewer, and the G7 evidence author/assembler. Any
   unavoidable exception requires explicit owner approval recorded before G8. After review, commit
   only the authorized G8 review record as the G8 review checkpoint, direct-parented to the G7
   evidence checkpoint; do not alter G7 evidence bytes.
10. **G9 — Governance-only closeout.** G9 may close only after the G8 review checkpoint records a
    passing verdict. `parent(G9 governance closeout commit)` must equal the G8 review checkpoint
    unless a later explicit owner decision changes that rule. G9 may record governance status only;
    it must not change implementation, fixtures, media, or evidence bytes.

G6 validator success does not substitute for the plan checkpoint, G1, G2, G4 parity review, G5,
G7 authorization/checkpoint, G8, or G9. A future live benchmark starts a separate plan/gate
sequence and cannot be attached to these P2-T5 evidence files.

## 11. Acceptance criteria

These are objective criteria for a future approved implementation. All remain unchecked while
this document is `P2-T5 DRAFT — READY_FOR_PRE_G1_PLAN_CHECKPOINT_REVIEW` and implementation
remains not approved:

### CLI and boundary

- [ ] `validate`, `understand --provider fixture`, and `evaluate` accept only the approved
      repository-relative input grammar and produce the exact proposed envelopes.
- [ ] Unsupported provider/mode/model/endpoint requests fail before protected live imports and
      return the approved exit/category pair.
- [ ] Empty, invalid, partial, expected-failure, recapture, T4-rejection, and unexpected-error
      behavior matches section 4; no partial report is mistaken for a valid run.
- [ ] Standard output/error contain only approved bounded status tokens and no privacy-sensitive
      raw data.

### Fixtures and oracle

- [ ] The owner-approved exact count and split are present; every ID is unique, stable,
      feature-qualified, lowercase-compatible with upstream contracts, and hash-bound.
- [ ] Every case has synthetic/non-child or approved licensed provenance, immutable media/case/
      expected hashes, expected T1/T2/T3/T4 outcome, and a coverage tag.
- [ ] The independent hand-authored oracle is created and reviewed before evaluator execution; no
      generator/scorer/implementation path can write expected values.
- [ ] No existing ASR Round-1, Vision B4/v3, P2-T4, FEAT-018, or live fixture/evidence is reused,
      rescored, pooled, or silently adopted.

### Report and metrics

- [ ] The report validates as the owner-approved `P2T5.P2T5EvaluationReportV1@1.0` version and includes
      manifest/oracle/split/profile/policy/environment/case/metric/failure/interpretation fields.
- [ ] T1–T4 identities, T4 canonical hashes, exact statuses, typed rejection fields, and source
      provenance are preserved without new upstream fields or a V2 projection.
- [ ] Schema, recapture, invalid-input, ASR WER/CER, entity/action/relation/theme, conflict, and
      optional overhead metrics use the approved formulas, eligibility, aggregation, empty-set,
      normalizer, percentile, and rounding rules.
- [ ] Every unavailable metric is an explicit typed `NOT_MEASURED` or approved
      `NOT_APPLICABLE`; no missing field or fabricated zero is accepted.

### Reproducibility, privacy, and architecture

- [ ] Two clean runs with identical approved bytes, run ID, injected timestamp, interpreter, and
      config produce byte-identical stable report content and identical case/oracle comparisons.
- [ ] The report and environment capture contain no raw provider/model output, raw exceptions,
      credentials, secrets, absolute paths, host identity, unapproved labels, or real child data.
- [ ] The exact G2 implementation/test/fixture/media paths and separately authorized G7 evidence
      paths are respected; no wildcard,
      generated, route, schema-mutation, or protected live path changes appear.
- [ ] The application service imports ports/contracts only; infrastructure composes fake adapters;
      CLI does not import live provider/model modules; no FEAT-018/FEAT-020 wiring exists.

### Evidence and validation

- [ ] Focused and full validation outputs are recorded at the authorized future paths with exact
      command, environment identity, input/reference, output, timestamp, reviewer, interpretation,
      and limitations.
- [ ] `git diff --check`, `python tools/validate_harness.py`,
      `python tools/validate_repository_security.py`, `python tools/validate_skeleton.py`, and
      `python tools/validate_architecture.py` are reported truthfully; the only permitted architecture
      finding is ARCHITECTURE-POLICY-B-BASELINE-001 at
      backend/src/sketch2life/application/services/backend_ai_workflow.py for finding application imports
      an outer layer with validator SHA-256 fa236c8d389b608251153d601fc370efe3f3e2479446ca4a56a3d395f892e0b5.
- [ ] Evidence binds the approved plan/implementation/fixture/T4 identities and is independently
      reviewed before closeout.
- [ ] No acceptance item is interpreted as live/runtime/model/provider/production approval.

## 12. Open owner decisions and risks

### 12.1 IMPLEMENTATION-BLOCKING OWNER DECISIONS

Each item below requires an explicit decision record before P2-T5 implementation approval. The
fixture-only v1 may not proceed to implementation approval until these blocking choices are
resolved.

The owner approved `P2T5.OwnerDecisionBundleV3@1.0` on 2026-09-19 (`DECISIONS.md`), which resolves
OD-2 through OD-13, OD-16, OD-19, and OD-20 exactly as stated in section 12.1.1/12.1.2 below. The
decision status for those rows is now `OWNER_APPROVED_V3_20260919`. OD-14 (exact paths/evidence
authorization) and OD-15 (CLI packaging alias) remain the literal **`OWNER DECISION REQUIRED`**,
as does any row reopened or changed outside the approved bundle's exact scope. None of this is an
implementation authority, fixture authorization, or evidence authorization.

| ID | Decision required | Current proposal/constraint |
|---|---|---|
| OD-2 | Exact fixture count, split, coverage matrix, and source method | Recommend 20 entries, 12 development/8 held-out, synthetic-only; no “about 20”. |
| OD-3 | Named ground-truth owner and independent reviewer | Recommend P2-T5 owner authors; a distinct reviewer verifies before implementation. |
| OD-4 | Final P2-T5 manifest/run/case/measurement/report/failure identities and versions | The `V1@1.0` identities in section 5 are proposals, not frozen contracts. |
| OD-5 | Matching-rule identity | Approve the unchanged B4 rule binding and the two separate payload/hash proposals in section 6.4, or approve replacement identities; no changed-rule reuse of old evidence. |
| OD-6 | Metric vocabulary and formulas | Approve or reject the exact collection/conflict vocabulary, WER/CER separation, eligibility, empty-set behavior, and micro-only aggregation in section 12.1.1; F1 and macro are not emitted in v1. |
| OD-7 | Normalization and rounding | Approve or reject the exact normalizer identities, six fractional places, `ROUND_HALF_EVEN`, decimal-string representation, and no binary-float serialization. |
| OD-8 | T4 policy instance | Name exact `P2T4FusionPolicyConfigV1` values, `confidence_floor`, `config_version`, and hash, or keep policy-dependent measurements unavailable. |
| OD-9 | Recapture/partial/correlation/retry semantics | Approve or reject the exact correlation/retry/duplicate/recapture proposal in section 12.1.1; no downstream execution follows T1 `RECAPTURE`, and missing output cannot produce a successful report. |
| OD-10 | Fixture-mode latency | Approve or reject the exact v1-disabled proposal: `NOT_APPLICABLE` / `FIXTURE_ONLY_LATENCY_DISABLED`; no wall-clock, warm-up, percentile, p95, or canonical timing field. |
| OD-11 | Measurement vocabulary | Approve or reject the exact `MEASURED | NOT_MEASURED | NOT_APPLICABLE` vocabulary and closed reason catalog in section 12.1.1; no silent reuse of `AsrBenchmarkMeasurementV1`. |
| OD-12 | Python and dependency policy | `OWNER DECISION REQUIRED` for binding the exact selected dependency/version set and canonical refusal/label; current repository lock identity is `NO_PYTHON_LOCKFILE`, and this task must not create a Python lockfile. |
| OD-13 | Output persistence | Decide which synthetic structured fields may be tracked; default is hash/status summaries only and no raw text/provider output. |
| OD-14 | Exact implementation/test/fixture/media paths and evidence authorization policy | G2 may approve only the file-level implementation/test/fixture/media list. G1 may freeze evidence naming templates and authorization policy only; every concrete evidence path requires later exact-path G7 approval. No wildcard directory approval. |
| OD-15 | CLI packaging and invocation | The module form is canonical; decide separately whether a `p2t5` alias is packaged and define its packaging changes. |
| OD-16 | Privacy sentinel scope | Approve rejection patterns for drive/rooted/UNC/home paths, usernames, hostnames, environment values, and validator output. |
| OD-19 | Approval/checkpoint/closeout identity rules | Approve the plan-checkpoint tuple, G1/G2 approval-record commits, `parent(G5)=G2`, no-intermediate-commit rule, G4/G5 byte/path parity, G7/G8 checkpoint chain, reviewer independence, and `parent(G9)=G8` rule. |
| OD-20 | Inherited baseline disposition | Pre-declare exact accepted fingerprints and the closed G6 verdict vocabulary; keep ARCHITECTURE-POLICY-B-BASELINE-001 at backend/src/sketch2life/application/services/backend_ai_workflow.py for finding application imports an outer layer with validator SHA-256 fa236c8d389b608251153d601fc370efe3f3e2479446ca4a56a3d395f892e0b5 truthful as `ARCHITECTURE_INVALID` without misclassifying inherited timing/mypy/Ruff findings as P2-T5 regressions. |

#### 12.1.1 Exact approved values

For bundle signability, the proposal was closed to the exact values below, and the owner approved
this complete set of values on 2026-09-19 as part of `P2T5.OwnerDecisionBundleV3@1.0`
(`DECISIONS.md`); the implementation may not choose a different value silently. Any earlier
`Recommend`, `Decide`, or alternative wording in the table above is superseded as an open-ended
design question by this exact approved value.

| Area | Exact proposed value |
|---|---|
| Contract set | The eleven identities listed in section 5.1; `P2T5-REPORT-CANONICAL-JSON-V1` is an algorithm identity only. |
| Fixture package | 20 cases: 12 `DEVELOPMENT`, 8 `HELD_OUT`, exactly 40 media paths, `SYNTHETIC_ONLY`. |
| Oracle | P2-T5 owner role authors; distinct reviewer freezes it; no implementation-derived oracle; held-out anti-tuning; no oracle raw hash/blob is bound until the future bytes exist. |
| Metrics | Collection `coverage`/`accuracy`; conflict `TP/FP/FN/precision/recall`; WER/CER separate; micro-only aggregate; no macro or F1 in v1. |
| Numeric output | Six fractional decimal places, `ROUND_HALF_EVEN`, decimal strings; no binary-float serialization. |
| Empty/unavailable states | Zero denominator and no eligible population are `NOT_MEASURED`; `NOT_APPLICABLE` is only deliberately out-of-population. |
| Correlation/retry | Same manifest/case/split keeps the deterministic correlation ID; duplicate execution gets a new run ID; recapture is terminal for the current run; missing output is `PARTIAL`/`FAILED` with no successful report. |
| Latency | Disabled in fixture-only v1: `NOT_APPLICABLE` / `FIXTURE_ONLY_LATENCY_DISABLED`; no timing in the canonical report. |
| Environment | PRE-G1 freezes only CPython `3.13.5`, no new dependencies, installation `NOT AUTHORIZED`, the raw backend/pyproject.toml identity, and `NO_PYTHON_LOCKFILE`; G2 materializes and binds the exact installed interpreter/package-version set and configuration identity; G6 reuses that exact identity with the permitted fixture state, with no re-resolve/upgrade/install/substitute/silent replacement; mismatch is an environment/baseline failure, not a valid comparison. |
| Scope | The 54 exact literals remain a proposed planning inventory; G2 must individually repeat the approved paths. G1 does not authorize evidence paths. |

### 12.1.2 P2-T5 Owner Decision Bundle V3

DECISION AUTHORITY FOR THIS PRE-G1 OWNER ACTION:
this exact Owner Decision Bundle V3

REFERENCE / SOURCE MATERIAL:
P2_T5_EVALUATION_HARNESS_PLAN.md
PLAN.md

The plans remain mutable draft inputs until approved decisions are synchronized, independently reviewed, and checkpointed.

BEGIN P2-T5 OWNER DECISION BUNDLE V3

bundle_identity: P2T5.OwnerDecisionBundleV3@1.0
bundle_status: OWNER_APPROVED
feature_task: FEAT-003-multimodal-understanding / P2-T5
scope: fixture-only v1
owner_decision_status: APPROVED_2026-09-19 (approvals/TASK_APPROVAL.md and DECISIONS.md, "P2-T5
  fixture-only v1 owner decision bundle"; confirmed by
  tmp/p2-t5-v3-owner-confirmation-20260919-r2/REPORT.md)

This delimited section is the P2-T5 owner decision object referenced by the authoritative
approval. It is not itself TASK_APPROVAL.md, not itself the approval record, not a plan
checkpoint, and not a mutable-plan citation. The bundle contains the exact values and immutable
rule bytes that the Project Owner approved as one fixture-only v1 decision on 2026-09-19, recorded
in `approvals/TASK_APPROVAL.md` and `DECISIONS.md`. This plan revision synchronizes that recorded
approval into the plan text without semantic change; it grants no G1, G2, implementation,
fixture/media, evidence, or runtime authority by itself.

#### 12.1.2.1 Contract identities and immutable rule bindings

The complete contract identity set in this bundle is exactly:

1. P2T5.P2T5FixtureManifestV1@1.0
2. P2T5.P2T5RunRecordV1@1.0
3. P2T5.P2T5ValidationSummaryV1@1.0
4. P2T5.P2T5FixtureCaseResultV1@1.0
5. P2T5.P2T5MeasurementV1@1.0
6. P2T5.P2T5FailureV1@1.0
7. P2T5.P2T5CommandEnvelopeV1@1.0
8. P2T5.CorrelationIdV1@1.0
9. P2T5.ASRMetricRuleV1@1.0
10. P2T5.ConflictMatchingRuleV1@1.0
11. P2T5.P2T5EvaluationReportV1@1.0

P2T5-REPORT-CANONICAL-JSON-V1 is an algorithm identity, not a twelfth contract identity.
Each contract identity is a namespace-qualified name and version; no T1-T4 contract is aliased or
silently replaced.

The bundle immutably binds the following rule objects by embedding their exact canonical UTF-8
bytes. Each payload line below is the complete JSON object with no leading/trailing whitespace and
no trailing newline. The byte count, SHA-256, rule identity, version, and scope are all binding
fields of this bundle.

Semantic B4 matching rule artifact
identity: vision-b4-matching-rule-v1
repository_path: features/FEAT-003-multimodal-understanding/fixtures/vision-b4/matching-rule-v1.md
source_commit: c3d3a2b7da33ef97f58431656f606dff4f3c840f
git_blob_id: 8102d272ba4b23b425ac99dcc81a718baa5c46a1
raw_byte_count: 2526
raw_sha256: 4e405275257f1428f8f73b5339dac1941ce6f008ff00d39cc19c391c035b96bb
scope: entity, action, relation, and theme matching only
allowed_use: same-collection label/predicate/endpoint/evidence-reference matching and collection coverage/accuracy
not_allowed: WER, CER, conflict sets, T1 validity, or reuse of B4 fixtures/evidence

T4 policy object
identity: P2T4FusionPolicyConfigV1@1.0
canonicalization: P2T4-CANONICAL-JSON-V1
canonical_byte_count: 466
canonical_sha256: 4b378f69a33b86aeefc7443a23ac819e46b986132525cdd8a55d112dfb96415c
scope: T4 entity/action/narration/negation policy instance only
projection_source: backend/src/sketch2life/contracts/schemas/p2_t4_fusion.py, P2T4FusionPolicyConfigV1
~~~json
{"confidence_floor":0.5,"config_version":"p2-t4-fusion-policy-fixture-v1","contract_name":"P2T4FusionPolicyConfigV1","contract_version":"1.0","corroboration_increment":"0.10","entity_match_mode":"WHOLE_TOKEN_SEQUENCE","match_view_version":"vision_policy_match_view-v2","narration_weight_mode":"SUPPORT_ONLY","negation_cues":[["not"],["no"],["never"],["isn","t"],["doesn","t"],["didn","t"]],"negation_window_tokens":3,"uncertainty_formula_id":"AGREEMENT_WEIGHTED_V1"}
~~~

ASR metric rule object
identity: P2T5.ASRMetricRuleV1@1.0
canonicalization: P2T5-OWNER-BUNDLE-CANONICAL-JSON-V1
canonical_byte_count: 1563
canonical_sha256: 8be5f74a13d7515a7995dbffcff2db8aca6876cd7fe3898c4da26ecf86823711
scope: WER and CER formulas, eligibility, denominators, exclusions, normalization, six-place representation, and unavailable-state handling only
source_provenance: backend/src/sketch2life/benchmark/asr_scoring.py raw SHA-256 955be57f55ea917f4ed1e6ed58bc2744d8b4a5218183e2bcd186900aea8e470c
~~~json
{"eligibility":{"asr_status":["SUCCEEDED"],"manifest_wer_cer_flags":["wer_eligible=true","cer_eligible=true"],"provider":"fixture","reference_view":"non_empty_after_normalization","t1_decision":["PASS"]},"empty_set_behavior":{"empty_eligible_population":"NOT_MEASURED: NO_ELIGIBLE_CASES","empty_normalized_reference":"excluded_before_scoring"},"exclusion_rules":["T1 decision is not PASS","ASR result is not SUCCEEDED","manifest WER/CER eligibility is false","normalized reference sequence is empty"],"metrics":{"CER":{"denominator":"reference_character_count","formula":"levenshtein_distance(reference_characters,hypothesis_characters) / reference_character_count","numerator":"levenshtein_distance(reference_characters,hypothesis_characters)"},"WER":{"denominator":"reference_token_count","formula":"levenshtein_distance(reference_tokens,hypothesis_tokens) / reference_token_count","numerator":"levenshtein_distance(reference_tokens,hypothesis_tokens)"}},"normalizer":{"cer_view":"remove_all_normalized_whitespace","id":"vi-asr-normalizer-v1","operations":["NFC","casefold","punctuation_to_space","unicode_whitespace_collapse"],"preserve":["diacritics","U+0111_LATIN_SMALL_LETTER_D_WITH_STROKE"],"source_path":"backend/src/sketch2life/benchmark/asr_scoring.py","source_sha256":"955be57f55ea917f4ed1e6ed58bc2744d8b4a5218183e2bcd186900aea8e470c","wer_view":"split_normalized_text_on_whitespace"},"rounding":{"decimal_places":6,"mode":"ROUND_HALF_EVEN","representation":"decimal_string"},"rule_id":"P2T5.ASRMetricRuleV1","rule_version":"1.0","scope":["WER","CER"]}
~~~

Conflict matching rule object
identity: P2T5.ConflictMatchingRuleV1@1.0
canonicalization: P2T5-OWNER-BUNDLE-CANONICAL-JSON-V1
canonical_byte_count: 1521
canonical_sha256: dfe093c10d82b36cc34bfd3d4fe7572d8de1fb3d5f1b0598e0adb85f9d7e5fd8
scope: exact P2T4 conflict-key TP/FP/FN and conflict precision/recall only
source_provenance: backend/src/sketch2life/contracts/schemas/p2_t4_fusion.py and backend/src/sketch2life/application/services/p2_t4_fusion.py
~~~json
{"eligibility":{"case_result_status":["FUSED"],"labeled_conflict_keys":true,"provider":"fixture","t1_decision":["PASS"]},"empty_set_behavior":{"eligible_case_with_both_empty_sets":{"fn":0,"fp":0,"precision":"NOT_MEASURED: ZERO_DENOMINATOR","recall":"NOT_MEASURED: ZERO_DENOMINATOR","tp":0},"no_labeled_conflict_keys_population":"NOT_MEASURED: NO_ELIGIBLE_CASES"},"exclusion_rules":["T1 decision is not PASS","fused result status is not FUSED","typed upstream failure, recapture, T4 rejection, or input failure","case has no labeled conflict keys"],"matching":{"allowed_reason_codes":["ENTITY_ATTRIBUTE_CONTRADICTION","ACTION_CONTRADICTION","RELATION_CONTRADICTION","LOW_CONFIDENCE_EVIDENCE"],"fn":"reference_keys - predicted_keys","fp":"predicted_keys - reference_keys","identity_invariant":"P2T4ConflictV1.vision_claim_ref equals fused_observation_id","include_low_confidence_evidence":true,"key_fields":["reason_code","fused_observation_id"],"non_key_fields":["conflict_id","narration_claim_ref","recommended_reviewer_attention"],"precision":"tp / (tp + fp)","recall":"tp / (tp + fn)","set_operation":"exact","source_contract_field_map":{"fused_observation_id":"P2T4ConflictV1.vision_claim_ref","reason_code":"P2T4ConflictV1.reason_code"},"tp":"intersection(reference_keys,predicted_keys)"},"normalizer":{"id":"NONE","text_normalization":"none"},"rounding":{"decimal_places":6,"mode":"ROUND_HALF_EVEN","representation":"decimal_string"},"rule_id":"P2T5.ConflictMatchingRuleV1","rule_version":"1.0","scope":["CONFLICT"]}
~~~

The ASR and conflict payloads are embedded immutable artifact values in the bundle, not merely
references to whatever text may later remain in a plan. A future external immutable blob is
acceptable only if it has the same exact no-newline bytes, byte count, SHA-256, identity, version,
and scope; an implementation may not bind a different payload, source-file hash, or cross-domain
alias. The ASR rule is never a conflict rule or collection-matching rule; the conflict rule is never
an ASR or collection-matching rule; and the T4 policy object is never a P2-T5 scoring rule.

#### 12.1.2.2 P2T5.P2T5EvaluationReportV1@1.0 Decision Package

decision_value: APPROVE_OR_REJECT_THIS_COMPLETE_PACKAGE_EXACTLY
decision_scope: P2T5.P2T5EvaluationReportV1@1.0 report envelope, deterministic core, volatile run metadata, canonicalization, and digest domains
source: copied from the complete detailed proposal in section 5.5 without semantic change

The owner approved this complete package as one value on 2026-09-19 (`DECISIONS.md`). The package
below is the explicit bundle decision value, now also synchronized as `OWNER_APPROVED_V3_20260919`
in section 5.5; the two are the same approved value, not a divergent draft. Any future rejection
or change would leave report production and all report-dependent measurements unavailable until a
new owner decision and bundle revision.

The report identity is P2T5.P2T5EvaluationReportV1@1.0. The serialized envelope must carry
contract_name = P2T5EvaluationReportV1 and contract_version = 1.0; the @1.0 form is the fully
qualified identity used in bindings. The envelope has exactly two conceptual regions:

1. deterministic_core, which is the only region hashed for deterministic_core_sha256; and
2. volatile_run_metadata, which is excluded from that hash and from all rerun-parity claims.

The complete report envelope contains exactly these five top-level fields:

~~~text
contract_name
contract_version
deterministic_core
deterministic_core_sha256
volatile_run_metadata
~~~

The contract_name and contract_version envelope values must equal the corresponding values inside
the core; they are duplicated so a consumer can reject the envelope before reading the core. The
deterministic-core projection contains only these stable paths, with no undeclared extras:

~~~text
deterministic_core.contract_name
deterministic_core.contract_version
deterministic_core.mode
deterministic_core.run.run_id
deterministic_core.run.executed_at
deterministic_core.run.manifest_id
deterministic_core.run.manifest_version
deterministic_core.run.manifest_sha256
deterministic_core.run.oracle_sha256
deterministic_core.run.fixture_split
deterministic_core.run.implementation_plan_identity
deterministic_core.run.implementation_commit
deterministic_core.run.environment_identity
deterministic_core.run.dependency_identity
deterministic_core.manifest.manifest_id
deterministic_core.manifest.manifest_version
deterministic_core.manifest.manifest_sha256
deterministic_core.manifest.oracle_sha256
deterministic_core.manifest.fixture_split
deterministic_core.manifest.fixture_ids
deterministic_core.manifest.data_policy
deterministic_core.manifest.matching_rules
deterministic_core.manifest.normalizers
deterministic_core.upstream_contracts
deterministic_core.profile_and_policy_identities
deterministic_core.case_results
deterministic_core.measurements
deterministic_core.typed_failure_summary
deterministic_core.interpretation_id
deterministic_core.limitations_id
~~~

`run_id` is a required caller-supplied lowercase token matching `[a-z0-9][a-z0-9-]{0,63}`. It
must remain stable for a deterministic rerun and is never generated from random state, a UUID, wall
clock, timestamp, hostname, username, process ID, filesystem order, or completion order. For the
same manifest, case, selected split, and configuration, a deterministic rerun may reuse the same
`run_id`; a separately retained duplicate execution must use a new explicit caller-supplied
`run_id`. `run_id` is part of `deterministic_core` and participates in
`deterministic_core_sha256`.

deterministic_core contains mode, run, manifest, fixture_split, upstream_contracts,
profile_and_policy_identities, case_results, measurements, typed_failure_summary,
interpretation_id, and limitations_id. manifest contains IDs, version, and raw hashes only.
run.environment_identity contains the sanitized interpreter, dependency, plan, and implementation
identities. case_results are sorted by stable fixture_id. typed_failure_summary is a closed count
map. interpretation_id and limitations_id select bounded, predefined fixture-only text rather than
arbitrary model/provider content.

profile_and_policy_identities contains the complete proposed T4 policy projection from section
3.3 plus its bound fusion_policy_config_hash, the two FAKE_DETERMINISTIC_V1 profile IDs, and their
approved catalog/config identities. case_results contain only stable IDs, stage states, closed
statuses/codes, correlation ID, source/result/policy/canonical digests, and metric
eligibility/count fields. They never contain media, reference or hypothesis transcript text,
Vision labels, prompts, provider payloads, raw exceptions, or paths. interpretation_id and
limitations_id select bounded, predeclared fixture-only text; free-form interpretation is not part
of the core.

The exact serialization algorithm identity is P2T5-REPORT-CANONICAL-JSON-V1. It is not a P2-T5
contract binding identity and is never serialized as contract_name:

~~~python
json.dumps(
    deterministic_core,
    ensure_ascii=False,
    sort_keys=True,
    separators=(",", ":"),
    allow_nan=False,
)
~~~

The returned string is encoded as UTF-8. sort_keys=true orders object keys by code point. Arrays
are sorted before serialization by these required keys: case_results by lowercase fixture_id;
measurements by metric_id; manifest.matching_rules by (scope, rule_id);
manifest.normalizers by (scope, normalizer_id); and all closed failure/count maps by lexical key.
No source traversal order, filesystem order, hash-map order, process order, hostname, or runtime
completion order may affect the core.

The scalar rules are exact: JSON null is retained for declared nullable stable fields and is never
replaced with omission; every datetime is normalized to UTC and serialized as
YYYY-MM-DDTHH:mm:ss.ffffffZ; non-finite numbers NaN, Infinity, and -Infinity are rejected before
projection and again by allow_nan=false; decimal measurements are parsed from decimal strings,
never from binary floats, quantized to exactly six fractional places using ROUND_HALF_EVEN, and
serialized as strings such as 0.000000 or 1.250000. Counts remain integers. A
status/value/denominator mismatch is a typed report failure, not a coercion.

deterministic_core_sha256 is the lowercase SHA-256 of the exact UTF-8 bytes of the serialized
deterministic_core above. The hash field is an envelope value excluded from the core projection.
The external raw-file SHA-256 is computed separately over the complete final report file bytes and
is recorded only in a separately authorized evidence or approval binding; it is not embedded in
the report that it hashes. The Git blob identity of the complete report file is external metadata
and is bound only in the separately authorized immutable checkpoint. Git blob IDs and plan/artifact
binding hashes are external metadata. Thus no artifact contains or hashes its own core hash,
raw-file hash, or Git blob ID. This is the explicit self-hash prohibition.

volatile_run_metadata is the only non-core region and has exactly these five keys, each with a
nullable value: started_at, finished_at, stage_durations_ms, harness_overhead_ms, and
timing_sample_counts. The two times use the same UTC six-fraction format; duration and sample
values are finite non-negative integers; maps are sorted by their closed stage/metric keys; a
missing optional observation is null rather than an invented zero. No process ID, temporary
location, host identity, environment value, exception text, or raw payload is a report field, even
in this volatile region. volatile_run_metadata is serialized in the complete report but is never
included in the deterministic core or any rerun-parity claim.

run.executed_at is not a volatile field. It is required exactly once in the stable core as a
caller-injected UTC instant formatted YYYY-MM-DDTHH:mm:ss.ffffffZ; the identical string is passed
to every invoked T4 call in the run and therefore participates in every fused T4 canonical digest.
It is never read from the wall clock, regenerated per case, rounded, or replaced by
started_at/finished_at. A missing, non-UTC, differently formatted, or per-case value is a typed
report/precondition failure. The full report itself uses the same UTF-8 compact JSON rules for its
five envelope fields, but only the deterministic_core bytes feed deterministic_core_sha256.

The P2T5-CASE-OUTCOME-CANONICAL-JSON-V1 projection is also closed: it contains the case
contract identity/version, fixture ID/split, T1 decision/reasons, four stage states, correlation ID,
upstream identities/versions/statuses, closed failure/rejection fields, source/result/policy
digests, and measurement status/count/value/eligibility fields. It excludes run_id, executed_at,
all volatile fields, raw media, transcript/label text, paths, rejected inputs, report-envelope
fields, and case_outcome_sha256 itself. Its arrays and maps use the section 5.5 order and scalar
rules; omission, reordering, or an undeclared field is a domain mismatch.

#### 12.1.2.3 Exact remaining fixture-only v1 decisions

The remaining values approved by this bundle are exactly:

- Fixture package: exactly 20 synthetic cases, exactly 12 DEVELOPMENT and 8 HELD_OUT, exactly 40
  media paths, with no live provider or real child data.
- Exact fixture ID decision value:
~~~text
feat003-p2t5-dev-001
feat003-p2t5-dev-002
feat003-p2t5-dev-003
feat003-p2t5-dev-004
feat003-p2t5-dev-005
feat003-p2t5-dev-006
feat003-p2t5-dev-007
feat003-p2t5-dev-008
feat003-p2t5-dev-009
feat003-p2t5-dev-010
feat003-p2t5-dev-011
feat003-p2t5-dev-012
feat003-p2t5-heldout-001
feat003-p2t5-heldout-002
feat003-p2t5-heldout-003
feat003-p2t5-heldout-004
feat003-p2t5-heldout-005
feat003-p2t5-heldout-006
feat003-p2t5-heldout-007
feat003-p2t5-heldout-008
~~~
The first twelve IDs are DEVELOPMENT and the final eight are HELD_OUT. The set is unique; the
manifest ID set, case ID set, expected-oracle ID set, and ID-matched media stem set must be equal
to this exact set. expected-v1.json has exactly one hand-authored oracle row per ID.

- Exact 40 ID-matched media path decision value:
~~~text
features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-dev-001.png
features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-dev-001.wav
features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-dev-002.png
features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-dev-002.wav
features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-dev-003.png
features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-dev-003.wav
features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-dev-004.png
features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-dev-004.wav
features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-dev-005.png
features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-dev-005.wav
features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-dev-006.png
features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-dev-006.wav
features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-dev-007.png
features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-dev-007.wav
features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-dev-008.png
features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-dev-008.wav
features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-dev-009.png
features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-dev-009.wav
features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-dev-010.png
features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-dev-010.wav
features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-dev-011.png
features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-dev-011.wav
features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-dev-012.png
features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-dev-012.wav
features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-heldout-001.png
features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-heldout-001.wav
features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-heldout-002.png
features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-heldout-002.wav
features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-heldout-003.png
features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-heldout-003.wav
features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-heldout-004.png
features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-heldout-004.wav
features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-heldout-005.png
features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-heldout-005.wav
features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-heldout-006.png
features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-heldout-006.wav
features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-heldout-007.png
features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-heldout-007.wav
features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-heldout-008.png
features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-heldout-008.wav
~~~
Each ID has exactly one PNG and one WAV path, with no unreferenced or duplicate path. The list is
planning authorization data only; no path is authorized for creation before the later gates.
- Oracle: the P2-T5 owner role authors the oracle and a distinct reviewer freezes it; the oracle is
  not implementation-derived. HELD_OUT observations and results cannot tune scorer logic, matching
  rules, generators, thresholds, or the oracle after evaluation starts. A future oracle raw
  SHA-256/blob ID is bound only after the approved bytes exist.
- Metrics: collection coverage and accuracy; conflict TP, FP, FN, precision, and recall; WER and
  CER remain separate; micro aggregation only; no macro aggregation and no F1 in v1.
- Exact metric formula decision value:
  - coverage = matched_ground_truth / eligible_ground_truth.
  - accuracy = matched_prediction / eligible_prediction.
  - schema validity = schema_valid_count / attempted_result_count; T1 RECAPTURE is not a malformed
    adapter result, and no attempted result is NOT_MEASURED.
  - Collection coverage and accuracy eligibility is limited to schema-mapped eligible results under
    the approved B4 matching rule for entity, action, relation, and theme collections. Schema-invalid,
    input-invalid, typed-failure, and T4-rejection cases are excluded from semantic-quality scoring;
    their typed counts remain first-class. The B4 rule is never used for T1 validity, WER, CER, or
    conflict metrics.
  - Semantic-quality eligibility is limited to schema-mapped eligible results. Schema-invalid,
    input-invalid, typed-failure, and T4-rejection cases receive no semantic-quality score; their
    typed counts remain first-class. Recapture and typed-failure counting uses the fixture case as
    the counting unit, with one count for each case and each ordered T1 reason/code; adapter
    attempt denominators remain separate.
  - Coverage with zero eligible ground-truth items is NOT_MEASURED and excluded from the aggregate
    coverage denominator. Accuracy with zero eligible predictions is NOT_MEASURED; nonzero
    predictions with zero matches produce measured 0.
  - ASR WER/CER eligibility requires T1 PASS, ASR SUCCEEDED, provider fixture, manifest
    wer_eligible=true and cer_eligible=true, and a non-empty normalized reference. Exclude T1
    non-PASS, ASR non-SUCCEEDED, false manifest WER/CER eligibility, and empty normalized
    reference.
  - Conflict eligibility requires T1 PASS, fused result status FUSED, provider fixture, and
    labeled conflict keys. Exclude T1 non-PASS, non-FUSED status, typed upstream failure,
    recapture, T4 rejection, input failure, and cases with no labeled conflict keys. A labeled
    both-empty eligible case has TP=0, FP=0, FN=0 and precision/recall
    NOT_MEASURED: ZERO_DENOMINATOR; no labeled-key population is
    NOT_MEASURED: NO_ELIGIBLE_CASES.
  - Aggregate numerators and denominators are summed only across eligible per-case measurements;
    missing or empty denominators are never coerced to zero. Micro aggregation is the only primary
    aggregate. Macro aggregation and F1 are not emitted in v1.
  - Every measured decimal uses six fractional places, ROUND_HALF_EVEN, and decimal-string
    serialization; binary-float serialization is prohibited. NOT_MEASURED is used for zero
    denominators and no eligible populations. NOT_APPLICABLE is reserved for deliberately
    out-of-population metrics, including fixture-only latency with
    FIXTURE_ONLY_LATENCY_DISABLED.
- Numeric representation: six fractional places, ROUND_HALF_EVEN, decimal strings, and no binary
  float serialization. Zero denominators and no eligible populations are NOT_MEASURED; deliberately
  out-of-population behavior is NOT_APPLICABLE.
- Correlation/retry: the same manifest, case, and split retain the deterministic correlation ID;
  duplicate execution receives a new run ID; recapture is terminal for the current run; missing
  output is PARTIAL or FAILED and cannot produce a successful report.
- Latency: fixture-only v1 is disabled for timing and records NOT_APPLICABLE with reason
  FIXTURE_ONLY_LATENCY_DISABLED; no wall-clock, warm-up, percentile, p95, or canonical timing
  field is emitted.
- Dependency/environment decision value:
  - PRE-G1 freezes only CPython 3.13.5; no new dependencies; dependency installation NOT
    AUTHORIZED; the raw backend/pyproject.toml identity
    (SHA-256 9ca3a54905d11fdb7f30a84356d23741f256b2115b254bcc9fba4efacdf17df6); and
    NO_PYTHON_LOCKFILE.
  - At G2, the implementation approval record must materialize the exact installed
    package/version set, capture the exact sanitized configuration identity, and bind the resulting
    dependency/environment identity in the G2 approval record. The identity must not be inferred
    from range declarations.
  - At G6, the parent and candidate runs must use exactly the G2-bound interpreter,
    package/version set, configuration identity, lock identity, and permitted fixture state. G6
    reuses the exact G2-bound dependency/environment identity; no re-resolve, upgrade, install,
    substitute, or silent replacement is permitted. Any mismatch is an environment/baseline
    failure, not a valid comparison.
  - pnpm-lock.yaml is excluded from Python identity unless frontend tooling is first proven to
    participate in the harness and a new owner-approved identity adds it. No dependency
    installation, Python lockfile, or lockfile change is authorized by this bundle.
- Planning inventory: the 54 exact implementation/test/fixture/media literals remain a planning
  inventory only. G2 must individually repeat the approved paths; G1 does not authorize evidence
  paths, and no wildcard directory authorization exists.

#### 12.1.2.4 Exact inherited fingerprint decisions

The architecture baseline in this bundle is exactly:

ARCHITECTURE-POLICY-B-BASELINE-001
file: backend/src/sketch2life/application/services/backend_ai_workflow.py
finding: application imports an outer layer
validator SHA-256: fa236c8d389b608251153d601fc370efe3f3e2479446ca4a56a3d395f892e0b5

The exact G6 fingerprint tuple is typed by diagnostic family:

- Mypy/Ruff: path + line + diagnostic code + exact message text.
- Architecture: validator identity + rule + repository-relative path + exact finding text.
- FEAT-018: exact test node + nonstable field + pre-existing/out-of-scope disposition.

The exact inherited Mypy fingerprints are:

MYPY-BASELINE-001
  tool: mypy
  path: backend/src/sketch2life/application/services/learning_media_resolver.py
  line: 101
  diagnostic_code: arg-type
  message: Argument "reason_code" to "LearningMediaResultV1" has incompatible type "str"; expected "Literal['CACHE_MISS', 'STALE_MEDIA', 'CORRUPT_MEDIA', 'UNSAFE_MEDIA', 'RENDERER_FAILURE', 'MEDIA_UNAVAILABLE', 'PROVIDER_TIMEOUT'] | None"
  message_text_in_identity: true
  disposition: pre-existing, inherited, unchanged, outside the P2-T5 allowlist; no fix or suppression
MYPY-BASELINE-001
  tool: mypy
  path: backend/src/sketch2life/application/services/learning_media_fallback.py
  line: 82
  diagnostic_code: arg-type
  message: Argument "fallback_type" to "LearningMediaResultV1" has incompatible type "str"; expected "Literal['STILL_NARRATION', 'WHOLE_IMAGE_REVEAL', 'SUPERVISED_HANDOFF'] | None"
  message_text_in_identity: true
  disposition: pre-existing, inherited, unchanged, outside the P2-T5 allowlist; no fix or suppression
MYPY-BASELINE-001
  tool: mypy
  path: backend/src/sketch2life/application/services/learning_media_fallback.py
  line: 85
  diagnostic_code: arg-type
  message: Argument "reason_code" to "LearningMediaResultV1" has incompatible type "str"; expected "Literal['CACHE_MISS', 'STALE_MEDIA', 'CORRUPT_MEDIA', 'UNSAFE_MEDIA', 'RENDERER_FAILURE', 'MEDIA_UNAVAILABLE', 'PROVIDER_TIMEOUT'] | None"
  message_text_in_identity: true
  disposition: pre-existing, inherited, unchanged, outside the P2-T5 allowlist; no fix or suppression

The exact inherited Ruff fingerprints are:

RUFF-BASELINE-001
  tool: ruff
  path: backend/src/sketch2life/contracts/schemas/learning_media.py
  line: 79
  diagnostic_code: E501
  message: Line too long (103 > 100)
  message_text_in_identity: true
  disposition: pre-existing, inherited, unchanged, outside the P2-T5 allowlist; no fix or suppression
RUFF-BASELINE-001
  tool: ruff
  path: backend/tests/unit/test_learning_media_scenario_matrix.py
  line: 1
  diagnostic_code: I001
  message: Import block is un-sorted or un-formatted
  message_text_in_identity: true
  disposition: pre-existing, inherited, unchanged, outside the P2-T5 allowlist; no fix or suppression
RUFF-BASELINE-001
  tool: ruff
  path: backend/tests/unit/test_learning_media_scenario_matrix.py
  line: 14
  diagnostic_code: E501
  message: Line too long (121 > 100)
  message_text_in_identity: true
  disposition: pre-existing, inherited, unchanged, outside the P2-T5 allowlist; no fix or suppression

The exact architecture fingerprint is:

ARCHITECTURE-POLICY-B-BASELINE-001
  validator_identity: python tools/validate_architecture.py
  rule: ARCHITECTURE-POLICY-B-BASELINE-001
  path: backend/src/sketch2life/application/services/backend_ai_workflow.py
  exact_finding_text: application imports an outer layer
  validator_sha256: fa236c8d389b608251153d601fc370efe3f3e2479446ca4a56a3d395f892e0b5

The exact FEAT-018 inherited fingerprint is:

FEAT-018-TIMING-001
  tool: pytest deterministic replay check
  test node: backend/tests/unit/test_feat018_live_lightning_execution.py::test_repeated_fake_execution_is_deterministic_and_does_not_add_an_outer_attempt
  nonstable_field: adapter_wall_clock_ms
  disposition: pre-existing/out-of-scope for P2-T5; no fix, rerun, or reclassification

The architecture result remains ARCHITECTURE_INVALID with exactly
ARCHITECTURE-POLICY-B-BASELINE-001. No inherited fingerprint may be relabeled as a P2-T5
regression or fixed under this bundle.

For this V3 remediation, the raw bytes were recomputed from the actual repository files rather than
copied from a prior report: backend/src/sketch2life/benchmark/asr_scoring.py is 4,156 bytes with
raw SHA-256 955be57f55ea917f4ed1e6ed58bc2744d8b4a5218183e2bcd186900aea8e470c, and
backend/pyproject.toml is 2,395 bytes with raw SHA-256
9ca3a54905d11fdb7f30a84356d23741f256b2115b254bcc9fba4efacdf17df6.

#### 12.1.2.5 Approval, synchronization, and gate boundary

Approval text (verbatim):

I approve the P2-T5 fixture-only v1 planning decisions exactly as stated in this owner decision bundle. The approved values may then be synchronized, without semantic change, into PLAN.md and P2_T5_EVALUATION_HARNESS_PLAN.md. The synchronized plans become authoritative only after post-sync reviews and the immutable pre-G1 plan candidate checkpoint.

The owner approves the bundle object itself, not a mutable plan. Synchronization occurs only after
that approval and must make no semantic change. After synchronization, the full technical,
governance, and privacy readthroughs must pass before the immutable pre-G1 plan candidate
checkpoint. G1 later binds the exact synchronized plan bytes, revisions, raw hashes, and immutable
blob IDs; G1 does not bind this bundle by reference alone.

The following topology invariants are part of the decision value:

- G1 is the separate plan-approval record; G2 is the separate implementation-approval record.
- G2 binds the exact installed interpreter/package-version set, configuration identity, lock
  identity, and permitted fixture state used for the baseline; G6 runs parent and candidate with
  exactly that bound environment identity and treats any mismatch as an environment/baseline
  failure, not a valid comparison.
- G4 reviews the exact uncommitted candidate working tree and diff, including the exact candidate
  bytes and paths; G4 does not review a later or reconstructed tree.
- G5 contains exactly the G4-reviewed bytes and paths with zero byte or path drift, and
  parent(G5) is the G2 implementation-approval commit.
- No intermediate tracked commit exists between G2 and G5; G3 remains the implementation working
  tree between those records.
- G8 is an independent reviewer distinct from the implementation author, the G4 reviewer, and the
  G7 evidence assembler/author.
- G9 is governance-only and cannot mutate code, tests, fixtures, media, or evidence.
- G1, G2, G7, G8, and G9 are separate records/checkpoints and cannot be collapsed into one record
  or inferred from another gate.

The owner decision is recorded in `approvals/TASK_APPROVAL.md` and `DECISIONS.md` (2026-09-19);
this synchronization revision reflects that recorded decision in the plan text. That approval is
not G1 approval, G2 implementation approval, G3 working-tree authorization, G4 review acceptance,
G5 implementation checkpoint, G6 validation verdict, G7 evidence authorization or evidence
checkpoint, G8 evidence review, G9 closeout, implementation authorization, fixture/media creation
authorization, evidence authorization, or runtime/live-provider authorization.

The proposed later topology is: bundle approval; semantic synchronization; post-sync technical,
governance, and privacy reviews; immutable pre-G1 plan candidate checkpoint; G1 exact plan approval
record; G2 exact implementation/test/fixture/media path approval record; G3 implementation in the
approved working tree with no intermediate commit; G4 independent review of that same uncommitted
tree; G5 one zero-drift implementation checkpoint whose parent is G2; G6 validation and closed
verdicts; G7 separately authorized exact evidence creation/checkpoint; G8 independent evidence
review/checkpoint; and G9 closeout whose direct parent is G8 unless a later owner decision is
recorded.

END P2-T5 OWNER DECISION BUNDLE V3

### 12.2 EXPLICITLY DEFERRED / NON-BLOCKING

These decisions are intentionally deferred and do not block fixture-only v1 planning or the future
fixture-only implementation approval. They cannot authorize live, integration, or cross-feature work,
and they must not re-enter v1 through a CLI flag, import, report field, fixture, acceptance item, or
evidence path.

Each deferred row remains **`OWNER DECISION REQUIRED`** if it is reopened or used to change v1;
`DEFERRED_NON_BLOCKING` describes timing only and is not an owner decision.

| ID | Decision required | Current proposal/constraint |
|---|---|---|
| OD-1 | Whether a future live benchmark is wanted at all | `DEFERRED_NON_BLOCKING`; v1 remains fixture-only, and any live work needs a separate plan and gate. |
| OD-17 | Integration compatibility note | `DEFERRED_NON_BLOCKING`; any contract/provenance-only note requires a separately allocated and approved Integration Sprint, and is not a P2-T5 implementation prerequisite. |
| OD-18 | P2-T3 closure prerequisite | `DEFERRED_NON_BLOCKING`; the separate P2-T3 overall closure action is not a prerequisite for fixture-only v1 unless a later owner decision explicitly creates a new dependency. |

### 12.3 Risks and mitigations

| Risk | Consequence | Required mitigation |
|---|---|---|
| Oracle becomes derived from implementation output | Circular scoring and false confidence | Hand-author expected data first; independent review/hash; scorer cannot write oracle. |
| Held-out leakage through generator or rule tuning | Inflated evaluation result | Freeze split and hashes before implementation; no held-out authoring/tuning; new version for any change. |
| T4 policy values remain unfrozen | Non-comparable fused output/policy hash | Require exact policy instance decision or publish policy metrics as `NOT_MEASURED`. |
| Fixed/floating timestamps or timing enter stable output | Rerun parity failure | Inject `executed_at`; exclude volatile timing from identity; stable-sort all arrays. |
| Paths/environment leak into report | Privacy/security failure despite repository validator pass | Relative-path validation and dedicated privacy-sentinel test; redact validator `root=` output. |
| New CLI reaches live modules | Scope violation or accidental provider execution | Protected-module list and AST/import test before any adapter composition. |
| Existing generic/FEAT-018 contracts are confused with P2 V1 | T4 rejection or cross-feature authority collision | Feature-qualified IDs, explicit contract table, exact T4 identity/rejection assertions. |
| Fixture metrics are read as model quality | Unsupported research/production claim | Report banner and limitations; fixture-only status; no model/provider fields or live run. |
| Existing baseline findings recur | False P2-T5 regression or hidden new defect | Capture parent baseline and compare architecture/validator/test findings by fingerprint. |
| Unavailable historical evidence is treated as authority | Plan depends on missing facts | Use current contracts/code and available canonical records only; record unavailable links as limitations. |
| Public/network TTS is used to create audio | Unapproved network/data egress | Use local deterministic/synthetic bytes or approved licensed local sources; no runtime generation. |

## 13. Remediation traceability and owner-review boundary

### 13.1 Remediated proposal set

The following proposal sections are the current documentation-only remediation boundary:

| Requirement | Plan location | State |
|---|---|---|
| B1 exact T4 policy binding | Sections 3.2–3.3 | Complete and `OWNER_APPROVED_V3_20260919`; exact projection, hash `4b378f69a33b86aeefc7443a23ac819e46b986132525cdd8a55d112dfb96415c`, pre-T4 integrity failure, and no unbound T4 output are specified. |
| B2 matching rule separation | Sections 6.3–6.4 and 7 | Complete and `OWNER_APPROVED_V3_20260919`; the unchanged B4 semantic binding and the complete ASR/conflict canonical payloads have independently reproducible, separate hashes and scope-limited domains. |
| B3 correlation and stage accounting | Section 3.5 | Complete and `OWNER_APPROVED_V3_20260919`; source, derivation, equality, terminal, partial, skipped, and failure states are closed. |
| B4 report/hash contract | Sections 5.1–5.5 and 8.2 | Complete and `OWNER_APPROVED_V3_20260919`; identity, serialized name, core projection, stable/volatile split, ordering, scalar rules, core hash, and external raw hash are defined. |
| B5 inherited baseline | Sections 8.5 and 10.2 | Complete and `OWNER_APPROVED_V3_20260919`; G2 binds the parent, G3 remains uncommitted, G4 reviews that exact working tree/diff, G5 commits the same bytes with zero drift and `parent(G5)=G2`, and G6 applies the closed verdict vocabulary under identical state, with exact finding IDs/locations plus ARCHITECTURE-POLICY-B-BASELINE-001 at backend/src/sketch2life/application/services/backend_ai_workflow.py for finding application imports an outer layer and validator SHA-256 fa236c8d389b608251153d601fc370efe3f3e2479446ca4a56a3d395f892e0b5, truthful `ARCHITECTURE_INVALID`, and no unrelated fixes. |
| H1 privacy separation | Section 9.5 and 10.1 | Complete and `OWNER_APPROVED_V3_20260919`; exact fixture/oracle-only raw-data locations and output/evidence/log restrictions are defined. |
| H2 exact path scope | Sections 9.2, 9.3, 9.5, and 10.1 | Complete as a proposed planning inventory; exactly 54 implementation/test/fixture/media paths are enumerated: 10 source/test, 4 fixture/oracle JSON, and 40 media. Evidence templates remain a separate unauthorized class until G7. |
| H3 evidence templates | Section 10.1 | Complete as naming proposals only; G2 never authorizes them and every concrete path needs separate exact G7 authorization. |
| H4 gate numbering | Section 10.2 and all G4–G9 template names | Complete as the synchronized pre-G1 plan-checkpoint and G1–G9 proposal; no checkpoint or gate is approved by this plan. |
| H5 fully-qualified versus serialized identity | Sections 5.1–5.3 and 6.4 | Complete and `OWNER_APPROVED_V3_20260919`; every P2-T5 object uses `P2T5.<ContractName>@1.0` for binding and `contract_name=<ContractName>`, `contract_version="1.0"` on the wire. |
| H6 canonical evidence interpreter | Sections 8.1, 8.4, 10.2, and OD-12 | Complete and `OWNER_APPROVED_V3_20260919`; CPython 3.13.5 is mandatory for canonical G6–G8 evidence, and other versions are noncanonical rather than silently accepted. |
| H7 no self-identity binding | Sections 5.5, 9.5, and 10.1 | Complete and `OWNER_APPROVED_V3_20260919`; a report/evidence/review artifact cannot embed its own final raw SHA-256 or Git blob ID, which must be supplied externally by a paired review/checkpoint. |

### 13.2 H5–H7 definitions and source mapping

The prior critique did not label these safeguards H5–H7, so this plan records the explicit mapping
instead of treating the labels as pre-existing authority:

- **H5 — identity distinction:** maps to the contract/report ambiguity findings in the critique
  (the report identity and serialized `contract_name` must not be conflated). The complete mapping
  table and rejection rule are in sections 5.1–5.3.
- **H6 — canonical interpreter:** maps to the reproducibility/determinism findings (the prior
  historical `CPython 3.13.x` range was too broad for canonical evidence). Section 8.1 pins canonical
  evidence to CPython 3.13.5 and records noncanonical behavior for every other version.
- **H7 — artifact self-hash prevention:** maps to the evidence-integrity findings (a document must
  not bind its own final hash or Git blob). Sections 5.5, 9.5, and 10.1 require external identity
  binding and reject self-referential fields.

These documentation-only proposal resolutions are now part of the owner-approved V3 bundle content
(`DECISIONS.md`, 2026-09-19). They do not authorize implementation, fixture creation, evidence
creation, or any gate. The plan status is
`P2-T5 DRAFT — READY_FOR_PRE_G1_PLAN_CHECKPOINT_REVIEW` and P2-T5 implementation, fixture creation,
evidence creation, and all gates remain not approved.

For continuity with the available critique, the plan also preserves these adjacent safeguards:
P2-T5 does not publish an Integration Sprint compatibility note without a separate integration
allocation, and that note is not a P2-T5 implementation prerequisite; `fallback` is only a
blocked-continuation test case, not a new P2 contract; every
record uses the feature/task label `FEAT003 P2-T5` and does not implement or satisfy
`FEAT018-P2-T5`; P2-T1 threshold calibration is excluded; “clean run” means the CPython 3.13.5,
no-network, no-secret, no-model/cache fresh-checkout condition in section 8.4; “demo” means local
CLI text/JSON only with no UI, HTTP, notebook, or hosted page; and each review is performed by a
session/person distinct from the author with identities recomputed from Git objects. These remain
proposals pending the owner decision bundle; they do not authorize implementation or any later gate.

### Independent-review remediation trace

| Finding | Resolution in this revision | Normative location |
|---|---|---|
| F-001 | Defines the exact StageExecutionState and CaseRunStatus sets, keeps T1 PASS/RECAPTURE separate, maps preflight, recapture, typed-failure, rejection, policy-integrity, unexpected, and split-exclusion rows, and removes EXPECTED_TERMINAL_FAILURE as a value. | Sections 3.5 and 5.3 |
| F-002 | Replaces every slash alternative with one exact FakeAsrScenario/FakeVisionScenario, result profile/status/code/detail/attempt/retryability/policy-state tuple, T4 outcome/oracle projection, and case/run status across exactly 12 development and 8 held-out IDs. | Sections 6.1 and 6.2 |
| F-003 | Defines raw media/file, T1, T2/T3, T4 result/rejection, policy, report core, case outcome, and external identity domains with exact bytes, encoding, normalization, ordering, and self-hash exclusions. | Sections 5.5, 5.6, and 8.2 |
| F-004 | Defines the fixture-only in-memory composition seam after fake-adapter output and before T4, the typed mutation fields/categories, exact rejection oracle fields, and non-disclosure rule for the observed value. | Sections 3.3, 6.2, and 9.2 |

These resolutions close the four cited review findings as documentation proposals only. The owner
decision bundle, exact fixture bytes, implementation allowlist, evidence paths, and all gates
remain pending and are not authorized by this trace.

### 13.3 Current owner-plan-review remediation trace

The following seven current owner-plan-review findings are resolved, and are part of the
owner-approved `P2T5.OwnerDecisionBundleV3@1.0` (`DECISIONS.md`, 2026-09-19). Recording them here
grants no G1, G2, implementation, or runtime authority:

| Finding | Resolution | Normative location |
|---|---|---|
| A1 | Binds the exact proposed T4 policy identity/version, token-array negation cues, decimal-string 0.10 representation, canonical UTF-8 bytes, 466-byte count, SHA-256, and terminal `T4_POLICY_INTEGRITY_FAILURE` with no fallback/default policy. | Section 3.3 |
| A2 | Separates semantic matching, ASR normalizer/source provenance, `P2T5.ASRMetricRuleV1@1.0`, and `P2T5.ConflictMatchingRuleV1@1.0`; distinguishes raw source-file hashes from canonical payload hashes. | Sections 6.3-6.4 |
| A3 | States that the owner approves or rejects the exact proposed correlation semantics while preserving metadata, canonicalization, SHA-derived ID, T2/T3/T4 propagation, and terminal T1 `RECAPTURE`; retry and duplicate-execution choices remain owner-gated. | Section 3.5 and OD-9 |
| Held-out oracle rule | Allows independently authored/frozen HELD_OUT ground truth/oracles while prohibiting held-out observations/results from tuning scorer logic, matching rules, generators, thresholds, or the oracle after evaluation starts. | Section 6.3 |
| Reproducibility | Records CPython 3.13.5, `backend/pyproject.toml` raw SHA-256, the selected direct dependency/version set, and lock identity `NO_PYTHON_LOCKFILE`; no Python lockfile is created. | Section 8.1 |
| Gate topology | Limits G2 to exact implementation/test/fixture/media paths; reserves separately named evidence paths for G7; labels evidence templates as naming proposals only; keeps the 54 paths as a proposed planning invariant until separately approved. | Sections 9.2, 9.5, 10.1, and 10.2 |
| Post-sync sequencing | Records owner value selection, decision recording, plan synchronization, two passing reviews, the exact two-file plan candidate checkpoint and tuple, `READY_FOR_OWNER_PLAN_APPROVAL`, G1 plan approval record, and separate G2 implementation approval record in order. | Section 10.2 and parent `PLAN.md` |

The current status is `P2-T5 DRAFT — READY_FOR_PRE_G1_PLAN_CHECKPOINT_REVIEW`; the owner approved
the V3 decision bundle on 2026-09-19, but owner *plan* approval (G1) is not granted, implementation
is not approved, and tracked P2-T5 fixture/media/evidence artifacts are not created. Any value
outside the approved V3 bundle's scope remains `OWNER DECISION REQUIRED`.

### 13.4 Current governance-workflow remediation trace

The ten process-review findings below are resolved and, as the separate G1-G9 topology, are part
of the owner-approved `P2T5.OwnerDecisionBundleV3@1.0` (`DECISIONS.md`, 2026-09-19). This trace
does not itself grant G1, G2, implementation, or any gate:

| # | Finding | Resolution | Normative location |
|---:|---|---|---|
| 1 | Evidence naming authority | G1 freezes templates and authorization policy only; every concrete G7 path requires later exact-path approval and no `<run-id>` expansion is pre-authorized. | Sections 10.1-10.2 |
| 2 | Pre-G1 plan checkpoint | After both post-sync reviews pass, a future checkpoint commits exactly the two synchronized plans and records commit SHA plus per-plan revision/raw SHA-256/Git blob ID for G1 binding. This task does not create it. | Section 10.2 |
| 3 | G4 review target | G4 independently reviews the exact uncommitted G3 working tree/diff, not a commit. | Sections 8.5 and 10.2 |
| 4 | G5 parity | G5 is one checkpoint containing exactly the G4-reviewed bytes/paths, with zero byte/path drift. | Section 10.2 |
| 5 | G2-to-G5 topology | Plan checkpoint, G1 record commit, G2 record commit, no intermediate commits, G3 working tree, G4 same tree, then G5; `parent(G5)=G2`. | Section 10.2 |
| 6 | G6 verdicts | The closed verdicts are `PASS`, `PASS_WITH_ACCEPTED_BASELINE_FINDINGS`, and `FAIL`; ARCHITECTURE-POLICY-B-BASELINE-001 at backend/src/sketch2life/application/services/backend_ai_workflow.py for finding application imports an outer layer and validator SHA-256 fa236c8d389b608251153d601fc370efe3f3e2479446ca4a56a3d395f892e0b5 remains truthfully `ARCHITECTURE_INVALID`. | Sections 8.5 and 10.2 |
| 7 | G7 state | G7 is creation/checkpoint only: `COMPLETE — EVIDENCE CHECKPOINT BOUND` or transient `EVIDENCE_CREATED`, never `G7: PASS`. | Section 10.2 |
| 8 | Evidence checkpoint chain | G6 verification, G7 exact authorization record, G7 creation/checkpoint, G8 exact-checkpoint review/review checkpoint, then G9; G9 direct-parents G8 absent a later owner decision. | Section 10.2 |
| 9 | G8 independence | The reviewer is distinct from the implementation author, G4 reviewer, and G7 evidence author/assembler unless an explicit owner-approved exception is recorded first. | Section 10.2 |
| 10 | G2 baseline bindings | G2 binds the implementation parent, CPython, pyproject hash, dependency/lock identity, validators, accepted fingerprints, and relevant configuration identities. | Sections 8.1, 8.5, and 10.2 |

No row above grants approval or starts a gate. The current position remains `PRE-G1`; the owner
decision bundle is approved, and the next action is this plan synchronization followed by
independent post-sync review and the immutable pre-G1 plan candidate checkpoint.

### 13.5 Owner-bundle signability remediation trace

The six findings from the latest owner-bundle review are resolved, and their resolutions are part
of the owner-approved `P2T5.OwnerDecisionBundleV3@1.0` (`DECISIONS.md`, 2026-09-19):

| Finding | Resolution | Normative location |
|---|---|---|
| A1 | The complete eleven P2-T5 contract identities are enumerated; `P2T5-REPORT-CANONICAL-JSON-V1` is explicitly an algorithm identity. | Sections 5.1 and 12.1.1 |
| A2 | ASR metric and conflict rules bind complete canonical payloads, canonical byte counts, payload hashes, source provenance, and scope; source-file hashes are not substituted. | Section 6.4 |
| A4/A5 | Exact approve/reject proposal freezes coverage/accuracy, conflict precision/recall, separate WER/CER, micro-only aggregation, no macro/F1, six-place half-even decimal strings, and closed unavailable semantics. | Sections 5.4, 7, and 12.1.1 |
| B2 | G1 freezes oracle ownership/versioning/independence/anti-tuning policy only; future oracle raw hash/blob binds only after approved bytes exist. | Sections 5.2, 6.1, 6.3, and 12.1.1 |
| B3/B4 | Correlation, retry, duplicate execution, recapture, typed failure, partial/failed output, and disabled fixture-latency semantics are explicit approve/reject proposals. | Sections 3.5, 7, and 12.1.1 |
| C1/D2 | Environment policy records CPython 3.13.5, no new dependencies, installation not authorized, `NO_PYTHON_LOCKFILE`; the 54 paths remain a count plus exact proposed literals, not authorization. | Sections 8.1, 9.2–9.3, and 12.1.1 |

The V3 remediation matrix for the six latest independent-review findings is:

| Finding | V3 resolution |
|---|---|
| 1 | The exact pre-G1 authority preamble names this exact Owner Decision Bundle V3; the owner approves the bundle object itself, plans synchronize only after approval, and G1 later binds exact synchronized plan bytes, revisions, raw SHA-256 values, and Git blob IDs. |
| 2 | B4 is bound as immutable artifact identity vision-b4-matching-rule-v1 with repository path, source commit, Git blob ID, 2,526 raw bytes, exact raw SHA-256, and exact semantic scope. |
| 3 | P2T5.P2T5EvaluationReportV1@1.0 has an explicit approve/reject Decision Package copied from section 5.5, including the exact envelope, stable/volatile projections, canonicalization, ordering, scalar rules, executed_at, digest domains, external raw-file/Git metadata, and self-hash prohibition. |
| 4 | The decision object freezes coverage, accuracy, schema validity, recapture/typed-failure counting, empty-set behavior, ASR/conflict eligibility and exclusions, summed micro-only aggregation, no macro/F1, six-place ROUND_HALF_EVEN decimal strings, NOT_MEASURED, and NOT_APPLICABLE. |
| 5 | The decision object freezes exactly 12 DEVELOPMENT IDs, 8 HELD_OUT IDs, uniqueness, one oracle row per ID, and the exact 40 ID-matched media paths. |
| 6 | The decision object freezes G4/G5/G8/G9 and G1/G2/G7/G8/G9 separation invariants, the typed G6 fingerprint tuple, the recomputed ASR/pyproject raw SHA-256 values, and the required technical/governance/privacy reviews and validators. |

These resolutions are part of the owner approval recorded in `DECISIONS.md` (2026-09-19); this
trace does not itself create a plan checkpoint or authorize any gate.

## Revision history

Revision `0.15` is the current documentation-only plan-synchronization revision. It records the
owner's already-approved `P2T5.OwnerDecisionBundleV3@1.0` decision (`DECISIONS.md`, 2026-09-19)
into the active plan text without semantic change; it does not itself create a checkpoint or
grant G1, G2, implementation, fixture/media, evidence, or runtime authority.

| Revision | Date | Change | Approval state |
|---|---|---|---|
| `0.15` | 2026-09-19 | Documentation-only synchronization of the owner-approved `P2T5.OwnerDecisionBundleV3@1.0` decision (confirmed by `tmp/p2-t5-v3-owner-confirmation-20260919-r2/REPORT.md`) into the active plan text: updated active status wording, bundle/owner-decision-status fields, and the nine `PROPOSED_PENDING_OWNER_APPROVAL` proposal markers now covered by the approved bundle; no semantic change to any frozen value; no G1, G2, implementation, or runtime authority granted. | `P2-T5 DRAFT — READY_FOR_PRE_G1_PLAN_CHECKPOINT_REVIEW`; current position `PRE-G1`; owner decision bundle V3 approved; no gate or implementation authority |
| `0.14` | 2026-09-19 | Narrow documentation-only V3 remediation closing the stable caller-supplied `run_id` rule inside the report Decision Package and the PRE-G1/G2/G6 dependency/environment materialization and reuse rule; no approval, authority, implementation, or artifact-state change. | `P2-T5 DRAFT - READY_FOR_OWNER_P2_T5_FIXTURE_ONLY_V1_DECISION_BUNDLE_APPROVAL`; current position `PRE-G1`; no gate or implementation authority |
| `0.13` | 2026-09-19 | Documentation-only V3 remediation of the six latest owner-bundle findings: exact pre-G1 authority and bundle self-binding, immutable B4 artifact metadata, complete report Decision Package, exact metric formulas and eligibility, exact 20 IDs and 40 media paths, typed baseline fingerprints, recomputed repository-byte hashes, and explicit G1-G9 topology/review boundaries. | `P2-T5 DRAFT - READY_FOR_OWNER_P2_T5_FIXTURE_ONLY_V1_DECISION_BUNDLE_APPROVAL`; current position `PRE-G1`; no gate or implementation authority |
| `0.12` | 2026-09-19 | Documentation-only remediation of the owner decision bundle: separately delimited V2 owner object; exact T4, ASR, and conflict canonical bytes, byte counts, and SHA-256 values; exact remaining fixture-only v1 values; exact architecture, Mypy, Ruff, and FEAT-018 fingerprints; verbatim approval/synchronization wording; and explicit G1-G9/runtime boundaries. | `P2-T5 DRAFT — READY_FOR_OWNER_P2_T5_FIXTURE_ONLY_V1_DECISION_BUNDLE_APPROVAL`; current position `PRE-G1`; no gate or implementation authority |
| `0.11` | 2026-09-19 | Documentation-only remediation of the six owner-bundle signability findings: complete eleven-identity set, exact rule payload/hash binding, closed metric proposal, future-only oracle hash binding, exact correlation/latency/environment proposals, and count-versus-path authorization separation. | `P2-T5 DRAFT — READY_FOR_OWNER_P2_T5_FIXTURE_ONLY_V1_DECISION_BUNDLE_APPROVAL`; current position `PRE-G1`; no gate or implementation authority |
| `0.10` | 2026-09-19 | Documentation-only remediation of the ten governance-workflow topology findings: plan checkpoint, immutable G1/G2/G5 ancestry, G4/G5 parity, G6 verdicts, G7/G8/G9 checkpoint chain, G8 independence, and complete G2 bindings. | `P2-T5 DRAFT — READY_FOR_OWNER_DECISION_BUNDLE_REVIEW`; current position `PRE-G1`; no gate or implementation authority |
| `0.9` | 2026-09-19 | Documentation-only remediation of the seven current owner-plan-review findings: exact T4 policy binding, four rule domains, owner-gated correlation, held-out anti-tuning, reproducibility/lock identity, G2/G7 topology, and post-sync sequencing. | `P2-T5 DRAFT — READY_FOR_OWNER_PLAN_REVIEW`; no implementation authority |
| `0.8` | 2026-09-19 | Documentation-only owner-decision labeling and final preliminary-plan remediation audit; no implementation or authority change. | `DRAFT - NEEDS OWNER REVIEW`; no implementation authority |
| `0.1` | 2026-09-17 | Preliminary plan created from the remediated fixture-only P2-T5 subsection, current T1–T4 contracts, T4 G9 records, existing layout, and critique findings. | `DRAFT — NEEDS OWNER REVIEW`; no implementation authority |
| `0.2` | 2026-09-17 | Documentation-only remediation of B1–B5 and H1–H4; synchronized G1–G9 proposal, exact path/template boundaries, and explicit missing H5–H7 source condition. | `DRAFT — NEEDS OWNER REVIEW`; no implementation authority |
| `0.3` | 2026-09-18 | Documentation-only remediation of B1–B5 and H1–H7; exact 54-path planning invariant, matching-rule artifact, identity separation, CPython 3.13.5 pin, dynamic baseline fingerprint rule, and no-self-hash binding. | `DRAFT — NEEDS OWNER REVIEW`; no implementation authority |
| `0.4` | 2026-09-18 | Documentation-only cross-document remediation of F-001 through F-004: synchronized B4 semantic matching rule/hash/scope, fully qualified P2-T5 identities, G1–G9 evidence naming/authorization, separate Integration Sprint allocation, and explicit CPython 3.13.5 canonical wording. | `DRAFT — NEEDS OWNER REVIEW`; no implementation authority |
| `0.5` | 2026-09-18 | Documentation-only remediation of the eight latest cross-document findings: exact ASR/conflict payloads and hashes, parent-plan authority reduction, G2-parent/G5-candidate topology, lowercase fixture IDs, canonical module CLI, and blocking/deferred owner-decision split. | `DRAFT — NEEDS OWNER REVIEW`; no implementation authority |
| `0.6` | 2026-09-18 | Documentation-only remediation of independent-review findings F-001 through F-004: closed stage/case vocabulary, exact twenty-case adapter/oracle matrix and completeness rules, field-by-field digest domains, and the in-memory T4 adversarial composition seam. | `DRAFT — NEEDS OWNER REVIEW`; no implementation authority |

| `0.7` | 2026-09-18 | Documentation-only remediation of exact T4 policy bytes, rule source/scope/byte bindings, exhaustive run/case/recapture/retry and report hash semantics, 20/12/8/40 audit invariants, held-out oracle independence, dependency/lock identities, privacy boundary, and synchronized G1–G9 topology. | `DRAFT — NEEDS OWNER REVIEW`; no implementation authority |

```text
P2-T5 PRE-G1
OWNER DECISION BUNDLE V3 APPROVED
G1 NOT GRANTED
G2 NOT GRANTED
IMPLEMENTATION NOT APPROVED
FIXTURE/MEDIA/EVIDENCE NOT AUTHORIZED
RUNTIME/LIVE/PROVIDER/MODEL/GPU/LIGHTNING/NETWORK NOT APPROVED.
```

**Final status:** `P2-T5 DRAFT — READY_FOR_PRE_G1_PLAN_CHECKPOINT_REVIEW`
**CURRENT POSITION:** `PRE-G1`
**NEXT ACTION:** `INDEPENDENT POST-SYNC TECHNICAL AND GOVERNANCE/PRIVACY REVIEW, THEN THE IMMUTABLE PRE-G1 PLAN CANDIDATE CHECKPOINT`
**CODE/FIXTURE/MEDIA/EVIDENCE:** `DO NOT CREATE`
**OWNER PLAN APPROVAL (G1):** `NOT GRANTED`
**IMPLEMENTATION:** `NOT APPROVED`
**RUNTIME/LIVE/PROVIDER/MODEL/GPU/LIGHTNING/NETWORK:** `NOT APPROVED`
**TRACKED P2-T5 FIXTURE/MEDIA/EVIDENCE ARTIFACTS:** `NOT CREATED`

## P2-T5 G9 governance closeout — 2026-09-21

Owner approval is recorded for exactly one governance-only G9 closeout commit,
bound to draft raw SHA-256
`8c6b8f79bc10a132d2abdede86caa5beb9299fddb876a383344f9434edf27765` and
direct-parented to G8 review checkpoint
`d9d32d9a7ff7977d86dd0596d0447a10abd75098`. Only the six literal paths in the
approval record may change; the resulting G9 SHA is external-only and is not
written here.

The immutable G7/G8 evidence chain remains bound to G5
`323ebf9d78fff10e204875770672b21e4b58dec9`, G7 authorization
`bea4da49c9dad6228446747bfad0df3bb1ac79c5`, G7 evidence checkpoint
`78e08ab11a7ac1f8b42dac8459f6088e4496fcd3`, G8 correction
`55d8a6426a27533980e3f5bd2210c784e73eaa44`, and G8 review `d9d32d9a7ff7977d86dd0596d0447a10abd75098`.
The G8 verdict is `PASS`; G7/G8 evidence bytes, implementation, tests,
fixtures, media, and all non-allowlisted paths are immutable.

G9 preserves `G6: PASS_WITH_ACCEPTED_FINDINGS`, the accepted Policy-B,
mypy/Ruff, `FEAT-018-TIMING-001`, pytest/blank-at-EOF, and sanitized
temporary-directory findings, the 12-case `DEVELOPMENT` fixture-only scope,
and all privacy/output restrictions. No implementation or runtime/live,
provider/model, GPU, Lightning, network, migration, production, integration,
push, or PR activity is authorized.

```text
P2-T5: COMPLETE — GOVERNANCE-CLOSED
CLOSEOUT: COMPLETE_WITH_ACCEPTED_G6_FINDINGS
G6: PASS_WITH_ACCEPTED_FINDINGS
G7: COMPLETE — EVIDENCE CHECKPOINT BOUND
G8: PASS
G9: COMPLETE
P2-T5 IMPLEMENTATION: COMPLETE AT G5 CHECKPOINT
RUNTIME/INTEGRATION/LIVE: NOT APPROVED
PROVIDER/MODEL/GPU/LIGHTNING/NETWORK: NOT APPROVED
```
