# C4 — reuse foundation lifecycle, add exact verification and explicit missing gates

Approved P4, historical goal file does not authorize widening BE2-12; later actual
BE2-14 revision1/P1-P5 approval authorizes this card. Foundation published files
stay unchanged until cross-owner CR/adoption. No provider calls/adoption inferred.

## C4a exact receipt boundary

Inspect/reuse domain/ai_jobs/provider_copy.py and existing application service/ports.
Add reference-only BE2-14 command/evidence shapes and authoritative verification
port. Backend actor/org outside payload, exact data-request ref/version/hash and
scope/action/key in command. Current owner guard resolves authority, purpose,
source/data-request expiry and adopted exact profile; no caller boolean or URL.
Bind principal/org/command/current authority revision/target copy kind/id/scope/
exact profile/operation key in canonical digest. Verifier authenticates exact
receipt bytes/hash/issuer/outcome and evidence kind, not just shape. Grant must
remain unchanged/current through verification exit; no invented TTL.

Rebuild native strict models to reject constructed coercions; exact verifier echo
must match binding/reference. Expired/mismatched/cross-org/profile receipts denied.
Verified false deletion remains pending through existing domain apply_receipt;
fixture evidence never actual_deletion_proven. Return foundation PurgeReceipt for
reuse, do not invent competing copy states or silently apply outside registry UoW.
This checkpoint does not dispatch/cancel/purge, mutate registry or prove deletion.

## C4b/C4c remaining, not replaced by C4a

Current foundation ProviderCopyRegistryPort has all-scope tuple reads, process-lock
candidate and fake-only infrastructure. Need own durable registry/atomic receipts,
late registration fence, stable pages and coverage/completeness. Current adapter
cancel returns None, purge has no operation key/receipt ref envelope, so cannot
prove external effect deduplication/restart or cancellation. CR must specify safe
additive extension/adoption before touching published surface. Missing hook must
be typed Unsupported/Pending without synthetic provider-deletion proof. Empty
registry is not complete coverage; BE1 owns overall data-request closure.

Then implement scoped execution with current guard/source expiry, durable exact
copy/profile/operation idempotency, cancellation/purge intents, verified receipts
and safe report to BE1. Preserve existing lifecycle semantics and all foundation
regressions. SQL/runtime/actual-provider verification are separate proof gates.

## C4b1 durable inventory checkpoint

Own copy scope/registration/coverage/audit metadata under ai_policy, forward ap_0004.
Registry is inventory/provenance, not a duplicate lifecycle or job table. Backend
registration requires exact original profile id/version/hash and copy kind/id/scope;
no state/verified/deleted input. Immutable registration includes whether observed
after scope purge fence; reuse foundation request_purge only to derive initial copy
metadata, never actual dispatch. Purging flag monotonic; no unpurge/resurrection.
Existing copies are fenced by scope flag even if originally registered earlier.

Scope UPDATE serializes registration/fence/coverage/audit. Duplicate exact copy is
no-op; changed original kind/profile conflicts, never silently overwrites history.
All mutation and audit/outbox intent share own UoW. No external calls under lock.
Read holds scope SHARE; sorted keyset page limit1..256 and expected scope revision
are required for continuation. Any intervening mutation invalidates old cursor;
no mixed-revision scan passed off as a stable snapshot.

Coverage observations are backend reports with exact attestation ref/hash, registry
revision, explicit nonempty required sources and observed subset. CAS expected
scope revision; store observation at next scope revision with audit, without any
copy mutation in between. New registration/fence invalidates old coverage. Empty
registry defaults unknown. reported_complete refers ONLY to declared-source report,
not authenticated provider-wide completeness, deletion or BE1 request closure.
Actual discovery authority/fence adoption remains C4b2/C4c, not client booleans.

No existing foundation interface changed/implicitly implemented: old unscoped get
and profile-string-only register cannot safely reconstruct original exact metadata.
Keep explicit own scoped port and CR OPEN. Follow with durable operation intents,
typed provider hook acknowledgment/verified receipt application and current-owner
registry commit fencing. Own SQL pack must test CAS/pages, late registration,
rollback/reconnect and immutable provenance; NOT_RUN until authorized PG17 profile.

