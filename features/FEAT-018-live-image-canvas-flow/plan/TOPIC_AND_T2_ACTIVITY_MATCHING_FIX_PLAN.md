# FEAT-018 Topic quality and T2 activity matching fix plan

Status: `IMPLEMENTED — owner Lightning smoke pending`

Feature: `FEAT-018-live-image-canvas-flow`

Branch: `codex/feat-018-contract-plan`

Date: 2026-09-22

## 1. Decision already confirmed by the owner

The implementation must satisfy these decisions:

1. Tapping **Tạo gợi ý thật** must trigger a real backend recommendation based on the
   Gate-A-confirmed JSON, not on a UI mock or a hardcoded topic.
2. The visible topic should be richer Vietnamese, combining a grounded subject/action/context
   when those claims are actually present.
3. If there is no exact catalog match, the backend may use a reviewed alias, semantic concept-family,
   or age-baseline fallback. The UI must label this as an expanded suggestion and retain the
   reason/provenance. It must never silently present a mock activity as a backend result.

No implementation is authorized until this plan is approved and the approval record is updated.

## 2. Scope and non-goals

### In scope

- The current BaoVC React Native workflow from image analysis through Gate A, T2 activity
  recommendation, P1 filter, ExperienceSpec, Gate B, and Pixi handoff.
- Synthetic/non-child image demo only, Android Emulator first, Lightning manually triggered by the
  owner under the already approved approximately 25-credit ceiling.
- Backend-owned topic/anchor ranking, Vietnamese display-topic composition, reviewed semantic
  matching, age/safety/material eligibility, and recommendation provenance.
- Removal of misleading butterfly-only presentation from the T2 recommendation/detail path.
- Contract-compatible adapter work, focused tests, evidence, and UI verification.
- Keeping the current in-memory session and application-port seams so future auth and durable save
  can be added without changing the domain flow.

### Explicitly out of scope

- Video generation or video upload.
- New authentication, durable child data, persistence, Firebase Storage/Firestore/Realtime Database,
  or mobile provider credentials.
- Changing FEAT-003 schemas, the Qwen model adapter, Lightning schema-repair behavior, or the
  approved image-admission contract.
- Codex-triggered Lightning requests.
- Inventing a subject that the image/confirmed JSON did not support.
- Replacing the reviewed activity catalog with arbitrary LLM-generated activities.

## 3. Diagnosis from the current code and owner screenshots

The failure is not primarily a network failure. The current UI reaches the backend, but the
supervised P1 path is unable to turn the returned claims into a useful catalog match.

### 3.1 Why the topic is too simple and often wrong

- `apps/ui-mobile/src/context/AppContext.tsx` currently flattens `entities`, `actions`, and
  `themes` into claims without role quality ranking, Vietnamese normalization, or semantic tags.
- After Vision succeeds, every claim is selected by default and the first flattened claim becomes
  primary. A background entity such as `grass` can therefore become the primary anchor before the
  adult sees the screen.
- The current scene title is assembled from that first raw label (`Câu chuyện từ ...`), so it is
  short, language-dependent, and not a reliable subject/action/context topic.
- Gate A currently stores only the selected label as a `SemanticAnchorV1` with empty semantic tags.
  It preserves provenance but does not provide the semantic concept information needed by the richer
  catalog matcher.
- The current live prompt/adapter can return technically valid claims while still placing scenery or
  broad themes ahead of the main visible subject. A valid JSON response is therefore not sufficient
  for a useful topic.

### 3.2 Why screenshot 2 shows no real T2 activity

- The `Tạo gợi ý thật` button does call `prepareActivityWorkflow()`, and that method calls the real
  `readContextOptions` endpoint with the selected child's age.
- The supervised backend currently builds `P1ContextOptionsV1` through the exact-label matcher in
  `P1ExperienceCompiler`. The composition root wires the template library and topic assets, but does
  not inject the existing semantic catalog V1/V2 into `SupervisedFlowService`.
- The current matcher therefore sees raw labels such as `grass`, `flying`, and `nature`, while the
  reviewed P1 catalog is Vietnamese and activity-specific. The observed age-60 audit found zero
  exact P1 matches for those labels; this explains the empty options response and the red error.
