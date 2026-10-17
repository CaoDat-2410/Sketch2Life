# C3a — server-side definition compatibility validation

Approved P2 requires more than well-formed reference strings. Implement an
application validator using an injected authoritative registry boundary: enter
verifies principal/org, holds current author authority and registry adoption/
compatibility stable through the call. No permissive production registry supplied.

For feature_scope and each exact profile/moderation/retry/budget/concurrency ref,
registry resolves only currently adopted, compatible definitions for exact org,
feature, role, id/version/hash. Resolver validates actual approved values, provider
profile status, mandatory safety ceiling and foundation compatibility internally;
it must not return an entry for unknown/revoked/incompatible/expired definitions.
No client-supplied adopted flag, arbitrary settings or numeric defaults. Immutable
binding receipt identifies registry revision, no raw config/secret/provider URL.

Validator independently checks returned organization/feature/role/reference and
snapshot revision; missing/mismatched results deny. Revalidate typed body even if
constructed through model_copy/construct. Missing boundary/registry operations
fail safely, not legacy fallback. Local check requires author capability; monitor
capability alone does not grant write validation. Results are observations, NOT
activation/usage authorization. Future command/publish/reservation service must
hold the same guard through its SQL commit, not trust an earlier validation.

Test positive complete binding, every role missing/mismatched/revoked, wrong
feature/scope/revision, malicious typed instances, errors without sensitive text,
current auth withdrawal and changed registry across repeated calls. Fixtures are
explicitly assumed current registry, not actual adoption or durable fencing proof.
Effective pointer/kill/accounting and actual authority adapter remain later C3 work.
