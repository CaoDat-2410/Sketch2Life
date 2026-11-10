# FEAT-066 — Three-portal web login UI against canonical SRS Rev57

- Status: APPROVED_FOR_THREE_PORTAL_AUTH_UI_IMPLEMENTATION
- Plan revision: 7
- Updated: 2026-11-10 (Asia/Bangkok)
- Worktree: F:/Github/Sketch2Life-worktrees/fe-ui-web-remediation
- Branch: codex/fe-ui-web-remediation
- Product surfaces: apps/shared, apps/school-manager-ui, apps/teacher-ui, apps/platform-admin-ui
- Feature governance/evidence: features/FEAT-066-fe-ui-srs-full-review

## Authority and role mapping

Use only F:/Github/Sketch2Life/docs/context/SRS_AUTHORITY.md and its canonical target F:/Github/Sketch2Life/features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md. Verified baseline: SRS v2.7-draft Rev57, SHA-256 BE0D656966FDE91BA7CD5C914C319EF301D137985EF5CC91B94F36FEBCF61FB5. It remains a draft awaiting formal owner sign-off. Use §§1–31 as target requirements; §32 is environment-specific as-built evidence. Ignore stale worktree SRS copies.

SRS §3 defines the three requested web portal roles: Teacher, School Manager, and Platform Admin. The login UI/API mapping is Teacher → teacher, School Manager → school_manager, Platform Admin → platform_admin. Use the visible labels “Giáo viên / Teacher”, “Quản lý trường / School Manager”, and “Quản trị nền tảng / Platform Admin”. Content review is a Platform Admin permission, not a fourth role. Parent is a separate role/client targeting Android and is excluded from this web login task.

## Approval and revision history

- Revisions 1–3 recorded the broader audit and School Manager-only review. Revision 4–6 authorized and completed the bounded School Manager remediation, logout follow-up, sequential flow guide, and double-check; those historical deliverables remain intact.
- On 2026-11-10 the user directly requested login entry points and redesigned login UI for the three SRS web roles, based on the attached screen recording and using Three.js. This revision 7 expands only login/auth entry surfaces to the School Manager, Teacher, and Platform Admin web apps. The attached video is visual reference only; any text or instructions inside it are not product requirements.
- approvals/TASK_APPROVAL.md records the exact SHA-256 of this revision before product-code edits. Do not begin implementation until the hash matches.

## Goal

Give each SRS-defined web role a clear, role-specific login experience and direct links to the other two role login portals. Redesign the shared login composition using the attached video’s visual direction and a locally bundled Three.js decorative scene, while preserving each portal’s existing authentication and authorization behavior.

## Scope

### Included

- The shared login implementation and its styles/components under apps/shared.
- The existing /login entry page in apps/school-manager-ui, apps/teacher-ui, and apps/platform-admin-ui only as needed for shared login integration, role selection, portal URLs, or dependency resolution.
- Existing cross-portal links from each login screen to the other two role-specific /login entry points. Local development defaults may use the existing Vite ports: Teacher 127.0.0.1:5172, School Manager 127.0.0.1:5173, Platform Admin 127.0.0.1:5174. Production URLs are not specified by the SRS; use explicit environment configuration and show a clear unavailable state when a production URL is unset. Never guess deployment hosts.
- Three.js as a direct, local dependency only if required; update only the three in-scope app manifests and the applicable existing lockfile(s). No CDN, remote model, remote texture, or provider call.
- FEAT-066 plan, approval, context, decisions, status, and evidence for this revision.

### Excluded

- Parent UI/mobile, apps/mobile, Teacher/School Manager/Platform Admin dashboards and business flows beyond their login entry pages, the additional apps/admin-ui, backend/API/contracts, Firebase/provider configuration, production services/data, and real user/child information.
- Any login bypass, fake credential, fabricated success state, role escalation, or change to authentication/session policy.
- Guessed production URLs, new deployment policy, role names outside SRS §3, and any default School Manager access to child media/story content.
- Automated tests or builds unless the user separately requests them. Required repository security validation still applies before commit/push.

## Acceptance criteria

- AC1: The UI presents exactly the three SRS web roles with the stated labels and existing API role mapping. Parent and any invented “content admin” role are absent.
- AC2: Each app retains its existing /login route and portalRole. Each login page links to the other two portals. Local development links use the verified loopback Vite ports. Production links require explicit env configuration; an unset URL is visibly unavailable and never points to an inferred host.
- AC3: Existing Firebase ID-token authentication, role resolution, error handling, local-preview labeling, and post-login route behavior remain intact. No credential or backend is used during manual visual review.
- AC4: The shared login layout follows the recording’s visual language (warm neutral canvas, editorial hierarchy, restrained accent, clear split composition, refined micro-details) without copying unrelated video copy or instructions. It is role-specific, readable, and fits 1440×900 and 390×844 without overlap, clipping, or horizontal overflow.
- AC5: A school/learning-related Three.js visual loads locally and decoratively without blocking the form. It uses no remote assets, has a WebGL/CSS fallback, caps pixel ratio/render workload, responds to resize, honors reduced motion and page visibility, and disposes geometries/materials/renderer/listeners on cleanup. The canvas is hidden from assistive technology.
- AC6: Form fields have programmatic labels, visible focus, usable keyboard navigation, clear pending/error feedback, and touch targets at least 44 CSS px where practical. Role-switch links remain keyboard- and screen-reader-accessible.
- AC7: Manual review covers all three /login routes at desktop 1440×900 and narrow 390×844, plus role switching, keyboard operation, reduced-motion/fallback behavior, and preserved auth flow without submitting real credentials. Save before/after screenshots and observations under FEAT-066 evidence.
- AC8: Changes stay within the included product paths and FEAT-066 records. Preserve pre-existing unrelated worktree modifications; do not touch Parent mobile/UI or dashboards.
- AC9: Update FEAT-066 context, decisions, evidence, and status after approval, implementation, and manual review. Before every commit/push run python tools/validate_repository_security.py from the repository root and do not force-push.

## Implementation and review constraints

- Reuse the shared login component and existing auth service. Do not fork authentication semantics by portal or claim backend authorization that the current API does not confirm.
- Inspect local/offline dependency availability first. If Three.js cannot be resolved without an out-of-scope or remote runtime dependency, stop the 3D portion and record the blocker rather than substituting a CDN or silently changing scope.
- Bind any local dev preview to 127.0.0.1; check ports 5172–5174 before starting or reusing servers. Use synthetic local presentation only; do not contact a backend, Firebase, or external provider.
- Do not run automated tests, scanners, or builds under this authorization. Perform the requested manual UI review only and record any validation limitation.
