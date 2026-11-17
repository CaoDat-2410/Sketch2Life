# BE2-02 C1 — Codex re-review of R01–R06, 2026-10-16

**Verdict: NEEDS_REVISION — C1-R04 remains OPEN (P2).** R01/R02/R03/R05/R06 are
**CLOSED_C1_COMPONENT_SCOPE**. This supersedes the prior all-open review disposition,
without changing either historical review or executor report. Full BE2-02 remains
IN_PROGRESS/NOT_DONE. No code/test/approval/approved-plan changes by this review.

## Reviewed snapshot and actual checks

- Worktree `.worktrees/be2-02-vision-correction`, branch
  `feature/be2-02-vision-correction`, HEAD/base `6dcc57ee0b3d053f071c8c92e72aaaee2e98d899`.
- All 19 source/test hashes match Claude's `C1_REVIEW_FIX_CHECKS_20261016.json`.
  Approval and approved plan SHA256 match their recorded values; staged paths 0.
- Existing Python 3.12.10; imports explicitly pinned to this worktree. Offline only,
  no installs, network/model/provider/service/Studio runs.
- Root reran the eight-file focused suite: **213 passed, 1 skipped**, 0 failures/errors.
  The Pillow-dependent production-route walk remains NOT_RUN.
- Root reran the exact six previously failing service probes: **6 passed**, 3 deselected.
- Root reran two selected legacy test modules: **56 passed**. This is a subset, not
  an independent rerun of Claude's broader 233-test legacy or 337-test foundation suites.
- Three delegated Codex reviewers examined service, domain/lineage/contracts and
  bridge/result retention. Their overlapping test counts must not be added to the
  root suite count. This is one Codex review, not owner or different-model sign-off.
- Exact source/probe/JUnit hashes and final structural checks:
  `evidence/metrics/C1_CODEX_REREVIEW_20261016.json`.
- Post-documentation harness, repository security (3,095 publishable files),
  architecture and `git diff --check` all exit 0. These checks do not close R04.
- Raw receipts: ignored `evidence/local/codex-rereview-20261016/`.

## Finding disposition

| ID | C1 disposition | Independent evidence |
|---|---|---|
| C1-R01 | CLOSED_C1_COMPONENT_SCOPE | Shared early/raced replay gate checks current eligibility/context/source; all original replay probes pass. No second call or original-record rewrite; accepted CMD-34 receipt semantics preserved. |
| C1-R02 | CLOSED_C1_COMPONENT_SCOPE | Complete eligibility gate now runs after provider execution. Session/unknown/out-of-range age/group failures reject without storage; valid 36/155 boundaries pass. |
| C1-R03 | CLOSED_C1_COMPONENT_SCOPE | Available foundation scope fields map into the view and are compared before/after invocation. 18 independent scope-mutation cases reject safely; no foundation writes. |
| C1-R04 | OPEN — P2 | Original length/count cases fixed, but Python reference validation still differs from the output DTO. Two concrete bypasses below. |
| C1-R05 | CLOSED_C1_COMPONENT_SCOPE | Projection cap removed with documented candidate rationale. 300 alternating Child/Teacher corrections produce valid complete history, retain receipts/original and replay the first receipt identically. |
| C1-R06 | CLOSED_C1_COMPONENT_SCOPE | Canonical complete typed result retained immutably and hash-verified; original rebuilt including correlation, no change after corrections. Teacher-only resolution, concealment, revocation, corruption rejection and atomic rollback independently pass. |

## R04 remaining: reference guard admits values the DTO rejects

**Affected code:** `backend/src/sketch2life/domain/vision_analysis.py:547` and `:551`
inside `observation_bounds_violation` (line numbers pinned to reviewed hashes).

1. `_OBSERVATION_REF.match(ref)` uses a Python regex ending in `$`. Python allows
   that anchor immediately before a final newline. A typed
   `EntityObservation("ent-1\n", ...)` supplied through the supported C1 fake provider
   passes this guard, so `record_observation` stores an accepted analysis. The DATA-22
   Pydantic regex rejects the same reference. Teacher CMD-34 returns **HTTP 500 after
   committing** analysis revision 2 plus one correction, receipt and invalidation.
   Root independently reran this full path, including DTO and API checks.
2. Optional action references are collected with `if ref`, which skips the empty
   string as well as None. `actor_ref=""` or `object_ref=""` therefore passes the
   guard and is stored, but `AnalysisRecordV1` rejects its original-observation
   projection. Both are strings within the current typed domain constructor, not
   object/type corruption. `None` is allowed; an empty non-None ref is not.

The unchanged legacy V2 parser rejects these malformed values, so the residual
path is the current typed non-legacy/fake provider seam. The C1 service explicitly
guards all providers and declares that an accepted record can be projected. This
is the same R04 producer/contract mismatch, not a new task or a production-provider claim.

**Small correction:** check every non-None optional ref, including empty strings,
and require complete-string matching (`fullmatch` or equivalent) consistent with the
DTO. Do not strip/normalize a bad ref, silently drop it, weaken the DTO, edit the
legacy adapter, or merely catch serialization after committing.

**Required regression:** typed-provider cases for final-newline IDs/refs and empty
optional action refs fail safely with OUTPUT_MALFORMED before any analysis/result
record is stored; None/valid refs and the existing 120/256 boundaries still pass.
Preserve the bridge→API and replay checks and all five closed findings.

**Reproduction:**

- `agent-domain/r04_final_newline_probe.py` and `_result.json`;
  root rerun `root-r04-final-newline.json` records 500 and post-commit counts.
- `agent-domain/r04_optional_refs_probe.py` and `_result.json`;
  root `root-r04-empty-optional-ref.json` reproduces accepted→record rejection.
- `agent-domain/r03_r04_r05_matrix.py` / `_result.json`: 18 scope checks, 22 actual
  legacy bridge boundary cases, and 300-correction history proof.
- `agent-bridge/r06_independent_results.json`: full-result retention/auth/integrity/rollback.

## Limits and next step

- N01 body buffering remains the previous non-blocking P3 note. Legacy F-01 remains
  contained; Pillow-dependent checks remain NOT_RUN.
- One stronger overlapping invalidation/replay probe fails if it demands the latest
  head at response time. The read can linearize at its initial head read while the
  invalidation overlaps; no explicit fresh-return fence was approved. This remains
  a qualified concurrency note, not a reopened R01 or new blocking finding.
- No new owner-fence, queue, persistence, provider, card or runtime work is added.
  BE2-01 stays WAITING_STUDIO; real integration remains ASSUMED_CONTRACT/NOT_RUN.
- Claude should fix only R04's remaining reference checks, add regression evidence,
  update current records, and stop FIXED_PENDING_CODEX_REVIEW. No stage/commit/push/
  merge/deploy or full-card closure.
