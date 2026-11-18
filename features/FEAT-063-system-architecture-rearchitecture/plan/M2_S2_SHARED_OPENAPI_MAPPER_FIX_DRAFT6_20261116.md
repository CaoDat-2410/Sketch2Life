# FEAT-063 M2-S2 Shared OpenAPI Catalog Mapper — Draft 6

**Status: DRAFT / NOT APPROVED / NOT LAUNCHED.** This is a planning-only successor to Draft 5, prepared under the owner’s direct instruction to preserve the current Draft 5 bytes and use them as the observed predecessor. The owner authorizes this Draft 6 and one fresh independent cold review of its exact pin only. No source/test edits, baseline collection, tests, validation, typecheck, lint, build, approval, implementation, or launch is authorized. `OWNER_MODAL_CALL_APPROVED=NO`

**Date:** 2026-11-16  
**Worktree:** `D:\GitHub\Sketch2Life\.worktrees\m2-s2`  
**Branch / HEAD:** `feature/feat063-m2-s2` / `5de30674bc826591ad4b3cc00fca53c7597ead51`  
**Observed pre-Draft-6 status:** 74 paths: 24 modified, 50 untracked, 0 staged. This snapshot includes unpublished changes owned by the worktree. It is not a clean-tree claim.

## 1. Authority, status, and Draft 5 provenance

- The active BE worktree follows its `docs/context/SRS_AUTHORITY.md` pointer to the unsigned FEAT-063 v2.7-draft Rev68 SRS. Rev68 is a working source, not a signed product baseline. The mapper proposal adds no route or product requirement.
- D-207 remains limited to its approved S2 allowlist; the generic OpenAPI mapper is outside that scope. The FEAT-047 upload-description overlay and the prior combined S2 verification authorization are consumed. M2-S2 remains **PARTIAL / NOT COMPLETE**. M2-S3 is a separate gate.
- The current Draft 5 file observed before this plan is 29,568 bytes, SHA-256 `61D198C946F08535622ED00236D54DB6FC347A8AF960821BB3D2E6F99B652243`.
- The earlier Draft 5 pin in `CONTEXT.md`, `SOURCE_REGISTER.md`, the Draft 5 review evidence, and the original cold-review request is 29,568 bytes, SHA-256 `61D198C946085F35622ED00236D54DB6FC347A8AF960821BB3D2E6F99B652243`. The fresh review thread `01a1e286-d311-78c3-9e52-1998f4f05f58` explicitly targeted that earlier hash; its ACCEPT applies only to those earlier bytes. It is not acceptance of the current Draft 5 bytes.
- The owner has directed that the current Draft 5 bytes be preserved. This plan does not label the hash difference a typo, does not restore or overwrite Draft 5, and does not treat the prior ACCEPT as applying to the current file. The provenance discrepancy is recorded here for the new reviewer.
- Draft 5 §8 records a 73-path / 24-modified / 49-untracked / 0-staged observation. The current pre-Draft-6 observation is 74 / 24 / 50 / 0. This is a changed status snapshot; no existing path was cleaned, reset, or rewritten.
- Static source and prior evidence are not runtime evidence. No claim is made here that database or network access is impossible, that Boto3 credential discovery was exercised, or that the mapper fix works.

## 2. Mapper decision and identity rule

The owner has already selected mapper-design **Option A** for planning: look up catalog metadata by the exact public OpenAPI `(method.lower(), path)` key. Preserve the generated operationId as an invariant: it must remain unchanged and unique across the pre/post schema. operationId is **not** the runtime lookup key. The mapper must not bind catalog entries to Python handler names or callable identity.

This contract-identity choice retains a known stale-entry risk: if a different handler later reuses the same public method/path, the catalog metadata can still attach to that operation. The acceptance checks below detect key-set, identity-invariant, and neighboring-metadata errors; they do not prove Python callable identity or runtime endpoint behavior.

The owner’s separate **allowlist Choice A** is also settled and is not this mapper-design choice. It is recorded exactly in §4.

## 3. Read-only source findings and verification limits

The current pinned source shows:

- `Settings` extends Pydantic `BaseSettings`, declares `env_prefix="SKETCH2LIFE_"`, and defines `s3_access_key` and `s3_secret_key`. There is no custom settings-source configuration disabling process environment loading.
- Passing `_env_file=None` disables dotenv-file loading for that Settings construction; it does **not** disable process-environment loading.
- The exact pytest node named in §7 constructs two `Settings` objects directly (`settings` and `staging_settings`) without explicit S3 fields. It then monkeypatches `app_module.get_settings`. The intervening `disabled_settings` is a `model_copy` of `settings`, so it retains the same S3 fields.
- Therefore, if the pytest process starts with nonempty synthetic `SKETCH2LIFE_S3_ACCESS_KEY` and `SKETCH2LIFE_S3_SECRET_KEY` values, those values are read by both directly constructed Settings objects through the active process-environment source. They are retained by `disabled_settings`. Do **not** claim that the test’s Settings objects ignore those environment variables.
- That node makes five `create_app()` calls: with `settings`, `disabled_settings`, `settings` after swapping in a SQLite engine, with `staging_settings`, and with `settings` after the engine factory is set to raise the synthetic missing-configuration error. Its four created test engines are disposed in the node; the final call has no engine.
- All five calls use the combined default app profile. The current `create_app` source unconditionally constructs `lesson_library_storage` for the combined profile and passes the configured S3 key pair to its adapter. The test’s `test` and `staging` settings leave `storage_example_enabled` false, so they do not enter the additional local storage-example branch. They nevertheless construct the lesson-library S3 client.
- Separately, the OpenAPI catalog fixture sets local environment, synthetic pilot enabled, and storage-example enabled before creating the combined app; it therefore exercises both combined-profile storage constructions. A future OpenAPI exporter must supply the synthetic pair before settings construction so both receive the synthetic values.
- The S3 adapter passes both explicit Boto3 credential keyword arguments when both configured values are nonempty. Source inspection therefore establishes the application call path passes the synthetic pair. It does not constitute runtime proof of Boto3’s provider behavior or of network isolation; both remain unverified.
- With `STORYRUN_LITE_MAIN_DEMO_ENABLED=0`, source selects `lifespan=None`. Calling `app.openapi()` builds the schema; it does not start the server or ASGI lifespan. This is a static source finding, not a runtime safety claim.
- The combined app creates the BE1 runtime and engine and uses a local artifact root. Source inspection of `create_engine` or engine disposal does not prove that an execution could not access a database. A DB sentinel, artifact root under the isolated temporary root, engine disposal, and owner-confirmed OS-level egress blocking remain required.

The source-level S3 correction above supersedes any earlier statement that `_env_file=None` prevents process environment variables from populating the directly constructed Settings objects. No test was run to confirm behavior at runtime.

## 4. Exact proposed allowlist — owner selected Choice A

This is a proposal for a **future** separate Task Approval. It is not authorization to edit any listed file now.

| Mode | Path | Proposed future use |
|---|---|---|
| E | `backend/src/sketch2life/interfaces/http/app.py` | Apply catalog metadata to the generated runtime OpenAPI operation using only its exact method/path key. Do not traverse the route tree or inspect FastAPI private route classes for a handler-name guard. Preserve the current response projection, request-ID amendments, and unrelated examples. |
| E | `backend/tests/contract/test_openapi_contract_catalog.py` | Extend exact runtime/published operation-set checks, catalog metadata, duplicate-declaration detection, operationId invariants, and allowed-delta assertions. |
| N | `backend/tests/contract/test_openapi_schema_catalog_mapping.py` | Add pure mapper tests for exact-key hits, missing/unexpected/stale keys, duplicate source declarations, neighboring-key isolation, and preservation of unrelated operation fields. |
| R | `backend/tests/contract/test_app_composition.py` | Read-only input. Do not edit or expand the allowlist to change its fixture. Its exact selected node is a future verification selection only. |

No other source, test, dependency, SRS, DTR, decision, approval, evidence, or generated artifact path is in this proposed allowlist.

## 5. Acceptance criteria proposed for a future approved implementation

These are planning criteria only. Draft 6 is not implementation evidence.

1. The mapper receives the generated schema and catalog and looks up each operation only by exact lowercase method and exact path. It does not enumerate `application.routes`, flatten router trees, inspect private FastAPI route objects, or check a Python name/callable.
2. Compare exact method/path sets. Every catalog key appears once in the expected runtime schema; the runtime-only set remains exactly `PILOT_ONLY_OPERATIONS | PR22_UNCATALOGUED_OPERATIONS` for the same approved profile. Missing, stale, unexpected, and duplicate catalog declarations fail explicitly; counts alone do not satisfy the check.
3. A source-level declaration check detects duplicate `(method, path)` literal keys before Python dictionary construction can overwrite them. If the declaration format changes beyond the checker’s recognized form, fail closed.
4. For every catalog key, public tag and description match the catalog rules. Preserve the five established description-prefix exceptions, the restore route’s appended Access text, and its existing restore response-description behavior. Do not normalize those exceptions away or alter unrelated descriptions.
5. Catalog response projection preserves exact response statuses, media types, schemas, and descriptions, including restore-specific descriptions and status pruning. Preserve every existing response header except the allowed `X-Request-ID` addition/normalization on its existing path prefixes. Preserve existing request-ID parameter behavior.
6. For both the full runtime schema and the published `app.openapi()` projection, compare pre/post artifacts generated from the same route composition, profile, settings, lock-matched environment, and non-mapper amendments. Report field-level differences by method/path and JSON field pointer. The comparator fails on any unapproved change.
7. The only allowed schema deltas are the explicitly approved catalog tag/description/response-projection fields; the restore text and response-description behavior above; and the existing `X-Request-ID` parameter/header normalization on its existing prefixes. Preserve exact path/method sets, each operation’s `operationId` value and uniqueness, security metadata, request parameters and bodies, component schemas, and all non-`X-Request-ID` response headers.
8. Confirm no catalog metadata is applied to an adjacent operation with a different key. Uncatalogued operations and all unrelated fields remain unchanged. This is a schema assertion, not proof that a Python handler changed or was invoked.
9. A future lock-matched targeted run covers the three selections in §7. Its results must be reported with actual exit codes and output artifacts. M2-S2 remains **PARTIAL / NOT COMPLETE** until its separate owner-approved closure evidence is accepted; this mapper task alone does not close S2 or S3.

