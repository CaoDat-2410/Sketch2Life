# C4b2b2 — exact internal operation intents

Parent edc1d40, feature/be2-08-14, approved P4/P5. 2026-10-18.

ProviderCopyOperationService.schedule(principal_id, organization_id, command,
copy_id) accepts existing strict ProviderCopyCommand (client request ID, exact
data-request ref/version/hash, scope and cancel/purge). Actor/org verified outside
body. It reuses own ProviderCopyVerificationBoundary, NOT a production default.
Authorize before read, resolve original exact profile outside SQL lock, authorize
full target binding, re-read original registration and confirm current rights in
write UoW. Owner/source/profile fences must be pre-acquired and held through commit;
confirmation under registry lock must not acquire new outer locks/network. Real
deadline-at-commit enforcement remains an adoption gate, not a fixture guarantee.

Operation key deterministically hashes actor/org/scope/client request/copy/action.
Full binding also covers exact data-request and original registration/profile.
Changing body under same key conflicts. Separate cancel/purge and distinct client
requests have distinct keys. No automatic new key on error, timeout or retry.
Original envelope/grant/time immutable; fresh authority observation appended on
every exact authorized retry without duplicate queued event or registry revision.
Do not reuse old authority when retrying. Get_operation(key) recovers historical
metadata only, not permission to dispatch or an enumeration/recovery worker.

Own forward ap_0006 adds copy_operation and copy_operation_authority, scoped FKs
to own copy registration and immutable update/delete triggers. Intent, queued
event, authority observation and purge scope fence share own transaction. Cancel
intent does NOT imply worker stopped; no current lifecycle mutation/ack/deletion.
All own store implementations must implement the two added operation methods;
no optional/no-op fallback. Private dependency errors remain sanitized.

689 own component, 477 selected regression, 114 targeted foundation PASS. Actual
PG78 prepared NOT_RUN; ASSUMED authority/MEMORY and offline codec proof only.
Use C2_SQL_RUNTIME.md for exact source-pinned four-pack commands, prerequisites,
impacts and safe report return on separately authorized disposable PG17. Do not
provision a server, call provider or mount default auth from this handoff.

Next C4c: scoped pending operation enumeration/claims, revalidated dispatch,
typed missing-hook/pending/error/cancel acknowledgments, current copy state and
verified receipt application, crash/late-result recovery. Provider hook dedup of
this exact operation key is not proven by internal intent idempotency. Foundation
CR remains OPEN. C5 safe bindings/projections, kill intent delivery and C6 full
acceptance plus actual owner/provider/PG integration remain separate open work.
