# Feature decisions

## D-069-01 — Canonical product requirements

Use FEAT-063 SRS v2.5-draft as the working target. Leader transcript items that conflict with it remain open owner questions; do not silently change activity order, child-profile data, or AI flow contracts.

## D-069-02 — Parent transcript and AI guide truthfulness

Keep adult transcript editing/review while removing redundant instruction copy. Do not imply ASR or line-sketch AI is connected. A code-native static guide may be topic-aware but must not use child profile/media.

## D-069-03 — Context confirmation

Use a compact confirmation dialog in place of a separate context-selection page. The adult still reviews and confirms the allowed context snapshot before story generation, as required by FR-P-06.

## D-069-04 — API data boundary

Teacher role screens remain preview-only until an authenticated principal and organization context can be resolved through a supported bridge and mounted endpoint. Do not seed tenant IDs or claim fixture counts came from backend.
