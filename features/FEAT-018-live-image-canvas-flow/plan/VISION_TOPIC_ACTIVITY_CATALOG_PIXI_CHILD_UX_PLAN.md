# FEAT-018 Vision, topic, activity catalog, Pixi and child UX repair plan

Status: `IMPLEMENTED — OFFLINE VERIFICATION COMPLETE — OWNER LIVE SMOKE PENDING`

Feature: `FEAT-018-live-image-canvas-flow`

Branch: `codex/feat-018-contract-plan`

Date: 2026-09-22

## 1. Owner-confirmed outcome

The owner confirmed the following product decisions:

1. Show at most three activity recommendations, in explicit priority order. Every displayed option
   must be related to the confirmed picture/narration topic and suitable for the same educational
   story/media direction. An unrelated age-safe fallback, such as a pouring activity for a bird
   drawing, is not acceptable.
2. The live Qwen path may perform one bounded quality re-analysis when the first result is valid
   JSON but is not useful enough for the demo.
3. Topic construction must combine image evidence and narration evidence according to confidence.
   The image remains the grounding source; narration may disambiguate visible content but may not
   introduce unsupported objects or actions.
4. Activity titles and instructions must be human-readable Vietnamese. Internal activity IDs,
   template IDs, contract names, reason codes and provider terms must not be shown in the normal UI.
5. Expected failures must appear in a friendly modal with a clear recovery action, not as raw red
   text inside the page.
6. The curated V2 expansion catalog must be loaded by the real HTTP runtime.
7. PixiJS must launch with the actual backend payload. If animation cannot start, the original
   drawing remains visible and the user receives a friendly retry/back path.
8. Video generation/playback remains outside this demo. The selected activity must nevertheless
   preserve topic/objective continuity for the future educational-media stage.

## 2. Current evidence and root causes

### 2.1 Image understanding and topic quality

- The live prompt requests Vietnamese labels, but the schema only validates that a language tag is
  structurally present. Qwen can therefore return English values such as `branch`, `leaf`,
  `perching` and `bird on branch` while marking them as Vietnamese.
- The current reviewed display lexicon translates `bird` but not those related labels. Unknown
  English text passes directly into the UI and into the topic composer.
- Claims are ranked but are not canonically deduplicated. The observed response displayed `leaf`
  twice and treated aggregate phrases such as `bird on branch` as an independent subject/story.
- The current topic composer can concatenate raw labels. This produced a mixed sentence containing
  English words and can also fall back to a single generic label.
- The existing second generation is limited to malformed schema or a fully empty semantic result.
  A structurally valid but demonstrably poor result does not receive a bounded quality repair.

### 2.2 Activity selection and catalog runtime

- The HTTP composition root loads the 100-activity baseline with
  `load_p1_template_library(..., include_mvp=True)` and the legacy semantic catalog. It does not load
  the existing curated V2 expansion at runtime.
- The curated V2 catalog already contains reviewed animal families and age-specific titles/actions,
  including observation, classification and movement variants. Those records are currently absent
  from the live supervised route.
- The current UI starts a P1 chain with the first option instead of first showing a bounded ranked
  shortlist for adult selection.
- An age-compatible fallback can survive discovery even when it has no direct semantic continuity
  with the confirmed topic. Strict compilation may reject it later, or a generic activity may be
  rendered with a synthetic bridge that only mentions the topic.
- `ActivityTemplateV1` preserves identity and safety data but does not carry the curated Vietnamese
  display title. The mobile mapper therefore uses `template_id`, producing headings such as
  `TPL-ACT-0026-V2` and raw material/safety identifiers.

### 2.3 UI/UX and error handling

- The BaoVC journey has reachable screens for splash, onboarding, dashboard, child profile,
  capture, narration, AI processing, scene confirmation, Pixi preview, activity recommendation,
  activity detail and feedback.
- Several screens render the global workflow error as inline red text. Technical copy contains
  `backend`, `Gate A`, `Gate B`, `ExperienceSpec`, `contract`, `Pixi protocol`, catalog/debug state
  and raw activity references.
- Child-facing and adult-facing information are mixed together. The primary pages have too much
  explanatory text, while safety details and diagnostics are not separated into a deliberate adult
  layer.
