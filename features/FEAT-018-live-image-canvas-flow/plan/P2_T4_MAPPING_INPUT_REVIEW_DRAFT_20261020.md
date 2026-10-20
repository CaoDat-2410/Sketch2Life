# FEAT-018 P2-T4 — Input Fixture Specification for Review

- Status: `DRAFT — REVIEW INPUT DESIGN ONLY`.
- Revision: 3, 2026-10-20; responds to Claude Cloud delta-review of commit `fc1f987`.
- Branch: `feature/feat018-p2t4-mapping-diagnostics`.
- Related plan: [mapping diagnostics plan](P2_T4_MAPPING_DIAGNOSTICS_PLAN_DRAFT_20261020.md).

This is a proposed test-input specification, not an executable manifest, runtime contract or owner
approval. Only documentation/source inspection has occurred. Future tests require implementation
approval for the exact file scope in the related plan.

## 1. Boundaries and source identity

Use B1 for Raw proposal/ref/narration validation, B2 for existing Gate A conversion with explicit
synthetic confirmation and in-memory dependencies, and B3 for unmodified per-profile P1 matching.
B3 is an observation oracle, not an eligibility resolver. No P1 context/age fit, compiler, Gate B,
model or provider execution is included.

The input manifest must identify fixture schema revision, case ID/family, target activity/version,
source artifact/claim IDs and synthetic source hash, upstream contract/profile/config identities,
Raw contract version, applicable gate-confirmation version/actor/meaning version, and boundary-specific
expectations. Keep original Raw and actual confirmation alongside derived anchor/scene projections;
do not add report metadata as extra fields to frozen contracts.

Fixture provenance is identified at manifest level by `provenance_kind=SYNTHETIC_FIXTURE` and
`provider_execution=NOT_EXECUTED`; include the fixture construction revision and input digest.
`RawProvenanceV1.profile_id` still uses the contract-required `QWEN3_VL_8B_INSTRUCT_BF16_V1` enum and
a successful Raw result still requires complete, contract-valid `model_provenance`. Reuse existing
typed fixture patterns; do not invent a synthetic enum, widen schemas or describe those required
model-identity fields as evidence of actual model execution/measurement.

For matcher checks record these independently:

- Golden target activity version: 2.
- Legacy catalog profile: `SAP-ACT-xxxx-V1`, `profile_version=1`, `activity_version=1` in the source
  profile JSON; this is not the golden template version.
- Effective V2 profile/version/digest as returned by the base catalog loader; source inspection
  shows `SAP2-ACT-xxxx-V2` for these templates. Confirm after approval instead of manufacturing a
  V2 profile or changing source JSON to match an expectation.
- Source file digest, profile `provenance_sha256`, effective activity version and observed variant
  ID. The current loader may retain `-V1` in a variant ID; report that lineage, not a silent rewrite.

## 2. Proposed exact-label inventory

The English pilot seeds remain contextual descriptions in `ACTIVITY_PILOT_MATRIX.md`. They are not
matcher inputs or a translation rule. The following proposed primary labels are copied from
`data/activity-catalog/golden/v1/semantic-anchor-profiles.v1.json`, `exact_phrases_vi[0]` for each
target. Bind the actual source/profile digest during fixture preparation; these strings alone
do not establish an observed match.

| Activity v2 | Proposed exact label | Legacy profile | Pilot fallback tier |
|---|---|---|---|
| ACT-0004 | tìm đồ vật dưới khăn | SAP-ACT-0004-V1 | NONE |
| ACT-0016 | chuyển đồ vật lớn giữa hai bát | SAP-ACT-0016-V1 | NONE |
| ACT-0019 | chuỗi rửa tay | SAP-ACT-0019-V1 | NONE |
| ACT-0020 | lau vết nước nhỏ | SAP-ACT-0020-V1 | NONE |
| ACT-0023 | tưới cây nhỏ | SAP-ACT-0023-V1 | NONE |
| ACT-0026 | rót hạt khô | SAP-ACT-0026-V1 | AGE_BASELINE |
| ACT-0030 | khung cài nút | SAP-ACT-0030-V1 | NONE |
| ACT-0033 | sắp bàn cho một người | SAP-ACT-0033-V1 | NONE |
| ACT-0039 | phân cấp bảng màu | SAP-ACT-0039-V1 | NONE |
| ACT-0046 | khung kim loại luyện nét | SAP-ACT-0046-V1 | NONE |
| ACT-0055 | quan sát các bộ phận của cây | SAP-ACT-0055-V1 | AGE_BASELINE |
| ACT-0058 | mô hình vòng tuần hoàn nước | SAP-ACT-0058-V1 | NONE |
| ACT-0061 | nhân với trò chơi tem | SAP-ACT-0061-V1 | NONE |
| ACT-0067 | phân tích từ loại bằng ký hiệu | SAP-ACT-0067-V1 | NONE |
| ACT-0074 | lập kế hoạch công việc tuần | SAP-ACT-0074-V1 | NONE |
| ACT-0085 | khảo sát và mô tả dữ liệu | SAP-ACT-0085-V1 | AGE_BASELINE |
| ACT-0087 | xây khóa phân loại | SAP-ACT-0087-V1 | NONE |
| ACT-0091 | mô hình pha mặt trăng | SAP-ACT-0091-V1 | NONE |
| ACT-0097 | viết lập luận dựa trên bằng chứng | SAP-ACT-0097-V1 | NONE |
| ACT-0099 | dự án nghiên cứu độc lập | SAP-ACT-0099-V1 | NONE |

