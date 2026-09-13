# FEAT-020 — Semantic Activity Selection and Scalable Activity System Remediation Plan

**Status:** IMPLEMENTED — VALIDATED

**Feature:** `FEAT-020-backend-ai-workflow-demo`

**Purpose:** Replace the current lexical activity selection path with a scalable,
auditable semantic recommendation system, while improving the activity catalog
and preventing avoidable `NO_ELIGIBLE_ACTIVITY` failures.

**Implementation rule:** This plan is approved and its implementation is tracked by the feature-local evidence. No implementation is
authorized until the open decisions at the end are answered and recorded in the
feature approval/decision records.

## 1. Why this remediation is required

The latest real-AI Lightning run proves that the provider path is working:

```text
media validation → real ASR → real VLM → fusion → P1 → story/scene → art intent → handoff
```

However, the current P1 selector derives activity labels from natural-language
activity text and then accepts a token overlap as sufficient continuity. This
creates false positives such as:

```text
"bình minh" → token "bình" → activity rót hạt bằng bình
"bướm bay" → token "bay" → activity vòng tuần hoàn nước / bay hơi
```

The current score can then report `drawing_relevance=80` and `total_score=94`
for a weak lexical connection. At the same time, a real input can fail for a
younger band because no current activity label happens to overlap its observed
anchors.

This is not a problem that should be solved by adding one more synonym, lowering
the threshold, always selecting the first activity, or changing the demo image
until the output looks successful. The system needs an explicit semantic
interface between AI observations and curated Montessori activities.

## 2. Owner-confirmed baseline and proposed defaults

The existing FEAT-020 decisions remain in force unless this revision explicitly
supersedes them:

- real ASR and VLM are required for acceptance;
- the original image and provenance remain immutable;
- all four age bands are exercised by the default matrix command;
- hard safety, readiness, prerequisite, material, supervision and Gate rules are
  never bypassed;
- PixiJS runtime and video generation remain out of scope for this remediation;
- demo gates remain explicitly marked `DEMO_AUTOPILOT`;
- input image and WAV remain pre-generated, replaceable test inputs;
- no raw model output, credentials or child data may be committed.

The owner confirmed the following decisions in the current task:

1. Hybrid curated semantic engine: deterministic reviewed concepts and aliases
   are the eligibility gate; embeddings or an LLM may rank candidates but may not
   promote an unsupported activity into an eligible result.
2. Safe fallback tier with AI suggestion: every age band has at least one
   reviewed baseline activity with broad but explicit anchor compatibility.
   Fallback is visible in the contract and is not reported as an exact semantic
   match. AI may suggest candidates, but every suggestion must pass the reviewed
   semantic profile and all hard rules before it can be selected.
3. Expand to the full 100-activity target now: the remediation includes the
   semantic profile, content-quality, material, safety and coverage work for the
   full planned catalog, not only the current 20 records.
4. Test matrix reports partial readiness: the backend test/demo matrix may return
   PARTIAL_SUCCESS and must explicitly list ready and unavailable age bands.
   Production/session behavior remains fail-closed until a separate product
   decision changes it.

## 3. Desired system behavior

For each requested age band, the workflow must produce one of these explicit
outcomes:

```text
EXACT_MATCH_READY
ALIAS_MATCH_READY
SAFE_FALLBACK_READY
NO_ELIGIBLE_ACTIVITY
HUMAN_REMAP_REQUIRED
```

The first three can continue to Gate B if all hard rules pass. The last two are
typed blocked outcomes and must never be silently converted to success.

The selected activity must retain:

- the source image/audio artifact IDs and hashes;
- the observation claim IDs used as evidence;
- the semantic concept IDs and match mode;
- the catalog activity/template/material versions;
- the age-band and readiness context;
- the match score breakdown and rejected alternatives;
- fallback reason, when fallback was used;
- supervision, duration range, safety rules and accessibility requirements.

## 4. Target architecture

### 4.1 New domain boundary: semantic activity compatibility

Add a provider-neutral domain model between `WorkflowFusionV1` and
`P1ExperienceCompiler`. The compiler should receive a typed compatibility result,
not infer semantics from arbitrary catalog prose.

Proposed concepts:

```text
ObservationClaim
  ├─ modality: VISION | ASR | FUSION
  ├─ kind: SUBJECT | ACTION | VISUAL_FEATURE | STORY
  ├─ canonical_concept_id
  ├─ surface_forms_vi
  ├─ confidence
  └─ source_claim_ids

ActivityAnchorProfile
  ├─ required_concepts
  ├─ accepted_concepts
  ├─ reviewed_aliases_vi
  ├─ accepted_observation_kinds
  ├─ required_relation_patterns
  ├─ disallowed_concepts
  ├─ fallback_tier
  └─ profile_version

ActivityCompatibility
  ├─ activity/template reference
  ├─ match_mode: EXACT | ALIAS | FALLBACK | NONE
  ├─ matched_concept_ids
  ├─ evidence_claim_ids
  ├─ score_breakdown
  ├─ ambiguity_penalty
  ├─ hard_failures
  └─ rejected_reason_codes
```

The model must be independent of Qwen, Whisper, embeddings, HTTP, database and
UI. Provider adapters only produce observations; the semantic boundary decides
what the catalog is allowed to consume.

### 4.2 Catalog schema evolution

Keep the existing activity records versioned and preserve their provenance. Add
a separate semantic profile rather than deriving eligibility from title or
`purpose_vi` at runtime.

Each activity should declare, in reviewed data:

- a stable activity concept family;
- exact phrases that are strong evidence;
- Vietnamese aliases and inflection variants;
- acceptable observation kinds;
- required co-occurring concepts or relations;
- concepts that are too ambiguous to use alone;
- disallowed concepts that indicate a false semantic bridge;
- whether the activity is an exact-match candidate, fallback candidate, or both;
- minimum evidence strength;
- age/readiness/prerequisite/material/safety references;
- content review status and schema/profile version.

Examples of required semantic tightening:

```text
ACT-0026: rót hạt khô / chuyển hạt giữa vật chứa
  allowed: hạt khô, rót hạt, chuyển hạt, vật chứa + thao tác rót
  reject-alone: bình, chứa, chuỗi

ACT-0058: vòng tuần hoàn nước
  allowed: bay hơi, ngưng tụ, giọt nước, mực nước theo thời gian
  reject-alone: bay, bướm, nước

ACT-0091: mô hình pha Mặt Trăng
  allowed: mặt trăng, pha mặt trăng, ánh sáng mặt trời + mặt trăng
  reject-alone: mặt, sáng, trăng nếu không có reviewed context

ACT-0004: tìm vật bị che
  allowed: đồ vật bị che, tìm vật dưới khăn, che một phần + tìm/lấy
  reject-alone: vật, khăn, tìm
```

These are design examples, not automatic catalog edits. Every mapping must be
reviewed against the activity's actual instructions and safety requirements.

### 4.3 Matching pipeline

Replace the current single-token path with ordered stages:

1. **Normalize without destroying provenance**
   - preserve original Vietnamese text;
   - normalize case, whitespace and punctuation;
   - retain diacritics and a canonical concept ID;
   - never collapse evidence into an untraceable string.

2. **Build observation claims**
   - map VLM entities/actions/themes and ASR claims into canonical concepts;
   - record modality support and claim IDs;
   - distinguish a phrase such as `bình minh` from the concept `bình`;
   - preserve unmatched and conflicting terms.

3. **Exact concept/phrase match**
   - strongest eligibility signal;
   - must match an explicit activity profile;
   - may pass hard semantic continuity if kind and relation requirements pass.

4. **Reviewed alias match**
   - only aliases declared by the catalog profile can match;
   - alias usage must be emitted in diagnostics;
   - generic token overlap is not an alias.

5. **Context/relation match**
   - require co-occurring concepts for ambiguous words;
   - examples: `bay hơi` is valid, `bay` alone is not; `mặt trăng` is valid,
     `mặt` alone is not.

6. **Optional model-assisted ranking**
   - embedding/LLM ranking can order already eligible candidates;
   - it cannot create a new eligibility edge;
   - low-confidence or contradictory results remain blocked or fallback-eligible
     only under explicit policy.

7. **Hard-rule compilation**
   - age, readiness, prerequisite, material, supervision, policy, safety and
     Gate A checks remain mandatory;
   - semantic match mode is evaluated before fit scoring;
   - no match mode may override hard failures.

### 4.4 Scoring model

Replace the current `match_score * 20` drawing score with a transparent score
vector. Suggested dimensions:

```text
semantic_evidence       0–100
phrase_strength         0–100
modality_agreement      0–100
relation_completeness   0–100
age_readiness_fit       0–100
ambiguity_penalty       0–100
contradiction_penalty   0–100
```

Rules:

- a single generic token cannot produce `PASS`;
- an ambiguity penalty can force `REJECT` even if other dimensions are high;
- an exact phrase with one modality can pass only if the activity profile allows
  that evidence type;
- corroboration from ASR and VLM improves ranking but is not required for every
  visual-only activity;
