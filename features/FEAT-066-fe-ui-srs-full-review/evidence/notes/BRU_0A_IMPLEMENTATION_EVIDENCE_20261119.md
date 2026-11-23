# BRU-0a implementation evidence — 2026-11-19

Status (updated 2026-11-19): the six allowlisted artifacts are present. Sections up to "Not verified" record the state at first implementation, when no Bruno CLI or backend command had been run and the guard was an unverified candidate; they are **superseded** by "Goal run record" and "B2 re-run record" at the end, which verified the guard for the CLI (hand-written URL parser, `collection.bru` 2,638 bytes, SHA-256 `AD0A6A9A42A5038090725FF3E7615CCB9AA3BC070B951035E6D2774C0E9B69EE`). The R5 pin table's `collection.bru` row (1,300 bytes) and the 144-file count are likewise superseded (146 request files plus A02 now).

## Authority, scope, and preconditions

The approved FEAT-066 BRU-0a entry is APPROVED_FOR_IMPLEMENTATION and names D-066-78. Addendum 1 and D-066-79 prevail for the guard details. (In the record drafts for the repository these two decisions are numbered D-066-81 and D-066-82, because D-066-78 and D-066-79 already exist in the web and BE lineages.) The implementation follows that addendum: it does not stop for missing Bruno 4.3.0 material; it records the interpolation and URL-parser questions as NOT VERIFIED. No scope mismatch with the supplied prompt was found.

The approved plan pin in seed1 matched: PLAN_L5_BRUNO_COVERAGE_DRAFT3_20261118.md, 18,584 bytes, SHA-256 3F5AFCC727F3C43451903582FF0DBA05BC0F181290AA6D510B0B6C54973786A9. The pinned round-3 review matched: L5_DRAFT3_REVIEW_R3_20261119.md, 34,247 bytes, SHA-256 7766C981A0140439B571A9877FB9C309E6D32EB537FED1ECC5D32E3523E6D5CF.

The prepared worktree is on feature/feat066-bru0 at 4e2f6d96eb7d196867d0d1f049cbbf216f04c25c. Its initial git status --short was empty and the branch has no upstream. The coordinator had already created the worktree; this implementation session did not run git worktree add or any Git write command. The seed1 baseline and required ancestors matched. bruno/.env is ignored by .gitignore line 2; it was not opened. requests/firebase-auth-helper/ was not opened. No existing request or environment file was edited, and no folder.bru was added.

## New-file fingerprints

- `features/FEAT-063-system-architecture-rearchitecture/artifacts/be-full/bruno/collection.bru` — size and SHA-256 are re-pinned below after the R5 corrections.
- `features/FEAT-063-system-architecture-rearchitecture/artifacts/be-full/bruno/requests/l5/README.md` — size and SHA-256 are re-pinned below after the final-LF update.
- `features/FEAT-063-system-architecture-rearchitecture/artifacts/be-full/bruno/requests/l5/shared/bru-0/001-health-get.bru` — size and SHA-256 are re-pinned below after the lowercase header update.
- `features/FEAT-066-fe-ui-srs-full-review/evidence/L5_EXPECTED_TARGET_FAILURES.md` — size and SHA-256 are re-pinned below after the final-LF update.
- `features/FEAT-066-fe-ui-srs-full-review/plan/L5_BRU0A_RUNBOOK_20261119.md` — size and SHA-256 are re-pinned below after the R5 corrections.

This evidence note's own final size and SHA-256 are reported in the session handoff; embedding its own full-file digest would change that digest.

### R5 correction pins

| File | Bytes | SHA-256 |
|---|---:|---|
| `features/FEAT-063-system-architecture-rearchitecture/artifacts/be-full/bruno/collection.bru` | 1,300 | `485B68F577D7A05E0B2672D0E7D6964D80B324144EC3DCD33DCBBEC1F86BB220` |
| `features/FEAT-063-system-architecture-rearchitecture/artifacts/be-full/bruno/requests/l5/README.md` | 3,744 | `DF83FC281D17B9118A4FAA3846B0B35C9D250CAA6EC99473683B119C0816830B` |
| `features/FEAT-063-system-architecture-rearchitecture/artifacts/be-full/bruno/requests/l5/shared/bru-0/001-health-get.bru` | 660 | `73011D3514FF7CE6183EA01EA8DCDA38222A9950693B61A5B7C5321EDF5345EE` |
| `features/FEAT-066-fe-ui-srs-full-review/evidence/L5_EXPECTED_TARGET_FAILURES.md` | 48 | `DC35B7820B35929C19A3C1A69D7DB1E784D81DA902861820A6F34E81E90D67E7` |
| `features/FEAT-066-fe-ui-srs-full-review/plan/L5_BRU0A_RUNBOOK_20261119.md` | 6,540 | `C454226EDBCFD1BD9F4953004A08CF395642248C68289FE91465D87E04D7AB25` |

