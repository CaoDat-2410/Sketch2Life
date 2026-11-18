# M2-S2 Shared OpenAPI Mapper — Draft 1 Cold Review R11 (sandboxed)

## Review identity

- Reviewer: Codex CLI v0.169.0, non-interactive run (`codex exec --sandbox read-only`), session `01a1e819-73f2-71e1-afc2-cd79bc17f45a`, model `gpt-6-luna`, reasoning effort `max`, fresh thread.
- Environment reported at start-up and by the reviewer: filesystem sandbox **read-only**; network **restricted**; approval mode on-request in a non-interactive run; no network call made.
- Reviewer commands: `Get-Content`, `Select-String`, `Get-Item`, `Get-FileHash`, `Test-Path`. No file written; no payload executed or imported; no test, validator or Git command run.
- Reviewed artifact: `features/FEAT-063-system-architecture-rearchitecture/plan/M2_S2_SHARED_OPENAPI_MAPPER_TASK_APPROVAL_DRAFT1_20261116.md`.
- Draft 1 pin: 305,717 bytes; SHA-256 `CE02785CAFD8F763BF0ACA442BF3B2050BBFB0128CE4E0F75FD930F2371C0F35`. The reviewer computed this pin itself before and after the review; both matched. The coordinating session also checked it before and after.
- Reviewer verdict: **NOT READY — 0 P1, 1 P2, 1 P3**.
- Review is planning-only. It does not approve the task, baseline collection, implementation, or launch.
- This review ran in parallel with R10 (Claude Opus 5.5, not sandboxed) on the same pin; the two reviewers did not see each other's output. R10 reported a P1 (comparator pinned-input cross-check) that this review did not report, and this review reported a P2 that R10 did not report. Both sets of findings stand.
- A first run of the same brief (session `01a1e818-bb55-76f1-a605-29bcb6dacf46`) stopped before reading the artifact because the brief then required the network to be reported as "disabled" and the sandbox reports it as "restricted". The brief's environment paragraph was corrected to accept "restricted"; that stopped run is not a review.
- The reviewer's verbatim final message is kept outside Git at the repository-root path `tmp/m2-s2-mapper-r8/R11_CODEX_REPORT_RUN2.md` (7,170 bytes).

## Receipt completeness

The reviewer's first wide display of lines 1–150 was clipped by its tool; it discarded that display and reread in smaller ranges. It listed 73 consecutive ranges from 1–25 through 3706–3759 and stated that lines 1–3759 were covered contiguously with no truncated line.

## Findings (line numbers refer to the reviewed pin)

### P2 — Comparator report hash is not bound to the bootstrap's read

The Pytest card checks the comparator report hash before its own read and again after pytest (line 581 and following). The launched child reads the report again at lines 1877–1879, and the pytest bootstrap reads it at lines 3734–3736. Neither receives or checks the expected hash, and the runner records the digest it sees without comparing it with the card's pin (lines 1566–1572). A report changed during the invocation could affect `comparatorPassed` and be restored before the card's final hash check. The reviewer therefore judged R8 finding F2 only partially resolved, although §5 (line 922) calls it resolved. Required correction: pass the expected digest through the runner and bootstrap and verify it against the bytes immediately before parsing the report.

### P3 — PowerShell path guards can emit rejected paths in error output

The uncaught `Get-Item -ErrorAction Stop` calls in the path helpers (for example lines 206–207 and 216–217; the helpers are repeated in later cards) can surface filesystem errors that contain the path, contrary to the path-free diagnostic claim at line 936. Required correction: catch these filesystem errors inside the helpers and replace them with fixed, path-free diagnostics.

## R9 disposition as judged by R11

F-A resolved; F-B resolved; F-C resolved; N-1 acceptably disclosed; N-2 resolved; N-3 acceptably disclosed; N-4 resolved; N-5 resolved.

## Section 1 pin check (hashes computed by the reviewer)

- `docs/context/SRS_AUTHORITY.md`: 5,120 bytes; SHA-256 `CACA7EC03CB570F3276AEA3EAF9214F93DDEC19F3030671A47DB590E19F74726` — matched.
- Canonical SRS: 701,157 bytes; SHA-256 `B9B1F42D0BB118C19C81607D3913B7E4F1D8B6F673F0C3FBB6402888FEB675F5` — matched.
- FEAT-063 `DECISIONS.md`: 219,748 bytes; SHA-256 `00776DF5428F15F83633FB7205D8AC8F526A60710AC1204FA493B9FF4C303572` — matched.
- All 13 present source/test/project/lock rows matched their recorded byte lengths and SHA-256 values; the N-path test file was absent.
- The five §7 payload fence bodies matched their recorded canonical byte lengths and SHA-256 values.
- The draft's statements about D-209 are consistent with the D-209 row.

## Preserved scope and status

Confirmed by the reviewer: no approval, launch, executed evidence or S2/S3 completion claimed; Draft 10 remains **ACCEPT WITH CORRECTIONS** with its ComparisonRoot P2; four-path E/E/N/R allowlist; mapper Option A; `operationId` invariant; OPEN fail-closed request-ID inventory; FastAPI 0.162.0–0.162.7 exception with 0.162.7 not called lock-matched; `OWNER_MODAL_CALL_APPROVED=NO`; S2 **PARTIAL / NOT COMPLETE**; criterion 12 proposed and not accepted. External inputs are boundary-checked before content reads, child-launch exceptions produce a failed or explicitly incomplete record, and Compare forwards exactly eight inputs. The safety-diagnostic claim is contradicted by the P3 finding, and the comparator-report pin is incomplete as described in the P2 finding.

## Limits stated by the reviewer

Static review only: no payload was executed or parsed, no card command was run, and runtime behaviour, lock evidence and OS-level network isolation were not verified. Source and test file contents were not read (their hashes were checked). The SRS authority record and D-209 were read; the full SRS body was not.

No Draft 1 change was made before this evidence file was written. No baseline, test, approval-record edit, implementation, staging, commit or push was performed for R11.
