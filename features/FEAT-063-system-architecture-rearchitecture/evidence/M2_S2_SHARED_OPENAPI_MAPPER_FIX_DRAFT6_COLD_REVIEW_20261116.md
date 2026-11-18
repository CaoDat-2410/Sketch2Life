# M2-S2 Shared OpenAPI Mapper Draft 6 Cold Review

**Review result: ACCEPT WITH CORRECTIONS — planning review only.** This is not implementation, baseline, test, approval, or launch authorization. M2-S2 remains **PARTIAL / NOT COMPLETE**.

## Reviewed artifact and provenance

- Plan: `plan/M2_S2_SHARED_OPENAPI_MAPPER_FIX_DRAFT6_20261116.md`
- Reviewed pin: 37,118 bytes; SHA-256 `70675F32B797557CDF24528039AFB04207596123A115DC9AB019DE75719EAAC5`
- Worktree / branch / HEAD: `.worktrees/m2-s2` / `feature/feat063-m2-s2` / `5de30674bc826591ad4b3cc00fca53c7597ead51`
- Observed current Draft 5 predecessor: 29,568 bytes; SHA-256 `61D198C946F08535622ED00236D54DB6FC347A8AF960821BB3D2E6F99B652243`
- Earlier Draft 5 review pin: 29,568 bytes; SHA-256 `61D198C946085F35622ED00236D54DB6FC347A8AF960821BB3D2E6F99B652243`. The earlier ACCEPT applies only to that hash. Draft 6 preserves and records the discrepancy; the review confirmed this boundary is stated correctly.
- Fresh reviewer thread: `01a1e2f0-c254-7e20-8197-649660ccb58e`
- Final review turn: `01a1e2f4-313f-7b11-8f27-57f5ecbd268a`
- Final review item: `msg_09b773d4d11c9477016afa9cefbaa087d0adedd0edb26b9c67`
- Reviewer was created with `readOnly` sandbox, `networkAccess: false`, and approval policy `never`. It received the plan and relevant source/evidence excerpts inline. The initial prompt was truncated by the bridge inside §7; the complete §§7–10 were then supplied in the same independent thread, and the final verdict covers the full Draft 6.
- The reviewer did not run commands, access files or network, modify files, or independently recheck filesystem pins. The reviewer treated the supplied pin table as declared evidence, not a verified pin audit.

## Prioritized findings

1. **P1 — Separate the pytest storage-example setting from the exporter setting.** Section 6’s exporter profile sets `SKETCH2LIFE_STORAGE_EXAMPLE_ENABLED=true`, and §7 says the pytest process uses the §6 allowlist. The selected composition node directly constructs `Settings` without setting `storage_example_enabled`; `_env_file=None` disables dotenv but still allows process-environment values. Therefore the node can receive `true`, contrary to §3’s claim that its test/staging settings leave the field false. Specify that the pytest process omits this variable or sets it to `false`; the catalog fixture can set it to `true` for its own test.

2. **P1 — Define the comparator report producer and handoff.** The pytest card requires `$ComparatorReport` to exist with `passed: true`, but its bootstrap invokes only pytest, and the comparator is a separate command family. The draft does not explain how the separately produced report reaches the fresh pytest run root. Specify an execution sequence and shared report path, or make comparator success a separate gate outside pytest. Keep the comparator result, input hashes, pytest results, and artifact hashes linked in the future approved evidence handoff.

3. **P2 — Enumerate the request-ID delta.** Sections 5.5 and 5.7 refer to “existing path prefixes.” Give the comparator a finite list of affected method/path keys and JSON field pointers, or a pinned reference that resolves to that exact list.

4. **P2 — Bound the engine-disposal claim.** The selected node has four explicit `dispose()` calls after assertions, but the supplied excerpt shows no `finally` block. It supports disposal on the normal path, not guaranteed disposal after an exception. Describe those calls as normal-path disposal; the exporter’s separate `finally` requirement remains appropriate.

## Checks that pass

- Sections 2 and 4 preserve mapper Option A as exact `(method.lower(), path)` lookup; `operationId` is a stable, unique invariant, not the lookup key. Allowlist Choice A remains exactly E `app.py`, E `test_openapi_contract_catalog.py`, N `test_openapi_schema_catalog_mapping.py`, and R `test_app_composition.py`.
- The supplied Settings and S3 adapter excerpts support the process-environment and explicit-credential explanation. The draft correctly leaves Boto3 provider-chain behavior, DB/provider access, and network isolation unverified at runtime.
- Sections 6–8 distinguish runtime and published schemas and make the future lock-matched environment, isolation controls, owner-confirmed egress block, command ceilings, separate approval, and launch instruction explicit gates. The planning text does not authorize baseline collection, tests, implementation, or launch.
- The reviewer found the provenance boundary and scope/identity choices correctly represented. No allowlist expansion was recommended.

## Disposition

The Draft 6 planning review returns **ACCEPT WITH CORRECTIONS**. The findings above remain open for owner disposition. Draft 6 was not edited after review, and this evidence record does not create an approval or launch instruction.
