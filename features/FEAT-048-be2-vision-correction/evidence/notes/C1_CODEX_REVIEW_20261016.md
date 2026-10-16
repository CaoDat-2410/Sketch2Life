# BE2-02 C1 — independent Codex review, 2026-10-16

**Verdict: NEEDS_REVISION.** Six blocking findings: 2 P1 and 4 P2. One P3 note is
non-blocking. This reviews the approved C1_COMPONENT_OFFLINE implementation; it does
not extend the card into real providers, persistence or owner integration.

## Identity and evidence

- Worktree: `.worktrees/be2-02-vision-correction`; branch
  `feature/be2-02-vision-correction`.
- HEAD/base: `6dcc57ee0b3d053f071c8c92e72aaaee2e98d899`; implementation uncommitted.
- Approved plan: `plan/PLAN_REV1_APPROVED.md`, SHA256
  `f4733c88797edbcce225ecd63700634f929ca75789362c7f3a58a2b57f19df30`.
- Reviewer: Codex root plus three delegated reviewers of service, domain/contracts,
  and bridge/API. Delegation is within the same Codex review; it is not independent
  owner sign-off or a different-model audit.
- Existing focused C1 suite independently rerun: **174 passed, 1 skipped** (Pillow
  absent). JUnit: `evidence/local/codex-review-20261016/focused-junit.xml`.
- Root reran the six service regression probes: **6 failed, 3 deselected**, pytest
  exit 1. These are intentional before-fix invariant assertions, not a passing suite.
- Root reran bridge and domain fact probes. Their exit 0 means the measurements
  completed; the JSON contains the defects below and does not mean C1 passed.
- Commands, reviewed source hashes, receipt hashes and verification results are in
  `evidence/metrics/C1_CODEX_REVIEW_20261016.json`. Raw probes/logs stay ignored under
  `evidence/local/codex-review-20261016/`.
- After recording review: harness, repository security, architecture, skeleton and
  `git diff --check` all exit 0. Security scanned 3,089 publishable files. These
  structural checks do not negate the reproduced behavioral findings.

Line numbers below apply to this reviewed source snapshot. No implementation,
tests, approved plan, approval, legacy adapter or other worktree was changed by review.

## C1-R01 — P1: replay bypasses current observation applicability

**Location:** `backend/src/sketch2life/application/services/vision_analysis.py:280–281`
and `_observation_replay` at 416–424.

After accepting an observation, change the current context, replace the render hash,
or revoke contributor consent, keeping the running job/attempt unchanged. The next
`observe` finds the existing analysis and returns before resolving current eligibility
or source. All three probes return `accepted`, `replayed=True`, `authoritative=True`,
with no second provider call. Stored acceptance is being treated as current authority.

**Required correction:** preserve the original analysis/observation identity and
deduplication, but evaluate current source/context/eligibility before returning replay
authority. Apply this to both the early replay and raced-winner path. A stale or
revoked result must not be represented as currently authoritative. Do not change the
separate accepted correction-receipt replay rule (current disclosure check followed
by the original receipt, even with old If-Match).

**Basis:** approved plan §3.2–3.3, V05/V06; actual approval requires changed context,
source or revoked consent not to produce authoritative results.

**Reproduction:** `agent-service/test_service_probes.py`, parameterized
`test_observation_replay_is_not_current_authority_after_owner_change`; root output
`root-service-probes.log` / `root-service-junit.xml`.

## C1-R02 — P1: acceptance after provider omits session and age eligibility

**Location:** `backend/src/sketch2life/application/services/vision_analysis.py:352–357`.

The post-provider gate checks consent/purpose but omits the rest of `eligibility_code`.
In the provider callback, end the session or change the contributor's authoritative
age to unknown/156 months without a context revision bump. Each case still stores
an accepted authoritative analysis at revision 1. The current context port exposes
these facts independently, so a revision comparison does not replace their checks.

**Required correction:** run the complete current eligibility gate before acceptance,
including active session and known eligible audience ages, with safe typed outcomes
and no accepted storage when ineligible. Preserve source/context-change stale handling
and existing consent/purpose rejection behavior.

**Basis:** approved plan §3.2, V05/V15; authoritative age range is 36–155 completed months.

**Reproduction:** `agent-service/test_service_probes.py`, parameterized
`test_full_eligibility_is_rechecked_after_provider`; the three root assertions fail.

## C1-R03 — P2: foundation job ownership scope is discarded

**Location:** `backend/src/sketch2life/infrastructure/vision_analysis/job_lineage.py:24–34`;
`domain/vision_analysis.py` `JobLineageView` and `check_lineage`.

The adapter retains organization/request/attempt fields but drops foundation
`JobScope.session_id`, `subject_refs`, `purpose_code` and `target_id`. A valid running
BE2-01 job with wrong values for all four, but matching organization, request ref,
revision, input hash and attempt, still invokes the provider and creates an accepted
analysis for the assistance pin's different scope. Current positive adapter tests
already use the expected matching values, but no comparison enforces them.

**Required correction:** carry the available ownership fields into the read-only
lineage view and compare them against the trusted assistance scope using an explicit
C1 mapping. Test each mismatch separately, plus the matching positive case. Reject
before provider/storage. Keep foundation code and its repository state unchanged;
do not invent BE1 class/canvas fields absent from the job contract.

**Basis:** approved plan §3.1, V05/V07 and actual approval's job/attempt guarantee.

