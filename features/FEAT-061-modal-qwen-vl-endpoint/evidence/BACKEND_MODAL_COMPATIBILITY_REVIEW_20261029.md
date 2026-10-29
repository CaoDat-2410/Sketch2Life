# Backend-to-Modal compatibility review — 2026-10-29

## Request and review boundary

The owner clarified that the question is whether the backend on `dev` and on the current feature branch can use the tested Modal AI endpoint as it uses Lightning. This is an offline source and Git-object review answering that question. It does not change runtime configuration, provider selection, deployment, contracts, prompts, or approvals, and it does not execute a backend-to-Modal request.

Compared revisions:

- `origin/dev`: `529cbef9c71c0b225dca0d6a88f50f099e05176e`.
- Current feature `HEAD`: `49f42e49c33871159f73cc419b6aad4837efbd04`, branch `feature/feat061-modal-qwen-vl-endpoint`.

Line references below refer to current feature source unless explicitly labelled `origin/dev`. Relative links resolve from this evidence directory. The root audit refreshed the remote-tracking ref with `git fetch origin refs/heads/dev:refs/remotes/origin/dev`, which completed successfully. The comparison then read the pinned Git objects; no merge, branch switch, working-tree replacement or backend-file copying occurred.

## Finding

**Both revisions contain an existing development adapter that can send the same authenticated Vision V2 request to the Modal Web Function URL.** The transport does not require a Lightning hostname. The existing `lightning_dev` configuration can therefore be reused for a bounded local Vision-only test without introducing a `modal` provider or changing the Runpod production policy.

This establishes source-level compatibility, not a passed integration test. The previously successful direct Modal synthetic requests establish endpoint observations only; they do not demonstrate either backend's upload, admission, artifact mapping, session workflow, or UI integration.

### Identical files in the two Git revisions

`git rev-parse origin/dev:<path>` and `git rev-parse HEAD:<path>` returned the same Git blob for every file below:

| Repository-relative path | Shared Git blob |
| --- | --- |
| `backend/src/sketch2life/infrastructure/ai/lightning_client.py` | `8694cccdd44ae815d85466993461b5ab4094464b` |
| `backend/src/sketch2life/infrastructure/ai/lightning_vision_v2.py` | `58a0f0e84c4bd319bca667c1d7e4fdfc15c0e17e` |
| `backend/src/sketch2life/application/services/live_image_demo.py` | `b98fe1fac02c335a3105c8b825785e7e4bd89a64` |
| `backend/src/sketch2life/interfaces/http/routers/images.py` | `9a311b8b69517640fe0c734b66993ff4848fc0be` |
| `apps/ui-mobile/src/demo/api.ts` | `1cdcdf46c4af3d13b8be12c230ff29a096526e65` |
| `apps/ui-mobile/BaoApp.tsx` | `5e823c65ceaea4ea71017cd1c210c8e45a4d644e` |
| `tools/lightning_vision_v2_server.py` | `a95fdff89f79d97577487eb7cf40362ab4a91c86` |

The whole backends are not identical. In particular, `dev` has newer classroom/demo composition and storage changes. Do not replace the `dev` backend with the feature branch's backend to consume the Modal endpoint.

## Existing request path and application entrypoints

The current mobile workflow sends:

1. `POST /v1/sessions` to create a local demo session.
2. `POST /v1/sessions/{session_id}/media/image` to upload and admit a synthetic non-child image.
3. `POST /v1/sessions/{session_id}/understanding` for an explicit analysis command.
4. The backend builds `VisionUnderstandingRequestV2` and sends `LightningVisionRequestV2` contract version `2.0` to provider `POST /v2/vision`.

Sources: [mobile client](../../../apps/ui-mobile/src/demo/api.ts), lines 283, 318 and 380; [image routes](../../../backend/src/sketch2life/interfaces/http/routers/images.py), lines 26 and 168; [understanding service](../../../backend/src/sketch2life/application/services/live_image_demo.py), line 933; [V2 adapter](../../../backend/src/sketch2life/infrastructure/ai/lightning_vision_v2.py), line 38. The V1 session/workflow URL and `MobileWorkflowResultV1` wrapper do not make the provider call Vision V1.

