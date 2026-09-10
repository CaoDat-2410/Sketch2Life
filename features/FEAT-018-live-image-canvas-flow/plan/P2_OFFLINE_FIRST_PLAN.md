# FEAT-018 P2 — Proposed offline-first implementation plan

- Revision: P2-R1, 2026-09-09
- Status: PARTIALLY APPROVED; the isolated P2-T1 image-admission D2 sub-slice is reviewed and
  accepted. D3, the remainder of O1, O2–O5 and all integration remain unapproved.
- Parent: FEAT-018 revision 2. This proposal does not replace the approved P1 slice or freeze shared contracts.
- Research: round-1 working report retained locally; not a canonical public record.
- Owner: Person 2. Any FEAT-003 edit or connection requires user review first.

## Outcome and boundaries

Deliver a standalone, fixture-tested image-understanding handoff component. Inputs are bounded source references and injected observations; output is either an auditable proposal, a confirmed anchor set after explicit confirmation, or a typed blocked/failure result. P1 owns objective/template/activity selection. Gate A UI, authentication, persistent session state, upload/picker and E2E remain shared work.

Offline acceptance and full P2 acceptance are separate milestones. Full acceptance retains the original plan's real JPG/PNG, exact backend model, optional narration, live evidence and integration checks.

## C0 — Review and freeze before implementation

1. Resolve R1 in the research report for both Vision and ASR. Recommended future source: preserve research Vision V2 and its provenance through a reviewed adapter. Do not emit a second incompatible Vision V1. Exact new integration names/versions and migration consumers must be recorded in the registry before code.
2. Review R2/R3: additive image-only validation boundary, finite byte/pixel/dimension/aspect/output limits, decode policy and original/working-copy references. Values must be agreed before inspector implementation; existing thresholds are starting references, not camera-quality evidence.
3. Review R4: candidates preserve nullable confidence. Existing P1 V1 handoff blocks unknown confidence; a nullable P1 successor is separately reviewed. No guessed default or confidence=1 from adult confirmation.
4. Review R5/R6: conservative taxonomy mapping and a finite versioned fixture vocabulary. Vocabulary coverage is not a model quality score.
5. Review R7/R11: one RawUnderstanding schema owner; define aggregation versus future semantic fusion. Qualify task IDs as FEAT018-P2-*.
6. Review R8/R9: one confirmed-anchor contract authority and explicit Gate A input. Shared integration must separately assign runtime ownership.

Deliverables: registry entries, schema sketches finalized as JSON Schema in the approved implementation slice, producer/consumer matrix and positive/negative migration fixtures. No approval checkbox is preselected by this proposal.

## Proposed data flow

```text
Source refs -> image/optional-audio validation -> injected observation results
            -> RawUnderstanding proposal -> unconfirmed anchor candidates
            -> explicit Gate A confirmation/correction input
            -> confirmed SemanticAnchorSet or typed blocked handoff -> P1
```

RawUnderstanding proposal sketch (all fields/version/status enums pending C0):

- Envelope identity/version, proposal ID/version, source references and validation-policy provenance.
- Separate Vision and ASR result references with exact source schema identity/version/digest; preserve model revision/config/catalog/adapter provenance where supplied, and truthful fixture provenance otherwise.
- Explicit modality availability and execution status: absent narration is not an ASR success with empty transcript. Present-but-invalid audio is distinguishable and requires recapture or an explicit user removal before continuing image-only.
- Claims with stable IDs, modality, source observation/segment references, structured labels, nullable confidence and uncertainty; no age/readiness/eligibility or psychological inference.
- Conflicts retain both sides and their references. The first slice aggregates explicit evidence and fixture conflicts; automatic semantic contradiction detection is deferred.
- Gate A required; failures contain bounded typed codes. Failed providers cannot yield successful claims.

Candidate sketch: candidate ID, proposed kind, source label, optional canonical label, mapping policy/vocabulary version, supporting claim IDs, source identity, nullable model confidence, and mapping status. Candidates are not instantiated as `SemanticAnchorV1`, whose validator already requires confirmation.

Confirmation input sketch: proposal ID/version, source hash, confirmed claim IDs, selected primary candidate, actor reference/role, meaning version, optional correction with its own provenance. Offline fixtures supply these explicitly; live values come from shared Gate A. A new adult claim must have a distinct correction record, never be falsely attributed to Vision.

## O1 — Source validation and missing narration

Progress (2026-09-10): the isolated bounded image-admission D2 subset is reviewed and accepted.
It covers snapshot acquisition, decode admission, provenance and deterministic fixtures only.
Image-quality scoring, missing-narration composition and D3 performance/native-memory evaluation
remain outstanding, so O1 and P2-T1 are not complete.

