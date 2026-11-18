# FEAT-063 M2-S2 Shared OpenAPI Catalog Mapper — Draft 9

**Status: DRAFT / NOT APPROVED / NOT LAUNCHED.** This planning-only successor preserves Drafts 5–8 and their review evidence and addresses only the remaining P2 finding from the independent Draft 8 review. The owner selected Draft 9 plus one fresh independent cold review of its exact pin. No baseline collection, tests, validation, typecheck, lint, build, Task Approval, implementation, or launch is authorized. OWNER_MODAL_CALL_APPROVED=NO

**Date:** 2026-11-16  
**Worktree:** `D:\GitHub\Sketch2Life\.worktrees\m2-s2`  
**Branch / HEAD:** `feature/feat063-m2-s2` / `5de30674bc826591ad4b3cc00fca53c7597ead51`  
**Observed pre-Draft-7 status:** 76 paths: 24 modified, 52 untracked, 0 staged. This snapshot includes pre-existing unpublished worktree changes. It is not a clean-tree claim.

## 1. Authority, status, and Draft 5 provenance

- The active BE worktree follows its `docs/context/SRS_AUTHORITY.md` pointer to the unsigned FEAT-063 v2.7-draft Rev68 SRS. Rev68 is a working source, not a signed product baseline. The mapper proposal adds no route or product requirement.
- D-207 remains limited to its approved S2 allowlist; the generic OpenAPI mapper is outside that scope. The FEAT-047 upload-description overlay and the prior combined S2 verification authorization are consumed. M2-S2 remains **PARTIAL / NOT COMPLETE**. M2-S3 is a separate gate.
- The current Draft 5 file observed before this plan is 29,568 bytes, SHA-256 `61D198C946F08535622ED00236D54DB6FC347A8AF960821BB3D2E6F99B652243`.
- The earlier Draft 5 pin in `CONTEXT.md`, `SOURCE_REGISTER.md`, the Draft 5 review evidence, and the original cold-review request is 29,568 bytes, SHA-256 `61D198C946085F35622ED00236D54DB6FC347A8AF960821BB3D2E6F99B652243`. The fresh review thread `01a1e286-d311-78c3-9e52-1998f4f05f58` explicitly targeted that earlier hash; its ACCEPT applies only to those earlier bytes. It is not acceptance of the current Draft 5 bytes.
- The owner has directed that the current Draft 5 bytes be preserved. This plan does not label the hash difference a typo, does not restore or overwrite Draft 5, and does not treat the prior ACCEPT as applying to the current file. This provenance discrepancy is carried forward unchanged from Draft 6.
- Draft 6 is pinned at 37,118 bytes / SHA-256 70675F32B797557CDF24528039AFB04207596123A115DC9AB019DE75719EAAC5. Its independent cold-review evidence is 4,878 bytes / SHA-256 285628543B2BBD7690B706B50C20D58DC33E9804DEACF9183A3A01B6FAAA7F52 and returns ACCEPT WITH CORRECTIONS — planning review only. Draft 7 addressed those four corrections.
- Draft 7 is pinned at 46,603 bytes / SHA-256 AAA38B9918F67EC12A1B1C8AC07D7635053F3F71DD6363BAC464C53BCDFC6C10. Its independent cold-review evidence is 4,352 bytes / SHA-256 F11EFBA5E1564C1F83A3A431A3466804E0551916453A33E9ED29F8AEB245FC0F and returns ACCEPT WITH CORRECTIONS — planning review only. The first delivery was truncated; §§1–6 were supplied in the same thread, then the reviewer confirmed receipt of all §§1–10. It found two P2 planning corrections in §6: normalized environment-identity comparison and failure-path hashing. The reviewer did not independently recalculate the Draft 7 hash or inspect the worktree.
- The owner selected Draft 8 plus one fresh independent cold review. Draft 8 addresses only those two Draft 7 review findings; it does not change the mapper decision or allowlist and does not authorize implementation, baseline collection, tests, or launch.
- Draft 8 is pinned at 54,016 bytes / SHA-256 30152C79064E035A8303187888F6830867DA0C22322E8CCCACD6CB38AF6C2038. Its independent cold-review evidence is 4,237 bytes / SHA-256 3AB12074BD337E94DFD4B574DBB7B5A43AB08A072A0CD2B494DA37A857580563 and returns ACCEPT WITH CORRECTIONS — planning review only. The reviewer confirmed receipt of all ten sections after §6 was supplied in the same thread and then confirmed the four Draft 6 findings from the prior review excerpt. It found one remaining P2 in §6: represent the new N-path pre-implementation as ABSENT with no hash, record the post-implementation hash, and include both states in the comparator output. The reviewer did not independently recalculate the Draft 8 hash or inspect the worktree.
- The owner selected Draft 9 plus one fresh independent cold review. Draft 9 addresses only that N-path state/hash finding and preserves the earlier mapper decision, allowlist, and corrections; it does not authorize implementation, baseline collection, tests, or launch.
- Draft 5 §8 recorded 73 paths / 24 modified / 49 untracked / 0 staged. Draft 6 recorded 74 / 24 / 50 / 0. The pre-Draft-7 observation was 76 / 24 / 52 / 0. The pre-Draft-8 observation was 78 / 24 / 54 / 0. The pre-Draft-9 observation is 80 / 24 / 56 / 0, with zero staged paths. The proposed N-path `backend/tests/contract/test_openapi_schema_catalog_mapping.py` remains absent. No pre-existing dirty path was changed to prepare Draft 9.
- Before creating Draft 9, read-only checks reconfirmed the Draft 5 through Draft 8 plan and review pins; the relevant source, governance, context, and approval pins in §9; branch `feature/feat063-m2-s2`; and HEAD `5de30674bc826591ad4b3cc00fca53c7597ead51`. Both Draft 9 target paths were absent. No CHANGED SINCE OBSERVATION was found for these checked inputs.
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
- That node makes five `create_app()` calls: with `settings`, `disabled_settings`, `settings` after swapping in a SQLite engine, with `staging_settings`, and with `settings` after the engine factory is set to raise the synthetic missing-configuration error. Its four created test engines have dispose() calls after assertions on the normal path; the final call has no engine. The inspected node has no finally-guaranteed cleanup.
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

