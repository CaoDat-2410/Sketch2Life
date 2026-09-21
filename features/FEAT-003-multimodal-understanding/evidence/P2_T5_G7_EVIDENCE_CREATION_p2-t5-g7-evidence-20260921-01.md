# P2-T5 G7 evidence creation - sanitized handoff

## Scope and status

| Field | Value |
|---|---|
| Feature/task | FEAT-003 / P2-T5 |
| G7 run ID | p2-t5-g7-evidence-20260921-01 |
| Evidence assembler | Codex agent; G7 evidence author/assembler |
| Model/session | Codex / GPT-5 (system-reported) |
| Stable session ID | 01a0c26b-d0e5-7861-9da6-d495e8667e61 |
| Evidence execution UTC | 2026-09-21T06:43:54.327722Z |
| G7 artifact state | EVIDENCE_CREATED; CHECKPOINT_BINDING_PENDING |
| G8 | NOT STARTED |
| G9 | NOT STARTED |
| Runtime/integration/live | NOT APPROVED |

This handoff records fixture-only, deterministic evidence creation under the
owner-authorized G7 scope. It does not authorize G8, G9, runtime, integration,
provider/model, GPU, Lightning, network, migration, production, push, or PR
activity.

## Authorization and topology

| Binding | Value |
|---|---|
| Approved draft raw SHA-256 | eb163b86954d0355189375480145828e8ab9372f89eba0f7f196082427caca10 |
| Authorization-record commit | bea4da49c9dad6228446747bfad0df3bb1ac79c5 |
| Authorization-record parent | 323ebf9d78fff10e204875770672b21e4b58dec9 |
| Authorization-record changed path | features/FEAT-003-multimodal-understanding/approvals/TASK_APPROVAL.md |
| JSON evidence path | features/FEAT-003-multimodal-understanding/evidence/P2_T5_G7_EVIDENCE_CREATION_p2-t5-g7-evidence-20260921-01.json |
| Markdown evidence path | features/FEAT-003-multimodal-understanding/evidence/P2_T5_G7_EVIDENCE_CREATION_p2-t5-g7-evidence-20260921-01.md |

The authorized topology is:

G5 implementation checkpoint -> G7 authorization record -> G7 evidence
creation -> G7 evidence checkpoint -> G8 independent review -> G8 checkpoint
-> G9.

Only the two evidence paths above are permitted. The future evidence
checkpoint must be a direct child of the authorization-record commit and must
verify exact path count, raw SHA-256, Git blob IDs, and unchanged bytes.

## Report contract and provenance

| Field | Value |
|---|---|
| Report identity | P2T5.P2T5EvaluationReportV1@1.0 |
| Serialized envelope | contract_name=P2T5EvaluationReportV1, contract_version=1.0 |
| Canonicalization | P2T5-REPORT-CANONICAL-JSON-V1 |
| JSON deterministic-core SHA-256 | 13f4cb2a9fc0d48423e08551848b1ccd6c5396b6a288e3a74dbb27782ac6abe0 |
| JSON raw SHA-256 | e574a02dc3b018162eb08fb63eaff7a1ad0be1370a736d6d405d1c50c82d116a |
| JSON Git blob ID | d029fb364a8076bb617acc710b8d1ba8942b3631 |
| JSON bytes | 32457 |

The JSON is the canonical machine-readable report. It contains no self-hash,
self-blob, or future evidence-commit binding. This Markdown file does not
contain its own raw hash or Git blob ID.

### G5 and G6 bindings

| Binding | Value |
|---|---|
| G5 implementation | 323ebf9d78fff10e204875770672b21e4b58dec9 |
| G5 direct parent | 9d6340672c5d1bbdd7a95004f5fad811718ec4a0 |
| G5 tree | 09f9cea8addd6922916514dde96b1a4c583ef24f |
| G5 ordered 54-path digest | dabf603ea2ccd6296a1f547a6b250b5f918f729048de1275d02ec9b7e03bbcf1 |
| G6 report | tmp/p2-t5-g6-checkpoint-verification-20260920/REPORT.md |
| G6 report bytes | 19412 |
| G6 report raw SHA-256 | c7d1057daa2ee7175675f5e6513dbca0520710ab3a1f73b5c7e829687089e410 |
| G6 disposition | PASS_WITH_ACCEPTED_FINDINGS |

### Fixture package

The package is p2-t5-evaluation-v1 version 1.0, with 20 synthetic-only
entries: 12 DEVELOPMENT, 8 HELD_OUT, and 40 referenced media files. This
run selected DEVELOPMENT and evaluated 12 entries in stable manifest order.

