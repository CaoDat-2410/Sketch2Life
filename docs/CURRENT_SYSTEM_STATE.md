# Sketch2Life — hiện trạng hệ thống, cấu trúc, luồng hoạt động và contract

> Snapshot kiểm tra ngày **2026-09-11** trên checkout codex/feat-018-contract-plan, commit 3f8d856 (test(feat018): verify online model compatibility at p1 boundary).
>
> Đây là snapshot của checkout hiện tại, không phải tuyên bố rằng toàn bộ target architecture đã chạy production. Mỗi phần được phân loại là **Implemented**, **Offline/fixture-only**, **Accepted architecture**, **Planned**, hoặc **Open/blocked**.

## 1. Tóm tắt điều hành

Sketch2Life biến bản vẽ và lời kể của trẻ thành một trải nghiệm học tập ngắn, sau đó chuyển trẻ sang một hoạt động Montessori ngoài màn hình và thu feedback từ người lớn. Product không phải generic image generator: bản vẽ gốc phải được giữ nguyên, suy luận AI phải được review, activity phải qua luật Montessori xác định và người lớn phải duyệt identity/version trước khi nội dung số hay activity vật lý được dùng.

| Khu vực | Tình trạng hiện tại | Mức độ |
|---|---|---|
| Governance/context/security | Harness và validators đã có | Chạy local |
| Backend | FastAPI health/live-fixture route, typed contracts, P2 admission, P1 compiler/catalog, AI adapters/provider guard | Từng boundary chạy; chưa production runtime đầy đủ |
| Mobile | Android-only React Native fixture flow, optional live-fixture call, auth port, Pixi protocol boundary | Fixture UI chạy; capture/auth/full session chưa có |
| P1 Montessori | 100 MVP activities, 20 golden activities, deterministic rules, ExperienceSpec, Gate B integrity | Offline; records vẫn production_eligible=false |
| P2 understanding | Media validation, ASR/VLM contract generations, fixtures, Lightning synthetic route, Qwen/Whisper boundaries | Offline/dev; model chưa freeze production |
| P3 renderer | PixiJS + GSAP standalone package, closed Motion DSL, provenance, fallback | Package chạy; chưa nối hoàn chỉnh vào mobile bridge |
| P4 learning media | Cache-first resolver, reviewed identity check, typed fallback/block, replay | Offline/in-memory; chưa có provider worker/S3 |
| Runtime integration | FEAT-015 fixture flow và FEAT-016 in-memory session/job semantics | Test harness; chưa là API/session persistence |
| Production infra/release | Compose + Android Gradle skeleton | Chưa wire migration/worker/auth/signing/release |

Kết luận: **đây là foundation với nhiều offline/fixture workstream đã harden, chưa phải sản phẩm end-to-end production-ready**.

## 2. Phạm vi và nguồn sự thật

### 2.1 Authority order

Khi tài liệu mâu thuẫn, thứ tự là:

1. Chỉ dẫn trực tiếp của project owner trong task hiện tại.
2. ADR hoặc decision đã được approval.
3. Mã nguồn và evidence tái lập trong checkout hiện tại.
4. Context/plan/approval của feature.
5. Handbook/workbook/reference bên ngoài trong docs/context/SOURCE_REGISTER.md.

External reference không tự cấp quyền implementation. Tài liệu này không chứa raw handbook/workbook, secret, seed account hoặc real child data.

### 2.2 Nguồn đã đối chiếu

- AGENTS.md: workflow và security rules.
- docs/context/PROJECT_CONTEXT.md: product invariants và owner decisions.
- docs/context/SOURCE_REGISTER.md: reference boundary.
- docs/SYSTEM_BASELINE.md: baseline ngày 2026-08-24; còn giá trị cho kiến trúc nền nhưng câu “product implementation not started” đã cũ so với FEAT-015–018.
- docs/architecture/OVERVIEW.md, BASE_PROJECT_STRUCTURE.md, CONTRACTS_AND_INTEGRATION.md.
- features/FEAT-015-integration-readiness-review/: readiness review và offline cross-workstream fixture.
- features/FEAT-016-runtime-integration/: fixture-only application/session/job runtime.
- features/FEAT-017-live-ai-dev-integration/: live AI development evidence/guide.
- features/FEAT-018-live-image-canvas-flow/: P1 compiler, P2 D2 image admission, P3/P4 offline integration và contract freeze.

### 2.3 Checkout caveat

Tại lúc kiểm tra, git status --short --branch cho thấy:

~~~
## codex/feat-018-contract-plan...origin/codex/feat-018-contract-plan [ahead 53]
 M features/FEAT-018-live-image-canvas-flow/approvals/TASK_APPROVAL.md
?? backend/tests/unit/test_p1_online_model_compatibility.py
?? features/FEAT-018-live-image-canvas-flow/plan/P1_ONLINE_MODEL_COMPATIBILITY_TEST_PLAN.md
~~~

Ba file trên hiện đã được ghi nhận trong commit 3f8d856 sau lần kiểm tra ban đầu. Tại thời điểm chốt snapshot, working tree chỉ còn các file FEAT-019/report mới.

## 3. Product boundary và invariants

### 3.1 Actor/account model

| Mode | Account độc lập | Trách nhiệm |
|---|---:|---|
| Parent | Có | Consent, supervision, Gate A/B, feedback |
| Guide | Có | Montessori review, activity/objective approval, feedback |
| Child | Không | Vẽ, kể, xem trải nghiệm và làm activity trong supervised session |

Parent/guide dùng Google Sign-In hoặc email/password. Firebase chỉ chứng minh identity; backend quyết định role, guardian relationship, quyền session/artifact và authorization.

### 3.2 Invariants