- A semantic catalog V2 already exists with reviewed exact phrases, aliases, concept-family matching,
  and `AGE_BASELINE_FALLBACK`, but the current mobile supervised path does not use it.
- The T2 card still renders `CraftButterflyArtwork` and the detail screen still renders
  `ButterflyIconSvg` regardless of the confirmed topic. This makes the screen look like a result even
  when the backend has not returned an activity and causes a visible topic/activity mismatch.
- The mobile state also initializes `selectedActivity` from `MOCK_ACTIVITIES[0]`; that state must not
  be allowed to leak into a failed or pre-request T2 screen.

### 3.3 Existing assets/contracts that must be reused

- `ActivitySemanticCatalog` and `ActivitySemanticCatalogV2` in
  `backend/src/sketch2life/infrastructure/catalog/` are the source of reviewed matching rules.
- `SemanticCatalogPort` and `SemanticCatalogV2Port` already exist in
  `backend/src/sketch2life/application/ports/workflow_dependencies.py`.
- `ConfirmedSceneUnderstandingV2` and `SemanticActivityMatchV2` already carry concepts, evidence
  claim IDs, match mode, reason codes, fallback reason, age fit, safety, and catalog quality.
- `P1ContextOptionV1` is intentionally small and currently carries identity, age, readiness,
  materials, supervision, and policy constraints only. The plan must not smuggle new fields into it
  without a versioned contract review.

## 4. Target behavior

The end-to-end behavior after implementation is:

```text
Lightning/Vision JSON
        |
        v
bounded claim normalizer + role/quality ranking
        |
        v
adult sees grounded Vietnamese topic + claims
        |
        v
adult selects primary/claims and confirms Gate A
        |
        v
stored confirmed JSON/anchor + age -> user taps T2 CTA
        |
        v
semantic resolver: exact -> reviewed alias -> reviewed concept -> safe age baseline
        |
        v
typed activity identity + provenance -> P1 context/filter -> ExperienceSpec -> Gate B -> Pixi
```

The resolver must return only an activity that passes the existing catalog review status and hard
eligibility rules. A baseline fallback is acceptable only when it is safe for the age/material/
supervision context and is visibly marked as `Gợi ý mở rộng`, with a closed reason such as
`AGE_BASELINE_FALLBACK`.

## 5. Implementation plan

### Phase A — Establish the contract and state boundary

1. Add a feature-local decision note and update the plan status only after approval. Do not modify
   FEAT-003-owned contracts.
2. Trace the exact payloads from `confirm_gate_a` through `read_p1_context_options`, `setP1Context`,
   `runP1Filter`, `prepareExperience`, and renderer launch.
3. Decide whether existing `MobileWorkflowResultV1` plus the current P1 payload can carry the required
   match provenance. Preferred order:
   - keep `P1ContextOptionsV1` unchanged and keep semantic evidence internal while the selected
     activity identity continues through the existing versioned P1/ExperienceSpec contracts;
   - if the UI must display match mode/reason before selection, introduce a separately versioned
     additive response (for example `P1ContextOptionsV2`) with a compatibility adapter, schema,
     mobile type, and migration tests;
   - do not add optional fields to V1 merely to avoid a version decision.
4. Preserve `source_image_artifact_ref`, source SHA-256, claim IDs, original labels, normalized labels,
   and Gate-A actor in the stored session record. The derived Vietnamese topic is display/selection
   metadata, not a replacement for the raw observation.

### Phase B — Improve claim quality and topic composition

1. Update the live understanding prompt/configuration only within the FEAT-018 live route boundary:
   ask the model to prioritize the main visible subject, then meaningful action, then concrete scene
   context; explicitly demote scenery/background and broad themes; keep all claims evidence-backed.
   Reuse the existing strict V2 mapping and one-repair-generation ceiling.
2. Add a deterministic backend claim-ranking policy, versioned and testable, with this order:
   - subject/entity with sufficient confidence and visual evidence;
   - specific action attached to or compatible with that subject;
   - concrete visual context/theme;
   - broad background labels only as secondary context.
   Ties must be deterministic. The policy may demote a claim but must not delete the raw claim or
   invent an object.