- The shared button component lacks a complete accessibility/disabled-state contract and does not
  guarantee one consistent minimum touch target for every size.
- A legacy video screen exists in source but is not part of the BaoVC route. It must remain
  unreachable in this no-video demo.

### 2.4 PixiJS launch

- The backend creates a valid `PixiRendererLaunchV1`, and the renderer HTML/assets return HTTP 200.
- Python serializes optional renderer fields as explicit `null`, including `cropVersion`,
  `maskVersion`, and unused motion parameters.
- The TypeScript/Zod renderer schema defines those values as optional, not nullable, and is strict.
  The same otherwise-valid command is therefore rejected in the mobile WebView bridge.
- The UI exposes this internal mismatch as `Backend launch không qua validation Pixi protocol v1`,
  which is neither actionable nor suitable for a child-facing demo.

## 3. Target workflow and invariants

```text
required image + optional audio/text narration
  -> image admission
  -> Qwen attempt 1
  -> deterministic quality gate
       -> pass, or one and only one repair/re-analysis attempt
  -> normalize/localize/deduplicate grounded claims
  -> adult confirms one primary topic at Gate A
  -> V2 catalog semantic match + age/safety/readiness filtering
  -> strict P1 viability check for every candidate
  -> return 0..3 prioritized display cards
  -> adult selects one card
  -> revalidate and compile that exact activity
  -> adult approves activity at Gate B
  -> Pixi source-preserving reveal
  -> handoff and feedback
```

The implementation must preserve these invariants:

- Image is required; narration is optional and may be audio/ASR or manually entered text.
- No workflow step advances with an empty or ungrounded understanding result.
- One user-triggered vision request causes at most two model generations total. A schema repair uses
  the same single repair budget as a semantic-quality re-analysis; the two repair paths may not
  stack.
- Provider/network/model-unavailable failures are not retried by this quality branch.
- Raw provider evidence and attempt provenance remain preserved server-side; normalized display
  labels never overwrite the source output.
- Only strict-fit reviewed catalog activities may be displayed. Safety or age compatibility alone
  is insufficient.
- Changing activity selection reruns P1/ExperienceSpec for the selected option but does not rerun
  Qwen while the confirmed Gate-A topic is unchanged. Changing the primary confirmed topic creates
  a new shortlist from the new anchor.
- The exact selected activity, template, objective and spec identity remain continuous through Gate
  B, Pixi, handoff and feedback.
- No mock activity, raw error code or provider payload is used as a successful fallback.

## 4. Contract strategy

### 4.1 Preserve frozen producer contracts

- Do not widen or reinterpret `VisionUnderstandingResultV2`, raw-understanding contracts,
  `SemanticAnchorSetV1`, `P1ContextV1`, `P1FilterResultV1`, `ExperienceSpecV1`, renderer V1 contracts,
  or Gate A/Gate B semantics.
- Continue to accept typed `BLOCKED` outcomes inside HTTP 200 envelopes. The mobile client must
  inspect workflow status rather than equating HTTP 200 with success.
- Keep all provider credentials/endpoints outside mobile and Git.

### 4.2 Add a bounded activity recommendation read model

Add a versioned application/read-model contract, carried additively in the existing workflow
payload, with a shape equivalent to:

```text
ActivityRecommendationSetV1
  topic_label_vi
  options[0..3]
    priority: 1 | 2 | 3
    activity_ref + template_ref + objective_ref
    title_vi
    summary_vi
    match_reason_vi
    duration_minutes
    age_label_vi
    supervision_label_vi
    material_labels_vi[]
    fit_source: DIRECT | RELATED
```

Rules for this read model:

- The backend owns every field and the priority order; mobile performs no semantic or safety
  ranking.
- IDs stay in the transport only for exact selection and audit. They are not rendered in the
  primary UI.
- Each option must have passed age, safety, readiness, material, supervision, policy, semantic
  continuity, objective continuity and the existing strict P1 fit threshold before exposure.
- `RELATED` is allowed only when V2 continuity metadata explicitly permits it, the educational
  bridge is reviewed, and its score is below a direct match in priority.
- The old `P1ContextOptionsV1` remains valid for existing clients. The new read model is additive,
  bounded to three options, and has its own contract name/version and tests.