1. Original child media immutable; derivative không âm thầm thay source.
2. Derivative giữ source artifact IDs, hash/version, model/config, actor/reason và timestamp phù hợp.
3. Gate A là human confirmation/correction của multimodal understanding.
4. Gate B khóa đồng thời activity identity/version và learning-objective identity/version.
5. Safety, age/readiness, prerequisite, material và supervision rules chạy trước model selector.
6. Original-art animation và learning media là hai artifact riêng.
7. Reviewed learning asset được resolve trước cache-miss generation.
8. AI/media failure trả fallback typed và không xóa off-screen activity.
9. Async result mang expected session version; completion cũ không mutate state mới.
10. Ready session phải dẫn tới Activity Bridge và feedback.
11. MVP development chỉ dùng fixture/synthetic data.

## 4. Cấu trúc repository

### 4.1 Sơ đồ cấp cao

~~~
CAPSTONE/
├─ apps/
│  ├─ mobile/                 React Native Android-only client active
│  ├─ api/                    inbound API boundary placeholder
│  ├─ child-app/             placeholder boundary
│  └─ parent-web/            placeholder boundary
├─ backend/
│  ├─ src/sketch2life/        Python modular monolith
│  ├─ tests/                  backend contract/unit tests
│  ├─ pyproject.toml          Python 3.12–3.13 package/dependencies
│  └─ .env.example            placeholder runtime settings
├─ services/                  future replaceable service boundaries
├─ packages/
│  ├─ art-renderer/           PixiJS/GSAP renderer
│  ├─ contracts/              language-neutral contract boundary
│  ├─ domain-montessori/      Montessori schema/spec boundary
│  ├─ domain-session/         session boundary placeholder
│  ├─ domain-experience/      experience boundary placeholder
│  ├─ application/            application boundary placeholder
│  ├─ infrastructure/         adapter boundary placeholder
│  └─ telemetry/              telemetry convention placeholder
├─ data/                      activity catalog + fixture manifests
├─ infra/                     infrastructure skeleton
├─ tests/                     shared Montessori fixtures/tests
├─ tools/                     validators, consoles, smoke tools
├─ scripts/                   replay entrypoints
├─ docs/                      architecture, ADR, context, setup, security
├─ features/                  plan/approval/evidence/fixture isolation
├─ compose.yaml               PostgreSQL + Redis + MinIO local stack
├─ package.json               root validation/type/test scripts
└─ AGENTS.md                  repository operating rules
~~~

### 4.2 Backend map

~~~
backend/src/sketch2life/
├─ main.py
├─ interfaces/http/
│  ├─ app.py                         FastAPI composition root
│  └─ routers/
│     ├─ health.py                   GET /health
│     └─ live_understanding.py       POST /v1/live-understanding
├─ application/
│  ├─ ports/                         AI, identity, decoder, policy interfaces
│  └─ services/
│     ├─ image_admission.py          FEAT-018 bounded snapshot admission
│     ├─ media_validation.py         deterministic PNG/WAV quality decision
│     ├─ p1_experience.py             P1/Gate B/ExperienceSpec
│     ├─ learning_media_resolver.py  cache-first resolver
│     └─ learning_media_fallback.py  typed fallback chain
├─ domain/understanding/             admission and quality policy
├─ contracts/schemas/                media, ASR, vision, P1, P4 contracts
├─ infrastructure/
│  ├─ ai/                            fake, Lightning, Whisper, Qwen boundaries
│  ├─ understanding/                 fixture/Whisper/Qwen adapters
│  ├─ catalog/p1_catalog.py
│  ├─ media_validation/              file inspector + PyAV adapter
│  └─ config/settings.py
└─ benchmark/                        ASR/VLM readiness and quality studies
~~~

### 4.3 Mobile map

~~~
apps/mobile/
├─ android/                           native Android project
├─ src/app/AppRoot.tsx                mounts FixtureFlowScreen
├─ src/features/fixture/
│  ├─ FixtureFlowScreen.tsx            reviewable UI harness
│  ├─ fixtureFlow.ts                   reducer/state/fixture contract
│  └─ rendererLifecycle.ts             sequence-aware bridge reducer
├─ src/bridge/pixi/
│  ├─ protocol/messages.ts             protocol version 1
│  └─ validation/isRendererMessage.ts
├─ src/infrastructure/
│  ├─ api/liveUnderstanding.ts         backend-only synthetic client
│  └─ auth/AuthSessionPort.ts          provider-neutral auth port
└─ __tests__/
   ├─ fixtureFlow.test.ts
   └─ bridgeProtocol.test.ts
~~~

Mobile baseline: com.sketch2life.mobile, minSdk 29, targetSdk 36, compileSdk 37, React Native 0.87, TypeScript, React Query, Zod và WebView. Không có iOS target.

### 4.4 Feature records

| Feature | Tình trạng/ý nghĩa |
|---|---|
| FEAT-000–014 | Harness, stack, Montessori, multimodal, mobile/backend foundation, security, allocation, golden hardening |
| FEAT-015 | Readiness review và offline cross-workstream fixture |
| FEAT-016 | Fixture-only application/session/job runtime; context status REVIEW |
| FEAT-017 | Live AI development integration evidence/guide; không phải production rollout |
| FEAT-018 | Active branch: P1 complete, P2-T1 D2 accepted, P3/P4 offline integration; downstream live/production pending |
| FEAT-019 | Report hiện trạng này; documentation-only |

## 5. Kiến trúc và dependency direction

### 5.1 Kiến trúc đích

~~~
apps / interface adapters
        ↓
application use cases + ports
        ↓
domain entities, policies, state machines
        ↓
versioned contracts
        ↑
infrastructure adapters: DB, object storage, queue, AI, telemetry
~~~