These are planning criteria only. Draft 9 is not implementation evidence.

1. The mapper receives the generated schema and catalog and looks up each operation only by exact lowercase method and exact path. It does not enumerate `application.routes`, flatten router trees, inspect private FastAPI route objects, or check a Python name/callable.
2. Compare exact method/path sets. Every catalog key appears once in the expected runtime schema; the runtime-only set remains exactly `PILOT_ONLY_OPERATIONS | PR22_UNCATALOGUED_OPERATIONS` for the same approved profile. Missing, stale, unexpected, and duplicate catalog declarations fail explicitly; counts alone do not satisfy the check.
3. A source-level declaration check detects duplicate `(method, path)` literal keys before Python dictionary construction can overwrite them. If the declaration format changes beyond the checker’s recognized form, fail closed.
4. For every catalog key, public tag and description match the catalog rules. Preserve the five established description-prefix exceptions, the restore route’s appended Access text, and its existing restore response-description behavior. Do not normalize those exceptions away or alter unrelated descriptions.
5. Catalog response projection preserves exact response statuses, media types, schemas, and descriptions, including restore-specific descriptions and status pruning. Preserve all existing non-request-ID response headers. Preserve the current X-Request-ID parameter/header schema exactly across pre/post artifacts; no request-ID schema change is allowed while the finite method/path and JSON-pointer list in §6 remains OPEN.
6. For both the full runtime schema and the published `app.openapi()` projection, compare pre/post artifacts generated from the same route composition, profile, settings, lock-matched environment, and non-mapper amendments. Report field-level differences by method/path and JSON field pointer. The comparator fails on any unapproved change.
7. The only allowed schema deltas are the explicitly approved catalog tag/description/response-projection fields and the specified restore text/response-description behavior. No X-Request-ID parameter or response-header delta is currently allowlisted. Preserve exact path/method sets; each operation’s operationId must remain unchanged and unique within each pre/post schema; preserve security metadata, request parameters and bodies, component schemas, and every non-X-Request-ID response header.
8. Confirm no catalog metadata is applied to an adjacent operation with a different key. Uncatalogued operations and all unrelated fields remain unchanged. This is a schema assertion, not proof that a Python handler changed or was invoked.
9. A future lock-matched targeted run covers the three selections in §7. Its results must be reported with actual exit codes and output artifacts. M2-S2 remains **PARTIAL / NOT COMPLETE** until its separate owner-approved closure evidence is accepted; this mapper task alone does not close S2 or S3.

## 6. Future OpenAPI baseline and comparator — not approved or run

### Profile and artifacts

The pinned catalog-contract test fixture sets `SKETCH2LIFE_ENV=local`, `SKETCH2LIFE_SYNTHETIC_PILOT_ENABLED=true`, and `SKETCH2LIFE_STORAGE_EXAMPLE_ENABLED=true`, then calls the combined app profile with the StoryRun-lite main demo disabled by default. Its source-pinned expectations are 151 runtime operations, 134 catalog operations over 118 catalog paths, and 17 classified runtime-only operations. A future pre/post exporter must match this exact profile and route composition; changing flags changes the baseline.

From one app instance per pre/post generation:

