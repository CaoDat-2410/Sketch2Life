# M2-S2 Shared OpenAPI Mapper Task Approval Draft 1 — Cold Review R6

## Review target

- Document: `features/FEAT-063-system-architecture-rearchitecture/plan/M2_S2_SHARED_OPENAPI_MAPPER_TASK_APPROVAL_DRAFT1_20261116.md`
- Size: 245,649 bytes
- SHA-256: `F04C21AFE3A6EC87B4479F6786B036F63BB58D098DDCE294FF3A1FBCF5883220`
- Review thread: `01a1e791-23ec-7781-8b7b-b1d5f339ae6f`
- Review mode: fresh-context, independent, read-only; the reviewer was instructed not to use tools, access files, or access the network.

## Receipt

The review thread receipt confirms delivery of all 31 document parts in sequence, without truncation, totaling 245,558 characters. The receipt binds those parts to the target document's 245,649-byte size and SHA-256 above. The reviewer confirmed the supplied text was reviewable.

## Verdict

**NOT READY — 0 P1, 3 P2, 2 P3.** This is a planning review only. It does not approve the task, authorize baseline collection, or authorize implementation.

## Findings

### P2 — Runner reads worktree files before source inventory validation

In §7, `task-runner.py` calls `normalized_environment_identity()` and reads/hashes `backend/pyproject.toml` and `backend/uv.lock` before the exporter validates the source inventory and Git status. Reorder the preflight so inventory paths and raw Git-status paths are validated and compared before any worktree file that may have changed is read.

### P2 — Expected source/test pins are not checked before export

The source/test pins listed in §1 and acceptance criteria in §2 are not all compared against expected hashes before export and app import. The runner checks the project and lock files, while the exporter captures current hashes and the comparator checks pre/post stability; these checks do not establish that the complete pre-export input state matches the pinned baseline. Add a pinned input manifest check before export/app import, requiring expected E-path pre-state hashes and all other relevant source/test pins to match; allow only the approved E/N post-state transitions.

### P2 — Comparator does not bind Git identity to the owner-pinned canonical executable

In §7, `schema-comparator.py` `source_compare.valid_git_identity()` checks that the Git path is absolute, ends in `git.exe`, and matches between pre/post state. It does not validate canonical path form or independently bind both path and hash to the owner-pinned identity. Reject noncanonical forms and require the expected owner-pinned path/hash.

### P3 — Exporter diagnostics include path values

In §7, `openapi-export.py` `source_state()` includes path values in `EXCLUDED_NO_READ` and unsafe/unclassifiable diagnostics, despite the generic-diagnostic rule. Remove path values from these messages and manifest errors.

### P3 — Process launch exceptions can leave incomplete artifacts

The disclosed process-launch limitation remains: if `subprocess.run` raises before returning, expected-artifact states and the invocation log may be absent. The review noted this limitation is disclosed, with stop/no-retry behavior; the evidence record does not claim complete artifacts for this failure mode.

## Requested checks

1. **Inventory ordering:** The exporter validates inventory and raw Git-status path names before its own changed-file reads, but the runner reads `pyproject.toml` and `uv.lock` earlier.
2. **Pinned Git executable:** Runner/bootstrap/exporter check and invoke the supplied absolute Git executable path/hash; the comparator checks pre/post equality but does not bind identity to a canonical owner-pinned value.
3. **Pytest bootstrap:** `pytest-bootstrap.py` has exactly one `main()` definition and its module entry point invokes it. The comparator payload also has one `main()`.

## Review boundaries

The reviewer received the complete Draft 1 pin above. No approval or launch authority was granted. Draft 10's historical **ACCEPT WITH CORRECTIONS** verdict and its ComparisonRoot P2 are unchanged. S2 remains **PARTIAL / NOT COMPLETE**.
