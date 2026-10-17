# Consolidated test handoff — C6a candidate, runtime NOT_RUN

Use the commit introducing C6a and this document, or a reviewed later checkpoint
with matching runner hashes. Earlier e792512 is parent only and lacks local runner.
Record `git rev-parse HEAD` and `git status --short` before executing; don't change
source mid-pack. Final checkpoint hash is reported in chat/Git history, source
maps in each receipt bind actual code/tests/tooling/config/feature records.
Missing/changed source/inventory or skipped test is not acceptance.

This is a consolidated entrypoint, not approval to provision or a declaration
that all local work is finished: health/queue projection remains local work per
ACCEPTANCE_AUDIT_20261018.md. Owner need not test each intermediate increment.

## 1. Local component check (no external service/GPU)

Existing approved project Python3.12 environment with its existing pytest/Ruff/
Mypy/dependencies; no installs or model stack changes. Activate that environment,
run from repo root (same command Windows/Linux):

```sh
python features/FEAT-049-be2-ai-policy/src/run_component_checks.py
```

Expected1028 exact own cases (node SHA25621dc838b...), zero fail/error/skip; targeted
foundation114, selected regression477, full61 own source Ruff/Mypy, governance/
security/whitespace PASS and source_unchanged=true. Exit0 only for whole local pack.
Writes ignored .runtime/ai-policy-component/<timestamp>/collection.log/component.xml/
foundation.xml/check logs/summary.json. Selected regression creates its own ignored
learning-content-component receipt directory and prints its path in regression477.log.
Not PG/provider/real-owner acceptance; no default app mount or network provisioning.

## 2. Actual PostgreSQL batch (104 cases, NOT_RUN)

Only after separately authorized disposable synthetic PG17 and existing environment
are available. Runner never starts/downloads/provisions a service. Restricted
account needs CREATEDB/permissions in generated test DBs, not superuser or shared
production access. Private password file stays outside Git; use environment names
AP_TEST_PG_HOST/PORT/USER/MAINTENANCE_DB/PASSWORD_FILE. No credential CLI/pasted logs.
Set AP_TEST_ALLOW_CREATE=1 only in that explicitly authorized shell/profile.
Exact fixtures create random ap49_<uuid> DBs and force-drop only those own generated
DBs in finally. Upgrade/downgrade only inside disposable DB; no production rollback.

Windows PowerShell commands: artifacts/C2_SQL_RUNTIME.md. Linux/Lightning with
existing approved environment and those variables supplied by trusted setup:

```sh
export AP_TEST_ALLOW_CREATE=1
python features/FEAT-049-be2-ai-policy/src/run_c2_sql_checks.py || exit $?
python features/FEAT-049-be2-ai-policy/src/run_c2_sql_checks.py --activation || exit $?
python features/FEAT-049-be2-ai-policy/src/run_c2_sql_checks.py --accounting || exit $?
python features/FEAT-049-be2-ai-policy/src/run_c2_sql_checks.py --copies || exit $?
```

Expected15 lifecycle +10 activation/stop/use +21 ledger/operations +58 copy cases,
four separate source-pinned PASS receipts, no skipped/duplicate/extra test IDs,
exit0 and unchanged source. Raw .runtime/ai-policy-c2/<timestamp> directories contain
collection/JUnit/pytest/summary; send all four redacted sets, not just screenshot.
First error: preserve original error/receipt and stop; don't blindly repeat or
install packages/change source/target a different DB to force PASS.

## 3. Provider/owner integration is a separate gate, not a GPU requirement here

PG/local code tests do not need GPU or infer actual WAN/TTS/provider behavior.
Actual providers need separately approved configuration, credentials/profile refs
and real owner adapters; none selected/activated by these commands. Test on
Lightning only after that gate, preferably using adopted owner conformance harness.
Required scenarios: current authority/source/consent/expiry revocation at dispatch/
completion/exposure; original pin/receipt binding; missing/unsupported/timeout;
crash-after-send dedup; forged/hash/action/profile mismatch; late result no exposure;
actual provider purge vs fixture; coverage/BE1 closure; exact-generation stop after
reactivation. Existing CR_KILL_NOTICE_PIN_FENCE.md and CR_PROVIDER_COPY_ADOPTION.md
remain OPEN, not approved third-party contracts. Never run broad cancellation as
a substitute. No claimed runnable real-provider harness without adopted adapters.

## Return / decision

Return source revision + dirty state, each summary/JUnit/collection/check log and
first failure if any, after checking no secrets/real child data/private endpoints.
Keep raw credential-bearing runtime files out of Git; redact before sharing.
Component PASS advances only local evidence; PG PASS advances only owned durable
evidence. Real owner/provider acceptance and original BE2-12 integration remain
separate. No whole-card/goal DONE, push/merge/deploy from this package.
