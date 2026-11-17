# BE2-01 B5 independent review —2026-10-15

- Result: **NEEDS_REVISION**, two bounded P2 findings **B5-R01/B5-R02 OPEN**.
- ACTIVE **Q01/B5_NEEDS_REVISION**. B5 is not closed; B6 NOT_STARTED. B2/B3/B4 and B4-R01/RT01
  stay closed. Existing PhaseBplanrev3B1–B6 approval applies;14cards/WIP1/full-cardDONE0.
- Codex primary and independent SQL, capability/worker and package/test reviewers inspected the
  exact25-file B5 delta,43-file source manifest and relevant callers/tests. Review changes
  documentation/evidence only; Claude remains backend executor. Do not run the current B5 ZIP
  as the next acceptance step; first correct the findings and re-review the new source/package.

## Reviewed checkpoint and actual checks

Current local B5 source matches manifestc74920973da54ccc48bdb0996cb4db2a13dedf6366e2766dae9622a093fee143.
Last-reportedStudio remains closedB4manifestf1c6834f, not B5. Base993a26cae78c0a4fe983033f03881838c886b176.
Only16existing protected files changed, all declared, plus9new implementation/test files;
the25-file delta also includes2existing paths newly added to the transport manifest. The Q00
trailing-blank-line disposition is explicitly carried with its B5 call-site update, as disclosed.

| Check | Actual result |
|---|---|
| Capability/worker unit tests |24PASS,exit0, direct local|
| Completion/effects/notices unit tests |25PASS,exit0, direct local|
| Fixture runner |20PASS/0FAIL,215checks/0failed,exit0,d17f58a3digest unchanged; optional HTTP NOT_RUN1|
| Independent SQL compile probe |5/5PASS, no PostgreSQL execution|
| Independent held-out service probe |B5-R01 reproduced; see below|
| Independent HMAC/worker/filter probe |B5-R02 reproduced; same findings confirmed by primary|
| Package |43currenthashes match;5package digests exact;25deltafiles,4ZIPmembers byte-identical; reverse-check0|
| Test collection |183cases=closedB4104+49B5unit+30B5PG/Redis; newruntime split9audit+6capability+8completion+7notice|
| Existing host runner proof |8flowsPASS, inspected receipts/Git/Dockerstub only; not runtime evidence|
| B5 PostgreSQL/Redis |**NOT_RUN**,30newcases; all94PG/Redis cases unrun locally|

Executor local89B2–B5PASS/94runtime skips and PhaseA223PASS/1Pillow skip remain attributed direct
local receipts, not remote proof. The executor's POSIX-only skip explanation was incorrect;
raw PhaseA output identifies test_ai_job_polling.py:180 importing the live app without Pillow.
That documentation wording is corrected; raw receipts/packages are preserved. Local RQ is2.11,
last-reportedStudio RQ2.12; no RQ2.12runtime claim is made by these local probes.

## B5-R01 — P2 — unavailable audit prefix indefinitely hides ready quarantine work

Locations under backend/src/sketch2life/: application/services/ai_jobs.py:789–811;
infrastructure/ai_jobs/sql/repository.py:621–677,757–758,911–919; corresponding fake methods.

`deliver_side_effects` claims the oldest limited page. On sink failure it immediately releases
the row. `claim_side_effects` orders by created_at/message_id and leases that same released
prefix again on every call, with no continuation or failure deferment. A failing audit sink can
therefore block independent quarantine rows behind50audit rows even after the artifact sink
has recovered. The SQL/fake share the failing selection/release behavior.

Actual current service/fake reproduction:50olderaudit intents; an unsafe completion commits an
owned quarantine intent while both sinks are unavailable, so direct delivery fails. Restore the
artifact sink, keep the audit sink down. Three leased delivery calls return[0,0,0]:150audit
attempts, **zero calls to the healthy quarantine sink**, output still unquarantined. Directly
applying that exact stored quarantine intent succeeds. This is not loss of intent persistence;
it is indefinite recovery starvation caused by an unrelated unavailable sink.

Proof: evidence/local/b5-codex-review-20261015/probe_side_effect_starvation.{py,json};
**DIRECT_LOCAL_ACTUAL_SERVICE_FAKE_REPOSITORY**, no PostgreSQL reproduction claimed.

