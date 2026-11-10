# FEAT-073 decisions

## D-073-01 — Make avatar choice profile-owned

Store a local ChildGender on ChildProfileItem and drive each avatar directly from that value. Do not derive the avatar from array order.

## D-073-02 — Keep the new value out of AI context

The requested choice selects an avatar only. Do not add gender to story context, AI personalization, consent, analytics, or an API contract because the canonical SRS does not define those uses.

## D-073-03 — Keep mock fixture appearance stable

Assign explicit demo values that preserve the current illustration shown for each seeded profile. These values are fixture choices, not gender inferred from names or real-child records.

## D-073-04 — Require explicit selection for new profiles

Start the create form with no selection and disable save until the parent chooses Nam or Nữ. Show both corresponding avatars in the selector. Let the profile detail form update the same value and preview it before saving.

## D-073-05 — Reuse current inline SVG artwork

Use the existing boy/girl avatar paths in ChildAvatarSvg. Add no external or generated image assets.

## D-073-06 — Keep the SRS requirement open

The implementation follows the owner's direct request in the local FE demo only. The canonical SRS v2.7-draft does not define profile gender or a gender-specific avatar. Do not treat this feature as SRS approval or extend the value into an API, persistence, or AI-context contract without a separate product decision.
