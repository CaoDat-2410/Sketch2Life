# C3b — lifecycle commands and atomic effective pin

Approved P1/P2/P5. Eight real application command handlers use current verified
registry/review guard through SQL commit, record/review CAS, scoped fingerprinted
receipts and current-authority replay. Create/edit/submit/positive-review/publish
require current exact adopted definitions. Negative review and retirement must
remain possible when a definition is withdrawn. Feature scope cannot change on
edit; that would require a different record and independently reviewed activation.

Publish atomically changes lifecycle AND one effective org/feature pin. A new
policy does not rewrite an old request pin or historical published version.
Recall/archive of the active exact pin disables it and emits a durable scope
cancellation/revalidation intent in that same transaction. Retiring a nonactive
version must not disable another effective pin. No synchronous cancellation or
provider completion claimed. Emergency pre-publication kill and budget/accounting
remain C3c work, not an invented ninth CMD-48 action.

Lock order: external current-access guard -> own org/feature scope UPDATE -> own
record UPDATE. Initial target-feature lookup is non-locking, followed by exact
revalidation after locks. Recheck receipt after scope lock. Conflicting receipt
insertion rolls back whole candidate, then at most one fresh winner-read, never
blind write retry. Replay returns recorded result with current revision/state,
does not republish/re-enable; stale review/publish receipts fail closed.

Add forward migration ap_0002 for separate activation metadata (scope + scoped
append-only transition/outbox intent). No old migration changed. Epoch increments
on effective publish/disable only; scope row lazily initialized epoch0. Logical
pin checked against own version under locked command transaction, no foreign
owner FK/write. Separate metadata preserves frozen lifecycle DDL identity.

C2 pack pins ap_0001 explicitly; C3 activation SQL pack upgrades current head.
Both need authorized actual PG profile before any runtime PASS. Memory store and
assumed registry/review guard tests are component-only. C5 supplies public error
translation/HTTP binding; no default app mount or real owner implementation here.
