# C4c2 — delivery claims/state and truthful hook response

2026-10-18 Asia/Saigon; feature/be2-08-14 parent f2afc7e, approved P4/P5.

## Internal APIs and composition obligations

Own domain DeliveryState/DeliveryResponse and claim_delivery/finish_delivery are
pure transition rules. Existing copy lifecycle remains untouched. Queued metadata
comes from existing immutable operation only; no arbitrary-key claim creation.
Current scope store transaction adds get_delivery, claim_delivery(operation_key,
expected_revision, token, expires_at), finish_delivery(response, expected_revision,
token). All mutations require UPDATE UoW. Persistence is NOT authorization; caller
must hold actual owner/profile/source/revocation/deadline guard through commit.
No default guard/worker hook is mounted, and no claim is granted by component tests.

Claim deadline is explicit, no TTL invented. Later trusted composition must bound
it to current approved authority/source/profile/retry definitions. Busy claims
cannot be replaced before expiry; after expiry only a new token/revision may take
over, preserving original provider operation key. Tokens retained to prevent ABA.
Wrong token/revision, expired or predating-claim response rejected. Exact recorded
last-response replay is no-op metadata; it never reauthorizes external execution.

Own forward ap_0007 current state/history share inventory scope serialization and
transaction with outbox. Strict JSON codec/row checks bind original envelope hash,
status/revision/deadline/reference. No separate ai_jobs/BE1 writes. History rejects
SQL update/delete; current row key/delete/revision skips guarded by own trigger.
Changing delivery advances inventory revision and invalidates old discovery pages.
No schema-backed pending filter yet: operation_page still enumerates ALL intents.

CopyHookResponse: exact operation key/body digest, outcome pending/unsupported/
exception with symbolic reason OR receipt_available with reference/hash. Strict
delivery_response bridge rejects forged/malformed native output. Reference is
NOT evidence authenticity, fixture/provider classification, verified deletion or
cancel confirmation. Unsupported/receipt states do not automatically redispatch.
Pending/exception retryability is mechanism, not permission/budget for retries.

ProviderCopyOperationHook is an internal protocol ONLY, no implementation/call.
Future dispatch must persist current-authorized claim first, exit DB UoW, recheck
owner eligibility and invoke adopted hook using original envelope/exact profile/
stable idempotency key. Durable claim does not prove provider deduplication or
prevent an already-sent external effect after process crash; hook adoption and
verified reconciliation remain required. Current-rights binding, safe timeout/
error mapping, pending query and typed cancel/purge verification still next.

## Evidence boundary

786 own local +477 selected regression +114 targeted foundation PASS; no skip.
86 actual PG cases prepared/collected NOT_RUN. Actual provider/worker/BE1/P4
integration NOT_RUN; no actual cancellation/deletion/BE1 closure or full-card DONE.
Use C2_SQL_RUNTIME.md only with separately authorized disposable PG17 profile;
no server provision/start or real credentials inferred. No push/merge/deploy.
