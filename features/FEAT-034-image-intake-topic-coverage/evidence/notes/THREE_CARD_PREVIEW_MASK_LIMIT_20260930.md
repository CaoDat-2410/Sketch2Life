# Three-card preview and mask-area mismatch

Owner selected three visible activities with “Xem thêm”. Mobile now slices the ordered list to three until expansion, retains all eligible candidates and adult selection, resets expansion for a new profile/session/topic, and labels a selected activity outside the preview after ranking changes. No readiness checklist added.

Read-only/in-memory diagnostic of the running failed session: source-derived mask is grayscale L, 335×597, black/white extrema 0/255; effective foreground fraction 0.815950398759969. No image bytes, tokens/capabilities, or child information retained here. Source, rig package and mask reads were HTTP 200; Android logs reported MASK_AREA_INVALID. Worker ceiling was 0.85 versus renderer 0.75. This establishes the rejection cause, not proof that the oversized mask describes the intended subject correctly.

Worker default ceiling is now 0.75. Existing multimask candidate selection prefers a valid alternative; if none qualifies it remains a typed rejection. Renderer safeguards are unchanged. No clipping, whole-frame animation or added automatic retries.

Verification: mobile `tsc --noEmit` passed; `validate-ui-copy.mjs` passed with updated preview assertions; SAM runtime suite 6 passed (including both new oversized-mask regressions); Ruff passed. Installed NumPy into the existing ignored backend virtualenv to execute previously skipped synthetic tests; no dependency manifest or provider/GPU changes.

Local `runtime-output/` logs are now explicitly ignored: startup/build logs contain machine paths and are not publication evidence. Files remain available locally; nothing was deleted.

Live deployment remains unverified: local Metro hot reload serves the UI change, but the external Lightning process needs this source revision and a restart. Existing cached masks are not replaced; use a new session after worker deployment. No claim of end-to-end successful rigging from synthetic tests.
