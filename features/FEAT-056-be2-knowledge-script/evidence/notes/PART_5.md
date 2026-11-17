# Part 5 — application commands, read and receipt mini-plan

A before source: root owns application/services/knowledge_bundle.py and focused service
tests. Dependencies are pure rules/strict DTOs/typed ports from1–4 and reviewed atomic6.
Separate create/edit command envelopes accept verified Principal, key, If-Match and strict
body. No HTTP route. Results use201 create/200 edit candidate API-CS-01 convention.

Parse bounded semantic body first; authorize current Teacher/read disclosure and scope;
look up scoped receipt (org, authenticated principal, contract, server target, key), check
semantic fingerprint and replay original immutable status/body. Exclude transient headers.
Unseen mutation checks current lifecycle/policy, exact trusted basis/audience/context refs,
per-contributor membership/purpose consent, exact reviewed source pins, and edit family ETag.
Create If-Match is forbidden; edit absent428/wrong412; body conflict409. Errors are typed
and safe for foreign/nonexistent resources. All guards/receipt/CAS/staged writes stay in6.

Create missing eligible catalog source gives immutable draft with exactly0claims,
NO_ELIGIBLE_SOURCE; no job/provider path exists. Teacher claim correction is server-attested
with exact source/reason/principal and OD03 fixture policy; no semantic truth claim.
Edit same content returns NO_CONTENT_CHANGE and no CAS/version/correction/receipt/audit/event.
Basis/audience pins remain fixed; new context needs a new bundle.

Nested conflict: after rollback and queued-publication drain, reread accepted winner receipt
in fresh coordinated unit and reauthorize current disclosure. Different-key loser conflicts;
same-key winner replays original without duplicate effects. Storage errors produce no success
receipt; retry is safe. Lost acknowledgement is ambiguous transport only; committed receipt
recovers original result and exact outbox identity.

Tests use real service and coordinated fixture ports: roles/foreign scope/safe existence,
generic zero consent calls, exact child contributors, source recall and all guard families,
fresh key versus accepted replay after head advance/pause/stale If-Match, withdrawn disclosure,
preconditions/conflict/no-op, fail-stage retry and nested/lost-ack races. Assert full state,
exact denied script absence, counts and original response values. Focused pytest/log/JUnit,
Ruff/strict mypy, independent atomic_review actual code review, fixes and regressions.

B/C NOT_RUN. Runtime authority/catalog/SQL/HTTP/delivery remain deferred.

## B checkpoint — 2026-10-20

All five completed own07 test modules pass:175 passed,0skipped. They exercise actual
create/edit/read/resolve, same/different nested keys, post-rollback replay disclosure,
lost acknowledgements, all staged failures, two concurrent edits,15guard families before
unit and in queued commit windows, rollback drains and real other-thread contention.
Ruff, normal/fresh-cache strict mypy,572backend/all-other-tracked invariants pass.
Snapshot: `5cb9c85e07eebc8ae0cd8825242a8176849b89dac1ea7eb9a81d874d2f1890f3`.
Raw receipt: local/part5-full-focused-retest; final independent C5 re-review pending.

One development expectation incorrectly required a Teacher-attested correction to depend
on later catalog-claim wording. OD03 requires its reviewed exact source and accountable
Teacher attestation; it does not require catalog text equality for attested content. The
catalog-change queued invalidation test now retains catalog-reviewed claims, and a separate
positive test asserts attested authorship/source readiness across catalog wording change.
The original1fail/102pass receipt is preserved at local/part5-handlers-races-initial.

An added whitespace-reason test initially constructed an invalid strict DTO before calling
the service. Changed its input to raw JSON to exercise the actual parser and typed400;
removed duplicate service validation already guaranteed by the strict boundary. Original
174pass/1fail receipt remains local/part5-full-focused. No assertion was removed to hide a
product failure. Supplemental independent mutants already caught skipped replay disclosure
and incorrectly applying fresh current guards to accepted historical receipts.

C5 closed by independent atomic_review after rerunning all175cases with0skips and stable
before/after hashes. Verdict PASS_WITH_OFFLINE_LIMITS, no concrete known P1/P2. Integrated
Rxx assertions and both replay mutants were independently inspected/executed. Final8 retains
explicit mixed-coordinator construction denial, other-session access, no-job/provider hooks,
C04 and final-batch/hash/map obligations; current C5 proof does not replace them.