The R5 update also removes the collection metadata keys other than `name`, changes the A02 response-header lookup to lowercase, replaces machine-specific runbook paths with owner-supplied `<repo-root>` placeholders, documents the foreground server and second-terminal import check, and adds three guard controls with their expected messages and shared collection pin requirement. All six artifacts end with one LF.

## A02 source evidence

| Named check | What the source proves | Source locations | Runtime status |
|---|---|---|---|
| A02 returns status 200 | The GET route is declared and the contract test asserts 200. | backend/src/sketch2life/interfaces/http/routers/health.py:16-18; backend/tests/contract/test_health.py:7-9 | Not run |
| A02 returns exact JSON | The handler returns the exact status/service object and the contract test asserts equality. | backend/src/sketch2life/interfaces/http/routers/health.py:18; backend/tests/contract/test_health.py:10 | Not run |
| CONV-1 response X-Request-ID is present and non-empty | be1_request_context creates or preserves the request ID and adds the response header when absent; the test checks that the /health header is truthy. The assertion does not compare the value. The request reads it with the lowercase name `x-request-id`. | backend/src/sketch2life/interfaces/http/app.py:430-447; backend/tests/contract/test_http_error_conventions.py:129-130 | Not run |

The request is auth: none and sends only Accept: application/json. It sends neither Authorization nor X-Request-ID. The three checks are separate named post-response tests. Checks 1 and 2 do not depend on check 3. The existing requests/health/090-health-health-get.bru is untouched.

The health route itself has no database read or database dependency in its handler. Whether the application process starts without a database is NOT VERIFIED.

## Guard candidate and verification boundary

collection.bru contains a collection-level script:pre-request candidate. Its first script comment marks it UNVERIFIED. It calls bru.interpolate(req.getUrl()), requires a string, parses it with URL, rejects user-info (including an authority containing @), allows only 127.0.0.1, localhost, and [::1], and throws guard-named errors on interpolation, type, parse, user-info, or host failure. If an uninterpolated template reaches URL parsing, the intended path is a parse failure and a guard-named throw. This behavior is a candidate design, not runtime proof.

The following questions remain NOT VERIFIED: whether bru.interpolate(req.getUrl()) is supported in the Bruno 4.3.0 pre-request sandbox and returns the interpolated request URL; whether URL is available there and reports the expected hostname representation; whether the collection-level script runs for every request in the CLI when a subfolder is selected; and how the CLI reports a thrown pre-request error. The --env-var baseUrl override is also NOT VERIFIED. Whether `res.getHeader` matches header names case-insensitively is NOT VERIFIED.

The following collection-format and CLI questions are also NOT VERIFIED: whether the `collection.bru` syntax accepts the current `meta` keys and `script:pre-request` block; how the CLI reacts to a `collection.bru` parse error; and whether the CLI parses a file ending with a final newline.

The intended CLI reach is every request in this collection: 144 tracked request files plus the local-only Firebase helper folder where it exists. This statement is CLI-only. Bruno desktop behavior is NOT VERIFIED. The initial URL check does not cover redirects or URL changes after the pre-request script. The README documents those limits and how to run a non-loopback request deliberately.

The owner-run positive loopback case must pass the guard and all three A02 assertions. The negative control must fail with a script or pre-request error naming the L5 loopback guard, not with a connection or DNS error. Record its error class and counts; zero traffic is not the criterion. The guard is unproven until both controls are recorded. The runbook is features/FEAT-066-fe-ui-srs-full-review/plan/L5_BRU0A_RUNBOOK_20261119.md.

## Static checks and validators

The host scan covered collection.bru and 001-health-get.bru only; the request uses {{baseUrl}} and no absolute URL literal host was found. The only hostnames listed in the guard are the three approved loopback names. The forbidden script API scan on both .bru files found zero matches. The required sensitive-pattern scan on all six new files found zero matches.

The byte scan found zero CR bytes and zero trailing-whitespace lines in all six files. Each new file was checked with git diff --no-index --check against the Windows NUL empty device because the sandbox denied creation of a scratch file. Each command returned exit 1 because the files differ from an empty input; there were no whitespace diagnostics. No scratch data file was saved.

The four required validators were run after the final evidence-note edit. Their exit codes were:
- python tools/validate_harness.py — 0
- python tools/validate_repository_security.py — 0
- python tools/validate_architecture.py — 0
- git diff --check — 0

No tests, Bruno CLI, Node, package manager, database, Docker, network, provider, Modal, or emulator command was run.