### 4.3 Selection command behavior

- Reuse the existing adult context/selected activity fields where they already carry an exact
  activity identity.
- Store the returned shortlist and its semantic evidence in process-local session state.
- A submitted activity must be a member of the current shortlist and match its exact version.
- A changed selection creates a new idempotency key and recompiles only that selected item.
- Stale versions, unknown selections, changed Gate-A anchors and replayed/tampered selections fail
  closed with a bounded internal reason; the UI receives only a mapped recovery category.

### 4.4 Renderer transport compatibility

- Keep `PixiRendererLaunchV1` and `RendererLoadCommandV1` versions unchanged.
- Serialize the HTTP/mobile renderer payload with aliases and `exclude_none=True`, so optional
  values are absent instead of `null`.
- Validate the Python-produced payload with the actual TypeScript
  `RendererLoadCommandSchema`. Do not maintain a second hand-written permissive schema.

## 5. Detailed implementation plan

### Phase 0 — Read-only audit of the current UI before implementation

This phase is a mandatory discovery gate. No application code, style, asset, contract, fixture or
runtime configuration may be changed while the audit is in progress.

1. Start the existing local backend/mobile app without changing source and walk the complete
   reachable BaoVC journey on the Android Emulator:
   - splash and onboarding;
   - dashboard and child profile;
   - image capture/upload;
   - audio narration and manual text narration;
   - AI processing;
   - scene understanding and adult confirmation;
   - Pixi reveal/source fallback;
   - activity recommendation and selection;
   - activity detail, handoff and feedback;
   - back navigation, retry, repeated tap, empty state, busy state and expected failure state.
2. Inspect the existing React Native source and styles read-only to identify issues that are not
   obvious from one happy-path screenshot, including overflow, keyboard overlap, small touch
   targets, inaccessible labels, stale state, duplicate navigation, hidden debug routes and
   inconsistent loading/disabled states.
3. Review each screen from three perspectives:
   - child: clarity, emotional tone, visual hierarchy, amount of text and obvious next action;
   - parent/guide: enough context to confirm, correct, supervise and recover safely;
   - system integrity: no backend/provider/contract terminology, IDs, raw reason codes or private
     diagnostics exposed.
4. Check common Android Emulator dimensions and text scaling for clipping, scrollability, keyboard
   avoidance, modal focus and primary CTA reachability. This remains observation only during the
   audit.
5. Create a feature-local UI audit matrix under `evidence/notes/` with one row per finding:

   ```text
   finding_id | screen/state | audience | evidence | severity | current behavior
   expected behavior | proposed repair | acceptance check | scope classification
   ```

6. Classify findings as:
   - `P0 FLOW_BLOCKER`: prevents the required workflow or loses user data/state;
   - `P1 DEMO_BLOCKER`: exposes technical failures, wrong activity/topic, broken Pixi or an
     unusable control;
   - `P2 CHILD_UX`: excessive text, unclear hierarchy, unfriendly wording or accessibility issue;
   - `P3 POLISH`: visual consistency that does not block the demo.
7. The already-observed problems in Sections 2.3 and 2.4 remain mandatory findings and may not be
   removed from scope by this audit. The audit is intended to discover additional issues.
8. End the audit with a bounded repair backlog mapped to the existing phases and acceptance
   criteria. Findings that fit the approved child-friendly UI/error/Pixi scope may be scheduled in
   Phase G/H. A new visual asset, incompatible contract change, video/auth/persistence work or other
   material scope expansion requires renewed owner approval before implementation.
9. Record an explicit `UI_AUDIT_COMPLETE — NO CODE CHANGED` checkpoint, including inspected commit,
   emulator/device configuration and sanitized screenshot references. Only after this checkpoint
   may implementation begin.

### Phase A — Freeze deterministic reproductions

1. Add sanitized fixtures for the observed bird-on-branch response, including duplicate leaves,
   English labels falsely tagged as Vietnamese, and narration that either supports or conflicts
   with the image.
2. Add a deterministic activity regression proving that a bird topic cannot produce the pouring
   activity family solely because it is age-safe.
3. Capture a Python-generated Pixi launch fixture containing currently-null optional fields and
   prove that the TypeScript schema rejects the pre-fix representation.
