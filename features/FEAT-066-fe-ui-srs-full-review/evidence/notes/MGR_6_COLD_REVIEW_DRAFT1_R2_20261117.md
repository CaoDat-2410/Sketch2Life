# MGR-6 Cold Review Draft 1 - R2

## Review scope and identity

Independent fresh-context, read-only review of the complete corrected MGR-6 Draft 1 plan and source-evidence note. The reviewer read 108 plan lines and 97 evidence lines and confirmed their exact pins below. The unchanged historical R1 report pin also matched.

- BE worktree: D:\GitHub\Sketch2Life\.worktrees\manager-api
- Branch / HEAD: feature/feat066-manager-api-contracts / 1c9148e88600a101887e477541c4c4893ba1c7df
- Canonical SRS: repository FEAT-063 Rev60, 553,948 bytes, SHA-256 70DA43A35106E8C02B4BB8FCCB9628C0376C9E7EA6CFC51909ACB569703B218B
- Corrected MGR-6 plan: 19,130 bytes, SHA-256 5310303E9B197A031AA81A8D89A78DCBF26F670E6EC84E452C9DB2158C752C07
- Corrected MGR-6 evidence: 17,060 bytes, SHA-256 E2FAD0BE89A37FA5A928CB0E0D239ADE49325A7BFBA342505F4B71841A0E2E18
- Historical combined MGR-5/MGR-6 R1 review, unchanged: 7,900 bytes, SHA-256 9B26DB1474F29C52A642B816CC2100EEA880CDC9DE60F45220B6F3E9DFA69297

## Verdict

**ACCEPT.** No actionable P0, P1, P2, or P3 findings remain in the corrected MGR-6 planning pair.

## Review results

- The grant-list and decision paths are corrected and consistent with the route declarations: GET /api/lesson-library/v1/organizations/{organization_id}/access-grants and POST /api/lesson-library/v1/organizations/{organization_id}/access-grants/{access_grant_id}/decision. The router prefix and static composition are separately cited (lesson_library.py:53,436-479; router_composition.py:73; app.py:256,1004-1011). Static operation-catalog entries are identified separately (openapi_contract.py:9509,9575); they are not represented as runtime verification.
- The SRS distinction is sound. Rev60 section 31.3 line 2536 pins exact versions/hashes for its named occurrence, plan, and StoryRun flows; section 31.3 lines 2547 and 2560 require School Manager review before PUBLIC. These do not directly prescribe a Manager review API or require the access grant to carry a content hash. Manager-specific hash binding is correctly labeled as a proposed technical safety contract, not a direct SRS requirement.
- The current superseded-grant behavior is described without inferring a target policy: service.py:1193-1220 checks grant state/revision and acts on grant.version_id without comparing it to lesson.current_version_id. No race or concurrency guarantee is claimed.
- Version/hash binding is represented accurately: current grant records carry version_id but no grant content hash; lesson detail exposes the current version/hash; the decision request has no version/hash field. The binding mechanism and superseded-grant outcome remain open/proposed rather than selected.
- Pagination is reconciled with Rev60 section 21.1 line 1613: the BE default of 50 differs from the SRS default of 25; the maximum is 100. The FE cursor behavior and proposed future contract correction are documented.
- The FE guard is accurately limited to matching grant.version_id with lesson.current_version.version_id and requiring content (ManagerScreens.tsx:69-72,247-265). It does not validate a content hash or replace server-side stale-version checks. The FE client paths are consistent (backendApi.tsx:446-453).
- D-066-62 is treated as working-tree provenance and absent from the pinned HEAD; it is not used as a committed MGR-6 baseline requirement.

## Remaining unverified or open

Runtime reachability, gateway/proxy path mapping, generated full OpenAPI output, database-enforced LessonVersion immutability, and runtime concurrency behavior were not verified. The draft appropriately leaves route/schema selection, hash-binding mechanism, superseded-grant policy, and race behavior open or proposed. No tests or runtime behavior are claimed.

## Authorization boundary

This review is a planning assessment only. It does not approve implementation, FE integration, launch, or any owner-policy choice. MGR-6 remains DRAFT / NOT APPROVED / NOT LAUNCHED.