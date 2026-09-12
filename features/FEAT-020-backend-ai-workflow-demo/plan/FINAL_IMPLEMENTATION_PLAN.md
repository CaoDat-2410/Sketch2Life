# FEAT-020 — Final Backend AI Workflow Demo Implementation Plan

**Status:** `IN_PROGRESS`
**Implementation:** `IN_PROGRESS`
**Date:** 2026-09-13
**Runtime:** Lightning Studio, full repository pulled from GitHub
**UI/PixiJS playback:** out of scope
**Video generation:** deferred in the first milestone
**First terminal success:** `BACKEND_CONTEXT_READY`

This is the canonical plan for the first complete backend demonstration. It consolidates the owner-confirmed decisions and is the implementation source of truth for FEAT-020.

## 1. Desired outcome

One backend command must run the main Sketch2Life workflow with real model calls and no UI:

```text
committed image + committed Vietnamese WAV
  → media validation and provenance
  → real ASR + real VLM
  → multimodal fusion
  → Gate A
  → all Montessori age bands
  → Gate B
  → experience context
  → story and scene context
  → original-art render intent
  → deferred video contract
  → off-screen activity handoff
  → demo feedback/history
  → BACKEND_CONTEXT_READY
```

The command must return a typed manifest explaining every stage. It must not claim that a video exists when video generation is deferred.

## 2. Confirmed owner decisions

1. Use the committed synthetic image and Vietnamese WAV as default test inputs.
2. Use both image and WAV in the single E2E so VLM, ASR, and fusion run.
3. Test assets are replaceable by CLI path or environment variable; changing files does not require code changes.
4. Pull the full repository into Lightning Studio from GitHub.
5. Cover every age band currently present in the golden catalog.
6. Use golden-catalog readiness criteria as the readiness baseline.
7. Prefer each record’s primary material; use only that record’s approved household substitute when needed.
8. Require adult/guide supervision for every activity.
9. Use duration from the selected activity record.
10. Use `DEMO_OPERATOR` for unattended Gate A, Gate B and demo feedback.
11. Defer video generation; represent it as `VIDEO_DEFERRED`.
12. Do not implement PixiJS; provide a static, hand-authored SVG asset catalog and asset-selection contract.
13. Do not generate missing PixiJS assets with AI during runtime.
14. Keep future decisions grouped; do not create one commit per small answer.

## 3. Scope

### Included

- one CLI entry point;
- real image and Vietnamese WAV validation;
- real direct/in-process VLM and ASR adapters in Lightning Studio;
- structured output validation and prohibited-inference filtering;
- modality fusion with conflict preservation;
- explicit Gate A and Gate B decisions;
- all four age bands in one E2E matrix;
- golden readiness/material/safety/supervision/duration rules;
- seeded variation and no-immediate-repeat selection;
- story/scene context;
- original-art-preserving render intent;
- deferred learning-media contract;
- off-screen activity handoff;
- in-memory demo feedback/history;
- static PixiJS asset IDs and render intents;
- sanitized result manifest and feature-local evidence;
- one real-AI E2E test function;
- Lightning Studio pull/install/preflight/run instructions.

### Excluded

- Android, React Native, web UI or PixiJS playback;
- video model integration and video file generation;
- Firebase Storage, Firestore or Realtime Database;
- durable session/history persistence;
- a separately operated provider server as a required process;
- runtime AI generation of PixiJS assets;
- real child data, credentials, tokens or raw prompts in Git;
- weakening catalog safety rules to force a result.

## 4. Current system gap

The repository already contains contracts, P1 logic, golden catalog, offline fixtures, a Lightning client, session semantics and a standalone art-renderer POC. The missing slice is the connected real-AI application workflow.

Current limitations to remove:

1. The live route is fixture-bound and stops before Gate A.
2. VLM-to-`SemanticAnchorSetV1` mapping is not yet a production application mapper.
3. ASR/VLM/fusion/gates/P1/story/art/activity/feedback are not driven by one orchestrator.
4. The first demo needs a typed deferred-video result instead of a cache/fallback pretending to be generated media.
5. The standalone PixiJS POC needs a catalog/selection contract, not renderer integration.
6. Selection must not always use the first candidate.