Modular monolith là boundary đầu tiên. Chỉ tách service khi evidence chứng minh chi phí vận hành hợp lý. Domain không import FastAPI, ORM, queue SDK, provider SDK hoặc UI. Application phụ thuộc domain và ports; infrastructure implement ports và map dữ liệu ngoài thành contract/domain type.

### 5.2 Topology đích

~~~mermaid
flowchart LR
    Parent[Parent / Guide] --> Mobile[Android React Native]
    Child[Child supervised mode] --> Mobile
    Mobile -->|HTTPS + Firebase ID token| API[FastAPI modular monolith]
    API --> Auth[Firebase Authentication verifier]
    API --> Domain[Application + Domain]
    Domain --> DB[(PostgreSQL)]
    Domain --> Queue[Redis / RQ]
    Domain --> Object[(S3-compatible storage)]
    Domain --> AiPort[AiGateway port]
    AiPort --> Lightning[Lightning dev/fixture]
    AiPort --> Runpod[Runpod production target]
    Mobile --> Bridge[PixiJS + GSAP controlled bridge]
~~~

### 5.3 Topology thực tế trong checkout

~~~mermaid
flowchart TD
    App[AppRoot] --> Fixture[FixtureFlowScreen]
    Fixture --> Reducer[fixtureFlow reducer]
    Fixture -. optional synthetic live call .-> LiveClient[requestLiveUnderstanding]
    LiveClient --> LiveRoute[POST /v1/live-understanding]
    LiveRoute --> FixtureInputs[FixtureInputs.load]
    LiveRoute --> LightningAdapters[Lightning ASR/Vision adapters]
    LightningAdapters -. configured only .-> Lightning[Lightning endpoint]
    P1[P1ExperienceCompiler] --> Catalog[offline catalog/fixtures]
    Admission[Feat018ImageAdmission] --> Decoder[ImageDecoderPort / PyAV]
    Media[LearningMediaResolver + Fallback] --> InMemory[In-memory asset store]
    Renderer[art-renderer] --> Browser[PixiJS browser demo]
    Runtime[FEAT-016 SessionAggregate] --> LocalJob[LocalJobStore + LocalTransport]
~~~

PostgreSQL, Redis, MinIO, Firebase, S3, RQ, Android capture và production provider chưa nằm trên một đường chạy hoàn chỉnh.

## 6. Luồng hoạt động

### 6.1 Mobile fixture flow

AppRoot mount trực tiếp fixture harness; đây chưa phải production navigation.

~~~
capture (session v1)
  → Ask the fixture AI
gate-a (v2)
  → Confirm meaning
gate-b (v3)
  → Approve this activity
experience (v4)
  → Play drawing reveal / simulate media fallback
handoff
  → Start activity
feedback (v5)
  → Save feedback
complete (v6)
~~~

Reducer fixtureFlow.ts có semantics:

1. RUN_FIXTURE_AI: chỉ từ capture; proposal butterfly, version 1→2.
2. START_LIVE_AI: chỉ bật loading và vẫn ở capture.
3. LIVE_AI_SUCCEEDED: chỉ nhận khi loading; sang Gate A nhưng chưa confirm.
4. CONFIRM_GATE_A: chỉ khi proposal ready; sang Gate B, version 2→3.
5. APPROVE_GATE_B: chỉ sau Gate A; khóa ACT-0004 v2 + OBJ_MOVEMENT_COORDINATION v1, version 3→4.
6. SIMULATE_MEDIA_FALLBACK: chỉ đổi media status, không làm mất activity.
7. PLAY_EXPERIENCE: chỉ khi renderer ready; sang handoff.
8. START_ACTIVITY: sang feedback, version 4→5.
9. SUBMIT_FEEDBACK: sang complete, version 5→6.
10. Command sai state hoặc duplicate không mutate state.

Màn hình đang dùng DrawingPreview synthetic/CSS-like butterfly. Pixi bridge là boundary intent; màn hình này chưa mount browser Pixi player thật.

### 6.2 Live-understanding synthetic backend

Mobile gọi requestLiveUnderstanding() mặc định tới http://10.0.2.2:8000 trong emulator:

~~~http
POST /v1/live-understanding
Content-Type: application/json
Accept: application/json
~~~

~~~json
{
  "mode": "live-lightning",
  "fixture_id": "integration-fixture-v1",
  "session_id": "session-fixture-001",
  "expected_session_version": 1,
  "request_id": "optional-client-generated-id"
}
~~~

live_understanding.py:

1. Parse Pydantic request với extra=forbid, mode/fixture ID là literal.
2. Reject nếu ai_provider != lightning_dev (503).
3. Reject nếu expected version khác 1 (409 STALE_SESSION_VERSION).
4. Load synthetic fixture root.
5. Tạo backend-only UrllibJsonTransport, đọc token từ secret file và tạo Lightning ASR/Vision adapters nếu chưa inject.
6. Chạy ASR/vision trên fixture sau media_validation=PASS.
7. Trả LiveUnderstandingResultV1 dạng dictionary với status, request/session/version, fixture, proposal label, gate_a_required=true, ASR và vision payload.

Route chỉ tạo proposal và dừng trước Gate A. Nó chưa tạo backend session aggregate, persist artifact, gọi P1/Gate B, queue job hoặc verify Firebase trong router. Đây là dev smoke boundary, không phải public API.

### 6.3 FEAT-015 offline integration fixture

Fixture integration-fixture-v1 có drawing/audio synthetic, manifest/hash, expected ASR/vision/P1/Gate A/Gate B/P3/P4/handoff/feedback.

~~~
load_fixture + verify source hashes
  → fuse_modalities(ASR, vision)
  → Gate A confirmation
  → P1 filter bằng context adult
  → Gate B approval với canonical identity
  → validate WHOLE_DRAWING manifest/hash
  → P4 cache HIT hoặc fallback/block
  → Activity Handoff vẫn reachable
