# M2-S2 Shared OpenAPI Mapper Task Approval Draft 1 — Cold Review

## Review identity

- Target: `features/FEAT-063-system-architecture-rearchitecture/plan/M2_S2_SHARED_OPENAPI_MAPPER_TASK_APPROVAL_DRAFT1_20261116.md`
- Reviewed pin: 221,869 bytes / SHA-256 `0BFB887C0EE52B102FFBC4FC0272378846361E662C79AAA851E1E86B5CF04878`
- Cold-review thread: `01a1e4f3-6272-7a82-bedd-bcaecd0263f2`
- Completed review turn: `01a1e4f5-7a10-7390-bf6c-47bb8c0ed001`
- Review sandbox: read-only; thread bridge reported `networkAccess=false`.
- Verdict: **NOT READY** — P1: 0, P2: 2, P3: 1.

The initial turns in this same thread could not inspect the worktree because the first prompt overbroadly prohibited all commands and the reviewer could not see the bridge-reported network setting. The coordinator clarified that read-only file inspection was allowed, supplied the exact bridge settings, and the reviewer then completed the static review. No second review thread was created.

## Findings

### P2 — Changed-path names are not independently validated by the comparator

The active `_validated_changed_paths` checks that each path is a nonempty string, sorted, and unique, but it does not reject absolute paths, `..`, backslashes, or sensitive-path names. An unchanged malformed row such as `../.env` can pass the non-allowlist pre/post comparison. This conflicts with criterion 11's repository-relative forward-slash path rule and fail-closed handling. Add path-format and denylist checks before inserting changed-path rows into the report map.

References: Draft 1 criterion 11 (§2, around line 91); `_validated_changed_paths` (around line 1892); active report validation (around line 2602).

### P2 — Compare and Check do not enforce the complete lock-resolved environment

The task runner checks the lock-evidence hash and binds the executing interpreter path and executable hash to it, but Compare and Check do not verify the actual FastAPI version or installed distribution set. The exporter and pytest bootstrap perform those checks; `run_check` does not, and the comparator runs without them. A site-packages change under the same interpreter executable could therefore violate the stated environment constraint without stopping those actions. Enforce and record the full environment identity for every action.

References: environment requirements (§3, around line 94); task-runner identity check (around line 881); Check implementation (around line 1166).

### P3 — A process-launch exception leaves incomplete failure artifacts

If `subprocess.run` raises before returning, the runner records a failure string and writes the run manifest, but does not reach expected-artifact enumeration or log creation. The manifest therefore lacks the promised explicit `MISSING`/`UNREADABLE` states and invocation log record. Initialize and finalize those records on this exception path.

References: runner evidence requirement (§3, around line 116); task-runner failure path (around line 961).

## Review coverage and result

The reviewer recomputed the five embedded payload hashes using the stated LF and final-newline convention; all byte counts and hashes matched the Draft 1 roster. The review found the requested corrections otherwise complete: Option A uses exact `(method.lower(), path)` keys; `operationId` is checked as a nonempty, unchanged, unique invariant; E/E/N/R and N pre/post rules align across the task record and payloads; and the active final comparator validates transition/state rows before building report maps. The earlier comparator `main()` around line 2205 is shadowed by the active CLI `main()` around line 2500. The prior duplicate-`main()` P3 observation remains out of scope and was not counted in this verdict.

The task record keeps OS-level egress blocking owner-provided and unverified and does not claim runtime, network, database, or provider isolation. This is a planning review only. It does not approve the Task Approval, authorize baseline collection or implementation, or establish S2 completion. Draft 10 remains **ACCEPT WITH CORRECTIONS**; S2 remains **PARTIAL / NOT COMPLETE**.

## Reference pins checked by the reviewer

| Input | Size | SHA-256 |
|---|---:|---|
| Draft 10 | 63,397 bytes | `8D486CEC1F84B4A195124A13851142827EDE7BFBB635E9F5737798C45531E6EA` |
| Draft 10 cold review | 3,508 bytes | `3550014378EB0D27B7D91AE56C8032948ECF0752B8956E5C28CFBF5BF76897FA` |
| Canonical Rev68 SRS | 639,948 bytes | `69C83FE49CD4689D5D2540656D3319721838CF7343BAD00E24CDE558B8F5E944` |
| `docs/context/SRS_AUTHORITY.md` | 4,313 bytes | `D6153D38000C95E43A4091C5DF2E856FAD872A33177E3A8542E30EF2BEDCAB60` |
| Feature-local `TASK_APPROVAL.md` | 410,676 bytes | `C6A506404AF68A6180E150B83DE120113CE5EA54FCD7DEDFF9EAB01E4D375088` |
| S2 implementation report | 25,879 bytes | `F49D1FDB2B3C26387FFABC51C316F226C5D1FC5FC12B4856B0A6172A81941F55` |

No payload, test, typecheck, lint, validator, diff-check, baseline, application, or runtime command was executed for this review. No source, test, approval, SRS, decision, or implementation-report file was edited. No staging, commit, push, reset, restore, stash, clean, or deletion occurred.
