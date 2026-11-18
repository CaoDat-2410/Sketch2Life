# M2-S2 Shared OpenAPI Mapper — Draft 1 Cold Review R14

## Review identity

- Reviewer session: `local_16fd78ed-8b69-4474-ae7f-eb93cafa9942` ("Cold review R14 (Opus): mapper Task Approval Draft 1"), a separate session started with a fresh context by the coordinating Claude session.
- Reviewer model and effort: `claude-opus-5-5`, effort `high` (confirmed from the session metadata by the coordinating session).
- Reviewer tools: Read, Grep and Glob only, by instruction; not an OS sandbox and the network was not disabled at OS level. The reviewer reported no execution, write, stage or commit.
- Reviewed artifact: `features/FEAT-063-system-architecture-rearchitecture/plan/M2_S2_SHARED_OPENAPI_MAPPER_TASK_APPROVAL_DRAFT1_20261116.md`.
- Draft 1 pin: 318,297 bytes; SHA-256 `9A56F151240940FD3119D1B2F5B0CDB7575F743C0764A2A225A504579E18ACA0`; 3,803 lines; CRLF. The coordinating session checked this pin before the review started and again after it ended; both checks matched. The reviewer could not recompute hashes.
- Reviewer verdict: **NOT READY — 0 P1, 0 P2, 3 P3**. The reviewer stated that all three findings are small corrections to wording or a single check and that it found nothing that would make any of the seven cards fail on its first real run.
- Review is planning-only. It does not approve the task, baseline collection, implementation, or launch.
- A sandboxed review (R15, Codex, read-only sandbox) was started on the same pin in parallel; it is recorded separately.

## Receipt completeness

The reviewer read the file directly in these consecutive line ranges: 1–150, 151–300, 301–500, 501–700, 701–900, 901–1050, 1051–1250, 1251–1450, 1451–1650, 1651–1850, 1851–2050, 2051–2250, 2251–2450, 2451–2650, 2651–2800, 2801–3000, 3001–3200, 3201–3350, 3351–3500, 3501–3650, 3651–3803. It stated that lines 1–3803 were covered with no gap and that no line appeared truncated. Supporting reads: the R12, R13 and rehearsal records, `docs/context/SRS_AUTHORITY.md`, the D-209 row, `.gitignore`, and targeted reads of seven pinned source/test files; beyond the brief's strict list it also ran one file-name search for `__init__.py` and two text searches under `backend/src`.

## Findings (line numbers refer to the reviewed pin)

### F-1 — P3 — The draft's rehearsal statements do not match the rehearsal record it cites

Line 1022 says rehearsal copies "differing only in two path/HEAD constants, were executed once", while the record shows a variant B carrying the R12 F-1 code change, several runs, and a wrapper that calls each payload's `main()` instead of the child bootstrap's `runpy` path; line 919 does describe variant B, so §7 contradicts §5. Line 921 says that `_safe_changed_path` "was called with sample paths" during the rehearsal, but the cited record lists no such step. The reviewer agreed with the "not reproduced" disposition from its own reading of lines 2705 and 2805–2817. Required correction: align lines 1022 and 919 with the record, and either cite where the sample calls are recorded or recast line 921 as static reading.

### F-2 — P3 — The R12 F-1 fix does not quite use "the same path form the runner uses"

The runner builds the child environment from `Path(args.RunRoot).absolute()` of the card's string (1445, 1611, 1726). The child bootstrap first calls `resolve(strict=True)` on RunRoot (1853) and forwards that resolved string (1882); the exporter then applies `.absolute()` to the already-resolved value (2627), as the pytest bootstrap does (3758). The string checks therefore pass only when the card's path matches the on-disk casing exactly; a mismatch fails closed. Line 919's claim is inaccurate. Required correction: forward the runner's unresolved RunRoot and Backend strings, or state the casing dependency accurately.

### F-3 — P3 — The Mypy baseline can count a run that stopped on a blocking error as a successful capture

The widened pattern (1940) now parses file-level lines, and the summary "Found N errors … (errors prevented further checking)" is skipped (1950), so a Mypy run that exits with status 2 without type-checking yields `unparsedCount 0` and `success: true` (1973–1974); the baseline card (680) does not check `toolExitCode`. The post cards still report NOT CLEAN, so no pass can result, but the baseline-relative signal would be empty. Required correction: treat a Mypy exit status of 2 or higher, or a summary containing "errors prevented further checking", as a failed capture, then recompute the child-bootstrap hash and the runner's `BOOTSTRAP_SHA256`.

## Data-flow tracing

The reviewer traced all seven cards end to end and found no defect: argument names and counts match from each card through the runner parser and forwarding code, the child-bootstrap parser and argument lists, to the payload parsers (Compare receives exactly eight inputs, Pytest exactly three selections); the run manifest and child result supply every key the cards read; source-state version 4 fields, the four-key `pinnedInputStates` rows, the `gitExecutable` object, the 26-key environment identity and the three expected-artifact lists match between writer and reader. For the part the rehearsal could not reach, it confirmed by reading that `create_app()` takes no required argument, that the runtime schema is stored on `application.state` when `openapi()` is called, that the settings and `be1_runtime` symbols exist, that no application is constructed at import time, that the comparator's schema rules mirror the source pipeline in `app.py`, and that both settings getters are cached.

## R12/R13/rehearsal disposition as judged by R14

R12 F-1 resolved (path-form residual F-2); R12 F-2 resolved; R13 `.env` finding — agreed not reproduced (evidence attribution corrected under F-1); R13 criterion 12 — resolved by owner decision, current-state statements agree, older lists are stated as historical, no formal approval claimed; rehearsal Mypy finding resolved (side effect F-3); pytest console paths and rehearsal coverage limits acceptably disclosed.

## Section 1 pin check (text only)

All 13 present rows match `PINNED_INPUTS` in the exporter and comparator; `BOOTSTRAP_SHA256` equals the roster value; the SRS pin matches `SRS_AUTHORITY.md` and the D-209 row; the draft claims no more than D-209 says.

## Preserved scope and status

Confirmed by the reviewer: Draft 10 still **ACCEPT WITH CORRECTIONS** with its one ComparisonRoot P2; four-path E/E/N/R allowlist; mapper Option A; `operationId` invariant; OPEN fail-closed request-ID inventory; FastAPI 0.162.0–0.162.7 exception with 0.162.7 not lock-matched; `OWNER_MODAL_CALL_APPROVED=NO`; S2 **PARTIAL / NOT COMPLETE**; no approval, launch authority, executed evidence or S2/S3 completion claimed. Criterion 12 is recorded as accepted for planning, not formally approved.

## Limits stated by the reviewer

All hash checks were skipped and nothing was executed. Unverified: Windows path casing returned by `resolve()` for the real paths; PowerShell 5.1 quoting of native arguments containing spaces (such as the Git path); Mypy and Ruff output on the real package tree; pytest conftest files and plugins; whether the lock-exact environment exposes `sketch2life` through an editable install pointing elsewhere. One ordering risk was not checked: the exporter writes with sorted keys, and where an operation has more than one 2xx status the comparator's choice of the first 2xx may differ from the application's insertion-order choice.

No Draft 1 change was made before this evidence file was written. No baseline, test, approval-record edit, implementation, staging, commit or push was performed for R14.
