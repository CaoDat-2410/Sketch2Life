# FEAT-036 plan revision 4 — Parent login animation

- Revision: 4
- Status: `APPROVED`
- Prepared: 2026-11-09
- Type: bounded Parent login visual update
- Product baseline: FEAT-063 SRS v2.7-draft Rev57 (unsigned), routed by `docs/context/SRS_AUTHORITY.md`
- Prior implementation: approved revision 3 (seven Parent UI fixes); kept as a separate completed batch

## Objective

Apply the owner-provided animated splash artwork to the Parent login presentation while preserving
the active UI color system and the existing login behavior.

## Source and current behavior

- The owner provided `h-y-tri-n-khai-animated.zip` and explicitly requested its use for login while
  retaining the current UI colors. The archive SHA-256 is
  `CEA2152B2E0CF66D1C0D645D4451F2BBD6A2490E909232ABFC83DAF7BBD39AA4`.
- The archive contains a standalone GSAP splash animation, not a login form. Its background and
  pencil artwork will be adapted to the existing React page; the current `Wordmark` will remain so
  the product's blue/amber/mint brand colors stay consistent. The archive's purple/amber logo image
  will not replace the current wordmark.
- Existing email/password fields, validation, auth bridge guard, notices, preview behavior, route,
  and onboarding flow remain authoritative and unchanged.
- Parent Web remains an open target-client question in this feature's SRS review. This request
  authorizes only a visual update to the existing local Parent UI implementation; it does not settle
  that product question.

## Scope

1. Preserve the provided background and pencil PNGs as approved/applied feature assets with source
   hashes and review provenance. Do not execute the archive's Vite project or install GSAP.
2. Replace the static login illustration with an animated hero using those assets and the current
   `Wordmark`, keeping the existing blue UI tokens for controls and text.
3. Keep the hero decorative for assistive technology; make all animation optional under
   `prefers-reduced-motion` and ensure the artwork stays visible in that mode.
4. Keep all authentication, registration, preview, error, routing, and backend behavior unchanged.
5. Store local visual evidence and implementation notes in this feature's evidence directory.

## Out of scope

- Backend or authentication-provider changes, API calls, new credentials, registration behavior,
  onboarding changes, or route changes.
- Recoloring or replacing the product wordmark, changing shared UI tokens, broad login copy/layout
  redesign, other portals, publishing, deployment, or resolving the Parent Web target-client question.
- Running the standalone archive project or adding its GSAP dependency.

## Acceptance criteria

1. The login page shows the supplied animated background and pencil artwork, with the current product
   `Wordmark` and existing blue controls.
2. Email/password required states, disabled auth-bridge state, plain-language backend notice, and
   local preview action behave as before.
3. Decorative assets are hidden from screen readers; reduced-motion mode shows a stable visible
   hero without entrance or looping animations.
4. The 430×932 login preview and a compact mobile viewport fit without clipping or horizontal
   overflow; the user can still reach both fields, the primary action, and the existing notice.
5. The preview is captured as feature-local evidence. Automated tests/builds are not part of this
   bounded task; do not change other approved revision-3 UI work.

## Implementation and review sequence

1. Record this owner request as the approval for revision 4 and record the source-asset review.
2. Copy only the selected source artwork into the feature's approved/applied asset directories and
   add its manifest.
3. Implement the hero within the existing login page and current design tokens.
4. Inspect the login preview at the agreed viewports, capture evidence, and update context,
   decisions, status, and the implementation note.

## Risks and limits

- The owner-supplied images are larger than the existing login illustration; verify the final layout
  and avoid loading unused archive assets.
- The SRS describes Parent Android; this narrow change does not establish Parent Web as a supported
  target client.
