# Feature decisions

## D27 — per-copy historical receipts never establish overall deletion

2026-10-18 approved P4/P5/AC08/09/11. Existing inventory report uses independent
exact current data-request read authority, not general operations capability.
Hold same scope SHARE/revision for bounded page and current lifecycle snapshots;
final grant/deadline confirmation before response. Pure projector validates native
source/current/scope/coverage/cursor bindings and emits only strict allowlist.
Reuse foundation_copy/report_label/actual_deletion_proven semantics; fixture deletion
and cancellation remain explicit not-actual labels. Opaque purge reference/hash/kind
are receipt backreferences, never raw bytes/provider URLs or execution authority.
Cancel confirmation not purge. Stored coverage remains historical attestation,
not fresh expiry/completeness proof. No global scan or vacuous all-deleted boolean:
overall_deletion fixed not_established even on empty/final/full-coverage page.
BE1 retains request closure; actual provider evidence/adoption remains separate.
No SQL migration/shared foundation/route/default app change. C6 audit next.

## D26 — operational counters are recorded metadata, never actual provider cost

2026-10-18 approved P2/P5/AC11. Internal AiPolicyOperations requires independent
current OPERATIONS_READ under held guard before any storage and rechecks rights
before return. Registry feature withdrawal does not hide remediation metadata.
Read own exact effective scope/policy pin/hash/state, never raw body/author/reason/
reviews. Caller-specified exact historical budget definition/unit/window is a
query filter, not adopted limit/current pin or permission. Reader uses existing
own SQL scope then bucket SHARE locks; no creating rows for monitoring. Missing
scope ends read immediately; missing bucket remains null, not false zero. Stored
zeros preserved. Optional reader absence remains unavailable, while failures/
corruption fail closed rather than become null success. Projection DTO revalidates
native bindings/booleans/counters; unknown private PolicyError sanitized.
Ledger counters include fixture settlements, so label recorded_ledger_not_actual_cost
and actual_cost=null. Never convert arbitrary units to money, fabricate provider
usage, or claim distributed snapshot/execution authority. No HTTP route, migration
or default app adopted; safe copy-report projection and C6 remain next.

## D25 — policy transport uses sole CMD-48; delayed stop needs generation fencing

2026-10-18 approved P1/P3/P5. Explicit bind_ai_policy(AiPolicyCommands) composes
existing strict AiPolicyCommand binding. Extend existing HTTP route's error seam,
not shared command/response fields or another endpoint. Closed known policy codes
retain safe statuses; unknown scope/definition/time/private messages generic503.
Uncaught private exceptions remain sanitized500; auth/preconditions/no-store/ETag
behavior retained. Never mount default app or choose permissive owner adapter.

Read foundation CancellationNotice/notice_matches/apply_cancellation_notice before
kill-delivery implementation. Current OR job_type/session/subject matching lacks
original policy-generation cutoff. Delayed stop after reactivation can hit new
work; do not guess feature-to-job mapping, mark delivered or rewrite published
foundation. Record explicit owner CR/payload semantics/tests and leave intent
pending. This is a genuine adoption gate, not task completion; continue approved
operational projection/review work while real wiring stays with teammates.

## D24 — atomic receipt resolution is historical evidence, not current authority

2026-10-18 approved C4/P4/P5. Hold exact receipt lease around own scope UPDATE
transaction, re-read immutable operation/delivery revision/reference and current
copy. Stable resolution key binds original envelope/delivery/reference/outcome/
verification/evidence-kind/reason, excluding renewed grant/time/proof expiry.
Exact retry still reauthorizes but returns current copy without new mutation.
Different verification semantics require copy CAS and immutable new observation.
Current snapshot, full before/after proof+grant and outbox commit together.
Strict read validation recomputes transition/binding against original operation;
history never grants execution. Forward ap_0009 prevents deleted provenance or
confirmed provider-cancel downgrade. Cancellation is distinct from purge/job
closure; foundation lifecycle remains unchanged. Fixture proof never becomes
actual deletion. Current rights/proof confirmed before commit; guard exit after
commit remains uncertainty, not rollback. Actual PG/provider/deadline fencing
requires separate external evidence; owner requests batched testing.

## D23 — exact operation proof lease, not a transport-success acknowledgment

