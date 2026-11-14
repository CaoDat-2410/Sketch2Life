# FEAT-069 Plan Rev6 — streamline and polish Parent home

- **Status:** APPROVED by the project owner's direct request in this conversation; record the exact plan hash in both task approval registers before implementation.
- **Date:** 2026-11-14 (Asia/Saigon).
- **Branch:** `FE_UI_Project_Ver2` (keep the current checkout).
- **Scope:** UI-only adjustment in `UI_Project/parent-ui` plus FEAT-069 evidence/status. Remove the redundant active-child summary card from the Parent homepage and refine the hero's spacing/emphasis so the story artwork and main action lead the page.

## Authority and behavior boundaries

- Canonical working product baseline: FEAT-063 SRS v2.5-draft, still unsigned. §5.1 describes choosing a child profile before creating a Parent run; the user's clarification says this choice already occurs in the start-story flow.
- Do not add a new profile picker to the home page. Keep the existing child selection in the story-start flow, Family Profile selection/editing, and child-specific story context unchanged.
- Keep the current UI-only preview contract: no API/auth/persistence, no new child data, no generated bitmap asset and no backend/SRS change.
- Leave Teacher, School Manager, Platform Admin, shared web, Android host logic, and previously excluded legacy `apps/`/Child Expo directories untouched.

## Changes

1. Remove the “ĐANG DÙNG HỒ SƠ” active-child card from `renderHome`; do not remove profile controls from the Family Profile or story-start flow.
2. Rebalance the Parent home vertical rhythm and hero presentation after the card is removed: lead directly from the brand/header into the story illustration, give its headline/art room to breathe, and preserve the prominent “Bắt đầu kể” action and fixed bottom navigation. Use existing assets and responsive styles.
3. Keep the active-run resume card when an unfinished story exists; this is a distinct continuation state, not a duplicate selected-profile summary.
4. Build the Parent workspace and inspect the running preview at a phone viewport.
5. Update FEAT-069 decisions, execution evidence, status and source/context records. Run `python tools/validate_repository_security.py` before every commit and immediately before any previously authorized normal push, with no force push.

## Acceptance criteria

- AC1: Parent home no longer shows the selected-child summary/banner.
- AC2: Tapping “Bắt đầu kể” still reaches the current child-profile choice in the story-start flow, and selecting a profile continues to control the run's child context.
- AC3: Family Profile and child profile controls still work; no profile CRUD or gender preview behavior is lost.
- AC4: The home composition reads clearly from header → story hero/art → start action; the card's old vertical gap is not left behind, and the page remains responsive at narrow mobile width.
- AC5: Existing active-run resume remains visible when applicable; the standard no-run home keeps its simple hierarchy.
- AC6: Parent `npm run build` passes, and the running preview returns the updated home for review.
- AC7: Feature status/evidence reflects the result and any limitation; repository security validation passes before commit/push.

## Explicit approval

The owner directly requested removal of the card, explained that the child is selected when starting a story, and authorized polishing the Parent homepage. This is exact approval for the bounded scope above. It does not authorize changes to APIs, data contracts, SRS, backend behavior, or other workspaces.
