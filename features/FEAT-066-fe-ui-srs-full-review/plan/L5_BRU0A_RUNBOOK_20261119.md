# BRU-0a owner-run runbook

Status: run instructions. The goal ran the positive run and the three negative controls on 2026-11-19 (see the BRU-0a evidence note, section "Goal run record"); the owner can repeat them with the steps below.

## 1. Start the backend from the bru0 source tree

`<repo-root>` is an owner-supplied placeholder for the root of the `bru0` worktree. Substitute its absolute path before running a command. The root backend virtual environment is outside the worktree and is referenced relative to it as `<repo-root>\..\..\backend\.venv\Scripts\`.

The repository's documented Uvicorn launch command is in `backend/README.md:17-21`. Use the root backend virtual environment executable, but point Python imports at the `bru0` source tree: the root environment's editable install points at the root checkout, which does not contain CONV-1. Starting with the `bru0` directory as the current directory is not sufficient. Uvicorn runs in the foreground; leave this terminal open.

In the first PowerShell terminal:

Set-Location '<repo-root>\backend'
$env:PYTHONPATH = '<repo-root>\backend\src'
& '<repo-root>\..\..\backend\.venv\Scripts\uvicorn.exe' sketch2life.main:app --host 127.0.0.1 --port 8000 --no-proxy-headers

Uvicorn stays in the foreground. In a second PowerShell terminal, use the same working directory and set the same `$env:PYTHONPATH` value before printing the imported package path:

Set-Location '<repo-root>\backend'
$env:PYTHONPATH = '<repo-root>\backend\src'
& '<repo-root>\..\..\backend\.venv\Scripts\python.exe' -c "import sketch2life; print(sketch2life.__file__)"

Record the printed `sketch2life.__file__` path. It must be inside `<repo-root>`. Also record the output of this read-only command: `git -C '<repo-root>' rev-parse HEAD`. If assertion 3 fails and `sketch2life.__file__` points outside `bru0`, the run is INVALID; this is not an A02 defect.

The route handler itself reads no database data. Whether the application process starts with no database is NOT VERIFIED. Record whether the running app is connected to the seed database or to none; A02 expects no database read. Do not write a database URL, database host, or credential in this runbook or run record. Use only the owner's existing local runtime configuration.

## 2. Owner run record

Create one run record for each owner run. Include:

- Bruno CLI version: @usebruno/cli 4.3.0
- Environment name: local
- Application worktree commit: output of git rev-parse HEAD in bru0
- Imported package path: printed sketch2life.__file__; it must be inside bru0
- Database connection: seed database or none; no database read is expected for A02
- Seed stage and non-sensitive database name pattern, if applicable; never a database URL
- Run classification: baseline or target
- Passed, failed, and skipped counts
- Each failed request path and error class only; do not record response headers or bodies
- Expected-failure list pin
- Exact `collection.bru` SHA-256

The positive run and each control must be recorded against the same exact `collection.bru` SHA-256. If that file changes, stop and re-pin before comparing results. `tmp/feat066-l5/` is relative to `<repo-root>`. Any reporter file or command output file must be under that directory and contain counts only. The hand-written run record lists each failed request path and error class, without response headers or bodies.

## 3. Positive A02 run

The Bruno collection root is `<repo-root>\features\FEAT-063-system-architecture-rearchitecture\artifacts\be-full\bruno`. From that directory, invoke only the request folder path below. Do not run from the collection root without a path:

Set-Location '<repo-root>\features\FEAT-063-system-architecture-rearchitecture\artifacts\be-full\bruno'
bru run requests/l5/shared/bru-0 --env local --reporter-skip-all-headers --reporter-skip-body

Run with @usebruno/cli 4.3.0. A valid positive run requires the loopback guard to pass and all three A02 assertions to pass. Until the positive run and the negative control both have recorded results, the guard remains unproven.

## 4. Negative guard control

Run each control against the same `collection.bru` SHA-256 recorded for the positive run. Expected guard results:

| Override URL | Expected guard message |
|---|---|
| `http://guard-test.invalid` | `only exact loopback hostnames are allowed` |
| `http://127.0.0.1@guard-test.invalid/` | `user-info is not allowed` |
| `http://localhost.guard-test.invalid/` | `only exact loopback hostnames are allowed` |

The `.invalid` domain is reserved and does not resolve. If a failed guard lets a control proceed to name resolution, it should end in a DNS error and cannot reach a real host; a DNS error is a failed control, not a passing guard result. The expected passing control result is the guard-named script or pre-request error shown above.

Run the A02 request once per control using the corresponding `baseUrl` override. The first command is:

bru run requests/l5/shared/bru-0 --env local --env-var baseUrl=http://guard-test.invalid --reporter-skip-all-headers --reporter-skip-body

Use the same command with `baseUrl=http://127.0.0.1@guard-test.invalid/` and `baseUrl=http://localhost.guard-test.invalid/` for the other two controls.

The --env-var override mechanism is verified (goal run 2026-11-19). The expected result is a script or pre-request error that names the L5 loopback guard, not a connection or DNS error. Record the error class and the run counts; zero traffic is not the criterion.

If the override does not apply, either run the control from a throwaway collection copy under `tmp/feat066-l5/`, or temporarily edit the tracked `environments/local.bru` and, after reverting it, verify that this command exits 0: `git -C '<repo-root>' diff --quiet -- features/FEAT-063-system-architecture-rearchitecture/artifacts/be-full/bruno/environments/local.bru`. This task does not edit an environment file. Never run `git add -u`.

Optional additional controls are http://127.0.0.1@guard-test.invalid/ and http://localhost.guard-test.invalid/.

## 5. Validity and guard limitations

A valid run uses the app started from the bru0 tree, has the package path inside bru0, passes the loopback guard, and passes assertions 1 through 3. An assertion-3 failure with a package imported from another tree is an INVALID RUN, not an A02 defect.

The candidate guard checks only the initial URL at pre-request time. Redirects and later URL changes are not covered. Interpolation, collection-script behavior and the --env-var override are verified with the CLI (goal run 2026-11-19); the URL global is absent in the CLI sandbox, so the guard parses by hand. Bruno desktop behavior is NOT VERIFIED.

## 6. B2 re-run and the full collection (2026-11-19)

The same steps were repeated from the B2 branch worktree with the application on port 8010 and the request-side override `--env-var baseUrl=http://127.0.0.1:8010` (no environment file edited). To run every request, pass the folder and the recursive flag: `bru run requests -r --env local --env-var baseUrl=http://127.0.0.1:8010 --reporter-skip-all-headers --reporter-skip-body`. Without `-r`, Bruno 4.3.0 runs zero requests for a folder that holds only sub-folders. The result record is `features/FEAT-066-fe-ui-srs-full-review/evidence/notes/B2_BRUNO_FULL_COLLECTION_RUN_20261119.md`.
