# Approved P3 reintroduction correction — 2026-10-17

Parent 96934b1; branch feature/be2-12-content-publication. Executor self-review.
Authority: reviewed plan revision 1/P3 (unchanged hash
b7406837014f5d855e766ba0f0ba15a588c193f8df1fd977b4c9879ff6b77faf),
actual owner approval includes P1–P4. This corrects a prior over-restriction;
no new capability, restore action or other-owner business implementation.

## Change and invariants

Domain edit always produces a different/new version; rejecting a retired head
also prevented approved reintroduction. Remove that blanket rejection, retain
AUTHOR/current record CAS and next-version checks. Application still limits edit
to current head and enforces current source/policy/usage. Fresh draft clears
review/context/publication/recall metadata. The old terminal version is not saved
or changed; exact old resolution and original publication receipt stay denied.
See artifacts/REINTRODUCTION_RULE.md for full semantics and API consumer sequence.

Earlier domain/component assertions prohibiting new draft creation from retired
head encoded the implementation error, not the approved requirement. Updated
them to prove old version cannot submit again, next_version cannot equal old,
old metadata persists and fresh version has no approvals. Four additional
component cases prove revoked author, unsafe source, denied policy and stale
record still deny new creation; no event/version leak on denial.

## Actual verification

- Initial focused domain/command run: 92 PASS. Style line-length finding fixed.
- Selected content/history/HTTP/foundation suite: **354 PASS / 0 skip, 6.03s**;
  four new negative cases plus corrected existing terminal-version tests.
- Focused Ruff and Mypy changed production domain source: PASS.
- Real PostgreSQL 17.11 consolidated runtime: C2 **9 PASS, 8.75s**; projection
  **1 PASS, 1.42s**; command/history expanded **13 PASS, 11.20s**, no skip.
- Two new SQL cases parameterized recall/archive exercise v1 publication,
  retirement, idempotent new v2 draft, denial before fresh reviews, explicit old
  approval rejection, new exact reviews/publish, v2 default resolution, old exact
  ref/old publication receipt denial, unchanged old state/hash/reason/reviews.
- Existing Alembic path_separator warnings: 11 + 1 + 13, recorded, not hidden.
- Runner source hashes unchanged before/after; scope still ASSUMED owner ports,
  not real BE1/review/source fencing. No live HTTP/owner integration PASS claimed.

Raw ignored receipts:

- .runtime/learning-content-c2/20261017-071313-172712/
- .runtime/learning-content-c3b/20261017-071329-310783/
- .runtime/local-pg-c2/lc-pg-d4ba8d60632a4deda32f0fafdfaf6a2b/

Pinned changed runtime source hashes:

- domain/learning_content/model.py:
  2be0f6b03b4a383aa4dc8f5ba03fba471ab657b2cb0fe395e4fc636f32a667d5
- integration/learning_content/test_commands_sql.py:
  eb66123b8d009adb76f2f7b151562e4df169961fb472b08a91ed66933b5daa62
- feature src/run_c3_commands_sql.py:
  dfdd9d7595c496d6b8d24fce472b0eaa34a95701c41bdc04ad0f69837d6f4238

## Cleanup and remaining gates

Official portable ZIP hash matched prior approved runtime. Cluster bound only
127.0.0.1:53171; random private credentials, disposable synthetic DBs. Graceful
stop and UUID runtime cleanup succeeded; direct checks found exact directory
absent and port not listening. Cluster/passwords/binaries/archive removed;
private logs retained. No unrelated material deleted; no system service/model/
GPU/package install, push/merge/deployment.

Local P3/F05 subfinding corrected. F01 closed delegate contracts/dispatcher,
F02 actual owner authority/source/review adapters, F04 consumers/notification
adoption and F05 source-pinned integrated closure remain incomplete. Source
inventory again found no owner schemas/delegate/boundary implementation in the
current backend. No full-card completion or fabricated owner sign-off.
