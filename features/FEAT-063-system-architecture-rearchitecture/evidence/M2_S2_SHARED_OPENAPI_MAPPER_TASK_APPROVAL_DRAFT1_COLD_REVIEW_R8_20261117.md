# M2-S2 Shared OpenAPI Mapper — Draft 1 Cold Review R8

## Review identity

- Reviewer session: `local_b3ba9d00-276f-41f5-a472-314a0d9f281f` ("Cold review R8 (Opus): mapper Task Approval Draft 1"), a separate session started with a fresh context by the coordinating Claude session.
- Reviewer model and effort: `claude-opus-5-5`, effort `high` (confirmed from the session metadata by the coordinating session).
- Reviewer tools: Read and Grep only. The brief forbade shell, Python, git, test, lint, typecheck, validator, web and write tools. This restriction was by instruction; unlike the Codex threads of R1–R7, the session was not placed in an OS sandbox with the network disabled. The reviewer reported no execution, write, stage or commit.
- Reviewed artifact: `features/FEAT-063-system-architecture-rearchitecture/plan/M2_S2_SHARED_OPENAPI_MAPPER_TASK_APPROVAL_DRAFT1_20261116.md`.
- Draft 1 pin: 301,590 bytes; SHA-256 `B422538517376D67243A861B771328036BF954F327CA36EA995929011F438699`; 3,805 lines; CRLF. The coordinating session checked this pin before the review started and again after it ended; both checks matched. The reviewer could not recompute hashes.
- Reviewer verdict: **NOT READY — 1 P1, 1 P2, 8 P3**.
- Review is planning-only. It does not approve the task, baseline collection, implementation, or launch.
- An earlier R8 attempt (session `local_85d321b4-5149-4861-8248-9a96f1546c23`) was stopped before it produced a verdict because it ran on a model the owner does not allow for independent reviews. It is not evidence and nothing from it is used here.

## Receipt completeness

The reviewer read the file directly, in these consecutive line ranges: 1–60, 61–150, 151–190, 191–340, 340–489, 490–649, 650–809, 810–929, 930–1029, 1030–1229, 1230–1429, 1430–1629, 1630–1829, 1830–2029, 2030–2229, 2230–2429, 2430–2629, 2630–2828, 2829–3028, 3029–3208, 3209–3408, 3409–3568, 3569–3805. It stated that lines 1–3805 were covered with no gap, that no truncation marker appeared and no line was cut off, and that a search for a trailing carriage return matched 3,805 lines. It also read the R7 review evidence in full. It did not read the source files pinned in the draft's §1.

## Findings (line numbers refer to the reviewed pin)

### F1 — P1 — The Compare action always fails, and its error output leaks local paths

Lines 1508–1510, 1524, 1575–1579 (runner), 1818 (bootstrap), 3409 (comparator); prose at 341 and 500. For Compare, the runner's `inputs` list holds the eight generated files plus `git.exe` and the lock evidence. All ten are forwarded as `-InputPaths` through the bootstrap to the comparator, which declares `-InputPaths` with `nargs=8`. The argument parser would reject the two extra values and exit with code 2, so Compare could never produce `passed: true`, and Pytest would be blocked. The parser's error text would print the two leftover absolute paths into `comparator.console.txt`, contrary to the path-free diagnostics claim. No false success would be recorded; the run fails closed. Required correction: forward only the eight generated inputs, in order, and repeat the static cross-check of argument counts.

### F2 — P2 — The comparator report that gates Pytest is never checked against a hash

Line 181 says a generated artifact must match its recorded manifest hash/state before it is read. For `field-delta-report.json` as used by Pytest, the card (570–578, 589–591), the runner (1457–1460), the child bootstrap (1841–1843) and the pytest bootstrap (3780) check the path only. No SHA-256 of the report or of the comparison run manifest is carried into the Pytest step, so the Pytest gate is not tied to the accepted comparison. Required correction: add the report hash as a Pytest card input and verify it before reading, or narrow the line 181 rule and disclose the gap.

### P3 findings

- **F3 — Pytest card ordering:** line 574 guards the pytest-bootstrap payload after the card's first `Get-FileHash` calls (567, 569), contrary to the rule at 179 and the R7 disposition at 905. Every file is still guarded before its own use.
- **F4 — Comparator echoes rejected path strings:** lines 2803, 2810, 2854 and 2861 put the path of a row that failed the duplicate or allowlist check into an error message that reaches the report, contrary to criterion 11 and line 907.
- **F5 — Line 343 overstates the comparator:** it says the comparator requires the exact fixture runtime-only set, but the comparator never references `PILOT_ONLY_OPERATIONS` or `PR22_UNCATALOGUED_OPERATIONS`; only the pytest selection covers that check.
- **F6 — Dead code contradicts criterion 4:** `compare_pair` (3054–3137) is never called and contains prefix-only description acceptance.
- **F7 — Initial hash manifest overwritten:** the Compare card writes `sha256.txt` (457, 480) and the runner overwrites it (1623–1629) with a different row set, while the prose at 500 implies the initial manifest is kept.
- **F8 — `backend\tmp` created before the reparse check:** `tmp.mkdir()` (1394) runs before `guard_chain` (1398); line 175 says creation happens after validating the canonical worktree/backend.
- **F9 — Line 152 blurs criteria 11 and 12:** it files pinned-input comparisons under accepted criterion 11, although the pinned-input manifest is criterion 12 material and criterion 12 is not accepted.
- **F10 — Catalog imported from the live worktree without a pin recheck:** the comparator (3423–3430) imports the catalog, amendments and SRS-projection modules at compare time and relies on the post-export source-state record; the gap between post export and compare should be disclosed or closed.

## R7 disposition as judged by R8

| R7 finding | Status |
|---|---|
| P2 external-input boundary/order | Resolved; residual ordering notes F3 and F8 |
| P3 launch exception | Resolved |
| P3 path-bearing diagnostics | Partially resolved; remaining leaks F4 and the argument-parser echo in F1 |
| P3 criterion 12 status | Resolved; minor wording issue F9 |

## Post-R7 correction check

The reviewer found all seven corrections listed in the draft's "Post-R7 coordinator consistency correction" note present in the body: `guard_chain` indentation, hash roster and `BOOTSTRAP_SHA256` consistency (not recomputed by the reviewer), Pytest/Mypy/Ruff guard calls (with the ordering problem F3), Compare `-PythonPath`, interpreter external check, baseline manifest as a generated artifact, and unreadable state marking evidence incomplete.

## Preserved scope and status

The reviewer confirmed that the draft claims no approval, launch authority, executed evidence or S2/S3 completion; keeps Draft 10's **ACCEPT WITH CORRECTIONS** verdict with its one ComparisonRoot P2; keeps the four-path E/E/N/R allowlist, mapper Option A, the `operationId` invariant, the OPEN fail-closed request-ID inventory, and the FastAPI 0.162.0–0.162.7 exception without calling 0.162.7 lock-matched; states `OWNER_MODAL_CALL_APPROVED=NO`; and keeps S2 **PARTIAL / NOT COMPLETE**. The §1 pin table matches `PINNED_INPUTS` in the exporter and the comparator row for row.

## Limits stated by the reviewer

It could not recompute any hash, and could not parse, execute, import, lint or typecheck any payload; syntax and behaviour were judged by reading. F1 rests on the documented behaviour of a fixed-count argument, not on a run. Factual claims about the pinned source files were not checked.

No Draft 1 change was made before this evidence file was written. No baseline, test, validator, approval-record edit, implementation, staging, commit or push was performed for R8.
