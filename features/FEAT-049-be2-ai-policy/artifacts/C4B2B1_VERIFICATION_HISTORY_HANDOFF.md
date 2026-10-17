# C4b2b1 — durable inventory verification history

Parent c3710e8, branch feature/be2-08-14; approved P4/P5, 2026-10-18.

ProviderCopyInventoryService now writes CopyInventoryEvidence through the SAME
ProviderCopyRegistryTransaction used for register/coverage/fence. Custom store
implementations must implement record_evidence and roll it back with inventory
if confirmation, evidence insert or transaction commit fails. No optional/no-op
fallback. Production owner/source boundary remains unbound, no permissive default.

Own forward ap_0005 creates copy_inventory_evidence with scope FK and immutable
history trigger. Each successful observation includes actor/org/context/exact
command digest, authority grant and timestamp; registration/source includes the
original exact profile and reference/hash, coverage includes explicit observation.
Source proof deadlines/verification and authority identity are strictly checked;
SQL writer recomputes exact canonical command binding and enforces transaction
actor/scope. Internal decode also checks column/payload consistency and digest.
No raw receipt bytes, credential/provider URL or child-media fields are stored.

Exact registration/fence retry revalidates rights/source and appends fresh history
with a distinct evidence ID, but does not duplicate inventory mutation/events or
advance registry revision. Read calls remain non-mutating. History is not a
current grant, provider-wide completeness proof, execution intent, acknowledgment
or deletion evidence. Do not dispatch from these records. No public route added.

Component645/477 selected regression/114 targeted foundation PASS; fixtures are
ASSUMED/MEMORY, offline SQL/DDL only. PG70 prepared NOT_RUN. Use the source-pinned
four-pack commands, prerequisites, impacts and log return in C2_SQL_RUNTIME.md
only on a separately authorized disposable PG17 profile; do not infer install/
server permission or run a production downgrade. No real provider side effect.

Next: exact cancel/purge operation envelopes/intents with recovery and operation
authority evidence, then typed missing-hook dispatch/ack/current lifecycle/verified
receipt application, C5 safe bindings/projections and consolidated acceptance.
Cross-owner CR/adoption and real BE1/P4/provider integration remain separate.
