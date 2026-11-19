# M2-S2 Shared OpenAPI Mapper — Draft 1 Cold Review R10

## Review identity

- Reviewer session: `local_136697ca-f747-40a7-9cc2-6dd4d47ce999` ("Cold review R10 (Opus): mapper Task Approval Draft 1"), a separate session started with a fresh context by the coordinating Claude session.
- Reviewer model and effort: `claude-opus-5-5`, effort `high`.
- Reviewer tools: Read, Grep and Glob only, by instruction; not an OS sandbox and the network was not disabled at OS level. The reviewer reported no execution, write, stage or commit.
- Reviewed artifact: `features/FEAT-063-system-architecture-rearchitecture/plan/M2_S2_SHARED_OPENAPI_MAPPER_TASK_APPROVAL_DRAFT1_20261116.md`.
- Draft 1 pin: 305,717 bytes; SHA-256 `CE02785CAFD8F763BF0ACA442BF3B2050BBFB0128CE4E0F75FD930F2371C0F35`; 3,759 lines; CRLF. The coordinating session checked this pin before the review started and again after it ended; both checks matched. The reviewer could not recompute hashes.
- Reviewer verdict: **NOT READY — 1 P1, 0 P2, 2 P3**.
- Review is planning-only. It does not approve the task, baseline collection, implementation, or launch.
- A second, sandboxed review (R11, Codex, read-only sandbox) was started on the same pin in parallel; it is recorded separately.

## Receipt completeness

The reviewer read the file directly in these consecutive line ranges: 1–150, 151–250, 251–400, 401–550, 551–700, 701–850, 851–970, 971–1120, 1121–1370, 1371–1620, 1621–1870, 1871–2070, 2071–2320, 2321–2570, 2571–2770, 2771–3020, 3021–3270, 3271–3520, 3521–3759. It stated that lines 1–3759 were covered contiguously and that no line appeared truncated. Supporting reads: the R9 evidence file, `docs/context/SRS_AUTHORITY.md`, the D-209 row of the FEAT-063 `DECISIONS.md`, a search of `.gitignore`, and name searches in eight pinned source/test/project files.

## Findings (line numbers refer to the reviewed pin)

### F-1 — P1 — The comparator's pinned-input check can never pass after implementation

Lines 2336, 2946, 2972–2980. The exporter writes each `pinnedInputStates` row as `{status, state, bytes, sha256}` with no `path` key, and the comparator requires exactly those four keys. The comparator then cross-checks every pinned input that has a non-blank status against its `changedPaths` row over `("path", "status", "state", "bytes", "sha256")`. The changed-path row carries the path string and the pinned-input row's `path` is always absent, so every Git-visible pinned input raises "pinned-input state differs from its Git-visible changed-path row". In the post state the N path always has status `??`, and both E paths are modified, so `passed` is always false, the comparator exits 2, the Compare card throws and consumes its single invocation, and Pytest can never start. Required correction: compare only `status/state/bytes/sha256`, or add `path` to the exporter row and the comparator's required key set; then recompute the affected roster hashes and obtain a fresh review. The reviewer stated that this defect predates R9.

### F-2 — P3 — The Mypy/Ruff delta ignores repeat counts

Lines 1944–1946; prose 612, 892. Signatures exclude line and column and the baseline/post delta is a set difference, so a new occurrence of a signature that already exists in the baseline produces no added signature. The prose does not say that repeated occurrences collapse. Required correction: compare signature counts (a multiset), or disclose the limitation.

### F-3 — P3 — Stale preflight label

Lines 55, 59. Line 55 is labelled "Read-only preflight for this in-place correction" but describes the R5-era check. No preflight is recorded for the R8 or R9 corrections, although the R9 correction changed the §1 SRS pins. Required correction: label line 55 as historical and record whether the 13 source pins and the new SRS, authority and DECISIONS pins were rechecked for this revision.

### Informational (no change required)

- The runner's appended `sha256.txt` rows use the bare file name, so the pre and post `environment.json` and `source-state.json` rows share names and differ only by order.
- The `sha256.txt` name filter noted as dead in R9 N-5 is still present and harmless.
- The comparator repeats the `copy`/`re` imports in the middle of the module.
- If Ruff returns a null `code`, the signature sort (outside the `try`) can raise; this fails closed after the raw output has been written.
- Removing a response status that carries an `X-Request-ID` header necessarily trips the OPEN request-ID check, consistent with criterion 9.

## R9 disposition as judged by R10

F-A resolved; F-B resolved and disclosed; F-C resolved; N-1 acceptably disclosed; N-2 resolved; N-3 acceptably disclosed; N-4 resolved; N-5 resolved in prose. The reviewer found that no R9 fix introduced a new defect, no name is used before definition, no syntax or indentation error is visible, and argument names and counts match at every hop.

## Section 1 pin check (text only)

All 13 source pins in the §1 table match `PINNED_INPUTS` in the exporter and the comparator; `BOOTSTRAP_SHA256` matches the roster; the SRS pin matches `SRS_AUTHORITY.md` and the D-209 row; the draft claims no more than D-209 says. File byte counts and hashes were not recomputed by the reviewer.

## Preserved scope and status

Confirmed by the reviewer: no approval, launch, executed evidence or S2/S3 completion claimed; Draft 10's **ACCEPT WITH CORRECTIONS** verdict and its ComparisonRoot P2 unchanged; four-path E/E/N/R allowlist; mapper Option A; `operationId` invariant; OPEN fail-closed request-ID inventory; FastAPI 0.162.0–0.162.7 exception with 0.162.7 never called lock-matched; `OWNER_MODAL_CALL_APPROVED=NO`; S2 **PARTIAL / NOT COMPLETE**; criterion 12 proposed and not accepted. Earlier findings still hold: external inputs are boundary-checked before being read, a launch exception leaves an honest failure record, safety diagnostics do not echo rejected paths, Compare forwards exactly eight inputs, and the comparator report is hash-checked before and after Pytest.

## Limits stated by the reviewer

All hash checks were skipped; the SRS text and the D-208 row were not read; runtime behaviour, the current Git state of the E and R paths, child environment variables added by an interpreter, and tool output formats were not established by static reading; source symbols were checked by name only.

No Draft 1 change was made before this evidence file was written. No baseline, test, approval-record edit, implementation, staging, commit or push was performed for R10.