2026-10-18 approved C4/P4. Receipt reference/hash derives from stored
receipt_available delivery at exact expected revision, not caller proof fields.
Current read authority before inventory; immutable command/actor/org/copy/profile
must match. Trusted proof binds full operation/delivery/reference/current authority
revision; native DTO, expiry and cancel-vs-purge outcome checks before yielding.
Frozen lease exposes binding/current grant/proof and confirms rights/deadlines
through context exit; no use after guard closes. Existing foundation purge rules
retain unverified pending and fixture-only deletion labels. Cancel acknowledgment
separate, no job mutation or false copy deletion. Synthetic provider-kind tests
exercise classification only, not actual provider evidence. Persistence/CAS/proof
history remains next; caller holds guard, re-reads states and confirms before
commit. Guard exit after successful commit is uncertainty, never fake rollback.

## D22 — pinned cutoff candidate queries never authorize retry or expired takeover

2026-10-18 approved C4/P4/P5. Internal CopyCandidateRequest supplies explicit
as_of for first page OR typed scoped cursor for continuation, not both. Cursor
retains org/scope/inventory revision/cutoff/key; fresh mutation rejects stale scan.
Own scoped SQL join filters missing delivery row (queued), pending/exception and
in-flight expiry <=cutoff, limit+1 keyset. Unsupported/receipt and active claims
excluded. No numeric retry/TTL policy chosen, schema changed or route mounted.
Cutoff is a scan timestamp, not wall-clock authority: even future-cutoff candidates
must pass actual current dispatcher retry/deadline/profile checks and claim CAS.
Internal cursor is metadata, not signed bearer permission; never expose directly
as a trusted public auth token. Scope absence read stays rev0/empty/no later query.

## D21 — phase history references immutable source states, not current permission

2026-10-18, approved P4/P5 C4c4. Own append-only ap_0008 evidence stores actor/org/
scope/key, phase, BEFORE delivery revision, observed grant/deadline/time. Original
immutable operation binds data-request/profile. Reconstruct source snapshot from
immutable delivery history (rev0 queued only for existing operation), recompute
full phase digest and validate authorized transition against current snapshot.
Claim and completion evidence share mutation rollback. Dispatch now uses UPDATE
UoW to durably record preparation evidence/outbox before hook; still no DB lock
during hook. This history does not prove send, provider ack/deletion or authority
for later execution. Missing/failure proof never silently falls back to no-op.
Actual owner/source commit/deadline fences and provider dedup remain unadopted;
SQL91 NOT_RUN, not completed acceptance from memory/offline checks.

## D20 — each delivery phase needs current authority, never an old envelope grant

2026-10-18 approved C4/P4/P5. New explicit delivery authority port binds exact
original envelope/full state/phase to current actor/org, retry/worker policy and
approved claim deadline bounded by current grant expiry. No default adapter or
caller-supplied deadline. Existing command guard authorizes before inventory read;
exact actor/org/data-request and original profile must match intent. Claim and
completion re-confirm unchanged authority inside own UoW. Dispatch rechecks claimed
state and current authority, exits DB transaction, then calls hook under owner
guard. Real remote-start/deadline-at-commit enforcement remains adoption work.

Missing hook -> Unsupported; private hook failure or malformed output -> safe
Exception metadata, never deleted/cancelled. Revoked/expired/late completion does
not rewrite state or fabricate rollback of already-sent effect; persisted claim
remains recoverable. Same original envelope/key on explicit authorized retry.
No provider/default live hook invoked. Current phase grants are verified but not
yet retained in durable phase-specific evidence history; that acceptance remains
open with verified receipt/current-copy/cancel reconciliation and pending filter.

## D19 — delivery ownership is distinct from authority and verified copy lifecycle

2026-10-18, approved P4/P5 C4c2. Add separate own pure delivery state, not a
replacement of foundation copy lifecycle. Explicit token/deadline (no TTL default),
revision CAS, busy unexpired claims, expired takeover with new token and retained
used-token history fence ABA/stale responses. No response earlier than claim start
or at/after deadline. Completion records reference-only hook metadata; identical
last-response replay returns unchanged history, not a new dispatch grant.

Unsupported/receipt-available do not automatically redispatch; pending/exception
are mechanically retryable only after future current authorization/retry policy
checks, NOT unlimited-retry permission. Receiving a reference/hash does not verify
provider evidence or confirm cancellation/deletion. Exact hook key/digest checked
by strict native response bridge; no raw verified/deleted/cancelled fields.

