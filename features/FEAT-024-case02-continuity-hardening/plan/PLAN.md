# FEAT-024 plan — Case 02 resilience and end-to-end continuity

## 1. Approval gate

Approval was recorded in `approvals/TASK_APPROVAL.md` on 2026-09-15. This
plan remains the source of scope for the implementation and its release gate.

## 2. Desired backend flow

```text
media validation
  -> real ASR + typed ASR diagnostics
  -> real VLM + bounded schema normalization
  -> fusion / scene understanding
  -> age-aware semantic matching
  -> continuity classification
  -> planned video scene + bridge script
  -> deferred video status (actual score = null)
  -> off-screen activity handoff
  -> feedback-ready context
```

When a real video renderer is introduced later:

```text
planned video
  -> generated video artifact
  -> post-generation continuity evaluator
  -> actual video continuity score
  -> final bridge/activity handoff
```

The demo must never claim the second half has run while video is deferred.

## 3. Workstream A — make case 02 pass without weakening safety

### A1. Capture a useful, closed diagnostic

Extend the typed workflow failure evidence so a VLM mapping failure reports a
closed diagnostic category (without raw provider content):

- strict JSON parse failure;
- JSON root is not an object;
- top-level key rejected;
- schema missing required field;
- schema extra field;
- schema type/constraint invalid;
- duplicate observation ID;
- reference integrity violation.

Include the same bounded category for ASR mapping/runtime failure where the
typed result permits it. Preserve `attempt_number`, `repair_attempted`,
`retryable`, and `policy_execution_state`. Do not expose raw model output,
prompt text, local model paths, or transcript content in failure evidence.

### A2. Add semantics-preserving VLM normalization

Before strict `VisionUnderstandingSuccessV2` validation, add one deterministic
normalization boundary. It may perform only mechanical repairs that do not
invent a scene claim:

- unwrap the already-supported JSON fence;
- normalize a scalar text `label`, `predicate`, or `note` into the declared
  Vietnamese text-field shape;
- fill omitted optional arrays with `[]`;
- generate deterministic local observation IDs only when the item is otherwise
  structurally valid and the ID is absent;
- discard an invalid relation/action reference rather than inventing a target;
- reject unknown top-level keys and malformed semantic values.

If no valid observable entity/theme remains after normalization, return the
typed schema failure. Never replace the VLM result with an image caption,
fixture, hard-coded bicycle concept, or catalog lookup.

### A3. Tighten the Vietnamese prompt protocol

Revise the prompt protocol version and add examples that are robust for simple
child drawings:

- entity-only output is valid;
- actions/relations/themes must be `[]` unless all IDs and references are
  valid;
- every text field must use the declared object shape;
- no inferred safety behavior, intention, or lifecycle stage unless visibly
  present;
- use fewer observations rather than risk invalid references.

The prompt remains Vietnamese and the protocol hash must flow into model
provenance/evidence.

### A4. Verify ASR as a separate failure surface

Run case 02 through real faster-whisper with the existing local model and
record only typed metadata: status, language, duration, segment count,
provider/runtime error category, and model provenance. Do not insert an
expected transcript into the workflow. If the WAV itself causes the ASR
failure, replace it with a short Vietnamese pre-generated narration and update
its provenance/hash; if the model runtime fails, fix the runtime boundary and
keep the current audio.

The acceptance result must distinguish:

- `ASR_FAILED` — ASR is required and failed;
- `VISION_SCHEMA_INVALID` — VLM output could not be safely mapped;
- `AI_FAILED` — only the aggregate terminal projection.

### A5. Real-AI case matrix

Use both replaceable input pairs on Lightning with the same model revisions:

- case 01 butterfly/flower: regression must remain successful;
- case 02 bicycle/safety: media, ASR, VLM, fusion and catalog stages must run;
- run `--age-mode all` and retain per-age readiness/unavailability;
- no fixture adapter or precomputed recommendation is allowed.

## 4. Workstream B — versioned continuity contract

### B1. Add `ExperienceContinuityV2`

Create a versioned contract with these dimensions:

```json
{
  "drawing_video_planned_score": 0,
  "drawing_activity_score": 0,
  "video_activity_planned_score": 0,
  "age_fit_score": 0,
  "objective_fit_score": 0,
  "safety_score": 0,
  "planned_overall_score": 0,
  "actual_video_continuity_score": null,
  "actual_video_status": "NOT_RENDERED",
  "continuity_mode": "DIRECT_CONTINUATION",
  "reason_codes": []
}
```

