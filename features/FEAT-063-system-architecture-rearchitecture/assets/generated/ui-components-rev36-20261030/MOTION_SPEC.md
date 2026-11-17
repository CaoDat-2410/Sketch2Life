# Motion notes — Rev36 component patterns

These notes are interaction recommendations only; the images do not implement behavior. Honor reduced-motion preferences, keyboard and screen-reader support, and server-confirmed state.

## UI01 — Foundations and controls

- Button press/focus/hover: 100–140 ms color/elevation transition; visible focus ring must not depend on animation.
- Switch: thumb transition 120–160 ms, then persist only after command/request acceptance where applicable.
- Disabled/loading controls remain static or show a small indicator; do not pulse every component.
- Reduced motion: immediate color/state change, keep focus outline.

## UI02 — Parent dialogs and bottom sheets

- Open/close: backdrop fade plus dialog scale/slide over 160–220 ms. Return focus to the invoking control.
- Script confirmation: closing the dialog never confirms; confirm is tied to the exact script revision/hash.
- Cancel-run: keep the non-refundable accepted-quota consequence visible until the adult chooses; require explicit destructive action. Do not imply quota refund.
- Camera sheet: explain camera and gallery paths before system permission prompt; denied camera still leaves gallery option available.
- Reduced motion: show/hide immediately. Preserve explicit actions and accessible focus order.

## UI03 — Web decision dialogs

- Dialog enters with a short 150–180 ms fade; checklist/required-reason validation appears inline.
- Manager approval, Teacher archive, and Admin hide update page/visibility only after the corresponding API response succeeds. No confetti or optimistic state.
- Reduced motion: no entrance transition; keep confirmation and focus management.

## UI04 — Toasts, snackbars and inline notices

- Success/informational toast: enter/exit in 140–180 ms; use brief auto-dismiss only when no action is required. Keep a close affordance.
- Warning/stale-revision notices remain until resolved or dismissed. Retryable send failure persists with action and retains the user's draft.
- Announce meaningful updates through the appropriate live region; do not announce transient decorative movement.
- Reduced motion: no slide; immediate appearance/disappearance.

## UI05 — API client states

- Skeleton shimmer is optional and short; show only while the read request is pending. Empty/error states appear when the request resolves.
- Stale revision reload occurs only after the adult/staff chooses “Tải lại”; never overwrite unsaved edits silently.
- Retry button is present only for retryable states. Safe 404/out-of-scope wording stays identical and does not reveal resource existence.
- Reduced motion: static skeleton blocks, immediate state swap.

## UI06 — Upload and extraction states

- Upload bar advances only from actual transferred-byte receipts. Scanning/extraction use discrete server-confirmed statuses, not animated percentage or ETA.
- Transition to `READY_FOR_REVIEW` only when completion/scan/extraction returns it. Reveal filtered fields after the extraction response; hold AI eligibility until Teacher confirms.
- Validation rejection is static with supported-file instructions and a replace-file action.
- Reduced motion: static progress fill and status labels.

## UI07 — Quota and AI job states

- Update quota only from Billing responses. Quota rejection shows purchase path when permitted and keeps old playback available.
- `AI_COST_LIMIT_REACHED` is a pre-admission hold, distinct from provider failure; do not start job progress or consume quota.
- Highlight the active named job stage only after the job-status API response. No fake percent, countdown or looping progress that suggests advancement.
- Reduced motion: static stage marker and direct status text.

## UI08 — Sharing and access grants

- Audience selection updates selected chips immediately in the unsaved form. Invite/revoke transitions show pending state only after API receipt.
- Revoke opens a confirmation dialog naming the exact grant and scope; after success, invalidate relevant access and show revoked state. Lesson grant and child-profile grant have independent state and copy.
- Do not animate or imply media access is included in Lesson access.
- Reduced motion: immediate selection and state change.

## UI09 — Feedback and notifications

- Feedback send button shows a small busy state while request is pending; append the message and show success only after API acceptance. On failure retain draft and expose retry.
- Unread badge may update after server/push receipt; use a single subtle scale/fade, no continuous pulse.
- Thread expansion 160–200 ms; no auto-scroll that interrupts reading unless the user sent a new message and the new item is in view.
- Reduced motion: immediate thread/badge state, static sent label.