## C4b2a current-owner inventory service

Compose own inventory port with held authoritative data-request/source/profile
guard, not fake default auth. Separate register/read/coverage/fence actions in
canonical binding; no new CMD-48 action or mounted endpoint. Context exact
data-request ref/scope, verified actor/org outside body. Registration also needs
reference-only source evidence; backend verifier authenticates original copy and
profile provenance and echoes exact digest/reference/expiry. Client never submits
verified/allowed flags or observed/required coverage assertions.

Coverage API accepts only expected revision and attestation reference; trusted
resolver returns strict scoped observation/proof. Verify exact org/scope/revision/
attestation binding, source proof/current owner expiry and unchanged authority.
Then enter own registry UoW, write, and confirm current owner/proof deadline again
before leaving commit context. Same registration/fence replay rechecks current
rights/evidence. Read page uses current owner and typed revision cursor; cached
coverage stays reported metadata, not fresh provider completeness authority.

Guard pre-acquires owner/source fences before registry lock; confirmation under
lock must not acquire outer locks or call provider network. Actual expiry-at-commit
fence adoption remains explicit, not inferred from mutex/application clock checks.
No provider side effect, actual deletion, closure or dispatch grant from result.
Durable exact operation intents remain next C4b2b; current state/typed dispatch/
acknowledgment/verified receipt application remain C4c, not replaced by service.

## C4b2b1 durable inventory verification history

Before operation scheduling, retain append-only verification records for successful
register/coverage/fence calls in the same inventory UoW. Store exact actor/org/context,
action and canonical command digest, current authority grant, verified source reference/
deadline, original registration or scoped coverage observation, and observation time.
Exact registration/fence retries retain a fresh verification record without advancing
inventory revision or duplicating mutation events. History is historical evidence,
never current permission or a dispatch envelope. Reads do not create scopes/history.
Own forward ap_0005 adds the table and immutable trigger; ap_0004 stays frozen.
Rollback must remove both inventory changes and evidence. Actual SQL proof remains
NOT_RUN pending separately authorized environment. Exact cancel/purge intents and
their recovery/dispatch remain the following checkpoint, not replaced by this history.

## C4b2b2 exact durable cancel/purge scheduling

Internal schedule(actor, org, command, copy_id) reuses held current copy verification
boundary: authorize scoped request before reading, resolve exact original profile
outside DB lock, authorize full target binding, then re-read immutable registration
under UPDATE scope lock. Own UoW stores immutable reference-only operation envelope,
authorization observations and queued event atomically. Purge also fences scope in
that transaction; cancel is only an intent, not a confirmed lifecycle transition.
Derive stable operation key from actor/org/scope/client request/copy/action. Bind
full data-request version/hash and original registration in command digest. Same key
with changed body conflicts; renewed authority/time never silently changes original
envelope or key. Exact retry still checks current rights/profile and stores a fresh
authority observation without another queued event. Read recovered envelope is
historical metadata, never a permission/claim to dispatch; no provider network under
DB lock. Forward ap_0006 adds owned operation/history tables and immutable triggers.
Test idempotency, forged/native models, scope/profile mismatch, expiry/revocation,
atomic intent/fence/event rollback and replay after reconnect; prepare PG cases
without provisioning. C4c delivery, provider acknowledgment/current lifecycle and
verified receipt handling remain required, not inferred from stored intent.

## C4c1 revision-bound intent discovery

Provide internal scoped keyset pages of immutable scheduled operation keys under
the existing scope SHARE lock. Limit1..256, SHA256 after-key and exact inventory
revision required on continuation; reject intervening writes. Missing-scope read
stays revision0/empty without a later phantom query. This enumerates ALL intents,
not only pending/eligible work: current delivery/ack state does not yet exist.
Never expose a public endpoint, call provider or treat enumeration as claim or
current authority. Worker must hold adopted owner read guard outside this UoW;
actual dispatch separately revalidates original command/current rights/profile.
No schema change; add SQL isolation/reconnect/stale-page cases to existing pack.

## C4c2 delivery claim and truthful response semantics