4. Record current UI text inventory for all reachable BaoVC screens. Screenshots are supporting
   visual evidence only; behavior must be covered by tests.
5. Do not call Lightning during this phase.

### Phase B — Improve Qwen output with one shared repair budget

1. Revise the Lightning prompt profile without changing the Vision V2 schema:
   - require Vietnamese surface labels when the model can identify the concept;
   - give concrete examples such as `con chim`, `cành cây`, `lá cây`, `đậu trên cành`;
   - require one canonical label per visible concept;
   - forbid duplicate singular/plural aliases and aggregate phrases that repeat an existing
     subject/relation;
   - prefer `con chim` + relation/action over a second entity named `chim trên cành`;
   - keep background details after the concrete main subject;
   - use narration only to disambiguate image-supported content.
2. Add a deterministic quality scorer after schema validation. Trigger repair only for closed,
   testable conditions such as:
   - no concrete foreground subject;
   - normalized duplicate claims;
   - declared-Vietnamese labels that fail the reviewed language/canonical-label policy;
   - only broad background/theme labels despite non-empty observations;
   - an aggregate scene phrase duplicates already-emitted subject/action/relation evidence;
   - the top usable grounded claim is below the approved confidence floor.
3. Share one repair budget between schema repair, semantic-empty repair and quality re-analysis.
   The maximum is initial generation plus one additional generation.
4. The repair prompt receives only closed diagnostics and the original permitted image/narration
   inputs. It must not echo raw model output or expand the task.
5. Select the final attempt deterministically. Prefer the repaired result only when it is schema
   valid, policy safe and has a higher quality score; otherwise retain the first valid grounded
   result or fail closed. Do not union contradictory claims across attempts.
6. Log only closed status, attempt count, repair category and aggregate counts. Never log image
   bytes, narration text, prompts, model output, tokens or child data.

### Phase C — Canonicalize and localize understanding

1. Add a reviewed canonical concept/display lexicon for the demo’s supported visible domains,
   including bird, branch, leaf, perch/fly, common animals, plants, people, vehicles, weather,
   shapes and common actions.
2. Normalize and deduplicate by canonical concept plus role. Preserve the highest-confidence claim
   and merge only provenance references, never confidence by addition.
3. Preserve raw labels in backend evidence. Child-facing payloads receive only reviewed Vietnamese
   display labels; an unknown non-Vietnamese label is omitted from child display rather than shown
   verbatim.
4. Treat aggregate scene phrases as context, not duplicate subjects, when their component evidence
   already exists.
5. Build a grounded scene representation that keeps:
   - primary concrete subject;
   - image-supported action/relation;
   - concise setting/context;
   - narration support/conflict status;
   - evidence IDs and confidence.
6. Apply evidence weighting:
   - image evidence is mandatory for the primary subject;
   - matching narration may increase confidence within a bounded cap;
   - narration may disambiguate two image-supported alternatives;
   - narration alone cannot create a visible entity/action;
   - conflict lowers confidence and requires adult confirmation instead of silent selection.

### Phase D — Produce a useful Vietnamese topic

1. Replace raw label concatenation with a deterministic Vietnamese sentence template using the
   grounded scene representation.
2. Target one concise child-friendly sentence, normally 8–16 words, containing the specific
   subject and—when grounded—the action/relation or setting. Example target:
   `Cùng khám phá chú chim đang đậu trên cành cây!`
3. Never emit a single raw word when at least one additional grounded action, relation, setting or
   narration cue is available.
4. Never mix English into the displayed topic. Unknown labels remain backend evidence, not UI text.
5. Use a stable generic Vietnamese fallback only when no more specific safe phrase is supported;
   the fallback must not invent a subject.
6. Recompute the topic after the adult changes the primary claim at Gate A.

### Phase E — Load and use the curated V2 catalog in the HTTP runtime

1. Update the composition root to load:
   - `load_p1_template_library(..., include_mvp=True, include_expansion=True)`;
   - `load_activity_semantic_catalog_v2(..., include_expansion=True)`.
2. Inject the V2 semantic catalog into the supervised-flow application service through a port; do
   not import infrastructure from domain/application policy code.
3. Convert the confirmed grounded scene/narration into the existing V2 scene-understanding input
   while preserving exact evidence IDs and confidence.
