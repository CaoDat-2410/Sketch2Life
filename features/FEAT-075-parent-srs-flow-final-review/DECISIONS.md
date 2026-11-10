# FEAT-075 Decisions

## D1 — Current requirement authority and flow boundary

Use only FEAT-063 SRS v2.7-draft Rev57 §§5.1, 6.2.2, 7.2, 7.4, UC-01/UC-02, and applicable BR/FR/AC requirements as the current product baseline. This SRS is unsigned and remains a working draft.

## D2 — Preserve open product questions

Parent activity catalog behavior for runs without a pinned lesson remains OPEN at §31.10(13). Do not infer or implement either policy branch in this UI review. Demo synthetic fixture behavior is not a product decision.

## D3 — Review and fix boundary

Manually run the user-requested FE-only flow. Change only a defect reproduced in the reviewed Parent UI. Keep all prior modified/untracked worktree files; no API, backend, provider, persistence, auth-model, payment, SRS or cross-feature policy changes.

## D4 — Keep seeded accepted-job state consistent and idempotent

The local fixture starts with a video job already in progress, so its script state is treated as accepted. Admission also checks the in-flight job state before spending quota. New drafts explicitly reset the script acceptance state; the READY state used by the quality-retry path remains eligible for a revised script.

## D5 — Return keyboard focus after closing a sheet

The shared Radix dialog records the focused element on open and restores focus on close when that element remains mounted. This preserves keyboard continuity for Escape and explicit close actions without changing route behavior.