- the score explanation must list the matched concepts and rejected evidence;
- score thresholds are versioned and tested as policy, not hidden constants.

## 5. Preventing `NO_ELIGIBLE_ACTIVITY` without unsafe bypasses

### 5.1 Coverage matrix

Create a machine-validated coverage matrix for every age band:

- at least one exact/alias activity for each supported concept family;
- at least one safe baseline fallback activity;
- material availability and substitute coverage;
- readiness/prerequisite satisfiability under demo context;
- supervision and safety completeness;
- duration range completeness;
- semantic positive and negative examples.

The validator must fail before runtime if an age band has no usable fallback or
if all activities are blocked by missing material/readiness/prerequisite data.

### 5.2 Safe fallback tier

Fallback is not “select the first activity.” It is a curated tier with:

- explicit `fallback_profile_id`;
- broad but bounded concept compatibility;
- age-specific steps and safety rules;
- known material options and substitutes;
- an adult confirmation requirement;
- a clear `SAFE_FALLBACK` match mode in the result;
- a reason such as `NO_EXACT_SEMANTIC_MATCH` or
  `EXACT_MATCH_BLOCKED_BY_READINESS`.

If no safe fallback can pass hard rules, the workflow must still return
`NO_ELIGIBLE_ACTIVITY`. The objective is to eliminate avoidable failures, not to
pretend that every input is safe for every age.

### 5.3 AI suggestion boundary

AI suggestion is an accelerator, not an authority. The suggestion service may:

- propose a canonical concept for an observation;
- rank reviewed aliases and activity profiles that already passed semantic
  compatibility;
- identify likely missing catalog coverage;
- explain why a candidate appears relevant.

It may not:

- invent an activity or activity ID;
- turn a generic token into an eligible concept;
- override age, readiness, prerequisite, material, supervision or safety rules;
- convert a blocked exact match into a successful fallback without the fallback
  profile passing its own rules;
- write directly to the catalog at runtime.

Every AI suggestion is recorded with model/provenance metadata, confidence,
candidate IDs, deterministic validation outcome and final human/demo decision.
### 5.4 All-age demo input

After the matcher and catalog are corrected, replace the current butterfly-only
demo input only if needed. The replacement image/WAV must be deliberately
multi-anchor and remain a replaceable pre-generated test asset. It must exercise
real ASR/VLM and must not contain precomputed activity IDs or fixture outputs.

The asset provenance record must document which observable concept families are
intended to cover each age band. Runtime generation of assets remains forbidden.

## 6. Activity catalog quality improvement

The remediation now includes the full planned 100-activity target. The existing
20 records are the migration pilot and the remaining 80 records must pass the
same schema, semantic, safety and material validators before they are visible as
eligible catalog entries:

### 6.1 Content completeness

Every activity record must have:

- clear child-facing objective in Vietnamese;
- observable readiness criteria;
- prerequisites and progression links;
- exact materials plus approved household substitutes;
- preparation steps;
- short, unambiguous presentation steps;
- independent child work cycle;
- restoration steps;
- control of error;
- duration minimum/maximum;
- direct supervision level;
- hazards and stop conditions;
- accessibility notes;
- feedback observations that do not infer personality or diagnosis;
- semantic anchor profile and negative examples.

### 6.2 Catalog review lifecycle

Use explicit statuses:

```text
DRAFT → SEMANTIC_REVIEW → SAFETY_REVIEW → OWNER_REVIEWED → DEMO_ELIGIBLE → PRODUCTION_ELIGIBLE
```

The current `PROVISIONAL_OWNER_REVIEWED` and `production_eligible=false` state
must remain honest until the appropriate review evidence exists. The backend
demo may consume demo-eligible records, but it must not label them production
ready.

### 6.3 Activity evaluation cases

Add reviewed examples per activity:

- positive exact phrase;
- positive alias;
- positive multimodal corroboration;
- ambiguous token that must be rejected;
- visually related but semantically wrong input;
- age/readiness/prerequisite block;
- material/safety block;
- fallback eligibility case.

These cases become automated contract tests and prevent future catalog edits from
reintroducing the current false positives.
### 6.4 Full 100-activity expansion workstream

The catalog expansion is a first-class workstream, not a list of placeholder
rows. For each of the 100 activities, complete:

- canonical activity ID/version and immutable provenance;
- age range, age-band coverage and progression links;
- objective mapping and Vietnamese child-facing wording;
- readiness and prerequisite graph membership;
- primary material plus approved household substitute;
- preparation, presentation, child work cycle and restoration steps;
- control of error, duration range and direct-supervision policy;
- hazard, stop-condition and accessibility metadata;
- semantic anchor profile with positive, alias, ambiguous and negative examples;
- fallback eligibility and fallback ordering where appropriate;
- review status and evidence references.

