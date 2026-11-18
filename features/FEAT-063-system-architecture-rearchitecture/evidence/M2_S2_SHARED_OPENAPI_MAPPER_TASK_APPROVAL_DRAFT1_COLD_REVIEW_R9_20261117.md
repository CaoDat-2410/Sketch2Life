# M2-S2 Shared OpenAPI Mapper — Draft 1 Cold Review R9

## Review identity

- Reviewer session: `local_84ea267d-41ad-4e40-9faf-5863f70511be` ("Cold review R9 (Opus): mapper Task Approval Draft 1"), a separate session started with a fresh context by the coordinating Claude session.
- Reviewer model and effort: `claude-opus-5-5`, effort `high` requested at launch.
- Reviewer tools: Read and Grep only, by instruction; not an OS sandbox and the network was not disabled at OS level. The reviewer reported no execution, write, stage or commit.
- Reviewed artifact: `features/FEAT-063-system-architecture-rearchitecture/plan/M2_S2_SHARED_OPENAPI_MAPPER_TASK_APPROVAL_DRAFT1_20261116.md`.
- Draft 1 pin: 301,425 bytes; SHA-256 `59878CFB2E9E03579B9284AF981E23E2E7A36414C7B265336C1520A2C431058E`; 3,741 lines; CRLF. The coordinating session checked this pin before the review started and again after it ended; both checks matched. The reviewer could not recompute hashes.
- Reviewer verdict: **NOT READY — 0 P1, 1 P2, 7 P3** (two P3 actionable, five informational).
- Review is planning-only. It does not approve the task, baseline collection, implementation, or launch.

## Receipt completeness

The reviewer read the file directly in these consecutive line ranges: 1–150, 151–300, 301–500, 501–700, 701–900, 901–1020, 1021–1270, 1271–1520, 1521–1770, 1771–2020, 2021–2270, 2270–2519, 2519–2718, 2719–2938, 2939–3158, 3159–3378, 3379–3578, 3579–3741. It stated that lines 1–3741 were covered contiguously and that no line appeared truncated. It also read the R8 evidence file in full and no source file from the draft's §1.

## Findings (line numbers refer to the reviewed pin)

### F-A — P2 — Mypy/Ruff check evidence does not keep the raw tool output or line locations the prose promises

Lines 874, 890 and 900 promise each check's complete console log; line 610 says source line numbers remain location metadata. In the child bootstrap, Mypy output is captured in-process, parsed and dropped (1882–1898), Ruff stdout/stderr are captured and never saved (1900–1912), line and column numbers are discarded, and the bootstrap prints nothing, so `check.console.txt` is empty. When `unparsedCount > 0` the sequence stops with no record of what failed to parse and no retry is allowed. Line 610 also says the identity uses a repository-relative path plus code/kind, while the code uses a backend-relative path plus severity. Required correction: write the raw tool output to a hashed artifact listed in the expected artifacts, or change the prose to say only normalized signatures and counts are kept.

### F-B — P3, actionable — Several child environment variables have no effect because the child runs with `-I`

The runner starts the child with `python -I` (1573), which ignores `PYTHONDONTWRITEBYTECODE`, `PYTHONUTF8`, `PYTHONNOUSERSITE` and `PYTHONPATH` (set at 1689–1690), while the manifests label them enabled (1315–1319, 2166–2170, 3627–3628). The bootstrap compensates for `PYTHONPATH` with a `sys.path` insert (1805); nothing sets `sys.dont_write_bytecode`. The exporter's app import, the comparator's catalog imports and pytest's assertion rewriting can therefore write `__pycache__` files next to worktree sources, which no section discloses. `text=True` decoding (1614, 1901) uses the locale encoding, not UTF-8. Required correction: set `sys.dont_write_bytecode = True` and decide UTF-8 handling in the bootstrap before any import or `runpy` call, or disclose the limitation.

### F-C — P3, actionable — One path-bearing diagnostic remains in the child bootstrap

`Path(...).resolve(strict=True)` at 1804 and the `child-result.json` write at 1871 are outside the bootstrap's `try`, and the entry point (1944–1945) has no generic handler, so a failure there prints a traceback with local paths into the console log, contrary to line 926. Required correction: add a generic top-level handler or disclose it.

### Informational notes (no change required before approval)

- **N-1:** the exporter parses the lock-evidence JSON before checking its hash (2535–2538); the pytest bootstrap parses before comparing (3703–3707); the runner verified the hash earlier (1500–1502).
- **N-2:** the export card hard-codes `pre` in the `$RunRoot` name (242); a post run must edit it by hand, and a mismatch fails closed but could use the post ceiling.
- **N-3:** the Pytest card's artifact lookups (591–593) do not require exactly one match, unlike 272–277; the runner always produces unique names.
- **N-4:** in §5 the "Risks / dependencies" heading (907) is empty and the risk bullets (929–936) sit under the R7 dispositions heading.
- **N-5:** line 503 omits `invocation.json` from the runner's appended `sha256.txt` rows, although the code includes it; the `sha256.txt` name filter at 1648 can never match.

## R8 disposition as judged by R9

F1 resolved (argument sets match at every hop); F2 resolved; F3 resolved; F4 resolved; F5 resolved; F6 resolved; F7 resolved; F8 resolved; F9 resolved; F10 acceptably disclosed.

## R7 carry-over check

External-input boundary/order holds; launch-exception record holds; path-free diagnostics hold with the residual F-C and the disclosed argument-parser echo; criterion 12 remains not accepted.

## Preserved scope and status

The reviewer confirmed all of: no approval, launch, executed evidence or S2/S3 completion claimed; Draft 10's **ACCEPT WITH CORRECTIONS** verdict and its ComparisonRoot P2 unchanged; four-path E/E/N/R allowlist; mapper Option A; `operationId` invariant; OPEN fail-closed request-ID inventory; FastAPI 0.162.0–0.162.7 exception with 0.162.7 never called lock-matched; `OWNER_MODAL_CALL_APPROVED=NO`; S2 **PARTIAL / NOT COMPLETE**; the SRS owner-direction bullet claimed no more than "not yet recorded"; the §1 pin table matches `PINNED_INPUTS` in the exporter and comparator and `BOOTSTRAP_SHA256` matches the roster, as text.

## Limits stated by the reviewer

No hash was recomputed and no payload was parsed, executed or imported. No §1 source file was read. The reviewer could not check whether `__pycache__` is ignored by Git, or whether the owner's interpreter adds environment variables to the child. The coordinating session checked the first point afterwards: the worktree `.gitignore` contains `__pycache__/`.

No Draft 1 change was made before this evidence file was written. No baseline, test, approval-record edit, implementation, staging, commit or push was performed for R9.
