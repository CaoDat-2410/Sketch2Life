# FEAT-018 P2-T4 — Pilot Mapping Diagnostics Plan

- Status: `APPROVED — DIAGNOSTIC IMPLEMENTATION ONLY`
- Revision: 3, 2026-10-20; response to the owner-relayed Claude Cloud delta-review of `fc1f987`.
- Owner: Person 2.
- Branch: `feature/feat018-p2t4-mapping-diagnostics`.
- Parent: P2-T3 status commit `fd474b12bb50a603e67fce5c25f889a95e968734`.

Person 2 approved revision 3 at source commit `b39a9f2f56509b0543184876eb538fc9faf0e1aa` on
2026-10-20. The original source digests, exact issuance, allowed files and exclusions are recorded
in `approvals/TASK_APPROVAL.md`. The 2026-10-21 acceptance rebase supersedes only the original
unresolved-requirements closure clause for diagnostic-deliverable acceptance; it does not change
implementation scope or any observed requirement status.

## Outcome and limits

Prepare an offline diagnostic matrix for the 20 golden pilot activity/version pairs in
`ACTIVITY_PILOT_MATRIX.md`. Each has six primary cases: exact, ambiguous, no-match, conflicting
image/narration, low numeric confidence, and adult correction: 120 uniquely identified rows.
The [input specification](P2_T4_MAPPING_INPUT_REVIEW_DRAFT_20261020.md) defines the proposed inputs.

The runtime has a P2 Raw proposal and a Gate-A-confirmed anchor handoff; no separate P2-owned
activity-candidate/no-match API was established by this inspection. This slice therefore proposes
fixtures, tests and a diagnostic report using existing contracts, with no new runtime envelope.
Report vocabulary is not a new public contract or an eligibility decision.

The 2026-10-21 owner amendment permits acceptance of the diagnostic deliverable while the product
requirements remain unresolved. Passing tests that accurately reproduce a defect do not mean the
product requirement is satisfied. Task 4 closure still requires the amendment's four final gates.

## Source basis and review response

- `PERSON_2_AI.md` specifies the six cases and P2/P1 ownership. `ACTIVITY_PILOT_MATRIX.md` supplies
  the activity v2 identity set, not executable English matching labels.
- `P2_OFFLINE_FIRST_PLAN.md` O3/O4 and C0 are proposed design requirements, not adopted authority
  for unapproved work. Later approvals of P2-T2, narration, T2 matching and subject recovery remain
  applicable to their own scopes; their existence does not approve this matrix or every C0 clause.
- `CONTRACT_FREEZE.md`, `ENGINE_REFINEMENT_PLAN.md`, `approvals/TASK_APPROVAL.md` and the current
  contract/service sources define the existing handoff. Person 2's dedicated approval for this
  diagnostic implementation slice and the later acceptance rebase are recorded in the approval file.
- `data/activity-catalog/golden/v1/semantic-anchor-profiles.v1.json` contains reviewed Vietnamese
  phrases and 100 legacy profiles. Profile versions and golden activity versions differ; retain
  both identities rather than rewriting catalog versions.
- The 2026-09-22 T2 matching work supplies existing catalog/matcher behavior and selected tests.
  FEAT-003/027 payload-mapping diagnostics and FEAT-003 `p2_t4_fusion*` are different deliverables.
- `docs/context/SOURCE_REGISTER.md` treats reference inputs as context, not implementation grants.

The Cloud review is external reviewer-reported static analysis. Coordinator source inspection
confirmed the key design gaps below; a Codex subagent separately checked the Gate A/projection
claims. Neither activity is a runtime test or acceptance verdict for this revision.