Own forward ap_0007 stores current snapshot/CAS plus immutable history in same
scope-serialized UoW as outbox event. Queued rev0 is lazy metadata only for an
existing immutable operation. No mutation of original envelope/foundation.
Production current-owner commit/deadline fences, approved claim/retry values and
guarded dispatcher/pending query remain unbound. Do not invoke hook under DB
transaction or treat persisted claim as permission. SQL86 NOT_RUN; no actual hook.

## D18 — discovery pages enumerate intent metadata, not pending execution grants

2026-10-18, approved C4/P4/P5. operation_page is an internal transaction method,
requiring adopted current read guard before opening own scope SHARE transaction.
No mounted route/default auth. SHA256 keyset cursor, limit1..256 and exact scope
revision on continuation prevent mixed-revision scans. A new intent/fence/copy/
coverage mutation invalidates old cursor; proof-only replay does not. Missing
scope read linearizes at absence, no later query mixing future intents into rev0.
Enumeration returns keys of ALL intents; pending/claim/ack state is not yet built.
It grants neither dispatch authority nor actual deletion/overall BE1 closure.
Worker revalidates original command/profile/rights before future claim/dispatch.

## D17 — stable operation identity separates original intent from renewed authority

2026-10-18, approved P4/P5 C4b2b2. Internal schedule accepts existing strict
ProviderCopyCommand plus exact copy ID, actor/org outside payload. Current copy
verification guard authorizes before inventory read, resolves original exact
profile outside own DB lock, then authorizes complete target binding. Re-read
immutable registration under UPDATE scope lock and confirm unchanged current
authority before commit. Guard owns real source/request expiry/revocation fencing;
fixtures do not prove production adoption. No published foundation changes.

Key hashes actor/org/scope/client-request/copy/action, independent of renewed
authority/time. Body digest includes exact data-request and original registration/
profile; same key/different body conflicts, no silent repinning. Owned ap_0006
stores original envelope and append-only authority observations. Exact retry adds
fresh authority history but no new queued event/revision; preserve original grant
as history, never current permission. Purge also fences scope atomically; cancel
is only an intent, not actual stopped acknowledgment. Recovery by exact known key
is historical read only; pending discovery/claims/delivery and verified outcomes
still belong to C4c. PG78 prepared NOT_RUN, real provider/owner adoption separate.

## D16 — historical verification is retained atomically, not reused as authority

2026-10-18, approved P4/P5 C4b2b1. Append-only own inventory evidence contains
exact action/body binding, actor/org/data-request, current authority revision/
deadline, source reference/hash/deadline and original registration/coverage.
Keep evidence and inventory writes in one UoW with rollback; immutable ap_0005
trigger rejects raw SQL update/delete. Frozen ap_0004 is unchanged. Retain a new
verification observation on exact registration/fence retry without advancing
inventory revision or duplicating mutation events. Scope revision pages are not
invalidated by proof-only history. Internal decode recomputes canonical binding
and checks scope/actor/time columns; no raw provider bytes or endpoint fields.

History proves only which backend checks were observed, not actual current
authority, provider completeness, dispatch, cancellation or deletion. Actual
owner/source adapters remain ASSUMED. Cancel/purge exact operation envelopes,
delivery/recovery and typed acknowledgment are still next, not replaced here.
PG70 NOT_RUN; no server/provisioning or real provider invocation authorized.

## D15 — source assertions come from guarded backend, not inventory caller

Approved P4 C4b2a adds reference-only context/read calls and guarded inventory
service. Register includes exact source ref/hash; coverage accepts only revision
and attestation ref. Backend source resolver authenticates original provenance/
explicit scoped observation; strict proof/native output validation rejects caller
booleans and substituted org/scope/digest/revision/reference. Separate action tags
in canonical digest preserve independent register/read/coverage/fence authority.
Replay still verifies current source/rights. Own current grant validation shared
with C4a without changing foundation/shared owner code.

Owner/source guard precedes registry UoW and stays held to commit; confirmation
checks unchanged current authority/deadline and source expiry before UoW exit.
Confirmation must use pre-acquired fences, not new outer locks/network under DB
lock. Actual owner deadline-at-commit adoption is not proven by prechecks/mutex.
An error after own DB commit is uncertain response, not fabricated rollback;
exact registration/fence retry rechecks authority and cannot duplicate mutation.

