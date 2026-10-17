# Feature decisions

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
