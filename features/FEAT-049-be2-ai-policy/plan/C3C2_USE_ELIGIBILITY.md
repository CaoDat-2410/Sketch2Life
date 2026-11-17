# C3c2 — exact request pin and current policy-use lease

Approved P2/P3: initial request pins exact effective policy/profile; later phases
keep that provenance, never silently substitute new versions. Every check holds
verified current-use/review/registry guard -> own feature SHARE -> own record SHARE
through consumer's nested guarded work/commit. A returned snapshot outside the
context is metadata only, not cached permission or cross-owner atomicity proof.

Typed request includes request id/revision/input hash/purpose/feature and explicit
profile ref (no auto provider/profile choice). Initial lease requires published
effective scope pin; continuation requires exact original request/policy/profile.
Current use owner decides identity/phase/source/consent/session/review/request
terminal validity for proposed or existing request; echo scope and canonical exact
binding digest checked independently. Role/Admin/author does not imply usage.
Missing real authorizer is fail closed; no production adapter is supplied.

Reject epoch0/null/disabled scope, missing/retired/tampered policy, invalid exact
publication proofs/governance, revoked/incompatible registry/profile and wrong
request/phase/scope decisions. All new uses of same pin are checked again.
Prior pin can survive ordinary policy replacement ONLY while its exact old version
is published, definitions/reviews/owner decisions still effective and no stop has
occurred after pin. Query immutable scope-transition history under scope lock;
the exact origin epoch must match an immutable activation of that same policy
version/hash, so modifying a pin's epoch cannot skip intervening stop history.
any intervening disabled epoch permanently invalidates that old pin even after
reviewed reactivation. No reanimation of terminal requests or silent repin.

No new schema/migration, job/session writes or gateway. Atomic budget/reservation,
transport/provider effect and cross-owner composition still separate required work.
Tests must distinguish MEMORY/assumed guard proof from actual PG locking and
durable kill-history proof; prepare PG cases without starting an unapproved server.