4. Build candidate pools from reviewed exact phrase, alias and concept-family matches. Age-baseline
   records may be inspected for diagnostics but may not be displayed without direct/approved
   related continuity to the topic.
5. Score candidates using, in order:
   - hard age/safety/readiness/material/supervision/policy eligibility;
   - direct topic and action/relation continuity;
   - image/narration evidence confidence;
   - objective alignment;
   - educational story/media continuity metadata;
   - reviewed catalog quality;
   - deterministic activity ID tie-break only after all meaningful scores.
6. Run the existing strict compiler viability check for every candidate before exposure.
7. Return at most three distinct eligible options with priorities 1–3. Direct matches outrank
   related expansions. If no option passes, return a typed no-result rather than an unrelated
   activity.
8. Include curated Vietnamese title, action summary, duration, material display labels and a short
   user-facing reason. Keep raw IDs, safety rule IDs and internal match codes out of visible copy.

### Phase F — Let the adult choose before compilation

1. Split the current `prepareActivityWorkflow` behavior into two explicit actions:
   - request/reload the ranked recommendation set;
   - select one option and compile that exact option.
2. Render up to three compact cards. Each card shows priority, Vietnamese title, one-sentence
   activity description, duration and a short relation to the child’s picture/story.
3. Require an adult tap on one card before P1 context, filter and ExperienceSpec compilation.
4. If the adult chooses another card, rerun only the downstream P1 chain for that exact selection.
   Do not call Qwen again unless Gate A/image/narration itself changes.
5. Preserve the existing synchronous request lock and idempotency behavior so rapid taps create one
   chain.
6. Preserve the last successful activity until a replacement succeeds. Returning to the screen
   reopens the current result without an unnecessary request.

### Phase G — Child-friendly full-flow UI/UX pass

1. Add one reusable app-level friendly status modal with:
   - short Vietnamese title;
   - one plain-language sentence;
   - primary recovery action (`Thử lại`, `Chọn lại`, `Quay về tranh` or `Đóng`);
   - optional secondary action;
   - non-alarming icon/illustration and accessible focus behavior.
2. Replace every reachable inline `workflowError` and renderer error with a structured UI error
   category. Raw backend codes/exceptions remain available only to development logging/tests.
3. Define a closed mapper from transport failures to UI categories: connectivity, invalid image,
   AI temporarily unavailable, understanding needs retry, session expired, no fitting activity,
   activity changed/stale, Pixi unavailable and unknown-safe fallback.
4. Audit and shorten every reachable screen:
   - Splash/onboarding: one value statement and one action.
   - Dashboard/profile: adult-oriented setup remains clear; no system jargon.
   - Capture/narration: image-required rule and audio/text alternatives are explicit.
   - AI processing: simple progress copy; remove Lightning/backend/ASR/Pixi wording.
   - Scene understanding: Vietnamese deduplicated claims; `Chọn ý chính` instead of Gate A terms.
   - Pixi preview: child-friendly reveal copy; technical details hidden.
   - Activity recommendations: up to three clear cards, no catalog/backend/mock copy.
   - Activity detail: real title, friendly material names and concise steps; safety and caregiver
     notes in a collapsed `Dành cho người lớn` section.
   - Feedback: simple observable choices; no internal contract state.
5. Keep one clear primary CTA per screen and use short verbs. Ensure every touch target is at least
   48x48 logical pixels, has disabled feedback, accessibility role/label/hint and sufficient color
   contrast.
6. Keep developer diagnostics behind an explicit development build/flag. The hidden native
   triple-tap route and debug screen must not expose internal screens/codes in the normal demo.
7. Keep the legacy video screen unreachable and do not add video generation/player work.

### Phase H — Fix PixiJS transport and recovery

1. Centralize renderer transport serialization and omit `None` optional fields.
2. Add a cross-language contract test that:
   - constructs the launch with the real Python model;
   - serializes it through the production HTTP path;
   - passes the exact JSON into the actual TypeScript `RendererLoadCommandSchema`;
   - verifies the renderer bootstrap/load/playback handshake.
3. Test whole-drawing `DRAW_REVEAL` with absent crop/mask/motion optionals and confirm no `null`
   values cross the bridge.
