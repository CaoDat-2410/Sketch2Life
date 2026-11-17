# F03 — immutable originals and derived review-history state

Date: 2026-10-17; branch feature/be2-12-content-publication; parent 531ef21.
Scope: approved P2/P3 history/provenance and audit F03 local omission. Not a new
business card, shared review standard or production owner integration.

## Implemented and reviewed

ContentReviewHistory.read checks verified scope/current READ under outer owner
guard, holds SQL parent SHARE through commit and enumerates all contexts of an
explicit version. Typed immutable page/entry returns original ReviewProof and
separate derived state/stale reason. No body/source/media, receipts or writes.
Pagination limits query size, enforces ordered distinct review revisions and
requires global record snapshot revision on continuation; changes force reload.

Reasons cover resubmitted context, replaced dimension, superseded unpublished
version, policy/audience changes, retired version and current owner ineffectiveness.
Old published v1 remains eligible for an effective review despite new draft v2.
Original decision/reason/state is never rewritten. Current owner boolean cannot
give exact revocation cause; explicitly owner_ineffective, not a fabricated cause.
History READ is not new-session usage eligibility and does not require an unsafe
source to become usable merely to audit its prior reviews. No new HTTP route,
shared DATA-24 change, frozen migration edit or foreign DB access.

## Actual local evidence

unit/test_learning_content_history.py: 24 new component cases PASS. Existing
selected content/HTTP/foundation suite plus new file: **350 PASS / 0 skip, 4.72s**
(240 content + 110 foundation). Cases cover snapshot pagination, original retention,
resubmit, replacement, published/unpublished edit, recall/archive readability,
current owner policy/effectiveness/READ withdrawal, invalid query/corrupt scope,
no receipt/event/content side effects. Assumed fixtures are not SQL proof.

Focused Ruff over changed source/tests/runner PASS; strict Mypy three changed
source files PASS; architecture/harness/security/whitespace PASS before commit.
First test run 18 PASS; initial import/line-length and SQL annotation/Literal
narrowing findings fixed before final checks. No functional runtime failure was
relabelled. No claimed independent owner review; this is executor self-review.

## Actual consolidated PostgreSQL run

Owner-approved portable PostgreSQL 17.11, official archive SHA256 unchanged:

- C2 inventory: 9 PASS / no skip, 6.55s.
- Projection: 1 PASS / no skip, 1.09s.
- Expanded command/history inventory: 11 PASS / no skip, 9.29s.
- Before/after source hash pinning includes new history source; unchanged true.
- Existing Alembic path_separator warnings: 11 + 1 + 11, not hidden.

Three added SQL cases prove prior-context/proof history across resubmit, changed
snapshot rejection, exact cross-org filtering, old proof JSON byte-value equality,
published vs unpublished version edits, and recall projection without original
approval mutation. History connection/repository reconstruction is not a new
independent-process claim; existing C2 separately proves child-process reads.

Raw ignored receipts:

- .runtime/learning-content-c2/20261017-070805-747899/
- .runtime/learning-content-c3b/20261017-070818-539080/
- .runtime/local-pg-c2/lc-pg-49bf135719084681989e162596a6ecd4/

Server was stopped gracefully, exact UUID directory removed including binaries,
ZIP, cluster and random private password files. Read-only checks: directory absent,
port 56632 not listening. Private logs and sanitized metrics retained; runtime
can only be recreated via setup. No unrelated material removed, no system service,
package/GPU/model install, push/merge or deployment.

## Closure scope

F03 CLOSED_COMPONENT_AND_OWNED_SQL only. Real owner authority/revocation reason
and fencing/adoption still F02; full dispatcher F01, consumers F04 and integrated
closure/reintroduction review F05 remain. Whole goal remains incomplete. Previous
historical C3b 8-case receipts remain untouched; current runner explicitly expects
11 and new source hashes rather than claiming old receipts cover these edits.
