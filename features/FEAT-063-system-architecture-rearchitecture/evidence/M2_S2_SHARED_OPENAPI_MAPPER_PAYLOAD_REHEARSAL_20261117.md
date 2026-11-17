# M2-S2 Shared OpenAPI Mapper — payload rehearsal on a synthetic worktree (2026-11-17)

## What this is, and what it is not

After four consecutive review rounds each found a defect that would make a command card fail on its first real run, the owner authorized (chat, 2026-11-17: "Cho chạy thử") a rehearsal of the Draft 1 payloads on synthetic data. This file records that rehearsal. It is **not** baseline evidence, **not** a run of any command card against the approved worktree, and it consumed **no** task ceiling. It approves nothing and launches nothing.

- Payload source: the five §7 fence bodies of Mapper Task Approval Draft 1 at pin 312,017 bytes / SHA-256 `B2638560DEF35B2B897BBE11BE6A1F6E0B0716698E0A8D78F7FBCFD74862F2D2`, materialized under the repository-root `tmp/m2-s2-mapper-rehearsal/run-56933b20/payloads/` after their roster hashes were verified.
- Rehearsal copies differ from the reviewed bytes only by two constants (`WORKTREE` and `EXPECTED_HEAD`, pointed at the synthetic repository). "Variant B" additionally carries the candidate correction for R12 F-1.
- Synthetic worktree: a new Git repository under the same `tmp` run folder, on a branch named like the real one, containing byte copies of the 13 pinned source/test/project/lock files only. The two E paths and the R path were committed as placeholders and then overwritten with the real bytes so that they are Git-modified, as in the real worktree. No other application source was copied, so the application cannot be imported there.
- Interpreter: the lock-exact environment described in the owner evidence package (Python 3.12.10, 107 of 107 distributions equal to the lock resolution, FastAPI 0.162.0). Lock evidence: `lock-resolution.json` from that package. Git: `C:\Program Files\Git\ucrt64\bin\git.exe`.
- To see why a payload stopped, each action payload was started through a small wrapper that calls the payload's own `main()` and writes any traceback to a file outside the synthetic worktree. The task runner and the child bootstrap ran unwrapped.
- The real worktree was not written: its Git status count was unchanged before and after, and `backend/tmp` does not exist there.
- Driver: repository-root `tmp/m2-s2-mapper-r8/rehearse.py`.

## Results

| Step | Result |
|---|---|
| OpenAPI export, pre, payloads as reviewed (variant A) | Failed closed in the exporter with "effective child environment category or path mismatch"; `source-state.json` present, `environment.json` and both schema files missing. This reproduces R12 finding F-1 by execution. |
| OpenAPI export, pre, with the F-1 correction (variant B) | Runner preflight, lock-evidence validation, Git pin, source-inventory match, pinned-input states and environment identity all passed; `source-state.json` and `environment.json` were written. The exporter then stopped at the first application import that the synthetic tree cannot satisfy (`ModuleNotFoundError`), which is the intended rehearsal boundary. |
| OpenAPI export, post (variant B), after creating the N test file in the synthetic tree | Same as pre: all checks before the application import passed, including the post inventory row and the N-path state. |
| Compare (variant B), using the two real `environment.json` and `source-state.json` files and four minimal stand-in schema documents | The comparator ran to completion and wrote its report. `sourceState.errors` was empty: allowlist transitions, pinned-input cross-check (the R10 F-1 correction) and source-state comparison passed on manifests written by the real exporter. All 138 reported errors concern schema content (for example 134 "runtime pre-schema missing catalog key"), as expected for empty stand-in schemas. `sha256.txt` kept the card's line and gained the runner's rows. |
| Ruff baseline and Ruff post (variant B) | Both succeeded end to end; the post comparison used the baseline manifest and reported no added signature; `check-raw-output.txt` present and hashed. |
| Mypy baseline (variant B) | Captured, but `unparsedCount` was 1 and the action failed closed. The unparsed line was a Mypy file-level error with no line number (`<path>: error: Source file found twice under different module names…`). That particular error is an artifact of the synthetic tree, which has no `__init__.py` files; the parser gap for file-level errors is real. |
| Pytest (variant B), with a stand-in comparator report | The report pin was accepted by the runner, the child bootstrap and the pytest bootstrap; pytest started and wrote JUnit output, then stopped at collection because the application is absent. |

## Defects and observations for Draft 1

1. **Confirmed (R12 F-1, P1):** the exporter must validate the child environment against the run root, not the worktree root. The one-line correction used in variant B is sufficient to pass that check.
2. **New (P3):** the Mypy output parser treats a file-level diagnostic without a line number as unparsed, which makes the Check action fail closed if Mypy emits one.
3. **Observation:** pytest's own console output can contain absolute local paths (seen in a collection error). This is tool output, not a safety diagnostic, and should be disclosed with the other console residuals.

## Not covered by this rehearsal

Application construction, the content of real runtime and published schemas, every comparator rule about schema content, the three real pytest selections, and Mypy on the real package tree were not exercised, because the synthetic tree does not contain the application. Those remain covered only by static review until the separately authorized baseline run.