~~~

| Scenario | Kết quả |
|---|---|
| happy_cache_hit | READY_FOR_OFFSCREEN_ACTIVITY, handoff true |
| modality_conflict_requires_gate_a | giữ cả claims, GATE_A_REQUIRED |
| no_eligible_activity_add_context | CONTEXT_REQUIRED |
| cache_miss_fallback | fallback nhưng handoff còn |
| blocked_learning_media | media blocked nhưng handoff preserved |
| asset_integrity_failure | reject hash/manifest |
| invalid_media_recap | recapture, chưa gọi AI |
| stale_gate_or_completion | stale version bị reject |

Đây là immutable cross-workstream test package, không phải shared mutable runtime/database.

### 6.4 FEAT-016 fixture runtime

State aggregate:

~~~
CREATED
 ├─ invalid media → MEDIA_RECAPTURE
 └─ valid media → GATE_A_PENDING
                  └─ confirm → UNDERSTANDING_PROPOSED
                               ├─ thiếu context → CONTEXT_REQUIRED → re-evaluate
                               └─ candidate → GATE_B_PENDING
                                             └─ approve → CANDIDATES_READY
                                                         → EXPERIENCE_READY
                                                         → HANDOFF_READY
                                                         → FEEDBACK_RECORDED
~~~

CommandEnvelope có command ID, session ID, expected version, actor ref và timezone-aware timestamp. _apply() replay cùng command ID bằng snapshot cũ; session ID sai và version cũ bị reject; command hợp lệ tăng version một lần. LocalJobStore reject stale completion/cancellation và không mutate terminal job. LocalTransport chỉ nhận RuntimeCommandV1/RuntimeResultV1 version 1.0.

FEAT-016 code còn nằm trong feature folder, chưa gắn FastAPI production route, DB repository, RQ worker, S3 hoặc mobile API client.

### 6.5 Luồng P1

P1ExperienceCompiler nhận SemanticAnchorSetV1 đã Gate A confirmed, P1ContextV1, typed templates và objective title map.

1. Gate A chưa confirmed → block.
2. Thiếu age/readiness/completed activities/materials/supervision/policy/candidate status → MISSING_CONTEXT.
3. Tìm template theo exact label/tag; token score chỉ xếp candidate.
4. Hard rules: active status, age, readiness, prerequisite, supervision, policy và material.
5. Không candidate hoặc equal-score ambiguous → block.
6. Chọn canonical activity/objective/template refs.
7. Fit evaluation gồm drawing relevance, objective alignment, video continuity, Montessori safety; threshold mặc định 80.
8. Strict continuity kiểm tra semantic kind, exact anchor label/tag, objective membership, bridge và downstream plans.
9. Compile immutable ExperienceSpecV1, tạo spec_id và spec_sha256 bằng canonical hash.
10. Gate B re-check catalog/version/identity/hash; pass mới tạo ActivityHandoffV1.

Data hiện có 100 MVP activities, 20 objectives, 20 golden activities và 20 material groups. Tất cả vẫn synthetic/provisional và production_eligible=false.

### 6.6 P2 image admission/media validation

Feat018ImageAdmission:

1. Mở source một lần và đọc bounded snapshot tối đa max_file_bytes + 1.
2. Oversized file bị reject trước khi hash.
3. Hash snapshot hợp lệ.
4. Inject ImageDecoderPort, decoder nhận bytes chứ không nhận path.
5. Đọc metadata, frame count, decode một frame và cross-check.
6. Chỉ admitted mới tạo SourceMediaReferenceV1 có hash.

FileMediaSignalInspector đọc PNG/WAV, không normalize/rewrite/upload. MediaValidationResultV1 quyết định PASS hoặc RECAPTURE và trả reason ổn định cho image dimensions/readability/luminance/blur/framing và audio duration/silence/speech/clipping. D2 đã review/accepted; D3 performance/memory và producer migration còn pending.

### 6.7 P3 original-art renderer

~~~
unknown input
  → Zod validate ArtAnimationPlan
  → known target IDs + unique motion IDs
  → source asset/provenance instructions
  → Pixi texture load
  → closed Motion DSL compile
  → GSAP playback
  → PLAYBACK_STARTED / PLAYBACK_COMPLETED
~~~

Motion DSL: MOVE, MOVE_TO, SCALE, ROTATE, FADE, FLY, JUMP, DRAW_REVEAL. Coordinates 0..1; stage 240..4096; duration 0.05..30; scale/rotation/opacity bounded. Extraction/mask failure tạo whole-drawing DRAW_REVEAL + conservative SCALE, giữ source ID/version/hash. Package có browser demo/benchmark/test; chưa phải full React Native WebView integration.

### 6.8 P4 learning media

LearningMediaResolver lookup exact cache_key:

1. Miss → BLOCKED/CACHE_MISS, không gọi generator.
2. Activity/objective/renderer identity mismatch → BLOCKED/STALE_MEDIA.
3. Asset STALE/CORRUPT/UNSAFE → typed block.
4. Reviewed + available hit → READY, generation_called=false.
5. Fallback có thể là STILL_NARRATION, WHOLE_IMAGE_REVEAL hoặc SUPERVISED_HANDOFF, luôn giữ identity request.

Hiện store là InMemoryLearningMediaStore; chưa có S3, media worker, live provider generation, video validation runtime hoặc retention job.

## 7. State machine và version semantics

### 7.1 Mobile fixture state

FixtureFlowState giữ:

~~~
step: capture | gate-a | gate-b | experience | handoff | feedback | complete
sessionVersion: number
aiStatus: idle | loading | ready | error
aiMode: fixture | live-backend
proposalLabel: string | null
gateAConfirmed: boolean
gateBApproved: boolean
mediaStatus: pending | cache-hit | fallback
rendererStatus: idle | ready | played
feedbackSubmitted: boolean
~~~

