# FEAT-084 task approval

## Plan Rev1 — Parent mobile UI review and polish

- **Status:** APPROVED
- **Approver:** Project owner, direct instruction in this conversation (2026-11-23 03:29:50 UTC): review all mobile Parent UI, make copy more concise and child-friendly where appropriate, add suitable visuals while preserving the current components and colors.
- **Approved scope:** The exact code-file allowlist and acceptance criteria in `plan/PLAN_REV1_PARENT_MOBILE_UI_POLISH_20261123.md`.
- **Plan SHA-256:** `0E368C391E983D268EAD5DCF2D07434E9FA14BB3B19EF33647876FEA98AEBB75`.
- **Runtime limits:** No tests/typecheck, emulator, API/Modal inference, database migration, security validation, commit or push.
- **Constraints:** Preserve existing workflow/business rules, safety and consent copy, data-driven suggestions, and existing approved artwork. No new raster assets.

## Plan Rev2 — Android UI screenshot evidence

- **Status:** APPROVED
- **Approver:** Project owner, direct request in this conversation (2026-11-23 03:46:24 UTC): run the UI and capture the screens.
- **Approved scope:** Launch the real Expo app on Android and capture accessible Parent screens under `evidence/screenshots/android/`, as detailed in `plan/PLAN_REV2_ANDROID_UI_SCREENSHOTS_ADDENDUM_20261123.md`.
- **Addendum SHA-256:** `198E10277E63B1EA22349416BE18C44BF633033BE6B5B80DEAF13AADB4F73C43`.
- **Runtime limits:** Existing synthetic session only; no new account/profile/consent or backend seed, no AI/Modal inference, tests/typecheck, API behavior test, commit or push.
- **Constraints:** No preview harness or fixture; avoid real child/account data and respect auth/consent/workflow gates.

## Plan Rev3 — Existing synthetic account for Parent screenshots

- **Status:** APPROVED
- **Approver:** Project owner, direct request in this conversation to run the UI and capture screens (2026-11-23).
- **Approved scope:** Sign in to the already provisioned Parent synthetic account from the ignored root `.env`, then navigate real app screens backed only by existing synthetic records; see `plan/PLAN_REV3_EXISTING_SYNTHETIC_LOGIN_SCREENSHOTS_20261123.md`.
- **Runtime limits:** Ordinary authentication and read-only retrieval solely for screen rendering are allowed. No account/profile/consent/session/lesson writes, seeds, AI/Modal/video/quota/payment, tests/typecheck, source-code changes, commit or push.
- **Constraints:** Never reveal or screenshot credentials; do not bypass auth, consent, or workflow gates; no preview harness or fixture; stop only the Metro/emulator started for this task.
- **Plan SHA-256:** `248747253C1BE7C4827CD0E532771B3A78C664C7217D4EC3E1365749622E98F6`.
