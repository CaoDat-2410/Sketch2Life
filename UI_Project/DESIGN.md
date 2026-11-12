# Sketch2Life Design System

## Design direction

Sketch2Life turns children's drawings and narration into stories and real-world activities. The Parent Android app should feel like a calm, illustrated story companion: one warm yellow creation moment, blue actions, original story artwork, and plain, reassuring steps. Teacher, School Manager, and Platform Admin use a shared web workspace with clear navigation, original page illustrations, warm paper surfaces, and an accent for each role.

The user-provided screens and video are visual references, not source copy or workflow authority. Product content and flows follow the repository's current SRS authority (2.7-draft Rev60 at the 12 November 2026 audit), leader review notes, and verified application behavior. Open decisions remain open in the interface.

## Visual tokens

| Token | Value | Use |
| --- | --- | --- |
| Brand blue | `#315EFB` | Main actions, focus, active states |
| Deep blue | `#244CD8` | Hover and strong links |
| Story yellow | `#F4C84E` | Parent creation moment and small warmth cues |
| Ink | `#17233B` | Main text |
| Secondary ink | `#46536A` | Supporting copy |
| Muted ink | `#68758A` | Metadata |
| Canvas | `#F6F8FC` | Parent stage and web workspace |
| Surface | `#FFFFFF` | Forms, cards, navigation |
| Rule | `#E1E7F0` | Borders and separators |
| Success | `#16835F` | Success state only |
| Danger | `#AF4646` | Destructive state only |

Use Baloo 2 for short Parent story headings, DM Sans for web workspace headings, and Be Vietnam Pro for reading and controls across all roles. Follow an 8px spacing rhythm and soft, low shadows. Web workspaces use warm paper neutrals with role accents: Teacher `#2E735D`, School Manager `#326A78`, Platform Admin `#536D9A`. Yellow `#F6D57E` draws attention to the primary dashboard action. Status color is always paired with a label or icon.

## Parent Android expression

- Design mobile-first and preserve the existing four destinations: Trang chủ, Lịch sử, Lượt tạo, and Cài đặt. Child profiles remain inside Settings.
- Use a full-height Android-sized canvas; respect safe areas and keep fixed navigation from covering scroll content.
- Translate the supplied mobile reference's cozy illustrated scenes, rounded character art, compact dashboard hierarchy, and bold dark CTA into original Sketch2Life story artwork. Use warm cream, sage, honey yellow, and charcoal surfaces; keep project blue in the brand mark and focus treatment.
- Use a restrained storybook depth: soft paper layering, one expressive home illustration, tactile buttons, and purposeful motion. Keep the rest of the interface calm and scannable.
- Adapt the reference's visual language to drawing-to-story creation; do not add unrelated streaks, coins, or reward mechanics to the Parent workflow.
- Use 48px minimum Android touch targets, clear pressed feedback, predictable back/continue actions, and visible focus states.
- Keep motion short and purposeful. Respect reduced-motion settings; never make essential progress depend on animation.
- Keep the lesson optional and pin its exact version before drawing. Do not add activity selection before video creation; show activities after the video only when the family pinned a lesson. Keep script review before video creation and feedback at the end of the completed session.
- Use concise visible labels and one-line helper copy; put secondary explanations inside disclosure panels or the relevant confirmation step.
- Maintain readable light and dark themes, reduced motion, visible keyboard focus, and descriptive accessible names for icon-only controls.

## Web workspace expression

- `web-ui` is the single entry point for Teacher, School Manager, and Platform Admin. It presents login, invitation-based activation preview, and account recovery preview before the role-specific workspaces. Real role resolution uses Firebase Authentication and `/api/auth/v1/me`; the existing BE registration endpoint is Parent-only, so the web activation form must not claim to create accounts.
- All three web roles share DM Sans headings, Be Vietnam Pro body text, a light paper canvas, white navigation rail, thin separators, and rounded surfaces. Role accents distinguish teaching, school operations, and platform operations.
- Keep Teacher, School Manager, and Platform Admin navigation and routes role-specific. No role may reveal another role's workspace.
- Keep the teacher teaching tasks grouped under “Bài giảng trên lớp”; keep settings separate. Place lesson sharing with lesson management.
- Use page titles, concise section labels, status chips, tables, and compact KPI strips to prioritize important information. Avoid nested cards and repeated explanatory paragraphs.
- Each role follows a different user-supplied dashboard reference: Teacher uses the Education layout with lesson progress, topic bars, class and sharing cards; School Manager uses the Project Management layout with class assignment progress, review work, teacher workload, and milestones; Platform Admin uses the E-Commerce layout with grouped content columns, catalog and moderation tables, organization status, and an operations snapshot. Keep the Sketch2Life shell, role colors, and data labels consistent across all three.
- Each dashboard has four role-specific KPI links. Derive preview counts and visualizations from the same fixture collections shown in lists. Do not invent growth trends, deadlines, or real-time telemetry. Teacher class data is limited to the signed-in teacher's assigned class in the preview.
- Keep dimensional motion to the paper illustration and short interaction feedback: a shallow 3D tilt, gentle floating, brief KPI lift, and chart reveal. Page changes use a short fade and upward arrival. Motion is optional and disabled by `prefers-reduced-motion`; text and actions never depend on it.
- Use dialogs only for confirmation or protected focus. Dialogs must support Escape, outside dismissal when safe, focus management, and a visible close or cancel action.
- The three role workspaces are UI previews. Search, filters, detail drawers, local drafts, and workflow steps work in the browser. Do not present a preview operation as a backend mutation. Restore role-specific API integration after the contracts are confirmed; see `WEB_UI_SCOPE.md` and `WEB_FEATURE_AUDIT.md`.

## Component and accessibility rules

- Radix Dialog and Accordion primitives provide focus management, keyboard behavior, and disclosure states. Keep the wrappers in `shared/ui.tsx` and theme them with shared design tokens.
- Use the project's existing SVG icon components. Do not use emoji as interface icons.
- Labels stay visible with form controls; errors appear next to the relevant control. Keep feedback and progress states legible without relying on color alone.
- Maintain a visible 3px focus ring, minimum 44px touch targets on Parent, and reduced-motion support.
- Preserve the documented workflow and permission boundaries while adding backend integration. Preview data is labeled explicitly until the corresponding API is connected.

## Brand

Keep the Sketch2Life name. Use the shared drawing-page mark in `shared/BrandMark.tsx`: a white drawing page, a blue story stroke, and one small yellow spark. Parent illustrations remain original project assets and are used sparingly at story moments.
