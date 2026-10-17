# C1 — policy contract / invariant matrix

Approved revision 1/P1–P5; C1 implements shape and pure lifecycle, NOT activation,
registry compatibility, atomic budgets, kill/cancellation or real owner fencing.

Eight CMD-48 actions share existing policy/ai routing and scoped request key.
Create requires body only; edit requires exact target + body; submit requires
exact target; record_review requires exact target + typed AI-policy review;
request_changes additionally requires nonblank reason and negative review;
publish requires exact target + distinct safety/pedagogical review-set refs;
recall/archive require exact target + nonblank reason. Unknown/irrelevant fields
(including explicit null) fail before effects. If-Match remains transport/service
precondition, not a payload authority assertion. No target learning_content alias.

Body: title, one feature_scope registry code, unique exact model profile refs,
exact moderation/retry/budget/concurrency refs and four required-true safety gates.
IDs/versions/hashes are existing shared primitives; strict refs do not prove
registry adoption/compatibility or authorization. Limits remain approved refs,
not arbitrary numeric values. No token/endpoint/optional settings dictionary.

Review: AI-policy exact record/version/hash, submission context revision,
dimension/decision, named review CAS, reason for negative, governance-policy
version. Server supplies reviewer and proof ID; client cannot assert effective.
Pure publish additionally requires matching context and current governance policy,
both dimensions/distinct IDs and independent publisher; runtime service must
revalidate real proof effectiveness/definitions/current policy through commit.

Domain own immutable versions/review proofs/state/capabilities, stdlib only.
Domain does not parse raw untrusted JSON: application supplies validated canonical
body; hashes cover sorted UTF-8 canonical JSON, no NaN/Unicode normalization.
Edit always new version/head+1/fresh reviews, including after retired head;
old version never restored. Request_changes invalidates both pending approvals;
resubmit advances context/review revision. Recall only published; archive any
nonterminal; all retirements keep originals/review evidence.

Existing StrictDelegateBinding validates the concrete BaseModel before handler;
no foundation/shared schema changes needed for C1. Policy review is owned here,
not a changed DATA-24 enum. Future handler must own CAS/idempotency/history/SQL
guards and must not infer real review proof from a fixture or routing success.
