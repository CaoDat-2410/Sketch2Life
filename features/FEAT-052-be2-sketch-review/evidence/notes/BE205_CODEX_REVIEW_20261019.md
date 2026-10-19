# BE2-05 independent implementation review — 2026-10-19

**Verdict: NEEDS_CHANGES — 1 P1 / 4 P2.**
verification_complete: false. Component NOT_ACCEPTED; BE2-05 IN_PROGRESS / NOT_DONE.

Review covers the approved offline K1–K7 implementation, not SQL/runtime/provider integration.
The defects below reproduce on the real accepted SK1 ->05 fixture chain and violate guarantees
inside this scope. No real child data, provider or production execution was used.

## Snapshot and authority

- Worktree .worktrees/be2-05-sketch-review; branch feature/be2-05-sketch-review.
- HEAD58293f1a29ec630e2603c2860b6a2337fadfa713; no upstream; index empty.
- TASK_APPROVAL records actual owner approval and the owner's FEAT052 allocation override.
- Approved candidate bytes: PLAN_R2_APPROVED.md SHA256
  ab29530545b94346102bd037822572e483828fa697582e74a74be334cecf0c00.
- All19 references in implementation metrics BE205_CHECKS_20261019.json match SHA256 and byte
  count before and after independent checks. Source/test/fixture/approval/plan unchanged.
- Shared DATA24, accepted SK1 and other owners' implementations were not edited.
- Independent review receipts/probes: ignored evidence/local/codex-review-20261019/.
  Implementation note/metrics and earlier reviews remain immutable historical evidence.

## RV-CR01 — P1: an old PASSED moderation admits content BLOCKED by the current policy

Source:
- backend/src/sketch2life/application/services/sketch_review.py:267-278,369-371.
- backend/src/sketch2life/infrastructure/sketch_review/coordination.py:172-180.

Moderation is stored/looked up only by proposal/version/content hash. Its policy identity is
recorded but not part of selection. _prepare computes a fresh verdict for the new policy, yet
_commit_review discards it whenever an older record exists; moderate also returns the old record.

Independent reproduction:
1. Promote a real04 proposal; moderate under review policy v1 -> PASSED.
2. Publish v2 through the real coordinated publication, with a term rule blocking that same text.
3. Fixture moderation under v2 returns BLOCKED.
4. CMD35 still returns201; stored moderation remains PASSED@v1; Child payload is available under
   the newly created review whose policy label is v2.

Fix direction: select append-only moderation by complete applicable identity, including the
current moderation policy and pinned content/ref hashes. Evaluate/use the current-policy verdict
for admission; record new policy assessments without rewriting old evidence. Queue/moderate,
approval and eligibility must agree. A newly blocked result records its quarantine intent after
the approved atomic protocol, and no approve/access bypass is possible.

Required regression: existing PASSED@v1 -> v2 BLOCKED on the same target. Test moderate and direct
approve paths, no effective approval/content, and correct current-policy record/intent.

Probe: fence-probes/review_fence_policy_probe.py, case policy_changed_reuses_old_moderation.
This is a P1 admission/safety defect in the component logic, not a claim of a production incident.

## RV-CR02 — P2: authority/policy reads before token capture can authorize revoked work

Source: application/services/sketch_review.py:170-179,210-243,353-365.

_require_teacher and _policy run before token(). _prepare neither rereads authority nor obtains
the policy again after token; it carries the earlier policy value. If an owner publication happens
after the port obtains its old value and before token capture, token records the new epoch while
the decision uses the old facts. Final hold then succeeds.

Independent reproductions use fresh harness instances and proper coordinated epoch publications:
- policy.current reads enabled v1, publishes disabled v2 before returning v1 -> CMD35 returns201
  while current policy is disabled.
- authority.allowed obtains True, publishes removal of the Teacher grant before returning ->
  CMD35 returns201 and stores a review after the grant has been removed.

These are not the DI18 unbumped-owner residual: both changes use the intended publication+epoch.
The same ordering occurs in moderate().

Fix direction: preliminary checks may remain, but all decisive authority/policy/context/moderation
reads must be observed after token capture, then verified by the final hold. Preserve the shared
coordinator, complete scopes and final UoW/CAS/receipt order already implemented.

Required regressions: mutate during initial authority/policy read BEFORE token, and verify no
decision/moderation is committed on the revoked/disabled old observation.

Probe: fence-probes/review_fence_policy_probe.py, policy_read_before_token and
grant_read_before_token.

## RV-CR03 — P2: warmed cache serves quarantined content without reauthorization

Source:
- infrastructure/sketch_review/fakes.py:178-183.
- infrastructure/sketch_review/coordination.py:96-100.

FakeChildCache checks only the05 sketch-review epoch. Quarantine, producer invalidation/consent,
analysis, review-policy/context and device binding changes can affect eligibility while bumping
other scopes. A cache hit returns the old content without calling child_payload/eligibility.

Independent reproduction:
approve -> warm cache -> coordinated quarantine of promoted refs -> cache still returns
available with text AND asset ref. Direct child_payload returns unavailable and producer04 is
stale. Cache misses remain1, proving that the stale cached value was returned.

The fake cache is part of the approved leakage acceptance, so this is not a deferred BE1 gateway
implementation issue. Current N14 only exercises Teacher reject, which happens to bump05 epoch.

Fix direction: authorize every hit, or validate a complete current eligibility token covering
all dependencies plus device identity/grant. Preserve content reuse only under a current grant.

Required regression: warm cache, independently change owner quarantine/consent,05 policy/context
and device binding, and prove no content is reused after denial without caller-managed refresh.

Probe: access-probes/cache_and_revival_probe.py, cache_after_quarantine.