- Save `application.state.runtime_openapi_schema` as the full runtime JSON.
- Save `application.openapi()` as the published SRS/OpenAPI projection. The current app source builds the runtime schema and passes it through `project_srs_v22_openapi` for this public projection.
- Do not use the historical `artifacts/be-full/openapi.runtime.json` or Rev45 FE JSON as a current runtime baseline. The BE inventory files listed in Draft 6 are absent from this worktree and are not inputs to this plan. Generate fresh pre/post artifacts only after separate owner approval.
- Each export writes runtime JSON, published JSON, and a sanitized environment manifest to its own fresh GUID directory beneath `backend/tmp/openapi-mapper-draft9-<guid>/`; the comparator writes its report and SHA-256 manifest to a third fresh GUID directory there. The current root `.gitignore` ignores `tmp/`. The baseline and post artifacts must use the same absolute lock-matched interpreter, working directory, profile, environment allowlist, and exporter logic.

### Isolation required for a future exporter

The process must start with a cleared child-process environment and only the minimum OS/Python bootstrap variables plus the explicit allowlist. Before importing or creating the app, set `SKETCH2LIFE_S3_ACCESS_KEY=synthetic-openapi-mapper-d7-access` and `SKETCH2LIFE_S3_SECRET_KEY=synthetic-openapi-mapper-d7-secret`; these are non-secret synthetic literals and must never be echoed. Match the catalog fixture with `SKETCH2LIFE_ENV=local`, `SKETCH2LIFE_SYNTHETIC_PILOT_ENABLED=true`, `SKETCH2LIFE_STORAGE_EXAMPLE_ENABLED=true`, and `STORYRUN_LITE_MAIN_DEMO_ENABLED=0`. Also set `SKETCH2LIFE_AUTH_PROVIDER=development` and `SKETCH2LIFE_AI_PROVIDER=disabled`. Set `SKETCH2LIFE_DATABASE_URL` to a synthetic loopback-only sentinel and `SKETCH2LIFE_BE1_ARTIFACT_ROOT` to a path under the run root.

Use a fresh GUID `HOME` and `USERPROFILE` under the run root; set `TEMP`/`TMP` there as well. Set `AWS_EC2_METADATA_DISABLED=true`. Point `AWS_CONFIG_FILE` and `AWS_SHARED_CREDENTIALS_FILE` to distinct paths under the run root and preflight that those files do not exist; do not create or reuse them. Do not inherit ambient AWS, Firebase, Google, proxy, database, or provider credentials.

Settings defaults name an absolute repository .env file. Clearing process environment by itself does **not** disable dotenv loading. Before app creation, the exporter must use a reviewed process-local bootstrap that sets `Settings.model_config["env_file"] = None` and `CoreDatabaseSettings.model_config["env_file"] = None` (or an equivalently source-verified mechanism). Process environment loading remains active, so the synthetic S3 variables still reach every Settings instance. The existing inventory helper demonstrates this dotenv-disable pattern but writes multiple inventory artifacts when its main generator is invoked; it is not approved as the mapper baseline command.

Set a loopback-only synthetic DB URL sentinel and a `SKETCH2LIFE_BE1_ARTIFACT_ROOT` under the run root. Any engine created must be disposed in a `finally` path. The exporter must call `app.openapi()` without starting a server/lifespan. Static code suggests token verification is the Firebase Admin call path and AI defaults disabled, but this does not prove no DB, network, or provider access during execution. **Owner-confirmed OS-level egress blocking is a prerequisite**, not an environment-variable claim.

### Normalized environment identity for comparison

Each pre/post `environment.json` must contain a sanitized `environment_identity` object. The comparator canonicalizes and compares that object before evaluating schema deltas. It includes:

- **Toolchain and dependency identity:** canonical absolute Python executable path and reported version; backend `pyproject.toml` and `uv.lock` SHA-256; lock-matched platform and architecture; and the selected dependency groups. A single environment identity must match pre/post.
- **Relevant worktree/source identity:** canonical BE worktree root, branch, and HEAD; plus repository-relative path/SHA-256 pairs for the immutable runtime and profile inputs listed in §9. Those immutable source pins must match pre/post. Record the read-only `test_app_composition.py` pin and require it unchanged. Record the E/N allowlisted source/test paths separately as pre/post state-and-hash tuples. For existing E paths, each tuple is `PRESENT` with that artifact’s SHA-256. For the new N path `backend/tests/contract/test_openapi_schema_catalog_mapping.py`, the pre-implementation tuple must be `ABSENT` with `sha256: null`, after verifying that the path does not exist; do not call a hash function on the absent file. The post-implementation tuple must be `PRESENT` with its actual SHA-256. The future Task Approval pins the baseline hashes for existing E paths, the N path’s required absent pre-state, and the exact allowed path set. The post hash is recorded from the resulting file and is not guessed in advance. The comparator emits both N-path tuples in its report, fails if the N path is present at pre-export, and fails if it is absent or unreadable at post-export. The comparator allows source differences only on the exact E/N paths. Any other source path or identity change fails closed.
- **Route/profile identity:** the route-composition label and exact non-credential profile values used by this exporter, including `SKETCH2LIFE_ENV`, synthetic-pilot flag, storage-example flag, demo flag, auth provider, AI provider, and the DB sentinel identity. The profile and route label must match pre/post.
- **Effective process allowlist:** exact allowlisted variable names and their effective non-credential values. Normalize any value rooted under the export run root by replacing that root with `<RUN_ROOT>` while preserving the relative path and variable role. Thus different GUIDs for HOME, USERPROFILE, TEMP/TMP, AWS config/credential paths, artifact root, and output paths do not cause a false identity mismatch. Record the unique run ID and absolute artifact paths separately as provenance; exclude those run-specific values from equality after normalization.
- **Synthetic S3 pair:** the bootstrap must verify the approved synthetic access/secret pair in memory before app creation. In the manifest, record only a fixed pair label (for example, `openapi-mapper-synthetic-s3-pair-v1`) and booleans showing both fields were present after verification. Never place either value, a raw environment dump, or a credential-derived hash in the manifest, comparator report, or console log.