- Maps to FEAT018-P2-T1 and the missing-audio part of T3.
- Input: local synthetic source refs, optional audio ref, approved limits/policy, injected inspector.
- Output: bounded validation decision/reasons, original hash and separate derived hash if needed, explicit missing narration.
- Work: additive inspector for JPG/PNG; size checks before bulk read/decode; bounded hashing; orientation derivative without original overwrite; MIME agreement; conservative image heuristics. Repeated hashes are provenance/duplicate signals, not automatic rejection unless policy says so.
- Acceptance: valid JPG/PNG passes; corrupt, unsupported, too-large, too-dark, blur/crop-risk and orientation cases are covered. Rejected media triggers zero provider calls. Original bytes/hash stay unchanged. Missing audio triggers zero ASR calls and can permit a valid image-only proposal. Supplied invalid audio is not silently dropped.
- Stop: undefined limits/policy, source change between validation and use, unbounded decode or a need to modify FEAT-003 validation.

## O2 — Raw proposal and injected adapter boundaries

- Maps to offline FEAT018-P2-T2/T3 and FEAT018-P2-E1.
- Input: validation result plus synthetic typed Vision/ASR success/failure data.
- Output: schema-valid raw proposal or typed failure with source/model-or-fixture provenance.
- Work: one proposal schema, explicit modality states, stable claim references, allowed fields, bounded text/output and failure mapping. Use injected fakes for execution; producer-specific FEAT-003 binding is deferred to O5 review.
- Acceptance: image-only, audio-only contract diagnostic, both-modality, failed-provider, malformed, extra-field, missing-provenance and source-mismatch cases. Audio-only diagnostics do not expand the image-required FEAT-018 product flow. No fabricated transcript, aggregate confidence or model provenance. Unsupported schema lineage fails closed.
- Stop: undeclared source schema, new semantic fusion behavior, hidden retry, or changes to FEAT-003 schema/prompt/adapter.

## O3 — Candidates and confirmed handoff

- Maps to FEAT018-P2-E2/E3/E4 and mapping cases in T4.
- Input: raw proposal, reviewed mapping/vocabulary policy, optional explicit fixture confirmation.
- Output: candidates awaiting confirmation, or current compatible confirmed anchor set, or typed blocked handoff.
- Work: map supported evidence; retain unknown/ambiguous/conflicting cases; reject dangling/duplicate claim IDs and source mismatches; verify confirmation binds to exact proposal/source/version. Validate all selected anchors. Primary selection comes from the reviewed confirmation/selection protocol, not list order.
- Acceptance: supported entity/action cases; unsupported relation/theme/region cases remain evidence or blocked; no invented feature/story/geometry. Unknown vocabulary is typed. Unconfirmed, stale, wrong-source and invalid-reference inputs cannot reach P1. Null confidence blocks current P1 V1; numeric synthetic fixture proves compatible handoff. Corrections preserve prior observations and create a new version/provenance.
- Stop: required P1 contract change, missing adult identity/version protocol or unsupported source claim.

## O4 — Pilot diagnostics and offline completion

- Maps to offline FEAT018-P2-T4/T5 and E3.
- Input: approved synthetic fixtures tied to all 20 golden pilot IDs and the agreed contracts.
- Output: feature-local compatibility report with pass/blocked outcomes and coverage manifest.
- Acceptance: each pilot has exact, ambiguous, no-match, image/audio conflict, low-or-unknown-confidence and adult-correction diagnostic cases. Expected blocked outcomes count as correct behavior; no forcing every activity to match every drawing. Keep 100-MVP catalog validation with P1; preserve 20-golden pilot scope.
- Evidence: schema/negative-case results, zero-model-call counts on rejections, source integrity, correction and fixture compatibility. Model latency/quality and live p50/p95 remain NOT_MEASURED. Report test timings separately if useful.
- Tests after code approval: focused new unit/contract tests, relevant existing media/vision/ASR/P1 regressions, schema compatibility and repository validators. No benchmark execution is needed for these tests.
- Offline exit: O1–O4 acceptance and relevant tests pass; review records and evidence index updated. Mark only the approved offline slice complete.

## O5 — Later FEAT-003 connection and live completion

This stage requires user review of every producer connection, actual Phase 8 safe results, model quality/safety readiness, source contracts and explicit compute scope. It does not tune or rescore FEAT-003 evidence.

Implement the approved producer-specific adapters and migration fixtures; confirm no loss of claim IDs, nullable values, source derivation, exact model/config provenance or failure semantics. Shared integration supplies real image intake, Gate A, authenticated actor, session/idempotency behavior and device wiring. Run the approved non-sensitive live smoke only then.

Full P2 exit additionally needs exact-model live evidence, optional narration behavior, malformed/prohibited/timeout/provider failure evidence, 20-pilot diagnostics, source preservation/redaction and the shared mobile credential scan. Report live sample count beside p50/p95; one smoke is not a performance benchmark. Fixture rollback remains available.

## Change-impact gate

Before any later implementation step, enumerate touched files. If it changes FEAT-003 contracts, validation, ASR/Qwen adapters, prompts/profiles, benchmark fixtures/runners/scoring/evidence, or wires them into FEAT-018, stop that dependency and present the exact diff/proposal for user review. Independent approved offline work may continue.

Proposed new code belongs in backend contract/application/infrastructure layers according to responsibility, with FEAT-018-specific tests and evidence; never place provider logic in domain or copy research contracts under the same public name. Concrete file paths are finalized with C0 so a duplicate schema family is not accidentally introduced.