3. Map only closed, reviewed labels/concepts into Vietnamese display labels. Preserve the raw label,
   normalized label, source kind, confidence, and evidence ID. Unknown labels remain visible in a
   safe neutral form rather than being guessed.
4. Compose a richer topic from confirmed claims, for example
   `Chú bướm bay giữa bãi cỏ` when the confirmed JSON actually contains those three grounded ideas.
   If the subject is not supported, use a truthful generic composition such as
   `Khám phá chuyển động trong thiên nhiên`; never manufacture `bướm` from a generic `flying` claim.
5. Make the initial mobile selection deterministic and conservative: select only the ranked primary
   claim by default, leave secondary claims unselected, show their role/confidence, and keep the
   adult correction path. The adult can change the primary claim before Gate A.
6. Ensure Gate A stores the selected primary plus selected supporting claims and the topic/semantic
   mapping provenance so T2 uses the exact confirmed state, not a later UI guess.

### Phase C — Wire the reviewed semantic resolver into T2

1. Add the existing semantic catalog adapter to the composition root and inject the appropriate
   `SemanticCatalogPort`/`SemanticCatalogV2Port` into the supervised application service through a
   typed application port. Do not import infrastructure catalog code directly into the domain.
2. Build a bounded mapper from the Gate-A-confirmed `SemanticAnchorV1`/stored raw claims to
   `ConfirmedSceneUnderstandingV2`. The mapper must include the source image identity, confirmed
   actor, primary/secondary concepts, observed labels, claim IDs, and a deterministic scene hash.
   If the required V2 fields cannot be justified, fail closed with a typed diagnostic instead of
   filling them with fabricated values.
3. Resolve candidates in this order:
   - exact reviewed phrase;
   - reviewed Vietnamese alias;
   - reviewed semantic concept-family;
   - age-baseline fallback only after personalized matching fails.
4. Apply existing hard gates after semantic scoring: age band, catalog review/production status,
   safety rule, material availability, supervision level, readiness/prerequisite constraints, and
   strict anchor/objective continuity. A high semantic score can never bypass a hard rule.
5. Convert the selected V2 match to the existing P1 evidence/selection path through the existing
   `to_legacy_evidence` boundary where possible. Keep the exact activity ID/version stable through
   P1, ExperienceSpec, Gate B, renderer, and feedback.
6. Return a typed no-result failure such as `NO_ELIGIBLE_ACTIVITY` with safe reason codes when no
   reviewed candidate or safe baseline is available. Do not return an empty success that the UI
   interprets as a generic backend outage.
7. Include match mode/provenance in the approved response only if the contract decision in Phase A
   requires it. For a fallback, the UI must receive enough closed information to show `Gợi ý mở
   rộng`, not claim a personalized exact match.

### Phase D — Correct the T2 and downstream UI

1. Before the CTA is pressed, show a neutral topic-aware placeholder and `Chưa gọi catalog backend`;
   do not show a butterfly activity image, title, or mock activity as if it were selected.
2. On CTA press, clear stale error/notice/result state, disable duplicate requests, call the real
   `readContextOptions` route with the current session version and age, and render a loading state.
3. On success, render the backend-selected activity identity and catalog/topic asset reference. The
   artwork must be resolved from the reviewed asset catalog or a neutral reviewed fallback, never
   from `CraftButterflyArtwork` unconditionally.
4. On semantic alias/concept/fallback success, display the returned Vietnamese topic and a clear
   provenance label such as `Gợi ý mở rộng từ catalog đã duyệt` with a concise reason. Do not call
   this an exact personalized match.
5. On no-result/failure, keep the source image and confirmed topic visible, show the typed safe
   message and an actionable retry/correction path, and keep the user out of P1/ExperienceSpec.
6. Remove the default `MOCK_ACTIVITIES[0]` from any reachable backend-result presentation. It may
   remain as an offline fixture only if it is explicitly isolated from the live state and cannot be
   handed off.