## 6. Future OpenAPI baseline and comparator — not approved or run

### Profile and artifacts

The pinned catalog-contract test fixture sets `SKETCH2LIFE_ENV=local`, `SKETCH2LIFE_SYNTHETIC_PILOT_ENABLED=true`, and `SKETCH2LIFE_STORAGE_EXAMPLE_ENABLED=true`, then calls the combined app profile with the StoryRun-lite main demo disabled by default. Its source-pinned expectations are 151 runtime operations, 134 catalog operations over 118 catalog paths, and 17 classified runtime-only operations. A future pre/post exporter must match this exact profile and route composition; changing flags changes the baseline.

From one app instance per pre/post generation:

- Save `application.state.runtime_openapi_schema` as the full runtime JSON.
- Save `application.openapi()` as the published SRS/OpenAPI projection. The current app source builds the runtime schema and passes it through `project_srs_v22_openapi` for this public projection.
- Do not use the existing `artifacts/be-full/openapi.runtime.json` as the pre-fix baseline: its pinned README describes an inventory with both optional local groups enabled and an earlier route snapshot. Do not use the Rev45 FE JSON as a current runtime baseline either. Generate fresh pre/post artifacts only after separate owner approval.
- Keep all output under a fresh GUID directory beneath `backend/tmp/openapi-mapper-draft6-<guid>/`, which is ignored by the current root `.gitignore`. Keep runtime/pre, published/pre, runtime/post, published/post, comparator JSON, and SHA-256 output there. The baseline and post artifacts must use the same absolute lock-matched interpreter, working directory, profile, environment allowlist, and exporter logic.

### Isolation required for a future exporter

The process must start with a cleared child-process environment and only the minimum OS/Python bootstrap variables plus the explicit allowlist. Before importing or creating the app, set both `SKETCH2LIFE_S3_ACCESS_KEY` and `SKETCH2LIFE_S3_SECRET_KEY` to nonempty synthetic, non-secret values; never print or log those values. Match the catalog fixture with `SKETCH2LIFE_ENV=local`, `SKETCH2LIFE_SYNTHETIC_PILOT_ENABLED=true`, `SKETCH2LIFE_STORAGE_EXAMPLE_ENABLED=true`, and `STORYRUN_LITE_MAIN_DEMO_ENABLED=0`. Also set `SKETCH2LIFE_AUTH_PROVIDER=development` and `SKETCH2LIFE_AI_PROVIDER=disabled`. Set `SKETCH2LIFE_DATABASE_URL` to a synthetic loopback-only sentinel and `SKETCH2LIFE_BE1_ARTIFACT_ROOT` to a path under the run root.

Use a fresh GUID `HOME` and `USERPROFILE` under the run root; set `TEMP`/`TMP` there as well. Set `AWS_EC2_METADATA_DISABLED=true`. Point `AWS_CONFIG_FILE` and `AWS_SHARED_CREDENTIALS_FILE` to distinct paths under the run root and preflight that those files do not exist; do not create or reuse them. Do not inherit ambient AWS, Firebase, Google, proxy, database, or provider credentials.

Settings defaults name an absolute repository .env file. Clearing process environment by itself does **not** disable dotenv loading. Before app creation, the exporter must use a reviewed process-local bootstrap that sets `Settings.model_config["env_file"] = None` and `CoreDatabaseSettings.model_config["env_file"] = None` (or an equivalently source-verified mechanism). Process environment loading remains active, so the synthetic S3 variables still reach every Settings instance. The existing inventory helper demonstrates this dotenv-disable pattern but writes multiple inventory artifacts when its main generator is invoked; it is not approved as the mapper baseline command.

