# MGR-3 Draft 1 Independent Cold Review

**Date:** 2026-11-17  
**Reviewer:** `/root/mgr3_r2_cold_review`  
**Worktree:** `D:\GitHub\Sketch2Life\.worktrees\manager-api`  
**Branch / HEAD:** `feature/feat066-manager-api-contracts` / `1c9148e88600a101887e477541c4c4893ba1c7df`

## Identity and pins

All supplied hard pins matched:

- Plan: 30,329 bytes; SHA-256 `D3B591600ED23597ADA10A087B644C00766DF8F8416DE9F540ECB867B3D9CBE7`.
- Source evidence: 20,056 bytes; SHA-256 `AE4C66C6FE1642EE12597B44C8EC00F28CEBC99FF590C22B0C84067A868FCFFB`.
- Historical review, read for context only: 3,137 bytes; SHA-256 `C96F0204AC0D5238663B0C661903815752A0F466982AEB09DBA8ADA569F247EA`.
- `docs/context/SRS_AUTHORITY.md`: 4,054 bytes; SHA-256 `032223EDDD46D251DE052C54BFF16AB1D4D794F865A457272507D893E3C1521F`.
- Canonical FEAT-063 Rev60 SRS: 553,948 bytes; SHA-256 `70DA43A35106E8C02B4BB8FCCB9628C0376C9E7EA6CFC51909ACB569703B218B`.

`DECISIONS.md` in the working tree is 38,951 bytes, SHA-256 `A99E5AC92E747E199E350F842C6E7444942FFDD1610205B3F07AB79F60E5F61C`, Git blob `c5e11a1b99aa72d636fa803cb2d9e33e526e70ad`. At pinned HEAD its blob is `ca0143cfd432bb70bfdf79e988228ef2066d9b50`; a direct search of that content found neither D-066-62 nor D-066-63. In the working tree, D-066-62 is at lines 260–268 and D-066-63 at lines 270–280.

All 14 BE source-file size and SHA-256 pins listed in the evidence note matched.

## Verdict

**ACCEPT WITH NOTES.**

The plan consistently labels itself DRAFT and contract planning only. It separates SRS requirements, source observations, owner decisions, proposals, and open items. D-066-62 is explicitly identified as a working-tree owner decision absent at pinned HEAD; the accessible MGR-1 owner disposition note supports its same-organization verified-Teacher rule and assignment-time revalidation (MGR-1 disposition §“Owner decisions — D-066-62,” lines 14–18). D-066-63 is clearly limited to MGR-2 and is not used as MGR-3 policy.

The reviewed Rev60 sections support the plan’s treatment of pagination, idempotency, assignment response revision, error envelope and scope behavior, and UC-12/13. The plan correctly leaves the candidate route and fields open, labels the example route and payload as proposals, and treats the UC-12 scope split as a proposal awaiting owner disposition.

Source evidence keeps router declaration and static composition separate from the OpenAPI catalog, projection allowlist, test-source presence, generated OpenAPI, and runtime. The current assignment route and its limitations are accurately described, including its `201` response, body-supplied `subject`, class-row lock/count, and missing candidate eligibility checks. The plan also recognizes that this route-level concurrency behavior does not prove a global one-active-Teacher invariant.

## Findings

### P3 — Original MGR-1 task attachment needs a locator

The plan cites an owner-authored task attachment by byte count, hash, and line numbers, but does not identify its path (plan §1, line 17; §4.1, line 67; evidence §1, lines 32–33 and 45). I could not independently locate that specific attachment in the worktree. The available MGR-1 owner disposition note does independently support the relevant decision at lines 14–18, so this does not block acceptance. Add a repository path or an accessible attachment reference when maintaining the evidence record.

**No P1 or P2 findings.**

## Not verified

- Tests were not run; test files were reviewed as source only.
- No OpenAPI generation or generated schema inspection was performed; only the catalog and projection source were reviewed.
- No build, validator, diff-check, runtime request, database, Docker, network/provider, or Modal command was run.
- Candidate-route absence is bounded to the audited BE1 registry, catalog, and projection source; runtime route availability was not probed.
- The cited original MGR-1 task attachment was not located as a worktree file.

## Approval boundary

This review grants **no implementation approval and no FE approval**. The plan remains **DRAFT / NOT APPROVED / NOT LAUNCHED**.
