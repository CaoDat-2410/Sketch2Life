# FEAT-071 decisions

## D-071-01 — Select directly from the profile list

Tapping an active child profile on P13 should make it the currently selected profile immediately and leave the user on the list. Profile editing/details remain a separate, explicitly labeled action.

## D-071-02 — Keep current selection session-local

The canonical SRS does not say whether the last selected child persists across reloads. This feature does not add storage or claim a durable default. The UI describes the current selection as Đang dùng.

## D-071-03 — Child profiles do not switch Parent accounts

The switcher changes the selected child within the signed-in Parent account. It does not change authentication identity or access to another Parent account.

## OQ-071-01 — Persist last selected child

Whether the eventual Parent client remembers the selected child after reload or a new session remains open in the canonical SRS. Do not resolve this question by adding local storage in the local preview.

## D-071-04 — Preserve the existing P10 route redirect

Implementation review confirmed /p10-child-profiles redirects to /p13-settings#child-profiles; there is no separate mounted P10 list screen to walk through. Keep that route mapping unchanged. The dormant P10ChildProfilesPage source shares the P13 row behavior, while the active P10 detail route remains available.