Set a loopback-only synthetic DB URL sentinel and a `SKETCH2LIFE_BE1_ARTIFACT_ROOT` under the run root. Any engine created must be disposed in a `finally` path. The exporter must call `app.openapi()` without starting a server/lifespan. Static code suggests token verification is the Firebase Admin call path and AI defaults disabled, but this does not prove no DB, network, or provider access during execution. **Owner-confirmed OS-level egress blocking is a prerequisite**, not an environment-variable claim.

### PowerShell command card and open items

No baseline or exporter was run. The following is a future card outline, not a launch instruction. The exact lock-matched `$Python` path and reviewable inline exporter/comparator code must be supplied and pinned in a separate Task Approval. No safe reusable exporter command is approved by this plan.

```powershell
# Future approval only. One new GUID root per export; never reuse an old one.
$Python = '<owner-supplied absolute python.exe from the lock-matched environment>'
$Backend = 'D:\GitHub\Sketch2Life\.worktrees\m2-s2\backend'
$RunRoot = Join-Path $Backend "tmp\openapi-mapper-d6-$([guid]::NewGuid().ToString('N'))"
if (Test-Path -LiteralPath $RunRoot) { throw 'GUID path exists; stop and request a new run.' }
New-Item -ItemType Directory -Path $RunRoot | Out-Null
$RuntimeJson = Join-Path $RunRoot 'runtime-pre.json' # use runtime-post.json for post
$PublishedJson = Join-Path $RunRoot 'published-pre.json' # use published-post.json for post
$ReportJson = Join-Path $RunRoot 'field-delta-report.json'
# A separately reviewed launcher must create a cleared child environment,
# set the isolation variables above, and invoke the pinned inline exporter.
# No exporter or comparator invocation is authorized by this card.
# After approved export, calculate artifact hashes without printing schema content.
Get-FileHash -LiteralPath $RuntimeJson,$PublishedJson -Algorithm SHA256
```

The future exporter writes both schema JSON files only under the run root. The comparator must recursively report every addition/removal/value change by schema kind (runtime/published), method, path, and JSON pointer; include input SHA-256 values and profile/route-composition labels in its JSON report. It must fail if:

- either pre/post exact method/path set differs;
- any operation ID changes or is duplicated in either schema;
- metadata appears on a neighboring/nonmatching key;
- any field outside the §5 delta allowlist changes; or
- any security, request/body schema, component schema, or non-`X-Request-ID` response header changes.

The comparator report must include `passed: true` only when every invariant holds. The generated files and report receive SHA-256 hashes. The actual published projection exporter and comparator code remain unverified until reviewed and pinned in the future Task Approval.

## 7. Future lock-matched environment, test card, and ceilings

### Environment gate

The last recorded local environment reported Python 3.12 / FastAPI 0.162.7; this turn did not re-probe it. `backend/uv.lock` currently pins FastAPI 0.162.0. The recorded 0.162.7 environment is not lock-matched and cannot support a locked-version claim.

Before any future baseline or verification, the owner must provide a pre-provisioned environment and provenance containing: the absolute interpreter path, interpreter version/build/architecture and executable or environment-manifest hash; the exact `uv.lock` and `pyproject.toml` hashes used; the platform and Python tags/markers; selected dependency groups/extras; and a complete installed-distribution manifest that matches the lock resolution for that platform and selection. A FastAPI version probe alone or a plain freeze without lock/marker comparison is insufficient. Do not install, sync, mutate, or regenerate the lock.

### Exact pytest selections and isolation card

The only proposed pytest selections are:

1. `tests/contract/test_openapi_schema_catalog_mapping.py`
2. `tests/contract/test_openapi_contract_catalog.py`
3. `tests/contract/test_app_composition.py::test_real_app_composes_pilot_only_for_valid_local_synthetic_gate`

For each future invocation, use a new GUID root under the ignored `backend/tmp` directory and confirm it does not exist before creating it. `--basetemp` must name a new absolute GUID path that does not exist; never delete or reuse a previous basetemp because pytest may remove its target. Use `-p no:cacheprovider` (this disables the cache plugin; setting `cache_dir` would only redirect its cache). Define the absolute Python executable, backend working directory, run root, base temp, JUnit XML, and schema-comparator report paths together in the separately approved command card.

Proposed PowerShell pytest card (not executed and not a launch instruction):

