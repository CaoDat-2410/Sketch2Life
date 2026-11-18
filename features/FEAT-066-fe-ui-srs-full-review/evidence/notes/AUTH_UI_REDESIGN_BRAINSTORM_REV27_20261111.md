# Web authentication redesign brainstorm — Rev27

## Problem frame

Three web portals share the `/login` component but identify separate actors: Teacher, School Manager and Platform Admin. The v2.7-draft Rev57 SRS is the canonical working baseline and remains unsigned. Content Admin is a permission within Platform Admin; Parent is a separate mobile role. Current auth already has correct portal mappings, role-aware copy, a Firebase/backend adapter, local-preview state, visible admin role-discovery limitation, and a mismatch page. The redesign should make the entry action and the currently selected role unmistakable without changing identity, authorization or routes.

The current split layout has a large role-specific headline and three portal cards competing with the login panel. It uses the shared warm paper/cobalt/crayon palette, but mobile compresses all three portal cards and hides their state labels. Existing Rev23 `auth-portals.png` is a visual concept, not a source of new auth requirements.

## Idea set

| Option | What changes | Benefit | Main trade-off / risk | Smallest validation |
|---|---|---|---|---|
| A. Refine current split | Reduce headline and portal-card weight, retain current form position and SVG art. | Lowest effort; preserves familiar hierarchy and routing. | Still feels close to the current screen; cramped three-card selector remains likely on phones. | Teacher desktop and 390px screenshot. |
| B. Crayon learning studio (recommended) | Put the role-specific sign-in panel first in hierarchy, keep three clear portal links in a compact accessible selector, use Vietnamese-first copy and a single school illustration. Reuse the existing Three.js school model on wide screens; keep a static SVG fallback and restrained/mobile-safe rendering. | Stronger focus on signing in, clearer role context, closest to the approved school/crayon visual language, and reversible within the shared component/CSS. | Requires careful form/selector order at 390px and a no-WebGL fallback. | Capture all three roles at 1440, 1024, 768 and 390; check link destinations, reduced motion, keyboard focus and fallback. |
| C. Role-first gateway | Replace the current role-specific login pages with a shared role-selection step before the form. | One explicit portal choice before credential entry. | Adds a step and changes navigation/session expectations without a requirement in SRS; creates more cross-role confusion. | Prototype flow only, but requires separate product approval. |

## Trade-off and recommendation

Option B has high user impact, moderate effort, high reversibility, and low authorization/privacy risk because it keeps every existing route, URL, auth adapter and role check. The existing Three.js dependency and scene are already in the worktree; reuse them rather than adding a dependency. Load the scene only as decoration, retain the SVG fallback, respect reduced motion, and ensure the form remains complete when WebGL is unavailable.

Option A is credible but does not address the mobile portal-card density or make a clear visual reset. Option C changes workflow without SRS support and is not selected.

## Decision and validation

Proceed with Option B under direct user authorization. Preserve `Teacher → teacher`, `School Manager → school_manager`, and `Platform Admin → platform_admin`; keep `Content Admin` as a permission only. Preserve local preview as clearly non-authenticating; never add sample credentials, fake success, a password-reset flow, support flow, organization picker or live provider request. Keep role mismatch behavior unchanged.

Before code, Rev27 plan and approval are recorded in FEAT-066. After implementation, capture 12 loopback-only images at 1440×900, 1024×768, 768×1024 and 390×844 for all three web roles. No production credentials, real user/child data, backend calls, tests/builds, commit or push.

## Open dependencies

- SRS v2.7-draft Rev57 remains unsigned.
- Platform Admin role discovery is explicitly not available in the current frontend/backend contract; keep its limitation visible.
- A local preview can validate presentation and existing synthetic preview behavior only; it cannot prove authenticated Firebase/backend behavior.