Đây là client-local reducer, không phải server-side source of truth.

### 7.2 FEAT-016 session state

SessionState gồm CREATED, MEDIA_RECAPTURE, UNDERSTANDING_PROPOSED, GATE_A_PENDING, CONTEXT_REQUIRED, CANDIDATES_READY, GATE_B_PENDING, EXPERIENCE_READY, HANDOFF_READY và FEEDBACK_RECORDED.

SessionSnapshot giữ source artifacts, raw understanding, Gate A, P1 context, Gate B, experience artifacts, handoff flag và feedback. State transition nằm trong application command handler, không nằm trong provider, worker, router hoặc UI.

### 7.3 Idempotency/stale handling

- Cùng command_id replay → cùng snapshot, không tăng version lần hai.
- Expected session version cũ → STALE_SESSION_VERSION.
- Job completion/cancellation lệch version → reject.
- Job terminal SUCCEEDED/FAILED/CANCELLED → không bị ghi đè.
- Renderer sequence không integer hoặc sequence <= lastSequence → bỏ qua.
- Gate A/B không được bypass bằng navigation/local flag.

## 8. Contract registry hiện tại

### 8.1 Envelope chung

Theo docs/architecture/CONTRACTS_AND_INTEGRATION.md, async command/result nên mang:

~~~
contract_name
contract_version
session_id
expected_session_version
artifact_id / artifact_version
source_artifact_ids[]
created_at
provenance: model/config/actor/reason
~~~

Backend contract là authority. Mobile types tương lai phải generated/derived từ schema versioned, không hand-maintained duplicate trong từng screen.

### 8.2 Media source và validation

Module backend/src/sketch2life/contracts/schemas/media_validation.py.

SourceMediaReferenceV1:

| Field | Ràng buộc |
|---|---|
| artifact_ref | source reference |
| sha256 | bắt buộc khi AVAILABLE, 64 hex |
| source_status | AVAILABLE, MISSING, UNREADABLE |
| working_copy_ref | hiện cố định None |

Available source phải có hash; unavailable source không được có hash.

MediaValidationResultV1 gồm decision, ordered recapture_reasons, image/audio refs, image/audio signals, recapture_message, validator_policy_version và validator name deterministic-media-validator.

Image signals: width, height, mean luminance, luminance deviation, edge strength, border ink ratio. Audio signals: duration, sample rate, channels, RMS, clipping ratio, speech activity ratio, zero-crossing ratio. Fixture manifest bắt buộc synthetic-only=true và expected decision/reasons.

### 8.3 Understanding contracts — hai generation phải phân biệt module path

Repository có hai lớp contract liên quan understanding. Không import theo tên ngắn một cách mơ hồ.

#### A. contracts/schemas/understanding.py — simple fixture/live boundary

- ModelProvenanceV1: provider fixture|lightning|runpod|unknown, model, adapter version, config version.
- AdapterFailureV1: VALIDATION_REJECTED, TIMEOUT, PROVIDER_ERROR, RATE_LIMITED, MALFORMED_OUTPUT, PROHIBITED_FIELD, SOURCE_MISMATCH và retryable.
- AsrRequestV1: SourceMediaReferenceV1 + media_validation=PASS.
- AsrResultV1: SUCCEEDED|FAILED, transcript/language/segments/quality hoặc typed failure.
- VisionRequestV1: source image, media_validation=PASS, response schema VisionUnderstandingResultV1.
- VisionUnderstandingResultV1: entities, actions, relations, themes, ambiguous regions, uncertainty, provenance hoặc failure.

Đây là contract mà live_understanding.py, LightningAsrAdapter, LightningVisionAdapter, FixtureAsrAdapter và FixtureVisionAdapter hiện sử dụng.

#### B. contracts/schemas/asr.py — richer ASR Phase A/B

AsrProfileCatalogV1 có deterministic fake profiles và experimental Faster-Whisper profiles. Profile real phải có model identifier/revision, weight provenance, adapter version, runtime version và compute profile thật; fake không được khai báo các field đó.

AsrRequestV1 của module này gồm correlation_id, source_audio_ref, optional processing_audio_ref + AudioDerivationProvenanceV1, optional MediaValidationProvenanceV1, requested_profile_id và optional LanguageHintV1.

AsrResultV1 gồm:

- AsrSuccessV1: raw transcript, speech diagnostic, detected language, segments/words/timestamps, duration/VAD, model/revision/adapter/runtime/config hash và quality metadata;
- AsrFailureV1: INPUT_NOT_VALIDATED, ASR_TIMEOUT, ASR_MODEL_UNAVAILABLE, ASR_PROVIDER_FAILURE, ASR_SCHEMA_INVALID + AsrErrorDetail + retryable.

Faster-Whisper optional extra đang exact-pin faster-whisper==1.2.1 và ctranslate2==4.8.1; đây là candidate/evidence boundary, chưa phải production default.

### 8.4 Vision contracts

Module backend/src/sketch2life/contracts/schemas/vision.py.

Input/provenance:

- VisionImageReferenceV1: artifact ref + required SHA-256.
- ImageDerivationProvenanceV1: transform name/config và source/processing hashes.
- VisionMediaValidationProvenanceV1: validation artifact ref/hash, PASS/RECAPTURE, policy version.
- VisionUnderstandingRequestV1: correlation ID, source/processing refs, derivation, validation, requested profile.

Structured observation:

- ObservedTextV1 có language declaration; language không tự được xem là ground truth.
- EntityCandidateV1, ActionCandidateV1, RelationCandidateV1, ThemeCandidateV1, AmbiguousRegionCandidateV1 đều có observation ID.
- Relation không self-reference.
- Action actor/object phải trỏ tới entity.
- Theme evidence refs phải trỏ tới observation hợp lệ.
- Duplicate observation ID và reference integrity violation bị reject.

