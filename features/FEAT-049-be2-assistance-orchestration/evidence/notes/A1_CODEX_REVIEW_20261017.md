# BE2-03 A1 implementation review — 2026-10-17

Disposition: **NEEDS_REVISION — 0 P1 / 5 P2** in the approved offline component.
The existing suites pass, but the additional probes below reproduce violations of
the approved behavior. No component acceptance or full-card closure is implied.

## Identity, authority and verification

- Worktree `.worktrees/be2-03-assistance-orchestration`, branch
  `feature/be2-03-assistance-orchestration`, HEAD
  `f120c4fce8f7853e5ab5e061eff4bf916d45603c`, staged 0.
- Actual approval is recorded verbatim in `approvals/TASK_APPROVAL.md`: A1.1–A1.5
  and D1–D11 as recommended. Approved plan bytes in `plan/PLAN_REV3_APPROVED.md`
  match SHA256 `e1fce645a5d8c98efe366865f5a8a1b9c81c8a48626723c4e73f0c646979d3e5`.
- Root verified the reported source hashes, read source/contracts/callers and ran
  the combined A1 + BE2-01 + BE2-02 suite: **851 passed, 0 failures/errors/skips**,
  29 test files. This is 101 A1 + 338 foundation + 412 Vision tests, not 851 new tests.
- Existing Pillow was loaded only as a process-local package, multipart from the
  already available local dependency directory. Imports resolve to this worktree.
  External sockets were blocked in the test process; needed local Python child
  tests were permitted. No shared environment modification or installation.
- Root `ruff` on 16 new source/test files and strict `mypy` on the 10 new source
  files passed. Harness/security/architecture/skeleton/diff checks passed.
- Three delegated same-family targeted reviews covered coordinator/races,
  semantics and contracts/HTTP. Their existing test subsets overlap the 851 and
  are not added to that total. This is not cross-role sign-off.

Python references below are relative to `backend/src/sketch2life/`, at the reviewed
source hashes in `../metrics/A1_CODEX_REVIEW_20261017.json`.

## A1-CR01 — P2: cache bypasses current disclosure withdrawal

**Location:** `application/services/assistance.py` lines 581–610, especially
593–602; cache acceptance at lines 490–497.

`_cache_candidate(principal, resolution)` does not use the principal or check
`authority.disclose(principal, original)`. The active-request dedup branch performs
that check; cache reuse does not.

Verified with ordinary valid fixture HTTP: a Teacher submits and completes a
request; its disclosure scope is withdrawn. A current read and original-key replay
both return 404. The same valid command with a new key instead returns **202
cache_hit**, and the Teacher projection includes the original assistance, request
revision, job, analysis and analysis revision in `cache_hit_of`.

**Fix:** require current authorization to disclose the original cached resource
before using or exposing its provenance, and preserve that decision through cache
acceptance. A new operation key cannot bypass access withdrawal. Add a new-key
cache regression after read withdrawal; retain successful same-scope cache behavior.

## A1-CR02 — P2: owner publications bypass the shared coordinator

**Location:** `infrastructure/assistance/fakes.py` lines 123–142, especially the
immediate callback at line 130 and deferred callback at line 141.

`request_publication()` checks thread-local foundation depth, then invokes an
immediate callback without acquiring the coordinator lock. `_run_deferred()` also
executes its callback without that lock. Cancellation callbacks happen to acquire
the assistance store lock, but generic owner-fact callbacks do not.

The approved plan explicitly routes fake owner facts through this helper. A probe
used it from a second thread to withdraw owner eligibility and bump the shared
epoch after a successful foundation hold. The callback completed before the
foundation commit, yet start returned true and stored RUNNING. This reproduces
the very post-hold/pre-commit gap the coordinator is meant to exclude.

**Fix:** serialize immediate and deferred publication execution under the shared
coordinator, retaining the documented lock ordering, same-thread deferral and
exception release. Do not rely on every callback independently taking another
lock. Add a cross-thread owner-revocation test at the successful-hold/pre-commit
seam; preserve R15/R16 cancellation and rollback cases.

## A1-CR03 — P2: the handoff gate is stale before its commit

**Location:** `application/services/assistance.py` lines 833–850 and 881–893.

The current analysis/digest gate runs before opening the assistance transaction.
The commit checks only the request record version. Owner facts may change without
a request notice/version bump, so a previously passed decision can be published
after its facts have already been revoked.

