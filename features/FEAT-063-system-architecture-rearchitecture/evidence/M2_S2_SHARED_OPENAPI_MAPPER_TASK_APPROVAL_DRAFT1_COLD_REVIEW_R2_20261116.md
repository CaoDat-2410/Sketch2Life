# M2-S2 Shared OpenAPI Mapper Task Approval Draft 1 — Cold Review R2

## Review identity

- Target: features/FEAT-063-system-architecture-rearchitecture/plan/M2_S2_SHARED_OPENAPI_MAPPER_TASK_APPROVAL_DRAFT1_20261116.md
- Reviewed pin: 227,888 bytes / SHA-256 7114A9116A54E10AF2615988014BBD0606F2A83D7EAA02C05D34C5EDA62F5349
- Prior review evidence: 5,173 bytes / SHA-256 D1DF030F356DBF2025562F3F635C52F7260721F1F79241E4E3F95F8DA61E5341
- Cold-review thread: 01a1e524-811a-7f31-ae36-69ab9dd606fe
- Completed review turn: 01a1e524-86e8-7f90-996e-48b02e1c50cd
- Review sandbox: read-only; thread bridge reported type=readOnly and networkAccess=false; no parent/forked thread.
- Verdict: READY for continued planning, with one retained P3 — P1: 0, P2: 0, P3: 1.

## Review findings

### Prior P2 — Unsafe changed-path names

The reviewer found this P2 closed. The active comparator validates changed-path names for canonical repository-relative form and rejects the reviewed absolute, drive/UNC, backslash, colon, empty/dot/dot-dot, control/nonprintable and noncanonical forms. It applies the case-insensitive no-read name and suffix policy before adding a row to maps. Rejections produce a generic diagnostic without echoing the rejected path. The active final CLI main uses the validated maps in its report path and returns nonzero when the invariant errors exist.

### Prior P2 — Compare/Check skipped complete environment validation

The reviewer found this P2 closed. Before the child launch for OpenApiExport, Compare, Pytest and Check, the task runner verifies the action-specific cleared environment and lock-resolved identity. The gate checks actual FastAPI against the owner-accepted 0.162.0–0.162.7 range and the uv.lock 0.162.0 pin, interpreter path and executable SHA-256, Python/platform/tags/markers, pyproject.toml and uv.lock hashes, the normalized installed distribution inventory against owner evidence, and every non-FastAPI installed version against the resolved records. The run manifest contains sanitized environment identity and counts/digests for installed and resolved maps; credential values, credential hashes and raw environment are excluded.

### Retained P3 — Process-launch artifact gap

This finding remains unresolved by direction. If subprocess.run raises before returning, the current task runner writes a failure manifest but does not reach expected-artifact enumeration or invocation-log creation; the failure record may lack explicit MISSING/UNREADABLE states and a log. Draft 1 documents this as an outstanding P3 and does not claim complete artifact capture for this exception path. The runner payload behavior was not changed to fix it.

## Hash and coverage confirmation

All five embedded payloads matched their Draft 1 roster using the canonical UTF-8, no-BOM, LF, one-final-LF convention:

| Payload | Canonical bytes | SHA-256 |
|---|---:|---|
| task-runner.py | 30,188 | 8D41740875D3434FFAA3C5FC5D65E4470690C227B084D6DF99FB6FE965C81953 |
| child-bootstrap.py | 9,669 | DEF61BBD36153C4F201B57E28387CE1D6CCCF33C5B5CC8CF63503D221C1EFF3D |
| openapi-export.py | 28,143 | D56152CC724E163A2361775BB37BE46BFF7D12363B4E00782181EE44369695E8 |
| schema-comparator.py | 49,836 | C0B7100D33375783DC4E94EB9D0FD49CD823BB913CE0DC5EC9F2EB35E6BABDD1 |
| pytest-bootstrap.py | 16,864 | 5FACF389BC35C856DC84F21067C4ED973602A4EABD2A47E03D01B5E605F7E13D |

The review covered the exact Draft 1 pin and the prior cold-review evidence, including the active comparator path, task-runner environment gate, retained P3, and payload roster. The reviewer noted that no matching .codex harness file was found in the inspected worktree. The coordinator separately read the repository-parent .codex/sketch2life-harness.md; the worktree-local .codex directory is absent.

No embedded payload was executed or imported. No tests, typecheck, lint, validator, diff-check, baseline/export, application/runtime, database, install/sync, network/provider, or Modal command was run by the reviewer. The review thread made no file edits.

## Disposition

This is a planning review only. It does not approve the Task Approval record, baseline collection, implementation, or launch. Draft 10 remains ACCEPT WITH CORRECTIONS; S2 remains PARTIAL / NOT COMPLETE.