VisionUnderstandingSuccessV1 yêu cầu policy_execution_state=PASSED, profile catalog hash, config hash, adapter version và timezone-aware executed_at.

Failure matrix tách input/provenance/hash, model/device, timeout, provider failure, schema mapping và prohibited claim. Prohibited categories là psychological inference, personality, diagnostic, mental state, trauma và developmental claim. Prohibited output phải BLOCKED, retryable=false, attempt=1 và repair=false.

vision_v2.py thêm local Qwen provenance, dependency pins, decoding config, model revision và weight hash metadata. Đây là candidate runtime contract; FEAT-018 freeze vẫn là VisionUnderstandingResultV1. Migration V1→V2 cần approval riêng.

### 8.5 P1/Montessori/Gate B contracts

Module backend/src/sketch2life/contracts/schemas/p1_experience.py.

| Contract | Nội dung chính |
|---|---|
| VersionedRefV1 | id + integer version |
| AnchorProvenanceV1 | source artifact/hash, source contract/version, claim IDs |
| SemanticAnchorV1 | subject/action/visual_feature/story, original/normalized label, tags, confidence, adult_confirmed, provenance |
| SemanticAnchorSetV1 | Gate A CONFIRMED, actor, source hash, primary/secondary anchors, correction |
| P1ContextV1 | session/version, age, readiness, completed activity, material, supervision, policy flags, candidate status, Gate A flag, optional selected refs |
| LearningFocusV1 | objective ref, selected anchor, child-facing goal, selection policy, rejected alternatives |
| ActivityTemplateV1 | activity/objective refs, supported labels/kinds, mode, age, readiness/prerequisite, materials, supervision, policy/safety, steps, provenance, review |
| MediaContinuityPlanV1 | VIDEO hoặc ORIGINAL_ART_ANIMATION, source, anchor, objective/template ref, continuity requirements |
| ActivityPlanV1 | activity/template/objective refs, materials, steps, safety |
| BridgeSentenceV1 | child-facing sentence + anchor/objective/template refs |
| ActivityFitEvaluationV1 | PASS/REJECT/BLOCKED, four dimensions, total/threshold, reason codes, evaluated refs |
| ExperienceSpecV1 | immutable spec identity/hash, source, anchor, focus, template, video/animation/activity plans, bridge, fit, policies |
| P1FilterResultV1 | VALID_CANDIDATE, MISSING_CONTEXT, NO_ELIGIBLE_ACTIVITY, UNKNOWN_ANCHOR, AMBIGUOUS_ANCHOR, CONFLICTING_ANCHOR |
| IntegrationGateDecisionV1 | Gate B APPROVED/BLOCKED, session/version, exact refs/spec/reasons |
| ActivityHandoffV1 | READY/BLOCKED và exact spec/activity/objective/template refs |

Anchor chưa adult-confirmed hoặc thiếu claim provenance không hợp lệ. ActivityTemplateV1 hiện review status PROVISIONAL_OWNER_REVIEWED và production_eligible=false. Gate B chỉ trả refs khi identity, fit, spec ID/hash và downstream continuity đều pass.

### 8.6 Learning media contracts

Module backend/src/sketch2life/contracts/schemas/learning_media.py.

LearningMediaRequestV1 có contract/version, session + expected/source session version, request/idempotency key, activity/objective IDs + versions, renderer plan ID/version và cache key.

ReviewedLearningMediaAssetV1 có asset ref/hash, activity/objective/renderer identity, cache key, review_status=REVIEWED và media status AVAILABLE|STALE|CORRUPT|UNSAFE.

LearningMediaResultV1:

| Field | Giá trị |
|---|---|
| status | READY, FALLBACK, BLOCKED |
| cache_status | HIT, MISS, NOT_ATTEMPTED |
| identity | activity/objective/renderer IDs và versions phải echo |
| asset_ref | bắt buộc với READY |
| fallback_type | STILL_NARRATION, WHOLE_IMAGE_REVEAL, SUPERVISED_HANDOFF khi FALLBACK |
| generation_called | phản ánh provider call thực tế |
| provenance | reviewed cache, synthetic fixture hoặc renderer fallback |
| reason_code | cache/stale/corrupt/unsafe/renderer/provider/media error |

Invariant: cache HIT phải READY; non-READY phải có reason; FALLBACK phải có fallback type.

### 8.7 Art renderer contracts

Module packages/art-renderer/src/contracts.ts.

ART_RENDERER_PROTOCOL_VERSION=1. ChildArtAsset gồm sourceAssetId, sourceAssetVersion, URI, asset kind WHOLE_DRAWING|CROP|TRANSPARENT_PNG|MASK, optional crop/mask version và source SHA-256. CROP bắt buộc crop provenance; MASK bắt buộc mask provenance.

ArtAnimationPlan gồm protocol version, plan ID/version, stage, objects và motions. Motion có ID/scene/target/kind/duration cùng bounded destination/scale/rotation/opacity. Validator reject unknown target và duplicate motion ID.

Playback events: PLAYBACK_STARTED, PLAYBACK_COMPLETED, FALLBACK_APPLIED, PLAYBACK_FAILED. Fallback reasons: EXTRACTION_UNAVAILABLE, MASK_INVALID, ASSET_LOAD_FAILED, MOTION_COMPILE_FAILED.

### 8.8 FEAT-016 runtime contracts

Module features/FEAT-016-runtime-integration/src/runtime_integration/contracts.py.