| Review topic | Current response |
|---|---|
| No established P2 candidate/no-match operation | Report-only diagnostic classification; preserve Raw proposal and gate evidence. Do not add a contract. |
| English seeds are not reviewed matching labels | Use the Vietnamese `exact_phrases_vi` values listed in the input specification; record the seed as context only. |
| Profile v1 versus activity v2 | Bind catalog/profile ID, profile version, source digest, effective activity/version, and observed variant ID separately. |
| Ambiguous-region versus competing claims | Two entity claims plus `UNRESOLVED_AMBIGUITY`; V1 confirms both with target primary. Bare region and target-only confirmation are supplemental. |
| Unknown Vision confidence is invalid in Raw | Test V2-null rejection separately; numeric low confidence tests preservation, without inventing a threshold. |
| Conflict after Gate A | Keep Raw plus confirmation plus anchor; record unsupported conflict/decision propagation as `UNRESOLVED`. |
| Adult correction provenance | Primary V2 recipe retains the target claim and has `primary_anchor_id=null`; empty-list V2 and V1 correction are supplemental. Preserve session/confirmation facts. |
| Working brief publication policy | The two sanitized draft documents were pushed for Cloud review at the user's request; this is not completed evidence publication or an exception for unrelated research. |

Two qualifications to the review are retained. `_FUSION_ALIASES` does include plant/flower-related
terms, so it is too broad to claim that it covers none of the pilot vocabulary. Explicit fixture
conflicts are still needed to test all pilots deterministically. Also, adult confidence `1.0` is an
observed implementation convention and a policy/calibration question, not a proven violation of an
adopted C0 threshold: C0 in the offline-first plan is still a proposal.

## Three observation boundaries

| Boundary | Exercise | Evidence and limits |
|---|---|---|
| B1: P2 proposal | Validate `RawUnderstandingSuccessV1`, refs, narration state and `claims_from_raw`; exercise the existing mapper for applicable supplemental cases. | Raw/proposal and claim identities remain distinct from confirmed anchors. Fixture-injected conflicts do not prove automatic contradiction detection. |
| B2: Gate A handoff | Call existing `SupervisedFlowService.confirm_gate_a` with explicit V1/V2 confirmation, a fresh synthetic in-memory session and injected dependencies. | Retain original Raw, confirmation/actor/meaning and session versions, returned anchor, and relevant post-confirmation session facts. No provider/backend server or real state. |
| B3: P1 matcher observation | Use existing per-profile `match` and, when valid scene input exists, `match_scene` without changing either implementation. | Observe match modes/fallbacks across the fixed base 100 profiles (`include_expansion=False`). No eligibility resolver, age fit, P1 compiler, Gate B or activity selection. |

`ConfirmedSceneUnderstandingV2` is a downstream projection for B3, not a replacement P2 contract.
If `confirmed_topic_scene` is exercised, its inferred modality/agreement and absent-audio markers
are implementation observations, not proof of source audio or genuine agreement. Retain B1/B2
evidence and record any disagreement. Never invent scene confidence or audio provenance to run B3.

Input specification section 4A binds B2 setup to a test-created ephemeral session/workflow store,
`create` followed by explicit `advance` to `GATE_A_PENDING`, fixture source/Raw dumps, and exact
pre-confirmation version. This establishes fixture state only, not understanding/admission evidence.

The 9–12 rows stay in the historical golden catalog diagnostics. This does not enable unsupported
ages in the current product flow, change the supported-age boundary, or start sessions for those ages.

## Known gaps requiring observation, not an automatic repair

- V1 correction preserves the original label and the full confirmation in session state, but the
  corrected anchor still carries Vision claim IDs/confidence without a separate adult assertion.
- V2 adult-subject confirmation adds an assertion ID and does not fabricate Vision claim IDs;
  it assigns confidence `1.0` and a provenance contract-name string that must be checked against
  registered contracts. Do not infer that a string alone defines a contract.
- Both branches project `PROJECT_OWNER` into the anchor role and default anchor-set version to 1;
  confirmation keeps the actual actor, and session-derived anchor IDs change. Different meaning,
  session and anchor versions must not be conflated. Positive calls in this local-demo service
  accept only `demo:local`; other command actors are rejected. This audit does not demonstrate an
  authenticated non-owner actor being silently assigned an owner role.