Verified with the real service chain over fakes: after the handoff gate passed,
a one-shot clock hook at line 839 used `request_publication` to revoke consent
coherently in the assistance owner, Vision context and foundation eligibility, and
incremented the shared epoch. No notice was delivered. Reconcile nevertheless
committed **analysis_ready and one simulated Sketch intent**. Current consent was
false and the current digest differed from the stored pin. A same-revision age-fact
update at the same seam reproduced the stale publication too.

This remains a gap even if CR02 makes each owner publication atomic: that
publication can validly commit between the decision read and the later assistance
commit.

**Fix:** bind current owner/source/analysis decisions to a versioned snapshot/epoch
that is validated through handoff publication, or use an equivalent coordinated
decision/commit protocol within the approved fake composition. Re-decide when facts
move. Apply the same rule to relevant submit/cache decisions; avoid calling the
foundation service while an assistance UoW is open. Add the exact pre-commit
consent/digest race, not merely a change before the gate begins or an owner notice
that already mutates the request version.

## A1-CR04 — P2: semantic changes wrongly supersede valid requests

**Location:** `application/services/assistance.py` lines 479–489.

Every request sharing `operation_target` is staled when its semantic identity
differs, even when its owner-fact digest is unchanged. The approved supersession
rule is for facts that are no longer current. A changed Child intent or requester
reason is a different semantic request, not proof that the old facts are stale.

At elapsed 0 seconds, changing only `child_intent` from "a cat" to "a dog" with the
same digest produced an old stale request, `counts_for_debounce=false`, a new
scheduled request and two jobs, with no rate refusal. A Teacher request followed
by a Child request for the same target did the same. Thus ordinary semantic changes
can invalidate a valid request and bypass the five-second fixture debounce.

**Fix:** supersede on actual resolved-fact binding movement, not merely different
semantic payload. Keep a valid same-digest request active and enforce debounce/
budget for new semantic requests. Preserve the changed-roster/consent/render cases
that legitimately supersede. Cover changed intent and Teacher-to-Child submissions
in the same debounce window without silently cancelling the older request.

## A1-CR05 — P2: valid LongText is rejected instead of normalized

**Location:** `application/services/assistance.py` lines 274–279.

The service computes `normalize_child_intent`, then rejects any text changed by
the normalization. The approved field map calls for normalized LongText and the
receipt fingerprint for a canonical normalized command, not already-normalized
client input only. The body DTO accepts these otherwise valid strings.

Verified: both " a cat " and decomposed-Unicode Vietnamese "con mèo" return
FIELD_VALIDATION_FAILED. Their canonical versions create successfully. This is
reachable with normal JSON text; it is not a malformed-header artifact.

**Fix:** normalize before fingerprinting, semantic comparison and storage using
one consistent command representation. Keep genuinely invalid control/oversize/
empty-after-normalization text refused. Add trim/NFC positive cases and same-key
replay equivalence, along with changed meaningful content conflicts.

## Probe evidence and exclusions

Raw probes/logs/JUnit remain ignored under
`evidence/local/codex-a1-review-20261017/`:

| Evidence | File |
|---|---|
| Root combined suite | `root-1792244159306355000/result.json` and `junit.xml` |
| Static checks | `static/result.json` and logs |
| Cache disclosure withdrawal through valid HTTP | `contracts/cache_read_scope_result.json` and `cache_read_scope_probe.py` |
| Cross-thread owner publication gap | `coordinator/probe_owner_publication.json` and `.py` |
| Changed semantic payload, age/consent handoff races | `semantics/probe_result.json` and `probe.py` |
| Valid text normalization refusal | `text_normalization_probe.json` |

Probe scripts deliberately observe the current wrong behavior; exit 0 means a
violation was reproduced, not that the product guarantee passed. These are actual
A1 services over synthetic fakes, not Studio/SQL/model evidence.

No additional finding is claimed for an invalid raw-LF HTTP header, an unproven
torn Vision revision read, or pre-existing module typing issues. The reported
FEAT-048 ID collision on the teammate branch is separate historical integration
work. No unrelated foundation/Vision source behavior was changed by this review.

## Next step

Correct these five issues and add meaningful regressions under the existing A1
approval. Preserve approved plan/approval and original implementation evidence;
append fix evidence, rerun focused/regression/static/repository checks, then stop
for Codex re-review. No component acceptance or Git publication yet. BE2-01 stays
WAITING_STUDIO; BE2-02 stays parked; BE2-03 remains IN_PROGRESS / NOT_DONE.
