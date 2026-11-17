# C5b — safe scoped policy/resource operations query

Approved P2/P5/AC11, parentf00f515. Internal application query only, no new HTTP
endpoint/dashboard/default activation. Current OPERATIONS_READ capability under
held registry/identity guard before any storage access; recheck before response.
Read existing own effective scope/immutable policy metadata and optional own ledger
reader, never job/BE1 tables. Registry withdrawal must not hide stopped metadata
from an authorized operator; metadata is not current use authorization.

Closed strict projection: org/feature, observed activation epoch/state/exact pin/
stored policy state, global occupied ledger slots, optionally exact requested
budget definition/unit/window with recorded held/spent counters. No raw policy
body/title/author/reason/review/proof/source/request/attempt/prompt/media/URL/token.
Exact historical window is caller query filter, never limits/authorization/current
definition adoption. Counters may include fixtures: explicitly ledger-recorded,
not actual provider usage/cost. Actual monetary cost unavailable/null, never0.
Absent reader/row/window remains unavailable/null; actual stored zero remains0.

New readonly SQL ledger reader uses existing tables, no migration or INSERT:
scope SHARE then exact scoped bucket SHARE; check original key/hash binding and
native counters. Missing scope returns immediately, no mixed later phantom bucket.
Metadata read consistency is local snapshot only, not distributed atomic exposure
grant or provider evidence. Wrong binding/malformed data fails closed, private
dependency errors sanitized. No broad catch turning denial/corruption into zero.

Test schema/redaction/absence/zero/binding/current rights/dependency/readonly shape;
prepare two actual PG cases for absence-no-write and stored fixture counters/scope
isolation. Existing batch runner inventory must change explicitly; PG NOT_RUN.