| Artifact | Raw bytes | Raw SHA-256 |
|---|---:|---|
| fixtures/p2-t5-evaluation-v1/manifest-v1.json | 17336 | 17f2a1af1f3644b9178283d8097ec5b73d11e54ae4e76da22be23fb66e07d21d |
| fixtures/p2-t5-evaluation-v1/cases-v1.json | 13527 | f715c8b65697b747751720726c10f1fcf744d7ce4cfe4fd760565c39c519fcbb |
| fixtures/p2-t5-evaluation-v1/expected-v1.json | 4838 | 23b7668f9ca30814e325cf1ba4f5f1ccae03bd37b52b3e49198e045fb5235b83 |
| fixtures/p2-t5-evaluation-v1/matching-rule-v1.json | 1053 | 43fa4f06e456cf1e1b7a2d79c7ad515d4caf89c556a590790f5ab0b6879f3a49 |

### T1-T4 and environment

| Binding | Value |
|---|---|
| Upstream contracts | P2.AsrResultV1@1.0, P2.VisionUnderstandingResultV1@1.0 |
| Fixture profiles | FAKE_DETERMINISTIC_V1 for ASR and Vision |
| Fused contract | P2T4.P2T4FusedResultV1@1.0 |
| Rejection contract | P2T4.P2T4FusionInputRejectionV2@2.0 |
| T4 policy | P2T4FusionPolicyConfigV1@1.0 |
| T4 policy SHA-256 | 4b378f69a33b86aeefc7443a23ac819e46b986132525cdd8a55d112dfb96415c |
| Interpreter | backend/.venv/Scripts/python.exe, CPython 3.13.5 |
| Dependency identity | NO_PYTHON_LOCKFILE |
| Dependency-set hash | 217f418ce003e9279bdcbe863437b90d0219f43264c3dafbcd7f6d459cefed48 |
| Plan identity | P2-T5-EVALUATION-HARNESS-PLAN@0.15 |
| Plan raw SHA-256 | 2a102acd689c0b53854562694692ce3a139ecdbbdee88f7c9fce7c136a5eea20 |

## Evaluation result summary

| Result | Count/value |
|---|---:|
| Selected split | DEVELOPMENT |
| Evaluated cases | 12 |
| COMPLETED | 6 |
| COMPLETED_WITH_TYPED_FAILURES | 4 |
| EXPECTED_TERMINAL | 2 |
| T1 executed | 12 |
| ASR executed / not executed | 10 / 2 |
| Vision executed / not executed | 10 / 2 |
| Fusion executed / not executed | 10 / 2 |
| Measurements | 20, all NOT_MEASURED with NO_ELIGIBLE_CASES |

Typed failure summary is closed-contract only:
ASR_MODEL_UNAVAILABLE=1, ASR_PROVIDER_FAILURE=1, ASR_TIMEOUT=1,
VISION_TIMEOUT=1.

Interpretation: P2T5-FIXTURE-ONLY-INTERPRETATION-V1.
Limitations: P2T5-FIXTURE-ONLY-LIMITATIONS-V1.

## Sanitization and limitations

The permitted outputs contain only contract identities, repository-relative
paths, hashes, counts, statuses, timestamps, role identity, commands, and
governance interpretation. The following are excluded: raw media, transcripts,
prompts, provider/model payloads, credentials, tokens, endpoints, absolute host
paths, hostnames, environment-variable values, unstructured failure details,
unapproved labels, and real child data.

The fixture evaluator completed with exit code 0. The focused offline
contract/evaluator/scoring/privacy tests passed. Two CLI test cases did not
start because the host temporary-directory permission precondition was denied;
this sanitized limitation is WIN_TEMP_DIRECTORY_PERMISSION_DENIED, with no
fixture or evidence-content effect. Harness and repository-security validation
passed. Architecture validation remains the accepted baseline finding
ARCHITECTURE-POLICY-B-BASELINE-001; no new architecture change is claimed.

## Governance interpretation

G7: EVIDENCE CREATED; CHECKPOINT BINDING PENDING
G8: READY ONLY FOR SEPARATE INDEPENDENT REVIEW AFTER CHECKPOINT
G9: NOT STARTED
RUNTIME/INTEGRATION/LIVE: NOT APPROVED

The evidence checkpoint is the separate next local governance step. No amend,
split, push, PR, G8 review, or G9 closeout is included in this evidence.
