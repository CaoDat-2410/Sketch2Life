# BE2-14 C3b application / effective-pin handoff

AiPolicyCommands.execute(principal_id, organization_id, AiPolicyCommand,
expected_revision=...) implements all eight actions and returns existing typed
DelegateResult. Identity is supplied by trusted composition, never body role claims.
Current PolicyCommandBoundary supplies registry rights, review governance version
and review_effective for existing AND newly proposed local proofs. Unknown/revoked
decisions must fail closed. No production boundary/default adapter is supplied.

Lock order: entered owner/registry guard -> exact own feature scope -> own record.
One store transaction covers lifecycle/review/event/outbox/effective-scope transition/
receipt. Publish updates one org/feature pin and epoch; recall/archive disables
only that exact active pin. An older version/record retirement must not disable a
replacement. Published historical versions/requests are not silently rewritten.
Edit cannot move a record to another feature; new scope needs a separate record.

No default application route mounted. Positive tests bind the real handler through
existing StrictDelegateBinding; C5 still must translate the closed AI_POLICY error
catalogue into safe public HTTP outcomes and complete authorized composition.
Do not let PolicyError become a raw exception body or borrow content permissions.

## Replay / failure

Key is org/principal/client_request_id; fingerprint includes full validated command
and record precondition. Same key/different body conflicts. Replays recheck current
rights/definitions/proof effectiveness; publication replay cannot re-enable retired
or disabled content. Receipt carries recorded metadata plus current revision/state,
not an activation/usage grant. Integrity conflict rolls back whole candidate, then
at most one fresh receipt read; no blind write retry. Nonexistent winner still fails.

Negative review and retirement remain available when a definition is withdrawn.
Create/edit/submit/positive-review/publication require exact adopted definitions.
Unknown target/version/hash, self-review/publish or stale record/review are denied.

## Scope transition intent, not a cancellation receipt

Forward migration ap_0002 adds effective_scope + scope_transition. Scope event
stores org/feature/epoch/exact record/version/hash/disabled/reason and is immutable
except delivery marker. Pending intent does not prove worker/provider stopped.
It does not authorize a wildcard cancellation of a newer pin: later delivery must
revalidate epoch/exact target and preserve source history. Foundation cancellation
adapter mapping and bounded operations policy remain to implement/adopt.

Epoch0/null pin is unusable even with disabled=false. Runtime code must never treat
that boolean alone, a validation receipt or a cached event as permission to run AI.
Emergency kill before publication, atomic budget/concurrency reservations and actual
current-work eligibility are still C3c, not a fabricated CMD-48 ninth action here.

## Verification status

252 own component cases PASS +477 existing selected regression PASS. New C3b uses
assumed boundary and transactional MEMORY store; not durable SQL/fence proof.
Actual PostgreSQL 15 lifecycle +4 activation cases are prepared/collected, NOT_RUN.
Runtime command pack: artifacts/C2_SQL_RUNTIME.md. No real provider/owner integration,
cost/load/purge/cancellation proof. Full-card BE2-14 remains IN_PROGRESS.