- Anchor-to-scene projection can infer agreement from non-empty narration without carrying Raw
  conflicts. An adult's explicit claim selection must not be reported as automatic source agreement.
- Matcher V2 `_phrase_match` uses escaped `\\s`/`\\w` patterns rather than whitespace/word classes.
  Cloud review reports a pure-regex reproduction; coordinator source inspection confirms the
  double-escaped expressions. Boundary/spacing cross-matches must be recorded as observed matcher
  behavior, not corrected by changing fixtures or product code in this slice. Runtime impact on
  the matrix has since been observed in the Modal run: the supplemental word-boundary and
  whitespace matcher expectations were recorded as mismatches. See the evidence note for row-level
  findings. No runtime repair is authorized.

At plan approval, these were static hypotheses pending execution. The Modal run has since exercised
the approved boundaries and recorded observations in the metrics report. No runtime fix to Gate A,
mapper, resolver, catalog or schema is authorized by this plan. If diagnostic results expose a
required repair, propose the exact repair and approval separately; product gaps remain open.

## Expected outcomes and completion rules

Each row records `case_id`, activity v2 identity, boundary, fixture digest, source/claim references,
profile identity/version/digest when applicable, intended behavior, observed behavior, and a test
reference. Report-only `requirement_status` is one of `SATISFIED`, `EXPECTED_BLOCKED`, `UNRESOLVED`
or `FAILED`; execution completion/error is recorded separately.

`NO_REVIEWED_VOCABULARY_MATCH` is a diagnostic report label. Record P1 fallback observations and
match modes separately; fallback cannot satisfy an exact/alias/concept-match expectation. Validate
the common no-match recipe against all 100 base profiles, not only the golden 20.

1. The primary matrix is exactly 20 activities × six families with no duplicates or missing rows.
   Supplemental null-confidence, uncertainty, alias, invalid-reference and V1-correction cases have
   their own IDs/counts and do not inflate the 120-row coverage figure.
2. Source labels, all raw observations, modality references and original fixture digests survive
   every applicable boundary. A normal adult selection can be recorded as such; no automatic
   conflict-resolution or model-certainty claim follows from it.
3. Low confidence `0.05` is a fixture value, not an adopted cutoff. Check preservation through Raw,
   anchor and the relevant scene concept. Observe matcher score/default 0.5 separately; it is not
   the source-confidence preservation verdict. Use `NOT_PROVIDED` only for Raw uncertainty status,
   not for a required numeric Vision claim field. No blocking threshold is asserted.
4. Tests independently validate input integrity, application observations and report dispositions.
   No unexplained skips/xfails, hardcoded all-pass summary, or missing B2/B3 evidence can close a row.
5. Bind construction and call instrumentation as input section 4A. Optional live/media dependencies
   are disabled and reported `NOT_INSTALLED`, not counted as measured zeros. Assert the installed
   compiler sentinel's zero count. A supplemental counting AutoRig stub must report its observed
   invocation even though the service catches its exception. No real provider is constructed.
6. Evidence contains sanitized IDs, hashes, codes, counts and observations. Synthetic label/text
   lives only in declared fixtures; raw session dumps, real transcripts, media or provider output
   do not become published evidence.
7. Under `W2_FEAT018_P2_T4_DIAGNOSTIC_ACCEPTANCE_REBASE_01`, diagnostic-deliverable acceptance covers
   the approved 120 primary cases, 43 separately counted supplemental cases, B1/B2/B3 within scope,
   the metrics report and evidence. The 60 primary and 5 supplemental `UNRESOLVED` results remain
   product gaps; they are not SATISFIED and are recorded as separate, unassigned follow-ups. Task 4
   closes only after: the provenance contract-name is checked or followed up; plan, evidence note,
   status and report are consistent with observed findings and review limits; final gates have valid
   results (mypy `INTERNAL ERROR` is not PASS); and an independent final review covers the handoff.