Read returns stored coverage as reported metadata, not newly authenticated global
provider completeness. Source-proof validation is guarded but not durable source
evidence history yet; registration persists original profile/id only. Next operation
envelope/evidence persistence remains C4b2b; dispatch/typed acknowledgments/current
copy lifecycle/receipt application C4c. Real authority/provider/PG65 NOT_RUN, not DONE.

## D14 — durable original inventory, not inferred provider-wide completion

Approved P4/P5 C4b1 adds own ai_policy copy_scope/registration/coverage/registry_event
and forward ap_0004. Store explicit exact original profile ref/version/hash, kind,
copy/org/scope and initial quarantine; immutable records, duplicate exact registration
no-op, changed provenance conflicts. Purging flag monotonic and revision-CAS; late
registration is initially quarantined using foundation request_purge for initial
metadata, not a provider call. Earlier copies remain fenced by scope flag, not by
rewriting original registration. initial_copy is explicitly NOT current lifecycle.

Scope UPDATE serializes writes and audit/outbox; scope SHARE freezes keyset pages.
Continuation requires revision, any intervening mutation rejects stale scan. Missing
scope read returns its observed empty revision0 snapshot without querying later
phantom rows, not provider-wide absence. Scope-bound coverage report carries source
attestation ref/hash, registry revision and explicit required/observed source sets.
CAS applies report to next scope revision, later registration/fence invalidates it.
reported_complete means declared-source report only; no deletion or BE1 closure.
Actual discovery authority/current-owner/expiry fence remains unbound.

Own scoped get/register/page port intentionally does not silently implement the
published foundation unscoped/profile-string-only interface. CR still OPEN, no
foundation/shared bytes modified. No current lifecycle/operation acknowledgment
or provider purge proof supplied by registration/coverage. Continue own intent/
authority services and verified receipt application; actual PG63 NOT_RUN, not DONE.

## D13 — exact copy verification bridge, no implicit foundation amendment

Approved P4 C4a reuses foundation copy state machine and PurgeReceipt. Own strict
reference-only command binds exact data request/scope/action/key; verified actor/org
outside body. Current owner guard must resolve subject/purpose/source expiry and
original adopted profile version/hash, not latest alias. Exact canonical binding
also includes copy id/kind, profile and authority revision; trusted backend verifier
authenticates bytes/hash/issuer/operation/outcome and echoes exact binding/reference.
Revalidate native grant/proof types (no allowed=1/verified=1) and current unchanged
authority/expiry after verification. Guard retained through yielded caller work,
but mutex alone cannot enforce wall-clock expiry at registry commit: real owner
commit-fence adoption remains required.

Only foundation PurgeReceipt returned; no provider side effect or registry mutation.
Unverified deletion remains pending, fixture deletion not actual. Synthetic test of
provider-kind mapping is not real provider verification. Published foundation/shared
bytes unchanged. CR_PROVIDER_COPY_ADOPTION documents missing durable registry pages/
coverage, immutable original profile ref, operation-key dispatch deduplication,
typed cancel acknowledgment/missing-hook outcomes and current commit fence. CR is
OPEN, not adopted schema or blocked whole-card work. Continue own registry/intent
code; real owner/provider wiring still deferred to teammates as instructed.

## D12 — service replay rechecks authority; cleanup never resurrects stopped work

Approved P3 C3c3c composes current-use lease -> accounting guard -> own ledger UoW
for reserve. Exact original supplied pin retained; stable original-pin/attempt id
across client keys prevents double holds. Every replay obtains a current exact
quote and use decision; changed numeric terms/window conflict rather than migrate
old held funds. Terminal reservation cannot resume. No provider call or permission
from a returned reservation/snapshot; dispatch remains separately fenced.

Settlement has explicit backend target feature (not client authorization), current
accounting guard, original reservation and authenticated reference-only terminal
evidence. Rebuild native proof/nested keys to reject bool-coercion or constructed
invalid values. Consume/release must match disposition; reconcile permits either.
Exact command fingerprint/receipt and terminal proof replay have no double delta;
receipt claiming a never-committed settlement is corruption, not permission to
complete it silently. Rights/evidence rechecked even after previous success.
Cleanup can finish after stop without invoking current-use grant. Real guard must
acquire owner fences before ledger lock; verifier cannot lock outer owner/policy
state or perform provider network work under ledger lock.