Alias coverage is supplemental with its own `ALIAS` expectation. Do not relabel an alias result
as `EXACT`. The existing catalog contains 100 profiles and shared concept families, so the exact
target need not be the only profile matched. Report other matches, including non-pilot activities,
without changing labels until a unique result appears. Base V2 matching uses `include_expansion=False`.

## 3. Six primary families: concrete construction and expectations

IDs use `feat018-p2-t4-<activity-id-lowercase>-<family>`. Claim/conflict IDs must meet the existing
lowercase reference grammar and be unique within each Raw record. Source/session/correlation refs
are explicit synthetic fixture values. Use confidence `0.90` except where the family specifies
another value; `0.90` is test data, not a production policy threshold.
Primary V1 confirmations use `meaning_version=1`; primary V2 confirmations use `meaning_version=2`.
Other version values belong to supplemental versioning cases, each with its own explicit expectation.

| Family | Construction | Expected observation and limits |
|---|---|---|
| EXACT | One Vision entity labelled with the exact phrase in section 2; narration `NOT_SUPPLIED`. Confirm its claim explicitly with Gate A V1, no correction. | B1 validates/selects the claim. B2 retains source hash, original label and claim ID. B3 should observe EXACT for the target V1 profile and PERSONALIZED_EXACT for a valid V2 projection; separately record all other matches and identity differences. Any deviation remains a finding. |
| AMBIGUOUS | Two Vision entities, one for the target and one for the next pilot in section 2 (last wraps to first), with distinct IDs, plus `UNRESOLVED_AMBIGUITY` referencing both. In B2 use V1, `confirmed_claim_ids=[target_claim_id, partner_claim_id]`, `primary_anchor_id=target_claim_id`, no correction. | B1 preserves both claims and explicit ambiguity. B2 must retain the target as primary and the partner as secondary; record tags merged from all confirmed claims. B3 V2 may match both labels as exact: observe both without claiming unique selection or model resolution of ambiguity. Keep Raw/confirmation; unsupported decision provenance remains UNRESOLVED. |
| NO_MATCH | One Vision entity with reserved synthetic label `zzfixture-no-reviewed-match-018`, no narration, and explicit no-correction gate confirmation for B2/B3. | Assert empty tags on the actual B2 anchor output; Raw has no semantic-tags field. Check that unmodified projection against all base 100-profile vocabulary/matchers, including aliases, negatives and concept routes. No non-fallback match may exist. If the recipe fails its precondition, report invalid input and revise the specification through review rather than searching for a passing string. No-match is report vocabulary only; fallback is observed separately. |
| CONFLICT | Target Vision claim plus an ASR claim containing the next pilot's exact phrase. Set `narration_status=ASR_SUCCEEDED`, ASR source `ASR`, and inject `SOURCE_DISAGREEMENT` referencing those two IDs. Explicitly confirm the target Vision claim as primary in B2; bind session narration and the B3 narration argument as described below. | B1 asserts the two references are distinct and from different modalities. This is an explicitly supplied synthetic disagreement, not detected contradiction. B2/B3 cannot claim the sources agree merely because narration is nonempty; record missing propagation or unsupported agreement as UNRESOLVED. |
| LOW | The EXACT Raw recipe with Vision confidence `0.05`; use the same explicit no-correction confirmation. | Check numeric preservation through Raw, selected anchor and the corresponding `SceneConceptV2` in B3. Observe matcher `concept_match_confidence` separately: its fallback default 0.5 is a finding about a derived score, not a pass/fail substitute for source-confidence preservation. No invented cutoff or single-claim LOW_CONFIDENCE conflict. |
| ADULT_CORRECTION | Preserve an EXACT Raw record; add a V2 confirmation with `confirmed_claim_ids=[target_claim_id]`, adult-authored synthetic label, actor `demo:local` and `meaning_version=2`. The workflow payload must include `primary_anchor_id=null`. | B2 should project the adult assertion as primary and the retained target claim as a secondary anchor; B3 V2 may still match the target via that secondary label. Compare Raw digests before/after and retain confirmation. Record confidence 1.0, role/meaning/anchor-version differences or unregistered provenance names as review items, not source-model certainty. |