Fix within B5 using bounded fair traversal past failed rows, or a correct retry-availability
mechanism using the existing outbox. Do not merely increase LIMIT, spin on the same rows, drop
work, remove lease fencing or add a new queue/scheduler/schema. Preserve deterministic event IDs,
sink dedup, finite per-call behavior, SQL/fake parity and attempt bookkeeping isolation.
Regression: more than a page of audit failures with a pending quarantine behind them; restore
only the artifact sink and prove quarantine delivery, audit rows retained, no duplicate effects,
and finite all-failed behavior. Include a real SQL-adapter case for the correction.

## B5-R02 — P2 — accepted malformed capability representation bypasses redaction

Locations: infrastructure/ai_jobs/worker_capability.py:33,67–68,117–149;
infrastructure/ai_jobs/worker.py:92–119.

`_unb64` uses permissive urlsafe_b64decode, which ignores nonalphabet characters in the signature.
Prefixing a valid signature segment with punctuation such as `!!!` preserves the decoded MAC.
The verifier accepts the resulting malformed token and returns the same verified claims.
The redaction regex requires base64url characters immediately after the signature separator,
so that accepted representation does not match and remains in an actual filtered LogRecord.

Independent probe confirms the altered token verifies, has the same job/attempt claims, and
passes the actual service plus DispatchWorker start/progress/completion to SUCCEEDED. A LogRecord
containing it survives CapabilityRedactionFilter unchanged. This is a valid bearer token escaping
the intended filter, violating malformed-token rejection/token-free-log acceptance B-05e/B-10c.
**No HMAC forgery, different-job/attempt access or privilege escalation is claimed.**

Proof: evidence/local/b5-codex-review-20261015/security/probe_signature_encoding.{py,json};
**DIRECT_LOCAL_HMAC_FILTER_PROBE**, no Redis/PG proof. Reports contain booleans only; no raw
token/signing key is printed or persisted. Primary reran and confirmed the probe.

Fix strict whole-token/base64url validation/canonical decoding before acceptance and ensure
defensive redaction handles malformed input on logging/error paths. Test nonalphabet/padding/
trailing variants while keeping valid HMAC, binding, expiry, rotation and receipt replay cases.
Do not change the selected token authority/scope, serialize keys or introduce another auth system.

## Other reviewed behavior and bounded test clarification

No additional actionable SQL/UoW/notice defect was found. Authoritative completion writes its
CAS/receipt/intents in one transaction; audit-only errors and both replay conflict paths are
handled; side-effect ACK is separate from dispatch bookkeeping; notice query locks all matching
org/nonterminal rows with correct OR selectors and no pagination; sink dedup/effect share a fixture
transaction. These code checks do not mark the30newPG/Redis cases passed.

The real-process duplicate test at test_capability.py:190–206 compares artifact scope names.
The fake provider reuses the same scope key for an attempt, so a second provider execution could
overwrite the same row and still pass that assertion. Existing unit tests correctly count provider
calls; no duplicate-provider backend bug was found. Strengthening the integration assertion with
an owner epoch/call count is a small optional improvement within existing B-05 coverage, not a
third finding or a separate gate/card.

## Next and preserved package

Claude corrects only B5-R01/R02 under the existing approval using ignored
evidence/local/claude/prompts/CLAUDE_PHASE_B_B5_FIX_PROMPT.md, obtains meaningful regressions and
builds a new package. Studio remains f1c6834f: the new package must start there, not assume the
unrun B5 ZIP has been applied. Preserve old25-filedelta671a8617/43manifestc7492097/runnere7813419/
ZIP9475fe27 as reviewed history; no current permission to treat them as corrected acceptance.
New source needs code/package review before a user Studio run and focused closure before B6.

Raw report/probes/protected535pathhashes/pre-review docs/checks are ignored under
evidence/local/b5-codex-review-20261015/. Review updates state/context/handover only, preserves
backend/tests/fixtures/packages/approvedplans/approvals/Gitindex. No install/service/provider/
stage/commit/push/deploy. OwnerFence remains ASSUMED_CONTRACT; realB12integration deferred.

Final harness/security/architecture/git diff --check exit0. All535protectedpaths and the real
Git index remain unchanged; operator prompt/handover Git-ignored. Independent final review/
prompt-scope/current-handover consistency audits PASS. No unchanged full suite was repeated.
