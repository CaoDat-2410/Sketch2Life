# Role navbar and notification icon refresh (Rev18)

Date: 2026-11-11 (Asia/Bangkok)

## Authority and approval

- Canonical working baseline: FEAT-063 SRS v2.7-draft Rev57, SHA-256 `BE0D656966FDE91BA7CD5C914C319EF301D137985EF5CC91B94F36FEBCF61FB5`; unsigned and awaiting owner sign-off. Rev18 is visual styling only.
- The user directly requested an icon redesign using the design skill and asked to stop after presenting it. Plan Rev18 and the matching approval were recorded before source edits. Plan SHA-256: `AA075090DFD47E98B62B5287BDDABF9BD199395847CDAA9FB1275C34A789D9FA`.
- Worktree/branch: `F:/Github/Sketch2Life-worktrees/fe-ui-web-remediation`, `codex/fe-ui-web-remediation`.
- Applied `design-taste-frontend` and `frontend-design`; the two user screenshots were used as visual references.

## Implementation

- Added a navigation/notification presentation variant to the shared icon renderer at `apps/shared/RoleDashboardIcon.tsx`. Navigation uses familiar full-color system emoji glyphs (house, people, books, art, video, star, clock, profile, settings and door); notification/inbox uses one clear bell across all roles.
- Applied the variant in the dedicated Teacher, School Manager and Platform Admin shells. It covers sidebar navigation, role marks, account/logout icons, quota/organization header marks, and notification/inbox controls. Disclosure chevrons remain directional glyphs. Page-content icons remain on the Rev17 SVG family.
- Emoji use the platform font stack (`Segoe UI Emoji`, `Apple Color Emoji`, `Noto Color Emoji`) without new assets or packages. Existing labels, aria names, role checks, routes, unread count, notification indicator and unavailable inbox semantics remain unchanged.

## Manual review

- EV-021 includes nine screenshots under `evidence/screenshots/role-nav-icons-v18/`: each role's authenticated dashboard at 1440x900 and 390x844, plus dark desktop at 1440x900.
- Captures used an isolated browser target and only the loopback Vite previews at `127.0.0.1:5172`, `:5173` and `:5174`; other HTTP(S) requests were blocked. The helper restores the browser storage snapshots after capture.
- All nine captures report no horizontal overflow or Vite error overlay; no browser runtime exception was observed. The Teacher unread badge remains visible, School Manager still labels its inbox unavailable, and the Platform Admin indicator remains present.
- Screenshots were visually inspected at all three breakpoints/themes. The emoji glyphs fit inside existing icon containers; no navigation label, hit area or navbar layout change was introduced.

## Validation limits

- Visual preview only; no automated tests/builds or screen-reader audit were run. The emoji glyph spans stay `aria-hidden`, while existing adjacent labels and button names remain.
- No backend/API, external asset/provider, user/child data or credential was used. The work remains uncommitted and unpushed for user review.