Before an activity becomes DEMO_ELIGIBLE, the catalog pipeline must prove:

- its profile has no generic-token-only eligibility path;
- its positive examples reach the intended activity;
- its negative examples reject lexical false positives;
- its age, readiness, prerequisite, material and safety rules are satisfiable in
  at least one valid context;
- its material IDs exist in the full material registry;
- its progression edges do not create cycles or impossible prerequisites;
- at least one asset/render-intent family can represent its activity handoff.

The 100-activity target may be delivered in catalog batches, but the coverage
validator must report incomplete batches explicitly and the workflow must never
treat a placeholder or unreviewed activity as eligible.

## 7. Contract and status changes

Introduce a backward-compatible contract revision rather than silently changing
the meaning of `BackendWorkflowResultV1`.

Required additions or revisions:

- `semantic_match_mode` on the selected band/context;
- `semantic_profile_id` and version;
- matched concept IDs and evidence claim IDs;
- score breakdown and rejected alternatives;
- `fallback_reason` when applicable;
- duration as `{min_minutes, max_minutes}` or an equivalent versioned range;
- explicit demo feedback status separate from real caregiver feedback;
- per-band aggregate counts for exact, alias, fallback and blocked outcomes;
- `NO_EXACT_MATCH`, `SAFE_FALLBACK_SELECTED` and
  `DEMO_FEEDBACK_PLACEHOLDER_READY` reason/stage vocabulary where needed.

Compatibility rules:

- keep the old contract readable for existing evidence;
- add a new contract version for materially new fields;
- never reinterpret old `FEEDBACK_RECORDED` data as real feedback;
- preserve manifest hashing over the complete sanitized payload;
- do not expose raw model prompts or raw model outputs.

## 8. Diagnostics and observability

For every age band, emit safe diagnostics such as:

```json
{
  "candidate_count": 20,
  "semantic_candidates": 3,
  "hard_rule_candidates": 1,
  "selected_match_mode": "ALIAS",
  "matched_concepts": ["..."],
  "rejected_reason_counts": {
    "AMBIGUOUS_SINGLE_TOKEN": 4,
    "MISSING_REQUIRED_RELATION": 5,
    "BLOCK_MISSING_READINESS": 2
  },
  "fallback_considered": true,
  "fallback_selected": false
}
```

For the test-only all-age matrix, add an explicit aggregate section:

{
  "matrix_policy": "REPORT_PARTIAL_TEST_ONLY",
  "ready_age_bands": ["3-6", "6-9", "9-12"],
  "unavailable_age_bands": [
    {
      "age_band": "0-3",
      "terminal_status": "NO_ELIGIBLE_ACTIVITY",
      "blocking_reason_codes": ["NO_EXACT_MATCH", "FALLBACK_NOT_READY"]
    }
  ]
}

PARTIAL_SUCCESS is valid only for this explicitly named test/demo matrix policy.
It must not change the behavior of a future real child session that requires one
ready activity for its selected age.
Diagnostics must be deterministic for a fixed seed and input contract, sanitized,
and stored under the FEAT-020 evidence directory. They must not include prompts,
provider payloads, secrets, absolute machine paths or raw child media.

## 9. Test strategy

### 9.1 Domain/unit tests

- exact phrase match succeeds;
- reviewed alias match succeeds;
- generic single-token match is rejected;
- `bình minh` does not match ACT-0026;
- `bướm bay` does not match ACT-0058;
- `mặt trời` matches only a reviewed compatible profile;
- contradictory modality evidence is preserved and penalized;
- hard rules still block otherwise semantically good activities;
- fallback is selected only when its profile and hard rules pass;
- no fallback produces typed `NO_ELIGIBLE_ACTIVITY`.

### 9.2 Catalog validation tests

- every activity has a semantic profile;
- every profile has positive and negative examples;
- every age band has exact/alias coverage and a usable fallback;
- every selected material ID exists and has a primary/substitute policy;
- duration ranges are valid;
- prerequisites form a valid progression graph;
- safety and supervision fields are complete;
- profile versions and record hashes are stable.

### 9.3 Contract/integration tests

- old manifest remains parseable where compatibility is promised;
- new manifest hash remains valid;
- selected activity, objective, template, semantic profile and source claims remain
  identity-consistent through story, art intent, video boundary and handoff;
- demo feedback cannot be serialized as completed caregiver feedback;
- all four age bands produce distinct or justified selection vectors under multiple
  seeds;
