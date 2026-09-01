# P2-T3 Phase B approval request — B0 dossier

- Evidence ID: EV-003-T3-PLAN-04
- Date: 2026-09-01 (drafted); revised same day across three correction rounds (see "Round-2
  correction", "Round-3 correction" below); all ten open owner decisions recorded the same day,
  see "Round-4 — owner decisions recorded" below; two further documentation defects found by a
  final read-only red-team review fixed the same day, see "Round-5 correction" below
- Owner: Person 2
- Status: **APPROVED — bounded Phase B B1–B5 scope, 2026-09-01.** All ten owner decisions
  (D-1 through D-6, D-8 through D-11; D-7 resolved by construction) are recorded with exact values,
  including the closed `VisionProfileIdV2` membership and `VisionProfileV2.compute_profile` enum.
  This dossier remains the decision rationale, not the approval record itself. The authoritative
  approval is `../../approvals/TASK_APPROVAL.md`, updated only after the owner's explicit instruction.
- Governing plan: `../../plan/P2_T3_VISION_RESEARCH_PLAN.md`, Phase B work packages V1–V5.
- Supersedes for Phase B planning: the B0 section of `P2_T3_PHASE_B_PREPARATION.md`
  (`EV-003-T3-PLAN-03`), which remains valid as the earlier planning context.
- Produced by: documentation-only work. No dependency was installed, no model or weight was
  downloaded, no GPU/cloud/provider was contacted, no runtime configuration was created, and no
  Python source, test, fixture, dependency file, or `.gitignore` entry was changed.

## What this document is

The B0 deliverable defined by `P2_T3_PHASE_B_PREPARATION.md:49-54`: a candidate-profile dossier
and a precise, additive contract amendment, written **before** any implementation, so the project
owner can approve or reject a bounded Phase B with full sight of its contract impact.

It resolves the accepted findings of the Round-1 red-team review of the Phase B package. Every
resolution below is either (a) a **convention** this dossier fixes, or (b) an explicit
**owner decision** listed in "Owner decisions register". Nothing is left implied.

## Phase A completion gate — CLOSED

`P2_T3_PHASE_B_PREPARATION.md:44-45` made "Phase A completion" a precondition for introducing a
real adapter. That gate is now closed.

- Record: `P2_T3_PHASE_A_IMPLEMENTATION.md` (`EV-003-T3-01`), including its
  "Correction — 2026-09-01" section.
- Delivered: the frozen provider-neutral contract, the interface-only `VisionUnderstandingPort`,
  the replaceable `ObservableContentPolicyV1` port, the deterministic
  `DeterministicFixtureVisionAdapter` with real source-image read/hash ingress verification, the
  synthetic-only `LexicalRegressionContentPolicy` over `vision-policy-match-view-v2`, and the
  synthetic fixture manifest.
- Verified on 2026-09-01, immediately before this dossier was written:

  | Command | Result |
  |---|---|
  | `pytest tests/unit/test_vision_phase_a_contracts.py tests/unit/test_vision_content_policy.py tests/unit/test_vision_phase_a_adapter.py tests/unit/test_vision_fixture_manifest.py` | **172 passed** (99 + 36 + 36 + 1) |
  | `pytest` (full backend) | **310 passed** |

  Earlier notes recorded 170/308; those figures predated the final absolute-path correction and
  are corrected wherever they appeared.

Closing this gate does not authorize Phase B. The two remaining Phase B blockers recorded at
`../../plan/P2_T3_VISION_RESEARCH_PLAN.md:921-930` — the semantic-safety mechanism and the
runtime/profile evidence decisions — are addressed by this dossier but require owner decisions.

## Round-1 review resolution

| # | Finding | Convention fixed by this dossier | How a future reviewer proves it |
|---|---|---|---|
| 1 | `known_policy_trigger_rate` is vacuous against a real model because the Phase A lexicon is six fictitious markers (`vision_lexical_policy.py:67-77`) | Against the synthetic fixture lexicon the metric is reported as **`NOT_APPLICABLE`**, never `0` and never omitted. Lexical-policy unit tests remain **wiring evidence only** — they prove the layer executes and blocks, never that a model is safe. A real-term lexicon requires a separate plan, owner approval, a `lexicon_version` bump, and its own review | B3/B4 reports contain the literal token `NOT_APPLICABLE` for this metric with the fixture lexicon named; no report contains a numeric trigger rate under `vision-prohibited-lexicon-fixture-v1` |
| 2 | B2 required a real model load with no execution location, and the only documented GPU is 8 GB (`P2_T2_PHASE_B_ROUND1_ASR_REPORT.md:126`) | **Lightning L4 (24 GB) is proposed as the development preflight location only** — see "Execution location". Local-GPU feasibility for the baseline at any precision is **unknown** and must be recorded at B1, not assumed | B1 evidence names the execution location and records measured VRAM headroom or an explicit `NOT_MEASURED` reason |
| 3 | Post-retry failures unconstructible: `VISION_SCHEMA_INVALID` and `PROHIBITED_CLAIM_DETECTED` at `attempt_number=2` are rejected by the V1 validator | The **V2 terminal-outcome matrix** (see below) admits `attempt_number ∈ {1, 2}` for both rows, plus every other post-retry terminal state (timeout-after-retry, permanent-failure-after-retry), each with a stated rationale. `VISION_TIMEOUT` stays non-retryable; `INPUT_NOT_VALIDATED` stays attempt `0`; `VISION_MODEL_UNAVAILABLE` stays attempt `1` only; the cap stays `2` | V2 contract tests construct every row at its permitted attempt number(s) and reject it at every other one; V1 remains byte-identical and still rejects attempt `2` everywhere |
| 4 | Adding nullable model fields to `VisionProfileV1` would silently change `vision_profile_config_hash` of the unchanged fake profile | **No field is added to any V1 model, and no member is added to `VisionProfileId`.** Real provenance lives on new, fully disjoint `VisionProfileIdV2` / `VisionProfileV2` / `VisionUnderstandingResultV2` types. The fake profile's `vision_profile_config_hash` is byte-identical forever | A B1 test contains a **committed golden-constant** digest for the fake profile and catalog, computed once against the current V1 implementation; see "V1 digest regression proof" |
| 5 | `profile_catalog_hash` changes on every result once a Qwen candidate joins the catalog | One canonical static catalog **per contract version, and per version only**: `vision_profile_catalog()` (V1, fake-only, unchanged) and `vision_profile_catalog_v2()` (V2, **real candidates only — never a fake**). V1 results keep their recorded catalog hash; V2 results carry the V2 snapshot hash. Results are never compared across catalog hashes | Every benchmark row records its `profile_catalog_hash`; the report refuses to aggregate rows whose hashes differ |
| 6 | Single-value literals must widen, and nothing forbade widening the one that must not | See "Profile contract separation": `VisionProfileId` gains no member at all; `timeout_retry_policy` stays `Literal["NEVER_RETRY"]` on both V1 and the new `VisionProfileV2`; `compute_profile` and `VisionProfileIdV2` membership are explicitly **decision-gated**, not silently assumed fixed | A V2 contract test asserts `NEVER_RETRY` is the only constructible value; `VisionProfileId`'s member count is asserted to stay `1` |
| 7 | Adapter catalog injection could diverge from the catalog used at request validation; a resolve miss escaped as an untyped `ValueError` | Request validation and adapter resolution use the **same** canonical catalog function for their contract version, and `VisionUnderstandingRequestV2`/`VisionProfileIdV2` can only ever resolve against `vision_profile_catalog_v2()` — never against V1's catalog or vice versa. Divergent injection is forbidden for the real V2 adapter (test-only injection stays permitted for the fake). A resolve miss maps to the new typed token `PROFILE_NOT_RESOLVABLE` under `INPUT_NOT_VALIDATED`, attempt `0` | A V2 test injects an intentionally incomplete `VisionProfileCatalogV2` and asserts a typed failure, never a raised exception |
| 8 | The lossless-repair rule was not frozen against Phase B pressure | **Frozen.** Lossless Markdown-fence unwrap of an already-complete JSON object is the only permitted repair. Low schema validity is a **measurement result**, not permission to add extraction/salvage | B3 reports the schema-valid rate as a finding; no B1–B5 diff adds substring/brace-scanning extraction to `_parse_raw_output` |
| 9 | No decoding-determinism requirement | Deterministic decoding fields become **profile fields** covered by `vision_profile_config_hash`; a repeat run is mandatory at B4 | Two B4 runs at the same profile/config hash reproduce quality metrics exactly, as P2-T2 Round 1 did (`../../CONTEXT.md`, repeat-run record) |
| 10 | Raw-output handling was under-specified, and is the true semantic-safety exposure | Ephemeral, gitignored, owner-only review; only safe counts and typed identifiers persist — see "Raw-output handling" | No evidence file, log, or commit contains model-produced free text; `validate_repository_security.py` passes on every Phase B commit |
| 11 | `.gitignore` had no vision weights/cache/env/payload entries | Exact future entries listed in "Repository hygiene"; none are added by this documentation-only step | The B1 diff adds exactly those entries before any download or fixture creation |
| 12 | Result-contract versioning undecided; `extra="forbid"` makes added fields consumer-breaking | **V2 is a new, separately named contract.** V1 consumers keep validating V1 payloads unchanged; a V2 payload is never presented as V1 | A V1 round-trip test still passes untouched after V2 exists |
| 13 | Model provenance on the failure branch undefined | Defined in "Provenance applicability": `model_provenance` is **required** on every model-reached outcome — `SUCCEEDED`, `PROHIBITED_CLAIM_DETECTED`, `VISION_SCHEMA_INVALID`, `VISION_MODEL_UNAVAILABLE`, `VISION_PROVIDER_FAILURE`, `VISION_TIMEOUT` — and **forbidden** only on `INPUT_NOT_VALIDATED`. (This row originally named only two of those six outcomes; a later drafting pass completed the table without this summary row being updated to match. Corrected here so the summary agrees with the section it cites, which has been the authoritative rule throughout.) | V2 tests assert provenance presence on all six required rows and rejection on `INPUT_NOT_VALIDATED` |
| 14 | Typed-failure preflight evidence had no anti-fabrication guard | Typed-failure paths are proven by **injected fakes**, following the ASR warmup-failure precedent; a hand-written failure record is never evidence | B2 evidence cites the injected-fake test module, not a narrative |
| 15 | B4 omitted two of five collections and the denominator rule | All five collections get a metric or an explicit `NOT_MEASURED` reason; every rate states its denominator — see "Benchmark design" | The B4 report has one row per collection and one denominator per rate |
| 16 | Ground-truth authorship/timing unspecified | Ground truth and matching rule are authored **and SHA-256-hashed before any model output is seen**; both hashes are recorded in the manifest and the report | The GT hash in the B4 report matches the hash recorded at manifest creation, dated before the first run |
| 17 | Timeout enforcement mechanics unspecified for a synchronous call | B1 must specify in-band deadline enforcement, or a killable subprocess; abandonment is forbidden — see "Timeout enforcement" | B1 evidence states the mechanism and shows a timed-out call returning `VISION_TIMEOUT` with no residual VRAM held |
| 18 | The preparation note's own gate 3 was stale | Closed above and marked in the preparation note | `P2_T3_PHASE_B_PREPARATION.md` cites `EV-003-T3-01` and marks gate 3 closed |
| 19 | B0's wording implied execution inside a documentation-only step | B0 **specifies** the regression set; B1 executes it. This document ran no Phase B code | This dossier's changed-files list contains no Python, test, dependency, or configuration file |
| 20 | Model licence and weight provenance unknown in-repo | Recorded as **unknown**; B1 must record exact identifier, immutable revision, weight source, weight digest, and licence **before** any download | The B1 candidate table has no blank or "TBD" provenance cell |
| 21 | No ADR reserved | **ADR-0007** reserved — see "Reserved ADR" | `docs/adr/ADR-0007-…` exists before any profile freeze is proposed |
| 22 | Dependency set unnamed and not isolated | An exact-pinned **optional extra** is required, mirroring the ASR precedent; exact package set and versions are recorded at B1 | `pyproject.toml` gains one optional extra; no default dependency of the backend changes |

## Round-2 correction — 2026-09-01

A second review of this dossier, before any owner decision, found five further logic defects in
the Round-1 resolution above. All five are documentation-only fixes to this file; no Python, test,
dependency, `.gitignore`, or `TASK_APPROVAL.md` change accompanies them.

| # | Defect | Convention fixed | Future proof |
|---|---|---|---|
| R2-1 | The Round-1 "V2, with V1 frozen" design still added a member to the shared `VisionProfileId` enum and let `VisionProfileCatalogV2` carry `VisionProfileV1` instances — a V1 contract change in substance (a wider legal value set, a V1 model constructible inside a V2 envelope) even though no V1 *field* changed | New disjoint `VisionProfileIdV2` and `VisionUnderstandingRequestV2` types; `VisionProfileCatalogV2.profiles: tuple[VisionProfileV2, ...]` only, never a union with `VisionProfileV1`; `VisionProfileId` gains zero members, ever — see "Type separation" and "Profile contract separation" | A V2 contract test asserts `VisionProfileId` still has exactly one member after V2 exists, and that `VisionProfileCatalogV2` rejects a `VisionProfileV1` instance passed into its `profiles` tuple |
| R2-2 | The V2 amendment widened only two rows (`VISION_SCHEMA_INVALID`, `PROHIBITED_CLAIM_DETECTED`) to `attempt_number ∈ {1,2}` without proving the other reachable post-retry outcomes (timeout-after-retry, permanent-failure-after-retry) were representable, or stating why untouched rows should stay untouched | The full **V2 terminal-outcome matrix** (see below): every terminal outcome, its permitted `attempt_number` set, and a stated rationale, including the three required traces (transient→timeout, transient→permanent, transient→schema-invalid-or-policy-blocked) and an explicit "deliberately not broadened" list | V2 contract tests construct all three required traces at attempt `2` and assert `VISION_MODEL_UNAVAILABLE`/`INPUT_NOT_VALIDATED` still reject attempt `2` |
| R2-3 | "Frozen V1 digests" said B1 must "record...the current digests...and assert they are unchanged," which reads as a same-run before/after comparison — a test that would pass even if both sides drifted together, not a real regression guard | "V1 digest regression proof": B1's test must contain **committed golden-constant** hex strings, computed once and hardcoded, so a future code change (not just a same-run comparison) fails the test. This dossier states it records no digest value itself | The B1 test diff shows a literal hex string constant, not a runtime-computed comparison |
| R2-4 | The V2 sketch had a literal `...` inside `compute_profile`'s `Literal[...]`, called the field list an "exact widening list" while `compute_profile` and `VisionProfileIdV2` membership were actually undecided, and gave `weight_sha256: str \| None` a "stated reason" with no field to hold it, plus an ambiguous single-string `runtime_version` | `compute_profile` and `VisionProfileIdV2` membership are removed from the exact sketch and placed in "Fields gated by an open owner decision," explicitly blocking **approval**, not just B1; `weight_sha256_absence_reason: VisionWeightHashAbsenceReason \| None` is a required-either-or pair with `weight_sha256`; `runtime_version: str` is replaced by structured, canonically-ordered `dependency_pins: tuple[VisionDependencyPinV1, ...]` | A V2 test asserts the either-or pairing is enforced and that a `VisionDependencyPinV1` tuple serializes byte-identically regardless of input order |
| R2-5 | Self-review had not specifically checked V1/V2 type leakage, every required post-retry trace, or whether D-4/D-6/D-7/D-9 still matched the corrected design | Self-review table below re-run with five targeted checks; D-4, D-6, D-7, and D-9 reworded so D-7 is marked resolved-by-construction (the alternative it offered — a shared V1/V2 catalog — is now structurally impossible) and D-4/D-9 explicitly state they also fix `compute_profile`/`VisionProfileIdV2` | The updated self-review table and owner-decision table below |

## Round-3 correction — 2026-09-01

A third, documentation-only consistency pass fixed three remaining defects, none touching Python,
tests, dependencies, `.gitignore`, or `TASK_APPROVAL.md`.

| # | Defect | Convention fixed | Future proof |
|---|---|---|---|
| R3-1 | The V2 terminal-outcome matrix correctly permits `VISION_TIMEOUT` at `attempt_number ∈ {1,2}`, but the "Timeout enforcement" section still said a timed-out call returns "at attempt `1`," contradicting the required transient@1 → timeout@2 trace it sits directly above | "Timeout enforcement" now states precisely: a timeout may terminate attempt `1` or attempt `2`; the timeout classification is itself never retried; no third attempt is possible at either origin; and no residual generation may retain device memory in either case | B2 evidence demonstrates a timed-out call at attempt `1` (direct) and, separately, a timed-out retry at attempt `2` (after an attempt-`1` transient failure), both releasing device memory |
| R3-2 | The dossier, `CONTEXT.md`, and `evidence/README.md` all counted "11 owner decisions (D-1…D-11) remain open" after D-7 had already been marked resolved-by-construction in the Round-2 correction — an accounting defect, not a design defect | **Ten** decisions remain open: D-1 through D-6 and D-8 through D-11. D-7 is kept in the register as a historical resolved entry, explicitly labeled as such, not counted among the open items, in all three files | The owner-decision table's own introductory line states the count and the exact ID range; `CONTEXT.md` and `evidence/README.md` state "ten" |
| R3-3 | The dossier's status line read "DRAFT / AWAITING OWNER DECISION" with no readiness signal distinguishing "ready for the owner to work through decisions" from "ready to be approved as written" — but D-4 and D-9 explicitly require a *written amendment* before approval is coherent, per "Fields gated by an open owner decision" | Status changed to **`READY_FOR_OWNER_DECISIONS`**, with an explicit statement that this is not yet `APPROVE P2-T3 PHASE B` because D-4/D-9 require a written amendment first | The status line itself states the distinction; a reader cannot mistake dossier completeness for approval-readiness |

## Round-4 — owner decisions recorded, 2026-09-01

The project owner reviewed the ten open decisions from what was then "Remaining owner decisions"
below and recorded an explicit answer for each, including the exact
`VisionProfileIdV2`/`compute_profile` values that D-4/D-9 required before approval could be
coherent. This section is the record of those answers; that section (renamed "Owner decisions
register" below) is retained with each row updated to show its resolution, so the decision history
stays auditable rather than being overwritten silently.

| ID | Decision recorded |
|---|---|
| D-1 | Semantic-safety control: **(a) synthetic-fixtures-only, with owner review before any real-model output enters feature evidence.** No automated semantic-safety claim is made |
| D-2 | Lexicon policy: **keep the synthetic fixture lexicon.** `known_policy_trigger_rate` stays `NOT_APPLICABLE` under it. A real-term lexicon remains a separate, later plan/approval/`lexicon_version` bump — not part of this authorization |
| D-3 | Execution location: **Lightning L4, development preflight/benchmark only.** Synthetic fixtures only; no production or Integration Sprint provider decision is made here |
| D-4 | Model identity: **`Qwen/Qwen3-VL-8B-Instruct` only**, no quantized/smaller variant in scope for Round 1. Exact immutable revision recorded at B1 before download, per the existing convention |
| D-5 | Contract versioning: **the new V2 contract, with V1 frozen**, as sketched in this dossier |
| D-6 | Terminal-outcome matrix: **the full V2 terminal-outcome matrix above, accepted as written** — every row, not only the four post-retry rows called out in discussion; `attempt_number` sets, `retryable`, and `repair_attempted` values exactly as tabulated |
| D-7 | *(not an open decision — resolved by construction; retained here only for completeness of the register)* |
| D-8 | Provenance applicability: **the applicability table accepted as written** — `model_provenance` required on every model-reached outcome, forbidden on `INPUT_NOT_VALIDATED` |
| D-9 | Candidate count and budget: **exactly one candidate profile**, `compute_profile = GPU_BF16`, `VisionProfileIdV2 = QWEN3_VL_8B_INSTRUCT_BF16_V1`; **one hour of Lightning L4 time authorized as a soft cap** across B2–B4 combined — see "Authorized compute budget" under "Execution location" for the stop-and-reauthorize rule |
| D-10 | Held-out fixture authorship: **Person 2 authors the synthetic drawings and the ground truth/matching rule**, both hashed before any model output is seen; **the project owner reviews the metadata and hashes** before B4 executes |
| D-11 | No-freeze confirmation: **confirmed.** Phase B freezes no profile and selects no runtime default. B5 may recommend only a further controlled experiment or `NOT_ENOUGH_EVIDENCE` |

**This is not itself the approval record.** Recording these answers in this evidence note closes
every content gap this dossier previously listed as blocking, but granting "APPROVE P2-T3 PHASE B"
is a separate governance action recorded in `../../approvals/TASK_APPROVAL.md`, edited only on the
owner's explicit instruction to do so — not implied by this note.

## Round-5 correction — 2026-09-01

A final, read-only red-team review of the complete P2-T3 package (performed after all ten owner
decisions were recorded) found two remaining documentation defects. Both are fixed here,
documentation-only; no Python, test, dependency, `.gitignore`, or `TASK_APPROVAL.md` change
accompanies them.

| # | Defect | Convention fixed | Future proof |
|---|---|---|---|
| R5-1 | Round-1 review-resolution row 13 said V2 failures carry `model_provenance` "only for `VISION_MODEL_UNAVAILABLE` and `VISION_PROVIDER_FAILURE`," while the authoritative "Provenance applicability" table (drafted in a later pass and never used to update this summary row) requires it on all **six** model-reached outcomes — also `SUCCEEDED`, `PROHIBITED_CLAIM_DETECTED`, `VISION_SCHEMA_INVALID`, and `VISION_TIMEOUT`. The row explicitly cited "Provenance applicability" as its source, so it read as a present-tense claim rather than a clearly historical snapshot | Row 13 rewritten to name all six required outcomes and the one forbidden outcome, matching the applicability table it cites, with a parenthetical noting the original row predated that table's expansion | A reader of row 13 alone now gets the same rule as a reader of "Provenance applicability" |
| R5-2 | The dossier gave V2 its own disjoint types for profile ID, request, profile, catalog, and result — including a distinctly named `vision_profile_catalog_v2()` — but never named V2 counterparts for the two hash functions. Prose (in "New types") implied reuse of the literal V1 function `vision_profile_config_hash`, whose actual signature (`vision.py`) is typed only to `VisionProfileV1`; reusing it for V2 would require widening that signature, the same class of V1-adjacent change R2-1 eliminated for the other symbols | New "V2 hash functions" subsection explicitly names `vision_profile_config_hash_v2(profile: VisionProfileV2) -> str` and `vision_profile_catalog_hash_v2(catalog: VisionProfileCatalogV2) -> str`, each SHA-256 over canonical JSON of its respective V2 object with the same ordering discipline as V1's functions; states plainly that no V1 hash function is ever widened or reused for a V2 value; clarifies the `config_hash`/`profile_catalog_hash` **envelope field names** stay unchanged across versions while the **function** that populates them differs | A V2 test asserts `vision_profile_config_hash_v2`/`vision_profile_catalog_hash_v2` reject a V1-typed argument at the type level, and that V1's two hash functions reject a V2-typed argument the same way |

## Contract amendment: a new V2, with V1 frozen

### Why V2 rather than nullable fields on V1

Adding nullable model-provenance fields to the Phase A models would change the canonical JSON of
every V1 value — Pydantic's `model_dump(mode="json")` emits `None` fields — and therefore change
`vision_profile_config_hash` for a fake profile whose configuration did not change. The Phase A
contract would silently stop reproducing its own recorded digests. This dossier therefore adds a
**separate, versioned contract** and leaves every V1 model untouched.

### Type separation: V1 and V2 share no enum, catalog, or request type

The Round-1 fix already stopped V2 from adding *fields* to V1 models. A follow-up review found it
still let V2 add a *member* to the shared `VisionProfileId` enum and let `VisionProfileCatalogV2`
carry `VisionProfileV1` instances inside its own tuple. Both are contract changes to V1 in
substance — widening the legal value set of a V1 type, or making a V1 model constructible inside a
V2 envelope, is not "preserving V1 literally" even though no V1 field changed. This dossier now
gives V2 its own identity types end to end:

- `VisionProfileId` — **zero change.** Still exactly one member, `FAKE_DETERMINISTIC_V1`. No Phase
  B amendment adds a member to it, ever.
- `VisionUnderstandingRequestV1`, `VisionProfileV1`, `VisionProfileCatalogV1`,
  `VisionUnderstandingResultV1` — **zero change**, byte-identical to the implementation cited in
  `P2_T3_PHASE_A_IMPLEMENTATION.md`.
- Every new identity-bearing type below is named `…V2` and is structurally disjoint from its V1
  counterpart: a `VisionProfileCatalogV2` cannot contain a `VisionProfileV1`; a
  `VisionUnderstandingRequestV2` cannot resolve a `VisionProfileId`; the Phase A fake adapter is
  never handed a V2 request and never asked to produce a V2 result.
- Value objects that carry no version-specific meaning — `VisionImageReferenceV1`,
  `ImageDerivationProvenanceV1`, `VisionMediaValidationProvenanceV1`, `ObservedTextV1`,
  `TextLanguageDeclarationV1`, and the five candidate types — are **reused by reference, unchanged**,
  inside both the V1 and V2 envelopes. This is not a V1/V2 leak: none of them is an enum whose
  membership could widen, a catalog whose contents could mix, or a hash input specific to one
  contract version. `VisionImageReferenceV1` already appears in three different V1 places today
  (`vision.py:194`, `vision.py:324`) without being "V1 leaking into V1's own branches"; appearing in
  a V2 envelope too is the same kind of reuse, not a new risk.

### New types (all frozen, all `extra="forbid"`)

```text
VisionProfileIdV2 (StrEnum):       # disjoint from VisionProfileId; real candidates only
  QWEN3_VL_8B_INSTRUCT_BF16_V1     # resolved by D-4/D-9, 2026-09-01 — the only member

VisionUnderstandingRequestV2:
  contract_name: Literal["VisionUnderstandingRequestV2"]
  contract_version: Literal["2.0"]
  correlation_id: str
  source_image_ref: VisionImageReferenceV1
  processing_image_ref: VisionImageReferenceV1 | None
  derivation_provenance: ImageDerivationProvenanceV1 | None
  media_validation: VisionMediaValidationProvenanceV1 | None
  requested_profile_id: VisionProfileIdV2   # resolves only against VisionProfileCatalogV2

VisionModelProvenanceV1:
  model_identifier: str            # e.g. an organisation/model name; never a local path
  model_revision: str              # immutable commit/revision; never a moving tag
  weight_source: str               # non-absolute reference; rejects absolute machine paths
  weight_sha256: str | None        # digest when the artifact publishes one
  weight_sha256_absence_reason: VisionWeightHashAbsenceReason | None   # required iff weight_sha256 is null
  weight_license: str
  dependency_pins: tuple[VisionDependencyPinV1, ...]   # replaces a single ambiguous "runtime_version" string

VisionWeightHashAbsenceReason (StrEnum):     # closed; exhaustive with weight_sha256 by an invariant
  SOURCE_DOES_NOT_PUBLISH_A_DIGEST
  DIGEST_ALGORITHM_INCOMPATIBLE_WITH_SHA256

VisionDependencyPinV1:
  package: str            # e.g. "transformers"; matches the pin as installed
  version: str             # exact pinned version string; no ranges

VisionProfileV2:                   # real-model profiles only; fakes stay on VisionProfileV1
  profile_id: VisionProfileIdV2
  adapter_kind: Literal["QWEN_VL_LOCAL"]   # the only adapter kind this dossier proposes; see D-3
  task: Literal["structured_observation"]
  compute_profile: Literal["GPU_BF16"]     # resolved by D-4/D-9, 2026-09-01 — the only value
  timeout_seconds: float           # > 0
  structured_output_mode: Literal["STRICT_JSON_OBJECT"]
  adapter_version: str
  timeout_retry_policy: Literal["NEVER_RETRY"]                        # unchanged, single value
  model_provenance: VisionModelProvenanceV1
  decoding: VisionDecodingV1

VisionDecodingV1:                  # deterministic decoding is part of the configuration identity
  sampling_enabled: Literal[False] # greedy only; sampling is unconstructible in Phase B
  temperature: None                # must be absent when sampling is disabled
  top_p: None
  top_k: None
  beam_count: Literal[1]
  max_new_tokens: int              # > 0, explicit
  repetition_penalty: float        # explicit, default recorded not implied
  seed: int                        # recorded even under greedy decoding
  image_preprocessing_version: str # resize/pixel-budget policy identity; affects output

VisionProfileCatalogV2:
  contract_name: Literal["VisionProfileCatalogV2"]
  contract_version: Literal["2.0"]
  profiles: tuple[VisionProfileV2, ...]   # real candidates only; never a VisionProfileV1 instance
```

`VisionDependencyPinV1` entries are sorted by `package` at construction and duplicate `package`
names are rejected — the same reject-don't-coerce, canonical-order discipline already used for
`TextLanguageDeclarationV1.tags` (`vision.py:88-92`) — so two content-equivalent pin sets always
serialize byte-identically and hash identically inside `vision_profile_config_hash_v2` (defined
immediately below).
`weight_sha256`/`weight_sha256_absence_reason` are a required-either-or pair, mirroring the
`processing_image_ref`/`derivation_provenance` pairing already enforced on `VisionUnderstandingRequestV1`
(`vision.py:201-215`): exactly one of the two is non-null, never both, never neither.

### V2 hash functions — explicitly separate from V1, never a widened V1 signature

V1's two hash functions are typed to V1's models only —
`vision_profile_config_hash(profile: VisionProfileV1) -> str` and
`vision_profile_catalog_hash(catalog: VisionProfileCatalogV1) -> str` — and neither is ever widened
to also accept a V2 type. Widening either signature to `VisionProfileV1 | VisionProfileV2` (or the
catalog equivalent) would be exactly the class of V1-adjacent change the "V1 gains zero members,
ever" principle forbids elsewhere in this dossier (R2-1); a shared function whose accepted-input set
grows is a change to that function's contract even when no existing call site's behavior moves.
This dossier therefore names two new, separately defined V2 functions, mirroring the same
`_v2`-suffix pattern already used for `vision_profile_catalog_v2()`:

```text
vision_profile_config_hash_v2(profile: VisionProfileV2) -> str
vision_profile_catalog_hash_v2(catalog: VisionProfileCatalogV2) -> str
```

Each is SHA-256 over the canonical JSON serialization — sorted keys, compact separators — of the
complete V2 value it names: `vision_profile_config_hash_v2` over the whole `VisionProfileV2`
(including its `model_provenance` and `decoding` sub-objects and the canonically-ordered
`dependency_pins`), `vision_profile_catalog_hash_v2` over the whole `VisionProfileCatalogV2`
(`contract_name`, `contract_version`, and the ordered `profiles` tuple). This is the identical
canonical-ordering discipline V1's two hash functions already use, applied to
`VisionProfileV2`/`VisionProfileCatalogV2` instead of their V1 counterparts. Neither V2 function's
output is stored inside the value it hashes; both are computed from it, exactly mirroring the V1
precedent (`vision.py:176-183`).

The shared envelope's `config_hash` and `profile_catalog_hash` **fields** keep their V1 names and
meaning unchanged on both contract versions — "V2 envelope carries every V1 envelope field
unchanged in name and meaning" (above) still holds. Only the *function that computes the value*
differs by version: a V1 result's `config_hash`/`profile_catalog_hash` is always produced by
`vision_profile_config_hash`/`vision_profile_catalog_hash`; a V2 result's is always produced by
`vision_profile_config_hash_v2`/`vision_profile_catalog_hash_v2`. No code path may call a V1 hash
function on a V2 value or vice versa — the type signatures make the wrong call a type error, not
merely a convention.

The contract-level decoding field names above are **proposed names for the configuration record**.
Their mapping onto the pinned runtime's generation API must be verified against that exact pinned
version and recorded at B1. This dossier does not assert any library's parameter names as fact.

### Fields resolved by owner decision (D-4/D-9) — 2026-09-01

The two fields that were intentionally absent from the sketch above, pending D-4 and D-9, are now
resolved with exact values. This section previously stated they were placeholders; they are not
placeholders any longer, and the sketch above should be read with these two fixed:

```text
VisionProfileIdV2 (StrEnum):
  QWEN3_VL_8B_INSTRUCT_BF16_V1      # the only member; Round 1 candidate

VisionProfileV2.compute_profile: Literal["GPU_BF16"]   # the only value
```

- **Model:** `Qwen/Qwen3-VL-8B-Instruct` only. No quantized or smaller variant is in scope for
  Round 1. The immutable revision hash is recorded at B1, before any download, per the existing
  convention (finding 20) — it is a factual lookup against the pinned model source, not a policy
  choice, and this dossier does not assert a value for it.
- **Candidate count:** exactly one profile. `VisionProfileCatalogV2` therefore contains exactly one
  `VisionProfileV2` entry for Round 1.
- **Precision / `compute_profile`:** `GPU_BF16`, the only value in the closed
  `Literal["GPU_BF16"]` set — mirroring the single-value-literal pattern V1 already uses for
  `compute_profile: Literal["NONE"]` and the `GPU_<PRECISION>` naming already used by
  `AsrProfileV1.compute_profile` (`GPU_INT8_FLOAT16`, `GPU_FLOAT16`).
- **`VisionProfileIdV2` member name:** `QWEN3_VL_8B_INSTRUCT_BF16_V1`, following the existing
  `<MODEL>_<VARIANT>_<PRECISION>_V<N>` naming convention already used for
  `AsrProfileId.WHISPER_TURBO_INT8_AUTO_V1` and `VisionProfileId.FAKE_DETERMINISTIC_V1`.

Because there is exactly one candidate, `VisionProfileIdV2`'s membership and
`VisionProfileV2.compute_profile`'s closed set are now both single-value, closed, and exact — the
condition this dossier's own gate required before the owner could approve Phase B.

```text
VisionUnderstandingResultV2 = VisionUnderstandingSuccessV2 | VisionUnderstandingFailureV2
  contract_name: Literal["VisionUnderstandingResultV2"]
  contract_version: Literal["2.0"]
```

The V2 envelope carries every V1 envelope field unchanged in name and meaning, plus
`model_provenance` where the applicability table below permits it.

### Provenance applicability

| Outcome | `model_provenance` | Rationale |
|---|---|---|
| `SUCCEEDED` | **Required** | The model actually produced the observations |
| `PROHIBITED_CLAIM_DETECTED` | **Required** | The model produced text; the policy blocked it |
| `VISION_SCHEMA_INVALID` | **Required** | The model produced output that failed mapping |
| `VISION_MODEL_UNAVAILABLE` | **Required** | Identifying which weights/device failed to load is the point of the record |
| `VISION_PROVIDER_FAILURE` | **Required** | The runtime was reached and failed |
| `VISION_TIMEOUT` | **Required** | The model was invoked and the deadline expired |
| `INPUT_NOT_VALIDATED` | **Forbidden** | Ingress rejected the request at attempt `0`; no model was loaded or invoked, so any provenance would be a claim about work that never happened |

`INPUT_NOT_VALIDATED` stays traceable through `profile_id`, `profile_catalog_hash`, the result
contract version, and the policy configuration fields — exactly as in V1.

### Backward compatibility

- Every V1 model, validator, digest, and test is untouched. The fake adapter keeps emitting V1.
- `VisionProfileId` and `VisionProfileIdV2` are disjoint enums; `VisionProfileCatalogV2` can never
  contain a `VisionProfileV1` instance; `VisionUnderstandingRequestV2` can never resolve a
  `VisionProfileId` member, and `VisionUnderstandingRequestV1` can never resolve a
  `VisionProfileIdV2` member. There is no code path in which a fake profile is validated, resolved,
  or reported through a V2 type, or a real profile through a V1 type.
- A V2 payload is never presented as a V1 payload, and vice versa; `contract_name` and
  `contract_version` differ, and `extra="forbid"` makes accidental cross-validation fail loudly
  rather than silently.
- P2-T4 (unbuilt) must accept `VisionUnderstandingResultV1 | VisionUnderstandingResultV2` when it
  is built; this dossier records that requirement and creates no P2-T4 code.
- No V1 evidence artifact is re-generated, re-hashed, or invalidated by Phase B.

### V1 digest regression proof

This dossier does not record a digest value anywhere in its own prose, because a hex string typed
into a document is unverified and can silently drift from the code that produces it — the failure
mode finding 4 exists to prevent. Instead, B1 must add a test that contains **committed golden
constants**: the literal hex digest strings for `vision_profile_config_hash(FAKE_DETERMINISTIC_V1)`
and `vision_profile_catalog_hash(vision_profile_catalog())`, computed once against the current V1
implementation and hardcoded into the test file (the same pattern already used for fixed-value
assertions elsewhere in this test suite, e.g. `test_vision_phase_a_contracts.py`'s exact-string
checks). The test asserts the function's **current** output equals that **committed** constant —
not a before/after comparison within one run, which would pass trivially even if both sides moved
together. Any future change to `VisionProfileV1`, `VisionProfileCatalogV1`, or either hashing
function then fails this test immediately, including a change made long after Phase B ships. This
dossier's proof obligation is therefore: the golden-constant test exists and is committed at B1;
it is not that a digest is recorded here, because none is.

## Profile contract separation — nothing on V1 widens

Earlier drafting of this dossier called this section an "exact widening list" and proposed adding
a member to the shared `VisionProfileId` enum. Both were defects: a shared enum that gains a
member has changed its legal value set for every existing caller, including the Phase A fake
adapter's own validation path, and an "exact" list should not have included a field
(`compute_profile`) whose value set was not actually fixed. This section replaces both.

| Symbol | V1 today | Phase B | Status |
|---|---|---|---|
| `VisionProfileId` | one member, `FAKE_DETERMINISTIC_V1` (`vision.py:120-123`) | **No change, ever.** No amendment in this dossier adds a member | Fixed |
| `VisionProfileV1.*` (every field) | as implemented | **No change** | Fixed |
| `VisionProfileCatalogV1` | fake-only tuple, one entry | **No change** | Fixed |
| `VisionUnderstandingRequestV1` / `VisionUnderstandingResultV1` | as implemented | **No change** | Fixed |
| `VisionProfileIdV2` | does not exist | New, disjoint enum. One member, `QWEN3_VL_8B_INSTRUCT_BF16_V1` — resolved by D-4/D-9, 2026-09-01 | Fixed |
| `VisionProfileV2.timeout_retry_policy` | n/a | `Literal["NEVER_RETRY"]`, the only constructible value | Fixed — **must not widen**; widening reopens a settled decision (`plan/P2_T3_VISION_RESEARCH_PLAN.md:160-163`) and needs its own approval, not this dossier |
| `VisionProfileV2.compute_profile` | n/a | `Literal["GPU_BF16"]`, the only value — resolved by D-4/D-9, 2026-09-01 | Fixed |
| `VisionProfileCatalogV2` | n/a | New; real candidates only, never a `VisionProfileV1` instance; exactly one entry for Round 1 | Fixed |

Because no field is added to `VisionProfileV1` and no member is added to `VisionProfileId`, no
Phase A digest moves and no Phase A validation path can accept a value it could not accept before.
This is the deliberate trade that makes finding 4 (and the type-leakage defect found in review)
unreachable by construction rather than merely documented.

## Catalog resolution and hash comparability

This section governs which **catalog-constructor** function resolves a request. The correspondingly
separate **hash** functions (`vision_profile_config_hash_v2`/`vision_profile_catalog_hash_v2`,
never a widened V1 signature) are defined under "V2 hash functions — explicitly separate from V1"
above.

1. **One canonical static catalog per contract version, and per version only.**
   `vision_profile_catalog()` (fake-only, unchanged) serves V1; a new `vision_profile_catalog_v2()`
   (real candidates only, per "Profile contract separation" above) serves V2. Within a version,
   request validation and adapter resolution call the **same** function, so the two can never
   disagree. Across versions, `VisionUnderstandingRequestV1.requested_profile_id` (`VisionProfileId`)
   can only ever resolve against `vision_profile_catalog()`, and
   `VisionUnderstandingRequestV2.requested_profile_id` (`VisionProfileIdV2`) can only ever resolve
   against `vision_profile_catalog_v2()` — the two request/catalog/ID triples never cross.
2. **No dynamic per-request catalog.** A caller may not supply a catalog with a request. Divergent
   constructor injection is forbidden for real V2 adapters; it remains available to the Phase A
   fake for tests only, which is how the defensive resolve-miss guard is exercised — unchanged from
   V1 and not extended to V2's real adapter.
3. **A resolve miss is typed, never raised.** New closed token `PROFILE_NOT_RESOLVABLE` under
   `INPUT_NOT_VALIDATED`, `attempt_number = 0`, `retryable = false`, `repair_attempted = false`,
   `policy_execution_state = NOT_EXECUTED`. No catalog condition may escape as an untyped
   exception.
4. **Comparability.** `profile_catalog_hash` pins the catalog snapshot that resolved a
   `profile_id`. Results carrying different catalog hashes are different populations: a report
   must name the hash, must not aggregate across hashes, and must not restate a V1-era number as a
   V2-era number. The same rule already governs `policy_match_view_version`.

## V2 terminal-outcome matrix

The Round-1 fix only widened two rows (`VISION_SCHEMA_INVALID`, `PROHIBITED_CLAIM_DETECTED`) to
admit `attempt_number = 2`, without proving every attempt-2 terminal outcome an adapter can
actually reach was representable, and without stating why the rows it left untouched should stay
untouched. This section replaces it with the complete matrix and a rationale per row.

**Definition.** `attempt_number` counts adapter **inference attempts** — real model invocations in
V2, simulated ones in the V1 fake. `attempt_number = 0` is reserved for a result that never reaches
inference at all (`INPUT_NOT_VALIDATED`; ingress verification runs first, per
`plan/P2_T3_VISION_RESEARCH_PLAN.md:315-333`). `attempt_number = 1` is always the first inference
attempt. `attempt_number = 2` exists **only** when attempt `1`'s outcome is classified
`TRANSIENT_RUNTIME_FAILURE`, which triggers the adapter's one permitted retry — the same rule V1
already enforces. No attempt number above `2` is constructible in either contract version; a
transient failure observed *at* attempt `2` is not retried again, because the retry budget is one,
not "one per transient classification."

V1's matrix (`plan/P2_T3_VISION_RESEARCH_PLAN.md:747-754`) is unchanged in every row. The table
below is the full V2 matrix — it repeats V1's unchanged rows for completeness rather than only
listing deltas, so every permitted terminal state is provable in one place.

| Terminal outcome | `error_code` | `error_detail` | `attempt_number` | `retryable` | `repair_attempted` | `policy_execution_state` | Rationale for exactly this attempt set |
|---|---|---|---|---|---|---|---|
| Success | *(status = SUCCEEDED)* | n/a | `{1, 2}` | n/a | as produced | `PASSED` | Direct success at `1`, or success on the one permitted retry after an attempt-`1` transient failure |
| Input rejected before inference | `INPUT_NOT_VALIDATED` | 4 existing tokens + new `PROFILE_NOT_RESOLVABLE` | `{0}` only | `false` | `false` | `NOT_EXECUTED` | Ingress verification (profile resolution, P2-T1 `PASS`, source hash) happens before any inference attempt; unchanged from V1 |
| Model/device failed to load | `VISION_MODEL_UNAVAILABLE` | `MODEL_LOAD_FAILED` / `DEVICE_UNAVAILABLE` | `{1}` only | `false` | `false` | `NOT_EXECUTED` | Model/device load is a **one-time precondition for the whole call**, not a per-attempt operation — there is exactly one load, so a load failure can only be attributed to attempt `1`. A device that fails **during** a retry's actual generation (after a successful load) is a `VISION_PROVIDER_FAILURE` at that attempt, never `VISION_MODEL_UNAVAILABLE` — this dossier does not broaden this row to `{1, 2}` |
| Deadline exceeded | `VISION_TIMEOUT` | `TIMEOUT_BUDGET_EXCEEDED` | `{1, 2}` | `false` | `false` | `NOT_EXECUTED` | A timeout can occur on the direct first attempt, or as the retry's own outcome (**required trace: transient@1 → timeout@2**). Wherever it occurs, timeout is terminal: it is a distinct classification from `TRANSIENT_RUNTIME_FAILURE`, so a timeout never itself triggers a further retry, and `attempt_number ≤ 2` forecloses a third attempt regardless |
| Provider failure, permanent, direct | `VISION_PROVIDER_FAILURE` | `PERMANENT_RUNTIME_FAILURE` | `{1}` | `false` | `false` | `NOT_EXECUTED` | A permanent classification on the first attempt is not retried — only a *transient* classification triggers the retry |
| Provider failure, permanent, after retry | `VISION_PROVIDER_FAILURE` | `PERMANENT_RUNTIME_FAILURE` | `{2}` | `false` | `false` | `NOT_EXECUTED` | **Required trace: transient@1 → permanent@2.** The retry attempt's own failure can be classified permanent even though attempt `1` was transient; this is a second, independent classification, not a contradiction |
| Provider failure, transient, exhausted | `VISION_PROVIDER_FAILURE` | `TRANSIENT_RUNTIME_FAILURE` | `{2}` only | `true` | `false` | `NOT_EXECUTED` | A transient failure at attempt `1` is never itself terminal — it always proceeds to the retry. This row is therefore observed only at attempt `2`, when the retry is *also* transient and the budget is exhausted. `retryable = true` records that the classification permits a retry in principle; it does not mean a further retry occurs, since none remains |
| Schema-invalid, direct | `VISION_SCHEMA_INVALID` | `OUTPUT_MAPPING_FAILED` / `DUPLICATE_OBSERVATION_ID` / `REFERENCE_INTEGRITY_VIOLATION` | `{1}` | `false` | `true` only after a lossless fenced unwrap, else `false` | `NOT_EXECUTED` | Direct mapping failure on the only/first attempt |
| Schema-invalid, after retry | `VISION_SCHEMA_INVALID` | same three tokens | `{2}` | `false` | `true` only after a lossless fenced unwrap, else `false` | `NOT_EXECUTED` | **Required trace: transient@1 → schema-invalid@2.** The mapping layer is never re-invoked a second time for its *own* failure (unchanged from V1); this row exists because the *inference* layer retried once, and the retry's output happened to fail mapping |
| Policy-blocked, direct | `PROHIBITED_CLAIM_DETECTED` | one of six categories | `{1}` | `false` | `true` only after a lossless fenced unwrap, else `false` | `BLOCKED` | Direct block on the only/first attempt |
| Policy-blocked, after retry | `PROHIBITED_CLAIM_DETECTED` | one of six categories | `{2}` | `false` | `true` only after a lossless fenced unwrap, else `false` | `BLOCKED` | **Required trace: transient@1 → policy-blocked@2.** Recording `repair_attempted = false` for output that genuinely arrived fenced would make the adapter record a falsehood, so the `true` value stays available here exactly as on the direct row |

**Rows deliberately not broadened**, stated so no future reader assumes an omission was an
oversight:

- `INPUT_NOT_VALIDATED` stays `{0}` only — it is defined as "before inference," so it structurally
  cannot occur at attempt `1` or `2`.
- `VISION_MODEL_UNAVAILABLE` stays `{1}` only — see its rationale cell above; broadening it would
  require modeling per-attempt reload, which this dossier does not propose.
- No row anywhere admits `attempt_number > 2`. The envelope field itself is bounded
  (`attempt_number: int = Field(ge=0, le=2)`, `vision.py:327`) and this dossier proposes no change
  to that bound.

Retry and repair stay enforced entirely inside the adapter. A caller must never add its own retry.

## Repair rule — frozen

The single permitted repair remains a **lossless unwrap of a Markdown fence whose contents are
already a complete JSON object**. Completing truncated JSON, closing delimiters, filling defaults,
coercing enums, scanning for the first `{…}` block, or extracting JSON from surrounding prose are
all prohibited, in Phase B as in Phase A.

Real vision-language output frequently arrives wrapped in prose or reasoning text. Under this rule
such output is `VISION_SCHEMA_INVALID`. **That is a measurement, not a defect to patch.** A low
schema-valid rate is a reportable B3 finding and a legitimate reason to recommend
`NOT_ENOUGH_EVIDENCE`; it is never a justification to widen repair. Changing the repair rule
requires a new plan and a new approval.

## Execution location — proposed

- **Proposed development preflight location: Lightning L4 (24 GB), development only.**
- Constraints, all binding:
  - Synthetic inputs only. No real child data, ever.
  - No endpoint, credential, provider URL, account identifier, or absolute machine path enters
    Git, evidence, logs, or this dossier.
  - No raw model output leaves the ephemeral local location defined below.
  - This is **not** a production decision, **not** a runtime default, and **not** a provider
    selection for the Integration Sprint. `ADR-0005` records Lightning as a fixture-only
    development provider that is explicitly **not** treated as private networking; uploading
    synthetic fixtures is acceptable precisely because they are synthetic.
  - The earlier one-off L4 smoke test remains **infrastructure reconnaissance only**: not
    benchmark evidence, not model selection, not approval, and cited nowhere as a result.
- **Local feasibility is unknown.** The only GPU documented in this repository is an 8 GB
  RTX 4060 laptop GPU (`P2_T2_PHASE_B_ROUND1_ASR_REPORT.md:126`). Whether the baseline runs there
  at any precision is not recorded anywhere and must be measured and reported at B1 — never
  assumed, and never reported as `0` when it means "not measured".

### Authorized compute budget — resolved by D-9, 2026-09-01

**One hour of Lightning L4 GPU time is authorized as a soft cap**, covering B2 (typed preflight)
through B4 (benchmark, including its mandatory repeat run) combined — not a separate hour per work
package. It is explicitly a **soft** cap, not a hard kill: if the one-hour mark is reached before
B2–B4 are complete, the runner must **stop**, record whatever was actually measured up to that
point (never fabricate a completed run to fit the budget), and the owner must **explicitly
re-authorize** additional time before any further GPU work continues under this dossier. No
implicit renewal, and no silent overrun, is permitted. This mirrors the existing
"never fabricate a measurement to fit a constraint" discipline already applied to P2-T2's warmup
handling (`DECISIONS.md`).

## Raw-output handling

| Rule | Requirement |
|---|---|
| Location | Raw model output exists only under an ephemeral, already-gitignored runtime path (`data/runtime/…` is ignored today by `.gitignore:59`). Nothing else may hold it |
| Lifetime | Deleted at the end of the study; never archived into `evidence/` |
| Who may read it | The project owner, and Person 2 while diagnosing mapping failures. No third party, no issue tracker, no chat transcript, no pull-request body |
| What may persist | Only safe counts and closed typed identifiers: schema-valid counts, typed failure codes/details, fence/truncation/extra-key counts, and category tokens |
| What may never persist | Model-produced free text, matched policy terms, the derived match view, lexicon entries, prompts containing observations, provider payloads, stack traces containing output |
| Why this matters | Schema-invalid payloads never reach the policy layer at all — the policy runs last, only over structurally valid results. A human diagnosing mapping failures is therefore reading model text that no policy has filtered. That is the real semantic-safety exposure of B3, and it is controlled by process, not by the lexical layer |

## Policy and semantic-safety limitation

- The Phase A layer is a **known-violation lexical regression check**, not a semantic-safety
  guarantee. A paraphrase absent from the lexicon is not detected. Nothing in Phase B changes this.
- Its lexicon is six deliberately fictitious synthetic markers. A real model will not emit them.
  Therefore, for B3 and B4, `known_policy_trigger_rate` measured against
  `vision-prohibited-lexicon-fixture-v1` is reported as **`NOT_APPLICABLE`** — never `0`, never
  omitted, and never phrased as evidence that the model produced no prohibited claim.
- The existing lexical-policy unit tests are **wiring evidence only**: they prove the layer runs,
  blocks, and never leaks matched text. They are not evidence about any model.
- `semantic_safety_coverage` and `semantic_safety_recall` remain `NOT_MEASURED` until both an
  approved mechanism and a dedicated labelled held-out set exist.
- Introducing a real-term lexicon requires a **separate plan, separate owner approval, a
  `lexicon_version` bump, and a recorded review**. It is out of scope here.

## Benchmark design (B4)

**Per-collection metrics.** One row per collection; no collection is silently absent.

| Collection | Metric | If unavailable |
|---|---|---|
| `entities` | Coverage/accuracy against pre-authored ground truth | `NOT_MEASURED` + reason |
| `actions` | Coverage/accuracy, plus optional-endpoint resolution rate | `NOT_MEASURED` + reason |
| `relations` | Coverage/accuracy, plus endpoint-kind validity rate | `NOT_MEASURED` + reason |
| `themes` | Coverage/accuracy, plus `evidence_refs` validity rate | `NOT_MEASURED` + reason |
| `ambiguous_regions` | Count and rate per result only. Accuracy is **`NOT_MEASURED`**, reason: Phase A regions carry no geometry and are not evidence targets, so there is nothing to score against | — |

**Denominators.** Every rate names its population explicitly:

| Metric | Denominator |
|---|---|
| Schema-valid result rate | Attempted fixture × profile runs, warmup excluded |
| Typed-failure counts by code | The same attempted-run population |
| Lossless-unwrap recovery rate | Runs whose raw output arrived fenced |
| Per-collection coverage | Ground-truth items of that collection for the scored fixtures |
| `known_policy_trigger_rate` | `NOT_APPLICABLE` under the fixture lexicon. When a real lexicon is ever approved: results that actually reached the policy layer, excluding every `policy_execution_state = NOT_EXECUTED` result, which was never inspected and is neither a trigger nor a clean pass |
| Latency p50/p95 | Non-warmup runs of that profile only; cold start reported separately |

**Ground truth.** The held-out synthetic manifest, the ground-truth labels, and the matching rule
(`vision-b4-matching-rule-v1`) are authored and SHA-256-hashed **before any model output is seen**;
those hashes are recorded at creation and repeated in the report. Post-hoc ground truth is not
measurement.

**Reproducibility.** Because decoding is greedy and pinned, B4 must execute a **repeat run** and
report both, following the P2-T2 Round-1 precedent. Quality metrics that do not reproduce
invalidate the run rather than being averaged.

**Non-comparability.** Runs are never merged across `profile_catalog_hash`, `config_hash`,
`content_policy_version`, or `policy_match_view_version`.

## Timeout enforcement

B1 must state, and B2 must demonstrate, how the deadline is enforced for a synchronous generation
call. Acceptable designs: an in-band deadline honoured by the generation loop, or generation in a
killable subprocess. **Abandoning a thread while generation continues is forbidden** — that is the
overlap/VRAM-exhaustion risk that made `NEVER_RETRY` mandatory.

A timed-out call returns `VISION_TIMEOUT` / `TIMEOUT_BUDGET_EXCEEDED` at **either attempt `1` or
attempt `2`** — the deadline applies to each inference attempt independently, so the direct first
attempt can time out (`attempt_number = 1`), and so can the one permitted retry after an
attempt-`1` transient failure (`attempt_number = 2`; this is the required transient@1 → timeout@2
trace in the V2 terminal-outcome matrix above). Wherever it occurs, the timeout itself is
**non-retryable**: a timeout is a distinct classification from `TRANSIENT_RUNTIME_FAILURE` and
never itself triggers a further retry, so **no third attempt is possible** — this holds whether the
timeout landed at attempt `1` or attempt `2`, and `attempt_number ≤ 2` forecloses it structurally
regardless. In every case, **no residual generation may retain device memory**: the enforcement
mechanism (in-band deadline or killable subprocess) must free the model/device state that attempt
was using before the typed result is returned.

## Repository hygiene — required before B1 executes

None of these are created by this documentation-only step. They are the exact changes B1 must make
first.

**`.gitignore` entries to add** (mirroring the ASR precedent at `.gitignore:5,13-14`):

```text
backend/.vision.env
features/FEAT-003-multimodal-understanding/fixtures/vision-b4/images/**
**/qwen-vl-cache/
models/
```

The held-out manifest, ground-truth metadata, and matching rule stay **versioned** (metadata and
hashes only, no image payloads). `data/runtime/` is already ignored (`.gitignore:59`) and is where
raw output lives.

**Dependency isolation.** One exact-pinned optional extra (e.g. `vision-qwen`) in
`backend/pyproject.toml`, so no other Sprint-1 component acquires a GPU dependency. Exact package
set and versions are recorded at B1 before install; this dossier asserts none, because asserting a
version that was never resolved would be fabricated provenance.

**Runtime configuration.** A standalone constructor-injected config object under
`backend/src/sketch2life/infrastructure/ai`, never added to the shared application `Settings`
class, with **no default model path anywhere**, reading only explicitly named environment
variables from an ignored local file. Only variable **names** are ever recorded in source or
evidence — never values.

## Reserved ADR

**ADR-0007 — Vision runtime, dependency pinning, and Qwen3-VL candidate profiles.** Reserved now
(`docs/adr/` currently holds ADR-0001…ADR-0006). It must exist, with the exact-pin rationale and
the candidate table, before any profile is proposed for freeze at B5. No profile is frozen and no
runtime default is selected by Phase B.

## Proposed approval scope

If the owner approves, Phase B is authorized for exactly this and nothing more:

1. **B1 — isolated real runtime.** Add the `.gitignore` entries and the exact-pinned optional
   extra; create the Qwen adapter and its constructor-injected runtime configuration; add the V2
   contracts, `VisionProfileCatalogV2` (containing exactly the one resolved candidate,
   `QWEN3_VL_8B_INSTRUCT_BF16_V1` at `compute_profile = GPU_BF16`), and the `PROFILE_NOT_RESOLVABLE`
   token; add `vision_profile_config_hash_v2`/`vision_profile_catalog_hash_v2` as new functions
   (never a widened V1 signature); record the candidate table with full model/weight/licence
   provenance for `Qwen/Qwen3-VL-8B-Instruct`, including its immutable revision, **before**
   downloading anything; add the V1-digest regression test; state the timeout-enforcement design.
2. **B2 — typed GPU preflight.** One real model load and one synthetic inference through the real
   adapter on Lightning L4, within the authorized one-hour soft-cap budget (see "Authorized compute
   budget"); typed-failure paths proven by injected fakes; record measured values or explicit
   `NOT_MEASURED` reasons.
3. **B3 — structured-output mapping study.** Measure schema-valid rate, fenced/truncated/extra-key
   counts, duplicate IDs, broken references, lossless-unwrap recovery, and typed-failure counts,
   under the raw-output handling rules above, within the same combined budget.
4. **B4 — controlled vision-only benchmark.** Held-out synthetic manifest authored by Person 2 with
   pre-authored hashed ground truth, reviewed by the owner before execution; all five collections;
   explicit denominators; mandatory repeat run; no cross-hash merging; within the same combined
   budget, stopping and requesting re-authorization if the one-hour cap is reached first.
5. **B5 — recommendation gate.** Comparison table plus a recommendation of either a further
   controlled experiment or `NOT_ENOUGH_EVIDENCE`, and ADR-0007.

## Explicit non-goals

Approving this package does **not** authorize: freezing any profile or selecting a runtime
default; a real-term prohibited lexicon; any claim of semantic safety; production deployment or a
production provider selection; real child data of any kind; provider credentials in Git; raw model
output in evidence, logs, or commits; HTTP/API, UI, mobile, session, job, database, queue, or
object-storage integration; P2-T4 or P2-T5 work, including the CLI and the end-to-end multimodal
report; user-facing output, Integration Sprint promotion, or any Gate A decision; changes to the
Phase A V1 contract, its digests, its fake adapter behavior, or its recorded evidence; and any
widening of the repair rule or of `timeout_retry_policy`.

## Owner decisions register

**All ten decisions are now recorded: D-1 through D-6 and D-8 through D-11.** D-7 was never an
open decision — see "Catalog structure": the design fix in R2-1 made its alternative option
structurally impossible. The table below keeps each item's original options alongside the recorded
answer, so the decision history stays auditable; see "Round-4 — owner decisions recorded" above for
the same answers presented as a flat record.

| ID | Decision | Options considered | Recorded answer (2026-09-01) |
|---|---|---|---|
| D-1 | Semantic-safety control for unknown paraphrases | (a) synthetic-fixtures-only with owner review before evidence — recommended minimal control; (b) an approved second-pass semantic check (needs its own dependency/model approval); (c) a narrower declared vocabulary | **(a)**, as recommended |
| D-2 | Lexicon policy for Phase B | Keep the synthetic fixture lexicon with `known_policy_trigger_rate = NOT_APPLICABLE` (proposed), or commission a real-term lexicon under a separate plan/approval/`lexicon_version` bump | **Keep the synthetic fixture lexicon**, as proposed |
| D-3 | Execution location | Approve Lightning L4 for development preflight only (proposed), require local-only execution pending a feasibility measurement, or defer B2 | **Lightning L4, development preflight/benchmark only**, as proposed |
| D-4 | Model identity and scope | Exact model identifier and immutable revision; whether a quantized or smaller variant is in scope as a separate candidate. Licence is currently **unknown** and must be recorded before download. **Jointly with D-9, this fixes `VisionProfileIdV2`'s membership and `VisionProfileV2.compute_profile`'s closed `Literal[...]` set — both are blocking, not merely informational** | **`Qwen/Qwen3-VL-8B-Instruct` only**, no variant. Revision recorded at B1 before download |
| D-5 | Contract versioning approach | Approve the new V2 contract with V1 frozen (proposed), or direct a different scheme | **New V2 contract, V1 frozen**, as proposed |
| D-6 | Terminal-outcome matrix | Approve the full V2 terminal-outcome matrix above (proposed): `attempt_number ∈ {1,2}` for success/timeout/permanent-failure/schema-invalid/policy-blocked, `{2}` only for exhausted-transient, `{1}` only for model-unavailable, `{0}` only for input-not-validated; `repair_attempted` truthfulness on the schema-invalid and policy-blocked rows | **Approved as written**, the full matrix, not only the outcomes discussed |
| D-7 | Catalog structure | **Resolved by construction, not open.** One canonical catalog per contract version is now the only structurally possible design, because `VisionProfileCatalogV2` cannot contain a `VisionProfileV1` instance (R2-1) — the earlier alternative ("a single shared catalog... accept that replayed Phase A runs carry a new hash") is foreclosed by that fix, not merely disfavored. Retained here only so a reader who saw the earlier draft can see it was closed, not dropped | *(no owner decision required)* |
| D-8 | Provenance applicability | Approve the applicability table (provenance on every model-reached outcome; forbidden on `INPUT_NOT_VALIDATED`) | **Approved as written** |
| D-9 | Candidate count and budget | How many candidate profiles B4 may compare, and what compute spend is authorized. **Jointly with D-4, this fixes `VisionProfileIdV2`'s membership and `VisionProfileV2.compute_profile`'s closed `Literal[...]` set — both are blocking, not merely informational** | **One candidate**, `compute_profile = GPU_BF16`, `VisionProfileIdV2 = QWEN3_VL_8B_INSTRUCT_BF16_V1`; **one hour of L4 time, soft cap**, stop-and-reauthorize if exceeded |
| D-10 | Held-out fixture authorship | Who authors the synthetic drawings and ground truth, and confirmation that they are synthetic-only | **Person 2 authors and hashes**; **owner reviews metadata/hashes** before B4 runs |
| D-11 | Confirmation of no-freeze | Confirm that Phase B freezes no profile and selects no runtime default, and that ADR-0007 is reserved for that separate decision | **Confirmed** — no freeze, no runtime default |

## Self-review — contradictions checked

### Targeted Round-2 checks

| Focus | Check | Result |
|---|---|---|
| V1/V2 type leakage | Does any V2 identity-bearing type (`VisionProfileIdV2`, `VisionUnderstandingRequestV2`, `VisionProfileV2`, `VisionProfileCatalogV2`, `VisionUnderstandingResultV2`) share membership, a union arm, or a resolution path with its V1 counterpart? | No. Checked each: `VisionProfileId` has no new member (`VisionProfileIdV2` is a separate, disjoint enum, resolved by D-4/D-9 to its one member, `QWEN3_VL_8B_INSTRUCT_BF16_V1`); `VisionProfileCatalogV2.profiles` is `tuple[VisionProfileV2, ...]` with no `VisionProfileV1` arm; `VisionUnderstandingRequestV2.requested_profile_id` types as `VisionProfileIdV2`, so it cannot even be constructed with a `VisionProfileId` value; the reused value objects (`VisionImageReferenceV1`, etc.) are plain structural types with no enum/catalog membership to leak |
| V1/V2 type leakage | Does reusing `VisionImageReferenceV1` etc. inside `VisionUnderstandingRequestV2` count as a V1 change? | No. The type itself is not modified; it is referenced from a second location, the same way it is already referenced from three places inside V1 today (`vision.py:194`, `:324`) |
| Every post-retry terminal trace | Are all three traces required by this round's instructions constructible? | Yes — transient@1→timeout@2 (`VISION_TIMEOUT` row, `{1,2}`), transient@1→permanent@2 (`VISION_PROVIDER_FAILURE`/`PERMANENT_RUNTIME_FAILURE` row, `{2}`), and transient@1→schema-invalid-or-policy-blocked@2 (both rows admit `{2}`) all appear as named rows in the V2 terminal-outcome matrix with a stated rationale each |
| Every post-retry terminal trace | Is any row broadened without justification? | No. `INPUT_NOT_VALIDATED` and `VISION_MODEL_UNAVAILABLE` are explicitly listed under "Rows deliberately not broadened" with a rationale each, and no row anywhere admits `attempt_number > 2` |
| Provenance applicability | Does the applicability table (`SUCCEEDED`/`PROHIBITED_CLAIM_DETECTED`/`VISION_SCHEMA_INVALID`/`VISION_MODEL_UNAVAILABLE`/`VISION_PROVIDER_FAILURE`/`VISION_TIMEOUT` = required, `INPUT_NOT_VALIDATED` = forbidden) still match the corrected terminal-outcome matrix's row set one-to-one? | Yes. The terminal-outcome matrix introduces no new `error_code` beyond the existing six plus the `PROFILE_NOT_RESOLVABLE` *detail* token (which stays under `INPUT_NOT_VALIDATED`, where provenance is already forbidden), so the applicability table needed no change |
| Digest proof | Does "V1 digest regression proof" claim a digest value is recorded in this dossier? | No. It explicitly states no value is pasted here and names the committed-golden-constant test as the sole authoritative check, correcting the ambiguous "record...and assert unchanged" wording this round found |
| Mislabeled-settled decisions | Was any open decision described as though it were already approved? | Yes, one, now fixed: D-7 previously read as a live choice between two catalog designs. The corrected design (R2-1) makes the "single shared catalog" alternative structurally impossible, not merely undesirable, so D-7 is now marked resolved-by-construction rather than left as a false open choice. D-4 and D-9 were under-scoped (they did not say they also gate `compute_profile` and `VisionProfileIdV2` membership as **blocking** items); both are now explicit |

### Carried-forward checks (Round 1)

| Check | Result |
|---|---|
| Did the dossier authorize Phase B by itself before the owner acted? | No. At this review's time, recording answers in this evidence note was not the governance act of approval. The owner subsequently approved the bounded B1–B5 scope in `TASK_APPROVAL.md` on 2026-09-01. |
| Does adding `PROFILE_NOT_RESOLVABLE` alter V1? | No. The token is added to the V2 detail enum only; V1's twelve tokens are unchanged |
| Does allowing `repair_attempted = true` on the V2 policy row contradict the frozen repair rule? | No. It records that a lossless unwrap happened; it does not permit any additional repair. It is listed as a deliberate V2 delta in D-6 |
| Does "Lightning L4 proposed" contradict "no provider selection"? | No. It is a development preflight location, explicitly not a production or Integration Sprint provider decision, and explicitly subject to D-3 |
| Does `NOT_APPLICABLE` for the trigger rate contradict "always report the metric"? | No. The metric is always named; its value under a fixture lexicon is `NOT_APPLICABLE`, which is a reported value, distinct from both `0` and omission |
| Does the V2 attempt-2 allowance weaken the retry limit? | No. `attempt_number ≤ 2` still caps at one retry; timeout is still non-retryable; only the *representability* of a post-retry outcome changed |
| Does the dossier claim any measurement? | No. Every Phase B number is future work. The only measurements cited are the Phase A test counts verified today and the GPU record from the P2-T2 report |
| Are any facts asserted that the repository does not contain? | No. Model licence, local VRAM feasibility, exact dependency versions, and the runtime's generation-parameter names are all explicitly marked unknown or to-be-recorded. `VisionProfileIdV2`/`compute_profile` are no longer in this category — they are owner **decisions**, not repository facts, and are now recorded as such, distinctly from the still-unknown items |

### Targeted Round-4 checks

| Focus | Check | Result |
|---|---|---|
| Decision completeness | Does every one of the ten open decisions now have a recorded answer, and does D-4/D-9's answer supply the exact closed values the dossier's own gate required (not just a directional preference)? | Yes. All ten rows in "Owner decisions register" carry a recorded answer; D-4/D-9 specifically supply `VisionProfileIdV2 = QWEN3_VL_8B_INSTRUCT_BF16_V1` and `compute_profile = Literal["GPU_BF16"]`, both single-value closed sets, satisfying "an exact closed enum recorded in a written amendment" |
| Naming consistency | Does the resolved `VisionProfileIdV2` member and `compute_profile` value follow this repository's existing naming conventions rather than an invented pattern? | Yes. `QWEN3_VL_8B_INSTRUCT_BF16_V1` follows the `<MODEL>_<VARIANT>_<PRECISION>_V<N>` pattern already used by `AsrProfileId.WHISPER_TURBO_INT8_AUTO_V1`; `GPU_BF16` follows the `GPU_<PRECISION>` pattern already used by `AsrProfileV1.compute_profile`'s `GPU_INT8_FLOAT16`/`GPU_FLOAT16` |
| Governance boundary | Does recording these decisions in this evidence note overstate itself as the approval? | No. The status line, the Round-4 section, and the self-review row above all state explicitly that this is not `approvals/TASK_APPROVAL.md`, and that file was not edited by this pass |
| Budget rule consistency | Does the one-hour soft cap contradict the mandatory B4 repeat-run requirement or the multi-stage B2–B4 scope? | No, by design: the cap is stated as covering B2–B4 **combined**, explicitly as a soft cap with a mandatory stop-and-reauthorize rule rather than a hard deadline, precisely because one hour may not be enough for preflight plus mapping study plus benchmark plus repeat run — the rule accepts that possibility rather than silently assuming the budget suffices |
| No unintended scope change | Did recording these ten decisions change any V1 behavior, any test, any dependency, or `approvals/TASK_APPROVAL.md`? | No. Every edit in this round is confined to this evidence note plus, where needed for consistency, `CONTEXT.md` and `evidence/README.md` |
