# FEAT-081 — Plan Revision 51E: Restore OpenMoji license source integrity

**Status:** APPROVED under the owner's direct 2026-11-21 instruction to inspect and fix backend defects.
**Authority:** FEAT-063 v2.7-draft, Rev71 local amendment, unsigned.
**Parent task:** Addenda 84–85, Parent SVG guide backend and catalog recovery.

## Finding

The OpenMoji turtle asset resolves after adding exact sea-turtle aliases, but the backend rejects the pack before rendering because its local CC BY-SA 4.0 legal-code text is one trailing LF short of the official plain-text source. The existing expected SHA-256 matches the official source exactly. This is a source-integrity issue, not an SVG/model problem.

## Authorized change

1. Restore the missing final LF to the local CC BY-SA legal-code text. Do not replace, reformat, or otherwise edit its contents.
2. Keep the existing license SHA-256 pins unchanged and verify the restored local bytes match the pinned official hash.
3. Run the focused SVG catalog resolution/API tests and resume the same real Parent flow.

## Allowed files and limits

- Allowed: `backend/src/sketch2life/infrastructure/svg/data/openmoji/CC-BY-SA-4.0-legalcode.txt`, the OpenMoji alias manifest/loader and focused tests already listed in Plan 51D, plus FEAT-081 plan/approval/context/status/evidence.
- Do not change source SVG geometry, attribution, license metadata, expected hash, other datasets or assets. No migration, seed/account mutation, quota/payment, secret/.env/SRS edit, Modal call, commit or push. All Addenda 81/84/85 limits remain.