The golden catalog is a domain reference. The committed image/WAV are input assets. Neither is a precomputed model response.

## 5. Lightning Studio runbook

### Repository and environment

```bash
git clone <repository-url>
cd CAPSTONE
git pull --ff-only origin <approved-branch>
python -m pip install -e backend
```

Use the existing Studio environment; do not create a nested virtual environment. Model checkpoints and non-secret configuration must use documented persistent Studio paths. Secrets must come from Lightning Secrets/environment and never be committed.

### Command

```bash
python -m sketch2life.workflow_demo \
  --image ./features/FEAT-020-backend-ai-workflow-demo/test-assets/input-image.png \
  --narration-audio ./features/FEAT-020-backend-ai-workflow-demo/test-assets/narration.wav \
  --age-mode all \
  --demo-autopilot \
  --output ./runtime-output/workflow-result.json
```

Optional debugging of one band:

```bash
python -m sketch2life.workflow_demo \
  --image ./features/FEAT-020-backend-ai-workflow-demo/test-assets/input-image.png \
  --narration-audio ./features/FEAT-020-backend-ai-workflow-demo/test-assets/narration.wav \
  --age-band 6-9 \
  --seed 123456 \
  --demo-autopilot \
  --output ./runtime-output/workflow-result.json
```

The CLI must support replacement paths and must not hard-code the committed filenames in domain logic. A nonzero exit code is returned for invalid input, blocked gates, runtime failure, or invalid context/handoff. Exit code `0` is reserved for `BACKEND_CONTEXT_READY`.

### Preflight

Check Python imports, CUDA/device, model revision/path, available VRAM/disk, secret presence without printing values, output directory, input media, catalog JSON, SVG XML, and asset-selection manifest. Fail fast as `RUNTIME_NOT_READY`.

## 6. Architecture and module responsibilities

Dependencies point inward:

```text
CLI/interface
  → application workflow orchestrator
    → domain contracts and ports
      ← Lightning model adapters
      ← catalog/asset adapters
      ← in-memory session/feedback adapters
```

### Domain/contracts

Reuse or extend versioned contracts for media provenance, ASR, VLM, fusion, `SemanticAnchorSetV1`, Gate A/B, P1 context/candidate/objective, `ExperienceSpecV1`, story/scene, art identity/render intent, PixiJS asset selection, deferred video, `ActivityHandoffV1`, feedback/history, and `BackendWorkflowResultV1`.

Every derived artifact keeps the source image artifact ID and SHA-256. Original bytes are immutable. Identity continuity is validated across story, art, video-context and activity branches.

### Application

Tentative file: `backend/src/sketch2life/application/services/backend_ai_workflow.py`

Own ordering, state transitions, gate enforcement, age matrix, random seed, catalog selection, deferred video, provenance, idempotency and final manifest. It must not import model SDKs, HTTP transports, PixiJS or SQL.

### Lightning infrastructure

Tentative package: `backend/src/sketch2life/infrastructure/lightning/`

Provide ports/adapters for direct local Qwen3-VL structured understanding, faster-whisper ASR, story/scene planning, runtime config, artifact writing and safe error mapping. The existing HTTP provider wrapper is not required by this acceptance path.

### CLI

Tentative file: `backend/src/sketch2life/interfaces/cli/workflow_demo.py`

Parse arguments, build dependencies, invoke the orchestrator, print safe progress, write sanitized output and map statuses to exit codes. No business rules belong in the CLI.

## 7. Input and provenance

Default inputs:

```text
features/FEAT-020-backend-ai-workflow-demo/test-assets/input-image.png
features/FEAT-020-backend-ai-workflow-demo/test-assets/narration.wav
```

The image is synthetic child-style artwork. The narration says:

`Con bướm xanh đang bay gần bông hoa đỏ.`

