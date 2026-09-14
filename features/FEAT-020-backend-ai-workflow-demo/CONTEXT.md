# FEAT-020 — Backend AI Workflow Demo

**Status:** `IN_PROGRESS`
**Date:** 2026-09-12
**Scope:** backend-only, one-command, real-AI vertical workflow for Lightning Studio; no UI implementation.

## 1. Purpose

This feature turns the current collection of contracts, offline fixtures, partial AI adapters, and isolated services into one executable backend workflow that demonstrates the main Sketch2Life journey:

`real image` → `understanding` → `Gate A` → `Montessori recommendation` → `Gate B` → `story/scene plan` → `personalized art output` → `learning micro-video` → `off-screen activity handoff` → `feedback/history`.

The demo must run inside Lightning Studio after the repository is pulled from GitHub. It must not require a separately managed application server or a UI. A single command is the operator entry point.

This document records a plan only. Per repository governance, implementation is blocked until explicit approval is recorded in `approvals/TASK_APPROVAL.md`.

## 2. What the attached workflow image means

The supplied image is treated as the product/workflow target and a source of intended behavior. It is not an instruction to build a frontend, not a request to reproduce the image as an asset, and not a substitute for executable contracts.

The user request adds the execution constraints:

- pull the repository from GitHub in Lightning Studio;
- do not build a separate custom provider server for the demo path;
- backend only, with no UI integration;
- real AI models, not fixture input or fake adapters;
- one command should run the connected backend flow;
- use one arbitrary real image, with optional real narration audio when the full multimodal path is needed.

The image describes both image and voice input. An image by itself cannot exercise ASR. Therefore this feature defines `IMAGE_ONLY` as the default smoke mode and `MULTIMODAL` as an optional mode with a real WAV/audio file. The output must state which mode actually ran.

## 3. Source authority and current baseline

The implementation plan is based on the repository source register and current project records, especially:

- `docs/context/SOURCE_REGISTER.md`;
- `docs/CURRENT_SYSTEM_STATE.md` (a snapshot that must be refreshed after implementation);
- `features/FEAT-017-live-ai-dev-integration/LIVE_AI_GUIDE.md`;
- `features/FEAT-018-live-image-canvas-flow/CONTEXT.md` and `DECISIONS.md`;
- `features/FEAT-015-integration-readiness-review/src/integration_fixture/flow.py`;
- `features/FEAT-016-runtime-integration/src/runtime_integration/application.py`;
- the P1 experience compiler, contract schemas, catalog, learning-media resolver, and current live-understanding route.

The current repository already has useful building blocks, but it does not yet have the requested connected real-AI workflow:

1. The live HTTP route accepts a fixture identifier, performs fixture-backed ASR/VLM calls, returns a proposal, and stops before Gate A.
2. The Lightning HTTP client and provider wrapper exist, but the unfixture real-model smoke is not yet evidenced and the main route is not an arbitrary-image workflow.
3. The VLM-to-`SemanticAnchorSetV1` conversion is represented in a test helper rather than a production application mapper.
4. P1 compilation and Gate B contracts are strong and reusable, but are not connected to a real session command path.
5. The learning-media resolver is reviewed-cache-first and has no real video generator in the current path; a cache miss can fall back or block.
6. The art renderer is standalone and the complete backend orchestration does not yet produce a single end-to-end manifest.
7. Session, feedback, and history semantics exist in memory, not as a durable production store.
8. Mobile/UI integration is intentionally outside this feature.

The post-merge D3/P2-T1 work is already recorded as closed for its offline cohorts. Older snapshot language that says this work is still pending must not be used as the current implementation status.

## 4. Intended outcome

After approval and implementation, an operator can execute one command in Lightning Studio with a real image. The command loads the configured local Lightning model adapters, runs the workflow orchestrator, and writes a sanitized result manifest. With a configured video model, the successful terminal state is `WORKFLOW_COMPLETE`; if a required stage cannot run, the command fails with a typed stage/status and evidence rather than silently claiming completion.

Demo-only human decisions are explicit `DEMO_AUTOPILOT` decisions. They are recorded with actor, timestamp, reason, and decision mode, and are forbidden as an implicit production bypass.