Canonicalize path fields with the selected platform’s path API before comparison. On Windows, compare canonical paths case-insensitively and serialize separators consistently. Replace the run-root prefix only at a path-component boundary, preserving each field’s variable/path role; a required isolated path outside the run root fails. Sort environment keys and source-path entries by name/path and compare their canonical JSON values exactly. Non-path, non-credential allowlist values compare exactly.

The normalized identity comparison requires equality for toolchain, lock, platform, groups, immutable source pins, worktree root/branch/HEAD, route/profile values, allowlist names, normalized non-credential values, and verified synthetic-pair label. Separately, the comparator validates that any source change is confined to the exact E/N path set in §4 and that the R path plus all immutable inputs remain unchanged. It records pre/post state-and-hash tuples for each allowed path; the new N path must be `ABSENT`/`null` before implementation and `PRESENT`/actual SHA-256 afterward. Missing fields, an unexpected allowlist key, an unnormalized per-run path, or any other identity mismatch fails the comparator. The comparator reports the identity-field names that differ and their non-secret normalized values; it does not report credentials.

### PowerShell command card and open items

No baseline or exporter was run. The following is a future card outline, not a launch instruction. The exact lock-matched `$Python` path and reviewable inline exporter/comparator code must be supplied and pinned in a separate Task Approval. No safe reusable exporter command is approved by this plan.

```powershell
# Future approval only. One new GUID root per export; never reuse an old one.
$Python = '<owner-supplied absolute python.exe from the lock-matched environment>'
$Backend = 'D:\GitHub\Sketch2Life\.worktrees\m2-s2\backend'
$RunRoot = Join-Path $Backend "tmp\openapi-mapper-d9-$([guid]::NewGuid().ToString('N'))"
if (Test-Path -LiteralPath $RunRoot) { throw 'GUID path exists; stop and request a new run.' }
New-Item -ItemType Directory -Path $RunRoot | Out-Null
$RuntimeJson = Join-Path $RunRoot 'runtime-pre.json' # use runtime-post.json for post
$PublishedJson = Join-Path $RunRoot 'published-pre.json' # use published-post.json for post
$EnvironmentManifest = Join-Path $RunRoot 'environment.json'
# ComparatorReport is produced under a separate fresh GUID ComparisonRoot; see the comparator card below.
# A separately reviewed launcher must create a cleared child environment,
# set the isolation variables above, and invoke the pinned inline exporter.
# No exporter or comparator invocation is authorized by this card.
# After approved export, calculate artifact hashes without printing schema content.
Get-FileHash -LiteralPath $RuntimeJson,$PublishedJson,$EnvironmentManifest -Algorithm SHA256
```

The future exporter writes both schema JSON files and a sanitized environment manifest only under its run root. The comparator must recursively report every addition/removal/value change by schema kind (runtime/published), method, path, and JSON pointer; include input SHA-256 values and profile/route-composition labels in its JSON report. It must fail if:

- either pre/post exact method/path set differs;
- any operation ID changes or is duplicated in either schema;
- metadata appears on a neighboring/nonmatching key;
- any field outside the §5 delta allowlist changes; or
- any security, request/body schema, component schema, or non-`X-Request-ID` response header changes.

The comparator report must include `passed: true` only when every invariant holds. The generated files and report receive SHA-256 hashes. The actual published projection exporter and comparator code remain unverified until reviewed and pinned in the future Task Approval.

### Comparator producer, inputs, execution order, and report handoff

The comparator is a separate gate and the sole producer of the report consumed by pytest. Pre-export, implementation, post-export, comparator, and pytest are ordered gates. The pre and post exporters each write to their own fresh GUID run root, including one sanitized environment.json manifest apiece. The comparator consumes exactly the four schema JSON paths and two environment-manifest paths from those pinned roots; its report is written to a third fresh GUID ComparisonRoot under backend/tmp. The later Task Approval must pin all three absolute roots, all six input paths, the interpreter, the profile/manifests, and exact inline comparator source and SHA-256. No source file is added.

