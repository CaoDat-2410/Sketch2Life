# FEAT-020 — Complete Backend AI Workflow Demo Plan

**Status:** `AWAITING_APPROVAL`
**Implementation status:** `NOT_STARTED`
**Approval:** pending in `approvals/TASK_APPROVAL.md`
**Target runtime:** Lightning Studio, GPU-backed, repository pulled from GitHub
**Primary deliverable:** one backend command and one real-AI E2E test

## 1. Objective

Implement one cohesive backend-only vertical slice for the current Sketch2Life workflow. The slice must use the existing domain contracts and services where they are valid, add the missing application orchestration and production mappings, and execute the main workflow with real model adapters in one Lightning Studio process.

The acceptance target is not a collection of isolated endpoints. It is a single executable workflow with typed contracts, explicit gates, provenance, safety validation, artifact identity continuity, and a final manifest that explains every stage.

## 2. Scope

### Included

- real JPEG/PNG input from a local path supplied at runtime;
- optional real narration audio for the ASR branch;
- image admission, normalization metadata, checksum, and provenance;
- direct in-process Lightning model adapters;
- structured VLM understanding and optional ASR;
- deterministic multimodal fusion that preserves conflicts;
- explicit Gate A and Gate B decisions using a demo actor when running demo mode;
- P1 filtering, Montessori selection, learning objective, and experience compilation;
- story and scene planning with reality-grounded constraints;
- original-art-preserving animation/artifact planning;
- real micro-video generation through an approved model adapter, followed by duration/content/safety validation;
- off-screen activity handoff and a demo feedback/observation/history record;
- a versioned workflow result contract and sanitized JSON manifest;
- one E2E test that uses real configured model adapters and one real image;
- Lightning Studio clone/pull/run documentation and preflight checks;
- feature-local evidence and governance updates.

### Explicitly excluded

- Android/mobile or web UI;
- UI rendering, PixiJS browser integration, and playback controls;
- Firebase Storage, Firestore, or Realtime Database;
- durable session/feedback storage in this feature;
- exposing S3, Lightning, Runpod, or model credentials to mobile;
- committing real child images, audio, credentials, or model secrets;
- treating the existing fixture flow as acceptance evidence;
- a separately operated HTTP provider server in the main demo path;
- silently replacing the child’s original image with a generated redraw;
- claiming a successful complete workflow when a required AI/video stage was skipped.

## 3. Current-state assessment: what is right and what needs correction

The supplied assessment is directionally correct about the principal gap: the repository has a substantial contract and fixture foundation, but not yet a production-shaped, real-AI, connected backend flow. Its numeric percentages are subjective unless the team first agrees on a rubric; they should be treated as prioritization signals, not measured project metrics.

| Assessment point | Current evidence | Correct interpretation |
|---|---|---|
| “The live route does not complete the workflow” | The route returns a proposal and `gate_a_required=true` after fixture-backed understanding | Correct. The missing work is the connected application workflow, not merely another route. |
| “No Lightning integration exists” | Lightning client and a provider wrapper are present | Partially wrong. Integration building blocks exist; an unfixture real-model end-to-end run is not yet evidenced, and the current route is fixture-bound. |
| “P1 has no implementation” | P1 compiler, catalog, filters, Gate B, and handoff contracts exist | Partially wrong. Core P1 logic exists; production VLM-to-anchor mapping and runtime connection are missing. |
| “Gate A is entirely absent” | Offline fixture flow and mobile fixture UI contain gate concepts | Too broad. Production/shared backend gate commands and persistence are absent; the gate concept itself is not absent. |
| “Video is absent” | Resolver is cache-first; cache miss blocks or selects a non-video fallback | Correct for real generation. A fallback can complete a degraded handoff, but it cannot satisfy this feature’s strict `WORKFLOW_COMPLETE` target. |
| “Feedback/history are absent” | In-memory runtime semantics exist; no durable store is wired | Correct for production persistence, but an in-memory demo record is enough for this backend-only slice. |
| “Voice is part of the workflow” | The target image includes ASR, but the requested demo input is one image | Both can be true. Image-only must report ASR as `NOT_PROVIDED`; exact multimodal coverage needs optional real audio. |

## 4. Runtime modes and the one-command contract

The implementation must expose a single module entry point. The exact package/module path may follow repository conventions, but the public operator contract is:

```powershell
python -m sketch2life.workflow_demo `
  --image .\runtime-input\sample.jpg `
  --demo-autopilot `
  --output .\runtime-output\workflow-result.json
```

Optional full multimodal execution:

```powershell
python -m sketch2life.workflow_demo `
  --image .\runtime-input\sample.jpg `
  --narration-audio .\runtime-input\narration.wav `
  --demo-autopilot `
  --output .\runtime-output\workflow-result.json
```

The command must:

1. validate runtime configuration and model availability;
2. load direct Lightning adapters in the same process;
3. execute every required stage in order;
4. emit structured progress without raw prompts, tokens, or child data;
5. write a sanitized manifest atomically;
6. return exit code `0` only for `WORKFLOW_COMPLETE`;
7. return a nonzero exit code with a typed failure status for a blocked/failed required stage.

`--demo-autopilot` is mandatory for the one-command unattended demo. Without it, the command must stop at a human gate with `GATE_A_REQUIRED` or `GATE_B_REQUIRED`; it must never infer consent silently.

## 5. Target architecture

Dependencies must point inward: interfaces/adapters → application → domain. The orchestrator may depend on ports and versioned contracts, never on a model SDK, HTTP client, database, or filesystem detail directly.

### 5.1 Domain and contract layer

Reuse or extend existing versioned schemas rather than creating parallel untyped dictionaries:

- media admission and provenance;
- ASR transcript;
- structured VLM understanding;
- multimodal fusion/proposal;
- `SemanticAnchorSetV1`;
- P1 context, candidate, objective, and `ExperienceSpecV1`;
- Gate A and Gate B decision records;
- story plan and scene plan;
- original-art animation artifact/identity;
- learning-media generation request/result and validation;
- `ActivityHandoffV1`;
- observation, feedback, and history update records;
- top-level `BackendWorkflowResultV1` with stage statuses and provenance.

Every derived artifact must point to the original input checksum and preserve the original artifact reference. Identity continuity must be machine-checkable across art, story, video, and activity branches.

### 5.2 Application layer

Add one application service/orchestrator, tentatively:

`backend/src/sketch2life/application/services/backend_ai_workflow.py`

Responsibilities:

- own the ordered state machine for one run;
- enforce preconditions and stale-version/idempotency behavior;
- call ports using contracts only;
- keep the in-memory session aggregate for the run;
- create explicit gate decisions;
- prevent a stage from claiming success when its required output is absent;
- collect evidence references and sanitized summaries;
- produce the final result contract.

The orchestrator must not contain model loading, HTTP transport, provider URLs, UI logic, or SQL.

### 5.3 Infrastructure layer

Add a Lightning runtime adapter package, tentatively:

`backend/src/sketch2life/infrastructure/lightning/`

The preferred path is direct in-process model execution in Lightning Studio:

- local Qwen3-VL adapter for structured image understanding;
- local faster-whisper adapter when narration audio is supplied;
- story/scene planner using an approved local model or deterministic constrained planner backed by real VLM output;
- real video-generation adapter using the approved Lightning-compatible video model;
- image/art artifact writer and validator;
- runtime configuration and model manifest loader.

The existing HTTP Lightning provider wrapper may remain useful for diagnostics or a later deployment topology, but it is not part of this feature’s acceptance path. The main path must not require starting a second server or calling a fixture endpoint.

Candidate model profiles already referenced by project records are Whisper large-v3-turbo via faster-whisper and Qwen/Qwen3-VL-8B-Instruct. A video profile such as Wan2.2-TI2V-5B is only a candidate until availability, license, VRAM, latency, and output quality are recorded in an ADR. The implementation must fail preflight if a required model profile is not actually configured.

### 5.4 Interface/CLI layer

Add a thin CLI entry point, tentatively:

`backend/src/sketch2life/interfaces/cli/workflow_demo.py`

It parses paths/options, invokes the application service, prints safe progress, writes the result, and maps terminal status to exit code. It must not duplicate workflow rules.

## 6. End-to-end execution sequence

### Stage 0 — Runtime preflight

- Confirm Python/package installation, CUDA visibility, model paths, disk, and available VRAM.
- Load model manifest and version/checksum metadata.
- Verify required environment variables without printing secret values.
- Validate that the output directory is local and ignored by Git.

Failure: `RUNTIME_NOT_READY`.

### Stage 1 — Input and provenance

- Read exactly one caller-supplied JPEG/PNG image.
- Validate MIME, decodability, dimensions, file size, and corruption.
- Calculate a stable source checksum.
- Record a redacted source reference and checksum in the public manifest.
- Preserve original bytes; derived artifacts use new IDs.

Failure: `MEDIA_RECAPTURE`.

### Stage 2 — Optional ASR

- If audio is supplied, validate it, run the real local ASR adapter, and record transcript/confidence/segments.
- If audio is absent, set `asr.status=NOT_PROVIDED`, not `SKIPPED` or a fabricated transcript.

Failure with supplied audio: `ASR_FAILED`.

### Stage 3 — VLM understanding

- Run the real VLM on the original image.
- Request only allowed child-drawing semantics: visible objects, colors, spatial relations, observable actions, topic, uncertainty, and safety flags.
- Prohibit diagnosis, personality, intelligence, emotion certainty, or other psychological inference.
- Validate structured output against the versioned schema.

Failure: `AI_FAILED` or `CONTENT_UNSAFE`.

### Stage 4 — Fusion and Gate A

- Fuse VLM output and transcript when both exist.
- Preserve modality conflict as a first-class field. Do not implement “voice wins” without an approved ADR.
- Build `SemanticAnchorSetV1` through a production mapper, not a test-only helper.
- In unattended mode, create Gate A with `decision_mode=DEMO_AUTOPILOT`, actor, reason, timestamp, and input hash.
- Without autopilot, stop with `GATE_A_REQUIRED`.

### Stage 5 — Montessori recommendation and Gate B

- Build P1 context from age/readiness/material/safety/supervision inputs. If absent from the one-image run, use a declared demo context profile, never an undeclared default.
- Run existing P1 catalog/filter/fit logic.
- Select a candidate and learning objective with evidence and safety constraints.
- Record Gate B approval with the same explicit demo mode in unattended execution.
- Compile `ExperienceSpecV1` and `ActivityHandoffV1` only after Gate B conditions pass.

Failure: `NO_ELIGIBLE_ACTIVITY`, `GATE_B_REQUIRED`, or `POLICY_BLOCKED`.

### Stage 6 — Story and scene planning

- Generate a short, reality-grounded story from the confirmed anchor and objective.
- Produce separate branches for original-art animation, micro-video learning explanation, and off-screen activity.
- Enforce child-image identity hash and reject unsupported story facts.
- Set micro-video target duration to 5–10 seconds and store plan/model provenance.

Failure: `STORY_PLAN_FAILED` or `SCENE_PLAN_FAILED`.

### Stage 7 — Personalized art artifact

- Use the original drawing as the identity source.
- Generate an animation manifest or rendered artifact that changes motion/presentation, not the underlying drawing identity.
- Pass through a versioned renderer contract when the standalone art renderer is used.
- Validate source hash, identity hash, and safety fields.

Failure: `ART_OUTPUT_INVALID`.

### Stage 8 — Real learning micro-video

- Call the configured real video-generation adapter; do not use a fixture, pre-baked video, or cache hit as proof of AI generation.
- Validate decodability, duration (5–10 seconds), content policy, and correspondence to the objective.
- Record model/version, safe job ID, inputs, output checksum, and validator results.
- A fallback may be a degraded handoff, but cannot receive `WORKFLOW_COMPLETE` in this strict feature.

Failure: `VIDEO_GENERATION_FAILED`, `VIDEO_BLOCKED`, or `VIDEO_INVALID`.

### Stage 9 — Activity bridge

- Produce off-screen activity instructions, materials/substitutes, setup guidance, supervision requirement, and learning objective.
- Keep instructions grounded in the selected activity and drawing identity.
- Mark the session ready for an adult-led real-world activity.

Failure: `HANDOFF_INVALID`.

### Stage 10 — Demo feedback and history

- For unattended demo only, create a clearly labelled example observation/feedback record such as completed/partially completed/not attempted.
- Record interest, independence, notes, and history update as in-memory versioned records.
- Do not imply this is a real caregiver observation; `source=DEMO_AUTOPILOT` is mandatory.

### Stage 11 — Final manifest

The result contains run ID, schema version, terminal status, timestamps, input mode, redacted source/checksum, per-stage status, contract/model provenance, Gate A/B decisions, anchor, P1 selection, objective, identity hash, artifact references, warnings, and degraded fields. It must not contain raw credentials, auth headers, unrestricted prompts, or unnecessary raw child data.

## 7. Contract and state requirements

Use the existing session semantics where possible:

`CREATED` → `INPUT_VALIDATED` → `UNDERSTANDING_PROPOSED` → `GATE_A_CONFIRMED` → `CONTEXT_READY` → `GATE_B_CONFIRMED` → `EXPERIENCE_READY` → `ART_READY` → `VIDEO_READY` → `HANDOFF_READY` → `FEEDBACK_RECORDED` → `WORKFLOW_COMPLETE`.

Every transition includes `session_id`, `run_id`, `expected_session_version`, new version, command/request ID, and decision provenance. Same-request commands are idempotent; stale versions are rejected; prior records are immutable.

Required terminal statuses include `WORKFLOW_COMPLETE`, `RUNTIME_NOT_READY`, `MEDIA_RECAPTURE`, `ASR_FAILED`, `AI_FAILED`, `CONTENT_UNSAFE`, `GATE_A_REQUIRED`, `GATE_B_REQUIRED`, `NO_ELIGIBLE_ACTIVITY`, `STORY_PLAN_FAILED`, `SCENE_PLAN_FAILED`, `ART_OUTPUT_INVALID`, `VIDEO_GENERATION_FAILED`, `VIDEO_BLOCKED`, `VIDEO_INVALID`, and `HANDOFF_INVALID`.

## 8. Lightning Studio operating plan

Lightning Studio is the execution environment, not a reason to add another server layer. The repository is pulled or updated in Studio, dependencies use the Studio environment, and the single CLI runs in the same process as the adapters.

### First-run setup

1. Open a GPU-backed Lightning Studio.
2. Clone the repository or pull the selected branch from GitHub.
3. Install the backend package in the existing Studio environment; do not create a nested virtual environment.
4. Make model weights available through a documented persistent path or controlled first-run download.
5. Inject tokens/credentials through Lightning Secrets or environment variables only when a model needs them.
6. Run preflight, then the one workflow command.

Illustrative commands, to be finalized against repository packaging:

```bash
git clone <repository-url>
cd CAPSTONE
git pull --ff-only origin <approved-branch>
python -m pip install -e backend
python -m sketch2life.workflow_demo --image ./runtime-input/sample.jpg --demo-autopilot --output ./runtime-output/workflow-result.json
```

The plan intentionally does not invent a repository URL, branch, GPU type, model download URL, or secret name. Those values belong in runtime configuration/ADR and must be verified in the target Studio.

## 9. The single real-AI E2E test

Add one acceptance test, for example `backend/tests/e2e/test_lightning_backend_workflow.py`. The test has one public test function. Helpers may prepare a temporary output directory, but the workflow itself must use:

- `SKETCH2LIFE_E2E_IMAGE` pointing to one real JPEG/PNG;
- optional `SKETCH2LIFE_E2E_AUDIO` for the multimodal run;
- `SKETCH2LIFE_DEMO_AUTOPILOT=1`;
- real configured Lightning model adapters;
- no fixture ID, fake model, network mock, pre-recorded generated result, or monkeypatch of stage success.

The test asserts at least:

1. terminal status is `WORKFLOW_COMPLETE`;
2. all required stage statuses are successful;
3. image checksum and immutable original reference are present;
4. VLM output is schema-valid and contains no prohibited psychological fields;
5. Gate A and Gate B have explicit `DEMO_AUTOPILOT` decisions;
6. P1 candidate, objective, and experience identity are present;
7. art output preserves source identity/hash;
8. video exists, is decodable, is 5–10 seconds, and passes safety/content validation;
9. activity handoff, demo feedback, and history records are present;
10. the sanitized manifest contains no secrets or raw credential headers.

If the configured video model is unavailable, the test fails preflight rather than downgrading acceptance to a cache/fallback result. A future degraded-mode test may cover fallback semantics, but it is not this feature’s success test.

## 10. Acceptance criteria

| ID | Criterion |
|---|---|
| AC-01 | Feature plan, context, decisions, approval record, and evidence location exist before implementation. |
| AC-02 | Main demo path runs in one Lightning Studio process after GitHub clone/pull and does not require a separately operated provider server. |
| AC-03 | One command accepts a real arbitrary image and produces a sanitized versioned workflow manifest. |
| AC-04 | Image validation rejects invalid/unsafe media and preserves checksum/provenance. |
| AC-05 | Image-only mode reports ASR `NOT_PROVIDED`; optional real audio runs real ASR with provenance. |
| AC-06 | Real VLM output maps through a production mapper to `SemanticAnchorSetV1`; it is not test-helper-only. |
| AC-07 | Fusion preserves cross-modal conflicts and validates prohibited inference fields. |
| AC-08 | Gate A and Gate B are explicit, auditable, and stop the run when autopilot is not enabled. |
| AC-09 | P1 selection and `ExperienceSpecV1` use existing catalog/rules and preserve identity continuity. |
| AC-10 | Story/scene plans cover art, micro-video, and off-screen activity and are reality-grounded. |
| AC-11 | Art output preserves the original drawing and records derived artifact provenance. |
| AC-12 | Configured real AI video generation produces a validated 5–10 second micro-video; fallback/cache cannot falsely yield complete success. |
| AC-13 | Activity handoff, demo feedback, and history records are connected in the same run. |
| AC-14 | A single real-AI E2E test covers the complete path without fixture IDs or fake adapters. |
| AC-15 | Runtime failures return typed statuses and nonzero exit codes; no stage is silently skipped. |
| AC-16 | Security, harness, architecture, skeleton, unit, and E2E validation pass before commit. |

## 11. Implementation milestones

Implementation remains blocked until approval.

### M0 — Approved design baseline

- Approve this plan and update `approvals/TASK_APPROVAL.md`.
- Create/update ADRs for model profiles, input modes, demo autopilot, strict video success, and in-memory demo persistence.
- Confirm branch and clean scope without touching unrelated user files.

### M1 — Lightning direct-runtime preflight

- Add runtime config/model manifest.
- Add direct in-process model ports/adapters.
- Validate CUDA, weights, model versions, and safe configuration errors.

### M2 — Real input and understanding

- Add image/audio admission and provenance.
- Add VLM/ASR adapters and structured validation.
- Add fusion and production VLM-to-anchor mapper.

### M3 — Gates and P1

- Connect session transitions, Gate A, P1 context/catalog, Gate B, compiler, and handoff contracts.
- Add explicit demo decision records.

### M4 — Story, scene, art, and video

- Add story/scene orchestration.
- Add original-art artifact path.
- Add real video adapter and 5–10 second safety/content validation.

### M5 — One-command orchestrator

- Add workflow service and thin CLI.
- Add sanitized manifest and exit-code mapping.

### M6 — One E2E test

- Run the complete flow against a real arbitrary image in Lightning Studio.
- Capture feature-local evidence for each stage and final result.

### M7 — Governance closeout

- Run repository security, harness, architecture, skeleton, unit, and E2E validation.
- Update context, decisions, evidence index, and status.
- Commit only after checks and approval gates pass.

## 12. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Arbitrary image is ambiguous | Return uncertainty; do not infer psychology; allow typed Gate A correction. |
| Image cannot test ASR | Make audio optional and report `NOT_PROVIDED`; use a second real audio input for multimodal coverage. |
| GPU/VRAM/model quota insufficient | Preflight; keep profiles configurable; fail `RUNTIME_NOT_READY`. |
| Video generation is slow/expensive | Use one small acceptance image, record timing, document model profile, never replace generation with a fixture. |
| Autopilot is mistaken for consent | Store `DEMO_AUTOPILOT`; disable outside demo CLI; block production entry points. |
| Model output drifts | Pin revision/manifest, validate schema/safety, store provenance. |
| In-memory records disappear | Scope as demo; make persistence a separate approved feature. |
| Sensitive input leaks into evidence | Redact paths/raw payloads, hash originals, keep artifacts ignored/local, run security validator. |

## 13. Required evidence

All evidence belongs under `features/FEAT-020-backend-ai-workflow-demo/evidence/` and must be sanitized:

- preflight output with model identifiers and secrets redacted;
- one-command stdout/stderr summary;
- sanitized final manifest;
- E2E test result and timing/resource summary;
- validator outputs;
- Gate A/B decision records;
- original-image immutability and identity-continuity checks.

No raw child image/audio, raw prompt, access token, or unrestricted model payload may be committed as evidence.