7. Replace the hardcoded butterfly icon/art in activity detail and any reachable recommendation
   hero with the selected backend activity/topic asset; retain PixiJS source-art preservation and
   existing asset rights/provenance gates.
8. Keep the existing Android flow and future auth seam unchanged: actor/session identifiers remain
   adapter-owned, and no token or durable-save logic enters the mobile client.

### Phase E — Verification and owner-run smoke

1. Add deterministic backend tests for ranking, display-topic composition, raw-label preservation,
   Vietnamese alias matching, concept-family matching, safe age fallback, hard-rule rejection, and
   no-result diagnostics.
2. Add contract tests for the selected response version, legacy compatibility (if used), idempotency,
   session-version conflicts, Gate-A requirement, and exact activity identity continuity.
3. Add mobile tests or a deterministic fixture harness for:
   - primary-only initial selection;
   - richer topic rendering;
   - T2 pre-call/loading/success/fallback/no-result states;
   - no hardcoded butterfly for an unrelated topic;
   - retry clearing stale UI state;
   - selected backend activity flowing into detail, ExperienceSpec, Gate B, and Pixi.
4. Run the existing TypeScript, focused backend tests, architecture/security validators, and
   `git diff --check`. Record commands, commit, environment, fixture IDs, outputs, and interpretation
   inside this feature's evidence directory.
5. The owner manually runs one or more Lightning requests using synthetic/non-child images only.
   Codex does not call the provider. The run remains within the already approved approximately
   25-credit total ceiling and checks that the live Qwen output reaches the same deterministic
   ranking/resolution path.

## 6. Contract and architecture safeguards

- No FEAT-003 schema or adapter change.
- No public V1 field widening without a new version and explicit approval.
- Application code consumes semantic matching through ports; infrastructure owns catalog loading.
- Raw claims and provenance remain immutable; display topic and semantic concepts are derived values.
- The backend, not React Native, owns activity eligibility and fallback choice.
- Fallback never bypasses age, safety, material, supervision, readiness, or Gate B continuity rules.
- The same activity/template/objective identity must survive T2, P1, ExperienceSpec, Pixi, and
  feedback.
- Auth/save remains a replaceable seam; current state remains process-local/in-memory.
- No provider credentials, raw images, child data, or raw model output are committed or logged.

## 7. Test matrix and acceptance criteria

### Required scenarios

| Scenario | Expected result |
| --- | --- |
| Subject is returned after scenery | Subject is ranked primary; scenery is secondary context. |
| Raw labels are English | Closed mapping/display label is Vietnamese; raw label and provenance remain. |
| Subject + action + context are grounded | Topic composes all supported parts without hallucinating. |
| Only generic/background claims are present | Truthful generic topic; no invented animal/object. |
| Exact reviewed catalog phrase | Personalized exact match. |
| Reviewed alias | Personalized alias match with reason/provenance. |
| Reviewed concept family | Personalized concept match with evidence claim IDs. |
| No personal match but safe age baseline exists | Age-baseline fallback, visibly labeled `Gợi ý mở rộng`. |
| No eligible candidate | Typed `NO_ELIGIBLE_ACTIVITY`; no mock activity or P1 continuation. |
| Unrelated topic | No butterfly-only artwork/title appears. |
| Duplicate CTA/retry | Idempotent/serialized request; stale result and error are cleared correctly. |
| Activity reaches Pixi | Activity/template/objective/asset identity is unchanged across all handoffs. |

### Acceptance criteria

1. A valid live JSON response produces a grounded Vietnamese topic that is more informative than a
   single raw label, while unsupported details are not invented.
2. The first returned claim is no longer automatically the primary anchor solely because of array
   order; background claims are not promoted over a supported subject.
3. Only the selected primary claim is initially selected; the adult can change it and Gate A records
   the final choice.
4. T2 is triggered by the explicit CTA and uses the stored Gate-A-confirmed JSON/anchor plus age.
5. `grass`/`flying`/`nature`-style raw output does not fail solely because of English-versus-
   Vietnamese exact matching; it resolves through a reviewed alias/concept or a safe labeled
   baseline, or returns a typed no-result.
