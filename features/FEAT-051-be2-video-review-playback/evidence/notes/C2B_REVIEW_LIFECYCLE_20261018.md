# E04 — guarded own review invalidation/version rebind

2026-10-18 Asia/Saigon; parent01b4be9, feature/be2-08-14. Owner "duyệt" continues
remaining internally approved revision1 work; frozen plan unchanged SHA256
eca121bb1ce17943936bb68cbbbce62777f6a3867c5ef4cf70594ba9838d82e7.

## Delivered / semantics

- Pure ReviewChangeRequest/Action/ReviewChange and changed_heads. Internal exact
  owner notice only, NOT a public client-side permission/invalidation endpoint.
- Invalidate preserves original review entry, makes stale/revoked head. A later
  revocation strengthens stale->revoked, never downgrades revoked to stale/effective.
  Different duplicate operations do not silently reset state; compatible same-key
  replay recovers original event without applying another transition.
- Rebind same org/session/video to current ready target archives previous exact
  head/entry and opens EMPTY current head, canonical revision+1. No approval copy,
  no restart at revision1, no08 job/run/row mutation. Old head remains history.
  Reject backward video/context/audience revisions and changed artifact under same
  content version; context/audience changes with same bytes still need fresh review.
- Exact content can regain eligibility under actual current owner guards after
  revocation/staleness: rebind to same subject preserves invalidated archive and
  opens NEW EMPTY head, never restores historical approval. New Teacher review
  required. Merely rebinding unchanged effective head rejected.
- Opaque pin digest includes policy epochs, not just script/media. Explicit source
  CONTENT_CHANGED notice requires appropriate new content version; CONTEXT_CHANGED
  may refer to verified policy/pin change without inventing a render/version bump.
  Actual source owner must authenticate notice cause/lineage; hash comparison
  alone is neither proof of script edit nor permission to relabel an edit as policy.
- Candidate ReviewLifecycleBoundary/Access/Store/Transaction and receipt ports.
  Actual current source/policy/session authority and eligibility of new target,
  especially reopen after revoke, must be held through commit. No default adopter.
- VideoReviewLifecycleService resolves current canonical head, checks notice/scope/
  CAS, uses one own transaction for head/archive/history/actor-key-body receipt+
  audit/outbox. Late denial rolls back fixture UoW. Missing/mismatched local head
  fails closed, not imported from external history. Initial empty bootstrap remains
  explicit review-write owner flow from E03, never guessed08 revision.
- Original change receipt queried before current-head resolution on replay; exact
  original key/body reauthorized, no duplicate change or resetting newer review.
  Result event ID/applied revision is HISTORICAL, not live approval/access state.
- Review-write and lifecycle key namespaces must conflict across operation kinds;
  actual P3 store must enforce this at unique key/CAS boundary, not only precheck.
  Lost commit/guard-exit ACK ->closed unavailable, recover original receipt later;
  no rollback claim or automatic external dispatch.

## Actual integration still OPEN

CR09-01 canonical head/projection/source-owner event adoption and CR09-02 actual
BE1 access/dispatch/fetch/range/resume revocation fence remain OPEN. Outbox alone
does NOT prevent late fetch or prove a player stopped. Actual change UoW must
coordinate current dispatch/access fences; synthetic old-playback rejection does
not prove those real races. Rebind is not implementing07 script editing/08 rendering.

P2 lifecycle component now available; P3 durable schemas/codecs/adapters/migrations/
HTTP and P4 consolidated audit/verification still next. No production source-owner
binding/default auth/route, SQL environment, provider/GPU/Lightning effect or shared
05/08/BE1/foundation schema/migration edits. Full09 IN_PROGRESS, not DONE.

## Verification

- 60 new tests/unit/test_video_review_lifecycle.py, cumulative249 own=189+60;
  explicit MEMORY/ASSUMED owner guards and synthetic review/playback fixtures.
- Cases:4 invalidation causes, stale->revoke, historical archive/new empty head,
  version/scope/notice/CAS/native invalidity, new-target current authority denial,
  rollback/late revoke/head mismatch, changed-key-body conflict/shared namespace,
  lost committed ACK/guard-exit recovery, duplicate after newer review, rebind->
  actual own review service, old review cannot call synthetic playback bridge,
  same-content restore still fresh-review-only and policy-epoch pin distinction.
- Initial collection hit pytest reserved parameter name request; renamed fixture
  parameter, no skipped tests.48 then55 focused cases passed. Final semantics
  review added safe same-content reopen/policy-pin distinction; one old negative
  fixture incorrectly treated changed pin as proof no context change, corrected
  fixture to unchanged pin/context. Final60 PASS; no test suppression/source auth
  bypass. Earlier55-case broad2138 receipt retained separately at C2b-20261018.
- Final58-suite regression2143 PASS,0 failures/errors/skips,13.832s, exit0:
  249 own +1894 prior08/policy/content/foundation cases, not actual09 integration.
  Existing backend venv pytest -q --disable-warnings --tb=short --junitxml=...
  on unit/contract prefixes ai_policy_/learning_content_/knowledge_video_/
  video_review_/video_playback plus3 existing foundation suites.
- Ignored final JUnit `.runtime/video-review/C2b-final-20261018/regression.xml`,
  SHA256cc7025781173096b85af09312629101cb90f42ecbfe889d82d2e6fce9b92ec35.
- 662 backend inventory files re-enumerated exact names/hashes before/after,
  unchanged=True. Sorted unique rg --files src tests alembic -g '*.py' plus
  pyproject.toml/alembic.ini; aggregate SHA256 UTF8 newline-joined sorted Windows
  relative path=UPPERCASE_FILE_SHA256:
  f2d0900e702ef76c768c6e9cfeff4862b6b56d49aeac1c385d3ee616e8796533.
- Ruff11 owned source modules/five own suites PASS; Mypy11 sources with
  --follow-imports=silent PASS. Architecture/harness/diff PASS, security before
  commit. Grouped documentation updated after tests, outside backend inventory.
