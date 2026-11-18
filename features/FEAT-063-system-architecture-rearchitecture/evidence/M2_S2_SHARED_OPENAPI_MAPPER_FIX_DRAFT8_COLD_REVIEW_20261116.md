# M2-S2 Shared OpenAPI Mapper Draft 8 Cold Review

**Verdict: ACCEPT WITH CORRECTIONS — planning review only.** Draft 8 remains **DRAFT / NOT APPROVED / NOT LAUNCHED**. This review does not authorize baseline collection, tests, implementation, launch, S2 closure, or S3. M2-S2 remains **PARTIAL / NOT COMPLETE**.

## Reviewed artifact and receipt

- Plan: `plan/M2_S2_SHARED_OPENAPI_MAPPER_FIX_DRAFT8_20261116.md`
- Coordinator-verified pin before review: 54,016 bytes; SHA-256 `30152C79064E035A8303187888F6830867DA0C22322E8CCCACD6CB38AF6C2038`
- Worktree / branch / HEAD: `.worktrees/m2-s2` / `feature/feat063-m2-s2` / `5de30674bc826591ad4b3cc00fca53c7597ead51`
- Cold-review thread: `01a1e337-1937-77d3-b89b-c8f21d7e20b3`
- Review turns: `01a1e337-1f4e-7803-b426-29850a10ac7d`, `01a1e337-a154-73d0-9792-104ebcd33dbf`, and `01a1e33a-61e1-78f3-a0b3-10c52e3128bb`
- Review destination used the same BE worktree, read-only sandbox, network disabled, and approval policy `never`.
- The initial prompt was truncated at the end of §6. The complete §6 was supplied in the same thread; the reviewer then confirmed receipt of all ten sections before issuing a verdict. The bounded four-finding excerpt from the Draft 6 review was also supplied in the same thread so the reviewer could assess carry-forward. No additional review thread was created.
- The reviewer did not run commands, inspect the worktree, or independently recompute the Draft 8 hash. The coordinator verified the pin before the review and again before recording this evidence. The verdict applies to the complete Draft 8 text supplied to the reviewer.

## Verdict and remaining correction

**ACCEPT WITH CORRECTIONS.** The reviewer confirmed that Draft 8 addresses both Draft 7 findings and preserves the four Draft 6 corrections. One P2 planning correction remains in §6:

- The plan records the new N-path as absent before implementation, but elsewhere requires pre/post hashes for every allowed E/N path. Define the new path’s pre-implementation state explicitly as `ABSENT` with no hash; require and record its post-implementation hash; include both states in the comparison output. Do not represent the absent pre-state as a hash.

This is a planning correction only. Draft 8 was not changed after review, and this review does not authorize a Draft 9, another review thread, or implementation.

## Findings confirmed by the reviewer

### Draft 7 findings

- **Normalized environment identity (§6):** covers the effective allowlist, relevant worktree/source identity, route/profile values, and GUID-rooted paths; uses canonical path comparison; keeps synthetic S3 values out of manifests, reports, and console logs.
- **Comparator failure evidence (§6):** writes the SHA manifest before failure checks; hashes the six inputs and comparator source, plus the report/log when present; records missing or unreadable artifacts, exit status, and report state; and stops without retrying.

### Draft 6 findings

- **Pytest environment (§§3, 7):** separates exporter `storage-example=true` from pytest `false`, retains the synthetic S3 pair, and explains process-environment loading despite `_env_file=None`.
- **Comparator handoff (§§6, 7):** names the sole report producer, order, inputs, separate output root, hashes, evidence handoff, and pytest gate.
- **Request-ID inventory (§6):** remains **OPEN** and fails closed on any such schema delta until an exact finite list is reviewed and approved.
- **Engine cleanup (§§3, 7):** describes disposal on the normal path and does not claim finally-guaranteed cleanup.

The reviewer also confirmed mapper Option A, allowlist Choice A, the Draft 5 provenance boundary, and Draft 8’s planning-only status. Its assessment was of supplied text and evidence excerpts; it did not verify the repository state or run checks.

## Scope and execution record

No test, typecheck, lint, validator, diff-check, OpenAPI generation, application/runtime, database/migration, Docker, install/sync, repository network, provider, or Modal command was run for this review. No source, test, SRS, decision, approval, or prior draft was changed. This evidence records the independent planning review and its remaining P2 correction only.
