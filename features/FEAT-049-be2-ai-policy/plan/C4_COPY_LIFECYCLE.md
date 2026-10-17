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