Define a pure delivery state machine separate from existing copy lifecycle.
Queued/pending/exception may be claimed by exact expected revision, explicit token
and explicit deadline supplied by current authorized application (no default TTL).
An unexpired in-flight claim is busy; expired claim may be replaced with a new
token/revision but old response must then fail, with same provider operation key.
Preserve used token history so a released/expired token is never reused (ABA).
Outcome completion requires current token/revision and unexpired claim; duplicate
identical recorded response is idempotent metadata, changed response conflicts.
Typed hook response carries exact operation key+binding digest, Pending/Unsupported/
Exception or receipt reference/hash. ReceiptAvailable is NOT verified/deleted or
cancel-confirmed. Unsupported and receipt-bearing states do not auto-retry;
subsequent verified lifecycle reconciliation remains distinct C4c work. Pure domain
cannot authorize execution; own SQL CAS/claim persistence, authoritative composition
and typed hook invocation still required before dispatch. Publish internal hook
port requiring exact original immutable envelope, stable provider idempotency key,
and no call under DB lock. No real hook/default implementation or provider call.

Persist delivery state/CAS and immutable state history in own forward ap_0007,
same existing inventory UoW/scope lock and outbox event. Lazy queued state derives
only from an existing exact operation, never from an arbitrary key. Fresh claim
and completion each advance delivery revision; duplicate recorded completion does
not write twice. Internal SQL transitions are not authority; guarded dispatch
composition remains subsequent C4c work. Strict persisted codec binds snapshot
operation/hash/revision/status back to immutable envelope. Prepare SQL rollback,
concurrent claim, expired takeover/late response, reconnect and immutability cases;
actual SQL NOT_RUN until separate environment approval.

## C4c3 guarded dispatcher composition

New explicit delivery authority boundary extends current copy owner/profile guard;
trusted authorize_delivery binds original envelope + current snapshot + phase
(claim/dispatch/completion), current worker/retry policy and explicit approved claim
deadline bounded by grant expiry. No caller deadline/default TTL/retry grant.
Authorize scoped read first, require exact actor/org/command/key binding and original
profile, claim in own UoW with authority confirmation, exit DB transaction before
hook. Re-read claimed token/state under SHARE and reauthorize dispatch immediately
before hook, while owner/profile guard held. Hook absence -> Unsupported; exception
or malformed output -> safe Exception metadata, not deletion/confirmed cancellation.
Completion reauthorizes and compares unchanged claim under UPDATE before recording
response; revoked/expired/late responses leave committed claim recoverable, never
invent rollback of external effects. No hook resend from completed metadata; future
retry needs explicit current authorized state/revision and stable original key.
Use ASSUMED/MEMORY tests, plus prepare SQL composition/restart tests. Real owner/
hook deadline enforcement and cross-process provider dedup still integration gates.

## C4c4 durable phase evidence

Append immutable phase authority referencing original operation and BEFORE delivery
revision, reconstructed from immutable history (rev0 queued only). Recompute exact
phase binding, validate observed grant/deadline/actor/org and allowed transition to
current state. Claim/completion evidence shares mutation UoW; dispatch evidence
commits before hook in own UPDATE UoW. Evidence of preparing to send is not proof
of send, ack or deletion. Forward ap_0008 own table/trigger; preserve frozen history.
Test atomic rollback/proof binding/reconnect/immutability, PG remains NOT_RUN.

## C4c5 bounded candidate discovery

Internal query selects unclaimed intents, pending/exception and in-flight claims
expired at explicit pinned as_of. Exclude unsupported/receipt-available and active
claims; candidate is NOT a permission/retry decision or provider completeness.
Closed typed request: first page supplies as_of, continuation only scoped cursor
(org/scope/inventory revision/as_of/key), never independent replacement cutoff.
Own scope SHARE/revision CAS prevents mixed-revision pages, empty missing-scope
stays revision0. Bounded keyset SQL join/filter/limit+1, no unbounded Python scan
or caller expression. Existing dispatcher still rechecks actual clock/current
rights/retry/profile and CAS. Synthetic query/PG cases; no worker/live provider.