Ledger commit is not distributed 2PC. If an outer guard reports an error after
ledger commit, do not invent rollback/refund; report safe dependency failure and
allow exact current-authorized retry to inspect committed receipt without a new
hold. Tests label MEMORY/ASSUMED truthfully. Current real-owner/evidence fencing,
actual provider cost and 44 actual PostgreSQL cases remain NOT_RUN; not full DONE.

## D11 — global scope serialization and atomic ledger intent, not direct dispatch

Approved P3/P5 C3c3b adds own resource_scope, budget_bucket, resource_reservation,
resource_receipt and resource_event with forward ap_0003. Scope UPDATE precedes
bucket/reservation access; global occupied slots do not reset across windows or
definitions. Unique original request-digest/attempt prevents second allocation
using a different reservation key/window. Counter transitions, immutable terminal
reservation, scoped receipt and pending audit/outbox intent share one own UoW.
Foreign keys for receipt/event include org/feature/reservation. No foreign owner
table touched or old migration rewritten. Event delivery marker is mutable, not
its audit payload; intent is not evidence of delivery or provider action.

Persistence is never a quote/current-use/terminal-proof authority. Following
application service must hold real use/accounting guards before ledger lock and
through commit, verify exact returned quote/proof and idempotent request identity.
No provider work while holding ledger lock. Current DDL/codec tests and 17 prepared
actual SQL cases do not prove runtime transactions/races; separate authorized
PostgreSQL execution still NOT_RUN. AC06 and full BE2-14 remain open.

## D10 — accounting transition is not a grant or an atomic ledger

Approved P3 C3c3a separates pure immutable resource accounting from authoritative
quote/terminal-evidence resolution and future atomic storage. Budget buckets bind
org/feature/exact definition/unit/window, while occupied slots remain global to
org/feature across window/definition changes. Explicit zero ceiling denies;
zero estimate still holds a slot. No adopted numeric defaults, expiry or refund
on assumed cancellation. Duplicate exact live reservation and same terminal proof
produce no delta; conflicting or terminal re-reservation denied. Actual verified
spend above estimate/ceiling remains truthful overrun, never clipped to conceal it.
Settlement uses original terms after policy/window changes; this does not grant
execution after stop. Fixture proof remains fixture, not actual provider cost.

Trusted quote binds actor/org/current held observation/attempt; reservation request
digest retains original pin across current-phase/epoch/registry rechecks. Caller
cannot set numeric terms or verified proof. Ports require held authoritative
guards; no permissive adapter or independently cacheable permission is supplied.
This checkpoint has no atomic ledger SQL, service or actual concurrency proof and
does not close AC06. Next implementation must persist own counters/reservation/
receipt/audit intent atomically and verify races, rollback and restart separately.

## D09 — original pin continuity, no resurrection across stopped epochs

Approved P2/P3 C3c2 gives backend-held current-use leases, not cacheable permission.
Explicit selected profile, exact request id/revision/input/purpose and original
policy/version/hash/epoch preserved. Every phase checks current use-authority,
registry/proofs/governance and scope. Ordinary replacement can preserve old pin
only while its old exact policy and current eligibility remain valid. Any stop
after original activation revokes that pin even after new reviewed activation.
Immutable activation history must match origin pin, so changing epoch cannot
skip a stop. Scope SHARE lock/current guard held through nested consumer work;
real owner fence and cross-owner composition remain separate integration proof.
No new migration, job/session writes, provider/profile values or extra CMD action.
Actual budget accounting/reservation and phase permission at provider remain open.

## D08 — emergency stop uses epoch CAS, not stale wildcard cancellation

Approved P3 internal stop contract requires feature/key/expected_epoch/reason;
verified actor/org outside payload, current DISABLE only. Existing known scope
can always be blocked for remediation even if registry definitions withdrawn;
uninitialized scope requires known available feature. Null-pin epoch0 is unusable.
Stop increments epoch once with intent/receipt in same own UoW; already disabled
exact epoch/new key records receipt without duplicate intent. Replay rechecks
current rights and exact stopped snapshot; after reviewed replacement/reactivation
old receipt fails, never stops newer pin. No ninth CMD-48 action, migration,
production timeout/budget/window or actual cancellation acknowledgment supplied.
Atomic budget/concurrency and current usage fencing remain subsequent work.

## D07 — commands and effective pin share one UoW, not a post-commit callback

