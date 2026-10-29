# One dev-backend-to-Modal Vision smoke check — 2026-10-29

## Scope and execution roles

Later owner chat authorization and the bounded procedure are recorded in
`../approvals/BACKEND_DEMO_MODAL_SMOKE_AUTHORIZATION_20261029.md` and
`../plan/BACKEND_DEMO_MODAL_SMOKE_PLAN_20261029.md`. The original revision-1
PLAN/approval remain unchanged. This is one synthetic backend Vision check,
not approval for the wider app, model quality, or production use.

- Backend: owner-started `sketch2life.demo_main:app` on loopback port 8001 in
  `.worktrees/modal-vision-dev`, branch `feature/modal-vision-dev`, based on
  `origin/dev` commit `529cbef9`.
- Provider: owner-started existing Modal configuration from the original
  feature checkout. The owner first listed the prior App as stopped with zero
  tasks, then supplied `Serving...` for App `ap-PMAK4LcJOs8qXnndTL0Fwr`.
- The reported function URL matches the URL assigned to the backend process.
  The backend uses its existing `lightning_dev` Vision V2 adapter; no provider
  was added and production Runpod policy is unchanged.
- The assistant called only the loopback backend. Provider credentials stayed
  in that backend; no secret or actual `.env` contents were read or printed.

## Checks actually executed

1. Local OpenAPI inspection confirmed POST session-create, image-upload and
   understanding routes. The demo profile has no `/health` route.
2. Created one new synthetic demo session: HTTP 201, typed `SUCCEEDED`, version 0.
3. Uploaded the existing AI-generated combined crayon source using `IDENTITY_V1`:
   HTTP 200, typed `ImageAdmissionReceiptV2`, `ADMITTED`, observed version 1.
4. After the owner supplied Modal startup, a read-only session preflight
   confirmed `SUCCEEDED`, version 1 and unused understanding budget.
5. Sent exactly one explicit understanding command with narration `NONE`.
   It returned HTTP 200 and outer `MobileWorkflowResultV1` / nested
   `RawUnderstandingResultV1` status `SUCCEEDED`, observed version 2.

The source is `../assets/generated/crayon-controls-v1/03-house-and-sun.png`,
SHA-256 `2846a1b6a710e931da6abccf8c9858a938cbd021c0325bbd3f0c98d513fd0c36`.
The backend created its own receipt/artifact reference; an earlier direct-provider
receipt was not substituted. Source reference, SHA-256, session and correlation
identity checks passed throughout this run.

## Returned understanding metadata

| Check | Observed result |
| --- | --- |
| Client wall time | 23.938 seconds |
| Modal HTTP duration / execution | 23.0 / 19.5 seconds, owner-supplied server log |
| Start / completion (UTC) | 2026-10-29 07:43:37.832819 / 07:44:01.776615 |
| Start / completion (Asia/Saigon) | 2026-10-29 14:43:37.832819 / 14:44:01.776615 |
| Upstream contract | VisionUnderstandingResultV2, version 2.0 |
| Profile | QWEN3_VL_8B_INSTRUCT_BF16_V1 |
| Model | Qwen/Qwen3-VL-8B-Instruct |
| Revision | 0c351dd01ed87e9c1b53cbc748cba10e6187ff3b |
| Adapter | qwen3-vl-local-adapter-v2-b1 |
| Catalog hash | 72651b96d2c2259344efcb6fb3349807d42b56079a5422530db09c1590f00947 |
| Config hash | 3082f03f32a1cb26e6f5c25fe73813039460129b0f18a15e647b9f5ff08e3267 |
| Provider attempts / repair flag | 1 / true |
| Entities / actions / relations / themes | 4 / 0 / 0 / 0 |
| Narration | NOT_SUPPLIED |
| Progress | TOPIC_READY, gate_a_ready=true, gate_a_required=true |

Wire contract names/versions and the typed payload were checked explicitly.
Model provenance equals the pinned profile, and catalog/config/adapter identities
match. Repair true is permitted normalization metadata; no retry was issued.
Predicted labels and raw response bodies were not printed or persisted by this probe.
An entity count of four does not establish exact recognition or a quality pass.

## Evidence and duplicate prevention

`backend-demo-smoke-20261029-v1/` contains the local probe, actual admission,
sanitized state/immutable commands, `results.jsonl` and
`understanding-reserved.json`. The exclusive-create reservation was flushed and
fsynced before the inference-bearing POST. It is retained after success and
must not be removed to repeat this run. The probe stops on failures/unknown
outcomes and refuses further understanding sends for this run.

The helper imported successfully, passed focused Ruff E/F/I checks with cache
disabled, and received an independent source review of protocol, identity and
duplicate prevention. Initial formatting-cache access and import-order issues
were corrected before execution; no runtime source was changed.

## Limits and cleanup

This confirms the selected dev backend can use the existing Modal Qwen-only
Vision V2 path for this admitted synthetic image. It does not test the feature
branch's full backend, mobile UI, Gate A confirmation or subsequent workflow,
ASR, SAM, ranking, preference classification, planner, or video. No runtime
source/schema/model/prompt change, merge, commit or push occurred.

This run did not measure instantaneous GPU peak, billed duration/cost, cache
reuse, controlled cold/warm performance, or quality against Lightning L4.
The separate FEAT-003 quality gate and production policy are unchanged.

The owner subsequently supplied the provider log: four checkpoint shards loaded,
`vision_request_completed status=SUCCEEDED entities=4`, attempt 1, repair true,
and `POST /v2/vision -> 200 OK` with HTTP duration 23.0 s and execution 19.5 s.
The log ended in keyboard-interrupt shutdown and `App aborted` for
`ap-PMAK4LcJOs8qXnndTL0Fwr`, confirming this temporary Modal session stopped.
These server timings have a different scope from client wall time and are not
billed resource duration.

The owner then supplied `Application shutdown complete` and
`Finished server process [44944]`, confirming local backend shutdown as well.
Both tested processes are stopped. The bounded test and cleanup are complete;
the single-request reservation remains used and no further provider call was made.

Backend settings were process-local and the token file/virtual environment are
local-only. The dev-based worktree has no tracked source changes; Git publication
would not transfer that runtime configuration. Reports/probe/evidence remain in
the original feature checkout, uncommitted by this run.