Proposed comparator card after the approved post-export:

```powershell
$Backend = 'D:\GitHub\Sketch2Life\.worktrees\m2-s2\backend'
$Python = '<owner-supplied absolute python.exe from the lock-matched environment>'
$PreRoot = '<absolute GUID root of the approved pre-fix export>'
$PostRoot = '<absolute GUID root of the approved post-fix export>'
$ComparisonRoot = Join-Path $Backend "tmp\openapi-mapper-d9-compare-$([guid]::NewGuid().ToString('N'))"
if (Test-Path -LiteralPath $ComparisonRoot) { throw 'GUID path exists; stop and request a new run.' }
New-Item -ItemType Directory -Path $ComparisonRoot | Out-Null
$RuntimePre = Join-Path $PreRoot 'runtime-pre.json'
$PublishedPre = Join-Path $PreRoot 'published-pre.json'
$RuntimePost = Join-Path $PostRoot 'runtime-post.json'
$PublishedPost = Join-Path $PostRoot 'published-post.json'
$EnvironmentPre = Join-Path $PreRoot 'environment.json'
$EnvironmentPost = Join-Path $PostRoot 'environment.json'
$ComparatorReport = Join-Path $ComparisonRoot 'field-delta-report.json'
$ComparatorLog = Join-Path $ComparisonRoot 'comparator.console.txt'
$ShaManifest = Join-Path $ComparisonRoot 'sha256.txt'
$ComparatorBootstrap = '<exact inline comparator source pinned in Task Approval>'
$ComparatorExit = $null
$InvocationErrorType = $null
try {
  & $Python -c $ComparatorBootstrap $RuntimePre $PublishedPre $RuntimePost $PublishedPost $EnvironmentPre $EnvironmentPost $ComparatorReport *> $ComparatorLog
  $ComparatorExit = $LASTEXITCODE
} catch {
  $InvocationErrorType = $_.Exception.GetType().FullName
}
$ReportState = 'MISSING'
$ComparatorPassed = $false
if (Test-Path -LiteralPath $ComparatorReport -PathType Leaf) {
  $ReportState = 'PRESENT_INVALID'
  try {
    $ComparatorResult = Get-Content -Raw -LiteralPath $ComparatorReport | ConvertFrom-Json -ErrorAction Stop
    if ($ComparatorResult.passed -eq $true) {
      $ComparatorPassed = $true
      $ReportState = 'PRESENT_PASSED_TRUE'
    } else {
      $ReportState = 'PRESENT_PASSED_FALSE_OR_MISSING'
    }
  } catch {
    $ReportState = 'PRESENT_INVALID_JSON'
  }
}
$HashTargets = @($RuntimePre,$PublishedPre,$RuntimePost,$PublishedPost,$EnvironmentPre,$EnvironmentPost,$ComparatorReport,$ComparatorLog)
$ManifestLines = [System.Collections.Generic.List[string]]::new()
foreach ($HashTarget in $HashTargets) {
  if (Test-Path -LiteralPath $HashTarget -PathType Leaf) {
    try {
      $InputHash = (Get-FileHash -LiteralPath $HashTarget -Algorithm SHA256 -ErrorAction Stop).Hash
      $ManifestLines.Add("SHA256=$InputHash  $HashTarget")
    } catch {
      $ManifestLines.Add("UNREADABLE  $HashTarget  $($_.Exception.GetType().FullName)")
    }
  } else {
    $ManifestLines.Add("MISSING  $HashTarget")
  }
}
$Sha = [Security.Cryptography.SHA256]::Create()
$ComparatorSourceHash = [BitConverter]::ToString($Sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($ComparatorBootstrap))).Replace('-', '')
$Sha.Dispose()
$ManifestLines.Add("SHA256=$ComparatorSourceHash  <inline-comparator>")
$ManifestLines.Add("ComparatorExit=$ComparatorExit")
$ManifestLines.Add("ComparatorReportState=$ReportState")
if ($InvocationErrorType) { $ManifestLines.Add("InvocationErrorType=$InvocationErrorType") }
[System.IO.File]::WriteAllLines($ShaManifest, $ManifestLines, [System.Text.Encoding]::ASCII)
$ManifestIncomplete = @($ManifestLines | Where-Object { $_ -match '^(MISSING|UNREADABLE)\s' }).Count -gt 0
if ($ManifestIncomplete) { throw "One or more expected artifacts are missing or unreadable; retain sha256.txt and stop." }
if ($null -eq $ComparatorExit -or $ComparatorExit -ne 0) { throw "Comparator failed or did not start (exit=$ComparatorExit); retain the console, report if present, and sha256.txt." }
if ($ReportState -ne 'PRESENT_PASSED_TRUE' -or -not $ComparatorPassed) { throw "Comparator report gate failed ($ReportState); retain the console, report if present, and sha256.txt." }
```

