# C5c — guarded redacted copy report

Approved P4/P5/AC08/09/11, parent1d4d185. Extend existing inventory service with
report(actor,org,CopyInventoryReadRequest), retaining existing exact data-request
current read authority and scope SHARE transaction through final confirmation.
Operations role alone never grants this data-request scope. Page and load current
copy state within same held scope/revision; bounded <=256 records, no global scan.

Return strict allowlist org/scope/revision/purging, copy id/kind/current revision,
foundation report label/actual-deletion flag, opaque purge receipt ref/hash/kind
and distinct cancel acknowledgment classification. No raw original profiles,
data-request provenance/authority/source lists/proof bytes/reason/provider URL.
Receipt references are metadata, not bearer permission or exposed provider bytes.
Keep fixture_deleted_not_actual and fixture cancel separate from adopted provider
evidence. Overall request deletion always not_established: empty list, terminal
page, stored coverage and cancel acknowledgment never establish all-provider purge.

Coverage status reports stored attestation only, not fresh completeness/expiry or
actual deletion. Continuation keeps exact revision; raw next_after not permission.
Strictly validate source/current registration binding, native booleans, scope,
revision, order/cursor/bounds and stored coverage consistency. No mutation, receipt
verification/network under lock, new SQL schema, shared foundation change or route.
Prepare actual PG empty/reconnect purge-vs-cancel/redaction/no-write cases in batch;
test local classifier/authority/cursor/redaction/late quarantine/stale/malformed.