Validate image MIME, decodability, dimensions, size, corruption, safety and checksum. Validate WAV container, PCM format, channel count, sample rate, bit depth, duration and decodability. Set input mode to `MULTIMODAL`.

Record safe source references, checksums, dimensions/audio metadata and provenance. Never include raw credentials, unnecessary local paths, unrestricted prompts or raw model payloads.

## 8. Age matrix and variation

### Catalog coverage

| Age band | Catalog guidance window | Golden records |
|---|---:|---:|
| `0-3` | 8–35 months across selected records | 5 |
| `3-6` | 42–71 months across selected records | 5 |
| `6-9` | 72–107 months across selected records | 5 |
| `9-12` | 108–155 months across selected records | 5 |

`--age-mode all` executes all four sub-runs using the same image/WAV. Source identity can remain stable; age-dependent context, candidate, objective, story complexity, material guidance and render intent must be evaluated separately.

### Selection algorithm

1. Generate a fresh random `run_seed` unless `--seed` is supplied.
2. Keep the raw seed in local run metadata and a safe fingerprint in the manifest.
3. Apply hard age, readiness, prerequisite, safety, supervision, material and active-status filters first.
4. Shuffle eligible candidates using the seed.
5. Apply no-immediate-repeat within the matrix/session.
6. Select activity/objective from the eligible set, never fixed first-match.
7. Support exact replay with `--seed`.

If only one eligible candidate remains, select it only if valid and record `variation_unavailable_reason=ONLY_ONE_ELIGIBLE_CANDIDATE`. Never invent variation by bypassing a rule or mutating the catalog.

The E2E must assert that all bands execute, fixed-seed replay is stable, and two unseeded runs produce different selection vectors when alternatives exist.

## 9. Montessori rules and demo constraints

Mandatory order:

```text
age → readiness → prerequisite → safety → supervision → material → active status → variation/ranking → objective → Gate B
```

- Readiness comes from observable golden-catalog criteria; no diagnostic inference.
- Primary material is preferred.
- Substitute may come only from the same activity record and its suitability/prohibited rules.
- Adult/guide supervision is mandatory.
- Duration comes from the selected activity record.
- No open flame, high heat, hot liquid or heating element.
- No sharp tools in an unsupervised flow.
- Stable, uncluttered work surface.
- Washable/non-toxic materials when catalog-compatible.
- No ingestion intent.
- No real child data.
- `0-3`: adult within arm’s reach, no loose small/detachable choking-risk parts, large washable materials, one action per step.
- `3-6`: adult handles restricted tools/substitutes, short concrete instructions, no rapid flashing.
- `6-9`: adult setup and safety check, ordered multi-step activity only when readiness passes.
- `9-12`: adult available for safety review/handoff, layered steps only when the record permits.
- Accessibility: visual plus spoken/text cue, no color-only meaning, reduced motion, high contrast, readable labels, structured safety/material fields.

Activity-specific catalog rules can make any of these stricter. The demo must return no-result/blocked status rather than weakening a rule.

## 10. Workflow stages

### 0 — Preflight

Load runtime/model/catalog/asset configuration and validate dependencies.

### 1 — Input validation

Validate and hash the image/WAV; create immutable source records.

### 2 — ASR

Run real faster-whisper/local ASR on the Vietnamese WAV. Record transcript, language, segments/confidence, model revision and timing. No precomputed transcript.

### 3 — VLM

Run real VLM on the original image. Permit observable objects, colors, spatial relations, topic, action, uncertainty and safety. Block diagnosis, personality, intelligence, certainty about emotion or other psychological inference.

### 4 — Fusion

Fuse transcript and VLM output with modality provenance and explicit conflict fields. Do not silently let voice override image.

### 5 — Gate A

Use a production mapper to create `SemanticAnchorSetV1`. In demo mode record `DEMO_OPERATOR`, `DEMO_AUTOPILOT`, timestamp, reason and input hash. Without autopilot, return `GATE_A_REQUIRED`.

### 6 — Montessori age matrix

Run four bands, golden readiness and all hard constraints. Select valid activity/objective/material using seeded variation. Produce context evidence.