Comparator logic required in that pinned inline source: load and validate the four schema JSON inputs and both sanitized environment manifests; calculate and report every addition, removal, or value change by schema kind (runtime/published), method, path, and RFC 6901 JSON pointer; compare exact method/path operation sets pre/post separately for runtime and published schemas; require each operationId to remain unchanged and unique within each schema; compare the complete normalized environment identity defined above; and assert catalog metadata appears only on its exact matching key, with adjacent keys unchanged. Include input hashes, profile/route-composition labels, normalized environment-identity results, environment-manifest hashes, invariant results, field deltas, and passed in the JSON report. Fail closed on missing/invalid input, changed environment identity, changed operation sets or operationIds, duplicate IDs, metadata leakage, any unapproved field delta, or any request-ID schema delta while the §6 request-ID inventory is OPEN. `passed: true` and exit code 0 are valid only when every invariant passes.

The PowerShell card must create `sha256.txt` **before any failure throw**, on both success and failure. It hashes each of the six schema/manifest inputs, the inline comparator source, and the report and console log when present; it writes an explicit `MISSING` or `UNREADABLE` entry for every expected file that is absent or cannot be read. It records comparator exit status, report state, and process-start error type when applicable. A nonzero/absent exit, missing/invalid report, or `passed` other than true still fails and stops after the manifest is written; retain all generated failure artifacts and do not retry beyond the comparator ceiling. If the manifest itself cannot be written, stop and report that failure without retrying. This manifest, report/hash, console output, exact run roots, environment/profile manifests, pytest artifacts, and exit codes travel together in the future evidence handoff.

ComparatorBootstrap is an inline, approval-pinned command payload, not a new repository source file. The command card is not runnable until the owner separately approves its exact code, inputs, environment, paths, ceiling, and launch instruction. No comparator or baseline was run for Draft 9.

### OPEN request-ID delta inventory

Current app.py source applies its schema overlay by iterating generated paths beginning with /api/be1/v1/ or /v1/parent/profiles, then operations with responses. It conditionally appends an X-Request-ID header parameter and adds X-Request-ID under each response headers map when absent. The observed JSON pointer families are /paths/{RFC6901-escaped-path}/{method}/parameters/{index} and /paths/{RFC6901-escaped-path}/{method}/responses/{status}/headers/X-Request-ID, including the parameter fields name, in, required, description, schema/type, schema/maxLength and schema/pattern, and the response-header fields description, schema/type and schema/maxLength. These are pointer patterns only, not an approved delta list.