Approved P1/P2/P5 C3b adds eight command handlers and forward ap_0002 scope/epoch
transition. Scope lock precedes parent record; target feature is revalidated after
locks. New version cannot move an existing record to another feature, preventing
ambiguous stale active pin routing; use separate independently governed record.
Publication/disable/receipt/outbox atomic; replay never repeats effective changes.
Withdrawn definitions do not prevent negative review or recall/archive remediation.
Newly proposed proofs require current owner decisions, not assumed remote existence.
Scope epoch0/null pin is not permission. No wildcard job cancellation or actual
provider effect inferred from pending scope intent. C3c limits/emergency kill and
C5 HTTP error catalogue/composition remain pending. C2 runtime tests now pin original
ap_0001; new --activation pack covers current head separately, both NOT_RUN until
environment authority exists. No previously published migration bytes modified.

## D06 — resolve exact adopted definitions, do not promote observations to grants

C3a under approved P2 adds side-effect-free author validation via candidate
current registry guard. Check exact org/feature/kind/id/version/hash/revision for
every reference, no fallback or raw settings. Registry adapter must validate actual
approved values, safety and foundation compatibility before resolving; fixture
does not prove that adapter exists. Mutation callers retain guard through commit;
earlier observations cannot authorize later activation/use. No production values
or authority invented. Native Python strict revalidation is necessary: serializer
may convert model_construct(version=True) into JSON integer 1 before validation,
so validate native dumps to preserve type rejection. One first-test FAIL exposed
this, then corrected with regression on body and returned binding instances.

## D05 — C2 schema isolation and honest pending runtime — 2026-10-17

Approved P5 gives own ai_policy lifecycle tables and independent frozen migration;
register metadata/schema additively in existing Alembic environment. Existing
published migration bytes and other modules' tests/logic unchanged. Record/review
CAS, append-only proofs/receipts/events, atomic outbox and scoped FKs owned here.
Store latest dimension proofs ordered by their own review revision so replacement
roundtrip matches domain ordering while all originals remain queryable. No unused
effective policy/kill epoch/reservation fields until C3 implementation uses them.
Offline compiled DDL/actual Alembic render is not runtime proof. AP opt-in is
separate from LC: BE2-12 isolated-server authorization is not reusable for BE2-14.
15 PG cases prepared; no server install/start. Runtime approval requested; no
claim that component regression proves actual migration or real current authority.

## D04 — strict policy review target and action round trips — 2026-10-17

C1 uses own ai_policy review DTO under approved P1, never learning_content target
or a modified DATA-24 schema. Strict action-specific presence rejects spare/null
fields; wrap serializer omits absent fields to retain valid receipt/binding round
trips. First run exposed default serialization adding spare nulls (8 FAIL/108 PASS);
fixed serializer without permitting client null spare fields. Existing dispatcher
binding remains unchanged. Literal[True] gates additionally require actual bool,
not coercible 1. Profile/definition refs are shape only until trusted registry
validation in application, not proof of compatible/adopted runtime settings.
Pure domain is separately owned and framework-free; services will retain original
proof history, own global CAS and external current-proof eligibility through commit.

## D03 — actual revision-1 implementation approval — 2026-10-17

Owner replied "duyệt" to the immediately preceding explicit request to approve
plan revision 1/P1–P5. Pinned SHA256 is unchanged. Begin C1 and scoped checkpoint
commits; no inferred permission for provider use, production values, PostgreSQL
provisioning or external owner sign-off. Historical proposed status is superseded
for these card-local decisions, not rewritten in reviewed plan bytes.

## D01 — new card, existing branch, separate approval — 2026-10-17

User requests next task after explicit BE2-14 proposal. Use free FEAT-049 and
same user-renamed feature/be2-08-14 branch. Preserve BE2-12 history/evidence and
owner integration deferral. No need to wait for full BE1/P4 wiring just to plan.
No inherited implementation or provisioning approval from BE2-12/ADR0018.

## D02 — whole-card plan, no provider/platform invention

Include ProviderCopyLifecycle ownership as required by FEAT040; existing
foundation support is reuse input, not full BE2-14 completion. Profile/limit
definitions reference approved values; no secrets or arbitrary fields. Keep
real provider verification, current auth and integration distinct from fixtures.
P1–P5 are proposals pending approval, not approved schema/security policy.