- ArtifactRef: artifact ID/version/kind và optional 64-hex hash.
- CommandEnvelope: command ID, session ID, expected version, actor ref, timezone-aware created_at.
- GateAConfirmation: meaning version, confirmed claim IDs, optional correction.
- GateBApproval: activity/objective ID + version.
- SessionSnapshot: session state/version, source artifacts, raw understanding, Gate A, P1 context, Gate B, experience artifacts, handoff, feedback.
- JobSnapshot: job/session ID, status, session version, optional result artifact/error.
- TransportEnvelope: contract name/version, command/session/version và payload; supported RuntimeCommandV1=1.0, RuntimeResultV1=1.0.

### 8.9 Mobile Pixi bridge contract

apps/mobile/src/bridge/pixi/protocol/messages.ts giữ PIXI_BRIDGE_PROTOCOL_VERSION=1. Message hiện typed là RENDERER_READY với payload rỗng và RENDERER_ERROR với code/message.

isRendererMessage() reject unknown protocol version hoặc payload không phải object. Fixture lifecycle riêng hỗ trợ RENDERER_READY, PLAYBACK_PROGRESS, RENDERER_ERROR và sequence monotonic. Đây là mismatch cần reconcile trước full bridge integration vì protocol message type và fixture lifecycle chưa hoàn toàn cùng một registry.

## 9. Security, data và trust boundary

### 9.1 Rules bắt buộc

- Không commit .env, credential, token, Firebase service account, Android keystore/signing password, seed user/account hoặc real child data.
- Firebase chỉ Authentication; cấm Firebase Storage, Firestore, Realtime Database.
- Mobile không chứa S3, Lightning, Runpod, database endpoint/credential.
- Object storage do backend port sở hữu; mobile không gọi S3 trực tiếp.
- Handbook/workbook originals và rendered extracts ở local external reference, không publish.
- Evidence chỉ lưu hash/metadata bounded, không raw image, prompt, model output, token, signed URL hoặc provider headers.

### 9.2 Provider policy

Settings có ai_provider=disabled|lightning_dev|runpod, Lightning URL/token file/model/path ở backend runtime, Runpod endpoint/key file cho production và timeout limits.

Staging/production yêu cầu Firebase config. Production yêu cầu ai_provider=runpod, endpoint ID và key file. Lightning là dev/fixture provider trên account bình thường, không được coi là private networking. Runpod Serverless là production target sau benchmark/approval.

### 9.3 Điểm cần hiểu đúng

Settings guard không đồng nghĩa route đã có authentication middleware. Route /v1/live-understanding hiện chưa thấy dependency verify Firebase ID token; đây là khoảng trống trước khi mở production API. AuthSessionPort trên mobile mới là interface, chưa có Firebase adapter.

## 10. Local infrastructure và release

### 10.1 Compose

compose.yaml định nghĩa PostgreSQL 17 Alpine ở port 5432, Redis 8 Alpine ở port 6379 với append-only persistence và MinIO ở 9000/9001. Đây là disposable local stack với placeholder credentials. Chưa có application adapter/migration/worker wiring đầy đủ.

### 10.2 Android release path

| Stage | Lệnh/artifact | Ý nghĩa |
|---|---|---|
| Developer smoke | pnpm --dir apps/mobile android:apk:debug | debug APK local/emulator |
| Controlled test | android:apk:release | signed release APK khi signing đã cấu hình |
| Play test/public | android:aab:release | signed AAB internal/closed/public track |

Wrapper apps/mobile/scripts/run-gradle.mjs chọn gradlew.bat trên Windows và ./gradlew trên Linux/macOS. Baseline ghi nhận Java có nhưng Android SDK/ANDROID_HOME chưa sẵn sàng; APK/AAB production chưa được xác nhận.

## 11. Validation và evidence

### 11.1 Validator snapshot

| Command | Kết quả |
|---|---|
| python tools/validate_harness.py | HARNESS_VALID |
| python tools/validate_skeleton.py | SKELETON_VALID |
| python tools/validate_architecture.py | ARCHITECTURE_VALID |
| python tools/validate_team_allocation.py | TEAM_ALLOCATION_VALID |
| python tools/validate_repository_security.py | REPOSITORY_SECURITY_VALID, 919 publishable files scanned |
| pnpm --dir apps/mobile typecheck | Pass |
| pnpm --dir apps/mobile test | Pass, 2 suites / 7 tests |
| pnpm --filter @sketch2life/art-renderer test | Pass, 1 suite / 6 tests |
| backend/.venv/Scripts/python.exe -m pytest backend/tests/unit/test_p1_experience.py -q | Pass, test mục tiêu |

### 11.2 Rerun bị giới hạn bởi môi trường

- Full backend collection bằng global Python dừng khi import test_image_admission.py vì thiếu optional av.
- Targeted backend run bằng .venv chạy được phần lớn contract/P1 tests nhưng test cần tmp_path bị PermissionError tại Windows temporary/cache directory.
- FEAT-015/016 tests khi gọi trực tiếp từ root cần PYTHONPATH feature source; sau khi bổ sung path, 30 test pass và 2 test hash/path bị cùng giới hạn temp-directory permission.

Đây là giới hạn execution environment của lần kiểm tra hiện tại, không được diễn giải thành business logic đã fail. Ngược lại, cũng không ghi là full suite hiện tại pass.

### 11.3 Historical evidence

FEAT-018 evidence ngày 2026-09-11 ghi nhận tại merge point: P3 typecheck/test/demo pass; P4 contract/cache/fallback/replay pass 15 tests; pnpm typecheck/test pass cho mobile và art-renderer; Python collection pass với expected skips; security validator pass.

Đó là evidence tại commit/branch/environment lúc merge. Snapshot này giữ chúng như historical evidence nhưng ưu tiên kết quả rerun hiện tại khi đánh giá checkout hiện tại.

Evidence tài liệu này nằm tại features/FEAT-019-current-system-documentation/evidence/README.md.

