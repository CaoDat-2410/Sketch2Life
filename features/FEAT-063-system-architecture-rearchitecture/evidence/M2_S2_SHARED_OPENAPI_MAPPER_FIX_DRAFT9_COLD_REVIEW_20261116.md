# M2-S2 Shared OpenAPI Mapper Fix Draft 9 — Cold Review Evidence

**Date:** 2026-11-16  
**Review result:** ACCEPT WITH CORRECTIONS — planning review only  
**Target:** `plan/M2_S2_SHARED_OPENAPI_MAPPER_FIX_DRAFT9_20261116.md`  
**Target pin:** 56,095 bytes; SHA-256 `F8AC1ECE7DACF31736C6450686B2817719BFB6E77CAA31E0DABE38B128F209AF`

## Review provenance

- Independent cold-review thread: `01a1e342-ba3d-7bf2-beaf-7963bf0a3e2a`.
- Initial review request ID: `m2s2-openapi-mapper-draft9-cold-review-20261116-f8ac1ece`.
- Complete-§6 continuation request ID: `m2s2-openapi-mapper-draft9-cold-review-send-section6-20261116`.
- The retained reviewer thread used the same BE worktree, a read-only sandbox, network disabled, and approval policy `never`.
- The reviewer first withheld its verdict because §6 was truncated. It later confirmed that §§1–5 and 7–10 arrived in the first message and the follow-up supplied §6 in full; all ten sections were received before the verdict.
- The reviewer assessed the supplied text. It did not run commands, independently recalculate the file hash, or inspect the worktree.

## Verdict and findings

**ACCEPT WITH CORRECTIONS.** This is a planning review only; it does not authorize a baseline, tests, implementation, approval, S2 closure, S3, or launch.

**P2 — §6, comparator command card:** The card checks whether `$ComparisonRoot` already exists and throws before creating `sha256.txt`. This conflicts with the later requirement to create the manifest before any failure throw. Clarify that manifest-before-throw applies only after a fresh comparison root is created, or define safe reporting for this pre-run collision without writing into the existing directory. As written, the Draft 7 failure-path hashing correction has this gap.

**Evidence gap — §1 and prior findings:** Draft 9 says Draft 7 addressed four Draft 6 findings but does not enumerate them, and those descriptions were not included in the review material. The reviewer therefore could not independently verify all four. The two Draft 7 findings are identified; normalized environment identity is addressed in §6, subject to the P2 above.

## Checks confirmed from the supplied Draft 9 text

- The Draft 8 N-path finding is addressed: pre-implementation state is `ABSENT` with `sha256: null` and no hash attempt; post-implementation state is `PRESENT` with its actual SHA-256. Both tuples must appear in comparator output, and the plan fails closed if the path exists before export or is absent/unreadable afterward.
- Mapper Option A uses the exact `(method.lower(), path)` lookup key. `operationId` remains stable and unique as an invariant, not the runtime key.
- The §4 allowlist matches Choice A: E `app.py`, E `test_openapi_contract_catalog.py`, N `test_openapi_schema_catalog_mapping.py`, and R `test_app_composition.py`.
- The Draft 5 provenance discrepancy is preserved; request-ID inventory remains OPEN and fail-closed; Draft 9 remains DRAFT / NOT APPROVED / NOT LAUNCHED.
- No implementation, baseline, test, approval, or launch authority is implied.