## Not verified

Not verified: any Bruno CLI behaviour (nothing was run).

Also NOT VERIFIED: whether the backend process starts without a database; Bruno desktop collection-script behavior; interpolation and URL-parser support in the CLI sandbox; the environment override; and the actual A02 assertions and guard controls against a running app.

## Goal run record (2026-11-19, goal v2 under the program approval)

- **Environment:** fresh disposable database `seed_bru0a_*` on the loopback container `frc08` (name pattern only), Alembic `upgrade heads` exit 0, S1 seed run twice (second run 0 new rows, all 16 counts equal to the expected counts). API started from the `be-integration` tree on 127.0.0.1:8000; `sketch2life.__file__` is inside that tree. Bruno CLI 4.3.0, environment `local`, app connected to the seed database.
- **First positive run failed:** the candidate guard threw "unable to parse the interpolated request URL". A throwaway collection showed that `bru.interpolate(req.getUrl())` works but the `URL` global is not defined in the CLI sandbox. A second candidate with regex literals failed in the CLI script preprocessor (esprima/decomment cannot tokenize a regex literal that contains slashes).
- **Fix:** `collection.bru` now parses the interpolated URL by hand with string methods. It rejects control characters, spaces and backslashes, non-http(s) schemes, any `@` in the authority, malformed ports, and every hostname other than `127.0.0.1`, `localhost` and `[::1]`.
- **Re-pinned `collection.bru`:** 2,638 bytes, SHA-256 `AD0A6A9A42A5038090725FF3E7615CCB9AA3BC070B951035E6D2774C0E9B69EE`. `requests/l5/README.md` and the runbook were updated to match; their pins in this note's R5 table are superseded by the files in the commit.
- **Positive run** (`requests/l5/shared/bru-0`): 1 request passed; the three A02 checks passed (status 200, exact JSON body, non-empty `x-request-id`). This confirms that `res.getHeader` with the lowercase name works.
- **Negative controls** (same `collection.bru` hash, `--env-var baseUrl=...`): `http://guard-test.invalid` and `http://localhost.guard-test.invalid/` fail with "only exact loopback hostnames are allowed"; `http://127.0.0.1@guard-test.invalid/` fails with "user-info is not allowed". All three are script errors naming the guard, not DNS errors. A request in a different folder (`requests/health`) with a non-loopback override is stopped by the same guard, so the collection script runs for other folders. `http://[::1]:9` passes the guard (connection refused, as expected); `http://127.0.0.1:abc` is refused by the guard.
- **Verified by this run:** interpolation, collection-script reach, `--env-var` override, error reporting, lowercase header lookup, the app starting against a seed database. **Still NOT VERIFIED:** Bruno desktop behavior; the app starting with no database.

## B2 re-run record (2026-11-19, branch `claude/feat066-b2-bruno-d20b0c`, cut from `6f10ec24`)

- **Environment:** a new disposable database (name pattern `b2_bru_*`) created on the loopback container `frc08` (127.0.0.1:55458); nothing dropped. `alembic upgrade heads` exit 0. The API ran from this worktree's `backend/src` (`sketch2life.__file__` inside this worktree) on 127.0.0.1:8010, connected to that database; the goal's port 8000 was not used. The Bruno request-side override was `--env-var baseUrl=http://127.0.0.1:8010`; no environment file was edited. Bruno CLI 4.3.0, environment `local`. The database was not seeded (the collection has no valid tokens, see the full-collection note).
- **`collection.bru` pin (unchanged since the goal run):** 2,638 bytes, SHA-256 `AD0A6A9A42A5038090725FF3E7615CCB9AA3BC070B951035E6D2774C0E9B69EE`.
- **Positive run** (`requests/l5/shared/bru-0`): 1 request passed; A02 status 200, A02 exact JSON body, non-empty `x-request-id` — 3 of 3 checks passed.
- **Negative controls** (same hash): `http://guard-test.invalid` and `http://localhost.guard-test.invalid/` fail with "L5 loopback guard: only exact loopback hostnames are allowed."; `http://127.0.0.1@guard-test.invalid/` fails with "L5 loopback guard: user-info is not allowed." All three are pre-request script errors naming the guard; none is inferred to have reached name resolution (from the error text; no traffic capture was taken, and the run output was not retained).
- **Request set after this task:** 146 tracked request files plus the L5 A02 request (147 requests run). Requests `145` and `146` were added for the C6 M9-B routes; `142` to `144`, `072`, `074`, `076`, `080` and `086` already carried the C4 and C5 changes. The full-collection classification is in `B2_BRUNO_FULL_COLLECTION_RUN_20261119.md`.