4. Keep the original uploaded drawing visible while Pixi loads and after a Pixi failure.
5. Replace protocol/version messages with the friendly modal. Internal parse details are captured
   only in development diagnostics.
6. Verify renderer capability expiry, duplicate message, oversized message, wrong instance and
   WebView load errors still fail closed without leaking details.

### Phase I — Verification and evidence

1. Vision/prompt tests:
   - bird/branch/leaf/perching fixture becomes Vietnamese, canonical and deduplicated;
   - malformed schema, empty result and poor-quality result share one repair budget;
   - at most two generations occur;
   - network/model/policy failures never use the quality retry;
   - narration supports/disambiguates but cannot invent a visual claim.
2. Topic tests:
   - no displayed English for covered labels;
   - no duplicate canonical claims;
   - specific subject outranks background;
   - topic is a concise sentence rather than one raw word when evidence permits;
   - conflicting narration lowers confidence and remains adult-confirmed.
3. Catalog/ranking tests:
   - HTTP runtime contains the curated expansion and V2 semantic matcher;
   - bird topics rank only animal/bird-related reviewed variants;
   - pouring/transfer activities are absent from the bird shortlist;
   - no more than three options are returned and priorities are stable;
   - every returned option independently passes strict P1 compilation;
   - no-fit returns zero options/typed blocked state, not a generic fallback;
   - changing selection preserves exact identity through ExperienceSpec and Gate B.
4. UI tests:
   - all reachable errors open the friendly modal;
   - rendered text never contains internal error/reason codes, contract names, template IDs,
     `backend`, `Gate A/B`, `ExperienceSpec`, `Pixi protocol` or provider names;
   - the recommendation screen shows 0..3 selectable titled cards;
   - activity detail shows Vietnamese display metadata, not IDs;
   - parent/guide details are available but collapsed by default;
   - rapid taps remain idempotent and existing-result recovery still works.
5. Pixi tests:
   - Python-to-TypeScript golden bridge parses successfully;
   - optional fields are omitted, not `null`;
   - Android WebView displays the original art and reports playback success;
   - failure preserves the source preview and presents a friendly modal.
6. Run focused and full relevant backend tests, Ruff, mypy for changed backend modules, mobile
   TypeScript/tests, renderer tests/build, `git diff --check`, architecture validation, harness
   validation and `python tools/validate_repository_security.py`.
7. Store sanitized outputs and owner emulator screenshots under this feature’s `evidence/` tree.
   Codex makes no Lightning/model request; the owner performs the final synthetic-image smoke under
   the existing approximately 25-credit ceiling.

## 6. Expected implementation areas

Likely files, subject to final tracing after approval:

- `tools/lightning_vision_v2_server.py`
- `backend/src/sketch2life/application/services/live_image_demo.py`
- `backend/src/sketch2life/application/services/raw_understanding_mapper.py`
- `backend/src/sketch2life/application/services/topic_semantics.py`
- `backend/src/sketch2life/application/services/semantic_activity_resolver.py`
- `backend/src/sketch2life/application/services/supervised_flow.py`
- `backend/src/sketch2life/application/ports/` for a V2 catalog/read-model port if needed
- `backend/src/sketch2life/contracts/schemas/` for the additive recommendation read model
- `backend/src/sketch2life/infrastructure/catalog/activity_semantics_v2.py`
- `backend/src/sketch2life/interfaces/http/app.py`
- focused backend unit/contract tests
- `apps/ui-mobile/BaoApp.tsx`
- `apps/ui-mobile/src/context/AppContext.tsx`
- `apps/ui-mobile/src/components/Kid3DButton.tsx`
- a reusable friendly modal component
- `apps/ui-mobile/src/screens/Flow1Screens.tsx`
- `apps/ui-mobile/src/screens/Flow2Screens.tsx`
- mobile tests and renderer bridge tests
- feature-local context, approval, decision and evidence records

No `.env`, provider token, model file, raw child data, external document, generated video or
unrelated FEAT-026 file may be staged.

## 7. Acceptance criteria

1. A bird-on-branch input with supporting narration yields a Vietnamese, deduplicated understanding
   containing a concrete bird subject when the model supplies sufficient grounded evidence.