```powershell
$Python = '<owner-supplied absolute python.exe from the lock-matched environment>'
$Backend = 'D:\GitHub\Sketch2Life\.worktrees\m2-s2\backend'
$RunRoot = Join-Path $Backend "tmp\pytest-openapi-draft6-$([guid]::NewGuid().ToString('N'))"
if (Test-Path -LiteralPath $RunRoot) { throw 'GUID path exists; stop and request a new run.' }
New-Item -ItemType Directory -Path $RunRoot | Out-Null
$Base = Join-Path $RunRoot 'pytest-basetemp'
if (Test-Path -LiteralPath $Base) { throw 'basetemp exists; stop and request a new run.' }
$Junit = Join-Path $RunRoot 'pytest.junit.xml'
$ComparatorReport = Join-Path $RunRoot 'field-delta-report.json'
$ConsoleLog = Join-Path $RunRoot 'pytest.console.txt'
# Run only inside the separately approved cleared PowerShell child process with
# the §6 allowlist; never execute from an ambient credential-bearing shell.
# Use a new RunRoot for every invocation, including any approved rerun.
$PytestBootstrap = @'
import sys
from sketch2life.infrastructure.config.settings import (
    CoreDatabaseSettings, Settings, get_core_database_settings, get_settings,
)
Settings.model_config["env_file"] = None
CoreDatabaseSettings.model_config["env_file"] = None
get_settings.cache_clear()
get_core_database_settings.cache_clear()
import pytest
base, junit = sys.argv[1:3]
raise SystemExit(pytest.main([
    "-q", "--basetemp", base, "-p", "no:cacheprovider", "--junitxml", junit,
    "tests/contract/test_openapi_schema_catalog_mapping.py",
    "tests/contract/test_openapi_contract_catalog.py",
    "tests/contract/test_app_composition.py::test_real_app_composes_pilot_only_for_valid_local_synthetic_gate",
]))
'@
& $Python -c $PytestBootstrap $Base $Junit *> $ConsoleLog
$ExitCode = $LASTEXITCODE
if ($ExitCode -ne 0) { throw "pytest failed with exit code $ExitCode; retain console and reports." }
if (-not (Test-Path -LiteralPath $Junit)) { throw 'JUnit output is missing; stop.' }
if (-not (Test-Path -LiteralPath $ComparatorReport)) { throw 'Comparator report is missing; stop.' }
$Result = Get-Content -Raw -LiteralPath $ComparatorReport | ConvertFrom-Json
if ($Result.passed -ne $true) { throw 'Comparator report did not pass; stop.' }
```

`$Python` must be the pinned interpreter and the working directory is `$Backend`. The future launcher runs the three selections above with `--basetemp $Base -p no:cacheprovider --junitxml $Junit`, retains console output in `$ConsoleLog`, checks the actual exit code, and then requires both `$Junit` and `$ComparatorReport` to exist with the comparator JSON field `passed` equal to true. Do not suppress missing-file errors. On nonzero exit, retain the exit code/output and stop without a retry beyond the ceiling. The launcher and its sanitized child environment must be pinned in the separate approval before use.

The future cleared process allowlist must include the same synthetic S3 pair used by the exporter, set before pytest imports the test modules; also include `STORYRUN_LITE_MAIN_DEMO_ENABLED=0`, `SKETCH2LIFE_AI_PROVIDER=disabled`, the loopback DB sentinel, and the run-root artifact path. Include `AWS_EC2_METADATA_DISABLED=true`, absent AWS config/credential paths, and isolated HOME/USERPROFILE/TEMP/TMP paths. Before pytest collection, the bootstrap in the card disables dotenv for both Settings classes and clears their caches; this is necessary because clearing process environment alone would not suppress the absolute repository dotenv path. The test fixture may temporarily override profile flags; that does not change the synthetic S3 variables.

For the named composition node, source shows its direct `Settings` objects read the synthetic pair through BaseSettings’ process-environment source even with `_env_file=None`; the test does not need or authorize an edit to `test_app_composition.py`. The random synthetic values must never be printed. The test’s own artifact root is under pytest’s temp directory, it disposes four constructed engines, and its database-settings getter is monkeypatched to a no-URL object. Retain a local DB sentinel and owner-confirmed OS egress block in the runner boundary; static source does not establish runtime isolation.

After the process ends, pytest success requires all of: exit code 0; the expected JUnit file exists; the comparator report exists; and its JSON says `passed: true`. Do not use `-ErrorAction SilentlyContinue` to hide missing output. On failure, record the exit code and retain console output and any generated JUnit/report; stop and do not retry outside the ceiling.

### Command ceilings and success signals proposed for separate approval