### 7 — Gate B and experience

Record explicit Gate B by `DEMO_OPERATOR`, then compile `ExperienceSpecV1` and `ActivityHandoffV1` only after preconditions pass.

### 8 — Story/scene context

Create reality-grounded story and scene plans for original-art presentation, learning-media context and off-screen activity. Store age band, objective, identity hash, constraints and model provenance.

### 9 — Original-art render intent

Reference the original child-art artifact and checksum. Emit non-destructive render intent and static PixiJS IDs. Never redraw or replace the original.

### 10 — Deferred video

Emit `video.status=DEFERRED` and reason `VIDEO_GENERATION_DEFERRED_FOR_FIRST_BACKEND_DEMO`, with target duration metadata 5–10 seconds. Do not emit a generated video file or fake success.

### 11 — Activity handoff

Emit steps, material/substitute, objective, duration, supervision, safety, accessibility and selected asset IDs. The activity is real-world/off-screen and adult-led.

### 12 — Feedback/history

Create in-memory demo records labelled `source=DEMO_AUTOPILOT`; do not represent them as real caregiver observations.

### 13 — Result

Write one sanitized matrix manifest containing each sub-run, stage status, seed fingerprint, provenance, decisions, selection vector, asset IDs, deferred video and warnings.

## 11. State and contract semantics

```text
CREATED
→ INPUT_VALIDATED
→ UNDERSTANDING_PROPOSED
→ GATE_A_CONFIRMED
→ CONTEXT_READY
→ GATE_B_CONFIRMED
→ EXPERIENCE_READY
→ STORY_SCENE_READY
→ ART_PLAN_READY
→ VIDEO_DEFERRED
→ HANDOFF_READY
→ FEEDBACK_RECORDED
→ BACKEND_CONTEXT_READY
```

Every transition includes session ID, run ID, age band, expected/current version, command ID and provenance. Same command/request ID is idempotent. Stale versions return `STALE_SESSION_VERSION`.

Minimum statuses: `BACKEND_CONTEXT_READY`, `RUNTIME_NOT_READY`, `MEDIA_RECAPTURE`, `ASR_FAILED`, `AI_FAILED`, `CONTENT_UNSAFE`, `GATE_A_REQUIRED`, `GATE_B_REQUIRED`, `NO_ELIGIBLE_ACTIVITY`, `ASSET_CATALOG_MISS`, `STORY_PLAN_FAILED`, `SCENE_PLAN_FAILED`, `ART_OUTPUT_INVALID`, `VIDEO_DEFERRED`, `HANDOFF_INVALID`, `STALE_SESSION_VERSION`.

## 12. PixiJS asset boundary

PixiJS is not loaded or implemented in FEAT-020. The static catalog is under `assets/generated/pixi/` and contains 12 hand-authored SVGs:

- scene: butterfly, flower, sun, grass;
- motion: sparkle, dotted path;
- activity: material basket, learning goal, adult guide, safety shield, feedback, timer.

The catalog and selection files are:

- `ASSET_CATALOG.json`;
- `WORKFLOW_ASSET_SELECTION.json`;
- `AGE_BAND_RENDER_INTENTS.json`.

Backend emits IDs/render intents only. It does not embed SVG markup or generate missing assets. A missing asset returns `ASSET_CATALOG_MISS` or whole-drawing/non-rendered fallback. Assets remain `GENERATED_PENDING_REVIEW` until visual approval; they are not copied to `approved/` or `applied/` yet.

Age render intent changes presentation complexity only; Montessori eligibility remains backend-authoritative.

## 13. Single E2E test

Tentative file: `backend/tests/e2e/test_lightning_backend_workflow.py`.

Use one public test function that loads real adapters once and runs four sub-runs for `0-3`, `3-6`, `6-9`, and `9-12`.

Forbidden in this test: fixture IDs, fake adapters, network mocks, precomputed model output, monkeypatched success, video generation, PixiJS runtime loading and checked-in generated video.

Assertions:

