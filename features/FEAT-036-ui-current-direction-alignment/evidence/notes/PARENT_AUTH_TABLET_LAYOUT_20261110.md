# Parent auth tablet layout review — 2026-11-10

## Scope and setup

Plan revision 14 covers presentation-only responsiveness for Parent sign-in, password recovery, and registration. Rendered review used the local Vite app in Edge with touch emulation enabled (pointer: coarse, hover: none) so the Parent shell occupied the viewport as it does on an iPad. The existing phone-auth design remains below the 700 px tablet breakpoint.

## Rendered measurements

| Viewport | Screen | Auth panel bounds (x, y, width, height) | Document width | Smallest primary action height |
|---|---|---:|---:|---:|
| 768×1024 portrait | Sign-in | 316, 237, 420, 551 px | 768 px | 52 px |
| 768×1024 portrait | Recovery | 316, 315, 420, 394 px | 768 px | 52 px |
| 768×1024 portrait | Registration | 316, 231, 420, 562 px | 768 px | 52 px |
| 1024×768 landscape | Sign-in | 572, 104, 420, 560 px | 1024 px | 52 px |
| 1024×768 landscape | Recovery | 572, 182, 420, 403 px | 1024 px | 52 px |
| 1024×768 landscape | Registration | 572, 98, 420, 571 px | 1024 px | 52 px |

Document width equaled viewport width at both orientations, so the reviewed pages had no horizontal overflow. Existing auth artwork and layout components were reused. The tablet layout adds safe-area-aware outer padding and larger touch controls. Sign-in, recovery, and registration routes were each opened and reviewed at both viewport sizes.

## Screenshot artifacts

The PNGs are local evidence under evidence/screenshots/parent-auth-tablet-rev14/; repository ignore rules exclude them from Git. SHA-256:

- login-ipad-portrait-768x1024.png — D873E97100F0F19789BE09902DF0C5CCA41D2633DF250B6E7729BB708D2EC044
- recovery-ipad-portrait-768x1024.png — A046F8C56B96C1370DE832F5ACE1CA577ECF8E8BBB55A4B21BB119F4C1405E76
- registration-ipad-portrait-768x1024.png — 7B0541D37A4A5A48434CA1B34E5508BD736BCD10F519685A3A429DE018BE11EE
- login-ipad-landscape-1024x768.png — 2EA8EA1290394DDAC71043F5D29BAFF28DD7536378C8AA53A55418E1F76B7F6A
- recovery-ipad-landscape-1024x768.png — 4B35C94BBB50B990BC78A816379A83E3C7A13FE7F48D9F606EDD3E89A44D606B
- registration-ipad-landscape-1024x768.png — 2E9A9179BF7B1E83CA52B46E7ED468D58B66F6ECC0DA4A3697460721DA2CC645

## Source verification and limits

Vite returned HTTP 200 for /p11-authentication, /p14-password-recovery, /p15-parent-registration, src/pages/ParentScreens.tsx, and src/styles/parent-login-animation.css. git diff --check passed; Git reported only CRLF-to-LF normalization warnings for existing feature Markdown. No automated tests or production build were run. This review used touch-emulated browser viewports, not a physical iPad. Parent Web target-client scope and Parent registration/recovery UX remain open in the canonical FEAT-063 SRS v2.7-draft.