- diagnostics explain every blocked band.

### 9.4 Real-AI Lightning acceptance

The single acceptance command remains the source of truth, but acceptance adds:

- at least three fixed seeds for variation checks;
- one all-age run using the committed test asset pair;
- one intentionally non-matching image/audio pair to verify safe fallback or
  typed no-match behavior;
- one input that exercises ambiguous vocabulary;
- verification that no runtime asset/model generation is used for PixiJS assets;
- no fixture adapter, no silent fallback, no fake model output.

## 10. Implementation sequence

The work should be delivered in a small number of meaningful changes, not one
commit per question or field:

### Phase A — Contract and policy foundation

- finalize the owner decisions;
- add ADR/decision record for semantic engine and fallback policy;
- define new semantic profile and compatibility contracts;
- define status vocabulary and duration range contract;
- add catalog/manifest migration rules.

### Phase B — Catalog and activity remediation

- migrate all 20 current activities to explicit semantic profiles;
- author and migrate the remaining 80 activities to the same versioned schema;
- add positive/negative semantic examples for all 100 activities;
- repair duration, material and progression metadata;
- add a fallback activity tier for each age band;
- run the full 100-activity content, semantic, material and safety review;
- add coverage validator and catalog evidence.

### Phase C — Matching and selection engine

- implement normalization and observation-claim mapping;
- implement exact/alias/context matching;
- remove token-only eligibility;
- integrate optional model-assisted ranking behind the deterministic gate;
- implement score breakdown and rejected-candidate diagnostics;
- preserve P1 hard rules and Gate B identity checks.

### Phase D — Workflow and lifecycle semantics

- connect semantic compatibility to the backend orchestrator;
- emit exact/alias/fallback modes;
- fix duration range propagation;
- separate demo feedback placeholder from real feedback;
- use REPORT_PARTIAL_TEST_ONLY for the test/demo all-age matrix, listing ready and unavailable bands explicitly;
- keep future real child-session selection fail-closed for the selected age band;
- update story/scene bridge to use the selected semantic concept, not an arbitrary
  surface token.

### Phase E — Test assets and real-AI validation

- revise the pre-generated image/WAV only after the matcher is correct;
- record asset provenance and intended age coverage;
- run static, unit, contract, catalog and security validators;
- run Lightning real-AI acceptance with fixed seeds;
- store sanitized manifests and diagnostics in feature-local evidence.

### Phase F — Scale preparation

- publish the semantic profile authoring guide;
- add a catalog lint command suitable for CI;
- validate the completed 100-activity catalog and define the next expansion boundary beyond 100;
- define material-family reuse and localization policy;
- document how future activity authors add concepts without creating token traps;
- leave embeddings/LLM ranking behind a replaceable port for future scale.

## 11. Acceptance criteria

The remediation is complete only when all of the following hold:

1. No eligible activity is selected solely because of a generic token overlap.
2. The current false positives are covered by regression tests and rejected.
3. Every one of the 100 planned activities has an explicit, versioned semantic
   profile, or is explicitly blocked as an incomplete catalog batch.
4. Every age band has at least one reviewed safe fallback or intentionally records
   why no safe fallback exists.
5. AI suggestions are auditable and cannot bypass deterministic semantic or hard
   eligibility checks.
6. The test all-age output may be PARTIAL_SUCCESS, but clearly distinguishes
   exact, alias, fallback, ready and unavailable bands.
7. Fit scores explain their evidence and no longer report the same high score for
   materially different weak matches.
8. Duration is present as a valid range when the catalog contains one.
9. Feedback/history output cannot be mistaken for real caregiver feedback.
10. Source image identity and provenance remain intact across all downstream
    contracts.
11. The real Lightning command produces a complete per-band matrix report for the
    approved all-age test input, including explicit unavailable bands when the
    test catalog is incomplete.
12. The real Lightning command succeeds with no fixture adapter and no runtime
    PixiJS asset generation once the approved coverage and fallback set is complete.
13. Security and harness validators pass before the implementation commit/push.

## 12. Approval boundary

The owner has answered the four planning questions in the current task:

- hybrid curated semantic eligibility;
- safe fallback per age band with bounded AI suggestions;
- full 100-activity catalog scope;
- test-only PARTIAL_SUCCESS with explicit ready and unavailable age bands.

The answers are recorded in
DECISIONS_SEMANTIC_ACTIVITY_REMEDIATION.md.

This plan is now ready for explicit implementation approval. Until that approval
is recorded in approvals/TASK_APPROVAL.md, no source, catalog or contract
implementation should begin.