| Revision | Entrypoint | Suitability for this test |
| --- | --- | --- |
| Current feature | `sketch2life.main:app` | Existing combined app includes demo image/session routes and constructs the V2 adapter. |
| `origin/dev` | `sketch2life.demo_main:app` | Dedicated local/in-memory demo app; suitable for this isolated workflow. |
| `origin/dev` | `sketch2life.main:app` | Combined compatibility app also includes this workflow. |
| `origin/dev` | `sketch2life.classroom_main:app` | Does not mount demo image/session routes or construct the demo Vision adapter; changing its AI URL alone does not add that workflow. |

Current sources: [main](../../../backend/src/sketch2life/main.py), line 3; [app composition](../../../backend/src/sketch2life/interfaces/http/app.py), lines 376, 397, 559 and 700. Dev-only source references, read with `git show origin/dev:<path>`: `backend/src/sketch2life/demo_main.py:3`, `backend/src/sketch2life/classroom_main.py:3`, `backend/src/sketch2life/interfaces/http/app.py:392`, `:603`, `:704`, `:709` and `:784`, and `backend/src/sketch2life/interfaces/http/router_composition.py:24` and `:30`.

The separate legacy [live-understanding route source](../../../backend/src/sketch2life/interfaces/http/routers/live_understanding.py), line 103, calls V1 vision and ASR. It is not the mobile image workflow above and is not a substitute for the V2 test.

## Transport, configuration and authentication

[UrllibJsonTransport](../../../backend/src/sketch2life/infrastructure/ai/lightning_client.py), lines 82–105, requires HTTPS outside loopback development, requires a nonempty token for a remote host, joins the configured base URL and operation path, and sends `Authorization: Bearer <token>`. It has no Lightning-domain allowlist, so an HTTPS Modal Web Function host satisfies its host checks.

The feature [adapter composition](../../../backend/src/sketch2life/interfaces/http/app.py), lines 700–729, and dev's corresponding `app.py:784–813` both use `settings.lightning_ai_base_url`, `settings.lightning_ai_token_file`, `settings.ai_request_timeout_seconds` and `settings.lightning_vision_v2_path`. They do not construct this adapter when the environment is `test`, the provider is not `lightning_dev`, the base URL is empty, or the token-file configuration/read fails.

The proposed local backend values are configuration instructions only; none was applied or read back during this review:

```dotenv
SKETCH2LIFE_ENV=local
SKETCH2LIFE_AI_PROVIDER=lightning_dev
SKETCH2LIFE_LIGHTNING_AI_BASE_URL=https://<active-modal-web-function-host>
SKETCH2LIFE_LIGHTNING_AI_TOKEN_FILE=${IGNORED_LOCAL_TOKEN_FILE_PATH}
SKETCH2LIFE_LIGHTNING_VISION_V2_PATH=/v2/vision
SKETCH2LIFE_AI_REQUEST_TIMEOUT_SECONDS=120
```

- Use the Web Function URL root as the base URL, without appending `/v2/vision` there.
- The token file contains the matching raw bearer value injected on Modal as `LIGHTNING_DEV_AUTH`; do not prefix the file contents with `Bearer `. No credential value is recorded here.
- [The reused server handler](../../../tools/lightning_vision_v2_server.py), lines 499–536, checks that bearer, source identity/hash/type, the 5,000,000-byte limit, and passed media admission. A hand-built image request without admission is insufficient.
- V2 selects the fixed `QWEN3_VL_8B_INSTRUCT_BF16_V1` profile in `live_image_demo.py:937`. Changing `SKETCH2LIFE_LIGHTNING_MODEL_PROFILE` is not required to select that V2 model.
- [Settings](../../../backend/src/sketch2life/infrastructure/config/settings.py), lines 19, 36–43, 62 and 99, load local settings and cache them; the app also constructs adapters at startup. Restart the backend after an operator changes local settings.
- Production still requires `runpod` under `settings.py:78–82`. This review proposes no production change.
- The mobile client uses `EXPO_PUBLIC_API_URL` for the backend address (`src/demo/api.ts:254–256`). Keep the provider URL and bearer file on the backend. The active app uses `AppContext.tsx:202` to create the workflow API client; the separate mock flag in `src/config/apiConfig.ts` does not control that client.

## Qwen-only and timing limits

The [Modal wrapper](../../../deployment/modal/qwen_vision_v2.py), lines 117–127, exposes only `GET /health` and `POST /v2/vision`. Its absence from the `dev` tree does not prevent a backend client there from consuming an already-running compatible endpoint.

