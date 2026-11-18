# M2-S2 Shared OpenAPI Mapper — Draft 1 Cold Review R12

## Review identity

- Reviewer session: `local_ec4cb823-837f-4ce6-b2c2-0981a54aae34` ("Cold review R12 (Opus): mapper Task Approval Draft 1"), a separate session started with a fresh context by the coordinating Claude session.
- Reviewer model and effort: `claude-opus-5-5`, effort `high`.
- Reviewer tools: Read and Grep only, by instruction; not an OS sandbox and the network was not disabled at OS level. The reviewer reported no execution, write, stage or commit. It did not read the optional R10 and R11 reports.
- Reviewed artifact: `features/FEAT-063-system-architecture-rearchitecture/plan/M2_S2_SHARED_OPENAPI_MAPPER_TASK_APPROVAL_DRAFT1_20261116.md`.
- Draft 1 pin: 312,017 bytes; SHA-256 `B2638560DEF35B2B897BBE11BE6A1F6E0B0716698E0A8D78F7FBCFD74862F2D2`; 3,787 lines; CRLF. The coordinating session checked this pin before the review started and again after it ended; both checks matched. The reviewer could not recompute hashes.
- Reviewer verdict: **NOT READY — 1 P1, 0 P2, 1 P3**.
- Review is planning-only. It does not approve the task, baseline collection, implementation, or launch.
- A sandboxed review (R13, Codex, read-only sandbox) was started on the same pin in parallel; it is recorded separately.

## Receipt completeness

The reviewer read the file directly in these consecutive line ranges: 1–120, 121–220, 221–370, 371–520, 521–650, 651–800, 801–920, 921–1020, 1021–1220, 1221–1420, 1421–1620, 1621–1820, 1821–2020, 2021–2220, 2221–2420, 2421–2620, 2620–2779, 2779–2938, 2939–3098, 3099–3248, 3249–3398, 3399–3548, 3548–3787. It stated that lines 1–3787 were covered contiguously and that no line appeared truncated.

## Findings (line numbers refer to the reviewed pin)

### F-1 — P1 — The exporter checks the child environment against the worktree root instead of the run root, so every OpenAPI export fails

`openapi-export.py` lines 2572, 2576 and 2610–2611; the checked values are at 2131–2143; the runner side is at 1249–1261 and 1710–1729; the prose it contradicts is at lines 173 and 343. `main()` sets `root = WORKTREE.resolve(strict=True)` and keeps the run root in `output`, then calls `normalized_environment_identity(root, backend, ...)` with the worktree root. That function requires `HOME`/`USERPROFILE`, `TEMP`/`TMP`/`TMPDIR`, the two AWS sentinel paths and `SKETCH2LIFE_BE1_ARTIFACT_ROOT` to sit under `root`, while the runner's `clean_environment` builds all of them under the GUID run root. The runner's own check and the pytest bootstrap use the run root correctly. The exporter would therefore always raise "effective child environment category or path mismatch" after writing `source-state.json`; the run fails closed (no false success), `environment.json` and both schema files are MISSING, and the pre-export card stops. Because Compare and Pytest depend on the exports, the whole sequence is blocked on its first real run. Required correction: pass the verified run root as the environment-root argument, keep the worktree root only for source identity and lock-file reads, make the exporter's path-string form match the runner's (`absolute()` versus `resolve()`), recompute the exporter roster hash, and record the fix in §5.

### F-2 — P3 — The R11 P3 residual disclosure leaves out two bare `Get-Item` calls

Compare card lines 427 and 433; disclosure at line 920. The disclosed residual names `Get-FileHash`, `Get-Content`, `New-Item` and `Set-Content`, but the Compare card also calls `Get-Item -LiteralPath … -ErrorAction Stop` outside the helpers at those two lines. Both follow a successful helper check of the same path, so the practical risk is low. Required correction: add those calls to the disclosed residual, or wrap them like the helpers.

## R10/R11 disposition as judged by R12

R10 F-1 resolved; R11 P2 resolved (every hop carries `-ComparatorReportSha256`, and hash and parse use the same bytes); R10 F-2 resolved; R10 F-3 resolved; R11 P3 mostly resolved with the incomplete disclosure F-2. Earlier guarantees still hold: external inputs guarded before first hash or launch, honest `FAILED_TO_START` record, path-free runner and exporter safety messages, exactly eight Compare inputs, and the report hash-checked before Pytest reads it. The reviewer traced the other six cards end to end as data and found argument names, counts and record shapes consistent between writers and readers.

## Section 1 pin check (text only)

All 13 present rows match `PINNED_INPUTS` in the exporter and the comparator; `BOOTSTRAP_SHA256` equals the roster value; the SRS pin matches `SRS_AUTHORITY.md` and the D-209 row; the draft claims nothing beyond D-209. The reviewer also confirmed by name that `tmp/` is git-ignored, that the two settings getters are cached (so the pytest bootstrap's `cache_clear()` calls are valid), and that the amendments and SRS-projection symbols the comparator uses exist.

## Preserved scope and status

Confirmed by the reviewer: Draft 10's **ACCEPT WITH CORRECTIONS** verdict and its one P2 unchanged; four-path E/E/N/R allowlist; mapper Option A; `operationId` invariant; OPEN fail-closed request-ID inventory; FastAPI 0.162.0–0.162.7 exception with 0.162.7 never called lock-matched; `OWNER_MODAL_CALL_APPROVED=NO`; S2 **PARTIAL / NOT COMPLETE**; criterion 12 proposed and not accepted; no approval, launch authority, executed evidence or S2/S3 completion claimed.

## Limits stated by the reviewer

All hash checks were skipped. Nothing was executed; the Windows behaviour of the cleared child environment, Mypy and Ruff output formats, pytest configuration, private helper call signatures and comparator import side effects remain unverified by static reading.

## Coordinator note on the review method

This is the fourth consecutive round (R8, R10, R12, with R11 a P2) in which a reviewer found a defect that would make a command card fail on its first real run. The owner and the coordinating session agreed on 2026-11-17 that if this round still reported a P1 or P2, further read-only rounds would be replaced by an owner-authorized rehearsal of the payloads on synthetic data outside the worktree. No such rehearsal has been authorized or run at the time of writing.

No Draft 1 change was made before this evidence file was written. No baseline, test, approval-record edit, implementation, staging, commit or push was performed for R12.
