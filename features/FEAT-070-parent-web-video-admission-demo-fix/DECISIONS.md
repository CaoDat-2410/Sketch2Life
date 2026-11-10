# FEAT-070 decisions

## D-070-01 — Admission result controls navigation

The script confirmation command reports whether the synthetic video request was accepted. The UI navigates to P07 only on acceptance; it does not independently infer acceptance from a quota value after the command returns.

## D-070-02 — Keep Parent quota gating

Keep the Parent-account quota check. An accepted request consumes exactly one synthetic unit, including when it is the last unit. A request with no units is rejected without navigation or consumption. The demo copy reports the post-use remaining count.

## D-070-03 — Local preview only

The Parent Web target-client question remains open. This work is a local synthetic UI preview and does not change the SRS or introduce API, billing, authentication, or provider integration.

## D-070-04 — Patch the actual served checkout

The port-5171 Vite process runs from fe-ui-full-remediation. Fixing a separate worktree did not change the user's current preview. Runtime acceptance must be verified against the source served from this active checkout.

## D-070-05 — Keep preview-mode toast behavior available in ParentContext

The active ParentContext already used `isLocalPreview()` to prefix local-only feedback, but its import was missing after separate auth-session changes. Restore that import so preview entry and accepted video admission do not throw before navigation. Keep the fix local to the existing context; do not add fallback toast behavior or suppress errors.