The exact affected method/path pairs and fully rendered JSON pointers cannot be established from the pinned planning inputs without generating and enumerating the runtime and published schemas. No baseline has been collected and none is authorized here. The finite request-ID delta inventory is OPEN. This plan allows no request-ID parameter or response-header change; the comparator must fail on any such change until a future reviewed plan provides the exact finite method/path pairs and pointers and the owner approves that list. Do not infer an allowlist from path prefixes.



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
$RunRoot = Join-Path $Backend "tmp\pytest-openapi-draft9-$([guid]::NewGuid().ToString('N'))"
if (Test-Path -LiteralPath $RunRoot) { throw 'GUID path exists; stop and request a new run.' }
New-Item -ItemType Directory -Path $RunRoot | Out-Null
$Base = Join-Path $RunRoot 'pytest-basetemp'
if (Test-Path -LiteralPath $Base) { throw 'basetemp exists; stop and request a new run.' }
$Junit = Join-Path $RunRoot 'pytest.junit.xml'
$ComparisonRoot = '<absolute GUID comparator root under backend/tmp pinned by the approved run>'
$ComparatorReport = Join-Path $ComparisonRoot 'field-delta-report.json'
$ConsoleLog = Join-Path $RunRoot 'pytest.console.txt'
# Run only inside the separately approved cleared PowerShell child process with
# the §7 pytest allowlist; never execute from an ambient credential-bearing shell.
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
if (-not (Test-Path -LiteralPath $ComparatorReport)) { throw 'Comparator report is missing; do not run pytest.' }
$ComparatorResult = Get-Content -Raw -LiteralPath $ComparatorReport | ConvertFrom-Json
if ($ComparatorResult.passed -ne $true) { throw 'Comparator did not pass; do not run pytest.' }
& $Python -c $PytestBootstrap $Base $Junit *> $ConsoleLog
$ExitCode = $LASTEXITCODE
if ($ExitCode -ne 0) { throw "pytest failed with exit code $ExitCode; retain console and reports." }
if (-not (Test-Path -LiteralPath $Junit)) { throw 'JUnit output is missing; stop.' }
if (-not (Test-Path -LiteralPath $ComparatorReport)) { throw 'Comparator report is missing; stop.' }
$Result = Get-Content -Raw -LiteralPath $ComparatorReport | ConvertFrom-Json
if ($Result.passed -ne $true) { throw 'Comparator report did not pass; stop.' }
```

`$Python` must be the pinned interpreter and the working directory is `$Backend`. The future launcher runs the three selections above with `--basetemp $Base -p no:cacheprovider --junitxml $Junit`, retains console output in `$ConsoleLog`, checks the actual exit code, and then requires both `$Junit` and `$ComparatorReport` to exist with the comparator JSON field `passed` equal to true. Do not suppress missing-file errors. On nonzero exit, retain the exit code/output and stop without a retry beyond the ceiling. The launcher and its sanitized child environment must be pinned in the separate approval before use.

The future pytest process allowlist must set `SKETCH2LIFE_S3_ACCESS_KEY=synthetic-openapi-mapper-d7-access`, `SKETCH2LIFE_S3_SECRET_KEY=synthetic-openapi-mapper-d7-secret`, and `SKETCH2LIFE_STORAGE_EXAMPLE_ENABLED=false` before pytest imports test modules. These are the same non-secret synthetic S3 literals used by the exporter; never echo them. The exporter uses storage-example=true to match the catalog fixture; this pytest process uses false for the selected composition node. The catalog test fixture may set true locally for its own profile. Also include `STORYRUN_LITE_MAIN_DEMO_ENABLED=0`, `SKETCH2LIFE_AI_PROVIDER=disabled`, the loopback DB sentinel, and the run-root artifact path. Include `AWS_EC2_METADATA_DISABLED=true`, absent AWS config/credential paths, and isolated HOME/USERPROFILE/TEMP/TMP paths. Before pytest collection, the bootstrap in the card disables dotenv for both Settings classes and clears their caches; this is necessary because clearing process environment alone would not suppress the absolute repository dotenv path. The test fixture may temporarily override profile flags; that does not change the synthetic S3 variables.

For the named composition node, source shows its direct `Settings` objects read the synthetic pair through BaseSettings’ process-environment source even with `_env_file=None`; the test does not need or authorize an edit to `test_app_composition.py`. The random synthetic values must never be printed. The test’s own artifact root is under pytest’s temp directory, and its four engine dispose() calls occur on the normal path after assertions; they are not finally-guaranteed. Its database-settings getter is monkeypatched to a no-URL object. Retain a local DB sentinel and owner-confirmed OS egress block in the runner boundary; static source does not establish runtime isolation.

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

All earlier D-207/FEAT-047/S2 command ceilings are consumed and cannot be reused. These new ceilings are proposals, not authorization. Each future retry/run needs the ceiling and direct launch instruction in its own Task Approval. No command listed here ran for Draft 9.

The last recorded historical diagnostics were 335 mypy errors and 17 Ruff diagnostics. They are existing debt, not a pass or a guaranteed fresh baseline. Re-capture baseline output only after separate approval; report exit codes and diagnostic deltas, and stop if the post-change run adds diagnostics.

## 8. Remaining owner gates and stop conditions

Before any baseline, tests, implementation, or verification, a separate approval must name the exact allowlist, lock-matched environment and provenance, profile, safe exporter/comparator code and artifact paths, process allowlist, new GUID temp/cache paths, owner-confirmed OS-level egress block, command ceilings, expected outputs, failure handling, and a direct launch instruction.

The owner has already selected allowlist Choice A and mapper-design Option A; this document does not ask to reopen those choices. Remaining open items are:

- provide evidence for an environment that matches all of `backend/uv.lock` on the selected platform/groups;
- confirm the OS-level egress block and that no DB/provider credential discovery is possible in the approved execution boundary;
- resolve the finite request-ID method/path and JSON-pointer inventory (currently OPEN), and pin the exact inline comparator source and hash;
- approve a separately pinned baseline/export/comparator command and decide when baseline collection may begin;
- approve future test/typecheck/lint ceilings and exact GUID-isolated output paths; and
- later create the exact Task Approval and launch instruction before implementation or verification.

Stop if a changed pin, route/profile, catalog count, source behavior, or acceptance scope affects these assumptions. Planning acceptance and cold-review acceptance never grant implementation, baseline, test, approval, or launch authority.

## 9. Rechecked input pins

The following are current read-only pins from the active BE worktree and repository governance files. The active worktree has no root .codex harness, and no parent checkout was accessed in this turn. Draft 5’s stored historical input table is not rewritten. The current Draft 5 pin and prior review pin are intentionally shown separately.

| Input | Bytes | SHA-256 | Use / boundary |
|---|---:|---|---|
| Active worktree `AGENTS.md` | 3,406 | `89ACC84AA4D838730205A03917B40DEB37E9622AAF7092E982476D934EC29A61` | Repository rules. |
| `docs/governance/WORKFLOW.md` | 1,240 | `23D8717F82A85DB8E66922C81460A16EC24022FFD766C63457D308491A8D98A3` | Workflow gate. |
| `docs/governance/APPROVAL_POLICY.md` | 707 | `F734FD4C6416A526EBF2C0031804069467F6361B3A9854E7B5DBCA0AEADE4216` | Approval boundary. |
| `docs/governance/EVIDENCE_MANAGEMENT.md` | 1,519 | `93A3A526421C6524FD4E1B13B45FC36FAA6E5D3F0673C27C2E58D2C6C81DCCE2` | Evidence location/provenance. |
| `docs/governance/FRONTEND_ASSET_GATE.md` | 831 | `28DD1E51B54206C7A85B8F3BA4E0DAA638D4CBCF4CAF23BA04A2CED4BC76DDC1` | Read as applicable governance context. |
| Active worktree root `.codex/sketch2life-harness.md` | — | — | ABSENT; no parent checkout accessed in this turn. Repository docs/governance pins below were read. |
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
| Mapper Draft 6 | 37,118 | `70675F32B797557CDF24528039AFB04207596123A115DC9AB019DE75719EAAC5` | Preserved predecessor; reviewed with corrections. |
| Draft 6 cold-review evidence | 4,878 | `285628543B2BBD7690B706B50C20D58DC33E9804DEACF9183A3A01B6FAAA7F52` | ACCEPT WITH CORRECTIONS; planning only. |
| Mapper Draft 7 | 46,603 | `AAA38B9918F67EC12A1B1C8AC07D7635053F3F71DD6363BAC464C53BCDFC6C10` | Preserved predecessor; reviewed with corrections. |
| Draft 7 cold-review evidence | 4,352 | `F11EFBA5E1564C1F83A3A431A3466804E0551916453A33E9ED29F8AEB245FC0F` | ACCEPT WITH CORRECTIONS; planning only; two §6 P2s addressed in this successor. |
| Mapper Draft 8 | 54,016 | `30152C79064E035A8303187888F6830867DA0C22322E8CCCACD6CB38AF6C2038` | Preserved predecessor; reviewed with corrections. |
| Draft 8 cold-review evidence | 4,237 | `3AB12074BD337E94DFD4B574DBB7B5A43AB08A072A0CD2B494DA37A857580563` | ACCEPT WITH CORRECTIONS; planning only; new N-path absence/hash-state finding addressed in this successor. |
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
| Existing BE inventory `artifacts/be-full/openapi.runtime.json` | — | — | NOT PRESENT in active worktree; historical only, not baseline. |
| Existing BE inventory README | — | — | NOT PRESENT in active worktree; historical only, not baseline. |
| Existing BE inventory generator | — | — | NOT PRESENT in active worktree; not invoked or used. |
| Historical FE Rev45 OpenAPI JSON | — | — | NOT PRESENT in active worktree; historical only, not current BE baseline. |
| FEAT-047 prior overlay plan | 7,886 | `235C19EF66BDD36BAEC03A89548D96B8172126EBADEA86202A48692ED976308B` | Historical one-time overlay; authorization consumed. |
| FEAT-047 prior approval | 3,023 | `67A69DF8CEE0344D8F5D8D79B5F0D432490FE0D7F1486ED8A58C806ADD451063` | Existing approval only; not reusable. |
| FEAT-047 prior overlay evidence | 13,596 | `0CF2C87996252058544D5F943967AB9F3A4E7A292D28CF1F6413620BFA6D8871` | Historical evidence only. |
| root `.gitignore` | 10,810 | `9DAA2701E3C5DE0060214AE206854E61F2F0EC50DBBA294FABA2EBE5E938E110` | Contains tmp/ ignore rule at line 99. |

## 10. Work performed and review boundary

Draft 9 is a planning-only successor. It preserves Draft 5 through Draft 8, their existing cold-review evidence, and all pre-existing dirty paths byte-for-byte. It changes no source/test, SRS, decision, approval, prior evidence, or allowlist file. It does not authorize baseline collection, tests, typecheck, lint, validation, implementation, or launch.

The owner authorized exactly one fresh independent cold review of the exact pinned Draft 9 bytes. The reviewer receives the complete Draft 9 text and only the prior review/source excerpts needed to assess its correction, in one retained Codex thread using this same BE worktree, a read-only sandbox, network disabled, and approval policy never. The reviewer must confirm receipt of all Draft 9 sections before giving a content-level verdict. If the prompt is truncated, ask the same reviewer to confirm the missing sections; do not create another review thread. Do not transmit secrets or unrelated repository content. If automatic approval review rejects the transmission or destination, stop and report the rejection without retrying, splitting, rephrasing, or using another route.

The requested evidence path is `features/FEAT-063-system-architecture-rearchitecture/evidence/M2_S2_SHARED_OPENAPI_MAPPER_FIX_DRAFT9_COLD_REVIEW_20261116.md`. Create that evidence only after the reviewer confirms complete receipt and returns a content-level verdict. A review verdict applies only to the exact Draft 9 pin and is planning review only. It cannot approve implementation, baseline collection, tests, S2 closure, or S3.