## Exact proposed file scope after approval

New implementation/fixture files, names deliberately qualified as FEAT-018:

- `tests/fixtures/feat018-p2-t4-mapping/manifest.v1.json`.
- `backend/tests/unit/test_feat018_p2_t4_mapping_diagnostics.py`.
- `backend/tests/contract/test_feat018_p2_t4_manifest_contract.py`.

Feature records (relative to this feature), created or updated only under the corresponding scope:

- `evidence/notes/P2_T4_MAPPING_DIAGNOSTICS_20261020.md`.
- `evidence/metrics/P2_T4_MAPPING_DIAGNOSTICS_20261020.json`.
- The two draft plan documents, `CONTEXT.md`, `DECISIONS.md`, `status/STATUS.md`, and
  `evidence/README.md`; `approvals/TASK_APPROVAL.md` records only actual owner approval.

Reuse contract constructors and fixture patterns from `test_raw_understanding.py`, existing
in-memory service fixtures, catalog loaders and matchers. Do not import private HTTP application
setup or a composition root that eagerly imports optional live/media libraries just for B2.

No change to `raw_understanding.py`, `gate_a.py`, `p1_experience.py`, `supervised_flow.py`,
`semantic_activity_resolver.py`, `semantic_personalization_v2.py`, mapper/scene/catalog runtime,
catalog JSON, FEAT-003 fusion, P4 fixtures, mobile, provider code or shared governance tools.

## Owner-approved scope and implementation checkpoint — 2026-10-20

Person 2 approved B1/B2/B3 with B3 as matcher observation only, 120 primary cases, separately
counted supplemental cases, and report labels restricted to diagnostics. The approval is recorded
verbatim in `approvals/TASK_APPROVAL.md`. It authorizes the exact files listed above, focused offline
checks, evidence creation, and implementation review. It does not authorize runtime/schema/catalog
changes or Lightning/model calls.

The initial local preflight report recorded 120 primary rows: B1 completed for all 120; B2 and B3
were NOT_RUN for all 120 because the active test environment lacked the required project dependency
`Pillow>=11,<13` (import module `PIL`). The dependency is required by the backend project, not an
optional Gate A/live dependency. At that point all 120 primary requirements remained UNRESOLVED. Of
43 supplemental rows, 34 executed and 9 Gate-A cases were NOT_RUN for the same environment
prerequisite. Twelve supplemental requirements remained UNRESOLVED in that report. The report kept
the 120 primary and 43 supplemental counts separate and recorded `full_p2_t4_acceptance=OPEN`.

Evidence and the offline check results are in
`evidence/notes/P2_T4_MAPPING_DIAGNOSTICS_20261020.md` and
`evidence/metrics/P2_T4_MAPPING_DIAGNOSTICS_20261020.json`. The initial result was partial, not Task 4
completion. B2/B3 evidence has since been added by the follow-up below. The 2026-10-21 amendment
allows diagnostic-deliverable acceptance without changing unresolved row statuses; separate
follow-ups and the required final gates remain. No runtime fix, provider/model call, or contract was
added.

## Follow-up execution evidence — 2026-10-20

The initial status above records the local preflight before Pillow was available. A later owner-run
Modal Notebook focused check at checkout `5c79741f9e3806626c1dc5c586fe409b2e9370a1` completed with
368 passed and one Pydantic deprecation warning. The regenerated metrics report records B1/B2/B3
COMPLETE for all 120 primary cases and execution COMPLETE for all 43 supplemental cases. The report
tuple and remaining unresolved requirements are recorded in the feature evidence note. This update
does not change the approved implementation scope. Person 2's 2026-10-21 amendment superseded only
the original unresolved-requirements closure clause for diagnostic-deliverable acceptance; it did
not change any row status or assign follow-ups to Task 5. Task 4 remains open pending the four final
gates, including valid final checks and independent review of the final handoff.