The existing backend uses one `lightning_ai_base_url` across multiple adapters. Pointing it at this Qwen-only endpoint also points the configured ASR, child-preference classifier, activity ranker, story/video, and any enabled optional adapters at the same host. Modal does not supply their `/v1/asr`, `/v2/profile/preferences/classify`, `/v2/p1/activity-rank`, `/v1/story-video/*`, SAM, localization, segmentation, or Pixi-planning operations. Those live operations cannot be assumed to work and will encounter missing routes if invoked. Reusing the Vision transport is not replacement of the complete Lightning service.

Relevant sources: `app.py:630`, `:652`, `:736`, `:818`, `:852` and `:889`; [classifier](../../../backend/src/sketch2life/infrastructure/ai/lightning_child_preference_classifier.py), line 38; [ranker](../../../backend/src/sketch2life/infrastructure/ai/lightning_activity_ranker.py), line 30; [story/video adapter](../../../backend/src/sketch2life/infrastructure/ai/lightning_story_video.py), lines 51–54.

For the first isolated test use narration `NONE`, which avoids ASR. Typed narration can travel inside the Vision request, but was not validated as a backend-to-Modal flow in this review. Avoid audio, preference classification, activity ranking, video and optional SAM/Pixi-planner operations in the first smoke check.

The backend transport defaults to 120 seconds (`settings.py:62`); the mobile understanding request allows 150 seconds (`src/demo/api.ts:385`); the Modal function has a 150-second execution limit and 300-second startup setting (`deployment/modal/qwen_vision_v2.py:90–91`). Cold start, queue delay, network delay, and total backend/UI time still need observation through the complete chain. The V2 adapter has no automatic retry loop (`lightning_vision_v2.py:38–43`); a later explicit retry may consume another inference.

The owner's `App aborted` shutdown means the temporary serving session is stopped. Publishing a Git branch does not start Modal, deploy a backend, configure either runtime, or prove end-to-end behavior.

## Proposed next verification sequence — not executed

This sequence is available independently on each revision, without merging branches, copying a backend tree, adding a provider, or changing production:

1. Prepare the chosen backend's existing local runtime and the proposed ignored local configuration/process environment before starting GPU work. Confirm existing image-admission/runtime dependencies and safe token-file handling without displaying credentials. Do not install model weights or GPU dependencies into Windows; any missing dependency remains an explicit environment gap.
2. Start a deliberately bounded owner-operated Qwen-only serving session using the already tested Modal configuration, and obtain its active function URL. Preserve its existing model/profile/secret choices and use the active host as the backend base URL.
3. Start current-feature `sketch2life.main:app`, or dev's `sketch2life.demo_main:app`. Keep this as local synthetic development, with the existing local demo behavior.
4. Check local backend health, then create a session and upload one existing synthetic non-child control through the backend's actual image-admission route. Submit one explicit understanding command with narration `NONE` and current session version/idempotency metadata.
5. Verify the workflow response and nested typed vision outcome, not HTTP 200 alone. Check source/correlation identity, profile/provenance, returned subjects, timing, and Gate A behavior. Record sanitized feature-local evidence; do not retain credentials or raw generated text.
6. Only after the backend chain passes, point the existing mobile workflow at that local backend and verify one upload/understanding/Gate A interaction. Stop before unsupported AI routes, and stop the temporary Modal app when the bounded check ends.

## Checks actually performed

- Read the project context/source register, FEAT-061 context/plan/approval/status, source files, placeholder `.env.example` files, and the relevant Git objects.
- Compared the pinned revisions and verified identical Git blob IDs for the seven files listed above.
- Inspected both app compositions/entrypoints, transport URL and bearer rules, request contracts, fixed V2 profile, timeout settings, and other adapters sharing the base URL.
- Created this evidence note only. No secret files or actual `.env` files were read. No live HTTP, Modal/GPU operation, package installation, runtime configuration change, import/startup check, or backend/mobile integration test was performed. No merge, deployment, commit, push, provider change, or approval edit was performed by this review.

**Unverified:** startup/dependency readiness on either chosen local runtime, a live backend-to-Modal request on either revision, actual timeout behavior through that chain, and mobile rendering/interaction of the resulting proposal. Prior direct synthetic endpoint successes do not close those checks or the separate model-quality gate.
