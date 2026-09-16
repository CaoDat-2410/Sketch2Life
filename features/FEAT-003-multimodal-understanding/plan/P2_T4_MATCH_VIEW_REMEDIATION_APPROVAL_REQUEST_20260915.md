# P2-T4 Vision match-view remediation approval request

- Status: **DECISIONS RECORDED 2026-09-15 — SUCCESSOR CONTRACT FREEZE APPROVED 2026-09-15 —
  INDEPENDENT ERRATUM REVIEW COMPLETE/PASS 2026-09-16 — RENEWED CORRECTED BINDINGS APPROVED —
  FOUR-FILE STATUS SYNCHRONIZATION APPROVED — REMEDIATION-IMPLEMENTATION APPROVAL NOT GRANTED**
- Request date: 2026-09-15
- Decisions-recorded date: 2026-09-15
- Owner: Person 2
- Feature: FEAT-003 Multimodal understanding, task P2-T4
- Analysis: `plan/P2_T4_MATCH_VIEW_REMEDIATION_PLAN.md`
- Audit verdict: **VERIFIED_DEFECT**
- Original G1 binding (unaffected, immutable): `P2T4.P2T4FusedResultV1@1.0`, freeze commit
  `18d0c33d35431ca96a76692a68c6b992098699e7`, freeze SHA-256
  `be96b32aa675b7b6e46eea30effb2dbb91c718dc68ba7ce36d4d627ad6058ee2`, package SHA-256
  `6821755722daf3bce622fe98eaf39124adb835c6854661143d79f48a943030d7`
- G2 approval record commit: `d9a13d2c51a16702c705795a3c7b497b61d945c0`
- Audited implementation checkpoint: `064ba62f32f1ffb964bc2208577eb0650b98e26a`
- Successor documents issued under this decision (docs-only, standalone; own internal status
  text as authored: `HOLD - NOT APPROVED`, a historical artifact not edited in place — see
  approval note below):
  - `plan/P2_T4_CONTRACT_FREEZE_REVISION_12.md`, normalized SHA-256
    `d592b135d2d8a90024d48d1b8335321660e8d7f089873e48687707c760e3d3e9`
  - `evidence/notes/P2_T4_IMPLEMENTATION_APPROVAL_PACKAGE_REVISION_16.md`, normalized SHA-256
    `ad886d261d2807bcc95264d05d6a385dc79cd2f0cad44e2b4f004531b8097d4f`
- **Successor contract-freeze approval ("G1 successor"): APPROVED**, 2026-09-15, bound to all
  four normalized SHA-256 identities above plus the two immutable predecessor digests (below),
  recorded in `approvals/TASK_APPROVAL.md` ("P2-T4 successor contract-freeze approval") and
  cross-cited in `CONTEXT.md`, `DECISIONS.md`, `plan/PLAN.md`, and
  `plan/P2_T4_FUSION_RESEARCH_PLAN.md`. This is a governance/freeze checkpoint only: the
  exact-seven-file remediation implementation remains **NOT APPROVED / NOT STARTED**, and
  integration/runtime/provider/model/GPU/Lightning/network/migration/production/live all remain
  **NOT APPROVED**. `P2T4.P2T4FusedResultV1@1.0` is unchanged, and predecessor revisions 11/15
  remain immutable history.
- **Digest-binding integrity defect (accepted 2026-09-16):** the normalized SHA-256 values that
  this document cites for freeze revisions 11/12 and package revisions 15/16 are legacy
  first-substring digests that bind only a prefix of each document. The owner accepted the finding
  and selected Option A (`approvals/TASK_APPROVAL.md`, 2026-09-16). The immutable erratum
  `plan/P2_T4_DIGEST_BINDING_ERRATUM_20260915.md` was independently reviewed **COMPLETE/PASS**,
  and its corrected normalized, raw-file, and Git identities received renewed **APPROVED** binding.
  The legacy values in this document are historical and non-canonical; the digest decision is
  **BINDING CORRECTION ONLY**. No implementation authority has been granted.
