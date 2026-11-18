# M2-S2 Shared OpenAPI Mapper — Draft 1 Cold Review R13 (sandboxed)

## Review identity

- Reviewer: Codex CLI v0.169.0, non-interactive run (`codex exec --sandbox read-only`), fresh thread, default model `gpt-6-luna` at reasoning effort `max` as in the earlier run of the same day; the reviewer reported its model as "GPT-6/Codex".
- Environment reported by the reviewer: filesystem sandbox **read-only**; network **restricted**; no network call made.
- Reviewer commands: `Get-Item`, `Get-FileHash`, `Get-Content`, `Select-String`, `Test-Path`. No payload, test or validator executed; no file written.
- Reviewed artifact: `features/FEAT-063-system-architecture-rearchitecture/plan/M2_S2_SHARED_OPENAPI_MAPPER_TASK_APPROVAL_DRAFT1_20261116.md`.
- Draft 1 pin: 312,017 bytes; SHA-256 `B2638560DEF35B2B897BBE11BE6A1F6E0B0716698E0A8D78F7FBCFD74862F2D2`; 3,787 lines. The reviewer computed the pin before and after the review; both matched. The coordinating session also checked it.
- Reviewer verdict: **NOT READY — 0 P1, 2 P2, 0 P3**.
- Review is planning-only. It does not approve the task, baseline collection, implementation, or launch.
- This review ran in parallel with R12 (Claude Opus 5.5, not sandboxed) on the same pin. R12 reported a P1 (exporter environment root) that this review did not report; this review reported two P2 findings that R12 did not report. Both sets stand.
- The reviewer's verbatim final message is kept outside Git at the repository-root path `tmp/m2-s2-mapper-r8/R13_CODEX_REPORT.md` (6,036 bytes).

## Receipt completeness

The reviewer listed 76 consecutive ranges from 1–100 through 3741–3787 (one overlap, 3541–3550) and stated that lines 1–3787 were covered contiguously with no truncated or unread line.

## Findings (line numbers refer to the reviewed pin)

### P2 — Comparator no-read policy misses `.env*` path components

Lines 126, 2689–2691, 2789–2801. Criterion 11 says the comparator applies the no-read policy to every path component and filename. The exporter does so (2065–2070), but the comparator's `NO_READ_PARTS` omits `.env` and `_safe_changed_path` checks `.env` only on the final filename, so a path such as `.env-cache/file.py` passes the comparator's independent check. Required correction: reject `.env`-prefixed names in every path component, consistent with the exporter.

### P2 — Criterion 12 is operationally enforced while marked unaccepted

Lines 128, 167, 2333–2361, 2541–2556, 2957–3052. Criterion 12 is explicitly proposed and excluded from the current acceptance set, yet the exporter makes pinned-input validation errors prevent `safeToCompare` and the comparator requires those states and compares immutable pins, which makes criterion 12 a mandatory export/comparison gate. Required correction: remove that gate from the accepted path, or revise the proposal so criterion 12 is presented for owner acceptance before it becomes mandatory.

## R10/R11 disposition as judged by R13

R10 F-1 resolved; R10 F-2 resolved; R10 F-3 resolved; R11 P2 resolved (the report hash is forwarded, checked before the pytest bootstrap reads it and again after pytest, and hashed and parsed from the same bytes); R11 P3 resolved with the residual disclosed.

## Section 1 pin check (hashes computed by the reviewer)

All 13 present source/test/project/lock pins matched their byte counts and SHA-256 values; the N path was absent; `uv.lock` records FastAPI 0.162.0. The SRS authority record (5,120 bytes), the canonical SRS (701,157 bytes) and the FEAT-063 decisions file (219,748 bytes) matched. The draft's statements about D-209 are supported by the D-209 row. The reviewer did not recompute the §7 payload roster hashes in this round.

## Preserved scope and status

Confirmed by the reviewer: Draft 10 remains **ACCEPT WITH CORRECTIONS** with its ComparisonRoot P2; four-path E/E/N/R allowlist; mapper Option A; `operationId` invariant; OPEN fail-closed request-ID inventory; FastAPI 0.162.0–0.162.7 exception with 0.162.7 never called lock-matched; `OWNER_MODAL_CALL_APPROVED=NO`; S2 **PARTIAL / NOT COMPLETE**; no approval, launch authority, executed evidence or S2/S3 completion claimed. Criterion 12 remains textually proposed and unaccepted, but its active payload gate conflicts with that status (second finding).

## Limits stated by the reviewer

No payload was executed or validated, no test was run, and the optional R10/R11 review files were not read.

No Draft 1 change was made before this evidence file was written. No baseline, test, approval-record edit, implementation, staging, commit or push was performed for R13.