| Command family | Future command and working directory | Maximum | Output, success signal, and stop condition |
|---|---|---:|---|
| OpenAPI pre-fix export | `$Python -c <pinned exporter>`; workdir `$Backend` | 1 | Runtime-pre and published-pre JSON plus SHA-256, profile, interpreter, and environment manifest. Stop on nonzero exit or missing output. |
| OpenAPI post-fix export | Same pinned exporter and `$Backend` workdir as pre | 1 | Runtime-post and published-post JSON plus SHA-256. Stop on environment/profile mismatch or missing output. |
| Field-level comparator | `$Python -c <pinned comparator>`; workdir `$Backend` | 1 | Report JSON with input hashes, field deltas, invariants, and `passed: true`. Fail on any out-of-allowlist delta; retain report. |
| Three exact pytest selections above | `$Python -m pytest ...`; workdir `$Backend` | 2 total, only after separate approval | New GUID root/base temp per invocation. Require exit 0, JUnit present, comparator report present and passed true. On failure retain exit code/output and stop; no extra retry. |
| Mypy baseline and post-change | `$Python -m mypy src/sketch2life`; workdir `$Backend` | 2 total | Retain separate complete outputs and exit codes under approved GUID roots. Compare diagnostic signatures; post-change must add none. Existing diagnostics remain debt, not a pass. Stop on additions. |
| Ruff baseline and post-change | `$Python -m ruff check src/sketch2life/interfaces/http/app.py tests/contract/test_openapi_contract_catalog.py tests/contract/test_openapi_schema_catalog_mapping.py`; workdir `$Backend` | 2 total | Retain separate complete outputs and exit codes under approved GUID roots. Compare diagnostic signatures; post-change must add none. Existing diagnostics remain debt, not a pass. Stop on additions. |
| Repository validator | None proposed; workdir would be repository root only if separately approved | 0 | Not part of this mapper verification. Repository security validation remains a commit/push gate and requires explicit future authorization. |
| `git diff --check` | None proposed; workdir would be repository root only if separately approved | 0 | Not part of this mapper verification; no diff-check has been run or authorized here. |

All earlier D-207/FEAT-047/S2 command ceilings are consumed and cannot be reused. These new ceilings are proposals, not authorization. Each future retry/run needs the ceiling and direct launch instruction in its own Task Approval. No command listed here ran for Draft 6.

The last recorded historical diagnostics were 335 mypy errors and 17 Ruff diagnostics. They are existing debt, not a pass or a guaranteed fresh baseline. Re-capture baseline output only after separate approval; report exit codes and diagnostic deltas, and stop if the post-change run adds diagnostics.

## 8. Remaining owner gates and stop conditions

Before any baseline, tests, implementation, or verification, a separate approval must name the exact allowlist, lock-matched environment and provenance, profile, safe exporter/comparator code and artifact paths, process allowlist, new GUID temp/cache paths, owner-confirmed OS-level egress block, command ceilings, expected outputs, failure handling, and a direct launch instruction.

The owner has already selected allowlist Choice A and mapper-design Option A; this document does not ask to reopen those choices. Remaining open items are:

- provide evidence for an environment that matches all of `backend/uv.lock` on the selected platform/groups;
- confirm the OS-level egress block and that no DB/provider credential discovery is possible in the approved execution boundary;
- approve a separately pinned baseline/export/comparator command and decide when baseline collection may begin;
- approve future test/typecheck/lint ceilings and exact GUID-isolated output paths; and
- later create the exact Task Approval and launch instruction before implementation or verification.

Stop if a changed pin, route/profile, catalog count, source behavior, or acceptance scope affects these assumptions. Planning acceptance and cold-review acceptance never grant implementation, baseline, test, approval, or launch authority.

## 9. Rechecked input pins

The following are current read-only pins from the active BE worktree and the applicable parent harness. They identify the planning inputs used here. Draft 5’s stored historical input table is not rewritten. The current Draft 5 pin and prior review pin are intentionally shown separately.

