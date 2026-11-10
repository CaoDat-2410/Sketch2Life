# Parent tablet/iPad layout review — 2026-11-10

## Scope and implementation

- Approved plan: `plan/PLAN_REV16_PARENT_TABLET_LAYOUT.md` (SHA-256 `A48D81C858DB9B5E6AEC754AE466DDD2C6460875D11F73DBB70A6DF939AD5932`).
- Updated `apps/shared/parent-ui.css` with a touch-first tablet breakpoint for non-auth Parent pages: content is centered up to 1080 px, the bottom navigation is centered up to 1000 px, safe-area-aware page spacing is applied, and primary controls receive larger minimum heights.
- Added a landscape quota grid so the usage summary and purchase controls can sit side by side while the usage history spans both columns.
- Preserved the existing auth tablet layout and phone rules. A final landscape-only Home density refinement reduces page gaps, the Home hero height, and story thumbnail height to expose more content above the bottom navigation.
- No Firebase/auth/API behavior, product requirements, assets, dependencies, or other portals changed.

## Visual evidence

The local Vite Parent preview used synthetic demo data. Screenshots were captured with touch emulation at the pixel viewport sizes shown in their filenames and were manually inspected:

| Screen | Portrait | Landscape |
|---|---|---|
| Home | `screenshots/parent-tablet-rev16/home-ipad-portrait-820x1180.png` | `screenshots/parent-tablet-rev16/home-ipad-landscape-1180x820.png` |
| History | `screenshots/parent-tablet-rev16/history-ipad-portrait-820x1180.png` | `screenshots/parent-tablet-rev16/history-ipad-landscape-1180x820.png` |
| Capture | `screenshots/parent-tablet-rev16/capture-ipad-portrait-820x1180.png` | `screenshots/parent-tablet-rev16/capture-ipad-landscape-1180x820.png` |
| Quota | `screenshots/parent-tablet-rev16/quota-ipad-portrait-820x1180.png` | `screenshots/parent-tablet-rev16/quota-ipad-landscape-1180x820.png` |
| Settings | `screenshots/parent-tablet-rev16/settings-ipad-portrait-820x1180.png` | `screenshots/parent-tablet-rev16/settings-ipad-landscape-1180x820.png` |
| Phone Home regression | `screenshots/parent-tablet-rev16/home-phone-regression-375x812.png` | — |

The reviewed tablet renders use viewport widths of 820 px and 1180 px, with screenshot heights of 1180 px and 820 px respectively. The landscape content column and navigation are visibly bounded and centered; the quota view uses two columns. The phone screenshot retains the compact phone composition. The screenshot set has the following SHA-256 hashes:

| Screenshot | SHA-256 |
|---|---|
| `capture-ipad-landscape-1180x820.png` | `6AADB8CC18D92CBE989C53CB3179BDA952FD83BFB9D636B5A1681E7E1E745834` |
| `capture-ipad-portrait-820x1180.png` | `6AC39FD9EC233ED8ED753B83DEF8612E0F6B166985BA6002AEC0A34806D59275` |
| `history-ipad-landscape-1180x820.png` | `02486626B50FD6C01AAFCC66D9EBAA7C6473D5B02B8F411208D7984522335A62` |
| `history-ipad-portrait-820x1180.png` | `3D78C9535924EB6253A2CAF742E0E71D6CEE4C8AA0A6D9A110F28AEBB948D748` |
| `home-ipad-landscape-1180x820.png` | `024ECE6324716E177403329F1692AE8296BE29DE01AE867A66C90AE2962FCD20` |
| `home-ipad-portrait-820x1180.png` | `7EB882D48687E81912EBA71CC68A1CEC04BEAD217A7706B48D26D9D7C4F57022` |
| `home-phone-regression-375x812.png` | `3EE083C8E3CFA9D517F34A90320698CEE168B52403E152229E87C27334CA6723` |
| `quota-ipad-landscape-1180x820.png` | `C55E2A4D4988FF5495F14B103958B21C259D40D3DB3D7011FDE7B8C19A88EE25` |
| `quota-ipad-portrait-820x1180.png` | `9342F071C02AC03B647B0926480A9F44D1BA9BE815E7A22AFCC529FBC7C5BCDF` |
| `settings-ipad-landscape-1180x820.png` | `D7EAC79C7867E0B93DB18940FD308EE8A4AF0D5C64FE3A33A010EE3A74C76E36` |
| `settings-ipad-portrait-820x1180.png` | `530D08B818FF115D0AE0FE449E23E5D9C56EE570E28CA7C30BB1E71CD7CC9CB5` |

## Limits

- The final landscape Home density rule was applied after these screenshots. Vite logged HMR updates for `apps/shared/parent-ui.css`, but this tool session could not connect to the local browser/CDP socket to recapture the final Home state. Treat the landscape Home screenshots above as evidence for the preceding tablet layout rules, not as a rendered image of the final density tweak.
- The screenshots were reviewed visually. A post-change DOM `scrollWidth` measurement was not available in this session, so no numeric document-width equality claim is made. No physical iPad was used.
- The local Vite server remained active at `http://127.0.0.1:5171/`. No automated tests/builds, deployment, commit, or push were performed.
