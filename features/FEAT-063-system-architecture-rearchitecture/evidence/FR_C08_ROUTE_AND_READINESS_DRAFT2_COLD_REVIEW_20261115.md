# FR-C-08 route/readiness and M3–M6 addenda Draft 2 — independent cold review

**Date:** 2026-11-15  
**Reviewer:** fresh-context independent reviewer `/root/frc08_final_package_review`  
**Verdict:** **CLEAN — 0 P1, 0 P2, 0 P3**  
**Disposition:** SRS-aligned enough for owner review only. This is not implementation approval.

## Reviewed target pins

| File | Bytes | SHA-256 |
|---|---:|---|
| `plan/FR_C08_DELETE_ROUTE_SCOPE_CORRECTION_DRAFT1_20261115.md` | 10,582 | `E19028505E3945F3F290525332F33BD8292EB5EC29CEBAD2F978EDB407E698CD` |
| `plan/FR_C08_IMPLEMENTATION_READINESS_ADDENDUM_DRAFT2_20261115.md` | 9,537 | `FE21C953B5DD9DCF564E0EACC884967D861995D84E3E6FE029AB0F60E9B3FEEA` |
| `plan/M3_M6_SRS_ALIGNED_ROADMAP_ADDENDUM_DRAFT2_20261115.md` | 8,024 | `8CE372A6F35F01C16EF67376636D3E0BA6A75E1F7D9F0CCCF6549E9B4B11D2C8` |
| `evidence/FR_C08_M2_BASELINE_SNAPSHOT_20261115.md` | 12,860 | `4826D95ED4DD2C57D2091F89DB2ECCD97628E522630B67C35ABADF700F7D455B` |

All four target pins and all 60 size/hash rows in the timestamped snapshot matched.

## Findings

- Rev68 §21.2 requires `DELETE /v1/story-runs/{id}` for explicit deletion of COMPLETED, FAILED, or ABANDONED. The current router lacks a DELETE handler. The correction treats this as an existing SRS operation missing from source and confines it to the existing router/composition paths.
- The correction leaves the request body, receipt representation and DELETE revision precondition open; it adds no public state or additional route. Its 202 response, lifecycle states, idempotency rule and current Parent/current Teacher authority follow Rev68 and D-208.
- Source/composition statements are bounded: the router prefix is `/v1/story-runs`; composition is conditional and app construction passes `not story_demo_enabled`. No runtime mount or generated OpenAPI result is claimed.
- The snapshot contains 60 matching manifest entries: 24 modified, 36 untracked, and 0 staged at its recorded time. Five later snapshot/review/addendum files explain the subsequent worktree count of 65. M2 remains **PARTIAL / NOT COMPLETE**; its historical non-passing/unavailable results are not converted to passes.
- Roadmap Addendum Draft 2 preserves Roadmap Draft 3's full Rev68 M3–M6 scope and dependency order. Task Approval precedes named owners; the executable pinned launch instruction follows owner assignment. The earlier Draft 4 CLEAN result is explicitly historical to its reviewed bytes.
- The root Rev60 and worktree Rev68 authority pointers are both stated; no silent authority switch was identified.

The reviewer checked the worktree authority, Rev68, D-208, M2 report, Contract Draft 2, Specification/Lifecycle Plan/Allowlist Draft 4, Draft 4 review, Roadmap Draft 3/review, relevant router/composition/app source pins, and every snapshot manifest pin. The owner-supplied Rev67 file was not in the active worktree, so the reviewer could not rehash that external file; the coordinator separately verified its `D:\Downloads` copy at 634,291 bytes / `B704163C9AAF7BB198D8578699F75DB8766C2226A52CD48B0ED1314AF5E21996`.

## Review boundary

No tests, validators, backend/runtime, database/migration, Docker, network, provider or Modal commands ran. The review approves no plan, allowlist, implementation, Task Approval, command ceiling, or launch. The separate contract update, final allowlist, technical blocker resolution, Task Approval, owner assignment and launch gates remain.