The deterministic partner rule supplies two different candidate labels; it does not claim every pair
shares a concept family or is logically contradictory. Explicit ambiguity/disagreement is part of the
fixture input. These cases verify representation and provenance, not automatic semantic judgment.

The conflict's ASR text is one declared synthetic fixture string. Bind that same text and its UTF-8
digest to the Raw ASR claim, a session fixture value `narration_result={"transcript": <same text>}`,
and the explicit `narration_text` argument if `confirmed_topic_scene` is called in B3. This dict is
session fixture data, not a new ASR wire contract. `confirm_gate_a` does not read `narration_result`;
checking it is fixture consistency only. Later P1 operations read its `transcript` key, but those
operations are not executed here. Assert text equality and non-empty B3 input. A Raw ASR claim alone
does not supply B3 narration. Empty/absent-text variants are supplemental; retain explicit synthetic
source/correlation identities and use the instrumentation rules below for any call-count claims.

In no-match cases consume the actual B2 anchor and its derived scene without overwriting tags,
labels or concepts. Empty tags are an output precondition to check, not an input extra field or
permission to repair a returned anchor. Any unexpected derived tags or matcher hit is an input/
behavior finding; no 100-profile exclusion claim follows until these checks complete.

The same no-match observation may be reused, but every activity has its own case ID and target
profile observation. Record all base-catalog fallbacks independently: the three golden fallback rows
are ACT-0026, ACT-0055 and ACT-0085, not necessarily the full set of fallbacks among all 100 profiles.

Proposed adult label recipe: `nhãn người lớn thử nghiệm <activity-id>`. It represents adult input,
not catalog vocabulary or an additional model claim. Do not assign confidence to the adult input
in the fixture to conceal the service's observed confidence convention.

## 4. Supplemental contract cases

These have separate IDs and counts and do not replace or increase the 120 primary combinations:

- Missing Vision confidence at the upstream V2-to-Raw mapper must reject without defaulting;
  `test_rejects_missing_v2_confidence_without_defaulting` is an existing regression to reuse.
- Nullable ASR confidence remains `None`; Raw uncertainty `NOT_PROVIDED` requires a null value,
  whereas `UPSTREAM_PROVIDED` requires an explicit value. These are separate quantities.
- A bare `RawAmbiguousObservationV1` has note/ID/source, no confidence or selectable label.
  Verify its B1 representation and that `claims_from_raw` does not invent an entity from it.
- Repeat the conflict with `TEXT_TYPED` and `TEXT_SUPPLIED`. Explicitly test source/status
  consistency because reference-valid Raw records alone do not enforce all modality semantics.
- Duplicate/dangling conflict refs, source/correlation mismatch, unknown selected claims, and stale
  confirmation/session versions must produce their existing typed failures or a documented gap.
- V1 correction, successive meaning versions and uncorrected V2 confirmation
  compare the session record with the anchor projection; none may be summarized as loss of all
  session attribution merely because the projection differs.
- A command actor other than `demo:local` is a negative test expecting `DEMO_ACTOR_INVALID`, not
  a successful confirmation with a different role. V2 without a nonblank adult label is likewise a
  negative test of the current service, even if the schema accepts claim IDs alone.
- Ambiguity with only the target confirmed and adult V2 correction with `confirmed_claim_ids=[]`
  are supplemental comparisons, each with explicit `primary_anchor_id` (target or null respectively).
  Their changed secondary-anchor/matcher outputs do not redefine the primary recipes.
- Reviewed aliases are distinct supplemental cases; family-related matches are observed without
  asserting uniqueness or treating them as P1 eligibility.

## 4A. B2 fixture preconditions and dependency instrumentation

