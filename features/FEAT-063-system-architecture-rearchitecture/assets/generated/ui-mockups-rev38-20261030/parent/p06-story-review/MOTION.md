# P06 — Motion notes

Role: Parent. Proposed interaction for a static mockup; no executable animation is included.

## Suggested behavior

Scenes stay read-only. Rewrite request updates revision and counter only after the response; no fake progress.

## Accessibility

- Respect reduced-motion preferences; use immediate state replacement.
- Do not communicate state by color or motion alone.
- Do not fabricate loading progress, ETA, or success.