| Input | Bytes | SHA-256 | Use / boundary |
|---|---:|---|---|
| Active worktree `AGENTS.md` | 3,406 | `89ACC84AA4D838730205A03917B40DEB37E9622AAF7092E982476D934EC29A61` | Repository rules. |
| Parent checkout `.codex/sketch2life-harness.md` | 2,178 | `0364DD280483D7AB56EAAF7F0B2CEF56A86D627393CA9996FC88A14E3318E12F` | Read-only workflow harness; active worktree has no root `.codex` directory. |
| Worktree `docs/context/SRS_AUTHORITY.md` | 4,313 | `D6153D38000C95E43A4091C5DF2E856FAD872A33177E3A8542E30EF2BEDCAB60` | Rev68 working authority. |
| FEAT-063 Rev68 SRS | 639,948 | `69C83FE49CD4689D5D2540656D3319721838CF7343BAD00E24CDE558B8F5E944` | Unsigned working SRS. |
| `docs/context/PROJECT_CONTEXT.md` | 83,919 | `B53D00641590E5B0DB7D6D19603AB796F19658F9F3F6AD8BC31076FDF51D631D` | Source context. |
| `docs/context/SOURCE_REGISTER.md` | 116,802 | `AA85FBB167AB065322258C5C90F05AF40B331BA30F9009020E40147B9DEACC6B` | Source routing. |
| FEAT-063 `CONTEXT.md` | 118,595 | `9AAF9081D1E5F96592DF8E0D312FC1B4119FEB0C695C3D55A3CF2EACE72E3653` | Current planning history; still records earlier Draft 5 hash. |
| FEAT-063 `SOURCE_REGISTER.md` | 71,135 | `A04CDAE6104AD2F3E4CCADD1DB244C04EC5596E4E8094F5E1655FBCCB36D3933` | Current source/evidence index; still records earlier Draft 5 hash. |
| FEAT-063 `DECISIONS.md` | 216,212 | `52F2E141244829281FF762BA100D1A991D5CADFF042A237C8C125F324300725F` | Decision context; not edited. |
| FEAT-063 `approvals/TASK_APPROVAL.md` | 410,676 | `C6A506404AF68A6180E150B83DE120113CE5EA54FCD7DEDFF9EAB01E4D375088` | Existing scope only; not edited. |
| FEAT-063 `plan/M2_S2_TASK_APPROVAL_DRAFT18_20261114.md` | 101,153 | `5CA09CC6F9D936C1BA74772251F4D3A9C0480F3E6F82818FE11114205FD3E331` | D-207 S2 scope. |
| FEAT-063 `evidence/M2_S2_IMPLEMENTATION_REPORT_20261114.md` | 25,879 | `F49D1FDB2B3C26387FFABC51C316F226C5D1FC5FC12B4856B0A6172A81941F55` | S2 ledger: PARTIAL / NOT COMPLETE. |
| FEAT-063 `plan/M2_S2_IMPLEMENTATION_ALLOWLIST_DRAFT1_20261114.md` | 14,768 | `7DCEEB785C2121D250B7C016EDC2030E2CD7912F87BE537F07CC8B359A2A0CE8` | D-207 allowlist boundary. |
| FEAT-063 `evidence/M2_S2_OUT_OF_SCOPE_OPENAPI_FINDING_20261114.md` | 3,456 | `D2C84E356C45653AB9973D94DFD09E4A8DB8439EA01BE4DA2D64B0849B80E5B2` | Historical failure evidence, not a new reproduction. |
| Mapper Draft 1 | 20,784 | `48B7A95133BDEAB9D14EE947BAF44D5B475ED60B99D118EAC24B51C9E0561BD6` | Historical plan. |
| Mapper Draft 2 | 15,345 | `9F9BD0C40FBEAA38515F92A4FBAB92F30535C3BC0150C94B986DE7F32192E803` | Historical reviewed plan. |
| Mapper Draft 3 | 17,569 | `47FBBDA1B3C21FFA6CCD4DFE4322BD1C6B9C8D4851A1B584699EA694E4019525` | Previous planning revision. |
| Mapper Draft 4 | 26,271 | `2EA7A344CF016FDBC3546967288B5B6628E15AB48920C14F7DBF8C68880A5DB8` | Prior cold review ACCEPT WITH CORRECTIONS; planning only. |
| Current observed Mapper Draft 5 | 29,568 | `61D198C946F08535622ED00236D54DB6FC347A8AF960821BB3D2E6F99B652243` | Observed predecessor; preserved. |
| Draft 5 cold-review evidence file | 2,787 | `9C2205798CE19E1391D873BEE2884E17682A680E520CD69F54A5F2C16F0A41D9` | Pins the earlier hash; ACCEPT does not transfer. |
| FEAT-063 `plan/M2_S3_TASK_APPROVAL_DRAFT6_20261116.md` | 17,317 | `BF7792925F06ED66720850CEE916EFBF2F724100B84D3B2BF3545F11E19108C4` | Separate S3 plan; no authority for this task. |
| `backend/src/sketch2life/interfaces/http/app.py` | 74,637 | `E7AE7BEA097929B83950B585A3ED9DEB682A4FF2A0D5E0CBE7ED36A1C1FCC031` | Mapper, app factory, runtime/published schema projection. |
| `backend/src/sketch2life/interfaces/http/openapi_contract.py` | 1,377,229 | `175FA3B3BDE475BA32743569DD276924CD20E32F8D29AA65F6C7AB68B2C9E9AE` | Rev37 catalog, read-only. |
| `backend/src/sketch2life/interfaces/http/openapi_contract_amendments.py` | 49,654 | `E16DE02140E7977A014F32D9CF131DAC8FC63EA622CEDD26B702958D7B92BB09` | Existing tag/response projection. |
| `backend/src/sketch2life/interfaces/http/openapi_srs_v22.py` | 11,122 | `29A0288E9F48EDD60F5E49A28360189BA68084B21A6A0FA2EAB2E5E0D3B6BCB3` | Published OpenAPI projection. |
| `backend/src/sketch2life/interfaces/http/router_composition.py` | 3,743 | `2CC4EA02A69E115C684B4383A1CA9BB63A4AAAB4B0E6C848852968C5E9599463` | Route composition. |
| `backend/src/sketch2life/interfaces/http/be1_runtime.py` | 16,807 | `62691ECC532F4544DBE4ABE0D277A67922CAA505DAF4D4803D1754039D754C85` | BE1 engine construction and Settings getter path. |
| `backend/src/sketch2life/interfaces/http/routers/be1_artifacts.py` | 17,501 | `7126EDF1193C547026CFD3388D2893FC0B726D0DBA2B42D3B60FF5BFD8F28CAF` | Existing storage route context. |
| `backend/src/sketch2life/infrastructure/config/settings.py` | 5,964 | `B430FA3036B1621CE0EB6283C94642E57AFF367FB8C45F7819E556D7D4180E65` | Settings prefix, dotenv, and field source. |
| `backend/src/sketch2life/infrastructure/storage/s3_compatible.py` | 3,568 | `43BE1BF9ACC454CF3A027F3AD4D6A5893ED266EB7171B45D0B4EEE9E891E1E8B` | Explicit-credential adapter path. |
| `backend/tests/contract/test_openapi_contract_catalog.py` | 18,753 | `BB798EF399168F2466470AA81F74B88E5304442BAB2EE88F87D24CA70C43B198` | Catalog fixture and assertions. |
| `backend/tests/contract/test_app_composition.py` | 13,507 | `1ED234FD8B75847F2668A2B23C9325C1D229CA679943B65166E96144A4463B52` | Read-only exact node source. |
| `backend/pyproject.toml` | 3,383 | `35F7635D77D80D787AB127C46D625C6FFE175F5C538759161E4B5B4549638AC2` | Backend dependency constraints. |
| `backend/uv.lock` | 398,117 | `830842CFAC04B5CA1EBDAA733E281F7D0AB9A4C94B19CFDF2B93E66854DBFB13` | FastAPI 0.162.0 lock pin. |
| Existing BE inventory `artifacts/be-full/openapi.runtime.json` | 615,320 | `A701C5FF1E429FD74F982F614E355A375B07F85D22440FD658A5EDA7871DAB19` | Historical, different optional-profile inventory; not baseline. |
| Existing BE inventory README | 5,568 | `36A7E793F8C77A19169B4DF6946CDB64043F4CF55D26846A14E25D0256B66E90` | Describes the inventory’s optional profile composition. |
| Existing BE inventory generator | 29,641 | `A46372F5179CD2F65D5709AF4E34FAF7AF4397F808CC1DD899C149B0E39E0FEC` | Writes inventory artifacts; do not invoke for this baseline. |
| Historical FE Rev45 OpenAPI JSON | 126,905 | `352EA298525A36B046D34D90DB97D7C0057F9D026582E52DD002710A56805C05` | Historical FE snapshot, not current BE runtime baseline. |
| FEAT-047 prior overlay plan | 7,886 | `235C19EF66BDD36BAEC03A89548D96B8172126EBADEA86202A48692ED976308B` | Historical one-time overlay; authorization consumed. |
| FEAT-047 prior approval | 3,023 | `67A69DF8CEE0344D8F5D8D79B5F0D432490FE0D7F1486ED8A58C806ADD451063` | Existing approval only; not reusable. |
| FEAT-047 prior overlay evidence | 13,596 | `0CF2C87996252058544D5F943967AB9F3A4E7A292D28CF1F6413620BFA6D8871` | Historical evidence only. |

## 10. Work performed and review boundary

Draft 6 is a new planning document only. It preserves the current Draft 5 file and its existing review evidence. It does not edit source/tests, the SRS, decisions, approval records, prior evidence, or any of the pre-existing dirty paths. It does not approve baseline collection, implementation, tests, or launch.

A fresh-context independent reviewer must receive the exact Draft 6 path, byte count, SHA-256, and this read-only input list; run no commands and use a read-only sandbox with network disabled. The reviewer must specifically confirm: the provenance boundary between the old ACCEPT pin and the current Draft 5 pin; exact allowlist Choice A with no expansion; the corrected Settings/process-environment explanation for both the exporter and selected pytest node; S3, dotenv, DB, provider, home/AWS-file, temp-root, and OS-egress isolation requirements; the FastAPI lock gate; the command ceilings and no-overclaim language; and any remaining ambiguity or finding.

The reviewer report is to be stored only at `features/FEAT-063-system-architecture-rearchitecture/evidence/M2_S2_SHARED_OPENAPI_MAPPER_FIX_DRAFT6_COLD_REVIEW_20261116.md`. Review acceptance is planning review only, not implementation approval. No report or review thread existed when this draft was pinned; the result will be recorded only in the specified evidence file after the independent review returns.

