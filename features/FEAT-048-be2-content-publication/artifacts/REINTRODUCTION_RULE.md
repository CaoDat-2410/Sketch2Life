# Retired-version reintroduction — approved P3, not restoration

Authority: unchanged plan revision 1/P3, approved explicitly with P1–P4. It says
retired versions are terminal and reintroduction creates a new version with fresh
review. Earlier code rejected all edits from a retired head, preventing the
already-approved new-version flow. This is a correction to that implementation,
not a new restore capability, permission, owner contract or business policy.

## Exact behavior

- Author with current independent AUTHOR capability may edit the exact current
  head version using current record If-Match and matching target version/hash.
- Edit always authors head+1 as a new draft, even when the prior head is recalled
  or archived. Old version bytes/state/reviews/recall metadata are untouched.
- New version gets its own authored_by/time, empty review/publication set, zero
  context/review revisions and no recall metadata. Identical content bytes may
  keep the same payload hash, but target_version is different: old reviews cannot
  authorize the new version, even with the same hash.
- Current policy/source/usage guards still apply to the new draft. This does not
  let an author bypass an unsafe source or a revoked capability.
- New draft cannot publish directly. Submit creates a fresh context; independent
  safety and pedagogical reviews must bind the new exact version/context/audience/
  policy. Publisher capability remains separate and author cannot self-publish.
- Exact requests for old retired version still fail resolution; default never
  resolves the new draft. Once new version is legitimately published, default
  may select it, but old publication receipt remains ineffective.
- Retire/archive/submit/publish do not transition the old terminal version back
  to active. After a new head exists, a new edit command aimed at old head is
  superseded; replay of an original retirement remains a history receipt only.
- No new action/route/migration/schema or direct owner-table write is introduced.

## Evidence scope

Pure domain tests now distinguish immutable terminal version from new-version
creation instead of locking in the earlier overly restrictive behavior. Component
tests verify current authority/source/policy/stale-record denial still applies.
Two parameterized SQL cases (recall/archive) test full fresh re-review/publication,
old-ref/old-receipt denial, exact-version resolution and immutable retired history.
Owner ports remain assumed in these SQL cases; true owner integration is still
F02 and integrated closure remains F05.