6. No mock or hardcoded butterfly activity is presented as backend output.
7. Alias/concept/fallback mode and reason are truthful and visible wherever the contract exposes them.
8. The backend-selected activity identity is the one used by P1, ExperienceSpec, Gate B, activity
   detail, Pixi launch, and feedback.
9. Existing age, safety, material, supervision, readiness, Gate A, Gate B, source provenance, and
   security constraints remain enforced.
10. Focused tests, TypeScript checks, architecture/security validators, and evidence review pass.

## 8. Risks and approval gates

- **Contract risk:** the current V1 context-options payload has no match-mode field. Phase A must
  decide whether internal provenance is sufficient or a new versioned response is required.
- **Model-quality risk:** prompt improvement cannot guarantee a correct subject on every image; the
  deterministic ranking, adult Gate A correction, and fail-closed fallback remain mandatory.
- **Catalog risk:** a semantic fallback is useful only when the reviewed catalog contains a safe,
  age-eligible activity. The resolver must not widen the catalog by generating activities.
- **UI risk:** replacing hardcoded art may expose missing topic assets. Use an approved neutral
  fallback and record asset provenance rather than silently reusing butterfly art.
- **Live-provider risk:** owner-run smoke is manual and credit-bounded; no automatic retry or Codex
  request is permitted.

Implementation starts only after the owner approves this exact plan. Any decision to add a new public
contract version, expand the catalog, or alter the FEAT-003 boundary requires a revised approval.

## 9. Implementation result — 2026-09-22

The approved plan is implemented without changing FEAT-003, the V2 vision schema, or the existing
P1 context contract. The application now ranks confirmed claims deterministically, keeps raw labels
and provenance, composes a bounded Vietnamese topic, and enriches the confirmed primary anchor with
reviewed semantic tags. The composition root injects the existing reviewed semantic catalog through
`SemanticCatalogPort`; exact P1 matches retain their previous path, while unmatched labels use the
ordered exact/alias/concept-family/safe-age-fallback resolver before the existing age, material,
readiness, supervision, safety and Gate-B identity checks.

The generic `MobileWorkflowResultV1.payload` carries optional `topic_label_vi` and
`recommendation` metadata; `P1ContextOptionsV1` itself and all public contract versions remain
unchanged. The Android UI selects only the ranked primary claim initially, clears stale T2 state on
retry, waits for the complete backend workflow before publishing a result, labels expanded/fallback
recommendations, and no longer presents the hardcoded butterfly artwork as a backend result.

Changed implementation surfaces include:

- `backend/src/sketch2life/application/services/topic_semantics.py`
- `backend/src/sketch2life/application/services/semantic_activity_resolver.py`
- `backend/src/sketch2life/application/services/supervised_flow.py`
- `backend/src/sketch2life/application/services/p1_experience.py`
- `backend/src/sketch2life/infrastructure/catalog/activity_semantics.py`
- `backend/src/sketch2life/interfaces/http/app.py`
- `apps/ui-mobile/src/context/AppContext.tsx`
- `apps/ui-mobile/src/screens/Flow2Screens.tsx`
- `tools/lightning_vision_v2_server.py`

Verification completed:

- `backend/tests/contract/test_live_image_demo_api.py`: 9 passed, including a real supervised-flow
  test for a raw `grass` label resolving to a reviewed age fallback with `EXPANDED` metadata.
- `backend/tests/unit/test_topic_activity_matching.py`: ranking/topic composition, safe fallback and
  reviewed concept-family matching passed.
- Semantic catalog and live-demo focused sweep: 27 passed.
- Targeted Ruff, mypy and `pnpm --dir apps/ui-mobile exec tsc --noEmit`: passed.
- `git diff --check`: passed before final documentation-only changes.

The repository-wide backend collection was also attempted. Its failures occurred during fixture setup
because this workstation denied access to the user temp directory and the backend pytest cache; they
were `PermissionError` setup failures rather than assertion failures in
this feature. No Lightning request was made by Codex. The owner still needs to run the Android/live
smoke manually within the existing approximately 25-credit ceiling.