- Relocation note: this file was originally written at the gitignored path
  `evidence/notes/P2_T4_MATCH_VIEW_REMEDIATION_APPROVAL_REQUEST_20260915.md` (excluded by the
  repository's `evidence/notes/*` ignore rule). It has been relocated verbatim in substance to
  this publishable `plan/` path, updated only to record the decisions below and the successor
  documents they authorized; the ignored duplicate at the old path has been removed after this
  transfer was verified.

This document originally requested five owner decisions and a sequence of separate approvals.
The five decisions are now recorded (below, and authoritatively in `approvals/TASK_APPROVAL.md`),
the two standalone successor documents were issued, and **the successor contract freeze has since
been approved** (below). This history does not itself authorize evidence. The
remediation-implementation approval remains a separate, **NOT GRANTED** gate, and this is a
governance/freeze checkpoint only — it does not authorize touching the seven
remediation-implementation paths.

## 1. Finding

G1 freeze section 5.2 (`plan/P2_T4_CONTRACT_FREEZE_DRAFT.md:278`) says that "successful fusion
requires the declared v2 match view". However:

- Upstream `VisionResultEnvelopeV1.policy_match_view_version` accepts any non-empty string
  (`backend/src/sketch2life/contracts/schemas/vision.py:330`), even though the canonical token is
  `vision-policy-match-view-v2` (`:16`).
- The P2-T4 service checks only ASR admissibility and correlation
  (`backend/src/sketch2life/application/services/p2_t4_fusion.py:306-337`).
- The fixture manifest records "no Vision-side rejection"
  (`fixtures/p2-t4-fusion-v1/manifest-v1.json:30`).

A local reproduction confirmed the consequence. Schema-valid Vision successes carrying
`vision-policy-match-view-v1`, `unit-view`, or `vision_policy_match_view-v2` each return `FUSED`
through `validate_and_fuse` and through typed `fuse()`; the only output difference is the source
digest. G1 gives this requirement no pipeline placement and no rejection encoding, so a fix
needs a successor freeze.

## 2. Owner decisions (recorded 2026-09-15)

The following five decisions are recorded authoritatively in `approvals/TASK_APPROVAL.md`
(2026-09-15 P2-T4 match-view successor-decisions entry). This request document records them for
traceability from the original analysis; `approvals/TASK_APPROVAL.md` is the governing record if
the two ever appear to differ.

| ID | Decision | Selected value | What it means |
|---|---|---|---|
| MV-1 | Rejection semantics | **B** | Add closed field code `POLICY_MATCH_VIEW_VERSION` at `ADMISSIBILITY`. |
| MV-2 | Scope of the invariant | **S2** | Enforce only for `VisionUnderstandingSuccessV1`; a `VisionUnderstandingFailureV1` is not checked. |
| MV-3 | Token comparator | **T1** | Compare exactly against the upstream constant `VISION_POLICY_MATCH_VIEW_VERSION` (`vision-policy-match-view-v2`); the T4 policy literal and `fusion_policy_config_hash` are unchanged. |
| MV-4 | Contract-version disposition | **V2** | Keep `P2T4.P2T4FusedResultV1@1.0`; replace the outer rejection contract with `P2T4.P2T4FusionInputRejectionV2@2.0`, superseding V1 for every outer-boundary rejection — no mixed V1/V2 rejection union. |
| MV-5 | Successor artifact strategy | **Standalone** | Issue new standalone documents (freeze revision 12, package revision 16); never edit revision 11/15 in place. |

Note that MV-4's selection (**V2**) differs from this plan's own recommendation (V1, retain
identities). The owner is entitled to select differently from a recommendation; the plan's
section 6/7 comparison tables record the trade-offs of both options, and the successor documents
implement the owner's actual selection (V2), not the plan's recommendation.

The normative successor semantics that follow from these five decisions — restated exactly as
the owner specified when recording them — are:

1. After strict upstream validation, run the ASR duplicate-index admissibility invariant first.
2. For `VisionUnderstandingSuccessV1`, require
   `policy_match_view_version == VISION_POLICY_MATCH_VIEW_VERSION` exactly.
3. A mismatch returns:
   ```text
   contract_name=P2T4FusionInputRejectionV2
   contract_version=2.0
   status=REJECTED
   input_slot=VISION
   phase=ADMISSIBILITY
   code=INVALID_STRUCTURE
   expected_identity=P2.VisionUnderstandingResultV1@1.0
   observed_identity=P2.VisionUnderstandingResultV1@1.0
   observed_status=SUCCEEDED
   field_code=POLICY_MATCH_VIEW_VERSION
   ```
4. The observed token and raw input are never exposed.
5. `VisionUnderstandingFailureV1` does not receive this check.
6. Match-view admissibility precedes correlation equality and typed upstream-status handling
   (and follows the ASR duplicate-index invariant, since ASR is checked before Vision).
7. `P2T4FusionInputRejectionV2` supersedes V1 for every outer-boundary rejection; no code path
   may emit a mixed V1/V2 rejection union.
8. The fused-result contract remains `P2T4.P2T4FusedResultV1@1.0`, and all unrelated fusion
   semantics (matching, negation, confidence, primary selection, uncertainty) remain unchanged.

The full option comparison behind MV-1 through MV-4, including the trade-offs of the options not
selected, is in `plan/P2_T4_MATCH_VIEW_REMEDIATION_PLAN.md` sections 4-7. The exact successor-freeze
content implementing these eight rules is in
`plan/P2_T4_CONTRACT_FREEZE_REVISION_12.md` (sections 1.0, 2, 3, 4, 5.2, 6.5, 10) and
`evidence/notes/P2_T4_IMPLEMENTATION_APPROVAL_PACKAGE_REVISION_16.md`.

## 3. Successor-freeze strategy actually used (MV-5)

1. **Two new standalone documents were created** in this docs-only successor-issuance task:
   - `features/FEAT-003-multimodal-understanding/plan/P2_T4_CONTRACT_FREEZE_REVISION_12.md`
     (freeze revision 12, superseding revision 11);
   - `features/FEAT-003-multimodal-understanding/evidence/notes/P2_T4_IMPLEMENTATION_APPROVAL_PACKAGE_REVISION_16.md`
     (package revision 16, superseding revision 15).
2. **The approved revision-11 and revision-15 files remain untouched.** Byte-identity was
   verified against the immutable commit `18d0c33d35431ca96a76692a68c6b992098699e7` after this
   task's edits; both files diff empty against that commit.
3. **The outer rejection identity changed** to `P2T4.P2T4FusionInputRejectionV2@2.0` (MV-4); the
   fused-result identity `P2T4.P2T4FusedResultV1@1.0` did not change. The `field_code` allowlist
   gained exactly one member, `POLICY_MATCH_VIEW_VERSION`.
4. **The exact invariant** `For VisionUnderstandingSuccessV1, policy_match_view_version MUST
   equal "vision-policy-match-view-v2" exactly` was added at the `ADMISSIBILITY` stage, after the
   ASR invariant and before correlation and typed status (freeze revision 12, section 3.3).
5. **The exact rejection form** is defined in freeze revision 12, section 4, and repeated in
   section 2 of this document.
6. **Digests were computed** with the existing normalization algorithm (freeze revision 11
   section 10.1 / package revision 15 section 7), reproduced independently twice with two
   differently coded implementations, and cross-checked against the already-approved revision
   11/15 digest values to confirm the algorithm itself was reproduced correctly. The binding
   records use `review_base_commit` `064ba62f32f1ffb964bc2208577eb0650b98e26a` and
   `future_source_commit` `UNKNOWN_UNTIL_REVIEW_APPROVED_COMMITTED`.
7. **The supersession** of revision 11 and revision 15 is recorded in each successor's section 1
   and revision history, including why the predecessors were never consumed (no G7 evidence,
   consumer, adoption, runtime, or P2-T5 use exists).

## 4. Exact remediation-implementation paths (unchanged; already exist)

The narrow remediation is limited to exactly these seven existing G2 paths, which already hold
the G2-approved offline-core implementation as of checkpoint `064ba62`:

1. `backend/src/sketch2life/contracts/schemas/p2_t4_fusion.py`
2. `backend/src/sketch2life/application/services/p2_t4_fusion.py`
3. `backend/tests/contract/test_p2_t4_contract.py`
4. `backend/tests/unit/test_p2_t4_fusion.py`
5. `features/FEAT-003-multimodal-understanding/fixtures/p2-t4-fusion-v1/manifest-v1.json`
6. `features/FEAT-003-multimodal-understanding/fixtures/p2-t4-fusion-v1/cases-v1.json`
7. `features/FEAT-003-multimodal-understanding/fixtures/p2-t4-fusion-v1/expected-v1.json`

Freeze revision 12 section 10.2 lists the per-file changes. Because MV-4 selected V2 (not V1),
the remediation's fixture impact is larger than a pure addition: all 16 existing `REJECTED`
entries in `expected-v1.json` currently carry `P2T4FusionInputRejectionV1`/`1.0` and will change
to `P2T4FusionInputRejectionV2`/`2.0`, changing each of those 16 entries' canonical bytes and
`canonical_sha256`, even for the 15 unrelated to the match-view fix itself. The 26 non-rejected
(`FUSED`/`UPSTREAM_FAILURE`) entries are unaffected and must remain byte-identical. The following
remain excluded from the remediation:

- the upstream `vision.py` and `vision_v2.py` contracts, the content-policy port and
  implementations, and the adapters;
- FEAT-018 and FEAT-020 code, the B0 mapping, and other fixtures;
- any new helper, evidence, or generated path;
- any import from `sketch2life.infrastructure` in the service.

## 5. Required review and approval order (updated: steps 1-5c are now complete)

Each remaining step still requires its own explicit owner instruction. No step implies approval
of a later step.

1. ~~Owner review of `plan/P2_T4_MATCH_VIEW_REMEDIATION_PLAN.md` and this request.~~ **Complete.**
2. ~~Owner decisions MV-1 through MV-5.~~ **Complete — recorded 2026-09-15 in
   `approvals/TASK_APPROVAL.md`** (section 2 above).
3. ~~Successor issuance: create the two standalone successor documents and compute their
   normalized digests.~~ **Complete** (freeze revision 12, package revision 16).
4. ~~Independent successor-freeze review~~ covering technical/contract consistency and
   governance/scope, including digest recomputation, the byte-immutability of revisions 11 and
   15, and the absence of implementation changes. **Complete** — performed as part of the
   successor-freeze approval task.
5. ~~Owner freeze approval (a new "G1 successor" gate)~~ against the exact successor commit,
   normalized freeze and package digests, and contract identity. **Complete — OWNER APPROVED
   2026-09-15**, recorded in `approvals/TASK_APPROVAL.md` ("P2-T4 successor contract-freeze
   approval").
5a. **Independent erratum review** of the immutable digest-binding erratum. **COMPLETE / PASS**.
5b. **Renewed corrected binding approval** against the corrected identities. **COMPLETE / APPROVED**.
    The normalized digests cited in the original approval are legacy first-substring values that
    bind only a prefix of each document. The owner accepted the defect and selected Option A; the
    corrected identities received renewed approval. Successor semantics remain **PREVIOUSLY
    APPROVED / UNCHANGED**, and the decision is **BINDING CORRECTION ONLY**.
5c. **Four-file renewed-binding status synchronization.** **APPROVED / COMPLETE** for this task at
   checkpoint `23992c54c8b19c0eb0a707ec0934599bddb97560`; documentation-only and no implementation
   authority.
6. **Separate remediation-implementation approval** naming exactly the seven paths in section 4.
   It must state that it is separate from the successor freeze and does not authorize evidence,
   runtime, integration, or live execution. **NOT GRANTED.**
7. **Remediation implementation** within the seven paths only. **NOT APPROVED / NOT STARTED.**
8. **Independent diff, contract, privacy, and governance review** of the candidate tree, followed
   by a separate remediation commit. **NOT STARTED** (future remediation review; G6-G9 remain
   **PAUSED**).
9. **Restart G6** on that remediation commit (focused and full tests, Ruff, mypy, validators with
   architecture under Policy B, CPython 3.13.x canonicalization), then G7 evidence (only under a
   separately named evidence authorization, binding the remediation commit and successor
   digests), G8 review, and G9 completion. **PAUSED / NOT STARTED**.

## 6. Gate state (current)

| Gate | State |
|---|---|
| G1 (original) | Approved; revision 11/15 remain immutable history and their digests verify unchanged. |
| G2 | Approved; the scope is used up by `064ba62` and does not cover remediation. |
| G3-G5 | The checkpoint `064ba62` exists (exactly seven paths, parent `d9a13d2`). |
| Successor-freeze decisions (MV-1..MV-5) | **Recorded** in `approvals/TASK_APPROVAL.md`, 2026-09-15. |
| Successor documents (freeze revision 12 / package revision 16) | **Issued.** Own internal status text (as authored): `HOLD - NOT APPROVED` — a historical artifact, not the current gate state (not edited in place). |
| Successor-freeze approval ("G1 successor") | **APPROVED** — `approvals/TASK_APPROVAL.md`, "P2-T4 successor contract-freeze approval", 2026-09-15, bound to all four normalized SHA-256 identities. Governance/freeze checkpoint only. |
| Digest-binding integrity defect | **Accepted** 2026-09-16 (`approvals/TASK_APPROVAL.md`); Option A selected. The four normalized identities cited in the row above are legacy first-substring digests and are historical and non-canonical. |
| Digest-binding erratum (`plan/P2_T4_DIGEST_BINDING_ERRATUM_20260915.md`) | **ISSUED / COMPLETE**; independent erratum review **COMPLETE/PASS**. The erratum remains byte-immutable. |
| Renewed corrected binding approval | **COMPLETE / APPROVED**; successor semantics are **PREVIOUSLY APPROVED / UNCHANGED** and the digest decision is **BINDING CORRECTION ONLY**. |
| Four-file renewed-binding status synchronization | **APPROVED / COMPLETE** at checkpoint `23992c54c8b19c0eb0a707ec0934599bddb97560`; documentation-only. |
| Remediation-implementation approval | **NOT GRANTED**; the seven-file remediation is **NOT APPROVED / NOT STARTED**. |
| G6-G9 | **PAUSED** pending the separate remediation-implementation approval, implementation, review, and checkpoint commit. |
| Runtime, integration, provider, model, GPU, Lightning, network, migration, production, live | **NOT APPROVED.** |
| `P2T4.P2T4FusedResultV1@1.0` | **Unchanged.** |
| Predecessor revisions 11/15 | Remain immutable history. |

## 7. Not authorized by the original request-writing task (historical)

This lists what the docs-only task that originally authored this request was not authorized to
do — a historical record of that task's boundaries, not the current gate state (see section 6
above for current state; the successor-freeze approval recorded there was granted by a later,
separate task):

- Editing the approved freeze (revision 11) or package (revision 15) in place.
- Any change to the seven remediation-implementation paths, or any other code, test, or fixture.
- Granting the successor-freeze approval or the remediation-implementation approval.
- G6 verification, G7 evidence, or any evidence artifact.
- Commits, pushes, branches, pull requests, runtime, provider, model, GPU, Lightning, network,
  migration, integration, P2-T5, or production work.

## 8. Owner response requested (updated)

The five decisions requested by the original version of this document are now recorded (section
2), and the owner has since separately approved the successor contract freeze (section 6). The
remaining owner action is the separate remediation-implementation approval (step 6 in section 5
above), naming exactly the seven paths in section 4; it must state that it is separate from the
successor freeze and does not authorize evidence, runtime, integration, or live execution.

Since then (2026-09-16), the owner accepted a digest-binding integrity defect in the four recorded
normalized identities and selected Option A. The immutable erratum was independently reviewed
**COMPLETE/PASS**, and renewed **APPROVED** binding was recorded for the corrected identities. The
successor semantics remain **PREVIOUSLY APPROVED / UNCHANGED**, and the decision is **BINDING
CORRECTION ONLY**. The four-file status synchronization is **APPROVED / COMPLETE** at checkpoint
`23992c54c8b19c0eb0a707ec0934599bddb97560`. The remediation-implementation approval remains **NOT
GRANTED**, and the remediation remains **NOT APPROVED / NOT STARTED**; it must not use the legacy
digests as the sole artifact identity.

## P2-T4 renewed digest-binding approval after independent erratum review - 2026-09-16

- The independent erratum review is **PASS**. The four corrected normalized and raw-file SHA-256
  hashes were reproduced independently; their source paths, source commits, Git blob IDs, byte/line
  counts, and binding-table/heading ranges were verified against erratum sections 4.1-4.4 and 5.
  The immutable erratum raw-file SHA-256 `8975d94b0d9be8e78935b66e1e851493c1cff5b2f1b83cdf49acfe7f9929276e`
  and Git blob ID `4b7ed999fed45e176d57c395e63fe62e8f12accc` were verified.
- The owner renewed approval exactly as follows:

  > I approve the P2-T4 renewed digest-binding decision exactly as written above.

- The previously approved successor semantics include P2T4.P2T4FusedResultV1@1.0 and P2T4.P2T4FusionInputRejectionV2@2.0; they remain unchanged, with no semantic reapproval.
- No implementation authority is granted by this binding approval.
- Renewed corrected artifact bindings are **APPROVED** against erratum sections 4.1-4.4. The renewed
  approval binds the corrected normalized/raw/blob/source/path identity tuples recorded in erratum
  section 4. The legacy first-substring digests are historical, non-canonical, and incomplete. The
  original freeze/package artifacts and the issued erratum remain byte-immutable; the erratum was
  not edited.
- This decision corrects bindings only. The successor semantics previously approved remain
  unchanged, with no semantic reapproval. The exact governance checkpoint allowlist is the six
  existing governance documents plus the immutable erratum. Separately, the exact seven-path
  remediation allowlist from `064ba62f32f1ffb964bc2208577eb0650b98e26a` remains unchanged, and none
  of those seven remediation files was modified in this checkpoint.
- The seven-file remediation is **NOT APPROVED / NOT STARTED**. G6-G9 remain **PAUSED**.
  Integration, runtime, provider/model, GPU, Lightning, network, migration, production, and live
  execution remain **NOT APPROVED**.
- No future checkpoint commit SHA is written into tracked files. The executor will report the
  resulting local governance commit SHA in the final handoff. This renewal record is superseded for
  active status by the four-file synchronization record below; earlier records and the immutable
  erratum preserve the historical issuance state.

## P2-T4 four-file renewed-binding status synchronization - 2026-09-16

- **Current state:** erratum issued **COMPLETE**; independent erratum review **COMPLETE/PASS**;
  renewed corrected binding approval **COMPLETE/APPROVED**; successor semantics **PREVIOUSLY
  APPROVED / UNCHANGED**; digest decision **BINDING CORRECTION ONLY**; four-file status
  synchronization **APPROVED / COMPLETE** at checkpoint
  `23992c54c8b19c0eb0a707ec0934599bddb97560`.
- Remediation-implementation approval is **NOT GRANTED**; the seven-file remediation is **NOT
  APPROVED / NOT STARTED**. G6-G9 remain **PAUSED**.
- Integration, runtime, provider/model, GPU, Lightning, network, migration, production, and live
  execution remain **NOT APPROVED**. The next step is a separately approved remediation task; this
  record grants no implementation, evidence, or execution authority.