2. The displayed topic is a natural Vietnamese sentence that combines subject and grounded
   action/context; covered concepts never appear as English or a lone raw word.
3. One vision request performs at most two model generations total across every repair mode.
4. The HTTP runtime uses the reviewed V2 expansion catalog and its semantic profiles.
5. The recommendation screen returns and displays at most three prioritized activities; every one
   passes the unchanged strict P1 eligibility/continuity checks before display.
6. A bird topic never displays the observed pouring/transfer activity or any other merely age-safe
   but semantically unrelated fallback.
7. Each option has a Vietnamese title, concise description, duration and human-readable material
   labels. Normal UI never displays activity/template IDs or safety/reason codes.
8. Selecting a different offered activity recompiles that exact activity without rerunning Qwen
   while Gate A remains unchanged.
9. All reachable expected errors use the friendly modal with a recovery action; no raw error code,
   exception, contract/provider term or absolute path is rendered.
10. All reachable BaoVC screens use concise child-friendly primary copy, one clear primary action,
    accessible controls and a collapsed adult detail layer where needed.
11. The backend Pixi launch passes the actual TypeScript schema, the WebView starts playback, and
    optional Python fields are omitted rather than serialized as `null`.
12. Pixi failure keeps the original drawing visible and offers a friendly retry/back action.
13. Image-required, audio/text narration, Gate A/Gate B authority, strict P1 policy, process-local
    demo state, future auth/save seams, original-art provenance and no-video scope remain intact.
14. Relevant tests and repository/security validators pass, and evidence contains no sensitive
    data or unrelated user-owned changes.
15. A feature-local full-flow UI audit matrix exists before implementation, covers every reachable
    screen and required error/loading/navigation state, records prioritized findings and ends with
    `UI_AUDIT_COMPLETE — NO CODE CHANGED` against the inspected commit.

## 8. Non-goals and safety boundaries

- No video generation/player integration.
- No production auth, persistence, Firebase storage/database or real child data.
- No LLM-generated activity outside the reviewed catalog.
- No weakening of age, safety, readiness, material, supervision, policy, fit or Gate B checks.
- No mobile-side semantic ranking or provider credentials/endpoints.
- No repeated Qwen retry loop and no Codex-triggered paid/live provider call.
- No generated visual asset changes in this scope; therefore the frontend visual-asset generation
  gate is not invoked. Existing approved/source artwork may be reused without mutation.

## 9. Implementation closure

The approved implementation is complete for the offline/API/UI scope. The runtime now loads the
curated V2 semantic catalog, returns at most three strict-fit activity cards, and revalidates the
adult's selected card before compiling the exact downstream activity. Topic display is localized,
deduplicated and grounded in the confirmed image/narration evidence; the live Qwen adapter has one
shared bounded quality-repair budget. The mobile journey uses friendly Vietnamese copy, a global
recovery modal, human-readable activity metadata, and source-preserving Pixi launch serialization.

Offline verification completed on 2026-09-23:

- focused vision/topic/activity/HTTP tests: 77 passed;
- full backend test collection: passed to 100% with configured skips only;
- mobile TypeScript check: passed;
- mobile UI copy/recovery guard: passed;
- art renderer tests: 9 passed;
- art renderer TypeScript check: passed;
- repository security validator: `REPOSITORY_SECURITY_VALID`;
- architecture validator: `ARCHITECTURE_VALID`;
- `git diff --check`: passed.

The owner remains responsible for the final Android emulator smoke and any live Lightning request
under the existing approximately 25-credit ceiling. No live provider request was made by Codex.

## 10. Approval gate

Implementation may start only after the owner approves this exact plan. On approval:

1. Compute and record this plan’s SHA-256 in `approvals/TASK_APPROVAL.md` with the approved scope,
   boundaries and timestamp.
2. Change the plan status to `APPROVED — IMPLEMENTATION AUTHORIZED`.
3. Complete Phase 0 read-only UI audit and record its no-code checkpoint before changing runtime or
   application source.
4. Implement in reviewable slices, updating feature context/evidence after each meaningful step.
5. Stop and request renewed approval if a frozen contract must be incompatibly changed, a new visual
   asset is required, or scope expands into video/auth/persistence/live-provider execution.