Use test-created `InMemorySessionRepository`, `InMemoryIdempotencyStore`, `InMemoryArtifactStore`
and `InMemoryDemoWorkflowStore` with `EphemeralSessionService`. Create a fresh synthetic session
using a valid `CREATE_SESSION` command (fresh UUIDv4 session ID, create actor `demo:local`, expected
version 0, payload exactly `{"operation":"CREATE_SESSION"}`, and fixed test clock). Then call
`advance` with the returned expected version, `allowed_states=("CREATED",)`,
`next_state="GATE_A_PENDING"`, and workflow updates containing validated fixture `source_image_ref`
and `raw_understanding` dumps with matching source identity/hash. Add the declared narration dict
for a conflict case. Read back the
seeded state/version before confirmation; use that version in both the workflow command and
confirmation. Bind session ID, request/idempotency IDs and meaning version explicitly. All positive
confirmation commands use actor `demo:local`, payload keys exactly `operation`, `user_initiated`,
`confirmation`, `primary_anchor_id`, with `operation="CONFIRM_GATE_A"` and `user_initiated=true`.
The service overwrites confirmation actor with the command actor. Distinct case/session/assertion
IDs identify synthetic adult actions; varying the accepted command actor is not supported here.

This is a test precondition, not observed image admission or a completed understanding/provider
request. Do not invoke admission/understanding, `create_app`, live composition roots or a provider
to establish it. Missing optional imports remain an execution limitation, not permission to alter
runtime imports or fake a successful boundary result.

Primary B2 construction uses `auto_rig_service=None`, `scene_localizer=None`, `activity_ranker=None`,
`pixi_show_planner=None`, all crop/asset/preview/motion issuers `None`, and no renderer capability
issuer. Supply a test-owned counting sentinel for the required `p1_compiler` dependency; any compile
attempt increments its counter before raising, and the test asserts the final count equals zero.
The compiler sentinel is not a provider and cannot establish a global provider-call count.

Record disabled dependencies as `NOT_INSTALLED`, not a measured zero. Provider/model execution is
excluded by this declared test construction; do not claim instrumentation on a boundary that was
not installed. For any installed counting fake, increment before returning/raising and assert its
counter after the operation, even when the application reports success.

One supplemental instrumentation case uses a test-only `CountingAutoRigStub` at the actual
`start_gate_a_preparation` method: increment then raise a controlled local test exception. The
service catches that exception, so the test must observe one attempted stub invocation, not infer
zero from success or from the absence of an outward error. The stub makes no provider call. This
checks reporting of a swallowed call; it does not test real AutoRig or grant runtime/model execution.

## 5. Diagnostic result design

Report-only fields distinguish intended requirements from actual observations:

- `execution_status`: `NOT_RUN`, `COMPLETE` or `ERROR`.
- `requirement_status`: `SATISFIED`, `EXPECTED_BLOCKED`, `UNRESOLVED` or `FAILED`.
- `p2_diagnostic`: optional descriptive code such as `NO_REVIEWED_VOCABULARY_MATCH`, not a runtime
  error code, schema field or assertion that the product has a P2 no-match endpoint.
- `p1_matches`: observed profile IDs/versions/modes and relevant digests; `p1_fallback_observed`
  records fallback separately. No pedagogical fit, eligibility or Gate-B result is produced.
- `boundary_findings`: ref/modality/actor/version/correction issues and the corresponding evidence
  IDs/hashes, retaining the full synthetic Raw/confirmation inputs in the declared test fixture.

Do not count an accepted synthetic input as a satisfied downstream preservation requirement.
Do not convert a known characterization gap to EXPECTED_BLOCKED or mark P2-T4 complete merely
because the tests accurately detect it. Missing optional dependencies yield an honest execution
limitation, not a successful B2 observation. Apply section 4A: counter claims require installed
fakes and explicit post-operation assertions; disabled dependencies are `NOT_INSTALLED` and the
mapper port alone cannot establish a provider-call count.

## 6. Recommended owner choices

Propose one bounded diagnostics scope: B1+B2 with B3 observation, exact phrases for the primary
matrix, aliases/unknown-confidence as supplemental cases, shared validated no-match recipe,
preservation-only low confidence, and an explicit gap list without runtime/schema fixes. There is
no need to adopt a low-confidence production threshold or create a P2 candidate API for this slice.

The two sanitized draft documents were published at the user's request for Cloud review. No raw
review attachment or general working-research publication is proposed. No owner adoption or test
implementation approval is implied by relaying a review or by writing these recommendations.

## 7. Re-review request

Review the revised plan and this specification against current source at the review commit.
Check whether recipe expectations are testable without changing product code, whether every
profile/version/ref is attributable, and whether gaps/completion are reported honestly. Identify
any remaining input ambiguity and propose the smallest correction with file/line evidence.

Only static review is requested: no edits, app/test/model/provider execution, approval adoption or
runtime assurance. The Gate A/projection subagent verification was coordinator-directed read-only
analysis; it was not external review of this revised specification and did not run the recipes.
