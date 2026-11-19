# M2-S2 Shared OpenAPI Mapper — Draft 1 Cold Review R7

## Review identity

- Review thread: `01a1e7b5-f14d-7642-99c0-0af7ea6c6f30` (fresh context, read-only sandbox, network disabled).
- Reviewed artifact: `features/FEAT-063-system-architecture-rearchitecture/plan/M2_S2_SHARED_OPENAPI_MAPPER_TASK_APPROVAL_DRAFT1_20261116.md`.
- Draft 1 pin: 262,855 bytes; SHA-256 `32EB2A238EF7F0CDF2D5C7354E1C8897F82AB07C94D8C094CB0DBD5A5CB584B2`.
- Character count used for transfer: 262,758 UTF-16 code units.
- Reviewer verdict: **NOT READY — 0 P1, 1 P2, 3 P3**.
- Review is planning-only. It does not approve the task, baseline collection, implementation, or launch.

## Transfer completeness

The document was sent as 33 contiguous numbered parts covering `[0,262758)`: parts 1–32 contained 8,000 code units each and part 33 contained 6,758. Each part received its exact numbered receipt. After the `COMPLETE` marker, the reviewer confirmed all 33 parts were present and contiguous and that no inter-part truncation was apparent.

The reviewer could not independently recompute the target byte count or SHA-256 because the review context had no file/tool access. The sending session independently checked the Draft 1 byte count, SHA-256, and character count before the final three parts and again after the review; both checks matched the pin above. The reviewer assessed the supplied transfer and payloads.

## Findings

### P2 — R6 runner preflight ordering remains incomplete

The runner defers worktree `pyproject.toml` and `uv.lock` reads for `OpenApiExport` and rejects arbitrary `InputPaths`, but it hashes the sibling bootstrap before exporter inventory validation and hashes `PayloadPath` before raw Git-status validation. Those paths and the lock-evidence path are not required to be outside the worktree, so the claimed preflight ordering is not enforced for worktree-located helper/evidence files.

Required planning correction: require and document that runner, bootstrap, exporter payload, and evidence inputs are outside the canonical worktree before reading them, or narrow the ordering claim to the pinned source inputs and account explicitly for these reads.

### R6 correction disposition

1. Runner/exporter source-input preflight ordering: **incomplete** (P2 above).
2. Exporter/comparator embedded pin manifest and pre/post state checks: **complete** per review.
3. Pinned Git executable path/hash propagation and source-state identity checks: **complete** per review.

### P3 findings

- **Process-launch exceptions:** if `subprocess.run` fails before returning, expected artifact states and the invocation log can be absent. The draft discloses this limitation; the reviewer says closing it would require finalizing artifact/log states on that exception path.
- **Path-bearing diagnostics:** source-state errors such as `EXCLUDED_NO_READ` interpolate a path, contrary to criterion 11's generic-diagnostic requirement. The reviewer recommends sanitizing path-bearing diagnostics and aligning the retained-note scope with the actual behavior.
- **Acceptance disposition coverage:** active criteria run through criterion 12, while the recorded owner disposition accepts criteria 1–11 only. Record criterion 12 as proposed/not accepted or obtain and record its planning disposition.

## Preserved scope and status

The reviewer confirmed the draft preserves Draft 10's **ACCEPT WITH CORRECTIONS** status and ComparisonRoot P2, the Rev68 boundary, E/E/N/R allowlist, Mapper Option A, the `operationId` invariant, request-ID OPEN/fail-closed treatment, and S2 **PARTIAL / NOT COMPLETE**. No approval or launch authority was granted.

No Draft 1 change was made after this review. No baseline, test, validator, approval-record edit, implementation, staging, commit, or push was performed for R7. The authorized correction and single review are consumed; stop for owner direction before any further planning correction or review.
