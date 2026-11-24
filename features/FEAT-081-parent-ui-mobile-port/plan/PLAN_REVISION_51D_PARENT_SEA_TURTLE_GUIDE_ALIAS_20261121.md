# FEAT-081 — Plan Revision 51D: Resolve the Parent sea-turtle SVG guide alias

**Status:** APPROVED by the owner's direct 2026-11-21 instruction to check and fix backend defects as well as frontend behavior.
**Authority:** FEAT-063 v2.7-draft, Rev71 local amendment, unsigned.
**Parent task:** Addendum 84 / Plan Revision 51C.

## Finding

The chosen Parent subject was “Rùa biển” (entered without diacritics in the synthetic UI run). The local OpenMoji source pack already contains a turtle illustration, but backend lookup normalizes accents and then requires an exact alias. Its manifest only lists generic turtle aliases, so “rùa biển” misses despite being the intended animal. The route then correctly returns its no-source 404. This is a catalog taxonomy gap in backend, not a missing route or Modal timeout.

## Authorized change

1. Add explicit Vietnamese/English sea-turtle aliases to the existing OpenMoji turtle asset metadata, preserving exact-match lookup and avoiding broad substring matches.
2. Update the pinned manifest SHA-256 so provenance and integrity verification remain fail-closed.
3. Add deterministic backend unit tests: “Rùa biển”, “Con rùa biển”, and unaccented “Rua Bien” resolve to the existing turtle asset; unrelated labels such as “sao biển” do not resolve to a turtle.
4. Verify the actual authenticated Parent route returns the curated SVG draft for the supported subject and that the returned draft meets the existing 4–8 stage and provenance contract. No AI/Modal request is needed for this catalog hit.
5. Resume the same real UI flow after the guide result; no duplicate account/profile/run.

## Limits and files

- Allowed: `backend/src/sketch2life/infrastructure/svg/openmoji_guide.py`, its `data/openmoji/parent-guide-manifest.json`, new focused test `backend/tests/unit/test_parent_svg_guide_resolution.py`, and FEAT-081 plan/approval/context/status/evidence.
- This is an alias-only mapping change. Do not alter SVG path data, licensing/source files, quality gates, guide stages, Modal workloads, other catalog assets, database schema or API payload.
- No seed/account mutation, migration/reseed, quota/payment, secret/.env/SRS changes, unrelated API edits, commit or push. Addendum 81 limits remain in force.