## 12. Đã có, chưa có và không nên hiểu nhầm

### 12.1 Đã implement trong source tree

- Governance/context/evidence harness và security gates.
- FastAPI app composition, /health, /v1/live-understanding synthetic route.
- Typed Pydantic contracts cho media, understanding, ASR, vision, P1, learning media.
- Deterministic PNG/WAV inspection và recapture reasons.
- FEAT-018 bounded image admission + injected decoder port.
- P1 catalog/compiler, hard rules, fit evaluation, immutable spec hash, strict continuity và Gate B identity checks.
- Fixture/fake ASR/vision adapters, provider-shaped Whisper/Qwen boundaries và Lightning transport adapters.
- Learning media cache resolver/fallback contracts và replay entrypoint.
- Standalone PixiJS/GSAP renderer, Motion DSL, provenance validation, fallback, benchmark.
- Android React Native skeleton, fixture reducer/UI, backend synthetic client, auth port, bridge message validation.
- Local Compose definitions cho Postgres/Redis/MinIO.

### 12.2 Chỉ offline/fixture-only

- FEAT-015 integration fixture/flow.
- FEAT-016 SessionAggregate/LocalJobStore/LocalTransport.
- P1 catalog runtime với catalog synthetic/provisional.
- P3 browser renderer demo.
- P4 InMemoryLearningMediaStore và replay.
- Lightning route nếu được cấu hình trên synthetic fixture.
- Mobile full-flow screen.

### 12.3 Chưa implement hoặc chưa wire vào production vertical slice

- Firebase ID-token verification middleware và role/authorization persistence.
- Parent/guide sign-in UI, child supervised session creation.
- Camera/image picker/microphone capture và consent UX.
- Backend session repository, DB migrations, PostgreSQL adapter.
- S3/MinIO object-storage adapter, upload authorization, retention/deletion jobs.
- Redis/RQ queue, worker orchestration, job resource API và polling endpoint.
- Full multimodal fusion producer migration sang frozen shared registry.
- Live ASR/VLM production model call, benchmark-based profile freeze, Runpod adapter.
- P1 recommendation HTTP/application endpoint.
- Full Gate A/Gate B backend commands và mobile review screens.
- Pixi WebView bridge playback inside mobile screen.
- P4 live video generation, media validation worker và cloud cache.
- Gallery/session journey, telemetry, CI/CD, cloud deployment.
- Signed Android APK/AAB và Play Console tracks.
- Qualified Montessori review; current records vẫn non-production eligible.

## 13. Roadmap hợp lý tiếp theo

Roadmap dependency-driven không phải team assignment. Mỗi bước cần feature plan và approval riêng.

1. Chuẩn hóa baseline/context để không còn câu “product implementation not started” gây hiểu nhầm.
2. Freeze shared contract registry V1; giải quyết hai generation ASR/vision và Pixi bridge event registry.
3. Cài Android SDK và chứng minh blank debug APK trên API 29/36.
4. Hoàn thiện Firebase Authentication adapter/backend verification bằng fixture trước.
5. Tạo session/artifact/job/auth API vertical slice với application-owned state.
6. Nối PostgreSQL, S3-compatible storage, Redis/RQ theo ports và provenance rules.
7. Nối P2 result → Gate A → P1 deterministic filter → Gate B bằng public backend contracts.
8. Nối Pixi WebView bridge + original-art player và P4 cache/fallback vào một approved ExperienceSpec.
9. Benchmark Lightning dev; sau đó benchmark/freeze Runpod production profile.
10. Thêm privacy/retention/deletion, observability/redaction và CI security/type/test gates.
11. Phát hành internal signed APK, sau đó AAB qua Play test tracks.

## 14. Traceability nhanh

| Muốn biết | Đọc file/source |
|---|---|
| Quy tắc làm việc | AGENTS.md, docs/governance/WORKFLOW.md |
| Product context | docs/context/PROJECT_CONTEXT.md |
| Baseline/frozen decisions | docs/SYSTEM_BASELINE.md |
| Backend layering | docs/architecture/PYTHON_BACKEND_ARCHITECTURE.md, backend/src/sketch2life/ |
| Mobile boundary | docs/architecture/REACT_NATIVE_ARCHITECTURE.md, apps/mobile/ |
| Contract rules | docs/architecture/CONTRACTS_AND_INTEGRATION.md, backend/src/sketch2life/contracts/schemas/ |
| Current live route | backend/src/sketch2life/interfaces/http/routers/live_understanding.py |
| Current P1 behavior | backend/src/sketch2life/application/services/p1_experience.py |
| Current image admission | backend/src/sketch2life/application/services/image_admission.py |
| Current learning media | backend/src/sketch2life/application/services/learning_media_resolver.py, learning_media_fallback.py |
| Current renderer | packages/art-renderer/src/ |
| Current mobile fixture | apps/mobile/src/features/fixture/ |
| Offline integration | features/FEAT-015-integration-readiness-review/ |
| In-memory session/job | features/FEAT-016-runtime-integration/src/runtime_integration/ |
| Latest FEAT-018 | features/FEAT-018-live-image-canvas-flow/CONTEXT.md, evidence/, plan/, approvals/ |

## 15. Kết luận

Sketch2Life hiện có nền tảng kiến trúc có kỷ luật: dependency direction rõ, contract có version/hash/provenance, Gate A/B được mô hình hóa, P1 hard rules đứng trước model selection, original art được bảo toàn, fallback không phá handoff, và security validator hoạt động.

Điểm quan trọng nhất khi tiếp tục là không nhầm các offline/fixture workstream đã xanh với production integration. Bước tiếp theo là freeze shared registry, nối application-owned session/API/storage/auth theo approval mới, rồi chứng minh một vertical slice có evidence đầy đủ từ capture đến feedback.
