# MGR-4 Draft 1 Independent Cold Review

**Reviewer:** `/root/mgr4_cold_review` (single fresh-context reviewer; read-only)  
**Date:** 2026-11-17  
**BE worktree:** `D:\GitHub\Sketch2Life\.worktrees\manager-api`  
**FE worktree:** `D:\GitHub\Sketch2Life\.worktrees\ui`

## Identity and pins

The expected BE and FE branch/HEAD identities matched. At the expected BE worktree, both MGR-4 artifact pins matched:

- Plan: 27,376 bytes; SHA-256 `5DAE342B0CCBDE02DCBA9F75471F2DBCEDBB9F8447EF2291A319C7DD373AD7CF`.
- Source evidence: 18,469 bytes; SHA-256 `43C62305C8D2BB980632C70F71DDD9C3D7F36952BAA0EE17812458A02840D44F`.
- The cited BE and FE source-file hashes matched the evidence pins.

**Process note:** the reviewer initially checked the repository-root-relative artifact path. After clarifying that artifact paths are relative to `.worktrees/manager-api`, the same reviewer verified the correct pins and continued this single review. No second reviewer was opened.

## Verdict

**CHANGES REQUIRED.**

## Findings

### P2 — Current 403 behavior for out-of-scope organization access is not recorded as a source gap

Plan §3, line 55 correctly states Rev60’s 403/404 rule, but Plan §5, line 86 and Evidence §4, line 65 only describe current error behavior generically. In source, group and invitation handlers call `_manager` before resource lookup; `require_assignment` returns `403 ACCOUNT_SCOPE_UNAVAILABLE` when the caller lacks an active assignment for that organization (`lesson_library.py:519, 535, 556`; `be1_common.py:108–115`). Rev60 §9.8, lines 837–838, requires same-shape 404 for out-of-scope resources and limits 403 to known in-scope denials. Record this as a current source gap while keeping unspecified operation-specific mappings OPEN.

### P2 — Revoke is described as validating a Parent actor, but source checks only the stored principal reference

Plan §5, line 82 and Evidence §4, line 59 describe matching-Parent self-revoke. The revoke handler falls back after a Manager 403 and passes the actor to the service (`lesson_library.py:611–622`); the service checks only whether stored `parent_principal_ref` equals that actor (`service.py:1605–1611`). It does not call `_parent_actor`, which checks active Parent role and issuer (`lesson_library.py:119–130`). Describe this as matching the stored member principal; leave Parent-role validation and self-leave authority OPEN.

### P3 — MGR-4 sequencing is misstated

Plan §1, line 17, Plan §7, lines 122–123, and Evidence §8, line 112 characterize MGR-5/MGR-6 or MGR-2/3/5/6 as MGR-4 dependencies. The roadmap’s MGR-4 row says MGR-4 depends on MGR-1 and runs in parallel with MGR-2/3/5/6; MGR-7 depends on the MGR-1–6 decisions (roadmap lines 35 and 38). Correct the summary so parallel contract work is not presented as blocking MGR-4.

## Review notes

The plan correctly separates Parent-group membership from Parent-profile consent and child-media access; labels D-066-62 as a working-tree decision absent pinned HEAD; and keeps recipient verification, route mapping, lifecycle policy, delivery, and concurrency open. The evidence separates route declaration, static composition, catalog, projection source, FE availability, test-source presence, and runtime verification. It correctly treats the outbox event as producer evidence, not delivery proof.

D-066-62 was verified in current working-tree `DECISIONS.md`, lines 260–268, and absent from pinned HEAD blob `ca0143cfd432bb70bfdf79e988228ef2066d9b50`; the MGR-1 disposition supports the owner decision. A contextual inconsistency remains in upstream MGR-2 evidence note §2, line 24, which says D-066-62 was present at its “pinned baseline.” The direct HEAD check shows it absent there; MGR-4’s working-tree-only description is accurate.

## Not verified

- Tests were not run.
- Generated OpenAPI, runtime reachability, gateway mapping, persistence or migrations, database concurrency, and invitation delivery were not verified.
- Route-absence findings are limited to inspected source, catalog, and projection files.
- No tests, builds, validators, OpenAPI generation, runtime, database, Docker, network/provider, or Modal commands were run.

## Approval boundary

This review grants no implementation approval, FE approval, or launch approval. MGR-4 remains **DRAFT / NOT APPROVED / NOT LAUNCHED**.
