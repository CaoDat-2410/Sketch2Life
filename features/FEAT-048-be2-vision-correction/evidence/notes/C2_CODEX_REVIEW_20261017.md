# C2 Codex implementation review —2026-10-17

Disposition: CODE_REVIEW_PASS_WITH_NOTES / PENDING_OWNER_COMPONENT_ACCEPTANCE.
No actionable new finding or blocking defect was established in the reviewed offline scope.
Full BE2-02 remains IN_PROGRESS / NOT_DONE; this review does not record owner acceptance.

## Reviewed identity and authority

Branch `feature/be2-02-vision-correction`, HEAD98876fe; staged0. Reviewed the16 source/test
paths and typed fixture pinned in C2_IMPLEMENTATION_CHECKS_20261017.json. Root verified their
hashes before/after testing; all matched Claude's implementation receipt. C1 approval/approved
plan/acceptance and C2 approval/approved revision2 bytes remain unchanged.

Sources: AGENTS, project/source register, FEAT-048 CONTEXT, SOURCE_AUDIT, approved C2 planrev2
(SHA2564b339514…), approval16af8a94…, implementation note/tests and C1 contracts/handoff.
Root reviewed the diff and performed fresh checks; three delegated agents separately inspected
service/authority, domain/contracts and adapter/legacy behavior. These are same-family agent
reviews, not an independent model-family or role-owner sign-off. No product code was changed.

## Fresh independent checks

| Check | Observed result |
|---|---|
| Root C2 focused + C1 focused/V2 server + legacy Vision/V2/Qwen |657 collected,652 passed,0 failures/errors,5 pre-existing legacy skips; exit0 |
| Root focused ruff / strict mypy |PASS,16 source/test paths each |
| Delegated domain + contract suite |107 passed,0 skipped; exit0; overlaps root suites |
| Delegated service suite |42 passed,0 skipped; exit0; overlaps root suites |
| Delegated adapter + legacy bridge suite |56 passed,0 skipped; exit0; overlaps root suites |
| Additional adapter adversarial matrix |9/9 cases returned OUTPUT_MALFORMED, one transport call, zero head/observation/provider-result writes |

The nine extra cases include matching-but-wrong identity/source in both response layers,
boolean confidence/context revision, missing nested result, wrong model revision, a non-JSON
object, Infinity and invalid Unicode. Newline age-band rejection was also verified; a suspected
regex issue was not a defect. Delegated counts are overlapping checks, not extra unique tests.

Root receipts: ignored `evidence/local/codex-c2-review-20261017/root-045152999215/`; delegated
receipts/probes are in sibling domain/service/adapter directories. Source hashes, JUnit hashes
and final document validators are in ../metrics/C2_CODEX_REVIEW_20261017.json.
Claude's338/338 BE2-01 regression remains executor evidence; root did not rerun that group.
No dependency installs, services, live requests or Studio run occurred during this review.

## Conclusions on the requested review points

1. Internal owner facts are separated from the minimized provider payload. Audience duplicates
   are refused before conversion; each member's eligibility/permissions are checked. Both digests
   have distinct canonical inputs; same-band exact-age drift changes the internal binding.
2. Pre/post typed gates retain C1 scope/source/lineage checks. Current revocation or unavailable/
   inconsistent owner facts discard the result without writes; eligible revision/digest movement
   retains only a stale original binding. Binding/result/observation/head are atomic in the fake UoW.
3. Replay/downstream/new corrections compare current typed applicability. Historical accepted
   CMD-34 receipts retain their original response after current disclosure checks. Revoking
   provider-transfer permission is distinct from revoking permission to read one's own receipt.
4. The adapter validates the new wrapper plus existing V2 result/provenance/bounds, retains the
   complete wrapper and reports offline_context_adapter truthfully. Legacy helper extraction
   preserved image_only behavior; existing golden bytes and old strict DTOs remain compatible.
5. Shared duplicate-participant rejection is intentional malformed-owner-data hardening, not
   a valid image_only behavior regression. The two explained C1 seam-test changes retain their
   privacy/refusal purpose and are covered by actual serialized payload tests.

## Non-blocking limits and interpretation

- `analysis_record()` is the historical stored observation/correction record. Its accepted_status
  is the stored disposition, not proof of current applicability after owner facts move. Consumers
  must use `downstream_meaning.state == confirmed` before using confirmed concepts, as specified
  by H_AI_REVIEW_HANDOFF. An authorized historical read/receipt does not revive authority.
- Admission evidence is a separate C1 source/media binding; it need not be folded into the typed
  context digest merely to repeat that binding. Current source/admission owner integration is
  still fixture/ASSUMED_CONTRACT, not demonstrated live owner-fence behavior.
- Nested V2 DTOs retain their existing coercion behavior; C2 adds strict wrapper/digest checks,
  raw-confidence and domain projection checks. Small constructor/DTO asymmetries without a
  reachable current failure were not promoted to speculative findings.
- Fake concurrency is controlled interleaving, not PostgreSQL isolation. Concurrent first
  submissions may each invoke once before one atomic winner; there is no global exactly-once
  provider claim. Real persistence/provider/server/model quality remain unverified.
- Age bands remain FIXTURE_ONLY / NOT_PEDAGOGICALLY_ADOPTED. Deferred Child text, Teacher
  feedback/confirmed meaning and action summaries remain FR022/UC-018 full-card gaps.

## Next checkpoint

Await the user's explicit C2 component acceptance. A commit/publication plan may follow under
its own instruction; do not stage/commit/push/merge automatically. No new implementation batch
was opened. BE2-01 remains WAITING_STUDIO, CR01 open, B-12 HANDOFF, OwnerFence ASSUMED_CONTRACT;
the pending named-Studio A17-fix01 verification/review still has priority when the user resumes it.