Required rules:

- `actual_video_continuity_score` is `null` while `generated_asset_ref` is
  `null` or video status is `DEFERRED`;
- `actual_video_status=ASSESSED` requires a generated video reference, source
  identity/hash, and post-generation evidence;
- `planned_*` fields are never serialized as `actual_*` fields;
- planned scores are bounded 0–100 and derived from explicit evidence;
- a related expansion cannot receive a perfect direct drawing score;
- a planned video score of 100 is permitted only when it means the plan
  preserves the confirmed anchor/objective/template; it must not be presented
  as rendered-video evidence.

Keep `ActivityFitEvaluationV1.video_continuity` readable for legacy consumers,
but mark it as a legacy projection of the planned score. New V2 payloads must
consume `ExperienceContinuityV2`.

### B2. Replace the current score shortcut

Remove the current binary behavior:

```python
continuity = 100 if anchor_matches and objective_matches else 0
```

Use evidence-based scoring:

- direct observed anchor in activity: high drawing/activity score;
- alias or concept-level match: lower score with reason code;
- related expansion: bounded score reduction and `RELATED_EXPANSION`;
- objective mismatch: hard reject or score below threshold;
- safety/prerequisite/age failures: hard reject;
- actual video score: unavailable until post-generation evaluation.

The ranking trace must include the continuity mode and planned score so a
candidate winning by a weak related expansion is explainable.

## 5. Workstream C — age objective and catalog corrections

### C1. Age 0–3 butterfly route

Use existing catalog objective IDs, not a new ungoverned ID:

- primary: `OBJ_MOVEMENT_COORDINATION` for dõi mắt/phối hợp tay-mắt;
- optional secondary: `OBJ_SENSORIAL_DISCRIMINATION` only when the variant
  actually asks for visual discrimination;
- replace the mismatched child-facing goal with a concrete Vietnamese goal,
  such as “Dõi mắt theo chuyển động chậm và chỉ vào cánh bướm.”;
- ensure `age_adaptation` and `activity_plan.presentation_steps_vi` express the
  same observable behavior.

Add a validator that checks the variant primary objective against its
observable behavior and rejects the old sensory-classification mismatch.

### C2. Age 9–12 lifecycle route

Keep lifecycle as a useful activity if it passes safety and catalog review, but
classify it as `RELATED_EXPANSION` because eggs/caterpillar/chrysalis are not
observed in the source drawing. It must:

- receive a reduced drawing relevance/planned continuity score;
- carry reason code `TOPIC_NOT_DIRECTLY_OBSERVED`;
- not be labeled `PERSONALIZED_EXACT`;
- provide a bridge cue that explicitly introduces the expansion before the
  off-screen task.

If a direct butterfly-structure/activity candidate exists for 9–12, ranking
must prefer it over the lifecycle expansion unless the direct candidate is
ineligible after age/safety/prerequisite filtering.

### C3. Catalog metadata

Extend the variant contract/loader with reviewable metadata for:

- `continuity_mode`;
- `direct_observation_concepts`;
- `expansion_bridge_required`;
- age-specific `child_facing_goal_vi`;
- age-specific `video_setup_vi` and `offscreen_handoff_vi`;
- optional `video_focus_cues_vi`.

For legacy rows, derive conservative defaults in the loader and emit a
validation warning. Butterfly rows must be explicit before the new acceptance
run. `DEMO_ELIGIBLE` remains `production_eligible=false`.

## 6. Workstream D — concrete video-to-activity bridge

### D1. Add `ActivityBridgeV2`

The bridge must be typed and catalog-driven, not one generic sentence:

- `bridge_mode`: `DIRECT_CONTINUATION` or `RELATED_EXPANSION`;
- `video_setup_vi`: what the planned video demonstrates;
- `video_focus_cues_vi`: what the child should notice;
- `handoff_prompt_vi`: the question/prompt at the end of the video;
- `offscreen_activity_intro_vi`: how the real-world task continues;
- `anchor_labels_vi`, objective ref, activity ref and age band;
- `status`: `PLANNED`, `READY_FOR_RENDER`, `BLOCKED`;
- source catalog revision and provenance.

Example 6–9 direct bridge:

```text
Video setup: bướm trong tranh bay đến bông hoa và dừng lại.
Focus cue: nhìn hai bên cánh bướm.
Handoff: “Con nhận ra hai bên cánh giống nhau ở điểm nào không?”
Off-screen: tìm điểm giống/khác và hoàn thiện nửa cánh còn thiếu.
```

Example 9–12 related bridge:

```text
Video setup: bướm lớn lên và thay đổi theo thời gian.
Handoff: “Bướm có thể thay đổi như thế nào trước khi bay?”
Off-screen: sắp xếp thẻ vòng đời và lập nhật ký quan sát.
```

When video is deferred, these are plans/scripts only. The output must say
`READY_FOR_RENDER` or `PLANNED`, never imply that the generated video already
contains the cues.

### D2. Identity validation

Bridge validation must fail if anchor, objective, activity, age band or
continuity mode diverges from the selected experience. It must also reject a
direct bridge that mentions an unobserved concept without explicitly changing
to `RELATED_EXPANSION`.

## 7. Tests and evidence

### Unit tests

- VLM mechanical normalization for valid simple entity-only output.
- Rejection of unknown keys, unsafe claims, malformed references and empty
  post-normalization observations.
- Closed mapping diagnostics for each schema error family.
- ASR typed failure projection and distinction from VLM failure.
- continuity score invariants: planned vs actual, deferred video, related
  expansion penalty, direct candidate preference.
- objective/observable-behavior validator for 0–3.
- bridge identity and mode validation.

### Offline corpus

Extend the provider-free corpus with butterfly direct, butterfly lifecycle
expansion, bicycle/transport and no-observation cases. Assert:

- no false `actual_video_continuity_score`;
- no perfect score for related expansion;
- age-specific objective/goal alignment;
- direct candidate outranks related expansion when both are eligible;
- bridge mode and reason codes are deterministic;
- same seed is reproducible and different seeds can diversify eligible
  activities.

### Lightning evidence

Record under this feature's `evidence/`:

- case 01 and case 02 commands, model revisions and environment readiness;
- media hashes and validation decisions;
- typed ASR/VLM/fusion stage outcomes;
- per-age readiness and selected activity identities;
- planned continuity fields and `actual_video_status=NOT_RENDERED`;
- no raw model output or sensitive media.

### Required verification commands

```bash
python -m pytest backend/tests/unit -q
python -m ruff check backend/src backend/tests
python -m mypy backend/src/sketch2life
python tools/validate_harness.py
python tools/validate_repository_security.py
python -m sketch2life.benchmark.catalog_offline
```

The real-AI smoke is a release-candidate gate on Lightning Studio, not a
fixture substitute for the offline suite.

## 8. Delivery sequence

1. Approve this plan and record the plan revision/hash.
2. Add/validate VLM and ASR diagnostic contracts and mechanical mapping tests.
3. Patch prompt/runtime mapping and rerun case 02 in Lightning.
4. Add continuity V2 contracts and scoring invariants.
5. Correct catalog age objectives and direct/related metadata.
6. Implement catalog-driven bridge and identity validation.
7. Run unit, lint, type, harness, security and offline corpus suites.
8. Run both real-AI cases on Lightning and store evidence.
9. Review diff/evidence, update status/context/decisions, then commit once.

## 9. Acceptance criteria

- [ ] Case 02 no longer stops at `VISION_SCHEMA_INVALID` for its current
  replaceable image/WAV under the pinned Lightning runtime, or produces a
  specific typed failure with a reproducible diagnostic if the runtime itself
  is unavailable.
- [ ] Case 01 remains passing under the same runtime.
- [ ] No fixture transcript, VLM result, recommendation or hard-coded case-02
  concept is used.
- [ ] 0–3 objective and child-facing goal describe the actual visual-tracking/
  hand-eye activity.
- [ ] 9–12 lifecycle activity is marked `RELATED_EXPANSION`, gets a non-perfect
  direct relevance score, and has an explicit bridge cue.
- [ ] Direct continuation outranks related expansion when both are eligible.
- [ ] Generic bridge text is replaced by a typed age/activity-specific bridge.
- [ ] Deferred video has `actual_video_continuity_score=null` and
  `actual_video_status=NOT_RENDERED`.
- [ ] No V2 contract claims rendered-video continuity without a generated
  artifact and post-generation evidence.
- [ ] Unit/offline suites pass; both real-AI cases are evidenced separately.
- [ ] Harness and repository security validation pass before commit.