**Reproduction:** `agent-bridge/probe_bridge_api.py`, final foundation-job case;
root output `root-bridge-results.json`: `provider_calls=1`, disposition `accepted`.

## C1-R04 — P2: accepted provider output can break CMD-34 after commit

**Location:** `backend/src/sketch2life/infrastructure/vision_analysis/legacy_v2.py:264–271`;
stricter output DTO constraints in `contracts/schemas/analysis_results.py`.

The bridge checks entity ShortText labels but not the complete mapped candidate.
Two schema-valid legacy V2 responses demonstrate the gap: a 121-character entity
observation ID, or 257 entities. Both are stored as accepted. Their DATA-22/record
projection then fails `observation_ref` length or `object_candidates` max 256.
Teacher CMD-34 returns **HTTP 500 after committing** one correction, receipt and
invalidation at revision 2. Identical replay also returns 500.

**Required correction:** validate all relevant mapped contract constraints before
acceptance/persistence, including references, candidate/uncertainty collection bounds
and compatible text shapes. Return a safe typed malformed-output outcome without
storing an accepted analysis. Do not truncate or silently alter the original result,
and do not merely catch a serialization error after commit. Keep dependency direction
inward; domain/application must not import outward DTO/infrastructure modules.

**Basis:** V01/V12/V13 and approved §5 safe handling of malformed outputs.

**Reproduction:** `agent-bridge/probe_bridge_api.py`; root `root-bridge-results.json`
includes both 500s, replay 500s, and persisted counts. The domain reviewer also used
an actual offline bridge to reproduce the 257-entity candidate rejection.

## C1-R05 — P2: valid correction history outgrows its own contract

**Location:** `backend/src/sketch2life/contracts/schemas/analysis_results.py:375`;
`application/services/vision_analysis.py:527–546` accepts an unbounded history.

Submit 257 valid Teacher corrections with unique keys and successive correct CAS
revisions. All are accepted, leaving revision 258 and 257 immutable corrections.
`analysis_record` then returns a record that fails `AnalysisRecordV1` because its
history is capped at 256. This is a supported command path, not corrupted storage.

**Required correction:** reconcile the accepted mutation history and output contract
within the C1 candidate design. Preserve all history and original receipts. Prefer a
small compatible schema/projection correction; document the chosen candidate policy.
Do not silently truncate history, add an arbitrary pedagogical command limit, or
build a generic pagination/storage platform to resolve this component mismatch.

**Basis:** D01/D02, V01/V04/V16 and approval's requirement to retain the whole history.

**Reproduction:** `agent-domain/domain_probes.py`; root `root-domain-results.json`:
257 accepted corrections, revision 258, `too_long` at `corrections`.

## C1-R06 — P2: emitted provider-result evidence has no retained artifact

**Location:** `backend/src/sketch2life/infrastructure/vision_analysis/legacy_v2.py:190–211`;
`application/services/vision_analysis.py:845–846`.

The bridge hashes the full typed `VisionUnderstandingSuccessV2` and returns only
mapped observations plus selected provenance/moderation. The full result is discarded.
The projection emits `provider_result.ref = result:<analysis_id>`, but the repository
stores no corresponding full result or resolvable artifact. For example, the original
correlation ID is lost from the persisted record. Consumers cannot resolve the emitted
reference to verify its hash or reconstruct the whole typed original.

**Required correction:** retain the canonical full typed provider result through a
narrow immutable component record/reference, with hash verification and an explicit
trusted resolution path. Commit it consistently with the accepted/stale observation;
failed writes must not leave a published dangling ref. Keep raw content internal and
unavailable to Child. An in-memory implementation is sufficient for C1; no DB/object
store/provider integration is required.

**Basis:** approved DATA-22 evidence/provenance rationale, D09's preservation of the
whole original result, V03/V13/V16 and project provenance rules.

**Reproduction:** `agent-domain/domain_probes.py` records emitted ref and stored fields;
static inspection of the provider outcome and repository port confirms no full-result
payload or resolver. `agent-domain/r06_full_provider_result_probe.py` uses the actual
offline bridge; the full typed-result hash matches the emitted hash while correlation
is lost from persisted state and no full-result resolver exists. Root reran it in
`root-full-result-proof.json`.

## N01 — P3, non-blocking: body cap is checked after buffering

`interfaces/http/routers/analysis_corrections.py:70–72` awaits the entire body before
checking 32 KiB. An authenticated chunked upload can exceed the cap while the handler
keeps receiving. `agent-bridge/probe_stream_limit.py` demonstrates an additional
receive after 40 KB. Impact is currently limited to the isolated fixture app. Record
this limitation; it is not an extra required fix batch in this review.

## Limits and disposition

- The correction TOCTOU probe and mutated job input-hash probe are retained as
  **qualified residual candidates**, not promoted findings: real owner fences are
  explicitly deferred, and foundation input hash is intended to be immutable.
- Shallow runtime dataclass typing, hash-coverage suggestions and nested legacy DTO
  coercion observations are not separate closure blockers in this review.
- Legacy F-01 remains a pre-existing contained defect. Pillow-dependent checks remain
  NOT_RUN. Neither should be represented as a newly introduced C1 defect.
- Real provider quality, typed provider context, real BE1/BE2-03 integration, SQL,
  delivery and live composition remain outside C1. BE2-01 stays WAITING_STUDIO.
- Fix R01–R06, add meaningful regression coverage and preserve before/after evidence,
  update affected handoff examples/docs, rerun appropriate checks, then stop for Codex
  re-review. No commit/push/merge/deploy; no full-card DONE.