1. all four age bands execute;
2. same image/WAV checksums are used in each sub-run;
3. real Vietnamese ASR and real VLM run;
4. schemas, safety and prohibited-inference checks pass;
5. fusion preserves provenance/conflicts;
6. Gate A/B use explicit `DEMO_OPERATOR` decisions;
7. golden readiness/material/supervision/duration rules apply;
8. activity selection is not fixed first-match;
9. seed fingerprint and selection vector are present;
10. fixed seed replay is stable;
11. unseeded runs vary when alternatives exist;
12. story/scene/art/handoff preserve identity hash;
13. video is `DEFERRED`, not generated;
14. asset IDs are valid and no runtime generation occurs;
15. feedback/history are labelled demo-generated;
16. terminal state is `BACKEND_CONTEXT_READY`;
17. manifest contains no secrets.

## 14. Implementation milestones

Implementation starts only after approval changes `approvals/TASK_APPROVAL.md` to `APPROVED`.

### M0 — Approval and ADR baseline

Confirm model revisions/checkpoints, direct Lightning runtime, seed policy, demo autopilot boundary, deferred video and exact module names.

### M1 — Runtime/input

Implement preflight, path overrides, image/WAV validation, checksums, provenance and safe artifact output.

### M2 — Real understanding

Implement direct VLM/ASR adapters, model manifest, schema/safety validation, fusion and production anchor mapper.

### M3 — Gates and Montessori

Connect session transitions, `DEMO_OPERATOR` gates, golden catalog rules, all-band matrix, constraints and seeded variation.

### M4 — Context and handoff

Connect story/scene, original-art render intent, deferred video, activity handoff and demo feedback/history.

### M5 — PixiJS boundary

Validate asset catalogs and emit asset IDs/render intents only. Do not implement PixiJS.

### M6 — CLI and E2E

Implement one command and one four-band real-AI E2E test. Run it in Lightning Studio.

### M7 — Evidence and closeout

Run validators/tests, capture sanitized feature-local evidence, update context/decisions/status, and create one grouped implementation commit.

## 15. Acceptance criteria

| ID | Criterion |
|---|---|
| AC-01 | Plan and approval gate exist before implementation. |
| AC-02 | Full GitHub-pulled repository runs in Lightning Studio without a required second server. |
| AC-03 | One command accepts replaceable image/WAV paths. |
| AC-04 | Real image and Vietnamese WAV pass validation/provenance. |
| AC-05 | Real ASR and VLM execute without fixture outputs. |
| AC-06 | Production mapper creates `SemanticAnchorSetV1`. |
| AC-07 | Fusion preserves modality conflicts/provenance. |
| AC-08 | All four catalog age bands execute in one E2E matrix. |
| AC-09 | Golden readiness and hard rules precede selection. |
| AC-10 | Material, substitute, safety, adult supervision and catalog duration rules are enforced. |
| AC-11 | Selection uses fresh seed/no-repeat and is not fixed first-match. |
| AC-12 | Explicit seed replay is stable; unseeded runs vary when alternatives exist. |
| AC-13 | Gate A/B use `DEMO_OPERATOR` and explicit demo mode. |
| AC-14 | Story, scene, original-art plan, handoff and feedback/history connect. |
| AC-15 | Original-art identity/hash is preserved. |
| AC-16 | Video is explicitly `VIDEO_DEFERRED`. |
| AC-17 | PixiJS asset IDs are valid; no PixiJS/runtime AI generation is used. |
| AC-18 | Terminal state is `BACKEND_CONTEXT_READY`, exit code zero. |
| AC-19 | One real-AI E2E public test covers the backend path. |
| AC-20 | Security, harness, architecture, skeleton, unit and E2E checks pass. |

## 16. Definition of Done

The feature is done only when the approved plan is implemented, the four-band E2E passes in Lightning Studio, the result reaches `BACKEND_CONTEXT_READY`, video is honestly deferred, PixiJS remains unimplemented, evidence is sanitized/local, and one grouped milestone commit contains the implementation and governance updates.