## RV-CR04 — P2: observed stale approvals revive when old policy/context values are restored

Source: application/services/sketch_review.py:531-540,584-617,691-708.

_applicable returns False when current policy/context differs, but eligibility/read denial does
not persist that invalidation or remember a monotonic observation. The entry stays effective.
Only explicit refresh/notice processing marks it stale. Restoring the old values makes the old
review eligible without a fresh decision.

Independent reproductions:
- approve under policy1 -> publish policy2 -> Child denied -> restore policy1 -> available with
  the SAME old review; entry effective, review count1.
- approve audience revision5 -> publish6 -> Child denied -> coordinated restore5 -> available
  again; entry effective, review count1.

Approved plan §4.9 makes pull authoritative and says stale reviews do not automatically become
effective again. Existing N11 calls refresh manually, masking the required pull-only behavior.

Fix direction: persist an observed invalidation under the appropriate coordinated decision
boundary, or pin a monotonic invalidation generation that survives value restoration. Do not
make callers remember an extra refresh call to enforce no resurrection.

Required regression: policy/context invalidation and restoration after a denial, without calling
refresh; old review remains unusable. A fresh explicitly authorized review can reopen an otherwise
nonterminal current target according to the approved policy.

Probe: access-probes/cache_and_revival_probe.py, policy_restoration and audience_restoration.

## RV-CR05 — P2: receipt fingerprint hashes raw input instead of normalized command semantics

Source:
- application/services/sketch_review.py:164-166.
- contracts/schemas/sketch_reviews.py:82-88,121-127.
- approved plan PLAN_R2_APPROVED.md:572.

The fingerprint is computed before the binder's NFC/trim and set ordering. Semantically
equivalent retries therefore fail receipt recovery:
- accepted reason Cafe + combining accent -> retry reason with spaces around composed Café:
  stored reason is identical after normalization, but retry returns409 IDEMPOTENCY_PAYLOAD_MISMATCH.
- accepted group participants(A,B) -> retry same participants(B,A): also409.
Both typed DTO and raw JSON paths reproduce; original operation returns201.

Fix direction: create a pure validated canonical command representation before fingerprint/
receipt lookup, normalizing reason and set-valued fields. Keep live target/policy binding checks
after historical receipt recovery as designed. Do not make replay require unchanged lifecycle.

Required regressions: typed and JSON normalized reasons/orderings replay the original operation;
a genuinely different semantic payload with the same key still conflicts.

Probe: contract-probes/fingerprint_probe.py, four cases.

## Independent verification

Environment: existing root backend/.venv CPython3.12.10, no installs; PYTHONPATH/MYPYPATH pinned
to this worktree/backend/src. Separate temporary directories for every test suite.

| Check actually run by Codex | Result |
|---|---|
| Focused05, six files |99 PASS,0 skip |
| Accepted SK1 focused |175 PASS,0 skip |
| BE2-02/03 selected14 unit files |405 PASS,0 skip |
| Ruff, correct backend cwd (15 new Python files) |PASS |
| mypy strict (9 new source files) |PASS |
| Harness/security/architecture/skeleton validators |PASS |
| Three probe scripts (3+3+4 cases) |Exit0; counterexamples reproduced, NOT acceptance PASS |

Initial Ruff invocation at the worktree root classified first-party imports differently and
reported7 I001 findings. The backend-cwd invocation matches repository usage and passes without
source edits. Both receipts remain; do not treat the initial invocation as a required code fix.

## Audit of executor receipts, not independent reruns

- Contract XML:403 cases =400 passed +3 Pillow-related skipped. Seven additional modules remain
  NOT_RUN due collection/import dependencies; this is not a complete contract-suite PASS.
- Unit XML comparison: task2426 passed/18 failed/34 errors/37 skipped; baseline2340 passed/
 18 failed/34 errors/37 skipped. Existing case status sets are identical;86 added unit cases pass.
  No baseline case disappeared. I independently parsed the two supplied XML inventories.
- I did not rerun the complete unit suite or those contract modules. Reported Pillow/imageio/
  catalog/tools-path failures remain baseline/environment limitations, not newly attributed bugs.
- Studio/provider/SQL/HTTP routing/UI/live integration NOT_RUN, consistent with scope.

## Other conclusions and notes

- The shared coordinator, complete target/ref-set scopes, final UoW lock and post-commit
  quarantine sink ordering are in place. The five findings do not require reopening the plan.
- Terminal marker/global revoke/current-entry projection implement the intended semantics in
  covered cases. The earlier candidate projection regression is not reopened.
- R03/R04/R05 receiving412 after producer invalidation is consistent with the composite ETag
  and guard order; preserving that result is acceptable when the actual stale hold is asserted.
- Pending vs unavailable in content-free Child payload is not independently classified as a
  blocking defect here. The actual cached-content exposure is RV-CR03.
- rp_<hash> as an OpaqueId mapping is not a defect; preserve its full policy label provenance.
- Tighten evidence wording where C02 normalizes EOL instead of literal byte comparison, and
  where N15c asserts only a subset of its advertised mutation/event/epoch allowlist. Actual shared
  pack/source drift was not observed. These are nonblocking assertion-strength notes.

## Next

Fix RV-CR01–05 within the existing approved K1–K7 scope, add targeted regressions and refresh
source-bound checks/evidence. Preserve the original implementation note/metrics and these
diagnostic probes. Review again before component acceptance or publication.

No new scope approval is requested by this review. No production source/test, original
approval/plan/evidence bytes, Git index/refs, commit/push/merge or external messaging were changed.
Only new review artifacts/probes and current review-routing ledgers were written.

