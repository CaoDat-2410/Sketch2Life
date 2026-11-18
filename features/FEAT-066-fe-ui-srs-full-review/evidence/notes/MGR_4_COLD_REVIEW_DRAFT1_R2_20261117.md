## MGR-4 Draft 1 cold review

**Identity and pins:** Worktree `D:\GitHub\Sketch2Life\.worktrees\manager-api`, branch `feature/feat066-manager-api-contracts`, HEAD `1c9148e88600a101887e477541c4c4893ba1c7df`.

- Plan: 30,075 bytes, SHA-256 `7248971517E56B06AC2F0532BE7B012FEFCD096280418BA710264E8F8514FFFF` — matched.
- Evidence: 20,743 bytes, SHA-256 `8410767D8D5AABE7EAA43F6C6F660E60A73CCA1380FE8171DACC3A6A855C6FB7` — matched.
- Historical review `MGR_4_COLD_REVIEW_DRAFT1_20261117.md`: 4,372 bytes, SHA-256 `5BAA0F0DCF9B15B353374953FB08451E7568A7947BFF06CF8DC603324D2F62D1` — matched.

**Verdict: ACCEPT WITH NOTES.** No P1 or P2 findings. Both targeted corrections are supported by direct source inspection.

### Findings

- **P3 — Prior dependency-sequencing note remains; outside this correction’s scope.** The plan still calls MGR-5 and MGR-6 “roadmap dependencies” at §1 line 17 and §7 lines 122–123. The roadmap table identifies MGR-1 as MGR-4’s dependency and MGR-2/3/5/6 as parallel work (table header and MGR-4 row, lines 29 and 35). The corrected evidence says those interfaces remain open, but does not make them blockers. This is the carryover noted in the prior review.

### Targeted corrections verified

- **Organization scope / error mapping:** Plan §5 line 86 and evidence §4 lines 61, 68 accurately call the current pre-lookup 403 a source gap and leave its safe resolution open. In `lesson_library.py` lines 519, 535, 556, `_manager` runs before service lookup; `be1_common.py` lines 83–114 returns 403 when assignment or account checks fail. Rev60 §9.8 lines 833–839 specifies same-shape 404 `RESOURCE_NOT_FOUND` for missing or out-of-scope resources, reserving 403 for known in-scope action denials.
- **Membership revoke:** Plan §5 line 82 and evidence §4 line 62 accurately distinguish bearer verification from current Parent authorization. `be1_runtime.py` lines 169–182 verifies the bearer principal; `lesson_library.py` lines 611–622 catches Manager 403s and passes the subject onward; `service.py` lines 1605–1611 checks stored principal-reference equality. The revoke path does not call `_parent_actor` (`lesson_library.py` lines 119–130), which checks active Parent role/state and issuer. The plan leaves Parent self-leave **OPEN-OWNER** and proposes current identity, role, and issuer checks if it is approved. Rev60 §31.3 lines 2547–2555 and FR-PL-23/BR-58 require revocable group membership but do not directly assign Parent self-leave authority.

I also reviewed the lifecycle, scope, provenance, and evidence-level distinctions. D-066-62 is correctly identified as working-tree-only: it appears in `DECISIONS.md` lines 260–268, while the pinned HEAD blob contains neither D-066-62 nor D-066-63; the MGR-1 disposition lines 14–18 corroborates it. The deferred upstream MGR-2 provenance discrepancy was not edited. Static route/composition/catalog/projection and FE evidence are distinguished from test-source presence, generated OpenAPI, and runtime behavior. The approval boundary remains explicit: **DRAFT / NOT APPROVED / NOT LAUNCHED**.

**Not verified:** Tests, builds, validators, OpenAPI generation or emitted OpenAPI, runtime/gateway reachability, database persistence or concurrency, and invitation delivery. The reviewer made no file changes; this review grants no implementation or launch approval.
